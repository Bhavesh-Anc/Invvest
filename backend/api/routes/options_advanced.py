"""
Advanced Options Strategies API
Provides volatility arbitrage, gamma scalping, and dispersion trading signals
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import pandas as pd
import numpy as np

# Import strategy modules
import sys
sys.path.append('../..')
from strategies.options_strategies import VolatilityArbitrage, GammaScalping, DispersionTrading, VolatilitySurface
from providers.market_data import get_market_data_provider
from utils.options_pricing import BlackScholes

router = APIRouter()

# Request/Response models
class VolatilityForecastRequest(BaseModel):
    symbol: str
    method: str = 'ewma'  # ewma, garch, historical
    lookback_days: int = 30

class PositionSizeRequest(BaseModel):
    capital: float
    option_price: float
    vega: float
    max_vega_exposure: float = 50000

class GammaScalpingRequest(BaseModel):
    option_price: float
    implied_vol: float
    spot_prices: List[float]
    gamma: float
    initial_delta: float
    transaction_cost: float = 10

class DispersionRequest(BaseModel):
    index: str = 'NIFTY'  # NIFTY or BANKNIFTY
    threshold: float = 0.10
    lookback_days: int = 30

class MispricedOption(BaseModel):
    strike: float
    type: str
    signal: str
    implied_vol: float
    forecasted_rv: float
    vol_spread: float
    edge: float
    moneyness: float
    explanation: str
    option_price: float

class GammaScalpingResult(BaseModel):
    total_pnl: float
    gamma_pnl: float
    hedge_pnl: float
    transaction_costs: float
    num_rehedges: int
    implied_vol_paid: float
    realized_vol: float
    vol_profit: float
    profitable: bool

class DispersionSignal(BaseModel):
    signal: str
    index_iv: float
    weighted_stock_iv: float
    implied_correlation: float
    historical_correlation: float
    correlation_spread: float
    edge: float
    explanation: str
    timestamp: datetime


# Volatility Arbitrage Endpoints

@router.get("/volatility-arbitrage/opportunities", response_model=List[MispricedOption])
async def get_volatility_opportunities(
    symbol: str = Query(..., description="Stock symbol (e.g., RELIANCE, TCS)"),
    forecasting_method: str = Query('ewma', description="Method: ewma, garch, or historical")
):
    """
    Find mispriced options based on implied vs realized volatility

    Returns options where |IV - forecasted RV| > threshold
    Buy when IV < RV (option underpriced)
    Sell when IV > RV (option overpriced)
    """
    try:
        provider = get_market_data_provider()
        vol_arb = VolatilityArbitrage()

        # Fetch historical prices
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        df = provider.get_historical_data(
            symbol=symbol,
            exchange="NSE",
            from_date=start_date,
            to_date=end_date,
            interval="day"
        )

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        prices = df.set_index('date')['close']

        # Forecast realized volatility
        forecasted_rv = vol_arb.forecast_realized_volatility(
            prices,
            method=forecasting_method
        )

        # Get current spot price
        spot_price = float(prices.iloc[-1])

        # Get options chain from provider (uses Kite if authenticated, mock otherwise)
        # Get next monthly expiry
        next_month = (datetime.now() + timedelta(days=30)).strftime("%b%y").upper()
        expiry = f"{next_month[:3]}{next_month[3:]}"  # e.g., "JAN24"

        options_chain_raw = provider.get_options_chain(symbol, expiry)

        # Calculate implied volatility from option prices using Black-Scholes
        bs = BlackScholes()
        options_chain = []

        for option in options_chain_raw[:50]:  # Limit to 50 options to avoid overwhelming
            strike = option.get('strike', 0)
            ltp = option.get('ltp', 0)
            option_type = option.get('option_type', 'CE')

            if ltp <= 0 or strike <= 0:
                continue

            # If IV already provided (from Kite), use it
            if 'iv' in option:
                iv = option['iv']
            else:
                # Otherwise, calculate from price (reverse Black-Scholes)
                try:
                    iv = bs.implied_volatility(
                        option_price=ltp,
                        spot_price=spot_price,
                        strike=strike,
                        time_to_maturity=0.0833,  # ~1 month
                        risk_free_rate=0.07,
                        option_type='call' if option_type == 'CE' else 'put'
                    )
                except:
                    # If IV calculation fails, use forecasted RV as baseline
                    iv = forecasted_rv

            options_chain.append({
                'strike': strike,
                'type': 'call' if option_type == 'CE' else 'put',
                'ltp': ltp,
                'implied_volatility': iv
            })

        if not options_chain:
            raise HTTPException(status_code=404, detail=f"No options data found for {symbol}")

        # Find mispriced options
        opportunities = vol_arb.find_mispriced_options(
            options_chain,
            spot_price,
            forecasted_rv,
            threshold=0.05
        )

        return opportunities

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/volatility-arbitrage/forecast/{symbol}")
async def forecast_volatility(
    symbol: str,
    method: str = Query('ewma', description="Forecasting method"),
    lookback: int = Query(30, description="Lookback period in days")
):
    """
    Forecast future realized volatility for a symbol

    Methods:
    - ewma: Exponentially Weighted Moving Average (RiskMetrics λ=0.94)
    - garch: GARCH(1,1) mean reversion model
    - historical: Simple historical average
    """
    try:
        market_data = IndianMarketData()
        vol_arb = VolatilityArbitrage()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=max(lookback * 2, 90))

        df = market_data.get_historical_data(symbol, start_date, end_date)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        prices = df.set_index('date')['close']

        # Calculate current realized volatility
        current_rv = vol_arb.calculate_realized_volatility(prices, lookback)

        # Forecast future volatility
        forecasted_rv = vol_arb.forecast_realized_volatility(
            prices,
            method=method,
            window=lookback
        )

        return {
            'symbol': symbol,
            'current_realized_vol': round(current_rv, 4),
            'forecasted_vol': round(forecasted_rv, 4),
            'method': method,
            'lookback_days': lookback,
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/volatility-arbitrage/position-size")
async def calculate_position_size(request: PositionSizeRequest):
    """
    Calculate optimal number of contracts to trade

    Constraints:
    - Maximum capital allocation
    - Maximum vega exposure
    """
    try:
        vol_arb = VolatilityArbitrage()

        quantity = vol_arb.calculate_position_size(
            capital=request.capital,
            option_price=request.option_price,
            vega=request.vega,
            max_vega_exposure=request.max_vega_exposure
        )

        total_cost = quantity * request.option_price * 50  # NIFTY lot size
        total_vega = quantity * request.vega

        return {
            'optimal_quantity': quantity,
            'total_contracts': quantity,
            'total_cost': round(total_cost, 2),
            'total_vega_exposure': round(total_vega, 2),
            'capital_utilization_pct': round((total_cost / request.capital) * 100, 2),
            'vega_utilization_pct': round((total_vega / request.max_vega_exposure) * 100, 2)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Gamma Scalping Endpoints

@router.post("/gamma-scalping/hedge-ratio")
async def calculate_hedge_ratio(
    options_positions: List[Dict] = Body(..., description="List of options with delta and quantity")
):
    """
    Calculate futures contracts needed for delta-neutral hedge

    Input: List of {delta, quantity} for each option position
    Output: Number of futures contracts to hedge (negative = short)
    """
    try:
        gamma_scalp = GammaScalping()

        hedge_ratio = gamma_scalp.calculate_hedge_ratio(options_positions)

        total_delta = sum(pos['delta'] * pos['quantity'] for pos in options_positions)

        return {
            'total_delta': round(total_delta, 2),
            'futures_contracts_needed': hedge_ratio,
            'direction': 'SHORT' if hedge_ratio < 0 else 'LONG',
            'explanation': f"{'Short' if hedge_ratio < 0 else 'Long'} {abs(hedge_ratio)} NIFTY futures to achieve delta-neutral"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gamma-scalping/simulate", response_model=GammaScalpingResult)
async def simulate_gamma_scalping(request: GammaScalpingRequest):
    """
    Simulate gamma scalping strategy over a price path

    Returns:
    - Total P&L breakdown (gamma, hedge, costs)
    - Number of rehedges
    - Realized vs implied volatility
    - Whether the strategy was profitable
    """
    try:
        gamma_scalp = GammaScalping(rehedge_threshold=0.1)

        spot_prices = pd.Series(request.spot_prices)

        result = gamma_scalp.simulate_gamma_scalping(
            initial_option_price=request.option_price,
            implied_vol=request.implied_vol,
            spot_prices=spot_prices,
            gamma=request.gamma,
            initial_delta=request.initial_delta,
            transaction_cost=request.transaction_cost
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gamma-scalping/optimize-rehedge")
async def optimize_rehedge_threshold(
    transaction_cost: float = Query(..., description="Cost per rehedge (₹)"),
    gamma: float = Query(..., description="Option gamma"),
    realized_vol: float = Query(..., description="Expected realized volatility")
):
    """
    Calculate optimal delta threshold for rehedging

    Balances:
    - Gamma P&L (benefit from rehedging)
    - Transaction costs (cost of rehedging)
    """
    try:
        gamma_scalp = GammaScalping()

        optimal_threshold = gamma_scalp.optimize_rehedge_frequency(
            transaction_cost=transaction_cost,
            gamma=gamma,
            realized_vol=realized_vol
        )

        return {
            'optimal_delta_threshold': round(optimal_threshold, 3),
            'explanation': f"Rehedge when delta deviation exceeds {optimal_threshold:.3f}",
            'trade_off': 'Lower threshold = more frequent rehedging = higher costs but better gamma capture'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Dispersion Trading Endpoints

@router.get("/dispersion/opportunity", response_model=DispersionSignal)
async def get_dispersion_opportunity(request: DispersionRequest = None):
    """
    Find dispersion trading opportunities

    Compares:
    - Index volatility (NIFTY/BANKNIFTY)
    - Weighted component volatilities
    - Implied vs realized correlation

    Signal:
    - buy_dispersion: Sell index vol, Buy stock vol (implied corr > realized)
    - sell_dispersion: Buy index vol, Sell stock vol (implied corr < realized)
    """
    try:
        dispersion = DispersionTrading()
        market_data = IndianMarketData()

        # Get NIFTY 50 stocks
        stocks = market_data.get_nifty_50_stocks()[:10]  # Top 10 for demo

        # Mock index and stock IVs (in production, fetch from NSE)
        index_iv = 0.15  # 15% NIFTY IV

        stock_ivs = {}
        for stock in stocks:
            # Simulate: individual stocks have higher vol than index
            stock_ivs[stock] = index_iv * np.random.uniform(1.1, 1.4)

        # Calculate historical correlation
        # In production, fetch actual returns and calculate correlation
        historical_corr = 0.65  # Typical NIFTY constituent correlation

        # Find opportunity
        signal = dispersion.find_dispersion_opportunity(
            index_iv=index_iv,
            stock_ivs=stock_ivs,
            historical_correlation=historical_corr,
            threshold=0.10
        )

        return signal

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dispersion/correlation")
async def calculate_correlation(
    index: str = Query('NIFTY', description="Index name (NIFTY or BANKNIFTY)"),
    lookback_days: int = Query(30, description="Lookback period")
):
    """
    Calculate implied and realized correlation

    Implied correlation: Derived from index IV and component IVs
    Realized correlation: Calculated from historical returns
    """
    try:
        dispersion = DispersionTrading()
        market_data = IndianMarketData()

        # Get index and stock data
        index_symbol = 'NIFTY 50' if index == 'NIFTY' else 'NIFTY BANK'
        stocks = market_data.get_nifty_50_stocks()[:10]

        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # Mock IV data
        index_iv = 0.15
        stock_ivs = {stock: 0.20 for stock in stocks}

        # Calculate weighted stock IV
        weighted_iv = dispersion.calculate_weighted_stock_iv(stock_ivs)

        # Calculate implied correlation
        implied_corr = dispersion.calculate_implied_correlation(index_iv, weighted_iv)

        # Mock realized correlation (in production, calculate from returns)
        realized_corr = 0.65

        return {
            'index': index,
            'index_iv': round(index_iv, 4),
            'weighted_stock_iv': round(weighted_iv, 4),
            'implied_correlation': round(implied_corr, 4),
            'realized_correlation': round(realized_corr, 4),
            'correlation_spread': round(implied_corr - realized_corr, 4),
            'lookback_days': lookback_days,
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Volatility Surface Endpoints

@router.get("/volatility-surface/skew")
async def calculate_volatility_skew(
    symbol: str = Query(..., description="Underlying symbol"),
    expiry_date: str = Query(..., description="Option expiry date (YYYY-MM-DD)")
):
    """
    Calculate volatility skew for an options chain

    Returns:
    - ITM average IV
    - OTM average IV
    - Skew (ITM - OTM)
    - Skew percentage
    """
    try:
        vol_surface = VolatilitySurface()
        market_data = IndianMarketData()

        # Get current spot price
        quote = market_data.get_live_quote(symbol)
        spot_price = quote['ltp']
        atm_strike = round(spot_price / 50) * 50  # Round to nearest 50

        # Mock options chain (in production, fetch from NSE)
        options_chain = []
        strikes = range(int(atm_strike * 0.90), int(atm_strike * 1.10), 50)

        for strike in strikes:
            # Simulate vol skew: ITM > ATM > OTM
            if strike < atm_strike:
                iv = 0.20  # ITM
            elif strike > atm_strike:
                iv = 0.15  # OTM
            else:
                iv = 0.18  # ATM

            options_chain.append({
                'strike': strike,
                'implied_volatility': iv
            })

        # Calculate skew
        skew_metrics = vol_surface.calculate_volatility_skew(options_chain, atm_strike)

        return {
            'symbol': symbol,
            'atm_strike': atm_strike,
            'spot_price': round(spot_price, 2),
            **skew_metrics,
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/volatility-surface/butterfly-arbitrage")
async def find_butterfly_arbitrage(
    symbol: str = Query(..., description="Underlying symbol"),
    transaction_cost: float = Query(50, description="Total transaction cost for 4-leg trade")
):
    """
    Find butterfly arbitrage opportunities in volatility surface

    Butterfly spread: Buy 1 lower strike, Sell 2 middle strike, Buy 1 upper strike
    Arbitrage exists if butterfly cost < 0 (receive net credit)
    """
    try:
        vol_surface = VolatilitySurface()
        market_data = IndianMarketData()

        # Get spot price
        quote = market_data.get_live_quote(symbol)
        spot_price = quote['ltp']

        # Mock options chain
        options_chain = []
        strikes = range(int(spot_price * 0.95), int(spot_price * 1.05), 50)

        for strike in strikes:
            # Simulate prices (in production, fetch from market)
            moneyness = spot_price / strike
            ltp = max(5, (spot_price - strike) + 50 * (1 - abs(1 - moneyness)))

            options_chain.append({
                'strike': strike,
                'ltp': ltp
            })

        # Find butterfly arbitrage
        opportunities = vol_surface.find_butterfly_arbitrage(
            options_chain,
            transaction_cost=transaction_cost
        )

        return {
            'symbol': symbol,
            'spot_price': round(spot_price, 2),
            'opportunities': opportunities,
            'count': len(opportunities),
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
