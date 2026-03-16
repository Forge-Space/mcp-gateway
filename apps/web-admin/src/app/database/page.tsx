'use client';

import { useCallback, useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Database,
  Search,
  RefreshCw,
  BarChart3,
  Activity,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Layers,
} from 'lucide-react';

interface CacheMetrics {
  cache_name: string;
  backend_type: string;
  hits: number;
  misses: number;
  evictions: number;
  total_requests: number;
  hit_rate: number;
  current_size: number;
  max_size: number;
  memory_usage: number;
  avg_get_time: number;
  health_status: string;
  redis_connected: boolean;
  redis_memory_usage: number;
  redis_key_count: number;
}

interface CacheSnapshot {
  timestamp: number;
  metrics: Record<string, CacheMetrics>;
  alerts: Array<{
    alert_id: string;
    alert_type: string;
    severity: string;
    message: string;
    cache_name: string;
    resolved: boolean;
  }>;
  summary?: {
    total_caches: number;
    healthy_caches: number;
    total_requests: number;
    overall_hit_rate: number;
    total_memory_usage: number;
  };
}

interface CacheDashboardStatus {
  running: boolean;
  cache_count: number;
  collection_interval: number;
  max_history_hours: number;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function formatMs(seconds: number): string {
  return `${(seconds * 1000).toFixed(1)} ms`;
}

function HealthBadge({ status }: { status: string }) {
  if (status === 'healthy') {
    return (
      <Badge variant="outline" className="text-green-600 border-green-600">
        <CheckCircle className="h-3 w-3 mr-1" />
        Healthy
      </Badge>
    );
  }
  if (status === 'degraded') {
    return (
      <Badge variant="outline" className="text-yellow-600 border-yellow-600">
        <AlertTriangle className="h-3 w-3 mr-1" />
        Degraded
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="text-red-600 border-red-600">
      <XCircle className="h-3 w-3 mr-1" />
      {status || 'Unknown'}
    </Badge>
  );
}

export default function DatabasePage() {
  const [snapshot, setSnapshot] = useState<CacheSnapshot | null>(null);
  const [dashStatus, setDashStatus] = useState<CacheDashboardStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [snapRes, statusRes] = await Promise.all([
        fetch('/api/cache/snapshot'),
        fetch('/api/cache/status'),
      ]);
      if (!snapRes.ok) throw new Error(`Snapshot error: ${snapRes.status}`);
      const snapData: CacheSnapshot = await snapRes.json();
      setSnapshot(snapData);
      if (statusRes.ok) {
        const statusData: CacheDashboardStatus = await statusRes.json();
        setDashStatus(statusData);
      }
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load cache data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const cacheList = snapshot
    ? Object.values(snapshot.metrics).filter(
        (c) =>
          c.cache_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.backend_type.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : [];

  const activeAlerts = snapshot?.alerts.filter((a) => !a.resolved) ?? [];

  const totalCaches = dashStatus?.cache_count ?? cacheList.length;
  const healthyCaches = cacheList.filter((c) => c.health_status === 'healthy').length;
  const totalRequests = cacheList.reduce((sum, c) => sum + c.total_requests, 0);
  const overallHitRate =
    cacheList.length > 0 ? cacheList.reduce((sum, c) => sum + c.hit_rate, 0) / cacheList.length : 0;

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Cache Store</h2>
          <p className="text-muted-foreground">
            Live cache metrics from the MCP Gateway cache dashboard
            {lastUpdated && (
              <span className="ml-2 text-xs">— updated {lastUpdated.toLocaleTimeString()}</span>
            )}
          </p>
        </div>
        <Button variant="outline" onClick={fetchData} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="rounded-md bg-destructive/10 border border-destructive/30 p-4 text-destructive text-sm">
          {error}
        </div>
      )}

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Caches</CardTitle>
            <Database className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{loading ? '—' : totalCaches}</div>
            {dashStatus && (
              <p className="text-xs text-muted-foreground mt-1">
                {dashStatus.running ? 'Collection running' : 'Collection stopped'}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Healthy Caches</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '—' : `${healthyCaches}/${cacheList.length}`}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Hit Rate</CardTitle>
            <BarChart3 className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '—' : `${(overallHitRate * 100).toFixed(1)}%`}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
            <Activity className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '—' : totalRequests.toLocaleString()}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Alerts */}
      {activeAlerts.length > 0 && (
        <Card className="border-yellow-400">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-yellow-600">
              <AlertTriangle className="h-5 w-5" />
              <span>Active Alerts ({activeAlerts.length})</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {activeAlerts.map((alert) => (
                <div
                  key={alert.alert_id}
                  className="flex items-center justify-between text-sm border rounded p-2"
                >
                  <span>{alert.message}</span>
                  <Badge variant="outline" className="text-yellow-600 border-yellow-600">
                    {alert.severity}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search caches..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
          <Layers className="h-4 w-4" />
          <span>MCP Gateway Cache Dashboard</span>
        </div>
      </div>

      {/* Cache List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="h-6 bg-muted rounded animate-pulse mb-2 w-1/3" />
                <div className="h-4 bg-muted rounded animate-pulse w-2/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {cacheList.map((cache) => (
            <Card key={cache.cache_name}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Database className="h-6 w-6 text-muted-foreground" />
                    <div>
                      <CardTitle className="text-lg font-mono">{cache.cache_name}</CardTitle>
                      <CardDescription>
                        {cache.backend_type}
                        {cache.redis_connected && ' — Redis connected'}
                      </CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <HealthBadge status={cache.health_status} />
                    <Badge variant="outline">
                      {cache.current_size}/{cache.max_size} entries
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <h4 className="font-medium mb-2">Hit/Miss Statistics</h4>
                    <div className="space-y-1 text-sm text-muted-foreground">
                      <div>Hit rate: {(cache.hit_rate * 100).toFixed(1)}%</div>
                      <div>Hits: {cache.hits.toLocaleString()}</div>
                      <div>Misses: {cache.misses.toLocaleString()}</div>
                      <div>Evictions: {cache.evictions.toLocaleString()}</div>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Performance</h4>
                    <div className="space-y-1 text-sm text-muted-foreground">
                      <div>Avg get: {formatMs(cache.avg_get_time)}</div>
                      <div>Total requests: {cache.total_requests.toLocaleString()}</div>
                      <div>Memory: {formatBytes(cache.memory_usage)}</div>
                    </div>
                  </div>
                  {cache.redis_connected && (
                    <div>
                      <h4 className="font-medium mb-2">Redis</h4>
                      <div className="space-y-1 text-sm text-muted-foreground">
                        <div>Keys: {cache.redis_key_count.toLocaleString()}</div>
                        <div>Memory: {formatBytes(cache.redis_memory_usage)}</div>
                        <div className="flex items-center space-x-1">
                          <CheckCircle className="h-3 w-3 text-green-600" />
                          <span>Connected</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}

          {cacheList.length === 0 && !error && (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Database className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No caches found</h3>
                <p className="text-muted-foreground text-center">
                  {searchTerm
                    ? 'Try adjusting your search terms'
                    : 'No cache metrics available from the gateway'}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Dashboard Config */}
      {dashStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Dashboard Configuration</span>
            </CardTitle>
            <CardDescription>Cache dashboard collection settings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h4 className="font-medium mb-2">Collection</h4>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <div>Status: {dashStatus.running ? 'Running' : 'Stopped'}</div>
                  <div>Interval: {dashStatus.collection_interval}s</div>
                  <div>History: {dashStatus.max_history_hours}h</div>
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-2">Coverage</h4>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <div>Monitored caches: {dashStatus.cache_count}</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
