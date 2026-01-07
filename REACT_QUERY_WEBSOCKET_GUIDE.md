# React Query & WebSocket Integration Guide

This guide explains how to use React Query and WebSocket in the QuantEdge Pro application for better performance, caching, and real-time updates.

## 🚀 Benefits

### React Query Benefits
- **Automatic Caching**: Data is cached and reused across components
- **Background Refetching**: Stale data is automatically refreshed in the background
- **Request Deduplication**: Multiple components requesting the same data share a single request
- **Loading & Error States**: Built-in state management
- **Optimistic Updates**: UI updates before server confirmation
- **Offline Support**: Works with cached data when offline
- **DevTools**: Visual debugging in development mode

### WebSocket Benefits
- **Real-time Updates**: Instant price and portfolio updates
- **Reduced Server Load**: Less polling, more push notifications
- **Auto-reconnect**: Handles connection drops gracefully
- **Channel-based**: Subscribe to specific data streams

## 📦 Setup

### 1. Wrap App with React Query Provider

In `/home/user/Invvest/frontend/app/layout.tsx`, wrap your app:

```typescript
import { ReactQueryProvider } from '@/components/providers/ReactQueryProvider'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ReactQueryProvider>
          {children}
        </ReactQueryProvider>
      </body>
    </html>
  )
}
```

### 2. Install Dependencies

```bash
cd frontend
npm install @tanstack/react-query@latest @tanstack/react-query-devtools@latest
```

## 🎯 Usage Examples

### Using React Query Hooks

#### Before (Manual State Management)
```typescript
const [loading, setLoading] = useState(true)
const [error, setError] = useState<Error | null>(null)
const [data, setData] = useState<any>(null)

useEffect(() => {
  const fetchData = async () => {
    try {
      setLoading(true)
      const result = await api.portfolio.getHoldings()
      setData(result)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }
  fetchData()
}, [])

if (loading) return <Loading />
if (error) return <ErrorDisplay error={error} />
```

#### After (React Query)
```typescript
import { usePortfolioHoldings } from '@/lib/hooks/useQueries'

const { data, isLoading, isError, error, refetch } = usePortfolioHoldings()

if (isLoading) return <Loading />
if (isError) return <ErrorDisplay error={error} onRetry={refetch} />
```

**Benefits**: 60% less code, automatic caching, background refetching, better TypeScript support.

### Using WebSocket for Real-time Updates

```typescript
import { useWebSocket } from '@/lib/websocket'
import { useCallback } from 'react'

export default function PortfolioPage() {
  const { data, refetch } = usePortfolioHoldings()

  // Handle real-time portfolio updates
  const handlePortfolioUpdate = useCallback((wsData: any) => {
    console.log('Portfolio updated:', wsData)
    refetch() // Refresh data from server
  }, [refetch])

  const { isConnected } = useWebSocket('portfolio', handlePortfolioUpdate)

  return (
    <div>
      {isConnected && (
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-success animate-pulse"></div>
          <span>Live Updates Active</span>
        </div>
      )}
      {/* Your component */}
    </div>
  )
}
```

## 📡 Available WebSocket Channels

- `market-data` - Live price updates for indices and stocks
- `portfolio` - Portfolio value and P&L updates
- `orders` - Order execution notifications
- `notifications` - System alerts and messages

## 🔧 Available Query Hooks

All hooks are in `/home/user/Invvest/frontend/lib/hooks/useQueries.ts`:

### Dashboard
- `useDashboardData()` - Complete dashboard data
- `useMarketData()` - Market indices (auto-refreshes every 5s)
- `usePortfolioMetrics()` - Portfolio summary

### Portfolio
- `usePortfolioHoldings()` - Holdings with tax info
- `usePortfolioData()` - Complete portfolio data

### Risk Management
- `useRiskData()` - All risk metrics, VaR, stress tests

### AI Models
- `useAIModelsData()` - Model leaderboard, regime detection, sentiment

### Backtesting
- `useBacktestData()` - Equity curves, performance metrics

### Algo Trading
- `useAlgoData()` - Strategies, indicators, execution
- `useToggleStrategy()` - Mutation to start/stop strategies

### Options
- `useOptionsData(underlying, expiry)` - Options chain, Greeks, IV skew

### Strategy Builder
- `useStrategyData()` - Templates, payoff diagrams

## 🎨 Advanced Patterns

### Optimistic Updates

```typescript
const { mutate } = useToggleStrategy()

mutate(strategyId, {
  onMutate: async () => {
    // Optimistically update UI before server responds
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['strategies'] })

    // Snapshot current value
    const previous = queryClient.getQueryData(['strategies'])

    // Optimistically update
    queryClient.setQueryData(['strategies'], (old: any) => ({
      ...old,
      status: old.status === 'active' ? 'paused' : 'active'
    }))

    return { previous }
  },
  onError: (err, variables, context) => {
    // Rollback on error
    queryClient.setQueryData(['strategies'], context?.previous)
  },
  onSettled: () => {
    // Always refetch after error or success
    queryClient.invalidateQueries({ queryKey: ['strategies'] })
  },
})
```

### Prefetching for Better UX

```typescript
import { prefetchQueries } from '@/lib/react-query'

// Prefetch data when user hovers over navigation link
<Link
  href="/portfolio"
  onMouseEnter={() => prefetchQueries.portfolio()}
>
  Portfolio
</Link>
```

### Manual Cache Invalidation

```typescript
import { invalidateQueries } from '@/lib/react-query'

// After placing an order
await placeOrder(orderData)
invalidateQueries.portfolio() // Refresh portfolio data
invalidateQueries.algo() // Refresh algo strategies
```

## 🔍 Debugging

### React Query DevTools

Open in development mode (bottom-right corner):
- View all queries and their states
- See cache data
- Force refetch/invalidate
- View query timeline

### WebSocket Debugging

```typescript
// Check connection status
import websocketService from '@/lib/websocket'

console.log('Connected:', websocketService.isConnected())
console.log('State:', websocketService.getConnectionState())
```

## ⚙️ Configuration

### Modify Cache Times

In `/home/user/Invvest/frontend/lib/react-query.ts`:

```typescript
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000, // Consider fresh for 30s
      gcTime: 5 * 60 * 1000, // Keep in cache for 5min
      refetchOnWindowFocus: true, // Refetch on tab focus
      refetchOnReconnect: true, // Refetch on network reconnect
    },
  },
})
```

### Per-Query Override

```typescript
const { data } = useQuery({
  queryKey: ['custom'],
  queryFn: fetchData,
  staleTime: 60 * 1000, // Override: 1 minute
  gcTime: 10 * 60 * 1000, // Override: 10 minutes
  refetchInterval: 5 * 1000, // Poll every 5 seconds
})
```

## 📊 Performance Tips

1. **Use Specific Queries**: Instead of fetching everything, use granular queries
2. **Enable Suspense**: Use `suspense: true` for cleaner loading states
3. **Prefetch on Hover**: Improve perceived performance
4. **Disable Auto-refetch**: For static data like historical backtests
5. **Use WebSocket**: For frequently changing data (prices, portfolio values)

## 🚨 Common Pitfalls

1. **Don't fetch in loops**: Use batch queries instead
2. **Avoid inline functions**: Memoize WebSocket callbacks with `useCallback`
3. **Check enabled flag**: Use `enabled: !!dependency` to prevent premature fetches
4. **Handle SSR**: WebSocket only works in browser, check `typeof window !== 'undefined'`

## 📝 Migration Checklist

- [ ] Wrap app with `ReactQueryProvider`
- [ ] Install dependencies
- [ ] Replace `useState/useEffect` with query hooks
- [ ] Add WebSocket for real-time data
- [ ] Add connection status indicators
- [ ] Test offline behavior
- [ ] Enable DevTools in development
- [ ] Configure cache times for your use case

## 🎯 Example: Complete Page Migration

See `/home/user/Invvest/frontend/app/page.tsx` (Dashboard) for a complete example of:
- React Query integration
- WebSocket real-time updates
- Connection status indicator
- Error handling with retry
- Optimized rendering

---

**Need help?** Check the [React Query docs](https://tanstack.com/query/latest/docs/react/overview) or [WebSocket API docs](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket).
