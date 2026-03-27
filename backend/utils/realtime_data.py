"""
Real-time Data Fetcher
Wrapper function for fetching live market data
"""

import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# Cache to avoid repeated imports
_indian_market = None


def get_indian_market():
    """Get or create IndianMarketData instance"""
    global _indian_market
    if _indian_market is None:
        from utils.indian_market import IndianMarketData
        _indian_market = IndianMarketData()
    return _indian_market


def get_realtime_data(symbol: str) -> Dict:
    """
    Get real-time data for a symbol (stock or index)

    Args:
        symbol: Stock symbol (e.g., "RELIANCE") or index name (e.g., "NIFTY 50")

    Returns:
        Dict with quote data including ltp, open, high, low, close, volume, change, change_percent

    Raises:
        Exception: If unable to fetch data from any source
    """
    try:
        market = get_indian_market()

        # Check if it's an index or stock
        index_names = ["NIFTY", "SENSEX", "BANKNIFTY", "NIFTY BANK", "INDIAVIX", "INDIA VIX"]
        is_index = any(idx in symbol.upper() for idx in index_names)

        if is_index:
            return market.get_index_data(symbol)
        else:
            return market.get_stock_quote(symbol)

    except Exception as e:
        logger.error(f"Error in get_realtime_data for {symbol}: {e}")
        raise


def get_multiple_quotes(symbols: list) -> Dict[str, Dict]:
    """
    Get quotes for multiple symbols efficiently

    Args:
        symbols: List of stock symbols

    Returns:
        Dict mapping symbol to quote data
    """
    results = {}
    market = get_indian_market()

    for symbol in symbols:
        try:
            results[symbol] = get_realtime_data(symbol)
        except Exception as e:
            logger.warning(f"Failed to fetch {symbol}: {e}")
            # Add placeholder for failed fetch
            results[symbol] = {
                "symbol": symbol,
                "ltp": 0.0,
                "change": 0.0,
                "change_percent": 0.0,
                "error": str(e),
                "timestamp": datetime.now()
            }

    return results


def stream_realtime_data(symbols: list, interval_seconds: int = 1):
    """
    Generator that yields real-time data at specified intervals

    Args:
        symbols: List of symbols to stream
        interval_seconds: Update interval in seconds

    Yields:
        Dict of symbol quotes
    """
    import time

    while True:
        yield get_multiple_quotes(symbols)
        time.sleep(interval_seconds)
