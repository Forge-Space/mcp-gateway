'use client';

import { cn } from '@/lib/utils';
import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Cpu,
  Database,
  Network,
  Pause,
  RefreshCw,
  Settings,
  Zap,
  BarChart3,
  AlertCircle,
  Info,
  Wifi,
  WifiOff,
  Server,
  Eye,
  EyeOff,
  XCircle,
  Search,
  Bell,
  Maximize2,
  Minimize2,
} from 'lucide-react';

interface RealTimeMetrics {
  timestamp: string;
  system: {
    cpu: number;
    memory: number;
    disk: number;
    network: {
      inbound: number;
      outbound: number;
    };
    uptime: string;
  };
  services: ServiceMetrics[];
  alerts: Alert[];
  performance: {
    avgResponseTime: number;
    requestsPerSecond: number;
    errorRate: number;
    throughput: number;
  };
}

interface ServiceMetrics {
  id: string;
  name: string;
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping' | 'sleeping';
  cpu: number;
  memory: number;
  disk: number;
  network: {
    inbound: number;
    outbound: number;
  };
  uptime: string;
  lastRestart: string;
  healthScore: number;
  requests: number;
  errors: number;
  avgResponseTime: number;
  replicas: number;
  autoScaling: boolean;
}

interface Alert {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  service?: string;
  resolved: boolean;
  acknowledged: boolean;
}

interface MonitoringConfig {
  refreshRate: number;
  autoRefresh: boolean;
  showOnlyActive: boolean;
  alertLevel: 'all' | 'warning' | 'error' | 'critical';
  timeRange: '1m' | '5m' | '15m' | '1h' | '6h' | '24h';
  services: string[];
}

type AlertLevel = MonitoringConfig['alertLevel'];
type TimeRange = MonitoringConfig['timeRange'];

const getAlertContainerClassName = (level: Alert['level']) =>
  cn({
    'border-red-200 bg-red-50': level === 'critical' || level === 'error',
    'border-yellow-200 bg-yellow-50': level === 'warning',
    'border-blue-200 bg-blue-50': level !== 'critical' && level !== 'error' && level !== 'warning',
  });

export default function RealTimeMonitoring() {
  const [metrics, setMetrics] = useState<RealTimeMetrics | null>(null);
  const [config, setConfig] = useState<MonitoringConfig>({
    refreshRate: 5000,
    autoRefresh: true,
    showOnlyActive: false,
    alertLevel: 'warning',
    timeRange: '15m',
    services: [],
  });
  const [isConnected, setIsConnected] = useState(false);
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [showAlerts, setShowAlerts] = useState(true);
  const [expandedView, setExpandedView] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const fetchRealMetrics = useCallback(async () => {
    try {
      const [perfRes, systemRes, cloudRes, aiRes] = await Promise.allSettled([
        fetch('/api/monitoring/performance'),
        fetch('/api/monitoring/system'),
        fetch('/api/cloud/health'),
        fetch('/api/ai/performance'),
      ]);

      const perf =
        perfRes.status === 'fulfilled' && perfRes.value.ok ? await perfRes.value.json() : null;
      const system =
        systemRes.status === 'fulfilled' && systemRes.value.ok
          ? await systemRes.value.json()
          : null;
      const cloud =
        cloudRes.status === 'fulfilled' && cloudRes.value.ok ? await cloudRes.value.json() : null;
      const ai = aiRes.status === 'fulfilled' && aiRes.value.ok ? await aiRes.value.json() : null;

      const uptimeSeconds: number = perf?.uptime_seconds ?? 0;
      const cacheHitRate: number = system?.cache_metrics?.cache_hit_rate ?? 0;
      const totalRequests: number = system?.cache_metrics?.total_requests ?? 0;
      const avgResponseTime: number = ai?.ai_selector?.average_response_time ?? 0;

      const services: ServiceMetrics[] = [];

      if (cloud?.providers) {
        for (const provider of cloud.providers) {
          const isHealthy = provider.status === 'healthy';
          const isDegraded = provider.status === 'degraded';
          services.push({
            id: `cloud-${provider.name}`,
            name: `Cloud: ${provider.name}`,
            status: isHealthy ? 'running' : isDegraded ? 'sleeping' : 'error',
            cpu: provider.metrics?.error_rate != null ? provider.metrics.error_rate * 100 : 0,
            memory: cacheHitRate * 100,
            disk: 0,
            network: {
              inbound: provider.metrics?.total_requests ?? 0,
              outbound: provider.metrics?.total_requests ?? 0,
            },
            uptime: formatUptime(uptimeSeconds),
            lastRestart: new Date(Date.now() - uptimeSeconds * 1000).toISOString(),
            healthScore: isHealthy ? 99 : isDegraded ? 70 : 30,
            requests: provider.metrics?.total_requests ?? 0,
            errors: provider.metrics?.total_failures ?? 0,
            avgResponseTime: provider.metrics?.avg_latency_ms ?? 0,
            replicas: 1,
            autoScaling: false,
          });
        }
      }

      if (ai?.providers) {
        for (const provider of ai.providers) {
          const isHealthy = provider.status === 'healthy';
          const isWarning = provider.status === 'warning';
          services.push({
            id: `ai-${provider.name}`,
            name: `AI: ${provider.name}`,
            status: isHealthy ? 'running' : isWarning ? 'sleeping' : 'error',
            cpu: 0,
            memory: 0,
            disk: 0,
            network: { inbound: provider.total_requests ?? 0, outbound: 0 },
            uptime: formatUptime(uptimeSeconds),
            lastRestart: new Date(Date.now() - uptimeSeconds * 1000).toISOString(),
            healthScore: isHealthy ? 99 : isWarning ? 80 : 50,
            requests: provider.total_requests ?? 0,
            errors: Math.round((provider.total_requests ?? 0) * (1 - (provider.success_rate ?? 1))),
            avgResponseTime: provider.average_response_time ?? 0,
            replicas: 1,
            autoScaling: false,
          });
        }
      }

      if (services.length === 0) {
        services.push({
          id: 'gateway',
          name: 'MCP Gateway',
          status: 'running',
          cpu: cacheHitRate * 100,
          memory: cacheHitRate * 100,
          disk: 0,
          network: { inbound: totalRequests, outbound: totalRequests },
          uptime: formatUptime(uptimeSeconds),
          lastRestart: new Date(Date.now() - uptimeSeconds * 1000).toISOString(),
          healthScore: cacheHitRate >= 0.9 ? 99 : cacheHitRate >= 0.7 ? 80 : 60,
          requests: totalRequests,
          errors: 0,
          avgResponseTime: avgResponseTime,
          replicas: 1,
          autoScaling: false,
        });
      }

      const recommendations: string[] = perf?.recommendations ?? [];
      const cloudWarnings: string[] =
        cloud?.providers
          ?.filter((p: { status: string }) => p.status !== 'healthy')
          .map(
            (p: { name: string; status: string }) => `Cloud provider ${p.name} is ${p.status}`
          ) ?? [];

      const allAlerts: Alert[] = [
        ...recommendations.map((rec: string, i: number) => ({
          id: `rec-${i}`,
          timestamp: new Date().toISOString(),
          level: 'warning' as const,
          title: 'Performance Recommendation',
          message: rec,
          service: 'gateway',
          resolved: false,
          acknowledged: false,
        })),
        ...cloudWarnings.map((warn: string, i: number) => ({
          id: `cloud-warn-${i}`,
          timestamp: new Date().toISOString(),
          level: 'warning' as const,
          title: 'Cloud Provider Warning',
          message: warn,
          service: 'cloud',
          resolved: false,
          acknowledged: false,
        })),
      ];

      const filteredAlerts = allAlerts.filter((alert) => {
        if (config.alertLevel === 'all') return true;
        if (config.alertLevel === 'warning')
          return alert.level === 'warning' || alert.level === 'error' || alert.level === 'critical';
        if (config.alertLevel === 'error')
          return alert.level === 'error' || alert.level === 'critical';
        if (config.alertLevel === 'critical') return alert.level === 'critical';
        return true;
      });

      const filteredServices =
        config.services.length > 0
          ? services.filter((s) => config.services.includes(s.id))
          : services;

      const totalReqs = filteredServices.reduce((sum, s) => sum + s.requests, 0);
      const totalErrs = filteredServices.reduce((sum, s) => sum + s.errors, 0);

      setMetrics({
        timestamp: new Date().toISOString(),
        system: {
          cpu: cacheHitRate * 100,
          memory: cacheHitRate * 100,
          disk: 0,
          network: {
            inbound: totalRequests,
            outbound: totalRequests,
          },
          uptime: formatUptime(uptimeSeconds),
        },
        services: filteredServices,
        alerts: filteredAlerts,
        performance: {
          avgResponseTime: avgResponseTime,
          requestsPerSecond: uptimeSeconds > 0 ? totalRequests / uptimeSeconds : 0,
          errorRate: totalReqs > 0 ? (totalErrs / totalReqs) * 100 : 0,
          throughput: totalReqs,
        },
      });
      setIsConnected(true);
    } catch {
      setIsConnected(false);
    }
  }, [config.alertLevel, config.services]);

  useEffect(() => {
    fetchRealMetrics();

    if (!config.autoRefresh) {
      return;
    }

    const interval = setInterval(() => {
      fetchRealMetrics();
    }, config.refreshRate);

    return () => clearInterval(interval);
  }, [config.autoRefresh, config.refreshRate, fetchRealMetrics]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'stopped':
        return <XCircle className="w-4 h-4 text-gray-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'starting':
      case 'stopping':
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'sleeping':
        return <Pause className="w-4 h-4 text-yellow-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'info':
        return <Info className="w-4 h-4 text-blue-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Bell className="w-4 h-4 text-gray-500" />;
    }
  };

  const getHealthColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const filteredServices =
    metrics?.services
      ?.filter((service) => !config.showOnlyActive || service.status === 'running')
      .filter(
        (service) => !searchTerm || service.name.toLowerCase().includes(searchTerm.toLowerCase())
      ) || [];

  const activeAlerts = metrics?.alerts?.filter((alert) => !alert.resolved) || [];
  const criticalAlerts = activeAlerts.filter((alert) => alert.level === 'critical');

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
          <p className="text-muted-foreground">Live system metrics and performance monitoring</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Switch
              checked={config.autoRefresh}
              onCheckedChange={(checked) =>
                setConfig((prev) => ({ ...prev, autoRefresh: checked }))
              }
            />
            <span className="text-sm">Auto-refresh</span>
          </div>
          <div className="flex items-center space-x-2">
            <Label htmlFor="refresh-rate" className="text-sm">
              Refresh:
            </Label>
            <Select
              id="refresh-rate"
              value={config.refreshRate.toString()}
              onChange={(event) =>
                setConfig((prev) => ({
                  ...prev,
                  refreshRate: Number.parseInt(event.target.value, 10),
                }))
              }
            >
              <option value="1000">1s</option>
              <option value="5000">5s</option>
              <option value="10000">10s</option>
              <option value="30000">30s</option>
            </Select>
          </div>
          <Button
            variant="outline"
            onClick={() => fetchRealMetrics()}
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
              <Button variant="outline" size="sm" onClick={() => setShowAlerts(!showAlerts)}>
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
                    className={`flex items-start space-x-3 rounded-lg border p-3 ${getAlertContainerClassName(alert.level)}`}
                  >
                    {getAlertIcon(alert.level)}
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">{alert.title}</h4>
                        <Badge variant="outline" className="text-xs">
                          {alert.service || 'System'}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{alert.message}</p>
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
                              console.log('Acknowledge alert:', alert.id);
                            }}
                          >
                            Acknowledge
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              // In a real implementation, this would resolve the alert
                              console.log('Resolve alert:', alert.id);
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
            </CardContent>
          )}
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
                  <span className="text-sm font-medium">
                    {(metrics.system.network.inbound / 1000).toFixed(1)}K/s
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Outbound</span>
                  <span className="text-sm font-medium">
                    {(metrics.system.network.outbound / 1000).toFixed(1)}K/s
                  </span>
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
                  <span className="text-sm font-medium">
                    {metrics.performance.avgResponseTime.toFixed(0)}ms
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Requests/s</span>
                  <span className="text-sm font-medium">
                    {metrics.performance.requestsPerSecond.toFixed(1)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Error Rate</span>
                  <span
                    className={`text-sm font-medium ${metrics.performance.errorRate > 5 ? 'text-red-500' : 'text-green-500'}`}
                  >
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
          <CardDescription>Configure monitoring display and alert settings</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <Label htmlFor="show-only-active">Show Only Active Services</Label>
              <Switch
                id="show-only-active"
                checked={config.showOnlyActive}
                onCheckedChange={(checked) =>
                  setConfig((prev) => ({ ...prev, showOnlyActive: checked }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="alert-level">Alert Level</Label>
              <Select
                id="alert-level"
                value={config.alertLevel}
                onChange={(event) => {
                  setConfig((prev) => ({ ...prev, alertLevel: event.target.value as AlertLevel }));
                }}
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
                id="time-range"
                value={config.timeRange}
                onChange={(event) => {
                  setConfig((prev) => ({ ...prev, timeRange: event.target.value as TimeRange }));
                }}
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
              <Button variant="outline" size="sm" onClick={() => fetchRealMetrics()}>
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </CardTitle>
          <CardDescription>Real-time service metrics and health status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredServices.map((service) => (
              <div key={service.id} className="rounded-lg border">
                <button
                  type="button"
                  className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-gray-50"
                  onClick={() =>
                    setSelectedService(service.id === selectedService ? null : service.id)
                  }
                  aria-expanded={service.id === selectedService}
                  aria-controls={`service-details-${service.id}`}
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
                        <span>
                          Health:{' '}
                          <span className={getHealthColor(service.healthScore)}>
                            {service.healthScore}%
                          </span>
                        </span>
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
                          <div className="text-xs text-red-500">{service.errors} errors</div>
                        )}
                      </div>
                    </div>
                  </div>
                </button>

                {selectedService === service.id && (
                  <div
                    id={`service-details-${service.id}`}
                    className="col-span-full mt-4 p-4 bg-gray-50 rounded-lg"
                  >
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
  );
}
