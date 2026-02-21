'use client'

import { useState } from 'react'
import { MCPBuilder } from '@/components/mcp-builder/mcp-builder'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Plus, Rocket } from 'lucide-react'
import Link from 'next/link'

export default function MCPBuilderPage() {
  const [isBuilding, setIsBuilding] = useState(false)
  const [completedServerId, setCompletedServerId] = useState<string | null>(null)

  const handleBuilderComplete = (serverId: string) => {
    setCompletedServerId(serverId)
    setIsBuilding(false)
  }

  const handleBuilderCancel = () => {
    setIsBuilding(false)
  }

  const handleStartBuilding = () => {
    setIsBuilding(true)
    setCompletedServerId(null)
  }

  if (isBuilding) {
    return (
      <div className="container mx-auto py-6">
        <div className="mb-6">
          <Link href="/admin">
            <Button variant="ghost" className="mb-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Admin
            </Button>
          </Link>
          <MCPBuilder
            onComplete={handleBuilderComplete}
            onCancel={handleBuilderCancel}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6">
      <div className="mb-6">
        <Link href="/admin">
          <Button variant="ghost" className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Admin
          </Button>
        </Link>
      </div>

        {completedServerId ? (
          <Card className="max-w-2xl mx-auto">
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <Rocket className="h-8 w-8 text-green-600" />
              </div>
              <CardTitle className="text-2xl">Server Deployed Successfully!</CardTitle>
              <CardDescription>
                Your MCP server has been deployed and is ready to use.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-4">
                  Server ID: <code className="bg-muted px-2 py-1 rounded">{completedServerId}</code>
                </p>
                <div className="flex justify-center space-x-4">
                  <Button onClick={handleStartBuilding}>
                    <Plus className="h-4 w-4 mr-2" />
                    Build Another Server
                  </Button>
                  <Button variant="outline" asChild>
                    <Link href="/admin">Back to Admin</Link>
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="max-w-2xl mx-auto">
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <Rocket className="h-8 w-8 text-blue-600" />
              </div>
              <CardTitle className="text-2xl">MCP Server Builder</CardTitle>
              <CardDescription>
                Create and deploy new MCP servers with our step-by-step wizard.
                Choose from pre-configured server types or build custom solutions.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">8+</div>
                  <div className="text-sm text-muted-foreground">Server Types</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">1-Click</div>
                  <div className="text-sm text-muted-foreground">Deployment</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">Auto</div>
                  <div className="text-sm text-muted-foreground">Configuration</div>
                </div>
              </div>

              <div className="text-center">
                <Button size="lg" onClick={handleStartBuilding} className="px-8">
                  <Rocket className="h-5 w-5 mr-2" />
                  Start Building
                </Button>
                <p className="text-sm text-muted-foreground mt-2">
                  No configuration required • Works with all major MCP servers
                </p>
              </div>

              <div className="border-t pt-6">
                <h3 className="font-medium mb-4">Available Server Types:</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>Filesystem</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>GitHub</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span>Database</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                    <span>AI Models</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span>Web Fetch</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                    <span>Memory</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                    <span>Sequential</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                    <span>Custom</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
    </div>
  )
}
