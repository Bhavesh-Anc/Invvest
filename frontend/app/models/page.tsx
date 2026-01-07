'use client'

import { Brain, TrendingUp, Zap } from 'lucide-react'
import { formatPercentage } from '@/lib/utils'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

// Mock data
const models = [
  { name: 'LSTM-Attention', accuracy: 68.4, sharpe: 2.14, trades: 234, status: 'deployed' },
  { name: 'Transformer', accuracy: 71.2, sharpe: 2.42, trades: 189, status: 'deployed' },
  { name: 'XGBoost Ensemble', accuracy: 64.8, sharpe: 1.86, trades: 312, status: 'testing' },
  { name: 'Random Forest', accuracy: 59.2, sharpe: 1.52, trades: 278, status: 'archived' },
  { name: 'GRU Network', accuracy: 66.7, sharpe: 1.98, trades: 256, status: 'testing' },
]

const regimeData = [
  { date: 'Dec', regime: 1 },
  { date: '8 Dec', regime: 1 },
  { date: '15 Dec', regime: 2 },
  { date: '22 Dec', regime: 2 },
  { date: '29 Dec', regime: 3 },
  { date: '5 Jan', regime: 3 },
]

const featureImportance = [
  { feature: 'RSI', importance: 0.24 },
  { feature: 'Volume', importance: 0.21 },
  { feature: 'MACD', importance: 0.18 },
  { feature: 'Volatility', importance: 0.16 },
  { feature: 'Momentum', importance: 0.14 },
  { feature: 'Market Regime', importance: 0.12 },
  { feature: 'FII/DII Flow', importance: 0.08 },
]

const sentimentData = [
  { date: '1 Jan', score: 65 },
  { date: '2 Jan', score: 72 },
  { date: '3 Jan', score: 68 },
  { date: '4 Jan', score: 75 },
  { date: '5 Jan', score: 82 },
  { date: '6 Jan', score: 78 },
  { date: '7 Jan', score: 85 },
]

export default function AIModelsPage() {
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

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-dark-700/30 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Current Sentiment</p>
            <h3 className="text-2xl font-bold text-success">85/100</h3>
            <p className="text-xs text-muted-foreground">Very Bullish</p>
          </div>

          <div className="p-4 bg-dark-700/30 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">News Sources</p>
            <h3 className="text-2xl font-bold text-white">1,247</h3>
            <p className="text-xs text-muted-foreground">Articles analyzed today</p>
          </div>

          <div className="p-4 bg-dark-700/30 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Sentiment Accuracy</p>
            <h3 className="text-2xl font-bold text-purple-500">73.2%</h3>
            <p className="text-xs text-muted-foreground">Backtested correlation</p>
          </div>
        </div>
      </div>

      {/* Model Performance Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LSTM-Attention */}
        <div className="card-glass rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">LSTM-Attention</h3>
            <span className="px-2 py-1 bg-success/20 text-success text-xs font-medium rounded">Active</span>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-muted-foreground">Accuracy</span>
                <span className="text-xs font-medium text-success">68.4%</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-success to-blue-500 h-2 rounded-full" style={{ width: '68.4%' }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-muted-foreground">Sharpe Ratio</span>
                <span className="text-xs font-medium text-blue-500">2.14</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full" style={{ width: '85.6%' }}></div>
              </div>
            </div>

            <div className="pt-2 border-t border-dark-700">
              <p className="text-xs text-muted-foreground">Best for: Trending markets</p>
            </div>
          </div>
        </div>

        {/* Transformer */}
        <div className="card-glass rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Transformer</h3>
            <span className="px-2 py-1 bg-success/20 text-success text-xs font-medium rounded">Active</span>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-muted-foreground">Accuracy</span>
                <span className="text-xs font-medium text-success">71.2%</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-success to-blue-500 h-2 rounded-full" style={{ width: '71.2%' }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-muted-foreground">Sharpe Ratio</span>
                <span className="text-xs font-medium text-blue-500">2.42</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full" style={{ width: '96.8%' }}></div>
              </div>
            </div>

            <div className="pt-2 border-t border-dark-700">
              <p className="text-xs text-muted-foreground">Best for: Complex patterns</p>
            </div>
          </div>
        </div>

        {/* XGBoost Ensemble */}
        <div className="card-glass rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">XGBoost Ensemble</h3>
            <span className="px-2 py-1 bg-blue-500/20 text-blue-500 text-xs font-medium rounded">Testing</span>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-muted-foreground">Accuracy</span>
                <span className="text-xs font-medium text-warning">64.8%</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-warning to-blue-500 h-2 rounded-full" style={{ width: '64.8%' }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-muted-foreground">Sharpe Ratio</span>
                <span className="text-xs font-medium text-blue-500">1.86</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full" style={{ width: '74.4%' }}></div>
              </div>
            </div>

            <div className="pt-2 border-t border-dark-700">
              <p className="text-xs text-muted-foreground">Best for: Mean reversion</p>
            </div>
          </div>
        </div>
      </div>

      {/* ML Pipeline Info */}
      <div className="card-glass rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">ML Pipeline Status</h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 bg-dark-700/30 rounded-lg border-l-4 border-purple-500">
            <p className="text-xs text-muted-foreground mb-1">Data Ingestion</p>
            <p className="text-sm font-medium text-white">Real-time</p>
            <div className="flex items-center gap-2 mt-2">
              <div className="w-2 h-2 rounded-full bg-success animate-pulse"></div>
              <span className="text-xs text-success">Active</span>
            </div>
          </div>

          <div className="p-4 bg-dark-700/30 rounded-lg border-l-4 border-blue-500">
            <p className="text-xs text-muted-foreground mb-1">Feature Engineering</p>
            <p className="text-sm font-medium text-white">150+ features</p>
            <div className="flex items-center gap-2 mt-2">
              <div className="w-2 h-2 rounded-full bg-success animate-pulse"></div>
              <span className="text-xs text-success">Active</span>
            </div>
          </div>

          <div className="p-4 bg-dark-700/30 rounded-lg border-l-4 border-warning">
            <p className="text-xs text-muted-foreground mb-1">Model Training</p>
            <p className="text-sm font-medium text-white">Daily retraining</p>
            <div className="flex items-center gap-2 mt-2">
              <div className="w-2 h-2 rounded-full bg-warning animate-pulse"></div>
              <span className="text-xs text-warning">Scheduled</span>
            </div>
          </div>

          <div className="p-4 bg-dark-700/30 rounded-lg border-l-4 border-success">
            <p className="text-xs text-muted-foreground mb-1">Inference</p>
            <p className="text-sm font-medium text-white">Every 5 min</p>
            <div className="flex items-center gap-2 mt-2">
              <div className="w-2 h-2 rounded-full bg-success animate-pulse"></div>
              <span className="text-xs text-success">Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
