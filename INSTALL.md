# Installation Guide

Step-by-step for traders who don't code.

---

## Step 1: Install Python

### Windows
1. Go to https://www.python.org/downloads/
2. Click "Download Python"
3. Run installer
4. ✅ CHECK "Add Python to PATH"
5. Click "Install Now"

### Mac
1. Go to https://www.python.org/downloads/
2. Click "Download Python"
3. Open downloaded file
4. Follow installation steps

### Verify
Open terminal and type:
```bash
python --version
```

Should show: `Python 3.12.x`

---

## Step 2: Get Scanner Files

Download ZIP from GitHub  
Extract to Desktop

Files you should have:
- crypto_scanner.py
- requirements.txt
- README.md
- INSTALL.md

---

## Step 3: Open Terminal

**Windows:** Press `Win + R`, type `cmd`, press Enter  
**Mac:** Press `Cmd + Space`, type `terminal`, press Enter

---

## Step 4: Navigate to Scanner Folder
```bash
cd Desktop/crypto-scanner
```

Verify you're in the right place:
```bash
dir
```
(Windows) or
```bash
ls
```
(Mac)

Should list your files.

---

## Step 5: Install Packages
```bash
pip install -r requirements.txt
```

Wait for installation to complete.

---

## Step 6: Run Scanner
```bash
streamlit run crypto_scanner.py
```

Browser opens automatically with the scanner!

If browser doesn't open, go to: `http://localhost:8501`

---

## First-Time Setup

When scanner opens:

### 1. Check BTC Market Regime (Top of Page)
Shows current market conditions across timeframes

### 2. Open Settings (Click Arrow >)
- Exchanges: Select "gateio" and "mexc"
- Timeframes: Select "5m"
- Max symbols: Set to 20
- Refresh: Set to 60 seconds

### 3. Click "Refresh Now"

### 4. Wait for Signals (1-2 minutes)

Scanner will show:
- Expansion signals (impulse moves)
- Trend Continuation signals (TC20 pullbacks)
- Reversion signals (trend exhaustion)

---

## Understanding Your First Signals

**Expansion Signal Example:**
```
BTC/USDT | LONG
GATEIO • Expansion • SQZ
Conviction A+: Clean setup
5m • 1 min ago
```
This means: Fresh breakout happening NOW

**Trend Continuation Signal Example:**
```
ETH/USDT | SHORT
MEXC • Trend Continuation • TC20
First pullback to 20 SMA, 15.2 min after SQZ expansion
Conviction A: Strong setup
5m • 2 min ago
```
This means: Trend started 15 min ago, now pullback entry

---

## Mobile Access

Scanner shows Network URL: `http://192.168.x.x:8501`

**On Your Phone (Same WiFi):**
1. Type that URL in mobile browser
2. Scanner loads on phone
3. Add to home screen for app-like experience

**Perfect for:**
- Monitoring while away from computer
- Quick signal checks
- Trading on the go

---

## Common Problems

**"Python not found"**  
→ Reinstall Python, check "Add to PATH"

**"pip not found"**  
→ Try: `python -m pip install -r requirements.txt`

**Browser doesn't open**  
→ Manually go to: `http://localhost:8501`

**BTC regime shows "Data unavailable"**  
→ Wait 30 seconds, data is loading

**No signals appearing**  
→ Normal! Good setups are rare. Be patient.

---

## Running Scanner Again

You only install once!

**Every time after first install:**
1. Open terminal
2. Navigate: `cd Desktop/crypto-scanner`
3. Run: `streamlit run crypto_scanner.py`

Done!

---

## Tips for Success

### Day 1-3: Learning Mode
- Run scanner
- Watch signals appear
- Check each on your charts
- DON'T trade yet
- Learn the patterns

### Day 4-7: Paper Trading
- Take signals on paper
- Track results
- See which work best
- Build confidence

### Week 2+: Live Trading
- Start with smallest size
- Only A+ and A signals
- Always visual confirmation
- Use stop losses
- Increase size slowly

---

Good luck! 📊
