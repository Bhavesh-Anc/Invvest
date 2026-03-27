"""
Broker Integrations for Indian Stock Market
Zerodha Kite, Upstox, AngelOne (Angel Broking)
Production-ready API wrappers with error handling and rate limiting
"""

import requests
import json
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"  # Stop Loss
    SL_M = "SL-M"  # Stop Loss Market


class TransactionType(Enum):
    """Transaction types"""
    BUY = "BUY"
    SELL = "SELL"


class ProductType(Enum):
    """Product types"""
    CNC = "CNC"  # Cash and Carry (delivery)
    NRML = "NRML"  # Normal (for F&O)
    MIS = "MIS"  # Margin Intraday Square-off
    BO = "BO"  # Bracket Order
    CO = "CO"  # Cover Order


class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class OrderResponse:
    """Standardized order response"""
    order_id: str
    status: OrderStatus
    message: str
    filled_quantity: float = 0
    average_price: float = 0


class BrokerAdapter(ABC):
    """
    Abstract base class for broker adapters
    Ensures consistent interface across brokers
    """

    def __init__(self, api_key: str, api_secret: str, **kwargs):
        """
        Args:
            api_key: Broker API key
            api_secret: Broker API secret
            **kwargs: Additional broker-specific parameters
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = None
        self.session = requests.Session()
        self.rate_limiter = RateLimiter()

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with broker"""
        pass

    @abstractmethod
    def place_order(self, symbol: str, transaction_type: TransactionType,
                   quantity: int, order_type: OrderType = OrderType.MARKET,
                   price: float = 0, product: ProductType = ProductType.MIS,
                   **kwargs) -> OrderResponse:
        """Place an order"""
        pass

    @abstractmethod
    def get_quote(self, symbol: str) -> Dict:
        """Get live quote for a symbol"""
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        pass

    @abstractmethod
    def get_orders(self) -> List[Dict]:
        """Get all orders"""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass

    @abstractmethod
    def modify_order(self, order_id: str, **kwargs) -> bool:
        """Modify an order"""
        pass


class ZerodhaKiteAdapter(BrokerAdapter):
    """
    Zerodha Kite API Adapter
    Most popular broker in India for retail algo trading
    """

    BASE_URL = "https://api.kite.trade"

    def __init__(self, api_key: str, api_secret: str, request_token: Optional[str] = None):
        """
        Args:
            api_key: Kite Connect API key
            api_secret: API secret
            request_token: Request token from login flow
        """
        super().__init__(api_key, api_secret)
        self.request_token = request_token

    def authenticate(self) -> bool:
        """
        Authenticate with Zerodha Kite

        Returns:
            True if successful
        """
        if not self.request_token:
            logger.error("Request token required for Zerodha authentication")
            return False

        try:
            # Generate checksum
            checksum = hashlib.sha256(
                f"{self.api_key}{self.request_token}{self.api_secret}".encode()
            ).hexdigest()

            # Get access token
            response = self.session.post(
                f"{self.BASE_URL}/session/token",
                data={
                    "api_key": self.api_key,
                    "request_token": self.request_token,
                    "checksum": checksum
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data['data']['access_token']
                self.session.headers.update({
                    'Authorization': f'token {self.api_key}:{self.access_token}',
                    'X-Kite-Version': '3'
                })
                logger.info("Zerodha authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def place_order(self, symbol: str, transaction_type: TransactionType,
                   quantity: int, order_type: OrderType = OrderType.MARKET,
                   price: float = 0, product: ProductType = ProductType.MIS,
                   **kwargs) -> OrderResponse:
        """
        Place order on Zerodha

        Args:
            symbol: Trading symbol (e.g., "RELIANCE")
            transaction_type: BUY or SELL
            quantity: Order quantity
            order_type: MARKET, LIMIT, SL, SL-M
            price: Limit price (for LIMIT orders)
            product: CNC, NRML, MIS, BO, CO
            **kwargs: Additional parameters (trigger_price, validity, etc.)

        Returns:
            OrderResponse
        """
        self.rate_limiter.check_limit('place_order')

        try:
            exchange = kwargs.get('exchange', 'NSE')

            order_params = {
                'exchange': exchange,
                'tradingsymbol': symbol,
                'transaction_type': transaction_type.value,
                'quantity': quantity,
                'order_type': order_type.value,
                'product': product.value,
                'validity': kwargs.get('validity', 'DAY')
            }

            if order_type in [OrderType.LIMIT, OrderType.SL]:
                order_params['price'] = price

            if order_type in [OrderType.SL, OrderType.SL_M]:
                order_params['trigger_price'] = kwargs.get('trigger_price', price * 0.99)

            response = self.session.post(
                f"{self.BASE_URL}/orders",
                data=order_params
            )

            if response.status_code == 200:
                data = response.json()
                order_id = data['data']['order_id']

                logger.info(f"Order placed successfully: {order_id}")

                return OrderResponse(
                    order_id=str(order_id),
                    status=OrderStatus.PENDING,
                    message="Order placed successfully"
                )
            else:
                error_msg = response.json().get('message', 'Unknown error')
                logger.error(f"Order placement failed: {error_msg}")

                return OrderResponse(
                    order_id="",
                    status=OrderStatus.REJECTED,
                    message=error_msg
                )

        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return OrderResponse(
                order_id="",
                status=OrderStatus.REJECTED,
                message=str(e)
            )

    def get_quote(self, symbol: str, exchange: str = 'NSE') -> Dict:
        """Get live quote"""
        self.rate_limiter.check_limit('get_quote')

        try:
            response = self.session.get(
                f"{self.BASE_URL}/quote",
                params={'i': f"{exchange}:{symbol}"}
            )

            if response.status_code == 200:
                data = response.json()
                quote_data = data['data'][f"{exchange}:{symbol}"]

                return {
                    'symbol': symbol,
                    'last_price': quote_data['last_price'],
                    'volume': quote_data['volume'],
                    'buy_quantity': quote_data['buy_quantity'],
                    'sell_quantity': quote_data['sell_quantity'],
                    'open': quote_data['ohlc']['open'],
                    'high': quote_data['ohlc']['high'],
                    'low': quote_data['ohlc']['low'],
                    'close': quote_data['ohlc']['close'],
                    'timestamp': quote_data['last_trade_time']
                }
            else:
                logger.error(f"Quote fetch failed: {response.text}")
                return {}

        except Exception as e:
            logger.error(f"Quote fetch error: {e}")
            return {}

    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        try:
            response = self.session.get(f"{self.BASE_URL}/portfolio/positions")

            if response.status_code == 200:
                data = response.json()
                return data['data']['net']
            else:
                logger.error(f"Positions fetch failed: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Positions fetch error: {e}")
            return []

    def get_orders(self) -> List[Dict]:
        """Get all orders"""
        try:
            response = self.session.get(f"{self.BASE_URL}/orders")

            if response.status_code == 200:
                data = response.json()
                return data['data']
            else:
                logger.error(f"Orders fetch failed: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Orders fetch error: {e}")
            return []

    def cancel_order(self, order_id: str, variety: str = 'regular') -> bool:
        """Cancel an order"""
        try:
            response = self.session.delete(
                f"{self.BASE_URL}/orders/{variety}/{order_id}"
            )

            if response.status_code == 200:
                logger.info(f"Order {order_id} cancelled successfully")
                return True
            else:
                logger.error(f"Order cancellation failed: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Order cancellation error: {e}")
            return False

    def modify_order(self, order_id: str, variety: str = 'regular', **kwargs) -> bool:
        """Modify an order"""
        try:
            response = self.session.put(
                f"{self.BASE_URL}/orders/{variety}/{order_id}",
                data=kwargs
            )

            if response.status_code == 200:
                logger.info(f"Order {order_id} modified successfully")
                return True
            else:
                logger.error(f"Order modification failed: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Order modification error: {e}")
            return False


class UpstoxAdapter(BrokerAdapter):
    """
    Upstox API Adapter
    Popular low-cost broker with good API
    """

    BASE_URL = "https://api.upstox.com/v2"

    def __init__(self, api_key: str, api_secret: str, access_token: Optional[str] = None):
        super().__init__(api_key, api_secret)
        if access_token:
            self.access_token = access_token
            self.session.headers.update({
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            })

    def authenticate(self) -> bool:
        """Authenticate with Upstox"""
        # Upstox uses OAuth 2.0
        # This requires user interaction for authorization
        logger.info("Upstox requires OAuth 2.0 authentication via web flow")
        return self.access_token is not None

    def place_order(self, symbol: str, transaction_type: TransactionType,
                   quantity: int, order_type: OrderType = OrderType.MARKET,
                   price: float = 0, product: ProductType = ProductType.MIS,
                   **kwargs) -> OrderResponse:
        """Place order on Upstox"""
        self.rate_limiter.check_limit('place_order')

        try:
            order_data = {
                'quantity': quantity,
                'product': product.value,
                'validity': 'DAY',
                'price': price if order_type == OrderType.LIMIT else 0,
                'tag': kwargs.get('tag', 'algo_trade'),
                'instrument_token': f"NSE_EQ|{symbol}",  # Simplified
                'order_type': order_type.value,
                'transaction_type': transaction_type.value,
                'disclosed_quantity': kwargs.get('disclosed_quantity', 0),
                'trigger_price': kwargs.get('trigger_price', 0),
                'is_amo': False
            }

            response = self.session.post(
                f"{self.BASE_URL}/order/place",
                json=order_data
            )

            if response.status_code == 200:
                data = response.json()
                order_id = data['data']['order_id']

                return OrderResponse(
                    order_id=str(order_id),
                    status=OrderStatus.PENDING,
                    message="Order placed successfully"
                )
            else:
                return OrderResponse(
                    order_id="",
                    status=OrderStatus.REJECTED,
                    message=response.text
                )

        except Exception as e:
            logger.error(f"Upstox order error: {e}")
            return OrderResponse(order_id="", status=OrderStatus.REJECTED, message=str(e))

    def get_quote(self, symbol: str) -> Dict:
        """Get quote from Upstox"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/market-quote/quotes",
                params={'symbol': f"NSE_EQ|{symbol}"}
            )

            if response.status_code == 200:
                data = response.json()
                quote = data['data'][f"NSE_EQ|{symbol}"]

                return {
                    'symbol': symbol,
                    'last_price': quote['last_price'],
                    'volume': quote['volume'],
                    'open': quote['ohlc']['open'],
                    'high': quote['ohlc']['high'],
                    'low': quote['ohlc']['low'],
                    'close': quote['ohlc']['close']
                }
            else:
                return {}

        except Exception as e:
            logger.error(f"Upstox quote error: {e}")
            return {}

    def get_positions(self) -> List[Dict]:
        """Get positions from Upstox"""
        try:
            response = self.session.get(f"{self.BASE_URL}/portfolio/short-term-positions")

            if response.status_code == 200:
                return response.json()['data']
            return []

        except Exception as e:
            logger.error(f"Upstox positions error: {e}")
            return []

    def get_orders(self) -> List[Dict]:
        """Get orders from Upstox"""
        try:
            response = self.session.get(f"{self.BASE_URL}/order/retrieve-all")

            if response.status_code == 200:
                return response.json()['data']
            return []

        except Exception as e:
            logger.error(f"Upstox orders error: {e}")
            return []

    def cancel_order(self, order_id: str) -> bool:
        """Cancel order on Upstox"""
        try:
            response = self.session.delete(f"{self.BASE_URL}/order/cancel?order_id={order_id}")
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Upstox cancel error: {e}")
            return False

    def modify_order(self, order_id: str, **kwargs) -> bool:
        """Modify order on Upstox"""
        try:
            response = self.session.put(f"{self.BASE_URL}/order/modify", json={'order_id': order_id, **kwargs})
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Upstox modify error: {e}")
            return False


class AngelOneAdapter(BrokerAdapter):
    """
    Angel One (Angel Broking) API Adapter
    SmartAPI for algorithmic trading
    """

    BASE_URL = "https://apiconnect.angelbroking.com"

    def __init__(self, api_key: str, client_id: str, password: str, totp_secret: Optional[str] = None):
        super().__init__(api_key, "")
        self.client_id = client_id
        self.password = password
        self.totp_secret = totp_secret
        self.feed_token = None

    def authenticate(self) -> bool:
        """Authenticate with Angel One"""
        try:
            # Login
            login_data = {
                'clientcode': self.client_id,
                'password': self.password
            }

            if self.totp_secret:
                # Generate TOTP
                import pyotp
                totp = pyotp.TOTP(self.totp_secret)
                login_data['totp'] = totp.now()

            response = self.session.post(
                f"{self.BASE_URL}/rest/auth/angelbroking/user/v1/loginByPassword",
                json=login_data,
                headers={'X-ClientLocalIP': '127.0.0.1', 'X-ClientPublicIP': '127.0.0.1',
                        'X-MACAddress': '00:00:00:00:00:00', 'Content-Type': 'application/json',
                        'Accept': 'application/json', 'X-PrivateKey': self.api_key}
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data['data']['jwtToken']
                self.feed_token = data['data']['feedToken']

                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-UserType': 'USER',
                    'X-SourceID': 'WEB',
                    'X-ClientLocalIP': '127.0.0.1',
                    'X-ClientPublicIP': '127.0.0.1',
                    'X-MACAddress': '00:00:00:00:00:00',
                    'X-PrivateKey': self.api_key
                })

                logger.info("Angel One authentication successful")
                return True
            else:
                logger.error(f"Angel One auth failed: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Angel One auth error: {e}")
            return False

    def place_order(self, symbol: str, transaction_type: TransactionType,
                   quantity: int, order_type: OrderType = OrderType.MARKET,
                   price: float = 0, product: ProductType = ProductType.MIS,
                   **kwargs) -> OrderResponse:
        """Place order on Angel One"""
        try:
            order_params = {
                'variety': 'NORMAL',
                'tradingsymbol': symbol,
                'symboltoken': kwargs.get('symbol_token', ''),  # Required
                'transactiontype': transaction_type.value,
                'exchange': kwargs.get('exchange', 'NSE'),
                'ordertype': order_type.value,
                'producttype': product.value,
                'duration': 'DAY',
                'price': str(price) if order_type == OrderType.LIMIT else '0',
                'squareoff': '0',
                'stoploss': '0',
                'quantity': str(quantity)
            }

            response = self.session.post(
                f"{self.BASE_URL}/rest/secure/angelbroking/order/v1/placeOrder",
                json=order_params
            )

            if response.status_code == 200:
                data = response.json()
                if data['status']:
                    order_id = data['data']['orderid']
                    return OrderResponse(
                        order_id=str(order_id),
                        status=OrderStatus.PENDING,
                        message=data['message']
                    )

            return OrderResponse(order_id="", status=OrderStatus.REJECTED, message=response.text)

        except Exception as e:
            logger.error(f"Angel One order error: {e}")
            return OrderResponse(order_id="", status=OrderStatus.REJECTED, message=str(e))

    def get_quote(self, symbol: str) -> Dict:
        """Get quote (simplified)"""
        return {}

    def get_positions(self) -> List[Dict]:
        """Get positions"""
        try:
            response = self.session.get(f"{self.BASE_URL}/rest/secure/angelbroking/order/v1/getPosition")

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            return []

        except Exception as e:
            logger.error(f"Angel One positions error: {e}")
            return []

    def get_orders(self) -> List[Dict]:
        """Get orders"""
        try:
            response = self.session.get(f"{self.BASE_URL}/rest/secure/angelbroking/order/v1/getOrderBook")

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            return []

        except Exception as e:
            logger.error(f"Angel One orders error: {e}")
            return []

    def cancel_order(self, order_id: str, variety: str = 'NORMAL') -> bool:
        """Cancel order"""
        try:
            response = self.session.post(
                f"{self.BASE_URL}/rest/secure/angelbroking/order/v1/cancelOrder",
                json={'variety': variety, 'orderid': order_id}
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Angel One cancel error: {e}")
            return False

    def modify_order(self, order_id: str, **kwargs) -> bool:
        """Modify order"""
        try:
            response = self.session.post(
                f"{self.BASE_URL}/rest/secure/angelbroking/order/v1/modifyOrder",
                json={'orderid': order_id, **kwargs}
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Angel One modify error: {e}")
            return False


class RateLimiter:
    """
    Rate limiter to prevent API throttling
    """

    def __init__(self):
        self.limits = {
            'place_order': {'max_calls': 100, 'time_window': 60, 'calls': []},
            'get_quote': {'max_calls': 200, 'time_window': 60, 'calls': []}
        }

    def check_limit(self, operation: str):
        """Check if operation is within rate limits"""
        if operation not in self.limits:
            return

        limit_config = self.limits[operation]
        current_time = time.time()

        # Remove calls outside time window
        limit_config['calls'] = [t for t in limit_config['calls']
                                 if current_time - t < limit_config['time_window']]

        # Check if limit exceeded
        if len(limit_config['calls']) >= limit_config['max_calls']:
            sleep_time = limit_config['time_window'] - (current_time - limit_config['calls'][0])
            logger.warning(f"Rate limit reached for {operation}. Sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        # Record this call
        limit_config['calls'].append(current_time)


if __name__ == "__main__":
    logger.info("Broker Integrations - Production Grade")

    # Example: Zerodha adapter (requires actual credentials)
    # zerodha = ZerodhaKiteAdapter(api_key="your_api_key", api_secret="your_secret", request_token="request_token")
    # if zerodha.authenticate():
    #     quote = zerodha.get_quote("RELIANCE")
    #     print(f"RELIANCE LTP: ₹{quote['last_price']}")

    print("Broker adapters initialized. Configure with your API credentials to use.")
