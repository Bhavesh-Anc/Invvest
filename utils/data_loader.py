# utils/data_loader_updated.py
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging
from datetime import datetime, timedelta
import os
import sqlite3
from pathlib import Path
import hashlib
from tqdm import tqdm
import warnings
import json
import sys
from typing import Optional, Dict, List, Tuple
import pickle

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)

# ==================== INDIVIDUAL STOCK DATA CONFIGURATION ====================

INDIVIDUAL_DATA_CONFIG = {
    'default_period': '15y',
    'max_period': '20y',
    'default_interval': '1d',
    'max_workers': 4,
    'retry_attempts': 3,
    'retry_delay': 2,
    'cache_enabled': True,
    'cache_duration_hours': 24,
    'request_delay': 0.2,
    'timeout': 30,
    'validate_data': True,
    'use_database': True,
    'data_quality_threshold': 0.7,
    'min_data_points': 200,
    'database_path': 'data/individual_stocks.db'
}

# ==================== INDIVIDUAL STOCK DATA MANAGER ====================

class IndividualStockDataManager:
    """Enhanced data manager for individual stock operations"""
    
    def __init__(self, database_path: str = None):
        self.database_path = database_path or INDIVIDUAL_DATA_CONFIG['database_path']
        self.ensure_database_directory()
        self.init_database()
        self.cache_stats = {'hits': 0, 'misses': 0, 'errors': 0}
    
    def ensure_database_directory(self):
        """Ensure database directory exists"""
        db_dir = Path(self.database_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def init_database(self):
        """Initialize database tables for individual stocks"""
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Individual stock data table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS individual_stock_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        date TEXT NOT NULL,
                        open_price REAL,
                        high_price REAL,
                        low_price REAL,
                        close_price REAL,
                        adj_close_price REAL,
                        volume INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, date)
                    )
                """)
                
                # Stock metadata table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS stock_metadata (
                        symbol TEXT PRIMARY KEY,
                        company_name TEXT,
                        sector TEXT,
                        industry TEXT,
                        market_cap REAL,
                        last_updated TIMESTAMP,
                        data_quality_score REAL,
                        total_records INTEGER,
                        earliest_date TEXT,
                        latest_date TEXT,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                
                # Data quality tracking
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_quality_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT,
                        check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        quality_score REAL,
                        issues_found TEXT,
                        records_checked INTEGER
                    )
                """)
                
                # Create indices for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_symbol_date ON individual_stock_data(symbol, date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_symbol ON individual_stock_data(symbol)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_metadata_symbol ON stock_metadata(symbol)")
                
                logging.info("✅ Individual stock database initialized successfully")
                
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            raise
    
    def fetch_and_cache_stock(self, symbol: str, period: str = None, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch and cache individual stock data"""
        
        period = period or INDIVIDUAL_DATA_CONFIG['default_period']
        
        # Check if data exists and is fresh (unless force refresh)
        if not force_refresh:
            cached_data = self.load_stock_data(symbol)
            if not cached_data.empty and self.is_data_fresh(symbol):
                logging.info(f"📊 Using cached data for {symbol}")
                self.cache_stats['hits'] += 1
                return cached_data
        
        # Fetch fresh data
        try:
            logging.info(f"🔄 Fetching fresh data for {symbol} ({period})")
            
            # Fetch from yfinance
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, auto_adjust=True, prepost=True)
            
            if data.empty:
                logging.warning(f"❌ No data retrieved for {symbol}")
                self.cache_stats['errors'] += 1
                return pd.DataFrame()
            
            # Validate data quality
            if INDIVIDUAL_DATA_CONFIG['validate_data']:
                data = self.validate_and_clean_data(data, symbol)
            
            # Cache the data
            if not data.empty:
                self.cache_stock_data(symbol, data)
                self.update_stock_metadata(symbol, data)
                logging.info(f"✅ Cached {len(data)} records for {symbol}")
                self.cache_stats['misses'] += 1
            
            return data
            
        except Exception as e:
            logging.error(f"Failed to fetch data for {symbol}: {e}")
            self.cache_stats['errors'] += 1
            return pd.DataFrame()
    
    def validate_and_clean_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Validate and clean stock data"""
        
        if data.empty:
            return data
        
        original_length = len(data)
        issues = []
        
        try:
            # Ensure required columns exist
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                issues.append(f"Missing columns: {missing_columns}")
                return pd.DataFrame()
            
            # Remove rows with invalid OHLC data
            invalid_ohlc = (
                (data['High'] < data['Low']) |
                (data['Open'] > data['High']) | (data['Open'] < data['Low']) |
                (data['Close'] > data['High']) | (data['Close'] < data['Low'])
            )
            
            if invalid_ohlc.any():
                data = data[~invalid_ohlc]
                issues.append(f"Removed {invalid_ohlc.sum()} rows with invalid OHLC")
            
            # Remove zero/negative prices
            zero_negative = (data[['Open', 'High', 'Low', 'Close']] <= 0).any(axis=1)
            if zero_negative.any():
                data = data[~zero_negative]
                issues.append(f"Removed {zero_negative.sum()} rows with zero/negative prices")
            
            # Handle missing values
            if data.isnull().any().any():
                data = data.fillna(method='ffill').fillna(method='bfill')
                issues.append("Filled missing values")
            
            # Remove duplicate dates
            if data.index.duplicated().any():
                data = data[~data.index.duplicated(keep='first')]
                issues.append("Removed duplicate dates")
            
            # Check for minimum data points
            if len(data) < INDIVIDUAL_DATA_CONFIG['min_data_points']:
                issues.append(f"Insufficient data: {len(data)} < {INDIVIDUAL_DATA_CONFIG['min_data_points']}")
            
            # Calculate quality score
            quality_score = len(data) / max(original_length, 1)
            
            # Log data quality
            self.log_data_quality(symbol, quality_score, issues, len(data))
            
            if quality_score < INDIVIDUAL_DATA_CONFIG['data_quality_threshold']:
                logging.warning(f"⚠️ Low quality data for {symbol}: {quality_score:.2f}")
            
            return data
            
        except Exception as e:
            logging.error(f"Data validation failed for {symbol}: {e}")
            return data
    
    def cache_stock_data(self, symbol: str, data: pd.DataFrame):
        """Cache stock data to database"""
        
        if data.empty:
            return
        
        try:
            # Prepare data for insertion
            data_records = []
            for date, row in data.iterrows():
                data_records.append((
                    symbol,
                    date.strftime('%Y-%m-%d'),
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    float(row.get('Adj Close', row['Close'])),
                    int(row['Volume']) if pd.notna(row['Volume']) else 0
                ))
            
            with sqlite3.connect(self.database_path) as conn:
                # Delete existing data for this symbol
                conn.execute("DELETE FROM individual_stock_data WHERE symbol = ?", (symbol,))
                
                # Insert new data
                conn.executemany("""
                    INSERT INTO individual_stock_data 
                    (symbol, date, open_price, high_price, low_price, close_price, adj_close_price, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, data_records)
                
                logging.info(f"💾 Cached {len(data_records)} records for {symbol}")
                
        except Exception as e:
            logging.error(f"Failed to cache data for {symbol}: {e}")
    
    def load_stock_data(self, symbol: str) -> pd.DataFrame:
        """Load stock data from cache"""
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                query = """
                    SELECT date, open_price, high_price, low_price, close_price, adj_close_price, volume
                    FROM individual_stock_data
                    WHERE symbol = ?
                    ORDER BY date
                """
                
                df = pd.read_sql_query(query, conn, params=(symbol,))
                
                if df.empty:
                    return pd.DataFrame()
                
                # Convert to proper format
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                # Rename columns to match yfinance format
                df.rename(columns={
                    'open_price': 'Open',
                    'high_price': 'High',
                    'low_price': 'Low',
                    'close_price': 'Close',
                    'adj_close_price': 'Adj Close',
                    'volume': 'Volume'
                }, inplace=True)
                
                return df
                
        except Exception as e:
            logging.error(f"Failed to load cached data for {symbol}: {e}")
            return pd.DataFrame()
    
    def update_stock_metadata(self, symbol: str, data: pd.DataFrame):
        """Update stock metadata"""
        
        if data.empty:
            return
        
        try:
            # Get additional stock info
            ticker_info = {}
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                ticker_info = {
                    'company_name': info.get('longName', ''),
                    'sector': info.get('sector', ''),
                    'industry': info.get('industry', ''),
                    'market_cap': info.get('marketCap', 0)
                }
            except:
                ticker_info = {
                    'company_name': symbol,
                    'sector': '',
                    'industry': '',
                    'market_cap': 0
                }
            
            # Calculate data quality score
            quality_score = min(1.0, len(data) / INDIVIDUAL_DATA_CONFIG['min_data_points'])
            
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO stock_metadata
                    (symbol, company_name, sector, industry, market_cap, last_updated,
                     data_quality_score, total_records, earliest_date, latest_date, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    ticker_info['company_name'],
                    ticker_info['sector'],
                    ticker_info['industry'],
                    ticker_info['market_cap'],
                    datetime.now().isoformat(),
                    quality_score,
                    len(data),
                    data.index[0].strftime('%Y-%m-%d'),
                    data.index[-1].strftime('%Y-%m-%d'),
                    True
                ))
                
        except Exception as e:
            logging.error(f"Failed to update metadata for {symbol}: {e}")
    
    def log_data_quality(self, symbol: str, quality_score: float, issues: List[str], records_checked: int):
        """Log data quality information"""
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT INTO data_quality_log
                    (symbol, quality_score, issues_found, records_checked)
                    VALUES (?, ?, ?, ?)
                """, (
                    symbol,
                    quality_score,
                    json.dumps(issues),
                    records_checked
                ))
        except Exception as e:
            logging.warning(f"Failed to log data quality for {symbol}: {e}")
    
    def is_data_fresh(self, symbol: str, max_age_hours: int = None) -> bool:
        """Check if cached data is fresh"""
        
        max_age_hours = max_age_hours or INDIVIDUAL_DATA_CONFIG['cache_duration_hours']
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute(
                    "SELECT last_updated FROM stock_metadata WHERE symbol = ?",
                    (symbol,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return False
                
                last_updated = datetime.fromisoformat(result[0])
                age_hours = (datetime.now() - last_updated).total_seconds() / 3600
                
                return age_hours < max_age_hours
                
        except Exception as e:
            logging.warning(f"Failed to check data freshness for {symbol}: {e}")
            return False
    
    def get_available_stocks(self) -> List[str]:
        """Get list of available stocks in cache"""
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute(
                    "SELECT symbol FROM stock_metadata WHERE is_active = TRUE ORDER BY symbol"
                )
                return [row[0] for row in cursor.fetchall()]
        
        except Exception as e:
            logging.error(f"Failed to get available stocks: {e}")
            return []
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get detailed stock information"""
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM stock_metadata WHERE symbol = ?",
                    (symbol,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
        
        except Exception as e:
            logging.error(f"Failed to get stock info for {symbol}: {e}")
            return None
    
    def remove_stock(self, symbol: str):
        """Remove stock from cache"""
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("DELETE FROM individual_stock_data WHERE symbol = ?", (symbol,))
                conn.execute("DELETE FROM stock_metadata WHERE symbol = ?", (symbol,))
                conn.execute("DELETE FROM data_quality_log WHERE symbol = ?", (symbol,))
            
            logging.info(f"🗑️ Removed {symbol} from cache")
            
        except Exception as e:
            logging.error(f"Failed to remove {symbol}: {e}")
    
    def cleanup_old_cache(self, days_old: int = 30):
        """Clean up old cached data"""
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            with sqlite3.connect(self.database_path) as conn:
                # Find old stocks
                cursor = conn.execute(
                    "SELECT symbol FROM stock_metadata WHERE last_updated < ?",
                    (cutoff_date.isoformat(),)
                )
                old_stocks = [row[0] for row in cursor.fetchall()]
                
                # Remove old data
                for symbol in old_stocks:
                    conn.execute("DELETE FROM individual_stock_data WHERE symbol = ?", (symbol,))
                    conn.execute("DELETE FROM stock_metadata WHERE symbol = ?", (symbol,))
                    conn.execute("DELETE FROM data_quality_log WHERE symbol = ?", (symbol,))
                
                logging.info(f"🧹 Cleaned up {len(old_stocks)} old stocks")
                
        except Exception as e:
            logging.error(f"Failed to cleanup old cache: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        
        stats = self.cache_stats.copy()
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Total stocks
                cursor = conn.execute("SELECT COUNT(*) FROM stock_metadata WHERE is_active = TRUE")
                stats['total_stocks'] = cursor.fetchone()[0]
                
                # Total records
                cursor = conn.execute("SELECT COUNT(*) FROM individual_stock_data")
                stats['total_records'] = cursor.fetchone()[0]
                
                # Database size
                stats['database_size_mb'] = Path(self.database_path).stat().st_size / (1024 * 1024)
                
        except Exception as e:
            logging.warning(f"Failed to get cache stats: {e}")
        
        return stats

# ==================== UTILITY FUNCTIONS ====================

def get_individual_stock_data(symbol: str, period: str = '15y', force_refresh: bool = False) -> pd.DataFrame:
    """Get individual stock data (convenience function)"""
    
    manager = IndividualStockDataManager()
    return manager.fetch_and_cache_stock(symbol, period, force_refresh)

def get_multiple_individual_stocks(symbols: List[str], period: str = '15y', 
                                  max_workers: int = 4) -> Dict[str, pd.DataFrame]:
    """Get multiple individual stocks data"""
    
    manager = IndividualStockDataManager()
    results = {}
    
    def fetch_single_stock(symbol):
        return symbol, manager.fetch_and_cache_stock(symbol, period)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {
            executor.submit(fetch_single_stock, symbol): symbol 
            for symbol in symbols
        }
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                symbol_result, data = future.result()
                if not data.empty:
                    results[symbol_result] = data
                time.sleep(INDIVIDUAL_DATA_CONFIG['request_delay'])
            except Exception as e:
                logging.error(f"Failed to fetch {symbol}: {e}")
    
    return results

def refresh_stock_data(symbol: str, manager: IndividualStockDataManager = None) -> pd.DataFrame:
    """Refresh specific stock data"""
    
    if manager is None:
        manager = IndividualStockDataManager()
    
    return manager.fetch_and_cache_stock(symbol, force_refresh=True)

def validate_stock_symbol(symbol: str) -> bool:
    """Validate stock symbol format"""
    
    if not symbol or not isinstance(symbol, str):
        return False
    
    symbol = symbol.upper().strip()
    
    # Basic validation
    if len(symbol) < 2:
        return False
    
    # NSE/BSE format validation
    if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
        return False
    
    # Check for invalid characters
    base_symbol = symbol.replace('.NS', '').replace('.BO', '')
    if not base_symbol.isalnum():
        return False
    
    return True

def search_stocks(query: str, manager: IndividualStockDataManager = None) -> List[str]:
    """Search for stocks (simple implementation)"""
    
    if manager is None:
        manager = IndividualStockDataManager()
    
    available_stocks = manager.get_available_stocks()
    
    # Simple text matching
    query = query.upper()
    matches = [stock for stock in available_stocks if query in stock.upper()]
    
    return matches

def generate_stock_summary(symbols: List[str], manager: IndividualStockDataManager = None) -> pd.DataFrame:
    """Generate summary of multiple stocks"""
    
    if manager is None:
        manager = IndividualStockDataManager()
    
    summary_data = []
    
    for symbol in symbols:
        try:
            stock_info = manager.get_stock_info(symbol)
            if stock_info:
                # Get latest price
                stock_data = manager.load_stock_data(symbol)
                latest_price = stock_data['Close'].iloc[-1] if not stock_data.empty else 0
                
                summary_data.append({
                    'Symbol': symbol,
                    'Company Name': stock_info.get('company_name', symbol)[:30],
                    'Sector': stock_info.get('sector', 'Unknown')[:20],
                    'Latest Price': latest_price,
                    'Market Cap': stock_info.get('market_cap', 0),
                    'Data Quality': stock_info.get('data_quality_score', 0),
                    'Total Records': stock_info.get('total_records', 0),
                    'Last Updated': stock_info.get('last_updated', '')[:10]
                })
        
        except Exception as e:
            logging.warning(f"Failed to get summary for {symbol}: {e}")
    
    return pd.DataFrame(summary_data)

def get_updated_nse_tickers() -> List[str]:
    """Get updated list of NSE tickers"""
    
    # This is a static list for now - in production, you'd fetch from a live source
    major_nse_stocks = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
        "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "LT.NS",
        "ITC.NS", "ASIANPAINT.NS", "MARUTI.NS", "AXISBANK.NS", "BAJFINANCE.NS",
        "WIPRO.NS", "ONGC.NS", "SUNPHARMA.NS", "NESTLEIND.NS", "TECHM.NS",
        "ULTRACEMCO.NS", "TITAN.NS", "POWERGRID.NS", "M&M.NS", "NTPC.NS",
        "HCLTECH.NS", "BAJAJFINSV.NS", "DIVISLAB.NS", "DRREDDY.NS", "TATASTEEL.NS",
        "GRASIM.NS", "CIPLA.NS", "JSWSTEEL.NS", "BRITANNIA.NS", "HEROMOTOCO.NS",
        "EICHERMOT.NS", "COALINDIA.NS", "UPL.NS", "ADANIENT.NS", "APOLLOHOSP.NS",
        "BAJAJ-AUTO.NS", "HDFCLIFE.NS", "SBILIFE.NS", "BPCL.NS", "TATACONSUM.NS",
        "INDUSINDBK.NS", "IOC.NS", "TATAMOTORS.NS", "HINDALCO.NS", "SHREECEM.NS"
    ]
    
    return major_nse_stocks

# ==================== BATCH OPERATIONS ====================

def batch_fetch_stocks(symbols: List[str], period: str = '15y', 
                      max_workers: int = 4, progress_callback=None) -> Dict[str, pd.DataFrame]:
    """Batch fetch multiple stocks with progress tracking"""
    
    manager = IndividualStockDataManager()
    results = {}
    completed = 0
    
    def fetch_with_progress(symbol):
        nonlocal completed
        try:
            data = manager.fetch_and_cache_stock(symbol, period)
            completed += 1
            
            if progress_callback:
                progress_callback(completed, len(symbols), symbol)
            
            return symbol, data
        
        except Exception as e:
            completed += 1
            if progress_callback:
                progress_callback(completed, len(symbols), symbol, error=str(e))
            return symbol, pd.DataFrame()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {
            executor.submit(fetch_with_progress, symbol): symbol 
            for symbol in symbols
        }
        
        for future in as_completed(future_to_symbol):
            symbol, data = future.result()
            if not data.empty:
                results[symbol] = data
            
            # Rate limiting
            time.sleep(INDIVIDUAL_DATA_CONFIG['request_delay'])
    
    return results

def batch_refresh_stocks(symbols: List[str], max_workers: int = 2) -> Dict[str, bool]:
    """Batch refresh multiple stocks"""
    
    manager = IndividualStockDataManager()
    results = {}
    
    def refresh_single(symbol):
        try:
            data = manager.fetch_and_cache_stock(symbol, force_refresh=True)
            return symbol, not data.empty
        except Exception as e:
            logging.error(f"Failed to refresh {symbol}: {e}")
            return symbol, False
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {
            executor.submit(refresh_single, symbol): symbol 
            for symbol in symbols
        }
        
        for future in as_completed(future_to_symbol):
            symbol, success = future.result()
            results[symbol] = success
            time.sleep(INDIVIDUAL_DATA_CONFIG['request_delay'])
    
    return results

# ==================== DATA ANALYSIS UTILITIES ====================

def analyze_stock_data_quality(symbol: str, manager: IndividualStockDataManager = None) -> Dict:
    """Analyze data quality for a stock"""
    
    if manager is None:
        manager = IndividualStockDataManager()
    
    data = manager.load_stock_data(symbol)
    if data.empty:
        return {'symbol': symbol, 'status': 'no_data'}
    
    analysis = {
        'symbol': symbol,
        'total_records': len(data),
        'date_range': {
            'start': data.index[0].strftime('%Y-%m-%d'),
            'end': data.index[-1].strftime('%Y-%m-%d'),
            'days': (data.index[-1] - data.index[0]).days
        },
        'data_completeness': {
            'missing_days': 0,  # Would need market calendar for accurate calculation
            'gaps_detected': len(data) != len(pd.date_range(data.index[0], data.index[-1], freq='D'))
        },
        'price_statistics': {
            'min_price': data['Close'].min(),
            'max_price': data['Close'].max(),
            'avg_price': data['Close'].mean(),
            'price_volatility': data['Close'].pct_change().std()
        },
        'volume_statistics': {
            'min_volume': data['Volume'].min(),
            'max_volume': data['Volume'].max(),
            'avg_volume': data['Volume'].mean(),
            'zero_volume_days': (data['Volume'] == 0).sum()
        }
    }
    
    return analysis

def get_data_health_report(manager: IndividualStockDataManager = None) -> Dict:
    """Get overall data health report"""
    
    if manager is None:
        manager = IndividualStockDataManager()
    
    available_stocks = manager.get_available_stocks()
    cache_stats = manager.get_cache_stats()
    
    health_report = {
        'total_stocks': len(available_stocks),
        'cache_statistics': cache_stats,
        'data_freshness': {},
        'quality_summary': {
            'high_quality': 0,
            'medium_quality': 0,
            'low_quality': 0
        }
    }
    
    # Check freshness and quality
    fresh_count = 0
    for symbol in available_stocks[:20]:  # Check first 20 for performance
        is_fresh = manager.is_data_fresh(symbol)
        if is_fresh:
            fresh_count += 1
        
        stock_info = manager.get_stock_info(symbol)
        if stock_info:
            quality_score = stock_info.get('data_quality_score', 0)
            if quality_score >= 0.8:
                health_report['quality_summary']['high_quality'] += 1
            elif quality_score >= 0.6:
                health_report['quality_summary']['medium_quality'] += 1
            else:
                health_report['quality_summary']['low_quality'] += 1
    
    health_report['data_freshness']['fresh_stocks'] = fresh_count
    health_report['data_freshness']['fresh_percentage'] = fresh_count / len(available_stocks) if available_stocks else 0
    
    return health_report

# ==================== MAIN EXPORTS ====================

__all__ = [
    'IndividualStockDataManager',
    'get_individual_stock_data',
    'get_multiple_individual_stocks',
    'refresh_stock_data',
    'validate_stock_symbol',
    'search_stocks',
    'generate_stock_summary',
    'get_updated_nse_tickers',
    'batch_fetch_stocks',
    'batch_refresh_stocks',
    'analyze_stock_data_quality',
    'get_data_health_report',
    'INDIVIDUAL_DATA_CONFIG'
]
