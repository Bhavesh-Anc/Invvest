"""
Pre-Trade Risk Management and Compliance Module
Institutional-grade risk checks and compliance framework for preventing losses
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskCheckStatus(Enum):
    """Status of risk check"""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WARNING = "WARNING"
    MODIFIED = "MODIFIED"


class ViolationType(Enum):
    """Types of risk violations"""
    POSITION_LIMIT = "POSITION_LIMIT"
    CONCENTRATION = "CONCENTRATION"
    SECTOR_EXPOSURE = "SECTOR_EXPOSURE"
    LEVERAGE = "LEVERAGE"
    NOTIONAL_LIMIT = "NOTIONAL_LIMIT"
    ORDER_VALUE = "ORDER_VALUE"
    DAILY_LOSS = "DAILY_LOSS"
    VAR_LIMIT = "VAR_LIMIT"
    INSIDER_TRADING = "INSIDER_TRADING"
    RESTRICTED_SECURITY = "RESTRICTED_SECURITY"
    WASH_TRADE = "WASH_TRADE"
    CIRCUIT_LIMIT = "CIRCUIT_LIMIT"


class OrderSide(Enum):
    """Order side"""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class RiskLimits:
    """Risk limit configuration"""
    # Position limits
    max_position_value: float = 10_00_00_000  # ₹10 Cr per position
    max_portfolio_value: float = 100_00_00_000  # ₹100 Cr total
    max_single_order_value: float = 1_00_00_000  # ₹1 Cr per order

    # Concentration limits
    max_stock_concentration: float = 0.15  # 15% max in single stock
    max_sector_concentration: float = 0.30  # 30% max in single sector

    # Leverage limits
    max_leverage: float = 3.0  # 3x max leverage
    max_margin_utilization: float = 0.80  # 80% max margin usage

    # Loss limits
    max_daily_loss: float = 50_00_000  # ₹50 L max daily loss
    max_position_loss: float = 10_00_000  # ₹10 L max per position loss
    stop_loss_percentage: float = 0.05  # 5% stop loss

    # Risk metrics limits
    max_portfolio_var_95: float = 0.05  # 5% max daily VaR at 95%
    max_portfolio_volatility: float = 0.25  # 25% max annualized volatility

    # Quantity limits
    max_quantity_per_order: int = 100_000  # Max shares per order
    max_adr_percentage: float = 0.10  # Max 10% of average daily volume

    # Time-based limits
    trading_hours_start: str = "09:15"
    trading_hours_end: str = "15:30"
    allow_pre_market: bool = False
    allow_post_market: bool = False


@dataclass
class OrderRequest:
    """Order request for risk validation"""
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    order_type: str = "LIMIT"
    product_type: str = "MIS"  # MIS, CNC, NRML
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: str = ""
    strategy_id: str = ""

    @property
    def order_value(self) -> float:
        """Calculate order value"""
        return self.quantity * self.price


@dataclass
class RiskCheckResult:
    """Result of risk validation"""
    status: RiskCheckStatus
    violations: List[ViolationType] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    modified_quantity: Optional[int] = None
    modified_price: Optional[float] = None

    @property
    def is_approved(self) -> bool:
        return self.status == RiskCheckStatus.APPROVED

    def add_violation(self, violation_type: ViolationType, message: str):
        """Add a violation"""
        self.violations.append(violation_type)
        self.messages.append(f"VIOLATION: {message}")
        self.status = RiskCheckStatus.REJECTED

    def add_warning(self, message: str):
        """Add a warning"""
        self.warnings.append(message)
        if self.status == RiskCheckStatus.APPROVED:
            self.status = RiskCheckStatus.WARNING


@dataclass
class Position:
    """Current position"""
    symbol: str
    quantity: int  # Positive for long, negative for short
    avg_price: float
    current_price: float
    sector: str = "Unknown"

    @property
    def market_value(self) -> float:
        return abs(self.quantity) * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return self.quantity * (self.current_price - self.avg_price)

    @property
    def pnl_percentage(self) -> float:
        if self.avg_price == 0:
            return 0
        return (self.current_price - self.avg_price) / self.avg_price


class PositionManager:
    """Manages current positions and exposure"""

    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.daily_pnl: float = 0
        self.daily_trades: List[Dict] = []
        self.last_reset: datetime = datetime.now().date()

    def add_position(self, position: Position):
        """Add or update position"""
        self.positions[position.symbol] = position

    def update_position(self, symbol: str, side: OrderSide, quantity: int, price: float):
        """Update position with new trade"""
        if symbol in self.positions:
            pos = self.positions[symbol]
            if side == OrderSide.BUY:
                new_quantity = pos.quantity + quantity
                if new_quantity != 0:
                    pos.avg_price = (pos.quantity * pos.avg_price + quantity * price) / new_quantity
                pos.quantity = new_quantity
            else:  # SELL
                realized_pnl = quantity * (price - pos.avg_price)
                self.daily_pnl += realized_pnl
                pos.quantity -= quantity
                if pos.quantity == 0:
                    del self.positions[symbol]
        else:
            # New position
            qty = quantity if side == OrderSide.BUY else -quantity
            self.positions[symbol] = Position(symbol, qty, price, price)

    def get_total_exposure(self) -> float:
        """Get total portfolio exposure"""
        return sum(pos.market_value for pos in self.positions.values())

    def get_sector_exposure(self) -> Dict[str, float]:
        """Get exposure by sector"""
        sector_exposure = defaultdict(float)
        for pos in self.positions.values():
            sector_exposure[pos.sector] += pos.market_value
        return dict(sector_exposure)

    def get_concentration(self, symbol: str) -> float:
        """Get concentration of a single stock"""
        total_value = self.get_total_exposure()
        if total_value == 0:
            return 0
        if symbol in self.positions:
            return self.positions[symbol].market_value / total_value
        return 0

    def get_unrealized_pnl(self) -> float:
        """Get total unrealized PnL"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    def reset_daily_metrics(self):
        """Reset daily metrics at start of day"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.daily_pnl = 0
            self.daily_trades = []
            self.last_reset = today


class ConcentrationRiskAnalyzer:
    """Analyzes portfolio concentration risk"""

    @staticmethod
    def calculate_herfindahl_index(positions: Dict[str, Position]) -> float:
        """
        Calculate Herfindahl-Hirschman Index for concentration
        Higher values indicate more concentration (0 to 1)
        """
        total_value = sum(pos.market_value for pos in positions.values())
        if total_value == 0:
            return 0

        weights = [pos.market_value / total_value for pos in positions.values()]
        hhi = sum(w ** 2 for w in weights)
        return hhi

    @staticmethod
    def calculate_effective_n(positions: Dict[str, Position]) -> float:
        """
        Calculate effective number of positions
        Higher is better (more diversified)
        """
        hhi = ConcentrationRiskAnalyzer.calculate_herfindahl_index(positions)
        if hhi == 0:
            return 0
        return 1 / hhi

    @staticmethod
    def check_concentration(positions: Dict[str, Position],
                          max_single_stock: float = 0.15,
                          max_sector: float = 0.30) -> Tuple[bool, List[str]]:
        """Check if concentration limits are violated"""
        violations = []
        total_value = sum(pos.market_value for pos in positions.values())

        if total_value == 0:
            return True, []

        # Check single stock concentration
        for symbol, pos in positions.items():
            concentration = pos.market_value / total_value
            if concentration > max_single_stock:
                violations.append(
                    f"Stock {symbol} concentration {concentration:.1%} exceeds limit {max_single_stock:.1%}"
                )

        # Check sector concentration
        sector_exposure = defaultdict(float)
        for pos in positions.values():
            sector_exposure[pos.sector] += pos.market_value

        for sector, exposure in sector_exposure.items():
            concentration = exposure / total_value
            if concentration > max_sector:
                violations.append(
                    f"Sector {sector} concentration {concentration:.1%} exceeds limit {max_sector:.1%}"
                )

        return len(violations) == 0, violations


class ComplianceRule:
    """Base class for compliance rules"""

    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled

    def check(self, order: OrderRequest, context: Dict) -> Tuple[bool, str]:
        """
        Check if order passes this rule
        Returns (passed, message)
        """
        raise NotImplementedError


class RestrictedSecurityRule(ComplianceRule):
    """Check if security is restricted"""

    def __init__(self, restricted_list: List[str] = None):
        super().__init__("Restricted Security Check")
        self.restricted_list = set(restricted_list or [])

    def check(self, order: OrderRequest, context: Dict) -> Tuple[bool, str]:
        if order.symbol in self.restricted_list:
            return False, f"Symbol {order.symbol} is on restricted list"
        return True, ""

    def add_restriction(self, symbol: str, reason: str = ""):
        """Add symbol to restricted list"""
        self.restricted_list.add(symbol)
        logger.info(f"Added {symbol} to restricted list. Reason: {reason}")

    def remove_restriction(self, symbol: str):
        """Remove symbol from restricted list"""
        self.restricted_list.discard(symbol)


class InsiderTradingRule(ComplianceRule):
    """Check for potential insider trading"""

    def __init__(self):
        super().__init__("Insider Trading Check")
        self.blackout_periods: Dict[str, Tuple[datetime, datetime]] = {}
        self.insider_list: Dict[str, List[str]] = {}  # user_id -> list of symbols

    def check(self, order: OrderRequest, context: Dict) -> Tuple[bool, str]:
        # Check blackout period
        if order.symbol in self.blackout_periods:
            start, end = self.blackout_periods[order.symbol]
            if start <= datetime.now() <= end:
                return False, f"Symbol {order.symbol} in blackout period until {end}"

        # Check insider list
        if order.user_id in self.insider_list:
            if order.symbol in self.insider_list[order.user_id]:
                return False, f"User {order.user_id} is insider for {order.symbol}"

        return True, ""

    def add_blackout_period(self, symbol: str, start: datetime, end: datetime):
        """Add blackout period for a symbol"""
        self.blackout_periods[symbol] = (start, end)

    def add_insider(self, user_id: str, symbols: List[str]):
        """Mark user as insider for specific symbols"""
        self.insider_list[user_id] = symbols


class WashTradeRule(ComplianceRule):
    """Detect potential wash trades"""

    def __init__(self, lookback_seconds: int = 30):
        super().__init__("Wash Trade Detection")
        self.lookback_seconds = lookback_seconds
        self.recent_trades: List[Dict] = []

    def check(self, order: OrderRequest, context: Dict) -> Tuple[bool, str]:
        now = datetime.now()

        # Clean old trades
        self.recent_trades = [
            t for t in self.recent_trades
            if (now - t['timestamp']).total_seconds() <= self.lookback_seconds
        ]

        # Check for opposite side trade in same symbol within lookback period
        for trade in self.recent_trades:
            if (trade['symbol'] == order.symbol and
                trade['user_id'] == order.user_id and
                trade['side'] != order.side):

                time_diff = (now - trade['timestamp']).total_seconds()
                return False, f"Potential wash trade: opposite trade {time_diff:.0f}s ago"

        # Record this order
        self.recent_trades.append({
            'symbol': order.symbol,
            'user_id': order.user_id,
            'side': order.side,
            'timestamp': now
        })

        return True, ""


class CircuitLimitRule(ComplianceRule):
    """Check if stock has hit circuit limits"""

    def __init__(self):
        super().__init__("Circuit Limit Check")
        self.circuit_stocks: Dict[str, Dict] = {}

    def check(self, order: OrderRequest, context: Dict) -> Tuple[bool, str]:
        if order.symbol in self.circuit_stocks:
            circuit_info = self.circuit_stocks[order.symbol]
            if circuit_info['side'] == order.side.value:
                return False, f"Stock {order.symbol} hit {circuit_info['type']} circuit on {order.side.value} side"
        return True, ""

    def update_circuit(self, symbol: str, side: str, circuit_type: str):
        """Update circuit information"""
        self.circuit_stocks[symbol] = {
            'side': side,
            'type': circuit_type,  # 'UPPER' or 'LOWER'
            'timestamp': datetime.now()
        }


class RiskChecker:
    """Main risk checking engine"""

    def __init__(self, limits: RiskLimits = None):
        self.limits = limits or RiskLimits()
        self.position_manager = PositionManager()
        self.compliance_rules: List[ComplianceRule] = []

        # Add default compliance rules
        self.restricted_rule = RestrictedSecurityRule()
        self.insider_rule = InsiderTradingRule()
        self.wash_trade_rule = WashTradeRule()
        self.circuit_rule = CircuitLimitRule()

        self.compliance_rules.extend([
            self.restricted_rule,
            self.insider_rule,
            self.wash_trade_rule,
            self.circuit_rule
        ])

        logger.info("RiskChecker initialized with default limits")

    def validate_order(self, order: OrderRequest) -> RiskCheckResult:
        """
        Validate order against all risk checks
        Returns RiskCheckResult
        """
        result = RiskCheckResult(status=RiskCheckStatus.APPROVED)

        # Reset daily metrics if needed
        self.position_manager.reset_daily_metrics()

        # 1. Basic order validation
        if order.quantity <= 0:
            result.add_violation(ViolationType.ORDER_VALUE, "Order quantity must be positive")
            return result

        if order.price <= 0:
            result.add_violation(ViolationType.ORDER_VALUE, "Order price must be positive")
            return result

        # 2. Trading hours check
        if not self._check_trading_hours(order, result):
            return result

        # 3. Order value check
        if order.order_value > self.limits.max_single_order_value:
            result.add_violation(
                ViolationType.ORDER_VALUE,
                f"Order value ₹{order.order_value:,.0f} exceeds limit ₹{self.limits.max_single_order_value:,.0f}"
            )

        # 4. Quantity limit check
        if order.quantity > self.limits.max_quantity_per_order:
            result.add_violation(
                ViolationType.ORDER_VALUE,
                f"Order quantity {order.quantity:,} exceeds limit {self.limits.max_quantity_per_order:,}"
            )

        # 5. Position limit check
        if not self._check_position_limits(order, result):
            return result

        # 6. Concentration check
        if not self._check_concentration(order, result):
            return result

        # 7. Leverage check
        if not self._check_leverage(order, result):
            return result

        # 8. Loss limit check
        if not self._check_loss_limits(order, result):
            return result

        # 9. Compliance rules check
        if not self._check_compliance_rules(order, result):
            return result

        # 10. Risk metrics check
        self._check_risk_metrics(order, result)

        logger.info(f"Risk check completed for {order.symbol}: {result.status.value}")
        return result

    def _check_trading_hours(self, order: OrderRequest, result: RiskCheckResult) -> bool:
        """Check if order is within trading hours"""
        current_time = order.timestamp.time()
        start_time = datetime.strptime(self.limits.trading_hours_start, "%H:%M").time()
        end_time = datetime.strptime(self.limits.trading_hours_end, "%H:%M").time()

        if not (start_time <= current_time <= end_time):
            result.add_warning(
                f"Order outside regular trading hours ({self.limits.trading_hours_start}-{self.limits.trading_hours_end})"
            )

        return True

    def _check_position_limits(self, order: OrderRequest, result: RiskCheckResult) -> bool:
        """Check position limits"""
        # Calculate post-trade position value
        current_pos = self.position_manager.positions.get(order.symbol)
        if current_pos:
            if order.side == OrderSide.BUY:
                new_quantity = current_pos.quantity + order.quantity
            else:
                new_quantity = current_pos.quantity - order.quantity
            position_value = abs(new_quantity) * order.price
        else:
            position_value = order.quantity * order.price

        if position_value > self.limits.max_position_value:
            result.add_violation(
                ViolationType.POSITION_LIMIT,
                f"Position value ₹{position_value:,.0f} exceeds limit ₹{self.limits.max_position_value:,.0f}"
            )
            return False

        # Check total portfolio value
        total_exposure = self.position_manager.get_total_exposure()
        if order.side == OrderSide.BUY:
            new_total = total_exposure + order.order_value
        else:
            new_total = total_exposure  # Selling doesn't increase exposure

        if new_total > self.limits.max_portfolio_value:
            result.add_violation(
                ViolationType.NOTIONAL_LIMIT,
                f"Portfolio value ₹{new_total:,.0f} exceeds limit ₹{self.limits.max_portfolio_value:,.0f}"
            )
            return False

        return True

    def _check_concentration(self, order: OrderRequest, result: RiskCheckResult) -> bool:
        """Check concentration limits"""
        # Simulate post-trade position
        temp_positions = self.position_manager.positions.copy()

        if order.symbol in temp_positions:
            pos = temp_positions[order.symbol]
            if order.side == OrderSide.BUY:
                new_qty = pos.quantity + order.quantity
                new_avg_price = (pos.quantity * pos.avg_price + order.quantity * order.price) / new_qty
                pos.quantity = new_qty
                pos.avg_price = new_avg_price
            else:
                pos.quantity -= order.quantity
        else:
            qty = order.quantity if order.side == OrderSide.BUY else -order.quantity
            temp_positions[order.symbol] = Position(
                order.symbol, qty, order.price, order.price
            )

        # Check concentration
        passed, violations = ConcentrationRiskAnalyzer.check_concentration(
            temp_positions,
            self.limits.max_stock_concentration,
            self.limits.max_sector_concentration
        )

        if not passed:
            for violation in violations:
                result.add_violation(ViolationType.CONCENTRATION, violation)
            return False

        return True

    def _check_leverage(self, order: OrderRequest, result: RiskCheckResult) -> bool:
        """Check leverage limits"""
        # This is a simplified check - real implementation would calculate actual leverage
        # based on margin requirements and available capital

        if order.product_type == "MIS":  # Intraday has higher leverage
            result.add_warning("Intraday order - ensure adequate margin available")

        return True

    def _check_loss_limits(self, order: OrderRequest, result: RiskCheckResult) -> bool:
        """Check loss limits"""
        # Check daily loss
        total_daily_loss = self.position_manager.daily_pnl + self.position_manager.get_unrealized_pnl()

        if abs(total_daily_loss) > self.limits.max_daily_loss:
            result.add_violation(
                ViolationType.DAILY_LOSS,
                f"Daily loss ₹{abs(total_daily_loss):,.0f} exceeds limit ₹{self.limits.max_daily_loss:,.0f}"
            )
            return False

        # Check position-level stop loss
        if order.symbol in self.position_manager.positions:
            pos = self.position_manager.positions[order.symbol]
            if pos.unrealized_pnl < -self.limits.max_position_loss:
                result.add_warning(
                    f"Position loss ₹{abs(pos.unrealized_pnl):,.0f} approaching limit ₹{self.limits.max_position_loss:,.0f}"
                )

        return True

    def _check_compliance_rules(self, order: OrderRequest, result: RiskCheckResult) -> bool:
        """Check all compliance rules"""
        context = {
            'positions': self.position_manager.positions,
            'daily_pnl': self.position_manager.daily_pnl
        }

        for rule in self.compliance_rules:
            if not rule.enabled:
                continue

            passed, message = rule.check(order, context)
            if not passed:
                if "wash trade" in message.lower():
                    result.add_violation(ViolationType.WASH_TRADE, message)
                elif "insider" in message.lower():
                    result.add_violation(ViolationType.INSIDER_TRADING, message)
                elif "restricted" in message.lower():
                    result.add_violation(ViolationType.RESTRICTED_SECURITY, message)
                elif "circuit" in message.lower():
                    result.add_violation(ViolationType.CIRCUIT_LIMIT, message)
                else:
                    result.messages.append(f"Compliance violation: {message}")
                    result.status = RiskCheckStatus.REJECTED
                return False

        return True

    def _check_risk_metrics(self, order: OrderRequest, result: RiskCheckResult):
        """Check portfolio risk metrics (VaR, volatility, etc.)"""
        # This is a simplified version - real implementation would calculate
        # actual VaR and other risk metrics

        hhi = ConcentrationRiskAnalyzer.calculate_herfindahl_index(
            self.position_manager.positions
        )

        if hhi > 0.25:  # High concentration
            result.add_warning(f"High portfolio concentration (HHI: {hhi:.2f})")

        effective_n = ConcentrationRiskAnalyzer.calculate_effective_n(
            self.position_manager.positions
        )

        if effective_n < 5:
            result.add_warning(f"Low diversification (Effective N: {effective_n:.1f})")

    def add_compliance_rule(self, rule: ComplianceRule):
        """Add custom compliance rule"""
        self.compliance_rules.append(rule)
        logger.info(f"Added compliance rule: {rule.name}")


class ComplianceEngine:
    """
    Compliance and audit trail manager
    Tracks all orders, violations, and compliance events
    """

    def __init__(self, db_path: str = "compliance.db"):
        self.db_path = db_path
        self.audit_trail: List[Dict] = []
        self.violation_history: List[Dict] = []
        self._init_database()

    def _init_database(self):
        """Initialize compliance database"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                symbol TEXT,
                side TEXT,
                quantity INTEGER,
                price REAL,
                order_value REAL,
                status TEXT,
                violations TEXT,
                warnings TEXT,
                messages TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS violation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                symbol TEXT,
                violation_type TEXT,
                message TEXT,
                severity TEXT
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Compliance database initialized at {self.db_path}")

    def log_order_check(self, order: OrderRequest, result: RiskCheckResult):
        """Log order risk check to audit trail"""
        import sqlite3

        audit_record = {
            'timestamp': order.timestamp.isoformat(),
            'user_id': order.user_id,
            'symbol': order.symbol,
            'side': order.side.value,
            'quantity': order.quantity,
            'price': order.price,
            'order_value': order.order_value,
            'status': result.status.value,
            'violations': ','.join([v.value for v in result.violations]),
            'warnings': ','.join(result.warnings),
            'messages': ','.join(result.messages)
        }

        self.audit_trail.append(audit_record)

        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_trail
            (timestamp, user_id, symbol, side, quantity, price, order_value,
             status, violations, warnings, messages)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            audit_record['timestamp'], audit_record['user_id'], audit_record['symbol'],
            audit_record['side'], audit_record['quantity'], audit_record['price'],
            audit_record['order_value'], audit_record['status'],
            audit_record['violations'], audit_record['warnings'], audit_record['messages']
        ))
        conn.commit()
        conn.close()

        # Log violations separately
        if result.violations:
            for violation in result.violations:
                self.log_violation(order, violation, "HIGH")

    def log_violation(self, order: OrderRequest, violation_type: ViolationType, severity: str = "MEDIUM"):
        """Log compliance violation"""
        import sqlite3

        violation_record = {
            'timestamp': datetime.now().isoformat(),
            'user_id': order.user_id,
            'symbol': order.symbol,
            'violation_type': violation_type.value,
            'message': f"{violation_type.value} violation for {order.symbol}",
            'severity': severity
        }

        self.violation_history.append(violation_record)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO violation_history
            (timestamp, user_id, symbol, violation_type, message, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            violation_record['timestamp'], violation_record['user_id'],
            violation_record['symbol'], violation_record['violation_type'],
            violation_record['message'], violation_record['severity']
        ))
        conn.commit()
        conn.close()

    def get_violation_summary(self, days: int = 30) -> pd.DataFrame:
        """Get violation summary for last N days"""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        query = """
            SELECT
                violation_type,
                COUNT(*) as count,
                severity
            FROM violation_history
            WHERE timestamp >= ?
            GROUP BY violation_type, severity
            ORDER BY count DESC
        """

        df = pd.read_sql_query(query, conn, params=(cutoff_date,))
        conn.close()

        return df

    def get_user_compliance_score(self, user_id: str, days: int = 90) -> Dict:
        """Calculate compliance score for a user"""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Get total orders
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM audit_trail
            WHERE user_id = ? AND timestamp >= ?
        """, (user_id, cutoff_date))
        total_orders = cursor.fetchone()[0]

        # Get violations
        cursor.execute("""
            SELECT COUNT(*) FROM violation_history
            WHERE user_id = ? AND timestamp >= ?
        """, (user_id, cutoff_date))
        total_violations = cursor.fetchone()[0]

        conn.close()

        if total_orders == 0:
            compliance_score = 100
        else:
            compliance_score = max(0, 100 - (total_violations / total_orders * 100))

        return {
            'user_id': user_id,
            'period_days': days,
            'total_orders': total_orders,
            'total_violations': total_violations,
            'compliance_score': round(compliance_score, 2),
            'rating': 'EXCELLENT' if compliance_score >= 95 else 'GOOD' if compliance_score >= 85 else 'NEEDS_IMPROVEMENT'
        }


# Example usage
if __name__ == "__main__":
    # Initialize risk checker
    limits = RiskLimits(
        max_position_value=50_00_000,  # ₹50L per position
        max_single_order_value=10_00_000,  # ₹10L per order
        max_stock_concentration=0.20,  # 20% max
        max_daily_loss=20_00_000  # ₹20L max loss
    )

    risk_checker = RiskChecker(limits)
    compliance_engine = ComplianceEngine()

    # Add some positions
    risk_checker.position_manager.add_position(
        Position("RELIANCE", 100, 2500, 2550, "Energy")
    )
    risk_checker.position_manager.add_position(
        Position("TCS", 50, 3500, 3600, "IT")
    )

    # Create test order
    order = OrderRequest(
        symbol="INFY",
        side=OrderSide.BUY,
        quantity=500,
        price=1500,
        user_id="trader_001",
        strategy_id="momentum_v1"
    )

    # Validate order
    result = risk_checker.validate_order(order)

    print(f"\nRisk Check Result: {result.status.value}")
    print(f"Approved: {result.is_approved}")

    if result.violations:
        print("\nViolations:")
        for violation in result.violations:
            print(f"  - {violation.value}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    if result.messages:
        print("\nMessages:")
        for message in result.messages:
            print(f"  - {message}")

    # Log to compliance
    compliance_engine.log_order_check(order, result)

    # Test restricted security
    risk_checker.restricted_rule.add_restriction("ADANIPORTS", "Under investigation")

    restricted_order = OrderRequest(
        symbol="ADANIPORTS",
        side=OrderSide.BUY,
        quantity=100,
        price=750,
        user_id="trader_001"
    )

    result2 = risk_checker.validate_order(restricted_order)
    print(f"\n\nRestricted Security Check: {result2.status.value}")
    print(f"Messages: {result2.messages}")

    # Get compliance score
    score = compliance_engine.get_user_compliance_score("trader_001")
    print(f"\n\nCompliance Score for trader_001:")
    print(f"  Score: {score['compliance_score']}")
    print(f"  Rating: {score['rating']}")
    print(f"  Total Orders: {score['total_orders']}")
    print(f"  Violations: {score['total_violations']}")
