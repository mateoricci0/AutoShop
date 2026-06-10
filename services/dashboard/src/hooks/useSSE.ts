'use client'

import { useEffect, useRef, useState } from 'react'

interface SSEState<T> {
  data: T | null
  error: Event | null
  readyState: number
}

export function useSSE<T = unknown>(url: string, enabled = true): SSEState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Event | null>(null)
  const [readyState, setReadyState] = useState<number>(EventSource.CLOSED)
  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!enabled || !url) return

    let isMounted = true
    let reconnectDelay = 1000

    function connect() {
      if (!isMounted) return

      const es = new EventSource(url, { withCredentials: true })
      eventSourceRef.current = es
      setReadyState(EventSource.CONNECTING)

      es.onopen = () => {
        if (!isMounted) return
        setReadyState(EventSource.OPEN)
        setError(null)
        reconnectDelay = 1000 // reset backoff on success
      }

      es.onmessage = (event) => {
        if (!isMounted) return
        try {
          const parsed = JSON.parse(event.data) as T
          setData(parsed)
        } catch {
          setData(event.data as unknown as T)
        }
      }

      es.onerror = (evt) => {
        if (!isMounted) return
        setError(evt)
        setReadyState(EventSource.CLOSED)
        es.close()
        // Auto-reconnect with exponential backoff (max 30s)
        reconnectTimeoutRef.current = setTimeout(() => {
          if (isMounted) {
            reconnectDelay = Math.min(reconnectDelay * 2, 30_000)
            connect()
          }
        }, reconnectDelay)
      }
    }

    connect()

    return () => {
      isMounted = false
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [url, enabled])

  return { data, error, readyState }
}
