'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { useServerStore } from '@/lib/store'
import type { Database } from '@/lib/supabase'
import { Server, Plus, Settings, Activity, Zap, Shield, Download, Copy, Check } from 'lucide-react'

type VirtualServer = Database['public']['Tables']['virtual_servers']['Row']

export default function ServersPage() {
  const { servers, loading, fetchServers, toggleServer, deleteServer } = useServerStore()
  const [copiedServer, setCopiedServer] = useState<string | null>(null)
  const [downloadedConfig, setDownloadedConfig] = useState<string | null>(null)

  useEffect(() => {
    fetchServers()
  }, [fetchServers])

  const copyToClipboard = async (text: string, serverName: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedServer(serverName)
      setTimeout(() => setCopiedServer(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const downloadConfig = (server: VirtualServer, ide: string) => {
    const config = generateIDEConfig(server, ide)
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${ide}-${server.name}-config.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    setDownloadedConfig(`${ide}-${server.name}`)
    setTimeout(() => setDownloadedConfig(null), 2000)
  }

  const generateIDEConfig = (server: VirtualServer, ide: string) => {
    const baseConfig = {
      mcpServers: {
        [server.name]: {
          command: "/path/to/forge-mcp-gateway/scripts/cursor-mcp-wrapper.sh",
          args: ["--server-name", server.name],
          env: {
            GATEWAY_URL: "http://localhost:4444",
            SERVER_ID: server.id
          }
        }
      }
    }

    // IDE-specific adjustments
    if (ide === "vscode") {
      return { "mcp.servers": baseConfig.mcpServers }
    }
    return baseConfig
  }

  const getStatusColor = (enabled: boolean) => {
    return enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
  }

  const getStatusIcon = (enabled: boolean) => {
    return enabled ? <Zap className="h-4 w-4" /> : <Shield className="h-4 w-4" />
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Virtual Servers</h2>
          <p className="text-muted-foreground">
            Manage your MCP gateway virtual servers and their configurations
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" />
            Configure CLI
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Server
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Servers</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{servers.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <Zap className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {servers.filter(s => s.enabled).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Inactive</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-muted-foreground">
              {servers.filter(s => !s.enabled).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tools</CardTitle>
            <Activity className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {servers.reduce((acc, server) => acc + server.tools.length, 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Servers List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          servers.map((server) => (
            <Card key={server.id} className="relative">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Server className="h-6 w-6 text-muted-foreground" />
                    <div>
                      <CardTitle className="text-lg">{server.name}</CardTitle>
                      <CardDescription>{server.description}</CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(server.enabled)}>
                      {getStatusIcon(server.enabled)}
                      <span className="ml-1">{server.enabled ? 'Active' : 'Inactive'}</span>
                    </Badge>
                    <Switch
                      checked={server.enabled}
                      onCheckedChange={() => toggleServer(server.id)}
                      disabled={loading}
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h4 className="font-medium mb-2">Configuration</h4>
                    <div className="space-y-1 text-sm text-muted-foreground">
                      <div>• Port: 8080</div>
                      <div>• Host: localhost</div>
                      <div>• Tools: {server.tools.length}</div>
                      <div>• Created: {new Date(server.created_at).toLocaleDateString()}</div>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Available Tools</h4>
                    <div className="flex flex-wrap gap-1">
                      {server.tools.slice(0, 5).map((tool) => (
                        <Badge key={tool} variant="outline" className="text-xs">
                          {tool}
                        </Badge>
                      ))}
                      {server.tools.length > 5 && (
                        <Badge variant="outline" className="text-xs">
                          +{server.tools.length - 5} more
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <Activity className="h-4 w-4" />
                    <span>Last updated: {new Date(server.updated_at).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button variant="outline" size="sm">
                      <Settings className="mr-2 h-4 w-4" />
                      Configure
                    </Button>
                    <Button variant="outline" size="sm">
                      <Activity className="mr-2 h-4 w-4" />
                      View Logs
                    </Button>
                  </div>
                </div>

                {/* IDE Integration Section */}
                <div className="mt-4 pt-4 border-t">
                  <h4 className="font-medium mb-3">IDE Integration</h4>
                  <div className="flex flex-wrap gap-2">
                    <div className="flex items-center space-x-1">
                      <span className="text-sm text-muted-foreground">Cursor:</span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(
                          JSON.stringify(generateIDEConfig(server, 'cursor'), null, 2),
                          `${server.name}-cursor`
                        )}
                      >
                        {copiedServer === `${server.name}-cursor` ? (
                          <Check className="mr-1 h-3 w-3" />
                        ) : (
                          <Copy className="mr-1 h-3 w-3" />
                        )}
                        Copy Config
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => downloadConfig(server, 'cursor')}
                      >
                        {downloadedConfig === `cursor-${server.name}` ? (
                          <Check className="mr-1 h-3 w-3" />
                        ) : (
                          <Download className="mr-1 h-3 w-3" />
                        )}
                        Download
                      </Button>
                    </div>

                    <div className="flex items-center space-x-1">
                      <span className="text-sm text-muted-foreground">VSCode:</span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(
                          JSON.stringify(generateIDEConfig(server, 'vscode'), null, 2),
                          `${server.name}-vscode`
                        )}
                      >
                        {copiedServer === `${server.name}-vscode` ? (
                          <Check className="mr-1 h-3 w-3" />
                        ) : (
                          <Copy className="mr-1 h-3 w-3" />
                        )}
                        Copy Config
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => downloadConfig(server, 'vscode')}
                      >
                        {downloadedConfig === `vscode-${server.name}` ? (
                          <Check className="mr-1 h-3 w-3" />
                        ) : (
                          <Download className="mr-1 h-3 w-3" />
                        )}
                        Download
                      </Button>
                    </div>

                    <div className="flex items-center space-x-1">
                      <span className="text-sm text-muted-foreground">Windsurf:</span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(
                          JSON.stringify(generateIDEConfig(server, 'windsurf'), null, 2),
                          `${server.name}-windsurf`
                        )}
                      >
                        {copiedServer === `${server.name}-windsurf` ? (
                          <Check className="mr-1 h-3 w-3" />
                        ) : (
                          <Copy className="mr-1 h-3 w-3" />
                        )}
                        Copy Config
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => downloadConfig(server, 'windsurf')}
                      >
                        {downloadedConfig === `windsurf-${server.name}` ? (
                          <Check className="mr-1 h-3 w-3" />
                        ) : (
                          <Download className="mr-1 h-3 w-3" />
                        )}
                        Download
                      </Button>
                    </div>

                    <div className="flex items-center space-x-1">
                      <span className="text-sm text-muted-foreground">Claude:</span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(
                          JSON.stringify(generateIDEConfig(server, 'claude'), null, 2),
                          `${server.name}-claude`
                        )}
                      >
                        {copiedServer === `${server.name}-claude` ? (
                          <Check className="mr-1 h-3 w-3" />
                        ) : (
                          <Copy className="mr-1 h-3 w-3" />
                        )}
                        Copy Config
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => downloadConfig(server, 'claude')}
                      >
                        {downloadedConfig === `claude-${server.name}` ? (
                          <Check className="mr-1 h-3 w-3" />
                        ) : (
                          <Download className="mr-1 h-3 w-3" />
                        )}
                        Download
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
        {servers.length === 0 && !loading && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <Server className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No servers configured</h3>
              <p className="text-muted-foreground text-center mb-4">
                Get started by adding your first virtual server to the MCP gateway.
              </p>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Server
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* CLI Integration Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Virtual Server Management</span>
          </CardTitle>
          <CardDescription>
            Manage virtual servers using the MCP gateway CLI and configuration
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="font-medium mb-2">Available Commands</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div><code className="bg-muted px-1 rounded">mcp server list</code> - List all servers</div>
                <div><code className="bg-muted px-1 rounded">mcp server enable &lt;server&gt;</code> - Enable server</div>
                <div><code className="bg-muted px-1 rounded">mcp server disable &lt;server&gt;</code> - Disable server</div>
                <div><code className="bg-muted px-1 rounded">mcp server create</code> - Create new server</div>
              </div>
            </div>
            <div>
              <h4 className="font-medium mb-2">Configuration</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• Config File: config/virtual-servers.yml</div>
                <div>• Server Registry: data/servers/registry.json</div>
                <div>• Auto-reload: Enabled</div>
                <div>• Health Checks: Every 30 seconds</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
