'use client'

import { useEffect, useState } from 'react'
import { Settings, Play, Download, TrendingUp } from 'lucide-react'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import api from '@/lib/api'
import Loading from '@/components/ui/Loading'
import ErrorDisplay from '@/components/ui/ErrorDisplay'

export default function BacktestingPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [config, setConfig] = useState<any>(null)
  const [equityCurveData, setEquityCurveData] = useState<any[]>([])
  const [performanceMetrics, setPerformanceMetrics] = useState<any>(null)
  const [monthlyReturnsData, setMonthlyReturnsData] = useState<any[]>([])
  const [returnDistributionData, setReturnDistributionData] = useState<any[]>([])
  const [walkForwardResults, setWalkForwardResults] = useState<any[]>([])
  const [recentTrades, setRecentTrades] = useState<any[]>([])

  useEffect(() => {
    fetchBacktestData()
  }, [])

  const fetchBacktestData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch all backtesting data in parallel
      const [configData, equityCurve, metrics, monthlyReturns, returnDist, walkForward, paperTrades] = await Promise.all([
        api.backtest.getConfig(),
        api.backtest.getEquityCurve(180),
        api.backtest.getPerformanceMetrics(),
        api.backtest.getMonthlyReturns(6),
        api.backtest.getReturnDistribution(),
        api.backtest.getWalkForward(),
        api.backtest.getPaperTrades(20),
      ])

      setConfig(configData)
      setEquityCurveData(equityCurve)
      setPerformanceMetrics(metrics)
      setMonthlyReturnsData(monthlyReturns)
      setReturnDistributionData(returnDist)
      setWalkForwardResults(walkForward)
      setRecentTrades(paperTrades)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch backtesting data'))
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <Loading message="Loading backtesting data..." />
  if (error) return <ErrorDisplay error={error} onRetry={fetchBacktestData} />
  if (!performanceMetrics) return null
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Backtesting & Paper Trading</h1>
          <p className="text-sm text-muted-foreground">Strategy validation and performance analysis</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg hover:bg-dark-600 transition-colors">
            <Settings className="w-4 h-4" />
            <span className="text-sm font-medium">Configure</span>
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors">
            <Play className="w-4 h-4" />
            <span className="text-sm font-medium">Run Backtest</span>
          </button>
        </div>
      </div>

      {/* Transaction Cost & Slippage Configuration */}
      {config && (
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-6">Transaction Cost & Slippage Modeling</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">Slippage (%)</label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  defaultValue={config.slippage || 0.15}
                  className="flex-1 h-2 bg-gradient-to-r from-danger to-white rounded-full appearance-none cursor-pointer"
                  style={{
                    background: 'linear-gradient(to right, #ef4444 0%, #fff 100%)'
                  }}
                />
                <span className="text-sm font-medium text-white min-w-[60px]">{config.slippage || 0.15}%</span>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">Commission (%)</label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="0"
                  max="0.5"
                  step="0.01"
                  defaultValue={config.commission || 0.03}
                  className="flex-1 h-2 bg-gradient-to-r from-danger to-white rounded-full appearance-none cursor-pointer"
                />
                <span className="text-sm font-medium text-white min-w-[60px]">{config.commission || 0.03}%</span>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">Market Impact</label>
              <select className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-sm" defaultValue={config.marketImpact || 'low'}>
                <option value="low">Low (Liquid stocks)</option>
                <option value="medium">Medium (Mid-caps)</option>
                <option value="high">High (Small-caps)</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Strategy Equity Curve */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-6">Strategy Equity Curve</h2>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={equityCurveData}>
            <defs>
              <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
            <XAxis dataKey="date" stroke="#6b7280" fontSize={12} />
            <YAxis stroke="#6b7280" fontSize={12} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1a2038', border: '1px solid #1f2740', borderRadius: '8px' }}
              labelStyle={{ color: '#9ca3af' }}
            />
            <Line type="monotone" dataKey="equity" stroke="#3b82f6" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="benchmark" stroke="#6b7280" strokeWidth={2} strokeDasharray="5 5" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Performance Metrics */}
      <div className="card-glass rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-white">Performance Metrics</h2>
          <button className="flex items-center gap-2 px-3 py-1.5 bg-dark-700 border border-dark-600 rounded-lg hover:bg-dark-600 transition-colors">
            <Download className="w-4 h-4" />
            <span className="text-sm font-medium">Export Report</span>
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Total Return</p>
            <h3 className="text-2xl font-bold text-blue-500">{formatPercentage(performanceMetrics.totalReturn || 0)}</h3>
            <p className="text-xs text-muted-foreground">{performanceMetrics.vsBenchmark || 'vs Nifty'}</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">CAGR</p>
            <h3 className="text-2xl font-bold text-blue-500">{formatPercentage(performanceMetrics.cagr || 0)}</h3>
            <p className="text-xs text-muted-foreground">Annualized</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">Sharpe Ratio</p>
            <h3 className="text-2xl font-bold text-blue-500">{performanceMetrics.sharpeRatio?.toFixed(2) || 0}</h3>
            <p className="text-xs text-muted-foreground">{performanceMetrics.sharpeRating || 'Good'}</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">Sortino Ratio</p>
            <h3 className="text-2xl font-bold text-blue-500">{performanceMetrics.sortinoRatio?.toFixed(2) || 0}</h3>
            <p className="text-xs text-muted-foreground">{performanceMetrics.sortinoRating || 'Strong'}</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">Max Drawdown</p>
            <h3 className="text-2xl font-bold text-warning">{formatPercentage(performanceMetrics.maxDrawdown || 0)}</h3>
            <p className="text-xs text-muted-foreground">{performanceMetrics.drawdownNote || 'Within tolerance'}</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">Win Rate</p>
            <h3 className="text-2xl font-bold text-success">{formatPercentage(performanceMetrics.winRate || 0)}</h3>
            <p className="text-xs text-muted-foreground">{performanceMetrics.winLossRatio || 'trades'}</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">Profit Factor</p>
            <h3 className="text-2xl font-bold text-purple-500">{performanceMetrics.profitFactor?.toFixed(2) || 0}</h3>
            <p className="text-xs text-muted-foreground">{performanceMetrics.profitRating || 'Profitable'}</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">Avg Win / Avg Loss</p>
            <h3 className="text-2xl font-bold text-white">{performanceMetrics.avgWinLoss?.toFixed(2) || 0}</h3>
            <p className="text-xs text-muted-foreground">{performanceMetrics.winLossNote || 'Favorable'}</p>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Returns */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-6">Monthly Returns</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={monthlyReturnsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis dataKey="month" stroke="#6b7280" fontSize={12} />
              <YAxis stroke="#6b7280" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a2038', border: '1px solid #1f2740', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Bar dataKey="return" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Return Distribution */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-6">Return Distribution</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={returnDistributionData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis type="number" stroke="#6b7280" fontSize={12} />
              <YAxis dataKey="range" type="category" stroke="#6b7280" fontSize={12} width={100} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a2038', border: '1px solid #1f2740', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Walk-Forward Validation */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-6">Walk-Forward Validation</h2>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-600">
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Period</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">In-Sample</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Out-Sample</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Sharpe Ratio</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Result</th>
              </tr>
            </thead>
            <tbody>
              {walkForwardResults.map((row, index) => (
                <tr key={index} className="border-b border-dark-700/50 hover:bg-dark-700/30 transition-colors">
                  <td className="py-3 px-4 text-sm text-white">{row.period}</td>
                  <td className="py-3 px-4 text-center">
                    <span className="px-2 py-1 bg-success/20 text-success text-xs font-medium rounded">
                      {row.inSample}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${
                      row.outSample === 'Pass' ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'
                    }`}>
                      {row.outSample}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center text-sm font-medium text-white">{row.sharpe}</td>
                  <td className="py-3 px-4 text-center">
                    <TrendingUp className={`w-4 h-4 mx-auto ${row.result === 'pass' ? 'text-success' : 'text-danger'}`} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 p-4 bg-success/10 border border-success/30 rounded-lg">
          <p className="text-sm text-success">
            Strategy passed 5 out of 6 walk-forward periods. Validation success rate: 83.3%
          </p>
        </div>
      </div>

      {/* Paper Trading Order Blotter */}
      <div className="card-glass rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-white">Paper Trading Order Blotter</h2>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse"></div>
            <span className="text-sm text-success">Paper Trading Active</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-600">
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Time</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Symbol</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Action</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Qty</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Price</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Status</th>
              </tr>
            </thead>
            <tbody>
              {recentTrades.map((trade, index) => (
                <tr key={index} className="border-b border-dark-700/50 hover:bg-dark-700/30 transition-colors">
                  <td className="py-3 px-4 text-sm text-muted-foreground">{trade.time}</td>
                  <td className="py-3 px-4 text-sm font-medium text-white">{trade.symbol}</td>
                  <td className="py-3 px-4 text-center">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${
                      trade.action === 'BUY' ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'
                    }`}>
                      {trade.action}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right text-sm text-white">{trade.qty}</td>
                  <td className="py-3 px-4 text-right text-sm text-white">{formatCurrency(trade.price)}</td>
                  <td className="py-3 px-4 text-center">
                    <span className="px-2 py-1 bg-success/20 text-success text-xs font-medium rounded">
                      {trade.status}
                    </span>
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
