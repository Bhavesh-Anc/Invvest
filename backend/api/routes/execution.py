"""
Optimal Execution Algorithms API
Provides VWAP, TWAP, market impact modeling, and smart order routing
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, time
from pydantic import BaseModel
import pandas as pd
import numpy as np

# Import strategy modules
import sys
sys.path.append('../..')
from strategies.optimal_execution import (
    VWAPAlgorithm,
    TWAPAlgorithm,
    MarketImpactModel,
    AdaptiveExecutionAlgorithm,
    SmartOrderRouter,
    Order,
    Fill,
    OrderType,
    OrderSide
)
from utils.indian_market import IndianMarketData

router = APIRouter()

# Request/Response models
class VWAPScheduleRequest(BaseModel):
    symbol: str
    total_quantity: int
    start_time: Optional[str] = None  # HH:MM format
    end_time: Optional[str] = None
    participation_rate: float = 0.10

class TWAPScheduleRequest(BaseModel):
    symbol: str
    total_quantity: int
    num_intervals: int = 12
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    randomize: bool = True

class MarketImpactRequest(BaseModel):
    quantity: int
    adv: float  # Average Daily Volume
    price: float
    execution_time: float = 0.5  # Fraction of day

class OrderRouteRequest(BaseModel):
    symbol: str
    side: str  # buy or sell
    quantity: int
    price: float
    venue_liquidity: Dict[str, int]  # {venue: available_quantity}

class ScheduleItem(BaseModel):
    interval: int
    execution_time: datetime
    quantity: int
    volume_pct: Optional[float] = None
    cumulative_quantity: int

class ImpactResult(BaseModel):
    permanent_impact: float
    temporary_impact: float
    total_impact: float
    total_cost: float
    impact_bps: float


# VWAP Endpoints

@router.post("/vwap/schedule")
async def generate_vwap_schedule(request: VWAPScheduleRequest):
    """
    Generate VWAP execution schedule

    Distributes order across time based on historical volume profile
    Minimizes market impact by trading with natural volume
    """
    try:
        vwap = VWAPAlgorithm(participation_rate=request.participation_rate)
        market_data = IndianMarketData()

        # Default to market hours if not specified
        if request.start_time is None:
            start_time = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
        else:
            h, m = map(int, request.start_time.split(':'))
            start_time = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)

        if request.end_time is None:
            end_time = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
        else:
            h, m = map(int, request.end_time.split(':'))
            end_time = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)

        # Mock volume profile (typical NSE intraday pattern)
        # In production, fetch actual historical volume profile
        volume_profile = pd.Series({
            0: 0.08,   # 9:15-9:45 (opening surge)
            1: 0.06,   # 9:45-10:15
            2: 0.05,   # 10:15-10:45
            3: 0.05,   # 10:45-11:15
            4: 0.05,   # 11:15-11:45
            5: 0.05,   # 11:45-12:15
            6: 0.06,   # 12:15-12:45
            7: 0.07,   # 12:45-13:15
            8: 0.09,   # 13:15-13:45
            9: 0.11,   # 13:45-14:15
            10: 0.14,  # 14:15-14:45
            11: 0.19   # 14:45-15:15 (closing surge)
        })

        # Generate schedule
        schedule = vwap.generate_execution_schedule(
            total_quantity=request.total_quantity,
            volume_profile=volume_profile,
            start_time=start_time,
            end_time=end_time
        )

        return {
            'symbol': request.symbol,
            'total_quantity': request.total_quantity,
            'participation_rate': request.participation_rate,
            'num_intervals': len(schedule),
            'start_time': start_time,
            'end_time': end_time,
            'schedule': schedule,
            'strategy': 'VWAP',
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vwap/evaluate")
async def evaluate_vwap_execution(
    fills: List[Dict] = Body(..., description="List of fills with quantity and price"),
    vwap_benchmark: float = Body(..., description="Market VWAP benchmark")
):
    """
    Evaluate VWAP execution performance

    Compares execution price vs VWAP benchmark
    Calculates slippage and cost metrics
    """
    try:
        vwap_algo = VWAPAlgorithm()

        # Convert to Fill objects
        fill_objects = []
        for f in fills:
            order = Order(
                symbol=f.get('symbol', 'UNKNOWN'),
                side=OrderSide.BUY if f.get('side') == 'buy' else OrderSide.SELL,
                quantity=f['quantity'],
                order_type=OrderType.MARKET
            )
            fill = Fill(
                order=order,
                filled_quantity=f['quantity'],
                fill_price=f['price'],
                timestamp=datetime.now(),
                commission=f.get('commission', 0)
            )
            fill_objects.append(fill)

        # Evaluate
        metrics = vwap_algo.evaluate_execution(fill_objects, vwap_benchmark)

        return {
            **metrics,
            'benchmark_type': 'VWAP',
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# TWAP Endpoints

@router.post("/twap/schedule")
async def generate_twap_schedule(request: TWAPScheduleRequest):
    """
    Generate TWAP execution schedule

    Distributes order evenly across time intervals
    Optional randomization to avoid detection
    """
    try:
        twap = TWAPAlgorithm(randomize=request.randomize)

        # Default times
        if request.start_time is None:
            start_time = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
        else:
            h, m = map(int, request.start_time.split(':'))
            start_time = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)

        if request.end_time is None:
            end_time = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
        else:
            h, m = map(int, request.end_time.split(':'))
            end_time = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)

        # Generate schedule
        schedule = twap.generate_execution_schedule(
            total_quantity=request.total_quantity,
            num_intervals=request.num_intervals,
            start_time=start_time,
            end_time=end_time
        )

        return {
            'symbol': request.symbol,
            'total_quantity': request.total_quantity,
            'num_intervals': request.num_intervals,
            'randomized': request.randomize,
            'start_time': start_time,
            'end_time': end_time,
            'schedule': schedule,
            'strategy': 'TWAP',
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/twap/evaluate")
async def evaluate_twap_execution(
    fills: List[Dict] = Body(...),
    start_price: float = Body(...),
    end_price: float = Body(...)
):
    """
    Evaluate TWAP execution performance

    Compares execution vs midpoint of start and end prices
    """
    try:
        twap_algo = TWAPAlgorithm()

        # Convert fills
        fill_objects = []
        for f in fills:
            order = Order(
                symbol=f.get('symbol', 'UNKNOWN'),
                side=OrderSide.BUY if f.get('side') == 'buy' else OrderSide.SELL,
                quantity=f['quantity'],
                order_type=OrderType.MARKET
            )
            fill = Fill(
                order=order,
                filled_quantity=f['quantity'],
                fill_price=f['price'],
                timestamp=datetime.now()
            )
            fill_objects.append(fill)

        # Evaluate
        metrics = twap_algo.evaluate_execution(fill_objects, start_price, end_price)

        return {
            **metrics,
            'benchmark_type': 'TWAP',
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Market Impact Endpoints

@router.post("/impact/calculate", response_model=ImpactResult)
async def calculate_market_impact(request: MarketImpactRequest):
    """
    Calculate market impact using Almgren-Chriss model

    Returns:
    - Permanent impact (information leakage)
    - Temporary impact (price pressure)
    - Total cost in bps and absolute
    """
    try:
        impact_model = MarketImpactModel()

        result = impact_model.calculate_total_impact(
            quantity=request.quantity,
            adv=request.adv,
            price=request.price,
            execution_time=request.execution_time
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/impact/optimize-time")
async def optimize_execution_time(
    quantity: int = Body(...),
    adv: float = Body(..., description="Average Daily Volume"),
    price: float = Body(...),
    max_time: float = Body(1.0, description="Maximum execution time (fraction of day)")
):
    """
    Optimize execution time to minimize total cost

    Balances market impact vs risk from delayed execution
    """
    try:
        impact_model = MarketImpactModel()

        optimal_time = impact_model.optimize_execution_time(
            quantity=quantity,
            adv=adv,
            price=price,
            max_time=max_time
        )

        # Calculate costs at optimal time
        impact = impact_model.calculate_total_impact(quantity, adv, price, optimal_time)

        return {
            'optimal_execution_time_days': round(optimal_time, 4),
            'optimal_execution_time_hours': round(optimal_time * 6.25, 2),  # NSE hours
            'total_impact_bps': impact['impact_bps'],
            'total_cost': impact['total_cost'],
            'explanation': f"Execute over {optimal_time*6.25:.1f} hours to minimize total cost",
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Smart Order Routing Endpoints

@router.post("/route")
async def route_order(request: OrderRouteRequest):
    """
    Smart order routing across NSE/BSE

    Optimizes routing based on:
    - Available liquidity at each venue
    - Transaction costs
    - Expected market impact
    """
    try:
        router = SmartOrderRouter()

        # Create order
        order = Order(
            symbol=request.symbol,
            side=OrderSide.BUY if request.side.lower() == 'buy' else OrderSide.SELL,
            quantity=request.quantity,
            order_type=OrderType.LIMIT,
            price=request.price
        )

        # Route order
        routing = router.route_order(order, request.venue_liquidity)

        return {
            'symbol': request.symbol,
            'total_quantity': request.quantity,
            'routing': routing,
            'num_venues': len(routing),
            'fully_routed': sum(r['quantity'] for r in routing) == request.quantity,
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/venues/evaluate")
async def evaluate_venues(
    symbol: str = Query(...),
    quantity: int = Query(...)
):
    """
    Evaluate execution costs across different venues

    Returns cost comparison for NSE vs BSE
    """
    try:
        router = SmartOrderRouter()
        market_data = IndianMarketData()

        # Get current price
        quote = market_data.get_live_quote(symbol)
        price = quote['ltp']

        # Mock liquidity (in production, fetch from order books)
        venue_liquidity = {
            'NSE': quantity * 2,  # NSE usually has more liquidity
            'BSE': int(quantity * 0.7)
        }

        evaluations = []
        for venue in ['NSE', 'BSE']:
            liquidity = venue_liquidity.get(venue, 0)
            eval_result = router.evaluate_venue(venue, quantity, liquidity, price)
            evaluations.append(eval_result)

        # Sort by cost
        evaluations.sort(key=lambda x: x['cost_per_share'])

        return {
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'venue_evaluations': evaluations,
            'recommended_venue': evaluations[0]['venue'],
            'cost_savings': round(evaluations[-1]['cost_per_share'] - evaluations[0]['cost_per_share'], 4),
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Adaptive Execution Endpoints

@router.post("/adaptive/adjust-schedule")
async def adjust_schedule_realtime(
    original_schedule: List[Dict] = Body(...),
    current_interval: int = Body(...),
    executed_quantity: int = Body(...),
    target_quantity: int = Body(...),
    current_volume_pct: float = Body(...),
    expected_volume_pct: float = Body(...)
):
    """
    Adjust execution schedule in real-time based on market conditions

    Increases aggressiveness when volume is high
    Decreases when volume is low
    """
    try:
        adaptive = AdaptiveExecutionAlgorithm(urgency=0.5)

        adjusted_schedule = adaptive.adjust_schedule_real_time(
            original_schedule=original_schedule,
            current_interval=current_interval,
            executed_quantity=executed_quantity,
            target_quantity=target_quantity,
            current_volume_pct=current_volume_pct,
            expected_volume_pct=expected_volume_pct
        )

        return {
            'adjusted_schedule': adjusted_schedule,
            'remaining_quantity': target_quantity - executed_quantity,
            'intervals_remaining': len(adjusted_schedule),
            'volume_deviation': round((current_volume_pct / expected_volume_pct - 1) * 100, 2),
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/adaptive/urgency")
async def calculate_urgency(
    time_elapsed_pct: float = Query(..., description="% of execution window elapsed"),
    quantity_executed_pct: float = Query(..., description="% of order executed")
):
    """
    Calculate dynamic urgency score

    Higher urgency when falling behind schedule
    """
    try:
        adaptive = AdaptiveExecutionAlgorithm()

        urgency = adaptive.calculate_urgency_score(
            time_elapsed=time_elapsed_pct / 100,
            total_time=1.0,
            pct_executed=quantity_executed_pct / 100
        )

        if quantity_executed_pct < time_elapsed_pct:
            status = 'BEHIND SCHEDULE'
            action = 'Increase execution rate'
        elif quantity_executed_pct > time_elapsed_pct * 1.2:
            status = 'AHEAD OF SCHEDULE'
            action = 'Can slow down execution'
        else:
            status = 'ON SCHEDULE'
            action = 'Maintain current pace'

        return {
            'urgency_score': round(urgency, 3),
            'time_elapsed_pct': time_elapsed_pct,
            'quantity_executed_pct': quantity_executed_pct,
            'status': status,
            'recommended_action': action,
            'timestamp': datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
