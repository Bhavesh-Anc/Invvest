import React from 'react'
import { AlertCircle } from 'lucide-react'

interface ErrorDisplayProps {
  error: Error
  onRetry?: () => void
}

export default function ErrorDisplay({ error, onRetry }: ErrorDisplayProps) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center max-w-md">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-danger/10 rounded-full mb-4">
          <AlertCircle className="w-8 h-8 text-danger" />
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">Something went wrong</h3>
        <p className="text-muted-foreground mb-4">{error.message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  )
}
