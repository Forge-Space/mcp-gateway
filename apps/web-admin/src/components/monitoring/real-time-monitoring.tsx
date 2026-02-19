'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Cpu,
  Database,
  Globe,
  HardDrive,
  Monitor,
  Network,
  Pause,
  Play,
  RefreshCw,
  Settings,
  TrendingDown,
  TrendingUp,
  Zap,
  BarChart3,
  LineChart,
  AlertCircle,
  Wifi,
  WifiOff,
  Server,
  Shield,
  Eye,
  EyeOff,
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

interface RealTimeMetrics {
  timestamp: string
  system: {
    cpu: number
    memory: number
    disk: number
    network: {
      inbound: number
      outbound: number
    }
    uptime: string
  }
  services: ServiceMetrics[]
  alerts: Alert[]
  performance: {
    avgResponseTime: number
    requestsPerSecond: number
    errorRate: number
    throughput: number
  }
}

interface ServiceMetrics {
  id: string
  name: string
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping' | 'sleeping'
  cpu: number
  memory: number
  disk: number
  network: {
    inbound: number
    outbound: number
  }
  uptime: string
  lastRestart: string
  healthScore: number
  requests: number
  errors: number
  avgResponseTime: number
  replicas: number
  autoScaling: boolean
}

interface Alert {
  id: string
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'critical'
  title: string
  message: string
  service?: string
  resolved: boolean
  acknowledged: boolean
}

interface MonitoringConfig {
  refreshRate: number
  autoRefresh: boolean
  showOnlyActive: boolean
  alertLevel: 'all' | 'warning' | 'error' | 'critical'
  timeRange: '1m' | '5m' | '15m' | '1h' | '6h' | '24h'
  services: string[]
}

export default function RealTimeMonitoring() {
  const [metrics, setMetrics] = useState<RealTimeMetrics | null>(null)
  const [config, setConfig] = useState<MonitoringConfig>({
    refreshRate: 5000,
    autoRefresh: true,
    showOnlyActive: false,
    alertLevel: 'warning',
    timeRange: '15m',
    services: []
  })
  const [isConnected, setIsConnected] = useState(false)
  const [selectedService, setSelectedService] = useState<string | null>(null)
  const [showAlerts, setShowAlerts] = useState(true)
  const [expandedView, setExpandedView] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Mock WebSocket connection for demonstration
  useEffect(() => {
    const connectWebSocket = () => {
      // In a real implementation, this would connect to a WebSocket endpoint
      // For now, we'll simulate the connection with polling
      setIsConnected(true)
      
      // Simulate real-time updates
      if (config.autoRefresh) {
        const interval = setInterval(() => {
          generateMockMetrics()
        }, config.refreshRate)
        
        return () => clearInterval(interval)
      }
    }

    const cleanup = connectWebSocket()
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      cleanup?.()
    }
  }, [config.autoRefresh, config.refreshRate])

  const generateMockMetrics = useCallback(() => {
    const mockServices: ServiceMetrics[] = [
      {
        id: 'gateway',
        name: 'Gateway',
        status: 'running',
        cpu: 25 + Math.random() * 15,
        memory: 35 + Math.random() * 20,
        disk: 15 + Math.random() * 10,
        network: {
          inbound: 1000 + Math.random() * 500,
          outbound: 800 + Math.random() * 400
        },
        uptime: '2d 14h 32m',
        lastRestart: '2025-02-16T10:30:00Z',
        healthScore: 95 + Math.random() * 5,
        requests: 15420 + Math.floor(Math.random() * 1000),
        errors: Math.floor(Math.random() * 10),
        avgResponseTime: 200 + Math.random() * 100,
        replicas: 1,
        autoScaling: false
      },
      {
        id: 'service-manager',
        name: 'Service Manager',
        status: 'running',
        cpu: 15 + Math.random() * 10,
        memory: 25 + Math.random() * 15,
        disk: 5 + Math.random() * 5,
        network: {
          inbound: 500 + Math.random() * 200,
          outbound: 400 + Math.random() * 200
        },
        uptime: '2d 14h 32m',
        lastRestart: '2025-02-16T10:30:00Z',
        healthScore: 98 + Math.random() * 2,
        requests: 8200 + Math.floor(Math.random() * 500),
        errors: Math.floor(Math.random() * 5),
        avgResponseTime: 150 + Math.random() * 50,
        replicas: 1,
        autoScaling: false
      },
      {
        id: 'tool-router',
        name: 'Tool Router',
        status: 'running',
        cpu: 30 + Math.random() * 20,
        memory: 40 + Math.random() * 25,
        disk: 10 + Math.random() * 8,
        network: {
          inbound: 2000 + Math.random() * 800,
          outbound: 1800 + Math.random() * 600
        },
        uptime: '2d 14h 32m',
        lastRestart: '2025-02-16T10:30:00Z',
        healthScore: 92 + Math.random() * 8,
        requests: 25800 + Math.floor(Math.random() * 2000),
        errors: Math.floor(Math.random() * 20),
        avgResponseTime: 250 + Math.random() * 150,
        replicas: 2,
        autoScaling: true
      },
      {
        id: 'translate',
        name: 'Translate Services',
        status: 'running',
        cpu: 20 + Math.random() * 15,
        memory: 30 + Math.random() * 20,
        disk: 8 + Math.random() * 6,
        network: {
          inbound: 800 + Math.random() * 300,
          outbound: 600 + Math.random() * 250
        },
        uptime: '2d 14h 32m',
        lastRestart: '2025-02-16T10:30:00Z',
        healthScore: 88 + Math.random() * 10,
        requests: 12000 + Math.floor(Math.random() * 1000),
        errors: Math.floor(Math.random() * 15),
        avgResponseTime: 180 + Math.random() * 80,
        replicas: 3,
        autoScaling: true
      },
      {
        id: 'cursor-default',
        name: 'Cursor Default',
        status: Math.random() > 0.8 ? 'sleeping' : 'running',
        cpu: Math.random() > 0.8 ? 2 : 35 + Math.random() * 20,
        memory: Math.random() > 0.8 ? 8 : 45 + Math.random() * 25,
        disk: 12 + Math.random() * 8,
        network: {
          inbound: 600 + Math.random() * 200,
          outbound: 500 + Math.random() * 200
        },
        uptime: '2d 14h 32m',
        lastRestart: '2025-02-16T10:30:00Z',
        healthScore: Math.random() > 0.8 ? 85 : 94 + Math.random() * 6,
        requests: 9800 + Math.floor(Math.random() * 800),
        errors: Math.floor(Math.random() * 10),
        avgResponseTime: 220 + Math.random() * 100,
        replicas: 2,
        autoScaling: true
      },
      {
        id: 'cursor-router',
        name: 'Cursor Router',
        status: 'running',
        cpu: 25 + Math.random() * 15,
        memory: 35 + Math.random() * 20,
        disk: 10 + Math.random() * 6,
        network: {
          inbound: 400 + Math.random() * 150,
          outbound: 350 + Math.random() * 150
        },
        uptime: '2d 14h 32m',
        lastRestart: '2025-02-16T10:30:00Z',
        healthScore: 90 + Math.random() * 8,
        requests: 6500 + Math.floor(Math.random() * 500),
        errors: Math.floor(Math.random() * 8),
        avgResponseTime: 190 + Math.random() * 90,
        replicas: 1,
        autoScaling: false
      }
    ]

    const mockAlerts: Alert[] = [
      {
        id: '1',
        timestamp: new Date().toISOString(),
        level: 'warning',
        title: 'High CPU Usage',
        message: 'Tool Router CPU usage exceeded 80%',
        service: 'tool-router',
        resolved: false,
        acknowledged: false
      },
      {
        id: '2',
        timestamp: new Date().toISOString(),
        level: 'info',
        title: 'Service Auto-scaled',
        message: 'Translate Services auto-scaled to 3 replicas',
        service: 'translate',
        resolved: true,
        acknowledged: true
      }
    ]

    const filteredServices = config.services.length > 0 
      ? mockServices.filter(s => config.services.includes(s.id))
      : mockServices

    const filteredAlerts = mockAlerts.filter(alert => {
      if (config.alertLevel === 'all') return true
      if (config.alertLevel === 'warning') return alert.level === 'warning' || alert.level === 'error' || alert.level === 'critical'
      if (config.alertLevel === 'error') return alert.level === 'error' || alert.level === 'critical'
      if (config.alertLevel === 'critical') return alert.level === 'critical'
      return true
    })

    setMetrics({
      timestamp: new Date().toISOString(),
      system: {
        cpu: filteredServices.reduce((sum, s) => sum + s.cpu, 0) / filteredServices.length,
        memory: filteredServices.reduce((sum, s) => sum + s.memory, 0) / filteredServices.length,
        disk: filteredServices.reduce((sum, s) => sum + s.disk, 0) / filteredServices.length,
        network: {
          inbound: filteredServices.reduce((sum, s) => sum + s.network.inbound, 0),
          outbound: filteredServices.reduce((sum, s) => sum + s.network.outbound, 0)
        },
        uptime: '2d 14h 32m'
      },
      services: filteredServices,
      alerts: filteredAlerts,
      performance: {
        avgResponseTime: filteredServices.reduce((sum, s) => sum + s.avgResponseTime, 0) / filteredServices.length,
        requestsPerSecond: filteredServices.reduce((sum, s) => sum + s.requests, 0) / 60,
        errorRate: filteredServices.reduce((sum, s) => sum + s.errors, 0) / filteredServices.reduce((sum, s) => sum + s.requests, 0) * 100,
        throughput: filteredServices.reduce((sum, s) => sum + s.requests, 0)
      }
    })
  }, [config.services, config.alertLevel])

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
      case 'sleeping':
        return <Pause className="w-4 h-4 text-yellow-500" />
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
      case 'sleeping':
        return 'bg-yellow-500'
      default:
        return 'bg-gray-400'
    }
  }

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'info':
        return <Info className="w-4 h-4 text-blue-500" />
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      default:
        return <Bell className="w-4 h-4 text-gray-500" />
    }
  }

  const getHealthColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  const filteredServices = metrics?.services?.filter(service => 
    !config.showOnlyActive || service.status === 'running'
  ).filter(service =>
    !searchTerm || service.name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  const activeAlerts = metrics?.alerts?.filter(alert => !alert.resolved) || []
  const criticalAlerts = activeAlerts.filter(alert => alert.level === 'critical')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            Real-time Monitoring
            {isConnected ? (
              <Wifi className="w-5 h-5 text-green-500" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-500" />
            )}
          </h2>
          <p className="text-muted-foreground">
            Live system metrics and performance monitoring
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Switch
              checked={config.autoRefresh}
              onCheckedChange={(checked) => setConfig(prev => ({ ...prev, autoRefresh: checked }))}
            />
            <span className="text-sm">Auto-refresh</span>
          </div>
          <div className="flex items-center space-x-2">
            <Label htmlFor="refresh-rate" className="text-sm">Refresh:</Label>
            <Select
              value={config.refreshRate.toString()}
              onValueChange={(value) => setConfig(prev => ({ ...prev, refreshRate: parseInt(value) }))}
            >
              <option value="1000">1s</option>
              <option value="5000">5s</option>
              <option value="10000">10s</option>
              <option value="30000">30s</option>
            </Select>
          </div>
          <Button
            variant="outline"
            onClick={() => generateMockMetrics()}
            className="flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
          <Button
            variant="outline"
            onClick={() => setExpandedView(!expandedView)}
            className="flex items-center gap-2"
          >
            {expandedView ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            {expandedView ? 'Compact' : 'Expanded'}
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {(criticalAlerts.length > 0 || activeAlerts.length > 0) && (
        <Card className={criticalAlerts.length > 0 ? 'border-red-200' : 'border-yellow-200'}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Bell className="w-5 h-5" />
                Active Alerts
                <Badge variant={criticalAlerts.length > 0 ? 'destructive' : 'secondary'}>
                  {activeAlerts.length}
                </Badge>
              </CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowAlerts(!showAlerts)}
              >
                {showAlerts ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
            </div>
          </CardHeader>
          {showAlerts && (
            <CardContent>
              <div className="space-y-2">
                {activeAlerts.slice(0, 5).map((alert) => (
                  <div
                    key={alert.id}
                    className={`flex items-start space-x-3 p-3 rounded-lg border ${
                      alert.level === 'critical' ? 'border-red-200 bg-red-50' :
                      alert.level === 'error' ? 'border-red-200 bg-red-50' :
                      alert.level === 'warning' ? 'border-yellow-200 bg-yellow-50' :
                      'border-blue-200 bg-blue-50'
                    }`}
                  >
                    {getAlertIcon(alert.level)}
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">{alert.title}</h4>
                        <Badge variant="outline" className="text-xs">
                          {alert.service || 'System'}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        {alert.message}
                      </p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-muted-foreground">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </span>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              // In a real implementation, this would acknowledge the alert
                              console.log('Acknowledge alert:', alert.id)
                            }}
                          >
                            Acknowledge
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              // In a real implementation, this would resolve the alert
                              console.log('Resolve alert:', alert.id)
                            }}
                          >
                            Resolve
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {activeAlerts.length > 5 && (
                  <div className="text-center text-sm text-muted-foreground py-2">
                    {activeAlerts.length - 5} more alerts...
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* System Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System CPU</CardTitle>
              <Cpu className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.system.cpu.toFixed(1)}%</div>
              <Progress value={metrics.system.cpu} className="mt-2" />
              <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
                <span>Usage</span>
                <span className={metrics.system.cpu > 80 ? 'text-red-500' : 'text-green-500'}>
                  {metrics.system.cpu > 80 ? 'High' : 'Normal'}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Memory</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.system.memory.toFixed(1)}%</div>
              <Progress value={metrics.system.memory} className="mt-2" />
              <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
                <span>Usage</span>
                <span className={metrics.system.memory > 80 ? 'text-red-500' : 'text-green-500'}>
                  {metrics.system.memory > 80 ? 'High' : 'Normal'}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Network I/O</CardTitle>
              <Network className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Inbound</span>
                  <span className="text-sm font-medium">{(metrics.system.network.inbound / 1000).toFixed(1)}K/s</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Outbound</span>
                  <span className="text-sm font-medium">{(metrics.system.network.outbound / 1000).toFixed(1)}K/s</span>
                </div>
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
                  <span className="text-sm">Avg Response</span>
                  <span className="text-sm font-medium">{metrics.performance.avgResponseTime.toFixed(0)}ms</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Requests/s</span>
                  <span className="text-sm font-medium">{metrics.performance.requestsPerSecond.toFixed(1)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Error Rate</span>
                  <span className={`text-sm font-medium ${metrics.performance.errorRate > 5 ? 'text-red-500' : 'text-green-500'}`}>
                    {metrics.performance.errorRate.toFixed(1)}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Monitoring Controls
          </CardTitle>
          <CardDescription>
            Configure monitoring display and alert settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <Label htmlFor="show-only-active">Show Only Active Services</Label>
              <Switch
                id="show-only-active"
                checked={config.showOnlyActive}
                onCheckedChange={(checked) => setConfig(prev => ({ ...prev, showOnlyActive: checked }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="alert-level">Alert Level</Label>
              <Select
                value={config.alertLevel}
                onValueChange={(value) => setConfig(prev => ({ ...prev, alertLevel: value as any }))}
              >
                <option value="all">All Alerts</option>
                <option value="warning">Warning & Above</option>
                <option value="error">Error & Critical</option>
                <option value="critical">Critical Only</option>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="time-range">Time Range</Label>
              <Select
                value={config.timeRange}
                onValueChange={(value) => setConfig(prev => ({ ...prev, timeRange: value as any }))}
              >
                <option value="1m">Last Minute</option>
                <option value="5m">Last 5 Minutes</option>
                <option value="15m">Last 15 Minutes</option>
                <option value="1h">Last Hour</option>
                <option value="6h">Last 6 Hours</option>
                <option value="24h">Last 24 Hours</option>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Services List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              Services
              <Badge variant="secondary">
                {filteredServices.length} / {metrics?.services?.length || 0}
              </Badge>
            </div>
            <div className="flex items-center space-x-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search services..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 w-64"
                />
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => generateMockMetrics()}
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            Real-time service metrics and health status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredServices.map((service) => (
              <div
                key={service.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                onClick={() => setSelectedService(service.id === selectedService ? null : service.id)}
              >
                <div className="flex items-center space-x-4">
                  {getStatusIcon(service.status)}
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium">{service.name}</h3>
                      <Badge variant={service.status === 'running' ? 'default' : 'secondary'}>
                        {service.status}
                      </Badge>
                      {service.autoScaling && (
                        <Badge variant="outline" className="text-purple-600">
                          <Zap className="w-3 h-3 mr-1" />
                          Auto-scaling
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center space-x-4 mt-1 text-sm text-muted-foreground">
                      <span>Replicas: {service.replicas}</span>
                      <span>Uptime: {service.uptime}</span>
                      <span>Health: <span className={getHealthColor(service.healthScore)}>{service.healthScore}%</span></span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-6">
                  <div className="text-right">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-sm">CPU:</span>
                      <Progress value={service.cpu} className="w-16 h-2" />
                      <span className="text-sm w-8">{service.cpu.toFixed(1)}%</span>
                    </div>
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-sm">Memory:</span>
                      <Progress value={service.memory} className="w-16 h-2" />
                      <span className="text-sm w-8">{service.memory.toFixed(1)}%</span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">
                        R/s: {(service.requests / 60).toFixed(1)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {service.avgResponseTime.toFixed(0)}ms avg
                      </div>
                      {service.errors > 0 && (
                        <div className="text-xs text-red-500">
                          {service.errors} errors
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {selectedService === service.id && (
                  <div className="col-span-full mt-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium mb-2">Service Details: {service.name}</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Status:</span>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(service.status)}
                          <span>{service.status}</span>
                        </div>
                      </div>
                      <div>
                        <span className="font-medium">Last Restart:</span>
                        <div>{new Date(service.lastRestart).toLocaleString()}</div>
                      </div>
                      <div>
                        <span className="font-medium">Network In:</span>
                        <div>{(service.network.inbound / 1000).toFixed(1)}K/s</div>
                      </div>
                      <div>
                        <span className="font-medium">Network Out:</span>
                        <div>{(service.network.outbound / 1000).toFixed(1)}K/s</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Import missing icon
import { Info } from 'lucide-react'
