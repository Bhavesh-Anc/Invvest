"""
Advanced Execution Engine & Smart Order Routing
TWAP, VWAP, POV, Iceberg Orders, and Smart Routing
Institutional-grade execution algorithms
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    ICEBERG = "ICEBERG"


class OrderSide(Enum):
    """Order sides"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    """Order representation"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "DAY"  # DAY, GTC, IOC, FOK
    timestamp: Optional[datetime] = None
    filled_quantity: float = 0
    avg_fill_price: float = 0
    status: OrderStatus = OrderStatus.PENDING
    parent_algo: Optional[str] = None  # TWAP, VWAP, POV, etc.


class ExecutionAlgorithm(ABC):
    """
    Base class for execution algorithms
    """

    def __init__(self, order: Order, execution_time_minutes: int = 60):
        """
        Args:
            order: Parent order to execute
            execution_time_minutes: Time window for execution
        """
        self.order = order
        self.execution_time_minutes = execution_time_minutes
        self.child_orders: List[Order] = []
        self.execution_start_time = None
        self.execution_end_time = None

    @abstractmethod
    def generate_schedule(self) -> List[Dict]:
        """
        Generate execution schedule (child orders)

        Returns:
            List of scheduled trades with timing
        """
        pass

    @abstractmethod
    def get_slice_size(self, time_slice: int, market_data: Dict) -> float:
        """
        Calculate slice size for current time interval

        Args:
            time_slice: Current time slice
            market_data: Current market data

        Returns:
            Quantity to execute in this slice
        """
        pass


class TWAPExecutor(ExecutionAlgorithm):
    """
    Time-Weighted Average Price (TWAP)
    Splits order evenly across time
    """

    def __init__(self, order: Order, execution_time_minutes: int = 60,
                 num_slices: int = 10):
        """
        Args:
            order: Parent order
            execution_time_minutes: Execution window
            num_slices: Number of time slices
        """
        super().__init__(order, execution_time_minutes)
        self.num_slices = num_slices
        self.slice_duration = execution_time_minutes / num_slices

    def generate_schedule(self) -> List[Dict]:
        """Generate TWAP schedule"""
        schedule = []
        slice_size = self.order.quantity / self.num_slices

        for i in range(self.num_slices):
            execution_time = datetime.now() + timedelta(minutes=i * self.slice_duration)

            schedule.append({
                'slice_number': i + 1,
                'execution_time': execution_time,
                'quantity': slice_size,
                'algorithm': 'TWAP',
                'order_type': OrderType.MARKET
            })

        return schedule

    def get_slice_size(self, time_slice: int, market_data: Dict) -> float:
        """Get slice size for TWAP (constant)"""
        return self.order.quantity / self.num_slices


class VWAPExecutor(ExecutionAlgorithm):
    """
    Volume-Weighted Average Price (VWAP)
    Splits order proportional to expected volume profile
    """

    def __init__(self, order: Order, execution_time_minutes: int = 60,
                 volume_profile: Optional[List[float]] = None):
        """
        Args:
            order: Parent order
            execution_time_minutes: Execution window
            volume_profile: Historical volume profile (if None, use default)
        """
        super().__init__(order, execution_time_minutes)
        self.volume_profile = volume_profile or self._default_volume_profile()

    def _default_volume_profile(self) -> List[float]:
        """
        Default intraday volume profile for Indian market
        U-shaped with peaks at open and close
        """
        # Simplified U-shape: higher volume at start and end of day
        hours = np.linspace(0, 1, 24)
        profile = 0.5 * (1 - np.cos(2 * np.pi * hours)) + 0.3

        # Normalize
        profile = profile / profile.sum()

        return profile.tolist()

    def generate_schedule(self) -> List[Dict]:
        """Generate VWAP schedule based on volume profile"""
        schedule = []
        num_slices = len(self.volume_profile)

        for i, volume_weight in enumerate(self.volume_profile):
            slice_size = self.order.quantity * volume_weight
            execution_time = datetime.now() + timedelta(minutes=i * (self.execution_time_minutes / num_slices))

            schedule.append({
                'slice_number': i + 1,
                'execution_time': execution_time,
                'quantity': slice_size,
                'volume_weight': volume_weight,
                'algorithm': 'VWAP',
                'order_type': OrderType.MARKET
            })

        return schedule

    def get_slice_size(self, time_slice: int, market_data: Dict) -> float:
        """Get slice size for VWAP (volume-weighted)"""
        if time_slice < len(self.volume_profile):
            return self.order.quantity * self.volume_profile[time_slice]
        return 0


class POVExecutor(ExecutionAlgorithm):
    """
    Percentage of Volume (POV) / Participation Rate
    Execute as percentage of market volume
    """

    def __init__(self, order: Order, execution_time_minutes: int = 60,
                 participation_rate: float = 0.10):
        """
        Args:
            order: Parent order
            execution_time_minutes: Execution window
            participation_rate: Target participation rate (e.g., 10% of market volume)
        """
        super().__init__(order, execution_time_minutes)
        self.participation_rate = participation_rate
        self.executed_quantity = 0

    def generate_schedule(self) -> List[Dict]:
        """
        Generate POV schedule
        Note: Actual execution is adaptive based on real-time volume
        """
        schedule = []

        # POV is adaptive, but we generate initial schedule
        num_slices = 20  # Check every 3 minutes for 60-minute execution
        slice_duration = self.execution_time_minutes / num_slices

        for i in range(num_slices):
            execution_time = datetime.now() + timedelta(minutes=i * slice_duration)

            schedule.append({
                'slice_number': i + 1,
                'execution_time': execution_time,
                'quantity': 'ADAPTIVE',  # Will be determined based on market volume
                'participation_rate': self.participation_rate,
                'algorithm': 'POV',
                'order_type': OrderType.MARKET
            })

        return schedule

    def get_slice_size(self, time_slice: int, market_data: Dict) -> float:
        """
        Get slice size for POV (adaptive based on market volume)

        Args:
            time_slice: Current slice
            market_data: Must include 'volume' key

        Returns:
            Quantity to execute
        """
        market_volume = market_data.get('volume', 0)

        # Execute as percentage of market volume
        target_quantity = market_volume * self.participation_rate

        # Don't exceed remaining quantity
        remaining = self.order.quantity - self.executed_quantity
        return min(target_quantity, remaining)


class IcebergOrderExecutor(ExecutionAlgorithm):
    """
    Iceberg Order Execution
    Shows only small portion of total order (tip of iceberg)
    """

    def __init__(self, order: Order, visible_quantity: float,
                 replenish_threshold: float = 0.2):
        """
        Args:
            order: Parent order
            visible_quantity: Quantity visible in order book
            replenish_threshold: When to replenish (as fraction of visible qty)
        """
        super().__init__(order)
        self.visible_quantity = visible_quantity
        self.replenish_threshold = replenish_threshold
        self.current_visible = visible_quantity

    def generate_schedule(self) -> List[Dict]:
        """Generate iceberg schedule"""
        schedule = []
        remaining = self.order.quantity
        slice_num = 0

        while remaining > 0:
            slice_size = min(self.visible_quantity, remaining)
            slice_num += 1

            schedule.append({
                'slice_number': slice_num,
                'quantity': slice_size,
                'visible_quantity': slice_size,
                'algorithm': 'ICEBERG',
                'order_type': OrderType.LIMIT,
                'replenish_on_fill': True
            })

            remaining -= slice_size

        return schedule

    def get_slice_size(self, time_slice: int, market_data: Dict) -> float:
        """Get slice size for iceberg"""
        return min(self.visible_quantity, self.order.quantity - self.order.filled_quantity)


class SmartOrderRouter:
    """
    Smart Order Routing (SOR)
    Routes orders to best execution venue
    """

    def __init__(self):
        """Initialize Smart Order Router"""
        self.venues = {
            'NSE': {'fee': 0.00325, 'liquidity_score': 0.9},
            'BSE': {'fee': 0.003, 'liquidity_score': 0.7}
        }

    def route_order(self, order: Order, market_data: Dict[str, Dict]) -> str:
        """
        Route order to best venue

        Args:
            order: Order to route
            market_data: Market data per venue

        Returns:
            Best venue name
        """
        best_venue = None
        best_score = -np.inf

        for venue, venue_info in self.venues.items():
            if venue not in market_data:
                continue

            venue_data = market_data[venue]

            # Score based on price improvement, fees, and liquidity
            if order.side == OrderSide.BUY:
                # For buy orders, prefer lower ask price
                price_score = -venue_data.get('ask', np.inf)
            else:
                # For sell orders, prefer higher bid price
                price_score = venue_data.get('bid', -np.inf)

            # Factor in fees
            fee_score = -venue_info['fee']

            # Factor in liquidity
            liquidity_score = venue_info['liquidity_score']

            # Combined score
            total_score = price_score + fee_score * 1000 + liquidity_score * 100

            if total_score > best_score:
                best_score = total_score
                best_venue = venue

        logger.info(f"Routed order to {best_venue} with score {best_score:.2f}")

        return best_venue or 'NSE'  # Default to NSE


class ExecutionEngine:
    """
    Main execution engine orchestrating all algorithms
    """

    def __init__(self, smart_router: Optional[SmartOrderRouter] = None):
        """
        Args:
            smart_router: Smart order router instance
        """
        self.smart_router = smart_router or SmartOrderRouter()
        self.active_orders: Dict[str, Order] = {}
        self.execution_history: List[Dict] = []

    def execute_order(self, order: Order, algorithm: str = 'TWAP',
                     **algo_params) -> List[Order]:
        """
        Execute order using specified algorithm

        Args:
            order: Order to execute
            algorithm: 'TWAP', 'VWAP', 'POV', 'ICEBERG', 'MARKET'
            **algo_params: Algorithm-specific parameters

        Returns:
            List of child orders
        """
        if algorithm == 'TWAP':
            executor = TWAPExecutor(
                order,
                execution_time_minutes=algo_params.get('execution_time_minutes', 60),
                num_slices=algo_params.get('num_slices', 10)
            )
        elif algorithm == 'VWAP':
            executor = VWAPExecutor(
                order,
                execution_time_minutes=algo_params.get('execution_time_minutes', 60),
                volume_profile=algo_params.get('volume_profile')
            )
        elif algorithm == 'POV':
            executor = POVExecutor(
                order,
                execution_time_minutes=algo_params.get('execution_time_minutes', 60),
                participation_rate=algo_params.get('participation_rate', 0.10)
            )
        elif algorithm == 'ICEBERG':
            executor = IcebergOrderExecutor(
                order,
                visible_quantity=algo_params.get('visible_quantity', order.quantity * 0.1)
            )
        else:
            # Direct market order
            return [order]

        # Generate execution schedule
        schedule = executor.generate_schedule()

        # Create child orders
        child_orders = []
        for i, slice_info in enumerate(schedule):
            child_order = Order(
                order_id=f"{order.order_id}_child_{i+1}",
                symbol=order.symbol,
                side=order.side,
                order_type=slice_info.get('order_type', OrderType.MARKET),
                quantity=slice_info['quantity'] if isinstance(slice_info['quantity'], (int, float)) else 0,
                timestamp=slice_info.get('execution_time'),
                parent_algo=algorithm
            )
            child_orders.append(child_order)
            self.active_orders[child_order.order_id] = child_order

        logger.info(f"Created {len(child_orders)} child orders for {algorithm} execution")

        return child_orders

    def get_execution_summary(self, order_id: str) -> Dict:
        """
        Get execution summary for an order

        Args:
            order_id: Order ID

        Returns:
            Execution summary
        """
        # Find all child orders
        child_orders = [o for o in self.active_orders.values()
                       if o.order_id.startswith(order_id)]

        if not child_orders:
            return {'error': 'Order not found'}

        total_filled = sum(o.filled_quantity for o in child_orders)
        total_quantity = sum(o.quantity for o in child_orders)

        avg_fill_price = sum(o.avg_fill_price * o.filled_quantity for o in child_orders
                            if o.filled_quantity > 0)
        avg_fill_price /= total_filled if total_filled > 0 else 1

        return {
            'order_id': order_id,
            'total_quantity': total_quantity,
            'filled_quantity': total_filled,
            'fill_rate': total_filled / total_quantity if total_quantity > 0 else 0,
            'avg_fill_price': avg_fill_price,
            'num_child_orders': len(child_orders),
            'completed': all(o.status == OrderStatus.FILLED for o in child_orders)
        }


class ExecutionCostAnalyzer:
    """
    Analyze execution costs and slippage
    Compare actual execution vs benchmarks (VWAP, TWAP, Arrival Price)
    """

    def __init__(self):
        pass

    def calculate_implementation_shortfall(self, order: Order,
                                          arrival_price: float,
                                          fill_prices: List[float],
                                          fill_quantities: List[float],
                                          benchmark_price: float) -> Dict:
        """
        Calculate Implementation Shortfall (total cost of execution)

        Args:
            order: Executed order
            arrival_price: Price when decision was made
            fill_prices: Actual fill prices
            fill_quantities: Fill quantities
            benchmark_price: Benchmark price (e.g., VWAP, TWAP)

        Returns:
            Cost analysis
        """
        total_filled = sum(fill_quantities)

        # Weighted average fill price
        avg_fill = sum(p * q for p, q in zip(fill_prices, fill_quantities)) / total_filled

        # Implementation shortfall components
        if order.side == OrderSide.BUY:
            # For buys, positive means we paid more
            delay_cost = (arrival_price - benchmark_price) * total_filled
            execution_cost = (avg_fill - arrival_price) * total_filled
            total_cost = (avg_fill - benchmark_price) * total_filled
        else:
            # For sells, positive means we received less
            delay_cost = (benchmark_price - arrival_price) * total_filled
            execution_cost = (arrival_price - avg_fill) * total_filled
            total_cost = (benchmark_price - avg_fill) * total_filled

        # Calculate cost in basis points
        delay_cost_bps = (delay_cost / (arrival_price * total_filled)) * 10000
        execution_cost_bps = (execution_cost / (arrival_price * total_filled)) * 10000
        total_cost_bps = (total_cost / (arrival_price * total_filled)) * 10000

        return {
            'avg_fill_price': avg_fill,
            'benchmark_price': benchmark_price,
            'arrival_price': arrival_price,
            'delay_cost': delay_cost,
            'execution_cost': execution_cost,
            'total_cost': total_cost,
            'delay_cost_bps': delay_cost_bps,
            'execution_cost_bps': execution_cost_bps,
            'total_cost_bps': total_cost_bps,
            'slippage_vs_arrival': avg_fill - arrival_price if order.side == OrderSide.BUY else arrival_price - avg_fill
        }

    def compare_to_vwap(self, fill_price: float, vwap_price: float,
                       order_side: OrderSide) -> Dict:
        """Compare execution to VWAP benchmark"""
        if order_side == OrderSide.BUY:
            performance = vwap_price - fill_price  # Positive is good (paid less than VWAP)
        else:
            performance = fill_price - vwap_price  # Positive is good (received more than VWAP)

        performance_bps = (performance / vwap_price) * 10000

        return {
            'fill_price': fill_price,
            'vwap_price': vwap_price,
            'performance': performance,
            'performance_bps': performance_bps,
            'vs_vwap': 'BEAT' if performance > 0 else 'MISSED'
        }


if __name__ == "__main__":
    logger.info("Advanced Execution Engine - Production Grade")

    # Example: Execute large order with TWAP
    large_order = Order(
        order_id="ORDER_001",
        symbol="RELIANCE",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=10000  # Large order: 10,000 shares
    )

    engine = ExecutionEngine()

    # Execute with TWAP over 60 minutes
    child_orders = engine.execute_order(
        large_order,
        algorithm='TWAP',
        execution_time_minutes=60,
        num_slices=12  # Execute every 5 minutes
    )

    print(f"\nTWAP Execution Plan:")
    print(f"Parent Order: {large_order.quantity} shares")
    print(f"Child Orders: {len(child_orders)}")
    print(f"Slice Size: {large_order.quantity / len(child_orders):.0f} shares per slice")

    # Example: VWAP execution
    vwap_order = Order(
        order_id="ORDER_002",
        symbol="TCS",
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        quantity=5000
    )

    child_orders_vwap = engine.execute_order(
        vwap_order,
        algorithm='VWAP',
        execution_time_minutes=60
    )

    print(f"\nVWAP Execution Plan:")
    print(f"Parent Order: {vwap_order.quantity} shares")
    print(f"Child Orders: {len(child_orders_vwap)}")

    # Example: POV execution
    pov_order = Order(
        order_id="ORDER_003",
        symbol="HDFC",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=8000
    )

    child_orders_pov = engine.execute_order(
        pov_order,
        algorithm='POV',
        participation_rate=0.15  # 15% of market volume
    )

    print(f"\nPOV Execution Plan:")
    print(f"Parent Order: {pov_order.quantity} shares")
    print(f"Participation Rate: 15% of market volume")

    # Execution cost analysis
    analyzer = ExecutionCostAnalyzer()

    cost_analysis = analyzer.calculate_implementation_shortfall(
        order=large_order,
        arrival_price=2500.00,
        fill_prices=[2500.50, 2501.00, 2500.75],
        fill_quantities=[3333, 3333, 3334],
        benchmark_price=2500.60
    )

    print(f"\nExecution Cost Analysis:")
    print(f"Average Fill Price: ₹{cost_analysis['avg_fill_price']:.2f}")
    print(f"Benchmark Price: ₹{cost_analysis['benchmark_price']:.2f}")
    print(f"Total Cost: ₹{cost_analysis['total_cost']:.2f} ({cost_analysis['total_cost_bps']:.2f} bps)")
    print(f"Slippage: ₹{cost_analysis['slippage_vs_arrival']:.2f}")
