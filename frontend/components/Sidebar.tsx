'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  PieChart,
  TrendingUp,
  Layers,
  Bot,
  Shield,
  LineChart,
  Brain,
  Settings,
  Activity,
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Portfolio Analytics', href: '/portfolio', icon: PieChart },
  { name: 'Options Analytics', href: '/options', icon: TrendingUp },
  { name: 'Strategy Builder', href: '/strategy', icon: Layers },
  { name: 'Algo Trading', href: '/algo', icon: Bot },
  { name: 'Market Making', href: '/market-making', icon: Activity },
  { name: 'Risk Management', href: '/risk', icon: Shield },
  { name: 'Backtesting', href: '/backtest', icon: LineChart },
  { name: 'AI Models', href: '/models', icon: Brain },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex flex-col w-64 bg-dark-800 border-r border-dark-600">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-dark-600">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
          <TrendingUp className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-white">QuantEdge Pro</h1>
          <p className="text-xs text-muted-foreground">NSE/BSE Terminal</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                isActive
                  ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20'
                  : 'text-muted-foreground hover:bg-dark-700 hover:text-white'
              )}
            >
              <Icon className="w-5 h-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Settings */}
      <div className="p-3 border-t border-dark-600">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:bg-dark-700 hover:text-white transition-all"
        >
          <Settings className="w-5 h-5" />
          Settings
        </Link>
      </div>
    </div>
  )
}
