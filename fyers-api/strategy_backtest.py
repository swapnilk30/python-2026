import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import pytz
from typing import List, Dict

# ==============================
# BACKTEST CONFIGURATION
# ==============================

TIMEZONE = pytz.timezone("Asia/Kolkata")

class OptionsBacktest:
    """
    Backtest the Nifty options strategy using historical data
    """
    
    def __init__(self, config):
        self.config = config
        self.trades = []
        self.equity_curve = []
        
    def simulate_option_price(self, spot, strike, option_type, dte, iv=0.15):
        """
        Simple Black-Scholes approximation for option pricing
        For backtesting purposes - uses simplified pricing
        """
        # Simplified intrinsic + time value estimation
        if option_type == "CE":
            intrinsic = max(0, spot - strike)
        else:
            intrinsic = max(0, strike - spot)
        
        # Time value decreases with DTE
        time_value = (strike * iv * np.sqrt(dte/365)) / 4
        
        return intrinsic + time_value
    
    def get_basket_prices(self, spot, strikes, dte):
        """Calculate theoretical prices for entire basket"""
        prices = {}
        
        for label, strike_config in strikes.items():
            price = self.simulate_option_price(
                spot,
                strike_config["strike"],
                "CE",
                dte
            )
            prices[label] = price
        
        return prices
    
    def calculate_basket_pnl(self, entry_prices, exit_prices, strikes, lot_size):
        """Calculate P&L for the basket"""
        pnl = 0
        
        for label, strike_config in strikes.items():
            entry = entry_prices[label]
            exit = exit_prices[label]
            qty = strike_config["qty"] * lot_size
            side = strike_config["side"]
            
            # BUY: exit - entry | SELL: entry - exit
            if side == 1:  # BUY
                pnl += (exit - entry) * qty
            else:  # SELL
                pnl += (entry - exit) * qty
        
        return pnl
    
    def calculate_deployed_capital(self, entry_prices, strikes, lot_size):
        """Estimate deployed capital (margin requirement)"""
        # Simplified: Total premium of short positions + margin buffer
        short_premium = 0
        long_premium = 0
        
        for label, strike_config in strikes.items():
            price = entry_prices[label]
            qty = strike_config["qty"] * lot_size
            
            if strike_config["side"] == -1:  # SELL
                short_premium += price * qty
            else:
                long_premium += price * qty
        
        # Typical margin for credit spreads: ~30% of short premium
        margin = short_premium * 0.3 + long_premium
        
        return margin
    
    def run_backtest(self, historical_data: pd.DataFrame):
        """
        Run backtest on historical Nifty data
        
        historical_data: DataFrame with columns ['date', 'open', 'high', 'low', 'close']
        """
        
        print("\n" + "="*60)
        print("RUNNING BACKTEST - NIFTY OPTIONS STRATEGY")
        print("="*60)
        
        # Filter for Mondays (entry day)
        historical_data['weekday'] = pd.to_datetime(historical_data['date']).dt.weekday
        entry_days = historical_data[historical_data['weekday'] == 0].copy()
        
        lot_size = self.config["LOT_SIZE"]
        target_pct = self.config["TARGET_PERCENT"] / 100
        sl_pct = self.config["STOP_LOSS_PERCENT"] / 100
        
        total_trades = 0
        winning_trades = 0
        total_pnl = 0
        
        for idx, entry_row in entry_days.iterrows():
            entry_date = pd.to_datetime(entry_row['date'])
            spot_entry = entry_row['close']
            
            # Calculate strikes
            atm_strike = round(spot_entry / 50) * 50
            
            strikes = {
                "BUY_ATM_CE": {
                    "strike": atm_strike + 200,
                    "qty": 1,
                    "side": 1
                },
                "SELL_CE": {
                    "strike": atm_strike + 400,
                    "qty": 3,
                    "side": -1
                },
                "BUY_HEDGE_CE": {
                    "strike": atm_strike + 600,
                    "qty": 2,
                    "side": 1
                }
            }
            
            # Entry prices (8 DTE)
            entry_prices = self.get_basket_prices(spot_entry, strikes, dte=8)
            deployed_capital = self.calculate_deployed_capital(entry_prices, strikes, lot_size)
            
            target_amount = deployed_capital * target_pct
            sl_amount = -deployed_capital * sl_pct
            
            # Simulate next 5 days
            exit_date = entry_date + timedelta(days=5)
            next_5_days = historical_data[
                (pd.to_datetime(historical_data['date']) > entry_date) &
                (pd.to_datetime(historical_data['date']) <= exit_date)
            ]
            
            trade_result = None
            exit_reason = None
            final_pnl = 0
            
            for _, day_row in next_5_days.iterrows():
                current_spot = day_row['close']
                current_date = pd.to_datetime(day_row['date'])
                days_elapsed = (current_date - entry_date).days
                dte_remaining = max(1, 8 - days_elapsed)
                
                # Current prices
                current_prices = self.get_basket_prices(current_spot, strikes, dte_remaining)
                
                # Calculate P&L
                current_pnl = self.calculate_basket_pnl(
                    entry_prices,
                    current_prices,
                    strikes,
                    lot_size
                )
                
                # Check exit conditions
                if current_pnl >= target_amount:
                    final_pnl = current_pnl
                    exit_reason = "TARGET"
                    break
                elif current_pnl <= sl_amount:
                    final_pnl = current_pnl
                    exit_reason = "STOP_LOSS"
                    break
            
            # If no exit, close at end of 5 days
            if exit_reason is None:
                final_spot = next_5_days.iloc[-1]['close'] if len(next_5_days) > 0 else spot_entry
                final_prices = self.get_basket_prices(final_spot, strikes, dte=3)
                final_pnl = self.calculate_basket_pnl(entry_prices, final_prices, strikes, lot_size)
                exit_reason = "DURATION"
            
            # Record trade
            total_trades += 1
            if final_pnl > 0:
                winning_trades += 1
            
            total_pnl += final_pnl
            
            self.trades.append({
                "entry_date": entry_date,
                "spot_entry": spot_entry,
                "atm_strike": atm_strike,
                "deployed_capital": deployed_capital,
                "pnl": final_pnl,
                "pnl_pct": (final_pnl / deployed_capital) * 100,
                "exit_reason": exit_reason
            })
            
            print(f"\nTrade #{total_trades}")
            print(f"Entry: {entry_date.date()} | Spot: {spot_entry:.2f}")
            print(f"P&L: ₹{final_pnl:,.2f} ({(final_pnl/deployed_capital)*100:.2f}%)")
            print(f"Exit: {exit_reason}")
        
        # Generate statistics
        self.generate_report(total_trades, winning_trades, total_pnl)
        
        return pd.DataFrame(self.trades)
    
    def generate_report(self, total_trades, winning_trades, total_pnl):
        """Generate backtest performance report"""
        
        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)
        
        if total_trades == 0:
            print("No trades executed")
            return
        
        win_rate = (winning_trades / total_trades) * 100
        avg_pnl = total_pnl / total_trades
        
        trades_df = pd.DataFrame(self.trades)
        
        max_win = trades_df['pnl'].max()
        max_loss = trades_df['pnl'].min()
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean()
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean()
        
        print(f"\nTotal Trades: {total_trades}")
        print(f"Winning Trades: {winning_trades}")
        print(f"Losing Trades: {total_trades - winning_trades}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"\nTotal P&L: ₹{total_pnl:,.2f}")
        print(f"Average P&L per Trade: ₹{avg_pnl:,.2f}")
        print(f"\nMax Win: ₹{max_win:,.2f}")
        print(f"Max Loss: ₹{max_loss:,.2f}")
        print(f"Average Win: ₹{avg_win:,.2f}")
        print(f"Average Loss: ₹{avg_loss:,.2f}")
        
        # Exit reason breakdown
        print("\nExit Reason Breakdown:")
        exit_counts = trades_df['exit_reason'].value_counts()
        for reason, count in exit_counts.items():
            print(f"{reason}: {count} ({(count/total_trades)*100:.1f}%)")
        
        print("\n" + "="*60)


# ==============================
# SAMPLE USAGE
# ==============================

def run_sample_backtest():
    """Run backtest with sample historical data"""
    
    # Sample configuration
    config = {
        "SCRIPT": "NIFTY",
        "DURATION_DAYS": 5,
        "ENTRY_DATE_DTE": 8,
        "TARGET_PERCENT": 1.0,
        "STOP_LOSS_PERCENT": 1.0,
        "LOT_SIZE": 50
    }
    
    # Generate sample historical data (replace with actual data)
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='B')
    
    np.random.seed(42)
    base_price = 22000
    
    # Simulate price movement
    returns = np.random.normal(0.0005, 0.015, len(dates))
    prices = base_price * np.exp(np.cumsum(returns))
    
    historical_data = pd.DataFrame({
        'date': dates,
        'open': prices * np.random.uniform(0.995, 1.005, len(dates)),
        'high': prices * np.random.uniform(1.005, 1.015, len(dates)),
        'low': prices * np.random.uniform(0.985, 0.995, len(dates)),
        'close': prices
    })
    
    # Run backtest
    backtest = OptionsBacktest(config)
    results = backtest.run_backtest(historical_data)
    
    # Save results
    results.to_csv("backtest_results.csv", index=False)
    print("\n✅ Results saved to backtest_results.csv")
    
    return results


if __name__ == "__main__":
    run_sample_backtest()
