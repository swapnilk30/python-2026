import os
import json
import pytz
from urllib import response
import yaml
from fyers_apiv3 import fyersModel
import pandas as pd


from datetime import datetime, timedelta

TIMEZONE = pytz.timezone("Asia/Kolkata")

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

    data = {"symbols":"NSE:SBIN-EQ,NSE:IDEA-EQ"}
    response = fyers.quotes(data=data)
    print(response)

    data = {
    "symbol":"NSE:SBIN-EQ",
    "resolution":"1",
    "date_format":"1",
    "range_from": str((datetime.now() - timedelta(days=5)).date()),#yyyy-mm-dd
    "range_to": str(datetime.now().date()),
    "cont_flag":"1"
    }

    response = fyers.history(data=data)
    df = pd.DataFrame(response["candles"],columns=["date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"], unit="s").dt.tz_localize("UTC").dt.tz_convert(TIMEZONE)
    print(df.sort_values("date"))


if __name__ == "__main__":
    main()