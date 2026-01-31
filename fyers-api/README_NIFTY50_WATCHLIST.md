# Nifty 50 Watchlist & Fyers Symbol Handler

Complete toolkit for handling Nifty 50 stocks with Fyers API symbol format.

## 📋 Table of Contents

- [Fyers Symbol Format](#fyers-symbol-format)
- [Files Overview](#files-overview)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Nifty 50 Constituents](#nifty-50-constituents)
- [Advanced Features](#advanced-features)

---

## 🔤 Fyers Symbol Format

Fyers uses a specific format for symbols:

### Format Structure
```
EXCHANGE:SYMBOL-INSTRUMENT
```

### Examples

| Type | Format | Example |
|------|--------|---------|
| **Equity** | `NSE:SYMBOL-EQ` | `NSE:RELIANCE-EQ` |
| **Index** | `NSE:INDEX-INDEX` | `NSE:NIFTY50-INDEX` |
| **Futures** | `NSE:SYMBOLYYMONFut` | `NSE:RELIANCE26JANFUT` |
| **Call Option** | `NSE:SYMBOLYYMON\<STRIKE\>CE` | `NSE:NIFTY26JAN21000CE` |
| **Put Option** | `NSE:SYMBOLYYMON\<STRIKE\>PE` | `NSE:NIFTY26JAN21000PE` |

### Key Rules

✅ **Always include:**
- Exchange prefix (`NSE:` or `BSE:`)
- Proper suffix (`-EQ`, `-INDEX`, `FUT`, `CE`, `PE`)

❌ **Don't use:**
- Plain symbols without exchange
- Incorrect separators
- Missing suffixes

---

## 📁 Files Overview

### 1. `nifty50_watchlist.py`
Complete Nifty 50 stock list with:
- All 50 constituent stocks
- Sector classification
- Lot sizes for F&O
- Symbol generation utilities
- Export to JSON

**Key Features:**
- `NIFTY50_STOCKS` - Dictionary with all stock details
- `FyersSymbolHandler` - Convert symbols to Fyers format
- `Nifty50Watchlist` - Generate watchlists by various criteria

### 2. `market_data_stream.py`
WebSocket streaming for live market data:
- Real-time price updates
- Quote data (LTP, Volume, OHLC)
- Order book depth
- Multiple watchlist strategies

**Key Features:**
- Stream live data for multiple symbols
- Sector-based filtering
- Top N stocks selection
- Custom watchlists

### 3. `symbol_utils.py`
Comprehensive symbol manipulation tools:
- Validation
- Conversion between formats
- Bulk operations
- Expiry code handling
- Symbol search

**Key Features:**
- `SymbolValidator` - Validate Fyers symbols
- `SymbolConverter` - Convert between formats
- `BulkSymbolOperations` - Process multiple symbols
- `ExpiryUtils` - Handle F&O expiry dates

---

## 🚀 Quick Start

### Installation

```bash
pip install fyers-apiv3 pyyaml
```

### Basic Setup

1. **View Nifty 50 List:**

```python
from nifty50_watchlist import Nifty50Watchlist

# Print full watchlist
Nifty50Watchlist.print_watchlist()

# Get all equity symbols
symbols = Nifty50Watchlist.get_equity_symbols()
print(f"Total: {len(symbols)} stocks")
```

2. **Create Watchlist by Sector:**

```python
# Get IT sector stocks
it_stocks = Nifty50Watchlist.get_symbols_by_sector("IT")

# Available sectors
sectors = Nifty50Watchlist.get_all_sectors()
print(sectors)  # ['IT', 'Banking', 'Energy', 'Auto', ...]
```

3. **Export to JSON:**

```python
# Export complete watchlist
Nifty50Watchlist.export_to_json("my_watchlist.json")
```

---

## 💡 Usage Examples

### Example 1: Create Custom Watchlist

```python
from nifty50_watchlist import FyersSymbolHandler

# Create equity symbols
reliance = FyersSymbolHandler.create_equity_symbol("RELIANCE")
# Output: 'NSE:RELIANCE-EQ'

tcs = FyersSymbolHandler.create_equity_symbol("TCS")
# Output: 'NSE:TCS-EQ'

# Create index symbols
nifty = FyersSymbolHandler.create_index_symbol("NIFTY50")
# Output: 'NSE:NIFTY50-INDEX'
```

### Example 2: Generate Futures Symbols

```python
from nifty50_watchlist import FyersSymbolHandler

# Get current month code
month_code = FyersSymbolHandler.get_current_month_code()
# Output: '26JAN' (for January 2026)

# Create future symbol
reliance_fut = FyersSymbolHandler.create_future_symbol("RELIANCE", month_code)
# Output: 'NSE:RELIANCE26JANFUT'

# Create option symbols
nifty_ce = FyersSymbolHandler.create_option_symbol("NIFTY", month_code, 21000, "CE")
# Output: 'NSE:NIFTY26JAN21000CE'

nifty_pe = FyersSymbolHandler.create_option_symbol("NIFTY", month_code, 21000, "PE")
# Output: 'NSE:NIFTY26JAN21000PE'
```

### Example 3: Stream Market Data

```python
from market_data_stream import FyersMarketDataWebSocket, WatchlistManager

# Load credentials
config = load_config()
access_token = load_access_token()
client_id = config["fyers"]["client_id"]

# Create watchlist
wm = WatchlistManager()
symbols = wm.create_top_n_by_volume(10)  # Top 10 stocks

# Create WebSocket
ws = FyersMarketDataWebSocket(
    client_id=client_id,
    access_token=access_token,
    symbols=symbols,
    data_type=FyersMarketDataWebSocket.SYMBOL_UPDATE
)

# Connect and stream
ws.connect()
```

### Example 4: Validate Symbols

```python
from symbol_utils import SymbolValidator

# Validate individual symbols
is_valid = SymbolValidator.is_valid("NSE:RELIANCE-EQ")
# Output: True

instrument_type = SymbolValidator.get_instrument_type("NSE:RELIANCE-EQ")
# Output: 'EQUITY'

# Validate multiple symbols
from symbol_utils import BulkSymbolOperations

symbols = [
    "NSE:RELIANCE-EQ",
    "NSE:NIFTY50-INDEX",
    "INVALID_SYMBOL"
]

result = BulkSymbolOperations.validate_list(symbols)
print(result)
# Output: {
#   'valid': ['NSE:RELIANCE-EQ', 'NSE:NIFTY50-INDEX'],
#   'invalid': ['INVALID_SYMBOL'],
#   'valid_count': 2,
#   'invalid_count': 1
# }
```

### Example 5: Parse Symbols

```python
from symbol_utils import SymbolConverter

# Parse Fyers symbol
parsed = SymbolConverter.from_fyers("NSE:RELIANCE-EQ")
print(parsed)
# Output: {
#   'exchange': 'NSE',
#   'symbol': 'RELIANCE',
#   'instrument': 'EQUITY',
#   'fyers_symbol': 'NSE:RELIANCE-EQ'
# }

# Parse option symbol
parsed_option = SymbolConverter.from_fyers("NSE:NIFTY26JAN21000CE")
print(parsed_option)
# Output: {
#   'exchange': 'NSE',
#   'symbol': 'NIFTY',
#   'instrument': 'OPTION',
#   'expiry': '26JAN',
#   'strike': 21000,
#   'option_type': 'CE'
# }
```

### Example 6: Work with Expiry Dates

```python
from symbol_utils import ExpiryUtils

# Get current month expiry
current = ExpiryUtils.get_current_expiry_code()
# Output: '26JAN'

# Get next month expiry
next_month = ExpiryUtils.get_next_expiry_code()
# Output: '26FEB'

# Get specific expiry
custom = ExpiryUtils.get_expiry_code(2026, 3)
# Output: '26MAR'

# Parse expiry code
parsed = ExpiryUtils.parse_expiry_code('26JAN')
# Output: {'year': 2026, 'month': 1}
```

---

## 📊 Nifty 50 Constituents

### By Sector

#### 🖥️ IT (6 stocks)
- TCS, INFY, HCLTECH, WIPRO, TECHM, LTIM

#### 🏦 Banking & Financial (8 stocks)
- HDFCBANK, ICICIBANK, SBIN, AXISBANK, KOTAKBANK, INDUSINDBK, BAJFINANCE, BAJAJFINSV

#### ⚡ Energy & Power (7 stocks)
- RELIANCE, ONGC, BPCL, ADANIPORTS, ADANIENT, POWERGRID, NTPC

#### 🚗 Auto (5 stocks)
- MARUTI, M&M, TATAMOTORS, BAJAJ-AUTO, EICHERMOT

#### 🛒 FMCG (5 stocks)
- HINDUNILVR, ITC, NESTLEIND, BRITANNIA, TATACONSUM

#### 💊 Pharma & Healthcare (4 stocks)
- SUNPHARMA, DRREDDY, CIPLA, APOLLOHOSP

#### ⚒️ Metals & Mining (4 stocks)
- TATASTEEL, HINDALCO, JSWSTEEL, COALINDIA

#### 🏗️ Cement & Construction (3 stocks)
- ULTRACEMCO, GRASIM, LT

#### 📡 Telecom (1 stock)
- BHARTIARTL

#### 🎨 Others (7 stocks)
- ASIANPAINT, TITAN, HEROMOTOCO, HDFCLIFE, SBILIFE

### Access Stock Information

```python
from nifty50_watchlist import Nifty50Watchlist

# Get info for a specific stock
info = Nifty50Watchlist.get_symbol_info("RELIANCE")
print(info)
# Output: {
#   'name': 'Reliance Industries',
#   'sector': 'Energy',
#   'lot_size': 250,
#   'fyers_symbol': 'NSE:RELIANCE-EQ',
#   'symbol': 'RELIANCE'
# }
```

---

## 🔧 Advanced Features

### 1. Bulk Symbol Conversion

```python
from symbol_utils import BulkSymbolOperations

# Convert multiple symbols at once
plain_symbols = ["RELIANCE", "TCS", "INFY", "HDFC"]
fyers_symbols = BulkSymbolOperations.convert_list_to_fyers(
    plain_symbols, 
    exchange="NSE", 
    instrument="EQ"
)
# Output: ['NSE:RELIANCE-EQ', 'NSE:TCS-EQ', 'NSE:INFY-EQ', 'NSE:HDFC-EQ']
```

### 2. Group Symbols

```python
from symbol_utils import BulkSymbolOperations

symbols = [
    "NSE:RELIANCE-EQ",
    "BSE:TCS-EQ",
    "NSE:NIFTY50-INDEX",
    "NSE:RELIANCE26JANFUT"
]

# Group by exchange
by_exchange = BulkSymbolOperations.group_by_exchange(symbols)
# Output: {
#   'NSE': ['NSE:RELIANCE-EQ', 'NSE:NIFTY50-INDEX', 'NSE:RELIANCE26JANFUT'],
#   'BSE': ['BSE:TCS-EQ']
# }

# Group by instrument type
by_instrument = BulkSymbolOperations.group_by_instrument(symbols)
# Output: {
#   'EQUITY': ['NSE:RELIANCE-EQ', 'BSE:TCS-EQ'],
#   'INDEX': ['NSE:NIFTY50-INDEX'],
#   'FUTURE': ['NSE:RELIANCE26JANFUT'],
#   'OPTION': [],
#   'UNKNOWN': []
# }
```

### 3. Filter Symbols

```python
from symbol_utils import BulkSymbolOperations

symbols = [
    "NSE:RELIANCE-EQ",
    "NSE:NIFTY50-INDEX",
    "NSE:RELIANCE26JANFUT"
]

# Get only equity symbols
equities = BulkSymbolOperations.filter_by_instrument(symbols, "EQUITY")
# Output: ['NSE:RELIANCE-EQ']

# Get only futures
futures = BulkSymbolOperations.filter_by_instrument(symbols, "FUTURE")
# Output: ['NSE:RELIANCE26JANFUT']
```

### 4. Search Symbols

```python
from symbol_utils import SymbolSearch

all_symbols = Nifty50Watchlist.get_equity_symbols()

# Search by keyword
results = SymbolSearch.search_by_keyword(all_symbols, "TATA")
# Output: ['NSE:TATAMOTORS-EQ', 'NSE:TATASTEEL-EQ', 'NSE:TATACONSUM-EQ']

# Search by pattern (regex)
results = SymbolSearch.search_by_pattern(all_symbols, r"^NSE:HDFC")
# Output: ['NSE:HDFCBANK-EQ', 'NSE:HDFCLIFE-EQ']
```

### 5. Custom Watchlist Strategies

```python
from market_data_stream import WatchlistManager

wm = WatchlistManager()

# Strategy 1: Full Nifty 50
full = wm.create_nifty50_full()

# Strategy 2: Indices only
indices = wm.create_nifty50_indices()

# Strategy 3: Sector-specific
it_stocks = wm.create_sector_watchlist("IT")
banking_stocks = wm.create_sector_watchlist("Banking")

# Strategy 4: Top N by popularity/liquidity
top_10 = wm.create_top_n_by_volume(10)

# Strategy 5: Custom selection
custom = wm.create_custom_watchlist(["RELIANCE", "TCS", "INFY"])

# Get watchlist summary
summary = wm.get_watchlist_summary(custom)
print(summary)
# Output: {
#   'total_symbols': 3,
#   'symbols': ['NSE:RELIANCE-EQ', 'NSE:TCS-EQ', 'NSE:INFY-EQ'],
#   'by_sector': {
#     'Energy': ['NSE:RELIANCE-EQ'],
#     'IT': ['NSE:TCS-EQ', 'NSE:INFY-EQ']
#   }
# }
```

---

## 📝 Common Patterns

### Pattern 1: Subscribe to Sector

```python
# Get all IT stocks
it_symbols = Nifty50Watchlist.get_symbols_by_sector("IT")

# Stream live data
ws = FyersMarketDataWebSocket(
    client_id=client_id,
    access_token=access_token,
    symbols=it_symbols,
    data_type=FyersMarketDataWebSocket.SYMBOL_UPDATE
)
ws.connect()
```

### Pattern 2: Create F&O Chain

```python
from nifty50_watchlist import FyersSymbolHandler
from symbol_utils import ExpiryUtils

symbol = "NIFTY"
expiry = ExpiryUtils.get_current_expiry_code()

# Create ATM options chain
atm_strike = 21000
strikes = range(atm_strike - 500, atm_strike + 500, 100)

options_chain = []
for strike in strikes:
    ce = FyersSymbolHandler.create_option_symbol(symbol, expiry, strike, "CE")
    pe = FyersSymbolHandler.create_option_symbol(symbol, expiry, strike, "PE")
    options_chain.extend([ce, pe])

print(f"Created {len(options_chain)} option symbols")
```

### Pattern 3: Validate User Input

```python
from symbol_utils import SymbolValidator, SymbolConverter

def process_user_symbol(user_input: str) -> dict:
    """Process and validate user-provided symbol."""
    
    # Check if already in Fyers format
    if SymbolValidator.is_valid(user_input):
        return {
            "status": "valid",
            "symbol": user_input,
            "parsed": SymbolConverter.from_fyers(user_input)
        }
    
    # Try to convert plain symbol
    try:
        fyers_symbol = FyersSymbolHandler.create_equity_symbol(user_input)
        return {
            "status": "converted",
            "symbol": fyers_symbol,
            "original": user_input
        }
    except:
        return {
            "status": "invalid",
            "error": "Could not process symbol"
        }

# Usage
result = process_user_symbol("RELIANCE")
print(result)
```

---

## 🎯 Best Practices

### 1. Always Validate Symbols
```python
# ✅ Good
if SymbolValidator.is_valid(symbol):
    ws.subscribe(symbol)

# ❌ Bad
ws.subscribe(symbol)  # May fail if invalid
```

### 2. Use Bulk Operations
```python
# ✅ Good - efficient
fyers_symbols = BulkSymbolOperations.convert_list_to_fyers(symbols)

# ❌ Bad - inefficient
fyers_symbols = [
    FyersSymbolHandler.create_equity_symbol(s) 
    for s in symbols
]
```

### 3. Handle Expiry Dates Dynamically
```python
# ✅ Good - always current
expiry = ExpiryUtils.get_current_expiry_code()

# ❌ Bad - hardcoded
expiry = "26JAN"  # Will be wrong next month
```

### 4. Group Symbols for Better Performance
```python
# ✅ Good - organized
by_sector = {
    sector: Nifty50Watchlist.get_symbols_by_sector(sector)
    for sector in Nifty50Watchlist.get_all_sectors()
}

# Process sector-wise
for sector, symbols in by_sector.items():
    process_sector(sector, symbols)
```

---

## 🐛 Troubleshooting

### Issue: Symbol Not Found

**Problem:** Symbol not recognized by Fyers API

**Solution:**
```python
# Check symbol format
symbol = "NSE:RELIANCE-EQ"
print(SymbolValidator.is_valid(symbol))
print(SymbolValidator.get_instrument_type(symbol))

# Try parsing
try:
    parsed = SymbolConverter.from_fyers(symbol)
    print(parsed)
except Exception as e:
    print(f"Invalid symbol: {e}")
```

### Issue: WebSocket Not Receiving Data

**Problem:** Connected but no messages

**Solution:**
- Verify symbol format
- Check subscription type
- Ensure market hours
- Verify access token

```python
# Debug mode
ws = FyersMarketDataWebSocket(
    client_id=client_id,
    access_token=access_token,
    symbols=symbols,
    data_type=FyersMarketDataWebSocket.SYMBOL_UPDATE
)

# Check connection
ws.connect()
time.sleep(2)
is_connected = ws.is_connected()
print(f"Connected: {is_connected}")
```

---

## 📚 Additional Resources

- [Fyers API Documentation](https://myapi.fyers.in/docs/)
- [Fyers WebSocket Guide](https://myapi.fyers.in/docsv3/#websocket-v3)
- [NSE Symbol Search](https://www.nseindia.com/)

---

## 🤝 Contributing

Feel free to extend these utilities with:
- Additional indices (Bank Nifty, Fin Nifty)
- Sectoral indices
- Mid-cap/Small-cap stocks
- Commodity symbols
- Currency pairs

---

## ⚖️ License

Use these utilities freely for your trading applications.

---

## 📞 Support

For issues with:
- **Fyers API**: Contact Fyers support
- **Symbol format**: Refer to this documentation
- **Code issues**: Check examples and troubleshooting section

---

**Happy Trading! 🚀📈**
