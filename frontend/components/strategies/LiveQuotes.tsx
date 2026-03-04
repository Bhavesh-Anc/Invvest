'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  Activity, TrendingUp, TrendingDown, Zap,
  RefreshCw, AlertCircle, Wifi, WifiOff, Package,
  DollarSign, BarChart3
} from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine
} from 'recharts'
import MetricCard from '@/components/ui/MetricCard'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { api } from '@/lib/api'

interface Quote {
  symbol: string
  bid: number
  ask: number
  bid_size: number
  ask_size: number
  spread: number
  mid: number
  timestamp?: string
}

interface InventoryData {
  symbol: string
  current_position: number
  target_position: number
  max_position: number
  inventory_ratio: number
  pnl: number
}

export default function LiveQuotes() {
  const [symbol, setSymbol] = useState('NIFTY')
  const [wsConnected, setWsConnected] = useState(false)
  const [quote, setQuote] = useState<Quote | null>(null)
  const [quoteHistory, setQuoteHistory] = useState<any[]>([])
  const [inventory, setInventory] = useState<InventoryData | null>(null)
  const [mmPnl, setMmPnl] = useState<any>(null)
  const [mmStats, setMmStats] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const symbols = ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY']

  const connectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    try {
      const ws = api.marketMaking.connectQuoteStream(symbol)
      wsRef.current = ws

      ws.onopen = () => {
        setWsConnected(true)
        setError(null)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.bid && data.ask) {
            setQuote(data)
            setQuoteHistory(prev => {
              const newEntry = {
                time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                bid: data.bid,
                ask: data.ask,
                spread: data.spread || (data.ask - data.bid),
                mid: data.mid || (data.bid + data.ask) / 2,
              }
              return [...prev.slice(-30), newEntry]
            })
          }
        } catch (_) {}
      }

      ws.onerror = () => {
        setWsConnected(false)
        setError('WebSocket connection failed. Using REST fallback.')
        fetchQuoteREST()
      }

      ws.onclose = () => {
        setWsConnected(false)
      }
    } catch (err) {
      setError('Could not establish WebSocket. Using REST fallback.')
      fetchQuoteREST()
    }
  }, [symbol])

  const fetchQuoteREST = async () => {
    setLoading(true)
    try {
      const q = await api.marketMaking.generateQuotes(symbol, 20000, 0.15, 0.05)
      setQuote(q)
    } catch (err) {
      setError('Failed to fetch quotes. Ensure backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const fetchSupportingData = async () => {
    try {
      const [inv, pnl, stats] = await Promise.all([
        api.marketMaking.getInventoryStatus(symbol),
        api.marketMaking.getPnLSummary(symbol),
        api.marketMaking.getMMStats(symbol),
      ])
      setInventory(inv)
      setMmPnl(pnl)
      setMmStats(stats)
    } catch (_) {}
  }

  useEffect(() => {
    connectWebSocket()
    fetchSupportingData()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [symbol])

  const spread = quote ? (quote.spread ?? (quote.ask - quote.bid)) : 0
  const spreadBps = quote && quote.mid > 0 ? (spread / quote.mid) * 10000 : 0
  const inventoryRatio = inventory?.inventory_ratio ?? 0

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
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
          wsConnected
            ? 'bg-green-400/10 text-green-400 border border-green-400/20'
            : 'bg-gray-400/10 text-gray-400 border border-gray-400/20'
        }`}>
          {wsConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
          {wsConnected ? 'Live Stream' : 'Disconnected'}
        </div>
        <button
          onClick={() => { connectWebSocket(); fetchSupportingData() }}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Reconnect
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-yellow-400/10 border border-yellow-400/20 rounded-lg text-yellow-400 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Live Bid/Ask Display */}
      <div className="bg-dark-800 border border-dark-600 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            <h3 className="text-white font-semibold">Live Market Making Quotes — {symbol}</h3>
          </div>
          {wsConnected && (
            <span className="flex items-center gap-1 text-xs text-green-400">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              Real-time
            </span>
          )}
        </div>

        {quote ? (
          <div className="grid grid-cols-3 gap-6">
            <div className="text-center p-4 bg-green-400/5 border border-green-400/20 rounded-xl">
              <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Bid</div>
              <div className="text-3xl font-bold text-green-400">{formatCurrency(quote.bid)}</div>
              <div className="text-sm text-muted-foreground mt-1">Size: {(quote.bid_size || 0).toLocaleString()}</div>
            </div>
            <div className="text-center p-4 bg-dark-700 border border-dark-500 rounded-xl">
              <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Spread</div>
              <div className="text-3xl font-bold text-white">{formatCurrency(spread)}</div>
              <div className="text-sm text-muted-foreground mt-1">{spreadBps.toFixed(1)} bps</div>
            </div>
            <div className="text-center p-4 bg-red-400/5 border border-red-400/20 rounded-xl">
              <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Ask</div>
              <div className="text-3xl font-bold text-red-400">{formatCurrency(quote.ask)}</div>
              <div className="text-sm text-muted-foreground mt-1">Size: {(quote.ask_size || 0).toLocaleString()}</div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground text-sm">
            {loading ? 'Fetching quotes...' : 'Connecting to quote stream...'}
          </div>
        )}
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Inventory Ratio"
          value={`${(Math.abs(inventoryRatio) * 100).toFixed(1)}%`}
          subtitle={inventoryRatio > 0 ? 'Long skew' : inventoryRatio < 0 ? 'Short skew' : 'Neutral'}
          icon={<Package className="w-5 h-5" />}
          color={Math.abs(inventoryRatio) > 0.7 ? 'red' : Math.abs(inventoryRatio) > 0.4 ? 'yellow' : 'green'}
        />
        <MetricCard
          title="Realized P&L"
          value={mmPnl?.realized_pnl != null ? formatCurrency(mmPnl.realized_pnl) : '—'}
          subtitle="Market making"
          icon={<DollarSign className="w-5 h-5" />}
          color={mmPnl?.realized_pnl >= 0 ? 'green' : 'red'}
        />
        <MetricCard
          title="Total Trades"
          value={mmStats?.total_trades != null ? mmStats.total_trades.toString() : '—'}
          subtitle="Today"
          icon={<Activity className="w-5 h-5" />}
          color="blue"
        />
        <MetricCard
          title="Fill Rate"
          value={mmStats?.fill_rate != null ? formatPercentage(mmStats.fill_rate) : '—'}
          subtitle="Quote fill"
          icon={<BarChart3 className="w-5 h-5" />}
          color="purple"
        />
      </div>

      {/* Quote History Chart */}
      {quoteHistory.length > 2 && (
        <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
          <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-400" />
            Bid/Ask History
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={quoteHistory} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
              <YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }}
                formatter={(val: any) => [formatCurrency(val), '']}
              />
              <Line dataKey="bid" stroke="#10B981" dot={false} strokeWidth={1.5} name="Bid" />
              <Line dataKey="ask" stroke="#EF4444" dot={false} strokeWidth={1.5} name="Ask" />
              <Line dataKey="mid" stroke="#F59E0B" dot={false} strokeWidth={1} strokeDasharray="4 2" name="Mid" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Inventory Position Bar */}
      {inventory && (
        <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
          <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
            <Package className="w-4 h-4 text-orange-400" />
            Inventory Position
          </h3>
          <div className="flex items-center gap-4 text-sm mb-2">
            <span className="text-muted-foreground">Current: <span className="text-white">{inventory.current_position.toLocaleString()}</span></span>
            <span className="text-muted-foreground">Target: <span className="text-white">{inventory.target_position.toLocaleString()}</span></span>
            <span className="text-muted-foreground">Max: <span className="text-white">{inventory.max_position.toLocaleString()}</span></span>
          </div>
          <div className="relative h-3 bg-dark-600 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                Math.abs(inventoryRatio) > 0.7 ? 'bg-red-500'
                  : Math.abs(inventoryRatio) > 0.4 ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(Math.abs(inventoryRatio) * 100, 100)}%` }}
            />
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            Inventory utilization: {(Math.abs(inventoryRatio) * 100).toFixed(1)}%
          </div>
        </div>
      )}
    </div>
  )
}
