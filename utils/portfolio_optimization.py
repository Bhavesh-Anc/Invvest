"""
Advanced Portfolio Optimization
Markowitz Mean-Variance, Black-Litterman, Risk Parity, and Maximum Sharpe
Institutional-grade implementation
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize, LinearConstraint
from scipy import linalg
from typing import Dict, List, Tuple, Optional
import logging
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarkowitzOptimizer:
    """
    Classic Markowitz Mean-Variance Portfolio Optimization
    Nobel Prize winning framework for optimal portfolio allocation
    """

    def __init__(self, risk_free_rate: float = 0.065):
        """
        Args:
            risk_free_rate: Annual risk-free rate (Indian 10Y G-Sec: 6.5%)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_returns_covariance(self, price_data: pd.DataFrame
                                    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate expected returns and covariance matrix

        Args:
            price_data: DataFrame with stock prices (columns = stocks, rows = dates)

        Returns:
            (expected_returns, covariance_matrix)
        """
        # Calculate returns
        returns = price_data.pct_change().dropna()

        # Annualized expected returns
        expected_returns = returns.mean() * 252

        # Annualized covariance matrix
        cov_matrix = returns.cov() * 252

        return expected_returns.values, cov_matrix.values

    def portfolio_performance(self, weights: np.ndarray,
                             expected_returns: np.ndarray,
                             cov_matrix: np.ndarray) -> Tuple[float, float, float]:
        """
        Calculate portfolio performance metrics

        Args:
            weights: Portfolio weights
            expected_returns: Expected returns
            cov_matrix: Covariance matrix

        Returns:
            (return, volatility, sharpe_ratio)
        """
        portfolio_return = np.sum(weights * expected_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility

        return portfolio_return, portfolio_volatility, sharpe_ratio

    def minimize_volatility(self, expected_returns: np.ndarray,
                           cov_matrix: np.ndarray,
                           target_return: float = None,
                           constraints: Dict = None) -> Dict:
        """
        Find minimum volatility portfolio

        Args:
            expected_returns: Expected returns array
            cov_matrix: Covariance matrix
            target_return: Target return (if None, find global minimum)
            constraints: Additional constraints

        Returns:
            Optimization result dictionary
        """
        n_assets = len(expected_returns)

        # Objective function: minimize portfolio variance
        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))

        # Constraints
        cons = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Weights sum to 1
        ]

        if target_return is not None:
            cons.append({
                'type': 'eq',
                'fun': lambda x: np.sum(x * expected_returns) - target_return
            })

        if constraints:
            cons.extend(constraints.get('additional', []))

        # Bounds: weights between 0 and 1 (no short selling)
        bounds = tuple((0, 1) for _ in range(n_assets))

        # Initial guess
        x0 = np.array([1 / n_assets] * n_assets)

        # Optimize
        result = minimize(
            portfolio_variance,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=cons
        )

        if result.success:
            weights = result.x
            ret, vol, sharpe = self.portfolio_performance(weights, expected_returns, cov_matrix)

            return {
                'weights': weights,
                'return': ret,
                'volatility': vol,
                'sharpe_ratio': sharpe,
                'success': True
            }
        else:
            logger.error("Optimization failed")
            return {'success': False}

    def maximize_sharpe_ratio(self, expected_returns: np.ndarray,
                             cov_matrix: np.ndarray,
                             constraints: Dict = None) -> Dict:
        """
        Find maximum Sharpe ratio portfolio

        Args:
            expected_returns: Expected returns
            cov_matrix: Covariance matrix
            constraints: Additional constraints

        Returns:
            Optimization result
        """
        n_assets = len(expected_returns)

        # Objective function: maximize Sharpe ratio (minimize negative Sharpe)
        def neg_sharpe(weights):
            ret, vol, sharpe = self.portfolio_performance(weights, expected_returns, cov_matrix)
            return -sharpe

        # Constraints
        cons = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]

        if constraints:
            cons.extend(constraints.get('additional', []))

        # Bounds
        bounds = tuple((0, 1) for _ in range(n_assets))

        # Initial guess
        x0 = np.array([1 / n_assets] * n_assets)

        # Optimize
        result = minimize(
            neg_sharpe,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=cons
        )

        if result.success:
            weights = result.x
            ret, vol, sharpe = self.portfolio_performance(weights, expected_returns, cov_matrix)

            return {
                'weights': weights,
                'return': ret,
                'volatility': vol,
                'sharpe_ratio': sharpe,
                'success': True
            }
        else:
            logger.error("Optimization failed")
            return {'success': False}

    def efficient_frontier(self, expected_returns: np.ndarray,
                          cov_matrix: np.ndarray,
                          n_points: int = 100) -> List[Dict]:
        """
        Generate efficient frontier

        Args:
            expected_returns: Expected returns
            cov_matrix: Covariance matrix
            n_points: Number of points on frontier

        Returns:
            List of portfolio points
        """
        min_return = np.min(expected_returns)
        max_return = np.max(expected_returns)

        target_returns = np.linspace(min_return, max_return, n_points)
        frontier = []

        for target in target_returns:
            result = self.minimize_volatility(expected_returns, cov_matrix, target_return=target)

            if result['success']:
                frontier.append(result)

        return frontier


class BlackLittermanOptimizer:
    """
    Black-Litterman Model
    Combines market equilibrium with investor views
    """

    def __init__(self, risk_free_rate: float = 0.065, risk_aversion: float = 2.5):
        """
        Args:
            risk_free_rate: Risk-free rate
            risk_aversion: Market risk aversion parameter (typically 2-4)
        """
        self.risk_free_rate = risk_free_rate
        self.risk_aversion = risk_aversion

    def calculate_implied_returns(self, market_caps: np.ndarray,
                                  cov_matrix: np.ndarray) -> np.ndarray:
        """
        Calculate market equilibrium implied returns

        Args:
            market_caps: Market capitalizations (proxy for market weights)
            cov_matrix: Covariance matrix

        Returns:
            Implied equilibrium returns
        """
        # Market weights
        market_weights = market_caps / np.sum(market_caps)

        # Implied returns: π = δ * Σ * w
        implied_returns = self.risk_aversion * np.dot(cov_matrix, market_weights)

        return implied_returns

    def black_litterman(self, cov_matrix: np.ndarray,
                       market_caps: np.ndarray,
                       views_matrix: np.ndarray,
                       views_returns: np.ndarray,
                       tau: float = 0.025) -> np.ndarray:
        """
        Black-Litterman expected returns

        Args:
            cov_matrix: Covariance matrix
            market_caps: Market capitalizations
            views_matrix: P matrix (views on assets)
            views_returns: Q vector (expected returns from views)
            tau: Uncertainty in prior (typically 0.01 - 0.05)

        Returns:
            Black-Litterman expected returns
        """
        # Implied equilibrium returns
        pi = self.calculate_implied_returns(market_caps, cov_matrix)

        # Omega: uncertainty in views (diagonal matrix)
        omega = np.diag(np.diag(np.dot(views_matrix, np.dot(tau * cov_matrix, views_matrix.T))))

        # Black-Litterman formula
        # E[R] = [(τΣ)^(-1) + P^T Ω^(-1) P]^(-1) [(τΣ)^(-1)π + P^T Ω^(-1) Q]

        tau_sigma = tau * cov_matrix
        tau_sigma_inv = linalg.inv(tau_sigma)

        omega_inv = linalg.inv(omega)

        # Posterior covariance
        M_inv = tau_sigma_inv + np.dot(views_matrix.T, np.dot(omega_inv, views_matrix))
        M = linalg.inv(M_inv)

        # Posterior expected returns
        bl_returns = np.dot(M, np.dot(tau_sigma_inv, pi) + np.dot(views_matrix.T, np.dot(omega_inv, views_returns)))

        return bl_returns

    def optimize_with_views(self, price_data: pd.DataFrame,
                           market_caps: np.ndarray,
                           views: List[Dict]) -> Dict:
        """
        Optimize portfolio using Black-Litterman with investor views

        Args:
            price_data: Price data
            market_caps: Market caps for each stock
            views: List of view dictionaries
                   [{'assets': [0, 1], 'weights': [1, -0.5], 'return': 0.05}]

        Returns:
            Optimal weights
        """
        # Calculate covariance
        returns = price_data.pct_change().dropna()
        cov_matrix = returns.cov().values * 252

        n_assets = len(price_data.columns)

        # Construct P and Q matrices from views
        n_views = len(views)
        P = np.zeros((n_views, n_assets))
        Q = np.zeros(n_views)

        for i, view in enumerate(views):
            for asset, weight in zip(view['assets'], view['weights']):
                P[i, asset] = weight
            Q[i] = view['return']

        # Black-Litterman returns
        bl_returns = self.black_litterman(cov_matrix, market_caps, P, Q)

        # Optimize using Markowitz with BL returns
        markowitz = MarkowitzOptimizer(self.risk_free_rate)
        result = markowitz.maximize_sharpe_ratio(bl_returns, cov_matrix)

        if result['success']:
            result['bl_returns'] = bl_returns
            return result
        else:
            return {'success': False}


class RiskParityOptimizer:
    """
    Risk Parity Portfolio Optimization
    Equal risk contribution from each asset
    """

    def __init__(self):
        pass

    def calculate_risk_contribution(self, weights: np.ndarray,
                                   cov_matrix: np.ndarray) -> np.ndarray:
        """
        Calculate risk contribution of each asset

        Args:
            weights: Portfolio weights
            cov_matrix: Covariance matrix

        Returns:
            Risk contribution array
        """
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        # Marginal contribution to risk
        marginal_risk = np.dot(cov_matrix, weights) / portfolio_volatility

        # Risk contribution
        risk_contribution = weights * marginal_risk

        return risk_contribution

    def optimize_risk_parity(self, cov_matrix: np.ndarray,
                            target_risk: np.ndarray = None) -> Dict:
        """
        Find risk parity portfolio

        Args:
            cov_matrix: Covariance matrix
            target_risk: Target risk contribution (default: equal)

        Returns:
            Optimization result
        """
        n_assets = cov_matrix.shape[0]

        if target_risk is None:
            target_risk = np.ones(n_assets) / n_assets

        # Objective: minimize difference between actual and target risk contributions
        def objective(weights):
            risk_contrib = self.calculate_risk_contribution(weights, cov_matrix)
            risk_contrib_pct = risk_contrib / np.sum(risk_contrib)
            return np.sum((risk_contrib_pct - target_risk) ** 2)

        # Constraints
        cons = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
        ]

        # Bounds
        bounds = tuple((0.001, 1) for _ in range(n_assets))  # Minimum weight to avoid division issues

        # Initial guess
        x0 = np.array([1 / n_assets] * n_assets)

        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=cons
        )

        if result.success:
            weights = result.x
            risk_contrib = self.calculate_risk_contribution(weights, cov_matrix)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

            return {
                'weights': weights,
                'volatility': portfolio_vol,
                'risk_contributions': risk_contrib,
                'risk_contributions_pct': risk_contrib / np.sum(risk_contrib),
                'success': True
            }
        else:
            logger.error("Risk parity optimization failed")
            return {'success': False}


class HierarchicalRiskParity:
    """
    Hierarchical Risk Parity (HRP)
    Advanced diversification using machine learning clustering
    """

    def __init__(self):
        pass

    def calculate_distance_matrix(self, cov_matrix: np.ndarray) -> np.ndarray:
        """Calculate distance matrix from covariance"""
        corr_matrix = self._cov_to_corr(cov_matrix)
        distance = np.sqrt((1 - corr_matrix) / 2)
        return distance

    def _cov_to_corr(self, cov_matrix: np.ndarray) -> np.ndarray:
        """Convert covariance to correlation"""
        std = np.sqrt(np.diag(cov_matrix))
        corr_matrix = cov_matrix / np.outer(std, std)
        return corr_matrix

    def quasi_diagonalization(self, link_matrix: np.ndarray) -> List:
        """
        Quasi-diagonalize using hierarchical clustering

        Args:
            link_matrix: Linkage matrix from clustering

        Returns:
            Sorted indices
        """
        # Recursive bisection
        sorted_indices = []

        def recurse(cluster_items):
            if len(cluster_items) == 1:
                sorted_indices.append(cluster_items[0])
            else:
                mid = len(cluster_items) // 2
                left = cluster_items[:mid]
                right = cluster_items[mid:]
                recurse(left)
                recurse(right)

        n = link_matrix.shape[0] + 1
        recurse(list(range(n)))

        return sorted_indices

    def recursive_bisection(self, cov_matrix: np.ndarray,
                           sorted_indices: List) -> np.ndarray:
        """
        Allocate weights using recursive bisection

        Args:
            cov_matrix: Covariance matrix
            sorted_indices: Sorted asset indices

        Returns:
            Portfolio weights
        """
        n_assets = len(sorted_indices)
        weights = np.ones(n_assets)

        def bisect(indices, weight):
            if len(indices) == 1:
                weights[indices[0]] = weight
            else:
                mid = len(indices) // 2
                left_indices = indices[:mid]
                right_indices = indices[mid:]

                # Calculate cluster variances
                left_var = self._cluster_variance(cov_matrix, left_indices)
                right_var = self._cluster_variance(cov_matrix, right_indices)

                # Allocate inversely proportional to variance
                total_inv_var = 1 / left_var + 1 / right_var
                left_weight = weight * (1 / left_var) / total_inv_var
                right_weight = weight * (1 / right_var) / total_inv_var

                bisect(left_indices, left_weight)
                bisect(right_indices, right_weight)

        bisect(list(range(n_assets)), 1.0)

        # Reorder weights
        hrp_weights = np.zeros(n_assets)
        for i, idx in enumerate(sorted_indices):
            hrp_weights[idx] = weights[i]

        return hrp_weights

    def _cluster_variance(self, cov_matrix: np.ndarray, indices: List) -> float:
        """Calculate variance of a cluster"""
        cov_cluster = cov_matrix[np.ix_(indices, indices)]
        inv_diag = 1 / np.diag(cov_cluster)
        weights = inv_diag / np.sum(inv_diag)
        cluster_var = np.dot(weights.T, np.dot(cov_cluster, weights))
        return cluster_var


if __name__ == "__main__":
    logger.info("Advanced Portfolio Optimization - Institutional Grade")

    # Example: Generate sample data
    np.random.seed(42)
    n_assets = 5
    n_days = 1000

    # Simulate correlated returns
    mean_returns = np.random.uniform(0.05, 0.15, n_assets)
    cov_matrix = np.random.rand(n_assets, n_assets)
    cov_matrix = (cov_matrix + cov_matrix.T) / 2 + np.eye(n_assets) * 0.1

    returns = np.random.multivariate_normal(mean_returns / 252, cov_matrix / 252, n_days)
    prices = 100 * np.exp(np.cumsum(returns, axis=0))

    price_data = pd.DataFrame(prices, columns=[f'Stock{i}' for i in range(n_assets)])

    # Markowitz optimization
    print("\n=== Markowitz Optimization ===")
    markowitz = MarkowitzOptimizer()
    exp_returns, cov_mat = markowitz.calculate_returns_covariance(price_data)

    max_sharpe = markowitz.maximize_sharpe_ratio(exp_returns, cov_mat)
    if max_sharpe['success']:
        print(f"Max Sharpe Portfolio:")
        print(f"  Weights: {max_sharpe['weights']}")
        print(f"  Return: {max_sharpe['return']:.2%}")
        print(f"  Volatility: {max_sharpe['volatility']:.2%}")
        print(f"  Sharpe Ratio: {max_sharpe['sharpe_ratio']:.2f}")

    # Risk Parity
    print("\n=== Risk Parity ===")
    risk_parity = RiskParityOptimizer()
    rp_result = risk_parity.optimize_risk_parity(cov_mat)
    if rp_result['success']:
        print(f"Risk Parity Portfolio:")
        print(f"  Weights: {rp_result['weights']}")
        print(f"  Volatility: {rp_result['volatility']:.2%}")
        print(f"  Risk Contributions: {rp_result['risk_contributions_pct']}")
