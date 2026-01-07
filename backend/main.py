"""
QuantEdge Pro - FastAPI Backend
Main application entry point for serving Next.js frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from api.routes import (
    dashboard,
    portfolio,
    options,
    strategy,
    algo,
    risk,
    backtest,
    models as ai_models
)
from core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting QuantEdge Pro API Server...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("Initializing market data connections...")

    yield

    # Shutdown
    logger.info("Shutting down QuantEdge Pro API Server...")

# Create FastAPI application
app = FastAPI(
    title="QuantEdge Pro API",
    description="Institutional-Grade Quantitative Finance Platform for Indian Stock Market",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(options.router, prefix="/api/options", tags=["Options"])
app.include_router(strategy.router, prefix="/api/strategy", tags=["Strategy"])
app.include_router(algo.router, prefix="/api/algo", tags=["Algo Trading"])
app.include_router(risk.router, prefix="/api/risk", tags=["Risk Management"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["Backtesting"])
app.include_router(ai_models.router, prefix="/api/models", tags=["AI Models"])

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "service": "QuantEdge Pro API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "QuantEdge Pro API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
