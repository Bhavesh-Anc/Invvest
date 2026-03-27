"""
Kite Connect API Integration for QuantEdge Pro
Provides real-time NSE/BSE market data and order execution via Zerodha Kite
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from enum import Enum

logger = logging.getLogger(__name__)

# Check if kiteconnect is available
try:
    from kiteconnect import KiteConnect, KiteTicker
    KITE_AVAILABLE = True
except ImportError:
    logger.warning("kiteconnect not available. Install with: pip install kiteconnect")
    KITE_AVAILABLE = False


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SL_M = "SL-M"


class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class ProductType(str, Enum):
    CNC = "CNC"  # Cash and Carry (delivery)
    MIS = "MIS"  # Margin Intraday Square-off
    NRML = "NRML"  # Normal (F&O)


class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"
    NFO = "NFO"  # NSE F&O
    BFO = "BFO"  # BSE F&O
    MCX = "MCX"


class KiteAPIClient:
    """
    Wrapper for Kite Connect API with enhanced functionality for quant strategies

    Usage:
        client = KiteAPIClient(api_key="your_api_key")
        client.set_access_token("your_access_token")

        # Get live quote
        quote = client.get_quote("NSE:NIFTY BANK")

        # Place order
        order_id = client.place_order(
            symbol="INFY",
            exchange="NSE",
            transaction_type="BUY",
            quantity=1,
            order_type="LIMIT",
            price=1500.0
        )
    """

    def __init__(self, api_key: str, access_token: Optional[str] = None):
        """
        Initialize Kite API client

        Args:
            api_key: Kite Connect API key from console.zerodha.com
            access_token: Access token (obtained via login flow)
        """
        if not KITE_AVAILABLE:
            raise ImportError("kiteconnect library not installed. Run: pip install kiteconnect")

        self.api_key = api_key
        self.kite = KiteConnect(api_key=api_key)

        if access_token:
            self.set_access_token(access_token)

        self.instruments_cache: Dict[str, pd.DataFrame] = {}
        self.instruments_last_updated: Optional[datetime] = None

    def set_access_token(self, access_token: str):
        """Set access token for authenticated requests"""
        self.kite.set_access_token(access_token)
        logger.info("Access token set successfully")

    def generate_session(self, request_token: str, api_secret: str) -> Dict:
        """
        Generate session using request token (from login callback)

        Args:
            request_token: Request token from Kite login callback
            api_secret: API secret from console.zerodha.com

        Returns:
            Session data with access_token
        """
        try:
            session = self.kite.generate_session(request_token, api_secret=api_secret)
            self.set_access_token(session["access_token"])
            logger.info(f"Session generated for user: {session.get('user_id')}")
            return session
        except Exception as e:
            logger.error(f"Failed to generate session: {e}")
            raise

    def get_login_url(self) -> str:
        """Get Kite login URL for user authentication"""
        return self.kite.login_url()

    # ===== Market Data Methods =====

    def get_quote(self, symbols: List[str] | str) -> Dict:
        """
        Get live market quotes for symbols

        Args:
            symbols: Single symbol or list of symbols (format: "EXCHANGE:SYMBOL")
                    Examples: "NSE:INFY", "NFO:NIFTY24JAN24000CE"

        Returns:
            Dict with symbol as key and quote data as value
        """
        try:
            if isinstance(symbols, str):
                symbols = [symbols]
            quotes = self.kite.quote(symbols)
            return quotes
        except Exception as e:
            logger.error(f"Failed to get quote: {e}")
            raise

    def get_ltp(self, symbols: List[str] | str) -> Dict[str, float]:
        """
        Get Last Traded Price for symbols

        Args:
            symbols: Single symbol or list of symbols

        Returns:
            Dict with symbol as key and LTP as value
        """
        try:
            if isinstance(symbols, str):
                symbols = [symbols]
            ltp_data = self.kite.ltp(symbols)
            return {symbol: data["last_price"] for symbol, data in ltp_data.items()}
        except Exception as e:
            logger.error(f"Failed to get LTP: {e}")
            raise

    def get_ohlc(self, symbols: List[str] | str) -> Dict:
        """Get OHLC and other market depth data for symbols"""
        try:
            if isinstance(symbols, str):
                symbols = [symbols]
            return self.kite.ohlc(symbols)
        except Exception as e:
            logger.error(f"Failed to get OHLC: {e}")
            raise

    def get_historical_data(
        self,
        instrument_token: int,
        from_date: datetime | str,
        to_date: datetime | str,
        interval: str = "day"
    ) -> pd.DataFrame:
        """
        Get historical candle data

        Args:
            instrument_token: Instrument token (from instruments list)
            from_date: Start date (datetime or "YYYY-MM-DD")
            to_date: End date (datetime or "YYYY-MM-DD")
            interval: Candle interval - "minute", "3minute", "5minute", "10minute",
                     "15minute", "30minute", "60minute", "day"

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        try:
            if isinstance(from_date, str):
                from_date = datetime.strptime(from_date, "%Y-%m-%d")
            if isinstance(to_date, str):
                to_date = datetime.strptime(to_date, "%Y-%m-%d")

            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )

            df = pd.DataFrame(data)
            return df
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            raise

    # ===== Instruments & Symbols =====

    def get_instruments(self, exchange: str = "NSE") -> pd.DataFrame:
        """
        Get list of all tradable instruments for an exchange
        Cached for 24 hours

        Args:
            exchange: Exchange name (NSE, BSE, NFO, BFO, MCX)

        Returns:
            DataFrame with instrument details
        """
        try:
            # Check cache
            now = datetime.now()
            if (exchange in self.instruments_cache and
                self.instruments_last_updated and
                (now - self.instruments_last_updated) < timedelta(hours=24)):
                return self.instruments_cache[exchange]

            # Fetch fresh data
            instruments = self.kite.instruments(exchange)
            df = pd.DataFrame(instruments)

            # Cache it
            self.instruments_cache[exchange] = df
            self.instruments_last_updated = now

            return df
        except Exception as e:
            logger.error(f"Failed to get instruments: {e}")
            raise

    def search_instruments(self, query: str, exchange: str = "NSE") -> pd.DataFrame:
        """
        Search for instruments by name or symbol

        Args:
            query: Search query (e.g., "INFY", "RELIANCE")
            exchange: Exchange to search in

        Returns:
            DataFrame with matching instruments
        """
        instruments = self.get_instruments(exchange)
        mask = (
            instruments['tradingsymbol'].str.contains(query, case=False, na=False) |
            instruments['name'].str.contains(query, case=False, na=False)
        )
        return instruments[mask]

    def get_instrument_token(self, symbol: str, exchange: str = "NSE") -> Optional[int]:
        """
        Get instrument token for a symbol

        Args:
            symbol: Trading symbol (e.g., "INFY", "NIFTY24JAN24000CE")
            exchange: Exchange name

        Returns:
            Instrument token or None if not found
        """
        instruments = self.get_instruments(exchange)
        match = instruments[instruments['tradingsymbol'] == symbol]
        if not match.empty:
            return int(match.iloc[0]['instrument_token'])
        return None

    # ===== Order Execution =====

    def place_order(
        self,
        symbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        order_type: str,
        product: str = "MIS",
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        variety: str = "regular",
        validity: str = "DAY",
        tag: Optional[str] = None
    ) -> str:
        """
        Place an order

        Args:
            symbol: Trading symbol (e.g., "INFY")
            exchange: Exchange (NSE, BSE, NFO, BFO)
            transaction_type: BUY or SELL
            quantity: Order quantity
            order_type: MARKET, LIMIT, SL, SL-M
            product: CNC, MIS, NRML
            price: Limit price (required for LIMIT and SL orders)
            trigger_price: Trigger price (required for SL and SL-M orders)
            variety: Order variety (regular, amo, co, iceberg)
            validity: Order validity (DAY, IOC)
            tag: Optional tag for order tracking

        Returns:
            Order ID
        """
        try:
            order_id = self.kite.place_order(
                variety=variety,
                exchange=exchange,
                tradingsymbol=symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                product=product,
                order_type=order_type,
                price=price,
                trigger_price=trigger_price,
                validity=validity,
                tag=tag
            )
            logger.info(f"Order placed: {order_id} | {transaction_type} {quantity} {symbol} @ {price}")
            return order_id
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise

    def modify_order(
        self,
        order_id: str,
        variety: str = "regular",
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        order_type: Optional[str] = None
    ) -> str:
        """Modify an existing order"""
        try:
            modified_order_id = self.kite.modify_order(
                variety=variety,
                order_id=order_id,
                quantity=quantity,
                price=price,
                trigger_price=trigger_price,
                order_type=order_type
            )
            logger.info(f"Order modified: {modified_order_id}")
            return modified_order_id
        except Exception as e:
            logger.error(f"Failed to modify order: {e}")
            raise

    def cancel_order(self, order_id: str, variety: str = "regular") -> str:
        """Cancel an order"""
        try:
            cancelled_order_id = self.kite.cancel_order(variety=variety, order_id=order_id)
            logger.info(f"Order cancelled: {cancelled_order_id}")
            return cancelled_order_id
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise

    def get_orders(self) -> List[Dict]:
        """Get list of all orders for the day"""
        try:
            return self.kite.orders()
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise

    def get_order_history(self, order_id: str) -> List[Dict]:
        """Get order history for a specific order"""
        try:
            return self.kite.order_history(order_id)
        except Exception as e:
            logger.error(f"Failed to get order history: {e}")
            raise

    def get_trades(self) -> List[Dict]:
        """Get list of all trades for the day"""
        try:
            return self.kite.trades()
        except Exception as e:
            logger.error(f"Failed to get trades: {e}")
            raise

    # ===== Portfolio & Positions =====

    def get_positions(self) -> Dict:
        """
        Get current positions (day + net)

        Returns:
            Dict with 'net' and 'day' positions
        """
        try:
            return self.kite.positions()
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    def get_holdings(self) -> List[Dict]:
        """Get long-term equity holdings"""
        try:
            return self.kite.holdings()
        except Exception as e:
            logger.error(f"Failed to get holdings: {e}")
            raise

    def get_margins(self, segment: Optional[str] = None) -> Dict:
        """
        Get account margins

        Args:
            segment: Specific segment (equity, commodity) or None for all

        Returns:
            Margin details
        """
        try:
            if segment:
                return self.kite.margins(segment)
            return self.kite.margins()
        except Exception as e:
            logger.error(f"Failed to get margins: {e}")
            raise

    # ===== WebSocket Streaming =====

    def create_ticker(self) -> 'KiteTicker':
        """
        Create a KiteTicker instance for WebSocket streaming

        Returns:
            KiteTicker instance (need to attach callbacks and start)
        """
        if not KITE_AVAILABLE:
            raise ImportError("kiteconnect not installed")

        ticker = KiteTicker(self.api_key, self.kite.access_token)
        return ticker

    # ===== Utility Methods =====

    def get_profile(self) -> Dict:
        """Get user profile"""
        try:
            return self.kite.profile()
        except Exception as e:
            logger.error(f"Failed to get profile: {e}")
            raise

    def invalidate_session(self) -> bool:
        """Invalidate current access token"""
        try:
            result = self.kite.invalidate_access_token()
            logger.info("Session invalidated")
            return result
        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")
            raise


# ===== Singleton Instance Management =====

_kite_client_instance: Optional[KiteAPIClient] = None


def get_kite_client(api_key: Optional[str] = None, access_token: Optional[str] = None) -> KiteAPIClient:
    """
    Get or create singleton KiteAPIClient instance

    Args:
        api_key: Kite API key (required on first call)
        access_token: Access token (optional)

    Returns:
        KiteAPIClient instance
    """
    global _kite_client_instance

    if _kite_client_instance is None:
        if api_key is None:
            raise ValueError("api_key required for first initialization")
        _kite_client_instance = KiteAPIClient(api_key, access_token)
    elif access_token:
        _kite_client_instance.set_access_token(access_token)

    return _kite_client_instance


def set_kite_client(client: KiteAPIClient):
    """Set the singleton KiteAPIClient instance"""
    global _kite_client_instance
    _kite_client_instance = client
