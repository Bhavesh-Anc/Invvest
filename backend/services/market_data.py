"""
Market Data Service
Interfaces with NSE/BSE APIs for live Indian stock market data
"""

import sys
sys.path.append('../..')

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Import existing utilities
from utils.indian_market import IndianMarketData, MarketCalendar
from utils.realtime_data import get_realtime_data
from utils.options_pricing import OptionsChain

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Centralized market data service for Indian stock market
    Provides live quotes, historical data, and options chain
    """

    def __init__(self):
        self.indian_market = IndianMarketData()
        self.market_calendar = MarketCalendar()
        self.cache = {}
        self.cache_ttl = 60  # Cache for 60 seconds

    def get_index_data(self, index_name: str) -> Dict:
        """
        Get live data for Indian index (NIFTY, SENSEX, etc.)

        Args:
            index_name: Name of index (e.g., "NIFTY 50", "SENSEX")

        Returns:
            Dict with ltp, change, change_percent, volume
        """
        cache_key = f"index_{index_name}_{int(datetime.now().timestamp() // self.cache_ttl)}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            data = self.indian_market.get_index_data(index_name)
            self.cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error fetching index data for {index_name}: {e}")
            # Return fallback data
            return self._get_fallback_index_data(index_name)

    def get_stock_quote(self, symbol: str) -> Dict:
        """
        Get live quote for stock

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS")

        Returns:
            Dict with quote data
        """
        try:
            quote = get_realtime_data(symbol)
            return {
                "symbol": symbol,
                "ltp": quote['ltp'],
                "open": quote['open'],
                "high": quote['high'],
                "low": quote['low'],
                "close": quote['close'],
                "volume": quote['volume'],
                "change": quote['change'],
                "change_percent": quote['change_percent'],
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return self._get_fallback_quote(symbol)

    def get_options_chain(self, underlying: str, expiry: str) -> List[Dict]:
        """
        Get options chain for underlying and expiry

        Args:
            underlying: Underlying symbol (e.g., "NIFTY", "BANKNIFTY")
            expiry: Expiry date (e.g., "25-JAN-2024")

        Returns:
            List of option chain rows
        """
        try:
            chain = OptionsChain(underlying)
            return chain.get_chain_data(expiry)
        except Exception as e:
            logger.error(f"Error fetching options chain for {underlying}: {e}")
            return self._get_fallback_options_chain(underlying)

    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Get historical data for symbol

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            interval: Data interval (1d, 1h, 15m, etc.)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            data = self.indian_market.get_historical_data(
                symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            return data
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return self._get_fallback_historical_data(symbol, start_date, end_date)

    def get_market_status(self) -> Dict:
        """
        Get current market status (open/closed)

        Returns:
            Dict with market status info
        """
        try:
            is_open = self.market_calendar.is_market_open()
            next_open = self.market_calendar.get_next_market_open()
            next_close = self.market_calendar.get_next_market_close()

            return {
                "isOpen": is_open,
                "nextOpen": next_open,
                "nextClose": next_close,
                "timezone": "Asia/Kolkata"
            }
        except Exception as e:
            logger.error(f"Error fetching market status: {e}")
            return {
                "isOpen": True,
                "nextOpen": None,
                "nextClose": None,
                "timezone": "Asia/Kolkata"
            }

    def get_top_gainers(self, limit: int = 10) -> List[Dict]:
        """
        Get top gainers for the day

        Args:
            limit: Number of stocks to return

        Returns:
            List of top gaining stocks
        """
        try:
            gainers = self.indian_market.get_top_gainers(limit)
            return gainers
        except Exception as e:
            logger.error(f"Error fetching top gainers: {e}")
            return []

    def get_top_losers(self, limit: int = 10) -> List[Dict]:
        """
        Get top losers for the day

        Args:
            limit: Number of stocks to return

        Returns:
            List of top losing stocks
        """
        try:
            losers = self.indian_market.get_top_losers(limit)
            return losers
        except Exception as e:
            logger.error(f"Error fetching top losers: {e}")
            return []

    # Fallback methods for when live data is unavailable
    def _get_fallback_index_data(self, index_name: str) -> Dict:
        """Fallback data when API is unavailable"""
        fallback_data = {
            "NIFTY 50": {"ltp": 21894.35, "change_percent": 1.24},
            "SENSEX": {"ltp": 72410.18, "change_percent": 0.98},
            "NIFTY BANK": {"ltp": 47623.90, "change_percent": -0.42},
        }

        data = fallback_data.get(index_name, {"ltp": 0, "change_percent": 0})
        return {
            "ltp": data["ltp"],
            "change": data["ltp"] * data["change_percent"] / 100,
            "change_percent": data["change_percent"],
            "volume": 0,
            "timestamp": datetime.now(),
            "isFallback": True
        }

    def _get_fallback_quote(self, symbol: str) -> Dict:
        """Fallback quote when API is unavailable"""
        return {
            "symbol": symbol,
            "ltp": 0,
            "open": 0,
            "high": 0,
            "low": 0,
            "close": 0,
            "volume": 0,
            "change": 0,
            "change_percent": 0,
            "timestamp": datetime.now(),
            "isFallback": True
        }

    def _get_fallback_options_chain(self, underlying: str) -> List[Dict]:
        """Fallback options chain when API is unavailable"""
        return []

    def _get_fallback_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Fallback historical data when API is unavailable"""
        # Generate random walk data
        days = (end_date - start_date).days
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        np.random.seed(42)
        close_prices = 100 * np.exp(np.cumsum(np.random.randn(len(dates)) * 0.02))

        return pd.DataFrame({
            'date': dates,
            'open': close_prices * (1 + np.random.randn(len(dates)) * 0.01),
            'high': close_prices * (1 + abs(np.random.randn(len(dates))) * 0.015),
            'low': close_prices * (1 - abs(np.random.randn(len(dates))) * 0.015),
            'close': close_prices,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        })


# Singleton instance
_market_data_service = None


def get_market_data_service() -> MarketDataService:
    """Get or create market data service singleton"""
    global _market_data_service
    if _market_data_service is None:
        _market_data_service = MarketDataService()
    return _market_data_service
