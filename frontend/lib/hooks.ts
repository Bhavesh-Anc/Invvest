import { useState, useEffect } from 'react'

export interface UseAPIOptions {
  immediate?: boolean
}

export function useAPI<T>(
  apiCall: () => Promise<T>,
  options: UseAPIOptions = { immediate: true }
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState<boolean>(options.immediate ?? true)
  const [error, setError] = useState<Error | null>(null)

  const execute = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await apiCall()
      setData(result)
      return result
    } catch (err) {
      const error = err instanceof Error ? err : new Error('An error occurred')
      setError(error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (options.immediate) {
      execute()
    }
  }, [])

  return { data, loading, error, refetch: execute }
}
