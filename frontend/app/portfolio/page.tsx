'use client'

import React, { useEffect, useState } from 'react'
import {
  TrendingUp, TrendingDown, PieChart, Activity,
  Shield, ArrowUpRight, ArrowDownRight, AlertCircle,
  Calendar, BarChart3, Target, LineChart as LineChartIcon
} from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, ScatterChart, Scatter,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts'
import MetricCard from '@/components/ui/MetricCard'
import TradingViewChart from '@/components/charts/TradingViewChart'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import api from '@/lib/api'
import Loading from '@/components/ui/Loading'
import ErrorDisplay from '@/components/ui/ErrorDisplay'

export default function PortfolioAnalyticsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [holdings, setHoldings] = useState<any[]>([])
  const [taxSummary, setTaxSummary] = useState<any>(null)
  const [monthlyReturns, setMonthlyReturns] = useState<any[]>([])
  const [riskMetrics, setRiskMetrics] = useState<any>(null)
  const [correlationData, setCorrelationData] = useState<any[]>([])
  const [drawdownData, setDrawdownData] = useState<any[]>([])
  const [selectedHolding, setSelectedHolding] = useState<string | null>(null)

  useEffect(() => {
    fetchPortfolioData()
  }, [])

  const fetchPortfolioData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch all portfolio data in parallel
      const [holdingsData, taxData, returnsData, metricsData, correlationRes, drawdownRes] = await Promise.all([
        api.portfolio.getHoldings(),
        api.portfolio.getTaxSummary(),
        api.portfolio.getMonthlyReturns(6),
        api.portfolio.getRiskMetrics(),
        api.portfolio.getCorrelation(),
        api.portfolio.getDrawdownHistory(180),
      ])

      setHoldings(holdingsData)
      setTaxSummary(taxData)
      setMonthlyReturns(returnsData)
      setRiskMetrics(metricsData)
      setCorrelationData(correlationRes)
      setDrawdownData(drawdownRes)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch portfolio data'))
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <Loading message="Loading portfolio analytics..." />
  if (error) return <ErrorDisplay error={error} onRetry={fetchPortfolioData} />
  if (!holdings || holdings.length === 0 || !riskMetrics) return null

  // Calculate portfolio metrics from holdings
  const totalCurrentValue = holdings.reduce((sum: number, h: any) => sum + h.currentValue, 0)
  const totalCost = holdings.reduce((sum: number, h: any) => sum + h.totalCost, 0)
  const totalPnL = totalCurrentValue - totalCost
  const totalPnLPercent = (totalPnL / totalCost) * 100
  const totalTaxLiability = holdings.reduce((sum: number, h: any) => sum + h.taxLiability, 0)

  const ltcgHoldings = holdings.filter((h: any) => h.taxType === 'LTCG')
  const stcgHoldings = holdings.filter((h: any) => h.taxType === 'STCG')
  const ltcgValue = ltcgHoldings.reduce((sum: number, h: any) => sum + h.currentValue, 0)
  const stcgValue = stcgHoldings.reduce((sum: number, h: any) => sum + h.currentValue, 0)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Portfolio Analytics</h1>
          <p className="text-muted-foreground">Tax-aware holdings analysis and risk metrics</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors">
            <Calendar className="w-4 h-4 inline mr-2" />
            Last 6 Months
          </button>
          <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors">
            Export Report
          </button>
        </div>
      </div>

      {/* Portfolio Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Holdings Value"
          value={formatCurrency(totalCurrentValue)}
          icon={<PieChart className="w-5 h-5" />}
          subtitle={`Cost: ${formatCurrency(totalCost)}`}
        />
        <MetricCard
          title="Unrealized P&L"
          value={formatCurrency(totalPnL)}
          change={totalPnLPercent}
          changeLabel="return"
          trend={totalPnL >= 0 ? 'up' : 'down'}
          icon={totalPnL >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
        />
        <MetricCard
          title="Tax Liability (Est.)"
          value={formatCurrency(totalTaxLiability)}
          icon={<Shield className="w-5 h-5" />}
          subtitle={`LTCG: ${formatCurrency(ltcgHoldings.reduce((sum: number, h: any) => sum + h.taxLiability, 0))}`}
        />
        <MetricCard
          title="Sharpe Ratio"
          value={riskMetrics.sharpeRatio?.toFixed(2) || '0.00'}
          icon={<Target className="w-5 h-5" />}
          subtitle={`Sortino: ${riskMetrics.sortinoRatio?.toFixed(2) || '0.00'}`}
        />
      </div>

      {/* Tax Breakdown */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-purple-500" />
          Tax Classification
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-dark-700/30 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-muted-foreground">Long Term Capital Gains (LTCG)</h3>
              <span className="text-xs px-2 py-1 bg-green-500/10 text-success rounded">10% Tax</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Holdings:</span>
                <span className="text-sm font-medium text-white">{ltcgHoldings.length} stocks</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Current Value:</span>
                <span className="text-sm font-medium text-white">{formatCurrency(ltcgValue)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Tax Liability:</span>
                <span className="text-sm font-bold text-success">{formatCurrency(ltcgHoldings.reduce((sum: number, h: any) => sum + h.taxLiability, 0))}</span>
              </div>
              <div className="text-xs text-muted-foreground mt-2">
                Held for &gt;12 months
              </div>
            </div>
          </div>

          <div className="p-4 bg-dark-700/30 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-muted-foreground">Short Term Capital Gains (STCG)</h3>
              <span className="text-xs px-2 py-1 bg-yellow-500/10 text-warning rounded">15% Tax</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Holdings:</span>
                <span className="text-sm font-medium text-white">{stcgHoldings.length} stocks</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Current Value:</span>
                <span className="text-sm font-medium text-white">{formatCurrency(stcgValue)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Tax Liability:</span>
                <span className="text-sm font-bold text-warning">{formatCurrency(stcgHoldings.reduce((sum: number, h: any) => sum + h.taxLiability, 0))}</span>
              </div>
              <div className="text-xs text-muted-foreground mt-2">
                Held for &lt;12 months
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-500" />
          Current Holdings
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-600">
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Symbol</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Qty</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Avg Price</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">LTP</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Current Value</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">P&L</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Tax</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Tax Liability</th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((holding: any, index: number) => (
                <tr
                  key={index}
                  className={`border-b border-dark-700/50 hover:bg-dark-700/30 transition-colors cursor-pointer ${selectedHolding === holding.symbol ? 'bg-purple-500/10' : ''}`}
                  onClick={() => setSelectedHolding(holding.symbol)}
                >
                  <td className="py-3 px-4">
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-white">{holding.symbol}</span>
                      <span className="text-xs text-muted-foreground">{holding.name}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right text-sm text-white">{holding.quantity}</td>
                  <td className="py-3 px-4 text-right text-sm text-white">{formatCurrency(holding.avgPrice)}</td>
                  <td className="py-3 px-4 text-right text-sm text-white">{formatCurrency(holding.ltp)}</td>
                  <td className="py-3 px-4 text-right text-sm font-medium text-white">{formatCurrency(holding.currentValue)}</td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex flex-col items-end">
                      <span className={`text-sm font-medium ${holding.pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                        {formatCurrency(holding.pnl)}
                      </span>
                      <span className={`text-xs ${holding.pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                        {formatPercentage(holding.pnlPercent)}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      holding.taxType === 'LTCG' ? 'bg-success/20 text-success' : 'bg-warning/20 text-warning'
                    }`}>
                      {holding.taxType}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right text-sm font-medium text-warning">{formatCurrency(holding.taxLiability)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stock Technical Analysis - TradingView Chart */}
      {selectedHolding && (
        <div className="card-glass rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <LineChartIcon className="w-5 h-5 text-blue-500" />
              <div>
                <h2 className="text-xl font-bold text-white">Technical Analysis - {selectedHolding}</h2>
                <p className="text-sm text-muted-foreground">Click any holding above to view its chart</p>
              </div>
            </div>
            <button
              onClick={() => setSelectedHolding(null)}
              className="px-3 py-1.5 bg-dark-700 hover:bg-dark-600 text-white text-sm rounded-lg transition-colors"
            >
              Close Chart
            </button>
          </div>
          <TradingViewChart
            symbol={selectedHolding}
            exchange="NSE"
            interval="D"
            theme="dark"
            height={500}
            showToolbar={true}
            allowSymbolChange={false}
            studies={['MASimple@tv-basicstudies', 'RSI@tv-basicstudies', 'MACD@tv-basicstudies', 'BB@tv-basicstudies']}
          />
        </div>
      )}

      {/* Monthly Returns */}
      {monthlyReturns && monthlyReturns.length > 0 && (
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-6">Monthly Returns vs Nifty 50</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={monthlyReturns}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis dataKey="month" stroke="#6b7280" fontSize={12} />
              <YAxis stroke="#6b7280" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a2038', border: '1px solid #1f2740', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Legend />
              <Bar dataKey="portfolio" fill="#8b5cf6" name="Portfolio" radius={[4, 4, 0, 0]} />
              <Bar dataKey="nifty" fill="#3b82f6" name="Nifty 50" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Risk Metrics */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-6">Risk-Adjusted Performance Metrics</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
          {riskMetrics && Object.keys(riskMetrics).map((key: string) => {
            const metricNames: Record<string, string> = {
              sharpeRatio: 'Sharpe Ratio',
              sortinoRatio: 'Sortino Ratio',
              calmarRatio: 'Calmar Ratio',
              informationRatio: 'Information Ratio',
              treynorRatio: 'Treynor Ratio',
              maxDrawdown: 'Max Drawdown',
              volatility: 'Volatility',
              beta: 'Beta',
              alpha: 'Alpha',
              rSquared: 'R-Squared'
            }
            const value = riskMetrics[key]
            const isPercentage = key === 'maxDrawdown' || key === 'volatility' || key === 'alpha'
            const displayValue = isPercentage ? formatPercentage(value) : typeof value === 'number' ? value.toFixed(2) : value

            return (
              <div key={key} className="p-4 bg-dark-700/30 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">{metricNames[key] || key}</p>
                <h3 className={`text-xl font-bold ${
                  key === 'maxDrawdown' ? 'text-danger' :
                  key === 'sharpeRatio' || key === 'sortinoRatio' ? 'text-success' : 'text-white'
                }`}>
                  {displayValue}
                </h3>
              </div>
            )
          })}
        </div>
      </div>

      {/* Correlation Analysis */}
      {correlationData && correlationData.length > 0 && (
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-6">Correlation Analysis</h2>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis type="number" dataKey="nifty" name="Nifty Correlation" stroke="#6b7280" fontSize={12} domain={[0, 1]} />
              <YAxis type="number" dataKey="sector" name="Sector Correlation" stroke="#6b7280" fontSize={12} domain={[0, 1]} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a2038', border: '1px solid #1f2740', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }}
                cursor={{ strokeDasharray: '3 3' }}
              />
              <Scatter data={correlationData} fill="#8b5cf6">
                {correlationData.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill="#8b5cf6" />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Drawdown History */}
      {drawdownData && drawdownData.length > 0 && (
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-6">Portfolio Drawdown History</h2>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={drawdownData}>
              <defs>
                <linearGradient id="colorDrawdownFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis dataKey="date" stroke="#6b7280" fontSize={12} />
              <YAxis stroke="#6b7280" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a2038', border: '1px solid #1f2740', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Area type="monotone" dataKey="drawdown" stroke="#ef4444" strokeWidth={2} fill="url(#colorDrawdownFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
