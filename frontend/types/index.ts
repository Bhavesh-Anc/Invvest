export interface Portfolio {
  totalValue: number
  todayPnl: number
  todayPnlPercent: number
  marginUsed: number
  marginAvailable: number
  sharpeRatio: number
}

export interface Position {
  symbol: string
  type: 'Cash' | 'Option' | 'Future'
  qty: number
  entry: number
  ltp: number
  value: number
  pnl: number
  pnlPercent: number
}

export interface Holding {
  symbol: string
  sector: string
  qty: number
  avgPrice: number
  ltp: number
  value: number
  pnl: number
  pnlPercent: number
  stcg?: number
  ltcg?: number
}

export interface OptionsChainRow {
  callOI: number
  callVol: number
  callIV: number
  callLTP: number
  strike: number
  putLTP: number
  putIV: number
  putVol: number
  putOI: number
}

export interface Greeks {
  delta: number
  gamma: number
  theta: number
  vega: number
  rho: number
}

export interface StrategyLeg {
  type: 'Buy' | 'Sell'
  option: 'Call' | 'Put'
  strike: number
  expiry: string
  qty: number
  premium: number
  total: number
}

export interface Strategy {
  name: string
  legs: StrategyLeg[]
  netPremium: number
  maxProfit: number
  maxLoss: number
  marginRequired: number
  breakeven: number[]
  profitTarget?: number
  riskReward?: number
}

export interface AlgoStrategy {
  id: string
  name: string
  type: string
  status: 'ACTIVE' | 'PAUSED' | 'INACTIVE'
  trades: number
  winRate: number
  pnl: number
  sharpe: number
}

export interface TechnicalIndicator {
  name: string
  value: number
  signal: 'Bullish' | 'Bearish' | 'Neutral'
  description?: string
}

export interface Trade {
  time: string
  symbol: string
  side: 'BUY' | 'SELL'
  qty: number
  price: number
  status: 'filled' | 'partial' | 'pending' | 'rejected'
}

export interface RiskMetric {
  name: string
  value: number | string
  status?: 'Better' | 'Neutral' | 'Worse'
  benchmark?: number | string
}

export interface MarketData {
  nifty: number
  niftyChange: number
  sensex: number
  sensexChange: number
  bankNifty: number
  bankNiftyChange: number
}
