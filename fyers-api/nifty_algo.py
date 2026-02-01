# ============================================================
# NIFTY RSI Scheduler Algo
# Config-driven | Logging enabled | FYERS compatible
# ============================================================

# =========================
# IMPORTS
# =========================
import os
import json
import yaml
import time
import logging
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta, time as dtime

from fyers_apiv3 import fyersModel
from strategy_config import TIMEFRAME_PROFILES


# =========================
# LOGGING SETUP
# =========================
def setup_logger():
    logger = logging.getLogger("nifty_algo")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    # File handler
    fh = logging.FileHandler("algo.log")
    fh.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger


logger = setup_logger()


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


# =========================
# APPLY TIMEFRAME CONFIG
# =========================
def apply_timeframe_config(cfg, timeframe):
    tf_cfg = TIMEFRAME_PROFILES[timeframe]

    cfg["indicator"]["timeframe"] = tf_cfg["resolution"]
    cfg["indicator"]["entry_level"] = tf_cfg["rsi_level"]
    cfg["scheduler"] = {
        "candle_closes": tf_cfg["candle_closes"]
    }
    return cfg


# =========================
# MARKET HOURS
# =========================
def is_market_open():
    now = datetime.now().time()
    return dtime(9, 15) <= now <= dtime(15, 30)


# =========================
# NEXT CANDLE CLOSE
# =========================
def next_candle_close(close_times):
    now = datetime.now()
    today = now.date()

    for t in close_times:
        hh, mm = map(int, t.split(":"))
        close_dt = datetime.combine(today, dtime(hh, mm))
        if now < close_dt:
            return close_dt

    hh, mm = map(int, close_times[0].split(":"))
    return datetime.combine(today + timedelta(days=1), dtime(hh, mm))


# =========================
# MARKET DATA
# =========================
def fetch_candles(fyers, symbol, timeframe, days):
    to_dt = datetime.now()
    from_dt = to_dt - timedelta(days=days)

    payload = {
        "symbol": symbol,
        "resolution": timeframe,
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
    return df


# =========================
# INDICATOR
# =========================
def compute_rsi(df, length):
    df["rsi"] = ta.rsi(df["close"], length=length)
    return df.iloc[-1]["rsi"], df.iloc[-1]["close"]


# =========================
# STRATEGY LOGIC
# =========================
def run_strategy(cfg, fyers):
    logger.info(f"Running strategy | TF={cfg['active_timeframe']}")

    df = fetch_candles(
        fyers,
        cfg["symbol"]["index"],
        cfg["indicator"]["timeframe"],
        cfg["data"]["history_days"]
    )

    rsi, spot = compute_rsi(df, cfg["indicator"]["length"])
    logger.info(f"Market Data | RSI={rsi:.2f} | Spot={spot}")


# =========================
# SCHEDULER
# =========================
def run_scheduler(cfg, fyers):
    close_times = cfg["scheduler"]["candle_closes"]
    logger.info(f"Scheduler started | TF={cfg['active_timeframe']}")

    while True:
        next_run = next_candle_close(close_times)
        sleep_sec = (next_run - datetime.now()).total_seconds()

        logger.info(f"Next candle close at {next_run.strftime('%H:%M')}")

        if sleep_sec > 0:
            time.sleep(sleep_sec)

        if is_market_open():
            try:
                run_strategy(cfg, fyers)
            except Exception:
                logger.exception("Strategy execution failed")

        time.sleep(10)


# =========================
# MAIN
# =========================
if __name__ == "__main__":

    # Load configs
    config = load_config()
    access_token = load_access_token()

    # Build runtime CONFIG
    CONFIG = {
        "active_timeframe": config["active_timeframe"],
        "symbol": config["symbol"],
        "indicator": config["indicator"],
        "data": config["data"],
        "scheduler": {}
    }

    # Apply timeframe profile
    CONFIG = apply_timeframe_config(CONFIG, CONFIG["active_timeframe"])

    # Create FYERS client
    client_id = config["fyers"]["client_id"]
    fyers = get_fyers_client(client_id, access_token)

    # Start scheduler
    run_scheduler(CONFIG, fyers)
