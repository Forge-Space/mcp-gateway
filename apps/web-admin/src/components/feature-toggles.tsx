'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Settings, Zap, Shield, BarChart3, Users, Moon, Sun } from 'lucide-react'

interface Feature {
  name: string
  description: string
  enabled: boolean
  category: 'global' | 'mcp-gateway' | 'uiforge-mcp' | 'uiforge-webapp'
  icon: React.ComponentType<{ className?: string }>
}

export default function FeatureToggles() {
  const [features, setFeatures] = useState<Feature[]>([
    {
      name: 'global.debug-mode',
      description: 'Enable debug logging and monitoring',
      enabled: false,
      category: 'global',
      icon: Settings
    },
    {
      name: 'global.beta-features',
      description: 'Enable beta functionality',
      enabled: false,
      category: 'global',
      icon: Zap
    },
    {
      name: 'global.enhanced-logging',
      description: 'Enable detailed logging',
      enabled: true,
      category: 'global',
      icon: BarChart3
    },
    {
      name: 'mcp-gateway.rate-limiting',
      description: 'Request rate limiting',
      enabled: true,
      category: 'mcp-gateway',
      icon: Shield
    },
    {
      name: 'mcp-gateway.security-headers',
      description: 'Security headers middleware',
      enabled: true,
      category: 'mcp-gateway',
      icon: Shield
    },
    {
      name: 'mcp-gateway.performance-monitoring',
      description: 'Performance monitoring',
      enabled: true,
      category: 'mcp-gateway',
      icon: BarChart3
    },
    {
      name: 'uiforge-mcp.ai-chat',
      description: 'Enable AI chat functionality',
      enabled: false,
      category: 'uiforge-mcp',
      icon: Users
    },
    {
      name: 'uiforge-mcp.template-management',
      description: 'Enable template management',
      enabled: true,
      category: 'uiforge-mcp',
      icon: Settings
    },
    {
      name: 'uiforge-webapp.dark-mode',
      description: 'Enable dark mode',
      enabled: false,
      category: 'uiforge-webapp',
      icon: Moon
    },
    {
      name: 'uiforge-webapp.advanced-analytics',
      description: 'Enable advanced analytics',
      enabled: false,
      category: 'uiforge-webapp',
      icon: BarChart3
    }
  ])

  const [loading, setLoading] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  const categories = [
    { value: 'all', label: 'All Features', color: 'bg-gray-100' },
    { value: 'global', label: 'Global', color: 'bg-blue-100' },
    { value: 'mcp-gateway', label: 'MCP Gateway', color: 'bg-green-100' },
    { value: 'uiforge-mcp', label: 'UIForge MCP', color: 'bg-purple-100' },
    { value: 'uiforge-webapp', label: 'UIForge WebApp', color: 'bg-orange-100' }
  ]

  const filteredFeatures = selectedCategory === 'all'
    ? features
    : features.filter(f => f.category === selectedCategory)

  const toggleFeature = async (featureName: string) => {
    setLoading(true)
    try {
      // Simulate API call to forge-features CLI
      await new Promise(resolve => setTimeout(resolve, 500))

      setFeatures(prev => prev.map(feature =>
        feature.name === featureName
          ? { ...feature, enabled: !feature.enabled }
          : feature
      ))
    } catch (error) {
      console.error('Failed to toggle feature:', error)
    } finally {
      setLoading(false)
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'global': return <Settings className="h-4 w-4" />
      case 'mcp-gateway': return <Shield className="h-4 w-4" />
      case 'uiforge-mcp': return <Users className="h-4 w-4" />
      case 'uiforge-webapp': return <Moon className="h-4 w-4" />
      default: return <Settings className="h-4 w-4" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'global': return 'bg-blue-100 text-blue-800'
      case 'mcp-gateway': return 'bg-green-100 text-green-800'
      case 'uiforge-mcp': return 'bg-purple-100 text-purple-800'
      case 'uiforge-webapp': return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="flex h-16 items-center px-4">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold">Feature Toggles</h1>
          </div>
          <div className="ml-auto flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <Settings className="mr-2 h-4 w-4" />
              Configure CLI
            </Button>
          </div>
        </div>
      </div>

      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Feature Management</h2>
            <p className="text-muted-foreground">
              Manage feature flags across all Forge projects using the centralized forge-features CLI
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline">
              <BarChart3 className="mr-2 h-4 w-4" />
              Export Config
            </Button>
            <Button>
              <Zap className="mr-2 h-4 w-4" />
              Apply Changes
            </Button>
          </div>
        </div>

        {/* Category Filter */}
        <div className="flex space-x-2">
          {categories.map((category) => (
            <Button
              key={category.value}
              variant={selectedCategory === category.value ? "default" : "outline"}
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
              <div className="text-2xl font-bold">{features.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Enabled</CardTitle>
              <Zap className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {features.filter(f => f.enabled).length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Disabled</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-muted-foreground">
                {features.filter(f => !f.enabled).length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Global Features</CardTitle>
              <BarChart3 className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {features.filter(f => f.category === 'global').length}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Features List */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredFeatures.map((feature) => {
            const Icon = feature.icon
            return (
              <Card key={feature.name} className="relative">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Icon className="h-5 w-5 text-muted-foreground" />
                      <Badge className={getCategoryColor(feature.category)}>
                        {feature.category}
                      </Badge>
                    </div>
                    <Switch
                      checked={feature.enabled}
                      onCheckedChange={() => toggleFeature(feature.name)}
                      disabled={loading}
                    />
                  </div>
                  <CardTitle className="text-lg">{feature.name}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Status</span>
                    <span className={`font-medium ${
                      feature.enabled ? 'text-green-600' : 'text-muted-foreground'
                    }`}>
                      {feature.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* CLI Integration Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="h-5 w-5" />
              <span>Forge Features CLI Integration</span>
            </CardTitle>
            <CardDescription>
              This dashboard integrates with the forge-features CLI for centralized feature management
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h4 className="font-medium mb-2">Available Commands</h4>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <div><code className="bg-muted px-1 rounded">forge-features list</code> - List all features</div>
                  <div><code className="bg-muted px-1 rounded">forge-features enable &lt;feature&gt;</code> - Enable feature</div>
                  <div><code className="bg-muted px-1 rounded">forge-features disable &lt;feature&gt;</code> - Disable feature</div>
                  <div><code className="bg-muted px-1 rounded">forge-features status</code> - Show feature status</div>
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-2">Configuration</h4>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <div>• Environment: Development</div>
                  <div>• CLI Path: /Users/lucassantana/Desenvolvimento/forge-patterns/scripts/forge-features</div>
                  <div>• Config File: patterns/feature-toggles/config/centralized-config.yml</div>
                  <div>• Auto-sync: Enabled</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
