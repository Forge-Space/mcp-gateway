'use client'

import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Bell,
  Clock,
  Info,
  Pause,
  RefreshCw,
  Wifi,
  WifiOff,
  XCircle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Zap,
  Server,
  HardDrive,
  MemoryStick,
  Cpu,
  Network
} from 'lucide-react'

interface ServiceMetrics {
  name: string
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping' | 'sleeping'
  cpu: number
  memory: number
  disk: number
  network: {
    inbound: number
    outbound: number
  }
  uptime: number
  responseTime: number
  errorRate: number
  requests: number
}

interface Alert {
  id: string
  level: 'info' | 'warning' | 'error' | 'critical'
  message: string
  service: string
  timestamp: Date
  resolved: boolean
  acknowledged: boolean
}

interface RealTimeMetrics {
  timestamp: Date
  services: ServiceMetrics[]
  alerts: Alert[]
  systemHealth: {
    overall: number
    cpu: number
    memory: number
    disk: number
    network: number
  }
}

interface MonitoringConfig {
  refreshRate: number
  autoRefresh: boolean
  showOnlyActive: boolean
  alertLevel: 'all' | 'warning' | 'error' | 'critical'
  timeRange: '1m' | '5m' | '15m' | '1h' | '6h' | '24h'
  services: string[]
}

// Helper function to create mock timestamps
const createMockTimestamp = (minutesAgo: number) => new Date(Date.now() - minutesAgo * 60000)

// Mock data for demonstration
const createMockMetrics = (): RealTimeMetrics => ({
  timestamp: new Date(),
  services: [
    {
      name: 'Gateway API',
      status: 'running',
      cpu: 45.2,
      memory: 67.8,
      disk: 23.4,
      network: { inbound: 125000, outbound: 89000 },
      uptime: 86400,
      responseTime: 120,
      errorRate: 0.1,
      requests: 12500
    },
    {
      name: 'Tool Router',
      status: 'running',
      cpu: 32.1,
      memory: 45.6,
      disk: 18.9,
      network: { inbound: 67000, outbound: 45000 },
      uptime: 86400,
      responseTime: 85,
      errorRate: 0.05,
      requests: 8900
    },
    {
      name: 'RAG Manager',
      status: 'running',
      cpu: 78.3,
      memory: 89.2,
      disk: 45.7,
      network: { inbound: 234000, outbound: 156000 },
      uptime: 43200,
      responseTime: 200,
      errorRate: 0.2,
      requests: 3400
    }
  ],
  alerts: [
    {
      id: '1',
      level: 'warning',
      message: 'High CPU usage on RAG Manager',
      service: 'RAG Manager',
      timestamp: createMockTimestamp(5),
      resolved: false,
      acknowledged: false
    },
    {
      id: '2',
      level: 'info',
      message: 'Service health check completed',
      service: 'Gateway API',
      timestamp: createMockTimestamp(10),
      resolved: true,
      acknowledged: true
    }
  ],
  systemHealth: {
    overall: 85.4,
    cpu: 52.0,
    memory: 67.5,
    disk: 29.3,
    network: 78.9
  }
})

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

  // Mock data for demonstration
  const mockMetrics = createMockMetrics()

  useEffect(() => {
    // Simulate real-time data updates
    const interval = setInterval(() => {
      setMetrics(mockMetrics)
      setIsConnected(true)
    }, config.refreshRate)

    return () => clearInterval(interval)
  }, [config.refreshRate])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'stopped':
        return <XCircle className="w-4 h-4 text-gray-500" />
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />
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
            Monitor system performance and service health in real-time
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Switch
            checked={config.autoRefresh}
            onCheckedChange={(checked) => setConfig({ ...config, autoRefresh: checked })}
          />
          <Label>Auto Refresh</Label>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setExpandedView(!expandedView)}
          >
            {expandedView ? 'Compact' : 'Expand'}
          </Button>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Health</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getHealthColor(metrics?.systemHealth.overall || 0)}`}>
              {metrics?.systemHealth.overall.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              System performance score
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.systemHealth.cpu.toFixed(1)}%</div>
            <Progress value={metrics?.systemHealth.cpu} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
            <MemoryStick className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.systemHealth.memory.toFixed(1)}%</div>
            <Progress value={metrics?.systemHealth.memory} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.systemHealth.disk.toFixed(1)}%</div>
            <Progress value={metrics?.systemHealth.disk} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Network I/O</CardTitle>
            <Network className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.systemHealth.network.toFixed(1)}%</div>
            <Progress value={metrics?.systemHealth.network} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* Alerts Section */}
      {criticalAlerts.length > 0 && (
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="text-red-600 flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              Critical Alerts ({criticalAlerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {criticalAlerts.map(alert => (
                <div key={alert.id} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    {getAlertIcon(alert.level)}
                    <div>
                      <p className="font-medium">{alert.message}</p>
                      <p className="text-sm text-muted-foreground">{alert.service}</p>
                    </div>
                  </div>
                  <Badge variant="destructive">{alert.level}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Services Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredServices.map(service => (
          <Card key={service.name} className="cursor-pointer hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(service.status)}
                  <CardTitle className="text-lg">{service.name}</CardTitle>
                </div>
                <Badge className={getStatusColor(service.status)}>
                  {service.status}
                </Badge>
              </div>
              <CardDescription>
                Uptime: {Math.floor(service.uptime / 3600)}h {Math.floor((service.uptime % 3600) / 60)}m
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm">CPU</span>
                  <div className="flex items-center gap-2">
                    <Progress value={service.cpu} className="w-16" />
                    <span className="text-sm font-medium">{service.cpu.toFixed(1)}%</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Memory</span>
                  <div className="flex items-center gap-2">
                    <Progress value={service.memory} className="w-16" />
                    <span className="text-sm font-medium">{service.memory.toFixed(1)}%</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Response Time</span>
                  <span className="text-sm font-medium">{service.responseTime}ms</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Requests/min</span>
                  <span className="text-sm font-medium">{Math.floor(service.requests / 60)}</span>
                </div>
                {service.errorRate > 0 && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-red-600">Error Rate</span>
                    <span className="text-sm font-medium text-red-600">{service.errorRate.toFixed(2)}%</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
