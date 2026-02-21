'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { getServerType, type ServerTypeId } from '@/lib/mcp-server-catalog'
import { Eye, EyeOff, Plus, Trash2 } from 'lucide-react'

export interface BuilderConfig {
  name: string
  description: string
  transport: 'SSE' | 'STREAMABLEHTTP'
  port: number
  dockerImage: string
  environment: Record<string, string>
  customTools: string[]
}

interface StepConfigurationProps {
  serverTypeId: ServerTypeId
  config: BuilderConfig
  usedPorts: number[]
  onChange: (config: BuilderConfig) => void
}

export function StepConfiguration({ serverTypeId, config, usedPorts, onChange }: StepConfigurationProps) {
  const serverType = getServerType(serverTypeId)
  const [revealedSecrets, setRevealedSecrets] = useState<Set<string>>(new Set())
  const [newToolName, setNewToolName] = useState('')

  if (!serverType) {return null}

  const update = (partial: Partial<BuilderConfig>) => {
    onChange({ ...config, ...partial })
  }

  const updateEnvVar = (key: string, value: string) => {
    onChange({ ...config, environment: { ...config.environment, [key]: value } })
  }

  const toggleReveal = (key: string) => {
    setRevealedSecrets((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  const addCustomTool = () => {
    const trimmed = newToolName.trim()
    if (!trimmed || config.customTools.includes(trimmed)) {return}
    update({ customTools: [...config.customTools, trimmed] })
    setNewToolName('')
  }

  const removeCustomTool = (tool: string) => {
    update({ customTools: config.customTools.filter((t) => t !== tool) })
  }

  const isPortConflict = usedPorts.includes(config.port)
  const isNameValid = /^[a-z0-9-]+$/.test(config.name)

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Configure your server</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Set up the details for your <strong>{serverType.name}</strong> server.
        </p>
      </div>

      {/* Basic Info */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium">
              Server Name <span className="text-destructive">*</span>
            </label>
            <Input
              value={config.name}
              onChange={(e) => update({ name: e.target.value.toLowerCase().replace(/\s+/g, '-') })}
              placeholder="my-github-server"
            />
            {config.name && !isNameValid && (
              <p className="text-xs text-destructive">Only lowercase letters, numbers, and hyphens allowed</p>
            )}
            <p className="text-xs text-muted-foreground">Used as the container name and gateway identifier</p>
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium">Description</label>
            <Input
              value={config.description}
              onChange={(e) => update({ description: e.target.value })}
              placeholder="Brief description of what this server does"
            />
          </div>
        </CardContent>
      </Card>

      {/* Network */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Network Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1">
              <label className="text-sm font-medium">
                Port <span className="text-destructive">*</span>
              </label>
              <Input
                type="number"
                value={config.port}
                onChange={(e) => update({ port: parseInt(e.target.value, 10) || serverType.defaultPort })}
                min={8000}
                max={9999}
              />
              {isPortConflict && (
                <p className="text-xs text-destructive">Port {config.port} is already in use</p>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">Transport</label>
              <div className="flex gap-2">
                {(['SSE', 'STREAMABLEHTTP'] as const).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => update({ transport: t })}
                    className={`flex-1 rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                      config.transport === t
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-border bg-background text-muted-foreground hover:border-primary/50'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {serverTypeId === 'custom' && (
            <div className="space-y-1">
              <label className="text-sm font-medium">
                Docker Image <span className="text-destructive">*</span>
              </label>
              <Input
                value={config.dockerImage}
                onChange={(e) => update({ dockerImage: e.target.value })}
                placeholder="my-org/my-mcp-server:latest"
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Environment Variables */}
      {serverType.envVars.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Environment Variables</CardTitle>
            <CardDescription className="text-xs">
              Configure the required settings for this server type
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {serverType.envVars.map((spec) => (
              <div key={spec.key} className="space-y-1">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium">
                    {spec.label}
                    {spec.required && <span className="text-destructive ml-1">*</span>}
                  </label>
                  {spec.secret && (
                    <Badge variant="outline" className="text-xs bg-yellow-50 text-yellow-700 border-yellow-200">
                      Secret
                    </Badge>
                  )}
                </div>
                <div className="relative">
                  <Input
                    type={spec.secret && !revealedSecrets.has(spec.key) ? 'password' : 'text'}
                    value={config.environment[spec.key] ?? ''}
                    onChange={(e) => updateEnvVar(spec.key, e.target.value)}
                    placeholder={spec.placeholder}
                    className={spec.secret ? 'pr-10' : ''}
                  />
                  {spec.secret && (
                    <button
                      type="button"
                      onClick={() => toggleReveal(spec.key)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {revealedSecrets.has(spec.key) ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  )}
                </div>
                {spec.description && (
                  <p className="text-xs text-muted-foreground">{spec.description}</p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Custom Tools (for custom type) */}
      {serverTypeId === 'custom' && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Tools</CardTitle>
            <CardDescription className="text-xs">
              List the tool names this server exposes (optional, for documentation)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <Input
                value={newToolName}
                onChange={(e) => setNewToolName(e.target.value)}
                placeholder="tool_name"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addCustomTool()
                  }
                }}
              />
              <Button type="button" variant="outline" size="sm" onClick={addCustomTool}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            {config.customTools.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {config.customTools.map((tool) => (
                  <Badge key={tool} variant="outline" className="gap-1 pr-1">
                    {tool}
                    <button
                      type="button"
                      onClick={() => removeCustomTool(tool)}
                      className="ml-1 hover:text-destructive"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
