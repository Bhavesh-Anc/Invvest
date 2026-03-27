/**
 * React Query Configuration for QuantEdge Pro
 * Provides caching, background refetching, and optimistic updates
 */

import { QueryClient } from '@tanstack/react-query'

// Create a client with custom configuration
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Stale time: Data is considered fresh for 30 seconds
      staleTime: 30 * 1000,

      // Cache time: Keep unused data in cache for 5 minutes
      gcTime: 5 * 60 * 1000,

      // Refetch on window focus for real-time feel
      refetchOnWindowFocus: true,

      // Refetch on reconnect
      refetchOnReconnect: true,

      // Don't refetch on mount if data is fresh
      refetchOnMount: false,

      // Retry failed requests 2 times with exponential backoff
      retry: 2,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

      // Show stale data while refetching
      keepPreviousData: true,
    },
    mutations: {
      // Retry mutations once
      retry: 1,
    },
  },
})

// Query keys for type safety and consistency
export const queryKeys = {
  // Dashboard
  dashboard: {
    all: ['dashboard'] as const,
    data: () => [...queryKeys.dashboard.all, 'data'] as const,
    marketData: () => [...queryKeys.dashboard.all, 'market-data'] as const,
    portfolioMetrics: () => [...queryKeys.dashboard.all, 'portfolio-metrics'] as const,
    chartData: (days: number) => [...queryKeys.dashboard.all, 'chart-data', days] as const,
    sectorAllocation: () => [...queryKeys.dashboard.all, 'sector-allocation'] as const,
    riskMetrics: () => [...queryKeys.dashboard.all, 'risk-metrics'] as const,
    positions: () => [...queryKeys.dashboard.all, 'positions'] as const,
    marketRegime: () => [...queryKeys.dashboard.all, 'market-regime'] as const,
  },

  // Portfolio
  portfolio: {
    all: ['portfolio'] as const,
    holdings: () => [...queryKeys.portfolio.all, 'holdings'] as const,
    taxSummary: () => [...queryKeys.portfolio.all, 'tax-summary'] as const,
    monthlyReturns: (months: number) => [...queryKeys.portfolio.all, 'monthly-returns', months] as const,
    riskMetrics: () => [...queryKeys.portfolio.all, 'risk-metrics'] as const,
    correlation: () => [...queryKeys.portfolio.all, 'correlation'] as const,
    drawdown: (days: number) => [...queryKeys.portfolio.all, 'drawdown', days] as const,
    summary: () => [...queryKeys.portfolio.all, 'summary'] as const,
  },

  // Options
  options: {
    all: ['options'] as const,
    greeksSummary: () => [...queryKeys.options.all, 'greeks-summary'] as const,
    chain: (underlying: string, expiry: string) => [...queryKeys.options.all, 'chain', underlying, expiry] as const,
    ivSkew: (underlying: string, expiry: string) => [...queryKeys.options.all, 'iv-skew', underlying, expiry] as const,
    greeksEvolution: () => [...queryKeys.options.all, 'greeks-evolution'] as const,
    oiDistribution: (underlying: string, expiry: string) => [...queryKeys.options.all, 'oi-distribution', underlying, expiry] as const,
    pcrAnalysis: (underlying: string, expiry: string) => [...queryKeys.options.all, 'pcr-analysis', underlying, expiry] as const,
    atmGreeks: (underlying: string, expiry: string) => [...queryKeys.options.all, 'atm-greeks', underlying, expiry] as const,
    expiryDates: (underlying: string) => [...queryKeys.options.all, 'expiry-dates', underlying] as const,
  },

  // Strategy
  strategy: {
    all: ['strategy'] as const,
    templates: () => [...queryKeys.strategy.all, 'templates'] as const,
    payoffDiagram: (strategyId: string) => [...queryKeys.strategy.all, 'payoff-diagram', strategyId] as const,
    expiryCalendar: () => [...queryKeys.strategy.all, 'expiry-calendar'] as const,
    greeksOptimization: () => [...queryKeys.strategy.all, 'greeks-optimization'] as const,
    savedStrategies: () => [...queryKeys.strategy.all, 'saved-strategies'] as const,
  },

  // Algo Trading
  algo: {
    all: ['algo'] as const,
    strategies: () => [...queryKeys.algo.all, 'strategies'] as const,
    intradayPerformance: () => [...queryKeys.algo.all, 'intraday-performance'] as const,
    technicalIndicators: (symbol: string) => [...queryKeys.algo.all, 'technical-indicators', symbol] as const,
    executionTimeline: (limit: number) => [...queryKeys.algo.all, 'execution-timeline', limit] as const,
    marketMicrostructure: () => [...queryKeys.algo.all, 'market-microstructure'] as const,
    summary: () => [...queryKeys.algo.all, 'summary'] as const,
  },

  // Risk Management
  risk: {
    all: ['risk'] as const,
    metrics: () => [...queryKeys.risk.all, 'metrics'] as const,
    varHistory: (days: number) => [...queryKeys.risk.all, 'var-history', days] as const,
    drawdownAnalysis: (days: number) => [...queryKeys.risk.all, 'drawdown-analysis', days] as const,
    stressTests: () => [...queryKeys.risk.all, 'stress-tests'] as const,
    positionRisk: () => [...queryKeys.risk.all, 'position-risk'] as const,
    circuitBreakers: () => [...queryKeys.risk.all, 'circuit-breakers'] as const,
    kellyCriterion: () => [...queryKeys.risk.all, 'kelly-criterion'] as const,
    complianceStatus: () => [...queryKeys.risk.all, 'compliance-status'] as const,
  },

  // Backtesting
  backtest: {
    all: ['backtest'] as const,
    config: () => [...queryKeys.backtest.all, 'config'] as const,
    equityCurve: (days: number) => [...queryKeys.backtest.all, 'equity-curve', days] as const,
    performanceMetrics: () => [...queryKeys.backtest.all, 'performance-metrics'] as const,
    monthlyReturns: (months: number) => [...queryKeys.backtest.all, 'monthly-returns', months] as const,
    returnDistribution: () => [...queryKeys.backtest.all, 'return-distribution'] as const,
    walkForward: () => [...queryKeys.backtest.all, 'walk-forward'] as const,
    paperTrades: (limit: number) => [...queryKeys.backtest.all, 'paper-trades', limit] as const,
    summary: () => [...queryKeys.backtest.all, 'summary'] as const,
  },

  // AI Models
  models: {
    all: ['models'] as const,
    leaderboard: () => [...queryKeys.models.all, 'leaderboard'] as const,
    regimeDetection: (days: number) => [...queryKeys.models.all, 'regime-detection', days] as const,
    featureImportance: (model: string) => [...queryKeys.models.all, 'feature-importance', model] as const,
    sentimentAnalysis: (days: number) => [...queryKeys.models.all, 'sentiment-analysis', days] as const,
    modelPerformance: () => [...queryKeys.models.all, 'model-performance'] as const,
    mlPipeline: () => [...queryKeys.models.all, 'ml-pipeline'] as const,
    currentRegime: () => [...queryKeys.models.all, 'current-regime'] as const,
    anomalyDetection: () => [...queryKeys.models.all, 'anomaly-detection'] as const,
    rlSuggestions: () => [...queryKeys.models.all, 'rl-suggestions'] as const,
    modelDrift: (modelName: string) => [...queryKeys.models.all, 'model-drift', modelName] as const,
    sentimentSummary: () => [...queryKeys.models.all, 'sentiment-summary'] as const,
  },

  // Health
  health: {
    all: ['health'] as const,
    check: () => [...queryKeys.health.all, 'check'] as const,
  },
} as const

// Helper to invalidate all queries for a module
export const invalidateQueries = {
  dashboard: () => queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all }),
  portfolio: () => queryClient.invalidateQueries({ queryKey: queryKeys.portfolio.all }),
  options: () => queryClient.invalidateQueries({ queryKey: queryKeys.options.all }),
  strategy: () => queryClient.invalidateQueries({ queryKey: queryKeys.strategy.all }),
  algo: () => queryClient.invalidateQueries({ queryKey: queryKeys.algo.all }),
  risk: () => queryClient.invalidateQueries({ queryKey: queryKeys.risk.all }),
  backtest: () => queryClient.invalidateQueries({ queryKey: queryKeys.backtest.all }),
  models: () => queryClient.invalidateQueries({ queryKey: queryKeys.models.all }),
  all: () => queryClient.invalidateQueries(),
}

// Prefetch helpers for better UX
export const prefetchQueries = {
  dashboard: () => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.dashboard.data(),
      queryFn: async () => {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/dashboard`)
        return response.json()
      },
    })
  },
  portfolio: () => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.portfolio.holdings(),
      queryFn: async () => {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/portfolio/holdings`)
        return response.json()
      },
    })
  },
}
