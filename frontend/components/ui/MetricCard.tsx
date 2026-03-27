import { ReactNode } from 'react'
import { cn, formatCurrency, formatPercentage, getChangeColor } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string | number
  change?: number
  changeLabel?: string
  icon?: ReactNode
  trend?: 'up' | 'down' | 'neutral'
  alert?: boolean
  subtitle?: string
  className?: string
}

export function MetricCard({
  title,
  value,
  change,
  changeLabel,
  icon,
  trend,
  alert,
  subtitle,
  className,
}: MetricCardProps) {
  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4" />
    if (trend === 'down') return <TrendingDown className="w-4 h-4" />
    return <Minus className="w-4 h-4" />
  }

  return (
    <div className={cn('card-glass rounded-xl p-5', className)}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          {subtitle && <p className="text-xs text-muted-foreground/60 mt-0.5">{subtitle}</p>}
        </div>
        {icon && (
          <div className={cn(
            'p-2 rounded-lg',
            alert ? 'bg-warning/20 text-warning' : 'bg-purple-600/20 text-purple-500'
          )}>
            {alert ? <AlertTriangle className="w-4 h-4" /> : icon}
          </div>
        )}
      </div>

      <div className="flex items-end justify-between">
        <div>
          <h3 className="text-2xl font-bold text-white mb-1">{value}</h3>
          {change !== undefined && (
            <div className={cn('flex items-center gap-1 text-sm font-medium', getChangeColor(change))}>
              {getTrendIcon()}
              <span>{changeLabel || formatPercentage(change)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
