"""
Nifty 50 Watchlist with Fyers Symbol Format
============================================

Fyers Symbol Format:
- Equity: NSE:SYMBOL-EQ (e.g., NSE:RELIANCE-EQ)
- Index: NSE:NIFTY50-INDEX
- Futures: NSE:SYMBOL24JANFUT (e.g., NSE:RELIANCE24JANFUT)
- Options: NSE:SYMBOL24JAN3000CE (e.g., NSE:NIFTY24JAN21000CE)
"""

import json
from typing import List, Dict, Any
from datetime import datetime

# ===============================
# NIFTY 50 CONSTITUENTS
# ===============================

NIFTY50_STOCKS = {
    # IT Sector
    "TCS": {"name": "Tata Consultancy Services", "sector": "IT", "lot_size": 150},
    "INFY": {"name": "Infosys", "sector": "IT", "lot_size": 300},
    "HCLTECH": {"name": "HCL Technologies", "sector": "IT", "lot_size": 550},
    "WIPRO": {"name": "Wipro", "sector": "IT", "lot_size": 1200},
    "TECHM": {"name": "Tech Mahindra", "sector": "IT", "lot_size": 725},
    "LTIM": {"name": "LTIMindtree", "sector": "IT", "lot_size": 150},
    
    # Banking & Financial Services
    "HDFCBANK": {"name": "HDFC Bank", "sector": "Banking", "lot_size": 550},
    "ICICIBANK": {"name": "ICICI Bank", "sector": "Banking", "lot_size": 1375},
    "SBIN": {"name": "State Bank of India", "sector": "Banking", "lot_size": 1500},
    "AXISBANK": {"name": "Axis Bank", "sector": "Banking", "lot_size": 1200},
    "KOTAKBANK": {"name": "Kotak Mahindra Bank", "sector": "Banking", "lot_size": 400},
    "INDUSINDBK": {"name": "IndusInd Bank", "sector": "Banking", "lot_size": 900},
    "BAJFINANCE": {"name": "Bajaj Finance", "sector": "NBFC", "lot_size": 125},
    "BAJAJFINSV": {"name": "Bajaj Finserv", "sector": "NBFC", "lot_size": 500},
    "HDFCLIFE": {"name": "HDFC Life Insurance", "sector": "Insurance", "lot_size": 900},
    "SBILIFE": {"name": "SBI Life Insurance", "sector": "Insurance", "lot_size": 600},
    
    # Energy & Oil
    "RELIANCE": {"name": "Reliance Industries", "sector": "Energy", "lot_size": 250},
    "ONGC": {"name": "Oil & Natural Gas Corp", "sector": "Energy", "lot_size": 3700},
    "BPCL": {"name": "Bharat Petroleum", "sector": "Energy", "lot_size": 1350},
    "ADANIPORTS": {"name": "Adani Ports & SEZ", "sector": "Infrastructure", "lot_size": 1100},
    "ADANIENT": {"name": "Adani Enterprises", "sector": "Conglomerate", "lot_size": 250},
    "POWERGRID": {"name": "Power Grid Corp", "sector": "Power", "lot_size": 3900},
    "NTPC": {"name": "NTPC", "sector": "Power", "lot_size": 3225},
    
    # Auto & Auto Components
    "MARUTI": {"name": "Maruti Suzuki", "sector": "Auto", "lot_size": 100},
    "M&M": {"name": "Mahindra & Mahindra", "sector": "Auto", "lot_size": 375},
    "TATAMOTORS": {"name": "Tata Motors", "sector": "Auto", "lot_size": 1650},
    "BAJAJ-AUTO": {"name": "Bajaj Auto", "sector": "Auto", "lot_size": 150},
    "EICHERMOT": {"name": "Eicher Motors", "sector": "Auto", "lot_size": 225},
    
    # FMCG
    "HINDUNILVR": {"name": "Hindustan Unilever", "sector": "FMCG", "lot_size": 300},
    "ITC": {"name": "ITC", "sector": "FMCG", "lot_size": 1600},
    "NESTLEIND": {"name": "Nestle India", "sector": "FMCG", "lot_size": 300},
    "BRITANNIA": {"name": "Britannia Industries", "sector": "FMCG", "lot_size": 200},
    "TATACONSUM": {"name": "Tata Consumer Products", "sector": "FMCG", "lot_size": 1050},
    
    # Pharma
    "SUNPHARMA": {"name": "Sun Pharmaceutical", "sector": "Pharma", "lot_size": 700},
    "DRREDDY": {"name": "Dr Reddy's Laboratories", "sector": "Pharma", "lot_size": 125},
    "CIPLA": {"name": "Cipla", "sector": "Pharma", "lot_size": 700},
    "APOLLOHOSP": {"name": "Apollo Hospitals", "sector": "Healthcare", "lot_size": 150},
    
    # Metals & Mining
    "TATASTEEL": {"name": "Tata Steel", "sector": "Metals", "lot_size": 6300},
    "HINDALCO": {"name": "Hindalco Industries", "sector": "Metals", "lot_size": 1800},
    "JSWSTEEL": {"name": "JSW Steel", "sector": "Metals", "lot_size": 1200},
    "COALINDIA": {"name": "Coal India", "sector": "Mining", "lot_size": 2700},
    
    # Cement & Construction
    "ULTRACEMCO": {"name": "UltraTech Cement", "sector": "Cement", "lot_size": 100},
    "GRASIM": {"name": "Grasim Industries", "sector": "Cement", "lot_size": 425},
    "LT": {"name": "Larsen & Toubro", "sector": "Construction", "lot_size": 300},
    
    # Telecom & Media
    "BHARTIARTL": {"name": "Bharti Airtel", "sector": "Telecom", "lot_size": 550},
    
    # Others
    "ASIANPAINT": {"name": "Asian Paints", "sector": "Paints", "lot_size": 300},
    "TITAN": {"name": "Titan Company", "sector": "Jewellery", "lot_size": 300},
    "HEROMOTOCO": {"name": "Hero MotoCorp", "sector": "Auto", "lot_size": 200},
}


# ===============================
# SYMBOL UTILITIES
# ===============================

class FyersSymbolHandler:
    """
    Handle Fyers symbol format conversions and utilities.
    """
    
    # Exchanges
    NSE = "NSE"
    BSE = "BSE"
    MCX = "MCX"
    
    # Instruments
    EQUITY = "EQ"
    INDEX = "INDEX"
    FUTURES = "FUT"
    CALL_OPTION = "CE"
    PUT_OPTION = "PE"
    
    @staticmethod
    def create_equity_symbol(symbol: str, exchange: str = "NSE") -> str:
        """
        Create equity symbol in Fyers format.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            exchange: Exchange name (default: 'NSE')
            
        Returns:
            Fyers formatted symbol (e.g., 'NSE:RELIANCE-EQ')
        """
        return f"{exchange}:{symbol}-{FyersSymbolHandler.EQUITY}"
    
    @staticmethod
    def create_index_symbol(index_name: str, exchange: str = "NSE") -> str:
        """
        Create index symbol in Fyers format.
        
        Args:
            index_name: Index name (e.g., 'NIFTY50', 'BANKNIFTY')
            exchange: Exchange name (default: 'NSE')
            
        Returns:
            Fyers formatted symbol (e.g., 'NSE:NIFTY50-INDEX')
        """
        return f"{exchange}:{index_name}-{FyersSymbolHandler.INDEX}"
    
    @staticmethod
    def create_future_symbol(symbol: str, expiry: str, exchange: str = "NSE") -> str:
        """
        Create futures symbol in Fyers format.
        
        Args:
            symbol: Stock/Index symbol
            expiry: Expiry in format YYMONTH (e.g., '24JAN', '24FEB')
            exchange: Exchange name (default: 'NSE')
            
        Returns:
            Fyers formatted symbol (e.g., 'NSE:RELIANCE24JANFUT')
        """
        return f"{exchange}:{symbol}{expiry}{FyersSymbolHandler.FUTURES}"
    
    @staticmethod
    def create_option_symbol(
        symbol: str, 
        expiry: str, 
        strike: int, 
        option_type: str, 
        exchange: str = "NSE"
    ) -> str:
        """
        Create option symbol in Fyers format.
        
        Args:
            symbol: Stock/Index symbol
            expiry: Expiry in format YYMONTH (e.g., '24JAN')
            strike: Strike price
            option_type: 'CE' for Call, 'PE' for Put
            exchange: Exchange name (default: 'NSE')
            
        Returns:
            Fyers formatted symbol (e.g., 'NSE:NIFTY24JAN21000CE')
        """
        return f"{exchange}:{symbol}{expiry}{strike}{option_type}"
    
    @staticmethod
    def parse_symbol(fyers_symbol: str) -> Dict[str, Any]:
        """
        Parse a Fyers symbol into components.
        
        Args:
            fyers_symbol: Fyers formatted symbol
            
        Returns:
            Dictionary with symbol components
        """
        parts = fyers_symbol.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid Fyers symbol format: {fyers_symbol}")
        
        exchange = parts[0]
        symbol_part = parts[1]
        
        result = {
            "exchange": exchange,
            "original": fyers_symbol
        }
        
        # Check for equity
        if symbol_part.endswith("-EQ"):
            result["symbol"] = symbol_part.replace("-EQ", "")
            result["instrument"] = "EQUITY"
        
        # Check for index
        elif symbol_part.endswith("-INDEX"):
            result["symbol"] = symbol_part.replace("-INDEX", "")
            result["instrument"] = "INDEX"
        
        # Check for futures
        elif "FUT" in symbol_part:
            result["instrument"] = "FUTURE"
            # More complex parsing needed for expiry
        
        # Check for options
        elif "CE" in symbol_part or "PE" in symbol_part:
            result["instrument"] = "OPTION"
            # More complex parsing needed
        
        return result
    
    @staticmethod
    def get_current_month_code() -> str:
        """
        Get current month code for futures/options.
        
        Returns:
            Month code (e.g., '24JAN', '24FEB')
        """
        now = datetime.now()
        year = str(now.year)[2:]  # Last 2 digits
        month = now.strftime("%b").upper()  # 3-letter month
        return f"{year}{month}"


# ===============================
# WATCHLIST GENERATOR
# ===============================

class Nifty50Watchlist:
    """
    Generate Nifty 50 watchlist in various formats.
    """
    
    @staticmethod
    def get_equity_symbols() -> List[str]:
        """
        Get all Nifty 50 stocks in Fyers equity format.
        
        Returns:
            List of Fyers equity symbols
        """
        return [
            FyersSymbolHandler.create_equity_symbol(symbol)
            for symbol in NIFTY50_STOCKS.keys()
        ]
    
    @staticmethod
    def get_symbols_by_sector(sector: str) -> List[str]:
        """
        Get stocks by sector in Fyers format.
        
        Args:
            sector: Sector name (e.g., 'IT', 'Banking')
            
        Returns:
            List of Fyers symbols in that sector
        """
        return [
            FyersSymbolHandler.create_equity_symbol(symbol)
            for symbol, data in NIFTY50_STOCKS.items()
            if data["sector"] == sector
        ]
    
    @staticmethod
    def get_all_sectors() -> List[str]:
        """
        Get unique list of all sectors.
        
        Returns:
            List of sector names
        """
        return sorted(list(set(data["sector"] for data in NIFTY50_STOCKS.values())))
    
    @staticmethod
    def get_symbol_info(symbol: str) -> Dict[str, Any]:
        """
        Get information about a symbol.
        
        Args:
            symbol: Stock symbol (without exchange prefix)
            
        Returns:
            Dictionary with symbol information
        """
        if symbol in NIFTY50_STOCKS:
            info = NIFTY50_STOCKS[symbol].copy()
            info["fyers_symbol"] = FyersSymbolHandler.create_equity_symbol(symbol)
            info["symbol"] = symbol
            return info
        return None
    
    @staticmethod
    def export_to_json(filepath: str = "nifty50_watchlist.json") -> None:
        """
        Export watchlist to JSON file.
        
        Args:
            filepath: Path to save JSON file
        """
        watchlist = {
            "index": {
                "nifty50": FyersSymbolHandler.create_index_symbol("NIFTY50"),
                "banknifty": FyersSymbolHandler.create_index_symbol("BANKNIFTY"),
            },
            "stocks": {},
            "by_sector": {}
        }
        
        # Add all stocks
        for symbol, data in NIFTY50_STOCKS.items():
            watchlist["stocks"][symbol] = {
                "fyers_symbol": FyersSymbolHandler.create_equity_symbol(symbol),
                "name": data["name"],
                "sector": data["sector"],
                "lot_size": data["lot_size"]
            }
        
        # Group by sector
        for sector in Nifty50Watchlist.get_all_sectors():
            watchlist["by_sector"][sector] = Nifty50Watchlist.get_symbols_by_sector(sector)
        
        with open(filepath, "w") as f:
            json.dump(watchlist, f, indent=2)
        
        print(f"✓ Watchlist exported to {filepath}")
    
    @staticmethod
    def print_watchlist() -> None:
        """
        Print formatted watchlist to console.
        """
        print("=" * 80)
        print("NIFTY 50 WATCHLIST - FYERS FORMAT")
        print("=" * 80)
        print()
        
        # Print indices
        print("📊 INDICES:")
        print(f"  • Nifty 50: {FyersSymbolHandler.create_index_symbol('NIFTY50')}")
        print(f"  • Bank Nifty: {FyersSymbolHandler.create_index_symbol('BANKNIFTY')}")
        print()
        
        # Print by sector
        for sector in Nifty50Watchlist.get_all_sectors():
            symbols = [s for s, d in NIFTY50_STOCKS.items() if d["sector"] == sector]
            print(f"📁 {sector.upper()} ({len(symbols)} stocks):")
            for symbol in sorted(symbols):
                fyers_symbol = FyersSymbolHandler.create_equity_symbol(symbol)
                name = NIFTY50_STOCKS[symbol]["name"]
                print(f"  • {fyers_symbol:25} | {name}")
            print()


# ===============================
# EXAMPLE USAGE
# ===============================

def main():
    """
    Example usage of Nifty 50 watchlist utilities.
    """
    # Print full watchlist
    Nifty50Watchlist.print_watchlist()
    
    # Get all equity symbols
    print("\n" + "=" * 80)
    print("ALL EQUITY SYMBOLS (for WebSocket/API):")
    print("=" * 80)
    equity_symbols = Nifty50Watchlist.get_equity_symbols()
    print(f"Total symbols: {len(equity_symbols)}")
    print(json.dumps(equity_symbols[:5], indent=2))  # Show first 5
    print("...")
    print()
    
    # Get IT sector stocks
    print("=" * 80)
    print("IT SECTOR STOCKS:")
    print("=" * 80)
    it_stocks = Nifty50Watchlist.get_symbols_by_sector("IT")
    for stock in it_stocks:
        print(f"  • {stock}")
    print()
    
    # Symbol examples
    print("=" * 80)
    print("SYMBOL FORMAT EXAMPLES:")
    print("=" * 80)
    
    # Equity
    print("\n1. EQUITY:")
    print(f"   {FyersSymbolHandler.create_equity_symbol('RELIANCE')}")
    
    # Index
    print("\n2. INDEX:")
    print(f"   {FyersSymbolHandler.create_index_symbol('NIFTY50')}")
    
    # Futures
    print("\n3. FUTURES:")
    current_month = FyersSymbolHandler.get_current_month_code()
    print(f"   {FyersSymbolHandler.create_future_symbol('RELIANCE', current_month)}")
    print(f"   {FyersSymbolHandler.create_future_symbol('NIFTY', current_month)}")
    
    # Options
    print("\n4. OPTIONS:")
    print(f"   {FyersSymbolHandler.create_option_symbol('NIFTY', current_month, 21000, 'CE')}")
    print(f"   {FyersSymbolHandler.create_option_symbol('NIFTY', current_month, 21000, 'PE')}")
    print()
    
    # Export to JSON
    Nifty50Watchlist.export_to_json()
    
    # Get symbol info
    print("\n" + "=" * 80)
    print("SYMBOL INFO EXAMPLE:")
    print("=" * 80)
    info = Nifty50Watchlist.get_symbol_info("RELIANCE")
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()