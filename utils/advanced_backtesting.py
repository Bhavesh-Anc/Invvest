"""
Advanced Backtesting Engine
Institutional-grade backtesting with realistic transaction costs, slippage, and market impact
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSide(Enum):
    """Order sides"""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Order:
    """Order representation"""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    timestamp: Optional[datetime] = None
    filled_price: Optional[float] = None
    filled_quantity: float = 0
    status: str = "PENDING"  # PENDING, FILLED, PARTIAL, CANCELLED


@dataclass
class Position:
    """Position representation"""
    symbol: str
    quantity: float
    avg_entry_price: float
    unrealized_pnl: float = 0
    realized_pnl: float = 0


class TransactionCostModel:
    """
    Model transaction costs for Indian stock market
    """

    def __init__(self,
                 brokerage_rate: float = 0.0003,  # 0.03% typical for algo trading
                 stt_rate: float = 0.00025,  # STT: 0.025% on sell side
                 exchange_txn_charge: float = 0.0000325,  # NSE: 0.00325%
                 sebi_charges: float = 0.0000001,  # SEBI: 0.00001%
                 gst_rate: float = 0.18,  # 18% GST on brokerage
                 stamp_duty: float = 0.00015):  # 0.015% on buy side
        """
        Args:
            brokerage_rate: Brokerage as fraction of trade value
            stt_rate: Securities Transaction Tax
            exchange_txn_charge: Exchange transaction charges
            sebi_charges: SEBI turnover charges
            gst_rate: GST on brokerage
            stamp_duty: Stamp duty
        """
        self.brokerage_rate = brokerage_rate
        self.stt_rate = stt_rate
        self.exchange_txn_charge = exchange_txn_charge
        self.sebi_charges = sebi_charges
        self.gst_rate = gst_rate
        self.stamp_duty = stamp_duty

    def calculate_cost(self, trade_value: float, side: OrderSide) -> float:
        """
        Calculate total transaction cost

        Args:
            trade_value: Value of trade (price * quantity)
            side: BUY or SELL

        Returns:
            Total cost
        """
        # Brokerage
        brokerage = trade_value * self.brokerage_rate

        # GST on brokerage
        gst = brokerage * self.gst_rate

        # Exchange charges
        exchange_charges = trade_value * self.exchange_txn_charge

        # SEBI charges
        sebi = trade_value * self.sebi_charges

        total_cost = brokerage + gst + exchange_charges + sebi

        if side == OrderSide.SELL:
            # STT on sell
            total_cost += trade_value * self.stt_rate
        else:
            # Stamp duty on buy
            total_cost += trade_value * self.stamp_duty

        return total_cost


class SlippageModel:
    """
    Model price slippage based on order size and market conditions
    """

    def __init__(self,
                 fixed_slippage: float = 0.0001,  # 1 basis point
                 volume_impact_coef: float = 0.1):
        """
        Args:
            fixed_slippage: Fixed slippage as fraction
            volume_impact_coef: Coefficient for volume impact
        """
        self.fixed_slippage = fixed_slippage
        self.volume_impact_coef = volume_impact_coef

    def calculate_slippage(self, order_size: float, avg_volume: float,
                          price: float, side: OrderSide) -> float:
        """
        Calculate slippage

        Args:
            order_size: Size of order
            avg_volume: Average trading volume
            price: Current price
            side: BUY or SELL

        Returns:
            Slippage amount (absolute)
        """
        # Fixed component
        fixed_component = price * self.fixed_slippage

        # Market impact based on order size relative to volume
        if avg_volume > 0:
            participation_rate = order_size / avg_volume
            market_impact = price * participation_rate * self.volume_impact_coef
        else:
            market_impact = 0

        total_slippage = fixed_component + market_impact

        # Slippage direction
        if side == OrderSide.BUY:
            return total_slippage  # Pay more
        else:
            return -total_slippage  # Receive less


class AdvancedBacktester:
    """
    Institutional-grade backtesting engine
    """

    def __init__(self,
                 initial_capital: float = 10000000,  # ₹1 Crore
                 transaction_cost_model: TransactionCostModel = None,
                 slippage_model: SlippageModel = None,
                 margin_requirement: float = 0.2):  # 20% for intraday
        """
        Args:
            initial_capital: Starting capital
            transaction_cost_model: Transaction cost model
            slippage_model: Slippage model
            margin_requirement: Margin requirement as fraction
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.portfolio_value = initial_capital

        self.transaction_cost_model = transaction_cost_model or TransactionCostModel()
        self.slippage_model = slippage_model or SlippageModel()
        self.margin_requirement = margin_requirement

        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.trades: List[Dict] = []
        self.equity_curve: List[Dict] = []

        self.total_transaction_costs = 0
        self.total_slippage = 0

    def place_order(self, order: Order):
        """Place an order"""
        self.orders.append(order)

    def execute_orders(self, current_prices: Dict[str, float],
                      current_volumes: Dict[str, float],
                      timestamp: datetime):
        """
        Execute pending orders

        Args:
            current_prices: Current market prices
            current_volumes: Current trading volumes
            timestamp: Current timestamp
        """
        for order in self.orders:
            if order.status == "PENDING" and order.symbol in current_prices:
                execution_price = current_prices[order.symbol]

                # Apply slippage
                avg_volume = current_volumes.get(order.symbol, 1000000)
                slippage = self.slippage_model.calculate_slippage(
                    order.quantity, avg_volume, execution_price, order.side
                )
                execution_price += slippage

                # Calculate trade value
                trade_value = execution_price * order.quantity

                # Calculate transaction costs
                transaction_cost = self.transaction_cost_model.calculate_cost(
                    trade_value, order.side
                )

                # Check if we have enough cash
                if order.side == OrderSide.BUY:
                    total_cost = trade_value + transaction_cost

                    if total_cost <= self.cash:
                        # Execute buy
                        self._execute_buy(order, execution_price, transaction_cost, timestamp)
                        order.status = "FILLED"
                    else:
                        order.status = "CANCELLED"
                        logger.warning(f"Insufficient cash for order: {order}")

                else:  # SELL
                    # Check if we have the position
                    if order.symbol in self.positions:
                        position = self.positions[order.symbol]

                        if position.quantity >= order.quantity:
                            # Execute sell
                            self._execute_sell(order, execution_price, transaction_cost, timestamp)
                            order.status = "FILLED"
                        else:
                            order.status = "CANCELLED"
                            logger.warning(f"Insufficient position for sell order: {order}")
                    else:
                        order.status = "CANCELLED"

        # Remove filled/cancelled orders
        self.orders = [o for o in self.orders if o.status == "PENDING"]

    def _execute_buy(self, order: Order, execution_price: float,
                    transaction_cost: float, timestamp: datetime):
        """Execute buy order"""
        trade_value = execution_price * order.quantity
        total_cost = trade_value + transaction_cost

        # Update cash
        self.cash -= total_cost

        # Update position
        if order.symbol in self.positions:
            position = self.positions[order.symbol]
            new_quantity = position.quantity + order.quantity
            new_avg_price = ((position.avg_entry_price * position.quantity) +
                            (execution_price * order.quantity)) / new_quantity

            position.quantity = new_quantity
            position.avg_entry_price = new_avg_price
        else:
            self.positions[order.symbol] = Position(
                symbol=order.symbol,
                quantity=order.quantity,
                avg_entry_price=execution_price
            )

        # Record trade
        self.trades.append({
            'timestamp': timestamp,
            'symbol': order.symbol,
            'side': 'BUY',
            'quantity': order.quantity,
            'price': execution_price,
            'transaction_cost': transaction_cost,
            'cash_after': self.cash
        })

        self.total_transaction_costs += transaction_cost

    def _execute_sell(self, order: Order, execution_price: float,
                     transaction_cost: float, timestamp: datetime):
        """Execute sell order"""
        trade_value = execution_price * order.quantity
        proceeds = trade_value - transaction_cost

        # Update cash
        self.cash += proceeds

        # Calculate realized P&L
        position = self.positions[order.symbol]
        realized_pnl = (execution_price - position.avg_entry_price) * order.quantity - transaction_cost

        position.realized_pnl += realized_pnl
        position.quantity -= order.quantity

        # Remove position if fully closed
        if position.quantity == 0:
            del self.positions[order.symbol]

        # Record trade
        self.trades.append({
            'timestamp': timestamp,
            'symbol': order.symbol,
            'side': 'SELL',
            'quantity': order.quantity,
            'price': execution_price,
            'transaction_cost': transaction_cost,
            'realized_pnl': realized_pnl,
            'cash_after': self.cash
        })

        self.total_transaction_costs += transaction_cost

    def update_portfolio_value(self, current_prices: Dict[str, float],
                              timestamp: datetime):
        """
        Update portfolio value and equity curve

        Args:
            current_prices: Current market prices
            timestamp: Current timestamp
        """
        # Calculate unrealized P&L
        holdings_value = 0

        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                market_value = current_price * position.quantity
                unrealized_pnl = (current_price - position.avg_entry_price) * position.quantity

                position.unrealized_pnl = unrealized_pnl
                holdings_value += market_value

        self.portfolio_value = self.cash + holdings_value

        # Record equity curve
        self.equity_curve.append({
            'timestamp': timestamp,
            'portfolio_value': self.portfolio_value,
            'cash': self.cash,
            'holdings_value': holdings_value
        })

    def run_backtest(self, price_data: pd.DataFrame,
                    strategy: Callable,
                    volume_data: pd.DataFrame = None) -> Dict:
        """
        Run backtest with a strategy

        Args:
            price_data: DataFrame with columns = symbols, index = timestamps
            strategy: Strategy function(prices, positions) -> list of orders
            volume_data: DataFrame with volume data (optional)

        Returns:
            Backtest results
        """
        if volume_data is None:
            # Use default volumes
            volume_data = pd.DataFrame(
                1000000,
                index=price_data.index,
                columns=price_data.columns
            )

        for timestamp in price_data.index:
            current_prices = price_data.loc[timestamp].to_dict()
            current_volumes = volume_data.loc[timestamp].to_dict()

            # Update portfolio value
            self.update_portfolio_value(current_prices, timestamp)

            # Generate orders from strategy
            new_orders = strategy(price_data.loc[:timestamp], self.positions, self.cash)

            # Place orders
            for order in new_orders:
                order.timestamp = timestamp
                self.place_order(order)

            # Execute orders
            self.execute_orders(current_prices, current_volumes, timestamp)

        # Calculate final metrics
        results = self.calculate_performance_metrics()
        return results

    def calculate_performance_metrics(self) -> Dict:
        """
        Calculate comprehensive performance metrics

        Returns:
            Performance metrics dictionary
        """
        equity_curve_df = pd.DataFrame(self.equity_curve)

        if len(equity_curve_df) == 0:
            return {'error': 'No data in equity curve'}

        # Returns
        total_return = (self.portfolio_value - self.initial_capital) / self.initial_capital

        # Daily returns
        equity_curve_df['returns'] = equity_curve_df['portfolio_value'].pct_change()
        daily_returns = equity_curve_df['returns'].dropna()

        # Sharpe ratio
        sharpe_ratio = np.sqrt(252) * daily_returns.mean() / (daily_returns.std() + 1e-6)

        # Sortino ratio (downside deviation)
        downside_returns = daily_returns[daily_returns < 0]
        sortino_ratio = np.sqrt(252) * daily_returns.mean() / (downside_returns.std() + 1e-6)

        # Maximum drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Calmar ratio
        calmar_ratio = (total_return * 252 / len(daily_returns)) / abs(max_drawdown) if max_drawdown != 0 else 0

        # Win rate
        winning_trades = [t for t in self.trades if t.get('realized_pnl', 0) > 0]
        win_rate = len(winning_trades) / len([t for t in self.trades if 'realized_pnl' in t]) if len(self.trades) > 0 else 0

        # Transaction cost impact
        transaction_cost_pct = self.total_transaction_costs / self.initial_capital

        return {
            'initial_capital': self.initial_capital,
            'final_portfolio_value': self.portfolio_value,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown * 100,
            'calmar_ratio': calmar_ratio,
            'num_trades': len(self.trades),
            'win_rate': win_rate,
            'win_rate_pct': win_rate * 100,
            'total_transaction_costs': self.total_transaction_costs,
            'transaction_cost_pct': transaction_cost_pct * 100,
            'trades': self.trades,
            'equity_curve': equity_curve_df
        }


# Example strategy
def simple_momentum_strategy(price_data: pd.DataFrame,
                            positions: Dict[str, Position],
                            cash: float) -> List[Order]:
    """
    Simple momentum strategy for demonstration

    Args:
        price_data: Historical price data up to current time
        positions: Current positions
        cash: Available cash

    Returns:
        List of orders
    """
    orders = []

    if len(price_data) < 20:
        return orders

    # Calculate 20-day momentum
    recent_prices = price_data.iloc[-20:]
    momentum = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]

    # Buy top performer if not already holding
    top_stock = momentum.idxmax()
    if top_stock not in positions and momentum[top_stock] > 0.05:  # 5% momentum threshold
        # Allocate 10% of capital
        allocation = cash * 0.1
        price = price_data[top_stock].iloc[-1]
        quantity = int(allocation / price)

        if quantity > 0:
            orders.append(Order(
                symbol=top_stock,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=quantity
            ))

    # Sell if momentum reverses
    for symbol, position in positions.items():
        if momentum[symbol] < -0.03:  # -3% momentum
            orders.append(Order(
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=position.quantity
            ))

    return orders


if __name__ == "__main__":
    logger.info("Advanced Backtesting Engine - Institutional Grade")

    # Example: Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICI']

    # Simulate price data
    price_data = pd.DataFrame(
        100 + np.cumsum(np.random.randn(len(dates), len(symbols)) * 2, axis=0),
        index=dates,
        columns=symbols
    )

    # Run backtest
    backtester = AdvancedBacktester(initial_capital=10000000)
    results = backtester.run_backtest(price_data, simple_momentum_strategy)

    print("\n=== Backtest Results ===")
    print(f"Initial Capital: ₹{results['initial_capital']:,.0f}")
    print(f"Final Value: ₹{results['final_portfolio_value']:,.0f}")
    print(f"Total Return: {results['total_return_pct']:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown_pct']:.2f}%")
    print(f"Number of Trades: {results['num_trades']}")
    print(f"Win Rate: {results['win_rate_pct']:.2f}%")
    print(f"Transaction Costs: ₹{results['total_transaction_costs']:,.0f} ({results['transaction_cost_pct']:.2f}%)")
