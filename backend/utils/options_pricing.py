"""
Options Pricing and Chain Data
Fetch options chain from NSE and calculate Greeks
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy.stats import norm

logger = logging.getLogger(__name__)

# Try importing jugaad-data
try:
    from jugaad_data.nse import NSELive
    JUGAAD_AVAILABLE = True
except ImportError:
    logger.warning("jugaad-data not available for options chain")
    JUGAAD_AVAILABLE = False


class OptionsChain:
    """
    Fetch and analyze options chain data from NSE
    """

    def __init__(self, underlying: str):
        """
        Initialize options chain fetcher

        Args:
            underlying: Underlying symbol (e.g., "NIFTY", "BANKNIFTY", "RELIANCE")
        """
        self.underlying = underlying.upper()
        self.nse_live = NSELive() if JUGAAD_AVAILABLE else None

    def get_chain_data(self, expiry: Optional[str] = None) -> List[Dict]:
        """
        Get options chain for underlying

        Args:
            expiry: Expiry date (e.g., "30-JAN-2026"). If None, gets nearest expiry.

        Returns:
            List of option chain rows with strikes and data
        """
        try:
            if not JUGAAD_AVAILABLE or not self.nse_live:
                return self._get_mock_chain_data()

            # Fetch options chain from NSE
            if self.underlying in ["NIFTY", "BANKNIFTY"]:
                chain = self.nse_live.index_option_chain(self.underlying)
            else:
                chain = self.nse_live.stock_option_chain(self.underlying)

            if not chain:
                return self._get_mock_chain_data()

            # Parse chain data
            records = chain.get('records', {})
            data = records.get('data', [])

            # Filter by expiry if specified
            if expiry:
                data = [row for row in data if row.get('expiryDate') == expiry]

            # Extract relevant data
            chain_data = []
            for row in data:
                strike = row.get('strikePrice')
                ce_data = row.get('CE', {})
                pe_data = row.get('PE', {})

                chain_data.append({
                    "strike": strike,
                    "call_ltp": ce_data.get('lastPrice', 0),
                    "call_oi": ce_data.get('openInterest', 0),
                    "call_volume": ce_data.get('totalTradedVolume', 0),
                    "call_iv": ce_data.get('impliedVolatility', 0),
                    "put_ltp": pe_data.get('lastPrice', 0),
                    "put_oi": pe_data.get('openInterest', 0),
                    "put_volume": pe_data.get('totalTradedVolume', 0),
                    "put_iv": pe_data.get('impliedVolatility', 0),
                    "expiry": row.get('expiryDate', ''),
                })

            return chain_data if chain_data else self._get_mock_chain_data()

        except Exception as e:
            logger.error(f"Error fetching options chain for {self.underlying}: {e}")
            return self._get_mock_chain_data()

    def _get_mock_chain_data(self) -> List[Dict]:
        """Generate mock options chain data"""
        # Determine ATM strike based on underlying
        atm_strikes = {
            "NIFTY": 22000,
            "BANKNIFTY": 47500,
            "RELIANCE": 2700,
            "TCS": 3700,
        }
        atm = atm_strikes.get(self.underlying, 1000)

        # Generate strikes around ATM
        strikes = []
        if self.underlying in ["NIFTY", "BANKNIFTY"]:
            # 100-point intervals for indices
            interval = 100
            for i in range(-10, 11):
                strikes.append(atm + (i * interval))
        else:
            # 50-point intervals for stocks
            interval = 50
            for i in range(-10, 11):
                strikes.append(atm + (i * interval))

        chain_data = []
        for strike in strikes:
            # Mock pricing based on distance from ATM
            moneyness = abs(strike - atm) / atm
            call_ltp = max(atm - strike + (atm * 0.02), atm * 0.005) if strike <= atm else atm * 0.01 * np.exp(-5 * moneyness)
            put_ltp = max(strike - atm + (atm * 0.02), atm * 0.005) if strike >= atm else atm * 0.01 * np.exp(-5 * moneyness)

            chain_data.append({
                "strike": strike,
                "call_ltp": round(call_ltp, 2),
                "call_oi": int(np.random.uniform(100000, 500000)),
                "call_volume": int(np.random.uniform(10000, 50000)),
                "call_iv": round(np.random.uniform(15, 25), 2),
                "put_ltp": round(put_ltp, 2),
                "put_oi": int(np.random.uniform(100000, 500000)),
                "put_volume": int(np.random.uniform(10000, 50000)),
                "put_iv": round(np.random.uniform(15, 25), 2),
                "expiry": "30-JAN-2026",
            })

        return chain_data

    def calculate_greeks(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float = 0.07,
        option_type: str = "call"
    ) -> Dict:
        """
        Calculate option Greeks using Black-Scholes

        Args:
            spot: Current price of underlying
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility (as decimal, e.g., 0.20 for 20%)
            risk_free_rate: Risk-free rate (default 7% for India)
            option_type: "call" or "put"

        Returns:
            Dict with delta, gamma, theta, vega, rho
        """
        try:
            # Avoid division by zero
            if time_to_expiry <= 0:
                return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}

            # Calculate d1 and d2
            d1 = (np.log(spot / strike) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry) / (
                volatility * np.sqrt(time_to_expiry)
            )
            d2 = d1 - volatility * np.sqrt(time_to_expiry)

            # Calculate Greeks
            if option_type.lower() == "call":
                delta = norm.cdf(d1)
                rho = strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2) / 100
            else:  # put
                delta = norm.cdf(d1) - 1
                rho = -strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) / 100

            gamma = norm.pdf(d1) / (spot * volatility * np.sqrt(time_to_expiry))

            theta = (
                -spot * norm.pdf(d1) * volatility / (2 * np.sqrt(time_to_expiry))
                - risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry)
                * (norm.cdf(d2) if option_type.lower() == "call" else norm.cdf(-d2))
            ) / 365  # Daily theta

            vega = spot * norm.pdf(d1) * np.sqrt(time_to_expiry) / 100

            return {
                "delta": round(delta, 4),
                "gamma": round(gamma, 6),
                "theta": round(theta, 2),
                "vega": round(vega, 2),
                "rho": round(rho, 4)
            }

        except Exception as e:
            logger.error(f"Error calculating Greeks: {e}")
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}

    def get_implied_volatility(
        self,
        option_price: float,
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float = 0.07,
        option_type: str = "call"
    ) -> float:
        """
        Calculate implied volatility using Newton-Raphson method

        Args:
            option_price: Market price of the option
            spot: Current price of underlying
            strike: Strike price
            time_to_expiry: Time to expiry in years
            risk_free_rate: Risk-free rate
            option_type: "call" or "put"

        Returns:
            Implied volatility (as decimal)
        """
        try:
            # Initial guess
            iv = 0.20  # 20%
            max_iterations = 100
            tolerance = 0.0001

            for _ in range(max_iterations):
                # Calculate option price with current IV
                d1 = (np.log(spot / strike) + (risk_free_rate + 0.5 * iv ** 2) * time_to_expiry) / (
                    iv * np.sqrt(time_to_expiry)
                )
                d2 = d1 - iv * np.sqrt(time_to_expiry)

                if option_type.lower() == "call":
                    price = spot * norm.cdf(d1) - strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
                else:
                    price = strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) - spot * norm.cdf(-d1)

                # Calculate vega
                vega = spot * norm.pdf(d1) * np.sqrt(time_to_expiry)

                # Newton-Raphson update
                diff = option_price - price

                if abs(diff) < tolerance:
                    return round(iv, 4)

                iv = iv + diff / vega

                # Ensure IV stays positive
                if iv <= 0:
                    iv = 0.01

            return round(iv, 4)

        except Exception as e:
            logger.error(f"Error calculating IV: {e}")
            return 0.20  # Default 20%


def calculate_black_scholes_price(
    spot: float,
    strike: float,
    time_to_expiry: float,
    volatility: float,
    risk_free_rate: float = 0.07,
    option_type: str = "call"
) -> float:
    """
    Calculate option price using Black-Scholes formula

    Args:
        spot: Current price of underlying
        strike: Strike price
        time_to_expiry: Time to expiry in years
        volatility: Volatility (as decimal)
        risk_free_rate: Risk-free rate
        option_type: "call" or "put"

    Returns:
        Option price
    """
    try:
        d1 = (np.log(spot / strike) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry) / (
            volatility * np.sqrt(time_to_expiry)
        )
        d2 = d1 - volatility * np.sqrt(time_to_expiry)

        if option_type.lower() == "call":
            price = spot * norm.cdf(d1) - strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
        else:
            price = strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) - spot * norm.cdf(-d1)

        return round(price, 2)

    except Exception as e:
        logger.error(f"Error calculating Black-Scholes price: {e}")
        return 0.0
