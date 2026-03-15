'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Cloud,
  Plus,
  Trash2,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  Globe,
  Activity,
  Zap,
  Settings,
} from 'lucide-react';

interface CloudProvider {
  name: string;
  cloud_type: string;
  region: string;
  url: string;
  enabled: boolean;
  priority: number;
  weight: number;
  status: string;
  tags: Record<string, string>;
}

interface CloudHealthSummary {
  overall: string;
  strategy: string;
  total_providers: number;
  healthy: number;
  degraded: number;
  unhealthy: number;
  providers: Array<{
    name: string;
    status: string;
    enabled: boolean;
    metrics: Record<string, unknown>;
  }>;
}

interface NewProviderForm {
  name: string;
  cloud_type: string;
  region: string;
  url: string;
  priority: number;
  weight: number;
  enabled: boolean;
}

const ROUTING_STRATEGIES = ['failover', 'round_robin', 'latency_weighted', 'random'];
const CLOUD_TYPES = ['aws', 'azure', 'gcp', 'custom'];

function getStatusIcon(status: string) {
  switch (status) {
    case 'healthy':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'degraded':
      return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    case 'unhealthy':
      return <XCircle className="h-4 w-4 text-red-500" />;
    default:
      return <AlertCircle className="h-4 w-4 text-gray-400" />;
  }
}

function getStatusBadge(status: string) {
  const variants: Record<string, string> = {
    healthy: 'bg-green-100 text-green-800',
    degraded: 'bg-yellow-100 text-yellow-800',
    unhealthy: 'bg-red-100 text-red-800',
    unknown: 'bg-gray-100 text-gray-600',
  };
  return variants[status] ?? variants.unknown;
}

export default function CloudManagement() {
  const [providers, setProviders] = useState<CloudProvider[]>([]);
  const [health, setHealth] = useState<CloudHealthSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [strategy, setStrategy] = useState('failover');
  const [strategyUpdating, setStrategyUpdating] = useState(false);
  const [newProvider, setNewProvider] = useState<NewProviderForm>({
    name: '',
    cloud_type: 'custom',
    region: 'us-east-1',
    url: '',
    priority: 0,
    weight: 1.0,
    enabled: true,
  });

  const fetchData = useCallback(async () => {
    try {
      const [providersRes, healthRes] = await Promise.all([
        fetch('/api/cloud/providers'),
        fetch('/api/cloud/health'),
      ]);

      if (providersRes.ok) {
        const data = await providersRes.json();
        setProviders(data.providers ?? []);
      }

      if (healthRes.ok) {
        const data: CloudHealthSummary = await healthRes.json();
        setHealth(data);
        setStrategy(data.strategy);
      }
    } catch (error) {
      console.error('Failed to fetch cloud data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const toggleProvider = async (name: string, enabled: boolean) => {
    try {
      const res = await fetch(`/api/cloud/providers/${name}/enabled`, {
        method: 'PATCH',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ enabled }),
      });
      if (res.ok) {
        setProviders((prev) => prev.map((p) => (p.name === name ? { ...p, enabled } : p)));
      }
    } catch (error) {
      console.error('Failed to toggle provider:', error);
    }
  };

  const deleteProvider = async (name: string) => {
    if (!confirm(`Remove provider "${name}"?`)) return;
    try {
      const res = await fetch(`/api/cloud/providers/${name}`, { method: 'DELETE' });
      if (res.ok || res.status === 204) {
        setProviders((prev) => prev.filter((p) => p.name !== name));
      }
    } catch (error) {
      console.error('Failed to delete provider:', error);
    }
  };

  const addProvider = async () => {
    if (!newProvider.name || !newProvider.url) return;
    try {
      const res = await fetch('/api/cloud/providers', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(newProvider),
      });
      if (res.ok) {
        const created: CloudProvider = await res.json();
        setProviders((prev) => [...prev, created]);
        setShowAddForm(false);
        setNewProvider({
          name: '',
          cloud_type: 'custom',
          region: 'us-east-1',
          url: '',
          priority: 0,
          weight: 1.0,
          enabled: true,
        });
      }
    } catch (error) {
      console.error('Failed to add provider:', error);
    }
  };

  const updateStrategy = async (newStrategy: string) => {
    setStrategyUpdating(true);
    try {
      const res = await fetch('/api/cloud/strategy', {
        method: 'PATCH',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ strategy: newStrategy }),
      });
      if (res.ok) {
        setStrategy(newStrategy);
      }
    } catch (error) {
      console.error('Failed to update strategy:', error);
    } finally {
      setStrategyUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 bg-gray-100 animate-pulse rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Cloud className="h-6 w-6" />
            Multi-Cloud Management
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage cloud provider endpoints and routing strategy
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
          <Button size="sm" onClick={() => setShowAddForm(true)}>
            <Plus className="h-4 w-4 mr-1" />
            Add Provider
          </Button>
        </div>
      </div>

      {/* Health Overview */}
      {health && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <Globe className="h-5 w-5 text-blue-500" />
                <div>
                  <p className="text-xs text-muted-foreground">Overall Status</p>
                  <p className="font-semibold capitalize">{health.overall}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <div>
                  <p className="text-xs text-muted-foreground">Healthy</p>
                  <p className="font-semibold">
                    {health.healthy} / {health.total_providers}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-yellow-500" />
                <div>
                  <p className="text-xs text-muted-foreground">Degraded</p>
                  <p className="font-semibold">{health.degraded}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <XCircle className="h-5 w-5 text-red-500" />
                <div>
                  <p className="text-xs text-muted-foreground">Unhealthy</p>
                  <p className="font-semibold">{health.unhealthy}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Routing Strategy */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Zap className="h-4 w-4" />
            Routing Strategy
          </CardTitle>
          <CardDescription>How requests are distributed across providers</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 flex-wrap">
            {ROUTING_STRATEGIES.map((s) => (
              <Button
                key={s}
                variant={strategy === s ? 'default' : 'outline'}
                size="sm"
                disabled={strategyUpdating}
                onClick={() => updateStrategy(s)}
                className="capitalize"
              >
                {s.replace('_', ' ')}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Add Provider Form */}
      {showAddForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Register New Provider</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  value={newProvider.name}
                  onChange={(e) => setNewProvider((p) => ({ ...p, name: e.target.value }))}
                  placeholder="my-aws-provider"
                />
              </div>
              <div>
                <Label htmlFor="url">Gateway URL *</Label>
                <Input
                  id="url"
                  value={newProvider.url}
                  onChange={(e) => setNewProvider((p) => ({ ...p, url: e.target.value }))}
                  placeholder="https://gateway.example.com"
                />
              </div>
              <div>
                <Label htmlFor="cloud_type">Cloud Type</Label>
                <select
                  id="cloud_type"
                  className="w-full border rounded px-3 py-2 text-sm"
                  value={newProvider.cloud_type}
                  onChange={(e) => setNewProvider((p) => ({ ...p, cloud_type: e.target.value }))}
                >
                  {CLOUD_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="region">Region</Label>
                <Input
                  id="region"
                  value={newProvider.region}
                  onChange={(e) => setNewProvider((p) => ({ ...p, region: e.target.value }))}
                  placeholder="us-east-1"
                />
              </div>
              <div>
                <Label htmlFor="priority">Priority (0–100)</Label>
                <Input
                  id="priority"
                  type="number"
                  min={0}
                  max={100}
                  value={newProvider.priority}
                  onChange={(e) =>
                    setNewProvider((p) => ({ ...p, priority: Number(e.target.value) }))
                  }
                />
              </div>
              <div>
                <Label htmlFor="weight">Weight</Label>
                <Input
                  id="weight"
                  type="number"
                  min={0.1}
                  step={0.1}
                  value={newProvider.weight}
                  onChange={(e) =>
                    setNewProvider((p) => ({ ...p, weight: Number(e.target.value) }))
                  }
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={newProvider.enabled}
                onCheckedChange={(v) => setNewProvider((p) => ({ ...p, enabled: v }))}
              />
              <Label>Enabled</Label>
            </div>
            <div className="flex gap-2">
              <Button onClick={addProvider} disabled={!newProvider.name || !newProvider.url}>
                Register Provider
              </Button>
              <Button variant="outline" onClick={() => setShowAddForm(false)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Providers List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="h-4 w-4" />
            Cloud Providers ({providers.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {providers.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Cloud className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>No cloud providers registered.</p>
              <p className="text-sm">Add a provider to start routing requests.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {providers.map((provider) => (
                <div
                  key={provider.name}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {getStatusIcon(provider.status)}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{provider.name}</span>
                        <Badge className={getStatusBadge(provider.status)}>{provider.status}</Badge>
                        <Badge variant="outline" className="text-xs">
                          {provider.cloud_type.toUpperCase()}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {provider.region} · Priority {provider.priority} · Weight {provider.weight}
                      </p>
                      <p className="text-xs text-muted-foreground truncate max-w-xs">
                        {provider.url}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={provider.enabled}
                        onCheckedChange={(v) => toggleProvider(provider.name, v)}
                      />
                      <span className="text-xs text-muted-foreground">
                        {provider.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteProvider(provider.name)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
