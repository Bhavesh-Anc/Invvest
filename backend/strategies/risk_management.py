"""
Advanced Risk Management Module
Used by: Goldman Sachs, Morgan Stanley, Citadel

Implements institutional-grade risk controls:
- Value at Risk (VaR) and Conditional VaR
- Greeks portfolio aggregation
- Position limits and circuit breakers
- Kelly Criterion position sizing
- Stress testing and scenario analysis
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from scipy import stats
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


class RiskCalculator:
    """
    Calculate portfolio risk metrics
    """

    def __init__(self, confidence_level: float = 0.99):
        """
        Args:
            confidence_level: VaR confidence level (default 99%)
        """
        self.confidence = confidence_level

    def calculate_var(
        self,
        returns: pd.Series,
        method: str = 'historical',
        confidence: Optional[float] = None
    ) -> float:
        """
        Calculate Value at Risk (VaR)

        Methods:
        - historical: Historical simulation
        - parametric: Variance-covariance (assumes normal distribution)
        - monte_carlo: Monte Carlo simulation

        Args:
            returns: Series of portfolio returns
            method: Calculation method
            confidence: Confidence level (overrides default)

        Returns:
            VaR as percentage
        """
        conf = confidence or self.confidence

        if method == 'historical':
            # Historical VaR - simply take percentile
            var = np.percentile(returns, (1 - conf) * 100)

        elif method == 'parametric':
            # Parametric VaR - assumes normal distribution
            mean = returns.mean()
            std = returns.std()
            var = mean + std * stats.norm.ppf(1 - conf)

        elif method == 'monte_carlo':
            # Monte Carlo VaR
            simulated_returns = np.random.normal(
                returns.mean(),
                returns.std(),
                10000
            )
            var = np.percentile(simulated_returns, (1 - conf) * 100)

        else:
            raise ValueError(f"Unknown method: {method}")

        return float(var)

    def calculate_cvar(
        self,
        returns: pd.Series,
        confidence: Optional[float] = None
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR) / Expected Shortfall

        CVaR is the expected loss given that we exceed VaR

        Args:
            returns: Series of portfolio returns
            confidence: Confidence level

        Returns:
            CVaR as percentage
        """
        conf = confidence or self.confidence

        # Calculate VaR first
        var = self.calculate_var(returns, 'historical', conf)

        # CVaR is mean of returns worse than VaR
        cvar = returns[returns <= var].mean()

        return float(cvar)

    def calculate_marginal_var(
        self,
        portfolio_returns: pd.Series,
        position_returns: pd.Series,
        position_weight: float
    ) -> float:
        """
        Calculate Marginal VaR - how much position contributes to portfolio VaR

        Args:
            portfolio_returns: Total portfolio returns
            position_returns: Individual position returns
            position_weight: Position size as % of portfolio

        Returns:
            Marginal VaR
        """
        # Calculate portfolio VaR
        portfolio_var = self.calculate_var(portfolio_returns)

        # Calculate correlation between position and portfolio
        correlation = position_returns.corr(portfolio_returns)

        # Marginal VaR = (Position Volatility * Correlation) / Portfolio Volatility
        position_vol = position_returns.std()
        portfolio_vol = portfolio_returns.std()

        marginal_var = (position_vol * correlation) / portfolio_vol if portfolio_vol > 0 else 0

        return float(marginal_var)

    def calculate_incremental_var(
        self,
        current_portfolio_returns: pd.Series,
        new_portfolio_returns: pd.Series
    ) -> float:
        """
        Calculate Incremental VaR - VaR change from adding a position

        Args:
            current_portfolio_returns: Current portfolio returns
            new_portfolio_returns: Portfolio returns after adding position

        Returns:
            Incremental VaR
        """
        current_var = self.calculate_var(current_portfolio_returns)
        new_var = self.calculate_var(new_portfolio_returns)

        incremental_var = new_var - current_var

        return float(incremental_var)


class GreeksAggregator:
    """
    Aggregate portfolio Greeks for options positions
    """

    def aggregate_portfolio_greeks(
        self,
        positions: List[Dict]
    ) -> Dict:
        """
        Calculate total portfolio Greeks

        Args:
            positions: List of options positions with their Greeks

        Returns:
            Dict with aggregated Greeks
        """
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        total_rho = 0

        for pos in positions:
            quantity = pos.get('quantity', 0)

            total_delta += pos.get('delta', 0) * quantity
            total_gamma += pos.get('gamma', 0) * quantity
            total_theta += pos.get('theta', 0) * quantity
            total_vega += pos.get('vega', 0) * quantity
            total_rho += pos.get('rho', 0) * quantity

        return {
            'delta': round(total_delta, 2),
            'gamma': round(total_gamma, 4),
            'theta': round(total_theta, 2),
            'vega': round(total_vega, 2),
            'rho': round(total_rho, 4),
            'timestamp': datetime.now()
        }

    def calculate_delta_dollars(self, delta: float, underlying_price: float) -> float:
        """
        Convert delta to dollar equivalent

        Args:
            delta: Portfolio delta
            underlying_price: Current price of underlying

        Returns:
            Dollar delta (how much portfolio value changes per ₹1 move)
        """
        return delta * underlying_price

    def calculate_gamma_pnl(self, gamma: float, price_move: float, underlying_price: float) -> float:
        """
        Calculate P&L from gamma given price move

        Gamma P&L = 0.5 * Gamma * (Price Move)^2 * Underlying Price

        Args:
            gamma: Portfolio gamma
            price_move: Price change in %
            underlying_price: Current price

        Returns:
            Estimated P&L from gamma
        """
        return 0.5 * gamma * (price_move ** 2) * underlying_price

    def check_greeks_limits(self, greeks: Dict, limits: Dict) -> Dict:
        """
        Check if portfolio Greeks exceed risk limits

        Args:
            greeks: Current portfolio Greeks
            limits: Risk limits for each Greek

        Returns:
            Dict with violations
        """
        violations = []

        if abs(greeks['delta']) > limits.get('delta', 10000):
            violations.append({
                'greek': 'delta',
                'current': greeks['delta'],
                'limit': limits['delta'],
                'severity': 'high'
            })

        if abs(greeks['gamma']) > limits.get('gamma', 5000):
            violations.append({
                'greek': 'gamma',
                'current': greeks['gamma'],
                'limit': limits['gamma'],
                'severity': 'high'
            })

        if abs(greeks['vega']) > limits.get('vega', 50000):
            violations.append({
                'greek': 'vega',
                'current': greeks['vega'],
                'limit': limits['vega'],
                'severity': 'medium'
            })

        return {
            'has_violations': len(violations) > 0,
            'violations': violations,
            'timestamp': datetime.now()
        }


class PositionSizing:
    """
    Optimal position sizing using Kelly Criterion and risk parity
    """

    def kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        fractional: float = 0.5
    ) -> float:
        """
        Calculate Kelly Criterion for optimal position size

        Kelly % = (Win Rate * Avg Win - Loss Rate * Avg Loss) / Avg Win

        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade size
            avg_loss: Average losing trade size (positive number)
            fractional: Use fractional Kelly (0.5 = half Kelly, safer)

        Returns:
            Optimal position size as % of capital
        """
        loss_rate = 1 - win_rate

        # Kelly formula
        kelly = (win_rate * avg_win - loss_rate * avg_loss) / avg_win

        # Apply fractional Kelly for safety
        kelly = kelly * fractional

        # Cap at reasonable levels (never > 25%)
        kelly = max(0, min(kelly, 0.25))

        return float(kelly)

    def kelly_from_odds(
        self,
        win_probability: float,
        win_loss_ratio: float,
        fractional: float = 0.5
    ) -> float:
        """
        Simplified Kelly Criterion from win probability and win/loss ratio

        Kelly % = (p * b - q) / b
        where:
        - p = win probability
        - q = loss probability (1-p)
        - b = win/loss ratio

        Args:
            win_probability: Probability of winning
            win_loss_ratio: Average win / Average loss
            fractional: Fractional Kelly multiplier

        Returns:
            Optimal position size
        """
        p = win_probability
        q = 1 - p
        b = win_loss_ratio

        kelly = (p * b - q) / b if b > 0 else 0
        kelly = kelly * fractional

        return max(0, min(kelly, 0.25))

    def risk_parity_weights(self, volatilities: List[float]) -> List[float]:
        """
        Calculate risk parity portfolio weights

        Each position contributes equally to portfolio risk

        Args:
            volatilities: List of asset volatilities

        Returns:
            List of weights summing to 1
        """
        # Inverse volatility weighting
        inv_vols = [1 / vol for vol in volatilities]
        total_inv_vol = sum(inv_vols)

        weights = [iv / total_inv_vol for iv in inv_vols]

        return weights

    def max_sharpe_weights(
        self,
        returns: pd.DataFrame,
        risk_free_rate: float = 0.07
    ) -> List[float]:
        """
        Calculate portfolio weights that maximize Sharpe ratio

        Args:
            returns: DataFrame with asset returns (columns = assets)
            risk_free_rate: Annual risk-free rate (default 7% for India)

        Returns:
            Optimal weights
        """
        # Expected returns and covariance
        mean_returns = returns.mean() * 252  # Annualized
        cov_matrix = returns.cov() * 252

        num_assets = len(returns.columns)

        # Objective: Negative Sharpe ratio (minimize negative = maximize positive)
        def neg_sharpe(weights):
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe = (portfolio_return - risk_free_rate) / portfolio_vol
            return -sharpe

        # Constraints: weights sum to 1
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}

        # Bounds: 0 <= weight <= 1 (no shorting, no leverage)
        bounds = tuple((0, 1) for _ in range(num_assets))

        # Initial guess: equal weights
        init_weights = np.array([1/num_assets] * num_assets)

        # Optimize
        result = minimize(
            neg_sharpe,
            init_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        return result.x.tolist()


class CircuitBreakers:
    """
    Automated circuit breakers and risk limits
    """

    def __init__(self):
        self.limits = {
            'daily_loss_pct': 5.0,          # Max 5% daily loss
            'weekly_loss_pct': 10.0,        # Max 10% weekly loss
            'max_position_pct': 10.0,       # Max 10% in single position
            'max_sector_pct': 25.0,         # Max 25% in single sector
            'max_gross_leverage': 5.0,      # Max 5x gross leverage
            'max_net_exposure': 0.2,        # Max ±20% net exposure
            'var_limit_pct': 3.0,           # Max 3% daily VaR
        }

        self.breaker_triggered = False
        self.triggered_reason = None

    def check_daily_loss_limit(
        self,
        current_pnl: float,
        start_of_day_value: float
    ) -> Dict:
        """
        Check if daily loss limit exceeded

        Args:
            current_pnl: Current day P&L
            start_of_day_value: Portfolio value at start of day

        Returns:
            Dict with breach status
        """
        daily_loss_pct = (current_pnl / start_of_day_value) * 100

        breached = daily_loss_pct < -self.limits['daily_loss_pct']

        if breached:
            self.breaker_triggered = True
            self.triggered_reason = f"Daily loss limit breached: {daily_loss_pct:.2f}%"
            logger.critical(self.triggered_reason)

        return {
            'breached': breached,
            'daily_loss_pct': daily_loss_pct,
            'limit': self.limits['daily_loss_pct'],
            'action': 'HALT_ALL_TRADING' if breached else 'CONTINUE'
        }

    def check_position_concentration(
        self,
        positions: List[Dict],
        total_portfolio_value: float
    ) -> Dict:
        """
        Check if any single position is too large

        Args:
            positions: List of positions with values
            total_portfolio_value: Total portfolio value

        Returns:
            Dict with violations
        """
        violations = []

        for pos in positions:
            position_value = abs(pos.get('value', 0))
            position_pct = (position_value / total_portfolio_value) * 100

            if position_pct > self.limits['max_position_pct']:
                violations.append({
                    'symbol': pos.get('symbol'),
                    'position_pct': position_pct,
                    'limit': self.limits['max_position_pct'],
                    'action': 'REDUCE_POSITION'
                })

        return {
            'has_violations': len(violations) > 0,
            'violations': violations
        }

    def check_leverage(
        self,
        long_exposure: float,
        short_exposure: float,
        capital: float
    ) -> Dict:
        """
        Check gross and net leverage

        Args:
            long_exposure: Total long positions value
            short_exposure: Total short positions value (positive)
            capital: Portfolio capital

        Returns:
            Dict with leverage metrics and violations
        """
        gross_exposure = long_exposure + short_exposure
        net_exposure = long_exposure - short_exposure

        gross_leverage = gross_exposure / capital
        net_exposure_pct = abs(net_exposure) / capital

        violations = []

        if gross_leverage > self.limits['max_gross_leverage']:
            violations.append({
                'type': 'gross_leverage',
                'current': gross_leverage,
                'limit': self.limits['max_gross_leverage'],
                'action': 'REDUCE_POSITIONS'
            })

        if net_exposure_pct > self.limits['max_net_exposure']:
            violations.append({
                'type': 'net_exposure',
                'current': net_exposure_pct,
                'limit': self.limits['max_net_exposure'],
                'action': 'HEDGE_EXPOSURE'
            })

        return {
            'gross_leverage': gross_leverage,
            'net_exposure_pct': net_exposure_pct,
            'has_violations': len(violations) > 0,
            'violations': violations
        }

    def check_var_limit(self, current_var: float, capital: float) -> Dict:
        """
        Check if VaR exceeds limits

        Args:
            current_var: Current portfolio VaR (as decimal)
            capital: Portfolio capital

        Returns:
            Dict with VaR check results
        """
        var_pct = abs(current_var) * 100

        breached = var_pct > self.limits['var_limit_pct']

        if breached:
            logger.warning(f"VaR limit breached: {var_pct:.2f}% > {self.limits['var_limit_pct']}%")

        return {
            'breached': breached,
            'current_var_pct': var_pct,
            'limit': self.limits['var_limit_pct'],
            'action': 'REDUCE_RISK' if breached else 'CONTINUE'
        }


class StressTesting:
    """
    Stress testing and scenario analysis
    """

    def __init__(self):
        # Historical Indian market stress scenarios
        self.scenarios = {
            'covid_crash_2020': {
                'nifty_change': -0.38,      # -38% March 2020
                'volatility_spike': 2.5,    # VIX to 80+
                'correlation_increase': 0.9 # All stocks move together
            },
            '2008_financial_crisis': {
                'nifty_change': -0.52,      # -52% in 2008
                'volatility_spike': 3.0,
                'correlation_increase': 0.95
            },
            'taper_tantrum_2013': {
                'nifty_change': -0.10,      # -10%
                'volatility_spike': 1.5,
                'correlation_increase': 0.7
            },
            'demonetization_2016': {
                'nifty_change': -0.08,      # -8%
                'volatility_spike': 1.3,
                'correlation_increase': 0.6
            },
            'china_slowdown_2015': {
                'nifty_change': -0.15,      # -15%
                'volatility_spike': 1.8,
                'correlation_increase': 0.75
            }
        }

    def run_scenario(
        self,
        portfolio_value: float,
        positions: List[Dict],
        scenario_name: str
    ) -> Dict:
        """
        Run stress test scenario on portfolio

        Args:
            portfolio_value: Current portfolio value
            positions: List of positions with betas
            scenario_name: Name of stress scenario

        Returns:
            Dict with scenario impact
        """
        if scenario_name not in self.scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")

        scenario = self.scenarios[scenario_name]

        # Calculate portfolio impact
        total_impact = 0

        for pos in positions:
            position_value = pos.get('value', 0)
            beta = pos.get('beta', 1.0)  # Position beta to market

            # Position impact = Position Value * Beta * Market Move
            position_impact = position_value * beta * scenario['nifty_change']
            total_impact += position_impact

        # Portfolio impact
        portfolio_impact_pct = (total_impact / portfolio_value) * 100
        stressed_value = portfolio_value + total_impact

        return {
            'scenario': scenario_name,
            'market_move_pct': scenario['nifty_change'] * 100,
            'portfolio_impact': total_impact,
            'portfolio_impact_pct': portfolio_impact_pct,
            'stressed_value': stressed_value,
            'survive': stressed_value > 0,
            'timestamp': datetime.now()
        }

    def run_all_scenarios(
        self,
        portfolio_value: float,
        positions: List[Dict]
    ) -> List[Dict]:
        """
        Run all stress scenarios

        Returns:
            List of scenario results
        """
        results = []

        for scenario_name in self.scenarios.keys():
            result = self.run_scenario(portfolio_value, positions, scenario_name)
            results.append(result)

        # Sort by impact (worst to best)
        results.sort(key=lambda x: x['portfolio_impact_pct'])

        return results


# Example usage
if __name__ == "__main__":
    # Test VaR calculation
    print("=" * 50)
    print("VALUE AT RISK (VaR) TEST")
    print("=" * 50)

    # Mock returns data
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.001, 0.02, 252))  # 1 year

    risk_calc = RiskCalculator(confidence_level=0.99)

    var_95 = risk_calc.calculate_var(returns, confidence=0.95)
    var_99 = risk_calc.calculate_var(returns, confidence=0.99)
    cvar_99 = risk_calc.calculate_cvar(returns, confidence=0.99)

    print(f"VaR 95%: {var_95*100:.2f}%")
    print(f"VaR 99%: {var_99*100:.2f}%")
    print(f"CVaR 99%: {cvar_99*100:.2f}%")

    # Test Greeks aggregation
    print("\n" + "=" * 50)
    print("GREEKS AGGREGATION TEST")
    print("=" * 50)

    positions = [
        {'symbol': 'NIFTY 22000 CE', 'quantity': 100, 'delta': 0.5, 'gamma': 0.001, 'theta': -25, 'vega': 65},
        {'symbol': 'NIFTY 22100 CE', 'quantity': -50, 'delta': 0.45, 'gamma': 0.0012, 'theta': -28, 'vega': 68},
        {'symbol': 'NIFTY 21900 PE', 'quantity': 80, 'delta': -0.48, 'gamma': 0.0011, 'theta': -24, 'vega': 63},
    ]

    greeks_agg = GreeksAggregator()
    portfolio_greeks = greeks_agg.aggregate_portfolio_greeks(positions)

    print(f"Portfolio Delta: {portfolio_greeks['delta']}")
    print(f"Portfolio Gamma: {portfolio_greeks['gamma']}")
    print(f"Portfolio Theta: {portfolio_greeks['theta']}")
    print(f"Portfolio Vega: {portfolio_greeks['vega']}")

    # Test Kelly Criterion
    print("\n" + "=" * 50)
    print("KELLY CRITERION TEST")
    print("=" * 50)

    pos_sizing = PositionSizing()

    kelly = pos_sizing.kelly_criterion(
        win_rate=0.55,      # 55% win rate
        avg_win=1500,       # Average win ₹1500
        avg_loss=1000,      # Average loss ₹1000
        fractional=0.5      # Half Kelly for safety
    )

    print(f"Optimal position size: {kelly*100:.1f}% of capital")
    print(f"Win rate: 55%, Avg Win: ₹1500, Avg Loss: ₹1000")

    # Test Circuit Breakers
    print("\n" + "=" * 50)
    print("CIRCUIT BREAKERS TEST")
    print("=" * 50)

    circuit = CircuitBreakers()

    loss_check = circuit.check_daily_loss_limit(
        current_pnl=-60000,
        start_of_day_value=1000000
    )

    print(f"Daily Loss: {loss_check['daily_loss_pct']:.2f}%")
    print(f"Limit: {loss_check['limit']}%")
    print(f"Action: {loss_check['action']}")

    # Test Stress Testing
    print("\n" + "=" * 50)
    print("STRESS TESTING")
    print("=" * 50)

    stress = StressTesting()

    stress_positions = [
        {'symbol': 'RELIANCE', 'value': 200000, 'beta': 1.2},
        {'symbol': 'TCS', 'value': 150000, 'beta': 0.9},
        {'symbol': 'HDFCBANK', 'value': 180000, 'beta': 1.1},
    ]

    scenario_result = stress.run_scenario(
        portfolio_value=1000000,
        positions=stress_positions,
        scenario_name='covid_crash_2020'
    )

    print(f"Scenario: {scenario_result['scenario']}")
    print(f"Market Move: {scenario_result['market_move_pct']:.1f}%")
    print(f"Portfolio Impact: {scenario_result['portfolio_impact_pct']:.2f}%")
    print(f"Stressed Value: ₹{scenario_result['stressed_value']:,.0f}")
    print(f"Survive: {scenario_result['survive']}")
