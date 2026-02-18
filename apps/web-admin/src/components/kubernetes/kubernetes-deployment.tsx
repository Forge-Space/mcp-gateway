'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import {
  Rocket,
  CheckCircle,
  AlertCircle,
  Loader2,
  Download,
  Upload,
  Settings,
  Activity,
  Plus,
  Trash2,
  Server
} from 'lucide-react'

interface KubernetesConfig {
  clusterName: string
  namespace: string
  replicas: number
  image: string
  port: number
  resources: {
    cpu: string
    memory: string
  }
  environment: Record<string, string>
}

export function KubernetesDeployment() {
  const [config, setConfig] = useState<KubernetesConfig>({
    clusterName: '',
    namespace: 'default',
    replicas: 1,
    image: '',
    port: 8080,
    resources: {
      cpu: '100m',
      memory: '128Mi'
    },
    environment: {}
  })

  const [deploying, setDeploying] = useState(false)
  const [deploymentResult, setDeploymentResult] = useState<{
    success: boolean
    message: string
    details?: any
  } | null>(null)

  const [generatedYaml, setGeneratedYaml] = useState('')

  const handleConfigChange = (field: keyof KubernetesConfig, value: any) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleResourceChange = (resource: 'cpu' | 'memory', value: string) => {
    setConfig(prev => ({
      ...prev,
      resources: {
        ...prev.resources,
        [resource]: value
      }
    }))
  }

  const handleEnvironmentChange = (key: string, value: string) => {
    setConfig(prev => ({
      ...prev,
      environment: {
        ...prev.environment,
        [key]: value
      }
    }))
  }

  const generateYaml = () => {
    const yaml = `apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${config.clusterName || 'mcp-gateway'}
  namespace: ${config.namespace}
spec:
  replicas: ${config.replicas}
  selector:
    matchLabels:
      app: ${config.clusterName || 'mcp-gateway'}
  template:
    metadata:
      labels:
        app: ${config.clusterName || 'mcp-gateway'}
    spec:
      containers:
      - name: ${config.clusterName || 'mcp-gateway'}
        image: ${config.image}
        ports:
        - containerPort: ${config.port}
        resources:
          requests:
            cpu: ${config.resources.cpu}
            memory: ${config.resources.memory}
          limits:
            cpu: ${config.resources.cpu}
            memory: ${config.resources.memory}
        env:
${Object.entries(config.environment).map(([key, value]) => `        - name: ${key}\n          value: "${value}"`).join('\n') || '        []'}
---
apiVersion: v1
kind: Service
metadata:
  name: ${config.clusterName || 'mcp-gateway'}-service
  namespace: ${config.namespace}
spec:
  selector:
    app: ${config.clusterName || 'mcp-gateway'}
  ports:
  - protocol: TCP
    port: 80
    targetPort: ${config.port}
  type: ClusterIP`

    setGeneratedYaml(yaml)
  }

  const handleDeploy = async () => {
    if (!config.clusterName || !config.image) {
      setDeploymentResult({
        success: false,
        message: 'Please provide cluster name and image',
      })
      return
    }

    setDeploying(true)
    setDeploymentResult(null)

    try {
      // In a real implementation, this would call the Kubernetes API
      await new Promise(resolve => setTimeout(resolve, 3000))

      // Simulate successful deployment
      setDeploymentResult({
        success: true,
        message: `Deployment "${config.clusterName}" created successfully`,
        details: {
          namespace: config.namespace,
          replicas: config.replicas,
          endpoint: `${config.clusterName}.${config.namespace}.svc.cluster.local`,
        },
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

  const downloadYaml = () => {
    const blob = new Blob([generatedYaml], { type: 'text/yaml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${config.clusterName || 'mcp-gateway'}-deployment.yaml`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const addEnvironmentVariable = () => {
    const key = prompt('Enter environment variable name:')
    if (key) {
      handleEnvironmentChange(key, '')
    }
  }

  const removeEnvironmentVariable = (key: string) => {
    setConfig(prev => ({
      ...prev,
      environment: Object.fromEntries(
        Object.entries(prev.environment).filter(([k]) => k !== key)
      )
    }))
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Server className="h-5 w-5" />
          Kubernetes Deployment
        </CardTitle>
        <CardDescription>
          Deploy MCP Gateway to Kubernetes clusters
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Basic Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="clusterName" className="text-sm font-medium text-gray-700">
              Cluster Name
            </Label>
            <Input
              id="clusterName"
              value={config.clusterName}
              onChange={(e) => handleConfigChange('clusterName', e.target.value)}
              placeholder="mcp-gateway"
            />
          </div>
          <div>
            <Label htmlFor="namespace" className="text-sm font-medium text-gray-700">
              Namespace
            </Label>
            <Select
              value={config.namespace}
              onChange={(e) => handleConfigChange('namespace', e.target.value)}
            >
              <option value="default">default</option>
              <option value="production">production</option>
              <option value="staging">staging</option>
              <option value="development">development</option>
            </Select>
          </div>
          <div>
            <Label htmlFor="replicas" className="text-sm font-medium text-gray-700">
              Replicas
            </Label>
            <Input
              id="replicas"
              type="number"
              min="1"
              max="10"
              value={config.replicas}
              onChange={(e) => handleConfigChange('replicas', parseInt(e.target.value))}
            />
          </div>
          <div>
            <Label htmlFor="port" className="text-sm font-medium text-gray-700">
              Container Port
            </Label>
            <Input
              id="port"
              type="number"
              min="1"
              max="65535"
              value={config.port}
              onChange={(e) => handleConfigChange('port', parseInt(e.target.value))}
            />
          </div>
        </div>

        {/* Image Configuration */}
        <div>
          <Label htmlFor="image" className="text-sm font-medium text-gray-700">
            Container Image
          </Label>
          <Input
            id="image"
            value={config.image}
            onChange={(e) => handleConfigChange('image', e.target.value)}
            placeholder="mcp-gateway:latest"
          />
        </div>

        {/* Resource Configuration */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-4">Resource Limits</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="cpu" className="text-sm font-medium text-gray-700">
                CPU Request/Limit
              </Label>
              <Select
                value={config.resources.cpu}
                onChange={(e) => handleResourceChange('cpu', e.target.value)}
              >
                <option value="50m">50m (0.05 cores)</option>
                <option value="100m">100m (0.1 cores)</option>
                <option value="200m">200m (0.2 cores)</option>
                <option value="500m">500m (0.5 cores)</option>
                <option value="1000m">1000m (1 core)</option>
              </Select>
            </div>
            <div>
              <Label htmlFor="memory" className="text-sm font-medium text-gray-700">
                Memory Request/Limit
              </Label>
              <Select
                value={config.resources.memory}
                onChange={(e) => handleResourceChange('memory', e.target.value)}
              >
                <option value="64Mi">64Mi</option>
                <option value="128Mi">128Mi</option>
                <option value="256Mi">256Mi</option>
                <option value="512Mi">512Mi</option>
                <option value="1Gi">1Gi</option>
                <option value="2Gi">2Gi</option>
              </Select>
            </div>
          </div>
        </div>

        {/* Environment Variables */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-gray-900">Environment Variables</h4>
            <Button variant="outline" size="sm" onClick={addEnvironmentVariable}>
              <Plus className="h-4 w-4 mr-2" />
              Add Variable
            </Button>
          </div>
          <div className="space-y-2">
            {Object.entries(config.environment).map(([key, value]) => (
              <div key={key} className="flex items-center space-x-2">
                <Input
                  value={key}
                  onChange={(e) => {
                    const newKey = e.target.value
                    const newValue = config.environment[key]
                    removeEnvironmentVariable(key)
                    if (newKey) {
                      handleEnvironmentChange(newKey, newValue)
                    }
                  }}
                  placeholder="Variable name"
                  className="flex-1"
                />
                <Input
                  value={value}
                  onChange={(e) => handleEnvironmentChange(key, e.target.value)}
                  placeholder="Variable value"
                  className="flex-1"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => removeEnvironmentVariable(key)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
            {Object.keys(config.environment).length === 0 && (
              <div className="text-center py-4 text-gray-500">
                No environment variables configured
              </div>
            )}
          </div>
        </div>

        {/* YAML Generation */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-gray-900">Generated YAML</h4>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={generateYaml}>
                <Settings className="h-4 w-4 mr-2" />
                Generate YAML
              </Button>
              {generatedYaml && (
                <Button variant="outline" size="sm" onClick={downloadYaml}>
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </Button>
              )}
            </div>
          </div>
          {generatedYaml && (
            <Textarea
              value={generatedYaml}
              onChange={(e) => setGeneratedYaml(e.target.value)}
              rows={20}
              className="font-mono text-sm"
            />
          )}
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
          disabled={!config.clusterName || !config.image || deploying}
          className="w-full"
        >
          {deploying ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Deploying to Kubernetes...
            </>
          ) : (
            <>
              <Rocket className="h-4 w-4 mr-2" />
              Deploy to Kubernetes
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
