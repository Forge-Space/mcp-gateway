#!/usr/bin/env python3

"""
Multi-Cloud Management Script for MCP Gateway
Provides cloud-agnostic deployment, monitoring, and cost management across multiple cloud providers
"""

import json
import time
import logging
import argparse
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import subprocess
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CloudProvider:
    """Cloud provider configuration"""
    name: str
    type: str  # aws, azure, gcp, digitalocean, oracle, ibm
    region: str
    credentials: Dict[str, str]
    services: Dict[str, str]
    enabled: bool = True

@dataclass
class ServiceConfig:
    """Service configuration for multi-cloud deployment"""
    name: str
    image: str
    replicas: int
    cpu_request: str
    memory_request: str
    ports: List[int]
    environment: Dict[str, str]
    providers: List[str]  # Preferred cloud providers

@dataclass
class DeploymentResult:
    """Deployment result"""
    success: bool
    provider: str
    service_id: str
    endpoint: str
    cost_estimate: float
    deployment_time: float
    error_message: Optional[str] = None

class MultiCloudManager:
    """Multi-cloud management system"""
    
    def __init__(self, config_file: str = "config/multi-cloud.yaml"):
        self.config_file = Path(config_file)
        self.providers = {}
        self.services = {}
        self.deployments = {}
        self._load_configuration()
        
    def _load_configuration(self):
        """Load multi-cloud configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    
                # Load providers
                for provider_config in config.get('providers', []):
                    provider = CloudProvider(**provider_config)
                    self.providers[provider.name] = provider
                
                # Load services
                for service_config in config.get('services', []):
                    service = ServiceConfig(**service_config)
                    self.services[service.name] = service
                
                logger.info(f"Loaded {len(self.providers)} providers and {len(self.services)} services")
            else:
                logger.warning(f"Configuration file {self.config_file} not found")
                self._create_default_configuration()
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._create_default_configuration()
    
    def _create_default_configuration(self):
        """Create default multi-cloud configuration"""
        default_config = {
            'multi_cloud': {
                'enabled': True,
                'default_provider': 'aws',
                'load_balancing': {
                    'strategy': 'weighted_round_robin',
                    'health_check_interval': 30,
                    'failover_threshold': 3
                }
            },
            'providers': [
                {
                    'name': 'aws',
                    'type': 'aws',
                    'region': 'us-east-1',
                    'credentials': {
                        'access_key_id': '${AWS_ACCESS_KEY_ID}',
                        'secret_access_key': '${AWS_SECRET_ACCESS_KEY}'
                    },
                    'services': {
                        'compute': 'ecs',
                        'storage': 's3',
                        'database': 'rds',
                        'monitoring': 'cloudwatch'
                    },
                    'enabled': True
                },
                {
                    'name': 'azure',
                    'type': 'azure',
                    'region': 'eastus',
                    'credentials': {
                        'client_id': '${AZURE_CLIENT_ID}',
                        'client_secret': '${AZURE_CLIENT_SECRET}',
                        'tenant_id': '${AZURE_TENANT_ID}'
                    },
                    'services': {
                        'compute': 'aks',
                        'storage': 'blob',
                        'database': 'sql',
                        'monitoring': 'monitor'
                    },
                    'enabled': False
                },
                {
                    'name': 'gcp',
                    'type': 'gcp',
                    'region': 'us-central1',
                    'credentials': {
                        'service_account_key': '${GCP_SERVICE_ACCOUNT_KEY}'
                    },
                    'services': {
                        'compute': 'gke',
                        'storage': 'gcs',
                        'database': 'cloudsql',
                        'monitoring': 'cloudmonitoring'
                    },
                    'enabled': False
                }
            ],
            'services': [
                {
                    'name': 'gateway',
                    'image': 'ghcr.io/ibm/mcp-context-forge:1.0.0-BETA-2',
                    'replicas': 3,
                    'cpu_request': '500m',
                    'memory_request': '512Mi',
                    'ports': [4444],
                    'environment': {
                        'NODE_ENV': 'production',
                        'LOG_LEVEL': 'info'
                    },
                    'providers': ['aws', 'azure', 'gcp']
                },
                {
                    'name': 'service-manager',
                    'image': 'forge-mcp-gateway-service-manager:latest',
                    'replicas': 2,
                    'cpu_request': '250m',
                    'memory_request': '256Mi',
                    'ports': [9000],
                    'environment': {
                        'NODE_ENV': 'production'
                    },
                    'providers': ['aws', 'azure']
                }
            ]
        }
        
        # Create config directory if it doesn't exist
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Write default configuration
        try:
            import yaml
            with open(self.config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            logger.info(f"Created default configuration at {self.config_file}")
        except ImportError:
            # Fallback to JSON if yaml not available
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default JSON configuration at {self.config_file}")
    
    def deploy_service(self, service_name: str, providers: List[str] = None) -> List[DeploymentResult]:
        """Deploy service to specified cloud providers"""
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} not found in configuration")
        
        service = self.services[service_name]
        target_providers = providers or service.providers
        
        # Filter enabled providers
        available_providers = [
            p for p in target_providers 
            if p in self.providers and self.providers[p].enabled
        ]
        
        if not available_providers:
            raise ValueError("No enabled providers available for deployment")
        
        results = []
        
        for provider_name in available_providers:
            provider = self.providers[provider_name]
            
            try:
                logger.info(f"Deploying {service_name} to {provider_name} ({provider.type})")
                start_time = time.time()
                
                result = self._deploy_to_provider(service, provider)
                result.deployment_time = time.time() - start_time
                
                results.append(result)
                
                if result.success:
                    logger.info(f"Successfully deployed {service_name} to {provider_name}")
                    self.deployments[f"{service_name}:{provider_name}"] = result
                else:
                    logger.error(f"Failed to deploy {service_name} to {provider_name}: {result.error_message}")
                    
            except Exception as e:
                logger.error(f"Error deploying {service_name} to {provider_name}: {e}")
                results.append(DeploymentResult(
                    success=False,
                    provider=provider_name,
                    service_id="",
                    endpoint="",
                    cost_estimate=0.0,
                    deployment_time=0.0,
                    error_message=str(e)
                ))
        
        return results
    
    def _deploy_to_provider(self, service: ServiceConfig, provider: CloudProvider) -> DeploymentResult:
        """Deploy service to specific cloud provider"""
        if provider.type == 'aws':
            return self._deploy_to_aws(service, provider)
        elif provider.type == 'azure':
            return self._deploy_to_azure(service, provider)
        elif provider.type == 'gcp':
            return self._deploy_to_gcp(service, provider)
        else:
            raise ValueError(f"Unsupported provider type: {provider.type}")
    
    def _deploy_to_aws(self, service: ServiceConfig, provider: CloudProvider) -> DeploymentResult:
        """Deploy service to AWS"""
        try:
            # Check if AWS CLI is available
            subprocess.run(['aws', '--version'], capture_output=True, check=True)
            
            # Create ECS task definition
            task_def = {
                'family': service.name,
                'networkMode': 'awsvpc',
                'requiresCompatibilities': ['FARGATE'],
                'cpu': int(service.cpu_request.rstrip('m')),
                'memory': int(service.memory_request.rstrip('Mi')),
                'executionRoleArn': f'arn:aws:iam::{provider.credentials.get("account_id", "unknown")}:role/ecsTaskExecutionRole',
                'containerDefinitions': [
                    {
                        'name': service.name,
                        'image': service.image,
                        'portMappings': [
                            {
                                'containerPort': port,
                                'protocol': 'tcp'
                            } for port in service.ports
                        ],
                        'environment': [
                            {
                                'name': key,
                                'value': value
                            } for key, value in service.environment.items()
                        ],
                        'logConfiguration': {
                            'logDriver': 'awslogs',
                            'options': {
                                'awslogs-group': f'/ecs/{service.name}',
                                'awslogs-region': provider.region,
                                'awslogs-stream-prefix': 'ecs'
                            }
                        }
                    }
                ]
            }
            
            # Register task definition
            result = subprocess.run([
                'aws', 'ecs', 'register-task-definition',
                '--cli-input-json', json.dumps(task_def),
                '--region', provider.region
            ], capture_output=True, text=True, check=True)
            
            task_def_arn = json.loads(result.stdout)['taskDefinition']['taskDefinitionArn']
            
            # Create ECS service
            service_name = f"{service.name}-{provider.name}"
            service_result = subprocess.run([
                'aws', 'ecs', 'create-service',
                '--cluster', 'mcp-gateway',
                '--service-name', service_name,
                '--task-definition', task_def_arn,
                '--desired-count', service.replicas,
                '--launch-type', 'FARGATE',
                '--network-configuration', json.dumps({
                    'awsvpcConfiguration': {
                        'subnets': ['subnet-12345', 'subnet-67890'],
                        'securityGroups': ['sg-12345'],
                        'assignPublicIp': 'ENABLED'
                    }
                }),
                '--region', provider.region
            ], capture_output=True, text=True, check=True)
            
            service_arn = json.loads(service_result.stdout)['service']['serviceArn']
            
            # Get load balancer endpoint
            lb_result = subprocess.run([
                'aws', 'elbv2', 'describe-load-balancers',
                '--names', [f'{service_name}-lb'],
                '--region', provider.region
            ], capture_output=True, text=True)
            
            if lb_result.returncode == 0:
                lb_data = json.loads(lb_result.stdout)
                endpoint = lb_data['LoadBalancers'][0]['DNSName']
            else:
                endpoint = f"{service_name}.{provider.region}.elb.amazonaws.com"
            
            # Estimate cost (simplified calculation)
            cost_estimate = self._estimate_aws_cost(service, provider)
            
            return DeploymentResult(
                success=True,
                provider=provider.name,
                service_id=service_arn,
                endpoint=endpoint,
                cost_estimate=cost_estimate,
                deployment_time=0.0
            )
            
        except subprocess.CalledProcessError as e:
            return DeploymentResult(
                success=False,
                provider=provider.name,
                service_id="",
                endpoint="",
                cost_estimate=0.0,
                deployment_time=0.0,
                error_message=f"AWS deployment failed: {e.stderr}"
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                provider=provider.name,
                service_id="",
                endpoint="",
                cost_estimate=0.0,
                deployment_time=0.0,
                error_message=f"AWS deployment error: {str(e)}"
            )
    
    def _deploy_to_azure(self, service: ServiceConfig, provider: CloudProvider) -> DeploymentResult:
        """Deploy service to Azure"""
        try:
            # Check if Azure CLI is available
            subprocess.run(['az', '--version'], capture_output=True, check=True)
            
            # Create resource group if it doesn't exist
            subprocess.run([
                'az', 'group', 'create',
                '--name', 'mcp-gateway-rg',
                '--location', provider.region
            ], capture_output=True, check=True)
            
            # Create container registry
            acr_name = f"mcpgateway{provider.name.lower()}"
            subprocess.run([
                'az', 'acr', 'create',
                '--name', acr_name,
                '--resource-group', 'mcp-gateway-rg',
                '--sku', 'Basic'
            ], capture_output=True, check=True)
            
            # Build and push container image
            subprocess.run([
                'az', 'acr', 'build',
                '--registry', acr_name,
                '--image', service.name,
                '.'
            ], capture_output=True, check=True)
            
            # Create container instance
            container_name = f"{service.name}-{provider.name}"
            instance_result = subprocess.run([
                'az', 'container', 'create',
                '--resource-group', 'mcp-gateway-rg',
                '--name', container_name,
                '--image', f"{acr_name}.azurecr.io/{service.name}",
                '--cpu', service.cpu_request.rstrip('m'),
                '--memory', service.memory_request.rstrip('Mi'),
                '--ports', ','.join(map(str, service.ports)),
                '--environment-variables', json.dumps(service.environment)
            ], capture_output=True, text=True, check=True)
            
            instance_data = json.loads(instance_result.stdout)
            
            # Get container IP
            ip_result = subprocess.run([
                'az', 'container', 'show',
                '--resource-group', 'mcp-gateway-rg',
                '--name', container_name
            ], capture_output=True, text=True, check=True)
            
            ip_data = json.loads(ip_result.stdout)
            endpoint = ip_data['ipAddress']['ip']
            
            # Estimate cost
            cost_estimate = self._estimate_azure_cost(service, provider)
            
            return DeploymentResult(
                success=True,
                provider=provider.name,
                service_id=instance_data['id'],
                endpoint=f"http://{endpoint}",
                cost_estimate=cost_estimate,
                deployment_time=0.0
            )
            
        except subprocess.CalledProcessError as e:
            return DeploymentResult(
                success=False,
                provider=provider.name,
                service_id="",
                endpoint="",
                cost_estimate=0.0,
                deployment_time=0.0,
                error_message=f"Azure deployment failed: {e.stderr}"
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                provider=provider.name,
                service_id="",
                endpoint="",
                cost_estimate=0.0,
                deployment_time=0.0,
                error_message=f"Azure deployment error: {str(e)}"
            )
    
    def _deploy_to_gcp(self, service: ServiceConfig, provider: CloudProvider) -> DeploymentResult:
        """Deploy service to GCP"""
        try:
            # Check if gcloud is available
            subprocess.run(['gcloud', '--version'], capture_output=True, check=True)
            
            # Set project
            subprocess.run([
                'gcloud', 'config', 'set', 'project', provider.credentials.get('project_id', 'mcp-gateway')
            ], capture_output=True, check=True)
            
            # Deploy to Cloud Run
            service_name = f"{service.name}-{provider.name}"
            
            # Build and push image
            subprocess.run([
                'gcloud', 'builds', 'submit',
                '--tag', f"gcr.io/{provider.credentials.get('project_id', 'mcp-gateway')}/{service_name}",
                '.'
            ], capture_output=True, check=True)
            
            # Deploy to Cloud Run
            deploy_result = subprocess.run([
                'gcloud', 'run', 'deploy', service_name,
                '--image', f"gcr.io/{provider.credentials.get('project_id', 'mcp-gateway')}/{service_name}",
                '--region', provider.region,
                '--platform', 'managed',
                '--cpu', service.cpu_request.rstrip('m'),
                '--memory', service.memory_request,
                '--port', str(service.ports[0]) if service.ports else '8080',
                '--allow-unauthenticated',
                '--set-env-vars', ','.join([f"{k}={v}" for k, v in service.environment.items()])
            ], capture_output=True, text=True, check=True)
            
            # Get service URL
            service_result = subprocess.run([
                'gcloud', 'run', 'services', 'describe', service_name,
                '--region', provider.region,
                '--format', 'value(status.url)'
            ], capture_output=True, text=True, check=True)
            
            endpoint = service_result.stdout.strip()
            
            # Estimate cost
            cost_estimate = self._estimate_gcp_cost(service, provider)
            
            return DeploymentResult(
                success=True,
                provider=provider.name,
                service_id=service_name,
                endpoint=endpoint,
                cost_estimate=cost_estimate,
                deployment_time=0.0
            )
            
        except subprocess.CalledProcessError as e:
            return DeploymentResult(
                success=False,
                provider=provider.name,
                service_id="",
                endpoint="",
                cost_estimate=0.0,
                deployment_time=0.0,
                error_message=f"GCP deployment failed: {e.stderr}"
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                provider=provider.name,
                service_id="",
                endpoint="",
                cost_estimate=0.0,
                deployment_time=0.0,
                error_message=f"GCP deployment error: {str(e)}"
            )
    
    def _estimate_aws_cost(self, service: ServiceConfig, provider: CloudProvider) -> float:
        """Estimate AWS cost (simplified)"""
        # Fargate pricing (simplified)
        cpu_cost = float(service.cpu_request.rstrip('m')) / 1000 * 0.048  # $0.048 per vCPU-hour
        memory_cost = float(service.memory_request.rstrip('Mi')) / 1024 * 0.0107  # $0.0107 per GB-hour
        hourly_cost = (cpu_cost + memory_cost) * service.replicas
        monthly_cost = hourly_cost * 24 * 30
        return monthly_cost
    
    def _estimate_azure_cost(self, service: ServiceConfig, provider: CloudProvider) -> float:
        """Estimate Azure cost (simplified)"""
        # Container Instances pricing (simplified)
        cpu_cost = float(service.cpu_request.rstrip('m')) / 1000 * 0.036  # $0.036 per vCPU-hour
        memory_cost = float(service.memory_request.rstrip('Mi')) / 1024 * 0.008  # $0.008 per GB-hour
        hourly_cost = (cpu_cost + memory_cost) * service.replicas
        monthly_cost = hourly_cost * 24 * 30
        return monthly_cost
    
    def _estimate_gcp_cost(self, service: ServiceConfig, provider: CloudProvider) -> float:
        """Estimate GCP cost (simplified)"""
        # Cloud Run pricing (simplified)
        cpu_cost = float(service.cpu_request.rstrip('m')) / 1000 * 0.024  # $0.024 per vCPU-hour
        memory_cost = float(service.memory_request.rstrip('Mi')) / 1024 * 0.0025  # $0.0025 per GB-hour
        hourly_cost = (cpu_cost + memory_cost) * service.replicas
        monthly_cost = hourly_cost * 24 * 30
        return monthly_cost
    
    def scale_service(self, service_name: str, replicas: int, provider: str = None) -> bool:
        """Scale service across cloud providers"""
        if provider:
            return self._scale_service_provider(service_name, replicas, provider)
        else:
            # Scale across all providers
            success = True
            for provider_name in self.providers:
                if self.providers[provider_name].enabled:
                    success &= self._scale_service_provider(service_name, replicas, provider_name)
            return success
    
    def _scale_service_provider(self, service_name: str, replicas: int, provider_name: str) -> bool:
        """Scale service on specific provider"""
        try:
            provider = self.providers[provider_name]
            
            if provider.type == 'aws':
                # Scale ECS service
                subprocess.run([
                    'aws', 'ecs', 'update-service',
                    '--cluster', 'mcp-gateway',
                    '--service', f"{service_name}-{provider_name}",
                    '--desired-count', replicas,
                    '--region', provider.region
                ], check=True)
                
            elif provider.type == 'azure':
                # Scale container instance
                subprocess.run([
                    'az', 'container', 'update',
                    '--resource-group', 'mcp-gateway-rg',
                    '--name', f"{service_name}-{provider_name}",
                    '--cpu', str(replicas)
                ], check=True)
                
            elif provider.type == 'gcp':
                # Scale Cloud Run service
                subprocess.run([
                    'gcloud', 'run', 'services', 'update', f"{service_name}-{provider_name}",
                    '--region', provider.region,
                    '--max-instances', str(replicas)
                ], check=True)
            
            logger.info(f"Scaled {service_name} to {replicas} replicas on {provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to scale {service_name} on {provider_name}: {e}")
            return False
    
    def get_multi_cloud_status(self) -> Dict[str, Any]:
        """Get multi-cloud deployment status"""
        status = {
            'providers': {},
            'services': {},
            'deployments': {},
            'total_cost': 0.0
        }
        
        # Provider status
        for name, provider in self.providers.items():
            status['providers'][name] = {
                'type': provider.type,
                'region': provider.region,
                'enabled': provider.enabled,
                'services': provider.services
            }
        
        # Service status
        for name, service in self.services.items():
            status['services'][name] = {
                'image': service.image,
                'replicas': service.replicas,
                'providers': service.providers,
                'ports': service.ports
            }
        
        # Deployment status
        for deployment_key, deployment in self.deployments.items():
            status['deployments'][deployment_key] = {
                'success': deployment.success,
                'provider': deployment.provider,
                'service_id': deployment.service_id,
                'endpoint': deployment.endpoint,
                'cost_estimate': deployment.cost_estimate,
                'deployment_time': deployment.deployment_time
            }
            status['total_cost'] += deployment.cost_estimate
        
        return status
    
    def generate_cost_report(self, time_range: str = "30d") -> Dict[str, Any]:
        """Generate multi-cloud cost report"""
        report = {
            'time_range': time_range,
            'providers': {},
            'services': {},
            'total_cost': 0.0,
            'optimization_recommendations': []
        }
        
        # Calculate costs by provider
        provider_costs = {}
        for deployment_key, deployment in self.deployments.items():
            if deployment.success:
                provider = deployment.provider
                if provider not in provider_costs:
                    provider_costs[provider] = 0.0
                provider_costs[provider] += deployment.cost_estimate
        
        report['providers'] = provider_costs
        report['total_cost'] = sum(provider_costs.values())
        
        # Generate optimization recommendations
        if report['total_cost'] > 1000:
            report['optimization_recommendations'].append(
                "Consider using reserved instances for cost savings"
            )
        
        if len(self.deployments) > 5:
            report['optimization_recommendations'].append(
                "Consolidate services to reduce management overhead"
            )
        
        return report

def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(description='Multi-Cloud Management for MCP Gateway')
    parser.add_argument('--deploy', help='Deploy service to multi-cloud')
    parser.add_argument('--scale', help='Scale service (format: service_name:replicas)')
    parser.add_argument('--provider', help='Target cloud provider')
    parser.add_argument('--status', action='store_true', help='Get multi-cloud status')
    parser.add_argument('--cost-report', action='store_true', help='Generate cost report')
    parser.add_argument('--config', default='config/multi-cloud.yaml', help='Configuration file path')
    
    args = parser.parse_args()
    
    manager = MultiCloudManager(args.config)
    
    if args.deploy:
        providers = [args.provider] if args.provider else None
        results = manager.deploy_service(args.deploy, providers)
        
        print(f"Deployment results for {args.deploy}:")
        for result in results:
            if result.success:
                print(f"✅ {result.provider}: {result.endpoint} (${result.cost_estimate:.2f}/month)")
            else:
                print(f"❌ {result.provider}: {result.error_message}")
    
    elif args.scale:
        if ':' not in args.scale:
            print("Error: Scale format must be service_name:replicas")
            sys.exit(1)
        
        service_name, replicas_str = args.scale.split(':')
        try:
            replicas = int(replicas_str)
            success = manager.scale_service(service_name, replicas, args.provider)
            if success:
                print(f"✅ Scaled {service_name} to {replicas} replicas")
            else:
                print(f"❌ Failed to scale {service_name}")
        except ValueError:
            print("Error: Replicas must be a number")
            sys.exit(1)
    
    elif args.status:
        status = manager.get_multi_cloud_status()
        print(json.dumps(status, indent=2))
    
    elif args.cost_report:
        report = manager.generate_cost_report()
        print(json.dumps(report, indent=2))
    
    else:
        # Default: show status
        status = manager.get_multi_cloud_status()
        print(json.dumps(status, indent=2))

if __name__ == '__main__':
    main()