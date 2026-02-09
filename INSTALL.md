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
4. Follow steps

### Verify
```bash
python --version
```

Should show: `Python 3.12.x`

---

## Step 2: Get Scanner Files

Download ZIP from GitHub  
Extract to Desktop

---

## Step 3: Open Terminal

**Windows:** Press `Win + R`, type `cmd`  
**Mac:** Press `Cmd + Space`, type `terminal`

---

## Step 4: Navigate to Folder
```bash
cd Desktop/crypto-scanner
```

Check files:
```bash
dir
```
(Windows) or
```bash
ls
```
(Mac)

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

Browser opens automatically!

If not, manually go to: `http://localhost:8501`

---

## First-Time Setup

When scanner opens:

1. **Check BTC Market Regime box at top**
   - Shows current market conditions
   - Guides your trading decisions

2. **Click arrow (>) for settings**
   - Exchanges: Select "gateio" and "mexc"
   - Timeframe: Select "5m"
   - Max symbols: Set to 10-20
   - Refresh: Set to 60 seconds

3. **Click "Refresh Now"**

4. **Wait for signals** (1-2 minutes)

---

## Mobile Access

Scanner shows Network URL: `http://192.168.x.x:8501`

On phone (same WiFi):
1. Type that URL in browser
2. Scanner loads on phone
3. Add to home screen for app-like experience

---

## Common Problems

**"Python not found"**  
→ Reinstall Python, check "Add to PATH"

**"pip not found"**  
→ Try: `python -m pip install -r requirements.txt`

**Browser doesn't open**  
→ Go to: `http://localhost:8501`

**BTC regime shows "Data unavailable"**  
→ Wait for data to load or check internet connection

---

## Running Again

You only install once!

**Next time:**
1. Open terminal
2. `cd Desktop/crypto-scanner`
3. `streamlit run crypto_scanner.py`

Done!

---

Good luck! 📊
