'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Shield, 
  Lock, 
  Key, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw,
  Settings,
  Users,
  Database,
  Globe,
  Eye,
  EyeOff
} from 'lucide-react'

export default function SecurityPage() {
  const [securityStats, setSecurityStats] = useState({
    vulnerabilities: {
      critical: 0,
      high: 1,
      medium: 3,
      low: 7
    },
    lastScan: new Date('2026-02-18T08:00:00Z'),
    scanDuration: '2m 34s',
    complianceScore: 94
  })

  const [recentScans] = useState([
    {
      id: 1,
      type: 'CodeQL Security Analysis',
      status: 'completed',
      findings: 11,
      timestamp: new Date('2026-02-18T08:00:00Z'),
      duration: '2m 34s'
    },
    {
      id: 2,
      type: 'Snyk Vulnerability Scan',
      status: 'completed',
      findings: 8,
      timestamp: new Date('2026-02-18T07:30:00Z'),
      duration: '1m 12s'
    },
    {
      id: 3,
      type: 'Trufflehog Secret Scan',
      status: 'completed',
      findings: 0,
      timestamp: new Date('2026-02-18T07:00:00Z'),
      duration: '45s'
    }
  ])

  const [securityPolicies] = useState([
    {
      name: 'Authentication',
      status: 'active',
      description: 'JWT-based authentication with 7-day token expiration',
      lastUpdated: new Date('2026-02-15T10:00:00Z')
    },
    {
      name: 'Row Level Security',
      status: 'active',
      description: 'RLS policies enabled on all user data tables',
      lastUpdated: new Date('2026-02-16T14:30:00Z')
    },
    {
      name: 'API Rate Limiting',
      status: 'active',
      description: 'Rate limiting applied to all API endpoints',
      lastUpdated: new Date('2026-02-14T09:15:00Z')
    },
    {
      name: 'Data Encryption',
      status: 'active',
      description: 'Encryption at rest and in transit for all sensitive data',
      lastUpdated: new Date('2026-02-13T16:45:00Z')
    }
  ])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'warning': return 'bg-yellow-100 text-yellow-800'
      case 'error': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800'
      case 'high': return 'bg-orange-100 text-orange-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const totalVulnerabilities = Object.values(securityStats.vulnerabilities).reduce((a, b) => a + b, 0)

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Security Center</h2>
          <p className="text-muted-foreground">
            Monitor security posture, vulnerability scans, and compliance status
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" />
            Configure
          </Button>
          <Button>
            <RefreshCw className="mr-2 h-4 w-4" />
            Run Scan
          </Button>
        </div>
      </div>

      {/* Security Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliance Score</CardTitle>
            <Shield className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{securityStats.complianceScore}%</div>
            <p className="text-xs text-muted-foreground">Excellent</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Findings</CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{totalVulnerabilities}</div>
            <p className="text-xs text-muted-foreground">Needs attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical Issues</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{securityStats.vulnerabilities.critical}</div>
            <p className="text-xs text-muted-foreground">Immediate action</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Scan</CardTitle>
            <RefreshCw className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{securityStats.scanDuration}</div>
            <p className="text-xs text-muted-foreground">{securityStats.lastScan.toLocaleTimeString()}</p>
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
            <CardDescription>
              Current security findings by severity level
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(securityStats.vulnerabilities).map(([severity, count]) => (
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
                          severity === 'critical' ? 'bg-red-500' :
                          severity === 'high' ? 'bg-orange-500' :
                          severity === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                        }`}
                        style={{ width: `${(count / totalVulnerabilities) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium w-8 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Shield className="h-5 w-5" />
              <span>Security Policies</span>
            </CardTitle>
            <CardDescription>
              Active security policies and configurations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {securityPolicies.map((policy, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    </div>
                    <div>
                      <p className="font-medium">{policy.name}</p>
                      <p className="text-sm text-muted-foreground">{policy.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(policy.status)}>
                      {policy.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Scans */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <RefreshCw className="h-5 w-5" />
            <span>Recent Security Scans</span>
          </CardTitle>
          <CardDescription>
            History of security scans and their results
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentScans.map((scan) => (
              <div key={scan.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-muted rounded-full flex items-center justify-center">
                    <Shield className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="font-medium">{scan.type}</p>
                    <p className="text-sm text-muted-foreground">
                      {scan.findings} findings • {scan.duration}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge className={getStatusColor(scan.status)}>
                    {scan.status}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {scan.timestamp.toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Security Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Security Configuration</span>
          </CardTitle>
          <CardDescription>
            Security tools and scanning configurations
          </CardDescription>
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
          <CardDescription>
            Authentication and authorization settings
          </CardDescription>
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
  )
}
