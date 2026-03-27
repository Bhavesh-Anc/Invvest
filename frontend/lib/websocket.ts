/**
 * WebSocket Service for Real-time Market Data Updates
 * Provides live updates for prices, portfolio values, and other time-sensitive data
 */

import { useEffect, useState } from 'react'

type WebSocketCallback = (data: any) => void
type WebSocketChannel = 'market-data' | 'portfolio' | 'orders' | 'notifications'

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000 // Start with 1 second
  private subscribers: Map<WebSocketChannel, Set<WebSocketCallback>> = new Map()
  private isConnecting = false
  private url: string

  constructor() {
    this.url = this.getWebSocketURL()
    this.initializeChannels()
  }

  private getWebSocketURL(): string {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    // Convert HTTP URL to WebSocket URL
    return apiUrl.replace(/^http/, 'ws') + '/ws'
  }

  private initializeChannels() {
    const channels: WebSocketChannel[] = ['market-data', 'portfolio', 'orders', 'notifications']
    channels.forEach(channel => {
      this.subscribers.set(channel, new Set())
    })
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return
    }

    this.isConnecting = true

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected')
        this.isConnecting = false
        this.reconnectAttempts = 0
        this.reconnectDelay = 1000

        // Subscribe to all active channels
        this.subscribers.forEach((_, channel) => {
          this.send({ type: 'subscribe', channel })
        })
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error)
        this.isConnecting = false
      }

      this.ws.onclose = () => {
        console.log('[WebSocket] Connection closed')
        this.isConnecting = false
        this.ws = null
        this.attemptReconnect()
      }
    } catch (error) {
      console.error('[WebSocket] Connection failed:', error)
      this.isConnecting = false
      this.attemptReconnect()
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1) // Exponential backoff

    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    setTimeout(() => {
      this.connect()
    }, delay)
  }

  private handleMessage(data: any) {
    const { channel, payload } = data

    if (!channel) {
      console.warn('[WebSocket] Received message without channel:', data)
      return
    }

    const subscribers = this.subscribers.get(channel as WebSocketChannel)
    if (subscribers) {
      subscribers.forEach(callback => {
        try {
          callback(payload)
        } catch (error) {
          console.error(`[WebSocket] Error in subscriber callback for channel ${channel}:`, error)
        }
      })
    }
  }

  subscribe(channel: WebSocketChannel, callback: WebSocketCallback): () => void {
    const subscribers = this.subscribers.get(channel)
    if (!subscribers) {
      console.error(`[WebSocket] Unknown channel: ${channel}`)
      return () => {}
    }

    subscribers.add(callback)

    // Connect if not already connected
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.connect()
    } else {
      // Already connected, send subscribe message
      this.send({ type: 'subscribe', channel })
    }

    // Return unsubscribe function
    return () => {
      subscribers.delete(callback)

      // If no more subscribers for this channel, unsubscribe
      if (subscribers.size === 0) {
        this.send({ type: 'unsubscribe', channel })
      }
    }
  }

  private send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  getConnectionState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// Export singleton instance
export const websocketService = new WebSocketService()

// Export hook for React components
export function useWebSocket(channel: WebSocketChannel, callback: WebSocketCallback) {
  if (typeof window === 'undefined') {
    // SSR - don't connect
    return { isConnected: false }
  }

  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    const unsubscribe = websocketService.subscribe(channel, callback)

    // Monitor connection state
    const checkConnection = setInterval(() => {
      setIsConnected(websocketService.isConnected())
    }, 1000)

    return () => {
      unsubscribe()
      clearInterval(checkConnection)
    }
  }, [channel, callback])

  return { isConnected }
}

// For non-React contexts
export default websocketService
