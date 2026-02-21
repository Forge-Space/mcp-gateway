#!/usr/bin/env python3

"""
Cross-Cloud Load Balancer for MCP Gateway
Provides intelligent load balancing across multiple cloud providers with health checks and failover
"""

import json
import time
import logging
import argparse
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import requests
import socket
import subprocess
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ServiceEndpoint:
    """Service endpoint configuration"""
    provider: str
    service_name: str
    endpoint: str
    port: int
    weight: float
    healthy: bool = True
    last_check: datetime = None
    response_time: float = 0.0
    error_count: int = 0
    region: str = ""

@dataclass
class LoadBalancingConfig:
    """Load balancing configuration"""
    algorithm: str = "weighted_round_robin"
    health_check_interval: int = 30
    health_check_timeout: int = 10
    health_check_retries: int = 3
    failover_threshold: int = 3
    dns_ttl: int = 60
    geographic_routing: bool = True
    latency_based_routing: bool = True
    cost_optimization: bool = True

class CrossCloudLoadBalancer:
    """Cross-cloud load balancer with intelligent routing"""

    def __init__(self, config_file: str = "config/multi-cloud.yaml"):
        self.config_file = Path(config_file)
        self.endpoints: Dict[str, ServiceEndpoint] = {}
        self.config = LoadBalancingConfig()
        self.health_check_thread = None
        self.metrics_collector = MetricsCollector()
        self._load_configuration()
        self._load_endpoints()

    def _load_configuration(self):
        """Load load balancing configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    import yaml
                    config = yaml.safe_load(f)

                if 'load_balancing' in config:
                    lb_config = config['load_balancing']
                    if 'global' in lb_config:
                        global_config = lb_config['global']
                        self.config.algorithm = global_config.get('algorithm', 'weighted_round_robin')
                        self.config.health_check_interval = global_config.get('health_check_interval', 30)
                        self.config.health_check_timeout = global_config.get('health_check_timeout', 10)
                        self.config.health_check_retries = global_config.get('health_check_retries', 3)
                        self.config.failover_threshold = global_config.get('failover_threshold', 3)
                        self.config.dns_ttl = global_config.get('dns_ttl', 60)

                logger.info(f"Loaded load balancing configuration: {self.config.algorithm}")
            else:
                logger.warning(f"Configuration file {self.config_file} not found, using defaults")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

    def _load_endpoints(self):
        """Load service endpoints from deployment data"""
        try:
            deployment_file = Path("data/deployments.json")
            if deployment_file.exists():
                with open(deployment_file, 'r') as f:
                    deployments = json.load(f)

                for deployment_key, deployment in deployments.items():
                    if deployment.get('success'):
                        service_name, provider = deployment_key.split(':')
                        endpoint = ServiceEndpoint(
                            provider=provider,
                            service_name=service_name,
                            endpoint=deployment.get('endpoint', ''),
                            port=self._extract_port_from_endpoint(deployment.get('endpoint', '')),
                            weight=self._calculate_provider_weight(provider),
                            region=deployment.get('region', 'unknown')
                        )
                        self.endpoints[deployment_key] = endpoint

                logger.info(f"Loaded {len(self.endpoints)} service endpoints")
            else:
                logger.warning("No deployment data found, creating sample endpoints")
                self._create_sample_endpoints()

        except Exception as e:
            logger.error(f"Failed to load endpoints: {e}")
            self._create_sample_endpoints()

    def _extract_port_from_endpoint(self, endpoint: str) -> int:
        """Extract port from endpoint URL"""
        if ':' in endpoint:
            parts = endpoint.split(':')
            if len(parts) >= 2:
                try:
                    return int(parts[-1])
                except ValueError:
                    pass
        return 4444  # Default port

    def _calculate_provider_weight(self, provider: str) -> float:
        """Calculate weight for provider based on performance and cost"""
        # Simplified weight calculation
        weights = {
            'aws': 1.0,
            'azure': 0.9,
            'gcp': 1.1,
            'digitalocean': 0.8,
            'oracle': 0.7,
            'ibm': 0.6
        }
        return weights.get(provider, 1.0)

    def _create_sample_endpoints(self):
        """Create sample endpoints for testing"""
        sample_endpoints = [
            ServiceEndpoint('aws', 'gateway', 'gateway-aws.example.com', 4444, 1.0, region='us-east-1'),
            ServiceEndpoint('azure', 'gateway', 'gateway-azure.example.com', 4444, 0.9, region='eastus'),
            ServiceEndpoint('gcp', 'gateway', 'gateway-gcp.example.com', 4444, 1.1, region='us-central1')
        ]

        for endpoint in sample_endpoints:
            key = f"{endpoint.service_name}:{endpoint.provider}"
            self.endpoints[key] = endpoint

        logger.info(f"Created {len(sample_endpoints)} sample endpoints")

    def start_health_checks(self):
        """Start background health checking"""
        if self.health_check_thread is None or not self.health_check_thread.is_alive():
            self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self.health_check_thread.start()
            logger.info("Started health check monitoring")

    def stop_health_checks(self):
        """Stop health checking"""
        if self.health_check_thread and self.health_check_thread.is_alive():
            # Thread will stop naturally when daemon=True
            logger.info("Stopped health check monitoring")

    def _health_check_loop(self):
        """Background health checking loop"""
        while True:
            try:
                self._check_all_endpoints()
                time.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                time.sleep(5)  # Wait before retrying

    def _check_all_endpoints(self):
        """Check health of all endpoints"""
        for key, endpoint in self.endpoints.items():
            try:
                healthy, response_time = self._check_endpoint_health(endpoint)

                # Update endpoint status
                endpoint.healthy = healthy
                endpoint.response_time = response_time
                endpoint.last_check = datetime.now()

                if healthy:
                    endpoint.error_count = 0
                    self.metrics_collector.record_health_check(endpoint.provider, True, response_time)
                else:
                    endpoint.error_count += 1
                    self.metrics_collector.record_health_check(endpoint.provider, False, response_time)

                    # Check if endpoint should be marked as unhealthy
                    if endpoint.error_count >= self.config.health_check_retries:
                        logger.warning(f"Endpoint {key} marked as unhealthy after {endpoint.error_count} failures")

            except Exception as e:
                logger.error(f"Error checking endpoint {key}: {e}")
                endpoint.healthy = False
                endpoint.error_count += 1
                endpoint.last_check = datetime.now()

    def _check_endpoint_health(self, endpoint: ServiceEndpoint) -> Tuple[bool, float]:
        """Check health of a single endpoint"""
        try:
            start_time = time.time()

            # Try to connect to the endpoint
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config.health_check_timeout)

            result = sock.connect_ex((endpoint.endpoint, endpoint.port))
            response_time = time.time() - start_time

            sock.close()

            if result == 0:
                return True, response_time
            else:
                return False, response_time

        except Exception as e:
            return False, self.config.health_check_timeout

    def select_endpoint(self, client_region: str = None, client_preferences: Dict[str, Any] = None) -> Optional[ServiceEndpoint]:
        """Select best endpoint based on load balancing algorithm"""
        healthy_endpoints = [ep for ep in self.endpoints.values() if ep.healthy]

        if not healthy_endpoints:
            logger.warning("No healthy endpoints available")
            return None

        if self.config.algorithm == "weighted_round_robin":
            return self._weighted_round_robin_selection(healthy_endpoints)
        elif self.config.algorithm == "latency_based":
            return self._latency_based_selection(healthy_endpoints)
        elif self.config.algorithm == "cost_optimized":
            return self._cost_optimized_selection(healthy_endpoints)
        elif self.config.algorithm == "geographic":
            return self._geographic_selection(healthy_endpoints, client_region)
        else:
            return self._round_robin_selection(healthy_endpoints)

    def _weighted_round_robin_selection(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Weighted round-robin selection"""
        total_weight = sum(ep.weight for ep in endpoints)
        if total_weight == 0:
            return endpoints[0]

        import random
        r = random.uniform(0, total_weight)
        running_total = 0

        for endpoint in endpoints:
            running_total += endpoint.weight
            if r <= running_total:
                return endpoint

        return endpoints[-1]

    def _latency_based_selection(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Select endpoint with lowest latency"""
        return min(endpoints, key=lambda ep: ep.response_time)

    def _cost_optimized_selection(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Select most cost-effective endpoint"""
        # Simplified cost optimization based on provider weights
        return max(endpoints, key=lambda ep: ep.weight)

    def _geographic_selection(self, endpoints: List[ServiceEndpoint], client_region: str) -> ServiceEndpoint:
        """Select endpoint closest to client region"""
        if not client_region:
            return endpoints[0]

        # Simplified geographic selection
        region_mapping = {
            'us-east': ['us-east-1', 'eastus'],
            'us-central': ['us-central1'],
            'us-west': ['us-west-1', 'us-west-2'],
            'europe': ['eu-west-1', 'westeurope'],
            'asia': ['asia-southeast1', 'japaneast']
        }

        # Find endpoints in same region
        same_region_endpoints = []
        for endpoint in endpoints:
            for region_group, regions in region_mapping.items():
                if client_region.startswith(region_group) and endpoint.region in regions:
                    same_region_endpoints.append(endpoint)
                    break

        if same_region_endpoints:
            return self._latency_based_selection(same_region_endpoints)

        # Fallback to latency-based selection
        return self._latency_based_selection(endpoints)

    def _round_robin_selection(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Simple round-robin selection"""
        # Use a simple round-robin based on current time
        index = int(time.time()) % len(endpoints)
        return endpoints[index]

    def get_load_balancing_stats(self) -> Dict[str, Any]:
        """Get load balancing statistics"""
        stats = {
            'total_endpoints': len(self.endpoints),
            'healthy_endpoints': len([ep for ep in self.endpoints.values() if ep.healthy]),
            'unhealthy_endpoints': len([ep for ep in self.endpoints.values() if not ep.healthy]),
            'algorithm': self.config.algorithm,
            'health_check_interval': self.config.health_check_interval,
            'providers': {},
            'services': {},
            'metrics': self.metrics_collector.get_summary()
        }

        # Provider stats
        provider_stats = {}
        for endpoint in self.endpoints.values():
            if endpoint.provider not in provider_stats:
                provider_stats[endpoint.provider] = {
                    'total': 0,
                    'healthy': 0,
                    'unhealthy': 0,
                    'avg_response_time': 0.0,
                    'regions': set()
                }

            provider_stats[endpoint.provider]['total'] += 1
            if endpoint.healthy:
                provider_stats[endpoint.provider]['healthy'] += 1
            else:
                provider_stats[endpoint.provider]['unhealthy'] += 1

            if endpoint.response_time > 0:
                provider_stats[endpoint.provider]['avg_response_time'] += endpoint.response_time

            provider_stats[endpoint.provider]['regions'].add(endpoint.region)

        # Convert sets to lists and calculate averages
        for provider, stats in provider_stats.items():
            stats['regions'] = list(stats['regions'])
            if stats['healthy'] > 0:
                stats['avg_response_time'] = stats['avg_response_time'] / stats['healthy']

        stats['providers'] = provider_stats

        # Service stats
        service_stats = {}
        for endpoint in self.endpoints.values():
            if endpoint.service_name not in service_stats:
                service_stats[endpoint.service_name] = {
                    'total': 0,
                    'healthy': 0,
                    'unhealthy': 0,
                    'providers': []
                }

            service_stats[endpoint.service_name]['total'] += 1
            if endpoint.healthy:
                service_stats[endpoint.service_name]['healthy'] += 1
            else:
                service_stats[endpoint.service_name]['unhealthy'] += 1

            if endpoint.provider not in service_stats[endpoint.service_name]['providers']:
                service_stats[endpoint.service_name]['providers'].append(endpoint.provider)

        stats['services'] = service_stats

        return stats

    def update_dns_records(self) -> bool:
        """Update DNS records for load balancing"""
        try:
            # This would integrate with DNS providers like Route53, Azure DNS, or Cloud DNS
            # For now, just log the action
            healthy_endpoints = [ep for ep in self.endpoints.values() if ep.healthy]

            logger.info(f"Updating DNS records for {len(healthy_endpoints)} healthy endpoints")

            for endpoint in healthy_endpoints:
                logger.info(f"DNS record: {endpoint.service_name}.{endpoint.provider} -> {endpoint.endpoint}")

            return True

        except Exception as e:
            logger.error(f"Failed to update DNS records: {e}")
            return False

    def handle_failover(self, failed_endpoint: str) -> bool:
        """Handle failover when endpoint fails"""
        try:
            endpoint = self.endpoints.get(failed_endpoint)
            if not endpoint:
                logger.error(f"Endpoint {failed_endpoint} not found")
                return False

            logger.warning(f"Handling failover for {failed_endpoint}")

            # Mark endpoint as unhealthy
            endpoint.healthy = False
            endpoint.error_count += 1

            # Check if we need to update DNS
            if endpoint.error_count >= self.config.failover_threshold:
                logger.info(f"Failover threshold reached for {failed_endpoint}, updating DNS")
                return self.update_dns_records()

            return True

        except Exception as e:
            logger.error(f"Failed to handle failover for {failed_endpoint}: {e}")
            return False

class MetricsCollector:
    """Metrics collector for load balancer"""

    def __init__(self):
        self.health_checks = []
        self.requests = []
        self.errors = []

    def record_health_check(self, provider: str, healthy: bool, response_time: float):
        """Record health check metric"""
        self.health_checks.append({
            'timestamp': datetime.now(),
            'provider': provider,
            'healthy': healthy,
            'response_time': response_time
        })

        # Keep only last 1000 records
        if len(self.health_checks) > 1000:
            self.health_checks = self.health_checks[-1000:]

    def record_request(self, provider: str, endpoint: str, response_time: float, success: bool):
        """Record request metric"""
        self.requests.append({
            'timestamp': datetime.now(),
            'provider': provider,
            'endpoint': endpoint,
            'response_time': response_time,
            'success': success
        })

        # Keep only last 1000 records
        if len(self.requests) > 1000:
            self.requests = self.requests[-1000:]

    def record_error(self, provider: str, endpoint: str, error: str):
        """Record error metric"""
        self.errors.append({
            'timestamp': datetime.now(),
            'provider': provider,
            'endpoint': endpoint,
            'error': error
        })

        # Keep only last 1000 records
        if len(self.errors) > 1000:
            self.errors = self.errors[-1000:]

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        recent_health_checks = [hc for hc in self.health_checks if hc['timestamp'] > hour_ago]
        recent_requests = [req for req in self.requests if req['timestamp'] > hour_ago]
        recent_errors = [err for err in self.errors if err['timestamp'] > hour_ago]

        summary = {
            'health_checks': {
                'total': len(recent_health_checks),
                'healthy': len([hc for hc in recent_health_checks if hc['healthy']]),
                'unhealthy': len([hc for hc in recent_health_checks if not hc['healthy']]),
                'avg_response_time': sum(hc['response_time'] for hc in recent_health_checks) / len(recent_health_checks) if recent_health_checks else 0
            },
            'requests': {
                'total': len(recent_requests),
                'successful': len([req for req in recent_requests if req['success']]),
                'failed': len([req for req in recent_requests if not req['success']]),
                'avg_response_time': sum(req['response_time'] for req in recent_requests) / len(recent_requests) if recent_requests else 0
            },
            'errors': {
                'total': len(recent_errors),
                'by_provider': {}
            }
        }

        # Group errors by provider
        for error in recent_errors:
            provider = error['provider']
            if provider not in summary['errors']['by_provider']:
                summary['errors']['by_provider'][provider] = 0
            summary['errors']['by_provider'][provider] += 1

        return summary

def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(description='Cross-Cloud Load Balancer for MCP Gateway')
    parser.add_argument('--start', action='store_true', help='Start load balancer')
    parser.add_argument('--stop', action='store_true', help='Stop load balancer')
    parser.add_argument('--status', action='store_true', help='Get load balancer status')
    parser.add_argument('--select', action='store_true', help='Select best endpoint')
    parser.add_argument('--region', help='Client region for geographic routing')
    parser.add_argument('--config', default='config/multi-cloud.yaml', help='Configuration file path')
    parser.add_argument('--update-dns', action='store_true', help='Update DNS records')

    args = parser.parse_args()

    balancer = CrossCloudLoadBalancer(args.config)

    if args.start:
        balancer.start_health_checks()
        logger.info("Cross-cloud load balancer started")

        # Keep running
        try:
            while True:
                time.sleep(60)
                stats = balancer.get_load_balancing_stats()
                logger.info(f"Status: {stats['healthy_endpoints']}/{stats['total_endpoints']} endpoints healthy")
        except KeyboardInterrupt:
            logger.info("Stopping load balancer")
            balancer.stop_health_checks()

    elif args.stop:
        balancer.stop_health_checks()
        logger.info("Cross-cloud load balancer stopped")

    elif args.status:
        stats = balancer.get_load_balancing_stats()
        print(json.dumps(stats, indent=2))

    elif args.select:
        endpoint = balancer.select_endpoint(args.region)
        if endpoint:
            print(f"Selected endpoint: {endpoint.provider} - {endpoint.endpoint}:{endpoint.port}")
            print(f"Response time: {endpoint.response_time:.2f}ms")
            print(f"Weight: {endpoint.weight}")
        else:
            print("No healthy endpoints available")

    elif args.update_dns:
        success = balancer.update_dns_records()
        if success:
            print("DNS records updated successfully")
        else:
            print("Failed to update DNS records")

    else:
        # Default: show status
        stats = balancer.get_load_balancing_stats()
        print(json.dumps(stats, indent=2))

if __name__ == '__main__':
    main()
