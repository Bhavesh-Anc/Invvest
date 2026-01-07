'use client'

import React, { useState, useEffect } from 'react'
import {
  Plus, Trash2, TrendingUp, TrendingDown, Activity,
  Target, Shield, Calendar, DollarSign, AlertCircle,
  Layers, Copy, Save, BarChart3
} from 'lucide-react'
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine
} from 'recharts'
import MetricCard from '@/components/ui/MetricCard'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import api from '@/lib/api'
import Loading from '@/components/ui/Loading'
import ErrorDisplay from '@/components/ui/ErrorDisplay'

interface StrategyLeg {
  id: string
  type: 'CE' | 'PE'
  action: 'BUY' | 'SELL'
  strike: number
  quantity: number
  premium: number
  expiry: string
}

export default function StrategyBuilderPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [legs, setLegs] = useState<StrategyLeg[]>([])
  const [templates, setTemplates] = useState<any[]>([])
  const [payoffData, setPayoffData] = useState<any[]>([])
  const [expiryCalendar, setExpiryCalendar] = useState<any[]>([])
  const [greeksOptimization, setGreeksOptimization] = useState<any>(null)

  useEffect(() => {
    fetchStrategyData()
  }, [])

  const fetchStrategyData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch all strategy data in parallel
      const [templatesData, payoff, calendar, greeksOpt] = await Promise.all([
        api.strategy.getTemplates(),
        api.strategy.getPayoffDiagram('bull-call-spread'),
        api.strategy.getExpiryCalendar(),
        api.strategy.getGreeksOptimization(),
      ])

      setTemplates(templatesData)
      setPayoffData(payoff)
      setExpiryCalendar(calendar)
      setGreeksOptimization(greeksOpt)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch strategy data'))
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <Loading message="Loading strategy builder..." />
  if (error) return <ErrorDisplay error={error} onRetry={fetchStrategyData} />
  if (!templates || templates.length === 0) return null

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Strategy Builder</h1>
          <p className="text-muted-foreground">Design & analyze multi-leg options strategies</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors">
            <Copy className="w-4 h-4 inline mr-2" />
            Load Saved
          </button>
          <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors">
            <Save className="w-4 h-4 inline mr-2" />
            Save Strategy
          </button>
        </div>
      </div>

      {/* Strategy Templates */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Layers className="w-5 h-5 text-purple-500" />
          Strategy Templates
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map(template => (
            <div
              key={template.id}
              className={`p-4 rounded-lg border cursor-pointer transition-all ${
                selectedTemplate === template.id
                  ? 'bg-purple-500/10 border-purple-500'
                  : 'bg-dark-700/30 border-dark-600 hover:border-purple-500/50'
              }`}
              onClick={() => loadTemplate(template)}
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-sm font-bold text-white">{template.name}</h3>
                <span
                  className={`text-xs px-2 py-1 rounded ${
                    template.sentiment === 'Bullish'
                      ? 'bg-success/10 text-success'
                      : template.sentiment === 'Bearish'
                      ? 'bg-danger/10 text-danger'
                      : 'bg-warning/10 text-warning'
                  }`}
                >
                  {template.sentiment}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mb-3">{template.description}</p>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Max Profit:</span>
                  <span className="text-success font-medium">
                    {template.maxProfit === Infinity ? '∞' : formatCurrency(template.maxProfit)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Max Loss:</span>
                  <span className="text-danger font-medium">
                    {template.maxLoss === Infinity ? '∞' : formatCurrency(template.maxLoss)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Margin:</span>
                  <span className="text-white font-medium">{formatCurrency(template.marginRequired)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Strategy Legs Builder */}
      <div className="card-glass rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-500" />
            Strategy Legs
          </h2>
          <button
            onClick={addLeg}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4 inline mr-2" />
            Add Leg
          </button>
        </div>

        {legs.length === 0 ? (
          <div className="text-center py-12">
            <Layers className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">No legs added. Select a template or add a custom leg.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {legs.map((leg, index) => (
              <div key={leg.id} className="p-4 bg-dark-700/30 rounded-lg">
                <div className="flex items-center gap-4">
                  <div className="flex items-center justify-center w-8 h-8 bg-purple-500/20 rounded-full">
                    <span className="text-sm font-bold text-purple-400">{index + 1}</span>
                  </div>

                  <div className="flex-1 grid grid-cols-6 gap-3">
                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">Action</label>
                      <select
                        value={leg.action}
                        onChange={(e) => updateLeg(leg.id, 'action', e.target.value)}
                        className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="BUY">BUY</option>
                        <option value="SELL">SELL</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">Type</label>
                      <select
                        value={leg.type}
                        onChange={(e) => updateLeg(leg.id, 'type', e.target.value)}
                        className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="CE">CE (Call)</option>
                        <option value="PE">PE (Put)</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">Strike</label>
                      <input
                        type="number"
                        value={leg.strike}
                        onChange={(e) => updateLeg(leg.id, 'strike', parseFloat(e.target.value))}
                        className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>

                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">Quantity</label>
                      <input
                        type="number"
                        value={leg.quantity}
                        onChange={(e) => updateLeg(leg.id, 'quantity', parseInt(e.target.value))}
                        className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>

                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">Premium</label>
                      <input
                        type="number"
                        step="0.05"
                        value={leg.premium}
                        onChange={(e) => updateLeg(leg.id, 'premium', parseFloat(e.target.value))}
                        className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>

                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">Expiry</label>
                      <select
                        value={leg.expiry}
                        onChange={(e) => updateLeg(leg.id, 'expiry', e.target.value)}
                        className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="25-JAN-2024">25-JAN-2024</option>
                        <option value="31-JAN-2024">31-JAN-2024</option>
                        <option value="29-FEB-2024">29-FEB-2024</option>
                      </select>
                    </div>
                  </div>

                  <button
                    onClick={() => removeLeg(leg.id)}
                    className="p-2 text-danger hover:bg-danger/10 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="mt-3 pt-3 border-t border-dark-600 flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">
                    Total: {leg.action} {leg.quantity} x {leg.type} {leg.strike}
                  </span>
                  <span className={`font-bold ${leg.action === 'BUY' ? 'text-danger' : 'text-success'}`}>
                    {leg.action === 'BUY' ? '-' : '+'}
                    {formatCurrency(leg.premium * leg.quantity)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Strategy Metrics & Payoff */}
      {legs.length > 0 && (
        <>
          {/* Strategy Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Total Cost"
              value={formatCurrency(metrics.totalCost)}
              icon={<TrendingDown className="w-5 h-5" />}
              subtitle="Premiums paid"
              trend="down"
            />
            <MetricCard
              title="Total Credit"
              value={formatCurrency(metrics.totalCredit)}
              icon={<TrendingUp className="w-5 h-5" />}
              subtitle="Premiums received"
              trend="up"
            />
            <MetricCard
              title="Net Debit/Credit"
              value={formatCurrency(Math.abs(metrics.netDebit))}
              icon={<DollarSign className="w-5 h-5" />}
              subtitle={metrics.netDebit > 0 ? 'Net Debit' : 'Net Credit'}
              trend={metrics.netDebit > 0 ? 'down' : 'up'}
            />
            <MetricCard
              title="Margin Required"
              value={formatCurrency(metrics.margin)}
              icon={<Shield className="w-5 h-5" />}
              subtitle="Estimated margin"
            />
          </div>

          {/* Payoff Diagram */}
          <div className="card-glass rounded-xl p-6">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-purple-500" />
              Payoff Diagram
            </h2>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={payoffData}>
                <defs>
                  <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorLoss" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.3} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
                <XAxis dataKey="price" stroke="#888" label={{ value: 'Underlying Price', position: 'insideBottom', offset: -5, fill: '#888' }} />
                <YAxis stroke="#888" label={{ value: 'P&L (₹K)', angle: -90, position: 'insideLeft', fill: '#888' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f1429',
                    border: '1px solid #1f2740',
                    borderRadius: '8px',
                  }}
                  formatter={(value: any) => `₹${value}K`}
                />
                <ReferenceLine y={0} stroke="#888" strokeDasharray="3 3" />
                <ReferenceLine x={21894} stroke="#8b5cf6" strokeDasharray="3 3" label={{ value: 'Current', fill: '#8b5cf6' }} />
                <Area
                  type="monotone"
                  dataKey="pnl"
                  stroke="#10b981"
                  strokeWidth={2}
                  fill="url(#colorProfit)"
                />
              </AreaChart>
            </ResponsiveContainer>
            <div className="mt-4 grid grid-cols-3 gap-4">
              <div className="p-3 bg-dark-700/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Max Profit</div>
                <div className="text-xl font-bold text-success">₹112.5K</div>
                <div className="text-xs text-muted-foreground">at 22000+</div>
              </div>
              <div className="p-3 bg-dark-700/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Max Loss</div>
                <div className="text-xl font-bold text-danger">₹87.5K</div>
                <div className="text-xs text-muted-foreground">at 21800-</div>
              </div>
              <div className="p-3 bg-dark-700/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Breakeven</div>
                <div className="text-xl font-bold text-warning">21,887.5</div>
                <div className="text-xs text-muted-foreground">+87.5 pts</div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Greeks Neutral Optimization & Expiry Calendar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Greeks Neutral Optimization */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-purple-500" />
            Greeks Neutral Optimization
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-muted-foreground mb-2">Current Delta</div>
                <div className="text-2xl font-bold text-white">{greeksOptimization.currentDelta}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-2">Target Delta</div>
                <div className="text-2xl font-bold text-success">{greeksOptimization.targetDelta}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-2">Current Gamma</div>
                <div className="text-2xl font-bold text-white">{greeksOptimization.currentGamma}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-2">Target Gamma</div>
                <div className="text-2xl font-bold text-success">{greeksOptimization.targetGamma}</div>
              </div>
            </div>
            <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-purple-400 mt-0.5" />
                <div>
                  <div className="text-sm font-medium text-white mb-1">Suggested Adjustment</div>
                  <div className="text-sm text-purple-200">{greeksOptimization.suggestedAdjustment}</div>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-muted-foreground mb-2">Current Theta</div>
                <div className="text-xl font-bold text-danger">{greeksOptimization.currentTheta}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-2">Current Vega</div>
                <div className="text-xl font-bold text-white">{greeksOptimization.currentVega}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Expiry Calendar */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-purple-500" />
            NSE Expiry Calendar
          </h2>
          <div className="space-y-3">
            {expiryCalendar.map((expiry, index) => (
              <div key={index} className="p-4 bg-dark-700/30 rounded-lg hover:bg-dark-700/50 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <div className="text-sm font-bold text-white">{expiry.date}</div>
                    <div className="text-xs text-muted-foreground">{expiry.instruments.join(', ')}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        expiry.type === 'Weekly'
                          ? 'bg-purple-500/10 text-purple-400'
                          : 'bg-warning/10 text-warning'
                      }`}
                    >
                      {expiry.type}
                    </span>
                    <span className="text-sm font-bold text-white">{expiry.daysLeft} days</span>
                  </div>
                </div>
                <div className="w-full h-1 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-purple-700"
                    style={{ width: `${Math.max(10, 100 - (expiry.daysLeft / 40) * 100)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
