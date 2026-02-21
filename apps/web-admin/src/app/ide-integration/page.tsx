'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Monitor,
  Download,
  Copy,
  Check,
  AlertCircle,
  Terminal,
  Zap,
  Settings,
  Globe,
  Code,
  FileText,
  RefreshCw
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface IDEConfig {
  name: string
  icon: React.ReactNode
  configPath: string
  detected: boolean
  configTemplate: string
  instructions: string[]
}

interface ServerInfo {
  id: string
  name: string
  url: string
  enabled: boolean
  tools: number
  description: string
}

export default function IDEIntegrationPage() {
  const { toast } = useToast()
  const [servers, setServers] = useState<ServerInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [copiedConfig, setCopiedConfig] = useState<string | null>(null)
  const [detectedIDEs, setDetectedIDEs] = useState<string[]>([])

  const ides: IDEConfig[] = [
    {
      name: 'Cursor',
      icon: <Code className="h-5 w-5" />,
      configPath: '~/.cursor/mcp.json',
      detected: detectedIDEs.includes('cursor'),
      configTemplate: `{
  "mcpServers": {
    "forge-mcp-gateway": {
      "command": "npx -y @forge-mcp-gateway/client",
      "args": ["--url", "http://localhost:4444/sse"]
    }
  }
}`,
      instructions: [
        'Open Cursor settings (Cmd+,)',
        'Navigate to Extensions → MCP Servers',
        'Add the configuration above',
        'Restart Cursor to apply changes'
      ]
    },
    {
      name: 'Windsurf',
      icon: <Globe className="h-5 w-5" />,
      configPath: '~/.codeium/windsurf/mcp_config.json',
      detected: detectedIDEs.includes('windsurf'),
      configTemplate: `{
  "mcpServers": {
    "forge-mcp-gateway": {
      "command": "npx -y @forge-mcp-gateway/client",
      "args": ["--url", "http://localhost:4444/sse"]
    }
  }
}`,
      instructions: [
        'Open Windsurf settings (Cmd+,)',
        'Navigate to Extensions → MCP Servers',
        'Add the configuration above',
        'Restart Windsurf to apply changes'
      ]
    },
    {
      name: 'VS Code',
      icon: <Monitor className="h-5 w-5" />,
      configPath: '~/.vscode/mcp.json',
      detected: detectedIDEs.includes('vscode'),
      configTemplate: `{
  "mcpServers": {
    "forge-mcp-gateway": {
      "command": "npx -y @forge-mcp-gateway/client",
      "args": ["--url", "http://localhost:4444/sse"]
    }
  }
}`,
      instructions: [
        'Install MCP extension for VS Code',
        'Open settings (Cmd+,)',
        'Add MCP server configuration',
        'Restart VS Code'
      ]
    },
    {
      name: 'Claude Desktop',
      icon: <FileText className="h-5 w-5" />,
      configPath: '~/Library/Application Support/Claude/claude_desktop_config.json',
      detected: detectedIDEs.includes('claude'),
      configTemplate: `{
  "mcpServers": {
    "forge-mcp-gateway": {
      "command": "npx -y @forge-mcp-gateway/client",
      "args": ["--url", "http://localhost:4444/sse"]
    }
  }
}`,
      instructions: [
        'Open Claude Desktop settings',
        'Navigate to Developer → Edit Config',
        'Add the configuration above',
        'Restart Claude Desktop'
      ]
    }
  ]

  useEffect(() => {
    fetchServers()
    detectIDEs()
  }, [])

  const fetchServers = async () => {
    try {
      const response = await fetch('/api/servers')
      const data = await response.json()
      setServers(data.filter((server: ServerInfo) => server.enabled))
    } catch (error) {
      console.error('Failed to fetch servers:', error)
    } finally {
      setLoading(false)
    }
  }

  const detectIDEs = async () => {
    try {
      const response = await fetch('/api/ides/detect')
      const data = await response.json()
      setDetectedIDEs(data.detected || [])
    } catch (error) {
      console.error('Failed to detect IDEs:', error)
      // Fallback to common IDE detection
      setDetectedIDEs(['cursor', 'windsurf'])
    }
  }

  const copyToClipboard = async (text: string, configName: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedConfig(configName)
      toast({
        title: "Configuration copied!",
        description: `${configName} configuration copied to clipboard`,
      })
      setTimeout(() => setCopiedConfig(null), 3000)
    } catch (error) {
      toast({
        title: "Failed to copy",
        description: "Please copy the configuration manually",
        variant: "destructive"
      })
    }
  }

  const generateFullConfig = (ideName: string) => {
    const selectedServer = servers.find(s => s.name.includes('default') || s.name.includes('router'))
    if (!selectedServer) return ides.find(ide => ide.name === ideName)?.configTemplate || ''

    return `{
  "mcpServers": {
    "forge-mcp-gateway": {
      "command": "npx -y @forge-mcp-gateway/client",
      "args": ["--url", "${selectedServer.url}"],
      "env": {
        "GATEWAY_URL": "http://localhost:4444"
      }
    }
  }
}`
  }

  const downloadConfig = (ideName: string, config: string) => {
    const blob = new Blob([config], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${ideName.toLowerCase().replace(/\s+/g, '-')}-mcp-config.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    toast({
      title: "Configuration downloaded!",
      description: `${ideName} configuration file downloaded`,
    })
  }

  const refreshDetection = () => {
    detectIDEs()
    toast({
      title: "IDE Detection Refreshed",
      description: "Scanning for installed IDEs...",
    })
  }

  if (loading) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">IDE Integration</h2>
          <p className="text-muted-foreground">
            Configure your IDE to connect to the MCP gateway with one-click setup
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={refreshDetection}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Detect IDEs
          </Button>
          <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" />
            Advanced Settings
          </Button>
        </div>
      </div>

      {/* Server Status */}
      <Alert>
        <Zap className="h-4 w-4" />
        <AlertDescription>
          <strong>Gateway Status:</strong> {servers.length} virtual servers available •
          <span className="ml-2">Ready to connect IDEs</span>
        </AlertDescription>
      </Alert>

      <Tabs defaultValue="setup" className="space-y-4">
        <TabsList>
          <TabsTrigger value="setup">Quick Setup</TabsTrigger>
          <TabsTrigger value="advanced">Advanced Configuration</TabsTrigger>
          <TabsTrigger value="troubleshoot">Troubleshooting</TabsTrigger>
        </TabsList>

        <TabsContent value="setup" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            {ides.map((ide) => (
              <Card key={ide.name} className="relative">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {ide.icon}
                      <div>
                        <CardTitle className="text-lg">{ide.name}</CardTitle>
                        <CardDescription>{ide.configPath}</CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {ide.detected && (
                        <Badge variant="secondary" className="bg-green-100 text-green-800">
                          <Check className="h-3 w-3 mr-1" />
                          Detected
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2">Configuration</h4>
                    <div className="relative">
                      <pre className="bg-muted p-3 rounded text-xs overflow-x-auto">
                        {generateFullConfig(ide.name)}
                      </pre>
                      <div className="absolute top-2 right-2 flex space-x-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => copyToClipboard(generateFullConfig(ide.name), ide.name)}
                        >
                          {copiedConfig === ide.name ? (
                            <Check className="h-3 w-3" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => downloadConfig(ide.name, generateFullConfig(ide.name))}
                        >
                          <Download className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium mb-2">Setup Instructions</h4>
                    <ol className="text-sm text-muted-foreground space-y-1">
                      {ide.instructions.map((instruction, index) => (
                        <li key={index} className="flex items-start">
                          <span className="font-mono mr-2">{index + 1}.</span>
                          <span>{instruction}</span>
                        </li>
                      ))}
                    </ol>
                  </div>

                  <div className="pt-2 border-t">
                    <Button className="w-full">
                      <Terminal className="mr-2 h-4 w-4" />
                      Configure {ide.name}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="advanced" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Advanced Configuration Options</CardTitle>
              <CardDescription>
                Customize your MCP gateway connection with advanced settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="font-medium mb-2">Available Virtual Servers</h4>
                <div className="grid gap-2">
                  {servers.map((server) => (
                    <div key={server.id} className="flex items-center justify-between p-3 border rounded">
                      <div>
                        <div className="font-medium">{server.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {server.tools} tools • {server.enabled ? 'Active' : 'Inactive'}
                        </div>
                      </div>
                      <Badge variant={server.enabled ? 'default' : 'secondary'}>
                        {server.enabled ? 'Use' : 'Disabled'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">Connection Methods</h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">NPX Client (Recommended)</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <p className="text-sm text-muted-foreground mb-2">
                        Cross-platform client with automatic JWT handling
                      </p>
                      <code className="text-xs bg-muted p-1 rounded">
                        npx -y @forge-mcp-gateway/client
                      </code>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Direct Connection</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <p className="text-sm text-muted-foreground mb-2">
                        Direct SSE connection with manual JWT
                      </p>
                      <code className="text-xs bg-muted p-1 rounded">
                        http://localhost:4444/sse
                      </code>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="troubleshoot" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5" />
                <span>Troubleshooting</span>
              </CardTitle>
              <CardDescription>
                Common issues and solutions for IDE integration
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="font-medium mb-3">Common Issues</h4>
                <div className="space-y-4">
                  <div className="p-3 border rounded">
                    <div className="font-medium text-sm mb-1">Connection Timeout</div>
                    <div className="text-sm text-muted-foreground mb-2">
                      IDE can&apos;t connect to the gateway
                    </div>
                    <div className="text-xs bg-muted p-2 rounded">
                      Solution: Ensure gateway is running with <code>make start</code> and
                      check port 4444 availability
                    </div>
                  </div>

                  <div className="p-3 border rounded">
                    <div className="font-medium text-sm mb-1">Authentication Failed</div>
                    <div className="text-sm text-muted-foreground mb-2">
                      JWT token expired or invalid
                    </div>
                    <div className="text-xs bg-muted p-2 rounded">
                      Solution: Generate new token with <code>make jwt</code> and
                      update configuration
                    </div>
                  </div>

                  <div className="p-3 border rounded">
                    <div className="font-medium text-sm mb-1">No Tools Available</div>
                    <div className="text-sm text-muted-foreground mb-2">
                      MCP server shows 0 tools
                    </div>
                    <div className="text-xs bg-muted p-2 rounded">
                      Solution: Register gateways with <code>make register</code> and
                      restart IDE
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-3">Quick Commands</h4>
                <div className="grid gap-2 text-sm">
                  <div className="flex justify-between p-2 bg-muted rounded">
                    <span>Check gateway status</span>
                    <code className="text-xs">make status</code>
                  </div>
                  <div className="flex justify-between p-2 bg-muted rounded">
                    <span>List virtual servers</span>
                    <code className="text-xs">make list-servers</code>
                  </div>
                  <div className="flex justify-between p-2 bg-muted rounded">
                    <span>Generate JWT token</span>
                    <code className="text-xs">make jwt</code>
                  </div>
                  <div className="flex justify-between p-2 bg-muted rounded">
                    <span>Register gateways</span>
                    <code className="text-xs">make register</code>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
