'use client'

import { useEffect, useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { AreaChart, Area, LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import api from '@/lib/api'
import Loading from '@/components/ui/Loading'
import ErrorDisplay from '@/components/ui/ErrorDisplay'

export default function RiskManagementPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [riskMetrics, setRiskMetrics] = useState<any>(null)
  const [varHistoryData, setVarHistoryData] = useState<any[]>([])
  const [drawdownData, setDrawdownData] = useState<any[]>([])
  const [stressTests, setStressTests] = useState<any[]>([])
  const [positions, setPositions] = useState<any[]>([])
  const [circuitBreakers, setCircuitBreakers] = useState<any[]>([])
  const [kellyCriterion, setKellyCriterion] = useState<any>(null)

  useEffect(() => {
    fetchRiskData()
  }, [])

  const fetchRiskData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch all risk data in parallel
      const [metrics, varHistory, drawdown, stress, positionRisk, breakers, kelly] = await Promise.all([
        api.risk.getMetrics(),
        api.risk.getVaRHistory(30),
        api.risk.getDrawdownAnalysis(180),
        api.risk.getStressTests(),
        api.risk.getPositionRisk(),
        api.risk.getCircuitBreakers(),
        api.risk.getKellyCriterion(),
      ])

      setRiskMetrics(metrics)
      setVarHistoryData(varHistory)
      setDrawdownData(drawdown)
      setStressTests(stress)
      setPositions(positionRisk)
      setCircuitBreakers(breakers)
      setKellyCriterion(kelly)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch risk data'))
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <Loading message="Loading risk management data..." />
  if (error) return <ErrorDisplay error={error} onRetry={fetchRiskData} />
  if (!riskMetrics) return null
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Risk Management</h1>
          <p className="text-sm text-muted-foreground">Portfolio risk analytics and stress testing</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-warning/20 border border-warning/30 rounded-lg">
          <span className="text-sm font-medium text-warning">Risk Score: {riskMetrics.riskScore || 'Medium'}</span>
        </div>
      </div>

      {/* Risk Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {riskMetrics.metrics && riskMetrics.metrics.map((metric: any, index: number) => (
          <div key={index} className="card-glass rounded-xl p-5">
            <div className="flex items-start justify-between mb-3">
              <p className="text-sm font-medium text-muted-foreground">{metric.label}</p>
              {metric.alert && (
                <div className="p-1.5 bg-danger/20 rounded-lg">
                  <AlertTriangle className="w-4 h-4 text-danger" />
                </div>
              )}
            </div>
            <h3 className="text-2xl font-bold text-white mb-1">{metric.value}</h3>
            <p className="text-xs text-muted-foreground">{metric.percent}</p>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* VaR History */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-6">Value at Risk (VaR)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={varHistoryData}>
              <defs>
                <linearGradient id="colorVar95" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorVar99" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis dataKey="date" stroke="#6b7280" fontSize={12} />
              <YAxis stroke="#6b7280" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a2038', border: '1px solid #1f2740', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Area type="monotone" dataKey="var95" stroke="#f59e0b" strokeWidth={2} fillOpacity={1} fill="url(#colorVar95)" />
              <Area type="monotone" dataKey="var99" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#colorVar99)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Drawdown Analysis */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-6">Drawdown Analysis</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={drawdownData}>
              <defs>
                <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis dataKey="date" stroke="#6b7280" fontSize={12} />
              <YAxis stroke="#6b7280" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a2038', border: '1px solid #1f2740', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Line type="monotone" dataKey="drawdown" stroke="#ef4444" strokeWidth={2} dot={{ fill: '#ef4444', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Stress Test Scenarios */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-6">Stress Test Scenarios (Indian Market)</h2>
        <div className="space-y-4">
          {stressTests.map((test, index) => (
            <div key={index} className="flex items-center justify-between p-4 bg-dark-700/30 rounded-lg hover:bg-dark-700/50 transition-colors">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-warning" />
                <div>
                  <h3 className="text-sm font-medium text-white">{test.name}</h3>
                  <p className="text-xs text-muted-foreground">Probability: {test.probability}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className={`text-sm font-bold ${test.impact < -10 ? 'text-danger' : 'text-warning'}`}>
                  {formatPercentage(test.impact)}
                </span>
                <div className="w-32 h-2 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${test.impact < -10 ? 'bg-danger' : 'bg-warning'}`}
                    style={{ width: `${Math.abs(test.impact) * 5}%` }}
                  ></div>
                </div>
                <span className="text-xs text-muted-foreground">Est. Impact</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Position-wise Risk */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-6">Position-wise Risk</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-dark-600">
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Position</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Exposure</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">VaR</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Margin</th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Status</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position, index) => (
                  <tr key={index} className="border-b border-dark-700/50 hover:bg-dark-700/30 transition-colors">
                    <td className="py-3 px-4 text-sm font-medium text-white">{position.symbol}</td>
                    <td className="py-3 px-4 text-right text-sm text-white">{formatCurrency(position.exposure)}</td>
                    <td className="py-3 px-4 text-right text-sm text-danger">{formatCurrency(position.var)}</td>
                    <td className="py-3 px-4 text-right text-sm text-warning">{formatCurrency(position.margin)}</td>
                    <td className="py-3 px-4 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        position.status === 'safe' ? 'bg-success/20 text-success' : 'bg-warning/20 text-warning'
                      }`}>
                        {position.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Circuit Breakers & Alerts */}
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-6">Circuit Breakers & Alerts</h2>
          <div className="space-y-4">
            {circuitBreakers.map((breaker, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-dark-700/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${breaker.status === 'safe' ? 'bg-success' : 'bg-warning'}`}></div>
                  <div>
                    <h3 className="text-sm font-medium text-white">{breaker.name}</h3>
                    <p className="text-xs text-muted-foreground">Threshold: {breaker.threshold}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`text-sm font-bold ${breaker.status === 'safe' ? 'text-success' : 'text-warning'}`}>
                    {breaker.status}
                  </span>
                  <p className="text-xs text-muted-foreground">Current: {breaker.current}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Kelly Criterion */}
          {kellyCriterion && (
            <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-white mb-1">Kelly Criterion Position Sizing</h3>
                  <p className="text-xs text-muted-foreground">
                    {kellyCriterion.description || `Suggested position size: ${kellyCriterion.suggestedSize || 'N/A'} per trade based on win rate (${kellyCriterion.winRate || 'N/A'}) and risk-reward (${kellyCriterion.riskReward || 'N/A'})`}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
