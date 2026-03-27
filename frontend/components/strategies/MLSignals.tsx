'use client'

import React, { useState, useEffect } from 'react'
import {
  Brain, TrendingUp, TrendingDown, Activity,
  RefreshCw, AlertCircle, Layers, MessageSquare, Zap
} from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine
} from 'recharts'
import MetricCard from '@/components/ui/MetricCard'
import { formatPercentage } from '@/lib/utils'
import { api } from '@/lib/api'

interface Signal {
  signal: string
  confidence: number
  prediction?: number
  expected_return?: number
  reasoning?: string
  explanation?: string
  features_used?: number
}

type ModelTab = 'ensemble' | 'lstm' | 'xgboost' | 'sentiment'

export default function MLSignals() {
  const [loading, setLoading] = useState(false)
  const [symbol, setSymbol] = useState('NIFTY')
  const [activeModel, setActiveModel] = useState<ModelTab>('ensemble')
  const [ensembleSignal, setEnsembleSignal] = useState<any>(null)
  const [lstmSignal, setLstmSignal] = useState<Signal | null>(null)
  const [xgbSignal, setXgbSignal] = useState<Signal | null>(null)
  const [sentimentSignal, setSentimentSignal] = useState<Signal | null>(null)
  const [featureData, setFeatureData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const symbols = ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICI']

  useEffect(() => {
    fetchSignals()
  }, [symbol])

  const fetchSignals = async () => {
    setLoading(true)
    setError(null)
    try {
      const today = new Date().toISOString().split('T')[0]
      const sixMonthsAgo = new Date(Date.now() - 180 * 86400000).toISOString().split('T')[0]

      const [ensemble, lstm, xgb, sentiment, features] = await Promise.all([
        api.mlStrategies.getEnsemblePrediction(symbol),
        api.mlStrategies.getLSTMPrediction(symbol),
        api.mlStrategies.getXGBoostSignal(symbol),
        api.mlStrategies.getSentimentSignal(symbol, 0.1, 0.2),
        api.mlStrategies.generateFeatures(symbol, sixMonthsAgo, today),
      ])

      setEnsembleSignal(ensemble)
      setLstmSignal(lstm)
      setXgbSignal(xgb)
      setSentimentSignal(sentiment)
      setFeatureData(features)
    } catch (err) {
      setError('Failed to fetch ML signals. Ensure backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const getSignalColor = (signal: string | undefined) => {
    if (!signal) return 'text-gray-400'
    if (signal === 'buy' || signal === 'bullish') return 'text-green-400'
    if (signal === 'sell' || signal === 'bearish') return 'text-red-400'
    return 'text-yellow-400'
  }

  const getSignalBadge = (signal: string | undefined) => {
    if (!signal) return 'bg-gray-400/10 text-gray-400 border border-gray-400/20'
    if (signal === 'buy' || signal === 'bullish') return 'bg-green-400/10 text-green-400 border border-green-400/20'
    if (signal === 'sell' || signal === 'bearish') return 'bg-red-400/10 text-red-400 border border-red-400/20'
    return 'bg-yellow-400/10 text-yellow-400 border border-yellow-400/20'
  }

  const getSignalArrow = (signal: string | undefined) => {
    if (!signal) return <Activity className="w-5 h-5 text-gray-400" />
    if (signal === 'buy' || signal === 'bullish') return <TrendingUp className="w-5 h-5 text-green-400" />
    if (signal === 'sell' || signal === 'bearish') return <TrendingDown className="w-5 h-5 text-red-400" />
    return <Activity className="w-5 h-5 text-yellow-400" />
  }

  const modelTabs: { key: ModelTab; label: string; icon: React.ReactNode }[] = [
    { key: 'ensemble', label: 'Ensemble', icon: <Layers className="w-4 h-4" /> },
    { key: 'lstm', label: 'LSTM', icon: <Brain className="w-4 h-4" /> },
    { key: 'xgboost', label: 'XGBoost', icon: <Zap className="w-4 h-4" /> },
    { key: 'sentiment', label: 'Sentiment', icon: <MessageSquare className="w-4 h-4" /> },
  ]

  const getCurrentSignal = (): Signal | null => {
    switch (activeModel) {
      case 'ensemble': return ensembleSignal
      case 'lstm': return lstmSignal
      case 'xgboost': return xgbSignal
      case 'sentiment': return sentimentSignal
      default: return null
    }
  }

  const currentSignal = getCurrentSignal()
  const signalStr = currentSignal?.signal

  // Build model comparison chart
  const modelComparison = [
    { model: 'LSTM', confidence: lstmSignal?.confidence ?? 0, signal: lstmSignal?.signal ?? 'hold' },
    { model: 'XGBoost', confidence: xgbSignal?.confidence ?? 0, signal: xgbSignal?.signal ?? 'hold' },
    { model: 'Sentiment', confidence: sentimentSignal?.confidence ?? 0, signal: sentimentSignal?.signal ?? 'hold' },
    { model: 'Ensemble', confidence: ensembleSignal?.confidence ?? 0, signal: ensembleSignal?.signal ?? 'hold' },
  ].map(m => ({ ...m, confidence: (m.confidence * 100) }))

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
        <button
          onClick={fetchSignals}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Analyzing...' : 'Run Models'}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-400/10 border border-red-400/20 rounded-lg text-red-400 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'LSTM', signal: lstmSignal },
          { label: 'XGBoost', signal: xgbSignal },
          { label: 'Sentiment', signal: sentimentSignal },
          { label: 'Ensemble', signal: ensembleSignal },
        ].map(({ label, signal }) => (
          <div key={label} className="bg-dark-800 border border-dark-600 rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">{label}</span>
              {getSignalArrow(signal?.signal)}
            </div>
            <div className={`text-xl font-bold ${getSignalColor(signal?.signal)}`}>
              {signal?.signal?.toUpperCase() ?? '—'}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Confidence: {signal ? (signal.confidence * 100).toFixed(0) + '%' : '—'}
            </div>
          </div>
        ))}
      </div>

      {/* Model Tabs */}
      <div className="bg-dark-800 border border-dark-600 rounded-xl overflow-hidden">
        <div className="flex border-b border-dark-600">
          {modelTabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveModel(tab.key)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                activeModel === tab.key
                  ? 'text-white border-b-2 border-purple-500 bg-dark-700'
                  : 'text-muted-foreground hover:text-white'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-4">
          {currentSignal ? (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div>
                  <span className="text-xs text-muted-foreground uppercase tracking-wide">Signal</span>
                  <div className={`mt-1 text-2xl font-bold ${getSignalColor(signalStr)}`}>
                    {signalStr?.toUpperCase() ?? '—'}
                  </div>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground uppercase tracking-wide">Confidence</span>
                  <div className="mt-1 text-2xl font-bold text-white">
                    {(currentSignal.confidence * 100).toFixed(1)}%
                  </div>
                </div>
                {currentSignal.prediction != null && (
                  <div>
                    <span className="text-xs text-muted-foreground uppercase tracking-wide">Prediction</span>
                    <div className={`mt-1 text-2xl font-bold ${currentSignal.prediction > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {currentSignal.prediction > 0 ? '+' : ''}{(currentSignal.prediction * 100).toFixed(2)}%
                    </div>
                  </div>
                )}
                {currentSignal.expected_return != null && (
                  <div>
                    <span className="text-xs text-muted-foreground uppercase tracking-wide">Expected Return</span>
                    <div className={`mt-1 text-2xl font-bold ${currentSignal.expected_return > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {currentSignal.expected_return > 0 ? '+' : ''}{(currentSignal.expected_return * 100).toFixed(2)}%
                    </div>
                  </div>
                )}
              </div>

              {(currentSignal.reasoning || currentSignal.explanation) && (
                <div className="p-3 bg-dark-700 rounded-lg text-sm text-muted-foreground">
                  {currentSignal.reasoning || currentSignal.explanation}
                </div>
              )}

              {currentSignal.features_used != null && (
                <p className="text-xs text-muted-foreground">Features used: {currentSignal.features_used}</p>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground text-sm">
              {loading ? 'Running ML models...' : 'Click "Run Models" to generate signals.'}
            </div>
          )}
        </div>
      </div>

      {/* Model Confidence Comparison */}
      {modelComparison.some(m => m.confidence > 0) && (
        <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
          <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
            <Brain className="w-4 h-4 text-purple-400" />
            Model Confidence Comparison
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={modelComparison} layout="vertical" margin={{ left: 10, right: 30, top: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis type="number" domain={[0, 100]} tick={{ fill: '#9CA3AF', fontSize: 11 }} unit="%" />
              <YAxis type="category" dataKey="model" tick={{ fill: '#9CA3AF', fontSize: 11 }} width={70} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }}
                formatter={(val: any) => [`${val.toFixed(1)}%`, 'Confidence']}
              />
              <Bar dataKey="confidence" radius={[0, 4, 4, 0]}>
                {modelComparison.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={
                      entry.signal === 'buy' || entry.signal === 'bullish' ? '#10B981'
                        : entry.signal === 'sell' || entry.signal === 'bearish' ? '#EF4444'
                        : '#F59E0B'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
