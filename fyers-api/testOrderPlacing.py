import os
import json
import yaml
from fyers_apiv3 import fyersModel

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
# ORDER PLACEMENT
# ===============================

def place_test_order(fyers):
    """
    SAFE TEST ORDER
    Qty = 1
    Intraday
    Market order
    FYERS sample compatible
    """

    order_data = {
        "symbol": "NSE:IDEA-EQ",
        "qty": 1,
        "type": 2,                # 2 = MARKET
        "side": 1,                # 1 = BUY
        "productType": "INTRADAY",
        "limitPrice": 0,
        "stopPrice": 0,
        "validity": "DAY",
        "disclosedQty": 0,
        "offlineOrder": False,
        "orderTag": "tag1",
        "isSliceOrder": False     # ✅ REQUIRED (Python boolean)
    }

    response = fyers.place_order(data=order_data)
    print("Order Response:", response)

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

    # ⚠️ ENABLE ONLY WHEN READY
    ENABLE_LIVE_ORDER = True

    if ENABLE_LIVE_ORDER:
        place_test_order(fyers)
    else:
        print("⚠️ Live order disabled")

if __name__ == "__main__":
    main()
