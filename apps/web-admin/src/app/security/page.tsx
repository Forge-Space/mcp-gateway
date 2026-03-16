'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Shield,
  Lock,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Settings,
  Users,
  Database,
  Globe,
  XCircle,
} from 'lucide-react';

interface VulnerabilityCounts {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

interface SecurityPolicy {
  name: string;
  status: string;
  description: string;
  last_updated: string;
}

interface SecurityStats {
  vulnerabilities: VulnerabilityCounts;
  compliance_score: number;
  policies: SecurityPolicy[];
  last_updated: string;
}

export default function SecurityPage() {
  const [securityStats, setSecurityStats] = useState<SecurityStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch('/api/security/stats');
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
      }
      const data: SecurityStats = await resp.json();
      setSecurityStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load security stats');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'inactive':
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const complianceScore = securityStats?.compliance_score ?? 0;
  const vulnerabilities = securityStats?.vulnerabilities ?? {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  };
  const totalVulnerabilities = Object.values(vulnerabilities).reduce((a, b) => a + b, 0);
  const policies = securityStats?.policies ?? [];

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Security Center</h2>
          <p className="text-muted-foreground">
            Monitor security posture, vulnerability counts, and compliance status
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" />
            Configure
          </Button>
          <Button onClick={fetchStats} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {/* Security Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliance Score</CardTitle>
            <Shield className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-8 w-16 animate-pulse rounded bg-muted" />
            ) : (
              <>
                <div
                  className={`text-2xl font-bold ${complianceScore >= 80 ? 'text-green-600' : complianceScore >= 50 ? 'text-yellow-600' : 'text-red-600'}`}
                >
                  {complianceScore}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {complianceScore >= 80
                    ? 'Excellent'
                    : complianceScore >= 50
                      ? 'Needs improvement'
                      : 'Critical'}
                </p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Findings</CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-8 w-16 animate-pulse rounded bg-muted" />
            ) : (
              <>
                <div className="text-2xl font-bold text-orange-600">{totalVulnerabilities}</div>
                <p className="text-xs text-muted-foreground">
                  {totalVulnerabilities === 0 ? 'All clear' : 'Needs attention'}
                </p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical Issues</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-8 w-16 animate-pulse rounded bg-muted" />
            ) : (
              <>
                <div className="text-2xl font-bold text-red-600">{vulnerabilities.critical}</div>
                <p className="text-xs text-muted-foreground">
                  {vulnerabilities.critical === 0 ? 'None' : 'Immediate action'}
                </p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Updated</CardTitle>
            <RefreshCw className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-8 w-32 animate-pulse rounded bg-muted" />
            ) : (
              <>
                <div className="text-sm font-bold">
                  {securityStats ? new Date(securityStats.last_updated).toLocaleTimeString() : '—'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {securityStats ? new Date(securityStats.last_updated).toLocaleDateString() : ''}
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Vulnerability Breakdown */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5" />
              <span>Vulnerability Breakdown</span>
            </CardTitle>
            <CardDescription>Current security findings by severity level</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-6 animate-pulse rounded bg-muted" />
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {(Object.entries(vulnerabilities) as [string, number][]).map(
                  ([severity, count]) => (
                    <div key={severity} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Badge className={getSeverityColor(severity)}>
                          {severity.charAt(0).toUpperCase() + severity.slice(1)}
                        </Badge>
                        <span className="text-sm font-medium capitalize">{severity}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-muted rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              severity === 'critical'
                                ? 'bg-red-500'
                                : severity === 'high'
                                  ? 'bg-orange-500'
                                  : severity === 'medium'
                                    ? 'bg-yellow-500'
                                    : 'bg-blue-500'
                            }`}
                            style={{
                              width:
                                totalVulnerabilities > 0
                                  ? `${(count / totalVulnerabilities) * 100}%`
                                  : '0%',
                            }}
                          />
                        </div>
                        <span className="text-sm font-medium w-8 text-right">{count}</span>
                      </div>
                    </div>
                  )
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Shield className="h-5 w-5" />
              <span>Security Policies</span>
            </CardTitle>
            <CardDescription>Active security policies and configurations</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-14 animate-pulse rounded bg-muted" />
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {policies.map((policy, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center ${policy.status === 'active' ? 'bg-green-100' : 'bg-red-100'}`}
                      >
                        {policy.status === 'active' ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-600" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium">{policy.name}</p>
                        <p className="text-sm text-muted-foreground">{policy.description}</p>
                      </div>
                    </div>
                    <Badge className={getStatusColor(policy.status)}>{policy.status}</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Security Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Security Configuration</span>
          </CardTitle>
          <CardDescription>Security tools and scanning configurations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="font-medium mb-2">Scanning Tools</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• CodeQL: Semantic security analysis</div>
                <div>• Snyk: Dependency vulnerability scanning</div>
                <div>• Trufflehog: Secret detection</div>
                <div>• ESLint Security: Code security rules</div>
              </div>
            </div>
            <div>
              <h4 className="font-medium mb-2">Scan Schedule</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• CodeQL: On every PR to main/release</div>
                <div>• Snyk: Daily automated scan</div>
                <div>• Trufflehog: On every commit</div>
                <div>• Manual: On-demand scanning available</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Access Control */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Lock className="h-5 w-5" />
            <span>Access Control</span>
          </CardTitle>
          <CardDescription>Authentication and authorization settings</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="flex items-center space-x-3 p-3 border rounded-lg">
              <Users className="h-8 w-8 text-blue-600" />
              <div>
                <p className="font-medium">User Authentication</p>
                <p className="text-sm text-muted-foreground">JWT-based with Supabase</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-3 border rounded-lg">
              <Database className="h-8 w-8 text-green-600" />
              <div>
                <p className="font-medium">Database Security</p>
                <p className="text-sm text-muted-foreground">Row Level Security enabled</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-3 border rounded-lg">
              <Globe className="h-8 w-8 text-purple-600" />
              <div>
                <p className="font-medium">API Security</p>
                <p className="text-sm text-muted-foreground">HTTPS + Rate limiting</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
