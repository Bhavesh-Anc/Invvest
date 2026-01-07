'use client'

import React from 'react'
import {
  TrendingUp, TrendingDown, PieChart, Activity,
  Shield, ArrowUpRight, ArrowDownRight, AlertCircle,
  Calendar, BarChart3, Target
} from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, ScatterChart, Scatter,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts'
import MetricCard from '@/components/ui/MetricCard'
import { formatCurrency, formatPercentage } from '@/lib/utils'

export default function PortfolioAnalyticsPage() {
  // Holdings data with tax implications
  const holdings = [
    {
      symbol: 'RELIANCE',
      name: 'Reliance Industries Ltd',
      quantity: 250,
      avgPrice: 2450.00,
      ltp: 2678.50,
      currentValue: 669625,
      totalCost: 612500,
      pnl: 57125,
      pnlPercent: 9.33,
      holdingDays: 425,
      taxType: 'LTCG',
      taxRate: 10,
      taxLiability: 5712.50,
    },
    {
      symbol: 'TCS',
      name: 'Tata Consultancy Services',
      quantity: 150,
      avgPrice: 3520.00,
      ltp: 3789.25,
      currentValue: 568387.50,
      totalCost: 528000,
      pnl: 40387.50,
      pnlPercent: 7.65,
      holdingDays: 520,
      taxType: 'LTCG',
      taxRate: 10,
      taxLiability: 4038.75,
    },
    {
      symbol: 'HDFCBANK',
      name: 'HDFC Bank Ltd',
      quantity: 400,
      avgPrice: 1580.00,
      ltp: 1642.80,
      currentValue: 657120,
      totalCost: 632000,
      pnl: 25120,
      pnlPercent: 3.97,
      holdingDays: 180,
      taxType: 'STCG',
      taxRate: 15,
      taxLiability: 3768.00,
    },
    {
      symbol: 'INFY',
      name: 'Infosys Ltd',
      quantity: 300,
      avgPrice: 1450.00,
      ltp: 1398.50,
      currentValue: 419550,
      totalCost: 435000,
      pnl: -15450,
      pnlPercent: -3.55,
      holdingDays: 95,
      taxType: 'STCG',
      taxRate: 15,
      taxLiability: 0,
    },
    {
      symbol: 'ICICIBANK',
      name: 'ICICI Bank Ltd',
      quantity: 500,
      avgPrice: 960.00,
      ltp: 1025.75,
      currentValue: 512875,
      totalCost: 480000,
      pnl: 32875,
      pnlPercent: 6.85,
      holdingDays: 240,
      taxType: 'STCG',
      taxRate: 15,
      taxLiability: 4931.25,
    },
    {
      symbol: 'BHARTIARTL',
      name: 'Bharti Airtel Ltd',
      quantity: 600,
      avgPrice: 880.00,
      ltp: 1142.30,
      currentValue: 685380,
      totalCost: 528000,
      pnl: 157380,
      pnlPercent: 29.81,
      holdingDays: 680,
      taxType: 'LTCG',
      taxRate: 10,
      taxLiability: 15738.00,
    },
  ]

  const totalCurrentValue = holdings.reduce((sum, h) => sum + h.currentValue, 0)
  const totalCost = holdings.reduce((sum, h) => sum + h.totalCost, 0)
  const totalPnL = totalCurrentValue - totalCost
  const totalPnLPercent = (totalPnL / totalCost) * 100
  const totalTaxLiability = holdings.reduce((sum, h) => sum + h.taxLiability, 0)

  const ltcgHoldings = holdings.filter(h => h.taxType === 'LTCG')
  const stcgHoldings = holdings.filter(h => h.taxType === 'STCG')
  const ltcgValue = ltcgHoldings.reduce((sum, h) => sum + h.currentValue, 0)
  const stcgValue = stcgHoldings.reduce((sum, h) => sum + h.currentValue, 0)

  // Monthly returns data
  const monthlyReturns = [
    { month: 'Jul', portfolio: 2.4, nifty: 1.8 },
    { month: 'Aug', portfolio: -1.2, nifty: -0.8 },
    { month: 'Sep', portfolio: 3.8, nifty: 2.5 },
    { month: 'Oct', portfolio: -2.5, nifty: -1.9 },
    { month: 'Nov', portfolio: 4.2, nifty: 3.1 },
    { month: 'Dec', portfolio: 5.6, nifty: 4.2 },
    { month: 'Jan', portfolio: 1.8, nifty: 2.1 },
  ]

  // Correlation data
  const correlationData = [
    { name: 'RELIANCE', nifty: 0.85, sector: 0.92, value: 669625 },
    { name: 'TCS', nifty: 0.78, sector: 0.88, value: 568387 },
    { name: 'HDFCBANK', nifty: 0.82, sector: 0.94, value: 657120 },
    { name: 'INFY', nifty: 0.76, sector: 0.89, value: 419550 },
    { name: 'ICICIBANK', nifty: 0.81, sector: 0.93, value: 512875 },
    { name: 'BHARTIARTL', nifty: 0.72, sector: 0.79, value: 685380 },
  ]

  // Risk-adjusted metrics
  const riskMetrics = {
    sharpeRatio: 1.84,
    sortinoRatio: 2.31,
    calmarRatio: 1.52,
    informationRatio: 0.68,
    treynorRatio: 12.4,
    maxDrawdown: -8.2,
    volatility: 14.8,
    beta: 0.92,
    alpha: 2.4,
    rSquared: 0.78,
  }

  // Drawdown history
  const drawdownData = [
    { date: 'Jul', drawdown: 0 },
    { date: 'Aug', drawdown: -2.1 },
    { date: 'Sep', drawdown: -1.2 },
    { date: 'Oct', drawdown: -4.8 },
    { date: 'Nov', drawdown: -2.3 },
    { date: 'Dec', drawdown: -1.1 },
    { date: 'Jan', drawdown: -0.5 },
  ]

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
          subtitle={`LTCG: ${formatCurrency(ltcgHoldings.reduce((sum, h) => sum + h.taxLiability, 0))}`}
        />
        <MetricCard
          title="Sharpe Ratio"
          value={riskMetrics.sharpeRatio.toFixed(2)}
          icon={<Target className="w-5 h-5" />}
          subtitle={`Sortino: ${riskMetrics.sortinoRatio.toFixed(2)}`}
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
                <span className="text-sm font-bold text-success">{formatCurrency(ltcgHoldings.reduce((sum, h) => sum + h.taxLiability, 0))}</span>
              </div>
              <div className="text-xs text-muted-foreground mt-2">
                Held for &gt;12 months
              </div>
            </div>
          </div>

          <div className="p-4 bg-dark-700/30 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-muted-foreground">Short Term Capital Gains (STCG)</h3>
              <span className="text-xs px-2 py-1 bg-warning/10 text-warning rounded">15% Tax</span>
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
                <span className="text-sm font-bold text-warning">{formatCurrency(stcgHoldings.reduce((sum, h) => sum + h.taxLiability, 0))}</span>
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
          <BarChart3 className="w-5 h-5 text-purple-500" />
          Holdings Details
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
                <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Holding</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Tax Type</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Tax Liability</th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((holding, index) => (
                <tr key={index} className="border-b border-dark-700/50 hover:bg-dark-700/30 transition-colors">
                  <td className="py-3 px-4">
                    <div>
                      <div className="text-sm font-medium text-white">{holding.symbol}</div>
                      <div className="text-xs text-muted-foreground">{holding.name}</div>
                    </div>
                  </td>
                  <td className="text-right py-3 px-4 text-sm text-white">{holding.quantity}</td>
                  <td className="text-right py-3 px-4 text-sm text-white">{formatCurrency(holding.avgPrice)}</td>
                  <td className="text-right py-3 px-4 text-sm text-white">{formatCurrency(holding.ltp)}</td>
                  <td className="text-right py-3 px-4 text-sm font-medium text-white">{formatCurrency(holding.currentValue)}</td>
                  <td className="text-right py-3 px-4">
                    <div className={`text-sm font-bold ${holding.pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                      {formatCurrency(holding.pnl)}
                    </div>
                    <div className={`text-xs ${holding.pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                      {formatPercentage(holding.pnlPercent)}
                    </div>
                  </td>
                  <td className="text-center py-3 px-4">
                    <span className="text-xs text-muted-foreground">{holding.holdingDays} days</span>
                  </td>
                  <td className="text-center py-3 px-4">
                    <span className={`text-xs px-2 py-1 rounded ${
                      holding.taxType === 'LTCG'
                        ? 'bg-green-500/10 text-success'
                        : 'bg-warning/10 text-warning'
                    }`}>
                      {holding.taxType} ({holding.taxRate}%)
                    </span>
                  </td>
                  <td className="text-right py-3 px-4">
                    <span className="text-sm font-medium text-white">
                      {holding.taxLiability > 0 ? formatCurrency(holding.taxLiability) : '-'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="border-t border-dark-600">
              <tr>
                <td colSpan={4} className="py-3 px-4 text-sm font-bold text-white">TOTAL</td>
                <td className="text-right py-3 px-4 text-sm font-bold text-white">{formatCurrency(totalCurrentValue)}</td>
                <td className="text-right py-3 px-4">
                  <div className={`text-sm font-bold ${totalPnL >= 0 ? 'text-success' : 'text-danger'}`}>
                    {formatCurrency(totalPnL)}
                  </div>
                  <div className={`text-xs ${totalPnL >= 0 ? 'text-success' : 'text-danger'}`}>
                    {formatPercentage(totalPnLPercent)}
                  </div>
                </td>
                <td colSpan={2}></td>
                <td className="text-right py-3 px-4 text-sm font-bold text-white">{formatCurrency(totalTaxLiability)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Monthly Returns & Risk Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Returns Chart */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-500" />
            Monthly Returns
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={monthlyReturns}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis dataKey="month" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f1429',
                  border: '1px solid #1f2740',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#fff' }}
              />
              <Legend />
              <Bar dataKey="portfolio" name="Portfolio" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="nifty" name="Nifty 50" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Risk-Adjusted Metrics */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-purple-500" />
            Risk-Adjusted Metrics
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-dark-700/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Sharpe Ratio</div>
                <div className="text-2xl font-bold text-white">{riskMetrics.sharpeRatio.toFixed(2)}</div>
                <div className="text-xs text-success mt-1">Excellent</div>
              </div>
              <div className="p-3 bg-dark-700/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Sortino Ratio</div>
                <div className="text-2xl font-bold text-white">{riskMetrics.sortinoRatio.toFixed(2)}</div>
                <div className="text-xs text-success mt-1">Strong</div>
              </div>
              <div className="p-3 bg-dark-700/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Calmar Ratio</div>
                <div className="text-2xl font-bold text-white">{riskMetrics.calmarRatio.toFixed(2)}</div>
                <div className="text-xs text-warning mt-1">Good</div>
              </div>
              <div className="p-3 bg-dark-700/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Information Ratio</div>
                <div className="text-2xl font-bold text-white">{riskMetrics.informationRatio.toFixed(2)}</div>
                <div className="text-xs text-muted-foreground mt-1">vs Nifty 50</div>
              </div>
            </div>
            <div className="pt-4 border-t border-dark-600 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Volatility (Annual)</span>
                <span className="text-sm font-medium text-white">{riskMetrics.volatility.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Portfolio Beta</span>
                <span className="text-sm font-medium text-white">{riskMetrics.beta.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Alpha (Annual)</span>
                <span className="text-sm font-medium text-success">{formatPercentage(riskMetrics.alpha)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">R-Squared</span>
                <span className="text-sm font-medium text-white">{riskMetrics.rSquared.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Correlation Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Correlation Scatter Plot */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-500" />
            Correlation with Nifty 50
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis
                type="number"
                dataKey="nifty"
                name="Nifty Correlation"
                stroke="#888"
                domain={[0.6, 0.95]}
                label={{ value: 'Nifty Correlation', position: 'insideBottom', offset: -5, fill: '#888' }}
              />
              <YAxis
                type="number"
                dataKey="sector"
                name="Sector Correlation"
                stroke="#888"
                domain={[0.7, 1.0]}
                label={{ value: 'Sector Correlation', angle: -90, position: 'insideLeft', fill: '#888' }}
              />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{
                  backgroundColor: '#0f1429',
                  border: '1px solid #1f2740',
                  borderRadius: '8px',
                }}
                formatter={(value: any) => value.toFixed(2)}
              />
              <Scatter name="Holdings" data={correlationData} fill="#8b5cf6">
                {correlationData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill="#8b5cf6" />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
          <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
            <AlertCircle className="w-4 h-4" />
            Higher correlation indicates stronger movement with benchmark
          </div>
        </div>

        {/* Drawdown Analysis */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-danger" />
            Drawdown Analysis
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={drawdownData}>
              <defs>
                <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
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
              <Area
                type="monotone"
                dataKey="drawdown"
                stroke="#ef4444"
                strokeWidth={2}
                fill="url(#colorDrawdown)"
              />
            </AreaChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="p-3 bg-dark-700/30 rounded-lg">
              <div className="text-xs text-muted-foreground mb-1">Max Drawdown</div>
              <div className="text-xl font-bold text-danger">{formatPercentage(riskMetrics.maxDrawdown)}</div>
            </div>
            <div className="p-3 bg-dark-700/30 rounded-lg">
              <div className="text-xs text-muted-foreground mb-1">Current Drawdown</div>
              <div className="text-xl font-bold text-warning">-0.5%</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
