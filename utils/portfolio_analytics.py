"""
Portfolio Analytics and Management System
Includes performance metrics, risk analysis, and Indian tax calculations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import sqlite3
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Portfolio:
    """
    Portfolio Management and Tracking System
    """

    def __init__(self, portfolio_name: str = 'default',
                 database_path: str = 'data/portfolio.db'):
        """
        Initialize Portfolio

        Args:
            portfolio_name: Portfolio identifier
            database_path: Path to SQLite database
        """
        self.portfolio_name = portfolio_name
        self.database_path = database_path
        self.ensure_database_directory()
        self.init_database()

    def ensure_database_directory(self):
        """Ensure database directory exists"""
        db_dir = Path(self.database_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def init_database(self):
        """Initialize portfolio database"""
        with sqlite3.connect(self.database_path) as conn:
            # Holdings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS holdings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    avg_buy_price REAL NOT NULL,
                    current_price REAL,
                    sector TEXT,
                    purchase_date TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(portfolio_name, symbol)
                )
            """)

            # Transactions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    transaction_date TEXT NOT NULL,
                    charges REAL DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Portfolio snapshots for historical tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_name TEXT NOT NULL,
                    snapshot_date TEXT NOT NULL,
                    total_value REAL NOT NULL,
                    invested_amount REAL NOT NULL,
                    realized_pnl REAL DEFAULT 0,
                    unrealized_pnl REAL DEFAULT 0,
                    holdings_json TEXT,
                    UNIQUE(portfolio_name, snapshot_date)
                )
            """)

            # Benchmarks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    benchmark_name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    close_price REAL NOT NULL,
                    UNIQUE(benchmark_name, date)
                )
            """)

            conn.commit()

    def add_transaction(self, symbol: str, transaction_type: str,
                       quantity: float, price: float, transaction_date: str = None,
                       charges: float = 0, notes: str = None):
        """
        Add a buy/sell transaction

        Args:
            symbol: Stock symbol
            transaction_type: 'BUY' or 'SELL'
            quantity: Number of shares
            price: Price per share
            transaction_date: Transaction date (default: today)
            charges: Brokerage and other charges
            notes: Additional notes
        """
        if transaction_date is None:
            transaction_date = datetime.now().strftime('%Y-%m-%d')

        transaction_type = transaction_type.upper()

        with sqlite3.connect(self.database_path) as conn:
            # Add transaction
            conn.execute("""
                INSERT INTO transactions
                (portfolio_name, symbol, transaction_type, quantity, price,
                 transaction_date, charges, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.portfolio_name, symbol, transaction_type, quantity,
                  price, transaction_date, charges, notes))

            # Update holdings
            if transaction_type == 'BUY':
                self._update_holdings_buy(conn, symbol, quantity, price, transaction_date)
            elif transaction_type == 'SELL':
                self._update_holdings_sell(conn, symbol, quantity, price)

            conn.commit()

        logger.info(f"Transaction added: {transaction_type} {quantity} {symbol} @ {price}")

    def _update_holdings_buy(self, conn, symbol: str, quantity: float,
                            price: float, purchase_date: str):
        """Update holdings for buy transaction"""
        # Get current holding
        cursor = conn.execute("""
            SELECT quantity, avg_buy_price FROM holdings
            WHERE portfolio_name = ? AND symbol = ?
        """, (self.portfolio_name, symbol))

        row = cursor.fetchone()

        if row:
            # Update existing holding
            current_qty, current_avg = row
            new_qty = current_qty + quantity
            new_avg = ((current_qty * current_avg) + (quantity * price)) / new_qty

            conn.execute("""
                UPDATE holdings
                SET quantity = ?, avg_buy_price = ?, last_updated = CURRENT_TIMESTAMP
                WHERE portfolio_name = ? AND symbol = ?
            """, (new_qty, new_avg, self.portfolio_name, symbol))
        else:
            # Add new holding
            conn.execute("""
                INSERT INTO holdings
                (portfolio_name, symbol, quantity, avg_buy_price, purchase_date)
                VALUES (?, ?, ?, ?, ?)
            """, (self.portfolio_name, symbol, quantity, price, purchase_date))

    def _update_holdings_sell(self, conn, symbol: str, quantity: float, price: float):
        """Update holdings for sell transaction"""
        cursor = conn.execute("""
            SELECT quantity FROM holdings
            WHERE portfolio_name = ? AND symbol = ?
        """, (self.portfolio_name, symbol))

        row = cursor.fetchone()

        if not row:
            logger.error(f"Cannot sell {symbol}: Not in holdings")
            return

        current_qty = row[0]

        if current_qty < quantity:
            logger.error(f"Cannot sell {quantity} {symbol}: Only {current_qty} available")
            return

        new_qty = current_qty - quantity

        if new_qty == 0:
            # Remove from holdings
            conn.execute("""
                DELETE FROM holdings
                WHERE portfolio_name = ? AND symbol = ?
            """, (self.portfolio_name, symbol))
        else:
            # Update quantity
            conn.execute("""
                UPDATE holdings
                SET quantity = ?, last_updated = CURRENT_TIMESTAMP
                WHERE portfolio_name = ? AND symbol = ?
            """, (new_qty, self.portfolio_name, symbol))

    def get_holdings(self) -> pd.DataFrame:
        """
        Get current holdings

        Returns:
            DataFrame with holdings
        """
        with sqlite3.connect(self.database_path) as conn:
            df = pd.read_sql_query("""
                SELECT * FROM holdings
                WHERE portfolio_name = ?
                ORDER BY symbol
            """, conn, params=(self.portfolio_name,))

        return df

    def update_current_prices(self, prices: Dict[str, float]):
        """
        Update current prices for holdings

        Args:
            prices: Dictionary mapping symbol to current price
        """
        with sqlite3.connect(self.database_path) as conn:
            for symbol, price in prices.items():
                conn.execute("""
                    UPDATE holdings
                    SET current_price = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE portfolio_name = ? AND symbol = ?
                """, (price, self.portfolio_name, symbol))
            conn.commit()

    def get_portfolio_summary(self) -> Dict:
        """
        Get portfolio summary with P&L

        Returns:
            Dictionary with portfolio metrics
        """
        holdings = self.get_holdings()

        if holdings.empty:
            return {
                'total_invested': 0,
                'current_value': 0,
                'unrealized_pnl': 0,
                'unrealized_pnl_percent': 0,
                'num_stocks': 0
            }

        total_invested = (holdings['quantity'] * holdings['avg_buy_price']).sum()
        current_value = (holdings['quantity'] * holdings['current_price'].fillna(holdings['avg_buy_price'])).sum()
        unrealized_pnl = current_value - total_invested
        unrealized_pnl_percent = (unrealized_pnl / total_invested) * 100 if total_invested > 0 else 0

        return {
            'total_invested': total_invested,
            'current_value': current_value,
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pnl_percent': unrealized_pnl_percent,
            'num_stocks': len(holdings),
            'holdings': holdings
        }

    def get_sector_allocation(self) -> pd.DataFrame:
        """
        Get sector-wise allocation

        Returns:
            DataFrame with sector allocation
        """
        holdings = self.get_holdings()

        if holdings.empty:
            return pd.DataFrame()

        holdings['value'] = holdings['quantity'] * holdings['current_price'].fillna(holdings['avg_buy_price'])
        sector_allocation = holdings.groupby('sector')['value'].sum().reset_index()
        sector_allocation['allocation_percent'] = (sector_allocation['value'] / sector_allocation['value'].sum()) * 100

        return sector_allocation.sort_values('allocation_percent', ascending=False)

    def save_snapshot(self):
        """Save current portfolio snapshot for historical tracking"""
        summary = self.get_portfolio_summary()
        holdings = summary['holdings']

        holdings_json = holdings.to_json(orient='records') if not holdings.empty else '[]'

        with sqlite3.connect(self.database_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO portfolio_snapshots
                (portfolio_name, snapshot_date, total_value, invested_amount,
                 unrealized_pnl, holdings_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.portfolio_name, datetime.now().strftime('%Y-%m-%d'),
                  summary['current_value'], summary['total_invested'],
                  summary['unrealized_pnl'], holdings_json))
            conn.commit()


class PerformanceMetrics:
    """
    Portfolio Performance Metrics Calculator
    """

    @staticmethod
    def calculate_returns(prices: pd.Series) -> pd.Series:
        """Calculate daily returns"""
        return prices.pct_change().dropna()

    @staticmethod
    def calculate_cumulative_returns(prices: pd.Series) -> pd.Series:
        """Calculate cumulative returns"""
        returns = PerformanceMetrics.calculate_returns(prices)
        return (1 + returns).cumprod() - 1

    @staticmethod
    def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.065,
                    periods_per_year: int = 252) -> float:
        """
        Calculate Sharpe Ratio

        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate (default 6.5%)
            periods_per_year: Trading days per year

        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return np.nan

        excess_returns = returns - (risk_free_rate / periods_per_year)
        sharpe = np.sqrt(periods_per_year) * excess_returns.mean() / excess_returns.std()
        return sharpe

    @staticmethod
    def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.065,
                     periods_per_year: int = 252) -> float:
        """
        Calculate Sortino Ratio (uses downside deviation)

        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate
            periods_per_year: Trading days per year

        Returns:
            Sortino ratio
        """
        if len(returns) < 2:
            return np.nan

        excess_returns = returns - (risk_free_rate / periods_per_year)
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0:
            return np.nan

        downside_std = downside_returns.std()
        sortino = np.sqrt(periods_per_year) * excess_returns.mean() / downside_std
        return sortino

    @staticmethod
    def calmar_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
        """
        Calculate Calmar Ratio (return / max drawdown)

        Args:
            returns: Series of returns
            periods_per_year: Trading days per year

        Returns:
            Calmar ratio
        """
        if len(returns) < 2:
            return np.nan

        cumulative = (1 + returns).cumprod()
        max_dd = PerformanceMetrics.max_drawdown(returns)

        if max_dd == 0:
            return np.nan

        annual_return = (cumulative.iloc[-1] ** (periods_per_year / len(returns))) - 1
        calmar = annual_return / abs(max_dd)
        return calmar

    @staticmethod
    def max_drawdown(returns: pd.Series) -> float:
        """
        Calculate Maximum Drawdown

        Args:
            returns: Series of returns

        Returns:
            Maximum drawdown (negative value)
        """
        if len(returns) < 2:
            return 0

        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    @staticmethod
    def beta(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        Calculate Beta relative to benchmark

        Args:
            returns: Portfolio returns
            benchmark_returns: Benchmark returns

        Returns:
            Beta coefficient
        """
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return np.nan

        covariance = np.cov(returns, benchmark_returns)[0][1]
        benchmark_variance = np.var(benchmark_returns)

        if benchmark_variance == 0:
            return np.nan

        return covariance / benchmark_variance

    @staticmethod
    def alpha(returns: pd.Series, benchmark_returns: pd.Series,
             risk_free_rate: float = 0.065, periods_per_year: int = 252) -> float:
        """
        Calculate Jensen's Alpha

        Args:
            returns: Portfolio returns
            benchmark_returns: Benchmark returns
            risk_free_rate: Annual risk-free rate
            periods_per_year: Trading days per year

        Returns:
            Alpha
        """
        portfolio_return = returns.mean() * periods_per_year
        benchmark_return = benchmark_returns.mean() * periods_per_year
        beta_value = PerformanceMetrics.beta(returns, benchmark_returns)

        alpha_value = portfolio_return - (risk_free_rate + beta_value * (benchmark_return - risk_free_rate))
        return alpha_value

    @staticmethod
    def information_ratio(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        Calculate Information Ratio

        Args:
            returns: Portfolio returns
            benchmark_returns: Benchmark returns

        Returns:
            Information ratio
        """
        if len(returns) != len(benchmark_returns):
            return np.nan

        active_returns = returns - benchmark_returns
        tracking_error = active_returns.std()

        if tracking_error == 0:
            return np.nan

        return active_returns.mean() / tracking_error * np.sqrt(252)

    @staticmethod
    def volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
        """
        Calculate annualized volatility

        Args:
            returns: Series of returns
            periods_per_year: Trading days per year

        Returns:
            Annualized volatility
        """
        return returns.std() * np.sqrt(periods_per_year)


class IndianTaxCalculator:
    """
    Indian Capital Gains Tax Calculator
    As per Income Tax Act, 1961
    """

    # Tax rates (as of 2024-25)
    LTCG_RATE = 0.10  # 10% on gains above ₹1 lakh
    LTCG_EXEMPTION = 100000  # ₹1 lakh exemption
    STCG_RATE = 0.15  # 15% on short-term gains

    # Holding period for equity
    LONG_TERM_PERIOD_DAYS = 365  # 1 year for equity

    @staticmethod
    def calculate_capital_gains(buy_price: float, sell_price: float,
                               quantity: float, holding_days: int,
                               charges: float = 0) -> Dict:
        """
        Calculate capital gains and tax

        Args:
            buy_price: Purchase price per share
            sell_price: Selling price per share
            quantity: Number of shares
            holding_days: Number of days held
            charges: Transaction charges (brokerage, STT, etc.)

        Returns:
            Dictionary with tax details
        """
        cost_of_acquisition = buy_price * quantity
        sale_consideration = sell_price * quantity
        capital_gain = sale_consideration - cost_of_acquisition - charges

        is_long_term = holding_days >= IndianTaxCalculator.LONG_TERM_PERIOD_DAYS

        if is_long_term:
            # LTCG calculation
            taxable_gain = max(capital_gain - IndianTaxCalculator.LTCG_EXEMPTION, 0)
            tax = taxable_gain * IndianTaxCalculator.LTCG_RATE
            gain_type = 'LTCG'
        else:
            # STCG calculation
            taxable_gain = capital_gain
            tax = max(taxable_gain * IndianTaxCalculator.STCG_RATE, 0)
            gain_type = 'STCG'

        return {
            'gain_type': gain_type,
            'capital_gain': capital_gain,
            'taxable_gain': taxable_gain,
            'tax_amount': tax,
            'net_gain': capital_gain - tax,
            'holding_days': holding_days,
            'is_long_term': is_long_term
        }

    @staticmethod
    def calculate_portfolio_tax(transactions: pd.DataFrame) -> Dict:
        """
        Calculate total tax liability from transaction history

        Args:
            transactions: DataFrame with buy/sell transactions

        Returns:
            Tax summary
        """
        # Match buy and sell transactions (FIFO method)
        total_stcg = 0
        total_ltcg = 0
        total_stcg_tax = 0
        total_ltcg_tax = 0

        # Group by symbol
        for symbol in transactions['symbol'].unique():
            symbol_txns = transactions[transactions['symbol'] == symbol].sort_values('transaction_date')

            buys = symbol_txns[symbol_txns['transaction_type'] == 'BUY'].copy()
            sells = symbol_txns[symbol_txns['transaction_type'] == 'SELL'].copy()

            for _, sell in sells.iterrows():
                remaining_qty = sell['quantity']
                sell_date = pd.to_datetime(sell['transaction_date'])

                for idx, buy in buys.iterrows():
                    if remaining_qty == 0:
                        break

                    if buy['quantity'] == 0:
                        continue

                    matched_qty = min(remaining_qty, buy['quantity'])
                    buy_date = pd.to_datetime(buy['transaction_date'])
                    holding_days = (sell_date - buy_date).days

                    tax_info = IndianTaxCalculator.calculate_capital_gains(
                        buy['price'], sell['price'], matched_qty, holding_days
                    )

                    if tax_info['is_long_term']:
                        total_ltcg += tax_info['capital_gain']
                        total_ltcg_tax += tax_info['tax_amount']
                    else:
                        total_stcg += tax_info['capital_gain']
                        total_stcg_tax += tax_info['tax_amount']

                    buys.at[idx, 'quantity'] -= matched_qty
                    remaining_qty -= matched_qty

        return {
            'total_stcg': total_stcg,
            'total_ltcg': total_ltcg,
            'stcg_tax': total_stcg_tax,
            'ltcg_tax': total_ltcg_tax,
            'total_tax': total_stcg_tax + total_ltcg_tax,
            'total_gains': total_stcg + total_ltcg,
            'net_gains': total_stcg + total_ltcg - total_stcg_tax - total_ltcg_tax
        }


if __name__ == "__main__":
    # Example usage
    portfolio = Portfolio('my_portfolio')

    # Add some transactions
    portfolio.add_transaction('RELIANCE', 'BUY', 10, 2500, '2024-01-15')
    portfolio.add_transaction('TCS', 'BUY', 5, 3800, '2024-02-20')

    # Update current prices
    portfolio.update_current_prices({
        'RELIANCE': 2650,
        'TCS': 3900
    })

    # Get summary
    summary = portfolio.get_portfolio_summary()
    print(f"Portfolio Value: ₹{summary['current_value']:.2f}")
    print(f"Unrealized P&L: ₹{summary['unrealized_pnl']:.2f} ({summary['unrealized_pnl_percent']:.2f}%)")

    # Calculate Sharpe ratio
    returns = pd.Series([0.01, -0.005, 0.02, 0.015, -0.01])
    sharpe = PerformanceMetrics.sharpe_ratio(returns)
    print(f"\nSharpe Ratio: {sharpe:.4f}")
