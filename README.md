# Crypto Futures Scanner

Mobile-friendly decision-support tool for crypto futures trading.

## ⚠️ IMPORTANT

**This is NOT an auto-trader!**  
All signals require YOUR visual confirmation before trading.

## Features

### BTC Market Regime Analysis
- Displays BTC market state on 15m, 1h, and 4h timeframes
- Provides global bias recommendation
- Helps contextualize all altcoin signals

### Trading Strategies (Priority Order)
1. **Expansion** (Highest Priority)
   - SQZ: SMAs close together → expansion
   - Crossover: 20 SMA crosses 100 SMA → expansion

2. **Trend Continuation (TC20)** (New!)
   - Captures FIRST pullback to 20 SMA after expansion
   - Never miss the trend continuation entry
   - Shows RSI, expansion origin, and time since expansion

3. **Reversion** (Lowest Priority)
   - After strong expansion, price pulls back to 20 SMA

**Important:** Scanner NEVER outputs conflicting signals for same symbol.

---

## Quick Start

### 1. Install Python
Download from https://www.python.org/downloads/  
Install Python 3.8 or higher

### 2. Install Packages
```bash
pip install -r requirements.txt
```

### 3. Run Scanner
```bash
streamlit run crypto_scanner.py
```

Scanner opens in your browser (works on mobile!)

---

## How to Use

### First Time
1. Click arrow (>) to open settings
2. Select "gateio" and "mexc" exchanges
3. Select "5m" timeframe
4. Set max symbols to 10-20
5. Click "Refresh Now"

### Understanding Signals

**BTC Market Regime (Top of Screen):**
- Shows BTC trend on 15m, 1h, 4h
- Provides trading bias recommendation
- Check this BEFORE taking any signal

**Signal Types:**
- **Expansion**: Fresh impulse move starting
- **Trend Continuation (TC20)**: First pullback in active trend
- **Reversion**: End of trend, reverting to mean

**Conviction Levels:**
- **A+** = Best quality, all conditions met
- **A** = Strong setup
- **B** = Tradeable with caution
- **C** = Avoid (choppy)

**Freshness:**
- Normal color = Fresh (within 2 candles)
- Grey/italic = STALE (too old to enter)

### Before Trading

**ALWAYS verify on your charts:**
1. Open your trading platform
2. Check BTC regime aligns with signal
3. Visually confirm the setup
4. Check RSI and context (for TC20 signals)
5. Only trade if YOU see it too

**Never trade blindly!**

---

## What Gets Reported

**All Signals Show:**
- Symbol and exchange
- Direction (LONG/SHORT)
- Strategy type
- Conviction tier with reason
- Entry timeframe
- Signal age

**Technical Details (Expandable):**
- Candle patterns
- SMA distances
- 15m context
- Firewall status
- Liquidity holes
- RSI (for TC20)
- Expansion origin (for TC20)

---

## Mobile Usage

Fully optimized for mobile:
- Touch-friendly interface
- BTC regime box at top
- Compact signal cards
- Expandable details

**Mobile Tips:**
- Use landscape mode
- Check BTC regime first
- Tap "Technical Details" for full info
- Keep screen timeout disabled

---

## Settings

**Exchanges:**
- Gate.io (recommended)
- MEXC (recommended)
- Binance (may be geo-blocked)

**Timeframes:**
- 3m = More signals, faster
- 5m = Cleaner signals, better quality

**Max Symbols:**
- 10-20 recommended
- Higher = more coverage but slower

---

## Trading Cycle

**How Signals Progress:**

1. **Expansion** → Price breaks away from consolidation
2. **Trend Continuation (TC20)** → First pullback to 20 SMA
3. **More continuation moves** (not signaled)
4. **Reversion** → Trend exhaustion, return to 100 SMA

Scanner captures steps 1, 2, and 4.

---

## Warnings

**Trading Risks:**
- Futures = extremely high risk
- Can lose more than deposit
- Use proper risk management
- Never risk rent money

**Scanner Limitations:**
- Not 100% accurate
- Requires your judgment
- BTC regime is guidance, not guarantee
- Signals can be wrong

**Your Responsibility:**
- Visual confirmation
- Risk management
- Trade decisions
- Position sizing
- Stop losses

---

**BTC regime guides → Scanner finds → You verify → You trade**

Never trade blindly. Always think for yourself.

Good luck! 📊
