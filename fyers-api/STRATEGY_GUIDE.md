# NIFTY BI-WEEKLY OPTIONS STRATEGY
## Complete Implementation Guide

---

## 📊 STRATEGY OVERVIEW

### Core Parameters
- **Instrument**: NIFTY (Index Options)
- **Duration**: 5 Days
- **Expiry**: Bi-Weekly (Wednesday)
- **Entry Date**: Monday (8 DTE - Days to Expiry)
- **Entry Time**: 09:45 AM IST
- **Target**: 1% on Deployed Capital
- **Stop Loss**: 1% on Deployed Capital
- **Lot Size**: 50

### Strike Selection Strategy

The strategy employs a **Ratio Call Spread** structure:

```
Position Structure:
├── BUY  1x CE @ ATM + 200 (26200 CE) - Lower OTM
├── SELL 3x CE @ ATM + 400 (26400 CE) - Middle OTM ⚠️ [Short]
└── BUY  2x CE @ ATM + 600 (26600 CE) - Upper OTM (Hedge)
```

**Example** (if Nifty Spot = 26,000):
- **BUY**  1 lot × 50 = 50 qty @ 26200 CE
- **SELL** 3 lots × 50 = 150 qty @ 26400 CE ⚠️
- **BUY**  2 lots × 50 = 100 qty @ 26600 CE

---

## 🎯 STRATEGY LOGIC

### Entry Conditions
✅ **All must be TRUE**:
1. Day = **Monday**
2. Time >= **09:45 AM IST**
3. Market = **OPEN**
4. DTE = **8 days** (bi-weekly Wednesday expiry)

### Exit Conditions
🔴 **Any ONE triggers exit**:
1. **Target Hit**: P&L >= +1% of deployed capital
2. **Stop Loss Hit**: P&L <= -1% of deployed capital
3. **Duration**: 5 trading days elapsed
4. **Market Close**: Auto-exit at 3:30 PM

### Position Monitoring
- Monitor every **30 seconds** during market hours
- Real-time P&L calculation
- Automatic basket exit on trigger

---

## 💰 RISK PROFILE

### Maximum Risk
The strategy has **LIMITED RISK** due to long hedge positions.

**Worst Case Scenario**: 
- If Nifty rallies sharply above 26600
- Short 26400 CE loses value
- Long 26600 CE provides protection

**Max Loss Calculation**:
```
Max Loss = Premium Paid - Premium Received + Spread Width × Short Qty
         = (Long Premium) - (Short Premium) + (200 points × 150 qty)
```

### Capital Deployment
- Margin blocked for short CE positions
- Premium paid for long CE positions
- Total deployed capital = Margin + Premium paid

### Risk-Reward
- **Target**: +1% of deployed capital
- **Risk**: -1% of deployed capital
- **Risk-Reward Ratio**: 1:1

---

## 📁 FILE STRUCTURE

```
project/
├── fyers_login.py              # Authentication & login
├── nifty_strategy.py           # Main strategy execution
├── strategy_backtest.py        # Backtesting module
├── Config.yaml                 # Configuration file
├── auth_tokens.json            # Auth tokens (auto-generated)
└── README.md                   # This file
```

---

## ⚙️ SETUP INSTRUCTIONS

### 1. Install Dependencies
```bash
pip install fyers-apiv3 pandas pyyaml pytz pyotp requests --break-system-packages
```

### 2. Configure Config.yaml
```yaml
fyers:
  username: "YOUR_FYERS_ID"           # e.g., XY12345
  secret_key: "YOUR_SECRET_KEY"       # From Fyers API dashboard
  client_id: "YOUR_APP_ID"            # From Fyers API dashboard
  redirect_uri: "https://www.google.co.in/"
  token: "YOUR_TOTP_SECRET"           # TOTP secret for 2FA
  pin: 1234                           # Your trading PIN

userid: XY12345

Algo_Setup: 
  TradeMode: Live                     # or Paper

Telegram:
  TelegramBotCredential: "BOT_TOKEN"  # Optional
  Chat_Id: "CHAT_ID"                  # Optional
```

### 3. First Time Login
```bash
python fyers_login.py
```
This will:
- Authenticate using TOTP
- Generate access token
- Save to `auth_tokens.json`

### 4. Run Strategy
```bash
python nifty_strategy.py
```

### 5. Run Backtest (Optional)
```bash
python strategy_backtest.py
```

---

## 🚀 LIVE EXECUTION FLOW

```
START
  ↓
Check Entry Conditions
  ├─ Not Monday → Wait
  ├─ Before 9:45 AM → Wait
  └─ Market Closed → Wait
  ↓
✅ Conditions Met
  ↓
Fetch Nifty Spot Price
  ↓
Calculate ATM Strike
  ↓
Determine Expiry (8 DTE)
  ↓
Build Strike Ladder
  ├─ 26200 CE (Buy 1x)
  ├─ 26400 CE (Sell 3x)
  └─ 26600 CE (Buy 2x)
  ↓
Execute Basket Order (Market Order)
  ↓
Calculate Deployed Capital
  ↓
Start Position Monitor
  ├─ Check P&L every 30s
  ├─ Target Hit? → EXIT ALL
  ├─ SL Hit? → EXIT ALL
  ├─ 5 Days Over? → EXIT ALL
  └─ Market Close? → EXIT ALL
  ↓
SQUARE OFF ALL POSITIONS
  ↓
Calculate Final P&L
  ↓
END
```

---

## 📊 EXPECTED PERFORMANCE METRICS

### Win Rate Target
- **60-70%** win rate (based on 1% target/SL)

### Typical Outcomes
- **Target Hit**: ~60-70% of trades
- **Stop Loss Hit**: ~20-30% of trades
- **Duration Exit**: ~10% of trades

### Annual Returns (Theoretical)
- Trades per month: ~4 (every Monday with 8 DTE)
- Average return per trade: +0.5% (after losses)
- Monthly: ~2%
- Annualized: ~24-30%

**Note**: Past performance does not guarantee future results.

---

## ⚠️ IMPORTANT SAFETY CHECKS

### Pre-Trade Checklist
- [ ] Sufficient margin in account
- [ ] Correct expiry selected (8 DTE)
- [ ] All strikes available for trading
- [ ] Market is open and liquid
- [ ] Config.yaml properly set
- [ ] Access token is valid

### Risk Management Rules
1. **Never override stop loss manually**
2. **Always let basket execute completely or fail completely**
3. **Don't add to losing positions**
4. **Monitor for network/API failures**
5. **Have manual exit plan ready**

### Common Issues & Solutions

**Issue**: "Order rejected - insufficient margin"
- **Solution**: Reduce lot size or add funds

**Issue**: "Strike not found"
- **Solution**: Check if expiry calculation is correct

**Issue**: "Market order slippage"
- **Solution**: Consider limit orders during high volatility

---

## 🧪 TESTING RECOMMENDATIONS

### Paper Trading
Before going live:
1. Run backtest on historical data
2. Paper trade for 1 month
3. Verify entry/exit logic
4. Test network failures
5. Validate margin calculations

### Live Trading Checklist
- [ ] Start with 1 lot minimum
- [ ] Monitor first 5 trades manually
- [ ] Keep detailed trade journal
- [ ] Review weekly performance
- [ ] Adjust if win rate < 50%

---

## 📈 MONITORING & LOGGING

### What to Track
- Entry date & time
- Spot price at entry
- Strikes selected
- Premium collected/paid
- Deployed capital
- Exit reason
- Final P&L
- P&L %

### Sample Trade Log
```
Trade #1
Date: 2026-02-03 (Monday)
Entry Time: 09:45:12
Spot: 26,123
Strikes: 26200/26400/26600 CE
Deployed: ₹1,25,000
Exit: TARGET (11:23 AM)
P&L: +₹1,250 (+1.0%)
```

---

## 🛠️ CUSTOMIZATION OPTIONS

### Adjustable Parameters (in code)

```python
STRATEGY_CONFIG = {
    "TARGET_PERCENT": 1.0,      # Change to 0.5 or 1.5
    "STOP_LOSS_PERCENT": 1.0,   # Adjust risk
    "LOT_SIZE": 50,             # Start small (25)
    "ENTRY_TIME": time(9, 45),  # Can shift to 10:00
    "DURATION_DAYS": 5,         # Reduce to 3
}
```

### Strategy Variants

**Conservative**: Target 0.5%, SL 0.5%, 3 lots max
**Aggressive**: Target 2%, SL 1%, 10 lots
**Quick Exit**: Duration 2 days, Target 0.75%

---

## 📞 SUPPORT & MAINTENANCE

### Regular Maintenance
- Update access tokens daily (automated)
- Review trade logs weekly
- Backtest with new data monthly
- Adjust parameters quarterly

### Emergency Contacts
- Fyers Support: 1800-266-3333
- Keep broker number handy
- Have manual exit plan

### Code Updates
- Check Fyers API version updates
- Test on paper account after any changes
- Maintain backup of Config.yaml

---

## 📚 ADDITIONAL RESOURCES

### Learn More
- [Fyers API Documentation](https://myapi.fyers.in/docs/)
- [Options Trading Strategies](https://www.investopedia.com/options-basics-tutorial-4583012)
- [Ratio Spreads Explained](https://www.optionsplaybook.com/option-strategies/)

### Tools
- Options Calculator: [optioncreator.com](https://optioncreator.com)
- Volatility Data: [nseindia.com](https://nseindia.com)
- Nifty Options Chain: Fyers/Zerodha/etc.

---

## ⚖️ DISCLAIMER

**IMPORTANT LEGAL NOTICE**:
- This strategy is for **educational purposes only**
- Past performance does not guarantee future results
- Options trading involves **substantial risk**
- Only trade with capital you can afford to lose
- Consult a financial advisor before trading
- The developer is **not responsible for any losses**
- Always comply with SEBI regulations

**By using this code, you accept all risks associated with automated trading.**

---

## 📝 VERSION HISTORY

**v1.0** (2026-01-31)
- Initial release
- Ratio call spread implementation
- 1% target/SL
- Monday entry, 5-day duration
- Auto-exit on target/SL/duration

---

## 🤝 CONTRIBUTING

Found a bug or have suggestions?
- Test thoroughly before suggesting changes
- Document any modifications
- Share backtest results

---

**Happy Trading! 🚀📈**

**Remember**: Discipline > Strategy. Stick to the rules!
