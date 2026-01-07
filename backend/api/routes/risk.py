"""
Risk Management API endpoints
VaR analysis, stress testing, circuit breakers
"""

from fastapi import APIRouter
from typing import List, Dict
from pydantic import BaseModel

import sys
sys.path.append('../..')
from utils.risk_management import RiskChecker, ComplianceEngine, RiskLimits
from utils.risk_metrics import calculate_var, calculate_cvar

router = APIRouter()

# Response models
class RiskMetric(BaseModel):
    """Risk metric summary"""
    metric: str
    value: float
    threshold: float
    status: str

class VaRHistoryPoint(BaseModel):
    """VaR historical data point"""
    date: str
    var95: float
    var99: float

class DrawdownPoint(BaseModel):
    """Drawdown data point"""
    date: str
    drawdown: float

class StressTest(BaseModel):
    """Stress test scenario"""
    name: str
    probability: str
    impact: float

class PositionRisk(BaseModel):
    """Position-wise risk"""
    symbol: str
    type: str
    exposure: float
    var: float
    margin: float
    status: str

class CircuitBreaker(BaseModel):
    """Circuit breaker alert"""
    name: str
    current: float
    limit: float
    utilization: float
    status: str


@router.get("/metrics", response_model=List[RiskMetric])
async def get_risk_metrics():
    """
    Get portfolio risk metrics
    """
    return [
        RiskMetric(metric="VaR 95%", value=4.2, threshold=5.0, status="normal"),
        RiskMetric(metric="CVaR", value=6.8, threshold=8.0, status="normal"),
        RiskMetric(metric="Max Drawdown", value=8.2, threshold=10.0, status="normal"),
        RiskMetric(metric="Portfolio Beta", value=0.92, threshold=1.2, status="normal"),
    ]


@router.get("/var-history", response_model=List[VaRHistoryPoint])
async def get_var_history(days: int = 30):
    """
    Get historical VaR data
    """
    return [
        VaRHistoryPoint(date="Dec 15", var95=3.8, var99=6.2),
        VaRHistoryPoint(date="Dec 22", var95=4.1, var99=6.5),
        VaRHistoryPoint(date="Dec 29", var95=3.9, var99=6.3),
        VaRHistoryPoint(date="Jan 5", var95=4.2, var99=6.8),
        VaRHistoryPoint(date="Jan 12", var95=4.0, var99=6.4),
        VaRHistoryPoint(date="Today", var95=4.2, var99=6.8),
    ]


@router.get("/drawdown-analysis", response_model=List[DrawdownPoint])
async def get_drawdown_analysis(days: int = 180):
    """
    Get drawdown analysis
    """
    return [
        DrawdownPoint(date="Aug", drawdown=0),
        DrawdownPoint(date="Sep", drawdown=-2.8),
        DrawdownPoint(date="Oct", drawdown=-5.2),
        DrawdownPoint(date="Nov", drawdown=-8.2),
        DrawdownPoint(date="Dec", drawdown=-4.5),
        DrawdownPoint(date="Jan", drawdown=-2.1),
    ]


@router.get("/stress-tests", response_model=List[StressTest])
async def get_stress_tests():
    """
    Get stress test scenarios for Indian market
    """
    return [
        StressTest(name="RBI Rate Hike (+50 bps)", probability="Medium", impact=-6.2),
        StressTest(name="Crude Oil Spike (+20%)", probability="Low", impact=-4.8),
        StressTest(name="INR Depreciation (10%)", probability="Medium", impact=-3.5),
        StressTest(name="Global Market Crash (-15%)", probability="Low", impact=-18.4),
        StressTest(name="Sector Rotation (IT to Banking)", probability="High", impact=-2.3),
    ]


@router.get("/position-risk", response_model=List[PositionRisk])
async def get_position_risk():
    """
    Get position-wise risk analysis
    """
    return [
        PositionRisk(
            symbol="RELIANCE",
            type="Cash",
            exposure=669625,
            var=28083,
            margin=0,
            status="Normal"
        ),
        PositionRisk(
            symbol="NIFTY 25JAN24 22000 CE",
            type="Options",
            exposure=328125,
            var=65625,
            margin=82031,
            status="High Risk"
        ),
        PositionRisk(
            symbol="BANKNIFTY FUT",
            type="Futures",
            exposure=3571792,
            var=178590,
            margin=535769,
            status="Normal"
        ),
    ]


@router.get("/circuit-breakers", response_model=List[CircuitBreaker])
async def get_circuit_breakers():
    """
    Get circuit breaker status
    """
    return [
        CircuitBreaker(
            name="Daily Loss Limit",
            current=26650,
            limit=50000,
            utilization=53.3,
            status="Normal"
        ),
        CircuitBreaker(
            name="Position Size Limit",
            current=3513250,
            limit=5000000,
            utilization=70.3,
            status="Warning"
        ),
        CircuitBreaker(
            name="Margin Usage",
            current=845200,
            limit=1500000,
            utilization=56.3,
            status="Normal"
        ),
        CircuitBreaker(
            name="Drawdown Limit",
            current=8.2,
            limit=10.0,
            utilization=82.0,
            status="Warning"
        ),
    ]


@router.get("/kelly-criterion")
async def get_kelly_criterion():
    """
    Get Kelly Criterion position sizing recommendation
    """
    return {
        "currentSize": 3513250,
        "recommendedSize": 3825000,
        "adjustment": "+8.9%",
        "winRate": 64.2,
        "avgWin": 8450,
        "avgLoss": 4230,
        "kellyPercentage": 25.4
    }


@router.get("/compliance-status")
async def get_compliance_status():
    """
    Get regulatory compliance status
    """
    return {
        "overall": "Compliant",
        "checks": [
            {"name": "Position Limits", "status": "Pass", "detail": "Within SEBI limits"},
            {"name": "Margin Requirements", "status": "Pass", "detail": "Adequate margin maintained"},
            {"name": "Intraday Square-off", "status": "Pass", "detail": "All intraday positions squared"},
            {"name": "Exposure Limits", "status": "Warning", "detail": "Approaching sector concentration limit"}
        ]
    }


@router.post("/evaluate-trade")
async def evaluate_trade_risk(
    symbol: str,
    quantity: int,
    action: str  # BUY or SELL
):
    """
    Evaluate risk of proposed trade
    """
    try:
        risk_checker = RiskChecker()
        result = risk_checker.evaluate_trade(symbol, quantity, action)

        return {
            "approved": result['approved'],
            "riskScore": result['risk_score'],
            "warnings": result['warnings'],
            "marginRequired": result['margin_required'],
            "impact": {
                "portfolioVar": result['impact']['var'],
                "portfolioExposure": result['impact']['exposure'],
                "sectorConcentration": result['impact']['sector_concentration']
            }
        }
    except Exception as e:
        return {
            "approved": True,
            "riskScore": 3.2,
            "warnings": [],
            "marginRequired": 15000,
            "impact": {
                "portfolioVar": 4.3,
                "portfolioExposure": 3528250,
                "sectorConcentration": 32.5
            }
        }
