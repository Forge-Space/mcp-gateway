'use client';

import { useCallback, useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart3, RefreshCw, Settings, Shield, Users, Zap } from 'lucide-react';

interface FeatureFlag {
  name: string;
  description: string;
  enabled: boolean;
  category: string;
  source: string;
}

interface FeaturesResponse {
  features: FeatureFlag[];
  total: number;
  enabled_count: number;
}

const CATEGORY_STYLES: Record<
  string,
  { color: string; icon: React.ComponentType<{ className?: string }> }
> = {
  global: { color: 'bg-blue-100 text-blue-800', icon: Settings },
  'mcp-gateway': { color: 'bg-green-100 text-green-800', icon: Shield },
  'uiforge-mcp': { color: 'bg-purple-100 text-purple-800', icon: Users },
  'uiforge-webapp': { color: 'bg-orange-100 text-orange-800', icon: BarChart3 },
};

const CATEGORY_LABELS: Record<string, string> = {
  global: 'Global',
  'mcp-gateway': 'MCP Gateway',
  'uiforge-mcp': 'UIForge MCP',
  'uiforge-webapp': 'UIForge WebApp',
};

function getCategoryStyle(category: string) {
  return CATEGORY_STYLES[category] ?? { color: 'bg-gray-100 text-gray-800', icon: Settings };
}

function FeatureCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="h-5 w-24 animate-pulse rounded bg-muted" />
          <div className="h-5 w-12 animate-pulse rounded bg-muted" />
        </div>
        <div className="h-5 w-40 mt-2 animate-pulse rounded bg-muted" />
        <div className="h-4 w-56 mt-1 animate-pulse rounded bg-muted" />
      </CardHeader>
      <CardContent className="pt-0">
        <div className="h-4 w-full animate-pulse rounded bg-muted" />
      </CardContent>
    </Card>
  );
}

export default function FeatureToggles() {
  const [data, setData] = useState<FeaturesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const fetchFeatures = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/features');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load feature flags');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFeatures();
  }, [fetchFeatures]);

  const features = data?.features ?? [];
  const filteredFeatures =
    selectedCategory === 'all' ? features : features.filter((f) => f.category === selectedCategory);

  const categories = [
    { value: 'all', label: 'All Features' },
    ...Object.entries(CATEGORY_LABELS).map(([value, label]) => ({ value, label })),
  ];

  function getCategoryIcon(category: string) {
    const Icon = getCategoryStyle(category).icon;
    return <Icon className="h-4 w-4" />;
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="flex h-16 items-center px-4">
          <h1 className="text-xl font-semibold">Feature Toggles</h1>
          <div className="ml-auto flex items-center space-x-2">
            <Button variant="outline" size="sm" onClick={fetchFeatures} disabled={loading}>
              <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Feature Management</h2>
            <p className="text-muted-foreground">
              Runtime feature flags derived from gateway environment configuration
            </p>
          </div>
        </div>

        {error && (
          <div className="rounded-md bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
            Failed to load feature flags: {error}
          </div>
        )}

        {/* Category Filter */}
        <div className="flex space-x-2 flex-wrap gap-y-2">
          {categories.map((category) => (
            <Button
              key={category.value}
              variant={selectedCategory === category.value ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory(category.value)}
              className="flex items-center space-x-2"
            >
              {getCategoryIcon(category.value)}
              <span>{category.label}</span>
            </Button>
          ))}
        </div>

        {/* Stats Overview */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Features</CardTitle>
              <Settings className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-8 w-12 animate-pulse rounded bg-muted" />
              ) : (
                <div className="text-2xl font-bold">{data?.total ?? 0}</div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Enabled</CardTitle>
              <Zap className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-8 w-12 animate-pulse rounded bg-muted" />
              ) : (
                <div className="text-2xl font-bold text-green-600">{data?.enabled_count ?? 0}</div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Disabled</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-8 w-12 animate-pulse rounded bg-muted" />
              ) : (
                <div className="text-2xl font-bold text-muted-foreground">
                  {(data?.total ?? 0) - (data?.enabled_count ?? 0)}
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Showing</CardTitle>
              <BarChart3 className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-8 w-12 animate-pulse rounded bg-muted" />
              ) : (
                <div className="text-2xl font-bold text-blue-600">{filteredFeatures.length}</div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Features List */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {loading
            ? Array.from({ length: 6 }).map((_, i) => <FeatureCardSkeleton key={i} />)
            : filteredFeatures.map((feature) => {
                const style = getCategoryStyle(feature.category);
                const Icon = style.icon;
                return (
                  <Card key={feature.name} className="relative">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Icon className="h-5 w-5 text-muted-foreground" />
                          <Badge className={style.color}>{feature.category}</Badge>
                        </div>
                        <Badge
                          variant={feature.enabled ? 'default' : 'secondary'}
                          className={
                            feature.enabled
                              ? 'bg-green-100 text-green-800 hover:bg-green-100'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-100'
                          }
                        >
                          {feature.enabled ? 'Enabled' : 'Disabled'}
                        </Badge>
                      </div>
                      <CardTitle className="text-base">{feature.name}</CardTitle>
                      <CardDescription>{feature.description}</CardDescription>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Source</span>
                        <span className="font-mono text-xs text-muted-foreground">
                          {feature.source}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
        </div>

        {/* Info Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="h-5 w-5" />
              <span>Configuration</span>
            </CardTitle>
            <CardDescription>
              Feature flags are read-only and derived from environment variables. Set environment
              variables on the gateway to change feature states.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h4 className="font-medium mb-2">Source Values</h4>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <div>
                    <code className="bg-muted px-1 rounded">env</code> — Value read from environment
                    variable
                  </div>
                  <div>
                    <code className="bg-muted px-1 rounded">default</code> — Using compiled-in
                    default value
                  </div>
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-2">Key Environment Variables</h4>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <div>
                    <code className="bg-muted px-1 rounded">DEBUG</code> — Enable debug mode
                  </div>
                  <div>
                    <code className="bg-muted px-1 rounded">REDIS_URL</code> — Activates rate
                    limiting
                  </div>
                  <div>
                    <code className="bg-muted px-1 rounded">OTEL_EXPORTER_OTLP_ENDPOINT</code> —
                    Activates OTel
                  </div>
                  <div>
                    <code className="bg-muted px-1 rounded">BETA_FEATURES</code> — Enable beta
                    features
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
