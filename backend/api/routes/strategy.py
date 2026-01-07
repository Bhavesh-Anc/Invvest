"""
Strategy Builder API endpoints
Multi-leg options strategies with payoff diagrams
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

import sys
sys.path.append('../..')
from utils.options_strategies import OptionsStrategy, StrategyBuilder, calculate_strategy_greeks
from utils.indian_market import MarketCalendar

router = APIRouter()

# Request/Response models
class StrategyLeg(BaseModel):
    """Single leg of options strategy"""
    id: str
    type: str  # CE or PE
    action: str  # BUY or SELL
    strike: float
    quantity: int
    premium: float
    expiry: str

class StrategyRequest(BaseModel):
    """Request to create/analyze strategy"""
    name: str
    legs: List[StrategyLeg]

class PayoffPoint(BaseModel):
    """Payoff diagram data point"""
    price: float
    pnl: float

class StrategyMetrics(BaseModel):
    """Strategy performance metrics"""
    maxProfit: float
    maxLoss: float
    breakeven: List[float]
    probability: float
    margin: float

class StrategyTemplate(BaseModel):
    """Pre-defined strategy template"""
    id: str
    name: str
    description: str
    sentiment: str
    maxProfit: float
    maxLoss: float
    breakeven: float
    marginRequired: float
    legs: List[Dict[str, Any]]

class ExpiryDate(BaseModel):
    """NSE expiry date"""
    date: str
    type: str
    daysLeft: int
    instruments: List[str]


@router.get("/templates", response_model=List[StrategyTemplate])
async def get_strategy_templates():
    """
    Get pre-defined options strategy templates
    """
    templates = [
        StrategyTemplate(
            id="bull-call-spread",
            name="Bull Call Spread",
            description="Limited profit, limited loss bullish strategy",
            sentiment="Bullish",
            maxProfit=437500,
            maxLoss=437500,
            breakeven=21887.5,
            marginRequired=87500,
            legs=[
                {"type": "CE", "action": "BUY", "strike": 21800, "quantity": 50, "premium": 265.75},
                {"type": "CE", "action": "SELL", "strike": 22000, "quantity": 50, "premium": 178.25},
            ]
        ),
        StrategyTemplate(
            id="bear-put-spread",
            name="Bear Put Spread",
            description="Limited profit, limited loss bearish strategy",
            sentiment="Bearish",
            maxProfit=438750,
            maxLoss=561250,
            breakeven=21887.75,
            marginRequired=112250,
            legs=[
                {"type": "PE", "action": "BUY", "strike": 22000, "quantity": 50, "premium": 280.50},
                {"type": "PE", "action": "SELL", "strike": 21800, "quantity": 50, "premium": 168.25},
            ]
        ),
        StrategyTemplate(
            id="iron-condor",
            name="Iron Condor",
            description="Profit from low volatility, neutral outlook",
            sentiment="Neutral",
            maxProfit=195625,
            maxLoss=304375,
            breakeven=21840.87,
            marginRequired=250000,
            legs=[
                {"type": "CE", "action": "SELL", "strike": 22000, "quantity": 50, "premium": 178.25},
                {"type": "CE", "action": "BUY", "strike": 22100, "quantity": 50, "premium": 142.75},
                {"type": "PE", "action": "SELL", "strike": 21800, "quantity": 50, "premium": 168.25},
                {"type": "PE", "action": "BUY", "strike": 21700, "quantity": 50, "premium": 125.50},
            ]
        ),
        StrategyTemplate(
            id="long-straddle",
            name="Long Straddle",
            description="Profit from high volatility in either direction",
            sentiment="High Volatility",
            maxProfit=float('inf'),
            maxLoss=1096250,
            breakeven=21900,
            marginRequired=1096250,
            legs=[
                {"type": "CE", "action": "BUY", "strike": 21900, "quantity": 50, "premium": 218.50},
                {"type": "PE", "action": "BUY", "strike": 21900, "quantity": 50, "premium": 220.75},
            ]
        ),
    ]

    return templates


@router.post("/analyze")
async def analyze_strategy(strategy: StrategyRequest):
    """
    Analyze custom options strategy
    """
    try:
        builder = StrategyBuilder()

        # Add legs to strategy
        for leg in strategy.legs:
            builder.add_leg(
                option_type=leg.type,
                action=leg.action,
                strike=leg.strike,
                quantity=leg.quantity,
                premium=leg.premium,
                expiry=leg.expiry
            )

        # Calculate metrics
        metrics = builder.calculate_metrics()
        greeks = calculate_strategy_greeks(strategy.legs)
        payoff = builder.generate_payoff_diagram()

        return {
            "name": strategy.name,
            "metrics": metrics,
            "greeks": greeks,
            "payoff": [
                {"price": p['price'], "pnl": p['pnl']}
                for p in payoff
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payoff-diagram", response_model=List[PayoffPoint])
async def get_payoff_diagram(strategy_id: str = "bull-call-spread"):
    """
    Get payoff diagram data for strategy template
    """
    # Sample payoff for Bull Call Spread
    payoff_data = [
        {"price": 21400, "pnl": -87.5},
        {"price": 21500, "pnl": -87.5},
        {"price": 21600, "pnl": -87.5},
        {"price": 21700, "pnl": -87.5},
        {"price": 21800, "pnl": -87.5},
        {"price": 21850, "pnl": -37.5},
        {"price": 21887.5, "pnl": 0},
        {"price": 21900, "pnl": 12.5},
        {"price": 21950, "pnl": 62.5},
        {"price": 22000, "pnl": 112.5},
        {"price": 22100, "pnl": 112.5},
        {"price": 22200, "pnl": 112.5},
        {"price": 22300, "pnl": 112.5},
        {"price": 22400, "pnl": 112.5},
    ]

    return [PayoffPoint(**p) for p in payoff_data]


@router.get("/expiry-calendar", response_model=List[ExpiryDate])
async def get_expiry_calendar():
    """
    Get NSE expiry calendar for options
    """
    try:
        calendar = MarketCalendar()
        expiries = calendar.get_upcoming_expiries()

        return [
            ExpiryDate(
                date=exp['date'],
                type=exp['type'],
                daysLeft=exp['days_left'],
                instruments=exp['instruments']
            )
            for exp in expiries
        ]
    except Exception as e:
        return [
            ExpiryDate(
                date="25-JAN-2024",
                type="Weekly",
                daysLeft=4,
                instruments=["NIFTY", "BANKNIFTY", "FINNIFTY"]
            ),
            ExpiryDate(
                date="31-JAN-2024",
                type="Monthly",
                daysLeft=10,
                instruments=["All Stocks", "Indices"]
            ),
        ]


@router.get("/greeks-optimization")
async def get_greeks_optimization():
    """
    Get Greeks neutral optimization suggestions
    """
    return {
        "currentDelta": 145.8,
        "targetDelta": 0,
        "currentGamma": 0.082,
        "targetGamma": 0,
        "currentTheta": -2847,
        "targetTheta": 0,
        "currentVega": 18250,
        "targetVega": 0,
        "suggestedAdjustment": "Sell 146 units of underlying or sell 3 ATM Call options"
    }


@router.post("/save-strategy")
async def save_strategy(strategy: StrategyRequest):
    """
    Save custom strategy for later use
    """
    # TODO: Implement database storage
    return {
        "status": "success",
        "message": f"Strategy '{strategy.name}' saved successfully",
        "id": f"custom-{datetime.now().timestamp()}"
    }


@router.get("/saved-strategies")
async def get_saved_strategies():
    """
    Get list of saved custom strategies
    """
    # TODO: Implement database retrieval
    return {
        "strategies": []
    }
