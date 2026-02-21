'use client'

import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { StepServerType } from './step-server-type'
import { StepConfiguration, type BuilderConfig } from './step-configuration'
import { StepReview } from './step-review'
import { StepDeploy } from './step-deploy'
import { useServerStore } from '@/lib/store'
import { getServerType, type ServerTypeId } from '@/lib/mcp-server-catalog'
import { ArrowLeft, ArrowRight, CheckCircle2, Circle, Loader2 } from 'lucide-react'

interface MCPBuilderProps {
  onComplete?: (serverId: string) => void
  onCancel?: () => void
}

type BuilderStep = 'server-type' | 'configuration' | 'review' | 'deploy'

interface StepState {
  id: BuilderStep
  title: string
  description: string
  completed: boolean
  current: boolean
}

export function MCPBuilder({ onComplete, onCancel }: MCPBuilderProps) {
  const { servers } = useServerStore()
  const [currentStep, setCurrentStep] = useState<BuilderStep>('server-type')
  const [selectedServerType, setSelectedServerType] = useState<ServerTypeId | null>(null)
  const [config, setConfig] = useState<BuilderConfig>({
    name: '',
    description: '',
    transport: 'SSE',
    port: 8040,
    dockerImage: '',
    environment: {},
    customTools: []
  })
  const [isDeploying, setIsDeploying] = useState(false)

  // Get used ports to avoid conflicts
  const usedPorts = servers.map(s => {
    const portMatch = s.name.match(/:(\d+)$/)
    return portMatch ? parseInt(portMatch[1]) : 0
  }).filter(p => p > 0)

  const steps: StepState[] = [
    {
      id: 'server-type',
      title: 'Server Type',
      description: 'Choose MCP server type',
      completed: selectedServerType !== null,
      current: currentStep === 'server-type'
    },
    {
      id: 'configuration',
      title: 'Configuration',
      description: 'Configure server settings',
      completed: config.name.trim() !== '' && config.port > 0,
      current: currentStep === 'configuration'
    },
    {
      id: 'review',
      title: 'Review',
      description: 'Review and confirm',
      completed: false,
      current: currentStep === 'review'
    },
    {
      id: 'deploy',
      title: 'Deploy',
      description: 'Deploy MCP server',
      completed: false,
      current: currentStep === 'deploy'
    }
  ]

  const currentStepIndex = steps.findIndex(s => s.id === currentStep)
  const canGoNext = steps[currentStepIndex].completed
  const canGoBack = currentStepIndex > 0

  const handleNext = () => {
    if (currentStep === 'review') {
      setCurrentStep('deploy')
      setIsDeploying(true)
    } else if (canGoNext) {
      const nextStep = steps[currentStepIndex + 1].id
      setCurrentStep(nextStep)
    }
  }

  const handleBack = () => {
    if (canGoBack) {
      const prevStep = steps[currentStepIndex - 1].id
      setCurrentStep(prevStep)
    }
  }

  const handleServerTypeSelect = (serverTypeId: ServerTypeId) => {
    setSelectedServerType(serverTypeId)
    // Initialize config with server type defaults
    const serverType = getServerType(serverTypeId)
    if (serverType) {
      setConfig(prev => ({
        ...prev,
        transport: serverType.defaultTransport,
        port: serverType.defaultPort,
        dockerImage: serverType.dockerImage,
        environment: serverType.envVars
          .filter(v => !v.required)
          .reduce((acc, v) => ({ ...acc, [v.key]: '' }), {})
      }))
    }
  }

  const handleDeployComplete = (serverId: string) => {
    setIsDeploying(false)
    onComplete?.(serverId)
  }

  const handleCancel = () => {
    if (isDeploying) {
      // Don't allow cancel during deployment
      return
    }
    onCancel?.()
  }


  function StepIcon({ completed, current }: { completed: boolean; current: boolean }) {
    if (completed) return <CheckCircle2 className="h-5 w-5 text-green-600" />
    if (current) return <Loader2 className="h-5 w-5 animate-spin text-primary" />
    return <Circle className="h-5 w-5 text-muted-foreground" />
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">MCP Server Builder</h2>
        <p className="text-muted-foreground">
          Create and deploy a new MCP server with our step-by-step wizard
        </p>
      </div>

      {/* Progress Steps */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex items-center space-x-3">
                  <StepIcon completed={step.completed} current={step.current} />
                  <div className={index === currentStepIndex ? 'text-foreground' : 'text-muted-foreground'}>
                    <div className="font-medium">{step.title}</div>
                    <div className="text-sm">{step.description}</div>
                  </div>
                </div>
                {index < steps.length - 1 && (
                  <div className={`flex-1 h-px mx-4 ${
                    step.completed ? 'bg-green-600' : 'bg-muted'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Step Content */}
      <Card>
        <CardContent className="pt-6">
          {currentStep === 'server-type' && (
            <StepServerType
              selected={selectedServerType}
              onSelect={handleServerTypeSelect}
            />
          )}

          {currentStep === 'configuration' && selectedServerType && (
            <StepConfiguration
              serverTypeId={selectedServerType}
              config={config}
              usedPorts={usedPorts}
              onChange={setConfig}
            />
          )}

          {currentStep === 'review' && selectedServerType && (
            <StepReview
              serverTypeId={selectedServerType}
              config={config}
            />
          )}

          {currentStep === 'deploy' && selectedServerType && (
            <StepDeploy
              serverTypeId={selectedServerType}
              config={config}
              onComplete={handleDeployComplete}
            />
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={!canGoBack || isDeploying}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={isDeploying}
          >
            Cancel
          </Button>

          <Button
            onClick={handleNext}
            disabled={!canGoNext || isDeploying}
          >
            {currentStep === 'deploy' ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Deploying...
              </>
            ) : currentStep === 'review' ? (
              <>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Deploy Server
              </>
            ) : (
              <>
                Next
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
