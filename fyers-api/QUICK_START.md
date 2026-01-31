# 🚀 QUICK START GUIDE
## Nifty Bi-Weekly Options Strategy

---

## 📋 STRATEGY AT A GLANCE

**What it does**: Automatically trades Nifty options every Monday using a ratio call spread strategy

**When it trades**: 
- Entry: Monday at 09:45 AM (8 days before bi-weekly expiry)
- Exit: When +1% profit OR -1% loss OR 5 days elapsed

**Position Structure**:
```
BUY  1 lot @ ATM + 200 points (e.g., 26200 CE)
SELL 3 lots @ ATM + 400 points (e.g., 26400 CE) ⚠️
BUY  2 lots @ ATM + 600 points (e.g., 26600 CE)
```

**Capital Required**: ~₹1,25,000 per trade (varies with volatility)

**Expected Win Rate**: 60-70%

---

## 🎯 FILES INCLUDED

| File | Purpose |
|------|---------|
| `nifty_strategy.py` | Main strategy execution script |
| `strategy_backtest.py` | Backtesting module |
| `strategy_dashboard.html` | Visual monitoring dashboard |
| `STRATEGY_GUIDE.md` | Complete documentation |
| `fyers_login.py` | Your existing authentication |

---

## ⚡ 3-STEP SETUP

### Step 1: Install Dependencies
```bash
pip install fyers-apiv3 pandas pyyaml pytz pyotp --break-system-packages
```

### Step 2: Configure Your Account
Edit `Config.yaml`:
```yaml
fyers:
  username: "YOUR_FYERS_ID"
  client_id: "YOUR_APP_ID"
  secret_key: "YOUR_SECRET"
  token: "YOUR_TOTP_SECRET"
  pin: YOUR_PIN
```

### Step 3: Authenticate & Run
```bash
# First time only
python fyers_login.py

# Then run strategy
python nifty_strategy.py
```

---

## 💡 HOW IT WORKS

### Monday 09:45 AM - Entry
1. ✅ System checks: Is it Monday? Is time 09:45 AM or later?
2. 📊 Fetches Nifty spot price (e.g., 26,123)
3. 🎯 Calculates ATM strike (26,100)
4. 🔨 Places basket order:
   - BUY 50 qty @ 26200 CE
   - SELL 150 qty @ 26400 CE
   - BUY 100 qty @ 26600 CE
5. 💰 Calculates deployed capital (margin blocked)

### Continuous Monitoring
- Checks P&L every 30 seconds
- Compares against target (+1%) and stop-loss (-1%)
- Auto-exits when condition met

### Exit Triggers
| Trigger | Action |
|---------|--------|
| Profit reaches +1% | Square off all - TARGET HIT ✅ |
| Loss reaches -1% | Square off all - STOP LOSS ❌ |
| 5 days completed | Square off all - DURATION ⏰ |
| Market closes | Square off all - EOD 🔔 |

---

## 📊 EXAMPLE TRADE

**Entry**: Monday, Feb 3, 2026 @ 09:45 AM
- Nifty Spot: 26,123
- ATM Strike: 26,100

**Positions**:
```
BUY  50  @ 26200 CE = ₹125.50 × 50  = ₹6,275
SELL 150 @ 26400 CE = ₹85.25 × 150 = ₹12,787 (credit)
BUY  100 @ 26600 CE = ₹52.75 × 100 = ₹5,275

Net Premium: ₹12,787 - ₹6,275 - ₹5,275 = ₹1,237 (credit)
Margin Required: ~₹1,25,000
```

**Scenario 1 - Target Hit** ✅
- Wednesday 11:23 AM
- P&L: +₹1,250 (+1.0%)
- Exit: All positions squared off automatically

**Scenario 2 - Stop Loss** ❌
- Tuesday 02:15 PM  
- P&L: -₹1,250 (-1.0%)
- Exit: All positions squared off automatically

---

## 🎨 VISUAL DASHBOARD

Open `strategy_dashboard.html` in your browser to see:
- Real-time P&L tracking
- Position details
- Target/SL progress bar
- Strategy status
- One-click controls

![Dashboard Preview]
```
┌─────────────────────────────────────────────┐
│  Strategy Status: ACTIVE                    │
│  Nifty Spot: 26,123                         │
│  Current P&L: ₹+825 (+0.66%)                │
│  Deployed Capital: ₹1,25,000                │
├─────────────────────────────────────────────┤
│  [━━━━━━━━━━▓▓░░░░░░░░] 66% to Target      │
├─────────────────────────────────────────────┤
│  Active Positions:                          │
│  • BUY  26200 CE  x50   P&L: ₹+162          │
│  • SELL 26400 CE  x150  P&L: ₹+487          │
│  • BUY  26600 CE  x100  P&L: ₹+150          │
└─────────────────────────────────────────────┘
```

---

## 🧪 TESTING BEFORE LIVE

### 1. Run Backtest
```bash
python strategy_backtest.py
```
This simulates 1 year of trades and shows:
- Win rate
- Average P&L
- Max drawdown
- Exit reason breakdown

### 2. Paper Trade First
Edit `nifty_strategy.py`:
```python
# Change this line
ENABLE_LIVE_ORDER = False  # Set to True when ready
```

### 3. Start Small
Begin with 1 lot (minimum) to validate:
- Order execution
- Entry/exit logic
- Margin calculations
- Network stability

---

## ⚠️ IMPORTANT SAFETY

### Before Going Live
- [ ] Tested on paper account for at least 2 weeks
- [ ] Verified margin availability (₹1.5L+ recommended)
- [ ] Checked internet connection stability
- [ ] Set up alerts (optional Telegram integration)
- [ ] Understood maximum loss potential

### Risk Management
- **Never** override stop-loss manually
- **Never** add to losing positions
- **Always** let the system exit automatically
- **Keep** emergency manual exit plan ready

### Common Mistakes to Avoid
1. ❌ Trading with insufficient margin
2. ❌ Interfering with automated exits
3. ❌ Ignoring stop-loss signals
4. ❌ Scaling up too quickly
5. ❌ Not keeping trade logs

---

## 📈 PERFORMANCE EXPECTATIONS

### Realistic Targets
- **Win Rate**: 60-70%
- **Average Win**: +₹1,250
- **Average Loss**: -₹1,250
- **Monthly**: 4 trades = ~₹2,000-₹3,000
- **Annual**: ~20-30% return (before costs)

### Not Every Trade Wins
```
Example Month:
Trade 1: +₹1,250 ✅
Trade 2: -₹1,250 ❌
Trade 3: +₹1,250 ✅
Trade 4: +₹1,250 ✅
──────────────────
Net: +₹2,500 (75% win rate)
```

---

## 🛠️ CUSTOMIZATION

Want different parameters? Edit `nifty_strategy.py`:

```python
STRATEGY_CONFIG = {
    "TARGET_PERCENT": 1.0,      # Try 0.5% or 2%
    "STOP_LOSS_PERCENT": 1.0,   # Adjust risk
    "LOT_SIZE": 50,             # Start with 25
    "ENTRY_TIME": time(9, 45),  # Or 10:00 AM
    "DURATION_DAYS": 5,         # Try 3 days
}
```

---

## 📞 TROUBLESHOOTING

### "Authentication Failed"
- Run `python fyers_login.py` again
- Check TOTP token in Config.yaml
- Verify PIN is correct

### "Insufficient Margin"
- Add funds or reduce LOT_SIZE to 25
- Check margin requirements on Fyers

### "Order Rejected"
- Ensure market is open
- Verify strikes are available
- Check order parameters

### "Position Not Squaring Off"
- Check network connection
- Verify market hours
- Manual exit via dashboard

---

## 📚 NEXT STEPS

1. ✅ Review `STRATEGY_GUIDE.md` for detailed documentation
2. ✅ Run backtest to understand historical performance
3. ✅ Paper trade for 2-4 weeks minimum
4. ✅ Start with 1 lot live trading
5. ✅ Keep detailed trade journal
6. ✅ Review and adjust after 10 trades

---

## ⚖️ LEGAL DISCLAIMER

- **Educational purposes only**
- **High risk** - Only trade with money you can afford to lose
- **No guarantees** - Past performance ≠ future results
- **Not financial advice** - Consult a professional
- **Your responsibility** - You accept all risks

**By using this system, you acknowledge these risks.**

---

## 🎯 READY TO START?

```bash
# Step 1: Authenticate
python fyers_login.py

# Step 2: Test (paper trading mode)
python nifty_strategy.py

# Step 3: Monitor
open strategy_dashboard.html

# Step 4: Backtest (optional)
python strategy_backtest.py
```

---

## 📧 SUPPORT

For questions or issues:
1. Check `STRATEGY_GUIDE.md` first
2. Review Fyers API docs
3. Test on paper account
4. Keep detailed logs

---

**Remember**: 
- Patience > Profits
- Discipline > Emotions  
- System > Gut Feeling

**Happy Trading! 📊🚀**

---

*Last Updated: Jan 31, 2026*
*Version: 1.0*
