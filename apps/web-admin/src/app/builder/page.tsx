'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { StepServerType } from '@/components/mcp-builder/step-server-type'
import { StepConfiguration, type BuilderConfig } from '@/components/mcp-builder/step-configuration'
import { StepReview } from '@/components/mcp-builder/step-review'
import { StepDeploy } from '@/components/mcp-builder/step-deploy'
import { getNextAvailablePort, getServerType, type ServerTypeId } from '@/lib/mcp-server-catalog'
import { useServerStore } from '@/lib/store'
import { ArrowLeft, ArrowRight, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

const STEPS = [
  { id: 'type', label: 'Server Type' },
  { id: 'config', label: 'Configuration' },
  { id: 'review', label: 'Review' },
  { id: 'deploy', label: 'Deploy' },
] as const

type StepId = (typeof STEPS)[number]['id']

function StepIndicator({ steps, current }: { steps: typeof STEPS; current: number }) {
  return (
    <nav aria-label="Progress" className="flex items-center gap-0">
      {steps.map((step, index) => {
        const isDone = index < current
        const isCurrent = index === current

        return (
          <div key={step.id} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-semibold transition-colors',
                  isDone && 'border-primary bg-primary text-primary-foreground',
                  isCurrent && 'border-primary bg-background text-primary',
                  !isDone && !isCurrent && 'border-muted-foreground/30 bg-background text-muted-foreground'
                )}
              >
                {isDone ? <Check className="h-4 w-4" /> : index + 1}
              </div>
              <span
                className={cn(
                  'mt-1 text-xs font-medium whitespace-nowrap',
                  isCurrent ? 'text-primary' : 'text-muted-foreground'
                )}
              >
                {step.label}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div
                className={cn(
                  'mx-2 mb-4 h-0.5 w-12 transition-colors',
                  index < current ? 'bg-primary' : 'bg-muted-foreground/20'
                )}
              />
            )}
          </div>
        )
      })}
    </nav>
  )
}

export default function BuilderPage() {
  const router = useRouter()
  const { servers } = useServerStore()
  const [currentStep, setCurrentStep] = useState(0)
  const [selectedType, setSelectedType] = useState<ServerTypeId | null>(null)
  const [deployedId, setDeployedId] = useState<string | null>(null)

  const usedPorts = servers.map((s) => s.port).filter(Boolean) as number[]

  const [config, setConfig] = useState<BuilderConfig>({
    name: '',
    description: '',
    transport: 'SSE',
    port: getNextAvailablePort(usedPorts),
    dockerImage: '',
    environment: {},
    customTools: [],
  })

  const canProceed = (): boolean => {
    if (currentStep === 0) {return selectedType !== null}
    if (currentStep === 1) {
      const nameValid = /^[a-z0-9-]+$/.test(config.name) && config.name.length > 0
      const portValid = config.port > 0 && !usedPorts.includes(config.port)
      return nameValid && portValid
    }
    return true
  }

  const handleNext = () => {
    if (currentStep === 0 && selectedType) {
      const serverType = getServerType(selectedType)
      if (serverType) {
        const suggestedPort = usedPorts.includes(serverType.defaultPort)
          ? getNextAvailablePort(usedPorts)
          : serverType.defaultPort
        setConfig((prev) => ({
          ...prev,
          port: suggestedPort,
          dockerImage: serverType.dockerImage,
          environment: Object.fromEntries(serverType.envVars.map((v) => [v.key, prev.environment[v.key] ?? ''])),
          customTools: [],
        }))
      }
    }
    setCurrentStep((s) => Math.min(s + 1, STEPS.length - 1))
  }

  const handleBack = () => {
    setCurrentStep((s) => Math.max(s - 1, 0))
  }

  const stepId: StepId = STEPS[currentStep].id

  return (
    <div className="container max-w-4xl py-8 px-4 mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-1">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1 text-muted-foreground -ml-2"
            onClick={() => router.push('/servers')}
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Servers
          </Button>
        </div>
        <h1 className="text-2xl font-bold">MCP Server Builder</h1>
        <p className="text-muted-foreground mt-1">
          Create and register a new MCP server with the Forge Gateway in a few steps.
        </p>
      </div>

      {/* Step Indicator */}
      <div className="mb-8 flex justify-center">
        <StepIndicator steps={STEPS} current={currentStep} />
      </div>

      {/* Step Content */}
      <div className="min-h-[400px]">
        {stepId === 'type' && (
          <StepServerType selected={selectedType} onSelect={setSelectedType} />
        )}

        {stepId === 'config' && selectedType && (
          <StepConfiguration
            serverTypeId={selectedType}
            config={config}
            usedPorts={usedPorts}
            onChange={setConfig}
          />
        )}

        {stepId === 'review' && selectedType && (
          <StepReview serverTypeId={selectedType} config={config} />
        )}

        {stepId === 'deploy' && selectedType && (
          <StepDeploy
            serverTypeId={selectedType}
            config={config}
            onComplete={(id) => setDeployedId(id)}
          />
        )}
      </div>

      {/* Navigation */}
      <div className="mt-8 flex items-center justify-between border-t pt-6">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={currentStep === 0 || stepId === 'deploy'}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>

        <div className="flex gap-3">
          {stepId === 'deploy' && deployedId && (
            <Button variant="outline" onClick={() => router.push('/servers')}>
              View All Servers
            </Button>
          )}

          {stepId !== 'deploy' && (
            <Button onClick={handleNext} disabled={!canProceed()} className="gap-2">
              {currentStep === STEPS.length - 2 ? 'Deploy' : 'Next'}
              {currentStep < STEPS.length - 2 && <ArrowRight className="h-4 w-4" />}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
