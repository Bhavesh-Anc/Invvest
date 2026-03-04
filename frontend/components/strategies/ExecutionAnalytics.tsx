'use client'

import React, { useState, useEffect } from 'react'
import {
  Clock, TrendingDown, Activity, Target,
  RefreshCw, AlertCircle, Zap, BarChart3, GitBranch
} from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine
} from 'recharts'
import MetricCard from '@/components/ui/MetricCard'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { api } from '@/lib/api'

type AlgoTab = 'vwap' | 'twap' | 'impact' | 'sor'

export default function ExecutionAnalytics() {
  const [loading, setLoading] = useState(false)
  const [activeAlgo, setActiveAlgo] = useState<AlgoTab>('vwap')
  const [symbol, setSymbol] = useState('NIFTY')
  const [quantity, setQuantity] = useState(1000)
  const [side, setSide] = useState('buy')
  const [vwapSchedule, setVwapSchedule] = useState<any>(null)
  const [twapSchedule, setTwapSchedule] = useState<any>(null)
  const [impactData, setImpactData] = useState<any>(null)
  const [sorData, setSorData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    runAlgorithm()
  }, [symbol, activeAlgo])

  const runAlgorithm = async () => {
    setLoading(true)
    setError(null)
    try {
      const today = new Date()
      const startTime = `${today.toISOString().split('T')[0]}T09:15:00`
      const endTime = `${today.toISOString().split('T')[0]}T15:30:00`

      if (activeAlgo === 'vwap') {
        const result = await api.execution.generateVWAPSchedule({
          symbol,
          quantity,
          side,
          start_time: startTime,
          end_time: endTime,
        })
        setVwapSchedule(result)
      } else if (activeAlgo === 'twap') {
        const result = await api.execution.generateTWAPSchedule({
          symbol,
          quantity,
          side,
          start_time: startTime,
          end_time: endTime,
          num_slices: 12,
        })
        setTwapSchedule(result)
      } else if (activeAlgo === 'impact') {
        const result = await api.execution.calculateMarketImpact({
          symbol,
          quantity,
          price: 20000,
          adv: 1000000,
          execution_time: 1.0,
        })
        setImpactData(result)
      } else if (activeAlgo === 'sor') {
        const result = await api.execution.optimizeSmartRouting({
          symbol,
          quantity,
          side,
          order_type: 'limit',
        })
        setSorData(result)
      }
    } catch (err) {
      setError('Failed to run execution algorithm. Ensure backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const algoTabs: { key: AlgoTab; label: string; icon: React.ReactNode }[] = [
    { key: 'vwap', label: 'VWAP', icon: <BarChart3 className="w-4 h-4" /> },
    { key: 'twap', label: 'TWAP', icon: <Clock className="w-4 h-4" /> },
    { key: 'impact', label: 'Market Impact', icon: <TrendingDown className="w-4 h-4" /> },
    { key: 'sor', label: 'Smart Routing', icon: <GitBranch className="w-4 h-4" /> },
  ]

  const renderVWAP = () => {
    if (!vwapSchedule) return null
    const slices = vwapSchedule.schedule || []
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard title="Total Quantity" value={(vwapSchedule.total_quantity || quantity).toLocaleString()} icon={<Target className="w-5 h-5" />} color="blue" />
          <MetricCard title="Num Slices" value={(vwapSchedule.num_slices || slices.length).toString()} icon={<Activity className="w-5 h-5" />} color="green" />
          <MetricCard title="Expected Cost" value={vwapSchedule.expected_impact_bps ? `${vwapSchedule.expected_impact_bps.toFixed(1)} bps` : '—'} icon={<TrendingDown className="w-5 h-5" />} color="yellow" />
          <MetricCard title="Algorithm" value="VWAP" icon={<BarChart3 className="w-5 h-5" />} color="purple" />
        </div>
        {slices.length > 0 && (
          <div className="bg-dark-700 rounded-xl p-4">
            <h4 className="text-sm text-white font-medium mb-3">Execution Schedule</h4>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={slices.slice(0, 20)} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time_slot" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
                <YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }} />
                <Bar dataKey="quantity" name="Qty to Execute" fill="#3B82F6" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    )
  }

  const renderTWAP = () => {
    if (!twapSchedule) return null
    const slices = twapSchedule.schedule || []
    const sliceQty = twapSchedule.slice_quantity || (quantity / 12)
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard title="Slice Qty" value={Math.round(sliceQty).toLocaleString()} icon={<Target className="w-5 h-5" />} color="blue" />
          <MetricCard title="Num Slices" value={(twapSchedule.num_slices || slices.length || 12).toString()} icon={<Activity className="w-5 h-5" />} color="green" />
          <MetricCard title="Interval" value={twapSchedule.interval_minutes ? `${twapSchedule.interval_minutes} min` : '30 min'} icon={<Clock className="w-5 h-5" />} color="yellow" />
          <MetricCard title="Algorithm" value="TWAP" icon={<Clock className="w-5 h-5" />} color="purple" />
        </div>
        <div className="bg-dark-700 rounded-xl p-4">
          <h4 className="text-sm text-white font-medium mb-3">Equal Time Slices</h4>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={Array.from({ length: 12 }, (_, i) => ({
              slice: `Slice ${i + 1}`,
              qty: Math.round(sliceQty),
              cumulative: Math.round(sliceQty * (i + 1)),
            }))} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="slice" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
              <YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }} />
              <Area dataKey="cumulative" name="Cumulative Qty" fill="#10B981" stroke="#10B981" fillOpacity={0.2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    )
  }

  const renderImpact = () => {
    if (!impactData) return null
    const permanent = impactData.permanent_impact_bps || 0
    const temporary = impactData.temporary_impact_bps || 0
    const total = impactData.total_impact_bps || permanent + temporary
    const impactChart = [
      { name: 'Permanent Impact', value: permanent },
      { name: 'Temporary Impact', value: temporary },
      { name: 'Total Impact', value: total },
    ]
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <MetricCard title="Permanent Impact" value={`${permanent.toFixed(1)} bps`} subtitle="Market footprint" icon={<TrendingDown className="w-5 h-5" />} color="red" />
          <MetricCard title="Temporary Impact" value={`${temporary.toFixed(1)} bps`} subtitle="Execution friction" icon={<Activity className="w-5 h-5" />} color="yellow" />
          <MetricCard title="Total Impact" value={`${total.toFixed(1)} bps`} subtitle="Almgren-Chriss model" icon={<Zap className="w-5 h-5" />} color="purple" />
        </div>
        <div className="bg-dark-700 rounded-xl p-4">
          <h4 className="text-sm text-white font-medium mb-3">Market Impact Breakdown</h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={impactChart} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" tick={{ fill: '#9CA3AF', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} unit=" bps" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }}
                formatter={(val: any) => [`${val.toFixed(2)} bps`, 'Impact']}
              />
              <Bar dataKey="value" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        {impactData.optimal_execution_time && (
          <div className="p-3 bg-dark-700 rounded-lg text-sm text-muted-foreground">
            Optimal execution time: <span className="text-white font-medium">{impactData.optimal_execution_time.toFixed(2)} hours</span>
            {impactData.participation_rate && (
              <> &nbsp;|&nbsp; Participation rate: <span className="text-white font-medium">{(impactData.participation_rate * 100).toFixed(1)}%</span></>
            )}
          </div>
        )}
      </div>
    )
  }

  const renderSOR = () => {
    if (!sorData) return null
    const venues = sorData.venue_allocation || []
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <MetricCard title="Best Venue" value={sorData.best_venue || 'NSE'} icon={<GitBranch className="w-5 h-5" />} color="blue" />
          <MetricCard title="Expected Price" value={sorData.expected_price ? formatCurrency(sorData.expected_price) : '—'} icon={<Target className="w-5 h-5" />} color="green" />
          <MetricCard title="Fill Probability" value={sorData.fill_probability ? `${(sorData.fill_probability * 100).toFixed(0)}%` : '—'} icon={<Activity className="w-5 h-5" />} color="yellow" />
        </div>
        {venues.length > 0 && (
          <div className="bg-dark-700 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-dark-600">
                  <th className="px-4 py-2 text-left text-muted-foreground">Venue</th>
                  <th className="px-4 py-2 text-right text-muted-foreground">Allocation %</th>
                  <th className="px-4 py-2 text-right text-muted-foreground">Quantity</th>
                  <th className="px-4 py-2 text-right text-muted-foreground">Liquidity Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-600">
                {venues.map((v: any, i: number) => (
                  <tr key={i} className="hover:bg-dark-600/50">
                    <td className="px-4 py-2 text-white font-medium">{v.venue}</td>
                    <td className="px-4 py-2 text-right text-white">{(v.allocation_pct || 0).toFixed(1)}%</td>
                    <td className="px-4 py-2 text-right text-white">{(v.quantity || 0).toLocaleString()}</td>
                    <td className="px-4 py-2 text-right text-white">{(v.liquidity_score || 0).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    )
  }

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
            {['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground">Qty:</label>
          <input
            type="number"
            value={quantity}
            onChange={e => setQuantity(Number(e.target.value))}
            className="bg-dark-700 border border-dark-500 text-white rounded-lg px-3 py-1.5 text-sm w-24"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground">Side:</label>
          <select
            value={side}
            onChange={e => setSide(e.target.value)}
            className="bg-dark-700 border border-dark-500 text-white rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="buy">Buy</option>
            <option value="sell">Sell</option>
          </select>
        </div>
        <button
          onClick={runAlgorithm}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-1.5 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
        >
          <Zap className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Running...' : 'Run Algorithm'}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-400/10 border border-red-400/20 rounded-lg text-red-400 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Algorithm Tabs */}
      <div className="bg-dark-800 border border-dark-600 rounded-xl overflow-hidden">
        <div className="flex border-b border-dark-600">
          {algoTabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveAlgo(tab.key)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                activeAlgo === tab.key
                  ? 'text-white border-b-2 border-green-500 bg-dark-700'
                  : 'text-muted-foreground hover:text-white'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
        <div className="p-4">
          {loading ? (
            <div className="text-center py-8 text-muted-foreground text-sm">Running execution algorithm...</div>
          ) : (
            <>
              {activeAlgo === 'vwap' && renderVWAP()}
              {activeAlgo === 'twap' && renderTWAP()}
              {activeAlgo === 'impact' && renderImpact()}
              {activeAlgo === 'sor' && renderSOR()}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
