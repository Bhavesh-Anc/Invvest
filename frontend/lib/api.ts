"""
QuantEdge Pro API Client
Centralized API client for backend communication
"""

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class APIError extends Error {
  constructor(public status: number, message: string, public data?: any) {
    super(message)
    this.name = 'APIError'
  }
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const defaultHeaders = {
    'Content-Type': 'application/json',
  }

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  }

  try {
    const response = await fetch(url, config)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new APIError(
        response.status,
        errorData.detail || `API Error: ${response.statusText}`,
        errorData
      )
    }

    return await response.json()
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

// Dashboard API
export const dashboardAPI = {
  getDashboardData: () => fetchAPI('/api/dashboard'),
  getMarketData: () => fetchAPI('/api/dashboard/market-data'),
  getPortfolioMetrics: () => fetchAPI('/api/dashboard/portfolio-metrics'),
  getChartData: (days: number = 30) => fetchAPI(`/api/dashboard/chart-data?days=${days}`),
  getSectorAllocation: () => fetchAPI('/api/dashboard/sector-allocation'),
  getRiskMetrics: () => fetchAPI('/api/dashboard/risk-metrics'),
  getPositions: () => fetchAPI('/api/dashboard/positions'),
  getMarketRegime: () => fetchAPI('/api/dashboard/market-regime'),
}

// Portfolio API
export const portfolioAPI = {
  getHoldings: () => fetchAPI('/api/portfolio/holdings'),
  getTaxSummary: () => fetchAPI('/api/portfolio/tax-summary'),
  getMonthlyReturns: (months: number = 6) => fetchAPI(`/api/portfolio/monthly-returns?months=${months}`),
  getRiskMetrics: () => fetchAPI('/api/portfolio/risk-metrics'),
  getCorrelation: () => fetchAPI('/api/portfolio/correlation'),
  getDrawdownHistory: (days: number = 180) => fetchAPI(`/api/portfolio/drawdown-history?days=${days}`),
  getSummary: () => fetchAPI('/api/portfolio/summary'),
}

// Options API
export const optionsAPI = {
  getGreeksSummary: () => fetchAPI('/api/options/greeks-summary'),
  getOptionsChain: (underlying: string = 'NIFTY', expiry: string = '25-JAN-2024') =>
    fetchAPI(`/api/options/options-chain?underlying=${underlying}&expiry=${expiry}`),
  getIVSkew: (underlying: string = 'NIFTY', expiry: string = '25-JAN-2024') =>
    fetchAPI(`/api/options/iv-skew?underlying=${underlying}&expiry=${expiry}`),
  getGreeksEvolution: () => fetchAPI('/api/options/greeks-evolution'),
  getOIDistribution: (underlying: string = 'NIFTY', expiry: string = '25-JAN-2024') =>
    fetchAPI(`/api/options/oi-distribution?underlying=${underlying}&expiry=${expiry}`),
  getPCRAnalysis: (underlying: string = 'NIFTY', expiry: string = '25-JAN-2024') =>
    fetchAPI(`/api/options/pcr-analysis?underlying=${underlying}&expiry=${expiry}`),
  getATMGreeks: (underlying: string = 'NIFTY', expiry: string = '25-JAN-2024') =>
    fetchAPI(`/api/options/atm-greeks?underlying=${underlying}&expiry=${expiry}`),
  getExpiryDates: (underlying: string = 'NIFTY') =>
    fetchAPI(`/api/options/expiry-dates?underlying=${underlying}`),
}

// Strategy API
export const strategyAPI = {
  getTemplates: () => fetchAPI('/api/strategy/templates'),
  analyzeStrategy: (strategy: any) =>
    fetchAPI('/api/strategy/analyze', {
      method: 'POST',
      body: JSON.stringify(strategy),
    }),
  getPayoffDiagram: (strategyId: string = 'bull-call-spread') =>
    fetchAPI(`/api/strategy/payoff-diagram?strategy_id=${strategyId}`),
  getExpiryCalendar: () => fetchAPI('/api/strategy/expiry-calendar'),
  getGreeksOptimization: () => fetchAPI('/api/strategy/greeks-optimization'),
  saveStrategy: (strategy: any) =>
    fetchAPI('/api/strategy/save-strategy', {
      method: 'POST',
      body: JSON.stringify(strategy),
    }),
  getSavedStrategies: () => fetchAPI('/api/strategy/saved-strategies'),
}

// Algo Trading API
export const algoAPI = {
  getStrategies: () => fetchAPI('/api/algo/strategies'),
  getIntradayPerformance: () => fetchAPI('/api/algo/intraday-performance'),
  getTechnicalIndicators: (symbol: string = 'NIFTY') =>
    fetchAPI(`/api/algo/technical-indicators?symbol=${symbol}`),
  getExecutionTimeline: (limit: number = 10) =>
    fetchAPI(`/api/algo/execution-timeline?limit=${limit}`),
  getMarketMicrostructure: () => fetchAPI('/api/algo/market-microstructure'),
  toggleStrategy: (strategyId: string) =>
    fetchAPI(`/api/algo/strategy/${strategyId}/toggle`, { method: 'POST' }),
  stopStrategy: (strategyId: string) =>
    fetchAPI(`/api/algo/strategy/${strategyId}/stop`, { method: 'POST' }),
  getSummary: () => fetchAPI('/api/algo/summary'),
}

// Risk Management API
export const riskAPI = {
  getMetrics: () => fetchAPI('/api/risk/metrics'),
  getVaRHistory: (days: number = 30) => fetchAPI(`/api/risk/var-history?days=${days}`),
  getDrawdownAnalysis: (days: number = 180) => fetchAPI(`/api/risk/drawdown-analysis?days=${days}`),
  getStressTests: () => fetchAPI('/api/risk/stress-tests'),
  getPositionRisk: () => fetchAPI('/api/risk/position-risk'),
  getCircuitBreakers: () => fetchAPI('/api/risk/circuit-breakers'),
  getKellyCriterion: () => fetchAPI('/api/risk/kelly-criterion'),
  getComplianceStatus: () => fetchAPI('/api/risk/compliance-status'),
  evaluateTrade: (symbol: string, quantity: number, action: string) =>
    fetchAPI('/api/risk/evaluate-trade', {
      method: 'POST',
      body: JSON.stringify({ symbol, quantity, action }),
    }),
}

// Backtesting API
export const backtestAPI = {
  getConfig: () => fetchAPI('/api/backtest/config'),
  updateConfig: (config: any) =>
    fetchAPI('/api/backtest/config', {
      method: 'POST',
      body: JSON.stringify(config),
    }),
  getEquityCurve: (days: number = 180) => fetchAPI(`/api/backtest/equity-curve?days=${days}`),
  getPerformanceMetrics: () => fetchAPI('/api/backtest/performance-metrics'),
  getMonthlyReturns: (months: number = 6) => fetchAPI(`/api/backtest/monthly-returns?months=${months}`),
  getReturnDistribution: () => fetchAPI('/api/backtest/return-distribution'),
  getWalkForward: () => fetchAPI('/api/backtest/walk-forward'),
  getPaperTrades: (limit: number = 20) => fetchAPI(`/api/backtest/paper-trading?limit=${limit}`),
  runBacktest: (strategyId: string, startDate: string, endDate: string, initialCapital: number = 1000000) =>
    fetchAPI('/api/backtest/run-backtest', {
      method: 'POST',
      body: JSON.stringify({ strategy_id: strategyId, start_date: startDate, end_date: endDate, initial_capital: initialCapital }),
    }),
  getSummary: () => fetchAPI('/api/backtest/summary'),
}

// AI Models API
export const modelsAPI = {
  getModelLeaderboard: () => fetchAPI('/api/models/model-leaderboard'),
  getRegimeDetection: (days: number = 60) => fetchAPI(`/api/models/regime-detection?days=${days}`),
  getFeatureImportance: (model: string = 'XGBoost') => fetchAPI(`/api/models/feature-importance?model=${model}`),
  getSentimentAnalysis: (days: number = 7) => fetchAPI(`/api/models/sentiment-analysis?days=${days}`),
  getModelPerformance: () => fetchAPI('/api/models/model-performance'),
  getMLPipeline: () => fetchAPI('/api/models/ml-pipeline'),
  getCurrentRegime: () => fetchAPI('/api/models/current-regime'),
  getAnomalyDetection: () => fetchAPI('/api/models/anomaly-detection'),
  getRLSuggestions: () => fetchAPI('/api/models/rl-suggestions'),
  retrainModel: (modelName: string) =>
    fetchAPI('/api/models/retrain-model', {
      method: 'POST',
      body: JSON.stringify({ model_name: modelName }),
    }),
  getModelDrift: (modelName: string = 'XGBoost') => fetchAPI(`/api/models/model-drift?model_name=${modelName}`),
  getSentimentSummary: () => fetchAPI('/api/models/sentiment-summary'),
}

// Health Check
export const healthAPI = {
  check: () => fetchAPI('/api/health'),
}

// Export all APIs
export const api = {
  dashboard: dashboardAPI,
  portfolio: portfolioAPI,
  options: optionsAPI,
  strategy: strategyAPI,
  algo: algoAPI,
  risk: riskAPI,
  backtest: backtestAPI,
  models: modelsAPI,
  health: healthAPI,
}

export default api
