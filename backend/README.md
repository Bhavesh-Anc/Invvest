# QuantEdge Pro - FastAPI Backend

Institutional-grade FastAPI backend for the QuantEdge Pro quantitative finance platform.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/user/Invvest
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cd backend
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 3. Run Development Server

```bash
cd backend
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## 📁 Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── core/
│   ├── config.py          # Configuration settings
│   └── __init__.py
├── api/
│   └── routes/            # API route handlers
│       ├── dashboard.py   # Dashboard endpoints
│       ├── portfolio.py   # Portfolio analytics
│       ├── options.py     # Options analytics
│       ├── strategy.py    # Strategy builder
│       ├── algo.py        # Algo trading
│       ├── risk.py        # Risk management
│       ├── backtest.py    # Backtesting
│       └── models.py      # AI models
├── services/
│   └── market_data.py     # Market data service
└── .env.example           # Environment variables template
```

## 🔌 API Endpoints

### Dashboard
- `GET /api/dashboard` - Complete dashboard data
- `GET /api/dashboard/market-data` - Live market indices
- `GET /api/dashboard/portfolio-metrics` - Portfolio summary
- `GET /api/dashboard/positions` - Open positions

### Portfolio Analytics
- `GET /api/portfolio/holdings` - All holdings with tax calculations
- `GET /api/portfolio/tax-summary` - LTCG/STCG summary
- `GET /api/portfolio/risk-metrics` - Risk-adjusted metrics
- `GET /api/portfolio/correlation` - Correlation analysis

### Options Analytics
- `GET /api/options/options-chain?underlying=NIFTY&expiry=25-JAN-2024` - Options chain
- `GET /api/options/greeks-summary` - Portfolio Greeks
- `GET /api/options/iv-skew` - IV skew analysis
- `GET /api/options/pcr-analysis` - Put-Call Ratio

### Strategy Builder
- `GET /api/strategy/templates` - Pre-defined strategies
- `POST /api/strategy/analyze` - Analyze custom strategy
- `GET /api/strategy/payoff-diagram` - Payoff diagram data
- `GET /api/strategy/expiry-calendar` - NSE expiry calendar

### Algo Trading
- `GET /api/algo/strategies` - All algo strategies
- `GET /api/algo/intraday-performance` - Intraday P&L
- `GET /api/algo/technical-indicators` - Real-time indicators
- `POST /api/algo/strategy/{id}/toggle` - Pause/resume strategy

### Risk Management
- `GET /api/risk/metrics` - Portfolio risk metrics
- `GET /api/risk/var-history` - VaR historical data
- `GET /api/risk/stress-tests` - Stress test scenarios
- `POST /api/risk/evaluate-trade` - Pre-trade risk check

### Backtesting
- `GET /api/backtest/equity-curve` - Equity curve data
- `GET /api/backtest/performance-metrics` - Performance metrics
- `GET /api/backtest/walk-forward` - Walk-forward validation
- `POST /api/backtest/run-backtest` - Run backtest

### AI Models
- `GET /api/models/model-leaderboard` - ML model rankings
- `GET /api/models/regime-detection` - Market regime history
- `GET /api/models/sentiment-analysis` - News sentiment
- `GET /api/models/anomaly-detection` - Real-time anomalies

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=sqlite:///./data/quantedge.db

# Optional broker API keys for live trading
ZERODHA_API_KEY=your_key
ZERODHA_API_SECRET=your_secret
```

### CORS Configuration

Update `core/config.py` to add your frontend URL:

```python
ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",
    "https://your-app.vercel.app"
]
```

## 📊 Market Data Sources

The backend integrates with:
- **NSE/BSE** - Indian stock market data via `jugaad-data`
- **Yahoo Finance** - Fallback for historical data via `yfinance`
- **Options Data** - NSE options chain for Greeks and IV analysis

## 🧪 Testing

Test the API locally:

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Test dashboard endpoint
curl http://localhost:8000/api/dashboard

# View API documentation
open http://localhost:8000/api/docs
```

## 🚢 Deployment

### Deploy to Railway

1. Create `Procfile`:
```
web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

2. Push to Railway:
```bash
railway login
railway init
railway up
```

3. Set environment variables in Railway dashboard

### Deploy to Render

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: quantedge-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

2. Connect GitHub repo to Render

## 📝 Development

### Adding New Endpoints

1. Create route handler in `api/routes/`:
```python
from fastapi import APIRouter
router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint():
    return {"data": "value"}
```

2. Register router in `main.py`:
```python
from api.routes import my_routes
app.include_router(my_routes.router, prefix="/api/my", tags=["My Routes"])
```

### Database Models

Currently using SQLite. To upgrade to PostgreSQL:

1. Update `.env`:
```
DATABASE_URL=postgresql://user:password@localhost/quantedge
```

2. Install psycopg2:
```bash
pip install psycopg2-binary
```

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## 🔒 Security

- Add authentication middleware for production
- Use environment variables for sensitive data
- Enable HTTPS in production
- Rate limiting configured in `core/config.py`

## 📄 License

Proprietary - QuantEdge Pro Platform
