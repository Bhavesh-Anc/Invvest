"""
Advanced Options Pricing Engine for Indian Stock Market
Implements Black-Scholes-Merton, Binomial Tree, and Greeks calculations
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import brentq
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlackScholesModel:
    """
    Black-Scholes-Merton Option Pricing Model
    Suitable for European options on stocks with no dividends or with continuous dividend yield
    """

    def __init__(self, risk_free_rate: float = 0.065):
        """
        Initialize Black-Scholes Model

        Args:
            risk_free_rate: Risk-free interest rate (default 6.5% for Indian 10-year G-Sec)
        """
        self.risk_free_rate = risk_free_rate

    def _d1(self, S: float, K: float, T: float, r: float, sigma: float, q: float = 0) -> float:
        """Calculate d1 parameter"""
        return (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

    def _d2(self, S: float, K: float, T: float, r: float, sigma: float, q: float = 0) -> float:
        """Calculate d2 parameter"""
        return self._d1(S, K, T, r, sigma, q) - sigma * np.sqrt(T)

    def call_price(self, S: float, K: float, T: float, sigma: float,
                   r: float = None, q: float = 0) -> float:
        """
        Calculate European Call Option Price

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            sigma: Volatility (annualized)
            r: Risk-free rate (uses default if None)
            q: Dividend yield (continuous)

        Returns:
            Call option price
        """
        if T <= 0:
            return max(S - K, 0)

        r = r or self.risk_free_rate
        d1 = self._d1(S, K, T, r, sigma, q)
        d2 = self._d2(S, K, T, r, sigma, q)

        call = S * np.exp(-q * T) * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)
        return call

    def put_price(self, S: float, K: float, T: float, sigma: float,
                  r: float = None, q: float = 0) -> float:
        """
        Calculate European Put Option Price

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            sigma: Volatility (annualized)
            r: Risk-free rate (uses default if None)
            q: Dividend yield (continuous)

        Returns:
            Put option price
        """
        if T <= 0:
            return max(K - S, 0)

        r = r or self.risk_free_rate
        d1 = self._d1(S, K, T, r, sigma, q)
        d2 = self._d2(S, K, T, r, sigma, q)

        put = K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * np.exp(-q * T) * stats.norm.cdf(-d1)
        return put

    def implied_volatility(self, option_price: float, S: float, K: float, T: float,
                          option_type: str = 'call', r: float = None, q: float = 0) -> float:
        """
        Calculate Implied Volatility using Brent's method

        Args:
            option_price: Market price of option
            S: Current stock price
            K: Strike price
            T: Time to expiration
            option_type: 'call' or 'put'
            r: Risk-free rate
            q: Dividend yield

        Returns:
            Implied volatility (annualized)
        """
        r = r or self.risk_free_rate

        def objective(sigma):
            if option_type.lower() == 'call':
                return self.call_price(S, K, T, sigma, r, q) - option_price
            else:
                return self.put_price(S, K, T, sigma, r, q) - option_price

        try:
            iv = brentq(objective, 0.001, 5.0)  # Search between 0.1% and 500% volatility
            return iv
        except Exception as e:
            logger.warning(f"IV calculation failed: {e}")
            return np.nan


class BinomialTreeModel:
    """
    Binomial Tree Model for American and European Options
    More flexible than Black-Scholes, can handle early exercise
    """

    def __init__(self, risk_free_rate: float = 0.065):
        """
        Initialize Binomial Tree Model

        Args:
            risk_free_rate: Risk-free interest rate
        """
        self.risk_free_rate = risk_free_rate

    def price_option(self, S: float, K: float, T: float, sigma: float,
                     option_type: str = 'call', style: str = 'european',
                     steps: int = 100, r: float = None, q: float = 0) -> float:
        """
        Price option using Binomial Tree

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            sigma: Volatility
            option_type: 'call' or 'put'
            style: 'european' or 'american'
            steps: Number of time steps
            r: Risk-free rate
            q: Dividend yield

        Returns:
            Option price
        """
        if T <= 0:
            if option_type.lower() == 'call':
                return max(S - K, 0)
            else:
                return max(K - S, 0)

        r = r or self.risk_free_rate
        dt = T / steps
        u = np.exp(sigma * np.sqrt(dt))  # Up factor
        d = 1 / u  # Down factor
        p = (np.exp((r - q) * dt) - d) / (u - d)  # Risk-neutral probability

        # Initialize asset prices at maturity
        stock_prices = np.zeros(steps + 1)
        for i in range(steps + 1):
            stock_prices[i] = S * (u ** (steps - i)) * (d ** i)

        # Initialize option values at maturity
        option_values = np.zeros(steps + 1)
        if option_type.lower() == 'call':
            option_values = np.maximum(stock_prices - K, 0)
        else:
            option_values = np.maximum(K - stock_prices, 0)

        # Backward induction
        for j in range(steps - 1, -1, -1):
            for i in range(j + 1):
                # Calculate option value from next period
                option_values[i] = np.exp(-r * dt) * (p * option_values[i] + (1 - p) * option_values[i + 1])

                # Check for early exercise (American option)
                if style.lower() == 'american':
                    stock_price = S * (u ** (j - i)) * (d ** i)
                    if option_type.lower() == 'call':
                        exercise_value = max(stock_price - K, 0)
                    else:
                        exercise_value = max(K - stock_price, 0)
                    option_values[i] = max(option_values[i], exercise_value)

        return option_values[0]


class GreeksCalculator:
    """
    Calculate Option Greeks (Delta, Gamma, Theta, Vega, Rho)
    Measures of option price sensitivity to various factors
    """

    def __init__(self, pricing_model: BlackScholesModel = None):
        """
        Initialize Greeks Calculator

        Args:
            pricing_model: BlackScholesModel instance
        """
        self.bs_model = pricing_model or BlackScholesModel()

    def delta(self, S: float, K: float, T: float, sigma: float,
              option_type: str = 'call', r: float = None, q: float = 0) -> float:
        """
        Calculate Delta: Rate of change of option price w.r.t. stock price
        Range: Call [0, 1], Put [-1, 0]
        """
        r = r or self.bs_model.risk_free_rate
        d1 = self.bs_model._d1(S, K, T, r, sigma, q)

        if option_type.lower() == 'call':
            return np.exp(-q * T) * stats.norm.cdf(d1)
        else:
            return np.exp(-q * T) * (stats.norm.cdf(d1) - 1)

    def gamma(self, S: float, K: float, T: float, sigma: float,
              r: float = None, q: float = 0) -> float:
        """
        Calculate Gamma: Rate of change of delta w.r.t. stock price
        Same for both calls and puts
        """
        r = r or self.bs_model.risk_free_rate
        d1 = self.bs_model._d1(S, K, T, r, sigma, q)

        gamma = (np.exp(-q * T) * stats.norm.pdf(d1)) / (S * sigma * np.sqrt(T))
        return gamma

    def theta(self, S: float, K: float, T: float, sigma: float,
              option_type: str = 'call', r: float = None, q: float = 0) -> float:
        """
        Calculate Theta: Rate of change of option price w.r.t. time
        Typically negative (time decay)
        Returns theta per day (divide by 365)
        """
        r = r or self.bs_model.risk_free_rate
        d1 = self.bs_model._d1(S, K, T, r, sigma, q)
        d2 = self.bs_model._d2(S, K, T, r, sigma, q)

        term1 = -(S * stats.norm.pdf(d1) * sigma * np.exp(-q * T)) / (2 * np.sqrt(T))

        if option_type.lower() == 'call':
            term2 = -q * S * stats.norm.cdf(d1) * np.exp(-q * T)
            term3 = r * K * np.exp(-r * T) * stats.norm.cdf(d2)
            theta = term1 + term2 + term3
        else:
            term2 = q * S * stats.norm.cdf(-d1) * np.exp(-q * T)
            term3 = -r * K * np.exp(-r * T) * stats.norm.cdf(-d2)
            theta = term1 + term2 + term3

        return theta / 365  # Convert to daily theta

    def vega(self, S: float, K: float, T: float, sigma: float,
             r: float = None, q: float = 0) -> float:
        """
        Calculate Vega: Rate of change of option price w.r.t. volatility
        Same for both calls and puts
        Returns vega per 1% change in volatility
        """
        r = r or self.bs_model.risk_free_rate
        d1 = self.bs_model._d1(S, K, T, r, sigma, q)

        vega = S * np.exp(-q * T) * stats.norm.pdf(d1) * np.sqrt(T)
        return vega / 100  # Vega per 1% volatility change

    def rho(self, S: float, K: float, T: float, sigma: float,
            option_type: str = 'call', r: float = None, q: float = 0) -> float:
        """
        Calculate Rho: Rate of change of option price w.r.t. interest rate
        Returns rho per 1% change in interest rate
        """
        r = r or self.bs_model.risk_free_rate
        d2 = self.bs_model._d2(S, K, T, r, sigma, q)

        if option_type.lower() == 'call':
            rho = K * T * np.exp(-r * T) * stats.norm.cdf(d2)
        else:
            rho = -K * T * np.exp(-r * T) * stats.norm.cdf(-d2)

        return rho / 100  # Rho per 1% interest rate change

    def calculate_all_greeks(self, S: float, K: float, T: float, sigma: float,
                            option_type: str = 'call', r: float = None,
                            q: float = 0) -> Dict[str, float]:
        """
        Calculate all Greeks at once

        Returns:
            Dictionary with all Greek values
        """
        return {
            'delta': self.delta(S, K, T, sigma, option_type, r, q),
            'gamma': self.gamma(S, K, T, sigma, r, q),
            'theta': self.theta(S, K, T, sigma, option_type, r, q),
            'vega': self.vega(S, K, T, sigma, r, q),
            'rho': self.rho(S, K, T, sigma, option_type, r, q)
        }


class OptionsChain:
    """
    Options Chain Analysis and Management
    """

    def __init__(self):
        self.bs_model = BlackScholesModel()
        self.greeks_calc = GreeksCalculator(self.bs_model)

    def analyze_option(self, S: float, K: float, T: float,
                      market_price: float, option_type: str = 'call',
                      r: float = None, q: float = 0) -> Dict:
        """
        Complete analysis of a single option

        Returns:
            Dictionary with price, IV, and all Greeks
        """
        r = r or self.bs_model.risk_free_rate

        # Calculate theoretical price (using historical volatility estimate)
        # For now, we'll use market price to derive IV
        iv = self.bs_model.implied_volatility(market_price, S, K, T, option_type, r, q)

        if np.isnan(iv):
            logger.warning(f"Could not calculate IV for {option_type} K={K}")
            iv = 0.25  # Default fallback

        # Calculate theoretical price with IV
        if option_type.lower() == 'call':
            theo_price = self.bs_model.call_price(S, K, T, iv, r, q)
        else:
            theo_price = self.bs_model.put_price(S, K, T, iv, r, q)

        # Calculate Greeks
        greeks = self.greeks_calc.calculate_all_greeks(S, K, T, iv, option_type, r, q)

        # Calculate moneyness
        moneyness = S / K

        return {
            'strike': K,
            'option_type': option_type,
            'market_price': market_price,
            'theoretical_price': theo_price,
            'implied_volatility': iv,
            'moneyness': moneyness,
            'intrinsic_value': max(S - K, 0) if option_type.lower() == 'call' else max(K - S, 0),
            'time_value': market_price - (max(S - K, 0) if option_type.lower() == 'call' else max(K - S, 0)),
            **greeks
        }

    def create_volatility_surface(self, options_data: pd.DataFrame,
                                  spot_price: float) -> pd.DataFrame:
        """
        Create volatility surface from options chain data

        Args:
            options_data: DataFrame with columns ['strike', 'expiry', 'call_price', 'put_price']
            spot_price: Current stock price

        Returns:
            DataFrame with volatility surface
        """
        results = []

        for _, row in options_data.iterrows():
            K = row['strike']
            expiry = pd.to_datetime(row['expiry'])
            T = (expiry - datetime.now()).days / 365.0

            if T <= 0:
                continue

            # Calculate IV for call
            if 'call_price' in row and pd.notna(row['call_price']) and row['call_price'] > 0:
                call_iv = self.bs_model.implied_volatility(
                    row['call_price'], spot_price, K, T, 'call'
                )
                results.append({
                    'strike': K,
                    'expiry': expiry,
                    'time_to_expiry': T,
                    'moneyness': spot_price / K,
                    'option_type': 'call',
                    'implied_vol': call_iv
                })

            # Calculate IV for put
            if 'put_price' in row and pd.notna(row['put_price']) and row['put_price'] > 0:
                put_iv = self.bs_model.implied_volatility(
                    row['put_price'], spot_price, K, T, 'put'
                )
                results.append({
                    'strike': K,
                    'expiry': expiry,
                    'time_to_expiry': T,
                    'moneyness': spot_price / K,
                    'option_type': 'put',
                    'implied_vol': put_iv
                })

        return pd.DataFrame(results)


# Utility functions
def calculate_historical_volatility(prices: pd.Series, window: int = 30) -> float:
    """
    Calculate historical volatility from price series

    Args:
        prices: Series of stock prices
        window: Rolling window for calculation

    Returns:
        Annualized volatility
    """
    returns = np.log(prices / prices.shift(1))
    volatility = returns.rolling(window=window).std() * np.sqrt(252)
    return volatility.iloc[-1]


def trading_days_to_expiry(expiry_date: datetime) -> float:
    """
    Calculate time to expiry in years (trading days)

    Args:
        expiry_date: Option expiry date

    Returns:
        Time to expiry in years
    """
    today = datetime.now()
    days = (expiry_date - today).days
    return max(days / 365.0, 0)


if __name__ == "__main__":
    # Example usage
    bs = BlackScholesModel(risk_free_rate=0.065)
    greeks = GreeksCalculator(bs)

    # Example: Price a call option
    S = 18500  # Nifty spot
    K = 18700  # Strike
    T = 30 / 365  # 30 days to expiry
    sigma = 0.15  # 15% volatility

    call_price = bs.call_price(S, K, T, sigma)
    put_price = bs.put_price(S, K, T, sigma)

    print(f"Call Price: ₹{call_price:.2f}")
    print(f"Put Price: ₹{put_price:.2f}")

    # Calculate Greeks
    greeks_values = greeks.calculate_all_greeks(S, K, T, sigma, 'call')
    print("\nGreeks for Call Option:")
    for greek, value in greeks_values.items():
        print(f"{greek.capitalize()}: {value:.4f}")
