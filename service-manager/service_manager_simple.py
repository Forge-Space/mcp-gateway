"""
Forge MCP Gateway Service Manager - Simplified Version

Basic service management without Docker dependencies for testing purposes.
"""

import asyncio
import signal
import sys
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

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
    command: list[str]
    port: int
    environment: dict[str, str] = {}
    volumes: dict[str, str] = {}
    resources: dict[str, Any] = {}
    auto_start: bool = False
    health_check: dict[str, Any] | None = None
    sleep_policy: dict[str, Any] | None = None


class SleepPolicy(BaseModel):
    """Sleep policy configuration for serverless-like behavior."""

    enabled: bool = True
    idle_timeout: int = 300  # 5 minutes
    min_sleep_time: int = 60  # Don't sleep if used recently
    memory_reservation: str = "128MB"  # Reduced memory in sleep
    priority: str = "normal"  # Wake priority: low, normal, high


class ServiceStatus(BaseModel):
    """Service status information."""

    name: str
    status: str  # running, stopped, starting, stopping, error, sleeping, waking
    container_id: str | None = None
    port: int | None = None
    last_accessed: str | None = None
    resource_usage: dict[str, float] = {}
    error_message: str | None = None
    sleep_start_time: float | None = None
    wake_count: int = 0
    total_sleep_time: float = 0.0
    # Enhanced metrics for high-efficiency Docker standards
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_limit: float = 0.0
    cpu_limit: float = 0.0
    wake_time_ms: float | None = None
    sleep_efficiency: float = 0.0  # Memory reduction percentage
    state_transitions: int = 0
    uptime_seconds: float = 0.0
    last_state_change: float | None = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for a service."""

    service_name: str
    wake_times: deque  # Recent wake times in milliseconds
    sleep_times: deque  # Recent sleep times in milliseconds
    resource_usage: deque  # Recent resource usage snapshots
    error_count: int = 0
    last_error: str | None = None
    total_requests: int = 0
    uptime_percentage: float = 0.0


class ServiceManager:
    """Simplified service manager without Docker dependencies."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.services: dict[str, ServiceConfig] = {}
        self.service_status: dict[str, ServiceStatus] = {}
        self.sleep_policies: dict[str, SleepPolicy] = {}
        self.performance_metrics: dict[str, PerformanceMetrics] = {}
        self._shutdown_event = asyncio.Event()
        self._auto_sleep_task: asyncio.Task | None = None

    async def initialize(self):
        """Initialize the service manager."""
        try:
            logger.info("Service manager initialized successfully (simplified mode)")
        except Exception as e:
            logger.error(f"Failed to initialize service manager: {e}")
            raise

        # Load configuration
        await self._load_configuration()

        logger.info(
            "Service manager initialized", config_path=self.settings.config_path, services_loaded=len(self.services)
        )

    async def _load_configuration(self):
        """Load service configurations from files."""
        config_path = Path(self.settings.config_path)

        # Load services configuration
        services_file = config_path / "services.yml"
        if services_file.exists():
            import yaml

            with open(services_file) as f:
                services_data = yaml.safe_load(f)
                # Handle the services wrapper
                services_dict = services_data.get("services", services_data)
                for name, config in services_dict.items():
                    # Ensure required fields are present and convert types
                    service_config = {
                        "name": name,
                        "image": config.get("image", "forge-mcp-gateway-translate:latest"),
                        "command": config.get("command", ["python3", "-m", "forge.translate"]),
                        "port": config.get("port", 8000),
                        "environment": {str(k): str(v) for k, v in config.get("environment", {}).items()},
                        "volumes": config.get("volumes", {}),
                        "resources": config.get("resources", {}),
                        "auto_start": config.get("auto_start", False),
                        "health_check": config.get("health_check"),
                        "sleep_policy": config.get("sleep_policy"),
                    }
                    self.services[name] = ServiceConfig(**service_config)
                    self.service_status[name] = ServiceStatus(name=name, status="stopped")
                    logger.info("Loaded service configuration", service=name)

        # Load sleep policies
        policies_file = config_path / "sleep_settings.yml"
        if policies_file.exists():
            import yaml

            with open(policies_file) as f:
                policies_data = yaml.safe_load(f)
                # Handle sleep_settings wrapper - this contains global settings, not individual service policies
                sleep_settings = policies_data.get("sleep_settings", policies_data)
                # For simplified version, we'll create a default policy
                default_policy = SleepPolicy(
                    enabled=sleep_settings.get("enabled", True),
                    idle_timeout=sleep_settings.get("sleep_check_interval", 300),
                    min_sleep_time=60,
                    memory_reservation="128MB",
                    priority="normal",
                )
                # Apply default policy to all services
                for service_name in self.services:
                    self.sleep_policies[service_name] = default_policy
                logger.info("Loaded default sleep policy for all services")

    async def start_service(self, service_name: str) -> ServiceStatus:
        """Start a service."""
        if service_name not in self.services:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

        current_status = self.service_status[service_name]
        service_config = self.services[service_name]
        metrics = self.performance_metrics.get(service_name)

        if current_status.status == "running":
            logger.info("Service already running", service=service_name)
            return current_status

        try:
            logger.info("Starting service", service=service_name)
            start_time = time.time()

            # Record state transition
            from_state = current_status.status
            current_status.status = "starting"
            current_status.last_state_change = start_time

            if metrics:
                metrics.record_state_transition(from_state, "starting", start_time)

            # Simulate service start (in real implementation, this would start Docker containers)
            await asyncio.sleep(2)  # Simulate startup time

            current_status.status = "running"
            current_status.last_accessed = str(start_time)
            current_status.port = service_config.port

            # Record transition from starting to running
            if metrics:
                metrics.record_state_transition("starting", "running", start_time + 2)
                metrics.total_requests += 1

            logger.info("Service started successfully", service=service_name, port=service_config.port)
            return current_status

        except Exception as e:
            from_state = current_status.status
            current_status.status = "error"
            current_status.error_message = str(e)
            if metrics:
                metrics.record_state_transition(from_state, "error")
                metrics.error_count += 1
                metrics.last_error = str(e)
            logger.error("Failed to start service", service=service_name, error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to start service {service_name}: {e!s}")

    async def stop_service(self, service_name: str) -> ServiceStatus:
        """Stop a service."""
        if service_name not in self.service_status:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

        current_status = self.service_status[service_name]
        metrics = self.performance_metrics.get(service_name)

        if current_status.status == "stopped":
            logger.info("Service already stopped", service=service_name)
            return current_status

        try:
            logger.info("Stopping service", service=service_name)
            stop_time = time.time()

            # Record state transition
            from_state = current_status.status
            current_status.status = "stopping"
            current_status.last_state_change = stop_time

            if metrics:
                metrics.record_state_transition(from_state, "stopping", stop_time)

            # Simulate service stop (in real implementation, this would stop Docker containers)
            await asyncio.sleep(1)  # Simulate stop time

            current_status.status = "stopped"
            current_status.container_id = None
            current_status.port = None

            # Record transition from stopping to stopped
            if metrics:
                metrics.record_state_transition("stopping", "stopped", stop_time + 1)

            logger.info("Service stopped successfully", service=service_name)
            return current_status

        except Exception as e:
            from_state = current_status.status
            current_status.status = "error"
            current_status.error_message = str(e)
            if metrics:
                metrics.record_state_transition(from_state, "error")
                metrics.error_count += 1
                metrics.last_error = str(e)
            logger.error("Failed to stop service", service=service_name, error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to stop service {service_name}: {e!s}")

    async def sleep_service(self, service_name: str) -> ServiceStatus:
        """Put a service to sleep."""
        if service_name not in self.service_status:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

        current_status = self.service_status[service_name]
        metrics = self.performance_metrics.get(service_name)
        sleep_policy = self.sleep_policies.get(service_name)

        if not sleep_policy or not sleep_policy.enabled:
            logger.info("Sleep not enabled for service", service=service_name)
            return current_status

        if current_status.status != "running":
            logger.info("Service not running, cannot sleep", service=service_name)
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

            # Simulate sleep (in real implementation, this would pause Docker containers)
            await asyncio.sleep(1)  # Simulate sleep time

            # Record sleep time
            sleep_duration = time.time() - sleep_start_time
            if metrics:
                metrics.sleep_times.append(sleep_duration * 1000)  # Convert to milliseconds
                metrics.total_sleep_duration += sleep_duration

            logger.info("Service slept successfully", service=service_name, sleep_duration_ms=sleep_duration * 1000)
            return current_status

        except Exception as e:
            from_state = current_status.status
            current_status.status = "error"
            if metrics:
                metrics.record_state_transition(from_state, "error")
                metrics.error_count += 1
                metrics.last_error = str(e)
            logger.error("Failed to sleep service", service=service_name, error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to sleep service {service_name}: {e!s}")

    async def wake_service(self, service_name: str) -> ServiceStatus:
        """Wake a service from sleep state."""
        if service_name not in self.service_status:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

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

            # Simulate wake (in real implementation, this would unpause Docker containers)
            await asyncio.sleep(1)  # Simulate wake time

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

            logger.info(
                "Service woke successfully",
                service=service_name,
                wake_time_ms=wake_duration * 1000,
                total_sleep_time=current_status.total_sleep_time,
            )

            return current_status

        except Exception as e:
            from_state = current_status.status
            current_status.status = "error"
            current_status.error_message = str(e)
            if metrics:
                metrics.record_state_transition(from_state, "error")
                metrics.error_count += 1
                metrics.last_error = str(e)
            logger.error("Failed to wake service", service=service_name, error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to wake service {service_name}: {e!s}")

    async def get_service_status(self, service_name: str) -> ServiceStatus:
        """Get the status of a specific service."""
        if service_name not in self.service_status:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

        return self.service_status[service_name]

    async def list_services(self) -> list[ServiceStatus]:
        """List all services and their status."""
        services = []
        for service_name in self.service_status:
            status = await self.get_service_status(service_name)
            services.append(status)
        return services

    async def get_performance_metrics(self) -> dict[str, dict[str, float]]:
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
                "uptime_seconds": status.uptime_seconds,
            }

            # Add wake time if available
            if status.wake_time_ms:
                metrics[service_name]["wake_time_ms"] = status.wake_time_ms

        return metrics

    async def get_system_metrics(self) -> dict[str, Any]:
        """Get system-wide performance metrics."""
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
            "running_ratio": running_count / max(total_services, 1) * 100,
        }

        return efficiency_metrics

    async def health_check(self) -> dict[str, str]:
        """Perform health check."""
        try:
            # Count running services
            running_count = sum(1 for status in self.service_status.values() if status.status == "running")

            return {
                "status": "healthy",
                "services_running": str(running_count),
                "services_total": str(len(self.services)),
            }
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {"status": "unhealthy", "error": str(e)}

    async def shutdown(self):
        """Shutdown the service manager."""
        logger.info("Shutting down service manager")

        # Cancel background tasks
        if self._auto_sleep_task and not self._auto_sleep_task.done():
            self._auto_sleep_task.cancel()
            try:
                await self._auto_sleep_task
            except asyncio.CancelledError:
                pass

        # Stop all running services
        for service_name in list(self.service_status.keys()):
            try:
                await self.stop_service(service_name)
            except Exception as e:
                logger.warning("Failed to stop service during shutdown", service=service_name, error=str(e))

        logger.info("Service manager shutdown complete")


# FastAPI application
app = FastAPI(
    title="Forge MCP Gateway Service Manager (Simplified)",
    description="Dynamic service management for MCP servers (simplified version)",
    version="1.0.0",
)

# Global service manager instance
service_manager: ServiceManager | None = None


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
        "service_manager_simple:app", host="0.0.0.0", port=settings.port, log_level=settings.log_level, reload=False
    )
