'use client'

import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useServerStore } from '@/lib/store'
import {
  Globe,
  Code,
  Server,
  Activity,
  Shield,
  Package,
  Settings,
  Plus,
  Download,
  Upload,
  Zap,
  Database
} from 'lucide-react'

export default function TemplatesPage() {
  const { templates, loading, fetchTemplates } = useServerStore()

  useEffect(() => {
    fetchTemplates()
  }, [fetchTemplates])

  const getCategoryIcon = (category: string): React.ReactElement => {
    switch (category) {
      case 'development': return <Code className="h-4 w-4" />
      case 'production': return <Server className="h-4 w-4" />
      case 'monitoring': return <Activity className="h-4 w-4" />
      case 'security': return <Shield className="h-4 w-4" />
      default: return <Package className="h-4 w-4" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'database': return 'bg-blue-100 text-blue-800'
      case 'security': return 'bg-red-100 text-red-800'
      case 'networking': return 'bg-green-100 text-green-800'
      case 'development': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const stats = [
    {
      title: 'Total Templates',
      value: templates.length,
      icon: Settings,
      color: 'text-blue-600'
    },
    {
      title: 'Categories',
      value: new Set(templates.map(t => t.category)).size,
      icon: Database,
      color: 'text-green-600'
    },
    {
      title: 'Total Tools',
      value: templates.reduce((acc, template) => acc + template.tools.length, 0),
      icon: Zap,
      color: 'text-purple-600'
    },
    {
      title: 'Deployments',
      value: templates.reduce((acc, template) => acc + 3, 0),
      icon: Server,
      color: 'text-orange-600'
    }
  ]

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Server Templates</h2>
          <p className="text-muted-foreground">
            Manage and deploy server templates for quick MCP gateway setup
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Import
          </Button>
          <Button variant="outline">
            <Upload className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Template
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
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Categories Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from(new Set(templates.map(t => t.category))).map((category) => {
          const categoryTemplates = templates.filter(t => t.category === category)
          return (
            <Card key={category}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium capitalize">
                  {category}
                </CardTitle>
                <span className="text-muted-foreground">{getCategoryIcon(category)}</span>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{categoryTemplates.length}</div>
                <p className="text-xs text-muted-foreground">
                  {categoryTemplates.reduce((acc, t) => acc + t.tools.length, 0)} tools total
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Templates List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          templates.map((template) => (
            <Card key={template.id} className="relative">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Settings className="h-6 w-6 text-muted-foreground" />
                    <div>
                      <CardTitle className="text-lg">{template.name}</CardTitle>
                      <CardDescription>{template.description}</CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getCategoryColor(template.category)}>
                      {getCategoryIcon(template.category)}
                      <span className="ml-1 capitalize">{template.category}</span>
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h4 className="font-medium mb-2">Template Details</h4>
                    <div className="space-y-1 text-sm text-muted-foreground">
                      <div>• Version: {template.version || '1.0.0'}</div>
                      <div>• Tools: {template.tools.length}</div>
                      <div>• Deployments: {template.deployments || 0}</div>
                      <div>• Created: {new Date(template.created_at).toLocaleDateString()}</div>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Included Tools</h4>
                    <div className="flex flex-wrap gap-1">
                      {template.tools.slice(0, 8).map((tool) => (
                        <Badge key={tool} variant="outline" className="text-xs">
                          {tool}
                        </Badge>
                      ))}
                      {template.tools.length > 8 && (
                        <Badge variant="outline" className="text-xs">
                          +{template.tools.length - 8} more
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <Settings className="h-4 w-4" />
                    <span>Last updated: {new Date(template.updated_at).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button variant="outline" size="sm">
                      <Download className="mr-2 h-4 w-4" />
                      Download
                    </Button>
                    <Button variant="outline" size="sm">
                      <Settings className="mr-2 h-4 w-4" />
                      Edit
                    </Button>
                    <Button size="sm">
                      <Server className="mr-2 h-4 w-4" />
                      Deploy
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
        {templates.length === 0 && !loading && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <Settings className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No templates available</h3>
              <p className="text-muted-foreground text-center mb-4">
                Create your first server template to streamline MCP gateway deployments.
              </p>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Template
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Template Management Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Template Management</span>
          </CardTitle>
          <CardDescription>
            Create, import, and deploy server templates for consistent configurations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="font-medium mb-2">Available Actions</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div><code className="bg-muted px-1 rounded">mcp template list</code> - List templates</div>
                <div><code className="bg-muted px-1 rounded">mcp template create</code> - Create template</div>
                <div><code className="bg-muted px-1 rounded">mcp template deploy &lt;template&gt;</code> - Deploy template</div>
                <div><code className="bg-muted px-1 rounded">mcp template import &lt;file&gt;</code> - Import template</div>
              </div>
            </div>
            <div>
              <h4 className="font-medium mb-2">Template Features</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• Pre-configured tool sets</div>
                <div>• Environment variables</div>
                <div>• Security policies</div>
                <div>• Performance tuning</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
