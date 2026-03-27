"""
Advanced Options Trading Strategies
Used by: Susquehanna (SIG), Optiver, IMC, Citadel Securities

Implements professional options trading strategies:
- Volatility Arbitrage (implied vs realized vol)
- Delta-Neutral Gamma Scalping
- Dispersion Trading (index vs components)
- Greeks-based hedging
- Volatility surface analysis
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from scipy.stats import norm
from scipy.optimize import minimize_scalar

logger = logging.getLogger(__name__)


class VolatilityArbitrage:
    """
    Volatility Arbitrage Strategy

    Used by: Susquehanna (SIG), Jane Street

    Principle:
    - Buy options when implied volatility (IV) < expected realized volatility (RV)
    - Sell options when IV > expected RV
    - Delta hedge to isolate volatility exposure
    - Profit from mean reversion of volatility
    """

    def __init__(self, risk_free_rate: float = 0.07):
        """
        Args:
            risk_free_rate: Annual risk-free rate (7% for India)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_realized_volatility(
        self,
        prices: pd.Series,
        window: int = 30,
        annualize: bool = True
    ) -> float:
        """
        Calculate historical realized volatility

        Args:
            prices: Price series
            window: Lookback window in days
            annualize: Annualize the volatility

        Returns:
            Realized volatility (as decimal, e.g., 0.20 = 20%)
        """
        # Calculate log returns
        returns = np.log(prices / prices.shift(1)).dropna()

        # Recent window
        recent_returns = returns.iloc[-window:]

        # Standard deviation
        vol = recent_returns.std()

        # Annualize (252 trading days)
        if annualize:
            vol = vol * np.sqrt(252)

        return float(vol)

    def forecast_realized_volatility(
        self,
        prices: pd.Series,
        method: str = 'ewma',
        **kwargs
    ) -> float:
        """
        Forecast future realized volatility

        Methods:
        - ewma: Exponentially Weighted Moving Average (RiskMetrics)
        - garch: GARCH(1,1) model
        - historical: Simple historical average

        Args:
            prices: Price series
            method: Forecasting method
            **kwargs: Method-specific parameters

        Returns:
            Forecasted volatility
        """
        returns = np.log(prices / prices.shift(1)).dropna()

        if method == 'ewma':
            # EWMA with lambda = 0.94 (RiskMetrics standard)
            lambda_param = kwargs.get('lambda_param', 0.94)
            variance_forecast = returns.ewm(alpha=1-lambda_param).var().iloc[-1]
            vol_forecast = np.sqrt(variance_forecast * 252)

        elif method == 'historical':
            # Simple historical volatility
            window = kwargs.get('window', 30)
            vol_forecast = self.calculate_realized_volatility(prices, window)

        elif method == 'garch':
            # GARCH(1,1) - simplified implementation
            # In production, use arch library
            window = kwargs.get('window', 60)
            recent_vol = self.calculate_realized_volatility(prices, window)
            long_run_vol = self.calculate_realized_volatility(prices, 252)

            # Mean reversion towards long-run volatility
            alpha = 0.7  # Weight on recent volatility
            vol_forecast = alpha * recent_vol + (1 - alpha) * long_run_vol

        else:
            raise ValueError(f"Unknown method: {method}")

        return float(vol_forecast)

    def find_mispriced_options(
        self,
        options_chain: List[Dict],
        spot_price: float,
        forecasted_rv: float,
        threshold: float = 0.05
    ) -> List[Dict]:
        """
        Find options with mispriced volatility

        Args:
            options_chain: List of options with IVs
            spot_price: Current underlying price
            forecasted_rv: Forecasted realized volatility
            threshold: Minimum IV-RV spread to trade (5% default)

        Returns:
            List of mispriced options with trading signals
        """
        opportunities = []

        for option in options_chain:
            implied_vol = option.get('implied_volatility', 0)
            strike = option.get('strike', 0)
            option_type = option.get('type', 'call')

            # Calculate moneyness
            moneyness = spot_price / strike if strike > 0 else 0

            # Vol spread
            vol_spread = implied_vol - forecasted_rv

            # Mispricing detected
            if abs(vol_spread) > threshold:
                if vol_spread > threshold:
                    # IV > RV: Option overpriced, sell volatility
                    signal = 'sell'
                    edge = vol_spread
                    explanation = f"IV {implied_vol:.1%} > RV {forecasted_rv:.1%}, sell option"

                else:
                    # IV < RV: Option underpriced, buy volatility
                    signal = 'buy'
                    edge = abs(vol_spread)
                    explanation = f"IV {implied_vol:.1%} < RV {forecasted_rv:.1%}, buy option"

                opportunities.append({
                    'strike': strike,
                    'type': option_type,
                    'signal': signal,
                    'implied_vol': implied_vol,
                    'forecasted_rv': forecasted_rv,
                    'vol_spread': vol_spread,
                    'edge': edge,
                    'moneyness': moneyness,
                    'explanation': explanation,
                    'option_price': option.get('ltp', 0)
                })

        # Sort by edge (biggest mispricings first)
        opportunities.sort(key=lambda x: abs(x['edge']), reverse=True)

        return opportunities

    def calculate_vega_pnl(
        self,
        vega: float,
        iv_change: float
    ) -> float:
        """
        Calculate P&L from volatility change

        Args:
            vega: Portfolio vega (per 1% vol change)
            iv_change: Change in implied volatility (in vol points, e.g., 0.02 = 2%)

        Returns:
            P&L from volatility change
        """
        # Vega P&L = Vega * (IV change in percentage points * 100)
        return vega * (iv_change * 100)

    def calculate_position_size(
        self,
        capital: float,
        option_price: float,
        vega: float,
        max_vega_exposure: float = 50000
    ) -> int:
        """
        Calculate optimal number of contracts

        Args:
            capital: Available capital
            option_price: Price per option contract
            vega: Vega per contract
            max_vega_exposure: Maximum portfolio vega

        Returns:
            Number of contracts
        """
        # Max contracts by capital
        max_by_capital = int(capital / (option_price * 50))  # NIFTY lot size = 50

        # Max contracts by vega limit
        max_by_vega = int(max_vega_exposure / abs(vega)) if vega != 0 else max_by_capital

        # Take minimum
        quantity = min(max_by_capital, max_by_vega)

        return max(0, quantity)


class GammaScalping:
    """
    Delta-Neutral Gamma Scalping

    Used by: Citadel Securities, IMC, Optiver

    Strategy:
    1. Buy options (positive gamma)
    2. Maintain delta-neutral by hedging with futures
    3. Profit from realized volatility being higher than paid (IV)
    4. Rehedge as delta changes (gamma effect)
    """

    def __init__(self, rehedge_threshold: float = 0.1):
        """
        Args:
            rehedge_threshold: Delta threshold for rehedging (0.1 = 10 delta)
        """
        self.rehedge_threshold = rehedge_threshold

    def calculate_hedge_ratio(
        self,
        options_positions: List[Dict]
    ) -> float:
        """
        Calculate futures needed to hedge delta

        Args:
            options_positions: List of options with deltas

        Returns:
            Number of futures contracts needed (negative = short)
        """
        total_delta = sum(
            pos.get('delta', 0) * pos.get('quantity', 0)
            for pos in options_positions
        )

        # Each NIFTY future has delta of 50 (lot size)
        # Hedge delta = -Total Delta / 50
        hedge_ratio = -total_delta / 50

        return round(hedge_ratio)

    def check_rehedge_needed(
        self,
        current_delta: float,
        target_delta: float = 0
    ) -> Dict:
        """
        Check if rehedging is needed

        Args:
            current_delta: Current portfolio delta
            target_delta: Target delta (usually 0 for delta-neutral)

        Returns:
            Dict with rehedge decision
        """
        delta_deviation = abs(current_delta - target_delta)

        needs_rehedge = delta_deviation > self.rehedge_threshold

        return {
            'needs_rehedge': needs_rehedge,
            'current_delta': current_delta,
            'target_delta': target_delta,
            'deviation': delta_deviation,
            'threshold': self.rehedge_threshold,
            'action': 'REHEDGE' if needs_rehedge else 'HOLD'
        }

    def calculate_gamma_pnl(
        self,
        gamma: float,
        price_move: float,
        spot_price: float
    ) -> float:
        """
        Calculate P&L from gamma given price movement

        Gamma P&L = 0.5 * Gamma * (ΔS)^2

        Args:
            gamma: Portfolio gamma
            price_move: Price change (absolute)
            spot_price: Current spot price

        Returns:
            P&L from gamma
        """
        return 0.5 * gamma * (price_move ** 2)

    def calculate_hedging_pnl(
        self,
        hedge_quantity: int,
        entry_price: float,
        exit_price: float
    ) -> float:
        """
        Calculate P&L from hedging trades

        Args:
            hedge_quantity: Number of futures contracts
            entry_price: Entry price of hedge
            exit_price: Exit price of hedge

        Returns:
            P&L from hedge
        """
        price_diff = exit_price - entry_price
        lot_size = 50  # NIFTY

        return hedge_quantity * lot_size * price_diff

    def optimize_rehedge_frequency(
        self,
        transaction_cost: float,
        gamma: float,
        realized_vol: float
    ) -> float:
        """
        Optimize rehedging frequency to balance gamma P&L vs transaction costs

        Args:
            transaction_cost: Cost per hedge transaction (₹)
            gamma: Portfolio gamma
            realized_vol: Expected realized volatility

        Returns:
            Optimal delta threshold for rehedging
        """
        # Higher gamma and vol → rehedge more frequently
        # Higher costs → rehedge less frequently

        # Simplified formula
        optimal_threshold = (2 * transaction_cost / (gamma * realized_vol)) ** 0.5

        # Cap between 0.05 and 0.5
        optimal_threshold = max(0.05, min(optimal_threshold, 0.5))

        return float(optimal_threshold)

    def simulate_gamma_scalping(
        self,
        initial_option_price: float,
        implied_vol: float,
        spot_prices: pd.Series,
        gamma: float,
        initial_delta: float,
        transaction_cost: float = 10
    ) -> Dict:
        """
        Simulate gamma scalping strategy

        Args:
            initial_option_price: Option price paid
            implied_vol: IV paid for option
            spot_prices: Realized spot price path
            gamma: Option gamma
            initial_delta: Starting delta
            transaction_cost: Cost per rehedge (₹)

        Returns:
            Simulation results with P&L breakdown
        """
        current_delta = initial_delta
        total_gamma_pnl = 0
        total_hedge_pnl = 0
        total_transaction_costs = 0
        num_rehedges = 0

        hedge_price = spot_prices.iloc[0]

        for i in range(1, len(spot_prices)):
            prev_price = spot_prices.iloc[i-1]
            current_price = spot_prices.iloc[i]
            price_move = current_price - prev_price

            # Gamma P&L from price movement
            gamma_pnl = 0.5 * gamma * (price_move ** 2)
            total_gamma_pnl += gamma_pnl

            # Update delta (simplified: delta changes with price)
            current_delta += gamma * price_move

            # Check if rehedge needed
            if abs(current_delta) > self.rehedge_threshold:
                # Hedge P&L
                hedge_pnl = current_delta * (current_price - hedge_price)
                total_hedge_pnl += hedge_pnl

                # Transaction cost
                total_transaction_costs += transaction_cost

                # Reset
                current_delta = 0
                hedge_price = current_price
                num_rehedges += 1

        # Calculate realized volatility
        realized_vol = spot_prices.pct_change().std() * np.sqrt(252)

        # Total P&L
        total_pnl = total_gamma_pnl + total_hedge_pnl - total_transaction_costs

        return {
            'total_pnl': round(total_pnl, 2),
            'gamma_pnl': round(total_gamma_pnl, 2),
            'hedge_pnl': round(total_hedge_pnl, 2),
            'transaction_costs': round(total_transaction_costs, 2),
            'num_rehedges': num_rehedges,
            'implied_vol_paid': implied_vol,
            'realized_vol': round(realized_vol, 4),
            'vol_profit': round(realized_vol - implied_vol, 4),
            'profitable': total_pnl > 0
        }


class DispersionTrading:
    """
    Dispersion Trading Strategy

    Used by: Citadel, Susquehanna, Millennium

    Principle:
    - Trade difference between index volatility and component volatilities
    - Index vol is usually cheaper due to diversification/correlation discount
    - Buy individual stock vol, Sell index vol
    - Profit when realized correlation < implied correlation
    """

    def __init__(self):
        self.nifty_weights = {
            # Approximate NIFTY 50 weights (top stocks)
            'RELIANCE': 0.10,
            'TCS': 0.075,
            'HDFCBANK': 0.085,
            'INFY': 0.065,
            'ICICIBANK': 0.06,
            'SBIN': 0.04,
            'BHARTIARTL': 0.045,
            'ITC': 0.035,
            'KOTAKBANK': 0.05,
            'LT': 0.035,
        }

    def calculate_implied_correlation(
        self,
        index_iv: float,
        weighted_stock_iv: float
    ) -> float:
        """
        Calculate implied correlation from index and component IVs

        Formula:
        ρ_implied = (σ_index / σ_components)^2

        Args:
            index_iv: Index implied volatility (e.g., NIFTY)
            weighted_stock_iv: Weighted average of component IVs

        Returns:
            Implied correlation (-1 to 1)
        """
        if weighted_stock_iv == 0:
            return 0

        implied_corr = (index_iv / weighted_stock_iv) ** 2

        # Cap between 0 and 1
        implied_corr = max(0, min(implied_corr, 1))

        return float(implied_corr)

    def calculate_realized_correlation(
        self,
        index_returns: pd.Series,
        stock_returns: pd.DataFrame
    ) -> float:
        """
        Calculate realized correlation between index and components

        Args:
            index_returns: Index return series
            stock_returns: DataFrame of stock returns (columns = stocks)

        Returns:
            Average pairwise correlation
        """
        # Calculate correlation of each stock with index
        correlations = []

        for stock in stock_returns.columns:
            corr = index_returns.corr(stock_returns[stock])
            correlations.append(corr)

        # Average correlation
        avg_correlation = np.mean(correlations)

        return float(avg_correlation)

    def calculate_weighted_stock_iv(
        self,
        stock_ivs: Dict[str, float],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate weighted average of component implied volatilities

        Args:
            stock_ivs: Dict mapping symbol to IV
            weights: Stock weights (uses NIFTY weights if None)

        Returns:
            Weighted IV
        """
        if weights is None:
            weights = self.nifty_weights

        weighted_iv = 0

        for stock, weight in weights.items():
            iv = stock_ivs.get(stock, 0)
            weighted_iv += weight * iv

        return float(weighted_iv)

    def find_dispersion_opportunity(
        self,
        index_iv: float,
        stock_ivs: Dict[str, float],
        historical_correlation: float,
        threshold: float = 0.10
    ) -> Dict:
        """
        Identify dispersion trading opportunity

        Args:
            index_iv: Index IV (e.g., NIFTY)
            stock_ivs: Component IVs
            historical_correlation: Historical realized correlation
            threshold: Minimum spread to trade (10% default)

        Returns:
            Trading signal and analysis
        """
        # Calculate weighted stock IV
        weighted_iv = self.calculate_weighted_stock_iv(stock_ivs)

        # Calculate implied correlation
        implied_corr = self.calculate_implied_correlation(index_iv, weighted_iv)

        # Correlation spread
        corr_spread = implied_corr - historical_correlation

        # Trading signal
        if corr_spread > threshold:
            # Implied correlation too high
            # Market expects stocks to move together more than they actually do
            signal = 'buy_dispersion'
            explanation = (
                f"Implied corr {implied_corr:.2%} > Historical {historical_correlation:.2%}. "
                f"Sell index vol ({index_iv:.1%}), Buy stock vol ({weighted_iv:.1%})"
            )

        elif corr_spread < -threshold:
            # Implied correlation too low
            signal = 'sell_dispersion'
            explanation = (
                f"Implied corr {implied_corr:.2%} < Historical {historical_correlation:.2%}. "
                f"Buy index vol ({index_iv:.1%}), Sell stock vol ({weighted_iv:.1%})"
            )

        else:
            signal = 'no_trade'
            explanation = f"Correlation spread {corr_spread:.2%} within threshold"

        return {
            'signal': signal,
            'index_iv': index_iv,
            'weighted_stock_iv': weighted_iv,
            'implied_correlation': implied_corr,
            'historical_correlation': historical_correlation,
            'correlation_spread': corr_spread,
            'edge': abs(corr_spread),
            'explanation': explanation,
            'timestamp': datetime.now()
        }

    def calculate_dispersion_pnl(
        self,
        index_vega: float,
        stock_vega: float,
        index_iv_change: float,
        stock_iv_change: float
    ) -> Dict:
        """
        Calculate P&L from dispersion trade

        Args:
            index_vega: Index options vega (per 1% vol)
            stock_vega: Stock options vega (per 1% vol)
            index_iv_change: Change in index IV
            stock_iv_change: Change in stock IV

        Returns:
            P&L breakdown
        """
        # P&L from index leg (short)
        index_pnl = -index_vega * (index_iv_change * 100)

        # P&L from stock leg (long)
        stock_pnl = stock_vega * (stock_iv_change * 100)

        # Total P&L
        total_pnl = index_pnl + stock_pnl

        return {
            'total_pnl': round(total_pnl, 2),
            'index_pnl': round(index_pnl, 2),
            'stock_pnl': round(stock_pnl, 2),
            'index_iv_change': round(index_iv_change, 4),
            'stock_iv_change': round(stock_iv_change, 4)
        }


class VolatilitySurface:
    """
    Volatility Surface Analysis

    Analyzes volatility smile/skew for arbitrage opportunities
    """

    def __init__(self):
        pass

    def calculate_volatility_skew(
        self,
        options_chain: List[Dict],
        atm_strike: float
    ) -> Dict:
        """
        Calculate volatility skew

        Args:
            options_chain: Options with strikes and IVs
            atm_strike: At-the-money strike

        Returns:
            Skew metrics
        """
        # Separate ITM, ATM, OTM
        itm_options = [opt for opt in options_chain if opt['strike'] < atm_strike]
        otm_options = [opt for opt in options_chain if opt['strike'] > atm_strike]

        # Average IVs
        itm_iv = np.mean([opt['implied_volatility'] for opt in itm_options]) if itm_options else 0
        otm_iv = np.mean([opt['implied_volatility'] for opt in otm_options]) if otm_options else 0

        # Skew
        skew = itm_iv - otm_iv

        return {
            'itm_iv': itm_iv,
            'otm_iv': otm_iv,
            'skew': skew,
            'skew_pct': (skew / otm_iv * 100) if otm_iv > 0 else 0
        }

    def find_butterfly_arbitrage(
        self,
        options_chain: List[Dict],
        transaction_cost: float = 50
    ) -> List[Dict]:
        """
        Find butterfly arbitrage opportunities in vol surface

        Butterfly spread should not be cheaper than intrinsic value

        Args:
            options_chain: Options chain
            transaction_cost: Total transaction cost for 4-leg trade

        Returns:
            List of arbitrage opportunities
        """
        opportunities = []

        # Sort by strike
        sorted_chain = sorted(options_chain, key=lambda x: x['strike'])

        # Check consecutive strikes
        for i in range(1, len(sorted_chain) - 1):
            lower = sorted_chain[i-1]
            middle = sorted_chain[i]
            upper = sorted_chain[i+1]

            # Butterfly: Buy 1 lower, Sell 2 middle, Buy 1 upper
            butterfly_cost = (
                lower['ltp']
                - 2 * middle['ltp']
                + upper['ltp']
            )

            # Maximum profit (distance between strikes)
            max_profit = upper['strike'] - middle['strike']

            # Arbitrage if butterfly cost < 0 (negative cost = credit received)
            if butterfly_cost < -transaction_cost:
                opportunities.append({
                    'type': 'butterfly_arbitrage',
                    'lower_strike': lower['strike'],
                    'middle_strike': middle['strike'],
                    'upper_strike': upper['strike'],
                    'cost': butterfly_cost,
                    'max_profit': max_profit,
                    'edge': abs(butterfly_cost),
                    'explanation': f"Butterfly credit {abs(butterfly_cost):.2f} > transaction cost"
                })

        return opportunities


# Example usage and testing
if __name__ == "__main__":
    # Test Volatility Arbitrage
    print("=" * 60)
    print("VOLATILITY ARBITRAGE TEST")
    print("=" * 60)

    # Mock price data
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=252, freq='D')
    prices = pd.Series(
        22000 * np.exp(np.cumsum(np.random.normal(0, 0.015, 252))),
        index=dates
    )

    vol_arb = VolatilityArbitrage()

    # Calculate realized volatility
    rv = vol_arb.calculate_realized_volatility(prices, window=30)
    forecasted_rv = vol_arb.forecast_realized_volatility(prices, method='ewma')

    print(f"Realized Volatility (30d): {rv:.2%}")
    print(f"Forecasted Volatility: {forecasted_rv:.2%}")

    # Mock options chain
    options_chain = [
        {'strike': 22000, 'type': 'call', 'ltp': 250, 'implied_volatility': 0.18},
        {'strike': 22100, 'type': 'call', 'ltp': 180, 'implied_volatility': 0.22},  # Overpriced
        {'strike': 22200, 'type': 'call', 'ltp': 120, 'implied_volatility': 0.12},  # Underpriced
    ]

    opportunities = vol_arb.find_mispriced_options(options_chain, 22050, forecasted_rv)

    print(f"\nFound {len(opportunities)} mispriced options:")
    for opp in opportunities:
        print(f"  {opp['strike']} {opp['type']}: {opp['signal']} (IV={opp['implied_vol']:.1%}, Edge={opp['edge']:.1%})")

    # Test Gamma Scalping
    print("\n" + "=" * 60)
    print("GAMMA SCALPING TEST")
    print("=" * 60)

    gamma_scalp = GammaScalping(rehedge_threshold=0.1)

    # Mock spot price path with volatility
    spot_path = pd.Series(
        22000 + np.cumsum(np.random.normal(0, 200, 50))
    )

    simulation = gamma_scalp.simulate_gamma_scalping(
        initial_option_price=250,
        implied_vol=0.15,
        spot_prices=spot_path,
        gamma=0.002,
        initial_delta=0.5,
        transaction_cost=10
    )

    print(f"Total P&L: ₹{simulation['total_pnl']:,.0f}")
    print(f"Gamma P&L: ₹{simulation['gamma_pnl']:,.0f}")
    print(f"Hedge P&L: ₹{simulation['hedge_pnl']:,.0f}")
    print(f"Transaction Costs: ₹{simulation['transaction_costs']:,.0f}")
    print(f"Number of Rehedges: {simulation['num_rehedges']}")
    print(f"IV Paid: {simulation['implied_vol_paid']:.1%}")
    print(f"Realized Vol: {simulation['realized_vol']:.1%}")
    print(f"Vol Profit: {simulation['vol_profit']:.2%}")

    # Test Dispersion Trading
    print("\n" + "=" * 60)
    print("DISPERSION TRADING TEST")
    print("=" * 60)

    dispersion = DispersionTrading()

    # Mock data
    nifty_iv = 0.15  # NIFTY IV = 15%
    stock_ivs = {
        'RELIANCE': 0.20,
        'TCS': 0.18,
        'HDFCBANK': 0.22,
        'INFY': 0.19,
        'ICICIBANK': 0.21,
    }

    historical_corr = 0.65  # Historical correlation = 65%

    signal = dispersion.find_dispersion_opportunity(
        nifty_iv, stock_ivs, historical_corr, threshold=0.10
    )

    print(f"Signal: {signal['signal']}")
    print(f"Index IV: {signal['index_iv']:.1%}")
    print(f"Weighted Stock IV: {signal['weighted_stock_iv']:.1%}")
    print(f"Implied Correlation: {signal['implied_correlation']:.1%}")
    print(f"Historical Correlation: {signal['historical_correlation']:.1%}")
    print(f"Explanation: {signal['explanation']}")
