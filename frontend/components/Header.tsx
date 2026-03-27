'use client'

import { Bell, User } from 'lucide-react'
import { formatCurrency, formatPercentage, getChangeColor } from '@/lib/utils'

// Mock data - will be replaced with real API data
const marketData = {
  nifty: 21894.35,
  niftyChange: 1.24,
  sensex: 72410.18,
  sensexChange: 0.98,
  bankNifty: 47623.90,
  bankNiftyChange: -0.42,
}

export function Header() {
  return (
    <header className="flex items-center justify-between px-6 py-4 bg-dark-800 border-b border-dark-600">
      {/* Market Indices */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 text-xs font-medium text-success bg-success/20 rounded-full">
            NSE OPEN
          </span>
        </div>

        <div className="flex items-center gap-1">
          <span className="text-sm font-medium text-muted-foreground">NIFTY 50</span>
          <span className="text-sm font-bold text-white">{marketData.nifty.toLocaleString()}</span>
          <span className={`text-xs font-medium ${getChangeColor(marketData.niftyChange)}`}>
            {formatPercentage(marketData.niftyChange)}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <span className="text-sm font-medium text-muted-foreground">SENSEX</span>
          <span className="text-sm font-bold text-white">{marketData.sensex.toLocaleString()}</span>
          <span className={`text-xs font-medium ${getChangeColor(marketData.sensexChange)}`}>
            {formatPercentage(marketData.sensexChange)}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <span className="text-sm font-medium text-muted-foreground">BANK NIFTY</span>
          <span className="text-sm font-bold text-white">{marketData.bankNifty.toLocaleString()}</span>
          <span className={`text-xs font-medium ${getChangeColor(marketData.bankNiftyChange)}`}>
            {formatPercentage(marketData.bankNiftyChange)}
          </span>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Account:</span>
          <span className="text-sm font-medium text-purple-500">Professional</span>
        </div>

        <button className="relative p-2 text-muted-foreground hover:text-white transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-danger rounded-full"></span>
        </button>

        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 text-xs font-medium text-success bg-success/20 rounded-full">
            Broker Connected
          </span>
        </div>

        <button className="flex items-center gap-2 px-3 py-2 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors">
          <User className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}
