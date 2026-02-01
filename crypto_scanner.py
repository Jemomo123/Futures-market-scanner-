"""
CRYPTO FUTURES MARKET SCANNER
Decision-support tool for expansion and reversion strategies
NO AUTO-TRADING - Human judgment required for all entries
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

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

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
    '3m': 6,  # minutes
    '5m': 10  # minutes
}

# ════════════════════════════════════════════════════════════════════════════
# DATA FETCHING
# ════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def get_futures_symbols(exchange_name: str) -> List[str]:
    """Fetch all USDT perpetual futures symbols"""
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
    except Exception as e:
        st.error(f"Error fetching symbols from {exchange_name}: {e}")
        return []

def fetch_ohlcv(exchange_name: str, symbol: str, timeframe: str, limit: int = 200) -> Optional[pd.DataFrame]:
    """Fetch OHLCV data for a symbol"""
    try:
        exchange = EXCHANGES[exchange_name]
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df
    except Exception as e:
        return None

# ════════════════════════════════════════════════════════════════════════════
# INDICATOR CALCULATIONS
# ════════════════════════════════════════════════════════════════════════════

def calculate_sma(df: pd.DataFrame, period: int) -> pd.Series:
    """Calculate Simple Moving Average"""
    return df['close'].rolling(window=period).mean()

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all required indicators"""
    df = df.copy()
    df['sma_20'] = calculate_sma(df, 20)
    df['sma_100'] = calculate_sma(df, 100)
    return df

# ════════════════════════════════════════════════════════════════════════════
# CANDLE ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

def analyze_candle(row: pd.Series, df: pd.DataFrame, idx: int) -> Dict:
    """
    Analyze candle characteristics WITHOUT making binary decisions
    Reports measurements for human judgment
    """
    body = abs(row['close'] - row['open'])
    total_range = row['high'] - row['low']
    upper_wick = row['high'] - max(row['close'], row['open'])
    lower_wick = min(row['close'], row['open']) - row['low']
    
    # Calculate average body size for context
    lookback = df.iloc[max(0, idx-20):idx]
    avg_body = abs(lookback['close'] - lookback['open']).mean() if len(lookback) > 0 else body
    
    # Body to total range ratio
    body_ratio = (body / total_range * 100) if total_range > 0 else 0
    
    # Wick analysis
    upper_wick_ratio = (upper_wick / total_range * 100) if total_range > 0 else 0
    lower_wick_ratio = (lower_wick / total_range * 100) if total_range > 0 else 0
    
    # Direction
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
    """
    Label candle patterns for human review
    NO HARD THRESHOLDS - descriptive only
    """
    labels = []
    
    # Elephant bar candidate (large body relative to recent candles)
    if candle_data['body_vs_avg'] > 1.5:
        labels.append(f"Elephant-like (body {candle_data['body_vs_avg']:.1f}x avg)")
    
    # Tail bar candidate (strong rejection wick)
    if candle_data['is_bullish'] and candle_data['lower_wick_ratio'] > 40:
        labels.append(f"Bullish Tail (lower wick {candle_data['lower_wick_ratio']:.0f}%)")
    elif not candle_data['is_bullish'] and candle_data['upper_wick_ratio'] > 40:
        labels.append(f"Bearish Tail (upper wick {candle_data['upper_wick_ratio']:.0f}%)")
    
    # Inverted tail (for reversions)
    if candle_data['is_bullish'] and candle_data['upper_wick_ratio'] > 40:
        labels.append(f"Inverted Tail Bull (upper wick {candle_data['upper_wick_ratio']:.0f}%)")
    elif not candle_data['is_bullish'] and candle_data['lower_wick_ratio'] > 40:
        labels.append(f"Inverted Tail Bear (lower wick {candle_data['lower_wick_ratio']:.0f}%)")
    
    return " | ".join(labels) if labels else "Standard candle"

# ════════════════════════════════════════════════════════════════════════════
# STRATEGY LOGIC - EXPANSION
# ════════════════════════════════════════════════════════════════════════════

def detect_sqz(df: pd.DataFrame, idx: int) -> Dict:
    """
    Report SMA proximity for SQZ evaluation
    NO binary decision - human judges if "visually very close"
    """
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
    """
    Detect SMA crossover (20 crossing 100)
    Returns direction or None
    """
    if idx < 1:
        return None
    
    curr = df.iloc[idx]
    prev = df.iloc[idx - 1]
    
    # Bullish cross: 20 crosses above 100
    if prev['sma_20'] <= prev['sma_100'] and curr['sma_20'] > curr['sma_100']:
        return 'bullish'
    
    # Bearish cross: 20 crosses below 100
    if prev['sma_20'] >= prev['sma_100'] and curr['sma_20'] < curr['sma_100']:
        return 'bearish'
    
    return None

def check_expansion(df: pd.DataFrame, idx: int, direction: str) -> Dict:
    """
    Check if price is moving away from 100 SMA
    Reports distance and direction - NO minimum threshold
    """
    row = df.iloc[idx]
    price = row['close']
    sma_100 = row['sma_100']
    
    distance_abs = abs(price - sma_100)
    distance_pct = (distance_abs / price * 100) if price > 0 else 0
    
    # Check if movement aligns with direction
    is_above = price > sma_100
    moving_away = (direction == 'long' and is_above) or (direction == 'short' and not is_above)
    
    # Get recent candle sequence
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

# ════════════════════════════════════════════════════════════════════════════
# STRATEGY LOGIC - REVERSION
# ════════════════════════════════════════════════════════════════════════════

def detect_reversion_setup(df: pd.DataFrame, idx: int) -> Optional[Dict]:
    """
    Detect reversion conditions
    Reports measurements - human judges if "widely separated"
    """
    if idx < 50:
        return None
    
    row = df.iloc[idx]
    price = row['close']
    sma_20 = row['sma_20']
    sma_100 = row['sma_100']
    
    # Calculate SMA separation
    sma_distance_abs = abs(sma_20 - sma_100)
    sma_distance_pct = (sma_distance_abs / price * 100) if price > 0 else 0
    
    # Count how long SMAs have been separated
    lookback = df.iloc[max(0, idx-50):idx+1]
    separation_duration = 0
    for i in range(len(lookback)-1, -1, -1):
        r = lookback.iloc[i]
        sep = abs(r['sma_20'] - r['sma_100']) / r['close'] * 100
        if sep > 0.5:  # Basic separation threshold for counting
            separation_duration += 1
        else:
            break
    
    # Check for choppiness (frequent crosses)
    crosses_50 = 0
    for i in range(len(lookback)-1):
        curr = lookback.iloc[i+1]
        prev = lookback.iloc[i]
        if (prev['sma_20'] > prev['sma_100'] and curr['sma_20'] < curr['sma_100']) or \
           (prev['sma_20'] < prev['sma_100'] and curr['sma_20'] > curr['sma_100']):
            crosses_50 += 1
    
    # Determine prior expansion direction
    prior_expansion = 'bullish' if sma_20 > sma_100 else 'bearish'
    
    # Check for reversion trigger
    reversion_signal = None
    
    # After bullish expansion → price falls below 20 SMA
    if prior_expansion == 'bullish' and price < sma_20:
        reversion_signal = 'short'
    
    # After bearish expansion → price rises above 20 SMA
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

# ════════════════════════════════════════════════════════════════════════════
# CONTEXT ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

def analyze_15m_context(df_15m: pd.DataFrame, direction: str) -> Dict:
    """
    Report 15m context for human judgment
    NO automatic alignment decision
    """
    if df_15m is None or len(df_15m) < 100:
        return {'status': '15m data unavailable'}
    
    latest = df_15m.iloc[-1]
    price = latest['close']
    sma_20 = latest['sma_20']
    sma_100 = latest['sma_100']
    
    # Price position
    above_20 = price > sma_20
    above_100 = price > sma_100
    
    # Recent candle direction
    lookback = df_15m.iloc[-5:]
    bullish_candles = sum(lookback['close'] > lookback['open'])
    
    # Basic structure
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
    """
    Report nearby swing levels
    NO automatic blocking - human decides significance
    """
    lookback = df.iloc[max(0, idx-50):idx]
    current_price = df.iloc[idx]['close']
    
    # Find recent swing highs and lows
    swing_highs = lookback['high'].nlargest(3)
    swing_lows = lookback['low'].nsmallest(3)
    
    if direction == 'long':
        # Check for resistance above
        nearest_high = swing_highs.min()
        distance_pct = ((nearest_high - current_price) / current_price * 100)
        proximity = "nearby" if distance_pct < 2 else "distant"
        return {
            'level': nearest_high,
            'distance_pct': distance_pct,
            'status': f"Resistance {proximity} ({distance_pct:.2f}% above) — visual confirmation required"
        }
    else:
        # Check for support below
        nearest_low = swing_lows.max()
        distance_pct = ((current_price - nearest_low) / current_price * 100)
        proximity = "nearby" if distance_pct < 2 else "distant"
        return {
            'level': nearest_low,
            'distance_pct': distance_pct,
            'status': f"Support {proximity} ({distance_pct:.2f}% below) — visual confirmation required"
        }

def detect_liquidity_hole(df: pd.DataFrame, idx: int, direction: str) -> Dict:
    """
    Report price zone characteristics
    Human judges if liquidity hole exists
    """
    lookback = df.iloc[max(0, idx-50):idx]
    current_price = df.iloc[idx]['close']
    
    if direction == 'long':
        # Look for space above
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
        # Look for space below
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

# ════════════════════════════════════════════════════════════════════════════
# CONVICTION SCORING
# ════════════════════════════════════════════════════════════════════════════

def calculate_conviction(signal_data: Dict) -> Tuple[str, str]:
    """
    Assign conviction tier based on signal quality
    Returns (tier, reason)
    """
    issues = []
    strengths = []
    
    # Check candle confirmation
    candle_label = signal_data.get('candle_type', '')
    if 'Elephant' in candle_label or 'Tail' in candle_label:
        strengths.append("Strong confirmation candle")
    else:
        issues.append("Weak confirmation candle")
    
    # Check firewall
    firewall = signal_data.get('firewall_status', '')
    if 'nearby' in firewall.lower():
        issues.append("Firewall nearby")
    else:
        strengths.append("Clear path")
    
    # Check liquidity
    liquidity = signal_data.get('liquidity_status', '')
    if 'low density' in liquidity.lower():
        strengths.append("Liquidity hole present")
    
    # Check choppiness (for reversions)
    if signal_data['strategy'] == 'Reversion':
        chop_status = signal_data.get('choppiness', '')
        if 'crosses' in chop_status and int(chop_status.split('crosses')[0].split()[-1]) > 5:
            issues.append("Market choppy")
    
    # Assign tier
    if len(issues) == 0 and len(strengths) >= 2:
        return 'A+', f"Clean setup: {', '.join(strengths)}"
    elif len(issues) <= 1 and len(strengths) >= 1:
        return 'A', f"Strong setup with minor issues: {', '.join(issues) if issues else 'good structure'}"
    elif len(issues) <= 2:
        return 'B', f"Tradeable with caution: {', '.join(issues)}"
    else:
        return 'C', f"Avoid: {', '.join(issues)}"

# ════════════════════════════════════════════════════════════════════════════
# MAIN SCANNER
# ════════════════════════════════════════════════════════════════════════════

def scan_symbol(exchange_name: str, symbol: str, timeframe: str, df_15m: pd.DataFrame) -> List[Dict]:
    """
    Scan a single symbol for all strategies
    Returns list of signals
    """
    signals = []
    
    # Fetch data
    df = fetch_ohlcv(exchange_name, symbol, timeframe, limit=200)
    if df is None or len(df) < 100:
        return signals
    
    # Calculate indicators
    df = calculate_indicators(df)
    
    # Analyze most recent candle
    idx = len(df) - 1
    row = df.iloc[idx]
    
    # Candle analysis
    candle_data = analyze_candle(row, df, idx)
    candle_label = label_candle_type(candle_data)
    
    # ═══════════════════════════════════════════════════════════════════════
    # EXPANSION STRATEGY - SQZ TRIGGER
    # ═══════════════════════════════════════════════════════════════════════
    
    sqz_data = detect_sqz(df, idx)
    
    # Check for expansion from SQZ (both directions)
    for direction in ['long', 'short']:
        expansion_check = check_expansion(df, idx, direction)
        
        if expansion_check['moving_away']:
            # Get 15m context
            context_15m = analyze_15m_context(df_15m, direction)
            
            # Get firewall and liquidity
            firewall = detect_firewall(df, idx, direction)
            liquidity = detect_liquidity_hole(df, idx, direction)
            
            # Build signal
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
            
            # Calculate conviction
            tier, reason = calculate_conviction(signal)
            signal['conviction'] = tier
            signal['reason'] = reason
            
            signals.append(signal)
    
    # ═══════════════════════════════════════════════════════════════════════
    # EXPANSION STRATEGY - CROSSOVER TRIGGER
    # ═══════════════════════════════════════════════════════════════════════
    
    crossover_dir = detect_crossover(df, idx)
    
    if crossover_dir:
        direction = 'long' if crossover_dir == 'bullish' else 'short'
        expansion_check = check_expansion(df, idx, direction)
        
        if expansion_check['moving_away']:
            # Get 15m context
            context_15m = analyze_15m_context(df_15m, direction)
            
            # Get firewall and liquidity
            firewall = detect_firewall(df, idx, direction)
            liquidity = detect_liquidity_hole(df, idx, direction)
            
            # Build signal
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
            
            # Calculate conviction
            tier, reason = calculate_conviction(signal)
            signal['conviction'] = tier
            signal['reason'] = reason
            
            signals.append(signal)
    
    # ═══════════════════════════════════════════════════════════════════════
    # REVERSION STRATEGY
    # ═══════════════════════════════════════════════════════════════════════
    
    reversion = detect_reversion_setup(df, idx)
    
    if reversion:
        direction = reversion['direction']
        
        # Get 15m context (should show weakening or reversal)
        context_15m = analyze_15m_context(df_15m, direction)
        
        # Get firewall and liquidity
        firewall = detect_firewall(df, idx, direction)
        liquidity = detect_liquidity_hole(df, idx, direction)
        
        # Build signal
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
        
        # Calculate conviction
        tier, reason = calculate_conviction(signal)
        signal['conviction'] = tier
        signal['reason'] = reason
        
        signals.append(signal)
    
    return signals

# ════════════════════════════════════════════════════════════════════════════
# STREAMLIT UI
# ════════════════════════════════════════════════════════════════════════════

def format_signal_age(signal: Dict) -> Tuple[int, bool]:
    """Calculate signal age in minutes and staleness"""
    now = datetime.now()
    detected = signal['detected_at']
    age_minutes = int((now - detected).total_seconds() / 60)
    
    stale_threshold = STALE_THRESHOLD[signal['entry_timeframe']]
    is_stale = age_minutes >= stale_threshold
    
    return age_minutes, is_stale

def render_signals_table(signals: List[Dict]):
    """Render signals in mobile-friendly format"""
    if not signals:
        st.info("No signals detected. Scanner running...")
        return
    
    for signal in signals:
        age_minutes, is_stale = format_signal_age(signal)
        
        # Style based on staleness
        if is_stale:
            st.markdown(f"""
            <div style="background-color: #2a2a2a; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #555; opacity: 0.6;">
                <p style="color: #888; font-style: italic; margin: 0;">
                    <strong>⚠️ STALE SIGNAL ({age_minutes} min ago)</strong>
                </p>
                <p style="color: #888; margin: 5px 0;">
                    {signal['symbol']} | {signal['exchange'].upper()} | {signal['direction']} | {signal['strategy']}
                </p>
                <p style="color: #888; font-size: 0.9em; margin: 5px 0;">
                    Conviction: {signal['conviction']} | {signal['trigger_type']} | {signal['entry_timeframe']}
                </p>
                <p style="color: #888; font-size: 0.85em; margin: 5px 0;">
                    {signal['reason']}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Fresh signal
            color = "#00ff00" if signal['direction'] == 'LONG' else "#ff4444"
            
            st.markdown(f"""
            <div style="background-color: #1a1a1a; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid {color};">
                <p style="color: {color}; font-weight: bold; font-size: 1.2em; margin: 0;">
                    {signal['symbol']} | {signal['direction']}
                </p>
                <p style="color: #ddd; margin: 5px 0;">
                    {signal['exchange'].upper()} | {signal['strategy']} | Conviction: <strong>{signal['conviction']}</strong>
                </p>
                <p style="color: #aaa; font-size: 0.9em; margin: 5px 0;">
                    {signal['trigger_type']} | {signal['entry_timeframe']} | {age_minutes} min ago
                </p>
                <p style="color: #fff; background-color: #333; padding: 8px; border-radius: 4px; margin: 10px 0;">
                    <strong>Reason:</strong> {signal['reason']}
                </p>
                <details style="margin-top: 10px;">
                    <summary style="color: #888; cursor: pointer;">Technical Details</summary>
                    <p style="color: #888; font-size: 0.85em; margin: 5px 0;">Candle: {signal['candle_type']}</p>
                    <p style="color: #888; font-size: 0.85em; margin: 5px 0;">{signal.get('sqz_status', 'N/A')}</p>
                    <p style="color: #888; font-size: 0.85em; margin: 5px 0;">{signal['expansion_status']}</p>
                    <p style="color: #888; font-size: 0.85em; margin: 5px 0;">15m: {signal['context_15m']}</p>
                    <p style="color: #888; font-size: 0.85em; margin: 5px 0;">{signal['firewall_status']}</p>
                    <p style="color: #888; font-size: 0.85em; margin: 5px 0;">{signal['liquidity_status']}</p>
                    {f"<p style='color: #888; font-size: 0.85em; margin: 5px 0;'>Choppiness: {signal['choppiness']}</p>" if signal['choppiness'] != 'N/A' else ''}
                </details>
            </div>
            """, unsafe_allow_html=True)

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Crypto Futures Scanner",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.title("📊 Crypto Futures Market Scanner")
    st.markdown("**Decision-Support Tool** | Human Judgment Required")
    
    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Exchange selection
        selected_exchanges = st.multiselect(
            "Exchanges",
            list(EXCHANGES.keys()),
            default=['binance']
        )
        
        # Timeframe selection
        selected_timeframes = st.multiselect(
            "Entry Timeframes",
            ['3m', '5m'],
            default=['5m']
        )
        
        # Symbol limit
        max_symbols = st.slider("Max symbols per exchange", 5, 50, 20)
        
        # Refresh interval
        refresh_interval = st.slider("Refresh interval (seconds)", 30, 300, 60)
        
        st.markdown("---")
        st.markdown("**Strategies Active:**")
        st.markdown("✅ Expansion (SQZ)")
        st.markdown("✅ Expansion (Crossover)")
        st.markdown("✅ Reversion")
    
    # Main scanning loop
    if 'signals' not in st.session_state:
        st.session_state.signals = []
    
    # Status placeholder
    status_placeholder = st.empty()
    signals_placeholder = st.empty()
    
    # Auto-refresh
    if st.button("🔄 Manual Refresh") or True:
        all_signals = []
        
        for exchange_name in selected_exchanges:
            status_placeholder.info(f"Fetching symbols from {exchange_name}...")
            
            symbols = get_futures_symbols(exchange_name)[:max_symbols]
            
            for symbol in symbols:
                for timeframe in selected_timeframes:
                    status_placeholder.info(f"Scanning {symbol} on {timeframe}...")
                    
                    # Fetch 15m context
                    df_15m = fetch_ohlcv(exchange_name, symbol, '15m', limit=200)
                    if df_15m is not None:
                        df_15m = calculate_indicators(df_15m)
                    
                    # Scan symbol
                    signals = scan_symbol(exchange_name, symbol, timeframe, df_15m)
                    all_signals.extend(signals)
        
        # Update session state
        st.session_state.signals = all_signals
        
        status_placeholder.success(f"✅ Scan complete. {len(all_signals)} signals detected.")
    
    # Render signals
    with signals_placeholder.container():
        if st.session_state.signals:
            # Sort by conviction and freshness
            sorted_signals = sorted(
                st.session_state.signals,
                key=lambda x: (
                    {'A+': 0, 'A': 1, 'B': 2, 'C': 3}[x['conviction']],
                    format_signal_age(x)[0]
                )
            )
            render_signals_table(sorted_signals)
        else:
            st.info("No signals yet. Click 'Manual Refresh' to start scanning.")
    
    # Auto-refresh
    time.sleep(refresh_interval)
    st.rerun()

if __name__ == "__main__":
    main()
