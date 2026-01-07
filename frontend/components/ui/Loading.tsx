import React from 'react'

export default function Loading({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500 mb-4"></div>
        <p className="text-muted-foreground">{message}</p>
      </div>
    </div>
  )
}
