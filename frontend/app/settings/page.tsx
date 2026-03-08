'use client'

import React, { useState, useEffect } from 'react'
import {
  Settings as SettingsIcon, Key, Shield, CheckCircle,
  XCircle, RefreshCw, ExternalLink, AlertCircle, Copy
} from 'lucide-react'
import MetricCard from '@/components/ui/MetricCard'
import { api } from '@/lib/api'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'kite' | 'general'>('kite')
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')
  const [requestToken, setRequestToken] = useState('')
  const [authStatus, setAuthStatus] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null)
  const [loginUrl, setLoginUrl] = useState('')

  useEffect(() => {
    fetchAuthStatus()
    // Check for request_token in URL (redirect from Kite login)
    const urlParams = new URLSearchParams(window.location.search)
    const token = urlParams.get('request_token')
    if (token) {
      setRequestToken(token)
      setMessage({ type: 'info', text: `Request token received: ${token.substring(0, 20)}...` })
    }
  }, [])

  const fetchAuthStatus = async () => {
    try {
      const status = await api.kite.getAuthStatus()
      setAuthStatus(status)
    } catch (err) {
      console.error('Failed to fetch auth status:', err)
    }
  }

  const handleSaveConfig = async () => {
    if (!apiKey || !apiSecret) {
      setMessage({ type: 'error', text: 'Please enter both API Key and API Secret' })
      return
    }

    setLoading(true)
    setMessage(null)

    try {
      await api.kite.saveConfig(apiKey, apiSecret)
      setMessage({ type: 'success', text: 'Configuration saved successfully!' })
      await fetchAuthStatus()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to save configuration' })
    } finally {
      setLoading(false)
    }
  }

  const handleGetLoginUrl = async () => {
    setLoading(true)
    setMessage(null)

    try {
      const response: any = await api.kite.getLoginUrl()
      setLoginUrl(response.login_url)
      setMessage({
        type: 'info',
        text: 'Login URL generated. Click the link below to login with your Zerodha credentials.'
      })
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to get login URL' })
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateSession = async () => {
    if (!apiKey || !apiSecret || !requestToken) {
      setMessage({ type: 'error', text: 'Please enter API Key, API Secret, and Request Token' })
      return
    }

    setLoading(true)
    setMessage(null)

    try {
      const response: any = await api.kite.generateSession(apiKey, apiSecret, requestToken)
      setMessage({
        type: 'success',
        text: `Authentication successful! Logged in as ${response.user_name} (${response.user_id})`
      })
      await fetchAuthStatus()
      setRequestToken('')
      // Clear URL params
      window.history.replaceState({}, document.title, window.location.pathname)
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to generate session' })
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    setLoading(true)
    try {
      await api.kite.logout()
      setMessage({ type: 'success', text: 'Logged out successfully' })
      await fetchAuthStatus()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to logout' })
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setMessage({ type: 'success', text: 'Copied to clipboard!' })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
        <p className="text-muted-foreground">Configure API credentials and platform settings</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-dark-600">
        {[
          { key: 'kite' as const, label: 'Kite Connect', icon: <Key className="w-4 h-4" /> },
          { key: 'general' as const, label: 'General', icon: <SettingsIcon className="w-4 h-4" /> },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-purple-500 text-white'
                : 'border-transparent text-muted-foreground hover:text-white'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Kite Connect Tab */}
      {activeTab === 'kite' && (
        <div className="space-y-6">
          {/* Status Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="API Configured"
              value={authStatus?.configured ? 'Yes' : 'No'}
              icon={authStatus?.configured ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
              color={authStatus?.configured ? 'green' : 'red'}
            />
            <MetricCard
              title="Authenticated"
              value={authStatus?.authenticated ? 'Yes' : 'No'}
              subtitle={authStatus?.user_id || 'Not logged in'}
              icon={authStatus?.authenticated ? <Shield className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
              color={authStatus?.authenticated ? 'green' : 'yellow'}
            />
            <MetricCard
              title="API Key"
              value={authStatus?.api_key ? `${authStatus.api_key}` : 'Not Set'}
              icon={<Key className="w-5 h-5" />}
              color="blue"
            />
            <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
              <button
                onClick={fetchAuthStatus}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh Status
              </button>
            </div>
          </div>

          {/* Message Display */}
          {message && (
            <div className={`flex items-start gap-2 p-3 rounded-lg border ${
              message.type === 'success' ? 'bg-green-400/10 border-green-400/20 text-green-400'
                : message.type === 'error' ? 'bg-red-400/10 border-red-400/20 text-red-400'
                : 'bg-blue-400/10 border-blue-400/20 text-blue-400'
            }`}>
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span className="text-sm">{message.text}</span>
            </div>
          )}

          {/* Configuration Section */}
          <div className="bg-dark-800 border border-dark-600 rounded-xl p-6 space-y-4">
            <h3 className="text-white font-semibold flex items-center gap-2">
              <Key className="w-5 h-5 text-purple-400" />
              API Configuration
            </h3>
            <p className="text-sm text-muted-foreground">
              Enter your Kite Connect API credentials from{' '}
              <a href="https://console.zerodha.com" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline inline-flex items-center gap-1">
                console.zerodha.com
                <ExternalLink className="w-3 h-3" />
              </a>
            </p>

            <div>
              <label className="text-sm text-muted-foreground mb-2 block">API Key</label>
              <input
                type="text"
                value={apiKey}
                onChange={e => setApiKey(e.target.value)}
                placeholder="Enter your API Key"
                className="w-full px-4 py-2 bg-dark-700 border border-dark-500 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div>
              <label className="text-sm text-muted-foreground mb-2 block">API Secret</label>
              <input
                type="password"
                value={apiSecret}
                onChange={e => setApiSecret(e.target.value)}
                placeholder="Enter your API Secret"
                className="w-full px-4 py-2 bg-dark-700 border border-dark-500 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <button
              onClick={handleSaveConfig}
              disabled={loading}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>

          {/* Authentication Section */}
          {authStatus?.configured && !authStatus?.authenticated && (
            <div className="bg-dark-800 border border-dark-600 rounded-xl p-6 space-y-4">
              <h3 className="text-white font-semibold flex items-center gap-2">
                <Shield className="w-5 h-5 text-yellow-400" />
                Login to Kite
              </h3>
              <p className="text-sm text-muted-foreground">
                Complete OAuth flow to authenticate with Zerodha Kite
              </p>

              <div className="flex gap-3">
                <button
                  onClick={handleGetLoginUrl}
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
                >
                  {loading ? 'Generating...' : 'Get Login URL'}
                </button>
              </div>

              {loginUrl && (
                <div className="p-4 bg-dark-700 rounded-lg space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Login URL:</span>
                    <button
                      onClick={() => copyToClipboard(loginUrl)}
                      className="text-blue-400 hover:text-blue-300 text-xs flex items-center gap-1"
                    >
                      <Copy className="w-3 h-3" />
                      Copy
                    </button>
                  </div>
                  <a
                    href={loginUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:underline text-sm break-all flex items-center gap-2"
                  >
                    {loginUrl.substring(0, 80)}...
                    <ExternalLink className="w-4 h-4 flex-shrink-0" />
                  </a>
                  <p className="text-xs text-muted-foreground mt-2">
                    After logging in, you'll be redirected back with a request_token in the URL. Copy it and paste below.
                  </p>
                </div>
              )}

              <div>
                <label className="text-sm text-muted-foreground mb-2 block">Request Token (from login callback URL)</label>
                <input
                  type="text"
                  value={requestToken}
                  onChange={e => setRequestToken(e.target.value)}
                  placeholder="Paste request token here"
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-500 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <button
                onClick={handleGenerateSession}
                disabled={loading || !requestToken}
                className="px-6 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
              >
                {loading ? 'Authenticating...' : 'Complete Authentication'}
              </button>
            </div>
          )}

          {/* Logout Section */}
          {authStatus?.authenticated && (
            <div className="bg-dark-800 border border-dark-600 rounded-xl p-6 space-y-4">
              <h3 className="text-white font-semibold flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-400" />
                Connected to Kite
              </h3>
              <p className="text-sm text-muted-foreground">
                User ID: <span className="text-white font-medium">{authStatus.user_id}</span>
              </p>
              <p className="text-sm text-muted-foreground">
                You are successfully authenticated. Access token is valid until 6 AM IST tomorrow.
              </p>
              <button
                onClick={handleLogout}
                disabled={loading}
                className="px-6 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
              >
                {loading ? 'Logging out...' : 'Logout'}
              </button>
            </div>
          )}

          {/* Instructions */}
          <div className="bg-dark-800 border border-dark-600 rounded-xl p-6 space-y-3">
            <h3 className="text-white font-semibold">Setup Instructions</h3>
            <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
              <li>Create a Kite Connect app at <a href="https://console.zerodha.com" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">console.zerodha.com</a></li>
              <li>Enter your API Key and API Secret above and click "Save Configuration"</li>
              <li>Click "Get Login URL" and open the link in a new tab</li>
              <li>Login with your Zerodha credentials (User ID + Password + TOTP)</li>
              <li>After successful login, copy the request_token from the redirect URL</li>
              <li>Paste the request_token and click "Complete Authentication"</li>
              <li>You're all set! The platform will now use live NSE/BSE data from Kite</li>
            </ol>
          </div>
        </div>
      )}

      {/* General Tab */}
      {activeTab === 'general' && (
        <div className="bg-dark-800 border border-dark-600 rounded-xl p-6">
          <h3 className="text-white font-semibold mb-4">General Settings</h3>
          <p className="text-muted-foreground text-sm">Coming soon...</p>
        </div>
      )}
    </div>
  )
}
