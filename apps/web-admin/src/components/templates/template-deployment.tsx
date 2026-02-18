'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useServerStore } from '@/lib/store'
import { useGatewayStore } from '@/lib/mcp-gateway'
import { Package, Rocket, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

interface TemplateDeploymentConfig {
  templateId: string
  name: string
  description: string
  variables: Record<string, string>
  targetProject?: string
}

export function TemplateDeployment() {
  const { templates, loading, fetchTemplates } = useServerStore()
  const { connected } = useGatewayStore()

  const [deploymentConfig, setDeploymentConfig] = useState<TemplateDeploymentConfig>({
    templateId: '',
    name: '',
    description: '',
    variables: {},
    targetProject: 'default',
  })

  const [deploying, setDeploying] = useState(false)
  const [deploymentResult, setDeploymentResult] = useState<{
    success: boolean
    message: string
    details?: any
  } | null>(null)

  const selectedTemplate = templates.find(t => t.id === deploymentConfig.templateId)

  useEffect(() => {
    fetchTemplates()
  }, [fetchTemplates])

  const handleTemplateChange = (templateId: string) => {
    const template = templates.find(t => t.id === templateId)
    setDeploymentConfig(prev => ({
      ...prev,
      templateId,
      name: template?.name || '',
      description: template?.description || '',
      variables: {},
    }))
  }

  const handleVariableChange = (key: string, value: string) => {
    setDeploymentConfig(prev => ({
      ...prev,
      variables: {
        ...prev.variables,
        [key]: value,
      },
    }))
  }

  const handleDeploy = async () => {
    if (!deploymentConfig.templateId || !deploymentConfig.name) {
      setDeploymentResult({
        success: false,
        message: 'Please select a template and provide a name',
      })
      return
    }

    setDeploying(true)
    setDeploymentResult(null)

    try {
      // In a real implementation, this would call the MCP Gateway API
      // For now, we'll simulate the deployment
      await new Promise(resolve => setTimeout(resolve, 2000))

      // Simulate successful deployment
      setDeploymentResult({
        success: true,
        message: `Template "${deploymentConfig.name}" deployed successfully`,
        details: {
          serverId: `server-${Date.now()}`,
          status: 'running',
          url: `${deploymentConfig.name.toLowerCase().replace(/\s+/g, '-')}.example.com`,
        },
      })

      // Reset form
      setDeploymentConfig({
        templateId: '',
        name: '',
        description: '',
        variables: {},
        targetProject: 'default',
      })
    } catch (error) {
      setDeploymentResult({
        success: false,
        message: `Deployment failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      })
    } finally {
      setDeploying(false)
    }
  }

  const renderVariableInputs = () => {
    const configKeys = selectedTemplate ? Object.keys(selectedTemplate.config) : []
    if (!selectedTemplate || configKeys.length === 0) {
      return null
    }

    return (
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-gray-900">Template Variables</h4>
        {configKeys.map(variable => (
          <div key={variable} className="space-y-2">
            <Label htmlFor={variable} className="text-sm font-medium text-gray-700">
              {variable}
              {variable.includes('required') && <span className="text-red-500">*</span>}
            </Label>
            <Input
              id={variable}
              value={deploymentConfig.variables[variable] || ''}
              onChange={(e) => handleVariableChange(variable, e.target.value)}
              placeholder={`Enter ${variable}`}
              required={variable.includes('required')}
            />
          </div>
        ))}
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Rocket className="h-5 w-5" />
          Template Deployment
        </CardTitle>
        <CardDescription>
          Deploy new servers from template registry with custom configurations
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {!connected && (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <Package className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500">Connect to gateway to deploy templates</p>
            </div>
          </div>
        )}

        {connected && (
          <>
            {/* Template Selection */}
            <div className="space-y-2">
              <Label htmlFor="template" className="text-sm font-medium text-gray-700">
                Template
              </Label>
              <Select
                value={deploymentConfig.templateId}
                onChange={(e) => handleTemplateChange(e.target.value)}
                disabled={loading || deploying}
              >
                <option value="">Select a template...</option>
                {templates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name} ({template.category})
                  </option>
                ))}
              </Select>
            </div>

            {/* Template Info */}
            {selectedTemplate && (
              <div className="p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">{selectedTemplate.name}</h4>
                <p className="text-sm text-gray-600 mb-2">{selectedTemplate.description}</p>
                <div className="flex items-center gap-2 text-sm">
                  <Badge>{selectedTemplate.category}</Badge>
                  {selectedTemplate.version && <Badge>{selectedTemplate.version}</Badge>}
                </div>
              </div>
            )}

            {/* Deployment Configuration */}
            <div className="space-y-4">
              <div>
                <Label htmlFor="name" className="text-sm font-medium text-gray-700">
                  Server Name
                </Label>
                <Input
                  id="name"
                  value={deploymentConfig.name}
                  onChange={(e) => setDeploymentConfig(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter server name"
                  disabled={loading || deploying}
                />
              </div>

              <div>
                <Label htmlFor="description" className="text-sm font-medium text-gray-700">
                  Description
                </Label>
                <Textarea
                  id="description"
                  value={deploymentConfig.description}
                  onChange={(e) => setDeploymentConfig(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Enter server description"
                  rows={3}
                  disabled={loading || deploying}
                />
              </div>

              <div>
                <Label htmlFor="targetProject" className="text-sm font-medium text-gray-700">
                  Target Project
                </Label>
                <Select
                  value={deploymentConfig.targetProject}
                  onChange={(e) => setDeploymentConfig(prev => ({ ...prev, targetProject: e.target.value }))}
                  disabled={loading || deploying}
                >
                  <option value="default">Default Project</option>
                  <option value="production">Production</option>
                  <option value="staging">Staging</option>
                  <option value="development">Development</option>
                </Select>
              </div>

              {/* Template Variables */}
              {renderVariableInputs()}
            </div>

            {/* Deployment Result */}
            {deploymentResult && (
              <div
                className={`p-4 rounded-lg ${
                  deploymentResult.success
                    ? 'bg-green-50 border-green-200'
                    : 'bg-red-50 border-red-200'
                }`}
              >
                <div className="flex items-center gap-2">
                  {deploymentResult.success ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-600" />
                  )}
                  <div>
                    <div className={`font-medium ${
                      deploymentResult.success ? 'text-green-900' : 'text-red-900'
                    }`}>
                      {deploymentResult.success ? 'Deployment Successful' : 'Deployment Failed'}
                    </div>
                    <div className={`text-sm ${
                      deploymentResult.success ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {deploymentResult.message}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Deploy Button */}
            <Button
              onClick={handleDeploy}
              disabled={!deploymentConfig.templateId || !deploymentConfig.name || deploying}
              className="w-full"
            >
              {deploying ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deploying...
                </>
              ) : (
                <>
                  <Rocket className="h-4 w-4 mr-2" />
                  Deploy Server
                </>
              )}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  )
}
