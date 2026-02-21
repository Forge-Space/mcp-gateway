'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getServerType, type ServerTypeId } from '@/lib/mcp-server-catalog'
import type { BuilderConfig } from './step-configuration'
import { Check, Copy } from 'lucide-react'

interface StepReviewProps {
  serverTypeId: ServerTypeId
  config: BuilderConfig
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Button variant="ghost" size="sm" onClick={handleCopy} className="h-7 gap-1 text-xs">
      {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
      {copied ? 'Copied' : 'Copy'}
    </Button>
  )
}

export function StepReview({ serverTypeId, config }: StepReviewProps) {
  const serverType = getServerType(serverTypeId)
  if (!serverType) {return null}

  const tools = serverTypeId === 'custom' ? config.customTools : serverType.defaultTools

  const gatewayEntry = `${config.name}|http://localhost:${config.port}/mcp|${config.transport}`

  const dockerSnippet = `  ${config.name}:
    image: ${config.dockerImage || serverType.dockerImage}
    container_name: forge-${config.name}
    restart: unless-stopped
    ports:
      - "${config.port}:${config.port}"
    environment:
${Object.entries(config.environment)
  .map(([k]) => `      ${k}: \${${k}}`)
  .join('\n') || '      # No environment variables configured'}
    networks:
      - mcp-network`

  const ideMcpEntry = JSON.stringify(
    {
      [config.name]: {
        url: `http://localhost:${config.port}/mcp`,
        transport: config.transport.toLowerCase(),
      },
    },
    null,
    2
  )

  const hasRequiredEnvVars = serverType.envVars
    .filter((v) => v.required)
    .every((v) => config.environment[v.key]?.trim())

  const isNameValid = /^[a-z0-9-]+$/.test(config.name) && config.name.length > 0

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Review your configuration</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Verify everything looks correct before deploying.
        </p>
      </div>

      {/* Validation Warnings */}
      {(!isNameValid || !hasRequiredEnvVars) && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-4 space-y-1">
            {!isNameValid && (
              <p className="text-sm text-yellow-800">⚠ Server name is missing or invalid</p>
            )}
            {!hasRequiredEnvVars && (
              <p className="text-sm text-yellow-800">⚠ Some required environment variables are not set</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Summary */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Server Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Type</dt>
              <dd className="font-medium">{serverType.name}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Name</dt>
              <dd className="font-mono font-medium">{config.name || '—'}</dd>
            </div>
            {config.description && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Description</dt>
                <dd className="text-right max-w-xs">{config.description}</dd>
              </div>
            )}
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Port</dt>
              <dd className="font-mono">{config.port}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Transport</dt>
              <dd>
                <Badge variant="outline" className="text-xs">{config.transport}</Badge>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Docker Image</dt>
              <dd className="font-mono text-xs">{config.dockerImage || serverType.dockerImage}</dd>
            </div>
            {tools.length > 0 && (
              <div className="flex justify-between items-start">
                <dt className="text-muted-foreground">Tools</dt>
                <dd className="flex flex-wrap gap-1 justify-end max-w-xs">
                  {tools.slice(0, 5).map((t) => (
                    <Badge key={t} variant="secondary" className="text-xs">{t}</Badge>
                  ))}
                  {tools.length > 5 && (
                    <Badge variant="secondary" className="text-xs">+{tools.length - 5} more</Badge>
                  )}
                </dd>
              </div>
            )}
            {Object.keys(config.environment).length > 0 && (
              <div className="flex justify-between items-start">
                <dt className="text-muted-foreground">Env Vars</dt>
                <dd className="flex flex-wrap gap-1 justify-end">
                  {Object.keys(config.environment).map((k) => (
                    <Badge key={k} variant="outline" className="text-xs font-mono">{k}</Badge>
                  ))}
                </dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>

      {/* Gateway Entry Preview */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">Gateway Entry (gateways.txt)</CardTitle>
            <CopyButton text={gatewayEntry} />
          </div>
        </CardHeader>
        <CardContent>
          <pre className="text-xs bg-muted rounded-md p-3 overflow-x-auto font-mono">
            {gatewayEntry}
          </pre>
          <p className="text-xs text-muted-foreground mt-2">
            This line will be added to <code>config/gateways.txt</code> to register the server with the gateway.
          </p>
        </CardContent>
      </Card>

      {/* Docker Compose Snippet */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">Docker Compose Service</CardTitle>
            <CopyButton text={dockerSnippet} />
          </div>
        </CardHeader>
        <CardContent>
          <pre className="text-xs bg-muted rounded-md p-3 overflow-x-auto font-mono whitespace-pre">
            {dockerSnippet}
          </pre>
        </CardContent>
      </Card>

      {/* IDE MCP Config */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">IDE MCP Config (mcp.json)</CardTitle>
            <CopyButton text={ideMcpEntry} />
          </div>
        </CardHeader>
        <CardContent>
          <pre className="text-xs bg-muted rounded-md p-3 overflow-x-auto font-mono">
            {ideMcpEntry}
          </pre>
          <p className="text-xs text-muted-foreground mt-2">
            Add this to your IDE&apos;s <code>mcp.json</code> after the server is running.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
