import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number, currency: string = '₹'): string {
  return `${currency}${value.toLocaleString('en-IN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`
}

export function formatPercentage(value: number, decimals: number = 2): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`
}

export function formatNumber(value: number, decimals: number = 2): string {
  return value.toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export function getChangeColor(value: number): string {
  if (value > 0) return 'text-success'
  if (value < 0) return 'text-danger'
  return 'text-muted-foreground'
}

export function getStatusColor(status: string): string {
  switch (status.toUpperCase()) {
    case 'ACTIVE':
      return 'bg-success/20 text-success border-success/30'
    case 'PAUSED':
      return 'bg-warning/20 text-warning border-warning/30'
    case 'INACTIVE':
      return 'bg-muted/20 text-muted-foreground border-muted/30'
    default:
      return 'bg-muted/20 text-muted-foreground border-muted/30'
  }
}

export function abbreviateNumber(value: number): string {
  if (value >= 10000000) {
    return `${(value / 10000000).toFixed(2)}Cr`
  }
  if (value >= 100000) {
    return `${(value / 100000).toFixed(2)}L`
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(2)}K`
  }
  return value.toString()
}
