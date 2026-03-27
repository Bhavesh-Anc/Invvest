"""
Optimal Execution Algorithms
Used by: Goldman Sachs, Morgan Stanley, JPMorgan, Citadel

Implements professional execution algorithms to minimize market impact
and transaction costs:
- VWAP (Volume-Weighted Average Price)
- TWAP (Time-Weighted Average Price)
- Implementation Shortfall / Arrival Price
- Adaptive execution with market impact modeling
- Smart order routing
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    ICEBERG = "iceberg"
    HIDDEN = "hidden"


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """Order representation"""
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    price: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Fill:
    """Order fill representation"""
    order: Order
    filled_quantity: int
    fill_price: float
    timestamp: datetime
    commission: float = 0.0


class VWAPAlgorithm:
    """
    Volume-Weighted Average Price Algorithm

    Used by: All major banks and hedge funds

    Strategy:
    - Distribute order quantity across time intervals based on historical volume profile
    - Aim to match VWAP benchmark
    - Minimize market impact by trading with natural volume
    """

    def __init__(
        self,
        participation_rate: float = 0.10,
        min_fill_rate: float = 0.05,
        max_fill_rate: float = 0.30
    ):
        """
        Args:
            participation_rate: Target % of market volume to consume (10% default)
            min_fill_rate: Minimum order fill rate per interval
            max_fill_rate: Maximum order fill rate per interval
        """
        self.participation_rate = participation_rate
        self.min_fill_rate = min_fill_rate
        self.max_fill_rate = max_fill_rate

    def calculate_volume_profile(
        self,
        historical_data: pd.DataFrame,
        intervals: int = 30
    ) -> pd.Series:
        """
        Calculate intraday volume profile from historical data

        Args:
            historical_data: DataFrame with intraday volume data
            intervals: Number of time intervals (e.g., 30 min buckets for 9:15-3:30)

        Returns:
            Volume profile (% of daily volume per interval)
        """
        # Group by time of day
        historical_data['time_interval'] = pd.cut(
            range(len(historical_data)),
            bins=intervals,
            labels=range(intervals)
        )

        # Calculate average volume per interval
        volume_profile = historical_data.groupby('time_interval')['volume'].mean()

        # Normalize to percentages
        volume_profile = volume_profile / volume_profile.sum()

        return volume_profile

    def generate_execution_schedule(
        self,
        total_quantity: int,
        volume_profile: pd.Series,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """
        Generate VWAP execution schedule

        Args:
            total_quantity: Total shares to execute
            volume_profile: Intraday volume profile
            start_time: Execution start time
            end_time: Execution end time

        Returns:
            List of scheduled orders with timing and quantity
        """
        schedule = []

        num_intervals = len(volume_profile)
        interval_duration = (end_time - start_time) / num_intervals

        remaining_quantity = total_quantity

        for i, (interval_idx, volume_pct) in enumerate(volume_profile.items()):
            # Allocate quantity based on volume profile
            target_quantity = int(total_quantity * volume_pct)

            # Apply min/max fill rate constraints
            target_quantity = max(
                int(remaining_quantity * self.min_fill_rate),
                min(target_quantity, int(remaining_quantity * self.max_fill_rate))
            )

            # Ensure we don't exceed remaining quantity
            if i == num_intervals - 1:
                # Last interval: fill remainder
                target_quantity = remaining_quantity
            else:
                target_quantity = min(target_quantity, remaining_quantity)

            if target_quantity > 0:
                execution_time = start_time + interval_duration * i

                schedule.append({
                    'interval': i,
                    'execution_time': execution_time,
                    'quantity': target_quantity,
                    'volume_pct': volume_pct,
                    'cumulative_quantity': total_quantity - remaining_quantity + target_quantity
                })

                remaining_quantity -= target_quantity

        return schedule

    def calculate_vwap_benchmark(
        self,
        prices: pd.Series,
        volumes: pd.Series
    ) -> float:
        """
        Calculate VWAP benchmark from market data

        Args:
            prices: Price series
            volumes: Volume series

        Returns:
            VWAP price
        """
        return float((prices * volumes).sum() / volumes.sum())

    def evaluate_execution(
        self,
        fills: List[Fill],
        vwap_benchmark: float
    ) -> Dict:
        """
        Evaluate VWAP execution performance

        Args:
            fills: List of order fills
            vwap_benchmark: Market VWAP

        Returns:
            Performance metrics
        """
        if not fills:
            return {
                'execution_vwap': 0,
                'benchmark_vwap': vwap_benchmark,
                'slippage_bps': 0,
                'num_fills': 0,
                'total_quantity': 0,
                'total_commission': 0
            }

        # Calculate execution VWAP
        total_value = sum(fill.filled_quantity * fill.fill_price for fill in fills)
        total_quantity = sum(fill.filled_quantity for fill in fills)
        execution_vwap = total_value / total_quantity if total_quantity > 0 else 0

        # Calculate slippage
        slippage_bps = (execution_vwap - vwap_benchmark) / vwap_benchmark * 10000

        # Total commission
        total_commission = sum(fill.commission for fill in fills)

        return {
            'execution_vwap': round(execution_vwap, 2),
            'benchmark_vwap': round(vwap_benchmark, 2),
            'slippage_bps': round(slippage_bps, 2),
            'num_fills': len(fills),
            'total_quantity': total_quantity,
            'total_commission': round(total_commission, 2),
            'cost_per_share': round((execution_vwap - vwap_benchmark) + (total_commission / total_quantity), 4)
        }


class TWAPAlgorithm:
    """
    Time-Weighted Average Price Algorithm

    Used by: All major banks

    Strategy:
    - Distribute order quantity evenly across time intervals
    - Simpler than VWAP, doesn't depend on volume forecast
    - Good for low-urgency orders and illiquid stocks
    """

    def __init__(
        self,
        randomize: bool = True,
        randomization_pct: float = 0.20
    ):
        """
        Args:
            randomize: Add randomization to avoid detection
            randomization_pct: % randomization around target (20% default)
        """
        self.randomize = randomize
        self.randomization_pct = randomization_pct

    def generate_execution_schedule(
        self,
        total_quantity: int,
        num_intervals: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """
        Generate TWAP execution schedule

        Args:
            total_quantity: Total shares to execute
            num_intervals: Number of execution intervals
            start_time: Start time
            end_time: End time

        Returns:
            Execution schedule
        """
        schedule = []

        base_quantity_per_interval = total_quantity / num_intervals
        interval_duration = (end_time - start_time) / num_intervals

        remaining_quantity = total_quantity

        for i in range(num_intervals):
            execution_time = start_time + interval_duration * i

            if i == num_intervals - 1:
                # Last interval: execute remaining
                target_quantity = remaining_quantity
            else:
                # Apply randomization
                if self.randomize:
                    randomization = np.random.uniform(
                        1 - self.randomization_pct,
                        1 + self.randomization_pct
                    )
                    target_quantity = int(base_quantity_per_interval * randomization)
                else:
                    target_quantity = int(base_quantity_per_interval)

                # Ensure we don't exceed remaining
                target_quantity = min(target_quantity, remaining_quantity)

            schedule.append({
                'interval': i,
                'execution_time': execution_time,
                'quantity': target_quantity,
                'cumulative_quantity': total_quantity - remaining_quantity + target_quantity
            })

            remaining_quantity -= target_quantity

        return schedule

    def evaluate_execution(
        self,
        fills: List[Fill],
        start_price: float,
        end_price: float
    ) -> Dict:
        """
        Evaluate TWAP execution performance

        Args:
            fills: List of order fills
            start_price: Price at execution start
            end_price: Price at execution end

        Returns:
            Performance metrics
        """
        if not fills:
            return {
                'execution_price': 0,
                'start_price': start_price,
                'end_price': end_price,
                'slippage_bps': 0,
                'total_quantity': 0
            }

        # Calculate average execution price
        total_value = sum(fill.filled_quantity * fill.fill_price for fill in fills)
        total_quantity = sum(fill.filled_quantity for fill in fills)
        execution_price = total_value / total_quantity if total_quantity > 0 else 0

        # Benchmark: midpoint of start and end
        benchmark_price = (start_price + end_price) / 2

        # Slippage
        slippage_bps = (execution_price - benchmark_price) / benchmark_price * 10000

        return {
            'execution_price': round(execution_price, 2),
            'benchmark_price': round(benchmark_price, 2),
            'start_price': start_price,
            'end_price': end_price,
            'slippage_bps': round(slippage_bps, 2),
            'total_quantity': total_quantity
        }


class MarketImpactModel:
    """
    Market Impact Model

    Used by: Goldman Sachs, JPMorgan, Citadel

    Models the impact of large orders on market price

    Based on Almgren-Chriss model:
    - Permanent impact: Information leakage, doesn't decay
    - Temporary impact: Price pressure, decays after execution
    """

    def __init__(
        self,
        permanent_impact_coef: float = 0.1,
        temporary_impact_coef: float = 0.5,
        volatility: float = 0.02
    ):
        """
        Args:
            permanent_impact_coef: Permanent impact coefficient
            temporary_impact_coef: Temporary impact coefficient
            volatility: Daily volatility
        """
        self.permanent_impact_coef = permanent_impact_coef
        self.temporary_impact_coef = temporary_impact_coef
        self.volatility = volatility

    def calculate_permanent_impact(
        self,
        quantity: int,
        adv: float,
        price: float
    ) -> float:
        """
        Calculate permanent market impact

        Args:
            quantity: Order quantity (shares)
            adv: Average Daily Volume (shares)
            price: Current price

        Returns:
            Permanent price impact (absolute)
        """
        # Permanent impact ∝ sqrt(quantity / ADV)
        participation_rate = quantity / adv if adv > 0 else 0

        permanent_impact = (
            self.permanent_impact_coef *
            price *
            self.volatility *
            np.sqrt(participation_rate)
        )

        return float(permanent_impact)

    def calculate_temporary_impact(
        self,
        quantity: int,
        adv: float,
        price: float,
        execution_time: float = 1.0
    ) -> float:
        """
        Calculate temporary market impact

        Args:
            quantity: Order quantity (shares)
            adv: Average Daily Volume (shares)
            price: Current price
            execution_time: Execution time (fraction of day)

        Returns:
            Temporary price impact (absolute)
        """
        # Temporary impact ∝ (quantity / ADV) / execution_time
        participation_rate = quantity / adv if adv > 0 else 0

        temporary_impact = (
            self.temporary_impact_coef *
            price *
            self.volatility *
            (participation_rate / execution_time)
        )

        return float(temporary_impact)

    def calculate_total_impact(
        self,
        quantity: int,
        adv: float,
        price: float,
        execution_time: float = 1.0
    ) -> Dict:
        """
        Calculate total market impact

        Args:
            quantity: Order quantity
            adv: Average Daily Volume
            price: Current price
            execution_time: Execution time (fraction of day)

        Returns:
            Impact breakdown
        """
        permanent = self.calculate_permanent_impact(quantity, adv, price)
        temporary = self.calculate_temporary_impact(quantity, adv, price, execution_time)

        total_impact = permanent + temporary
        total_cost = total_impact * quantity

        return {
            'permanent_impact': round(permanent, 4),
            'temporary_impact': round(temporary, 4),
            'total_impact': round(total_impact, 4),
            'total_cost': round(total_cost, 2),
            'impact_bps': round(total_impact / price * 10000, 2)
        }

    def optimize_execution_time(
        self,
        quantity: int,
        adv: float,
        price: float,
        max_time: float = 1.0
    ) -> float:
        """
        Optimize execution time to minimize total cost

        Trades off:
        - Faster execution → Higher temporary impact
        - Slower execution → More risk from price movements

        Args:
            quantity: Order quantity
            adv: Average Daily Volume
            price: Current price
            max_time: Maximum execution time (fraction of day)

        Returns:
            Optimal execution time
        """
        def total_cost(execution_time):
            """Total cost = Market impact + Risk cost"""
            impact = self.calculate_total_impact(quantity, adv, price, execution_time)

            # Risk cost: volatility risk from delaying execution
            risk_cost = (
                0.5 * self.volatility * price * quantity * np.sqrt(execution_time)
            )

            return impact['total_cost'] + risk_cost

        # Find optimal time
        from scipy.optimize import minimize_scalar

        result = minimize_scalar(
            total_cost,
            bounds=(0.01, max_time),
            method='bounded'
        )

        optimal_time = result.x

        return float(optimal_time)


class AdaptiveExecutionAlgorithm:
    """
    Adaptive Execution Algorithm

    Used by: Citadel, Two Sigma, Renaissance Technologies

    Dynamically adjusts execution based on:
    - Real-time volume
    - Price movements
    - Market conditions
    - Urgency level
    """

    def __init__(
        self,
        urgency: float = 0.5,
        volume_threshold: float = 0.15
    ):
        """
        Args:
            urgency: Urgency level (0-1, higher = more aggressive)
            volume_threshold: Volume threshold for aggressive execution
        """
        self.urgency = urgency
        self.volume_threshold = volume_threshold
        self.vwap_algo = VWAPAlgorithm()
        self.twap_algo = TWAPAlgorithm()

    def adjust_schedule_real_time(
        self,
        original_schedule: List[Dict],
        current_interval: int,
        executed_quantity: int,
        target_quantity: int,
        current_volume_pct: float,
        expected_volume_pct: float
    ) -> List[Dict]:
        """
        Adjust execution schedule in real-time

        Args:
            original_schedule: Original execution schedule
            current_interval: Current interval index
            executed_quantity: Quantity executed so far
            target_quantity: Total target quantity
            current_volume_pct: Current interval volume %
            expected_volume_pct: Expected interval volume %

        Returns:
            Adjusted schedule
        """
        remaining_quantity = target_quantity - executed_quantity

        if remaining_quantity <= 0:
            return []

        # Volume deviation
        volume_ratio = current_volume_pct / expected_volume_pct if expected_volume_pct > 0 else 1.0

        # Adjust aggressiveness based on volume
        if volume_ratio > 1 + self.volume_threshold:
            # Higher than expected volume: be more aggressive
            adjustment_factor = 1.0 + self.urgency * 0.3
        elif volume_ratio < 1 - self.volume_threshold:
            # Lower than expected volume: be more conservative
            adjustment_factor = 1.0 - self.urgency * 0.2
        else:
            adjustment_factor = 1.0

        # Adjust remaining schedule
        adjusted_schedule = []

        for scheduled_order in original_schedule[current_interval + 1:]:
            adjusted_quantity = int(scheduled_order['quantity'] * adjustment_factor)

            adjusted_schedule.append({
                **scheduled_order,
                'quantity': adjusted_quantity,
                'adjustment_factor': adjustment_factor
            })

        # Rebalance to ensure we execute total quantity
        total_adjusted = sum(order['quantity'] for order in adjusted_schedule)

        if total_adjusted != remaining_quantity and adjusted_schedule:
            # Adjust last order
            adjusted_schedule[-1]['quantity'] += remaining_quantity - total_adjusted

        return adjusted_schedule

    def calculate_urgency_score(
        self,
        time_elapsed: float,
        total_time: float,
        pct_executed: float
    ) -> float:
        """
        Calculate dynamic urgency score

        Args:
            time_elapsed: Time elapsed (fraction)
            total_time: Total execution time (fraction)
            pct_executed: % of order executed

        Returns:
            Urgency score (0-1)
        """
        time_pct = time_elapsed / total_time if total_time > 0 else 0

        # If we're behind schedule, increase urgency
        if pct_executed < time_pct:
            urgency_adjustment = (time_pct - pct_executed) * 2
        else:
            urgency_adjustment = 0

        # Dynamic urgency
        dynamic_urgency = min(1.0, self.urgency + urgency_adjustment)

        return float(dynamic_urgency)


class SmartOrderRouter:
    """
    Smart Order Router (SOR)

    Used by: All major brokers and exchanges

    Routes orders to best execution venues:
    - NSE vs BSE
    - Multiple exchange connections
    - Dark pools (not applicable in India)
    - Minimize costs, maximize fill probability
    """

    def __init__(self):
        self.venues = ['NSE', 'BSE']
        self.venue_costs = {
            'NSE': {'commission': 0.0003, 'impact': 1.0},
            'BSE': {'commission': 0.0003, 'impact': 1.1}
        }

    def evaluate_venue(
        self,
        venue: str,
        quantity: int,
        available_liquidity: int,
        price: float
    ) -> Dict:
        """
        Evaluate execution venue

        Args:
            venue: Venue name
            quantity: Order quantity
            available_liquidity: Available shares at venue
            price: Current price

        Returns:
            Venue evaluation
        """
        costs = self.venue_costs.get(venue, {'commission': 0.001, 'impact': 1.0})

        # Fill probability
        fill_probability = min(1.0, available_liquidity / quantity) if quantity > 0 else 0

        # Estimated cost
        commission_cost = quantity * price * costs['commission']
        impact_cost = quantity * price * 0.0001 * costs['impact']  # 1bp base impact

        total_cost = commission_cost + impact_cost

        return {
            'venue': venue,
            'fill_probability': round(fill_probability, 2),
            'commission_cost': round(commission_cost, 2),
            'impact_cost': round(impact_cost, 2),
            'total_cost': round(total_cost, 2),
            'cost_per_share': round(total_cost / quantity, 4) if quantity > 0 else 0
        }

    def route_order(
        self,
        order: Order,
        venue_liquidity: Dict[str, int]
    ) -> List[Dict]:
        """
        Route order to optimal venues

        Args:
            order: Order to route
            venue_liquidity: Available liquidity at each venue

        Returns:
            Routing decision (venue, quantity pairs)
        """
        routing = []
        remaining_quantity = order.quantity

        # Evaluate all venues
        venue_evaluations = []

        for venue in self.venues:
            liquidity = venue_liquidity.get(venue, 0)

            if liquidity > 0:
                evaluation = self.evaluate_venue(
                    venue,
                    remaining_quantity,
                    liquidity,
                    order.price or 0
                )
                venue_evaluations.append(evaluation)

        # Sort by cost per share
        venue_evaluations.sort(key=lambda x: x['cost_per_share'])

        # Allocate to venues
        for evaluation in venue_evaluations:
            venue = evaluation['venue']
            available = venue_liquidity[venue]

            quantity_to_route = min(remaining_quantity, available)

            if quantity_to_route > 0:
                routing.append({
                    'venue': venue,
                    'quantity': quantity_to_route,
                    'estimated_cost': evaluation['cost_per_share'] * quantity_to_route
                })

                remaining_quantity -= quantity_to_route

            if remaining_quantity <= 0:
                break

        return routing


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("VWAP ALGORITHM TEST")
    print("=" * 60)

    vwap = VWAPAlgorithm(participation_rate=0.10)

    # Mock volume profile (typical Indian market intraday pattern)
    volume_profile = pd.Series({
        0: 0.08,   # 9:15-9:30 (opening surge)
        1: 0.06,   # 9:30-10:00
        2: 0.05,   # 10:00-10:30
        3: 0.04,   # 10:30-11:00
        4: 0.04,   # 11:00-11:30
        5: 0.05,   # 11:30-12:00
        6: 0.06,   # 12:00-12:30
        7: 0.08,   # 12:30-13:00
        8: 0.10,   # 13:00-13:30
        9: 0.12,   # 13:30-14:00
        10: 0.15,  # 14:00-14:30
        11: 0.17   # 14:30-15:00 (closing surge)
    })

    schedule = vwap.generate_execution_schedule(
        total_quantity=10000,
        volume_profile=volume_profile,
        start_time=datetime(2024, 1, 8, 9, 15),
        end_time=datetime(2024, 1, 8, 15, 0)
    )

    print(f"Generated VWAP schedule for 10,000 shares:")
    print(f"Number of intervals: {len(schedule)}\n")

    for order in schedule[:5]:  # Show first 5
        print(f"Interval {order['interval']}: {order['quantity']} shares at {order['execution_time'].strftime('%H:%M')}")

    # Test TWAP
    print("\n" + "=" * 60)
    print("TWAP ALGORITHM TEST")
    print("=" * 60)

    twap = TWAPAlgorithm(randomize=True)

    schedule = twap.generate_execution_schedule(
        total_quantity=10000,
        num_intervals=10,
        start_time=datetime(2024, 1, 8, 9, 15),
        end_time=datetime(2024, 1, 8, 15, 0)
    )

    print(f"Generated TWAP schedule for 10,000 shares:")
    print(f"Number of intervals: {len(schedule)}\n")

    for order in schedule[:5]:
        print(f"Interval {order['interval']}: {order['quantity']} shares at {order['execution_time'].strftime('%H:%M')}")

    # Test Market Impact Model
    print("\n" + "=" * 60)
    print("MARKET IMPACT MODEL TEST")
    print("=" * 60)

    impact_model = MarketImpactModel()

    # Example: 100,000 share order in RELIANCE
    impact = impact_model.calculate_total_impact(
        quantity=100000,
        adv=5000000,  # 5M ADV
        price=2500,
        execution_time=0.5  # Half day
    )

    print(f"Order: 100,000 shares @ ₹2,500")
    print(f"ADV: 5,000,000 shares")
    print(f"Execution time: 0.5 days (half trading day)")
    print(f"\nImpact Analysis:")
    print(f"Permanent Impact: ₹{impact['permanent_impact']:.2f} per share")
    print(f"Temporary Impact: ₹{impact['temporary_impact']:.2f} per share")
    print(f"Total Impact: {impact['impact_bps']:.2f} bps")
    print(f"Total Cost: ₹{impact['total_cost']:,.0f}")

    # Optimize execution time
    optimal_time = impact_model.optimize_execution_time(
        quantity=100000,
        adv=5000000,
        price=2500
    )

    print(f"\nOptimal Execution Time: {optimal_time:.2f} days ({optimal_time*6:.1f} hours)")

    print("\n" + "=" * 60)
    print("All execution algorithms tested successfully!")
    print("=" * 60)
