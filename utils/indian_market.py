"""
Indian Stock Market Data Integration
Supports NSE/BSE data, F&O, Corporate Actions, and Market Calendar
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import requests
from bs4 import BeautifulSoup
import json
import sqlite3
from pathlib import Path
import time

try:
    from jugaad_data.nse import stock_df, index_df, stock_raw
    JUGAAD_AVAILABLE = True
except ImportError:
    JUGAAD_AVAILABLE = False
    logging.warning("jugaad-data not available, using yfinance only")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IndianMarketData:
    """
    Unified data interface for Indian Stock Market (NSE/BSE)
    """

    # NSE Index symbols
    NSE_INDICES = {
        'NIFTY50': '^NSEI',
        'NIFTY100': '^CNX100',
        'NIFTY500': '^CRSLDX',
        'NIFTYBANK': '^NSEBANK',
        'NIFTYMIDCAP': '^NSEMDCP50',
        'NIFTYIT': '^CNXIT',
        'NIFTYPHARMA': '^CNXPHARMA',
        'NIFTYAUTO': '^CNXAUTO',
        'NIFTYFMCG': '^CNXFMCG',
        'NIFTYMETAL': '^CNXMETAL',
        'SENSEX': '^BSESN'
    }

    # NSE Sector mapping
    NSE_SECTORS = {
        'IT': ['INFY', 'TCS', 'WIPRO', 'HCLTECH', 'TECHM', 'LTTS', 'PERSISTENT'],
        'BANKING': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK', 'INDUSINDBK'],
        'PHARMA': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'BIOCON', 'AUROPHARMA'],
        'AUTO': ['MARUTI', 'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'HEROMOTOCO', 'EICHERMOT'],
        'FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR', 'MARICO'],
        'METAL': ['TATASTEEL', 'HINDALCO', 'JSWSTEEL', 'VEDL', 'COALINDIA', 'NMDC'],
        'ENERGY': ['RELIANCE', 'ONGC', 'BPCL', 'IOC', 'GAIL', 'NTPC', 'POWERGRID'],
        'TELECOM': ['BHARTIARTL', 'IDEA', 'TATACOMM']
    }

    def __init__(self, database_path: str = 'data/indian_market.db'):
        """
        Initialize Indian Market Data fetcher

        Args:
            database_path: Path to SQLite database
        """
        self.database_path = database_path
        self.ensure_database_directory()
        self.init_database()

    def ensure_database_directory(self):
        """Ensure database directory exists"""
        db_dir = Path(self.database_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.database_path) as conn:
            # Stock master table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_master (
                    symbol TEXT PRIMARY KEY,
                    company_name TEXT,
                    exchange TEXT,
                    sector TEXT,
                    industry TEXT,
                    isin TEXT,
                    market_cap REAL,
                    listing_date TEXT,
                    is_fno BOOLEAN DEFAULT FALSE,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Options chain data
            conn.execute("""
                CREATE TABLE IF NOT EXISTS options_chain (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    strike_price REAL NOT NULL,
                    option_type TEXT NOT NULL,
                    ltp REAL,
                    open_interest INTEGER,
                    volume INTEGER,
                    bid_price REAL,
                    ask_price REAL,
                    implied_volatility REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, expiry_date, strike_price, option_type, timestamp)
                )
            """)

            # Corporate actions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS corporate_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    ex_date TEXT NOT NULL,
                    record_date TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, action_type, ex_date)
                )
            """)

            # F&O data
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fno_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    instrument_type TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    strike_price REAL,
                    option_type TEXT,
                    ltp REAL,
                    open_interest INTEGER,
                    volume INTEGER,
                    date TEXT NOT NULL,
                    UNIQUE(symbol, instrument_type, expiry_date, strike_price, option_type, date)
                )
            """)

            conn.commit()

    def convert_to_nse_symbol(self, symbol: str) -> str:
        """
        Convert symbol to NSE format for yfinance

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')

        Returns:
            yfinance compatible symbol (e.g., 'RELIANCE.NS')
        """
        symbol = symbol.upper().strip()
        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            return f"{symbol}.NS"  # Default to NSE
        return symbol

    def convert_to_bse_symbol(self, symbol: str) -> str:
        """Convert symbol to BSE format"""
        symbol = symbol.upper().strip()
        if not symbol.endswith('.BO'):
            return f"{symbol}.BO"
        return symbol

    def get_stock_data(self, symbol: str, start_date: str = None,
                      end_date: str = None, exchange: str = 'NSE') -> pd.DataFrame:
        """
        Fetch historical stock data

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            exchange: 'NSE' or 'BSE'

        Returns:
            DataFrame with OHLCV data
        """
        if exchange.upper() == 'NSE':
            symbol = self.convert_to_nse_symbol(symbol)
        else:
            symbol = self.convert_to_bse_symbol(symbol)

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365 * 5)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        try:
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if data.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()

            data = data.reset_index()
            logger.info(f"Fetched {len(data)} records for {symbol}")
            return data

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def get_index_data(self, index_name: str, start_date: str = None,
                      end_date: str = None) -> pd.DataFrame:
        """
        Fetch index data (Nifty, Sensex, etc.)

        Args:
            index_name: Index name (e.g., 'NIFTY50', 'SENSEX')
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with index data
        """
        if index_name.upper() not in self.NSE_INDICES:
            logger.error(f"Unknown index: {index_name}")
            return pd.DataFrame()

        symbol = self.NSE_INDICES[index_name.upper()]
        return self.get_stock_data(symbol.replace('^', ''), start_date, end_date)

    def get_live_quote(self, symbol: str, exchange: str = 'NSE') -> Dict:
        """
        Get real-time quote

        Args:
            symbol: Stock symbol
            exchange: 'NSE' or 'BSE'

        Returns:
            Dictionary with live quote data
        """
        if exchange.upper() == 'NSE':
            symbol = self.convert_to_nse_symbol(symbol)
        else:
            symbol = self.convert_to_bse_symbol(symbol)

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                'symbol': symbol,
                'ltp': info.get('currentPrice', info.get('regularMarketPrice')),
                'open': info.get('open', info.get('regularMarketOpen')),
                'high': info.get('dayHigh', info.get('regularMarketDayHigh')),
                'low': info.get('dayLow', info.get('regularMarketDayLow')),
                'previous_close': info.get('previousClose', info.get('regularMarketPreviousClose')),
                'volume': info.get('volume', info.get('regularMarketVolume')),
                'change': info.get('currentPrice', 0) - info.get('previousClose', 0),
                'change_percent': ((info.get('currentPrice', 0) - info.get('previousClose', 1)) / info.get('previousClose', 1)) * 100,
                'market_cap': info.get('marketCap'),
                'timestamp': datetime.now()
            }

        except Exception as e:
            logger.error(f"Error fetching live quote for {symbol}: {e}")
            return {}

    def get_stock_info(self, symbol: str, exchange: str = 'NSE') -> Dict:
        """
        Get comprehensive stock information

        Args:
            symbol: Stock symbol
            exchange: Exchange name

        Returns:
            Dictionary with stock info
        """
        if exchange.upper() == 'NSE':
            symbol = self.convert_to_nse_symbol(symbol)
        else:
            symbol = self.convert_to_bse_symbol(symbol)

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                'symbol': symbol,
                'company_name': info.get('longName', info.get('shortName')),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'pb_ratio': info.get('priceToBook'),
                'dividend_yield': info.get('dividendYield'),
                'beta': info.get('beta'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                'avg_volume': info.get('averageVolume'),
                'eps': info.get('trailingEps'),
                'book_value': info.get('bookValue'),
                'face_value': info.get('faceValue', 10)  # Default face value
            }

        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            return {}

    def get_sector_stocks(self, sector: str) -> List[str]:
        """
        Get list of stocks in a sector

        Args:
            sector: Sector name (IT, BANKING, etc.)

        Returns:
            List of stock symbols
        """
        sector = sector.upper()
        return self.NSE_SECTORS.get(sector, [])

    def is_market_open(self) -> bool:
        """
        Check if Indian market is currently open

        Returns:
            True if market is open, False otherwise
        """
        now = datetime.now()

        # Check if weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Check trading hours (9:15 AM to 3:30 PM IST)
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        return market_open <= now <= market_close

    def get_next_expiry_dates(self, num_expiries: int = 3) -> List[datetime]:
        """
        Get next F&O expiry dates (last Thursday of month)

        Args:
            num_expiries: Number of expiry dates to return

        Returns:
            List of expiry dates
        """
        expiry_dates = []
        current_date = datetime.now()

        for _ in range(num_expiries):
            # Find last Thursday of current month
            year = current_date.year
            month = current_date.month

            # Get last day of month
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year

            last_day = (datetime(next_year, next_month, 1) - timedelta(days=1))

            # Find last Thursday
            while last_day.weekday() != 3:  # Thursday = 3
                last_day -= timedelta(days=1)

            if last_day > current_date:
                expiry_dates.append(last_day)

            # Move to next month
            if month == 12:
                current_date = datetime(year + 1, 1, 15)
            else:
                current_date = datetime(year, month + 1, 15)

        return expiry_dates

    def get_fno_stocks(self) -> List[str]:
        """
        Get list of stocks available in F&O segment

        Returns:
            List of F&O stock symbols
        """
        # Top liquid F&O stocks in NSE
        fno_stocks = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR',
            'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'LT', 'AXISBANK',
            'BAJFINANCE', 'ASIANPAINT', 'MARUTI', 'HCLTECH', 'SUNPHARMA',
            'TITAN', 'ULTRACEMCO', 'TATAMOTORS', 'TECHM', 'WIPRO', 'NESTLEIND',
            'M&M', 'POWERGRID', 'NTPC', 'BAJAJFINSV', 'ADANIENT', 'ONGC',
            'TATASTEEL', 'COALINDIA', 'INDUSINDBK', 'DRREDDY', 'JSWSTEEL',
            'CIPLA', 'GRASIM', 'HINDALCO', 'BRITANNIA', 'EICHERMOT', 'DIVISLAB'
        ]
        return fno_stocks

    def add_corporate_action(self, symbol: str, action_type: str,
                            ex_date: str, record_date: str = None,
                            details: str = None):
        """
        Add corporate action to database

        Args:
            symbol: Stock symbol
            action_type: Type (DIVIDEND, BONUS, SPLIT, MERGER)
            ex_date: Ex-date
            record_date: Record date
            details: Additional details
        """
        with sqlite3.connect(self.database_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO corporate_actions
                (symbol, action_type, ex_date, record_date, details)
                VALUES (?, ?, ?, ?, ?)
            """, (symbol, action_type, ex_date, record_date, details))
            conn.commit()

    def get_corporate_actions(self, symbol: str = None,
                             start_date: str = None) -> pd.DataFrame:
        """
        Get corporate actions

        Args:
            symbol: Filter by symbol (optional)
            start_date: Filter by date (optional)

        Returns:
            DataFrame with corporate actions
        """
        with sqlite3.connect(self.database_path) as conn:
            query = "SELECT * FROM corporate_actions WHERE 1=1"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            if start_date:
                query += " AND ex_date >= ?"
                params.append(start_date)

            query += " ORDER BY ex_date DESC"

            return pd.read_sql_query(query, conn, params=params)


class MarketCalendar:
    """
    Indian Stock Market Trading Calendar
    """

    # NSE Holidays 2024-2025 (update annually)
    NSE_HOLIDAYS = [
        '2024-01-26',  # Republic Day
        '2024-03-08',  # Maha Shivaratri
        '2024-03-25',  # Holi
        '2024-03-29',  # Good Friday
        '2024-04-11',  # Id-Ul-Fitr
        '2024-04-17',  # Ram Navami
        '2024-04-21',  # Mahavir Jayanti
        '2024-05-01',  # Maharashtra Day
        '2024-05-23',  # Buddha Pournima
        '2024-06-17',  # Bakri Id
        '2024-07-17',  # Moharram
        '2024-08-15',  # Independence Day
        '2024-08-26',  # Janmashtami
        '2024-09-16',  # Milad-Un-Nabi
        '2024-10-02',  # Gandhi Jayanti
        '2024-10-12',  # Dussehra
        '2024-11-01',  # Diwali
        '2024-11-02',  # Diwali (Balipratipada)
        '2024-11-15',  # Gurunanak Jayanti
        '2024-12-25',  # Christmas
        '2025-02-26',  # Maha Shivaratri
        '2025-03-14',  # Holi
        '2025-03-31',  # Id-Ul-Fitr
        '2025-04-10',  # Mahavir Jayanti
        '2025-04-14',  # Ambedkar Jayanti
        '2025-04-18',  # Good Friday
        '2025-05-01',  # Maharashtra Day
        '2025-06-06',  # Bakri Id
        '2025-08-15',  # Independence Day
        '2025-08-27',  # Ganesh Chaturthi
        '2025-10-02',  # Gandhi Jayanti
        '2025-10-21',  # Dussehra
        '2025-11-01',  # Diwali (Balipratipada)
        '2025-11-05',  # Gurunanak Jayanti
        '2025-12-25',  # Christmas
    ]

    @classmethod
    def is_trading_day(cls, date: datetime) -> bool:
        """
        Check if given date is a trading day

        Args:
            date: Date to check

        Returns:
            True if trading day, False otherwise
        """
        # Check weekend
        if date.weekday() >= 5:
            return False

        # Check holidays
        date_str = date.strftime('%Y-%m-%d')
        return date_str not in cls.NSE_HOLIDAYS

    @classmethod
    def get_next_trading_day(cls, date: datetime = None) -> datetime:
        """
        Get next trading day

        Args:
            date: Starting date (default: today)

        Returns:
            Next trading day
        """
        if date is None:
            date = datetime.now()

        next_day = date + timedelta(days=1)
        while not cls.is_trading_day(next_day):
            next_day += timedelta(days=1)

        return next_day


if __name__ == "__main__":
    # Example usage
    market = IndianMarketData()

    # Fetch Reliance data
    data = market.get_stock_data('RELIANCE', start_date='2024-01-01')
    print(f"Fetched {len(data)} records for RELIANCE")

    # Get live quote
    quote = market.get_live_quote('TCS')
    print(f"\nTCS Live Quote: ₹{quote.get('ltp', 'N/A')}")

    # Check market status
    print(f"\nMarket Open: {market.is_market_open()}")

    # Get next expiries
    expiries = market.get_next_expiry_dates(3)
    print(f"\nNext 3 Expiries: {[e.strftime('%Y-%m-%d') for e in expiries]}")
