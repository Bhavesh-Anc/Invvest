"""
Kite Connect API Routes
Provides authentication, market data, and order execution via Zerodha Kite
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from integrations.kite_client import get_kite_client, KiteAPIClient
from config.kite_config import get_kite_config

logger = logging.getLogger(__name__)
router = APIRouter()

# ===== Request/Response Models =====


class KiteAuthRequest(BaseModel):
    api_key: str
    api_secret: str
    request_token: str


class KiteAuthResponse(BaseModel):
    success: bool
    access_token: str
    user_id: str
    user_name: str
    message: str


class KiteConfigRequest(BaseModel):
    api_key: str
    api_secret: str


class OrderRequest(BaseModel):
    symbol: str
    exchange: str
    transaction_type: str  # BUY or SELL
    quantity: int
    order_type: str  # MARKET, LIMIT, SL, SL-M
    product: str = "MIS"  # CNC, MIS, NRML
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    tag: Optional[str] = None


class OrderResponse(BaseModel):
    order_id: str
    status: str
    message: str


class HistoricalDataRequest(BaseModel):
    symbol: str
    exchange: str
    from_date: str  # YYYY-MM-DD
    to_date: str  # YYYY-MM-DD
    interval: str = "day"


# ===== Helper Functions =====


def get_client() -> KiteAPIClient:
    """Get configured Kite client or raise error"""
    config = get_kite_config()

    if not config.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Kite API not configured. Please set API key and secret."
        )

    if not config.has_access_token():
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please login via /api/kite/auth/login"
        )

    try:
        client = get_kite_client(config.api_key, config.access_token)
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Kite client: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Authentication Endpoints =====


@router.get("/auth/login-url")
async def get_login_url():
    """
    Get Kite login URL for user authentication

    Returns URL to redirect user for Kite login.
    After login, user will be redirected back with request_token.
    """
    config = get_kite_config()

    if not config.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Kite API not configured. Use POST /api/kite/config to set API credentials."
        )

    try:
        client = get_kite_client(config.api_key)
        login_url = client.get_login_url()

        return {
            "login_url": login_url,
            "instructions": [
                "1. Open the login URL in a browser",
                "2. Login with your Zerodha credentials",
                "3. After successful login, you'll be redirected with a request_token in URL",
                "4. Copy the request_token and use POST /api/kite/auth/session to complete authentication"
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get login URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/session", response_model=KiteAuthResponse)
async def generate_session(auth_request: KiteAuthRequest):
    """
    Generate session and access token using request_token from Kite login

    Args:
        api_key: Your Kite API key
        api_secret: Your Kite API secret
        request_token: Request token from Kite login callback URL

    Returns:
        Access token and user details
    """
    try:
        # Create client
        client = get_kite_client(auth_request.api_key)

        # Generate session
        session_data = client.generate_session(
            request_token=auth_request.request_token,
            api_secret=auth_request.api_secret
        )

        # Save config
        config = get_kite_config()
        config.api_key = auth_request.api_key
        config.api_secret = auth_request.api_secret
        config.user_id = session_data.get("user_id")
        config.save_to_file()
        config.save_access_token(session_data["access_token"])

        # Get profile
        profile = client.get_profile()

        return KiteAuthResponse(
            success=True,
            access_token=session_data["access_token"],
            user_id=session_data["user_id"],
            user_name=profile.get("user_name", ""),
            message="Authentication successful"
        )
    except Exception as e:
        logger.error(f"Failed to generate session: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/config")
async def save_config(config_request: KiteConfigRequest):
    """
    Save Kite API credentials (without authentication)

    Args:
        api_key: Your Kite API key from console.zerodha.com
        api_secret: Your Kite API secret
    """
    try:
        config = get_kite_config()
        config.api_key = config_request.api_key
        config.api_secret = config_request.api_secret
        config.save_to_file()

        return {
            "success": True,
            "message": "Configuration saved. Use /api/kite/auth/login-url to authenticate."
        }
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/status")
async def get_auth_status():
    """Check authentication status"""
    config = get_kite_config()

    return {
        "configured": config.is_configured(),
        "authenticated": config.has_access_token(),
        "user_id": config.user_id,
        "api_key": config.api_key[:4] + "..." + config.api_key[-4:] if config.api_key else None
    }


@router.post("/auth/logout")
async def logout():
    """Invalidate current session"""
    try:
        client = get_client()
        client.invalidate_session()

        # Clear access token
        config = get_kite_config()
        config.access_token = None

        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Failed to logout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Market Data Endpoints =====


@router.get("/quote")
async def get_quote(symbols: str = Query(..., description="Comma-separated symbols (e.g., NSE:INFY,NSE:RELIANCE)")):
    """
    Get live quotes for symbols

    Args:
        symbols: Comma-separated list of symbols in format EXCHANGE:SYMBOL
                Example: NSE:INFY,NSE:RELIANCE,NFO:NIFTY24JAN24000CE

    Returns:
        Quote data for all symbols
    """
    try:
        client = get_client()
        symbol_list = [s.strip() for s in symbols.split(',')]
        quotes = client.get_quote(symbol_list)
        return quotes
    except Exception as e:
        logger.error(f"Failed to get quotes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ltp")
async def get_ltp(symbols: str = Query(..., description="Comma-separated symbols")):
    """
    Get Last Traded Price for symbols

    Args:
        symbols: Comma-separated list of symbols (e.g., NSE:INFY,NSE:RELIANCE)

    Returns:
        LTP for all symbols
    """
    try:
        client = get_client()
        symbol_list = [s.strip() for s in symbols.split(',')]
        ltp = client.get_ltp(symbol_list)
        return ltp
    except Exception as e:
        logger.error(f"Failed to get LTP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/historical")
async def get_historical_data(request: HistoricalDataRequest):
    """
    Get historical OHLC data

    Args:
        symbol: Trading symbol
        exchange: Exchange (NSE, BSE, NFO, etc.)
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        interval: Candle interval (minute, day, etc.)

    Returns:
        Historical candle data
    """
    try:
        client = get_client()

        # Get instrument token
        token = client.get_instrument_token(request.symbol, request.exchange)
        if not token:
            raise HTTPException(status_code=404, detail=f"Symbol {request.symbol} not found on {request.exchange}")

        # Fetch historical data
        df = client.get_historical_data(
            instrument_token=token,
            from_date=request.from_date,
            to_date=request.to_date,
            interval=request.interval
        )

        # Convert to JSON-serializable format
        data = df.to_dict(orient='records')

        return {
            "symbol": request.symbol,
            "exchange": request.exchange,
            "interval": request.interval,
            "data": data
        }
    except Exception as e:
        logger.error(f"Failed to get historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instruments/{exchange}")
async def get_instruments(exchange: str):
    """
    Get list of all instruments for an exchange

    Args:
        exchange: Exchange name (NSE, BSE, NFO, BFO, MCX)

    Returns:
        List of all tradable instruments
    """
    try:
        client = get_client()
        df = client.get_instruments(exchange.upper())

        # Return first 1000 instruments (to avoid huge response)
        instruments = df.head(1000).to_dict(orient='records')

        return {
            "exchange": exchange,
            "total": len(df),
            "returned": len(instruments),
            "instruments": instruments
        }
    except Exception as e:
        logger.error(f"Failed to get instruments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_instruments(
    query: str = Query(..., description="Search query"),
    exchange: str = Query("NSE", description="Exchange to search")
):
    """
    Search for instruments by symbol or name

    Args:
        query: Search string (e.g., "INFY", "RELIANCE")
        exchange: Exchange to search in

    Returns:
        Matching instruments
    """
    try:
        client = get_client()
        df = client.search_instruments(query, exchange.upper())
        instruments = df.to_dict(orient='records')

        return {
            "query": query,
            "exchange": exchange,
            "count": len(instruments),
            "instruments": instruments
        }
    except Exception as e:
        logger.error(f"Failed to search instruments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Order Execution Endpoints =====


@router.post("/order/place", response_model=OrderResponse)
async def place_order(order: OrderRequest):
    """
    Place a new order

    Args:
        Order details including symbol, quantity, price, etc.

    Returns:
        Order ID and status
    """
    try:
        client = get_client()

        order_id = client.place_order(
            symbol=order.symbol,
            exchange=order.exchange,
            transaction_type=order.transaction_type,
            quantity=order.quantity,
            order_type=order.order_type,
            product=order.product,
            price=order.price,
            trigger_price=order.trigger_price,
            tag=order.tag
        )

        return OrderResponse(
            order_id=order_id,
            status="success",
            message=f"Order placed successfully: {order.transaction_type} {order.quantity} {order.symbol}"
        )
    except Exception as e:
        logger.error(f"Failed to place order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/order/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an order"""
    try:
        client = get_client()
        cancelled_id = client.cancel_order(order_id)

        return {
            "success": True,
            "order_id": cancelled_id,
            "message": "Order cancelled successfully"
        }
    except Exception as e:
        logger.error(f"Failed to cancel order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_orders():
    """Get all orders for the day"""
    try:
        client = get_client()
        orders = client.get_orders()
        return {"count": len(orders), "orders": orders}
    except Exception as e:
        logger.error(f"Failed to get orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades")
async def get_trades():
    """Get all executed trades for the day"""
    try:
        client = get_client()
        trades = client.get_trades()
        return {"count": len(trades), "trades": trades}
    except Exception as e:
        logger.error(f"Failed to get trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Portfolio Endpoints =====


@router.get("/positions")
async def get_positions():
    """Get current positions (day + net)"""
    try:
        client = get_client()
        positions = client.get_positions()
        return positions
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/holdings")
async def get_holdings():
    """Get long-term holdings"""
    try:
        client = get_client()
        holdings = client.get_holdings()
        return {"count": len(holdings), "holdings": holdings}
    except Exception as e:
        logger.error(f"Failed to get holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/margins")
async def get_margins(segment: Optional[str] = None):
    """Get account margins"""
    try:
        client = get_client()
        margins = client.get_margins(segment)
        return margins
    except Exception as e:
        logger.error(f"Failed to get margins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile")
async def get_profile():
    """Get user profile"""
    try:
        client = get_client()
        profile = client.get_profile()
        return profile
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))
