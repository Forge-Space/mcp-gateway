"""
Comprehensive tests for serverless MCP sleep/wake functionality.
"""

import asyncio
import time
from collections import deque
from unittest.mock import Mock, patch

import docker
import pytest
from service_manager import (
    GlobalSleepSettings,
    PerformanceMetrics,
    ResourceMonitor,
    ServiceManager,
    ServiceStatus,
    SleepPolicy,
)


@pytest.fixture
def mock_docker_client():
    """Create a mock Docker client."""
    client = Mock(spec=docker.DockerClient)
    return client


@pytest.fixture
def mock_container():
    """Create a mock Docker container."""
    container = Mock()
    container.pause = Mock()
    container.unpause = Mock()
    container.update = Mock()
    container.stats.return_value = {
        "cpu_stats": {
            "cpu_usage": {"total_usage": 1000000, "percpu_usage": [100000, 200000]},
            "system_cpu_usage": 2000000,
        },
        "precpu_stats": {"cpu_usage": {"total_usage": 800000}, "system_cpu_usage": 1800000},
        "memory_stats": {
            "usage": 134217728,  # 128MB
            "limit": 268435456,  # 256MB
        },
    }
    return container


@pytest.fixture
def service_manager(mock_docker_client):
    """Create a ServiceManager instance with mocked dependencies."""
    # Mock settings
    settings = Mock()
    settings.config_path = "test_config"

    # Create service manager
    manager = ServiceManager(settings)
    manager.docker_client = mock_docker_client

    # Setup test data
    manager.services = {
        "test-service": Mock(name="test-service", sleep_policy=None),
        "priority-service": Mock(name="priority-service", sleep_policy=None),
    }

    manager.service_status = {
        "test-service": ServiceStatus(name="test-service", status="running", container_id="container-123"),
        "priority-service": ServiceStatus(name="priority-service", status="running", container_id="container-456"),
    }

    manager.sleep_policies = {
        "test-service": SleepPolicy(enabled=True, idle_timeout=300, min_sleep_time=60, memory_reservation="128MB")
    }

    manager.global_sleep_settings = GlobalSleepSettings(
        enabled=True,
        max_sleeping_services=10,
        system_memory_threshold="4GB",
        sleep_check_interval=30,
        wake_timeout=10,
        resource_monitoring={"enabled": True, "check_interval": 60},
        performance_optimization={"wake_prediction_enabled": True},
        wake_priorities={"high": ["priority-service"], "normal": ["test-service"], "low": []},
        resource_thresholds={
            "high_memory_pressure": 0.9,
            "moderate_memory_pressure": 0.75,
            "low_memory_pressure": 0.5,
            "cpu_pressure_threshold": 0.8,
        },
    )

    manager.performance_metrics = {
        "test-service": PerformanceMetrics(
            service_name="test-service",
            wake_times=deque(maxlen=100),
            sleep_times=deque(maxlen=100),
            resource_usage=deque(maxlen=100),
        )
    }

    manager.resource_monitor = ResourceMonitor()
    manager._wake_queue = asyncio.Queue()
    manager._processing_wake = False

    return manager


class TestServiceSleep:
    """Test service sleep functionality."""

    @pytest.mark.asyncio
    async def test_sleep_service_success(self, service_manager, mock_container):
        """Test successful service sleep."""
        # Setup
        service_manager.docker_client.containers.get.return_value = mock_container

        # Mock system resources to be under pressure threshold
        with patch.object(service_manager.resource_monitor, "get_system_resources") as mock_resources:
            mock_resources.return_value = {
                "cpu_percent": 50.0,
                "memory_percent": 60.0,
                "memory_available_gb": 8.0,
                "memory_used_gb": 4.0,
                "memory_total_gb": 12.0,
            }

            # Execute
            result = await service_manager.sleep_service("test-service")

            # Verify
            assert result.status == "sleeping"
            assert result.sleep_start_time is not None
            mock_container.pause.assert_called_once()

            # Check memory optimization was applied
            mock_container.update.assert_called_once_with(
                mem_limit=134217728,  # 128MB in bytes
                mem_reservation=134217728,
            )

    @pytest.mark.asyncio
    async def test_sleep_service_disabled(self, service_manager):
        """Test sleep when disabled for service."""
        # Setup - disable sleep policy
        service_manager.sleep_policies["test-service"].enabled = False

        # Execute
        result = await service_manager.sleep_service("test-service")

        # Verify - service should remain running
        assert result.status == "running"

    @pytest.mark.asyncio
    async def test_sleep_service_not_running(self, service_manager):
        """Test sleep when service is not running."""
        # Setup - service is already sleeping
        service_manager.service_status["test-service"].status = "sleeping"

        # Execute
        result = await service_manager.sleep_service("test-service")

        # Verify - service should remain sleeping
        assert result.status == "sleeping"

    @pytest.mark.asyncio
    async def test_sleep_service_resource_pressure(self, service_manager):
        """Test sleep skipped due to resource pressure."""
        # Setup - mock high memory pressure
        with patch.object(service_manager.resource_monitor, "get_system_resources") as mock_resources:
            mock_resources.return_value = {
                "cpu_percent": 50.0,
                "memory_percent": 95.0,  # High memory pressure
                "memory_available_gb": 1.0,
                "memory_used_gb": 11.0,
                "memory_total_gb": 12.0,
            }

            # Execute
            result = await service_manager.sleep_service("test-service")

            # Verify - sleep should be skipped
            assert result.status == "running"

    @pytest.mark.asyncio
    async def test_sleep_service_min_sleep_time(self, service_manager):
        """Test sleep skipped due to recent access."""
        # Setup - service accessed recently
        service_manager.service_status["test-service"].last_accessed = str(time.time() - 30)  # 30 seconds ago

        # Execute
        result = await service_manager.sleep_service("test-service")

        # Verify - sleep should be skipped (min_sleep_time is 60 seconds)
        assert result.status == "running"

    @pytest.mark.asyncio
    async def test_sleep_service_error(self, service_manager, mock_container):
        """Test sleep error handling."""
        # Setup - mock container error
        mock_container.pause.side_effect = Exception("Docker error")
        service_manager.docker_client.containers.get.return_value = mock_container

        # Mock system resources
        with patch.object(service_manager.resource_monitor, "get_system_resources") as mock_resources:
            mock_resources.return_value = {
                "cpu_percent": 50.0,
                "memory_percent": 60.0,
                "memory_available_gb": 8.0,
                "memory_used_gb": 4.0,
                "memory_total_gb": 12.0,
            }

            # Execute & Verify
            with pytest.raises(Exception) as exc_info:
                await service_manager.sleep_service("test-service")

            assert "Failed to sleep service" in str(exc_info.value)
            assert service_manager.service_status["test-service"].status == "error"


class TestServiceWake:
    """Test service wake functionality."""

    @pytest.mark.asyncio
    async def test_wake_service_success(self, service_manager, mock_container):
        """Test successful service wake."""
        # Setup
        service_manager.service_status["test-service"].status = "sleeping"
        service_manager.service_status["test-service"].sleep_start_time = time.time() - 300  # 5 minutes ago
        service_manager.docker_client.containers.get.return_value = mock_container

        # Execute
        result = await service_manager.wake_service("test-service")

        # Verify
        assert result.status == "running"
        assert result.wake_count == 1
        assert result.sleep_start_time is None
        assert result.last_accessed is not None
        mock_container.unpause.assert_called_once()

        # Check memory settings were restored
        mock_container.update.assert_called_with(mem_limit=0, mem_reservation=0)

    @pytest.mark.asyncio
    async def test_wake_service_not_sleeping(self, service_manager):
        """Test wake when service is not sleeping."""
        # Setup - service is already running
        service_manager.service_status["test-service"].status = "running"

        # Execute
        result = await service_manager.wake_service("test-service")

        # Verify - service should remain running
        assert result.status == "running"

    @pytest.mark.asyncio
    async def test_wake_service_error(self, service_manager, mock_container):
        """Test wake error handling."""
        # Setup
        service_manager.service_status["test-service"].status = "sleeping"
        mock_container.unpause.side_effect = Exception("Docker error")
        service_manager.docker_client.containers.get.return_value = mock_container

        # Execute & Verify
        with pytest.raises(Exception) as exc_info:
            await service_manager.wake_service("test-service")

        assert "Failed to wake service" in str(exc_info.value)
        assert service_manager.service_status["test-service"].status == "error"


class TestResourceMonitoring:
    """Test resource monitoring functionality."""

    def test_get_system_resources(self, service_manager):
        """Test system resource monitoring."""
        with patch("psutil.cpu_percent", return_value=50.0), patch("psutil.virtual_memory") as mock_memory:
            mock_memory.return_value = Mock(
                percent=60.0,
                available=8589934592,  # 8GB
                used=4294967296,  # 4GB
                total=12884901888,  # 12GB
            )

            result = service_manager.resource_monitor.get_system_resources()

            assert result["cpu_percent"] == 50.0
            assert result["memory_percent"] == 60.0
            assert result["memory_available_gb"] == 8.0
            assert result["memory_used_gb"] == 4.0
            assert result["memory_total_gb"] == 12.0

    def test_get_container_resources(self, service_manager, mock_container):
        """Test container resource monitoring."""
        result = service_manager.resource_monitor.get_container_resources(mock_container)

        assert "cpu_percent" in result
        assert "memory_usage_mb" in result
        assert "memory_limit_mb" in result
        assert "memory_percent" in result
        assert result["memory_usage_mb"] == 128.0  # 128MB
        assert result["memory_limit_mb"] == 256.0  # 256MB


class TestWakePrediction:
    """Test wake prediction algorithms."""

    def test_predict_service_wake_need(self, service_manager):
        """Test wake need prediction."""
        # Setup - service with some usage
        metrics = service_manager.performance_metrics["test-service"]
        metrics.total_requests = 50
        metrics.wake_times.extend([100, 150, 200])  # Recent wake times

        result = service_manager.predict_service_wake_need("test-service")

        assert 0.0 <= result <= 1.0
        assert result > 0.5  # Should be moderately likely due to usage

    def test_predict_service_wake_need_unknown_service(self, service_manager):
        """Test prediction for unknown service."""
        result = service_manager.predict_service_wake_need("unknown-service")

        assert result == 0.5  # Default probability

    def test_get_pre_warm_candidates(self, service_manager):
        """Test getting pre-warm candidates."""
        # Setup - make one service sleeping
        service_manager.service_status["test-service"].status = "sleeping"

        candidates = service_manager.get_pre_warm_candidates()

        assert isinstance(candidates, list)
        assert len(candidates) >= 0
        for service_name, probability in candidates:
            assert isinstance(service_name, str)
            assert 0.0 <= probability <= 1.0

    @pytest.mark.asyncio
    async def test_apply_wake_predictions_disabled(self, service_manager):
        """Test applying predictions when disabled."""
        # Setup - disable predictions
        service_manager.global_sleep_settings.performance_optimization["wake_prediction_enabled"] = False

        # Execute - should return early
        await service_manager.apply_wake_predictions()

        # No assertions needed - just ensure no errors


class TestPriorityManagement:
    """Test priority-based wake ordering."""

    def test_get_service_priority(self, service_manager):
        """Test service priority retrieval."""
        # Test high priority service
        priority = service_manager._get_service_priority("priority-service")
        assert priority == 0  # High priority

        # Test normal priority service
        priority = service_manager._get_service_priority("test-service")
        assert priority == 1  # Normal priority

        # Test unknown service
        priority = service_manager._get_service_priority("unknown-service")
        assert priority == 2  # Low priority (default)

    def test_should_skip_sleep_due_to_pressure(self, service_manager):
        """Test sleep skipping due to resource pressure."""
        # Test normal resources
        resources = {"memory_percent": 60.0, "cpu_percent": 50.0}
        result = service_manager._should_skip_sleep_due_to_pressure(resources)
        assert result is False

        # Test high memory pressure
        resources = {"memory_percent": 95.0, "cpu_percent": 50.0}
        result = service_manager._should_skip_sleep_due_to_pressure(resources)
        assert result is True

        # Test high CPU pressure
        resources = {"memory_percent": 60.0, "cpu_percent": 85.0}
        result = service_manager._should_skip_sleep_due_to_pressure(resources)
        assert result is True


class TestAPIEndpoints:
    """Test API endpoints."""

    @pytest.mark.asyncio
    async def test_request_wake_endpoint(self, service_manager):
        """Test wake request API endpoint."""
        from fastapi.testclient import TestClient
        from service_manager import app

        # Setup
        app.dependency_overrides[lambda: service_manager] = lambda: service_manager
        client = TestClient(app)

        # Setup sleeping service
        service_manager.service_status["test-service"].status = "sleeping"

        # Execute
        response = client.post("/services/test-service/wake-request")

        # Verify
        assert response.status_code == 200
        assert "wake request queued" in response.json()["message"]

    def test_get_service_metrics_endpoint(self, service_manager):
        """Test service metrics API endpoint."""
        from fastapi.testclient import TestClient
        from service_manager import app

        # Setup
        app.dependency_overrides[lambda: service_manager] = lambda: service_manager
        client = TestClient(app)

        # Setup some metrics
        metrics = service_manager.performance_metrics["test-service"]
        metrics.wake_times.append(100)
        metrics.sleep_times.append(50)
        metrics.total_requests = 10

        # Execute
        response = client.get("/services/test-service/metrics")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["service_name"] == "test-service"
        assert "wake_time_stats" in data
        assert "sleep_time_stats" in data
        assert data["total_requests"] == 10


class TestMemoryOptimization:
    """Test memory optimization functionality."""

    def test_parse_memory_string(self, service_manager):
        """Test memory string parsing."""
        assert service_manager._parse_memory_string("128MB") == 128 * 1024 * 1024
        assert service_manager._parse_memory_string("1GB") == 1024 * 1024 * 1024
        assert service_manager._parse_memory_string("512KB") == 512 * 1024
        assert service_manager._parse_memory_string("1024") == 1024

    @pytest.mark.asyncio
    async def test_apply_memory_optimization(self, service_manager, mock_container):
        """Test memory optimization application."""
        await service_manager._apply_memory_optimization(mock_container, "128MB")

        mock_container.update.assert_called_once_with(
            mem_limit=134217728,  # 128MB in bytes
            mem_reservation=134217728,
        )

    @pytest.mark.asyncio
    async def test_restore_memory_settings(self, service_manager, mock_container):
        """Test memory settings restoration."""
        await service_manager._restore_memory_settings(mock_container)

        mock_container.update.assert_called_once_with(mem_limit=0, mem_reservation=0)


if __name__ == "__main__":
    pytest.main([__file__])
