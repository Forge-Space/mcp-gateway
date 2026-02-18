'use client'

import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useGatewayStore } from '@/lib/mcp-gateway'
import { Server, Activity, Cpu, HardDrive, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export function ServerMetrics() {
  const { servers, connected, fetchServers } = useGatewayStore()

  useEffect(() => {
    if (connected) {
      fetchServers()

      // Set up polling for real-time updates
      const interval = setInterval(fetchServers, 10000) // 10 seconds

      return () => clearInterval(interval)
    }
  }, [connected, fetchServers])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Server className="h-4 w-4" />
      case 'stopped':
        return <Activity className="h-4 w-4" />
      case 'error':
        return <AlertTriangle className="h-4 w-4" />
      default:
        return <Server className="h-4 w-4" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-800'
      case 'stopped':
        return 'bg-gray-100 text-gray-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
  }

  const getPerformanceIcon = (cpu: number, memory: number) => {
    if (cpu > 80 || memory > 80) return <TrendingUp className="h-4 w-4" />
    if (cpu < 20 && memory < 20) return <TrendingDown className="h-4 w-4" />
    return <Activity className="h-4 w-4" />
  }

  const getPerformanceColor = (cpu: number, memory: number) => {
    if (cpu > 80 || memory > 80) return 'text-red-600'
    if (cpu < 20 && memory < 20) return 'text-green-600'
    return 'text-yellow-600'
  }

  const chartData = servers.map(server => ({
    name: server.name,
    cpu: server.cpu,
    memory: server.memory,
    requests: server.requests,
    errors: server.errors,
  }))

  const totalRequests = servers.reduce((sum, server) => sum + server.requests, 0)
  const totalErrors = servers.reduce((sum, server) => sum + server.errors, 0)
  const avgCpu = servers.length > 0 ? servers.reduce((sum, server) => sum + server.cpu, 0) / servers.length : 0
  const avgMemory = servers.length > 0 ? servers.reduce((sum, server) => sum + server.memory, 0) / servers.length : 0

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle className="text-lg">Server Metrics</CardTitle>
          <CardDescription>
            Real-time server performance and activity monitoring
          </CardDescription>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={connected ? "default" : "outline"}>
            {servers.length} Servers
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchServers}
            disabled={!connected}
          >
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {!connected ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <Server className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500">Connect to gateway to view server metrics</p>
            </div>
          </div>
        ) : servers.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <Activity className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500">No servers available</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-4 gap-4">
              <div>
                <div className="text-sm font-medium text-gray-500">Total Requests</div>
                <div className="text-2xl font-bold">{totalRequests.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Total Errors</div>
                <div className="text-2xl font-bold text-red-600">{totalErrors.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Avg CPU</div>
                <div className="text-2xl font-bold">{avgCpu.toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Avg Memory</div>
                <div className="text-2xl font-bold">{avgMemory.toFixed(1)}%</div>
              </div>
            </div>

            {/* Performance Chart */}
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-4">Performance Overview</h4>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="cpu" fill="#8884d8" name="CPU %" />
                  <Bar dataKey="memory" fill="#82ca9d" name="Memory %" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Server List */}
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-4">Server Details</h4>
              <div className="space-y-3">
                {servers.map((server) => (
                  <div
                    key={server.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-full ${getStatusColor(server.status)}`}>
                        {getStatusIcon(server.status)}
                      </div>
                      <div>
                        <div className="font-medium">{server.name}</div>
                        <div className="text-sm text-gray-500">
                          Last activity: {new Date(server.lastActivity).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <div className="text-sm text-gray-500">CPU</div>
                        <div className={`font-medium ${getPerformanceColor(server.cpu, server.memory)}`}>
                          {server.cpu.toFixed(1)}%
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-500">Memory</div>
                        <div className={`font-medium ${getPerformanceColor(server.cpu, server.memory)}`}>
                          {server.memory.toFixed(1)}%
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-500">Requests</div>
                        <div className="font-medium">{server.requests}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-500">Errors</div>
                        <div className={`font-medium ${server.errors > 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {server.errors}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
