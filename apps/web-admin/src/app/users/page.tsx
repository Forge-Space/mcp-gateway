'use client';

import { useCallback, useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Users,
  Search,
  Shield,
  Key,
  Lock,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  XCircle,
} from 'lucide-react';

interface RoleEntry {
  role: string;
  display_name: string;
  description: string;
  permissions: string[];
  permission_count: number;
  is_privileged: boolean;
}

interface UsersResponse {
  roles: RoleEntry[];
  total_roles: number;
  total_permissions: number;
}

export default function UsersPage() {
  const [data, setData] = useState<UsersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'privileged' | 'standard'>('all');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/users');
      if (!res.ok) throw new Error(`Gateway returned ${res.status}`);
      setData(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load access control data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filteredRoles = (data?.roles ?? []).filter((r) => {
    const matchesSearch =
      r.role.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter =
      selectedFilter === 'all' ||
      (selectedFilter === 'privileged' && r.is_privileged) ||
      (selectedFilter === 'standard' && !r.is_privileged);
    return matchesSearch && matchesFilter;
  });

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'developer':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'user':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
    }
  };

  const getPermissionCategory = (perm: string) => {
    const [cat] = perm.split(':');
    return cat;
  };

  const privilegedCount = data?.roles.filter((r) => r.is_privileged).length ?? 0;
  const standardCount = data?.roles.filter((r) => !r.is_privileged).length ?? 0;

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Access Control</h2>
          <p className="text-muted-foreground">Gateway RBAC roles and permission matrix</p>
        </div>
        <Button variant="outline" onClick={fetchData} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="flex items-center space-x-2 rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Roles</CardTitle>
            <Users className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-8 w-12 animate-pulse rounded bg-muted" />
            ) : (
              <div className="text-2xl font-bold">{data?.total_roles ?? 0}</div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Privileged Roles</CardTitle>
            <Shield className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-8 w-12 animate-pulse rounded bg-muted" />
            ) : (
              <div className="text-2xl font-bold">{privilegedCount}</div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Standard Roles</CardTitle>
            <Users className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-8 w-12 animate-pulse rounded bg-muted" />
            ) : (
              <div className="text-2xl font-bold">{standardCount}</div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Permissions</CardTitle>
            <Key className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-8 w-12 animate-pulse rounded bg-muted" />
            ) : (
              <div className="text-2xl font-bold">{data?.total_permissions ?? 0}</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search roles..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant={selectedFilter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedFilter('all')}
          >
            All Roles
          </Button>
          <Button
            variant={selectedFilter === 'privileged' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedFilter('privileged')}
          >
            Privileged
          </Button>
          <Button
            variant={selectedFilter === 'standard' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedFilter('standard')}
          >
            Standard
          </Button>
        </div>
      </div>

      {/* Role cards */}
      <div className="space-y-4">
        {loading ? (
          <>
            {[1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <div className="flex items-center space-x-4">
                    <div className="h-10 w-10 animate-pulse rounded-full bg-muted" />
                    <div className="space-y-2">
                      <div className="h-5 w-32 animate-pulse rounded bg-muted" />
                      <div className="h-4 w-64 animate-pulse rounded bg-muted" />
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="h-24 w-full animate-pulse rounded bg-muted" />
                </CardContent>
              </Card>
            ))}
          </>
        ) : (
          filteredRoles.map((role) => {
            const permsByCategory = role.permissions.reduce<Record<string, string[]>>((acc, p) => {
              const cat = getPermissionCategory(p);
              if (!acc[cat]) acc[cat] = [];
              acc[cat].push(p);
              return acc;
            }, {});

            return (
              <Card key={role.role}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 bg-muted rounded-full flex items-center justify-center">
                        {role.is_privileged ? (
                          <Shield className="h-5 w-5 text-muted-foreground" />
                        ) : (
                          <Users className="h-5 w-5 text-muted-foreground" />
                        )}
                      </div>
                      <div>
                        <CardTitle className="text-lg flex items-center space-x-2">
                          <span>{role.display_name}</span>
                          {role.is_privileged && (
                            <Badge className="bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 text-xs">
                              Privileged
                            </Badge>
                          )}
                        </CardTitle>
                        <CardDescription>{role.description}</CardDescription>
                      </div>
                    </div>
                    <Badge className={getRoleColor(role.role)}>
                      <Lock className="h-3 w-3 mr-1" />
                      <span className="capitalize">{role.role}</span>
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <h4 className="font-medium mb-2 text-sm">
                        Permissions ({role.permission_count})
                      </h4>
                      <div className="space-y-2">
                        {Object.entries(permsByCategory).map(([cat, perms]) => (
                          <div key={cat}>
                            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                              {cat}
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {perms.map((p) => (
                                <Badge key={p} variant="outline" className="text-xs font-mono">
                                  {p}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        ))}
                        {role.permission_count === 0 && (
                          <p className="text-sm text-muted-foreground">No permissions</p>
                        )}
                      </div>
                    </div>
                    <div>
                      <h4 className="font-medium mb-2 text-sm">Access Summary</h4>
                      <div className="space-y-1 text-sm">
                        {[
                          ['Audit Logs', 'audit:read'],
                          ['Policy Management', 'policy:read'],
                          ['System Admin', 'system:admin'],
                          ['User Management', 'user:manage'],
                          ['Tool Execution', 'tool:execute'],
                        ].map(([label, perm]) => (
                          <div
                            key={perm}
                            className="flex items-center space-x-2 text-muted-foreground"
                          >
                            {role.permissions.includes(perm) ? (
                              <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                            ) : (
                              <XCircle className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                            )}
                            <span>{label}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
        {!loading && filteredRoles.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <Users className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No roles found</h3>
              <p className="text-muted-foreground text-center">
                {searchTerm || selectedFilter !== 'all'
                  ? 'Try adjusting your search or filter'
                  : 'No roles configured in the gateway'}
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Auth info card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Key className="h-5 w-5" />
            <span>Authentication</span>
          </CardTitle>
          <CardDescription>Gateway authentication and authorization model</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="font-medium mb-2">Authentication</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• JWT bearer token (Authorization header)</div>
                <div>• Role extracted from token claims</div>
                <div>• Unauthenticated requests treated as guest</div>
                <div>• Roles: admin, developer, user, guest</div>
              </div>
            </div>
            <div>
              <h4 className="font-medium mb-2">Authorization</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• Role-based access control (RBAC)</div>
                <div>• Per-endpoint permission enforcement</div>
                <div>• Audit logging of all access events</div>
                <div>• {data?.total_permissions ?? 16} distinct permissions</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
