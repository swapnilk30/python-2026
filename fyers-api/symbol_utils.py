"""
Fyers Symbol Utilities
======================

Comprehensive utilities for handling Fyers symbols:
- Validation
- Conversion
- Bulk operations
- Symbol search
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum


# ===============================
# ENUMS
# ===============================

class Exchange(Enum):
    """Supported exchanges."""
    NSE = "NSE"
    BSE = "BSE"
    MCX = "MCX"
    CDS = "CDS"


class Instrument(Enum):
    """Supported instrument types."""
    EQUITY = "EQ"
    INDEX = "INDEX"
    FUTURE = "FUT"
    CALL = "CE"
    PUT = "PE"
    CURRENCY = "CUR"
    COMMODITY = "COM"


# ===============================
# SYMBOL VALIDATOR
# ===============================

class SymbolValidator:
    """
    Validate Fyers symbols.
    """
    
    # Regex patterns
    EQUITY_PATTERN = r'^(NSE|BSE):[A-Z0-9&\-]+-(EQ)$'
    INDEX_PATTERN = r'^(NSE|BSE):[A-Z0-9]+-(INDEX)$'
    FUTURE_PATTERN = r'^(NSE|BSE|MCX):[A-Z0-9]+\d{2}[A-Z]{3}(FUT)$'
    OPTION_PATTERN = r'^(NSE|BSE):[A-Z0-9]+\d{2}[A-Z]{3}\d+[CP]E$'
    
    @staticmethod
    def is_valid_equity(symbol: str) -> bool:
        """Check if symbol is valid equity format."""
        return bool(re.match(SymbolValidator.EQUITY_PATTERN, symbol))
    
    @staticmethod
    def is_valid_index(symbol: str) -> bool:
        """Check if symbol is valid index format."""
        return bool(re.match(SymbolValidator.INDEX_PATTERN, symbol))
    
    @staticmethod
    def is_valid_future(symbol: str) -> bool:
        """Check if symbol is valid future format."""
        return bool(re.match(SymbolValidator.FUTURE_PATTERN, symbol))
    
    @staticmethod
    def is_valid_option(symbol: str) -> bool:
        """Check if symbol is valid option format."""
        return bool(re.match(SymbolValidator.OPTION_PATTERN, symbol))
    
    @staticmethod
    def is_valid(symbol: str) -> bool:
        """Check if symbol is in valid Fyers format."""
        return (
            SymbolValidator.is_valid_equity(symbol) or
            SymbolValidator.is_valid_index(symbol) or
            SymbolValidator.is_valid_future(symbol) or
            SymbolValidator.is_valid_option(symbol)
        )
    
    @staticmethod
    def get_instrument_type(symbol: str) -> Optional[str]:
        """Identify instrument type from symbol."""
        if SymbolValidator.is_valid_equity(symbol):
            return "EQUITY"
        elif SymbolValidator.is_valid_index(symbol):
            return "INDEX"
        elif SymbolValidator.is_valid_future(symbol):
            return "FUTURE"
        elif SymbolValidator.is_valid_option(symbol):
            return "OPTION"
        return None


# ===============================
# SYMBOL CONVERTER
# ===============================

class SymbolConverter:
    """
    Convert between different symbol formats.
    """
    
    @staticmethod
    def to_fyers(
        symbol: str, 
        exchange: str = "NSE", 
        instrument: str = "EQ"
    ) -> str:
        """
        Convert plain symbol to Fyers format.
        
        Args:
            symbol: Base symbol (e.g., 'RELIANCE')
            exchange: Exchange (e.g., 'NSE')
            instrument: Instrument type (e.g., 'EQ')
        
        Returns:
            Fyers formatted symbol
        """
        return f"{exchange}:{symbol}-{instrument}"
    
    @staticmethod
    def from_fyers(fyers_symbol: str) -> Dict[str, str]:
        """
        Parse Fyers symbol into components.
        
        Args:
            fyers_symbol: Fyers formatted symbol
        
        Returns:
            Dictionary with components
        """
        if ':' not in fyers_symbol:
            raise ValueError(f"Invalid Fyers symbol: {fyers_symbol}")
        
        exchange, rest = fyers_symbol.split(':', 1)
        
        result = {
            "exchange": exchange,
            "fyers_symbol": fyers_symbol
        }
        
        # Parse based on instrument type
        if '-EQ' in rest:
            result["symbol"] = rest.replace('-EQ', '')
            result["instrument"] = "EQUITY"
        
        elif '-INDEX' in rest:
            result["symbol"] = rest.replace('-INDEX', '')
            result["instrument"] = "INDEX"
        
        elif 'FUT' in rest:
            result["instrument"] = "FUTURE"
            # Extract base symbol and expiry
            match = re.match(r'([A-Z0-9]+)(\d{2}[A-Z]{3})FUT', rest)
            if match:
                result["symbol"] = match.group(1)
                result["expiry"] = match.group(2)
        
        elif re.search(r'\d+[CP]E$', rest):
            result["instrument"] = "OPTION"
            # Extract components
            match = re.match(r'([A-Z0-9]+)(\d{2}[A-Z]{3})(\d+)([CP]E)', rest)
            if match:
                result["symbol"] = match.group(1)
                result["expiry"] = match.group(2)
                result["strike"] = int(match.group(3))
                result["option_type"] = match.group(4)
        
        return result
    
    @staticmethod
    def nse_to_bse(nse_symbol: str) -> str:
        """Convert NSE symbol to BSE."""
        if not nse_symbol.startswith("NSE:"):
            raise ValueError("Not an NSE symbol")
        return nse_symbol.replace("NSE:", "BSE:")
    
    @staticmethod
    def bse_to_nse(bse_symbol: str) -> str:
        """Convert BSE symbol to NSE."""
        if not bse_symbol.startswith("BSE:"):
            raise ValueError("Not a BSE symbol")
        return bse_symbol.replace("BSE:", "NSE:")


# ===============================
# BULK OPERATIONS
# ===============================

class BulkSymbolOperations:
    """
    Perform operations on multiple symbols.
    """
    
    @staticmethod
    def convert_list_to_fyers(
        symbols: List[str], 
        exchange: str = "NSE", 
        instrument: str = "EQ"
    ) -> List[str]:
        """
        Convert list of symbols to Fyers format.
        
        Args:
            symbols: List of base symbols
            exchange: Exchange
            instrument: Instrument type
        
        Returns:
            List of Fyers formatted symbols
        """
        return [
            SymbolConverter.to_fyers(s, exchange, instrument)
            for s in symbols
        ]
    
    @staticmethod
    def validate_list(symbols: List[str]) -> Dict[str, List[str]]:
        """
        Validate a list of symbols.
        
        Args:
            symbols: List of Fyers symbols
        
        Returns:
            Dictionary with valid and invalid symbols
        """
        valid = []
        invalid = []
        
        for symbol in symbols:
            if SymbolValidator.is_valid(symbol):
                valid.append(symbol)
            else:
                invalid.append(symbol)
        
        return {
            "valid": valid,
            "invalid": invalid,
            "valid_count": len(valid),
            "invalid_count": len(invalid)
        }
    
    @staticmethod
    def group_by_exchange(symbols: List[str]) -> Dict[str, List[str]]:
        """
        Group symbols by exchange.
        
        Args:
            symbols: List of Fyers symbols
        
        Returns:
            Dictionary grouped by exchange
        """
        grouped = {}
        
        for symbol in symbols:
            exchange = symbol.split(':')[0] if ':' in symbol else 'UNKNOWN'
            if exchange not in grouped:
                grouped[exchange] = []
            grouped[exchange].append(symbol)
        
        return grouped
    
    @staticmethod
    def group_by_instrument(symbols: List[str]) -> Dict[str, List[str]]:
        """
        Group symbols by instrument type.
        
        Args:
            symbols: List of Fyers symbols
        
        Returns:
            Dictionary grouped by instrument
        """
        grouped = {
            "EQUITY": [],
            "INDEX": [],
            "FUTURE": [],
            "OPTION": [],
            "UNKNOWN": []
        }
        
        for symbol in symbols:
            inst_type = SymbolValidator.get_instrument_type(symbol)
            if inst_type:
                grouped[inst_type].append(symbol)
            else:
                grouped["UNKNOWN"].append(symbol)
        
        return grouped
    
    @staticmethod
    def filter_by_instrument(
        symbols: List[str], 
        instrument_type: str
    ) -> List[str]:
        """
        Filter symbols by instrument type.
        
        Args:
            symbols: List of Fyers symbols
            instrument_type: Type to filter (EQUITY/INDEX/FUTURE/OPTION)
        
        Returns:
            Filtered list
        """
        return [
            s for s in symbols 
            if SymbolValidator.get_instrument_type(s) == instrument_type
        ]


# ===============================
# EXPIRY UTILITIES
# ===============================

class ExpiryUtils:
    """
    Utilities for handling expiry dates.
    """
    
    MONTH_CODES = {
        1: "JAN", 2: "FEB", 3: "MAR", 4: "APR",
        5: "MAY", 6: "JUN", 7: "JUL", 8: "AUG",
        9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"
    }
    
    @staticmethod
    def get_current_expiry_code() -> str:
        """
        Get current month expiry code.
        
        Returns:
            Expiry code (e.g., '24JAN')
        """
        now = datetime.now()
        year = str(now.year)[2:]
        month = ExpiryUtils.MONTH_CODES[now.month]
        return f"{year}{month}"
    
    @staticmethod
    def get_next_expiry_code() -> str:
        """
        Get next month expiry code.
        
        Returns:
            Expiry code (e.g., '24FEB')
        """
        now = datetime.now()
        next_month = now.replace(day=28) + timedelta(days=4)
        year = str(next_month.year)[2:]
        month = ExpiryUtils.MONTH_CODES[next_month.month]
        return f"{year}{month}"
    
    @staticmethod
    def get_expiry_code(year: int, month: int) -> str:
        """
        Get expiry code for specific year and month.
        
        Args:
            year: Year (e.g., 2024)
            month: Month (1-12)
        
        Returns:
            Expiry code
        """
        year_code = str(year)[2:]
        month_code = ExpiryUtils.MONTH_CODES[month]
        return f"{year_code}{month_code}"
    
    @staticmethod
    def parse_expiry_code(expiry_code: str) -> Dict[str, int]:
        """
        Parse expiry code into year and month.
        
        Args:
            expiry_code: Expiry code (e.g., '24JAN')
        
        Returns:
            Dictionary with year and month
        """
        if len(expiry_code) != 5:
            raise ValueError(f"Invalid expiry code: {expiry_code}")
        
        year_code = expiry_code[:2]
        month_code = expiry_code[2:]
        
        # Get year
        year = 2000 + int(year_code)
        
        # Get month
        month = None
        for m, code in ExpiryUtils.MONTH_CODES.items():
            if code == month_code:
                month = m
                break
        
        if month is None:
            raise ValueError(f"Invalid month code: {month_code}")
        
        return {"year": year, "month": month}


# ===============================
# SYMBOL SEARCH
# ===============================

class SymbolSearch:
    """
    Search and filter symbols.
    """
    
    @staticmethod
    def search_by_pattern(
        symbols: List[str], 
        pattern: str
    ) -> List[str]:
        """
        Search symbols by regex pattern.
        
        Args:
            symbols: List of symbols to search
            pattern: Regex pattern
        
        Returns:
            Matching symbols
        """
        compiled = re.compile(pattern, re.IGNORECASE)
        return [s for s in symbols if compiled.search(s)]
    
    @staticmethod
    def search_by_keyword(
        symbols: List[str], 
        keyword: str
    ) -> List[str]:
        """
        Search symbols by keyword.
        
        Args:
            symbols: List of symbols
            keyword: Keyword to search
        
        Returns:
            Matching symbols
        """
        keyword_upper = keyword.upper()
        return [s for s in symbols if keyword_upper in s.upper()]
    
    @staticmethod
    def get_base_symbol(fyers_symbol: str) -> str:
        """
        Extract base symbol from Fyers symbol.
        
        Args:
            fyers_symbol: Fyers formatted symbol
        
        Returns:
            Base symbol
        """
        parsed = SymbolConverter.from_fyers(fyers_symbol)
        return parsed.get("symbol", "")


# ===============================
# EXAMPLE USAGE
# ===============================

def main():
    """Example usage of symbol utilities."""
    
    print("=" * 80)
    print("SYMBOL UTILITIES EXAMPLES")
    print("=" * 80)
    
    # 1. Validation
    print("\n1. SYMBOL VALIDATION:")
    symbols_to_validate = [
        "NSE:RELIANCE-EQ",
        "NSE:NIFTY50-INDEX",
        "NSE:RELIANCE24JANFUT",
        "NSE:NIFTY24JAN21000CE",
        "INVALID_SYMBOL"
    ]
    
    for symbol in symbols_to_validate:
        is_valid = SymbolValidator.is_valid(symbol)
        inst_type = SymbolValidator.get_instrument_type(symbol)
        print(f"  {symbol:30} Valid: {is_valid:5} Type: {inst_type}")
    
    # 2. Conversion
    print("\n2. SYMBOL CONVERSION:")
    fyers_symbol = "NSE:RELIANCE-EQ"
    parsed = SymbolConverter.from_fyers(fyers_symbol)
    print(f"  Parsed: {parsed}")
    
    # 3. Bulk operations
    print("\n3. BULK OPERATIONS:")
    symbols = ["RELIANCE", "TCS", "INFY"]
    fyers_symbols = BulkSymbolOperations.convert_list_to_fyers(symbols)
    print(f"  Converted: {fyers_symbols}")
    
    # 4. Expiry utilities
    print("\n4. EXPIRY UTILITIES:")
    current_expiry = ExpiryUtils.get_current_expiry_code()
    next_expiry = ExpiryUtils.get_next_expiry_code()
    print(f"  Current expiry: {current_expiry}")
    print(f"  Next expiry: {next_expiry}")
    
    parsed_expiry = ExpiryUtils.parse_expiry_code(current_expiry)
    print(f"  Parsed: {parsed_expiry}")
    
    # 5. Search
    print("\n5. SYMBOL SEARCH:")
    all_symbols = [
        "NSE:RELIANCE-EQ",
        "NSE:RELIANCEIND-EQ",
        "NSE:TCS-EQ",
        "NSE:INFY-EQ"
    ]
    results = SymbolSearch.search_by_keyword(all_symbols, "RELIANCE")
    print(f"  Search 'RELIANCE': {results}")


if __name__ == "__main__":
    main()