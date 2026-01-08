"""
Quantitative Trading Strategies API
Provides statistical arbitrage, mean reversion, and momentum signals
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import pandas as pd
import numpy as np

# Import strategy modules
import sys
sys.path.append('../..')
from strategies.statistical_arbitrage import PairsTrading, MeanReversion, Momentum
from utils.indian_market import IndianMarketData

router = APIRouter()

# Response models
class PairSignal(BaseModel):
    pair: tuple
    signal: str
    z_score: float
    current_spread: float
    explanation: str
    hedge_ratio: float
    timestamp: datetime

class MeanReversionSignal(BaseModel):
    symbol: str
    signal: str
    z_score: float
    bb_position: float
    current_price: float
    sma: float
    upper_band: float
    lower_band: float
    explanation: str
    timestamp: datetime

class MomentumSignal(BaseModel):
    symbol: str
    signal: str
    momentum_score: float
    adj_momentum: float
    returns_12m: float
    volatility: float
    explanation: str
    timestamp: datetime

class BacktestResult(BaseModel):
    pair: str
    total_return_pct: float
    num_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown_pct: float


@router.get("/pairs-trading/find-pairs", response_model=List[Dict])
async def find_cointegrated_pairs():
    """
    Scan market for cointegrated pairs suitable for pairs trading

    Returns:
        List of cointegrated stock pairs with statistics
    """
    try:
        market_data = IndianMarketData()
        pairs_trader = PairsTrading()

        # Fetch historical data for candidate pairs
        price_data = {}
        lookback_days = 180

        for stock1, stock2 in pairs_trader.candidate_pairs:
            try:
                # Fetch historical data
                end_date = datetime.now()
                start_date = end_date - timedelta(days=lookback_days)

                df1 = market_data.get_historical_data(stock1, start_date, end_date)
                df2 = market_data.get_historical_data(stock2, start_date, end_date)

                if not df1.empty and not df2.empty:
                    price_data[stock1] = df1.set_index('date')['close']
                    price_data[stock2] = df2.set_index('date')['close']

            except Exception as e:
                continue

        # Find cointegrated pairs
        cointegrated_pairs = pairs_trader.find_cointegrated_pairs(price_data)

        return cointegrated_pairs

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding pairs: {str(e)}")


@router.get("/pairs-trading/signals/{stock1}/{stock2}", response_model=PairSignal)
async def get_pairs_trading_signal(
    stock1: str,
    stock2: str,
    lookback: int = Query(60, description="Days of history for calculation")
):
    """
    Get current pairs trading signal for a specific pair

    Args:
        stock1: First stock symbol
        stock2: Second stock symbol
        lookback: Lookback period in days

    Returns:
        Trading signal with z-score and recommendations
    """
    try:
        market_data = IndianMarketData()
        pairs_trader = PairsTrading(lookback_period=lookback)

        # Fetch historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback + 60)

        df1 = market_data.get_historical_data(stock1, start_date, end_date)
        df2 = market_data.get_historical_data(stock2, start_date, end_date)

        if df1.empty or df2.empty:
            raise HTTPException(status_code=404, detail="Historical data not available")

        price1 = df1.set_index('date')['close']
        price2 = df2.set_index('date')['close']

        # Test cointegration
        coint_result = pairs_trader.test_cointegration(price1, price2)

        if not coint_result['is_cointegrated']:
            raise HTTPException(
                status_code=400,
                detail=f"Pair {stock1}-{stock2} is not cointegrated (p={coint_result['p_value']:.4f})"
            )

        # Generate signal
        signal = pairs_trader.generate_signals(
            stock1, stock2,
            price1, price2,
            coint_result['hedge_ratio']
        )

        return PairSignal(**signal)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating signal: {str(e)}")


@router.post("/pairs-trading/backtest")
async def backtest_pairs_strategy(
    stock1: str,
    stock2: str,
    lookback_days: int = 180,
    initial_capital: float = 1000000
):
    """
    Backtest pairs trading strategy for a specific pair

    Args:
        stock1: First stock symbol
        stock2: Second stock symbol
        lookback_days: Historical data period
        initial_capital: Starting capital

    Returns:
        Backtest performance metrics
    """
    try:
        market_data = IndianMarketData()
        pairs_trader = PairsTrading()

        # Fetch historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        df1 = market_data.get_historical_data(stock1, start_date, end_date)
        df2 = market_data.get_historical_data(stock2, start_date, end_date)

        price_data = {
            stock1: df1.set_index('date')['close'],
            stock2: df2.set_index('date')['close']
        }

        # Run backtest
        result = pairs_trader.backtest_pair(stock1, stock2, price_data, initial_capital)

        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest error: {str(e)}")


@router.get("/mean-reversion/signals/{symbol}", response_model=MeanReversionSignal)
async def get_mean_reversion_signal(
    symbol: str,
    lookback: int = Query(20, description="Bollinger Bands period")
):
    """
    Get mean reversion signal based on Bollinger Bands

    Args:
        symbol: Stock symbol
        lookback: Period for Bollinger Bands calculation

    Returns:
        Mean reversion trading signal
    """
    try:
        market_data = IndianMarketData()
        mean_rev = MeanReversion(lookback=lookback)

        # Fetch historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback * 3)

        df = market_data.get_historical_data(symbol, start_date, end_date)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")

        prices = df.set_index('date')['close']

        # Generate signal
        signal = mean_rev.generate_signals(symbol, prices)

        return MeanReversionSignal(**signal)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/momentum/signals/{symbol}", response_model=MomentumSignal)
async def get_momentum_signal(symbol: str):
    """
    Get momentum signal for a stock

    Args:
        symbol: Stock symbol

    Returns:
        Momentum trading signal with multi-timeframe analysis
    """
    try:
        market_data = IndianMarketData()
        momentum = Momentum()

        # Fetch historical data (1 year)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        df = market_data.get_historical_data(symbol, start_date, end_date)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")

        prices = df.set_index('date')['close']

        # Generate signal
        signal = momentum.generate_signals(symbol, prices)

        return MomentumSignal(**signal)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/momentum/rankings")
async def get_momentum_rankings(top_n: int = Query(20, description="Number of top stocks")):
    """
    Get top stocks ranked by momentum

    Returns:
        List of stocks with highest momentum scores
    """
    try:
        market_data = IndianMarketData()
        momentum = Momentum()

        # Nifty 50 stocks for screening
        nifty_50 = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
            'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'WIPRO', 'ITC',
            'LT', 'AXISBANK', 'ASIANPAINT', 'MARUTI', 'HCLTECH',
            'ULTRACEMCO', 'BAJFINANCE', 'TITAN', 'SUNPHARMA', 'NESTLEIND',
            'TECHM', 'ONGC', 'POWERGRID', 'NTPC', 'M&M',
            'TATASTEEL', 'BAJAJFINSV', 'ADANIENT', 'JSWSTEEL', 'HINDALCO'
        ]

        # Fetch historical data
        price_data = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        for symbol in nifty_50:
            try:
                df = market_data.get_historical_data(symbol, start_date, end_date)
                if not df.empty:
                    price_data[symbol] = df.set_index('date')['close']
            except:
                continue

        # Rank by momentum
        rankings = momentum.rank_stocks_by_momentum(price_data, top_n)

        return rankings

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/combined-signals/{symbol}")
async def get_combined_signals(symbol: str):
    """
    Get combined signals from all strategies for a stock

    Returns:
        Aggregated trading signals from multiple strategies
    """
    try:
        # Get signals from all strategies
        momentum_sig = await get_momentum_signal(symbol)
        mean_rev_sig = await get_mean_reversion_signal(symbol)

        # Aggregate signals
        signals = {
            'symbol': symbol,
            'momentum': {
                'signal': momentum_sig.signal,
                'score': momentum_sig.momentum_score,
                'explanation': momentum_sig.explanation
            },
            'mean_reversion': {
                'signal': mean_rev_sig.signal,
                'z_score': mean_rev_sig.z_score,
                'explanation': mean_rev_sig.explanation
            },
            'timestamp': datetime.now()
        }

        # Consensus signal
        buy_count = sum([
            momentum_sig.signal == 'buy',
            mean_rev_sig.signal == 'buy'
        ])
        sell_count = sum([
            momentum_sig.signal == 'sell',
            mean_rev_sig.signal == 'sell'
        ])

        if buy_count >= 2:
            signals['consensus'] = 'strong_buy'
        elif buy_count == 1:
            signals['consensus'] = 'buy'
        elif sell_count >= 2:
            signals['consensus'] = 'strong_sell'
        elif sell_count == 1:
            signals['consensus'] = 'sell'
        else:
            signals['consensus'] = 'hold'

        return signals

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
