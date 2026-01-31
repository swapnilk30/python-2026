"""
Integrated Example: Nifty 50 Market Data Streaming
===================================================

This example shows how to:
1. Load Nifty 50 watchlist
2. Subscribe to live market data via WebSocket
3. Handle incoming quotes/trades
"""

import os
import json
import yaml
from typing import Dict, Any, List
import logging
import signal
import sys
import time
from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws

# Import watchlist utilities
from nifty50_watchlist import (
    Nifty50Watchlist,
    FyersSymbolHandler,
    NIFTY50_STOCKS
)

# ===============================
# LOGGING SETUP
# ===============================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ===============================
# CONFIG LOADERS
# ===============================

def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_access_token(path: str = "auth_tokens.json") -> str:
    """Load access token from JSON file."""
    with open(path, "r") as f:
        return json.load(f)["access_token"]


# ===============================
# MARKET DATA CALLBACKS
# ===============================

def on_message(message: Any) -> None:
    """
    Handle incoming market data messages.
    
    Message types:
    - Quotes: Real-time price updates
    - Depth: Order book data
    - Trades: Executed trades
    """
    try:
        if isinstance(message, dict):
            # Extract symbol and data
            symbol = message.get("symbol", "UNKNOWN")
            
            # Quote data
            if "ltp" in message:  # Last Traded Price
                logger.info("=" * 60)
                logger.info(f"📈 QUOTE UPDATE: {symbol}")
                logger.info(f"  LTP: ₹{message.get('ltp', 0):.2f}")
                logger.info(f"  Volume: {message.get('volume', 0):,}")
                logger.info(f"  Change: {message.get('chp', 0):.2f}%")
                logger.info(f"  High: ₹{message.get('high', 0):.2f}")
                logger.info(f"  Low: ₹{message.get('low', 0):.2f}")
                logger.info(f"  Open: ₹{message.get('open_price', 0):.2f}")
                logger.info(f"  Prev Close: ₹{message.get('prev_close_price', 0):.2f}")
                logger.info("=" * 60)
            
            # Depth data (order book)
            elif "bid" in message or "ask" in message:
                logger.info(f"📊 DEPTH UPDATE: {symbol}")
                logger.debug(json.dumps(message, indent=2))
            
            # Trade data
            elif "trade_price" in message:
                logger.info(f"💰 TRADE: {symbol} @ ₹{message.get('trade_price', 0):.2f}")
            
            else:
                logger.info(f"📬 UPDATE: {symbol}")
                logger.debug(json.dumps(message, indent=2))
        
        else:
            logger.info(f"Message: {message}")
            
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)


def on_error(message: Any) -> None:
    """Handle WebSocket errors."""
    logger.error(f"❌ WebSocket Error: {message}")


def on_close(message: Any) -> None:
    """Handle WebSocket close."""
    logger.warning(f"🔴 WebSocket Closed: {message}")


def on_open(ws_instance: data_ws.FyersDataSocket, symbols: List[str], data_type: str) -> None:
    """
    Subscribe to symbols when WebSocket opens.
    
    Args:
        ws_instance: WebSocket instance
        symbols: List of Fyers symbols to subscribe
        data_type: Type of data (quotes/depth/trades)
    """
    logger.info("=" * 60)
    logger.info("🟢 WEBSOCKET CONNECTED")
    logger.info("=" * 60)
    
    try:
        # Subscribe to symbols
        ws_instance.subscribe(symbol=symbols, data_type=data_type)
        logger.info(f"✓ Subscribed to {len(symbols)} symbols")
        logger.info(f"✓ Data type: {data_type}")
        
        # Keep running
        ws_instance.keep_running()
        
    except Exception as e:
        logger.error(f"Error subscribing: {e}")
        raise


# ===============================
# MARKET DATA WEBSOCKET MANAGER
# ===============================

class FyersMarketDataWebSocket:
    """
    Manager for Fyers market data WebSocket.
    """
    
    # Data types
    SYMBOL_UPDATE = "SymbolUpdate"  # Quotes
    DEPTH_UPDATE = "DepthUpdate"    # Order book
    
    def __init__(
        self, 
        client_id: str, 
        access_token: str, 
        symbols: List[str],
        data_type: str = SYMBOL_UPDATE
    ):
        """
        Initialize market data WebSocket.
        
        Args:
            client_id: Fyers client ID
            access_token: Access token
            symbols: List of Fyers symbols
            data_type: Type of data to subscribe
        """
        self.client_id = client_id
        self.access_token = f'{client_id}:{access_token}'
        self.symbols = symbols
        self.data_type = data_type
        self.ws = None
        self._is_running = False
    
    def create_connection(self) -> data_ws.FyersDataSocket:
        """Create WebSocket connection."""
        self.ws = data_ws.FyersDataSocket(
            access_token=self.access_token,
            log_path="",
            litemode=False,
            write_to_file=False,
            reconnect=True,
            on_connect=lambda: on_open(self.ws, self.symbols, self.data_type),
            on_close=on_close,
            on_error=on_error,
            on_message=on_message
        )
        logger.info("Market data WebSocket instance created")
        return self.ws
    
    def connect(self) -> None:
        """Connect to WebSocket."""
        if self.ws is None:
            self.create_connection()
        
        try:
            logger.info("Connecting to Fyers market data WebSocket...")
            self._is_running = True
            self.ws.connect()
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._is_running = False
            raise
    
    def disconnect(self) -> None:
        """Disconnect WebSocket."""
        if self.ws and self._is_running:
            try:
                logger.info("Disconnecting...")
                self._is_running = False
                
                if hasattr(self.ws, 'close_connection'):
                    self.ws.close_connection()
                
                time.sleep(0.5)
                logger.info("✓ Disconnected successfully")
            except Exception as e:
                logger.error(f"Disconnect error: {e}")
                self._is_running = False
    
    @property
    def is_running(self) -> bool:
        """Check if running."""
        return self._is_running


# ===============================
# WATCHLIST MANAGER
# ===============================

class WatchlistManager:
    """
    Manage multiple watchlists and subscriptions.
    """
    
    def __init__(self):
        self.watchlists = {}
    
    def create_nifty50_full(self) -> List[str]:
        """Get all Nifty 50 stocks."""
        return Nifty50Watchlist.get_equity_symbols()
    
    def create_nifty50_indices(self) -> List[str]:
        """Get Nifty indices."""
        return [
            FyersSymbolHandler.create_index_symbol("NIFTY50"),
            FyersSymbolHandler.create_index_symbol("BANKNIFTY"),
        ]
    
    def create_sector_watchlist(self, sector: str) -> List[str]:
        """Get stocks by sector."""
        return Nifty50Watchlist.get_symbols_by_sector(sector)
    
    def create_top_n_by_volume(self, n: int = 10) -> List[str]:
        """
        Get top N stocks (by popularity/liquidity).
        This is a simplified version - you'd fetch actual volumes from API.
        """
        top_stocks = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
            "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "BAJFINANCE"
        ]
        return [FyersSymbolHandler.create_equity_symbol(s) for s in top_stocks[:n]]
    
    def create_custom_watchlist(self, symbols: List[str]) -> List[str]:
        """Create custom watchlist from symbol list."""
        return [FyersSymbolHandler.create_equity_symbol(s) for s in symbols]
    
    def get_watchlist_summary(self, symbols: List[str]) -> Dict[str, Any]:
        """Get summary of watchlist."""
        summary = {
            "total_symbols": len(symbols),
            "symbols": symbols,
            "by_sector": {}
        }
        
        for symbol in symbols:
            # Extract base symbol
            base_symbol = symbol.split(":")[1].replace("-EQ", "")
            if base_symbol in NIFTY50_STOCKS:
                sector = NIFTY50_STOCKS[base_symbol]["sector"]
                if sector not in summary["by_sector"]:
                    summary["by_sector"][sector] = []
                summary["by_sector"][sector].append(symbol)
        
        return summary


# ===============================
# SIGNAL HANDLER
# ===============================

class SignalHandler:
    """Handle graceful shutdown."""
    
    def __init__(self, ws_manager: FyersMarketDataWebSocket):
        self.ws_manager = ws_manager
        signal.signal(signal.SIGINT, self._handler)
        signal.signal(signal.SIGTERM, self._handler)
    
    def _handler(self, signum, frame):
        logger.info(f"\n{'=' * 60}")
        logger.info(f"🛑 Shutdown signal received ({signum})")
        logger.info(f"{'=' * 60}")
        self.ws_manager.disconnect()
        logger.info("👋 Goodbye!")
        sys.exit(0)


# ===============================
# MAIN
# ===============================

def main():
    """
    Main function - Stream market data for Nifty 50 stocks.
    """
    ws_manager = None
    
    try:
        logger.info("🚀 Starting Nifty 50 Market Data Stream...")
        
        # Load credentials
        config = load_config()
        access_token = load_access_token()
        client_id = config["fyers"]["client_id"]
        
        # Create watchlist manager
        wm = WatchlistManager()
        
        # Choose watchlist strategy:
        # 1. Full Nifty 50 (all 50 stocks)
        # symbols = wm.create_nifty50_full()
        
        # 2. Indices only
        # symbols = wm.create_nifty50_indices()
        
        # 3. Sector-specific (e.g., IT stocks)
        # symbols = wm.create_sector_watchlist("IT")
        
        # 4. Top 10 by volume/popularity
        symbols = wm.create_top_n_by_volume(10)
        
        # 5. Custom selection
        # symbols = wm.create_custom_watchlist(["RELIANCE", "TCS", "INFY"])
        
        # Get summary
        summary = wm.get_watchlist_summary(symbols)
        
        # Display watchlist info
        logger.info("=" * 60)
        logger.info("📋 WATCHLIST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total symbols: {summary['total_symbols']}")
        for sector, stocks in summary['by_sector'].items():
            logger.info(f"  {sector}: {len(stocks)} stocks")
        logger.info("")
        logger.info("Symbols:")
        for symbol in symbols:
            logger.info(f"  • {symbol}")
        logger.info("=" * 60)
        
        # Create WebSocket manager
        # Data types: SYMBOL_UPDATE (quotes) or DEPTH_UPDATE (order book)
        ws_manager = FyersMarketDataWebSocket(
            client_id=client_id,
            access_token=access_token,
            symbols=symbols,
            data_type=FyersMarketDataWebSocket.SYMBOL_UPDATE
        )
        
        # Setup signal handler
        signal_handler = SignalHandler(ws_manager)
        
        # Connect
        ws_manager.connect()
        time.sleep(1)
        
        # Status
        logger.info("=" * 60)
        logger.info("🟢 LIVE MARKET DATA STREAMING")
        logger.info("📊 Watching Nifty 50 stocks...")
        logger.info("⌨️  Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        # Keep alive
        while ws_manager.is_running:
            time.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("\n⌨️  Keyboard interrupt")
        if ws_manager:
            ws_manager.disconnect()
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        if ws_manager:
            ws_manager.disconnect()
        raise
    
    finally:
        logger.info("=" * 60)
        logger.info("✓ Application terminated")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()