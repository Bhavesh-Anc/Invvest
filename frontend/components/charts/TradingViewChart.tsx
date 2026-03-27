'use client'

/**
 * TradingView Advanced Chart Component
 * Professional-grade candlestick charts with 50+ indicators
 */

import { useEffect, useRef, memo } from 'react'

declare global {
  interface Window {
    TradingView: any
  }
}

interface TradingViewChartProps {
  symbol: string
  exchange?: 'NSE' | 'BSE' | 'NYSE' | 'NASDAQ'
  interval?: 'D' | '60' | '30' | '15' | '5' | '1'
  theme?: 'dark' | 'light'
  height?: number
  showToolbar?: boolean
  allowSymbolChange?: boolean
  studies?: string[]
  timezone?: string
}

function TradingViewChart({
  symbol,
  exchange = 'NSE',
  interval = 'D',
  theme = 'dark',
  height = 600,
  showToolbar = true,
  allowSymbolChange = true,
  studies = ['MASimple@tv-basicstudies', 'RSI@tv-basicstudies', 'MACD@tv-basicstudies'],
  timezone = 'Asia/Kolkata',
}: TradingViewChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const widgetRef = useRef<any>(null)

  useEffect(() => {
    // Load TradingView script
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/tv.js'
    script.async = true
    script.onload = () => initWidget()
    document.head.appendChild(script)

    return () => {
      // Cleanup
      if (widgetRef.current) {
        try {
          widgetRef.current.remove()
        } catch (e) {
          console.error('Error removing TradingView widget:', e)
        }
      }
      document.head.removeChild(script)
    }
  }, [])

  useEffect(() => {
    // Reinitialize when symbol changes
    if (window.TradingView && containerRef.current) {
      initWidget()
    }
  }, [symbol, interval, theme])

  const initWidget = () => {
    if (!containerRef.current || !window.TradingView) return

    // Remove existing widget
    if (widgetRef.current) {
      try {
        widgetRef.current.remove()
      } catch (e) {
        console.error('Error removing existing widget:', e)
      }
    }

    // Clear container
    containerRef.current.innerHTML = ''

    // Create new widget
    widgetRef.current = new window.TradingView.widget({
      autosize: true,
      symbol: `${exchange}:${symbol}`,
      interval: interval,
      timezone: timezone,
      theme: theme,
      style: '1', // Candlestick
      locale: 'en',
      toolbar_bg: theme === 'dark' ? '#0A0E27' : '#ffffff',
      enable_publishing: false,
      hide_side_toolbar: !showToolbar,
      allow_symbol_change: allowSymbolChange,
      container_id: containerRef.current.id,

      // Studies/Indicators
      studies: studies,

      // Disabled features for cleaner UI
      disabled_features: [
        'header_symbol_search',
        'symbol_search_hot_key',
        'header_compare',
        'compare_symbol',
        'border_around_the_chart',
        'remove_library_container_border',
      ],

      // Enabled features
      enabled_features: [
        'study_templates',
        'side_toolbar_in_fullscreen_mode',
        'header_in_fullscreen_mode',
      ],

      // Overrides for dark theme
      overrides: {
        'paneProperties.background': theme === 'dark' ? '#0A0E27' : '#ffffff',
        'paneProperties.backgroundType': 'solid',
        'paneProperties.vertGridProperties.color': theme === 'dark' ? '#1A2038' : '#e0e0e0',
        'paneProperties.horzGridProperties.color': theme === 'dark' ? '#1A2038' : '#e0e0e0',
        'scalesProperties.textColor': theme === 'dark' ? '#9CA3AF' : '#333333',
        'scalesProperties.backgroundColor': theme === 'dark' ? '#131829' : '#ffffff',

        // Candlestick colors
        'mainSeriesProperties.candleStyle.upColor': '#10B981',
        'mainSeriesProperties.candleStyle.downColor': '#EF4444',
        'mainSeriesProperties.candleStyle.borderUpColor': '#10B981',
        'mainSeriesProperties.candleStyle.borderDownColor': '#EF4444',
        'mainSeriesProperties.candleStyle.wickUpColor': '#10B981',
        'mainSeriesProperties.candleStyle.wickDownColor': '#EF4444',
      },

      // Loading screen
      loading_screen: {
        backgroundColor: theme === 'dark' ? '#0A0E27' : '#ffffff',
        foregroundColor: theme === 'dark' ? '#8B5CF6' : '#3B82F6',
      },
    })
  }

  return (
    <div className="w-full" style={{ height: `${height}px` }}>
      <div
        id={`tradingview-chart-${symbol}`}
        ref={containerRef}
        className="w-full h-full rounded-xl overflow-hidden"
      />
    </div>
  )
}

export default memo(TradingViewChart)
