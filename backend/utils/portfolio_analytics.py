"""
Portfolio Analytics Utilities
Portfolio management, performance tracking, and risk calculations
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class Portfolio:
    """
    Portfolio management and analytics
    Currently uses mock data; will integrate with database when user auth is added
    """

    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id or "demo_user"
        self.holdings = self._get_mock_holdings()

    def _get_mock_holdings(self) -> List[Dict]:
        """
        Get mock portfolio holdings
        In production, this will fetch from database
        """
        from utils.realtime_data import get_realtime_data

        holdings = [
            {"symbol": "RELIANCE", "quantity": 250, "avg_price": 2450.00, "purchase_date": datetime(2024, 6, 15)},
            {"symbol": "TCS", "quantity": 120, "avg_price": 3680.00, "purchase_date": datetime(2024, 5, 20)},
            {"symbol": "INFY", "quantity": 200, "avg_price": 1520.00, "purchase_date": datetime(2024, 7, 10)},
            {"symbol": "HDFCBANK", "quantity": 180, "avg_price": 1640.00, "purchase_date": datetime(2024, 8, 5)},
            {"symbol": "ICICIBANK", "quantity": 150, "avg_price": 980.00, "purchase_date": datetime(2024, 9, 1)},
        ]

        # Enrich with live prices
        enriched_holdings = []
        for holding in holdings:
            try:
                quote = get_realtime_data(holding["symbol"])
                ltp = quote["ltp"]
            except:
                # Fallback price (mock)
                ltp = holding["avg_price"] * 1.1  # Assume 10% gain

            current_value = holding["quantity"] * ltp
            cost = holding["quantity"] * holding["avg_price"]
            pnl = current_value - cost
            pnl_percent = (pnl / cost) * 100 if cost > 0 else 0

            enriched_holdings.append({
                **holding,
                "ltp": ltp,
                "current_value": current_value,
                "cost": cost,
                "pnl": pnl,
                "pnl_percent": pnl_percent
            })

        return enriched_holdings

    def get_summary_metrics(self) -> Dict:
        """Get portfolio summary metrics"""
        if not self.holdings:
            return {
                "total_value": 0,
                "today_pnl": 0,
                "today_pnl_percent": 0,
                "margin_used": 0,
                "margin_available": 0,
                "sharpe_ratio": 0
            }

        total_value = sum(h["current_value"] for h in self.holdings)
        total_cost = sum(h["cost"] for h in self.holdings)
        total_pnl = total_value - total_cost

        # Mock today's P&L (1-2% of total value)
        today_pnl = total_value * np.random.uniform(0.01, 0.02)
        today_pnl_percent = (today_pnl / total_value) * 100

        # Mock margin (40% used, 60% available)
        margin_used = total_value * 0.4
        margin_available = total_value * 0.6

        return {
            "total_value": round(total_value, 2),
            "today_pnl": round(today_pnl, 2),
            "today_pnl_percent": round(today_pnl_percent, 2),
            "margin_used": round(margin_used, 2),
            "margin_available": round(margin_available, 2),
            "sharpe_ratio": round(np.random.uniform(1.5, 2.5), 2)  # Mock Sharpe ratio
        }

    def get_performance_history(self, days: int = 30) -> pd.DataFrame:
        """
        Get portfolio performance history

        Args:
            days: Number of days of history

        Returns:
            DataFrame with date, value, and return_percent columns
        """
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

        # Generate mock portfolio performance (random walk with positive drift)
        np.random.seed(42)
        returns = np.random.normal(0.15, 1.2, days)  # Mean 0.15% daily, std 1.2%
        cumulative_returns = np.cumsum(returns)

        return pd.DataFrame({
            'date': dates,
            'return_percent': cumulative_returns,
            'value': 3500000 * (1 + cumulative_returns / 100)  # Base value 35L
        })

    def get_sector_allocation(self) -> Dict:
        """Get portfolio allocation by sector"""
        # Mock sector mapping
        sector_map = {
            "RELIANCE": "Energy",
            "TCS": "IT",
            "INFY": "IT",
            "HDFCBANK": "Banking",
            "ICICIBANK": "Banking",
        }

        sector_values = {}
        total_value = sum(h["current_value"] for h in self.holdings)

        for holding in self.holdings:
            sector = sector_map.get(holding["symbol"], "Other")
            sector_values[sector] = sector_values.get(sector, 0) + holding["current_value"]

        return {
            sector: {
                "value": value,
                "percent": round((value / total_value) * 100, 1)
            }
            for sector, value in sector_values.items()
        }

    def get_risk_metrics(self) -> Dict:
        """Calculate portfolio risk metrics"""
        # Get performance history
        performance = self.get_performance_history(180)  # 6 months
        returns = performance['return_percent'].diff().dropna()

        # Calculate metrics
        volatility = returns.std() * np.sqrt(252)  # Annualized
        var_95 = np.percentile(returns, 5)  # 5th percentile
        max_drawdown = (performance['return_percent'].cummax() - performance['return_percent']).max()

        # Mock beta (correlation with market)
        beta = np.random.uniform(0.85, 1.15)

        return {
            "var_95": abs(round(var_95, 2)),
            "var_threshold": 5.0,
            "max_drawdown": round(max_drawdown, 2),
            "beta": round(beta, 2),
            "volatility": round(volatility, 2)
        }

    def get_open_positions(self) -> List[Dict]:
        """
        Get list of open positions
        Combines holdings with mock options/futures positions
        """
        positions = []

        # Add cash positions from holdings
        for holding in self.holdings[:3]:  # Show top 3
            positions.append({
                "symbol": holding["symbol"],
                "type": "Cash",
                "quantity": holding["quantity"],
                "avg_price": holding["avg_price"],
                "ltp": holding["ltp"],
                "pnl": holding["pnl"],
                "pnl_percent": holding["pnl_percent"]
            })

        # Add mock options position
        positions.append({
            "symbol": "NIFTY 25JAN26 22000 CE",
            "type": "Options",
            "quantity": 150,
            "avg_price": 185.50,
            "ltp": 218.75,
            "pnl": 4987.50,
            "pnl_percent": 17.93
        })

        # Add mock futures position
        positions.append({
            "symbol": "BANKNIFTY FUT",
            "type": "Futures",
            "quantity": 75,
            "avg_price": 47250.00,
            "ltp": 47623.90,
            "pnl": 28042.50,
            "pnl_percent": 0.79
        })

        return positions


class PerformanceMetrics:
    """
    Calculate portfolio performance metrics
    """

    @staticmethod
    def calculate_sharpe_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.07
    ) -> float:
        """
        Calculate Sharpe ratio

        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate (default 7% for India)

        Returns:
            Sharpe ratio
        """
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        return np.sqrt(252) * excess_returns.mean() / returns.std()

    @staticmethod
    def calculate_sortino_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.07
    ) -> float:
        """
        Calculate Sortino ratio (considers only downside volatility)
        """
        excess_returns = returns - (risk_free_rate / 252)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std()

        if downside_std == 0:
            return 0

        return np.sqrt(252) * excess_returns.mean() / downside_std

    @staticmethod
    def calculate_max_drawdown(equity_curve: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = equity_curve.cummax()
        drawdown = (equity_curve - cumulative) / cumulative
        return drawdown.min() * 100

    @staticmethod
    def calculate_calmar_ratio(
        returns: pd.Series,
        equity_curve: pd.Series
    ) -> float:
        """
        Calculate Calmar ratio (return / max drawdown)
        """
        annual_return = returns.mean() * 252
        max_dd = abs(PerformanceMetrics.calculate_max_drawdown(equity_curve))

        if max_dd == 0:
            return 0

        return annual_return / max_dd

    @staticmethod
    def calculate_var(
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk

        Args:
            returns: Series of returns
            confidence: Confidence level (e.g., 0.95 for 95%)

        Returns:
            VaR as percentage
        """
        return np.percentile(returns, (1 - confidence) * 100)

    @staticmethod
    def calculate_cvar(
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR) / Expected Shortfall

        Args:
            returns: Series of returns
            confidence: Confidence level

        Returns:
            CVaR as percentage
        """
        var = PerformanceMetrics.calculate_var(returns, confidence)
        return returns[returns <= var].mean()
