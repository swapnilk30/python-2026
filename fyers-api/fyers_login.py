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