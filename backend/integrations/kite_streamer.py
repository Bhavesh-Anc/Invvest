"""
Kite WebSocket Streaming
Real-time tick-by-tick market data via Kite Ticker WebSocket
"""

import logging
from typing import Dict, List, Callable, Optional
import asyncio
import json
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from kiteconnect import KiteTicker
    KITE_AVAILABLE = True
except ImportError:
    logger.warning("kiteconnect not available")
    KITE_AVAILABLE = False


class KiteStreamManager:
    """
    Manages Kite WebSocket connections for real-time market data streaming

    Usage:
        manager = KiteStreamManager(api_key, access_token)
        manager.on_tick(my_callback)
        manager.subscribe([256265])  # NIFTY 50
        manager.start()
    """

    def __init__(self, api_key: str, access_token: str):
        """
        Initialize Kite stream manager

        Args:
            api_key: Kite API key
            access_token: Access token from authentication
        """
        if not KITE_AVAILABLE:
            raise ImportError("kiteconnect library not installed")

        self.api_key = api_key
        self.access_token = access_token
        self.ticker: Optional[KiteTicker] = None
        self.subscribed_tokens: List[int] = []
        self.tick_callbacks: List[Callable] = []
        self.connect_callbacks: List[Callable] = []
        self.close_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        self.is_connected = False

        logger.info("KiteStreamManager initialized")

    def _create_ticker(self):
        """Create KiteTicker instance"""
        if self.ticker:
            return

        self.ticker = KiteTicker(self.api_key, self.access_token)

        # Attach event handlers
        self.ticker.on_ticks = self._on_ticks
        self.ticker.on_connect = self._on_connect
        self.ticker.on_close = self._on_close
        self.ticker.on_error = self._on_error
        self.ticker.on_reconnect = self._on_reconnect
        self.ticker.on_noreconnect = self._on_noreconnect

        logger.info("KiteTicker instance created")

    def _on_ticks(self, ws, ticks: List[Dict]):
        """Handle incoming ticks"""
        try:
            # Add timestamp
            for tick in ticks:
                tick['timestamp'] = datetime.now().isoformat()

            # Call all registered callbacks
            for callback in self.tick_callbacks:
                try:
                    callback(ticks)
                except Exception as e:
                    logger.error(f"Error in tick callback: {e}")

        except Exception as e:
            logger.error(f"Error processing ticks: {e}")

    def _on_connect(self, ws, response):
        """Handle connection established"""
        self.is_connected = True
        logger.info(f"WebSocket connected: {response}")

        # Subscribe to instruments if any were set before connection
        if self.subscribed_tokens:
            self._subscribe_tokens(self.subscribed_tokens)

        # Call connect callbacks
        for callback in self.connect_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in connect callback: {e}")

    def _on_close(self, ws, code, reason):
        """Handle connection closed"""
        self.is_connected = False
        logger.warning(f"WebSocket closed: code={code}, reason={reason}")

        # Call close callbacks
        for callback in self.close_callbacks:
            try:
                callback(code, reason)
            except Exception as e:
                logger.error(f"Error in close callback: {e}")

    def _on_error(self, ws, code, reason):
        """Handle WebSocket error"""
        logger.error(f"WebSocket error: code={code}, reason={reason}")

        # Call error callbacks
        for callback in self.error_callbacks:
            try:
                callback(code, reason)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")

    def _on_reconnect(self, ws, attempts_count):
        """Handle reconnection attempt"""
        logger.info(f"Attempting to reconnect (attempt #{attempts_count})...")

    def _on_noreconnect(self, ws):
        """Handle max reconnection attempts reached"""
        logger.error("Max reconnection attempts reached. WebSocket will not reconnect.")
        self.is_connected = False

    def _subscribe_tokens(self, tokens: List[int]):
        """Subscribe to instrument tokens"""
        if not self.ticker or not self.is_connected:
            return

        try:
            # Subscribe to tokens
            self.ticker.subscribe(tokens)

            # Set mode to FULL for complete market depth
            self.ticker.set_mode(self.ticker.MODE_FULL, tokens)

            logger.info(f"Subscribed to {len(tokens)} instruments")
        except Exception as e:
            logger.error(f"Failed to subscribe to tokens: {e}")

    def on_tick(self, callback: Callable):
        """
        Register callback for tick events

        Args:
            callback: Function that takes list of ticks as argument
                     Signature: callback(ticks: List[Dict])
        """
        self.tick_callbacks.append(callback)

    def on_connect(self, callback: Callable):
        """
        Register callback for connection established

        Args:
            callback: Function with no arguments
        """
        self.connect_callbacks.append(callback)

    def on_close(self, callback: Callable):
        """
        Register callback for connection closed

        Args:
            callback: Function that takes (code, reason)
        """
        self.close_callbacks.append(callback)

    def on_error(self, callback: Callable):
        """
        Register callback for errors

        Args:
            callback: Function that takes (code, reason)
        """
        self.error_callbacks.append(callback)

    def subscribe(self, tokens: List[int]):
        """
        Subscribe to instrument tokens for streaming

        Args:
            tokens: List of instrument tokens to subscribe to
        """
        self.subscribed_tokens.extend(tokens)
        self.subscribed_tokens = list(set(self.subscribed_tokens))  # Remove duplicates

        if self.is_connected:
            self._subscribe_tokens(tokens)

    def unsubscribe(self, tokens: List[int]):
        """
        Unsubscribe from instrument tokens

        Args:
            tokens: List of instrument tokens to unsubscribe
        """
        if self.ticker and self.is_connected:
            try:
                self.ticker.unsubscribe(tokens)
                for token in tokens:
                    if token in self.subscribed_tokens:
                        self.subscribed_tokens.remove(token)
                logger.info(f"Unsubscribed from {len(tokens)} instruments")
            except Exception as e:
                logger.error(f"Failed to unsubscribe: {e}")

    def start(self, threaded: bool = True):
        """
        Start WebSocket connection

        Args:
            threaded: Run in background thread (default True)
        """
        self._create_ticker()

        if not self.ticker:
            raise RuntimeError("Failed to create ticker instance")

        logger.info("Starting Kite WebSocket stream...")

        try:
            if threaded:
                # Run in background thread
                self.ticker.connect(threaded=True)
            else:
                # Blocking call
                self.ticker.connect(threaded=False)
        except Exception as e:
            logger.error(f"Failed to start WebSocket: {e}")
            raise

    def stop(self):
        """Stop WebSocket connection"""
        if self.ticker:
            try:
                self.ticker.close()
                logger.info("Kite WebSocket stopped")
            except Exception as e:
                logger.error(f"Error stopping WebSocket: {e}")

        self.is_connected = False


# ===== Singleton Instance Management =====

_stream_manager_instance: Optional[KiteStreamManager] = None


def get_stream_manager(api_key: Optional[str] = None, access_token: Optional[str] = None) -> KiteStreamManager:
    """
    Get or create singleton KiteStreamManager instance

    Args:
        api_key: Kite API key (required on first call)
        access_token: Access token (required on first call)

    Returns:
        KiteStreamManager instance
    """
    global _stream_manager_instance

    if _stream_manager_instance is None:
        if not api_key or not access_token:
            # Try to get from config
            from config.kite_config import get_kite_config
            config = get_kite_config()

            if not config.has_access_token():
                raise ValueError("Not authenticated. Please login to Kite first.")

            api_key = config.api_key
            access_token = config.access_token

        _stream_manager_instance = KiteStreamManager(api_key, access_token)

    return _stream_manager_instance


def reset_stream_manager():
    """Reset stream manager instance (useful for testing)"""
    global _stream_manager_instance
    if _stream_manager_instance:
        _stream_manager_instance.stop()
    _stream_manager_instance = None
