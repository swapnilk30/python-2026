import pandas as pd
from datetime import datetime, timedelta
from services.fyers_client import get_fyers_client
from config import MARKET_CONFIG

def fetch_nifty_ohlc():
    fyers = get_fyers_client()

    to_dt = datetime.now()
    from_dt = to_dt - timedelta(days=MARKET_CONFIG["history_days"])

    payload = {
        "symbol": MARKET_CONFIG["symbol"],
        "resolution": MARKET_CONFIG["resolution"],
        "date_format": "1",
        "range_from": from_dt.strftime("%Y-%m-%d"),
        "range_to": to_dt.strftime("%Y-%m-%d"),
        "cont_flag": "1"
    }

    response = fyers.history(data=payload)

    df = pd.DataFrame(
        response["candles"],
        columns=["ts", "open", "high", "low", "close", "volume"]
    )

    df["datetime"] = pd.to_datetime(df["ts"], unit="s")
    return df
