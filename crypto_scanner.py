"""
CRYPTO FUTURES MARKET SCANNER
Decision-support tool for expansion and reversion strategies
NO AUTO-TRADING - Human judgment required for all entries
MOBILE-OPTIMIZED INTERFACE
"""

import streamlit as st
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

EXCHANGES = {
    'binance': ccxt.binance(),
    'gateio': ccxt.gateio(),
    'mexc': ccxt.mexc()
}

TIMEFRAMES = {
    '3m': 3,
    '5m': 5,
    '15m': 15
}

STALE_THRESHOLD = {
    '3m': 6,
    '5m': 10
}

@st.cache_data(ttl=60)
def get_futures_symbols(exchange_name: str) -> List[str]:
    try:
        exchange = EXCHANGES[exchange_name]
        markets = exchange.load_markets()
        symbols = [
            symbol for symbol, market in markets.items()
            if market.get('type') == 'swap' 
            and market.get('quote') == 'USDT'
            and market.get('active', True)
        ]
        return sorted(symbols)
    except ccxt.errors.ExchangeError as e:
        error_msg = str(e)
        if '451' in error_msg or 'restricted location' in error_msg.lower():
            st.warning(f"⚠️ {exchange_name.upper()} blocked in your location. Try Gate.io or MEXC, or use VPN.")
        else:
            st.error(f"Error from {exchange_name}: {error_msg[:100]}")
        return []
    except Exception as e:
        st.error(f"Error fetching symbols from {exchange_name}: {str(e)[:100]}")
        return []

def fetch_ohlcv(exchange_name: str, symbol: str, timeframe: str, limit: int = 200) -> Optional[pd.DataFrame]:
    try:
        exchange = EXCHANGES[exchange_name]
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        return None

def calculate_sma(df: pd.DataFrame, period: int) -> pd.Series:
    return df['close'].rolling(window=period).mean()

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['sma_20'] = calculate_sma(df, 20)
    df['sma_100'] = calculate_sma(df, 100)
    return df

def analyze_candle(row: pd.Series, df: pd.DataFrame, idx: int) -> Dict:
    body = abs(row['close'] - row['open'])
    total_range = row['high'] - row['low']
    upper_wick = row['high'] - max(row['close'], row['open'])
    lower_wick = min(row['close'], row['open']) - row['low']
    lookback = df.iloc[max(0, idx-20):idx]
    avg_body = abs(lookback['close'] - lookback['open']).mean() if len(lookback) > 0 else body
    body_ratio = (body / total_range * 100) if total_range > 0 else 0
    upper_wick_ratio = (upper_wick / total_range * 100) if total_range > 0 else 0
    lower_wick_ratio = (lower_wick / total_range * 100) if total_range > 0 else 0
    is_bullish = row['close'] > row['open']
    return {
        'body_size': body,
        'avg_body': avg_body,
        'body_vs_avg': (body / avg_body) if avg_body > 0 else 1,
        'body_ratio': body_ratio,
        'upper_wick': upper_wick,
        'lower_wick': lower_wick,
        'upper_wick_ratio': upper_wick_ratio,
        'lower_wick_ratio': lower_wick_ratio,
        'total_range': total_range,
        'is_bullish': is_bullish
    }

def label_candle_type(candle_data: Dict) -> str:
    labels = []
    if candle_data['body_vs_avg'] > 1.5:
        labels.append(f"Elephant-like (body {candle_data['body_vs_avg']:.1f}x avg)")
    if candle_data['is_bullish'] and candle_data['lower_wick_ratio'] > 40:
        labels.append(f"Bullish Tail (lower wick {candle_data['lower_wick_ratio']:.0f}%)")
    elif not candle_data['is_bullish'] and candle_data['upper_wick_ratio'] > 40:
        labels.append(f"Bearish Tail (upper wick {candle_data['upper_wick_ratio']:.0f}%)")
    if candle_data['is_bullish'] and candle_data['upper_wick_ratio'] > 40:
        labels.append(f"Inverted Tail Bull (upper wick {candle_data['upper_wick_ratio']:.0f}%)")
    elif not candle_data['is_bullish'] and candle_data['lower_wick_ratio'] > 40:
        labels.append(f"Inverted Tail Bear (lower wick {candle_data['lower_wick_ratio']:.0f}%)")
    return " | ".join(labels) if labels else "Standard candle"

def detect_sqz(df: pd.DataFrame, idx: int) -> Dict:
    row = df.iloc[idx]
    sma_20 = row['sma_20']
    sma_100 = row['sma_100']
    price = row['close']
    distance_abs = abs(sma_20 - sma_100)
    distance_pct = (distance_abs / price * 100) if price > 0 else 0
    return {
        'distance_abs': distance_abs,
        'distance_pct': distance_pct,
        'status': f"SMAs {distance_pct:.2f}% apart — visual SQZ check required"
    }

def detect_crossover(df: pd.DataFrame, idx: int) -> Optional[str]:
    if idx < 1:
        return None
    curr = df.iloc[idx]
    prev = df.iloc[idx - 1]
    if prev['sma_20'] <= prev['sma_100'] and curr['sma_20'] > curr['sma_100']:
        return 'bullish'
    if prev['sma_20'] >= prev['sma_100'] and curr['sma_20'] < curr['sma_100']:
        return 'bearish'
    return None

def check_expansion(df: pd.DataFrame, idx: int, direction: str) -> Dict:
    row = df.iloc[idx]
    price = row['close']
    sma_100 = row['sma_100']
    distance_abs = abs(price - sma_100)
    distance_pct = (distance_abs / price * 100) if price > 0 else 0
    is_above = price > sma_100
    moving_away = (direction == 'long' and is_above) or (direction == 'short' and not is_above)
    lookback = min(5, idx)
    recent = df.iloc[idx-lookback:idx+1]
    if direction == 'long':
        directional_candles = sum(recent['close'] > recent['open'])
    else:
        directional_candles = sum(recent['close'] < recent['open'])
    return {
        'distance_abs': distance_abs,
        'distance_pct': distance_pct,
        'moving_away': moving_away,
        'directional_candles': f"{directional_candles}/{lookback+1}",
        'status': f"Price {distance_pct:.2f}% from 100 SMA, {directional_candles}/{lookback+1} directional candles"
    }

def detect_reversion_setup(df: pd.DataFrame, idx: int) -> Optional[Dict]:
    if idx < 50:
        return None
    row = df.iloc[idx]
    price = row['close']
    sma_20 = row['sma_20']
    sma_100 = row['sma_100']
    sma_distance_abs = abs(sma_20 - sma_100)
    sma_distance_pct = (sma_distance_abs / price * 100) if price > 0 else 0
    lookback = df.iloc[max(0, idx-50):idx+1]
    separation_duration = 0
    for i in range(len(lookback)-1, -1, -1):
        r = lookback.iloc[i]
        sep = abs(r['sma_20'] - r['sma_100']) / r['close'] * 100
        if sep > 0.5:
            separation_duration += 1
        else:
            break
    crosses_50 = 0
    for i in range(len(lookback)-1):
        curr = lookback.iloc[i+1]
        prev = lookback.iloc[i]
        if (prev['sma_20'] > prev['sma_100'] and curr['sma_20'] < curr['sma_100']) or \
           (prev['sma_20'] < prev['sma_100'] and curr['sma_20'] > curr['sma_100']):
            crosses_50 += 1
    prior_expansion = 'bullish' if sma_20 > sma_100 else 'bearish'
    reversion_signal = None
    if prior_expansion == 'bullish' and price < sma_20:
        reversion_signal = 'short'
    elif prior_expansion == 'bearish' and price > sma_20:
        reversion_signal = 'long'
    if reversion_signal:
        return {
            'direction': reversion_signal,
            'sma_distance_pct': sma_distance_pct,
            'separation_duration': separation_duration,
            'crosses_50': crosses_50,
            'prior_expansion': prior_expansion,
            'status': f"SMAs {sma_distance_pct:.2f}% apart for {separation_duration} candles, {crosses_50} crosses in 50 bars"
        }
    return None

def analyze_15m_context(df_15m: pd.DataFrame, direction: str) -> Dict:
    if df_15m is None or len(df_15m) < 100:
        return {'status': '15m data unavailable'}
    latest = df_15m.iloc[-1]
    price = latest['close']
    sma_20 = latest['sma_20']
    sma_100 = latest['sma_100']
    above_20 = price > sma_20
    above_100 = price > sma_100
    lookback = df_15m.iloc[-5:]
    bullish_candles = sum(lookback['close'] > lookback['open'])
    if above_20 and above_100:
        structure = "Bullish structure"
    elif not above_20 and not above_100:
        structure = "Bearish structure"
    else:
        structure = "Mixed structure"
    return {
        'price_vs_20': 'above' if above_20 else 'below',
        'price_vs_100': 'above' if above_100 else 'below',
        'recent_direction': f"{bullish_candles}/5 bullish candles",
        'structure': structure,
        'status': f"{structure}, price {('above' if above_20 else 'below')} 20 SMA — human judgment required"
    }

def detect_firewall(df: pd.DataFrame, idx: int, direction: str) -> Dict:
    lookback = df.iloc[max(0, idx-50):idx]
    current_price = df.iloc[idx]['close']
    swing_highs = lookback['high'].nlargest(3)
    swing_lows = lookback['low'].nsmallest(3)
    if direction == 'long':
        nearest_high = swing_highs.min()
        distance_pct = ((nearest_high - current_price) / current_price * 100)
        proximity = "nearby" if distance_pct < 2 else "distant"
        return {
            'level': nearest_high,
            'distance_pct': distance_pct,
            'status': f"Resistance {proximity} ({distance_pct:.2f}% above) — visual confirmation required"
        }
    else:
        nearest_low = swing_lows.max()
        distance_pct = ((current_price - nearest_low) / current_price * 100)
        proximity = "nearby" if distance_pct < 2 else "distant"
        return {
            'level': nearest_low,
            'distance_pct': distance_pct,
            'status': f"Support {proximity} ({distance_pct:.2f}% below) — visual confirmation required"
        }

def detect_liquidity_hole(df: pd.DataFrame, idx: int, direction: str) -> Dict:
    lookback = df.iloc[max(0, idx-50):idx]
    current_price = df.iloc[idx]['close']
    if direction == 'long':
        above_zone = lookback[lookback['low'] > current_price]
        if len(above_zone) > 0:
            next_swing = above_zone['low'].min()
            distance_pct = ((next_swing - current_price) / current_price * 100)
            candles_in_zone = len(lookback[(lookback['high'] >= current_price) & (lookback['low'] <= next_swing)])
        else:
            next_swing = lookback['high'].max()
            distance_pct = ((next_swing - current_price) / current_price * 100)
            candles_in_zone = 0
    else:
        below_zone = lookback[lookback['high'] < current_price]
        if len(below_zone) > 0:
            next_swing = below_zone['high'].max()
            distance_pct = ((current_price - next_swing) / current_price * 100)
            candles_in_zone = len(lookback[(lookback['low'] <= current_price) & (lookback['high'] >= next_swing)])
        else:
            next_swing = lookback['low'].min()
            distance_pct = ((current_price - next_swing) / current_price * 100)
            candles_in_zone = 0
    density = "low" if candles_in_zone < 5 else "high"
    return {
        'next_swing': next_swing,
        'distance_pct': distance_pct,
        'candle_density': candles_in_zone,
        'status': f"Next swing {distance_pct:.2f}% away, {density} density ({candles_in_zone} candles) — liquidity hole possible"
    }

def calculate_conviction(signal_data: Dict) -> Tuple[str, str]:
    issues = []
    strengths = []
    candle_label = signal_data.get('candle_type', '')
    if 'Elephant' in candle_label or 'Tail' in candle_label:
        strengths.append("Strong confirmation candle")
    else:
        issues.append("Weak confirmation candle")
    firewall = signal_data.get('firewall_status', '')
    if 'nearby' in firewall.lower():
        issues.append("Firewall nearby")
    else:
        strengths.append("Clear path")
    liquidity = signal_data.get('liquidity_status', '')
    if 'low density' in liquidity.lower():
        strengths.append("Liquidity hole present")
    if signal_data['strategy'] == 'Reversion':
        chop_status = signal_data.get('choppiness', '')
        if 'crosses' in chop_status and int(chop_status.split('crosses')[0].split()[-1]) > 5:
            issues.append("Market choppy")
    if len(issues) == 0 and len(strengths) >= 2:
        return 'A+', f"Clean setup: {', '.join(strengths)}"
    elif len(issues) <= 1 and len(strengths) >= 1:
        return 'A', f"Strong setup with minor issues: {', '.join(issues) if issues else 'good structure'}"
    elif len(issues) <= 2:
        return 'B', f"Tradeable with caution: {', '.join(issues)}"
    else:
        return 'C', f"Avoid: {', '.join(issues)}"

def scan_symbol(exchange_name: str, symbol: str, timeframe: str, df_15m: pd.DataFrame) -> List[Dict]:
    signals = []
    df = fetch_ohlcv(exchange_name, symbol, timeframe, limit=200)
    if df is None or len(df) < 100:
        return signals
    df = calculate_indicators(df)
    idx = len(df) - 1
    row = df.iloc[idx]
    candle_data = analyze_candle(row, df, idx)
    candle_label = label_candle_type(candle_data)
    sqz_data = detect_sqz(df, idx)
    for direction in ['long', 'short']:
        expansion_check = check_expansion(df, idx, direction)
        if expansion_check['moving_away']:
            context_15m = analyze_15m_context(df_15m, direction)
            firewall = detect_firewall(df, idx, direction)
            liquidity = detect_liquidity_hole(df, idx, direction)
            signal = {
                'symbol': symbol,
                'exchange': exchange_name,
                'strategy': 'Expansion',
                'direction': direction.upper(),
                'entry_timeframe': timeframe,
                'trigger_type': 'SQZ',
                'candle_type': candle_label,
                'sqz_status': sqz_data['status'],
                'expansion_status': expansion_check['status'],
                'context_15m': context_15m['status'],
                'firewall_status': firewall['status'],
                'liquidity_status': liquidity['status'],
                'choppiness': 'N/A',
                'detected_at': datetime.now(),
                'timeframe_minutes': TIMEFRAMES[timeframe]
            }
            tier, reason = calculate_conviction(signal)
            signal['conviction'] = tier
            signal['reason'] = reason
            signals.append(signal)
    crossover_dir = detect_crossover(df, idx)
    if crossover_dir:
        direction = 'long' if crossover_dir == 'bullish' else 'short'
        expansion_check = check_expansion(df, idx, direction)
        if expansion_check['moving_away']:
            context_15m = analyze_15m_context(df_15m, direction)
            firewall = detect_firewall(df, idx, direction)
            liquidity = detect_liquidity_hole(df, idx, direction)
            signal = {
                'symbol': symbol,
                'exchange': exchange_name,
                'strategy': 'Expansion',
                'direction': direction.upper(),
                'entry_timeframe': timeframe,
                'trigger_type': 'Crossover',
                'candle_type': candle_label,
                'sqz_status': 'N/A',
                'expansion_status': expansion_check['status'],
                'context_15m': context_15m['status'],
                'firewall_status': firewall['status'],
                'liquidity_status': liquidity['status'],
                'choppiness': 'N/A',
                'detected_at': datetime.now(),
                'timeframe_minutes': TIMEFRAMES[timeframe]
            }
            tier, reason = calculate_conviction(signal)
            signal['conviction'] = tier
            signal['reason'] = reason
            signals.append(signal)
    reversion = detect_reversion_setup(df, idx)
    if reversion:
        direction = reversion['direction']
        context_15m = analyze_15m_context(df_15m, direction)
        firewall = detect_firewall(df, idx, direction)
        liquidity = detect_liquidity_hole(df, idx, direction)
        signal = {
            'symbol': symbol,
            'exchange': exchange_name,
            'strategy': 'Reversion',
            'direction': direction.upper(),
            'entry_timeframe': timeframe,
            'trigger_type': 'Mean Reversion',
            'candle_type': candle_label,
            'sqz_status': 'N/A',
            'expansion_status': reversion['status'],
            'context_15m': context_15m['status'],
            'firewall_status': firewall['status'],
            'liquidity_status': liquidity['status'],
            'choppiness': f"{reversion['crosses_50']} crosses in 50 bars",
            'detected_at': datetime.now(),
            'timeframe_minutes': TIMEFRAMES[timeframe]
        }
        tier, reason = calculate_conviction(signal)
        signal['conviction'] = tier
        signal['reason'] = reason
        signals.append(signal)
    return signals

def format_signal_age(signal: Dict) -> Tuple[int, bool]:
    now = datetime.now()
    detected = signal['detected_at']
    age_minutes = int((now - detected).total_seconds() / 60)
    stale_threshold = STALE_THRESHOLD[signal['entry_timeframe']]
    is_stale = age_minutes >= stale_threshold
    return age_minutes, is_stale

def render_signals_table(signals: List[Dict]):
    if not signals:
        st.info("📡 No signals detected. Scanner running...")
        return
    for signal in signals:
        age_minutes, is_stale = format_signal_age(signal)
        if is_stale:
            st.markdown(f"""
            <div style="background-color: #2a2a2a; padding: 12px; margin: 8px 0; border-radius: 6px; border-left: 3px solid #555; opacity: 0.6;">
                <p style="color: #888; font-style: italic; font-size: 0.9em; margin: 0;">
                    ⚠️ STALE ({age_minutes} min ago)
                </p>
                <p style="color: #888; font-size: 0.85em; margin: 3px 0;">
                    {signal['symbol']} | {signal['direction']} | {signal['conviction']}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            color = "#00ff00" if signal['direction'] == 'LONG' else "#ff4444"
            st.markdown(f"""
            <div style="background-color: #1a1a1a; padding: 12px; margin: 8px 0; border-radius: 6px; border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <p style="color: {color}; font-weight: bold; font-size: 1.1em; margin: 0;">
                        {signal['symbol']}
                    </p>
                    <p style="color: {color}; font-weight: bold; font-size: 1.1em; margin: 0;">
                        {signal['direction']}
                    </p>
                </div>
                <p style="color: #aaa; font-size: 0.85em; margin: 5px 0;">
                    {signal['exchange'].upper()} • {signal['strategy']} • {signal['trigger_type']}
                </p>
                <div style="background-color: #333; padding: 8px; border-radius: 4px; margin: 8px 0;">
                    <p style="color: #fff; font-size: 0.9em; margin: 0;">
                        <strong>Conviction {signal['conviction']}:</strong> {signal['reason']}
                    </p>
                </div>
                <p style="color: #888; font-size: 0.8em; margin: 5px 0;">
                    {signal['entry_timeframe']} • {age_minutes} min ago
                </p>
                <details style="margin-top: 8px;">
                    <summary style="color: #888; font-size: 0.85em; cursor: pointer;">📊 Technical Details</summary>
                    <div style="padding: 8px 0; font-size: 0.8em;">
                        <p style="color: #888; margin: 3px 0;">🕯️ {signal['candle_type']}</p>
                        <p style="color: #888; margin: 3px 0;">📏 {signal['expansion_status']}</p>
                        <p style="color: #888; margin: 3px 0;">⏱️ 15m: {signal['context_15m']}</p>
                        <p style="color: #888; margin: 3px 0;">🚧 {signal['firewall_status']}</p>
                        <p style="color: #888; margin: 3px 0;">💧 {signal['liquidity_status']}</p>
                        {f"<p style='color: #888; margin: 3px 0;'>🌊 Chop: {signal['choppiness']}</p>" if signal['choppiness'] != 'N/A' else ''}
                    </div>
                </details>
            </div>
            """, unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="Crypto Scanner",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    st.title("📊 Crypto Futures Scanner")
    st.caption("Decision-Support Tool • Human Judgment Required")
    with st.sidebar:
        st.header("⚙️ Settings")
        selected_exchanges = st.multiselect(
            "Exchanges",
            list(EXCHANGES.keys()),
            default=['gateio', 'mexc']
        )
        selected_timeframes = st.multiselect(
            "Timeframes",
            ['3m', '5m'],
            default=['5m']
        )
        max_symbols = st.slider("Max symbols", 5, 50, 20)
        refresh_interval = st.slider("Refresh (sec)", 30, 300, 60)
        st.markdown("---")
        st.markdown("**Active Strategies:**")
        st.markdown("✅ Expansion (SQZ)")
        st.markdown("✅ Expansion (Crossover)")
        st.markdown("✅ Reversion")
        st.markdown("---")
        st.markdown("**💡 If Binance blocked:**")
        st.markdown("Use Gate.io & MEXC or enable VPN")
    if 'signals' not in st.session_state:
        st.session_state.signals = []
    status_placeholder = st.empty()
    signals_placeholder = st.empty()
    if st.button("🔄 Refresh Now") or True:
        all_signals = []
        working_exchanges = []
        for exchange_name in selected_exchanges:
            status_placeholder.info(f"📡 Scanning {exchange_name}...")
            symbols = get_futures_symbols(exchange_name)
            if symbols:
                working_exchanges.append(exchange_name)
                symbols = symbols[:max_symbols]
                for symbol in symbols:
                    for timeframe in selected_timeframes:
                        df_15m = fetch_ohlcv(exchange_name, symbol, '15m', limit=200)
                        if df_15m is not None:
                            df_15m = calculate_indicators(df_15m)
                        signals = scan_symbol(exchange_name, symbol, timeframe, df_15m)
                        all_signals.extend(signals)
        st.session_state.signals = all_signals
        if working_exchanges:
            status_placeholder.success(f"✅ Found {len(all_signals)} signals from {', '.join([e.upper() for e in working_exchanges])}")
        else:
            status_placeholder.error("❌ No exchanges accessible. Try Gate.io/MEXC or use VPN for Binance")
    with signals_placeholder.container():
        if st.session_state.signals:
            sorted_signals = sorted(
                st.session_state.signals,
                key=lambda x: (
                    {'A+': 0, 'A': 1, 'B': 2, 'C': 3}[x['conviction']],
                    format_signal_age(x)[0]
                )
            )
            render_signals_table(sorted_signals)
        else:
            st.info("📱 Click 'Refresh Now' to start scanning")
    time.sleep(refresh_interval)
    st.rerun()

if __name__ == "__main__":
    main()
