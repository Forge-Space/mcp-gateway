/**
 * MCP Gateway Integration Service
 * Provides real-time connection and API integration with the MCP Gateway
 */

import { create } from 'zustand'

export interface GatewayStatus {
  status: 'online' | 'offline' | 'error'
  uptime: number
  version: string
  lastCheck: Date
}

export interface ServerMetrics {
  id: string
  name: string
  status: 'running' | 'stopped' | 'error'
  cpu: number
  memory: number
  requests: number
  errors: number
  lastActivity: Date
}

export interface GatewayConfig {
  apiUrl: string
  apiKey: string
  wsUrl: string
  reconnectInterval: number
  maxReconnectAttempts: number
}

interface GatewayState {
  status: GatewayStatus | null
  servers: ServerMetrics[]
  connected: boolean
  loading: boolean
  error: string | null
  config: GatewayConfig
  connect: () => void
  disconnect: () => void
  fetchStatus: () => Promise<void>
  fetchServers: () => Promise<void>
  updateConfig: (config: Partial<GatewayConfig>) => void
}

export const useGatewayStore = create<GatewayState>((set, get) => ({
  status: null,
  servers: [],
  connected: false,
  loading: false,
  error: null,
  config: {
    apiUrl: process.env.NEXT_PUBLIC_MCP_GATEWAY_URL || 'http://localhost:4444',
    apiKey: process.env.NEXT_PUBLIC_MCP_GATEWAY_API_KEY || '',
    wsUrl: process.env.NEXT_PUBLIC_MCP_GATEWAY_WS_URL || 'ws://localhost:4444/ws',
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
  },

  connect: () => {
    const { config } = get()

    if (!config.apiUrl || !config.apiKey) {
      set({ error: 'Gateway configuration missing' })
      return
    }

    set({ loading: true, error: null })

    // Test connection first
    fetch(config.apiUrl + '/health', {
      headers: {
        'Authorization': `Bearer ${config.apiKey}`,
        'Content-Type': 'application/json',
      },
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        return response.json()
      })
      .then((data: any) => {
        set({
          status: {
            status: 'online',
            uptime: data.uptime || 0,
            version: data.version || 'unknown',
            lastCheck: new Date(),
          },
          connected: true,
          loading: false,
          error: null,
        })

        // Start WebSocket connection
        connectWebSocket()
      })
      .catch((error: unknown) => {
        set({
          error: error instanceof Error ? error.message : String(error),
          connected: false,
          loading: false,
        })
      })
  },

  disconnect: () => {
    set({
      connected: false,
      status: null,
      servers: [],
      error: null,
    })
  },

  fetchStatus: async () => {
    const { config } = get()

    try {
      const response = await fetch(config.apiUrl + '/health', {
        headers: {
          'Authorization': `Bearer ${config.apiKey}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json() as { uptime?: number; version?: string }

      set({
        status: {
          status: 'online',
          uptime: data.uptime || 0,
          version: data.version || 'unknown',
          lastCheck: new Date(),
        },
        connected: true,
        error: null,
      })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : String(error),
        connected: false,
        status: {
          status: 'offline',
          uptime: 0,
          version: 'unknown',
          lastCheck: new Date(),
        },
      })
    }
  },

  fetchServers: async () => {
    const { config } = get()

    try {
      const response = await fetch(config.apiUrl + '/api/servers', {
        headers: {
          'Authorization': `Bearer ${config.apiKey}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const servers = await response.json()

      set({
        servers: (servers as Array<ServerMetrics & { lastActivity?: string | number }>).map(server => ({
          ...server,
          lastActivity: new Date(server.lastActivity || Date.now()),
        }))
      })
    } catch (error) {
      set({ error: error instanceof Error ? error.message : String(error) })
    }
  },

  updateConfig: (newConfig: Partial<GatewayConfig>) => {
    set({ config: { ...get().config, ...newConfig } })
  },
}))

// WebSocket connection management
let ws: WebSocket | null = null
let reconnectAttempts = 0
let reconnectTimer: NodeJS.Timeout | null = null

function connectWebSocket() {
  const { config } = useGatewayStore.getState()

  if (ws) {
    ws.close()
  }

  try {
    ws = new WebSocket(config.wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected to MCP Gateway')
      reconnectAttempts = 0
      useGatewayStore.setState({ connected: true })
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'server_update':
            useGatewayStore.setState({
              servers: useGatewayStore.getState().servers.map(server =>
                server.id === data.server.id
                  ? { ...server, ...data.server }
                  : server
              )
            })
            break
          case 'status_update':
            useGatewayStore.setState({
              status: data.status
            })
            break
          case 'metrics_update':
            useGatewayStore.setState({
              servers: data.servers
            })
            break
        }
      } catch (error) {
        console.error('WebSocket message error:', error)
      }
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      useGatewayStore.setState({ connected: false })

      // Attempt reconnection
      if (reconnectAttempts < config.maxReconnectAttempts) {
        reconnectTimer = setTimeout(() => {
          reconnectAttempts++
          connectWebSocket()
        }, config.reconnectInterval)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      useGatewayStore.setState({
        error: 'WebSocket connection error',
        connected: false
      })
    }
  } catch (error) {
    console.error('WebSocket connection error:', error)
    useGatewayStore.setState({
      error: 'Failed to connect to WebSocket',
      connected: false
    })
  }
}

// Cleanup on unmount
if (typeof window !== 'undefined') {
  (window as any).addEventListener('beforeunload', () => {
    if (ws) {
      ws.close()
    }
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
    }
  })
}
