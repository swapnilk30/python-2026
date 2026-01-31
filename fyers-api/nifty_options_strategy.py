
import os
import json
import yaml
from fyers_apiv3 import fyersModel
import pandas as pd
from datetime import datetime, time, timedelta
import time as time_module
import math


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
# STRATEGY CLASS
# ===============================

class NiftyOptionsStrategy:

    def __init__(self, fyers_client, config):
        """
        Initialize Nifty Options Strategy
        
        Args:
            fyers_client: Initialized Fyers API client
            config: Configuration dictionary from config.yaml
        """
        self.fyers = fyers_client
        self.config = config
        
        # Strategy parameters from config
        
        



# ===============================
# MAIN EXECUTION
# ===============================

def main():
    """
    Main function to run the strategy
    """
    print("\n" + "=" * 60)
    print("NIFTY OPTIONS STRATEGY - FYERS API")
    print("=" * 60)
    
    # Load configuration and credentials
    try:
        config = load_config()
        access_token = load_access_token()
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print("\nMake sure you have:")
        print("  1. config.yaml - with strategy parameters")
        print("  2. auth_tokens.json - with access_token")
        return
    
    # Get Fyers credentials from config
    client_id = config["fyers"]["client_id"]
    
    # Initialize Fyers client
    try:
        fyers = get_fyers_client(client_id, access_token)
        print("✓ Fyers client initialized")
    except Exception as e:
        print(f"❌ Error initializing Fyers client: {e}")
        return

    # Verify login
    try:
        profile = fyers.get_profile()
        print("Profile:", profile)
        #print(f"✓ Profile verified: {profile.get('data', {}).get('name', 'User')}")
    except Exception as e:
        print(f"❌ Error verifying profile: {e}")
        return

    # Initialize strategy
    strategy = NiftyOptionsStrategy(fyers, config)
    print("✓ Strategy initialized")


if __name__ == "__main__":
    main()