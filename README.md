# Crypto Futures Scanner

A decision-support tool for crypto futures trading. Detects expansion and reversion setups on 3m and 5m timeframes.

**⚠️ THIS IS NOT AN AUTO-TRADER**  
All signals require your visual confirmation before trading.

---

## Quick Start (3 Steps)

### 1️⃣ Install Python
- Download from https://www.python.org/downloads/
- Install Python 3.8 or higher
- During installation, check "Add Python to PATH"

### 2️⃣ Install Required Packages
Open terminal (Mac/Linux) or Command Prompt (Windows) and run:
```bash
pip install -r requirements.txt
```

### 3️⃣ Run the Scanner
In the same terminal, run:
```bash
streamlit run crypto_scanner.py
```

The scanner will open in your web browser automatically.

---

## How to Use

### First Time Setup
When the scanner opens in your browser:

1. **Click the arrow (>) on the left** to open settings
2. **Select Exchange**: Start with "binance" 
3. **Select Timeframe**: Start with "5m"
4. **Max Symbols**: Set to 10-20
5. **Refresh Interval**: Set to 60 seconds
6. **Click "Manual Refresh"**

### Reading Signals

Each signal shows:
- **Symbol**: e.g., BTC/USDT
- **Direction**: LONG (green) or SHORT (red)  
- **Conviction**: A+, A, B, or C
- **Reason**: Why the scanner flagged this setup

**Signal Quality:**
- **A+** = Best quality, all conditions met
- **A** = Strong setup, minor issue
- **B** = Valid but needs extra caution
- **C** = Choppy/unclear - DO NOT TRADE

**Signal Freshness:**
- **Normal color** = Fresh (within 2 candles)
- **Grey/italic** = STALE (too old to enter)

### Before You Trade

**NEVER take a signal blindly!**

For EVERY signal:
1. Open your trading platform
2. Find the symbol and timeframe
3. Look at the chart yourself
4. Verify what the scanner says
5. Only trade if YOU see the setup too

---

## What the Scanner Detects

### Expansion Strategy (2 triggers)
1. **SQZ**: When 20 SMA and 100 SMA are very close together, then price expands away
2. **Crossover**: When 20 SMA crosses 100 SMA and price expands

### Reversion Strategy  
After a strong expansion, when price pulls back to the 20 SMA, scanner looks for reversal back to 100 SMA

### What Gets Checked
For each signal, scanner reports:
- Candle type (Elephant bar, Tail bar, etc.)
- Distance from moving averages
- 15-minute timeframe context
- Nearby support/resistance (firewall)
- Open space in the direction (liquidity hole)
- Market choppiness

**You make the final decision on all of these!**

---

## Settings You Can Change

In the sidebar (left panel):

**Exchanges**: 
- Binance (recommended for beginners)
- Gate.io
- MEXC

**Timeframes**:
- 3m (faster, more signals)
- 5m (slower, cleaner signals)

**Max Symbols**:
- Lower number = faster scanning
- Higher number = more coverage

**Refresh Interval**:
- How often scanner updates (30-300 seconds)

---

## Common Questions

**Q: No signals showing?**
- Market might be ranging (no clear setups)
- Try more symbols or different timeframe
- Good setups don't appear constantly - be patient

**Q: Should I take every A+ signal?**
- NO! Always check your charts first
- Scanner assists, YOU decide
- Never trade mechanically

**Q: What does "STALE" mean?**
- Signal is older than 2 candles
- Entry timing may be too late
- Use for reference, not entry

**Q: Can I auto-trade these signals?**
- ABSOLUTELY NOT
- This tool requires human judgment
- Not designed for automation

**Q: Scanner shows different conviction than I see?**
- Trust your eyes over the scanner
- Scanner is an assistant, not a boss
- If you don't see the setup clearly, skip it

---

## Important Warnings

### ⚠️ Trading Risks
- Futures trading is extremely risky
- You can lose more than your investment
- High leverage = high risk
- Use proper risk management
- Never risk money you can't afford to lose

### ⚠️ Scanner Limitations
- Not 100% accurate
- Requires your judgment
- Can give false signals
- Markets change constantly
- No guarantee of profits

### ⚠️ Your Responsibilities
- Visual confirmation on charts
- Risk management (stop losses, position sizing)
- Trade management (exits, targets)
- Emotional control
- Continuous learning

---

## Troubleshooting

**"Error fetching symbols"**
- Check your internet connection
- Exchange might be down temporarily
- Try a different exchange

**"ModuleNotFoundError"**
```bash
pip install streamlit ccxt pandas numpy
```

**Scanner is slow**
- Reduce max symbols
- Increase refresh interval
- Scan one timeframe at a time

**Can't install packages**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## File Structure

Your scanner folder should have:
```
my-scanner/
├── crypto_scanner.py    (main scanner code)
├── requirements.txt     (package list)
└── README.md           (this file)
```

---

## Support

This scanner implements your exact trading edge with no modifications.

For technical issues:
1. Read this README completely
2. Check your Python installation
3. Verify all packages installed correctly
4. Make sure you have internet connection

---

## Remember

**Scanner REPORTS → You DECIDE → You TRADE**

- Scanner finds potential setups
- You verify on your charts  
- You manage the trade
- You are responsible for results

**Never trade blindly. Always think for yourself.**

Good luck and trade safely! 📊
