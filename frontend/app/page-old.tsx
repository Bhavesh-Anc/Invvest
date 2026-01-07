'use client'

import { MetricCard } from '@/components/ui/MetricCard'
import { TrendingUp, DollarSign, TrendingDown, Target } from 'lucide-react'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { AreaChart, Area, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

// Mock data
const portfolioData = {
  totalValue: 1234560,
  todayPnl: 6448,
  todayPnlPercent: 0.53,
  marginUsed: 456200,
  marginPercent: 68.2,
  sharpeRatio: 1.84,
}

const chartData = [
  { date: 'Jan 1', portfolio: 1100000, nifty: 1000000 },
  { date: 'Jan 8', portfolio: 1120000, nifty: 1020000 },
  { date: 'Jan 15', portfolio: 1080000, nifty: 980000 },
  { date: 'Jan 22', portfolio: 1180000, nifty: 1050000 },
  { date: 'Jan 29', portfolio: 1170000, nifty: 1030000 },
  { date: 'Feb 5', portfolio: 1250000, nifty: 1100000 },
  { date: 'Today', portfolio: 1234560, nifty: 1120000 },
]

const sectorData = [
  { name: 'IT', value: 28, color: '#3b82f6' },
  { name: 'Banking', value: 24, color: '#8b5cf6' },
  { name: 'FMCG', value: 14, color: '#06b6d4' },
  { name: 'Energy', value: 10, color: '#10b981' },
  { name: 'Pharma', value: 16, color: '#f59e0b' },
  { name: 'Others', value: 8, color: '#6b7280' },
]

const positions = [
  { symbol: 'RELIANCE', type: 'Cash', qty: 150, ltp: 2876.50, pnl: 4680, pnlPercent: 1.10 },
  { symbol: 'INFY', type: 'Cash', qty: 200, ltp: 1478.90, pnl: 4540, pnlPercent: 1.56 },
  { symbol: 'NIFTY 21JAN 21900 CE', type: 'Option', qty: 50, ltp: 156.30, pnl: 1590, pnlPercent: 25.54 },
  { symbol: 'HDFCBANK FUT', type: 'Future', qty: 1250, ltp: 1628.20, pnl: -8250, pnlPercent: -0.40 },
  { symbol: 'TCS', type: 'Cash', qty: 80, ltp: 3891.20, pnl: 3888, pnlPercent: 1.26 },
]

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Portfolio Value"
          value={formatCurrency(portfolioData.totalValue)}
          change={2.88}
          changeLabel="+₹34,560"
          icon={<DollarSign className="w-4 h-4" />}
          trend="up"
        />
        <MetricCard
          title="Today's P&L"
          value={formatCurrency(portfolioData.todayPnl)}
          change={portfolioData.todayPnlPercent}
          changeLabel="vs yesterday"
          icon={<TrendingUp className="w-4 h-4" />}
          trend="up"
        />
        <MetricCard
          title="Margin Used"
          value={formatCurrency(portfolioData.marginUsed)}
          subtitle={`${portfolioData.marginPercent}% of available`}
          icon={<Target className="w-4 h-4" />}
          alert={portfolioData.marginPercent > 60}
        />
        <MetricCard
          title="Sharpe Ratio"
          value={portfolioData.sharpeRatio.toFixed(2)}
          subtitle="Excellent risk-adjusted"
          icon={<TrendingUp className="w-4 h-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Portfolio Chart */}
        <div className="lg:col-span-2 card-glass rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-white">Portfolio vs Nifty 50</h2>
              <p className="text-sm text-muted-foreground">Performance comparison</p>
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
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorNifty" x1="0" y1="0" x2="0" y2="1">
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
              <Area type="monotone" dataKey="portfolio" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorPortfolio)" />
              <Area type="monotone" dataKey="nifty" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorNifty)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* AI Market Regime */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-6">AI Market Regime</h2>

          <div className="flex flex-col items-center justify-center py-8">
            <div className="w-32 h-32 rounded-full bg-gradient-to-br from-success/20 to-success/5 flex items-center justify-center mb-4">
              <TrendingUp className="w-16 h-16 text-success" />
            </div>
            <h3 className="text-2xl font-bold text-success mb-2">BULLISH</h3>
            <p className="text-sm text-muted-foreground mb-6">Confidence: 84%</p>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Volatility:</span>
              <span className="text-sm font-medium text-warning">Medium</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Trend Strength:</span>
              <span className="text-sm font-medium text-success">Strong</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">VIX (India):</span>
              <span className="text-sm font-medium text-white">13.42</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sector Allocation */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-6">Sector Allocation</h2>

          <div className="flex items-center gap-8">
            <ResponsiveContainer width="60%" height={200}>
              <PieChart>
                <Pie
                  data={sectorData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {sectorData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>

            <div className="flex-1 space-y-2">
              {sectorData.map((sector) => (
                <div key={sector.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: sector.color }}></div>
                    <span className="text-sm text-muted-foreground">{sector.name}</span>
                  </div>
                  <span className="text-sm font-medium text-white">{sector.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Risk Summary */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-6">Risk Summary</h2>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-muted-foreground">Value at Risk (95%)</span>
                <span className="text-sm font-bold text-danger">₹42,340</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-danger to-warning h-2 rounded-full" style={{ width: '42%' }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-muted-foreground">Max Drawdown</span>
                <span className="text-sm font-bold text-warning">-8.2%</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-warning to-success h-2 rounded-full" style={{ width: '18%' }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-muted-foreground">Beta vs Nifty</span>
                <span className="text-sm font-bold text-blue-500">1.18</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full" style={{ width: '59%' }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-muted-foreground">Portfolio Volatility</span>
                <span className="text-sm font-bold text-purple-500">16.4%</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full" style={{ width: '32%' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Open Positions */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-6">Open Positions</h2>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-600">
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Symbol</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Type</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Qty</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">LTP</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">P&L</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">P&L %</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((position, index) => (
                <tr key={index} className="border-b border-dark-700/50 hover:bg-dark-700/30 transition-colors">
                  <td className="py-3 px-4">
                    <div className="text-sm font-medium text-white">{position.symbol}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      position.type === 'Cash' ? 'bg-blue-500/20 text-blue-500' :
                      position.type === 'Option' ? 'bg-purple-500/20 text-purple-500' :
                      'bg-orange-500/20 text-orange-500'
                    }`}>
                      {position.type}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right text-sm text-white">{position.qty}</td>
                  <td className="py-3 px-4 text-right text-sm text-white">{formatCurrency(position.ltp)}</td>
                  <td className={`py-3 px-4 text-right text-sm font-medium ${
                    position.pnl > 0 ? 'text-success' : 'text-danger'
                  }`}>
                    {formatCurrency(position.pnl)}
                  </td>
                  <td className={`py-3 px-4 text-right text-sm font-medium ${
                    position.pnlPercent > 0 ? 'text-success' : 'text-danger'
                  }`}>
                    {formatPercentage(position.pnlPercent)}
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
