from fyers_apiv3 import fyersModel
from config import FYERS_CONFIG

def get_fyers_client():
    return fyersModel.FyersModel(
        client_id=FYERS_CONFIG["client_id"],
        token=FYERS_CONFIG["access_token"],
        log_path=""
    )
