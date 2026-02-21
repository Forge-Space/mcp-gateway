'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Progress } from '@/components/ui/progress'
import {
  Server,
  Plus,
  Trash2,
  Edit,
  Play,
  Pause,
  RotateCcw,
  Settings,
  Activity,
  CheckCircle,
  XCircle,
  AlertCircle,
  Zap,
  Clock,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Monitor,
  Database,
  Globe,
  Shield,
  Cpu,
  HardDrive,
  Network,
  RefreshCw,
  Download,
  Upload,
  Filter,
  Search,
  Bell,
  BellOff,
  Maximize2,
  Minimize2,
  X
} from 'lucide-react'

interface VirtualServer {
  id: string
  name: string
  enabled: boolean
  gateways: string[]
  description: string
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping'
  cpuUsage: number
  memoryUsage: number
  uptime: string
  lastRestart: string
  healthScore: number
  aiOptimized: boolean
  autoScaling: boolean
  replicas: number
  createdAt: string
  updatedAt: string
}

interface ServerMetrics {
  totalServers: number
  runningServers: number
  stoppedServers: number
  errorServers: number
  avgCpuUsage: number
  avgMemoryUsage: number
  avgHealthScore: number
  totalRequests: number
  avgResponseTime: number
}

interface DeploymentConfig {
  clusterName: string
  namespace: string
  replicas: number
  image: string
  port: number
  resources: {
    cpu: string
    memory: string
  }
  environment: Record<string, string>
  autoScaling: {
    enabled: boolean
    minReplicas: number
    maxReplicas: number
    targetCpuUtilization: number
  }
  healthChecks: {
    enabled: boolean
    path: string
    interval: number
    timeout: number
  }
}

export default function EnhancedServerManagement() {
  const [servers, setServers] = useState<VirtualServer[]>([])
  const [metrics, setMetrics] = useState<ServerMetrics | null>(null)
  const [selectedServer, setSelectedServer] = useState<VirtualServer | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showDeployModal, setShowDeployModal] = useState(false)
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(5000)

  // Mock data for demonstration
  useEffect(() => {
    const mockServers: VirtualServer[] = [
    {
      id: 'cursor-default',
      name: 'Cursor Default',
      enabled: true,
      gateways: ['sequential-thinking', 'filesystem', 'tavily'],
      description: 'Default cursor server with AI-enhanced tool selection',
      status: 'running',
      cpuUsage: 45,
      memoryUsage: 62,
      uptime: '2d 14h 32m',
      lastRestart: '2025-02-16T10:30:00Z',
      healthScore: 95,
      aiOptimized: true,
      autoScaling: true,
      replicas: 2,
      createdAt: '2025-02-14T09:00:00Z',
      updatedAt: '2025-02-18T15:45:00Z'
    },
    {
      id: 'cursor-router',
      name: 'Cursor Router',
      enabled: true,
      gateways: ['tool-router', 'github'],
      description: 'Optimized routing server with enhanced AI selection',
      status: 'running',
      cpuUsage: 38,
      memoryUsage: 55,
      uptime: '1d 8h 15m',
      lastRestart: '2025-02-17T12:15:00Z',
      healthScore: 92,
      aiOptimized: true,
      autoScaling: false,
      replicas: 1,
      createdAt: '2025-02-15T14:30:00Z',
      updatedAt: '2025-02-18T09:20:00Z'
    },
    {
      id: 'cursor-disabled',
      name: 'Cursor Disabled',
      enabled: false,
      gateways: ['playwright', 'chrome-devtools'],
      description: 'Browser automation server (currently disabled)',
      status: 'stopped',
      cpuUsage: 0,
      memoryUsage: 0,
      uptime: '0s',
      lastRestart: '2025-02-16T08:00:00Z',
      healthScore: 0,
      aiOptimized: false,
      autoScaling: false,
      replicas: 0,
      createdAt: '2025-02-14T11:00:00Z',
      updatedAt: '2025-02-16T08:00:00Z'
    },
    {
      id: 'legacy-server',
      name: 'Legacy Server',
      enabled: true,
      gateways: ['tool-router', 'github'],
      description: 'Legacy server for backward compatibility',
      status: 'running',
      cpuUsage: 28,
      memoryUsage: 41,
      uptime: '3d 2h 18m',
      lastRestart: '2025-02-15T16:45:00Z',
      healthScore: 88,
      aiOptimized: false,
      autoScaling: false,
      replicas: 1,
      createdAt: '2025-02-13T10:00:00Z',
      updatedAt: '2025-02-17T14:30:00Z'
    }
  ]

  const mockMetrics: ServerMetrics = {
    totalServers: mockServers.length,
    runningServers: mockServers.filter(s => s.status === 'running').length,
    stoppedServers: mockServers.filter(s => s.status === 'stopped').length,
    errorServers: mockServers.filter(s => s.status === 'error').length,
    avgCpuUsage: mockServers.reduce((sum, s) => sum + s.cpuUsage, 0) / mockServers.length,
    avgMemoryUsage: mockServers.reduce((sum, s) => sum + s.memoryUsage, 0) / mockServers.length,
    avgHealthScore: mockServers.reduce((sum, s) => sum + s.healthScore, 0) / mockServers.length,
    totalRequests: 15420,
    avgResponseTime: 245
  }

  setServers(mockServers)
  setMetrics(mockMetrics)
  setLoading(false)
  }, [])

  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      // Simulate real-time updates
      setServers(prev => prev.map(server => ({
        ...server,
        cpuUsage: Math.max(0, Math.min(100, server.cpuUsage + (Math.random() - 0.5) * 10)),
        memoryUsage: Math.max(0, Math.min(100, server.memoryUsage + (Math.random() - 0.5) * 8)),
        healthScore: Math.max(0, Math.min(100, server.healthScore + (Math.random() - 0.5) * 5))
      })))
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval])

  const handleServerAction = async (serverId: string, action: string) => {
    setServers(prev => prev.map(server => {
      if (server.id === serverId) {
        switch (action) {
          case 'start':
            return { ...server, status: 'starting' }
          case 'stop':
            return { ...server, status: 'stopping' }
          case 'restart':
            return { ...server, status: 'starting' }
          case 'toggle':
            return { ...server, enabled: !server.enabled }
          default:
            return server
        }
      }
      return server
    }))

    // Simulate action completion
    setTimeout(() => {
      setServers(prev => prev.map(server => {
        if (server.id === serverId) {
          switch (action) {
            case 'start':
            case 'restart':
              return { ...server, status: 'running', lastRestart: new Date().toISOString() }
            case 'stop':
              return { ...server, status: 'stopped', cpuUsage: 0, memoryUsage: 0 }
            default:
              return server
          }
        }
        return server
      }))
    }, 2000)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'stopped':
        return <XCircle className="w-4 h-4 text-gray-500" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'starting':
      case 'stopping':
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-500'
      case 'stopped':
        return 'bg-gray-500'
      case 'error':
        return 'bg-red-500'
      case 'starting':
      case 'stopping':
        return 'bg-blue-500'
      default:
        return 'bg-gray-400'
    }
  }

  const getHealthColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Enhanced Server Management</h2>
          <p className="text-muted-foreground">
            Manage virtual servers with AI optimization and auto-scaling
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Switch
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
            />
            <span className="text-sm">Auto-refresh</span>
          </div>
          <Button
            variant="outline"
            onClick={() => setShowDeployModal(true)}
            className="flex items-center gap-2"
          >
            <Upload className="w-4 h-4" />
            Deploy Service
          </Button>
          <Button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create Server
          </Button>
        </div>
      </div>

      {/* Metrics Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Servers</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.totalServers}</div>
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>{metrics.runningServers} running</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                  <span>{metrics.stoppedServers} stopped</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Average Health</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.avgHealthScore.toFixed(1)}%</div>
              <Progress value={metrics.avgHealthScore} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Resource Usage</CardTitle>
              <Cpu className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">CPU</span>
                  <span className="text-sm font-medium">{metrics.avgCpuUsage.toFixed(1)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Memory</span>
                  <span className="text-sm font-medium">{metrics.avgMemoryUsage.toFixed(1)}%</span>
                </div>
                <Progress value={(metrics.avgCpuUsage + metrics.avgMemoryUsage) / 2} className="mt-2" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Performance</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Requests</span>
                  <span className="text-sm font-medium">{metrics.totalRequests.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Avg Response</span>
                  <span className="text-sm font-medium">{metrics.avgResponseTime}ms</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Server List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            Virtual Servers
          </CardTitle>
          <CardDescription>
            Manage and monitor virtual server instances
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {servers.map((server) => (
              <div
                key={server.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  {getStatusIcon(server.status)}
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium">{server.name}</h3>
                      <Badge variant={server.enabled ? "default" : "secondary"}>
                        {server.enabled ? "Enabled" : "Disabled"}
                      </Badge>
                      {server.aiOptimized && (
                        <Badge variant="outline" className="text-purple-600">
                          <Zap className="w-3 h-3 mr-1" />
                          AI Optimized
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{server.description}</p>
                    <div className="flex items-center space-x-4 mt-1">
                      <span className="text-xs text-muted-foreground">
                        Gateways: {server.gateways.join(', ')}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Replicas: {server.replicas}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">CPU:</span>
                      <Progress value={server.cpuUsage} className="w-16 h-2" />
                      <span className="text-sm w-8">{server.cpuUsage}%</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">Memory:</span>
                      <Progress value={server.memoryUsage} className="w-16 h-2" />
                      <span className="text-sm w-8">{server.memoryUsage}%</span>
                    </div>
                    <div className="text-right">
                      <div className={`text-sm font-medium ${getHealthColor(server.healthScore)}`}>
                        Health: {server.healthScore}%
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Uptime: {server.uptime}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {server.status === 'running' ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleServerAction(server.id, 'restart')}
                      >
                        <RotateCcw className="w-4 h-4" />
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleServerAction(server.id, 'start')}
                      >
                        <Play className="w-4 h-4" />
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleServerAction(server.id, 'toggle')}
                    >
                      {server.enabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedServer(server)}
                    >
                      <Settings className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Kubernetes Deployment Modal */}
      {showDeployModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Deploy to Kubernetes</h3>
              <Button
                variant="outline"
                onClick={() => setShowDeployModal(false)}
              >
                ×
              </Button>
            </div>
            <div className="text-center py-8">
              <Server className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h4 className="text-lg font-medium mb-2">Kubernetes Deployment</h4>
              <p className="text-muted-foreground mb-4">
                Kubernetes deployment is not available. The MCP Gateway uses Docker Compose for optimal simplicity and efficiency.
              </p>
              <div className="space-y-2 text-sm text-left max-w-md mx-auto">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Docker Compose provides simpler deployment</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>60-80% memory reduction with sleep/wake</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>Better suited for individual developers</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
