"""
Indian Market Data Utilities
Real-time and historical data for NSE/BSE using jugaad-data and yfinance
"""

import logging
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, Optional, List
import pandas as pd
import numpy as np
import pytz

logger = logging.getLogger(__name__)

# Try importing data sources
try:
    from jugaad_data.nse import NSELive, stock_df
    JUGAAD_AVAILABLE = True
except ImportError:
    logger.warning("jugaad-data not available, falling back to yfinance only")
    JUGAAD_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    logger.warning("yfinance not available")
    YFINANCE_AVAILABLE = False


class IndianMarketData:
    """
    Fetches live and historical data for Indian stock market (NSE/BSE)
    Uses jugaad-data as primary source, yfinance as fallback
    """

    def __init__(self):
        self.nse_live = NSELive() if JUGAAD_AVAILABLE else None
        self.ist = pytz.timezone('Asia/Kolkata')

        # Symbol mapping for indices
        self.index_mapping = {
            "NIFTY 50": ("NIFTY", "^NSEI"),
            "NIFTY": ("NIFTY", "^NSEI"),
            "SENSEX": ("SENSEX", "^BSESN"),
            "NIFTY BANK": ("NIFTYBANK", "^NSEBANK"),
            "BANKNIFTY": ("NIFTYBANK", "^NSEBANK"),
            "NIFTY IT": ("NIFTYIT", "^CNXIT"),
            "INDIA VIX": ("INDIAVIX", "^INDIAVIX"),
            "INDIAVIX": ("INDIAVIX", "^INDIAVIX"),
        }

    def get_index_data(self, index_name: str) -> Dict:
        """
        Get live data for Indian index

        Args:
            index_name: Name of index (e.g., "NIFTY 50", "SENSEX")

        Returns:
            Dict with ltp, change, change_percent, volume
        """
        try:
            # Try jugaad-data first
            if JUGAAD_AVAILABLE and self.nse_live:
                jugaad_symbol, yf_symbol = self.index_mapping.get(
                    index_name.upper(),
                    (index_name, f"^{index_name}")
                )

                try:
                    # Get index quote from NSE
                    quote = self.nse_live.index_quote(jugaad_symbol)

                    return {
                        "ltp": float(quote['last']),
                        "change": float(quote['change']),
                        "change_percent": float(quote['pChange']),
                        "open": float(quote.get('open', quote['last'])),
                        "high": float(quote.get('dayHigh', quote['last'])),
                        "low": float(quote.get('dayLow', quote['last'])),
                        "volume": int(quote.get('totalTradedVolume', 0)),
                        "timestamp": datetime.now(self.ist),
                        "source": "NSE Live"
                    }
                except Exception as e:
                    logger.warning(f"jugaad-data failed for {index_name}: {e}")

            # Fallback to yfinance
            if YFINANCE_AVAILABLE:
                _, yf_symbol = self.index_mapping.get(
                    index_name.upper(),
                    (index_name, f"^{index_name}")
                )

                ticker = yf.Ticker(yf_symbol)
                info = ticker.info
                hist = ticker.history(period="1d", interval="1m")

                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev_close = info.get('previousClose', info.get('regularMarketPreviousClose', latest['Close']))

                    ltp = float(latest['Close'])
                    change = ltp - prev_close
                    change_percent = (change / prev_close) * 100 if prev_close else 0

                    return {
                        "ltp": ltp,
                        "change": change,
                        "change_percent": change_percent,
                        "open": float(latest['Open']),
                        "high": float(latest['High']),
                        "low": float(latest['Low']),
                        "volume": int(latest['Volume']),
                        "timestamp": datetime.now(self.ist),
                        "source": "Yahoo Finance"
                    }

        except Exception as e:
            logger.error(f"Error fetching index data for {index_name}: {e}")

        # Return None to trigger fallback in calling code
        raise Exception(f"Unable to fetch data for {index_name}")

    def get_stock_quote(self, symbol: str) -> Dict:
        """
        Get live quote for stock

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS")

        Returns:
            Dict with quote data
        """
        try:
            # Try jugaad-data first (NSE)
            if JUGAAD_AVAILABLE and self.nse_live:
                try:
                    quote = self.nse_live.stock_quote(symbol)
                    price_info = quote['priceInfo']

                    return {
                        "symbol": symbol,
                        "ltp": float(price_info['lastPrice']),
                        "open": float(price_info.get('open', price_info['lastPrice'])),
                        "high": float(price_info.get('intraDayHighLow', {}).get('max', price_info['lastPrice'])),
                        "low": float(price_info.get('intraDayHighLow', {}).get('min', price_info['lastPrice'])),
                        "close": float(price_info.get('close', price_info['lastPrice'])),
                        "volume": int(quote.get('totalTradedVolume', 0)),
                        "change": float(price_info.get('change', 0)),
                        "change_percent": float(price_info.get('pChange', 0)),
                        "timestamp": datetime.now(self.ist),
                        "source": "NSE Live"
                    }
                except Exception as e:
                    logger.warning(f"jugaad-data failed for {symbol}: {e}")

            # Fallback to yfinance
            if YFINANCE_AVAILABLE:
                # Add .NS suffix for NSE stocks
                yf_symbol = f"{symbol}.NS"
                ticker = yf.Ticker(yf_symbol)
                hist = ticker.history(period="1d", interval="1m")

                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev_close = ticker.info.get('previousClose', latest['Close'])

                    ltp = float(latest['Close'])
                    change = ltp - prev_close
                    change_percent = (change / prev_close) * 100 if prev_close else 0

                    return {
                        "symbol": symbol,
                        "ltp": ltp,
                        "open": float(latest['Open']),
                        "high": float(latest['High']),
                        "low": float(latest['Low']),
                        "close": prev_close,
                        "volume": int(latest['Volume']),
                        "change": change,
                        "change_percent": change_percent,
                        "timestamp": datetime.now(self.ist),
                        "source": "Yahoo Finance"
                    }

        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")

        # Return None to trigger fallback in calling code
        raise Exception(f"Unable to fetch quote for {symbol}")

    def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: int = 30,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Get historical data for symbol

        Args:
            symbol: Stock symbol or index name
            start_date: Start date (optional)
            end_date: End date (optional)
            days: Number of days if dates not specified
            interval: Data interval (1d, 1h, etc.)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=days)

            # Try jugaad-data for daily NSE data
            if JUGAAD_AVAILABLE and interval == "1d" and symbol.upper() not in self.index_mapping:
                try:
                    df = stock_df(
                        symbol=symbol,
                        from_date=start_date,
                        to_date=end_date,
                        series="EQ"
                    )

                    if not df.empty:
                        # Rename columns to standard format
                        df = df.rename(columns={
                            'DATE': 'date',
                            'OPEN': 'open',
                            'HIGH': 'high',
                            'LOW': 'low',
                            'CLOSE': 'close',
                            'VOLUME': 'volume'
                        })
                        df['date'] = pd.to_datetime(df['date'])
                        return df[['date', 'open', 'high', 'low', 'close', 'volume']]
                except Exception as e:
                    logger.warning(f"jugaad-data historical failed for {symbol}: {e}")

            # Fallback to yfinance
            if YFINANCE_AVAILABLE:
                # Determine yfinance symbol
                if symbol.upper() in self.index_mapping:
                    _, yf_symbol = self.index_mapping[symbol.upper()]
                else:
                    yf_symbol = f"{symbol}.NS"

                ticker = yf.Ticker(yf_symbol)
                df = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=interval
                )

                if not df.empty:
                    df = df.reset_index()
                    df = df.rename(columns={
                        'Date': 'date',
                        'Datetime': 'date',
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume'
                    })
                    return df[['date', 'open', 'high', 'low', 'close', 'volume']]

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")

        # Return empty DataFrame
        raise Exception(f"Unable to fetch historical data for {symbol}")

    def get_top_gainers(self, limit: int = 10) -> List[Dict]:
        """Get top gaining stocks from NSE"""
        try:
            if JUGAAD_AVAILABLE and self.nse_live:
                gainers = self.nse_live.top_gainers()
                return gainers[:limit] if gainers else []
        except Exception as e:
            logger.error(f"Error fetching top gainers: {e}")
        return []

    def get_top_losers(self, limit: int = 10) -> List[Dict]:
        """Get top losing stocks from NSE"""
        try:
            if JUGAAD_AVAILABLE and self.nse_live:
                losers = self.nse_live.top_losers()
                return losers[:limit] if losers else []
        except Exception as e:
            logger.error(f"Error fetching top losers: {e}")
        return []


class MarketCalendar:
    """
    Indian market calendar and trading hours
    """

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.market_open_time = dt_time(9, 15)  # 9:15 AM IST
        self.market_close_time = dt_time(15, 30)  # 3:30 PM IST

        # NSE holidays for 2026 (update annually)
        self.holidays_2026 = [
            datetime(2026, 1, 26),  # Republic Day
            datetime(2026, 3, 14),  # Holi
            datetime(2026, 3, 30),  # Ram Navami
            datetime(2026, 4, 2),   # Mahavir Jayanti
            datetime(2026, 4, 3),   # Good Friday
            datetime(2026, 4, 10),  # Id-Ul-Fitr
            datetime(2026, 4, 14),  # Dr. Ambedkar Jayanti
            datetime(2026, 5, 1),   # Maharashtra Day
            datetime(2026, 6, 17),  # Bakri Id
            datetime(2026, 8, 15),  # Independence Day
            datetime(2026, 8, 16),  # Parsi New Year
            datetime(2026, 9, 2),   # Ganesh Chaturthi
            datetime(2026, 10, 2),  # Gandhi Jayanti
            datetime(2026, 10, 21), # Dussehra
            datetime(2026, 10, 26), # Diwali Balipratipada
            datetime(2026, 11, 4),  # Guru Nanak Jayanti
            datetime(2026, 12, 25), # Christmas
        ]

    def is_market_open(self, dt: Optional[datetime] = None) -> bool:
        """
        Check if market is currently open

        Args:
            dt: Datetime to check (default: now)

        Returns:
            True if market is open
        """
        if dt is None:
            dt = datetime.now(self.ist)
        else:
            dt = dt.astimezone(self.ist)

        # Check if weekend (Saturday=5, Sunday=6)
        if dt.weekday() >= 5:
            return False

        # Check if holiday
        dt_date = dt.date()
        for holiday in self.holidays_2026:
            if dt_date == holiday.date():
                return False

        # Check if within trading hours
        current_time = dt.time()
        return self.market_open_time <= current_time <= self.market_close_time

    def get_next_market_open(self, dt: Optional[datetime] = None) -> datetime:
        """Get next market open time"""
        if dt is None:
            dt = datetime.now(self.ist)
        else:
            dt = dt.astimezone(self.ist)

        # If market is currently open, return current time
        if self.is_market_open(dt):
            return dt

        # Start from next day if after market close
        if dt.time() > self.market_close_time:
            dt = dt + timedelta(days=1)

        # Find next trading day
        for _ in range(10):  # Check next 10 days
            dt = dt.replace(hour=9, minute=15, second=0, microsecond=0)
            if dt.weekday() < 5 and dt.date() not in [h.date() for h in self.holidays_2026]:
                return dt
            dt = dt + timedelta(days=1)

        return dt

    def get_next_market_close(self, dt: Optional[datetime] = None) -> datetime:
        """Get next market close time"""
        if dt is None:
            dt = datetime.now(self.ist)
        else:
            dt = dt.astimezone(self.ist)

        # If market will close today
        if dt.time() < self.market_close_time and dt.weekday() < 5:
            close_time = dt.replace(hour=15, minute=30, second=0, microsecond=0)
            if close_time.date() not in [h.date() for h in self.holidays_2026]:
                return close_time

        # Otherwise next trading day's close
        next_open = self.get_next_market_open(dt)
        return next_open.replace(hour=15, minute=30, second=0, microsecond=0)
