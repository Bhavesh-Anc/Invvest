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

// Options Advanced API (Institutional Strategies)
export const optionsAdvancedAPI = {
  // Volatility Arbitrage
  getVolatilityOpportunities: (symbol: string, method: string = 'ewma') =>
    fetchAPI(`/api/options/volatility-arbitrage/opportunities?symbol=${symbol}&forecasting_method=${method}`),
  forecastVolatility: (symbol: string, method: string = 'ewma') =>
    fetchAPI(`/api/options/volatility-arbitrage/forecast/${symbol}?method=${method}`),
  calculatePositionSize: (capital: number, optionPrice: number, vega: number, maxVegaExposure: number = 50000) =>
    fetchAPI('/api/options/volatility-arbitrage/position-size', {
      method: 'POST',
      body: JSON.stringify({ capital, option_price: optionPrice, vega, max_vega_exposure: maxVegaExposure }),
    }),

  // Gamma Scalping
  calculateHedgeRatio: (optionsPositions: Array<{ delta: number; quantity: number }>) =>
    fetchAPI('/api/options/gamma-scalping/hedge-ratio', {
      method: 'POST',
      body: JSON.stringify(optionsPositions),
    }),
  simulateGammaScalping: (params: any) =>
    fetchAPI('/api/options/gamma-scalping/simulate', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  optimizeRehedge: (transactionCost: number, gamma: number, realizedVol: number) =>
    fetchAPI(`/api/options/gamma-scalping/optimize-rehedge?transaction_cost=${transactionCost}&gamma=${gamma}&realized_vol=${realizedVol}`),

  // Dispersion Trading
  getDispersionOpportunity: (index: string = 'NIFTY', threshold: number = 0.10) =>
    fetchAPI(`/api/options/dispersion/opportunity?index=${index}&threshold=${threshold}`),
  getCorrelationAnalysis: (index: string = 'NIFTY', lookbackDays: number = 30) =>
    fetchAPI(`/api/options/dispersion/correlation?index=${index}&lookback_days=${lookbackDays}`),

  // Volatility Surface
  getVolatilitySkew: (symbol: string, expiryDate: string) =>
    fetchAPI(`/api/options/volatility-surface/skew?symbol=${symbol}&expiry_date=${expiryDate}`),
  getButterflyArbitrage: (symbol: string, transactionCost: number = 50) =>
    fetchAPI(`/api/options/volatility-surface/butterfly-arbitrage?symbol=${symbol}&transaction_cost=${transactionCost}`),
}

// Machine Learning Strategies API
export const mlStrategiesAPI = {
  // Feature Engineering
  generateFeatures: (symbol: string, startDate: string, endDate: string) =>
    fetchAPI('/api/ml/features/generate', {
      method: 'POST',
      body: JSON.stringify({ symbol, start_date: startDate, end_date: endDate }),
    }),
  getFeatureImportance: (symbol: string, topN: number = 20) =>
    fetchAPI(`/api/ml/features/importance/${symbol}?top_n=${topN}`),

  // LSTM
  trainLSTM: (params: any) =>
    fetchAPI('/api/ml/lstm/train', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  predictPrice: (symbol: string, horizon: string = '1d') =>
    fetchAPI(`/api/ml/lstm/predict/${symbol}?horizon=${horizon}`),

  // XGBoost
  trainXGBoost: (params: any) =>
    fetchAPI('/api/ml/xgboost/train', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  getXGBoostSignals: (symbol: string, threshold: number = 0.002) =>
    fetchAPI(`/api/ml/xgboost/signals/${symbol}?threshold=${threshold}`),

  // Sentiment Analysis
  analyzeSentiment: (newsItems: Array<{ title: string; description?: string }>) =>
    fetchAPI('/api/ml/sentiment/analyze', {
      method: 'POST',
      body: JSON.stringify(newsItems),
    }),
  getSentimentSignal: (symbol: string) =>
    fetchAPI(`/api/ml/sentiment/signal/${symbol}`),
  detectSentimentDivergence: (symbol: string, lookbackDays: number = 30) =>
    fetchAPI(`/api/ml/sentiment/divergence/${symbol}?lookback_days=${lookbackDays}`, {
      method: 'POST',
    }),

  // Ensemble
  ensemblePredict: (symbol: string, models: Array<{ name: string; weight: number }>) =>
    fetchAPI('/api/ml/ensemble/predict', {
      method: 'POST',
      body: JSON.stringify({ symbol, models }),
    }),
}

// Optimal Execution API
export const executionAPI = {
  // VWAP
  generateVWAPSchedule: (params: any) =>
    fetchAPI('/api/execution/vwap/schedule', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  evaluateVWAP: (fills: any[], vwapBenchmark: number) =>
    fetchAPI('/api/execution/vwap/evaluate', {
      method: 'POST',
      body: JSON.stringify({ fills, vwap_benchmark: vwapBenchmark }),
    }),

  // TWAP
  generateTWAPSchedule: (params: any) =>
    fetchAPI('/api/execution/twap/schedule', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  evaluateTWAP: (fills: any[], startPrice: number, endPrice: number) =>
    fetchAPI('/api/execution/twap/evaluate', {
      method: 'POST',
      body: JSON.stringify({ fills, start_price: startPrice, end_price: endPrice }),
    }),

  // Market Impact
  calculateImpact: (quantity: number, adv: number, price: number, executionTime: number = 0.5) =>
    fetchAPI('/api/execution/impact/calculate', {
      method: 'POST',
      body: JSON.stringify({ quantity, adv, price, execution_time: executionTime }),
    }),
  optimizeExecutionTime: (quantity: number, adv: number, price: number, maxTime: number = 1.0) =>
    fetchAPI('/api/execution/impact/optimize-time', {
      method: 'POST',
      body: JSON.stringify({ quantity, adv, price, max_time: maxTime }),
    }),

  // Smart Routing
  routeOrder: (params: any) =>
    fetchAPI('/api/execution/route', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  evaluateVenues: (symbol: string, quantity: number) =>
    fetchAPI(`/api/execution/venues/evaluate?symbol=${symbol}&quantity=${quantity}`),

  // Adaptive Execution
  adjustSchedule: (params: any) =>
    fetchAPI('/api/execution/adaptive/adjust-schedule', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  calculateUrgency: (timeElapsedPct: number, quantityExecutedPct: number) =>
    fetchAPI(`/api/execution/adaptive/urgency?time_elapsed_pct=${timeElapsedPct}&quantity_executed_pct=${quantityExecutedPct}`),
}

// Market Making API
export const marketMakingAPI = {
  // Quote Generation
  generateQuotes: (symbol: string, fairValue: number, volatility: number, orderFlowImbalance: number = 0) =>
    fetchAPI('/api/market-making/quotes/generate', {
      method: 'POST',
      body: JSON.stringify({ symbol, fair_value: fairValue, volatility, order_flow_imbalance: orderFlowImbalance }),
    }),
  analyzeSpread: (symbol: string, volatility: number, inventoryPct: number = 0) =>
    fetchAPI(`/api/market-making/quotes/spread-analysis?symbol=${symbol}&volatility=${volatility}&inventory_pct=${inventoryPct}`),

  // Inventory Management
  getInventoryPosition: (symbol: string) =>
    fetchAPI(`/api/market-making/inventory/position?symbol=${symbol}`),
  checkPositionLimit: (symbol: string, currentPosition: number, proposedTradeSize: number, side: string) =>
    fetchAPI('/api/market-making/inventory/check-limit', {
      method: 'POST',
      body: JSON.stringify({ symbol, current_position: currentPosition, proposed_trade_size: proposedTradeSize, side }),
    }),
  calculateInventoryUrgency: (symbol: string, currentPosition: number, targetPosition: number = 0) =>
    fetchAPI(`/api/market-making/inventory/urgency?symbol=${symbol}&current_position=${currentPosition}&target_position=${targetPosition}`),

  // Order Flow
  calculateOrderFlowImbalance: (buyVolume: number[], sellVolume: number[], lookback: number = 20) =>
    fetchAPI('/api/market-making/flow/imbalance', {
      method: 'POST',
      body: JSON.stringify({ buy_volume: buyVolume, sell_volume: sellVolume, lookback }),
    }),
  detectAdverseSelection: (prices: number[], tradeDirections: number[]) =>
    fetchAPI('/api/market-making/flow/adverse-selection', {
      method: 'POST',
      body: JSON.stringify({ prices, trade_directions: tradeDirections }),
    }),

  // P&L & Fills
  processFill: (symbol: string, side: string, quantity: number, price: number) =>
    fetchAPI('/api/market-making/process-fill', {
      method: 'POST',
      body: JSON.stringify({ symbol, side, quantity, price }),
    }),
  getPnL: (symbol: string, currentPrice?: number) =>
    fetchAPI(`/api/market-making/pnl?symbol=${symbol}${currentPrice ? `&current_price=${currentPrice}` : ''}`),

  // Volatility
  estimateVolatility: (symbol: string, lookbackDays: number = 30) =>
    fetchAPI(`/api/market-making/volatility/estimate?symbol=${symbol}&lookback_days=${lookbackDays}`),

  // Reset
  resetMarketMaker: (symbol: string) =>
    fetchAPI(`/api/market-making/reset/${symbol}`, { method: 'POST' }),

  // WebSocket (for real-time quotes)
  connectQuoteStream: (symbol: string): WebSocket => {
    const wsUrl = API_BASE_URL.replace('http', 'ws')
    return new WebSocket(`${wsUrl}/api/market-making/ws/quotes/${symbol}`)
  },
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
  // New institutional quant strategy APIs
  optionsAdvanced: optionsAdvancedAPI,
  mlStrategies: mlStrategiesAPI,
  execution: executionAPI,
  marketMaking: marketMakingAPI,
}

export default api
