'use client'

import React, { useState } from 'react'
import { Activity, Package, DollarSign, BarChart3 } from 'lucide-react'
import LiveQuotes from '@/components/strategies/LiveQuotes'
import { api } from '@/lib/api'

type MMTab = 'live_quotes' | 'flow_analysis' | 'spread_opt'

export default function MarketMakingPage() {
  const [activeTab, setActiveTab] = useState<MMTab>('live_quotes')
  const [flowSymbol, setFlowSymbol] = useState('NIFTY')
  const [flowData, setFlowData] = useState<any>(null)
  const [spreadData, setSpreadData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const fetchFlowAnalysis = async () => {
    setLoading(true)
    try {
      const data = await api.marketMaking.analyzeOrderFlow(flowSymbol, 100)
      setFlowData(data)
    } catch (_) {}
    setLoading(false)
  }

  const fetchSpreadOptimization = async () => {
    setLoading(true)
    try {
      const data = await api.marketMaking.optimizeSpread(flowSymbol, 0.15, 0)
      setSpreadData(data)
    } catch (_) {}
    setLoading(false)
  }

  const tabs: { key: MMTab; label: string; icon: React.ReactNode }[] = [
    { key: 'live_quotes', label: 'Live Quotes', icon: <Activity className="w-4 h-4" /> },
    { key: 'flow_analysis', label: 'Order Flow', icon: <BarChart3 className="w-4 h-4" /> },
    { key: 'spread_opt', label: 'Spread Optimizer', icon: <DollarSign className="w-4 h-4" /> },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Market Making</h1>
        <p className="text-muted-foreground">Institutional market making with two-sided quoting, inventory management, and adverse selection detection</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-dark-600">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-yellow-500 text-white'
                : 'border-transparent text-muted-foreground hover:text-white'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'live_quotes' && <LiveQuotes />}

      {activeTab === 'flow_analysis' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <select
              value={flowSymbol}
              onChange={e => setFlowSymbol(e.target.value)}
              className="bg-dark-700 border border-dark-500 text-white rounded-lg px-3 py-1.5 text-sm"
            >
              {['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY'].map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <button
              onClick={fetchFlowAnalysis}
              disabled={loading}
              className="px-4 py-1.5 bg-yellow-600 hover:bg-yellow-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              {loading ? 'Analyzing...' : 'Analyze Flow'}
            </button>
          </div>
          {flowData ? (
            <div className="bg-dark-800 border border-dark-600 rounded-xl p-4 space-y-3">
              <h3 className="text-white font-medium">Order Flow Analysis — {flowSymbol}</h3>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Buy Volume</span>
                  <p className="text-white font-semibold mt-1">{flowData.buy_volume?.toLocaleString() ?? '—'}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Sell Volume</span>
                  <p className="text-white font-semibold mt-1">{flowData.sell_volume?.toLocaleString() ?? '—'}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Imbalance</span>
                  <p className={`font-semibold mt-1 ${(flowData.imbalance ?? 0) > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {flowData.imbalance != null ? `${(flowData.imbalance * 100).toFixed(1)}%` : '—'}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Adverse Selection Risk</span>
                  <p className={`font-semibold mt-1 ${(flowData.adverse_selection_risk ?? 0) > 0.5 ? 'text-red-400' : 'text-green-400'}`}>
                    {flowData.adverse_selection_risk != null ? `${(flowData.adverse_selection_risk * 100).toFixed(0)}%` : '—'}
                  </p>
                </div>
              </div>
              {flowData.recommendation && (
                <div className="p-3 bg-dark-700 rounded-lg text-sm text-muted-foreground">
                  {flowData.recommendation}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground text-sm">
              Click "Analyze Flow" to run order flow analysis.
            </div>
          )}
        </div>
      )}

      {activeTab === 'spread_opt' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <select
              value={flowSymbol}
              onChange={e => setFlowSymbol(e.target.value)}
              className="bg-dark-700 border border-dark-500 text-white rounded-lg px-3 py-1.5 text-sm"
            >
              {['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY'].map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <button
              onClick={fetchSpreadOptimization}
              disabled={loading}
              className="px-4 py-1.5 bg-yellow-600 hover:bg-yellow-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              {loading ? 'Optimizing...' : 'Optimize Spread'}
            </button>
          </div>
          {spreadData ? (
            <div className="bg-dark-800 border border-dark-600 rounded-xl p-4 space-y-3">
              <h3 className="text-white font-medium">Optimal Spread — {flowSymbol}</h3>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Optimal Spread</span>
                  <p className="text-white font-semibold mt-1">
                    {spreadData.optimal_spread != null ? `${(spreadData.optimal_spread * 100).toFixed(3)}%` : '—'}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Half Spread</span>
                  <p className="text-white font-semibold mt-1">
                    {spreadData.half_spread != null ? `${(spreadData.half_spread * 100).toFixed(3)}%` : '—'}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Expected P&L</span>
                  <p className={`font-semibold mt-1 ${(spreadData.expected_pnl ?? 0) > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {spreadData.expected_pnl != null ? `₹${spreadData.expected_pnl.toFixed(2)}` : '—'}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground text-sm">
              Click "Optimize Spread" to compute the optimal bid-ask spread.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
