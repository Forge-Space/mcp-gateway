'use client'

import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useGatewayStore } from '@/lib/mcp-gateway'
import { Activity, Wifi, WifiOff, AlertCircle, RefreshCw } from 'lucide-react'

export function GatewayStatus() {
  const { status, connected, loading, error, fetchStatus, connect, disconnect } = useGatewayStore()

  useEffect(() => {
    // Initial status fetch
    fetchStatus()

    // Set up polling for status updates
    const interval = setInterval(fetchStatus, 30000) // 30 seconds

    return () => clearInterval(interval)
  }, [fetchStatus])

  const getStatusIcon = () => {
    if (!status) return <AlertCircle className="h-5 w-5" />
    switch (status.status) {
      case 'online':
        return <Wifi className="h-5 w-5" />
      case 'offline':
        return <WifiOff className="h-5 w-5" />
      case 'error':
        return <AlertCircle className="h-5 w-5" />
      default:
        return <Activity className="h-5 w-5" />
    }
  }

  const getStatusColor = () => {
    if (!status) return 'text-gray-500'
    switch (status.status) {
      case 'online':
        return 'text-green-600'
      case 'offline':
        return 'text-red-600'
      case 'error':
        return 'text-orange-600'
      default:
        return 'text-gray-500'
    }
  }

  const getStatusBadge = () => {
    if (!status) return <Badge variant="outline">Unknown</Badge>
    switch (status.status) {
      case 'online':
        return <Badge className="bg-green-100 text-green-800">Online</Badge>
      case 'offline':
        return <Badge className="bg-red-100 text-red-800">Offline</Badge>
      case 'error':
        return <Badge className="bg-orange-100 text-orange-800">Error</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  const formatUptime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-2">
          <div className={`p-2 rounded-full bg-gray-100 ${getStatusColor()}`}>
            {getStatusIcon()}
          </div>
          <div>
            <CardTitle className="text-lg">Gateway Status</CardTitle>
            <CardDescription>
              Real-time MCP Gateway connection status
            </CardDescription>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusBadge()}
          <Button
            variant="outline"
            size="sm"
            onClick={connected ? disconnect : connect}
            disabled={loading}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            {connected ? 'Disconnect' : 'Connect'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-center">
              <AlertCircle className="h-4 w-4 text-red-600 mr-2" />
              <span className="text-sm text-red-800">{error}</span>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-gray-400 mr-2" />
            <span className="text-gray-500">Checking gateway status...</span>
          </div>
        ) : status ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm font-medium text-gray-500">Status</div>
                <div className="text-lg font-semibold">{getStatusBadge()}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Version</div>
                <div className="text-lg font-semibold">{status.version}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Uptime</div>
                <div className="text-lg font-semibold">{formatUptime(status.uptime)}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Last Check</div>
                <div className="text-lg font-semibold">
                  {new Date(status.lastCheck).toLocaleTimeString()}
                </div>
              </div>
            </div>

            <div className="pt-2 border-t">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-500">
                  Connection Status
                </div>
                <div className={`text-sm font-medium ${connected ? 'text-green-600' : 'text-red-600'}`}>
                  {connected ? 'Connected' : 'Disconnected'}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <Activity className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500">No gateway status available</p>
              <Button
                variant="outline"
                size="sm"
                onClick={fetchStatus}
                className="mt-2"
              >
                Check Status
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
