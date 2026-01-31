import os
import json
import yaml
import pytz
import pandas as pd
from datetime import datetime, timedelta, time
from fyers_apiv3 import fyersModel
from time import sleep

# ==============================
# CONFIGURATION
# ==============================

CONFIG_FILE = "Config.yaml"
TOKEN_FILE = "auth_tokens.json"
TIMEZONE = pytz.timezone("Asia/Kolkata")

# Strategy Parameters (from screenshot)
STRATEGY_CONFIG = {
    "SCRIPT": "NIFTY",
    "DURATION_DAYS": 5,
    "EXPIRY_TYPE": "BI-WEEKLY",
    "ENTRY_DATE_DTE": 8,  # Monday (8 DTE)
    "ENTRY_TIME": time(9, 45),  # 09:45 AM
    "TARGET_PERCENT": 1.0,  # 1% on deployed capital
    "STOP_LOSS_PERCENT": 1.0,  # 1% on deployed capital
    "LOT_SIZE": 50,
    "PRODUCT_TYPE": "INTRADAY",
    
    # Strike Selection Configuration
    "STRIKES": {
        "ATM_CE": {"qty_multiplier": 1, "otm_offset": 200, "label": "26200 CE"},
        "SELL_CE": {"qty_multiplier": 3, "otm_offset": 400, "label": "26400 CE"},
        "BUY_CE": {"qty_multiplier": 2, "otm_offset": 600, "label": "26600 CE"}
    }
}

# ==============================
# HELPER FUNCTIONS
# ==============================

def load_config(path=CONFIG_FILE):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_access_token(path=TOKEN_FILE):
    with open(path, "r") as f:
        return json.load(f)["access_token"]


def get_fyers_client(client_id, access_token):
    return fyersModel.FyersModel(
        client_id=client_id,
        token=access_token,
        is_async=False,
        log_path=os.getcwd()
    )


def get_current_time():
    return datetime.now(TIMEZONE)


def is_market_open():
    """Check if market is open (9:15 AM to 3:30 PM IST)"""
    now = get_current_time()
    market_open = time(9, 15)
    market_close = time(15, 30)
    
    # Check if weekday and within market hours
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    
    current_time = now.time()
    return market_open <= current_time <= market_close


def get_next_expiry(dte_target=8):
    """
    Calculate next bi-weekly expiry that matches the DTE target
    Nifty bi-weekly expires on Wednesday
    """
    now = get_current_time()
    
    # Find next Wednesday
    days_until_wednesday = (2 - now.weekday()) % 7
    if days_until_wednesday == 0:
        days_until_wednesday = 7  # Next Wednesday if today is Wednesday
    
    expiry_date = now + timedelta(days=days_until_wednesday)
    
    # Format: DDMMMYY (e.g., 05FEB26)
    return expiry_date.strftime("%d%b%y").upper()


def calculate_atm_strike(spot_price, strike_interval=50):
    """Round spot price to nearest strike (typically 50 points for Nifty)"""
    return round(spot_price / strike_interval) * strike_interval


def get_nifty_spot_price(fyers):
    """Fetch current Nifty spot price"""
    response = fyers.quotes({"symbols": "NSE:NIFTY50-INDEX"})
    
    if response.get("s") == "ok":
        ltp = response["d"][0]["v"]["lp"]
        return ltp
    else:
        raise Exception(f"Failed to fetch Nifty spot: {response}")


def calculate_deployed_capital(fyers, positions):
    """
    Calculate total capital deployed in the strategy
    Based on margin blocked for all positions
    """
    # For simplicity, using total margin from funds
    funds = fyers.funds()
    
    if funds.get("s") == "ok":
        # Use utilized margin as deployed capital
        deployed = funds["fund_limit"][0].get("utilized_margin", 0)
        return deployed
    
    return 0


def build_option_symbol(underlying, expiry, strike, option_type):
    """
    Build Fyers option symbol
    Format: NSE:NIFTY24JAN2626200CE
    """
    return f"NSE:{underlying}{expiry}{strike}{option_type}"


# ==============================
# STRATEGY LOGIC
# ==============================

class NiftyOptionsStrategy:
    def __init__(self, fyers, config):
        self.fyers = fyers
        self.config = config
        self.positions = []
        self.entry_price_total = 0
        self.deployed_capital = 0
        self.position_active = False
        
    def should_enter_trade(self):
        """Check if current time matches entry criteria"""
        now = get_current_time()
        
        # Check if it's Monday
        if now.weekday() != 0:  # 0 = Monday
            return False
        
        # Check if time is exactly or past entry time
        if now.time() < self.config["ENTRY_TIME"]:
            return False
        
        # Check if market is open
        if not is_market_open():
            return False
        
        return True
    
    def get_strike_configuration(self, spot_price):
        """
        Calculate strikes based on spot price and configuration
        Returns: dict with strike details
        """
        atm_strike = calculate_atm_strike(spot_price)
        
        strikes = {
            "BUY_ATM_CE": {
                "strike": atm_strike + 200,  # 200 points OTM
                "qty": 1,
                "side": 1  # BUY
            },
            "SELL_CE": {
                "strike": atm_strike + 400,  # 400 points OTM
                "qty": 3,
                "side": -1  # SELL
            },
            "BUY_HEDGE_CE": {
                "strike": atm_strike + 600,  # 600 points OTM
                "qty": 2,
                "side": 1  # BUY
            }
        }
        
        return strikes, atm_strike
    
    def execute_basket_entry(self):
        """Execute the complete basket order entry"""
        print("\n" + "="*50)
        print("EXECUTING NIFTY OPTIONS STRATEGY ENTRY")
        print("="*50)
        
        # Get current Nifty spot
        spot_price = get_nifty_spot_price(self.fyers)
        print(f"Nifty Spot Price: {spot_price}")
        
        # Calculate strikes
        strikes, atm_strike = self.get_strike_configuration(spot_price)
        print(f"ATM Strike (Base): {atm_strike}")
        
        # Get expiry
        expiry = get_next_expiry(self.config["ENTRY_DATE_DTE"])
        print(f"Expiry: {expiry}")
        
        # Build positions
        lot_size = self.config["LOT_SIZE"]
        
        basket_orders = []
        for label, strike_config in strikes.items():
            symbol = build_option_symbol(
                self.config["SCRIPT"],
                expiry,
                strike_config["strike"],
                "CE"
            )
            
            order = {
                "symbol": symbol,
                "qty": strike_config["qty"] * lot_size,
                "side": strike_config["side"],
                "strike": strike_config["strike"],
                "label": label
            }
            
            basket_orders.append(order)
        
        # Place orders
        print("\nPlacing Orders:")
        print("-" * 50)
        
        order_ids = []
        total_premium = 0
        
        for order in basket_orders:
            payload = {
                "symbol": order["symbol"],
                "qty": order["qty"],
                "type": 2,  # MARKET ORDER
                "side": order["side"],
                "productType": self.config["PRODUCT_TYPE"],
                "limitPrice": 0,
                "stopPrice": 0,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": False,
                "orderTag": order["label"],
                "isSliceOrder": False
            }
            
            response = self.fyers.place_order(data=payload)
            
            action = "BUY" if order["side"] == 1 else "SELL"
            print(f"{action} {order['qty']} x {order['symbol']}")
            print(f"Response: {response}")
            
            if response.get("s") == "ok":
                order_ids.append({
                    "id": response.get("id"),
                    "label": order["label"],
                    "symbol": order["symbol"],
                    "qty": order["qty"],
                    "side": order["side"]
                })
                
                # Track for monitoring
                self.positions.append(order)
            else:
                print(f"❌ Order failed: {order['label']}")
                # Optionally: exit all positions if basket execution fails
                return False
            
            sleep(0.5)  # Avoid rate limiting
        
        self.position_active = True
        self.deployed_capital = calculate_deployed_capital(self.fyers, order_ids)
        
        print("\n" + "="*50)
        print(f"✅ BASKET EXECUTED | Deployed Capital: ₹{self.deployed_capital:,.2f}")
        print("="*50)
        
        return True
    
    def calculate_current_pnl(self):
        """Calculate current P&L of the strategy"""
        if not self.position_active:
            return 0
        
        # Fetch current positions
        positions = self.fyers.positions()
        
        if positions.get("s") != "ok":
            return 0
        
        net_pnl = positions.get("netPositions", [])
        
        total_pnl = sum([pos.get("pl", 0) for pos in net_pnl])
        
        return total_pnl
    
    def check_exit_conditions(self):
        """Check if target or stop-loss is hit"""
        if not self.position_active:
            return False, None
        
        current_pnl = self.calculate_current_pnl()
        
        target_amount = self.deployed_capital * (self.config["TARGET_PERCENT"] / 100)
        sl_amount = -self.deployed_capital * (self.config["STOP_LOSS_PERCENT"] / 100)
        
        print(f"Current P&L: ₹{current_pnl:,.2f} | Target: ₹{target_amount:,.2f} | SL: ₹{sl_amount:,.2f}")
        
        # Check target
        if current_pnl >= target_amount:
            return True, "TARGET"
        
        # Check stop-loss
        if current_pnl <= sl_amount:
            return True, "STOP_LOSS"
        
        return False, None
    
    def exit_all_positions(self, reason="MANUAL"):
        """Square off all positions"""
        if not self.position_active:
            print("No active positions to exit")
            return
        
        print(f"\n🔴 EXITING ALL POSITIONS | Reason: {reason}")
        
        positions = self.fyers.positions()
        
        if positions.get("s") != "ok":
            print("Failed to fetch positions")
            return
        
        net_positions = positions.get("netPositions", [])
        
        for pos in net_positions:
            symbol = pos.get("symbol")
            net_qty = pos.get("netQty", 0)
            
            if net_qty == 0:
                continue
            
            # Exit: reverse the side
            exit_side = -1 if net_qty > 0 else 1
            exit_qty = abs(net_qty)
            
            exit_order = {
                "symbol": symbol,
                "qty": exit_qty,
                "type": 2,  # MARKET
                "side": exit_side,
                "productType": self.config["PRODUCT_TYPE"],
                "limitPrice": 0,
                "stopPrice": 0,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": False,
                "orderTag": f"EXIT_{reason}",
                "isSliceOrder": False
            }
            
            response = self.fyers.place_order(data=exit_order)
            print(f"Exit {symbol}: {response}")
            
            sleep(0.5)
        
        self.position_active = False
        final_pnl = self.calculate_current_pnl()
        
        print(f"\n✅ ALL POSITIONS CLOSED | Final P&L: ₹{final_pnl:,.2f}")
    
    def monitor_positions(self, check_interval=30):
        """
        Monitor positions continuously
        check_interval: seconds between checks
        """
        print("\n📊 Starting Position Monitor...")
        
        while self.position_active and is_market_open():
            should_exit, exit_reason = self.check_exit_conditions()
            
            if should_exit:
                self.exit_all_positions(reason=exit_reason)
                break
            
            sleep(check_interval)
        
        # Auto-exit at market close
        if self.position_active and not is_market_open():
            print("\n⏰ Market closing - Auto-exiting positions")
            self.exit_all_positions(reason="MARKET_CLOSE")


# ==============================
# MAIN EXECUTION
# ==============================

def main():
    print("="*60)
    print("NIFTY BI-WEEKLY OPTIONS STRATEGY")
    print("="*60)
    
    # Load configuration
    config = load_config()
    access_token = load_access_token()
    client_id = config["fyers"]["client_id"]
    
    # Initialize Fyers client
    fyers = get_fyers_client(client_id, access_token)
    
    # Verify connection
    profile = fyers.get_profile()
    print(f"\n✅ Logged in as: {profile['data']['name']}")
    
    # Initialize strategy
    strategy = NiftyOptionsStrategy(fyers, STRATEGY_CONFIG)
    
    # Check if it's entry time
    if strategy.should_enter_trade():
        print("\n🚀 Entry conditions met - Executing strategy")
        
        success = strategy.execute_basket_entry()
        
        if success:
            # Start monitoring
            strategy.monitor_positions(check_interval=30)
        else:
            print("❌ Strategy execution failed")
    else:
        now = get_current_time()
        print(f"\n⏸️  Entry conditions not met")
        print(f"Current Day: {now.strftime('%A')}")
        print(f"Current Time: {now.strftime('%H:%M:%S')}")
        print(f"Entry Day: Monday")
        print(f"Entry Time: {STRATEGY_CONFIG['ENTRY_TIME']}")
        print(f"Market Open: {is_market_open()}")


if __name__ == "__main__":
    main()
