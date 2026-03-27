'use client'

import { useEffect, useState } from 'react'
import { Brain, TrendingUp, Zap } from 'lucide-react'
import { formatPercentage } from '@/lib/utils'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import api from '@/lib/api'
import Loading from '@/components/ui/Loading'
import ErrorDisplay from '@/components/ui/ErrorDisplay'

export default function AIModelsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [models, setModels] = useState<any[]>([])
  const [regimeData, setRegimeData] = useState<any[]>([])
  const [featureImportance, setFeatureImportance] = useState<any[]>([])
  const [sentimentData, setSentimentData] = useState<any[]>([])
  const [sentimentSummary, setSentimentSummary] = useState<any>(null)
  const [modelPerformance, setModelPerformance] = useState<any[]>([])
  const [mlPipeline, setMlPipeline] = useState<any>(null)

  useEffect(() => {
    fetchAIData()
  }, [])

  const fetchAIData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch all AI model data in parallel
      const [leaderboard, regime, features, sentiment, sentSummary, performance, pipeline] = await Promise.all([
        api.models.getModelLeaderboard(),
        api.models.getRegimeDetection(60),
        api.models.getFeatureImportance('XGBoost'),
        api.models.getSentimentAnalysis(7),
        api.models.getSentimentSummary(),
        api.models.getModelPerformance(),
        api.models.getMLPipeline(),
      ])

      setModels(leaderboard)
      setRegimeData(regime)
      setFeatureImportance(features)
      setSentimentData(sentiment)
      setSentimentSummary(sentSummary)
      setModelPerformance(performance)
      setMlPipeline(pipeline)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch AI model data'))
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <Loading message="Loading AI models data..." />
  if (error) return <ErrorDisplay error={error} onRetry={fetchAIData} />
  if (!models || models.length === 0) return null
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">AI & Machine Learning Insights</h1>
          <p className="text-sm text-muted-foreground">Advanced predictive models and analytics</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-purple-600/20 border border-purple-600/30 rounded-lg">
          <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></div>
          <span className="text-sm font-medium text-purple-500">AI Engine: Active</span>
        </div>
      </div>

      {/* Model Leaderboard */}
      <div className="card-glass rounded-xl p-6">
        <div className="flex items-center gap-2 mb-6">
          <Brain className="w-5 h-5 text-purple-500" />
          <h2 className="text-lg font-semibold text-white">Model Leaderboard</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-600">
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Model</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Accuracy</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Sharpe</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Trades</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Status</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Action</th>
              </tr>
            </thead>
            <tbody>
              {models.map((model, index) => (
                <tr key={index} className="border-b border-dark-700/50 hover:bg-dark-700/30 transition-colors">
                  <td className="py-3 px-4 text-sm font-medium text-white">{model.name}</td>
                  <td className={`py-3 px-4 text-right text-sm font-medium ${
                    model.accuracy > 65 ? 'text-success' : model.accuracy > 60 ? 'text-warning' : 'text-muted-foreground'
                  }`}>
                    {model.accuracy}%
                  </td>
                  <td className="py-3 px-4 text-right text-sm font-medium text-blue-500">{model.sharpe}</td>
                  <td className="py-3 px-4 text-right text-sm text-white">{model.trades}</td>
                  <td className="py-3 px-4 text-center">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${
                      model.status === 'deployed' ? 'bg-success/20 text-success' :
                      model.status === 'testing' ? 'bg-blue-500/20 text-blue-500' :
                      'bg-muted/20 text-muted-foreground'
                    }`}>
                      {model.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button className="px-3 py-1 bg-purple-600 text-white text-xs font-medium rounded hover:bg-purple-700 transition-colors">
                      Deploy
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Regime Detection */}
        <div className="card-glass rounded-xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <Zap className="w-5 h-5 text-blue-500" />
            <h2 className="text-lg font-semibold text-white">Regime Detection</h2>
          </div>

          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={regimeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis dataKey="date" stroke="#6b7280" fontSize={12} />
              <YAxis stroke="#6b7280" fontSize={12} domain={[0, 4]} ticks={[0, 1, 2, 3, 4]} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a2038', border: '1px solid #1f2740', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Line type="stepAfter" dataKey="regime" stroke="#3b82f6" strokeWidth={3} dot={{ fill: '#3b82f6', r: 6 }} />
            </LineChart>
          </ResponsiveContainer>

          <div className="grid grid-cols-3 gap-2 mt-4">
            <div className="px-3 py-2 bg-danger/20 border border-danger/30 rounded-lg text-center">
              <p className="text-xs text-danger font-medium">1 - Bear</p>
            </div>
            <div className="px-3 py-2 bg-warning/20 border border-warning/30 rounded-lg text-center">
              <p className="text-xs text-warning font-medium">2 - Sideways</p>
            </div>
            <div className="px-3 py-2 bg-success/20 border border-success/30 rounded-lg text-center">
              <p className="text-xs text-success font-medium">3 - Bull</p>
            </div>
          </div>
        </div>

        {/* Feature Importance */}
        <div className="card-glass rounded-xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <Zap className="w-5 h-5 text-warning" />
            <h2 className="text-lg font-semibold text-white">Feature Importance (XGBoost)</h2>
          </div>

          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={featureImportance} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
              <XAxis type="number" stroke="#6b7280" fontSize={12} domain={[0, 0.25]} />
              <YAxis dataKey="feature" type="category" stroke="#6b7280" fontSize={12} width={100} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a2038', border: '1px solid #1f2740', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Bar dataKey="importance" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Sentiment Analysis */}
      <div className="card-glass rounded-xl p-6">
        <div className="flex items-center gap-2 mb-6">
          <TrendingUp className="w-5 h-5 text-success" />
          <h2 className="text-lg font-semibold text-white">Sentiment Analysis (Indian Financial News)</h2>
        </div>

        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={sentimentData}>
            <defs>
              <linearGradient id="colorSentiment" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2740" />
            <XAxis dataKey="date" stroke="#6b7280" fontSize={12} />
            <YAxis stroke="#6b7280" fontSize={12} domain={[0, 100]} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1a2038', border: '1px solid #1f2740', borderRadius: '8px' }}
              labelStyle={{ color: '#9ca3af' }}
            />
            <Line type="monotone" dataKey="score" stroke="#10b981" strokeWidth={2} fill="url(#colorSentiment)" />
          </LineChart>
        </ResponsiveContainer>

        {sentimentSummary && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-dark-700/30 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Current Sentiment</p>
              <h3 className={`text-2xl font-bold ${sentimentSummary.currentScore >= 70 ? 'text-success' : sentimentSummary.currentScore >= 50 ? 'text-warning' : 'text-danger'}`}>
                {sentimentSummary.currentScore || 0}/100
              </h3>
              <p className="text-xs text-muted-foreground">{sentimentSummary.sentiment || 'Neutral'}</p>
            </div>

            <div className="p-4 bg-dark-700/30 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">News Sources</p>
              <h3 className="text-2xl font-bold text-white">{sentimentSummary.articlesAnalyzed?.toLocaleString() || 0}</h3>
              <p className="text-xs text-muted-foreground">Articles analyzed today</p>
            </div>

            <div className="p-4 bg-dark-700/30 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Sentiment Accuracy</p>
              <h3 className="text-2xl font-bold text-purple-500">{sentimentSummary.accuracy || 0}%</h3>
              <p className="text-xs text-muted-foreground">Backtested correlation</p>
            </div>
          </div>
        )}
      </div>

      {/* Model Performance Comparison */}
      {modelPerformance && modelPerformance.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {modelPerformance.slice(0, 3).map((model: any, index: number) => (
            <div key={index} className="card-glass rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-white">{model.name}</h3>
                <span className={`px-2 py-1 text-xs font-medium rounded ${
                  model.status === 'deployed' || model.status === 'Active' ? 'bg-success/20 text-success' :
                  model.status === 'testing' || model.status === 'Testing' ? 'bg-blue-500/20 text-blue-500' :
                  'bg-muted/20 text-muted-foreground'
                }`}>
                  {model.status}
                </span>
              </div>

              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs text-muted-foreground">Accuracy</span>
                    <span className={`text-xs font-medium ${model.accuracy > 65 ? 'text-success' : model.accuracy > 60 ? 'text-warning' : 'text-muted-foreground'}`}>
                      {model.accuracy}%
                    </span>
                  </div>
                  <div className="w-full bg-dark-700 rounded-full h-2">
                    <div className="bg-gradient-to-r from-success to-blue-500 h-2 rounded-full" style={{ width: `${model.accuracy}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs text-muted-foreground">Sharpe Ratio</span>
                    <span className="text-xs font-medium text-blue-500">{model.sharpe}</span>
                  </div>
                  <div className="w-full bg-dark-700 rounded-full h-2">
                    <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full" style={{ width: `${Math.min(100, (model.sharpe / 2.5) * 100)}%` }}></div>
                  </div>
                </div>

                <div className="pt-2 border-t border-dark-700">
                  <p className="text-xs text-muted-foreground">{model.bestFor || 'General purpose'}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ML Pipeline Info */}
      {mlPipeline && (
        <div className="card-glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">ML Pipeline Status</h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {mlPipeline.stages && mlPipeline.stages.map((stage: any, index: number) => {
              const borderColors = ['border-purple-500', 'border-blue-500', 'border-warning', 'border-success']
              const statusColors = {
                Active: 'success',
                Scheduled: 'warning',
                Idle: 'muted-foreground'
              }
              const statusColor = statusColors[stage.status as keyof typeof statusColors] || 'success'

              return (
                <div key={index} className={`p-4 bg-dark-700/30 rounded-lg border-l-4 ${borderColors[index % 4]}`}>
                  <p className="text-xs text-muted-foreground mb-1">{stage.name}</p>
                  <p className="text-sm font-medium text-white">{stage.description}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <div className={`w-2 h-2 rounded-full bg-${statusColor} ${stage.status === 'Active' || stage.status === 'Scheduled' ? 'animate-pulse' : ''}`}></div>
                    <span className={`text-xs text-${statusColor}`}>{stage.status}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
