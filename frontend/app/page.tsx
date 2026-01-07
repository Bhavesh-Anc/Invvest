'use client'

import { useCallback } from 'react'
import MetricCard from '@/components/ui/MetricCard'
import Loading from '@/components/ui/Loading'
import ErrorDisplay from '@/components/ui/ErrorDisplay'
import { TrendingUp, DollarSign, TrendingDown, Target, Activity, Shield } from 'lucide-react'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { AreaChart, Area, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { useDashboardData, useMarketData } from '@/lib/hooks/useQueries'
import { useWebSocket } from '@/lib/websocket'

export default function DashboardPage() {
  // Use React Query for automatic caching, background refetching, and better state management
  const { data: dashboardData, isLoading, isError, error, refetch } = useDashboardData()

  // Separate query for market data with faster refresh (every 5s)
  const { data: marketDataLive } = useMarketData()

  // WebSocket for real-time portfolio value updates
  const handlePortfolioUpdate = useCallback((data: any) => {
    // Portfolio changed - refetch dashboard data
    refetch()
  }, [refetch])

  const { isConnected } = useWebSocket('portfolio', handlePortfolioUpdate)

  if (isLoading) return <Loading message="Loading dashboard data..." />
  if (isError) return <ErrorDisplay error={error as Error} onRetry={() => refetch()} />
  if (!dashboardData) return null

  const { portfolio, marketData, chartData, sectorAllocation, riskMetrics, positions, marketRegime } = dashboardData

  return (
    <div className="space-y-6">
      {/* Market Status Bar */}
      <div className="card-glass rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            {/* WebSocket Connection Status */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-dark-700/50 rounded-lg">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-success animate-pulse' : 'bg-muted-foreground'}`}></div>
              <span className="text-xs font-medium text-muted-foreground">
                {isConnected ? 'Live' : 'Offline'}
              </span>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">NIFTY 50</span>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-white">{formatCurrency(marketData.nifty, '')}</span>
                <span className={`text-sm ${marketData.niftyChange >= 0 ? 'text-success' : 'text-danger'}`}>
                  {formatPercentage(marketData.niftyChange)}
                </span>
              </div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">SENSEX</span>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-white">{formatCurrency(marketData.sensex, '')}</span>
                <span className={`text-sm ${marketData.sensexChange >= 0 ? 'text-success' : 'text-danger'}`}>
                  {formatPercentage(marketData.sensexChange)}
                </span>
              </div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">BANK NIFTY</span>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-white">{formatCurrency(marketData.bankNifty, '')}</span>
                <span className={`text-sm ${marketData.bankNiftyChange >= 0 ? 'text-success' : 'text-danger'}`}>
                  {formatPercentage(marketData.bankNiftyChange)}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse"></div>
            <span className="text-sm text-muted-foreground">Market Open</span>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Portfolio Value"
          value={formatCurrency(portfolio.totalValue)}
          change={portfolio.todayPnlPercent}
          changeLabel={formatCurrency(portfolio.todayPnl)}
          icon={<DollarSign className="w-4 h-4" />}
          trend={portfolio.todayPnl >= 0 ? 'up' : 'down'}
        />
        <MetricCard
          title="Today's P&L"
          value={formatCurrency(portfolio.todayPnl)}
          change={portfolio.todayPnlPercent}
          changeLabel="vs yesterday"
          icon={portfolio.todayPnl >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          trend={portfolio.todayPnl >= 0 ? 'up' : 'down'}
        />
        <MetricCard
          title="Margin Used"
          value={formatCurrency(portfolio.marginUsed)}
          subtitle={`Available: ${formatCurrency(portfolio.marginAvailable)}`}
          icon={<Target className="w-4 h-4" />}
          alert={(portfolio.marginUsed / (portfolio.marginUsed + portfolio.marginAvailable)) * 100 > 60}
        />
        <MetricCard
          title="Sharpe Ratio"
          value={portfolio.sharpeRatio.toFixed(2)}
          subtitle="Excellent risk-adjusted"
          icon={<Activity className="w-4 h-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Portfolio Chart */}
        <div className="lg:col-span-2 card-glass rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-white">Portfolio vs Nifty 50</h2>
              <p className="text-sm text-muted-foreground">Performance comparison (Last 30 days)</p>
            </div>
            <div className="flex gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                <span className="text-sm text-muted-foreground">Portfolio</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span className="text-sm text-muted-foreground">Nifty 50</span>
              </div>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorPortfolio" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorNifty" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis dataKey="date" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f1429',
                  border: '1px solid #1f2740',
                  borderRadius: '8px',
                }}
              />
              <Area type="monotone" dataKey="portfolio" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorPortfolio)" />
              <Area type="monotone" dataKey="nifty" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorNifty)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* AI Market Regime */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">AI Market Regime</h2>
          <div className="space-y-4">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-24 h-24 bg-success/10 rounded-full mb-3">
                <span className="text-3xl font-bold text-success">{marketRegime.regime}</span>
              </div>
              <div className="text-2xl font-bold text-white mb-1">{marketRegime.confidence}%</div>
              <p className="text-xs text-muted-foreground mb-4">Confidence Level</p>
              <p className="text-sm text-white">{marketRegime.signal}</p>
            </div>
            <div className="pt-4 border-t border-dark-600">
              <div className="flex justify-between text-xs mb-2">
                <span className="text-muted-foreground">Bear</span>
                <span className="text-muted-foreground">Bull</span>
              </div>
              <div className="w-full h-2 bg-dark-700 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-danger via-warning to-success" style={{ width: `${marketRegime.confidence}%` }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sector Allocation */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Sector Allocation</h2>
          <div className="flex items-center justify-between">
            <ResponsiveContainer width="50%" height={200}>
              <PieChart>
                <Pie
                  data={sectorAllocation}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {sectorAllocation.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'][index % 5]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-2">
              {sectorAllocation.map((sector: any, index: number) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'][index % 5] }}></div>
                    <span className="text-sm text-white">{sector.name}</span>
                  </div>
                  <span className="text-sm font-semibold text-white">{sector.percent}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Risk Summary */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-purple-500" />
            Risk Summary
          </h2>
          <div className="space-y-4">
            {riskMetrics.map((metric: any, index: number) => (
              <div key={index}>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-muted-foreground">{metric.metric}</span>
                  <span className="text-sm font-semibold text-white">{metric.value}%</span>
                </div>
                <div className="w-full h-2 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${metric.status === 'normal' ? 'bg-success' : metric.status === 'warning' ? 'bg-warning' : 'bg-danger'}`}
                    style={{ width: `${(metric.value / metric.threshold) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Open Positions */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Open Positions</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-600">
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Symbol</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Type</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Qty</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">LTP</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">P&L</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">%</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((position: any, index: number) => (
                <tr key={index} className="border-b border-dark-700/50 hover:bg-dark-700/30 transition-colors">
                  <td className="py-3 px-4 text-sm font-medium text-white">{position.symbol}</td>
                  <td className="py-3 px-4">
                    <span className={`text-xs px-2 py-1 rounded ${
                      position.type === 'Cash' ? 'bg-blue-500/10 text-blue-400' :
                      position.type === 'Options' ? 'bg-purple-500/10 text-purple-400' :
                      'bg-warning/10 text-warning'
                    }`}>
                      {position.type}
                    </span>
                  </td>
                  <td className="text-right py-3 px-4 text-sm text-white">{position.quantity}</td>
                  <td className="text-right py-3 px-4 text-sm text-white">{formatCurrency(position.ltp)}</td>
                  <td className="text-right py-3 px-4">
                    <span className={`text-sm font-semibold ${position.pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                      {formatCurrency(position.pnl)}
                    </span>
                  </td>
                  <td className="text-right py-3 px-4">
                    <span className={`text-sm ${position.pnlPercent >= 0 ? 'text-success' : 'text-danger'}`}>
                      {formatPercentage(position.pnlPercent)}
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
