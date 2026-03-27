'use client'

import React, { useState, useEffect } from 'react'
import {
  TrendingUp, TrendingDown, Activity, Target,
  RefreshCw, Zap, BarChart3, AlertCircle
} from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, Cell
} from 'recharts'
import MetricCard from '@/components/ui/MetricCard'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { api } from '@/lib/api'

interface MispricedOption {
  symbol: string
  strike: number
  expiry: string
  option_type: string
  implied_volatility: number
  forecasted_volatility: number
  mispricing: number
  theoretical_price: number
  market_price: number
  action: string
  confidence: number
}

interface VolatilitySurface {
  strikes: number[]
  expiries: string[]
  surface: number[][]
}

export default function VolatilityArbitrage() {
  const [loading, setLoading] = useState(false)
  const [symbol, setSymbol] = useState('NIFTY')
  const [forecastMethod, setForecastMethod] = useState('ewma')
  const [opportunities, setOpportunities] = useState<MispricedOption[]>([])
  const [forecastData, setForecastData] = useState<any>(null)
  const [surfaceData, setSurfaceData] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  const symbols = ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY', 'HDFC']
  const methods = ['ewma', 'garch', 'historical']

  useEffect(() => {
    fetchData()
  }, [symbol, forecastMethod])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [opps, forecast] = await Promise.all([
        api.optionsAdvanced.getVolatilityOpportunities(symbol, forecastMethod),
        api.optionsAdvanced.forecastVolatility(symbol, forecastMethod),
      ])
      setOpportunities(opps)
      setForecastData(forecast)
      // Build scatter data for IV vs RV comparison
      if (opps.length > 0) {
        setSurfaceData(opps.map((o: MispricedOption) => ({
          strike: o.strike,
          iv: (o.implied_volatility * 100).toFixed(2),
          rv: (o.forecasted_volatility * 100).toFixed(2),
          mispricing: (o.mispricing * 100).toFixed(2),
          action: o.action,
        })))
      }
    } catch (err) {
      setError('Failed to fetch volatility data. Ensure backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const getActionColor = (action: string) => {
    if (action === 'buy_vol') return 'text-green-400'
    if (action === 'sell_vol') return 'text-red-400'
    return 'text-yellow-400'
  }

  const getActionBadge = (action: string) => {
    if (action === 'buy_vol') return 'bg-green-400/10 text-green-400 border border-green-400/20'
    if (action === 'sell_vol') return 'bg-red-400/10 text-red-400 border border-red-400/20'
    return 'bg-yellow-400/10 text-yellow-400 border border-yellow-400/20'
  }

  const buyVol = opportunities.filter(o => o.action === 'buy_vol').length
  const sellVol = opportunities.filter(o => o.action === 'sell_vol').length
  const avgMispricing = opportunities.length > 0
    ? opportunities.reduce((s, o) => s + Math.abs(o.mispricing), 0) / opportunities.length
    : 0

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground">Symbol:</label>
          <select
            value={symbol}
            onChange={e => setSymbol(e.target.value)}
            className="bg-dark-700 border border-dark-500 text-white rounded-lg px-3 py-1.5 text-sm"
          >
            {symbols.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground">Vol Forecast:</label>
          <select
            value={forecastMethod}
            onChange={e => setForecastMethod(e.target.value)}
            className="bg-dark-700 border border-dark-500 text-white rounded-lg px-3 py-1.5 text-sm"
          >
            {methods.map(m => <option key={m} value={m}>{m.toUpperCase()}</option>)}
          </select>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Scanning...' : 'Scan'}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-400/10 border border-red-400/20 rounded-lg text-red-400 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Summary Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Opportunities Found"
          value={opportunities.length.toString()}
          icon={<Target className="w-5 h-5" />}
          color="blue"
        />
        <MetricCard
          title="Buy Volatility"
          value={buyVol.toString()}
          subtitle="IV underpriced"
          icon={<TrendingUp className="w-5 h-5" />}
          color="green"
        />
        <MetricCard
          title="Sell Volatility"
          value={sellVol.toString()}
          subtitle="IV overpriced"
          icon={<TrendingDown className="w-5 h-5" />}
          color="red"
        />
        <MetricCard
          title="Avg Mispricing"
          value={formatPercentage(avgMispricing)}
          subtitle="IV vs Forecast"
          icon={<Activity className="w-5 h-5" />}
          color="yellow"
        />
      </div>

      {/* Forecast Info */}
      {forecastData && (
        <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
          <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
            <Zap className="w-4 h-4 text-yellow-400" />
            {forecastMethod.toUpperCase()} Volatility Forecast — {symbol}
          </h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Forecasted RV</span>
              <p className="text-white font-semibold mt-1">
                {forecastData.forecasted_volatility != null
                  ? formatPercentage(forecastData.forecasted_volatility)
                  : '—'}
              </p>
            </div>
            <div>
              <span className="text-muted-foreground">Method</span>
              <p className="text-white font-semibold mt-1 uppercase">{forecastData.method || forecastMethod}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Symbol</span>
              <p className="text-white font-semibold mt-1">{forecastData.symbol || symbol}</p>
            </div>
          </div>
        </div>
      )}

      {/* IV vs RV Scatter */}
      {surfaceData.length > 0 && (
        <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
          <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            IV vs Forecasted RV by Strike
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={surfaceData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="strike" tick={{ fill: '#9CA3AF', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} unit="%" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }}
                labelStyle={{ color: '#F9FAFB' }}
              />
              <Legend />
              <Bar dataKey="iv" name="Implied Vol %" fill="#3B82F6" radius={[3, 3, 0, 0]} />
              <Bar dataKey="rv" name="Forecasted RV %" fill="#10B981" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Opportunities Table */}
      <div className="bg-dark-800 border border-dark-600 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-dark-600">
          <h3 className="text-sm font-medium text-white flex items-center gap-2">
            <Target className="w-4 h-4 text-purple-400" />
            Mispriced Options — Arbitrage Opportunities
          </h3>
        </div>
        {opportunities.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground text-sm">
            {loading ? 'Scanning for opportunities...' : 'No significant mispricing detected at current thresholds.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-dark-700">
                  <th className="px-4 py-2 text-left text-muted-foreground font-medium">Strike</th>
                  <th className="px-4 py-2 text-left text-muted-foreground font-medium">Type</th>
                  <th className="px-4 py-2 text-left text-muted-foreground font-medium">Expiry</th>
                  <th className="px-4 py-2 text-right text-muted-foreground font-medium">IV</th>
                  <th className="px-4 py-2 text-right text-muted-foreground font-medium">Forecast RV</th>
                  <th className="px-4 py-2 text-right text-muted-foreground font-medium">Mispricing</th>
                  <th className="px-4 py-2 text-right text-muted-foreground font-medium">Mkt Price</th>
                  <th className="px-4 py-2 text-right text-muted-foreground font-medium">Theo Price</th>
                  <th className="px-4 py-2 text-center text-muted-foreground font-medium">Action</th>
                  <th className="px-4 py-2 text-right text-muted-foreground font-medium">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-600">
                {opportunities.map((opp, i) => (
                  <tr key={i} className="hover:bg-dark-700/50 transition-colors">
                    <td className="px-4 py-2.5 text-white font-medium">{opp.strike.toLocaleString()}</td>
                    <td className="px-4 py-2.5 text-white">{opp.option_type}</td>
                    <td className="px-4 py-2.5 text-muted-foreground">{opp.expiry}</td>
                    <td className="px-4 py-2.5 text-right text-white">{formatPercentage(opp.implied_volatility)}</td>
                    <td className="px-4 py-2.5 text-right text-white">{formatPercentage(opp.forecasted_volatility)}</td>
                    <td className={`px-4 py-2.5 text-right font-medium ${opp.mispricing > 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {opp.mispricing > 0 ? '+' : ''}{formatPercentage(opp.mispricing)}
                    </td>
                    <td className="px-4 py-2.5 text-right text-white">{formatCurrency(opp.market_price)}</td>
                    <td className="px-4 py-2.5 text-right text-white">{formatCurrency(opp.theoretical_price)}</td>
                    <td className="px-4 py-2.5 text-center">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${getActionBadge(opp.action)}`}>
                        {opp.action.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right text-white">{(opp.confidence * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
