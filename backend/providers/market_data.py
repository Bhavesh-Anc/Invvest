"""
Market Data Provider - Unified interface for live and mock data
Automatically switches between Kite API (live) and mock data based on authentication status
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class MarketDataProvider(ABC):
    """Abstract base class for market data providers"""

    @abstractmethod
    def get_quote(self, symbol: str, exchange: str = "NSE") -> Dict:
        """Get live quote for a symbol"""
        pass

    @abstractmethod
    def get_ltp(self, symbol: str, exchange: str = "NSE") -> float:
        """Get last traded price"""
        pass

    @abstractmethod
    def get_historical_data(
        self,
        symbol: str,
        exchange: str,
        from_date: datetime | str,
        to_date: datetime | str,
        interval: str = "day"
    ) -> pd.DataFrame:
        """Get historical OHLC data"""
        pass

    @abstractmethod
    def get_options_chain(self, symbol: str, expiry: str) -> List[Dict]:
        """Get options chain for a symbol"""
        pass

    @abstractmethod
    def search_instruments(self, query: str, exchange: str = "NSE") -> List[Dict]:
        """Search for instruments"""
        pass


class KiteDataProvider(MarketDataProvider):
    """Live market data from Kite Connect API"""

    def __init__(self):
        from integrations.kite_client import get_kite_client
        from config.kite_config import get_kite_config

        config = get_kite_config()
        if not config.has_access_token():
            raise ValueError("Kite API not authenticated. Please login first.")

        self.client = get_kite_client(config.api_key, config.access_token)
        logger.info("KiteDataProvider initialized - LIVE MODE")

    def get_quote(self, symbol: str, exchange: str = "NSE") -> Dict:
        """Get live quote from Kite"""
        try:
            symbol_key = f"{exchange}:{symbol}"
            quotes = self.client.get_quote([symbol_key])
            return quotes.get(symbol_key, {})
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            raise

    def get_ltp(self, symbol: str, exchange: str = "NSE") -> float:
        """Get last traded price from Kite"""
        try:
            symbol_key = f"{exchange}:{symbol}"
            ltp_data = self.client.get_ltp([symbol_key])
            return ltp_data.get(symbol_key, 0.0)
        except Exception as e:
            logger.error(f"Failed to get LTP for {symbol}: {e}")
            raise

    def get_historical_data(
        self,
        symbol: str,
        exchange: str,
        from_date: datetime | str,
        to_date: datetime | str,
        interval: str = "day"
    ) -> pd.DataFrame:
        """Get historical data from Kite"""
        try:
            # Get instrument token
            token = self.client.get_instrument_token(symbol, exchange)
            if not token:
                raise ValueError(f"Symbol {symbol} not found on {exchange}")

            # Fetch data
            df = self.client.get_historical_data(
                instrument_token=token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            return df
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            raise

    def get_options_chain(self, symbol: str, expiry: str) -> List[Dict]:
        """
        Get options chain from Kite
        Note: Kite doesn't have a direct options chain API, so we filter instruments
        """
        try:
            # Get NFO instruments
            instruments = self.client.get_instruments("NFO")

            # Filter for the underlying and expiry
            mask = (
                (instruments['name'] == symbol) &
                (instruments['expiry'].astype(str).str.contains(expiry, na=False))
            )
            options = instruments[mask]

            # Get live quotes for all options
            option_symbols = [f"NFO:{row['tradingsymbol']}" for _, row in options.iterrows()]

            if not option_symbols:
                return []

            # Batch get quotes (max 500 at a time)
            quotes = {}
            for i in range(0, len(option_symbols), 500):
                batch = option_symbols[i:i+500]
                batch_quotes = self.client.get_quote(batch)
                quotes.update(batch_quotes)

            # Combine instrument data with quotes
            chain = []
            for _, row in options.iterrows():
                symbol_key = f"NFO:{row['tradingsymbol']}"
                quote = quotes.get(symbol_key, {})

                chain.append({
                    "symbol": row['tradingsymbol'],
                    "strike": row['strike'],
                    "expiry": str(row['expiry']),
                    "option_type": row['instrument_type'],
                    "ltp": quote.get('last_price', 0),
                    "bid": quote.get('depth', {}).get('buy', [{}])[0].get('price', 0) if quote.get('depth') else 0,
                    "ask": quote.get('depth', {}).get('sell', [{}])[0].get('price', 0) if quote.get('depth') else 0,
                    "volume": quote.get('volume', 0),
                    "oi": quote.get('oi', 0),
                })

            return chain
        except Exception as e:
            logger.error(f"Failed to get options chain for {symbol}: {e}")
            raise

    def search_instruments(self, query: str, exchange: str = "NSE") -> List[Dict]:
        """Search instruments on Kite"""
        try:
            df = self.client.search_instruments(query, exchange)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Failed to search instruments: {e}")
            raise


class MockDataProvider(MarketDataProvider):
    """Mock data provider for testing without Kite API"""

    def __init__(self):
        logger.info("MockDataProvider initialized - DEMO MODE")

    def get_quote(self, symbol: str, exchange: str = "NSE") -> Dict:
        """Generate mock quote"""
        base_price = self._get_base_price(symbol)
        return {
            "instrument_token": 123456,
            "last_price": base_price,
            "ohlc": {
                "open": base_price * 0.99,
                "high": base_price * 1.02,
                "low": base_price * 0.98,
                "close": base_price * 1.01,
            },
            "change": np.random.uniform(-2, 2),
            "volume": int(np.random.uniform(100000, 5000000)),
            "oi": int(np.random.uniform(10000, 500000)),
            "depth": {
                "buy": [{"price": base_price * 0.999, "quantity": 100, "orders": 5}],
                "sell": [{"price": base_price * 1.001, "quantity": 100, "orders": 5}],
            }
        }

    def get_ltp(self, symbol: str, exchange: str = "NSE") -> float:
        """Get mock LTP"""
        return self._get_base_price(symbol)

    def get_historical_data(
        self,
        symbol: str,
        exchange: str,
        from_date: datetime | str,
        to_date: datetime | str,
        interval: str = "day"
    ) -> pd.DataFrame:
        """Generate mock historical data"""
        if isinstance(from_date, str):
            from_date = datetime.strptime(from_date, "%Y-%m-%d")
        if isinstance(to_date, str):
            to_date = datetime.strptime(to_date, "%Y-%m-%d")

        # Generate date range
        dates = pd.date_range(start=from_date, end=to_date, freq='D')
        base_price = self._get_base_price(symbol)

        # Generate random walk
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = base_price * np.exp(np.cumsum(returns))

        data = []
        for i, date in enumerate(dates):
            open_price = prices[i] * np.random.uniform(0.99, 1.01)
            close_price = prices[i]
            high_price = max(open_price, close_price) * np.random.uniform(1.0, 1.02)
            low_price = min(open_price, close_price) * np.random.uniform(0.98, 1.0)

            data.append({
                "date": date,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": int(np.random.uniform(100000, 5000000))
            })

        return pd.DataFrame(data)

    def get_options_chain(self, symbol: str, expiry: str) -> List[Dict]:
        """Generate mock options chain"""
        base_price = self._get_base_price(symbol)
        strikes = np.arange(
            base_price * 0.9,
            base_price * 1.1,
            base_price * 0.01
        )

        chain = []
        for strike in strikes:
            for option_type in ["CE", "PE"]:
                # Mock IV and pricing
                moneyness = strike / base_price
                iv = 0.15 + abs(moneyness - 1.0) * 0.5
                intrinsic = max(0, base_price - strike) if option_type == "CE" else max(0, strike - base_price)
                time_value = base_price * iv * 0.1
                ltp = intrinsic + time_value

                chain.append({
                    "symbol": f"{symbol}{expiry}{int(strike)}{option_type}",
                    "strike": strike,
                    "expiry": expiry,
                    "option_type": option_type,
                    "ltp": ltp,
                    "bid": ltp * 0.99,
                    "ask": ltp * 1.01,
                    "volume": int(np.random.uniform(1000, 100000)),
                    "oi": int(np.random.uniform(10000, 500000)),
                    "iv": iv,
                })

        return chain

    def search_instruments(self, query: str, exchange: str = "NSE") -> List[Dict]:
        """Return mock search results"""
        symbols = ["RELIANCE", "TCS", "INFY", "HDFC", "ICICI", "SBIN", "ITC"]
        matches = [s for s in symbols if query.upper() in s]

        return [
            {
                "tradingsymbol": symbol,
                "name": f"{symbol} LTD",
                "exchange": exchange,
                "instrument_token": hash(symbol) % 1000000,
                "tick_size": 0.05,
                "lot_size": 1,
            }
            for symbol in matches[:5]
        ]

    def _get_base_price(self, symbol: str) -> float:
        """Get base price for a symbol"""
        price_map = {
            "NIFTY": 21500,
            "NIFTY 50": 21500,
            "NIFTY BANK": 46000,
            "BANKNIFTY": 46000,
            "RELIANCE": 2450,
            "TCS": 3650,
            "INFY": 1520,
            "HDFC": 2750,
            "ICICI": 1050,
            "SBIN": 620,
        }
        return price_map.get(symbol.upper(), 1000 + hash(symbol) % 10000)


# ===== Singleton Provider Management =====

_provider_instance: Optional[MarketDataProvider] = None
_provider_mode: str = "auto"  # auto, live, mock


def get_market_data_provider() -> MarketDataProvider:
    """
    Get market data provider (singleton)

    Returns live Kite provider if authenticated, otherwise mock provider
    """
    global _provider_instance, _provider_mode

    if _provider_instance is not None:
        return _provider_instance

    # Auto mode: try Kite first, fallback to mock
    if _provider_mode == "auto":
        try:
            from config.kite_config import get_kite_config
            config = get_kite_config()
            if config.has_access_token():
                _provider_instance = KiteDataProvider()
                logger.info("Using KiteDataProvider (LIVE MODE)")
            else:
                _provider_instance = MockDataProvider()
                logger.info("Using MockDataProvider (DEMO MODE) - Kite not authenticated")
        except Exception as e:
            logger.warning(f"Failed to initialize Kite provider: {e}. Using mock data.")
            _provider_instance = MockDataProvider()

    elif _provider_mode == "live":
        _provider_instance = KiteDataProvider()

    elif _provider_mode == "mock":
        _provider_instance = MockDataProvider()

    return _provider_instance


def set_provider_mode(mode: str):
    """
    Set market data provider mode

    Args:
        mode: "auto" (try live, fallback to mock), "live" (Kite only), or "mock" (demo only)
    """
    global _provider_instance, _provider_mode

    if mode not in ["auto", "live", "mock"]:
        raise ValueError("Mode must be 'auto', 'live', or 'mock'")

    _provider_mode = mode
    _provider_instance = None  # Reset to force re-initialization
    logger.info(f"Market data provider mode set to: {mode}")


def reset_provider():
    """Reset provider instance (useful for testing)"""
    global _provider_instance
    _provider_instance = None
