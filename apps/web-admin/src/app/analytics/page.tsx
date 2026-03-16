'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  BarChart3,
  Activity,
  TrendingUp,
  Server,
  Zap,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock,
  Database,
} from 'lucide-react';

interface PerformanceSummary {
  timestamp: number;
  uptime_seconds: number;
  cache_performance: {
    overall_hit_rate: number;
    total_requests: number;
    total_cache_size: number;
  };
  query_cache: {
    enabled: boolean;
    cache_size: number;
    hit_rate: number;
  };
  recommendations: string[];
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

function formatPercent(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`;
}

const TIME_RANGES = [
  { value: '1h', label: 'Last Hour' },
  { value: '24h', label: 'Last 24 Hours' },
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
];

export default function AnalyticsPage() {
  const [data, setData] = useState<PerformanceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('24h');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/analytics/performance?period=${timeRange}`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body?.detail ?? `HTTP ${res.status}`);
      }
      const json: PerformanceSummary = await res.json();
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load performance data');
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const cacheHitRate = data?.cache_performance.overall_hit_rate ?? 0;
  const queryCacheHitRate = data?.query_cache.hit_rate ?? 0;

  const stats = [
    {
      title: 'Uptime',
      value: data ? formatUptime(data.uptime_seconds) : '—',
      icon: Clock,
      color: 'text-blue-600',
      sub: data ? new Date(data.timestamp * 1000).toLocaleTimeString() : 'Loading…',
    },
    {
      title: 'Cache Hit Rate',
      value: data ? formatPercent(cacheHitRate) : '—',
      icon: Server,
      color:
        cacheHitRate >= 0.8
          ? 'text-green-600'
          : cacheHitRate >= 0.5
            ? 'text-yellow-600'
            : 'text-red-600',
      sub: data
        ? `${data.cache_performance.total_requests.toLocaleString()} total requests`
        : 'Loading…',
    },
    {
      title: 'Query Cache Hit Rate',
      value: data ? formatPercent(queryCacheHitRate) : '—',
      icon: Database,
      color: queryCacheHitRate >= 0.5 ? 'text-green-600' : 'text-yellow-600',
      sub: data ? `Size: ${data.query_cache.cache_size}` : 'Loading…',
    },
    {
      title: 'Total Cache Size',
      value: data ? data.cache_performance.total_cache_size.toLocaleString() : '—',
      icon: Zap,
      color: 'text-purple-600',
      sub: data?.query_cache.enabled ? 'Query cache: enabled' : 'Query cache: disabled',
    },
  ];

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Performance Analytics</h2>
          <p className="text-muted-foreground">
            Gateway cache performance, query metrics, and system health
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1">
            {TIME_RANGES.map((range) => (
              <Button
                key={range.value}
                variant={timeRange === range.value ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTimeRange(range.value)}
              >
                {range.label}
              </Button>
            ))}
          </div>
          <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center space-x-2 rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="h-8 w-24 animate-pulse rounded bg-muted" />
                ) : (
                  <div className="text-2xl font-bold">{stat.value}</div>
                )}
                <p className="text-xs text-muted-foreground mt-1">{stat.sub}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Cache breakdown */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>Cache Performance</span>
            </CardTitle>
            <CardDescription>Hit rate and request volume breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[1, 2].map((i) => (
                  <div key={i} className="h-6 animate-pulse rounded bg-muted" />
                ))}
              </div>
            ) : data ? (
              <div className="space-y-4">
                {[
                  { label: 'Overall Cache Hit Rate', rate: cacheHitRate },
                  { label: 'Query Cache Hit Rate', rate: queryCacheHitRate },
                ].map(({ label, rate }) => (
                  <div key={label} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{label}</span>
                      <span className="text-muted-foreground">{formatPercent(rate)}</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${rate >= 0.8 ? 'bg-green-500' : rate >= 0.5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                        style={{ width: `${Math.min(rate * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>System Status</span>
            </CardTitle>
            <CardDescription>Current system configuration and state</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-6 animate-pulse rounded bg-muted" />
                ))}
              </div>
            ) : data ? (
              <div className="space-y-3">
                {[
                  {
                    label: 'Query Cache',
                    active: data.query_cache.enabled,
                    detail: `${data.query_cache.cache_size} entries`,
                  },
                  {
                    label: 'Cache Layer',
                    active: data.cache_performance.total_cache_size > 0,
                    detail: `${data.cache_performance.total_cache_size} total entries`,
                  },
                  {
                    label: 'Metrics Collection',
                    active: true,
                    detail: `${data.cache_performance.total_requests.toLocaleString()} requests tracked`,
                  },
                ].map(({ label, active, detail }) => (
                  <div key={label} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {active ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-muted-foreground" />
                      )}
                      <span className="text-sm font-medium">{label}</span>
                    </div>
                    <Badge variant={active ? 'default' : 'secondary'} className="text-xs">
                      {detail}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5" />
            <span>Performance Recommendations</span>
          </CardTitle>
          <CardDescription>
            Auto-generated tuning suggestions based on current metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {[1, 2].map((i) => (
                <div key={i} className="h-10 animate-pulse rounded bg-muted" />
              ))}
            </div>
          ) : data?.recommendations?.length ? (
            <ul className="space-y-2">
              {data.recommendations.map((rec, i) => (
                <li key={i} className="flex items-start space-x-2 text-sm p-3 border rounded-lg">
                  <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <TrendingUp className="h-12 w-12 mx-auto mb-2" />
              <p>No recommendations at this time</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
