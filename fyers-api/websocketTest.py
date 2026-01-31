import os
import json
import yaml
from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import order_ws
from typing import Dict, Any, Optional
import logging
import signal
import sys
import time

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
    """
    Load configuration from YAML file.
    
    Args:
        path: Path to the config file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {path}")
            return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML config: {e}")
        raise


def load_access_token(path: str = "auth_tokens.json") -> str:
    """
    Load access token from JSON file.
    
    Args:
        path: Path to the auth tokens file
        
    Returns:
        Access token string
        
    Raises:
        FileNotFoundError: If token file doesn't exist
        KeyError: If 'access_token' key is missing
    """
    try:
        with open(path, "r") as f:
            data = json.load(f)
            token = data["access_token"]
            logger.info("Access token loaded successfully")
            return token
    except FileNotFoundError:
        logger.error(f"Auth token file not found: {path}")
        raise
    except KeyError:
        logger.error("'access_token' key not found in auth tokens file")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON token file: {e}")
        raise


# ===============================
# FYERS CLIENT
# ===============================

def get_fyers_client(client_id: str, access_token: str) -> fyersModel.FyersModel:
    """
    Create and return a Fyers API client.
    
    Args:
        client_id: Fyers client ID
        access_token: Access token for authentication
        
    Returns:
        Configured FyersModel instance
    """
    return fyersModel.FyersModel(
        client_id=client_id,
        token=access_token,
        is_async=False,
        log_path=os.getcwd()
    )


# ===============================
# WEBSOCKET CALLBACKS
# ===============================

def on_message(message: Dict[str, Any]) -> None:
    """
    Unified callback to handle all updates from WebSocket.
    Handles orders, trades, positions, and general updates.
    
    Args:
        message: Update message from WebSocket
    """
    try:
        # Check message type and route accordingly
        if isinstance(message, dict):
            # General status messages
            if 'code' in message and 'message' in message:
                msg_type = message.get('type', 'General')
                logger.info(f"{msg_type}: {message}")
                return
            
            # Order updates
            if 'orderNumber' in message or 'id' in message:
                logger.info("=" * 60)
                logger.info("📋 ORDER UPDATE RECEIVED")
                logger.info(json.dumps(message, indent=2))
                logger.info("=" * 60)
                return
            
            # Trade updates
            if 'tradeNumber' in message:
                logger.info("=" * 60)
                logger.info("💰 TRADE UPDATE RECEIVED")
                logger.info(json.dumps(message, indent=2))
                logger.info("=" * 60)
                return
            
            # Position updates
            if 'netQty' in message or 'qty' in message:
                logger.info("=" * 60)
                logger.info("📊 POSITION UPDATE RECEIVED")
                logger.info(json.dumps(message, indent=2))
                logger.info("=" * 60)
                return
            
            # Default: log as generic update
            logger.info("=" * 60)
            logger.info("📬 UPDATE RECEIVED")
            logger.info(json.dumps(message, indent=2))
            logger.info("=" * 60)
        else:
            logger.info(f"Message: {message}")
            
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)


def on_error(message: Dict[str, Any]) -> None:
    """
    Callback to handle WebSocket errors.
    
    Args:
        message: Error message
    """
    logger.error("=" * 60)
    logger.error("❌ WEBSOCKET ERROR")
    logger.error(json.dumps(message, indent=2) if isinstance(message, dict) else str(message))
    logger.error("=" * 60)


def on_close(message: Dict[str, Any]) -> None:
    """
    Callback to handle WebSocket connection close.
    
    Args:
        message: Close message
    """
    logger.warning("=" * 60)
    logger.warning("🔴 WEBSOCKET CLOSED")
    logger.warning(json.dumps(message, indent=2) if isinstance(message, dict) else str(message))
    logger.warning("=" * 60)


def on_open(ws_instance: order_ws.FyersOrderSocket, data_types: str) -> None:
    """
    Callback to subscribe to data streams upon WebSocket connection.
    
    Args:
        ws_instance: The WebSocket instance
        data_types: Comma-separated data types to subscribe to
    """
    logger.info("=" * 60)
    logger.info("🟢 WEBSOCKET CONNECTION ESTABLISHED")
    logger.info("=" * 60)
    
    try:
        ws_instance.subscribe(data_type=data_types)
        logger.info(f"✓ Successfully subscribed to: {data_types}")
        
        # Keep the socket running to receive real-time data
        ws_instance.keep_running()
    except Exception as e:
        logger.error(f"Error subscribing to data: {e}")
        raise


# ===============================
# WEBSOCKET MANAGER
# ===============================

class FyersOrderWebSocket:
    """
    Manager class for Fyers Order WebSocket connection.
    """
    
    # Available subscription types
    ORDERS = "OnOrders"
    TRADES = "OnTrades"
    POSITIONS = "OnPositions"
    GENERAL = "OnGeneral"
    ALL = "OnOrders,OnTrades,OnPositions,OnGeneral"
    
    def __init__(self, client_id: str, access_token: str, data_types: str = ORDERS):
        """
        Initialize the WebSocket manager.
        
        Args:
            client_id: Fyers client ID
            access_token: Access token (without client_id prefix)
            data_types: Comma-separated data types to subscribe to
        """
        self.client_id = client_id
        self.access_token = f'{client_id}:{access_token}'
        self.data_types = data_types
        self.ws: Optional[order_ws.FyersOrderSocket] = None
        self._is_running = False
        
    def create_connection(self) -> order_ws.FyersOrderSocket:
        """
        Create and configure the WebSocket connection.
        
        Returns:
            Configured FyersOrderSocket instance
        """
        self.ws = order_ws.FyersOrderSocket(
            access_token=self.access_token,
            write_to_file=False,
            log_path="",
            on_connect=lambda: on_open(self.ws, self.data_types),
            on_close=on_close,
            on_error=on_error,
            on_orders=on_message,  # Single callback handles all message types
        )
        logger.info("WebSocket instance created")
        return self.ws
    
    def connect(self) -> None:
        """
        Establish WebSocket connection.
        """
        if self.ws is None:
            self.create_connection()
        
        try:
            logger.info("Attempting to connect to Fyers WebSocket...")
            self._is_running = True
            self.ws.connect()
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            self._is_running = False
            raise
    
    def is_connected(self) -> bool:
        """
        Check if WebSocket is connected.
        
        Returns:
            True if connected, False otherwise
        """
        if self.ws:
            connected = self.ws.is_connected()
            logger.info(f"Connection status: {'Connected ✓' if connected else 'Disconnected ✗'}")
            return connected
        return False
    
    def disconnect(self) -> None:
        """
        Close the WebSocket connection gracefully.
        """
        if self.ws and self._is_running:
            try:
                logger.info("Initiating graceful disconnect...")
                self._is_running = False
                
                # Use the correct method name
                if hasattr(self.ws, 'close_connection'):
                    self.ws.close_connection()
                elif hasattr(self.ws, 'close'):
                    self.ws.close()
                else:
                    logger.warning("No close method found on WebSocket object")
                
                time.sleep(0.5)  # Give time for threads to clean up
                logger.info("✓ WebSocket disconnected successfully")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
                # Even if there's an error, mark as not running
                self._is_running = False
    
    @property
    def is_running(self) -> bool:
        """Check if WebSocket is running."""
        return self._is_running


# ===============================
# SIGNAL HANDLER
# ===============================

class WebSocketSignalHandler:
    """
    Handle graceful shutdown on SIGINT/SIGTERM.
    """
    
    def __init__(self, ws_manager: FyersOrderWebSocket):
        self.ws_manager = ws_manager
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup signal handlers."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"\n{'=' * 60}")
        logger.info(f"🛑 Received shutdown signal ({signum})")
        logger.info(f"{'=' * 60}")
        self.ws_manager.disconnect()
        logger.info("👋 Shutdown complete. Goodbye!")
        sys.exit(0)


# ===============================
# MAIN
# ===============================

def main():
    """
    Main function to initialize and run the Fyers Order WebSocket.
    """
    ws_manager = None
    
    try:
        # Load configuration and credentials
        logger.info("🚀 Starting Fyers Order WebSocket Client...")
        config = load_config()
        access_token = load_access_token()
        client_id = config["fyers"]["client_id"]
        
        # Choose what to subscribe to:
        # - FyersOrderWebSocket.ORDERS    -> Only order updates
        # - FyersOrderWebSocket.TRADES    -> Only trade updates
        # - FyersOrderWebSocket.POSITIONS -> Only position updates
        # - FyersOrderWebSocket.GENERAL   -> Only general updates
        # - FyersOrderWebSocket.ALL       -> Everything (recommended for testing)
        # - Custom: "OnOrders,OnTrades"   -> Multiple specific types
        
        subscription = FyersOrderWebSocket.ALL  # Subscribe to everything for testing
        
        # Create WebSocket manager
        ws_manager = FyersOrderWebSocket(client_id, access_token, subscription)
        
        # Setup signal handler for graceful shutdown
        signal_handler = WebSocketSignalHandler(ws_manager)
        
        # Connect to WebSocket
        ws_manager.connect()
        
        # Verify connection
        time.sleep(1)  # Brief pause to ensure connection is established
        ws_manager.is_connected()
        
        # Display status
        logger.info("=" * 60)
        logger.info("🟢 WEBSOCKET IS LIVE AND LISTENING")
        logger.info(f"📡 Subscribed to: {subscription}")
        logger.info("⌨️  Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        # Keep the main thread alive
        while ws_manager.is_running:
            time.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("\n⌨️  Keyboard interrupt detected")
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