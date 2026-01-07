'use client'

import { Settings, Play, Download, TrendingUp } from 'lucide-react'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

// Mock data
const equityCurveData = [
  { date: '1 Jan', equity: 1000000, benchmark: 1000000 },
  { date: '15 Jan', equity: 1025000, benchmark: 1015000 },
  { date: '1 Feb', equity: 1048000, benchmark: 1028000 },
  { date: '15 Feb', equity: 1072000, benchmark: 1042000 },
  { date: '1 Mar', equity: 1095000, benchmark: 1055000 },
  { date: '15 Mar', equity: 1118000, benchmark: 1068000 },
  { date: '1 Apr', equity: 1142000, benchmark: 1082000 },
  { date: '15 Apr', equity: 1165000, benchmark: 1095000 },
]

const monthlyReturnsData = [
  { month: 'Jan', return: 4.8 },
  { month: 'Feb', return: -1.2 },
  { month: 'Mar', return: 5.6 },
  { month: 'Apr', return: 2.8 },
  { month: 'May', return: 3.2 },
  { month: 'Jun', return: -0.5 },
  { month: 'Jul', return: 4.1 },
  { month: 'Aug', return: 6.2 },
]

const returnDistributionData = [
  { range: '-10% to -5%', count: 2 },
  { range: '-5% to 0%', count: 8 },
  { range: '0% to 5%', count: 18 },
  { range: '5% to 10%', count: 7 },
  { range: '10%+', count: 1 },
]

const walkForwardResults = [
  { period: 'Jan-Feb 2025', inSample: 'Pass', outSample: 'Pass', sharpe: 1.92, result: 'pass' },
  { period: 'Mar-Apr 2025', inSample: 'Pass', outSample: 'Pass', sharpe: 1.76, result: 'pass' },
  { period: 'May-Jun 2025', inSample: 'Pass', outSample: 'Fail', sharpe: 0.84, result: 'fail' },
  { period: 'Jul-Aug 2025', inSample: 'Pass', outSample: 'Pass', sharpe: 2.12, result: 'pass' },
  { period: 'Sep-Oct 2025', inSample: 'Pass', outSample: 'Pass', sharpe: 1.88, result: 'pass' },
  { period: 'Nov-Dec 2025', inSample: 'Pass', outSample: 'Pass', sharpe: 1.94, result: 'pass' },
]

const recentTrades = [
  { time: '14:23:45', symbol: 'INFY', action: 'BUY', qty: 100, price: 1478.90, status: 'Filled' },
  { time: '14:18:32', symbol: 'TCS', action: 'SELL', qty: 50, price: 3891.20, status: 'Filled' },
  { time: '13:45:18', symbol: 'RELIANCE', action: 'BUY', qty: 75, price: 2876.50, status: 'Filled' },
  { time: '13:22:05', symbol: 'HDFCBANK', action: 'SELL', qty: 120, price: 1628.20, status: 'Filled' },
]

export default function BacktestingPage() {
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
                defaultValue="0.15"
                className="flex-1 h-2 bg-gradient-to-r from-danger to-white rounded-full appearance-none cursor-pointer"
                style={{
                  background: 'linear-gradient(to right, #ef4444 0%, #fff 100%)'
                }}
              />
              <span className="text-sm font-medium text-white min-w-[60px]">0.15%</span>
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
                defaultValue="0.03"
                className="flex-1 h-2 bg-gradient-to-r from-danger to-white rounded-full appearance-none cursor-pointer"
              />
              <span className="text-sm font-medium text-white min-w-[60px]">0.03%</span>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-muted-foreground mb-2 block">Market Impact</label>
            <select className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-sm">
              <option value="low">Low (Liquid stocks)</option>
              <option value="medium">Medium (Mid-caps)</option>
              <option value="high">High (Small-caps)</option>
            </select>
          </div>
        </div>
      </div>

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
            <h3 className="text-2xl font-bold text-blue-500">29.8%</h3>
            <p className="text-xs text-muted-foreground">+15% vs Nifty</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">CAGR</p>
            <h3 className="text-2xl font-bold text-blue-500">24.6%</h3>
            <p className="text-xs text-muted-foreground">Annualized</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">Sharpe Ratio</p>
            <h3 className="text-2xl font-bold text-blue-500">1.84</h3>
            <p className="text-xs text-muted-foreground">Excellent</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">Sortino Ratio</p>
            <h3 className="text-2xl font-bold text-blue-500">2.31</h3>
            <p className="text-xs text-muted-foreground">Strong</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">Max Drawdown</p>
            <h3 className="text-2xl font-bold text-warning">-8.2%</h3>
            <p className="text-xs text-muted-foreground">Within tolerance</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">Win Rate</p>
            <h3 className="text-2xl font-bold text-success">64.2%</h3>
            <p className="text-xs text-muted-foreground">568/885 trades</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">Profit Factor</p>
            <h3 className="text-2xl font-bold text-purple-500">2.14</h3>
            <p className="text-xs text-muted-foreground">Profitable</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">Avg Win / Avg Loss</p>
            <h3 className="text-2xl font-bold text-white">1.48</h3>
            <p className="text-xs text-muted-foreground">Favorable</p>
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
