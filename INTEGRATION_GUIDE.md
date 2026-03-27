# Frontend-Backend Integration Guide
## QuantEdge Pro - Complete Setup Instructions

## 🎯 Current Status

### ✅ Completed
1. **FastAPI Backend** - All 8 modules with 60+ endpoints
2. **API Client** - Centralized service for all backend calls
3. **UI Components** - Loading and Error display components
4. **Dashboard Page** - Fully integrated with live backend data

### 🔄 In Progress
Remaining 7 pages need API integration following the same pattern

## 📁 Project Structure

```
Invvest/
├── backend/                    # FastAPI Backend
│   ├── main.py                # Entry point
│   ├── api/routes/            # API endpoints
│   │   ├── dashboard.py       # ✅ Dashboard APIs
│   │   ├── portfolio.py       # Portfolio APIs
│   │   ├── options.py         # Options APIs
│   │   ├── strategy.py        # Strategy APIs
│   │   ├── algo.py            # Algo trading APIs
│   │   ├── risk.py            # Risk management APIs
│   │   ├── backtest.py        # Backtesting APIs
│   │   └── models.py          # AI models APIs
│   ├── services/
│   │   └── market_data.py     # Market data service
│   └── core/
│       └── config.py          # Configuration
│
└── frontend/                   # Next.js Frontend
    ├── app/
    │   ├── page.tsx           # ✅ Dashboard (INTEGRATED)
    │   ├── portfolio/page.tsx # Portfolio Analytics
    │   ├── options/page.tsx   # Options Analytics
    │   ├── strategy/page.tsx  # Strategy Builder
    │   ├── algo/page.tsx      # Algo Trading
    │   ├── risk/page.tsx      # Risk Management
    │   ├── backtest/page.tsx  # Backtesting
    │   └── models/page.tsx    # AI Models
    ├── lib/
    │   ├── api.ts             # ✅ API Client
    │   └── hooks.ts           # ✅ Custom hooks
    └── components/ui/
        ├── Loading.tsx         # ✅ Loading component
        └── ErrorDisplay.tsx    # ✅ Error component
```

## 🚀 Setup Instructions

### 1. Backend Setup

```bash
# Install dependencies
cd /home/user/Invvest
pip install -r requirements.txt

# Create environment file
cd backend
cp .env.example .env

# Edit .env (optional - API keys for live data)
# For testing, default values work fine

# Run backend server
python main.py

# Backend will start on http://localhost:8000
# API docs: http://localhost:8000/api/docs
```

### 2. Frontend Setup

```bash
# Install dependencies
cd /home/user/Invvest/frontend
npm install

# Create environment file
cp .env.local.example .env.local

# Edit .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run frontend dev server
npm run dev

# Frontend will start on http://localhost:3000
```

### 3. Test Integration

1. Open http://localhost:3000
2. Dashboard should load with data from backend
3. Check browser console for any API errors
4. Check backend logs at terminal running Python server

## 📝 Page Integration Pattern

### Example: Dashboard Page (COMPLETED ✅)

**Before:**
```typescript
// Mock data
const portfolioData = {
  totalValue: 1234560,
  todayPnl: 6448,
  // ...
}

export default function DashboardPage() {
  return (
    <div>
      <MetricCard value={portfolioData.totalValue} />
    </div>
  )
}
```

**After (with API):**
```typescript
'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'
import Loading from '@/components/ui/Loading'
import ErrorDisplay from '@/components/ui/ErrorDisplay'

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await api.dashboard.getDashboardData()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch data'))
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <Loading />
  if (error) return <ErrorDisplay error={error} onRetry={fetchData} />
  if (!data) return null

  return (
    <div>
      <MetricCard value={data.portfolio.totalValue} />
    </div>
  )
}
```

## 🔧 Updating Remaining Pages

### Portfolio Analytics (`frontend/app/portfolio/page.tsx`)

**API Calls Needed:**
```typescript
// Fetch holdings with tax calculations
const holdings = await api.portfolio.getHoldings()

// Fetch tax summary
const taxSummary = await api.portfolio.getTaxSummary()

// Fetch monthly returns
const monthlyReturns = await api.portfolio.getMonthlyReturns(6)

// Fetch risk metrics
const riskMetrics = await api.portfolio.getRiskMetrics()

// Fetch correlation data
const correlation = await api.portfolio.getCorrelation()

// Fetch drawdown history
const drawdown = await api.portfolio.getDrawdownHistory(180)
```

**Steps:**
1. Import `api` from `@/lib/api`
2. Import `Loading` and `ErrorDisplay` components
3. Add state management (`useState` for data, loading, error)
4. Add `useEffect` to fetch data on mount
5. Replace mock data with API responses
6. Add loading and error handling

### Options Analytics (`frontend/app/options/page.tsx`)

**API Calls Needed:**
```typescript
// Portfolio Greeks
const greeks = await api.options.getGreeksSummary()

// Options chain
const chain = await api.options.getOptionsChain('NIFTY', '25-JAN-2024')

// IV Skew
const ivSkew = await api.options.getIVSkew('NIFTY', '25-JAN-2024')

// Greeks evolution
const evolution = await api.options.getGreeksEvolution()

// OI distribution
const oiDist = await api.options.getOIDistribution('NIFTY', '25-JAN-2024')

// PCR analysis
const pcr = await api.options.getPCRAnalysis('NIFTY', '25-JAN-2024')
```

### Strategy Builder (`frontend/app/strategy/page.tsx`)

**API Calls Needed:**
```typescript
// Strategy templates
const templates = await api.strategy.getTemplates()

// Analyze custom strategy
const analysis = await api.strategy.analyzeStrategy(strategyData)

// Payoff diagram
const payoff = await api.strategy.getPayoffDiagram('bull-call-spread')

// Expiry calendar
const calendar = await api.strategy.getExpiryCalendar()

// Greeks optimization
const optimization = await api.strategy.getGreeksOptimization()
```

### Algo Trading (`frontend/app/algo/page.tsx`)

**API Calls Needed:**
```typescript
// All strategies
const strategies = await api.algo.getStrategies()

// Intraday performance
const performance = await api.algo.getIntradayPerformance()

// Technical indicators
const indicators = await api.algo.getTechnicalIndicators('NIFTY')

// Execution timeline
const timeline = await api.algo.getExecutionTimeline(10)

// Market microstructure
const microstructure = await api.algo.getMarketMicrostructure()
```

### Risk Management (`frontend/app/risk/page.tsx`)

**API Calls Needed:**
```typescript
// Risk metrics
const metrics = await api.risk.getMetrics()

// VaR history
const varHistory = await api.risk.getVaRHistory(30)

// Stress tests
const stressTests = await api.risk.getStressTests()

// Position risk
const positionRisk = await api.risk.getPositionRisk()

// Circuit breakers
const circuitBreakers = await api.risk.getCircuitBreakers()
```

### Backtesting (`frontend/app/backtest/page.tsx`)

**API Calls Needed:**
```typescript
// Backtest config
const config = await api.backtest.getConfig()

// Equity curve
const equityCurve = await api.backtest.getEquityCurve(180)

// Performance metrics
const metrics = await api.backtest.getPerformanceMetrics()

// Walk-forward results
const walkForward = await api.backtest.getWalkForward()

// Paper trades
const paperTrades = await api.backtest.getPaperTrades(20)
```

### AI Models (`frontend/app/models/page.tsx`)

**API Calls Needed:**
```typescript
// Model leaderboard
const leaderboard = await api.models.getModelLeaderboard()

// Regime detection
const regimeData = await api.models.getRegimeDetection(60)

// Feature importance
const features = await api.models.getFeatureImportance('XGBoost')

// Sentiment analysis
const sentiment = await api.models.getSentimentAnalysis(7)

// Anomaly detection
const anomalies = await api.models.getAnomalyDetection()

// RL suggestions
const rlSuggestions = await api.models.getRLSuggestions()
```

## 🧪 Testing Checklist

### Backend Tests
- [ ] Backend starts without errors: `python backend/main.py`
- [ ] API docs accessible: http://localhost:8000/api/docs
- [ ] Health check works: http://localhost:8000/api/health
- [ ] Dashboard endpoint returns data: http://localhost:8000/api/dashboard
- [ ] All 8 route modules load correctly

### Frontend Tests
- [ ] Frontend starts without errors: `npm run dev`
- [ ] Dashboard loads and displays data
- [ ] Loading state shows while fetching
- [ ] Error state shows if backend is down
- [ ] Retry button works after error
- [ ] Charts render correctly with backend data
- [ ] No console errors (check browser console)

### Integration Tests
- [ ] Stop backend → Frontend shows error message
- [ ] Start backend → Retry button fetches data successfully
- [ ] All API calls complete within 2 seconds
- [ ] No CORS errors in browser console
- [ ] Data updates when backend data changes

## 🐛 Troubleshooting

### Issue: "Failed to fetch" Error

**Cause:** Backend not running or wrong API URL

**Fix:**
1. Check backend is running: `ps aux | grep python`
2. Check API_URL in `.env.local`: Should be `http://localhost:8000`
3. Restart backend: `cd backend && python main.py`

### Issue: CORS Errors

**Cause:** Frontend origin not allowed by backend

**Fix:**
Edit `backend/core/config.py`:
```python
ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Add your Vercel URL when deploying
]
```

### Issue: "Module not found" in Backend

**Cause:** Missing Python dependencies

**Fix:**
```bash
cd /home/user/Invvest
pip install -r requirements.txt
```

### Issue: "Cannot find module" in Frontend

**Cause:** Missing npm dependencies

**Fix:**
```bash
cd /home/user/Invvest/frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: API Returns 404

**Cause:** Endpoint path mismatch

**Fix:**
- Check API path in `lib/api.ts` matches backend route
- Example: `/api/dashboard` in frontend = `@app.get("/api/dashboard")` in backend
- Check backend logs for actual routes registered

## 📊 Development Workflow

1. **Start Backend**:
   ```bash
   cd /home/user/Invvest/backend
   python main.py
   # Keep this terminal open
   ```

2. **Start Frontend** (new terminal):
   ```bash
   cd /home/user/Invvest/frontend
   npm run dev
   # Keep this terminal open
   ```

3. **Make Changes**:
   - Edit page in `frontend/app/*/page.tsx`
   - Save file → Next.js auto-reloads
   - Check browser for updates

4. **Test**:
   - Open http://localhost:3000
   - Click through all pages
   - Check console for errors

5. **Commit**:
   ```bash
   git add .
   git commit -m "feat: Integrate [page name] with backend API"
   git push
   ```

## 🚀 Next Steps

### Immediate (Complete Integration)
1. ✅ Update Portfolio Analytics page
2. ✅ Update Options Analytics page
3. ✅ Update Strategy Builder page
4. ✅ Update Algo Trading page
5. ✅ Update Risk Management page
6. ✅ Update Backtesting page
7. ✅ Update AI Models page
8. ✅ Test all pages locally
9. ✅ Commit and push changes

### Short-term (Enhancements)
- Add WebSocket for real-time updates
- Implement data caching (React Query or SWR)
- Add authentication/authorization
- Implement user preferences
- Add dark/light theme toggle

### Long-term (Production)
- Deploy backend to Railway/Render
- Deploy frontend to Vercel
- Set up CI/CD pipeline
- Add monitoring and logging
- Implement rate limiting
- Add comprehensive error tracking

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Next.js Docs**: https://nextjs.org/docs
- **API Client Pattern**: See `frontend/lib/api.ts`
- **Backend README**: `/home/user/Invvest/backend/README.md`
- **Frontend README**: `/home/user/Invvest/frontend/README.md`

## 💡 Tips

1. **Use API Docs**: Visit http://localhost:8000/api/docs to test endpoints
2. **Check Network Tab**: Browser DevTools → Network to see API calls
3. **Console Logs**: Add `console.log(data)` to debug API responses
4. **Type Safety**: Use TypeScript interfaces for API responses
5. **Error Handling**: Always wrap API calls in try-catch
6. **Loading States**: Show loading indicator while fetching
7. **Fallback Data**: Consider showing cached/stale data during fetch

## ⚙️ Configuration Files

### Frontend Environment (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend Environment (`.env`)
```env
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=sqlite:///./data/quantedge.db
```

## 🔐 Security Notes

- Never commit `.env` or `.env.local` files
- Use `.env.example` templates instead
- Rotate API keys regularly
- Use HTTPS in production
- Implement rate limiting
- Validate all user inputs
- Sanitize data before displaying

---

**Happy Coding! 🚀**

For questions or issues, check:
- Backend logs in terminal running `python main.py`
- Frontend console in browser DevTools
- API documentation at http://localhost:8000/api/docs
