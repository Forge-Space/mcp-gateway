'use client'

import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useServerStore, useAnalyticsStore } from '@/lib/store'
import { getSupabaseConfigError } from '@/lib/supabase-config'
import { Activity, Server, Settings, BarChart3, Users, Zap, Rocket } from 'lucide-react'
import { GatewayStatus } from '@/components/dashboard/gateway-status'
import { ServerMetrics } from '@/components/dashboard/server-metrics'
import Link from 'next/link'

export default function Dashboard() {
  const { servers, templates, fetchServers, fetchTemplates } = useServerStore()
  const { analytics, fetchAnalytics } = useAnalyticsStore()
  const configError = getSupabaseConfigError()

  useEffect(() => {
    if (configError) {
      return
    }

    fetchServers()
    fetchTemplates()
    fetchAnalytics('24h')
  }, [configError, fetchServers, fetchTemplates, fetchAnalytics])

  const stats = [
    {
      title: 'Active Servers',
      value: servers.filter(s => s.enabled).length,
      total: servers.length,
      icon: Server,
      color: 'text-blue-600'
    },
    {
      title: 'Total Templates',
      value: templates.length,
      total: templates.length,
      icon: Settings,
      color: 'text-green-600'
    },
    {
      title: 'Usage Events (24h)',
      value: analytics.length,
      total: analytics.length,
      icon: Activity,
      color: 'text-purple-600'
    },
    {
      title: 'System Health',
      value: '98.5%',
      total: '100%',
      icon: Zap,
      color: 'text-orange-600'
    }
  ]

  if (configError) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Configuration required</CardTitle>
            <CardDescription>
              Add the public Supabase variables before using the admin dashboard.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-800">
              {configError}
            </div>
            <div className="rounded-md border border-border bg-muted/30 px-4 py-3 font-mono text-xs text-foreground">
              NEXT_PUBLIC_SUPABASE_URL
              <br />
              NEXT_PUBLIC_SUPABASE_ANON_KEY
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Gateway Status */}
      <GatewayStatus />

      {/* Server Metrics */}
      <ServerMetrics />

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">
                Total: {stat.total}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common management tasks</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button asChild className="w-full">
              <Link href="/mcp-builder">
                <Rocket className="h-4 w-4 mr-2" />
                Build MCP Server
              </Link>
            </Button>
            <Button variant="outline" className="w-full">
              <Settings className="h-4 w-4 mr-2" />
              Manage Servers
            </Button>
            <Button variant="outline" className="w-full">
              <Users className="h-4 w-4 mr-2" />
              User Management
            </Button>
            <Button variant="outline" className="w-full">
              <BarChart3 className="h-4 w-4 mr-2" />
              View Analytics
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
