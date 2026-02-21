'use client'

import { useEffect, useRef, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { getServerType, type ServerTypeId } from '@/lib/mcp-server-catalog'
import type { BuilderConfig } from './step-configuration'
import { Check, CheckCircle2, Circle, Copy, Loader2, XCircle } from 'lucide-react'
import { useServerStore } from '@/lib/store'

type StepStatus = 'pending' | 'running' | 'done' | 'error'

interface DeployStep {
  id: string
  label: string
  status: StepStatus
  detail?: string
}

interface StepDeployProps {
  serverTypeId: ServerTypeId
  config: BuilderConfig
  onComplete: (serverId: string) => void
}

function StepIcon({ status }: { status: StepStatus }) {
  if (status === 'running') {return <Loader2 className="h-4 w-4 animate-spin text-primary" />}
  if (status === 'done') {return <CheckCircle2 className="h-4 w-4 text-green-600" />}
  if (status === 'error') {return <XCircle className="h-4 w-4 text-destructive" />}
  return <Circle className="h-4 w-4 text-muted-foreground" />
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

const SERVICE_MANAGER_URL =
  process.env.NEXT_PUBLIC_SERVICE_MANAGER_URL ?? 'http://localhost:9000'

export function StepDeploy({ serverTypeId, config, onComplete }: StepDeployProps) {
  const serverType = getServerType(serverTypeId)
  const { createServer } = useServerStore()
  const [steps, setSteps] = useState<DeployStep[]>([
    { id: 'supabase', label: 'Saving server definition to database', status: 'pending' },
    { id: 'service-manager', label: 'Registering with Service Manager', status: 'pending' },
    { id: 'health', label: 'Verifying server status', status: 'pending' },
  ])
  const [deployed, setDeployed] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const hasStarted = useRef(false)

  const updateStep = (id: string, patch: Partial<DeployStep>) => {
    setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, ...patch } : s)))
  }

  useEffect(() => {
    if (hasStarted.current) {return}
    hasStarted.current = true

    const deploy = async () => {
      if (!serverType) {return}

      const tools = serverTypeId === 'custom' ? config.customTools : serverType.defaultTools

      // Step 1: Save to Supabase
      updateStep('supabase', { status: 'running' })
      let serverId: string
      try {
        await createServer({
          name: config.name,
          description: config.description,
          tools,
          enabled: true,
          port: config.port,
          host: `localhost`,
          created_by: 'admin',
        })
        serverId = crypto.randomUUID()
        updateStep('supabase', { status: 'done', detail: 'Saved to virtual_servers table' })
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Unknown error'
        updateStep('supabase', { status: 'error', detail: msg })
        setError(`Failed to save server: ${msg}`)
        return
      }

      // Step 2: Register with Service Manager (best-effort)
      updateStep('service-manager', { status: 'running' })
      try {
        const payload = {
          name: config.name,
          image: config.dockerImage || serverType.dockerImage,
          port: config.port,
          environment: config.environment,
          auto_start: true,
          enabled: true,
        }
        const res = await fetch(`${SERVICE_MANAGER_URL}/services`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          signal: AbortSignal.timeout(5000),
        })
        if (res.ok) {
          updateStep('service-manager', { status: 'done', detail: 'Service registered and starting' })
        } else {
          const text = await res.text()
          updateStep('service-manager', {
            status: 'error',
            detail: `Service Manager returned ${res.status}: ${text.slice(0, 80)}`,
          })
        }
      } catch {
        updateStep('service-manager', {
          status: 'error',
          detail: 'Service Manager unreachable — add the service manually via docker-compose',
        })
      }

      // Step 3: Health check (best-effort)
      updateStep('health', { status: 'running' })
      await new Promise((r) => setTimeout(r, 1500))
      try {
        const res = await fetch(`http://localhost:${config.port}/health`, {
          signal: AbortSignal.timeout(3000),
        })
        if (res.ok) {
          updateStep('health', { status: 'done', detail: 'Server is responding' })
        } else {
          updateStep('health', {
            status: 'error',
            detail: 'Server not yet healthy — it may still be starting up',
          })
        }
      } catch {
        updateStep('health', {
          status: 'error',
          detail: 'Could not reach server — it may still be starting up',
        })
      }

      setDeployed(true)
      onComplete(serverId)
    }

    deploy()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (!serverType) {return null}

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

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Deploying your server</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Setting up <strong>{config.name}</strong> — this usually takes a few seconds.
        </p>
      </div>

      {/* Progress Steps */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          {steps.map((step) => (
            <div key={step.id} className="flex items-start gap-3">
              <div className="mt-0.5">
                <StepIcon status={step.status} />
              </div>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${step.status === 'error' ? 'text-destructive' : ''}`}>
                  {step.label}
                </p>
                {step.detail && (
                  <p className={`text-xs mt-0.5 ${step.status === 'error' ? 'text-destructive/80' : 'text-muted-foreground'}`}>
                    {step.detail}
                  </p>
                )}
              </div>
              {step.status === 'done' && (
                <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200 shrink-0">
                  Done
                </Badge>
              )}
              {step.status === 'error' && (
                <Badge variant="outline" className="text-xs bg-red-50 text-red-700 border-red-200 shrink-0">
                  Warning
                </Badge>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Fatal error */}
      {error && (
        <Card className="border-destructive bg-destructive/5">
          <CardContent className="pt-4">
            <p className="text-sm text-destructive font-medium">Deployment failed</p>
            <p className="text-xs text-destructive/80 mt-1">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Success state */}
      {deployed && !error && (
        <div className="space-y-4">
          <Card className="border-green-200 bg-green-50">
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <p className="text-sm font-medium text-green-800">
                  Server <strong>{config.name}</strong> has been created successfully!
                </p>
              </div>
              <p className="text-xs text-green-700 mt-2">
                The server definition is saved. If the Service Manager was reachable, the container is starting now.
                Otherwise, add the service to your <code>docker-compose.yml</code> using the snippet from the Review step.
              </p>
            </CardContent>
          </Card>

          {/* IDE snippet */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Add to your IDE (mcp.json)</CardTitle>
                <CopyButton text={ideMcpEntry} />
              </div>
            </CardHeader>
            <CardContent>
              <pre className="text-xs bg-muted rounded-md p-3 overflow-x-auto font-mono">
                {ideMcpEntry}
              </pre>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
