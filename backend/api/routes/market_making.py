"""
Market Making API
Provides live quoting, inventory management, P&L tracking, and order flow analysis
Includes WebSocket support for real-time quote streaming
"""

from fastapi import APIRouter, HTTPException, Query, Body, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import json
import asyncio

# Import strategy modules
import sys
sys.path.append('../..')
from strategies.market_making import (
    MarketMaker,
    OrderFlowAnalyzer,
    VolatilityEstimator,
    InventoryManager,
    Quote,
    QuoteSide
)
from utils.indian_market import IndianMarketData

router = APIRouter()

# Active market makers (keyed by symbol)
active_market_makers: Dict[str, MarketMaker] = {}

# WebSocket connections for quote streaming
active_connections: List[WebSocket] = []

# Request/Response models
class QuoteGenerationRequest(BaseModel):
    symbol: str
    fair_value: float
    volatility: float
    order_flow_imbalance: float = 0.0

class FillRequest(BaseModel):
    symbol: str
    side: str  # bid or ask
    quantity: int
    price: float

class InventoryCheckRequest(BaseModel):
    current_position: int
    proposed_trade_size: int
    side: str  # bid or ask

class OrderFlowRequest(BaseModel):
    buy_volume: List[float]
    sell_volume: List[float]
    lookback: int = 20

class AdverseSelectionRequest(BaseModel):
    prices: List[float]
    trade_directions: List[int]  # 1 for buy, -1 for sell

class QuoteResponse(BaseModel):
    symbol: str
    bid_price: float
    bid_size: int
    ask_price: float
    ask_size: int
    mid_price: float
    spread: float
    spread_bps: float
    timestamp: datetime

class PnLResponse(BaseModel):
    symbol: str
    inventory: int
    avg_cost: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    total_trades: int


# Helper function to get or create market maker
def get_market_maker(symbol: str) -> MarketMaker:
    """Get existing market maker or create new one"""
    if symbol not in active_market_makers:
        active_market_makers[symbol] = MarketMaker(
            base_spread_bps=10,
            quote_size=100,
            max_inventory=5000,
            risk_aversion=0.01
        )
    return active_market_makers[symbol]


# Quote Generation Endpoints

@router.post("/quotes/generate", response_model=QuoteResponse)
async def generate_market_quotes(request: QuoteGenerationRequest):
    """
    Generate bid and ask quotes for market making

    Automatically adjusts:
    - Spread based on volatility and order flow
    - Quote skew based on inventory position
    - Quote sizes based on inventory limits
    """
    try:
        mm = get_market_maker(request.symbol)

        # Generate quotes
        quote = mm.generate_quotes(
            symbol=request.symbol,
            fair_value=request.fair_value,
            volatility=request.volatility,
            order_flow_imbalance=request.order_flow_imbalance
        )

        return {
            'symbol': quote.symbol,
            'bid_price': quote.bid_price,
            'bid_size': quote.bid_size,
            'ask_price': quote.ask_price,
            'ask_size': quote.ask_size,
            'mid_price': quote.mid_price,
            'spread': quote.spread,
            'spread_bps': quote.spread_bps,
            'timestamp': quote.timestamp
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quotes/spread-analysis")
async def analyze_spread(
    symbol: str = Query(...),
    volatility: float = Query(...),
    inventory_pct: float = Query(0.0, description="Inventory as % of max (-1 to 1)")
):
    """
    Analyze optimal spread calculation

    Shows how spread adjusts based on:
    - Market volatility
    - Order flow imbalance
    - Inventory position
    """
    try:
        mm = get_market_maker(symbol)

        # Calculate optimal spread
        order_flow_imbalance = 0.0  # Neutral for analysis

        optimal_spread = mm.calculate_optimal_spread(
            volatility=volatility,
            order_flow_imbalance=order_flow_imbalance,
            inventory_pct=inventory_pct
        )

        # Calculate inventory skew
        skew = mm.calculate_inventory_skew(inventory_pct)

        return {
            'symbol': symbol,
            'optimal_spread_bps': round(optimal_spread, 2),
            'base_spread_bps': mm.base_spread_bps,
            'volatility_multiplier': round(1 + (volatility / 0.01), 2),
            'inventory_skew_bps': round(skew, 2),
            'inventory_pct': inventory_pct,
            'explanation': {
                'spread': f"Optimal spread: {optimal_spread:.1f} bps",
                'skew': f"Inventory skew: {skew:+.1f} bps ({'lower quotes' if skew < 0 else 'higher quotes'})"
            },
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Inventory Management Endpoints

@router.get("/inventory/position")
async def get_inventory_position(symbol: str = Query(...)):
    """
    Get current inventory position for a symbol

    Returns:
    - Current quantity
    - Average cost
    - Unrealized P&L
    - Position limits
    """
    try:
        mm = get_market_maker(symbol)
        market_data = IndianMarketData()

        # Get current price
        quote = market_data.get_live_quote(symbol)
        current_price = quote['ltp']

        # Calculate P&L
        pnl = mm.calculate_pnl(current_price)

        # Position metrics
        inventory_pct = (mm.inventory / mm.max_inventory * 100) if mm.max_inventory > 0 else 0

        return {
            'symbol': symbol,
            'inventory': mm.inventory,
            'avg_cost': mm.avg_cost,
            'current_price': current_price,
            'unrealized_pnl': pnl['unrealized_pnl'],
            'realized_pnl': pnl['realized_pnl'],
            'total_pnl': pnl['total_pnl'],
            'total_trades': pnl['total_trades'],
            'max_inventory': mm.max_inventory,
            'inventory_pct': round(inventory_pct, 2),
            'remaining_capacity': mm.max_inventory - abs(mm.inventory),
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inventory/check-limit")
async def check_inventory_limit(
    symbol: str = Body(...),
    request: InventoryCheckRequest = Body(...)
):
    """
    Check if proposed trade violates position limits

    Prevents excessive inventory buildup
    """
    try:
        mm = get_market_maker(symbol)
        inventory_mgr = InventoryManager(
            max_position=mm.max_inventory,
            max_position_value=10000000
        )

        side = QuoteSide.BID if request.side.lower() == 'bid' else QuoteSide.ASK

        result = inventory_mgr.check_position_limit(
            current_position=request.current_position,
            proposed_trade_size=request.proposed_trade_size,
            side=side
        )

        return {
            'symbol': symbol,
            **result,
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/urgency")
async def calculate_inventory_urgency(
    symbol: str = Query(...),
    current_position: int = Query(...),
    target_position: int = Query(0)
):
    """
    Calculate urgency to flatten inventory

    Higher urgency → need to reduce position quickly
    """
    try:
        mm = get_market_maker(symbol)
        inventory_mgr = InventoryManager(
            max_position=mm.max_inventory,
            max_position_value=10000000
        )

        urgency = inventory_mgr.calculate_inventory_urgency(
            current_position=current_position,
            target_position=target_position
        )

        if urgency > 0.8:
            priority = 'CRITICAL'
            action = 'Aggressively flatten position'
        elif urgency > 0.5:
            priority = 'HIGH'
            action = 'Increase quote sizes on exit side'
        elif urgency > 0.2:
            priority = 'MEDIUM'
            action = 'Skew quotes toward flattening'
        else:
            priority = 'LOW'
            action = 'Normal operations'

        return {
            'symbol': symbol,
            'urgency_score': round(urgency, 3),
            'priority': priority,
            'recommended_action': action,
            'current_position': current_position,
            'target_position': target_position,
            'position_deviation': abs(current_position - target_position),
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Order Flow Analysis Endpoints

@router.post("/flow/imbalance")
async def calculate_order_flow_imbalance(request: OrderFlowRequest):
    """
    Calculate order flow imbalance from buy/sell volumes

    Returns:
    - Imbalance score (-1 to 1)
    - Interpretation (buy/sell pressure)
    """
    try:
        import pandas as pd

        flow_analyzer = OrderFlowAnalyzer(lookback_periods=request.lookback)

        buy_volume = pd.Series(request.buy_volume)
        sell_volume = pd.Series(request.sell_volume)

        imbalance = flow_analyzer.calculate_order_flow_imbalance(buy_volume, sell_volume)

        if imbalance > 0.2:
            interpretation = 'Strong buy pressure'
            action = 'Widen ask spread, tighten bid'
        elif imbalance < -0.2:
            interpretation = 'Strong sell pressure'
            action = 'Widen bid spread, tighten ask'
        else:
            interpretation = 'Balanced flow'
            action = 'Normal spreads'

        return {
            'imbalance': round(imbalance, 3),
            'interpretation': interpretation,
            'recommended_action': action,
            'buy_volume_sum': sum(request.buy_volume[-request.lookback:]),
            'sell_volume_sum': sum(request.sell_volume[-request.lookback:]),
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flow/adverse-selection")
async def detect_adverse_selection(request: AdverseSelectionRequest):
    """
    Detect adverse selection (informed trading)

    If price moves against us after providing liquidity,
    we're suffering from adverse selection → widen spreads
    """
    try:
        import pandas as pd

        flow_analyzer = OrderFlowAnalyzer()

        prices = pd.Series(request.prices)
        trade_directions = pd.Series(request.trade_directions)

        result = flow_analyzer.detect_adverse_selection(prices, trade_directions)

        if result['is_high']:
            recommendation = 'WIDEN SPREADS - High adverse selection detected'
        else:
            recommendation = 'Normal operations - Acceptable adverse selection rate'

        return {
            **result,
            'recommendation': recommendation,
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Fill Processing & P&L Endpoints

@router.post("/process-fill")
async def process_trade_fill(request: FillRequest):
    """
    Process a trade fill (execution)

    Updates:
    - Inventory position
    - Average cost
    - Realized P&L
    """
    try:
        mm = get_market_maker(request.symbol)

        side = QuoteSide.BID if request.side.lower() == 'bid' else QuoteSide.ASK

        fill_result = mm.process_fill(
            side=side,
            quantity=request.quantity,
            price=request.price
        )

        return {
            'symbol': request.symbol,
            **fill_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pnl", response_model=PnLResponse)
async def get_pnl(
    symbol: str = Query(...),
    current_price: Optional[float] = Query(None)
):
    """
    Get comprehensive P&L for a symbol

    Returns:
    - Realized P&L (from closed trades)
    - Unrealized P&L (mark-to-market)
    - Total P&L
    - Trade count
    """
    try:
        mm = get_market_maker(symbol)
        market_data = IndianMarketData()

        # Get current price
        if current_price is None:
            quote = market_data.get_live_quote(symbol)
            current_price = quote['ltp']

        pnl = mm.calculate_pnl(current_price)

        return {
            'symbol': symbol,
            **pnl
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Volatility Estimation Endpoints

@router.get("/volatility/estimate")
async def estimate_volatility(
    symbol: str = Query(...),
    lookback_days: int = Query(30)
):
    """
    Estimate real-time volatility for spread adjustment

    Uses recent price history to calculate volatility
    """
    try:
        from datetime import timedelta
        import pandas as pd

        market_data = IndianMarketData()
        vol_estimator = VolatilityEstimator(window=100)

        # Fetch historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        df = market_data.get_historical_data(symbol, start_date, end_date)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        prices = df.set_index('date')['close']

        # Estimate volatility
        volatility = vol_estimator.estimate_realized_volatility(prices, frequency='1min')

        return {
            'symbol': symbol,
            'volatility': round(volatility, 4),
            'volatility_pct': round(volatility * 100, 2),
            'lookback_days': lookback_days,
            'data_points': len(prices),
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket for Real-Time Quote Streaming

@router.websocket("/ws/quotes/{symbol}")
async def websocket_quotes(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for real-time quote streaming

    Streams live bid/ask quotes with inventory-adjusted pricing
    """
    await websocket.accept()
    active_connections.append(websocket)

    try:
        mm = get_market_maker(symbol)
        market_data = IndianMarketData()

        while True:
            # Get current market data
            quote_data = market_data.get_live_quote(symbol)
            fair_value = quote_data['ltp']

            # Mock volatility and flow (in production, calculate real-time)
            volatility = 0.02
            order_flow_imbalance = 0.0

            # Generate quotes
            quote = mm.generate_quotes(symbol, fair_value, volatility, order_flow_imbalance)

            # Send to client
            await websocket.send_json({
                'symbol': symbol,
                'bid_price': quote.bid_price,
                'bid_size': quote.bid_size,
                'ask_price': quote.ask_price,
                'ask_size': quote.ask_size,
                'mid_price': quote.mid_price,
                'spread_bps': quote.spread_bps,
                'inventory': mm.inventory,
                'timestamp': quote.timestamp.isoformat()
            })

            # Update every 1 second
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        active_connections.remove(websocket)
        print(f"WebSocket error: {e}")


# Reset endpoint for testing

@router.post("/reset/{symbol}")
async def reset_market_maker(symbol: str):
    """
    Reset market maker state for a symbol

    Useful for testing and starting fresh
    """
    try:
        if symbol in active_market_makers:
            del active_market_makers[symbol]

        return {
            'symbol': symbol,
            'status': 'reset',
            'message': 'Market maker state cleared',
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
