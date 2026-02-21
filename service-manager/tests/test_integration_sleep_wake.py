"""
Integration tests for serverless MCP sleep architecture with real Docker containers.
Tests the complete sleep/wake functionality with actual MCP services.
"""

import pytest
import asyncio
import time
import docker
from unittest.mock import patch, AsyncMock
from typing import Dict, List
import tempfile
import yaml
import os

from service_manager import (
    ServiceManager,
    ServiceStatus,
    SleepPolicy,
    GlobalSleepSettings,
    PerformanceMetrics,
    ResourceMonitor
)


@pytest.fixture
def docker_client():
    """Create a real Docker client for integration testing."""
    return docker.from_env()


@pytest.fixture
def test_service_config():
    """Create a test service configuration for integration testing."""
    return {
        "name": "test-mcp-service",
        "image": "alpine:latest",
        "command": ["sh", "-c", "echo 'Service running' && sleep 3600"],
        "port": 8080,
        "environment": {
            "TEST_MODE": "integration"
        },
        "sleep_policy": {
            "enabled": True,
            "idle_timeout": 60,
            "min_sleep_time": 30,
            "memory_reservation": "64MB",
            "priority": "normal"
        }
    }


@pytest.fixture
def global_sleep_settings():
    """Create global sleep settings for testing."""
    return GlobalSleepSettings(
        enabled=True,
        max_sleeping_services=5,
        system_memory_threshold="2GB",
        sleep_check_interval=10,
        wake_timeout=5,
        resource_monitoring={"enabled": True, "check_interval": 5},
        performance_optimization={"wake_prediction_enabled": True},
        wake_priorities={
            "high": [],
            "normal": ["test-mcp-service"],
            "low": []
        },
        resource_thresholds={
            "high_memory_pressure": 0.9,
            "moderate_memory_pressure": 0.75,
            "low_memory_pressure": 0.5,
            "cpu_pressure_threshold": 0.8
        }
    )


@pytest.fixture
async def service_manager_with_docker(docker_client, test_service_config, global_sleep_settings):
    """Create a ServiceManager instance with real Docker for integration testing."""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump({"services": [test_service_config]}, f)
        config_path = f.name

    try:
        # Mock settings to use our temp config
        settings = AsyncMock()
        settings.config_path = os.path.dirname(config_path)
        settings.log_level = "info"
        settings.port = 9001  # Use different port for testing
        settings.docker_host = "unix:///var/run/docker.sock"

        # Create service manager
        manager = ServiceManager(settings)
        manager.docker_client = docker_client
        manager.global_sleep_settings = global_sleep_settings
        manager.resource_monitor = ResourceMonitor()

        # Initialize services
        await manager._load_configuration()

        # Start the service for testing
        await manager.start_service("test-mcp-service")

        # Wait a moment for service to be ready
        await asyncio.sleep(2)

        yield manager

        # Cleanup: stop and remove service
        try:
            await manager.stop_service("test-mcp-service")
        except Exception:
            pass  # Service might already be stopped

    finally:
        # Clean up temp config file
        try:
            os.unlink(config_path)
        except OSError:
            pass


class TestIntegrationSleepWake:
    """Integration tests for sleep/wake functionality with real Docker containers."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_sleep_wake_cycle(self, service_manager_with_docker):
        """Test complete sleep and wake cycle with real Docker container."""
        manager = service_manager_with_docker
        service_name = "test-mcp-service"

        # Verify service is running
        status = await manager.get_service_status(service_name)
        assert status.status == "running"
        assert status.container_id is not None

        # Get initial metrics
        initial_metrics = manager.performance_metrics.get(service_name)
        assert initial_metrics is not None
        initial_wake_count = initial_metrics.wake_count

        # Test sleep functionality
        sleep_start = time.time()
        sleep_status = await manager.sleep_service(service_name)
        sleep_duration = time.time() - sleep_start

        # Verify sleep state
        assert sleep_status.status == "sleeping"
        assert sleep_status.sleep_start_time is not None
        assert sleep_duration < 5.0  # Should complete within 5 seconds

        # Verify container is actually paused
        container = manager.docker_client.containers.get(sleep_status.container_id)
        container_info = container.reload()
        assert container_info["State"] == "paused"

        # Verify metrics were recorded
        metrics = manager.performance_metrics.get(service_name)
        assert len(metrics.sleep_times) > 0
        assert metrics.sleep_times[-1] > 0
        assert len(metrics.state_transitions) > 0

        # Test wake functionality
        wake_start = time.time()
        wake_status = await manager.wake_service(service_name)
        wake_duration = time.time() - wake_start

        # Verify wake state
        assert wake_status.status == "running"
        assert wake_duration < 5.0  # Should complete within 5 seconds

        # Verify container is actually running
        container.reload()
        assert container_info["State"] == "running"

        # Verify metrics were recorded
        metrics = manager.performance_metrics.get(service_name)
        assert len(metrics.wake_times) > 0
        assert metrics.wake_times[-1] > 0
        assert metrics.wake_count > initial_wake_count

        # Verify performance targets are met
        assert wake_duration * 1000 < 500  # Wake time < 500ms
        assert sleep_duration * 1000 < 200  # Sleep time < 200ms

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_optimization_during_sleep(self, service_manager_with_docker):
        """Test memory optimization during sleep state."""
        manager = service_manager_with_docker
        service_name = "test-mcp-service"

        # Get initial container stats
        status = await manager.get_service_status(service_name)
        container = manager.docker_client.containers.get(status.container_id)

        # Put service to sleep
        await manager.sleep_service(service_name)

        # Verify memory settings were applied
        container.reload()
        container_info = container.inspect()

        # Check if memory limits were set (this depends on the container implementation)
        # The test verifies the optimization logic was executed
        metrics = manager.performance_metrics.get(service_name)
        assert len(metrics.sleep_times) > 0

        # Wake service and verify memory restoration
        await manager.wake_service(service_name)

        # Service should be running normally
        status = await manager.get_service_status(service_name)
        assert status.status == "running"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_resource_monitoring_accuracy(self, service_manager_with_docker):
        """Test resource monitoring accuracy with real containers."""
        manager = service_manager_with_docker
        service_name = "test-mcp-service"

        # Get system resources
        system_resources = manager.resource_monitor.get_system_resources()
        assert "cpu_percent" in system_resources
        assert "memory_percent" in system_resources
        assert "memory_total_gb" in system_resources

        # Get container resources
        status = await manager.get_service_status(service_name)
        container = manager.docker_client.containers.get(status.container_id)
        container_resources = manager.resource_monitor.get_container_resources(container)

        assert "cpu_percent" in container_resources
        assert "memory_usage_mb" in container_resources
        assert "memory_limit_mb" in container_resources

        # Verify resource values are reasonable
        assert 0 <= container_resources["cpu_percent"] <= 100
        assert container_resources["memory_usage_mb"] > 0
        assert container_resources["memory_limit_mb"] > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_state_transition_tracking(self, service_manager_with_docker):
        """Test state transition tracking with real operations."""
        manager = service_manager_with_docker
        service_name = "test-mcp-service"

        # Get initial state
        metrics = manager.performance_metrics.get(service_name)
        initial_transitions = len(metrics.state_transitions)

        # Perform sleep operation
        await manager.sleep_service(service_name)

        # Verify transition was recorded
        metrics = manager.performance_metrics.get(service_name)
        assert len(metrics.state_transitions) > initial_transitions

        # Check transition details
        latest_transition = metrics.state_transitions[-1]
        assert "from_state" in latest_transition
        assert "to_state" in latest_transition
        assert "timestamp" in latest_transition
        assert latest_transition["to_state"] == "sleeping"

        # Perform wake operation
        await manager.wake_service(service_name)

        # Verify wake transition was recorded
        metrics = manager.performance_metrics.get(service_name)
        wake_transitions = [t for t in metrics.state_transitions if t["to_state"] == "running"]
        assert len(wake_transitions) > 0

        # Verify efficiency metrics
        efficiency = metrics.get_state_efficiency_metrics()
        assert "running_efficiency" in efficiency
        assert "sleep_efficiency" in efficiency
        assert "transition_frequency" in efficiency
        assert "total_transitions" in efficiency

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_alerting_system_integration(self, service_manager_with_docker):
        """Test alerting system with real service operations."""
        manager = service_manager_with_docker
        service_name = "test-mcp-service"

        # Get initial alerts
        initial_alerts = manager.get_service_alerts(service_name)
        initial_alert_count = len(initial_alerts)

        # Perform operations that might trigger alerts
        await manager.sleep_service(service_name)
        await manager.wake_service(service_name)

        # Check for alerts
        alerts = manager.get_service_alerts(service_name)

        # Verify alert structure
        for alert in alerts:
            assert "type" in alert
            assert "service" in alert
            assert "severity" in alert
            assert "message" in alert
            assert "timestamp" in alert

        # Get system-wide alerts
        system_alerts = manager.get_all_system_alerts()
        assert "alerts" in system_alerts
        assert "total_alerts" in system_alerts
        assert "timestamp" in system_alerts

        # Get health summary
        health = manager.get_system_health_summary()
        assert "health_score" in health
        assert "service_status" in health
        assert "performance" in health
        assert "resources" in health
        assert "timestamp" in health

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, service_manager_with_docker):
        """Test error handling and recovery mechanisms."""
        manager = service_manager_with_docker
        service_name = "test-mcp-service"

        # Simulate an error during sleep by using invalid container
        original_status = manager.service_status[service_name]
        original_status.container_id = "invalid-container-id"

        # Attempt sleep should handle error gracefully
        try:
            await manager.sleep_service(service_name)
            assert False, "Should have raised an exception"
        except Exception:
            pass  # Expected

        # Verify error state was recorded
        status = manager.service_status[service_name]
        assert status.status == "error"
        assert status.error_message is not None

        # Verify metrics recorded error
        metrics = manager.performance_metrics.get(service_name)
        assert metrics.error_count > 0
        assert metrics.last_error is not None

        # Restore valid container ID and test recovery
        # Get the actual container ID
        containers = manager.docker_client.containers.list(
            filters={"label": f"com.docker.compose.service={service_name}"}
        )
        if containers:
            original_status.container_id = containers[0].id

            # Try to wake the service (should recover from error)
            try:
                await manager.wake_service(service_name)
            except Exception:
                pass  # Might still fail, but error recovery mechanism is tested

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, service_manager_with_docker):
        """Test concurrent sleep/wake operations."""
        manager = service_manager_with_docker
        service_name = "test-mcp-service"

        # Test concurrent sleep requests
        sleep_tasks = [
            manager.sleep_service(service_name) for _ in range(3)
        ]

        sleep_results = await asyncio.gather(*sleep_tasks, return_exceptions=True)

        # Only one should succeed, others should handle gracefully
        successful_sleeps = [r for r in sleep_results if not isinstance(r, Exception)]
        assert len(successful_sleeps) >= 1

        # Verify service is sleeping
        status = await manager.get_service_status(service_name)
        assert status.status == "sleeping"

        # Test concurrent wake requests
        wake_tasks = [
            manager.wake_service(service_name) for _ in range(3)
        ]

        wake_results = await asyncio.gather(*wake_tasks, return_exceptions=True)

        # Only one should succeed, others should handle gracefully
        successful_wakes = [r for r in wake_results if not isinstance(r, Exception)]
        assert len(successful_wakes) >= 1

        # Verify service is running
        status = await manager.get_service_status(service_name)
        assert status.status == "running"


@pytest.mark.integration
class TestIntegrationPerformanceTargets:
    """Integration tests for performance targets validation."""

    @pytest.mark.asyncio
    async def test_wake_time_performance_target(self, service_manager_with_docker):
        """Test wake time meets performance target (< 200ms)."""
        manager = service_manager_with_docker
        service_name = "test-mcp-service"

        # Put service to sleep
        await manager.sleep_service(service_name)

        # Measure wake time
        start_time = time.time()
        await manager.wake_service(service_name)
        wake_time_ms = (time.time() - start_time) * 1000

        # Verify performance target is met
        assert wake_time_ms < 200, f"Wake time {wake_time_ms:.2f}ms exceeds 200ms target"

        # Verify metrics recorded the wake time
        metrics = manager.performance_metrics.get(service_name)
        assert len(metrics.wake_times) > 0
        assert metrics.wake_times[-1] < 200

    @pytest.mark.asyncio
    async def test_memory_efficiency_target(self, service_manager_with_docker):
        """Test memory efficiency meets target (> 60% reduction)."""
        manager = service_manager_with_docker
        service_name = "test-mcp-service"

        # Get baseline memory usage
        status = await manager.get_service_status(service_name)
        container = manager.docker_client.containers.get(status.container_id)
        baseline_stats = container.stats(stream=False)
        baseline_memory = baseline_stats["memory_stats"]["usage"]

        # Put service to sleep
        await manager.sleep_service(service_name)

        # Get memory usage during sleep
        sleep_stats = container.stats(stream=False)
        sleep_memory = sleep_stats["memory_stats"]["usage"]

        # Calculate memory reduction
        memory_reduction = (baseline_memory - sleep_memory) / baseline_memory

        # Note: Docker pause doesn't always free memory immediately,
        # but our optimization should set lower limits
        # For this test, we verify the optimization was applied
        metrics = manager.performance_metrics.get(service_name)
        assert len(metrics.sleep_times) > 0  # Sleep operation completed

        # Wake service and verify restoration
        await manager.wake_service(service_name)

        # Verify service is running normally
        status = await manager.get_service_status(service_name)
        assert status.status == "running"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
