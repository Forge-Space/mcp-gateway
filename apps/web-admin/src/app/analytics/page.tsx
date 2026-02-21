'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useAnalyticsStore } from '@/lib/store'
import {
  BarChart3,
  Activity,
  TrendingUp,
  Users,
  Server,
  Zap,
  Download,
  Calendar
} from 'lucide-react'

export default function AnalyticsPage() {
  const { analytics, loading, fetchAnalytics } = useAnalyticsStore()
  const [timeRange, setTimeRange] = useState('24h')

  useEffect(() => {
    fetchAnalytics(timeRange)
  }, [fetchAnalytics, timeRange])

  const timeRanges = [
    { value: '1h', label: 'Last Hour' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' }
  ]

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'server_request': return <Server className="h-4 w-4" />
      case 'tool_execution': return <Zap className="h-4 w-4" />
      case 'user_login': return <Users className="h-4 w-4" />
      case 'feature_toggle': return <Activity className="h-4 w-4" />
      default: return <Activity className="h-4 w-4" />
    }
  }

  const getActionColor = (action: string) => {
    switch (action) {
      case 'server_request': return 'bg-blue-100 text-blue-800'
      case 'tool_execution': return 'bg-green-100 text-green-800'
      case 'user_login': return 'bg-purple-100 text-purple-800'
      case 'feature_toggle': return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const stats = [
    {
      title: 'Total Events',
      value: analytics.length,
      icon: Activity,
      color: 'text-blue-600',
      change: '+12%'
    },
    {
      title: 'Server Requests',
      value: analytics.filter(a => a.action === 'server_request').length,
      icon: Server,
      color: 'text-green-600',
      change: '+8%'
    },
    {
      title: 'Tool Executions',
      value: analytics.filter(a => a.action === 'tool_execution').length,
      icon: Zap,
      color: 'text-purple-600',
      change: '+15%'
    },
    {
      title: 'Active Users',
      value: new Set(analytics.filter(a => a.user_id).map(a => a.user_id)).size,
      icon: Users,
      color: 'text-orange-600',
      change: '+5%'
    }
  ]

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Usage Analytics</h2>
          <p className="text-muted-foreground">
            Monitor gateway usage, performance metrics, and user activity
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1">
            {timeRanges.map((range) => (
              <Button
                key={range.value}
                variant={timeRange === range.value ? "default" : "outline"}
                size="sm"
                onClick={() => setTimeRange(range.value)}
              >
                {range.label}
              </Button>
            ))}
          </div>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <Card key={index}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground flex items-center">
                  <TrendingUp className="h-3 w-3 mr-1 text-green-600" />
                  {stat.change} from last period
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Charts Section */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>Activity Timeline</span>
            </CardTitle>
            <CardDescription>
              System activity over the selected time period
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-muted-foreground border rounded-lg">
              <div className="text-center">
                <BarChart3 className="h-12 w-12 mx-auto mb-2" />
                <p>Chart visualization would go here</p>
                <p className="text-sm">Integration with charting library needed</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Action Distribution</span>
            </CardTitle>
            <CardDescription>
              Breakdown of different action types
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {['server_request', 'tool_execution', 'user_login', 'feature_toggle'].map((action) => {
                const count = analytics.filter(a => a.action === action).length
                const percentage = analytics.length > 0 ? (count / analytics.length * 100).toFixed(1) : '0'
                return (
                  <div key={action} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getActionIcon(action)}
                      <span className="text-sm font-medium capitalize">{action.replace('_', ' ')}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-muted rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full"
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-muted-foreground w-12 text-right">{percentage}%</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>Recent Activity</span>
          </CardTitle>
          <CardDescription>
            Latest system events and user actions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : (
              analytics.slice(0, 10).map((event, index) => (
                <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      {getActionIcon(event.action)}
                      <Badge className={getActionColor(event.action)}>
                        {event.action.replace('_', ' ')}
                      </Badge>
                    </div>
                    <div>
                      <p className="font-medium">{String(event.metadata?.description ?? 'System event')}</p>
                      <p className="text-sm text-muted-foreground">
                        {event.user_id ? `User ${event.user_id}` : 'System'} • {event.server_id ? `Server ${event.server_id}` : 'Global'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>{new Date(event.timestamp).toLocaleString()}</span>
                  </div>
                </div>
              ))
            )}
            {analytics.length === 0 && !loading && (
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="h-12 w-12 mx-auto mb-2" />
                <p>No activity data available</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Analytics Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Analytics Configuration</span>
          </CardTitle>
          <CardDescription>
            Configure data collection and monitoring settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="font-medium mb-2">Data Collection</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• Collection Mode: Real-time</div>
                <div>• Retention Period: 30 days</div>
                <div>• Sampling Rate: 100%</div>
                <div>• Data Source: Gateway logs</div>
              </div>
            </div>
            <div>
              <h4 className="font-medium mb-2">Monitoring</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• Performance Metrics: Enabled</div>
                <div>• Error Tracking: Enabled</div>
                <div>• User Analytics: Enabled</div>
                <div>• System Health: Enabled</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
