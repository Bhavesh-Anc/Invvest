'use client'

import React, { useState } from 'react'
import {
  Play, Pause, Square, TrendingUp, TrendingDown,
  Activity, Zap, Clock, DollarSign, Target,
  AlertCircle, CheckCircle, XCircle, Settings,
  BarChart3, LineChart as LineChartIcon, RefreshCw
} from 'lucide-react'
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine
} from 'recharts'
import MetricCard from '@/components/ui/MetricCard'
import { formatCurrency, formatPercentage } from '@/lib/utils'

interface AlgoStrategy {
  id: string
  name: string
  status: 'active' | 'paused' | 'stopped'
  todayPnl: number
  todayPnlPercent: number
  totalTrades: number
  winRate: number
  sharpe: number
  capital: number
  leverage: number
}

export default function AlgoTradingPage() {
  const [strategies, setStrategies] = useState<AlgoStrategy[]>([
    {
      id: 'strat-1',
      name: 'Mean Reversion - Bank Nifty',
      status: 'active',
      todayPnl: 18450,
      todayPnlPercent: 3.24,
      totalTrades: 12,
      winRate: 75,
      sharpe: 2.14,
      capital: 569250,
      leverage: 2.5,
    },
    {
      id: 'strat-2',
      name: 'Momentum Breakout - Nifty IT',
      status: 'active',
      todayPnl: -4250,
      todayPnlPercent: -0.92,
      totalTrades: 8,
      winRate: 62.5,
      sharpe: 1.86,
      capital: 462000,
      leverage: 3.0,
    },
    {
      id: 'strat-3',
      name: 'Volatility Arbitrage - Options',
      status: 'paused',
      todayPnl: 12800,
      todayPnlPercent: 1.78,
      totalTrades: 24,
      winRate: 83.3,
      sharpe: 2.42,
      capital: 719200,
      leverage: 1.5,
    },
    {
      id: 'strat-4',
      name: 'Pair Trading - Banking Sector',
      status: 'active',
      todayPnl: 9650,
      todayPnlPercent: 2.41,
      totalTrades: 6,
      winRate: 66.7,
      sharpe: 1.68,
      capital: 400150,
      leverage: 2.0,
    },
  ])

  // Intraday performance data
  const intradayPerformance = [
    { time: '09:15', pnl: 0, cumulative: 0 },
    { time: '09:30', pnl: 2450, cumulative: 2450 },
    { time: '10:00', pnl: 1850, cumulative: 4300 },
    { time: '10:30', pnl: -1200, cumulative: 3100 },
    { time: '11:00', pnl: 3650, cumulative: 6750 },
    { time: '11:30', pnl: 2100, cumulative: 8850 },
    { time: '12:00', pnl: -950, cumulative: 7900 },
    { time: '12:30', pnl: 4200, cumulative: 12100 },
    { time: '13:00', pnl: 1850, cumulative: 13950 },
    { time: '13:30', pnl: 3250, cumulative: 17200 },
    { time: '14:00', pnl: 2800, cumulative: 20000 },
    { time: '14:30', pnl: 1650, cumulative: 21650 },
    { time: '15:00', pnl: 3200, cumulative: 24850 },
    { time: '15:30', pnl: 1800, cumulative: 26650 },
  ]

  // Technical indicators
  const technicalIndicators = [
    { name: 'RSI (14)', value: 58.4, signal: 'Neutral', threshold: 50, color: 'warning' },
    { name: 'MACD', value: 12.8, signal: 'Bullish', threshold: 0, color: 'success' },
    { name: 'ADX (14)', value: 24.6, signal: 'Weak Trend', threshold: 25, color: 'warning' },
    { name: 'Bollinger %B', value: 0.68, signal: 'Overbought', threshold: 0.8, color: 'danger' },
    { name: 'Stochastic', value: 72.3, signal: 'Overbought', threshold: 80, color: 'warning' },
    { name: 'ATR (14)', value: 142.5, signal: 'High Vol', threshold: 100, color: 'danger' },
  ]

  // Execution timeline
  const executionTimeline = [
    {
      time: '14:52:18',
      strategy: 'Mean Reversion - Bank Nifty',
      action: 'BUY',
      instrument: 'BANKNIFTY 25JAN24 47600 CE',
      quantity: 50,
      price: 245.75,
      status: 'executed',
      pnl: 0,
    },
    {
      time: '14:38:45',
      strategy: 'Pair Trading - Banking Sector',
      action: 'SELL',
      instrument: 'HDFCBANK FUT',
      quantity: 550,
      price: 1642.80,
      status: 'executed',
      pnl: 2850,
    },
    {
      time: '14:15:22',
      strategy: 'Momentum Breakout - Nifty IT',
      action: 'BUY',
      instrument: 'TCS',
      quantity: 100,
      price: 3789.25,
      status: 'executed',
      pnl: -1200,
    },
    {
      time: '13:47:11',
      strategy: 'Mean Reversion - Bank Nifty',
      action: 'SELL',
      instrument: 'BANKNIFTY 25JAN24 47500 PE',
      quantity: 75,
      price: 182.40,
      status: 'executed',
      pnl: 5625,
    },
    {
      time: '13:22:56',
      strategy: 'Volatility Arbitrage - Options',
      action: 'BUY',
      instrument: 'NIFTY 25JAN24 21900 CE',
      quantity: 150,
      price: 218.50,
      status: 'partial',
      pnl: 0,
    },
    {
      time: '12:58:33',
      strategy: 'Pair Trading - Banking Sector',
      action: 'BUY',
      instrument: 'ICICIBANK FUT',
      quantity: 625,
      price: 1025.75,
      status: 'executed',
      pnl: 3120,
    },
  ]

  // Market microstructure
  const marketMicrostructure = {
    bidAskSpread: 0.15,
    marketDepth: 'Good',
    orderBookImbalance: 0.62,
    volumeProfile: 'Above Average',
    tickerTape: [
      { symbol: 'NIFTY', price: 21894.35, change: 1.24, volume: '124.5Cr' },
      { symbol: 'BANKNIFTY', price: 47623.90, change: -0.42, volume: '89.2Cr' },
      { symbol: 'FINNIFTY', price: 20145.75, change: 0.68, volume: '34.8Cr' },
    ],
  }

  const totalTodayPnl = strategies.reduce((sum, s) => sum + s.todayPnl, 0)
  const totalCapital = strategies.reduce((sum, s) => sum + s.capital, 0)
  const totalTodayPnlPercent = (totalTodayPnl / totalCapital) * 100
  const activeStrategies = strategies.filter(s => s.status === 'active').length
  const totalTrades = strategies.reduce((sum, s) => sum + s.totalTrades, 0)

  const toggleStrategyStatus = (id: string) => {
    setStrategies(
      strategies.map(s => {
        if (s.id === id) {
          return {
            ...s,
            status: s.status === 'active' ? 'paused' : 'active',
          }
        }
        return s
      })
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Algorithmic Trading</h1>
          <p className="text-muted-foreground">Live strategy monitoring and execution analytics</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors">
            <RefreshCw className="w-4 h-4 inline mr-2" />
            Refresh
          </button>
          <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors">
            <Settings className="w-4 h-4 inline mr-2" />
            Configure
          </button>
        </div>
      </div>

      {/* Overall Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Today's P&L"
          value={formatCurrency(totalTodayPnl)}
          change={totalTodayPnlPercent}
          changeLabel="return"
          trend={totalTodayPnl >= 0 ? 'up' : 'down'}
          icon={totalTodayPnl >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
        />
        <MetricCard
          title="Active Strategies"
          value={activeStrategies.toString()}
          icon={<Zap className="w-5 h-5" />}
          subtitle={`${strategies.length} total strategies`}
        />
        <MetricCard
          title="Total Trades"
          value={totalTrades.toString()}
          icon={<Activity className="w-5 h-5" />}
          subtitle="Across all strategies"
        />
        <MetricCard
          title="Total Capital"
          value={formatCurrency(totalCapital)}
          icon={<DollarSign className="w-5 h-5" />}
          subtitle="Deployed capital"
        />
      </div>

      {/* Intraday Performance */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <LineChartIcon className="w-5 h-5 text-purple-500" />
          Intraday Performance
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={intradayPerformance}>
            <defs>
              <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
            <XAxis dataKey="time" stroke="#888" />
            <YAxis stroke="#888" label={{ value: 'Cumulative P&L (₹)', angle: -90, position: 'insideLeft', fill: '#888' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f1429',
                border: '1px solid #1f2740',
                borderRadius: '8px',
              }}
            />
            <Area
              type="monotone"
              dataKey="cumulative"
              stroke="#10b981"
              strokeWidth={2}
              fill="url(#colorPnl)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Active Strategies */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-purple-500" />
          Active Strategies
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {strategies.map(strategy => (
            <div
              key={strategy.id}
              className="p-4 bg-dark-700/30 rounded-lg border border-dark-600 hover:border-purple-500/50 transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-sm font-bold text-white mb-1">{strategy.name}</h3>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        strategy.status === 'active'
                          ? 'bg-success/10 text-success'
                          : strategy.status === 'paused'
                          ? 'bg-warning/10 text-warning'
                          : 'bg-danger/10 text-danger'
                      }`}
                    >
                      {strategy.status.toUpperCase()}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {strategy.leverage}x Leverage
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {strategy.status === 'active' ? (
                    <button
                      onClick={() => toggleStrategyStatus(strategy.id)}
                      className="p-2 text-warning hover:bg-warning/10 rounded transition-colors"
                      title="Pause"
                    >
                      <Pause className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      onClick={() => toggleStrategyStatus(strategy.id)}
                      className="p-2 text-success hover:bg-success/10 rounded transition-colors"
                      title="Resume"
                    >
                      <Play className="w-4 h-4" />
                    </button>
                  )}
                  <button className="p-2 text-danger hover:bg-danger/10 rounded transition-colors" title="Stop">
                    <Square className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-3">
                <div className="p-2 bg-dark-700/50 rounded">
                  <div className="text-xs text-muted-foreground mb-1">Today's P&L</div>
                  <div className={`text-lg font-bold ${strategy.todayPnl >= 0 ? 'text-success' : 'text-danger'}`}>
                    {formatCurrency(strategy.todayPnl)}
                  </div>
                  <div className={`text-xs ${strategy.todayPnl >= 0 ? 'text-success' : 'text-danger'}`}>
                    {formatPercentage(strategy.todayPnlPercent)}
                  </div>
                </div>
                <div className="p-2 bg-dark-700/50 rounded">
                  <div className="text-xs text-muted-foreground mb-1">Capital</div>
                  <div className="text-lg font-bold text-white">{formatCurrency(strategy.capital)}</div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <div className="text-muted-foreground mb-1">Trades</div>
                  <div className="font-medium text-white">{strategy.totalTrades}</div>
                </div>
                <div>
                  <div className="text-muted-foreground mb-1">Win Rate</div>
                  <div className="font-medium text-success">{strategy.winRate}%</div>
                </div>
                <div>
                  <div className="text-muted-foreground mb-1">Sharpe</div>
                  <div className="font-medium text-white">{strategy.sharpe}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Technical Indicators & Market Microstructure */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Technical Indicators */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-500" />
            Technical Indicators (NIFTY 50)
          </h2>
          <div className="space-y-3">
            {technicalIndicators.map((indicator, index) => (
              <div key={index} className="p-3 bg-dark-700/30 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-white">{indicator.name}</span>
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      indicator.color === 'success'
                        ? 'bg-success/10 text-success'
                        : indicator.color === 'danger'
                        ? 'bg-danger/10 text-danger'
                        : 'bg-warning/10 text-warning'
                    }`}
                  >
                    {indicator.signal}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold text-white">{indicator.value}</span>
                  <div className="flex-1 h-2 bg-dark-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        indicator.color === 'success'
                          ? 'bg-success'
                          : indicator.color === 'danger'
                          ? 'bg-danger'
                          : 'bg-warning'
                      }`}
                      style={{ width: `${Math.min((indicator.value / indicator.threshold) * 50, 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Market Microstructure */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-500" />
            Market Microstructure
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-dark-700/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Bid-Ask Spread</div>
                <div className="text-xl font-bold text-success">{marketMicrostructure.bidAskSpread}%</div>
                <div className="text-xs text-muted-foreground">Tight spread</div>
              </div>
              <div className="p-3 bg-dark-700/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Market Depth</div>
                <div className="text-xl font-bold text-white">{marketMicrostructure.marketDepth}</div>
                <div className="text-xs text-muted-foreground">Liquidity</div>
              </div>
              <div className="p-3 bg-dark-700/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">OB Imbalance</div>
                <div className="text-xl font-bold text-warning">{marketMicrostructure.orderBookImbalance}</div>
                <div className="text-xs text-muted-foreground">Buy pressure</div>
              </div>
              <div className="p-3 bg-dark-700/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Volume Profile</div>
                <div className="text-xl font-bold text-white">{marketMicrostructure.volumeProfile}</div>
                <div className="text-xs text-muted-foreground">Trading activity</div>
              </div>
            </div>

            <div className="pt-4 border-t border-dark-600">
              <h3 className="text-sm font-medium text-muted-foreground mb-3">Live Indices</h3>
              <div className="space-y-2">
                {marketMicrostructure.tickerTape.map((ticker, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-dark-700/30 rounded">
                    <div>
                      <div className="text-sm font-medium text-white">{ticker.symbol}</div>
                      <div className="text-xs text-muted-foreground">Vol: {ticker.volume}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-white">{formatCurrency(ticker.price)}</div>
                      <div className={`text-xs ${ticker.change >= 0 ? 'text-success' : 'text-danger'}`}>
                        {formatPercentage(ticker.change)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Execution Timeline */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-purple-500" />
          Execution Timeline
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-600">
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Time</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Strategy</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Action</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Instrument</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Qty</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Price</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Status</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">P&L</th>
              </tr>
            </thead>
            <tbody>
              {executionTimeline.map((trade, index) => (
                <tr key={index} className="border-b border-dark-700/50 hover:bg-dark-700/30 transition-colors">
                  <td className="py-3 px-4 text-sm text-muted-foreground">{trade.time}</td>
                  <td className="py-3 px-4 text-sm text-white">{trade.strategy}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`text-xs px-2 py-1 rounded font-medium ${
                        trade.action === 'BUY' ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'
                      }`}
                    >
                      {trade.action}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-white">{trade.instrument}</td>
                  <td className="text-right py-3 px-4 text-sm text-white">{trade.quantity}</td>
                  <td className="text-right py-3 px-4 text-sm text-white">{formatCurrency(trade.price)}</td>
                  <td className="text-center py-3 px-4">
                    {trade.status === 'executed' ? (
                      <CheckCircle className="w-4 h-4 text-success mx-auto" />
                    ) : trade.status === 'partial' ? (
                      <AlertCircle className="w-4 h-4 text-warning mx-auto" />
                    ) : (
                      <XCircle className="w-4 h-4 text-danger mx-auto" />
                    )}
                  </td>
                  <td className="text-right py-3 px-4">
                    {trade.pnl !== 0 && (
                      <span className={`text-sm font-bold ${trade.pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                        {formatCurrency(trade.pnl)}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
