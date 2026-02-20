'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  Zap,
  BarChart3,
  PieChart
} from 'lucide-react'

interface AIMetrics {
  provider: string
  model: string
  totalRequests: number
  successfulRequests: number
  failedRequests: number
  averageResponseTime: number
  averageConfidence: number
  successRate: number
  lastUpdated: string
}

interface ProviderMetrics {
  name: string
  models: AIMetrics[]
  totalRequests: number
  successRate: number
  averageResponseTime: number
  status: 'healthy' | 'warning' | 'error'
}

interface LearningMetrics {
  taskType: string
  totalTasks: number
  successRate: number
  averageConfidence: number
  improvementRate: number
  lastUpdated: string
}

export default function AIPerformanceDashboard() {
  const [providerMetrics, setProviderMetrics] = useState<ProviderMetrics[]>([])
  const [learningMetrics, setLearningMetrics] = useState<LearningMetrics[]>([])
  const [selectedProvider, setSelectedProvider] = useState<string>('all')
  const [timeRange, setTimeRange] = useState<string>('24h')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate fetching AI performance metrics
    const fetchMetrics = async () => {
      setLoading(true)

      // Mock data for demonstration
      const mockProviderData: ProviderMetrics[] = [
        {
          name: 'Ollama',
          models: [
            {
              provider: 'Ollama',
              model: 'llama3.2:3b',
              totalRequests: 1250,
              successfulRequests: 1180,
              failedRequests: 70,
              averageResponseTime: 850,
              averageConfidence: 0.82,
              successRate: 94.4,
              lastUpdated: new Date().toISOString()
            },
            {
              provider: 'Ollama',
              model: 'qwen2.5:7b',
              totalRequests: 890,
              successfulRequests: 845,
              failedRequests: 45,
              averageResponseTime: 1200,
              averageConfidence: 0.88,
              successRate: 94.9,
              lastUpdated: new Date().toISOString()
            }
          ],
          totalRequests: 2140,
          successRate: 94.6,
          averageResponseTime: 975,
          status: 'healthy'
        },
        {
          name: 'OpenAI',
          models: [
            {
              provider: 'OpenAI',
              model: 'gpt-4o-mini',
              totalRequests: 2100,
              successfulRequests: 2058,
              failedRequests: 42,
              averageResponseTime: 650,
              averageConfidence: 0.91,
              successRate: 98.0,
              lastUpdated: new Date().toISOString()
            }
          ],
          totalRequests: 2100,
          successRate: 98.0,
          averageResponseTime: 650,
          status: 'healthy'
        },
        {
          name: 'Anthropic',
          models: [
            {
              provider: 'Anthropic',
              model: 'claude-haiku',
              totalRequests: 1680,
              successfulRequests: 1596,
              failedRequests: 84,
              averageResponseTime: 720,
              averageConfidence: 0.89,
              successRate: 95.0,
              lastUpdated: new Date().toISOString()
            }
          ],
          totalRequests: 1680,
          successRate: 95.0,
          averageResponseTime: 720,
          status: 'healthy'
        }
      ]

      const mockLearningData: LearningMetrics[] = [
        {
          taskType: 'file_operations',
          totalTasks: 450,
          successRate: 92.5,
          averageConfidence: 0.85,
          improvementRate: 5.2,
          lastUpdated: new Date().toISOString()
        },
        {
          taskType: 'data_analysis',
          totalTasks: 320,
          successRate: 88.7,
          averageConfidence: 0.82,
          improvementRate: 3.8,
          lastUpdated: new Date().toISOString()
        },
        {
          taskType: 'code_generation',
          totalTasks: 280,
          successRate: 85.3,
          averageConfidence: 0.79,
          improvementRate: 7.1,
          lastUpdated: new Date().toISOString()
        },
        {
          taskType: 'search_queries',
          totalTasks: 890,
          successRate: 96.2,
          averageConfidence: 0.91,
          improvementRate: 2.4,
          lastUpdated: new Date().toISOString()
        }
      ]

      setProviderMetrics(mockProviderData)
      setLearningMetrics(mockLearningData)
      setLoading(false)
    }

    fetchMetrics()

    // Set up real-time updates
    const interval = setInterval(fetchMetrics, 30000) // Update every 30 seconds

    return () => clearInterval(interval)
  }, [timeRange])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500'
      case 'warning':
        return 'bg-yellow-500'
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4" />
      case 'warning':
        return <Activity className="w-4 h-4" />
      case 'error':
        return <XCircle className="w-4 h-4" />
      default:
        return <Clock className="w-4 h-4" />
    }
  }

  const getImprovementIcon = (rate: number) => {
    return rate > 0 ? (
      <TrendingUp className="w-4 h-4 text-green-500" />
    ) : (
      <TrendingDown className="w-4 h-4 text-red-500" />
    )
  }

  const filteredProviders = selectedProvider === 'all'
    ? providerMetrics
    : providerMetrics.filter(p => p.name === selectedProvider)

  const totalRequests = filteredProviders.reduce((sum, p) => sum + p.totalRequests, 0)
  const averageSuccessRate = filteredProviders.length > 0
    ? filteredProviders.reduce((sum, p) => sum + p.successRate, 0) / filteredProviders.length
    : 0
  const averageResponseTime = filteredProviders.length > 0
    ? filteredProviders.reduce((sum, p) => sum + p.averageResponseTime, 0) / filteredProviders.length
    : 0

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">AI Performance Dashboard</h2>
          <p className="text-muted-foreground">
            Monitor AI tool selection performance and learning metrics
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Providers</option>
            <option value="Ollama">Ollama</option>
            <option value="OpenAI">OpenAI</option>
            <option value="Anthropic">Anthropic</option>
          </select>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalRequests.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Across all providers
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{averageSuccessRate.toFixed(1)}%</div>
            <Progress value={averageSuccessRate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{averageResponseTime}ms</div>
            <p className="text-xs text-muted-foreground">
              Across all providers
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Models</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {filteredProviders.reduce((sum, p) => sum + p.models.length, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Currently active
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Provider Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Provider Performance
            </CardTitle>
            <CardDescription>
              Success rates and response times by provider
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredProviders.map((provider) => (
                <div key={provider.name} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${getStatusColor(provider.status)}`} />
                      <span className="font-medium">{provider.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(provider.status)}
                      <span className="text-sm text-muted-foreground">
                        {provider.totalRequests} requests
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="flex items-center justify-between">
                        <span>Success Rate</span>
                        <span className="font-medium">{provider.successRate.toFixed(1)}%</span>
                      </div>
                      <Progress value={provider.successRate} className="mt-1" />
                    </div>
                    <div>
                      <div className="flex items-center justify-between">
                        <span>Avg Time</span>
                        <span className="font-medium">{provider.averageResponseTime}ms</span>
                      </div>
                      <div className="mt-1 h-2 bg-gray-200 rounded">
                        <div
                          className="h-2 bg-blue-500 rounded"
                          style={{ width: `${Math.min((provider.averageResponseTime / 2000) * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              Learning Progress
            </CardTitle>
            <CardDescription>
              Task type performance and improvement
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {learningMetrics.map((metric) => (
                <div key={metric.taskType} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium capitalize">{metric.taskType.replace('_', ' ')}</span>
                    <div className="flex items-center gap-1">
                      {getImprovementIcon(metric.improvementRate)}
                      <span className="text-sm text-muted-foreground">
                        {metric.improvementRate > 0 ? '+' : ''}{metric.improvementRate.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="flex items-center justify-between">
                        <span>Success Rate</span>
                        <span className="font-medium">{metric.successRate.toFixed(1)}%</span>
                      </div>
                      <Progress value={metric.successRate} className="mt-1" />
                    </div>
                    <div>
                      <div className="flex items-center justify-between">
                        <span>Confidence</span>
                        <span className="font-medium">{(metric.averageConfidence * 100).toFixed(0)}%</span>
                      </div>
                      <div className="mt-1 h-2 bg-gray-200 rounded">
                        <div
                          className="h-2 bg-green-500 rounded"
                          style={{ width: `${metric.averageConfidence * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {metric.totalTasks} tasks completed
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Model Details */}
      <Card>
        <CardHeader>
          <CardTitle>Model Performance Details</CardTitle>
          <CardDescription>
            Detailed metrics for each AI model
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Provider</th>
                  <th className="text-left py-2">Model</th>
                  <th className="text-right py-2">Requests</th>
                  <th className="text-right py-2">Success Rate</th>
                  <th className="text-right py-2">Avg Response</th>
                  <th className="text-right py-2">Avg Confidence</th>
                  <th className="text-center py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredProviders.flatMap(provider =>
                  provider.models.map(model => (
                    <tr key={`${provider.name}-${model.model}`} className="border-b">
                      <td className="py-2">{provider.name}</td>
                      <td className="py-2">{model.model}</td>
                      <td className="text-right py-2">{model.totalRequests}</td>
                      <td className="text-right py-2">
                        <Badge variant={model.successRate > 90 ? "default" : "secondary"}>
                          {model.successRate.toFixed(1)}%
                        </Badge>
                      </td>
                      <td className="text-right py-2">{model.averageResponseTime}ms</td>
                      <td className="text-right py-2">{(model.averageConfidence * 100).toFixed(0)}%</td>
                      <td className="text-center py-2">
                        <Badge variant={model.successRate > 90 ? "default" : "destructive"}>
                          {model.successRate > 90 ? "Good" : "Needs Attention"}
                        </Badge>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
