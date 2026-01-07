/**
 * React Query Hooks for QuantEdge Pro
 * Type-safe hooks for all API endpoints with automatic caching and refetching
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import api from '@/lib/api'

// ============================================================================
// Dashboard Hooks
// ============================================================================

export function useDashboardData() {
  return useQuery({
    queryKey: queryKeys.dashboard.data(),
    queryFn: () => api.dashboard.getDashboardData(),
    staleTime: 30 * 1000, // 30 seconds
  })
}

export function useMarketData() {
  return useQuery({
    queryKey: queryKeys.dashboard.marketData(),
    queryFn: () => api.dashboard.getMarketData(),
    refetchInterval: 5 * 1000, // Refetch every 5 seconds for real-time feel
  })
}

export function usePortfolioMetrics() {
  return useQuery({
    queryKey: queryKeys.dashboard.portfolioMetrics(),
    queryFn: () => api.dashboard.getPortfolioMetrics(),
  })
}

// ============================================================================
// Portfolio Hooks
// ============================================================================

export function usePortfolioHoldings() {
  return useQuery({
    queryKey: queryKeys.portfolio.holdings(),
    queryFn: () => api.portfolio.getHoldings(),
  })
}

export function usePortfolioData() {
  return useQuery({
    queryKey: queryKeys.portfolio.all,
    queryFn: async () => {
      const [holdings, taxSummary, monthlyReturns, riskMetrics, correlation, drawdown] = await Promise.all([
        api.portfolio.getHoldings(),
        api.portfolio.getTaxSummary(),
        api.portfolio.getMonthlyReturns(6),
        api.portfolio.getRiskMetrics(),
        api.portfolio.getCorrelation(),
        api.portfolio.getDrawdownHistory(180),
      ])
      return { holdings, taxSummary, monthlyReturns, riskMetrics, correlation, drawdown }
    },
  })
}

// ============================================================================
// Risk Management Hooks
// ============================================================================

export function useRiskData() {
  return useQuery({
    queryKey: queryKeys.risk.all,
    queryFn: async () => {
      const [metrics, varHistory, drawdown, stress, positionRisk, breakers, kelly] = await Promise.all([
        api.risk.getMetrics(),
        api.risk.getVaRHistory(30),
        api.risk.getDrawdownAnalysis(180),
        api.risk.getStressTests(),
        api.risk.getPositionRisk(),
        api.risk.getCircuitBreakers(),
        api.risk.getKellyCriterion(),
      ])
      return { metrics, varHistory, drawdown, stress, positionRisk, breakers, kelly }
    },
  })
}

// ============================================================================
// AI Models Hooks
// ============================================================================

export function useAIModelsData() {
  return useQuery({
    queryKey: queryKeys.models.all,
    queryFn: async () => {
      const [leaderboard, regime, features, sentiment, sentSummary, performance, pipeline] = await Promise.all([
        api.models.getModelLeaderboard(),
        api.models.getRegimeDetection(60),
        api.models.getFeatureImportance('XGBoost'),
        api.models.getSentimentAnalysis(7),
        api.models.getSentimentSummary(),
        api.models.getModelPerformance(),
        api.models.getMLPipeline(),
      ])
      return { leaderboard, regime, features, sentiment, sentSummary, performance, pipeline }
    },
  })
}

// ============================================================================
// Backtesting Hooks
// ============================================================================

export function useBacktestData() {
  return useQuery({
    queryKey: queryKeys.backtest.all,
    queryFn: async () => {
      const [config, equityCurve, metrics, monthlyReturns, returnDist, walkForward, paperTrades] = await Promise.all([
        api.backtest.getConfig(),
        api.backtest.getEquityCurve(180),
        api.backtest.getPerformanceMetrics(),
        api.backtest.getMonthlyReturns(6),
        api.backtest.getReturnDistribution(),
        api.backtest.getWalkForward(),
        api.backtest.getPaperTrades(20),
      ])
      return { config, equityCurve, metrics, monthlyReturns, returnDist, walkForward, paperTrades }
    },
  })
}

// ============================================================================
// Algo Trading Hooks
// ============================================================================

export function useAlgoData() {
  return useQuery({
    queryKey: queryKeys.algo.all,
    queryFn: async () => {
      const [strategies, performance, indicators, timeline, marketMicro] = await Promise.all([
        api.algo.getStrategies(),
        api.algo.getIntradayPerformance(),
        api.algo.getTechnicalIndicators('NIFTY'),
        api.algo.getExecutionTimeline(10),
        api.algo.getMarketMicrostructure(),
      ])
      return { strategies, performance, indicators, timeline, marketMicro }
    },
  })
}

export function useToggleStrategy() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (strategyId: string) => api.algo.toggleStrategy(strategyId),
    onSuccess: () => {
      // Invalidate and refetch strategies
      queryClient.invalidateQueries({ queryKey: queryKeys.algo.strategies() })
    },
  })
}

// ============================================================================
// Options Hooks
// ============================================================================

export function useOptionsData(underlying: string, expiry: string) {
  return useQuery({
    queryKey: [...queryKeys.options.all, underlying, expiry],
    queryFn: async () => {
      const [greeks, chain, skew, evolution, oiDist, pcr] = await Promise.all([
        api.options.getGreeksSummary(),
        api.options.getOptionsChain(underlying, expiry),
        api.options.getIVSkew(underlying, expiry),
        api.options.getGreeksEvolution(),
        api.options.getOIDistribution(underlying, expiry),
        api.options.getPCRAnalysis(underlying, expiry),
      ])
      return { greeks, chain, skew, evolution, oiDist, pcr }
    },
    enabled: !!underlying && !!expiry, // Only fetch if we have both params
  })
}

// ============================================================================
// Strategy Builder Hooks
// ============================================================================

export function useStrategyData() {
  return useQuery({
    queryKey: queryKeys.strategy.all,
    queryFn: async () => {
      const [templates, payoff, calendar, greeksOpt] = await Promise.all([
        api.strategy.getTemplates(),
        api.strategy.getPayoffDiagram('bull-call-spread'),
        api.strategy.getExpiryCalendar(),
        api.strategy.getGreeksOptimization(),
      ])
      return { templates, payoff, calendar, greeksOpt }
    },
  })
}

// ============================================================================
// Health Check Hook
// ============================================================================

export function useHealthCheck() {
  return useQuery({
    queryKey: queryKeys.health.check(),
    queryFn: () => api.health.check(),
    refetchInterval: 60 * 1000, // Check every minute
    retry: 3,
  })
}
