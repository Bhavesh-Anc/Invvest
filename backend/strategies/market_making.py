"""
Market Making Strategies
Used by: Citadel Securities, Virtu Financial, Jane Street, IMC, Optiver

Implements professional market making algorithms:
- Continuous two-sided quoting
- Inventory management and risk controls
- Spread optimization based on volatility and order flow
- Adverse selection avoidance
- Quote skewing based on inventory position
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QuoteSide(Enum):
    """Quote side"""
    BID = "bid"
    ASK = "ask"
    BOTH = "both"


@dataclass
class Quote:
    """Market maker quote"""
    symbol: str
    bid_price: float
    bid_size: int
    ask_price: float
    ask_size: int
    timestamp: datetime
    mid_price: float = None

    def __post_init__(self):
        if self.mid_price is None:
            self.mid_price = (self.bid_price + self.ask_price) / 2

    @property
    def spread(self) -> float:
        """Bid-ask spread in absolute terms"""
        return self.ask_price - self.bid_price

    @property
    def spread_bps(self) -> float:
        """Bid-ask spread in basis points"""
        return (self.spread / self.mid_price) * 10000 if self.mid_price > 0 else 0


@dataclass
class InventoryPosition:
    """Inventory tracking"""
    symbol: str
    quantity: int
    avg_cost: float
    market_value: float
    unrealized_pnl: float
    timestamp: datetime


class MarketMaker:
    """
    Basic Market Making Strategy

    Used by: All professional market makers

    Core principles:
    1. Provide liquidity by quoting both bid and ask
    2. Capture bid-ask spread
    3. Manage inventory risk
    4. Avoid adverse selection
    5. Adjust quotes based on market conditions
    """

    def __init__(
        self,
        base_spread_bps: float = 10,
        min_spread_bps: float = 5,
        max_spread_bps: float = 50,
        quote_size: int = 100,
        max_inventory: int = 10000,
        target_inventory: int = 0,
        risk_aversion: float = 0.01
    ):
        """
        Args:
            base_spread_bps: Base bid-ask spread (10 bps default)
            min_spread_bps: Minimum spread
            max_spread_bps: Maximum spread
            quote_size: Size of each quote
            max_inventory: Maximum inventory position
            target_inventory: Target inventory (0 = market neutral)
            risk_aversion: Risk aversion parameter for inventory skewing
        """
        self.base_spread_bps = base_spread_bps
        self.min_spread_bps = min_spread_bps
        self.max_spread_bps = max_spread_bps
        self.quote_size = quote_size
        self.max_inventory = max_inventory
        self.target_inventory = target_inventory
        self.risk_aversion = risk_aversion

        # State tracking
        self.inventory = 0
        self.avg_cost = 0
        self.total_trades = 0
        self.total_pnl = 0

    def calculate_fair_value(
        self,
        last_price: float,
        bid: float,
        ask: float,
        bid_size: int,
        ask_size: int
    ) -> float:
        """
        Calculate fair value from order book

        Args:
            last_price: Last traded price
            bid: Best bid
            ask: Best ask
            bid_size: Bid size
            ask_size: Ask size

        Returns:
            Fair value estimate
        """
        # Weighted average of bid/ask based on sizes
        if bid_size + ask_size > 0:
            fair_value = (bid * ask_size + ask * bid_size) / (bid_size + ask_size)
        else:
            fair_value = (bid + ask) / 2

        # Blend with last price (70% book, 30% last price)
        fair_value = 0.7 * fair_value + 0.3 * last_price

        return float(fair_value)

    def calculate_optimal_spread(
        self,
        volatility: float,
        order_flow_imbalance: float,
        inventory_pct: float
    ) -> float:
        """
        Calculate optimal bid-ask spread

        Based on:
        - Market volatility (higher vol → wider spread)
        - Order flow imbalance (toxic flow → wider spread)
        - Inventory position (extreme inventory → adjust spread)

        Args:
            volatility: Recent volatility (e.g., 5-min returns std)
            order_flow_imbalance: Order flow imbalance (-1 to 1)
            inventory_pct: Current inventory as % of max

        Returns:
            Optimal spread in bps
        """
        # Base spread
        spread = self.base_spread_bps

        # Volatility adjustment: spread ∝ volatility
        volatility_multiplier = 1 + (volatility / 0.01)  # Normalize by 1% vol
        spread *= volatility_multiplier

        # Order flow adjustment: widen spread if imbalanced (adverse selection)
        flow_adjustment = 1 + abs(order_flow_imbalance) * 0.5
        spread *= flow_adjustment

        # Inventory adjustment: widen spread when inventory extreme
        inventory_adjustment = 1 + abs(inventory_pct) * 0.3
        spread *= inventory_adjustment

        # Clamp to min/max
        spread = max(self.min_spread_bps, min(spread, self.max_spread_bps))

        return float(spread)

    def calculate_inventory_skew(
        self,
        inventory_pct: float
    ) -> float:
        """
        Calculate quote skew based on inventory

        When long (positive inventory):
        - Skew quotes down to encourage selling
        - Widen ask, tighten bid

        When short (negative inventory):
        - Skew quotes up to encourage buying
        - Widen bid, tighten ask

        Args:
            inventory_pct: Current inventory as % of max (-1 to 1)

        Returns:
            Skew in bps (negative = lower quotes, positive = higher quotes)
        """
        # Linear skew based on inventory
        # When inventory = +100%, skew = -risk_aversion * spread
        # When inventory = -100%, skew = +risk_aversion * spread

        skew_bps = -inventory_pct * self.risk_aversion * self.base_spread_bps * 100

        return float(skew_bps)

    def generate_quotes(
        self,
        symbol: str,
        fair_value: float,
        volatility: float,
        order_flow_imbalance: float
    ) -> Quote:
        """
        Generate bid and ask quotes

        Args:
            symbol: Symbol to quote
            fair_value: Fair value estimate
            volatility: Recent volatility
            order_flow_imbalance: Order flow imbalance

        Returns:
            Quote with bid/ask prices and sizes
        """
        # Calculate inventory metrics
        inventory_pct = self.inventory / self.max_inventory if self.max_inventory > 0 else 0

        # Optimal spread
        spread_bps = self.calculate_optimal_spread(
            volatility,
            order_flow_imbalance,
            inventory_pct
        )

        # Inventory skew
        skew_bps = self.calculate_inventory_skew(inventory_pct)

        # Half spread in absolute terms
        half_spread = (spread_bps / 10000) * fair_value / 2

        # Skew in absolute terms
        skew_amount = (skew_bps / 10000) * fair_value

        # Generate quotes
        bid_price = fair_value - half_spread + skew_amount
        ask_price = fair_value + half_spread + skew_amount

        # Quote sizes
        bid_size = self.quote_size
        ask_size = self.quote_size

        # Adjust sizes based on inventory
        if inventory_pct > 0.5:
            # Long: increase ask size, decrease bid size
            ask_size = int(self.quote_size * 1.5)
            bid_size = int(self.quote_size * 0.5)
        elif inventory_pct < -0.5:
            # Short: increase bid size, decrease ask size
            bid_size = int(self.quote_size * 1.5)
            ask_size = int(self.quote_size * 0.5)

        # Check inventory limits
        if abs(self.inventory) >= self.max_inventory:
            if self.inventory > 0:
                # Too long: only quote ask (exit only)
                bid_size = 0
            else:
                # Too short: only quote bid (exit only)
                ask_size = 0

        return Quote(
            symbol=symbol,
            bid_price=round(bid_price, 2),
            bid_size=bid_size,
            ask_price=round(ask_price, 2),
            ask_size=ask_size,
            timestamp=datetime.now(),
            mid_price=fair_value
        )

    def process_fill(
        self,
        side: QuoteSide,
        quantity: int,
        price: float
    ) -> Dict:
        """
        Process a fill (trade execution)

        Args:
            side: Which side was hit (BID or ASK)
            quantity: Quantity filled
            price: Fill price

        Returns:
            Fill details and updated inventory
        """
        realized_pnl = 0

        if side == QuoteSide.BID:
            # Our bid was hit: we bought
            old_inventory = self.inventory
            old_avg_cost = self.avg_cost

            # Update inventory
            self.inventory += quantity

            # Update average cost
            if self.inventory != 0:
                self.avg_cost = (
                    (old_inventory * old_avg_cost + quantity * price) / self.inventory
                )
            else:
                self.avg_cost = price

            fill_type = "BUY"

        else:  # ASK
            # Our ask was hit: we sold
            old_inventory = self.inventory

            # Calculate realized P&L
            if old_inventory > 0:
                realized_pnl = quantity * (price - self.avg_cost)
                self.total_pnl += realized_pnl

            # Update inventory
            self.inventory -= quantity

            # If we flip from long to short, reset avg cost
            if old_inventory > 0 and self.inventory < 0:
                self.avg_cost = price

            fill_type = "SELL"

        self.total_trades += 1

        return {
            'fill_type': fill_type,
            'quantity': quantity,
            'price': price,
            'inventory_before': old_inventory if side == QuoteSide.BID else old_inventory,
            'inventory_after': self.inventory,
            'avg_cost': round(self.avg_cost, 2),
            'realized_pnl': round(realized_pnl, 2),
            'timestamp': datetime.now()
        }

    def calculate_pnl(
        self,
        current_price: float
    ) -> Dict:
        """
        Calculate current P&L

        Args:
            current_price: Current market price

        Returns:
            P&L breakdown
        """
        # Mark-to-market
        unrealized_pnl = self.inventory * (current_price - self.avg_cost)

        total_pnl = self.total_pnl + unrealized_pnl

        return {
            'inventory': self.inventory,
            'avg_cost': round(self.avg_cost, 2),
            'current_price': round(current_price, 2),
            'unrealized_pnl': round(unrealized_pnl, 2),
            'realized_pnl': round(self.total_pnl, 2),
            'total_pnl': round(total_pnl, 2),
            'total_trades': self.total_trades
        }


class OrderFlowAnalyzer:
    """
    Order Flow Analysis for Market Making

    Used by: Citadel Securities, Virtu Financial, Jane Street

    Analyzes order flow to detect:
    - Informed trading (adverse selection)
    - Toxic flow vs uninformed flow
    - Order flow imbalance
    """

    def __init__(self, lookback_periods: int = 20):
        """
        Args:
            lookback_periods: Number of periods for flow analysis
        """
        self.lookback_periods = lookback_periods

    def calculate_order_flow_imbalance(
        self,
        buy_volume: pd.Series,
        sell_volume: pd.Series
    ) -> float:
        """
        Calculate order flow imbalance

        Args:
            buy_volume: Recent buy volume series
            sell_volume: Recent sell volume series

        Returns:
            Imbalance (-1 to 1, negative = sell pressure)
        """
        recent_buy = buy_volume.iloc[-self.lookback_periods:].sum()
        recent_sell = sell_volume.iloc[-self.lookback_periods:].sum()

        total_volume = recent_buy + recent_sell

        if total_volume > 0:
            imbalance = (recent_buy - recent_sell) / total_volume
        else:
            imbalance = 0

        return float(imbalance)

    def detect_adverse_selection(
        self,
        prices: pd.Series,
        trade_directions: pd.Series
    ) -> Dict:
        """
        Detect adverse selection (informed trading)

        If price moves against us after we provide liquidity,
        we're suffering from adverse selection.

        Args:
            prices: Price series
            trade_directions: 1 for buy, -1 for sell

        Returns:
            Adverse selection metrics
        """
        # Calculate price changes after trades
        price_changes = prices.diff()

        # Adverse selection: buy trades followed by price drops (and vice versa)
        adverse_events = (
            ((trade_directions == 1) & (price_changes < 0)) |
            ((trade_directions == -1) & (price_changes > 0))
        )

        adverse_selection_rate = adverse_events.sum() / len(trade_directions)

        return {
            'adverse_selection_rate': round(float(adverse_selection_rate), 3),
            'is_high': adverse_selection_rate > 0.6,  # > 60% is concerning
            'avg_adverse_move': round(float(price_changes[adverse_events].abs().mean()), 2)
        }

    def calculate_effective_spread(
        self,
        fill_prices: pd.Series,
        mid_prices: pd.Series,
        trade_sides: pd.Series
    ) -> float:
        """
        Calculate effective spread (actual cost paid by traders)

        Args:
            fill_prices: Execution prices
            mid_prices: Mid prices at execution time
            trade_sides: 1 for buy, -1 for sell

        Returns:
            Effective spread in bps
        """
        # Effective spread = 2 * |fill_price - mid_price| / mid_price
        spreads = 2 * np.abs(fill_prices - mid_prices) / mid_prices

        avg_effective_spread_pct = spreads.mean()
        avg_effective_spread_bps = avg_effective_spread_pct * 10000

        return float(avg_effective_spread_bps)


class VolatilityEstimator:
    """
    Real-time volatility estimation for market making

    Used by: All market makers

    Estimates short-term volatility for spread adjustment
    """

    def __init__(self, window: int = 100):
        """
        Args:
            window: Rolling window for volatility calculation
        """
        self.window = window

    def estimate_realized_volatility(
        self,
        prices: pd.Series,
        frequency: str = '1min'
    ) -> float:
        """
        Estimate realized volatility from recent prices

        Args:
            prices: Price series
            frequency: Data frequency ('1min', '5min', etc.)

        Returns:
            Annualized volatility
        """
        # Log returns
        returns = np.log(prices / prices.shift(1)).dropna()

        # Recent volatility
        recent_returns = returns.iloc[-self.window:]
        volatility = recent_returns.std()

        # Annualize based on frequency
        if frequency == '1min':
            periods_per_day = 375  # 6.25 hours * 60 minutes
        elif frequency == '5min':
            periods_per_day = 75
        else:
            periods_per_day = 375

        annualized_vol = volatility * np.sqrt(periods_per_day * 252)

        return float(annualized_vol)

    def estimate_garman_klass_volatility(
        self,
        high: pd.Series,
        low: pd.Series,
        open_: pd.Series,
        close: pd.Series
    ) -> float:
        """
        Garman-Klass volatility estimator

        More efficient than close-to-close volatility

        Args:
            high: High prices
            low: Low prices
            open_: Open prices
            close: Close prices

        Returns:
            Annualized volatility
        """
        # Garman-Klass formula
        hl = np.log(high / low)
        co = np.log(close / open_)

        variance = 0.5 * (hl ** 2) - (2 * np.log(2) - 1) * (co ** 2)

        recent_variance = variance.iloc[-self.window:].mean()
        volatility = np.sqrt(recent_variance * 252)

        return float(volatility)


class InventoryManager:
    """
    Advanced Inventory Management

    Used by: Citadel Securities, Jane Street

    Manages inventory risk through:
    - Position limits
    - Risk-based pricing
    - Inventory flattening
    """

    def __init__(
        self,
        max_position: int,
        max_position_value: float,
        max_exposure_pct: float = 0.10
    ):
        """
        Args:
            max_position: Maximum position in shares
            max_position_value: Maximum position value in currency
            max_exposure_pct: Maximum exposure as % of capital
        """
        self.max_position = max_position
        self.max_position_value = max_position_value
        self.max_exposure_pct = max_exposure_pct

    def check_position_limit(
        self,
        current_position: int,
        proposed_trade_size: int,
        side: QuoteSide
    ) -> Dict:
        """
        Check if proposed trade violates position limits

        Args:
            current_position: Current inventory
            proposed_trade_size: Size of proposed trade
            side: Trade side (BID = buy, ASK = sell)

        Returns:
            Limit check result
        """
        # Calculate new position
        if side == QuoteSide.BID:
            new_position = current_position + proposed_trade_size
        else:
            new_position = current_position - proposed_trade_size

        # Check limit
        exceeds_limit = abs(new_position) > self.max_position

        # Calculate remaining capacity
        if side == QuoteSide.BID:
            remaining_capacity = self.max_position - current_position
        else:
            remaining_capacity = self.max_position + current_position

        return {
            'allowed': not exceeds_limit,
            'current_position': current_position,
            'proposed_position': new_position,
            'max_position': self.max_position,
            'remaining_capacity': max(0, remaining_capacity),
            'utilization_pct': round(abs(new_position) / self.max_position * 100, 1)
        }

    def calculate_inventory_urgency(
        self,
        current_position: int,
        target_position: int = 0
    ) -> float:
        """
        Calculate urgency to flatten inventory

        Args:
            current_position: Current inventory
            target_position: Target inventory (usually 0)

        Returns:
            Urgency score (0-1, higher = more urgent)
        """
        position_deviation = abs(current_position - target_position)
        max_deviation = self.max_position

        urgency = min(1.0, position_deviation / max_deviation)

        # Non-linear urgency (accelerates as position grows)
        urgency = urgency ** 2

        return float(urgency)


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("MARKET MAKING SIMULATION")
    print("=" * 60)

    # Initialize market maker
    mm = MarketMaker(
        base_spread_bps=10,
        quote_size=100,
        max_inventory=5000,
        risk_aversion=0.01
    )

    # Simulate market conditions
    np.random.seed(42)

    # Fair value around 1000
    fair_value = 1000.0
    volatility = 0.02  # 2% daily vol
    order_flow_imbalance = 0.1  # Slightly more buying

    print(f"Initial State:")
    print(f"Fair Value: ₹{fair_value:.2f}")
    print(f"Volatility: {volatility:.1%}")
    print(f"Order Flow Imbalance: {order_flow_imbalance:+.2f}")
    print()

    # Generate initial quotes
    quote = mm.generate_quotes('NIFTY', fair_value, volatility, order_flow_imbalance)

    print(f"Initial Quotes:")
    print(f"Bid: ₹{quote.bid_price:.2f} x {quote.bid_size}")
    print(f"Ask: ₹{quote.ask_price:.2f} x {quote.ask_size}")
    print(f"Spread: ₹{quote.spread:.2f} ({quote.spread_bps:.1f} bps)")
    print(f"Inventory: {mm.inventory} shares")
    print()

    # Simulate some trades
    print("Simulating trades...")
    print("-" * 60)

    # Trade 1: Someone hits our bid (we buy)
    fill1 = mm.process_fill(QuoteSide.BID, 100, quote.bid_price)
    print(f"Fill 1: {fill1['fill_type']} {fill1['quantity']} @ ₹{fill1['price']:.2f}")
    print(f"  Inventory: {fill1['inventory_after']}")

    # Trade 2: Someone hits our ask (we sell)
    quote2 = mm.generate_quotes('NIFTY', fair_value + 1, volatility, order_flow_imbalance)
    fill2 = mm.process_fill(QuoteSide.ASK, 50, quote2.ask_price)
    print(f"\nFill 2: {fill2['fill_type']} {fill2['quantity']} @ ₹{fill2['price']:.2f}")
    print(f"  Inventory: {fill2['inventory_after']}")
    print(f"  Realized P&L: ₹{fill2['realized_pnl']:.2f}")

    # Trade 3: Build long position
    fill3 = mm.process_fill(QuoteSide.BID, 200, quote.bid_price)
    print(f"\nFill 3: {fill3['fill_type']} {fill3['quantity']} @ ₹{fill3['price']:.2f}")
    print(f"  Inventory: {fill3['inventory_after']}")

    # Generate quotes with inventory
    quote3 = mm.generate_quotes('NIFTY', fair_value, volatility, order_flow_imbalance)
    print(f"\nQuotes with inventory ({mm.inventory} shares):")
    print(f"Bid: ₹{quote3.bid_price:.2f} x {quote3.bid_size}")
    print(f"Ask: ₹{quote3.ask_price:.2f} x {quote3.ask_size}")
    print(f"Spread: {quote3.spread_bps:.1f} bps")
    print(f"Note: Quotes skewed DOWN to encourage selling inventory")

    # Calculate final P&L
    print()
    print("=" * 60)
    current_price = fair_value + 0.5
    pnl = mm.calculate_pnl(current_price)

    print(f"FINAL P&L:")
    print(f"Current Price: ₹{pnl['current_price']:.2f}")
    print(f"Inventory: {pnl['inventory']} shares")
    print(f"Avg Cost: ₹{pnl['avg_cost']:.2f}")
    print(f"Unrealized P&L: ₹{pnl['unrealized_pnl']:.2f}")
    print(f"Realized P&L: ₹{pnl['realized_pnl']:.2f}")
    print(f"Total P&L: ₹{pnl['total_pnl']:.2f}")
    print(f"Total Trades: {pnl['total_trades']}")

    # Test Order Flow Analyzer
    print("\n" + "=" * 60)
    print("ORDER FLOW ANALYSIS")
    print("=" * 60)

    flow_analyzer = OrderFlowAnalyzer()

    # Mock order flow data
    buy_volume = pd.Series(np.random.randint(100, 1000, 50))
    sell_volume = pd.Series(np.random.randint(100, 1000, 50))

    imbalance = flow_analyzer.calculate_order_flow_imbalance(buy_volume, sell_volume)
    print(f"Order Flow Imbalance: {imbalance:+.3f}")
    print(f"  Interpretation: {'Buy pressure' if imbalance > 0 else 'Sell pressure'}")

    # Test Volatility Estimator
    print("\n" + "=" * 60)
    print("VOLATILITY ESTIMATION")
    print("=" * 60)

    vol_estimator = VolatilityEstimator()

    # Mock price data
    prices = pd.Series(1000 + np.cumsum(np.random.randn(200) * 5))
    vol = vol_estimator.estimate_realized_volatility(prices)

    print(f"Realized Volatility: {vol:.2%} annualized")

    print("\n" + "=" * 60)
    print("Market making simulation complete!")
    print("=" * 60)
