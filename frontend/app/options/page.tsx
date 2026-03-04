'use client'

import React, { useState, useEffect } from 'react'
import {
  TrendingUp, TrendingDown, Activity, Target,
  AlertCircle, Search, RefreshCw, ChevronDown,
  Calendar, DollarSign, Zap, BarChart3
} from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ScatterChart, Scatter, Cell
} from 'recharts'
import MetricCard from '@/components/ui/MetricCard'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import api from '@/lib/api'
import Loading from '@/components/ui/Loading'
import ErrorDisplay from '@/components/ui/ErrorDisplay'
import VolatilityArbitrage from '@/components/strategies/VolatilityArbitrage'

type PageTab = 'analytics' | 'vol_arb'

export default function OptionsAnalyticsPage() {
  const [activeTab, setActiveTab] = useState<PageTab>('analytics')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [selectedStock, setSelectedStock] = useState('NIFTY')
  const [selectedExpiry, setSelectedExpiry] = useState('25-JAN-2024')
  const [greeksSummary, setGreeksSummary] = useState<any>(null)
  const [optionsChain, setOptionsChain] = useState<any[]>([])
  const [ivSkew, setIvSkew] = useState<any[]>([])
  const [greeksEvolution, setGreeksEvolution] = useState<any[]>([])
  const [oiDistribution, setOiDistribution] = useState<any[]>([])
  const [pcrAnalysis, setPcrAnalysis] = useState<any>(null)

  useEffect(() => {
    fetchOptionsData()
  }, [selectedStock, selectedExpiry])

  const fetchOptionsData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch all options data in parallel
      const [greeks, chain, skew, evolution, oiDist, pcr] = await Promise.all([
        api.options.getGreeksSummary(),
        api.options.getOptionsChain(selectedStock, selectedExpiry),
        api.options.getIVSkew(selectedStock, selectedExpiry),
        api.options.getGreeksEvolution(),
        api.options.getOIDistribution(selectedStock, selectedExpiry),
        api.options.getPCRAnalysis(selectedStock, selectedExpiry),
      ])

      setGreeksSummary(greeks)
      setOptionsChain(chain)
      setIvSkew(skew)
      setGreeksEvolution(evolution)
      setOiDistribution(oiDist)
      setPcrAnalysis(pcr)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch options data'))
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <Loading message="Loading options analytics..." />
  if (error) return <ErrorDisplay error={error} onRetry={fetchOptionsData} />
  if (!greeksSummary || !optionsChain) return null

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Options Analytics</h1>
          <p className="text-muted-foreground">Advanced Greeks, Options Chain & Volatility Analysis</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={fetchOptionsData} className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors">
            <RefreshCw className="w-4 h-4 inline mr-2" />
            Refresh
          </button>
          <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors">
            Strategy Builder
          </button>
        </div>
      </div>

      {/* Page Tabs */}
      <div className="flex border-b border-dark-600">
        {[
          { key: 'analytics' as PageTab, label: 'Options Chain & Greeks', icon: <Activity className="w-4 h-4" /> },
          { key: 'vol_arb' as PageTab, label: 'Volatility Arbitrage', icon: <BarChart3 className="w-4 h-4" /> },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-purple-500 text-white'
                : 'border-transparent text-muted-foreground hover:text-white'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'vol_arb' && <VolatilityArbitrage />}

      {activeTab === 'analytics' && <>

      {/* Stock & Expiry Selector */}
      <div className="card-glass rounded-xl p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="text-xs text-muted-foreground mb-2 block">Underlying</label>
            <select
              value={selectedStock}
              onChange={(e) => setSelectedStock(e.target.value)}
              className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="NIFTY">NIFTY 50</option>
              <option value="BANKNIFTY">BANK NIFTY</option>
              <option value="FINNIFTY">FIN NIFTY</option>
              <option value="RELIANCE">RELIANCE</option>
              <option value="TCS">TCS</option>
              <option value="HDFCBANK">HDFC BANK</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="text-xs text-muted-foreground mb-2 block">Expiry Date</label>
            <select
              value={selectedExpiry}
              onChange={(e) => setSelectedExpiry(e.target.value)}
              className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="25-JAN-2024">25-JAN-2024 (Weekly)</option>
              <option value="01-FEB-2024">01-FEB-2024 (Weekly)</option>
              <option value="29-FEB-2024">29-FEB-2024 (Monthly)</option>
              <option value="28-MAR-2024">28-MAR-2024 (Monthly)</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="text-xs text-muted-foreground mb-2 block">Current Price</label>
            <div className="px-4 py-2 bg-dark-700/50 border border-dark-600 rounded-lg">
              <div className="text-lg font-bold text-white">{formatCurrency(currentPrice)}</div>
            </div>
          </div>
          <div className="flex-1">
            <label className="text-xs text-muted-foreground mb-2 block">Days to Expiry</label>
            <div className="px-4 py-2 bg-dark-700/50 border border-dark-600 rounded-lg">
              <div className="text-lg font-bold text-warning">4 days</div>
            </div>
          </div>
        </div>
      </div>

      {/* Portfolio Greeks Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <MetricCard
          title="Portfolio Delta"
          value={greeksSummary.portfolioDelta.toFixed(1)}
          icon={<Target className="w-5 h-5" />}
          subtitle="Directional exposure"
          trend="neutral"
        />
        <MetricCard
          title="Portfolio Gamma"
          value={greeksSummary.portfolioGamma.toFixed(3)}
          icon={<Activity className="w-5 h-5" />}
          subtitle="Delta sensitivity"
          trend="neutral"
        />
        <MetricCard
          title="Portfolio Theta"
          value={formatCurrency(greeksSummary.portfolioTheta, '')}
          icon={<TrendingDown className="w-5 h-5" />}
          subtitle="Daily decay"
          trend="down"
        />
        <MetricCard
          title="Portfolio Vega"
          value={formatCurrency(greeksSummary.portfolioVega, '')}
          icon={<Zap className="w-5 h-5" />}
          subtitle="IV sensitivity"
          trend="up"
        />
        <MetricCard
          title="Portfolio Rho"
          value={formatCurrency(greeksSummary.portfolioRho, '')}
          icon={<DollarSign className="w-5 h-5" />}
          subtitle="Rate sensitivity"
          trend="neutral"
        />
      </div>

      {/* Greeks Evolution & IV Skew */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Greeks Evolution (Intraday) */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-500" />
            Greeks Evolution (Today)
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={greeksEvolution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis dataKey="time" stroke="#888" />
              <YAxis yAxisId="left" stroke="#888" />
              <YAxis yAxisId="right" orientation="right" stroke="#888" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f1429',
                  border: '1px solid #1f2740',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="delta" stroke="#8b5cf6" strokeWidth={2} name="Delta" />
              <Line yAxisId="right" type="monotone" dataKey="theta" stroke="#ef4444" strokeWidth={2} name="Theta" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* IV Skew */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-purple-500" />
            Implied Volatility Skew
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={ivSkewData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis dataKey="strike" stroke="#888" />
              <YAxis stroke="#888" label={{ value: 'IV (%)', angle: -90, position: 'insideLeft', fill: '#888' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f1429',
                  border: '1px solid #1f2740',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="callIV" stroke="#10b981" strokeWidth={2} name="Call IV" />
              <Line type="monotone" dataKey="putIV" stroke="#ef4444" strokeWidth={2} name="Put IV" />
            </LineChart>
          </ResponsiveContainer>
          <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
            <AlertCircle className="w-4 h-4" />
            Put IV skew suggests mild bearish sentiment
          </div>
        </div>
      </div>

      {/* Open Interest Analysis */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <BarChart className="w-5 h-5 text-purple-500" />
          Open Interest Distribution
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={oiChartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
            <XAxis dataKey="strike" stroke="#888" />
            <YAxis stroke="#888" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f1429',
                border: '1px solid #1f2740',
                borderRadius: '8px',
              }}
            />
            <Legend />
            <Bar dataKey="callOI" name="Call OI" fill="#10b981" radius={[4, 4, 0, 0]} />
            <Bar dataKey="putOI" name="Put OI" fill="#ef4444" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="p-3 bg-dark-700/30 rounded-lg">
            <div className="text-xs text-muted-foreground mb-1">Max Call OI</div>
            <div className="text-lg font-bold text-success">22,000</div>
            <div className="text-xs text-muted-foreground">Resistance</div>
          </div>
          <div className="p-3 bg-dark-700/30 rounded-lg">
            <div className="text-xs text-muted-foreground mb-1">Max Put OI</div>
            <div className="text-lg font-bold text-danger">22,000</div>
            <div className="text-xs text-muted-foreground">Support</div>
          </div>
          <div className="p-3 bg-dark-700/30 rounded-lg">
            <div className="text-xs text-muted-foreground mb-1">PCR (OI)</div>
            <div className="text-lg font-bold text-warning">0.94</div>
            <div className="text-xs text-muted-foreground">Neutral</div>
          </div>
        </div>
      </div>

      {/* Options Chain Table */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-purple-500" />
          Options Chain - {selectedStock}
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-600">
                <th colSpan={5} className="text-center py-3 px-2 text-xs font-medium text-success">CALLS</th>
                <th className="text-center py-3 px-2 text-xs font-medium text-white bg-dark-700">STRIKE</th>
                <th colSpan={5} className="text-center py-3 px-2 text-xs font-medium text-danger">PUTS</th>
              </tr>
              <tr className="border-b border-dark-600">
                <th className="text-right py-2 px-2 text-xs font-medium text-muted-foreground">OI</th>
                <th className="text-right py-2 px-2 text-xs font-medium text-muted-foreground">Chg%</th>
                <th className="text-right py-2 px-2 text-xs font-medium text-muted-foreground">Vol</th>
                <th className="text-right py-2 px-2 text-xs font-medium text-muted-foreground">LTP</th>
                <th className="text-right py-2 px-2 text-xs font-medium text-muted-foreground">IV%</th>
                <th className="text-center py-2 px-2 text-xs font-medium text-white bg-dark-700">Price</th>
                <th className="text-left py-2 px-2 text-xs font-medium text-muted-foreground">IV%</th>
                <th className="text-left py-2 px-2 text-xs font-medium text-muted-foreground">LTP</th>
                <th className="text-left py-2 px-2 text-xs font-medium text-muted-foreground">Vol</th>
                <th className="text-left py-2 px-2 text-xs font-medium text-muted-foreground">Chg%</th>
                <th className="text-left py-2 px-2 text-xs font-medium text-muted-foreground">OI</th>
              </tr>
            </thead>
            <tbody>
              {optionsChain.map((row, index) => {
                const isATM = row.strike === atmStrike
                const rowClass = isATM ? 'bg-purple-500/10 border-l-2 border-r-2 border-purple-500' : 'hover:bg-dark-700/30'

                return (
                  <tr key={index} className={`border-b border-dark-700/50 ${rowClass} transition-colors`}>
                    {/* Call Side */}
                    <td className="text-right py-2 px-2 text-white">{row.callOI.toLocaleString()}</td>
                    <td className="text-right py-2 px-2">
                      <span className={row.callOIChange >= 0 ? 'text-success' : 'text-danger'}>
                        {formatPercentage(row.callOIChange)}
                      </span>
                    </td>
                    <td className="text-right py-2 px-2 text-white">{row.callVolume.toLocaleString()}</td>
                    <td className="text-right py-2 px-2 text-white font-medium">{formatCurrency(row.callLTP)}</td>
                    <td className="text-right py-2 px-2 text-muted-foreground">{row.callIV.toFixed(1)}%</td>

                    {/* Strike Price */}
                    <td className="text-center py-2 px-2 bg-dark-700">
                      <span className={`font-bold ${isATM ? 'text-purple-400' : 'text-white'}`}>
                        {row.strike}
                      </span>
                      {isATM && <span className="ml-2 text-xs text-purple-400">ATM</span>}
                    </td>

                    {/* Put Side */}
                    <td className="text-left py-2 px-2 text-muted-foreground">{row.putIV.toFixed(1)}%</td>
                    <td className="text-left py-2 px-2 text-white font-medium">{formatCurrency(row.putLTP)}</td>
                    <td className="text-left py-2 px-2 text-white">{row.putVolume.toLocaleString()}</td>
                    <td className="text-left py-2 px-2">
                      <span className={row.putOIChange >= 0 ? 'text-success' : 'text-danger'}>
                        {formatPercentage(row.putOIChange)}
                      </span>
                    </td>
                    <td className="text-left py-2 px-2 text-white">{row.putOI.toLocaleString()}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Greeks Details for Selected Strike */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Target className="w-5 h-5 text-purple-500" />
          Greeks Breakdown - ATM Strike ({atmStrike})
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-6">
          {optionsChain
            .filter(row => row.strike === atmStrike)
            .map(row => (
              <React.Fragment key={row.strike}>
                <div className="p-4 bg-dark-700/30 rounded-lg">
                  <div className="text-xs text-muted-foreground mb-2">Delta</div>
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-lg font-bold text-success">Call: {row.callDelta.toFixed(2)}</div>
                      <div className="text-lg font-bold text-danger">Put: {row.putDelta.toFixed(2)}</div>
                    </div>
                  </div>
                </div>
                <div className="p-4 bg-dark-700/30 rounded-lg">
                  <div className="text-xs text-muted-foreground mb-2">Gamma</div>
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-lg font-bold text-white">Call: {row.callGamma.toFixed(4)}</div>
                      <div className="text-lg font-bold text-white">Put: {row.putGamma.toFixed(4)}</div>
                    </div>
                  </div>
                </div>
                <div className="p-4 bg-dark-700/30 rounded-lg">
                  <div className="text-xs text-muted-foreground mb-2">Theta</div>
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-lg font-bold text-danger">Call: {row.callTheta.toFixed(1)}</div>
                      <div className="text-lg font-bold text-danger">Put: {row.putTheta.toFixed(1)}</div>
                    </div>
                  </div>
                </div>
                <div className="p-4 bg-dark-700/30 rounded-lg">
                  <div className="text-xs text-muted-foreground mb-2">Vega</div>
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-lg font-bold text-purple-400">Call: {row.callVega.toFixed(1)}</div>
                      <div className="text-lg font-bold text-purple-400">Put: {row.putVega.toFixed(1)}</div>
                    </div>
                  </div>
                </div>
                <div className="p-4 bg-dark-700/30 rounded-lg">
                  <div className="text-xs text-muted-foreground mb-2">Implied Volatility</div>
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-lg font-bold text-white">Call: {row.callIV.toFixed(1)}%</div>
                      <div className="text-lg font-bold text-white">Put: {row.putIV.toFixed(1)}%</div>
                    </div>
                  </div>
                </div>
              </React.Fragment>
            ))}
        </div>
      </div>

      {/* Put-Call Ratio Analysis */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-purple-500" />
          Put-Call Ratio (PCR) Analysis
        </h2>
        <div className="space-y-3">
          {pcrData.map((item, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-dark-700/30 rounded-lg">
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium text-white w-20">Strike: {item.strike}</span>
                <div className="w-48 h-2 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${
                      item.pcr < 0.7 ? 'bg-success' : item.pcr > 1.0 ? 'bg-danger' : 'bg-warning'
                    }`}
                    style={{ width: `${Math.min(item.pcr * 50, 100)}%` }}
                  ></div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-lg font-bold text-white">{item.pcr.toFixed(2)}</span>
                <span
                  className={`text-xs px-3 py-1 rounded ${
                    item.type === 'Bullish'
                      ? 'bg-success/10 text-success'
                      : item.type === 'Bearish'
                      ? 'bg-danger/10 text-danger'
                      : 'bg-warning/10 text-warning'
                  }`}
                >
                  {item.type}
                </span>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 p-4 bg-dark-700/30 rounded-lg">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <AlertCircle className="w-4 h-4" />
            <span>PCR &lt; 0.7 = Bullish | PCR 0.7-1.0 = Neutral | PCR &gt; 1.0 = Bearish</span>
          </div>
        </div>
      </div>

      </>}
    </div>
  )
}
