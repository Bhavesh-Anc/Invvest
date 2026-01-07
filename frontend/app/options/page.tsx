'use client'

import React, { useState } from 'react'
import {
  TrendingUp, TrendingDown, Activity, Target,
  AlertCircle, Search, RefreshCw, ChevronDown,
  Calendar, DollarSign, Zap
} from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ScatterChart, Scatter, Cell
} from 'recharts'
import MetricCard from '@/components/ui/MetricCard'
import { formatCurrency, formatPercentage } from '@/lib/utils'

export default function OptionsAnalyticsPage() {
  const [selectedStock, setSelectedStock] = useState('NIFTY')
  const [selectedExpiry, setSelectedExpiry] = useState('25-JAN-2024')

  // Greeks summary
  const greeksSummary = {
    portfolioDelta: 145.8,
    portfolioGamma: 0.082,
    portfolioTheta: -2847.50,
    portfolioVega: 18250.00,
    portfolioRho: 1240.00,
  }

  // Options chain data
  const optionsChain = [
    {
      strike: 21600,
      callOI: 45620,
      callOIChange: 12.5,
      callVolume: 18950,
      callLTP: 385.50,
      callIV: 14.2,
      callDelta: 0.68,
      callGamma: 0.0024,
      callTheta: -42.5,
      callVega: 125.0,
      putOI: 28340,
      putOIChange: -5.2,
      putVolume: 9820,
      putLTP: 92.75,
      putIV: 15.8,
      putDelta: -0.32,
      putGamma: 0.0024,
      putTheta: -38.2,
      putVega: 118.0,
    },
    {
      strike: 21700,
      callOI: 52340,
      callOIChange: 18.2,
      callVolume: 24580,
      callLTP: 320.25,
      callIV: 13.8,
      callDelta: 0.58,
      callGamma: 0.0028,
      callTheta: -48.5,
      callVega: 142.0,
      putOI: 38920,
      putOIChange: 8.4,
      putVolume: 15240,
      putLTP: 125.50,
      putIV: 16.2,
      putDelta: -0.42,
      putGamma: 0.0028,
      putTheta: -44.8,
      putVega: 138.0,
    },
    {
      strike: 21800,
      callOI: 68750,
      callOIChange: 25.6,
      callVolume: 32840,
      callLTP: 265.75,
      callIV: 13.5,
      callDelta: 0.52,
      callGamma: 0.0032,
      callTheta: -52.8,
      callVega: 158.0,
      putOI: 54280,
      putOIChange: 15.8,
      putVolume: 22680,
      putLTP: 168.25,
      putIV: 16.8,
      putDelta: -0.48,
      putGamma: 0.0032,
      putTheta: -50.2,
      putVega: 154.0,
    },
    {
      strike: 21900,
      callOI: 82450,
      callOIChange: 32.4,
      callVolume: 41250,
      callLTP: 218.50,
      callIV: 13.2,
      callDelta: 0.45,
      callGamma: 0.0034,
      callTheta: -56.2,
      callVega: 168.0,
      putOI: 72840,
      putOIChange: 28.5,
      putVolume: 31450,
      putLTP: 220.75,
      putIV: 17.5,
      putDelta: -0.55,
      putGamma: 0.0034,
      putTheta: -54.8,
      putVega: 165.0,
    },
    {
      strike: 22000,
      callOI: 125680,
      callOIChange: 45.8,
      callVolume: 58920,
      callLTP: 178.25,
      callIV: 13.0,
      callDelta: 0.38,
      callGamma: 0.0032,
      callTheta: -54.5,
      callVega: 162.0,
      putOI: 142500,
      putOIChange: 52.4,
      putVolume: 64280,
      putLTP: 280.50,
      putIV: 18.2,
      putDelta: -0.62,
      putGamma: 0.0032,
      putTheta: -58.2,
      putVega: 172.0,
    },
    {
      strike: 22100,
      callOI: 98240,
      callOIChange: 22.8,
      callVolume: 38450,
      callLTP: 142.75,
      callIV: 12.8,
      callDelta: 0.32,
      callGamma: 0.0028,
      callTheta: -48.2,
      callVega: 145.0,
      putOI: 118640,
      putOIChange: 38.6,
      putVolume: 48920,
      putLTP: 345.25,
      putIV: 19.0,
      putDelta: -0.68,
      putGamma: 0.0028,
      putTheta: -52.5,
      putVega: 152.0,
    },
  ]

  // ATM strike (closest to current price)
  const currentPrice = 21894
  const atmStrike = 21900

  // IV Skew data
  const ivSkewData = [
    { strike: 21600, callIV: 14.2, putIV: 15.8, moneyness: -1.34 },
    { strike: 21700, callIV: 13.8, putIV: 16.2, moneyness: -0.89 },
    { strike: 21800, callIV: 13.5, putIV: 16.8, moneyness: -0.43 },
    { strike: 21900, callIV: 13.2, putIV: 17.5, moneyness: 0.03 },
    { strike: 22000, callIV: 13.0, putIV: 18.2, moneyness: 0.48 },
    { strike: 22100, callIV: 12.8, putIV: 19.0, moneyness: 0.94 },
  ]

  // Greeks evolution (intraday)
  const greeksEvolution = [
    { time: '09:30', delta: 142.5, gamma: 0.078, theta: -2650, vega: 17800 },
    { time: '10:30', delta: 144.2, gamma: 0.080, theta: -2720, vega: 17950 },
    { time: '11:30', delta: 145.8, gamma: 0.082, theta: -2785, vega: 18100 },
    { time: '12:30', delta: 146.5, gamma: 0.083, theta: -2820, vega: 18200 },
    { time: '13:30', delta: 145.9, gamma: 0.082, theta: -2840, vega: 18230 },
    { time: '14:30', delta: 145.8, gamma: 0.082, theta: -2847, vega: 18250 },
  ]

  // Put-Call Ratio data
  const pcrData = [
    { strike: 21600, pcr: 0.62, type: 'Bullish' },
    { strike: 21700, pcr: 0.74, type: 'Neutral' },
    { strike: 21800, pcr: 0.79, type: 'Neutral' },
    { strike: 21900, pcr: 0.88, type: 'Neutral' },
    { strike: 22000, pcr: 1.13, type: 'Bearish' },
    { strike: 22100, pcr: 1.21, type: 'Bearish' },
  ]

  // Open Interest chart data
  const oiChartData = optionsChain.map(row => ({
    strike: row.strike,
    callOI: row.callOI,
    putOI: row.putOI,
  }))

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Options Analytics</h1>
          <p className="text-muted-foreground">Advanced Greeks, Options Chain & Volatility Analysis</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors">
            <RefreshCw className="w-4 h-4 inline mr-2" />
            Refresh
          </button>
          <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors">
            Strategy Builder
          </button>
        </div>
      </div>

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
    </div>
  )
}
