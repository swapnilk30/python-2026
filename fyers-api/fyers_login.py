import os
import json
import base64
import warnings
import requests
import yaml
import pytz
import pyotp
import pandas as pd

from urllib.parse import parse_qs, urlparse
from datetime import datetime, timedelta
from time import sleep
from fyers_apiv3 import fyersModel

# ==============================
# GLOBAL CONFIG
# ==============================
warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", None)

CONFIG_FILE = "Config.yaml"
TOKEN_FILE = "auth_tokens.json"
TIMEZONE = pytz.timezone("Asia/Kolkata")

# ==============================
# CONFIG & TOKEN HANDLING
# ==============================

def load_config(path: str = CONFIG_FILE) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def save_tokens(auth_code: str, access_token: str, path: str = TOKEN_FILE):
    with open(path, "w") as f:
        json.dump(
            {"auth_code": auth_code, "access_token": access_token},
            f,
            indent=4
        )


def read_tokens(path: str = TOKEN_FILE):
    if not os.path.exists(path):
        return None, None

    with open(path, "r") as f:
        data = json.load(f)
        return data.get("auth_code"), data.get("access_token")

# ==============================
# FYERS AUTH HELPERS
# ==============================

def _b64_encode(value: str) -> str:
    return base64.b64encode(str(value).encode("ascii")).decode("ascii")


def send_login_otp(username: str) -> dict:
    url = "https://api-t2.fyers.in/vagator/v2/send_login_otp_v2"
    payload = {"fy_id": _b64_encode(username), "app_id": "2"}
    return _post(url, payload)


def verify_otp(request_key: str, totp_token: str) -> dict:
    otp = pyotp.TOTP(totp_token).now()
    url = "https://api-t2.fyers.in/vagator/v2/verify_otp"
    payload = {"request_key": request_key, "otp": otp}
    return _post(url, payload)


def verify_pin(request_key: str, pin: str) -> dict:
    url = "https://api-t2.fyers.in/vagator/v2/verify_pin_v2"
    payload = {
        "request_key": request_key,
        "identity_type": "pin",
        "identifier": _b64_encode(pin)
    }
    return _post(url, payload)


def generate_auth_code(session: requests.Session, payload: dict) -> str:
    url = "https://api-t1.fyers.in/api/v3/token"
    response = session.post(url, json=payload).json()
    return extract_auth_code(response["Url"])


def extract_auth_code(url: str) -> str:
    parsed = urlparse(url)
    return parse_qs(parsed.query)["auth_code"][0]


def generate_access_token(
    auth_code: str,
    client_id: str,
    secret_key: str,
    redirect_uri: str
) -> str:
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type="code",
        grant_type="authorization_code"
    )
    session.set_token(auth_code)
    return session.generate_token()["access_token"]

# ==============================
# FYERS CLIENT
# ==============================

def create_fyers_client(client_id: str, access_token: str):
    return fyersModel.FyersModel(
        client_id=client_id,
        token=access_token,
        is_async=False,
        log_path=os.getcwd()
    )

# ==============================
# MARKET DATA HELPERS
# ==============================

def fetch_candles(fyers, symbol: str, days: int = 2) -> pd.DataFrame:
    payload = {
        "symbol": symbol,
        "resolution": "1",
        "date_format": "1",
        "range_from": str((datetime.now() - timedelta(days=days)).date()),
        "range_to": str(datetime.now().date()),
        "cont_flag": "1"
    }

    response = fyers.history(data=payload)
    df = pd.DataFrame(
        response["candles"],
        columns=["date", "open", "high", "low", "close", "volume"]
    )

    df["date"] = pd.to_datetime(df["date"], unit="s").dt.tz_localize("UTC").dt.tz_convert(TIMEZONE)
    return df.sort_values("date")

# ==============================
# HTTP UTILS
# ==============================

def _post(url: str, payload: dict) -> dict:
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"API Error {response.status_code}: {response.text}")
    return response.json()

# ==============================
# MAIN FLOW
# ==============================

def main():
    config = load_config()

    fy = config["fyers"]
    username = fy["username"]
    pin = fy["pin"]
    totp = fy["token"]
    client_id = fy["client_id"]
    secret_key = fy["secret_key"]
    redirect_uri = fy["redirect_uri"]

    # --- LOGIN FLOW ---
    otp_resp = send_login_otp(username)
    otp_verify = verify_otp(otp_resp["request_key"], totp)
    pin_verify = verify_pin(otp_verify["request_key"], pin)

    bearer_token = pin_verify["data"]["access_token"]
    session = requests.Session()
    session.headers.update({"authorization": f"Bearer {bearer_token}"})

    auth_payload = {
        "fyers_id": username,
        "app_id": client_id[:-4],
        "redirect_uri": redirect_uri,
        "appType": "100",
        "response_type": "code",
        "create_cookie": True
    }

    auth_code = generate_auth_code(session, auth_payload)
    access_token = generate_access_token(auth_code, client_id, secret_key, redirect_uri)

    save_tokens(auth_code, access_token)

    # --- FYERS CLIENT ---
    fyers = create_fyers_client(client_id, access_token)

    print("Profile:", fyers.get_profile())
    print("Funds:", fyers.funds())
    print("Holdings:", fyers.holdings())
    print("Trades:", fyers.tradebook())

    print("Quotes:", fyers.quotes({"symbols": "NSE:SBIN-EQ,NSE:IDEA-EQ"}))

    candles = fetch_candles(fyers, "NSE:SBIN-EQ")
    print(candles)

    print("✅ FYERS Login Successful")

# ==============================
# ENTRY POINT
# ==============================

if __name__ == "__main__":
    main()
