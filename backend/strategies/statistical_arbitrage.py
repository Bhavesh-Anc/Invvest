"""
Statistical Arbitrage Strategies
Pairs Trading, Mean Reversion, and Momentum strategies for Indian markets
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from scipy import stats
from statsmodels.tsa.stattools import coint, adfuller
from statsmodels.regression.linear_model import OLS

logger = logging.getLogger(__name__)


class PairsTrading:
    """
    Pairs Trading Strategy - Long-Short Statistical Arbitrage

    Used by: Jane Street, Citadel, Two Sigma

    Strategy:
    1. Find cointegrated stock pairs (move together historically)
    2. Calculate spread between pairs
    3. When spread deviates significantly, trade mean reversion
    4. Long underperformer, Short overperformer
    """

    def __init__(self, lookback_period: int = 60, z_entry: float = 2.0, z_exit: float = 0.5):
        """
        Args:
            lookback_period: Days of history to calculate mean/std
            z_entry: Z-score threshold to enter position (default 2.0 = 2 std devs)
            z_exit: Z-score threshold to exit position (default 0.5)
        """
        self.lookback_period = lookback_period
        self.z_entry = z_entry
        self.z_exit = z_exit

        # Indian market pairs (known to be correlated)
        self.candidate_pairs = [
            ('HDFCBANK', 'ICICIBANK'),  # Private banks
            ('SBIN', 'PNB'),            # PSU banks
            ('TCS', 'INFY'),            # IT services
            ('WIPRO', 'TECHM'),         # Mid-tier IT
            ('RELIANCE', 'ONGC'),       # Oil & Gas
            ('BPCL', 'IOC'),            # Oil refiners
            ('MARUTI', 'TATAMOTORS'),   # Auto
            ('HEROMOTOCO', 'BAJAJ-AUTO'), # Two-wheelers
            ('ASIANPAINT', 'BERGER'),   # Paints
            ('TITAN', 'KALYANIJWEL'),   # Jewelry
            ('COALINDIA', 'NMDC'),      # Mining
            ('POWERGRID', 'NTPC'),      # Power utilities
        ]

    def test_cointegration(self, price_series_1: pd.Series, price_series_2: pd.Series) -> Dict:
        """
        Test if two price series are cointegrated using Engle-Granger test

        Returns:
            Dict with cointegration test results
        """
        try:
            # Engle-Granger cointegration test
            score, p_value, _ = coint(price_series_1, price_series_2)

            # Augmented Dickey-Fuller test on spread
            # Calculate spread using OLS regression
            model = OLS(price_series_1, price_series_2).fit()
            hedge_ratio = model.params[0]
            spread = price_series_1 - hedge_ratio * price_series_2

            adf_stat, adf_p_value, *_ = adfuller(spread)

            # Cointegrated if p-value < 0.05 (95% confidence)
            is_cointegrated = p_value < 0.05 and adf_p_value < 0.05

            return {
                'is_cointegrated': is_cointegrated,
                'p_value': p_value,
                'adf_p_value': adf_p_value,
                'hedge_ratio': hedge_ratio,
                'correlation': price_series_1.corr(price_series_2),
                'spread_mean': spread.mean(),
                'spread_std': spread.std()
            }

        except Exception as e:
            logger.error(f"Error in cointegration test: {e}")
            return {'is_cointegrated': False, 'error': str(e)}

    def find_cointegrated_pairs(self, price_data: Dict[str, pd.Series]) -> List[Dict]:
        """
        Find all cointegrated pairs from candidate list

        Args:
            price_data: Dict mapping symbol to price series

        Returns:
            List of cointegrated pairs with their statistics
        """
        cointegrated_pairs = []

        for stock1, stock2 in self.candidate_pairs:
            if stock1 not in price_data or stock2 not in price_data:
                continue

            result = self.test_cointegration(
                price_data[stock1],
                price_data[stock2]
            )

            if result['is_cointegrated']:
                cointegrated_pairs.append({
                    'pair': (stock1, stock2),
                    'hedge_ratio': result['hedge_ratio'],
                    'spread_mean': result['spread_mean'],
                    'spread_std': result['spread_std'],
                    'correlation': result['correlation'],
                    'p_value': result['p_value']
                })

                logger.info(f"Found cointegrated pair: {stock1}-{stock2} "
                          f"(p={result['p_value']:.4f}, corr={result['correlation']:.2f})")

        return cointegrated_pairs

    def calculate_spread(self, price1: pd.Series, price2: pd.Series, hedge_ratio: float) -> pd.Series:
        """Calculate spread between two stocks using hedge ratio"""
        return price1 - hedge_ratio * price2

    def generate_signals(
        self,
        stock1: str,
        stock2: str,
        price1: pd.Series,
        price2: pd.Series,
        hedge_ratio: float
    ) -> Dict:
        """
        Generate trading signals based on spread z-score

        Returns:
            Dict with signal ('long_stock1', 'short_stock1', 'close', or 'hold')
        """
        # Calculate spread
        spread = self.calculate_spread(price1, price2, hedge_ratio)

        # Recent spread statistics
        spread_recent = spread.iloc[-self.lookback_period:]
        spread_mean = spread_recent.mean()
        spread_std = spread_recent.std()

        # Current spread z-score
        current_spread = spread.iloc[-1]
        z_score = (current_spread - spread_mean) / spread_std if spread_std > 0 else 0

        # Generate signal
        signal = None
        if z_score > self.z_entry:
            # Spread too high - stock1 overvalued relative to stock2
            signal = 'short_stock1_long_stock2'
            explanation = f"{stock1} overvalued vs {stock2} (z={z_score:.2f})"

        elif z_score < -self.z_entry:
            # Spread too low - stock1 undervalued relative to stock2
            signal = 'long_stock1_short_stock2'
            explanation = f"{stock1} undervalued vs {stock2} (z={z_score:.2f})"

        elif abs(z_score) < self.z_exit:
            # Spread returned to mean - close position
            signal = 'close_position'
            explanation = f"Spread normalized (z={z_score:.2f})"

        else:
            signal = 'hold'
            explanation = f"No action (z={z_score:.2f})"

        return {
            'signal': signal,
            'z_score': z_score,
            'current_spread': current_spread,
            'spread_mean': spread_mean,
            'spread_std': spread_std,
            'explanation': explanation,
            'stock1': stock1,
            'stock2': stock2,
            'hedge_ratio': hedge_ratio,
            'timestamp': datetime.now()
        }

    def calculate_position_size(
        self,
        capital: float,
        stock1_price: float,
        stock2_price: float,
        hedge_ratio: float,
        max_position_pct: float = 0.1
    ) -> Dict:
        """
        Calculate optimal position sizes for pair

        Args:
            capital: Total capital available
            stock1_price: Current price of stock1
            stock2_price: Current price of stock2
            hedge_ratio: Beta between stocks
            max_position_pct: Max % of capital per position (default 10%)

        Returns:
            Dict with quantities to trade
        """
        # Allocate capital equally to both legs
        capital_per_leg = capital * max_position_pct / 2

        # Stock1 quantity
        qty1 = int(capital_per_leg / stock1_price)

        # Stock2 quantity (hedged using hedge ratio)
        qty2 = int(qty1 * hedge_ratio)

        # Actual capital deployed
        actual_capital = (qty1 * stock1_price) + (qty2 * stock2_price)

        return {
            'stock1_quantity': qty1,
            'stock2_quantity': qty2,
            'capital_deployed': actual_capital,
            'leverage': actual_capital / (capital * max_position_pct)
        }

    def backtest_pair(
        self,
        stock1: str,
        stock2: str,
        price_data: Dict[str, pd.Series],
        initial_capital: float = 1000000
    ) -> Dict:
        """
        Backtest pairs trading strategy

        Returns:
            Performance metrics
        """
        price1 = price_data[stock1]
        price2 = price_data[stock2]

        # Test cointegration
        coint_result = self.test_cointegration(price1, price2)
        if not coint_result['is_cointegrated']:
            return {'error': 'Pair not cointegrated'}

        hedge_ratio = coint_result['hedge_ratio']
        spread = self.calculate_spread(price1, price2, hedge_ratio)

        # Backtesting
        positions = []  # Track open positions
        trades = []
        pnl_history = []
        capital = initial_capital

        for i in range(self.lookback_period, len(spread)):
            # Calculate z-score using rolling window
            spread_window = spread.iloc[i-self.lookback_period:i]
            z_score = (spread.iloc[i] - spread_window.mean()) / spread_window.std()

            # Entry signals
            if not positions:  # No position
                if z_score > self.z_entry:
                    # Short stock1, Long stock2
                    positions.append({
                        'type': 'short_long',
                        'entry_price1': price1.iloc[i],
                        'entry_price2': price2.iloc[i],
                        'entry_date': price1.index[i],
                        'entry_z': z_score
                    })
                elif z_score < -self.z_entry:
                    # Long stock1, Short stock2
                    positions.append({
                        'type': 'long_short',
                        'entry_price1': price1.iloc[i],
                        'entry_price2': price2.iloc[i],
                        'entry_date': price1.index[i],
                        'entry_z': z_score
                    })

            # Exit signals
            elif abs(z_score) < self.z_exit:
                for pos in positions:
                    # Calculate P&L
                    if pos['type'] == 'short_long':
                        pnl1 = (pos['entry_price1'] - price1.iloc[i]) * 100  # Shorted stock1
                        pnl2 = (price2.iloc[i] - pos['entry_price2']) * 100  # Longed stock2
                    else:
                        pnl1 = (price1.iloc[i] - pos['entry_price1']) * 100  # Longed stock1
                        pnl2 = (pos['entry_price2'] - price2.iloc[i]) * 100  # Shorted stock2

                    total_pnl = pnl1 + pnl2
                    capital += total_pnl

                    trades.append({
                        'entry_date': pos['entry_date'],
                        'exit_date': price1.index[i],
                        'entry_z': pos['entry_z'],
                        'exit_z': z_score,
                        'pnl': total_pnl,
                        'return_pct': (total_pnl / initial_capital) * 100
                    })

                positions = []

            pnl_history.append(capital - initial_capital)

        # Calculate metrics
        if not trades:
            return {'error': 'No trades executed'}

        total_return = (capital - initial_capital) / initial_capital * 100
        num_trades = len(trades)
        winning_trades = [t for t in trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / num_trades if num_trades > 0 else 0

        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0

        # Sharpe ratio (assuming 252 trading days, 7% risk-free rate)
        returns = pd.Series(pnl_history).pct_change().dropna()
        sharpe = (returns.mean() * 252 - 0.07) / (returns.std() * np.sqrt(252)) if len(returns) > 0 else 0

        # Max drawdown
        cumulative = pd.Series(pnl_history).cumsum()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / initial_capital * 100
        max_drawdown = drawdown.min()

        return {
            'pair': f"{stock1}-{stock2}",
            'total_return_pct': round(total_return, 2),
            'num_trades': num_trades,
            'win_rate': round(win_rate * 100, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
            'sharpe_ratio': round(sharpe, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'final_capital': round(capital, 2),
            'trades': trades
        }


class MeanReversion:
    """
    Mean Reversion Strategy

    Used by: Renaissance Technologies, D.E. Shaw

    Principle: Prices that deviate from mean tend to revert
    """

    def __init__(self, lookback: int = 20, z_entry: float = 2.0, z_exit: float = 0.5):
        self.lookback = lookback
        self.z_entry = z_entry
        self.z_exit = z_exit

    def calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, num_std: float = 2) -> Dict:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()

        upper_band = sma + (num_std * std)
        lower_band = sma - (num_std * std)

        return {
            'sma': sma,
            'upper': upper_band,
            'lower': lower_band,
            'bandwidth': (upper_band - lower_band) / sma
        }

    def generate_signals(self, symbol: str, prices: pd.Series) -> Dict:
        """Generate mean reversion signals"""
        bb = self.calculate_bollinger_bands(prices, self.lookback)

        current_price = prices.iloc[-1]
        sma = bb['sma'].iloc[-1]
        upper = bb['upper'].iloc[-1]
        lower = bb['lower'].iloc[-1]

        # Calculate position relative to bands
        bb_position = (current_price - lower) / (upper - lower) if (upper - lower) > 0 else 0.5

        # Z-score
        std = (upper - sma) / 2
        z_score = (current_price - sma) / std if std > 0 else 0

        # Generate signal
        if current_price < lower or z_score < -self.z_entry:
            signal = 'buy'
            explanation = f"Price below lower band (z={z_score:.2f}), expect mean reversion up"
        elif current_price > upper or z_score > self.z_entry:
            signal = 'sell'
            explanation = f"Price above upper band (z={z_score:.2f}), expect mean reversion down"
        elif abs(z_score) < self.z_exit:
            signal = 'close'
            explanation = f"Price returned to mean (z={z_score:.2f})"
        else:
            signal = 'hold'
            explanation = f"No action (z={z_score:.2f})"

        return {
            'symbol': symbol,
            'signal': signal,
            'z_score': z_score,
            'bb_position': bb_position,
            'current_price': current_price,
            'sma': sma,
            'upper_band': upper,
            'lower_band': lower,
            'explanation': explanation,
            'timestamp': datetime.now()
        }


class Momentum:
    """
    Momentum Strategy

    Used by: AQR Capital, Winton Group

    Principle: Stocks with strong past performance continue to perform
    """

    def __init__(self, lookback_short: int = 60, lookback_long: int = 252):
        """
        Args:
            lookback_short: Short-term momentum (3 months)
            lookback_long: Long-term momentum (12 months)
        """
        self.lookback_short = lookback_short
        self.lookback_long = lookback_long

    def calculate_momentum_score(self, prices: pd.Series) -> Dict:
        """
        Calculate momentum score using multiple timeframes

        Returns:
            Dict with momentum metrics
        """
        # Returns over different periods
        returns_1m = (prices.iloc[-1] / prices.iloc[-21] - 1) * 100 if len(prices) >= 21 else 0
        returns_3m = (prices.iloc[-1] / prices.iloc[-self.lookback_short] - 1) * 100 if len(prices) >= self.lookback_short else 0
        returns_6m = (prices.iloc[-1] / prices.iloc[-126] - 1) * 100 if len(prices) >= 126 else 0
        returns_12m = (prices.iloc[-1] / prices.iloc[-self.lookback_long] - 1) * 100 if len(prices) >= self.lookback_long else 0

        # Weighted momentum score (more weight to medium-term)
        momentum_score = (
            0.1 * returns_1m +
            0.3 * returns_3m +
            0.4 * returns_6m +
            0.2 * returns_12m
        )

        # Volatility-adjusted momentum (Sharpe-like)
        recent_returns = prices.pct_change().iloc[-60:]
        vol = recent_returns.std() * np.sqrt(252) if len(recent_returns) > 0 else 1
        adj_momentum = momentum_score / (vol * 100) if vol > 0 else 0

        return {
            'momentum_score': momentum_score,
            'adj_momentum': adj_momentum,
            'returns_1m': returns_1m,
            'returns_3m': returns_3m,
            'returns_6m': returns_6m,
            'returns_12m': returns_12m,
            'volatility': vol * 100
        }

    def generate_signals(self, symbol: str, prices: pd.Series, threshold: float = 10.0) -> Dict:
        """
        Generate momentum trading signals

        Args:
            threshold: Momentum score threshold for signal (default 10%)
        """
        momentum = self.calculate_momentum_score(prices)
        score = momentum['momentum_score']

        # Generate signal
        if score > threshold:
            signal = 'buy'
            explanation = f"Strong positive momentum ({score:.1f}%), ride the trend"
        elif score < -threshold:
            signal = 'sell'
            explanation = f"Strong negative momentum ({score:.1f}%), avoid or short"
        else:
            signal = 'hold'
            explanation = f"Weak momentum ({score:.1f}%), no clear direction"

        return {
            'symbol': symbol,
            'signal': signal,
            'momentum_score': score,
            'adj_momentum': momentum['adj_momentum'],
            'returns_12m': momentum['returns_12m'],
            'volatility': momentum['volatility'],
            'explanation': explanation,
            'timestamp': datetime.now()
        }

    def rank_stocks_by_momentum(self, price_data: Dict[str, pd.Series], top_n: int = 20) -> List[Dict]:
        """
        Rank all stocks by momentum score

        Returns:
            List of top N stocks by momentum
        """
        rankings = []

        for symbol, prices in price_data.items():
            if len(prices) < self.lookback_short:
                continue

            momentum = self.calculate_momentum_score(prices)
            rankings.append({
                'symbol': symbol,
                'momentum_score': momentum['momentum_score'],
                'adj_momentum': momentum['adj_momentum'],
                'returns_12m': momentum['returns_12m']
            })

        # Sort by adjusted momentum (risk-adjusted)
        rankings.sort(key=lambda x: x['adj_momentum'], reverse=True)

        return rankings[:top_n]


# Example usage and testing
if __name__ == "__main__":
    # Mock data for testing
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', end='2025-01-01', freq='D')

    # Create correlated mock prices for pairs trading test
    stock1_prices = pd.Series(
        100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, len(dates)))),
        index=dates,
        name='HDFCBANK'
    )

    # Stock 2 correlated with stock 1
    noise = np.random.normal(0, 0.01, len(dates))
    stock2_prices = pd.Series(
        stock1_prices * 0.8 + noise,
        index=dates,
        name='ICICIBANK'
    )

    # Test Pairs Trading
    print("=" * 50)
    print("PAIRS TRADING TEST")
    print("=" * 50)

    pairs = PairsTrading()
    coint_result = pairs.test_cointegration(stock1_prices, stock2_prices)
    print(f"Cointegrated: {coint_result['is_cointegrated']}")
    print(f"P-value: {coint_result['p_value']:.4f}")
    print(f"Hedge Ratio: {coint_result['hedge_ratio']:.4f}")

    # Generate signal
    signal = pairs.generate_signals(
        'HDFCBANK', 'ICICIBANK',
        stock1_prices, stock2_prices,
        coint_result['hedge_ratio']
    )
    print(f"\nSignal: {signal['signal']}")
    print(f"Z-score: {signal['z_score']:.2f}")
    print(f"Explanation: {signal['explanation']}")

    # Test Mean Reversion
    print("\n" + "=" * 50)
    print("MEAN REVERSION TEST")
    print("=" * 50)

    mean_rev = MeanReversion()
    mr_signal = mean_rev.generate_signals('HDFCBANK', stock1_prices)
    print(f"Signal: {mr_signal['signal']}")
    print(f"Z-score: {mr_signal['z_score']:.2f}")
    print(f"Explanation: {mr_signal['explanation']}")

    # Test Momentum
    print("\n" + "=" * 50)
    print("MOMENTUM TEST")
    print("=" * 50)

    momentum = Momentum()
    mom_signal = momentum.generate_signals('HDFCBANK', stock1_prices)
    print(f"Signal: {mom_signal['signal']}")
    print(f"Momentum Score: {mom_signal['momentum_score']:.2f}%")
    print(f"12M Returns: {mom_signal['returns_12m']:.2f}%")
    print(f"Explanation: {mom_signal['explanation']}")
