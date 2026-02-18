"""
Forge MCP Gateway Service Manager

Dynamic service management for MCP servers with on-demand scaling,
health monitoring, and configuration-driven deployment.
"""

import asyncio
import datetime
import signal
import sys
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

import docker
import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class ServiceState(Enum):
    """Service states for serverless-like behavior."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    SLEEPING = "sleeping"
    WAKING = "waking"
    STOPPING = "stopping"
    ERROR = "error"


class Settings(BaseSettings):
    """Service manager configuration."""
    config_path: str = "/config"
    log_level: str = "info"
    port: int = 9000
    docker_host: Optional[str] = None

    class Config:
        env_prefix = ""
        case_sensitive = False

    @classmethod
    def from_env(cls):
        """Create settings from environment."""
        settings = cls()
        return settings


class ServiceConfig(BaseModel):
    """Individual service configuration."""
    name: str
    image: str = "forge-mcp-gateway-translate:latest"
    command: List[str]
    port: int
    environment: Dict[str, str] = {}
    volumes: Dict[str, str] = {}
    resources: Dict[str, Any] = {}
    auto_start: bool = False
    health_check: Optional[Dict[str, Any]] = None
    sleep_policy: Optional[Dict[str, Any]] = None


class SleepPolicy(BaseModel):
    """Sleep policy configuration for serverless-like behavior."""
    enabled: bool = True
    idle_timeout: int = 300  # 5 minutes
    min_sleep_time: int = 60  # Don't sleep if used recently
    memory_reservation: str = "128MB"  # Reduced memory in sleep
    priority: str = "normal"  # Wake priority: low, normal, high


class ScalingPolicy(BaseModel):
    """Scaling policy configuration."""
    min_instances: int = 0
    max_instances: int = 1
    idle_timeout: int = 300  # 5 minutes
    target_cpu_utilization: float = 0.7
    target_memory_utilization: float = 0.8


class ServiceStatus(BaseModel):
    """Service status information."""
    name: str
    status: str  # running, stopped, starting, stopping, error, sleeping, waking
    container_id: Optional[str] = None
    port: Optional[int] = None
    last_accessed: Optional[str] = None
    resource_usage: Dict[str, float] = {}
    error_message: Optional[str] = None
    sleep_start_time: Optional[float] = None
    wake_count: int = 0
    total_sleep_time: float = 0.0
    # Enhanced metrics for high-efficiency Docker standards
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_limit: float = 0.0
    cpu_limit: float = 0.0
    wake_time_ms: Optional[float] = None
    sleep_efficiency: float = 0.0  # Memory reduction percentage
    state_transitions: int = 0
    uptime_seconds: float = 0.0
    last_state_change: Optional[float] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for a service."""
    service_name: str
    wake_times: deque  # Recent wake times in milliseconds
    sleep_times: deque   # Recent sleep times in milliseconds
    resource_usage: deque  # Recent resource usage snapshots
    error_count: int = 0
    last_error: Optional[str] = None
    total_requests: int = 0
    uptime_percentage: float = 0.0

    # Phase 4: Enhanced state transition metrics
    state_transitions: deque = None  # Track all state changes with timestamps
    transition_history: dict = None  # Count of each transition type
    state_durations: dict = None  # Time spent in each state
    last_state_change: Optional[float] = None
    current_state_start: Optional[float] = None

    # Performance and efficiency metrics
    wake_count: int = 0
    sleep_count: int = 0
    error_recovery_count: int = 0
    average_wake_time: float = 0.0
    average_sleep_time: float = 0.0
    total_sleep_duration: float = 0.0
    total_wake_duration: float = 0.0

    # Resource efficiency metrics
    memory_efficiency_score: float = 0.0  # 0-1, higher is better
    cpu_efficiency_score: float = 0.0     # 0-1, higher is better
    resource_utilization_efficiency: float = 0.0  # Overall efficiency

    # Alerting thresholds
    wake_time_threshold_ms: float = 500.0  # Alert if wake takes longer
    sleep_time_threshold_ms: float = 200.0  # Alert if sleep takes longer
    error_rate_threshold: float = 0.05     # Alert if error rate exceeds 5%

    def __post_init__(self):
        """Initialize deques and dictionaries."""
        if self.state_transitions is None:
            self.state_transitions = deque(maxlen=1000)
        if self.transition_history is None:
            self.transition_history = {
                'stopped_to_running': 0,
                'running_to_sleeping': 0,
                'sleeping_to_running': 0,
                'running_to_stopped': 0,
                'sleeping_to_stopped': 0,
                'stopped_to_sleeping': 0,
                'running_to_error': 0,
                'sleeping_to_error': 0,
                'stopped_to_error': 0,
                'error_to_running': 0,
                'error_to_sleeping': 0,
                'error_to_stopped': 0
            }
        if self.state_durations is None:
            self.state_durations = {
                'running': 0.0,
                'sleeping': 0.0,
                'stopped': 0.0,
                'error': 0.0,
                'starting': 0.0,
                'stopping': 0.0,
                'waking': 0.0
            }

    def record_state_transition(self, from_state: str, to_state: str, timestamp: Optional[float] = None):
        """Record a state transition with timing."""
        if timestamp is None:
            timestamp = time.time()

        # Update current state duration
        if self.current_state_start is not None and self.last_state_change:
            duration = timestamp - self.current_state_start
            if self.last_state_change in self.state_durations:
                self.state_durations[self.last_state_change] += duration

        # Record the transition
        transition_key = f"{from_state}_to_{to_state}"
        self.transition_history[transition_key] = self.transition_history.get(transition_key, 0) + 1

        # Add to transition history
        self.state_transitions.append({
            'from_state': from_state,
            'to_state': to_state,
            'timestamp': timestamp,
            'duration': duration if self.current_state_start else 0
        })

        # Update tracking variables
        self.last_state_change = to_state
        self.current_state_start = timestamp

        # Update counters
        if to_state == 'running' and from_state in ['sleeping', 'stopped', 'error']:
            self.wake_count += 1
        elif to_state == 'sleeping' and from_state in ['running', 'stopped', 'error']:
            self.sleep_count += 1
        elif to_state == 'running' and from_state == 'error':
            self.error_recovery_count += 1

    def get_state_efficiency_metrics(self) -> dict:
        """Calculate efficiency metrics for current state."""
        total_time = 0.0

        # Calculate total recorded time
        for duration in self.state_durations.values():
            total_time += duration

        if total_time == 0:
            return {
                'running_efficiency': 0.0,
                'sleep_efficiency': 0.0,
                'error_rate': 0.0,
                'transition_frequency': 0.0
            }

        running_efficiency = self.state_durations['running'] / total_time
        sleep_efficiency = self.state_durations['sleeping'] / total_time
        error_rate = self.state_durations['error'] / total_time
        transition_frequency = len(self.state_transitions) / max(total_time, 1)

        return {
            'running_efficiency': running_efficiency,
            'sleep_efficiency': sleep_efficiency,
            'error_rate': error_rate,
            'transition_frequency': transition_frequency,
            'total_transitions': len(self.state_transitions)
        }

    def should_trigger_alert(self, metric_type: str, value: float) -> bool:
        """Check if an alert should be triggered based on thresholds."""
        if metric_type == 'wake_time' and value > self.wake_time_threshold_ms:
            return True
        elif metric_type == 'sleep_time' and value > self.sleep_time_threshold_ms:
            return True
        elif metric_type == 'error_rate':
            total_requests = max(self.total_requests, 1)
            error_rate = self.error_count / total_requests
            return error_rate > self.error_rate_threshold
        return False


class GlobalSleepSettings(BaseModel):
    """Global sleep settings configuration."""

    model_config = {"arbitrary_types_allowed": True}

    enabled: bool = True
    max_sleeping_services: int = 15
    system_memory_threshold: str = "4GB"
    sleep_check_interval: int = 30
    wake_timeout: int = 10
    resource_monitoring: Dict[str, any] = {}
    performance_optimization: Dict[str, bool] = {}
    wake_priorities: Dict[str, List[str]] = {}
    resource_thresholds: Dict[str, float] = {}
    monitoring: Dict[str, any] = {}


class ResourceMonitor:
    """System resource monitoring."""

    def __init__(self):
        self.metrics_history = deque(maxlen=1000)

    def get_system_resources(self) -> Dict[str, float]:
        """Get current system resource usage."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "memory_used_gb": psutil.virtual_memory().used / (1024**3),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
        }

    def get_container_resources(self, container) -> Dict[str, float]:
        """Get resource usage for a specific container."""
        try:
            stats = container.stats(stream=False)
            return {
                "cpu_percent": self._calculate_cpu_percent(stats),
                "memory_usage_mb": stats["memory_stats"]["usage"] / (1024**2),
                "memory_limit_mb": stats["memory_stats"]["limit"] / (1024**2),
                "memory_percent": (stats["memory_stats"]["usage"] / stats["memory_stats"]["limit"]) * 100,
            }
        except Exception as e:
            logger.warning("Failed to get container stats", error=str(e))
            return {}

    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU percentage from container stats."""
        try:
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_cpu_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            if system_cpu_delta > 0:
                return (cpu_delta / system_cpu_delta) * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100
        except (KeyError, ZeroDivisionError):
            pass
        return 0.0


class ServiceManager:
    """Main service manager class."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.docker_client = None
        self.services: Dict[str, ServiceConfig] = {}
        self.service_status: Dict[str, ServiceStatus] = {}
        self.scaling_policies: Dict[str, ScalingPolicy] = {}
        self.sleep_policies: Dict[str, SleepPolicy] = {}
        self.global_sleep_settings: Optional[GlobalSleepSettings] = None
        self.resource_monitor = ResourceMonitor()
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self._shutdown_event = asyncio.Event()
        self._auto_sleep_task: Optional[asyncio.Task] = None
        self._resource_monitor_task: Optional[asyncio.Task] = None
        self._wake_queue: asyncio.Queue = asyncio.Queue()
        self._processing_wake = False

    async def initialize(self):
        """Initialize the service manager."""
        try:
            self.docker_client = docker.DockerClient(base_url="unix://var/run/docker.sock")
            self.docker_client.ping()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.warning(f"Docker client initialization failed - running in limited mode: {e}")
            self.docker_client = None

        # Load configuration
        await self._load_configuration()

        logger.info("Service manager initialized",
                   config_path=self.settings.config_path,
                   services_loaded=len(self.services))

    async def _load_configuration(self):
        """Load service configurations from files."""
        config_path = Path(self.settings.config_path)

        # Load services configuration
        services_file = config_path / "services.yml"
        if services_file.exists():
            import yaml
            with open(services_file, 'r') as f:
                services_data = yaml.safe_load(f)
                for name, config in services_data.get('services', {}).items():
                    # Convert environment values to strings
                    env_config = config.get('environment', {})
                    env_config = {str(k): str(v) for k, v in env_config.items()}
                    config['environment'] = env_config
                    self.services[name] = ServiceConfig(name=name, **config)

        # Load scaling policies
        policies_file = config_path / "scaling-policies.yml"
        if policies_file.exists():
            import yaml
            with open(policies_file, 'r') as f:
                policies_data = yaml.safe_load(f)
                for name, policy in policies_data.get('policies', {}).items():
                    self.scaling_policies[name] = ScalingPolicy(**policy)

        # Load global sleep settings
        sleep_settings_file = config_path / "sleep_settings.yml"
        if sleep_settings_file.exists():
            import yaml
            with open(sleep_settings_file, 'r') as f:
                sleep_data = yaml.safe_load(f)
                self.global_sleep_settings = GlobalSleepSettings(**sleep_data.get('sleep_settings', {}))
        else:
            # Default settings if file doesn't exist
            self.global_sleep_settings = GlobalSleepSettings()

        # Load sleep policies from service configurations
        for service_name, service_config in self.services.items():
            if service_config.sleep_policy:
                self.sleep_policies[service_name] = SleepPolicy(**service_config.sleep_policy)

        # Initialize service status and performance metrics
        for service_name in self.services:
            self.service_status[service_name] = ServiceStatus(
                name=service_name,
                status="stopped"
            )
            # Initialize performance metrics with history size from config
            history_size = self.global_sleep_settings.monitoring.get("performance_history_size", 1000)
            self.performance_metrics[service_name] = PerformanceMetrics(
                service_name=service_name,
                wake_times=deque(maxlen=history_size),
                sleep_times=deque(maxlen=history_size),
                resource_usage=deque(maxlen=history_size)
            )

        # Start background tasks
        self._auto_sleep_task = asyncio.create_task(self._auto_sleep_manager())
        self._resource_monitor_task = asyncio.create_task(self._resource_monitor_loop())
        self._wake_processor_task = asyncio.create_task(self._wake_processor())

    async def start_service(self, service_name: str) -> ServiceStatus:
        """Start a specific service."""
        if service_name not in self.services:
            raise HTTPException(
                status_code=404,
                detail=f"Service {service_name} not found"
            )

        service_config = self.services[service_name]
        current_status = self.service_status[service_name]

        if current_status.status == "running":
            logger.info("Service already running", service=service_name)
            return current_status

        try:
            logger.info("Starting service", service=service_name)

            # Update status
            current_status.status = "starting"

            # Prepare container configuration
            container_config = {
                "image": service_config.image,
                "command": service_config.command,
                "detach": True,
                "remove": True,
                "ports": {f"{service_config.port}/tcp": service_config.port},
                "environment": {
                    **service_config.environment,
                    "FORGE_SERVICE_NAME": service_name,
                },
                "name": f"forge-{service_name}",
            }

            # Add volumes if specified
            if service_config.volumes:
                container_config["volumes"] = service_config.volumes

            # Start container
            container = self.docker_client.containers.run(**container_config)

            # Update status
            current_status.status = "running"
            current_status.container_id = container.id
            current_status.port = service_config.port
            current_status.last_accessed = asyncio.get_event_loop().time()

            logger.info("Service started successfully",
                       service=service_name,
                       container_id=container.id)

            return current_status

        except Exception as e:
            current_status.status = "error"
            current_status.error_message = str(e)
            logger.error("Failed to start service",
                        service=service_name,
                        error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start service {service_name}: {str(e)}"
            )

    async def stop_service(self, service_name: str) -> ServiceStatus:
        """Stop a specific service."""
        if service_name not in self.service_status:
            raise HTTPException(
                status_code=404,
                detail=f"Service {service_name} not found"
            )

        current_status = self.service_status[service_name]

        if current_status.status != "running":
            logger.info("Service not running", service=service_name)
            return current_status

        try:
            logger.info("Stopping service", service=service_name)

            current_status.status = "stopping"

            if current_status.container_id:
                container = self.docker_client.containers.get(current_status.container_id)
                container.stop(timeout=10)
                container.remove()

            current_status.status = "stopped"
            current_status.container_id = None
            current_status.port = None

            logger.info("Service stopped successfully", service=service_name)

            return current_status

        except Exception as e:
            current_status.status = "error"
            current_status.error_message = str(e)
            logger.error("Failed to stop service",
                        service=service_name,
                        error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to stop service {service_name}: {str(e)}"
            )

    async def sleep_service(self, service_name: str) -> ServiceStatus:
        """Transition service to sleep state using Docker pause with resource optimization."""
        if service_name not in self.service_status:
            raise HTTPException(
                status_code=404,
                detail=f"Service {service_name} not found"
            )

        current_status = self.service_status[service_name]
        sleep_policy = self.sleep_policies.get(service_name)
        metrics = self.performance_metrics.get(service_name)

        # Check if sleep is enabled for this service
        if not sleep_policy or not sleep_policy.enabled:
            logger.info("Sleep not enabled for service", service=service_name)
            return current_status

        if current_status.status != "running":
            logger.info("Service not running, cannot sleep", service=service_name)
            return current_status

        # Check system resource pressure
        system_resources = self.resource_monitor.get_system_resources()
        if self._should_skip_sleep_due_to_pressure(system_resources):
            logger.info("Skipping sleep due to system resource pressure",
                       service=service_name,
                       memory_percent=system_resources["memory_percent"])
            return current_status

        # Check minimum sleep time
        current_time = time.time()
        if current_status.last_accessed:
            last_accessed_time = float(current_status.last_accessed)
            if current_time - last_accessed_time < sleep_policy.min_sleep_time:
                logger.info("Service used too recently, skipping sleep",
                           service=service_name,
                           time_since_access=current_time - last_accessed_time)
                return current_status

        try:
            logger.info("Sleeping service", service=service_name)
            sleep_start_time = time.time()

            # Record state transition from running to sleeping
            from_state = current_status.status
            current_status.status = "sleeping"
            current_status.sleep_start_time = sleep_start_time

            if metrics:
                metrics.record_state_transition(from_state, "sleeping", sleep_start_time)

            if current_status.container_id:
                container = self.docker_client.containers.get(current_status.container_id)

                # Apply memory optimization if configured
                if sleep_policy.memory_reservation:
                    await self._apply_memory_optimization(container, sleep_policy.memory_reservation)

                # Record pre-sleep metrics
                container_resources = self.resource_monitor.get_container_resources(container)
                if metrics and container_resources:
                    metrics.resource_usage.append(container_resources)

                # Pause the container
                container.pause()

            # Record sleep time
            sleep_duration = time.time() - sleep_start_time
            if metrics:
                metrics.sleep_times.append(sleep_duration * 1000)  # Convert to milliseconds
                metrics.total_sleep_duration += sleep_duration

            logger.info("Service slept successfully",
                       service=service_name,
                       sleep_duration_ms=sleep_duration * 1000)
            return current_status

        except Exception as e:
            from_state = current_status.status
            current_status.status = "error"
            if metrics:
                metrics.record_state_transition(from_state, "error")
                metrics.error_count += 1
                metrics.last_error = str(e)
            logger.error("Failed to sleep service",
                        service=service_name,
                        error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sleep service {service_name}: {str(e)}"
            )

    async def wake_service(self, service_name: str) -> ServiceStatus:
        """Wake service from sleep state using Docker unpause with performance monitoring."""
        if service_name not in self.service_status:
            raise HTTPException(
                status_code=404,
                detail=f"Service {service_name} not found"
            )

        current_status = self.service_status[service_name]
        metrics = self.performance_metrics.get(service_name)

        if current_status.status != "sleeping":
            logger.info("Service not sleeping, cannot wake", service=service_name)
            return current_status

        try:
            logger.info("Waking service", service=service_name)
            wake_start_time = time.time()

            # Record state transition from sleeping to waking
            from_state = current_status.status
            current_status.status = "waking"

            if metrics:
                metrics.record_state_transition(from_state, "waking", wake_start_time)

            if current_status.container_id:
                container = self.docker_client.containers.get(current_status.container_id)

                # Unpause the container
                container.unpause()

                # Restore memory settings if optimized
                sleep_policy = self.sleep_policies.get(service_name)
                if sleep_policy and sleep_policy.memory_reservation:
                    await self._restore_memory_settings(container)

            # Update sleep statistics and performance metrics
            if current_status.sleep_start_time:
                sleep_duration = wake_start_time - current_status.sleep_start_time
                current_status.total_sleep_time += sleep_duration
                current_status.sleep_start_time = None

            wake_duration = time.time() - wake_start_time
            current_status.wake_count += 1
            current_status.status = "running"
            current_status.last_accessed = str(wake_start_time)

            # Record transition from waking to running
            if metrics:
                metrics.record_state_transition("waking", "running", wake_start_time + wake_duration)
                metrics.wake_times.append(wake_duration * 1000)  # Convert to milliseconds
                metrics.total_wake_duration += wake_duration
                metrics.total_requests += 1

            logger.info("Service woke successfully",
                       service=service_name,
                       wake_time_ms=wake_duration * 1000,
                       total_sleep_time=current_status.total_sleep_time)

            return current_status

        except Exception as e:
            from_state = current_status.status
            current_status.status = "error"
            current_status.error_message = str(e)
            if metrics:
                metrics.record_state_transition(from_state, "error")
                metrics.error_count += 1
                metrics.last_error = str(e)
            logger.error("Failed to wake service",
                        service=service_name,
                        error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to wake service {service_name}: {str(e)}"
            )

    # Phase 4: Alerting System for Sleep/Wake Events
    def _check_and_trigger_alerts(self, service_name: str, metrics: PerformanceMetrics):
        """Check if any alerts should be triggered based on metrics."""
        alerts = []

        # Check wake time alerts
        if metrics.wake_times:
            latest_wake_time = metrics.wake_times[-1]
            if metrics.should_trigger_alert('wake_time', latest_wake_time):
                alerts.append({
                    'type': 'wake_time_exceeded',
                    'service': service_name,
                    'value': latest_wake_time,
                    'threshold': metrics.wake_time_threshold_ms,
                    'message': f'Wake time {latest_wake_time:.2f}ms exceeded threshold {metrics.wake_time_threshold_ms}ms',
                    'severity': 'warning',
                    'timestamp': time.time()
                })

        # Check sleep time alerts
        if metrics.sleep_times:
            latest_sleep_time = metrics.sleep_times[-1]
            if metrics.should_trigger_alert('sleep_time', latest_sleep_time):
                alerts.append({
                    'type': 'sleep_time_exceeded',
                    'service': service_name,
                    'value': latest_sleep_time,
                    'threshold': metrics.sleep_time_threshold_ms,
                    'message': f'Sleep time {latest_sleep_time:.2f}ms exceeded threshold {metrics.sleep_time_threshold_ms}ms',
                    'severity': 'warning',
                    'timestamp': time.time()
                })

        # Check error rate alerts
        total_operations = metrics.wake_count + metrics.sleep_count
        if total_operations > 0:
            error_rate = metrics.error_count / total_operations
            if metrics.should_trigger_alert('error_rate', error_rate):
                alerts.append({
                    'type': 'high_error_rate',
                    'service': service_name,
                    'value': error_rate,
                    'threshold': metrics.error_rate_threshold,
                    'message': f'Error rate {error_rate:.2%} exceeded threshold {metrics.error_rate_threshold:.2%}',
                    'severity': 'critical',
                    'timestamp': time.time()
                })

        # Check state transition frequency alerts
        efficiency_metrics = metrics.get_state_efficiency_metrics()
        if efficiency_metrics['transition_frequency'] > 0.1:  # More than 1 transition per 10 seconds
            alerts.append({
                'type': 'high_transition_frequency',
                'service': service_name,
                'value': efficiency_metrics['transition_frequency'],
                'threshold': 0.1,
                'message': f'Transition frequency {efficiency_metrics["transition_frequency"]:.3f} transitions/second is unusually high',
                'severity': 'warning',
                'timestamp': time.time()
            })

        # Log alerts
        for alert in alerts:
            logger.warning("Alert triggered",
                         service=alert['service'],
                         type=alert['type'],
                         severity=alert['severity'],
                         message=alert['message'])

        return alerts

    def get_service_alerts(self, service_name: str) -> List[dict]:
        """Get recent alerts for a specific service."""
        if service_name not in self.performance_metrics:
            return []

        metrics = self.performance_metrics[service_name]
        return self._check_and_trigger_alerts(service_name, metrics)

    def get_all_system_alerts(self) -> dict:
        """Get all system alerts across all services."""
        all_alerts = {}

        for service_name, metrics in self.performance_metrics.items():
            service_alerts = self._check_and_trigger_alerts(service_name, metrics)
            if service_alerts:
                all_alerts[service_name] = service_alerts

        return {
            'alerts': all_alerts,
            'total_alerts': sum(len(alerts) for alerts in all_alerts.values()),
            'timestamp': time.time()
        }

    def get_system_health_summary(self) -> dict:
        """Get overall system health summary for monitoring dashboard."""
        total_services = len(self.services)
        running_count = sum(1 for s in self.service_status.values() if s.status == "running")
        sleeping_count = sum(1 for s in self.service_status.values() if s.status == "sleeping")
        stopped_count = sum(1 for s in self.service_status.values() if s.status == "stopped")
        error_count = sum(1 for s in self.service_status.values() if s.status == "error")

        # Calculate aggregate metrics
        total_wake_time = 0
        total_sleep_time = 0
        total_errors = 0
        total_transitions = 0

        for metrics in self.performance_metrics.values():
            if metrics.wake_times:
                total_wake_time += sum(metrics.wake_times)
            if metrics.sleep_times:
                total_sleep_time += sum(metrics.sleep_times)
            total_errors += metrics.error_count
            total_transitions += len(metrics.state_transitions)

        # Get system resources
        system_resources = self.resource_monitor.get_system_resources()

        # Calculate health score (0-100)
        health_score = 100
        if total_services > 0:
            error_penalty = (error_count / total_services) * 30
            resource_penalty = max(0, (system_resources["memory_percent"] - 70) * 0.5)
            health_score = max(0, 100 - error_penalty - resource_penalty)

        return {
            'health_score': round(health_score, 1),
            'service_status': {
                'total': total_services,
                'running': running_count,
                'sleeping': sleeping_count,
                'stopped': stopped_count,
                'error': error_count
            },
            'performance': {
                'total_wake_time_ms': total_wake_time,
                'total_sleep_time_ms': total_sleep_time,
                'total_errors': total_errors,
                'total_transitions': total_transitions,
                'avg_wake_time_ms': total_wake_time / max(total_wake_time, 1),
                'avg_sleep_time_ms': total_sleep_time / max(total_sleep_time, 1)
            },
            'resources': system_resources,
            'alerts': self.get_all_system_alerts(),
            'timestamp': time.time()
        }

    async def get_service_status(self, service_name: str) -> ServiceStatus:
        """Get the status of a specific service."""
        if service_name not in self.service_status:
            raise HTTPException(
                status_code=404,
                detail=f"Service {service_name} not found"
            )

        current_status = self.service_status[service_name]

        # Update container status if running
        if current_status.status == "running" and current_status.container_id:
            try:
                container = self.docker_client.containers.get(current_status.container_id)
                container.reload()

                if container.status != "running":
                    current_status.status = "stopped"
                    current_status.container_id = None
                    current_status.port = None

            except docker.errors.NotFound:
                current_status.status = "stopped"
                current_status.container_id = None
                current_status.port = None
            except Exception as e:
                logger.warning("Failed to check container status",
                            service=service_name,
                            error=str(e))

        return current_status

    async def list_services(self) -> List[ServiceStatus]:
        """List all services and their status."""
        services = []
        for service_name in self.service_status:
            status = await self.get_service_status(service_name)
            services.append(status)
        return services

    async def auto_scale_services(self):
        """Automatically scale services based on policies."""
        # This is a placeholder for future auto-scaling implementation
        # For now, we'll just log the action
        logger.info("Auto-scaling check completed")

    async def _apply_memory_optimization(self, container, memory_reservation: str):
        """Apply memory optimization for sleeping containers."""
        try:
            # Convert memory reservation to bytes
            memory_bytes = self._parse_memory_string(memory_reservation)

            # Update container memory limits
            container.update(
                mem_limit=memory_bytes,
                mem_reservation=memory_bytes
            )
            logger.info("Applied memory optimization",
                       memory_reservation=memory_reservation)
        except Exception as e:
            logger.warning("Failed to apply memory optimization",
                         error=str(e))

    async def _restore_memory_settings(self, container):
        """Restore original memory settings for waking containers."""
        try:
            # Reset to default memory limits (or service-specific limits)
            container.update(
                mem_limit=0,  # Remove limit
                mem_reservation=0  # Remove reservation
            )
            logger.info("Restored memory settings")
        except Exception as e:
            logger.warning("Failed to restore memory settings",
                         error=str(e))

    def _parse_memory_string(self, memory_str: str) -> int:
        """Parse memory string (e.g., '128MB', '1GB') to bytes."""
        memory_str = memory_str.upper()
        if memory_str.endswith('MB'):
            return int(memory_str[:-2]) * 1024 * 1024
        elif memory_str.endswith('GB'):
            return int(memory_str[:-2]) * 1024 * 1024 * 1024
        elif memory_str.endswith('KB'):
            return int(memory_str[:-2]) * 1024
        else:
            # Assume bytes if no unit
            return int(memory_str)

    def _should_skip_sleep_due_to_pressure(self, system_resources: Dict[str, float]) -> bool:
        """Check if sleep should be skipped due to system resource pressure."""
        if not self.global_sleep_settings:
            return False

        thresholds = self.global_sleep_settings.resource_thresholds

        # Check memory pressure
        memory_pressure = system_resources.get("memory_percent", 0) / 100
        if memory_pressure > thresholds.get("high_memory_pressure", 0.9):
            return True

        # Check CPU pressure
        cpu_pressure = system_resources.get("cpu_percent", 0) / 100
        if cpu_pressure > thresholds.get("cpu_pressure_threshold", 0.8):
            return True

        return False

    def _get_service_priority(self, service_name: str) -> int:
        """Get wake priority for a service (lower number = higher priority)."""
        if not self.global_sleep_settings:
            return 2  # Default priority

        priorities = self.global_sleep_settings.wake_priorities

        for priority_level, services in priorities.items():
            if service_name in services:
                if priority_level == "high":
                    return 0
                elif priority_level == "normal":
                    return 1
                else:
                    return 2

        return 2  # Default to low priority

    async def _resource_monitor_loop(self):
        """Background task to monitor system resources and optimize states."""
        while not self._shutdown_event.is_set():
            try:
                if not self.global_sleep_settings or not self.global_sleep_settings.resource_monitoring.get("enabled", True):
                    await asyncio.sleep(60)
                    continue

                system_resources = self.resource_monitor.get_system_resources()
                self.resource_monitor.metrics_history.append(system_resources)

                # Check for resource pressure and adjust service states accordingly
                await self._handle_resource_pressure(system_resources)

                # Wait for next check
                check_interval = self.global_sleep_settings.resource_monitoring.get("check_interval", 60)
                await asyncio.wait_for(self._shutdown_event.wait(), timeout=check_interval)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("Error in resource monitor loop", error=str(e))
                await asyncio.sleep(30)

    async def _handle_resource_pressure(self, system_resources: Dict[str, float]):
        """Handle system resource pressure by adjusting service states."""
        memory_pressure = system_resources.get("memory_percent", 0) / 100
        thresholds = self.global_sleep_settings.resource_thresholds

        # If high memory pressure, force sleep low-priority services
        if memory_pressure > thresholds.get("high_memory_pressure", 0.9):
            await self._force_sleep_low_priority_services()

        # If low memory pressure, consider pre-warming critical services
        elif memory_pressure < thresholds.get("low_memory_pressure", 0.5):
            if self.global_sleep_settings.performance_optimization.get("pre_warm_critical_services", False):
                await self._pre_warm_critical_services()

    async def _force_sleep_low_priority_services(self):
        """Force sleep low-priority services under memory pressure."""
        running_services = [
            name for name, status in self.service_status.items()
            if status.status == "running"
        ]

        # Sort by priority (low priority first)
        running_services.sort(key=lambda x: self._get_service_priority(x), reverse=True)

        for service_name in running_services:
            if self._get_service_priority(service_name) >= 2:  # Low priority
                try:
                    await self.sleep_service(service_name)
                    logger.info("Force-slept low priority service due to memory pressure",
                               service=service_name)
                except Exception as e:
                    logger.warning("Failed to force sleep service",
                                service=service_name,
                                error=str(e))

    async def _pre_warm_critical_services(self):
        """Pre-warm critical services when resources are available."""
        sleeping_services = [
            name for name, status in self.service_status.items()
            if status.status == "sleeping"
        ]

        # Sort by priority (high priority first)
        sleeping_services.sort(key=lambda x: self._get_service_priority(x))

        for service_name in sleeping_services:
            if self._get_service_priority(service_name) <= 0:  # High priority
                try:
                    await self.wake_service(service_name)
                    logger.info("Pre-warmed critical service",
                               service=service_name)
                except Exception as e:
                    logger.warning("Failed to pre-warm service",
                                service=service_name,
                                error=str(e))

    async def _wake_processor(self):
        """Background task to process wake requests with priority ordering."""
        while not self._shutdown_event.is_set():
            try:
                # Wait for wake requests
                service_name = await asyncio.wait_for(self._wake_queue.get(), timeout=1.0)

                if not self._processing_wake:
                    self._processing_wake = True
                    try:
                        await self.wake_service(service_name)
                    finally:
                        self._processing_wake = False

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("Error in wake processor", error=str(e))
                self._processing_wake = False

    async def request_wake(self, service_name: str):
        """Request a service wake with priority queuing."""
        if service_name not in self.service_status:
            raise HTTPException(
                status_code=404,
                detail=f"Service {service_name} not found"
            )

        current_status = self.service_status[service_name]

        if current_status.status == "sleeping":
            # Add to wake queue (priority is handled by queue processing)
            await self._wake_queue.put(service_name)
            logger.info("Queued wake request", service=service_name)
        elif current_status.status == "running":
            logger.info("Service already running", service=service_name)
        else:
            logger.info("Service not in sleepable state",
                       service=service_name,
                       status=current_status.status)

    def predict_service_wake_need(self, service_name: str, hours_ahead: int = 1) -> float:
        """Predict the likelihood that a service will need to be woken up in the next N hours.

        Returns a probability score between 0.0 (unlikely) and 1.0 (very likely).
        """
        if service_name not in self.performance_metrics:
            return 0.5  # Default probability for unknown services

        metrics = self.performance_metrics[service_name]
        current_time = datetime.datetime.now()

        # Factors for prediction:
        factors = []

        # 1. Recent usage frequency (higher = more likely to be needed)
        if metrics.total_requests > 0:
            # Simple heuristic: more requests = higher probability
            usage_factor = min(metrics.total_requests / 100.0, 1.0)
            factors.append(usage_factor)

        # 2. Time of day patterns (business hours vs off-hours)
        current_hour = current_time.hour
        if 9 <= current_hour <= 17:  # Business hours
            time_factor = 0.7
        elif 18 <= current_hour <= 22:  # Evening
            time_factor = 0.5
        else:  # Night/early morning
            time_factor = 0.3
        factors.append(time_factor)

        # 3. Service priority (high priority services more likely to be needed)
        priority = self._get_service_priority(service_name)
        if priority == 0:  # High priority
            priority_factor = 0.8
        elif priority == 1:  # Normal priority
            priority_factor = 0.5
        else:  # Low priority
            priority_factor = 0.3
        factors.append(priority_factor)

        # 4. Recent wake patterns (if recently woken, might be needed again)
        if metrics.wake_times and len(metrics.wake_times) > 0:
            # Check if service was woken recently (last hour)
            recent_wakes = len([t for t in metrics.wake_times if time.time() - t/1000 < 3600])
            wake_factor = min(recent_wakes / 5.0, 1.0)
            factors.append(wake_factor)

        # Calculate weighted average
        if factors:
            return sum(factors) / len(factors)
        else:
            return 0.5  # Default probability

    def get_pre_warm_candidates(self, max_candidates: int = 3) -> List[Tuple[str, float]]:
        """Get services that should be pre-warmed based on prediction.

        Returns a list of (service_name, probability) tuples sorted by probability.
        """
        candidates = []

        for service_name in self.services:
            if service_name not in self.service_status:
                continue

            current_status = self.service_status[service_name]

            # Only consider sleeping services for pre-warming
            if current_status.status != "sleeping":
                continue

            # Calculate wake probability
            probability = self.predict_service_wake_need(service_name)
            candidates.append((service_name, probability))

        # Sort by probability (highest first) and return top candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:max_candidates]

    async def apply_wake_predictions(self):
        """Apply wake predictions to pre-warm likely services."""
        if not self.global_sleep_settings or not self.global_sleep_settings.performance_optimization.get("wake_prediction_enabled", False):
            return

        # Get pre-warm candidates
        candidates = self.get_pre_warm_candidates()

        # Check system resources before pre-warming
        system_resources = self.resource_monitor.get_system_resources()
        memory_pressure = system_resources.get("memory_percent", 0) / 100

        # Only pre-warm if memory pressure is low
        if memory_pressure > 0.7:  # 70% memory usage threshold
            logger.info("Skipping pre-warming due to memory pressure",
                       memory_percent=memory_pressure * 100)
            return

        # Pre-warm high-probability services
        for service_name, probability in candidates:
            if probability > 0.7:  # High probability threshold
                try:
                    await self.wake_service(service_name)
                    logger.info("Pre-warmed service based on prediction",
                               service=service_name,
                               probability=probability)
                except Exception as e:
                    logger.warning("Failed to pre-warm service",
                                service=service_name,
                                error=str(e))

    async def _auto_sleep_manager(self):
        """Background task to manage service sleep states."""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()

                for service_name, status in self.service_status.items():
                    sleep_policy = self.sleep_policies.get(service_name)

                    # Skip if sleep is not enabled
                    if not sleep_policy or not sleep_policy.enabled:
                        continue

                    # Only check running services
                    if status.status != "running":
                        continue

                    # Check if service should sleep due to inactivity
                    if status.last_accessed:
                        last_accessed_time = float(status.last_accessed)
                        idle_time = current_time - last_accessed_time

                        if idle_time >= sleep_policy.idle_timeout:
                            logger.info("Auto-sleeping service due to inactivity",
                                       service=service_name,
                                       idle_time=idle_time)
                            try:
                                await self.sleep_service(service_name)
                            except Exception as e:
                                logger.error("Failed to auto-sleep service",
                                            service=service_name,
                                            error=str(e))

                # Wait before next check (30 seconds)
                try:
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=30.0)
                except asyncio.TimeoutError:
                    continue  # Continue the loop

            except Exception as e:
                logger.error("Error in auto-sleep manager", error=str(e))
                await asyncio.sleep(30)  # Wait before retrying

    async def _collect_resource_metrics(self, service_name: str, container_id: str):
        """Collect resource usage metrics for a container."""
        try:
            container = self.docker_client.containers.get(container_id)
            stats = container.stats(stream=False)

            # Calculate CPU and memory usage
            cpu_usage = 0.0
            memory_usage = 0.0
            memory_limit = 0.0

            if stats:
                # CPU usage calculation
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                          stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                             stats['precpu_stats']['system_cpu_usage']

                if system_delta > 0:
                    cpu_usage = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100

                # Memory usage
                memory_usage = stats['memory_stats']['usage']
                memory_limit = stats['memory_stats']['limit']

            # Update service status with metrics
            if service_name in self.service_status:
                status = self.service_status[service_name]
                status.cpu_usage = round(cpu_usage, 2)
                status.memory_usage = round(memory_usage / 1024 / 1024, 2)  # MB
                status.memory_limit = round(memory_limit / 1024 / 1024, 2)  # MB

                # Calculate sleep efficiency if service has memory reservation
                if service_name in self.sleep_policies:
                    sleep_policy = self.sleep_policies[service_name]
                    running_memory = status.memory_usage
                    sleep_memory = float(sleep_policy.memory_reservation.replace('MB', ''))
                    if running_memory > 0:
                        status.sleep_efficiency = round(((running_memory - sleep_memory) / running_memory) * 100, 2)

            logger.debug("Collected resource metrics",
                        service=service_name,
                        cpu_usage=cpu_usage,
                        memory_usage_mb=memory_usage / 1024 / 1024)

        except Exception as e:
            logger.warning("Failed to collect resource metrics",
                        service=service_name,
                        error=str(e))

    async def _update_service_metrics(self, service_name: str):
        """Update all metrics for a service."""
        if service_name not in self.service_status:
            return

        status = self.service_status[service_name]
        current_time = time.time()

        # Update uptime
        if status.status == "running" and status.last_state_change:
            status.uptime_seconds = current_time - status.last_state_change

        # Collect resource metrics if container is running
        if status.container_id and status.status in ["running", "sleeping"]:
            await self._collect_resource_metrics(service_name, status.container_id)

    async def get_performance_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for all services."""
        metrics = {}

        for service_name, status in self.service_status.items():
            metrics[service_name] = {
                "cpu_usage": status.cpu_usage,
                "memory_usage": status.memory_usage,
                "memory_limit": status.memory_limit,
                "wake_count": status.wake_count,
                "total_sleep_time": status.total_sleep_time,
                "sleep_efficiency": status.sleep_efficiency,
                "state_transitions": status.state_transitions,
                "uptime_seconds": status.uptime_seconds
            }

            # Add wake time if available
            if status.wake_time_ms:
                metrics[service_name]["wake_time_ms"] = status.wake_time_ms

        return metrics

    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide performance metrics."""
        try:
            # Get Docker system info if client is available
            if self.docker_client:
                docker_info = self.docker_client.info()
            else:
                docker_info = {}

            # Count services by state
            running_count = sum(1 for s in self.service_status.values() if s.status == "running")
            sleeping_count = sum(1 for s in self.service_status.values() if s.status == "sleeping")
            stopped_count = sum(1 for s in self.service_status.values() if s.status == "stopped")
            error_count = sum(1 for s in self.service_status.values() if s.status == "error")

            # Calculate total resource usage
            total_memory_usage = sum(s.memory_usage for s in self.service_status.values())
            total_cpu_usage = sum(s.cpu_usage for s in self.service_status.values())

            # Calculate efficiency metrics
            total_services = len(self.service_status)
            efficiency_metrics = {
                "services_running": running_count,
                "services_sleeping": sleeping_count,
                "services_stopped": stopped_count,
                "services_error": error_count,
                "total_services": total_services,
                "total_memory_usage_mb": total_memory_usage,
                "average_cpu_usage": total_cpu_usage / max(total_services, 1),
                "sleep_ratio": sleeping_count / max(total_services, 1) * 100,
                "running_ratio": running_count / max(total_services, 1) * 100
            }

            # Add Docker system info if available
            if docker_info:
                efficiency_metrics.update({
                    "docker_version": docker_info.get("ServerVersion", "unknown"),
                    "docker_ncpu": docker_info.get("NCPU", 0),
                    "docker_mem_total": docker_info.get("MemTotal", 0),
                    "docker_mem_free": docker_info.get("MemFree", 0)
                })

            return efficiency_metrics

        except Exception as e:
            logger.error("Failed to get system metrics", error=str(e))
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, str]:
        """Perform health check."""
        try:
            # Check Docker connection if client is available
            if self.docker_client:
                self.docker_client.ping()
                docker_connection = "ok"
            else:
                docker_connection = "limited_mode"

            # Count running services
            running_count = sum(
                1 for status in self.service_status.values()
                if status.status == "running"
            )

            return {
                "status": "healthy",
                "docker_connection": docker_connection,
                "services_running": str(running_count),
                "services_total": str(len(self.services))
            }
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def shutdown(self):
        """Shutdown the service manager."""
        logger.info("Shutting down service manager")

        # Cancel background tasks
        tasks_to_cancel = [
            self._auto_sleep_task,
            self._resource_monitor_task,
        ]

        # Add wake processor task if it exists
        if hasattr(self, '_wake_processor_task'):
            tasks_to_cancel.append(self._wake_processor_task)

        for task in tasks_to_cancel:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Wake all sleeping services before stopping
        for service_name, status in self.service_status.items():
            if status.status == "sleeping":
                try:
                    await self.wake_service(service_name)
                    logger.info("Woke sleeping service during shutdown", service=service_name)
                except Exception as e:
                    logger.warning("Failed to wake sleeping service during shutdown",
                                service=service_name,
                                error=str(e))

        # Stop all running services
        for service_name in list(self.service_status.keys()):
            try:
                await self.stop_service(service_name)
            except Exception as e:
                logger.warning("Failed to stop service during shutdown",
                            service=service_name,
                            error=str(e))

        # Close Docker client
        if self.docker_client:
            self.docker_client.close()

        logger.info("Service manager shutdown complete")


# FastAPI application
app = FastAPI(
    title="Forge MCP Gateway Service Manager",
    description="Dynamic service management for MCP servers",
    version="1.0.0"
)

# Global service manager instance
service_manager: Optional[ServiceManager] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the service manager on startup."""
    global service_manager

    settings = Settings.from_env()
    service_manager = ServiceManager(settings)
    await service_manager.initialize()

    logger.info("Service manager started", port=settings.port)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global service_manager
    if service_manager:
        await service_manager.shutdown()


@app.get("/health")
async def health():
    """Health check endpoint."""
    if service_manager:
        return await service_manager.health_check()
    return {"status": "initializing"}


@app.get("/services")
async def list_services():
    """List all services."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    return await service_manager.list_services()


@app.get("/services/{service_name}")
async def get_service(service_name: str):
    """Get specific service status."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    return await service_manager.get_service_status(service_name)


@app.post("/services/{service_name}/start")
async def start_service(service_name: str):
    """Start a service."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    return await service_manager.start_service(service_name)


@app.post("/services/{service_name}/stop")
async def stop_service(service_name: str):
    """Stop a service."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    return await service_manager.stop_service(service_name)


@app.post("/services/{service_name}/sleep")
async def sleep_service(service_name: str):
    """Put a service to sleep."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    return await service_manager.sleep_service(service_name)


@app.post("/services/{service_name}/wake")
async def wake_service(service_name: str):
    """Wake a service from sleep."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    return await service_manager.wake_service(service_name)


@app.post("/services/auto-scale")
async def auto_scale():
    """Trigger auto-scaling."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    await service_manager.auto_scale_services()
    return {"message": "Auto-scaling triggered"}


@app.get("/metrics/performance")
async def get_performance_metrics():
    """Get performance metrics for all services."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    return await service_manager.get_performance_metrics()


@app.get("/metrics/system")
async def get_system_metrics():
    """Get system-wide performance metrics."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    return await service_manager.get_system_metrics()


@app.get("/metrics/efficiency")
async def get_efficiency_metrics():
    """Get efficiency metrics and compliance status."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    system_metrics = await service_manager.get_system_metrics()

    # Efficiency targets from high-efficiency Docker standards
    efficiency_targets = {
        "sleep_ratio_target": 70.0,  # 70% of services should be sleeping when idle
        "wake_time_target_ms": 200.0,  # < 200ms wake time
        "memory_reduction_target": 60.0,  # > 60% memory reduction when sleeping
        "cpu_usage_target": 5.0,  # < 5% CPU for sleeping services
        "service_availability_target": 99.8  # 99.8% effective availability
    }

    # Current efficiency metrics
    current_efficiency = {
        "sleep_ratio": system_metrics.get("sleep_ratio", 0.0),
        "running_ratio": system_metrics.get("running_ratio", 0.0),
        "total_memory_usage_mb": system_metrics.get("total_memory_usage_mb", 0.0),
        "average_cpu_usage": system_metrics.get("average_cpu_usage", 0.0)
    }

    # Compliance status
    compliance_status = {
        "sleep_ratio_compliant": current_efficiency["sleep_ratio"] >= efficiency_targets["sleep_ratio_target"] * 0.5,  # At least half of target
        "cpu_usage_compliant": current_efficiency["average_cpu_usage"] <= efficiency_targets["cpu_usage_target"],
        "overall_compliance": "unknown"  # Will be calculated below
    }

    # Calculate overall compliance
    compliant_checks = sum(1 for v in compliance_status.values() if v is True)
    total_checks = len([k for k, v in compliance_status.items() if k != "overall_compliance"])
    compliance_percentage = (compliant_checks / total_checks * 100) if total_checks > 0 else 0
    compliance_status["overall_compliance"] = "compliant" if compliance_percentage >= 80 else "needs_improvement"

    return {
        "efficiency_targets": efficiency_targets,
        "current_efficiency": current_efficiency,
        "compliance_status": compliance_status,
        "compliance_percentage": round(compliance_percentage, 2),
        "system_metrics": system_metrics
    }


@app.post("/services/{service_name}/wake-request")
async def request_wake(service_name: str):
    """Request a service wake with priority queuing."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    await service_manager.request_wake(service_name)
    return {"message": f"Wake request queued for {service_name}"}


@app.get("/services/{service_name}/metrics")
async def get_service_metrics(service_name: str):
    """Get performance metrics for a specific service."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    if service_name not in service_manager.performance_metrics:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    metrics = service_manager.performance_metrics[service_name]

    # Calculate statistics
    wake_times = list(metrics.wake_times) if metrics.wake_times else []
    sleep_times = list(metrics.sleep_times) if metrics.sleep_times else []

    return {
        "service_name": metrics.service_name,
        "wake_count": metrics.wake_count,
        "total_requests": metrics.total_requests,
        "error_count": metrics.error_count,
        "last_error": metrics.last_error,
        "wake_time_stats": {
            "count": len(wake_times),
            "avg_ms": sum(wake_times) / len(wake_times) if wake_times else 0,
            "min_ms": min(wake_times) if wake_times else 0,
            "max_ms": max(wake_times) if wake_times else 0,
            "p95_ms": sorted(wake_times)[int(len(wake_times) * 0.95)] if wake_times and len(wake_times) > 20 else 0,
        },
        "sleep_time_stats": {
            "count": len(sleep_times),
            "avg_ms": sum(sleep_times) / len(sleep_times) if sleep_times else 0,
            "min_ms": min(sleep_times) if sleep_times else 0,
            "max_ms": max(sleep_times) if sleep_times else 0,
        },
        "uptime_percentage": metrics.uptime_percentage,
    }


@app.get("/system/resources")
async def get_system_resources():
    """Get current system resource usage."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    return service_manager.resource_monitor.get_system_resources()


@app.get("/system/metrics")
async def get_system_metrics():
    """Get system-wide performance metrics."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    # Aggregate metrics across all services
    total_services = len(service_manager.services)
    running_count = sum(1 for s in service_manager.service_status.values() if s.status == "running")
    sleeping_count = sum(1 for s in service_manager.service_status.values() if s.status == "sleeping")
    stopped_count = sum(1 for s in service_manager.service_status.values() if s.status == "stopped")
    error_count = sum(1 for s in service_manager.service_status.values() if s.status == "error")

    # Calculate aggregate performance metrics
    all_wake_times = []
    all_sleep_times = []
    total_errors = 0

    for metrics in service_manager.performance_metrics.values():
        all_wake_times.extend(metrics.wake_times)
        all_sleep_times.extend(metrics.sleep_times)
        total_errors += metrics.error_count

    return {
        "service_counts": {
            "total": total_services,
            "running": running_count,
            "sleeping": sleeping_count,
            "stopped": stopped_count,
            "error": error_count,
        },
        "performance_stats": {
            "wake_times": {
                "count": len(all_wake_times),
                "avg_ms": sum(all_wake_times) / len(all_wake_times) if all_wake_times else 0,
                "min_ms": min(all_wake_times) if all_wake_times else 0,
                "max_ms": max(all_wake_times) if all_wake_times else 0,
                "p95_ms": sorted(all_wake_times)[int(len(all_wake_times) * 0.95)] if all_wake_times and len(all_wake_times) > 20 else 0,
            },
            "sleep_times": {
                "count": len(all_sleep_times),
                "avg_ms": sum(all_sleep_times) / len(all_sleep_times) if all_sleep_times else 0,
                "min_ms": min(all_sleep_times) if all_sleep_times else 0,
                "max_ms": max(all_sleep_times) if all_sleep_times else 0,
            },
        },
        "total_errors": total_errors,
        "global_settings": service_manager.global_sleep_settings.dict() if service_manager.global_sleep_settings else None,
    }


@app.get("/settings/sleep")
async def get_sleep_settings():
    """Get global sleep settings."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    return service_manager.global_sleep_settings.dict() if service_manager.global_sleep_settings else {}


@app.put("/settings/sleep")
async def update_sleep_settings(settings: dict):
    """Update global sleep settings."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    try:
        service_manager.global_sleep_settings = GlobalSleepSettings(**settings.get("sleep_settings", {}))
        logger.info("Updated global sleep settings")
        return {"message": "Sleep settings updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid settings: {str(e)}")


@app.get("/services/predictions")
async def get_wake_predictions():
    """Get wake predictions for all sleeping services."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    candidates = service_manager.get_pre_warm_candidates()

    return {
        "predictions": [
            {
                "service_name": service_name,
                "wake_probability": probability,
                "recommendation": "pre_warm" if probability > 0.7 else "monitor"
            }
            for service_name, probability in candidates
        ],
        "timestamp": datetime.datetime.now().isoformat()
    }


@app.post("/services/apply-predictions")
async def apply_wake_predictions():
    """Apply wake predictions to pre-warm likely services."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    await service_manager.apply_wake_predictions()
    return {"message": "Wake predictions applied successfully"}


# Phase 4: Enhanced Monitoring and Alerting API Endpoints
@app.get("/services/{service_name}/state-transitions")
async def get_service_state_transitions(service_name: str):
    """Get detailed state transition history for a service."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    if service_name not in service_manager.performance_metrics:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    metrics = service_manager.performance_metrics[service_name]

    return {
        "service_name": service_name,
        "transition_history": metrics.transition_history,
        "state_durations": metrics.state_durations,
        "recent_transitions": list(metrics.state_transitions)[-50:],  # Last 50 transitions
        "efficiency_metrics": metrics.get_state_efficiency_metrics(),
        "total_transitions": len(metrics.state_transitions),
        "timestamp": time.time()
    }


@app.get("/services/{service_name}/alerts")
async def get_service_alerts(service_name: str):
    """Get alerts for a specific service."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    alerts = service_manager.get_service_alerts(service_name)

    return {
        "service_name": service_name,
        "alerts": alerts,
        "alert_count": len(alerts),
        "timestamp": time.time()
    }


@app.get("/system/alerts")
async def get_system_alerts():
    """Get all system alerts across all services."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    return service_manager.get_all_system_alerts()


@app.get("/system/health")
async def get_system_health():
    """Get comprehensive system health summary."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    return service_manager.get_system_health_summary()


@app.get("/system/efficiency")
async def get_system_efficiency_metrics():
    """Get system-wide efficiency metrics."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    # Calculate aggregate efficiency metrics
    total_services = len(service_manager.services)
    total_efficiency = 0.0
    service_efficiencies = {}

    for service_name, metrics in service_manager.performance_metrics.items():
        efficiency = metrics.get_state_efficiency_metrics()
        service_efficiencies[service_name] = efficiency

        # Weight efficiency by service importance (running services weighted higher)
        status = service_manager.service_status.get(service_name)
        weight = 1.0
        if status and status.status == "running":
            weight = 2.0

        total_efficiency += efficiency.get('running_efficiency', 0) * weight

    # Calculate system-wide averages
    avg_efficiency = total_efficiency / max(total_services * 2, 1)  # Normalize by max weight

    return {
        "system_efficiency_score": round(avg_efficiency * 100, 1),
        "service_count": total_services,
        "service_efficiencies": service_efficiencies,
        "efficiency_breakdown": {
            "avg_running_efficiency": round(
                sum(s.get('running_efficiency', 0) for s in service_efficiencies.values()) / max(total_services, 1) * 100, 1
            ),
            "avg_sleep_efficiency": round(
                sum(s.get('sleep_efficiency', 0) for s in service_efficiencies.values()) / max(total_services, 1) * 100, 1
            ),
            "avg_error_rate": round(
                sum(s.get('error_rate', 0) for s in service_efficiencies.values()) / max(total_services, 1) * 100, 1
            )
        },
        "timestamp": time.time()
    }


@app.get("/monitoring/dashboard")
async def get_monitoring_dashboard():
    """Get comprehensive monitoring dashboard data."""
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not initialized")

    # Combine all monitoring data
    health_summary = service_manager.get_system_health_summary()
    system_alerts = service_manager.get_all_system_alerts()
    efficiency_metrics = service_manager.get_system_efficiency_metrics()

    return {
        "health": health_summary,
        "alerts": system_alerts,
        "efficiency": efficiency_metrics,
        "resources": service_manager.resource_monitor.get_system_resources(),
        "timestamp": time.time(),
        "dashboard_version": "1.0"
    }


def handle_signal(signum, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal", signal=signum)
    if service_manager:
        asyncio.create_task(service_manager.shutdown())
    sys.exit(0)


if __name__ == "__main__":
    import uvicorn

    # Setup signal handlers
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    # Run the application
    settings = Settings.from_env()
    uvicorn.run(
        "service_manager:app",
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level,
        reload=False
    )
