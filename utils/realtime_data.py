"""
AI Stock Advisor Pro - Real-time Data Provider
Enhanced real-time market data integration
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import json
from config.secrets import FINNHUB_API_KEY, ALPHA_VANTAGE_API_KEY
from config.settings import API_CONFIG, DATA_CONFIG

logging.basicConfig(level=logging.INFO)

class RealTimeDataProvider:
    """Advanced real-time data provider with multiple sources"""

    def __init__(self):
        self.finnhub_key = FINNHUB_API_KEY
        self.alpha_vantage_key = ALPHA_VANTAGE_API_KEY
        self.db_path = "data/realtime_data.db"
        self._init_database()

    def _init_database(self):
        """Initialize real-time data database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS realtime_quotes (
                    symbol TEXT,
                    timestamp DATETIME,
                    price REAL,
                    volume INTEGER,
                    bid REAL,
                    ask REAL,
                    high_24h REAL,
                    low_24h REAL,
                    change_pct REAL,
                    PRIMARY KEY (symbol, timestamp)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_status (
                    market TEXT PRIMARY KEY,
                    is_open BOOLEAN,
                    last_updated DATETIME
                )
            """)

    def get_real_time_quote(self, symbol: str) -> Dict:
        """Get real-time quote for a symbol"""
        try:
            # Try yfinance first (free)
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d", interval="1m")

            if not hist.empty:
                latest = hist.iloc[-1]
                quote = {
                    'symbol': symbol,
                    'price': float(latest['Close']),
                    'volume': int(latest['Volume']),
                    'high': float(hist['High'].max()),
                    'low': float(hist['Low'].min()),
                    'change_pct': float((latest['Close'] - hist.iloc[0]['Open']) / hist.iloc[0]['Open'] * 100),
                    'timestamp': datetime.now(),
                    'source': 'yfinance'
                }

                self._cache_quote(quote)
                return quote

        except Exception as e:
            logging.warning(f"yfinance failed for {symbol}: {e}")

        # Fallback to Finnhub
        return self._get_finnhub_quote(symbol)

    def _get_finnhub_quote(self, symbol: str) -> Dict:
        """Get quote from Finnhub API"""
        if not self.finnhub_key:
            return {}

        try:
            url = f"https://finnhub.io/api/v1/quote"
            params = {'symbol': symbol, 'token': self.finnhub_key}

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if 'c' in data:  # current price
                quote = {
                    'symbol': symbol,
                    'price': float(data['c']),
                    'high': float(data['h']),
                    'low': float(data['l']),
                    'change_pct': float(data['dp']),
                    'timestamp': datetime.now(),
                    'source': 'finnhub'
                }

                self._cache_quote(quote)
                return quote

        except Exception as e:
            logging.error(f"Finnhub API error for {symbol}: {e}")

        return {}

    def get_market_status(self, market: str = 'NSE') -> Dict:
        """Get market open/close status"""
        try:
            # Check cache first
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT is_open, last_updated FROM market_status WHERE market = ?",
                    (market,)
                )
                row = cursor.fetchone()

                if row:
                    last_updated = datetime.fromisoformat(row[1])
                    if (datetime.now() - last_updated).seconds < 300:  # 5 min cache
                        return {
                            'market': market,
                            'is_open': bool(row[0]),
                            'last_updated': last_updated,
                            'cached': True
                        }

            # Get fresh status
            is_open = self._check_market_hours(market)
            status = {
                'market': market,
                'is_open': is_open,
                'last_updated': datetime.now(),
                'cached': False
            }

            # Cache result
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO market_status (market, is_open, last_updated)
                    VALUES (?, ?, ?)
                """, (market, is_open, datetime.now().isoformat()))

            return status

        except Exception as e:
            logging.error(f"Market status error: {e}")
            return {'market': market, 'is_open': False, 'error': str(e)}

    def _check_market_hours(self, market: str) -> bool:
        """Check if market is currently open"""
        now = datetime.now()

        if market == 'NSE':
            # NSE: 9:15 AM to 3:30 PM, Monday to Friday
            if now.weekday() >= 5:  # Weekend
                return False

            market_open = now.replace(hour=9, minute=15, second=0)
            market_close = now.replace(hour=15, minute=30, second=0)

            return market_open <= now <= market_close

        return False  # Default to closed for unknown markets

    def get_intraday_data(self, symbol: str, interval: str = '5m') -> pd.DataFrame:
        """Get intraday data for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval=interval)

            if not data.empty:
                # Add additional metrics
                data['returns'] = data['Close'].pct_change()
                data['vwap'] = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
                data['spread'] = (data['High'] - data['Low']) / data['Close']

                return data

        except Exception as e:
            logging.error(f"Intraday data error for {symbol}: {e}")

        return pd.DataFrame()

    def _cache_quote(self, quote: Dict):
        """Cache real-time quote"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO realtime_quotes 
                    (symbol, timestamp, price, volume, high_24h, low_24h, change_pct)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    quote['symbol'],
                    quote['timestamp'].isoformat(),
                    quote['price'],
                    quote.get('volume', 0),
                    quote.get('high', 0),
                    quote.get('low', 0),
                    quote.get('change_pct', 0)
                ))

        except Exception as e:
            logging.warning(f"Cache error: {e}")

    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get real-time quotes for multiple symbols"""
        quotes = {}

        for symbol in symbols:
            quote = self.get_real_time_quote(symbol)
            if quote:
                quotes[symbol] = quote

            # Rate limiting
            time.sleep(API_CONFIG.get('yfinance_delay', 0.1))

        return quotes

    def get_market_movers(self, market: str = 'NSE', limit: int = 10) -> Dict:
        """Get market movers (gainers/losers)"""
        try:
            # This would typically use a specialized API
            # For now, return mock data structure
            return {
                'gainers': [],
                'losers': [],
                'most_active': [],
                'market': market,
                'timestamp': datetime.now()
            }

        except Exception as e:
            logging.error(f"Market movers error: {e}")
            return {}

class MarketDataStream:
    """Real-time market data streaming"""

    def __init__(self):
        self.provider = RealTimeDataProvider()
        self.subscribers = {}
        self.is_streaming = False

    def subscribe(self, symbol: str, callback):
        """Subscribe to real-time updates for a symbol"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)

    def unsubscribe(self, symbol: str, callback):
        """Unsubscribe from updates"""
        if symbol in self.subscribers:
            try:
                self.subscribers[symbol].remove(callback)
                if not self.subscribers[symbol]:
                    del self.subscribers[symbol]
            except ValueError:
                pass

    def start_streaming(self, update_interval: int = 60):
        """Start real-time data streaming"""
        self.is_streaming = True

        while self.is_streaming:
            try:
                for symbol in self.subscribers:
                    quote = self.provider.get_real_time_quote(symbol)

                    if quote:
                        for callback in self.subscribers[symbol]:
                            try:
                                callback(symbol, quote)
                            except Exception as e:
                                logging.error(f"Callback error for {symbol}: {e}")

                time.sleep(update_interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"Streaming error: {e}")
                time.sleep(5)

        self.is_streaming = False

    def stop_streaming(self):
        """Stop real-time streaming"""
        self.is_streaming = False

# ==================== USAGE EXAMPLE ====================

if __name__ == "__main__":
    provider = RealTimeDataProvider()

    # Test real-time quote
    quote = provider.get_real_time_quote("RELIANCE.NS")
    if quote:
        print(f"Real-time quote for RELIANCE: ₹{quote['price']}")

    # Test market status
    status = provider.get_market_status("NSE")
    print(f"NSE Market Status: {'Open' if status['is_open'] else 'Closed'}")

    # Test intraday data
    intraday = provider.get_intraday_data("TCS.NS", "5m")
    if not intraday.empty:
        print(f"Intraday data for TCS: {len(intraday)} records")
