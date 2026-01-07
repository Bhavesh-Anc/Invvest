# Quick Guide: Update All Pages with API Integration

## ✅ Already Complete
- ✅ Dashboard (`app/page.tsx`) - Fully integrated

## 🔄 Pages to Update (Simple Pattern)

Each page follows the EXACT same pattern. Here's the template:

### Universal Update Pattern

```typescript
'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'
import Loading from '@/components/ui/Loading'
import ErrorDisplay from '@/components/ui/ErrorDisplay'
// ... other imports stay the same

export default function YourPage() {
  // 1. ADD STATE
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [data, setData] = useState<any>(null)

  // 2. ADD FETCH FUNCTION
  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await api.yourModule.yourEndpoint()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch'))
    } finally {
      setLoading(false)
    }
  }

  // 3. ADD LOADING/ERROR STATES
  if (loading) return <Loading message="Loading..." />
  if (error) return <ErrorDisplay error={error} onRetry={fetchData} />
  if (!data) return null

  // 4. REPLACE MOCK DATA
  // OLD: const mockData = [...]
  // NEW: Use `data` from state

  return (
    // ... rest of component JSX stays the same
    // Just use `data` instead of `mockData`
  )
}
```

---

## 📋 Page-by-Page API Calls

### 1. Portfolio Analytics (`app/portfolio/page.tsx`)

**Replace mock data with:**
```typescript
const fetchData = async () => {
  try {
    setLoading(true)
    const [holdings, taxSummary, returns, riskMetrics, correlation, drawdown] =
      await Promise.all([
        api.portfolio.getHoldings(),
        api.portfolio.getTaxSummary(),
        api.portfolio.getMonthlyReturns(7),
        api.portfolio.getRiskMetrics(),
        api.portfolio.getCorrelation(),
        api.portfolio.getDrawdownHistory(180)
      ])

    setHoldings(holdings)
    setTaxSummary(taxSummary)
    setMonthlyReturns(returns)
    setRiskMetrics(riskMetrics)
    setCorrelationData(correlation)
    setDrawdownData(drawdown)
  } catch (err) {
    setError(err)
  } finally {
    setLoading(false)
  }
}
```

### 2. Options Analytics (`app/options/page.tsx`)

**Replace mock data with:**
```typescript
const fetchData = async () => {
  try {
    setLoading(true)
    const [greeks, chain, ivSkew, evolution, oiDist, pcr] = await Promise.all([
      api.options.getGreeksSummary(),
      api.options.getOptionsChain(selectedStock, selectedExpiry),
      api.options.getIVSkew(selectedStock, selectedExpiry),
      api.options.getGreeksEvolution(),
      api.options.getOIDistribution(selectedStock, selectedExpiry),
      api.options.getPCRAnalysis(selectedStock, selectedExpiry)
    ])

    setGreeksSummary(greeks)
    setOptionsChain(chain)
    setIVSkew(ivSkew)
    setGreeksEvolution(evolution)
    setOIData(oiDist)
    setPCRData(pcr)
  } catch (err) {
    setError(err)
  } finally {
    setLoading(false)
  }
}

// Re-fetch when selection changes
useEffect(() => {
  if (selectedStock && selectedExpiry) {
    fetchData()
  }
}, [selectedStock, selectedExpiry])
```

### 3. Strategy Builder (`app/strategy/page.tsx`)

**Replace mock data with:**
```typescript
const fetchData = async () => {
  try {
    setLoading(true)
    const [templates, calendar, optimization] = await Promise.all([
      api.strategy.getTemplates(),
      api.strategy.getExpiryCalendar(),
      api.strategy.getGreeksOptimization()
    ])

    setTemplates(templates)
    setExpiryCalendar(calendar)
    setGreeksOptimization(optimization)
  } catch (err) {
    setError(err)
  } finally {
    setLoading(false)
  }
}

// Load payoff when template selected
const loadPayoff = async (strategyId: string) => {
  const payoff = await api.strategy.getPayoffDiagram(strategyId)
  setPayoffData(payoff)
}
```

### 4. Algo Trading (`app/algo/page.tsx`)

**Replace mock data with:**
```typescript
const fetchData = async () => {
  try {
    setLoading(true)
    const [strategies, performance, indicators, timeline, microstructure] =
      await Promise.all([
        api.algo.getStrategies(),
        api.algo.getIntradayPerformance(),
        api.algo.getTechnicalIndicators('NIFTY'),
        api.algo.getExecutionTimeline(10),
        api.algo.getMarketMicrostructure()
      ])

    setStrategies(strategies)
    setIntradayPerformance(performance)
    setIndicators(indicators)
    setExecutionTimeline(timeline)
    setMicrostructure(microstructure)
  } catch (err) {
    setError(err)
  } finally {
    setLoading(false)
  }
}

// Toggle strategy
const toggleStrategy = async (id: string) => {
  await api.algo.toggleStrategy(id)
  fetchData() // Refresh
}
```

### 5. Risk Management (`app/risk/page.tsx`)

**Replace mock data with:**
```typescript
const fetchData = async () => {
  try {
    setLoading(true)
    const [metrics, varHistory, stressTests, positionRisk, circuitBreakers] =
      await Promise.all([
        api.risk.getMetrics(),
        api.risk.getVaRHistory(30),
        api.risk.getStressTests(),
        api.risk.getPositionRisk(),
        api.risk.getCircuitBreakers()
      ])

    setRiskMetrics(metrics)
    setVaRHistory(varHistory)
    setStressTests(stressTests)
    setPositionRisk(positionRisk)
    setCircuitBreakers(circuitBreakers)
  } catch (err) {
    setError(err)
  } finally {
    setLoading(false)
  }
}
```

### 6. Backtesting (`app/backtest/page.tsx`)

**Replace mock data with:**
```typescript
const fetchData = async () => {
  try {
    setLoading(true)
    const [config, equity, metrics, walkForward, paperTrades] =
      await Promise.all([
        api.backtest.getConfig(),
        api.backtest.getEquityCurve(180),
        api.backtest.getPerformanceMetrics(),
        api.backtest.getWalkForward(),
        api.backtest.getPaperTrades(20)
      ])

    setConfig(config)
    setEquityCurve(equity)
    setPerformanceMetrics(metrics)
    setWalkForward(walkForward)
    setPaperTrades(paperTrades)
  } catch (err) {
    setError(err)
  } finally {
    setLoading(false)
  }
}

// Update config
const updateConfig = async (newConfig: any) => {
  await api.backtest.updateConfig(newConfig)
  fetchData() // Refresh
}
```

### 7. AI Models (`app/models/page.tsx`)

**Replace mock data with:**
```typescript
const fetchData = async () => {
  try {
    setLoading(true)
    const [leaderboard, regime, features, sentiment, performance, pipeline] =
      await Promise.all([
        api.models.getModelLeaderboard(),
        api.models.getRegimeDetection(60),
        api.models.getFeatureImportance('XGBoost'),
        api.models.getSentimentAnalysis(7),
        api.models.getModelPerformance(),
        api.models.getMLPipeline()
      ])

    setLeaderboard(leaderboard)
    setRegimeData(regime)
    setFeatures(features)
    setSentiment(sentiment)
    setPerformance(performance)
    setPipeline(pipeline)
  } catch (err) {
    setError(err)
  } finally {
    setLoading(false)
  }
}
```

---

## 🚀 Quick Update Steps (Per Page)

### Step 1: Add Imports
```typescript
import { useEffect, useState } from 'react'
import api from '@/lib/api'
import Loading from '@/components/ui/Loading'
import ErrorDisplay from '@/components/ui/ErrorDisplay'
```

### Step 2: Add State (top of component)
```typescript
const [loading, setLoading] = useState(true)
const [error, setError] = useState<Error | null>(null)
const [data, setData] = useState<any>(null)
// Add more state for each data piece
```

### Step 3: Add Fetch Function
```typescript
useEffect(() => {
  fetchData()
}, [])

const fetchData = async () => {
  try {
    setLoading(true)
    setError(null)
    // API calls here
    setData(result)
  } catch (err) {
    setError(err instanceof Error ? err : new Error('Failed'))
  } finally {
    setLoading(false)
  }
}
```

### Step 4: Add Loading/Error Guards (before return)
```typescript
if (loading) return <Loading message="Loading..." />
if (error) return <ErrorDisplay error={error} onRetry={fetchData} />
if (!data) return null
```

### Step 5: Replace Mock Data
```typescript
// OLD:
const holdings = [/* mock data */]

// NEW:
// Remove mock data, use `holdings` from state
```

### Step 6: Test
- Save file
- Check browser for errors
- Verify data loads
- Check loading state shows
- Test error state (stop backend)

---

## ⚡ Even Faster: Bash Script

Create `update-pages.sh`:

```bash
#!/bin/bash

# Backup all pages
for page in portfolio options strategy algo risk backtest models; do
  cp frontend/app/$page/page.tsx frontend/app/$page/page-old.tsx
  echo "Backed up $page"
done

# You can then manually update each or use sed/awk
# But manual is safer for TypeScript
```

---

## 🎯 Prioritized Order

Update in this order (easiest to hardest):

1. **Risk Management** - Simplest (just metrics and charts)
2. **AI Models** - Straightforward data display
3. **Backtesting** - Config + charts
4. **Portfolio Analytics** - Multiple data sources
5. **Algo Trading** - Interactive (toggle strategies)
6. **Options Analytics** - Dropdown selections
7. **Strategy Builder** - Most complex (strategy creation)

---

## ✅ Testing Checklist

After updating each page:

- [ ] Page loads without errors
- [ ] Loading spinner shows initially
- [ ] Data displays correctly
- [ ] Charts render properly
- [ ] Error message shows if backend down
- [ ] Retry button works
- [ ] Browser console has no errors
- [ ] Network tab shows API calls
- [ ] Data matches backend response

---

## 🐛 Common Issues & Fixes

### Issue: "Cannot read property of undefined"
**Fix:** Add null check before accessing nested data
```typescript
{data?.portfolio?.totalValue || 0}
```

### Issue: "Infinite loop / too many re-renders"
**Fix:** Add dependency array to useEffect
```typescript
useEffect(() => {
  fetchData()
}, []) // Empty array = run once
```

### Issue: "API call returns 404"
**Fix:** Check endpoint path in `lib/api.ts` matches backend

### Issue: "CORS error"
**Fix:** Ensure backend CORS allows `http://localhost:3000`

---

## 📊 Estimated Time Per Page

- **Risk Management:** 15-20 minutes
- **AI Models:** 15-20 minutes
- **Backtesting:** 20-25 minutes
- **Portfolio Analytics:** 25-30 minutes
- **Algo Trading:** 20-25 minutes
- **Options Analytics:** 25-30 minutes
- **Strategy Builder:** 30-35 minutes

**Total:** ~2.5-3 hours for all 7 pages

---

## 🎓 Learn By Example

Study the Dashboard page (`app/page.tsx`) - it shows the complete pattern:

1. State management
2. Async data fetching
3. Error handling
4. Loading states
5. Data rendering

Copy this exact pattern for other pages, just change:
- API endpoint
- State variable names
- Data structure

---

**Ready to proceed? I can update all 7 pages now following this pattern!**

Would you like me to:
A) Update all pages automatically
B) Update them one by one so you can review each
C) Create the update script for you to run manually

Let me know and I'll proceed immediately!
