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

def place_ce_basket(fyers):
    """
    Basket:
    1 BUY CE (ATM)
    3 SELL CE (+200)
    2 BUY CE (+400)
    """

    UNDERLYING = "NIFTY"
    EXPIRY = "24JAN"
    ATM_STRIKE = 22000
    LOT_SIZE = 50
    PRODUCT = "INTRADAY"

    basket_orders = [
        {
            "symbol": f"NSE:{UNDERLYING}{EXPIRY}{ATM_STRIKE}CE",
            "qty": 1 * LOT_SIZE,
            "side": 1,   # BUY
            "tag": "BUY_ATM_CE"
        },
        {
            "symbol": f"NSE:{UNDERLYING}{EXPIRY}{ATM_STRIKE + 200}CE",
            "qty": 3 * LOT_SIZE,
            "side": -1,  # SELL
            "tag": "SELL_200_CE"
        },
        {
            "symbol": f"NSE:{UNDERLYING}{EXPIRY}{ATM_STRIKE + 400}CE",
            "qty": 2 * LOT_SIZE,
            "side": 1,   # BUY
            "tag": "BUY_400_CE"
        }
    ]

    order_ids = []

    for order in basket_orders:
        payload = {
            "symbol": order["symbol"],
            "qty": order["qty"],
            "type": 2,                 # MARKET
            "side": order["side"],
            "productType": PRODUCT,
            "limitPrice": 0,
            "stopPrice": 0,
            "validity": "DAY",
            "disclosedQty": 0,
            "offlineOrder": False,
            "orderTag": order["tag"],
            "isSliceOrder": False
        }

        response = fyers.place_order(data=payload)
        print(f"Order Response ({order['tag']}):", response)

        if response.get("s") == "ok":
            order_ids.append(response.get("id"))
        else:
            print("❌ Basket execution stopped due to failure")
            break

    return order_ids

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
        #basket_ids = place_ce_basket(fyers)
        #print("Basket Order IDs:", basket_ids)
    else:
        print("⚠️ Live order disabled")



if __name__ == "__main__":
    main()
