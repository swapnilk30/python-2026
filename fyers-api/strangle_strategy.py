import os
import json
import yaml
from fyers_apiv3 import fyersModel
from datetime import datetime, time
import time as tm
import math

# ===============================
# STRATEGY CONFIGURATION
# ===============================

STRATEGY = {
    'index': 'NIFTY',  # or 'BANKNIFTY'
    'index_symbol': 'NSE:NIFTY50-INDEX',  # or 'NSE:NIFTYBANK-INDEX'
    'quantity': 65,  # lot size
    'strike_base': 50,  # 50 for NIFTY, 100 for BANKNIFTY
    'entry_time': {'hour': 9, 'minute': 20},
    'exit_time': {'hour': 15, 'minute': 0}
}

# ===============================
# CONFIG LOADERS
# ===============================

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_access_token(path="auth_tokens.json"):
    with open(path, "r") as f:
        return json.load(f)["access_token"]

# ===============================
# FYERS CLIENT
# ===============================

def get_fyers_client(client_id, access_token):
    return fyersModel.FyersModel(
        client_id=client_id,
        token=access_token,
        is_async=False,
        log_path=os.getcwd()
    )

# ===============================
# UTILITY FUNCTIONS
# ===============================

def get_atm_strike(ltp, base=50):
    """Round LTP to nearest strike based on base (50 for NIFTY/BANKNIFTY)"""
    return base * round(ltp / base)


def get_nearest_expiry(fyers, symbol="NSE:NIFTY50-INDEX"):
    """Get the nearest weekly expiry for options"""
    data = {
        "symbol": symbol,
        "strikecount": 5,
        "timestamp": ""
    }
    response = fyers.optionchain(data=data)
    
    if response['s'] == 'ok':
        expiries = response['data']['expiryData']
        nearest_expiry = min(expiries, key=lambda x: x['date'])
        return nearest_expiry['date']
    return None


def build_option_symbol(index, expiry, strike, option_type):
    """
    Build Fyers option symbol
    Format: NSE:NIFTY24JAN25000CE or NSE:BANKNIFTY24JAN50000PE
    """
    if index == "NIFTY":
        base = "NSE:NIFTY"
    elif index == "BANKNIFTY":
        base = "NSE:BANKNIFTY"
    else:
        base = f"NSE:{index}"
    
    # Parse expiry date (format: YYYYMMDD to YYMMMDD)
    exp_date = datetime.strptime(str(expiry), "%Y%m%d")
    exp_str = exp_date.strftime("%y%b").upper()
    
    return f"{base}{exp_str}{int(strike)}{option_type}"


def get_ltp(fyers, symbol):
    """Get Last Traded Price"""
    data = {"symbols": symbol}
    response = fyers.quotes(data=data)
    
    if response['s'] == 'ok' and response['d']:
        return response['d'][0]['v']['lp']
    return None

# ===============================
# ORDER PLACEMENT
# ===============================

def place_order(fyers, symbol, qty, side, order_type="MARKET"):
    """Place order on Fyers"""
    data = {
        "symbol": symbol,
        "qty": qty,
        "type": 2 if order_type == "MARKET" else 1,  # 2=MARKET, 1=LIMIT
        "side": 1 if side == "BUY" else -1,  # 1=BUY, -1=SELL
        "productType": "INTRADAY",
        "limitPrice": 0,
        "stopPrice": 0,
        "validity": "DAY",
        "disclosedQty": 0,
        "offlineOrder": False
    }
    
    response = fyers.place_order(data=data)
    print(f"Order Response for {symbol}: {response}")
    return response

# ===============================
# STRATEGY LOGIC
# ===============================

def execute_strangle_entry(fyers):
    """Execute strangle entry at 9:20 AM"""
    
    index = STRATEGY['index']
    index_symbol = STRATEGY['index_symbol']
    quantity = STRATEGY['quantity']
    strike_base = STRATEGY['strike_base']
    
    print(f"\n{'='*50}")
    print(f"EXECUTING STRANGLE ENTRY at {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}")
    
    # Get current LTP of index
    ltp = get_ltp(fyers, index_symbol)
    if not ltp:
        print("Failed to fetch index LTP")
        return None
    
    print(f"{index} LTP: {ltp}")
    
    # Calculate ATM and strikes
    atm_strike = get_atm_strike(ltp, strike_base)
    ce_strike = atm_strike + 100
    pe_strike = atm_strike + 100
    
    print(f"ATM Strike: {atm_strike}")
    print(f"CE Strike (ATM+100): {ce_strike}")
    print(f"PE Strike (ATM+100): {pe_strike}")
    
    # Get nearest expiry
    expiry = get_nearest_expiry(fyers, index_symbol)
    if not expiry:
        print("Failed to fetch expiry")
        return None
    
    print(f"Expiry: {expiry}")
    
    # Build option symbols
    ce_symbol = build_option_symbol(index, expiry, ce_strike, "CE")
    pe_symbol = build_option_symbol(index, expiry, pe_strike, "PE")
    
    print(f"\nCE Symbol: {ce_symbol}")
    print(f"PE Symbol: {pe_symbol}")
    
    # Place orders
    print("\nPlacing SELL orders...")
    ce_order = place_order(fyers, ce_symbol, quantity, "SELL")
    pe_order = place_order(fyers, pe_symbol, quantity, "SELL")
    
    positions = {
        'ce_symbol': ce_symbol,
        'pe_symbol': pe_symbol,
        'ce_strike': ce_strike,
        'pe_strike': pe_strike,
        'quantity': quantity,
        'entry_time': datetime.now().strftime('%H:%M:%S'),
        'ce_order_id': ce_order.get('id') if ce_order.get('s') == 'ok' else None,
        'pe_order_id': pe_order.get('id') if pe_order.get('s') == 'ok' else None
    }
    
    return positions


def execute_strangle_exit(fyers, positions):
    """Exit strangle positions at 3:00 PM"""
    
    print(f"\n{'='*50}")
    print(f"EXECUTING STRANGLE EXIT at {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}")
    
    ce_symbol = positions['ce_symbol']
    pe_symbol = positions['pe_symbol']
    quantity = positions['quantity']
    
    print(f"Closing CE: {ce_symbol}")
    print(f"Closing PE: {pe_symbol}")
    
    # Buy back to close short positions
    ce_exit = place_order(fyers, ce_symbol, quantity, "BUY")
    pe_exit = place_order(fyers, pe_symbol, quantity, "BUY")
    
    print("\nPositions closed successfully!")
    return True


def run_strategy(fyers):
    """Main strategy execution loop"""
    
    entry_time = time(STRATEGY['entry_time']['hour'], STRATEGY['entry_time']['minute'])
    exit_time = time(STRATEGY['exit_time']['hour'], STRATEGY['exit_time']['minute'])
    
    positions = None
    entry_done = False
    exit_done = False
    
    print(f"\nStrategy Started. Waiting for entry time ({entry_time.strftime('%H:%M')})...")
    print(f"Exit scheduled at {exit_time.strftime('%H:%M')}")
    print(f"Trading: {STRATEGY['index']} | Quantity: {STRATEGY['quantity']} | Strike Base: {STRATEGY['strike_base']}")
    
    while True:
        now = datetime.now().time()
        
        # Entry logic
        if not entry_done and now >= entry_time:
            positions = execute_strangle_entry(fyers)
            entry_done = True
            
            if positions:
                print("\n✓ Entry completed successfully")
            else:
                print("\n✗ Entry failed")
                break
        
        # Exit logic
        if entry_done and not exit_done and now >= exit_time:
            if positions:
                execute_strangle_exit(fyers, positions)
                exit_done = True
                print("\n✓ Strategy completed for the day")
                break
            else:
                print("\n✗ No positions to exit")
                break
        
        # Sleep for 10 seconds before next check
        if entry_done and not exit_done:
            print(f"Monitoring positions... Current time: {now.strftime('%H:%M:%S')}", end='\r')
        
        tm.sleep(10)

# ===============================
# MAIN
# ===============================

def main():
    config = load_config()
    access_token = load_access_token()

    client_id = config["fyers"]["client_id"]

    fyers = get_fyers_client(client_id, access_token)

    # Verify login
    profile = fyers.get_profile()
    print("Profile:", profile)
    
    if profile.get('s') == 'ok':
        print(f"\n✓ Login successful: {profile['data']['name']}")
        
        # Run the strategy
        run_strategy(fyers)
    else:
        print("\n✗ Login failed")


if __name__ == "__main__":
    main()