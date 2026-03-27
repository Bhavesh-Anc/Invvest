"""
Statistical Arbitrage and Pairs Trading Strategies
Institutional-grade implementation with cointegration, mean reversion, and momentum
"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import coint, adfuller
from statsmodels.regression.linear_model import OLS
from typing import List, Tuple, Dict, Optional
import logging
from itertools import combinations
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PairsTradingStrategy:
    """
    Pairs Trading using Cointegration
    Based on Engle-Granger two-step method
    """

    def __init__(self, entry_threshold: float = 2.0, exit_threshold: float = 0.5,
                 stop_loss: float = 3.0):
        """
        Args:
            entry_threshold: Z-score threshold to enter trade (e.g., 2.0)
            exit_threshold: Z-score threshold to exit trade (e.g., 0.5)
            stop_loss: Z-score threshold for stop loss (e.g., 3.0)
        """
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.stop_loss = stop_loss

        self.cointegrated_pairs = []
        self.pair_params = {}

    def find_cointegrated_pairs(self, price_data: pd.DataFrame,
                                significance_level: float = 0.05) -> List[Tuple]:
        """
        Find cointegrated pairs from price data

        Args:
            price_data: DataFrame with columns as stock symbols, rows as dates
            significance_level: P-value threshold for cointegration

        Returns:
            List of (stock1, stock2, p_value, hedge_ratio) tuples
        """
        n_stocks = price_data.shape[1]
        stock_names = price_data.columns.tolist()

        cointegrated_pairs = []

        # Test all combinations
        for i in range(n_stocks):
            for j in range(i + 1, n_stocks):
                stock1 = stock_names[i]
                stock2 = stock_names[j]

                price1 = price_data[stock1].values
                price2 = price_data[stock2].values

                # Perform cointegration test
                score, pvalue, _ = coint(price1, price2)

                if pvalue < significance_level:
                    # Calculate hedge ratio using OLS
                    model = OLS(price1, price2).fit()
                    hedge_ratio = model.params[0]

                    cointegrated_pairs.append((stock1, stock2, pvalue, hedge_ratio))

                    # Store parameters
                    self.pair_params[(stock1, stock2)] = {
                        'hedge_ratio': hedge_ratio,
                        'pvalue': pvalue
                    }

        self.cointegrated_pairs = sorted(cointegrated_pairs, key=lambda x: x[2])

        logger.info(f"Found {len(cointegrated_pairs)} cointegrated pairs")

        return cointegrated_pairs

    def calculate_spread(self, price1: np.ndarray, price2: np.ndarray,
                        hedge_ratio: float) -> np.ndarray:
        """
        Calculate spread between two stocks

        Args:
            price1: Price series of stock 1
            price2: Price series of stock 2
            hedge_ratio: Hedge ratio from cointegration

        Returns:
            Spread series
        """
        return price1 - hedge_ratio * price2

    def calculate_zscore(self, spread: np.ndarray, window: int = 20) -> np.ndarray:
        """
        Calculate rolling z-score of spread

        Args:
            spread: Spread series
            window: Rolling window size

        Returns:
            Z-score series
        """
        spread_series = pd.Series(spread)
        mean = spread_series.rolling(window=window).mean()
        std = spread_series.rolling(window=window).std()

        zscore = (spread_series - mean) / std
        return zscore.values

    def generate_signals(self, price_data: pd.DataFrame, stock1: str, stock2: str,
                        hedge_ratio: float = None) -> pd.DataFrame:
        """
        Generate trading signals for a pair

        Args:
            price_data: DataFrame with price data
            stock1: First stock symbol
            stock2: Second stock symbol
            hedge_ratio: Hedge ratio (calculated if not provided)

        Returns:
            DataFrame with signals
        """
        price1 = price_data[stock1].values
        price2 = price_data[stock2].values

        # Get hedge ratio
        if hedge_ratio is None:
            if (stock1, stock2) in self.pair_params:
                hedge_ratio = self.pair_params[(stock1, stock2)]['hedge_ratio']
            else:
                model = OLS(price1, price2).fit()
                hedge_ratio = model.params[0]

        # Calculate spread and z-score
        spread = self.calculate_spread(price1, price2, hedge_ratio)
        zscore = self.calculate_zscore(spread)

        # Generate signals
        signals = pd.DataFrame(index=price_data.index)
        signals['price1'] = price1
        signals['price2'] = price2
        signals['spread'] = spread
        signals['zscore'] = zscore
        signals['signal'] = 0

        # Entry signals
        signals.loc[zscore > self.entry_threshold, 'signal'] = -1  # Short stock1, long stock2
        signals.loc[zscore < -self.entry_threshold, 'signal'] = 1  # Long stock1, short stock2

        # Exit signals
        signals.loc[np.abs(zscore) < self.exit_threshold, 'signal'] = 0

        # Stop loss
        signals.loc[zscore > self.stop_loss, 'signal'] = 0
        signals.loc[zscore < -self.stop_loss, 'signal'] = 0

        return signals

    def backtest_pair(self, price_data: pd.DataFrame, stock1: str, stock2: str,
                     initial_capital: float = 1000000) -> Dict:
        """
        Backtest pairs trading strategy

        Args:
            price_data: Price data
            stock1: First stock
            stock2: Second stock
            initial_capital: Starting capital

        Returns:
            Backtest results
        """
        hedge_ratio = self.pair_params.get((stock1, stock2), {}).get('hedge_ratio')
        signals = self.generate_signals(price_data, stock1, stock2, hedge_ratio)

        # Initialize positions
        position = 0  # 0 = no position, 1 = long spread, -1 = short spread
        pnl = []
        trades = []
        capital = initial_capital

        for i in range(1, len(signals)):
            signal = signals['signal'].iloc[i]

            # Entry
            if position == 0 and signal != 0:
                position = signal
                entry_price1 = signals['price1'].iloc[i]
                entry_price2 = signals['price2'].iloc[i]
                entry_spread = signals['spread'].iloc[i]

                trades.append({
                    'date': signals.index[i],
                    'action': 'ENTRY',
                    'position': position,
                    'price1': entry_price1,
                    'price2': entry_price2,
                    'spread': entry_spread
                })

            # Exit
            elif position != 0 and signal == 0:
                exit_price1 = signals['price1'].iloc[i]
                exit_price2 = signals['price2'].iloc[i]
                exit_spread = signals['spread'].iloc[i]

                # Calculate P&L
                if position == 1:  # Long spread
                    trade_pnl = exit_spread - entry_spread
                else:  # Short spread
                    trade_pnl = entry_spread - exit_spread

                pnl.append(trade_pnl)
                capital += trade_pnl

                trades.append({
                    'date': signals.index[i],
                    'action': 'EXIT',
                    'position': position,
                    'price1': exit_price1,
                    'price2': exit_price2,
                    'spread': exit_spread,
                    'pnl': trade_pnl
                })

                position = 0

        # Calculate metrics
        if len(pnl) > 0:
            total_return = (capital - initial_capital) / initial_capital
            sharpe_ratio = np.mean(pnl) / (np.std(pnl) + 1e-6) * np.sqrt(252)
            win_rate = sum(1 for p in pnl if p > 0) / len(pnl)
            max_drawdown = self._calculate_max_drawdown(pnl)
        else:
            total_return = 0
            sharpe_ratio = 0
            win_rate = 0
            max_drawdown = 0

        results = {
            'stock1': stock1,
            'stock2': stock2,
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_return': total_return,
            'num_trades': len(pnl),
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'trades': trades,
            'pnl_series': pnl
        }

        return results

    def _calculate_max_drawdown(self, pnl_series: List[float]) -> float:
        """Calculate maximum drawdown"""
        cumulative = np.cumsum(pnl_series)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / (running_max + 1)
        return np.min(drawdown)


class MeanReversionStrategy:
    """
    Mean Reversion Strategy using Ornstein-Uhlenbeck Process
    """

    def __init__(self, lookback_period: int = 20, entry_threshold: float = 1.5,
                 exit_threshold: float = 0.5):
        """
        Args:
            lookback_period: Period for calculating mean and std
            entry_threshold: Z-score threshold to enter
            exit_threshold: Z-score threshold to exit
        """
        self.lookback_period = lookback_period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold

    def calculate_ou_parameters(self, prices: np.ndarray) -> Tuple[float, float, float]:
        """
        Estimate Ornstein-Uhlenbeck parameters

        Args:
            prices: Price series

        Returns:
            (theta, mu, sigma) - mean reversion speed, long-term mean, volatility
        """
        log_prices = np.log(prices)
        delta_log_prices = np.diff(log_prices)

        # OLS regression: delta_log_price = theta * (mu - log_price) + noise
        X = log_prices[:-1].reshape(-1, 1)
        y = delta_log_prices

        model = OLS(y, np.c_[np.ones(len(X)), X]).fit()

        theta = -model.params[1]
        mu = model.params[0] / theta
        sigma = np.std(model.resid)

        return theta, mu, sigma

    def calculate_half_life(self, prices: np.ndarray) -> float:
        """
        Calculate half-life of mean reversion

        Args:
            prices: Price series

        Returns:
            Half-life in days
        """
        theta, _, _ = self.calculate_ou_parameters(prices)
        half_life = np.log(2) / theta
        return half_life

    def generate_signals(self, price_data: pd.Series) -> pd.DataFrame:
        """
        Generate mean reversion signals

        Args:
            price_data: Price series

        Returns:
            DataFrame with signals
        """
        signals = pd.DataFrame(index=price_data.index)
        signals['price'] = price_data.values

        # Calculate z-score
        signals['mean'] = price_data.rolling(window=self.lookback_period).mean()
        signals['std'] = price_data.rolling(window=self.lookback_period).std()
        signals['zscore'] = (price_data - signals['mean']) / signals['std']

        # Generate signals
        signals['signal'] = 0

        # Entry signals
        signals.loc[signals['zscore'] > self.entry_threshold, 'signal'] = -1  # Short (overvalued)
        signals.loc[signals['zscore'] < -self.entry_threshold, 'signal'] = 1  # Long (undervalued)

        # Exit signals
        signals.loc[np.abs(signals['zscore']) < self.exit_threshold, 'signal'] = 0

        return signals


class StatisticalArbitragePortfolio:
    """
    Statistical Arbitrage Portfolio Manager
    Combines multiple pairs and mean reversion strategies
    """

    def __init__(self, capital_per_pair: float = 1000000):
        """
        Args:
            capital_per_pair: Capital allocated per pair
        """
        self.capital_per_pair = capital_per_pair
        self.active_pairs = {}
        self.pairs_strategy = PairsTradingStrategy()
        self.mean_reversion = MeanReversionStrategy()

    def discover_opportunities(self, price_data: pd.DataFrame,
                              min_cointegration_score: float = 0.05) -> List[Dict]:
        """
        Discover statistical arbitrage opportunities

        Args:
            price_data: Price data for multiple stocks
            min_cointegration_score: Maximum p-value for cointegration

        Returns:
            List of opportunities with scores
        """
        # Find cointegrated pairs
        pairs = self.pairs_strategy.find_cointegrated_pairs(
            price_data, significance_level=min_cointegration_score
        )

        opportunities = []

        for stock1, stock2, pvalue, hedge_ratio in pairs:
            # Calculate spread
            price1 = price_data[stock1].values
            price2 = price_data[stock2].values
            spread = price1 - hedge_ratio * price2

            # Test stationarity of spread
            adf_result = adfuller(spread)
            is_stationary = adf_result[1] < 0.05

            if is_stationary:
                # Calculate half-life
                half_life = self.mean_reversion.calculate_half_life(spread)

                # Calculate current z-score
                zscore = self.pairs_strategy.calculate_zscore(spread)[-1]

                opportunities.append({
                    'stock1': stock1,
                    'stock2': stock2,
                    'pvalue': pvalue,
                    'hedge_ratio': hedge_ratio,
                    'half_life': half_life,
                    'current_zscore': zscore,
                    'is_stationary': is_stationary,
                    'score': abs(zscore) / pvalue  # Opportunity score
                })

        # Sort by score
        opportunities = sorted(opportunities, key=lambda x: x['score'], reverse=True)

        logger.info(f"Found {len(opportunities)} statistical arbitrage opportunities")

        return opportunities

    def allocate_capital(self, opportunities: List[Dict], max_pairs: int = 10) -> Dict:
        """
        Allocate capital to top opportunities

        Args:
            opportunities: List of opportunities
            max_pairs: Maximum number of pairs to trade

        Returns:
            Allocation dictionary
        """
        selected_pairs = opportunities[:max_pairs]

        allocation = {}

        for pair in selected_pairs:
            key = (pair['stock1'], pair['stock2'])
            allocation[key] = {
                'capital': self.capital_per_pair,
                'hedge_ratio': pair['hedge_ratio'],
                'half_life': pair['half_life'],
                'score': pair['score']
            }

        return allocation

    def calculate_portfolio_statistics(self, backtest_results: List[Dict]) -> Dict:
        """
        Calculate portfolio-level statistics

        Args:
            backtest_results: List of backtest results for each pair

        Returns:
            Portfolio statistics
        """
        total_return = np.mean([r['total_return'] for r in backtest_results])
        avg_sharpe = np.mean([r['sharpe_ratio'] for r in backtest_results])
        total_trades = sum([r['num_trades'] for r in backtest_results])
        avg_win_rate = np.mean([r['win_rate'] for r in backtest_results])

        # Combine PnL series
        all_pnl = []
        for result in backtest_results:
            all_pnl.extend(result['pnl_series'])

        if len(all_pnl) > 0:
            portfolio_sharpe = np.mean(all_pnl) / (np.std(all_pnl) + 1e-6) * np.sqrt(252)
        else:
            portfolio_sharpe = 0

        return {
            'num_pairs': len(backtest_results),
            'total_return': total_return,
            'average_sharpe': avg_sharpe,
            'portfolio_sharpe': portfolio_sharpe,
            'total_trades': total_trades,
            'average_win_rate': avg_win_rate
        }


if __name__ == "__main__":
    logger.info("Statistical Arbitrage Module - Institutional Grade")

    # Example: Generate synthetic data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')

    # Create two cointegrated stocks
    stock1_prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)
    stock2_prices = 50 + 0.5 * stock1_prices + np.random.randn(len(dates)) * 2

    price_data = pd.DataFrame({
        'STOCK1': stock1_prices,
        'STOCK2': stock2_prices
    }, index=dates)

    # Find cointegrated pairs
    pairs_strategy = PairsTradingStrategy()
    pairs = pairs_strategy.find_cointegrated_pairs(price_data)

    if len(pairs) > 0:
        print(f"Found cointegrated pair: {pairs[0]}")

        # Generate signals
        signals = pairs_strategy.generate_signals(price_data, 'STOCK1', 'STOCK2')
        print(f"Generated {len(signals[signals['signal'] != 0])} signals")

        # Backtest
        results = pairs_strategy.backtest_pair(price_data, 'STOCK1', 'STOCK2')
        print(f"Backtest Results:")
        print(f"  Total Return: {results['total_return']:.2%}")
        print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"  Win Rate: {results['win_rate']:.2%}")
        print(f"  Num Trades: {results['num_trades']}")
