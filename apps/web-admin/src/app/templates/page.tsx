'use client';

import { useCallback, useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Globe,
  Server,
  Activity,
  Settings,
  Search,
  RefreshCw,
  CheckCircle,
  XCircle,
  Layers,
} from 'lucide-react';

interface VirtualServer {
  name: string;
  enabled: boolean;
  gateways: string[];
  description: string;
}

function GatewayBadge({ gateway }: { gateway: string }) {
  const colorMap: Record<string, string> = {
    cloud: 'bg-blue-100 text-blue-800',
    local: 'bg-green-100 text-green-800',
    homelab: 'bg-purple-100 text-purple-800',
    dev: 'bg-yellow-100 text-yellow-800',
  };
  const cls = colorMap[gateway] ?? 'bg-gray-100 text-gray-800';
  return <Badge className={cls}>{gateway}</Badge>;
}

export default function TemplatesPage() {
  const [servers, setServers] = useState<VirtualServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/servers');
      if (!res.ok) throw new Error(`Server list error: ${res.status}`);
      const data: VirtualServer[] = await res.json();
      setServers(data);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load server templates');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filtered = servers.filter(
    (s) =>
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.gateways.some((g) => g.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const enabledCount = servers.filter((s) => s.enabled).length;
  const gatewaySet = new Set(servers.flatMap((s) => s.gateways));
  const totalGateways = gatewaySet.size;

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Virtual Server Templates</h2>
          <p className="text-muted-foreground">
            Virtual server configurations registered in the MCP Gateway
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
            <CardTitle className="text-sm font-medium">Total Servers</CardTitle>
            <Server className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{loading ? '—' : servers.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Enabled</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '—' : `${enabledCount}/${servers.length}`}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Gateways</CardTitle>
            <Globe className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{loading ? '—' : totalGateways}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Disabled</CardTitle>
            <XCircle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '—' : servers.length - enabledCount}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search servers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
          <Layers className="h-4 w-4" />
          <span>MCP Gateway virtual servers</span>
        </div>
      </div>

      {/* Server List */}
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
        <div className="space-y-3">
          {filtered.map((server) => (
            <Card key={server.name}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Settings className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <CardTitle className="text-base font-mono">{server.name}</CardTitle>
                      {server.description && (
                        <CardDescription>{server.description}</CardDescription>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {server.enabled ? (
                      <Badge variant="outline" className="text-green-600 border-green-600">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Enabled
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-muted-foreground">
                        <XCircle className="h-3 w-3 mr-1" />
                        Disabled
                      </Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              {server.gateways.length > 0 && (
                <CardContent className="pt-0">
                  <div className="flex items-center space-x-2">
                    <Activity className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Gateways:</span>
                    <div className="flex flex-wrap gap-1">
                      {server.gateways.map((g) => (
                        <GatewayBadge key={g} gateway={g} />
                      ))}
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>
          ))}

          {filtered.length === 0 && !error && (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Server className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No servers found</h3>
                <p className="text-muted-foreground text-center">
                  {searchTerm
                    ? 'Try adjusting your search terms'
                    : 'No virtual server configurations available from the gateway'}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
