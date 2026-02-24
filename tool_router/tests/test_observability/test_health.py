"""Tests for observability health monitoring functionality."""

from __future__ import annotations

from unittest.mock import Mock, patch

from tool_router.observability.health import (
    ComponentHealth,
    HealthCheck,
    HealthCheckResult,
    HealthStatus,
)


class TestHealthCheck:
    """Test cases for HealthCheck functionality."""

    def test_health_check_initialization(self) -> None:
        """Test HealthCheck initialization."""
        health_check = HealthCheck()

        assert health_check is not None
        assert hasattr(health_check, "check_gateway_connection")
        assert hasattr(health_check, "check_configuration")
        assert hasattr(health_check, "check_all")

    def test_check_gateway_connection_success(self) -> None:
        """Test successful gateway connection check."""
        health_check = HealthCheck()

        # Mock successful connection
        with patch("tool_router.observability.health.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_get.return_value = mock_response

            result = health_check.check_gateway_connection()

            assert isinstance(result, HealthCheckResult)
            assert result.status == HealthStatus.HEALTHY
            assert result.component == "gateway_connection"
            assert result.message == "Gateway connection successful"

    def test_check_gateway_connection_failure(self) -> None:
        """Test failed gateway connection check."""
        health_check = HealthCheck()

        # Mock failed connection
        with patch("tool_router.observability.health.requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection failed")

            result = health_check.check_gateway_connection()

            assert isinstance(result, HealthCheckResult)
            assert result.status == HealthStatus.UNHEALTHY
            assert result.component == "gateway_connection"
            assert "Connection failed" in result.message

    def test_check_configuration_valid(self) -> None:
        """Test valid configuration check."""
        health_check = HealthCheck()

        # Mock valid configuration
        with patch(
            "tool_router.observability.health.ToolRouterConfig.load_from_environment"
        ) as mock_load:
            mock_config = Mock()
            mock_config.is_valid.return_value = True
            mock_load.return_value = mock_config

            result = health_check.check_configuration()

            assert isinstance(result, HealthCheckResult)
            assert result.status == HealthStatus.HEALTHY
            assert result.component == "configuration"
            assert result.message == "Configuration is valid"

    def test_check_configuration_invalid(self) -> None:
        """Test invalid configuration check."""
        health_check = HealthCheck()

        # Mock invalid configuration
        with patch(
            "tool_router.observability.health.ToolRouterConfig.load_from_environment"
        ) as mock_load:
            mock_config = Mock()
            mock_config.is_valid.return_value = False
            mock_config.validation_errors = ["Missing API key", "Invalid port"]
            mock_load.return_value = mock_config

            result = health_check.check_configuration()

            assert isinstance(result, HealthCheckResult)
            assert result.status == HealthStatus.UNHEALTHY
            assert result.component == "configuration"
            assert "Missing API key" in result.message

    def test_check_all_healthy(self) -> None:
        """Test overall health check when all components are healthy."""
        health_check = HealthCheck()

        # Mock all checks as healthy
        with (
            patch.object(health_check, "check_gateway_connection") as mock_gateway,
            patch.object(health_check, "check_configuration") as mock_config,
        ):
            mock_gateway.return_value = HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="gateway_connection",
                message="Gateway connection successful",
            )
            mock_config.return_value = HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="configuration",
                message="Configuration is valid",
            )

            result = health_check.check_all()

            assert isinstance(result, ComponentHealth)
            assert result.status == HealthStatus.HEALTHY
            assert len(result.components) == 2
            assert all(
                comp.status == HealthStatus.HEALTHY for comp in result.components
            )

    def test_check_all_degraded(self) -> None:
        """Test overall health check when some components are degraded."""
        health_check = HealthCheck()

        # Mock mixed health status
        with (
            patch.object(health_check, "check_gateway_connection") as mock_gateway,
            patch.object(health_check, "check_configuration") as mock_config,
        ):
            mock_gateway.return_value = HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="gateway_connection",
                message="Gateway connection successful",
            )
            mock_config.return_value = HealthCheckResult(
                status=HealthStatus.DEGRADED,
                component="configuration",
                message="Configuration has warnings",
            )

            result = health_check.check_all()

            assert isinstance(result, ComponentHealth)
            assert result.status == HealthStatus.DEGRADED
            assert len(result.components) == 2

    def test_check_readiness(self) -> None:
        """Test readiness check."""
        health_check = HealthCheck()

        # Mock readiness check
        with patch.object(health_check, "check_all") as mock_check_all:
            mock_component_health = Mock(spec=ComponentHealth)
            mock_component_health.status = HealthStatus.HEALTHY
            mock_component_health.is_ready.return_value = True
            mock_check_all.return_value = mock_component_health

            result = health_check.check_readiness()

            assert result is True

    def test_check_liveness(self) -> None:
        """Test liveness check."""
        health_check = HealthCheck()

        # Mock liveness check
        with patch.object(health_check, "check_all") as mock_check_all:
            mock_component_health = Mock(spec=ComponentHealth)
            mock_component_health.status = HealthStatus.HEALTHY
            mock_component_health.is_alive.return_value = True
            mock_check_all.return_value = mock_component_health

            result = health_check.check_liveness()

            assert result is True

    def test_health_check_result_to_dict(self) -> None:
        """Test HealthCheckResult serialization."""
        result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            component="test_component",
            message="Test message",
            details={"key": "value"},
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["status"] == "healthy"
        assert result_dict["component"] == "test_component"
        assert result_dict["message"] == "Test message"
        assert result_dict["details"]["key"] == "value"

    def test_component_health_properties(self) -> None:
        """Test ComponentHealth properties."""
        components = [
            HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="gateway",
                message="Gateway healthy",
            ),
            HealthCheckResult(
                status=HealthStatus.DEGRADED,
                component="database",
                message="Database slow",
            ),
        ]

        component_health = ComponentHealth(
            status=HealthStatus.DEGRADED, components=components
        )

        assert component_health.status == HealthStatus.DEGRADED
        assert len(component_health.components) == 2
        assert component_health.is_ready() is True  # Degraded but ready
        assert component_health.is_alive() is True  # Degraded but alive

    def test_health_status_values(self) -> None:
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_component_health_all_healthy(self) -> None:
        """Test ComponentHealth with all healthy components."""
        components = [
            HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="gateway",
                message="Gateway healthy",
            ),
            HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="database",
                message="Database healthy",
            ),
        ]

        component_health = ComponentHealth(
            status=HealthStatus.HEALTHY, components=components
        )

        assert component_health.status == HealthStatus.HEALTHY
        assert component_health.is_ready() is True
        assert component_health.is_alive() is True

    def test_component_health_unhealthy(self) -> None:
        """Test ComponentHealth with unhealthy components."""
        components = [
            HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="gateway",
                message="Gateway healthy",
            ),
            HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                component="database",
                message="Database down",
            ),
        ]

        component_health = ComponentHealth(
            status=HealthStatus.UNHEALTHY, components=components
        )

        assert component_health.status == HealthStatus.UNHEALTHY
        assert component_health.is_ready() is False
        assert component_health.is_alive() is False

    def test_health_check_with_timeout(self) -> None:
        """Test health check with timeout handling."""
        health_check = HealthCheck()

        # Mock timeout
        with patch("tool_router.observability.health.requests.get") as mock_get:
            mock_get.side_effect = TimeoutError("Request timed out")

            result = health_check.check_gateway_connection()

            assert isinstance(result, HealthCheckResult)
            assert result.status == HealthStatus.UNHEALTHY
            assert "timed out" in result.message.lower()

    def test_health_check_metrics_collection(self) -> None:
        """Test health check metrics collection."""
        health_check = HealthCheck()

        # Mock metrics collection
        with patch.object(health_check, "check_gateway_connection") as mock_gateway:
            mock_result = HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="gateway_connection",
                message="Gateway connection successful",
                metrics={"response_time_ms": 150, "status_code": 200},
            )
            mock_gateway.return_value = mock_result

            result = health_check.check_gateway_connection()

            assert result.metrics is not None
            assert result.metrics["response_time_ms"] == 150
            assert result.metrics["status_code"] == 200

    def test_health_check_component_dependency(self) -> None:
        """Test health check with component dependencies."""
        health_check = HealthCheck()

        # Mock dependent component checks
        with (
            patch.object(health_check, "check_gateway_connection") as mock_gateway,
            patch.object(health_check, "check_configuration") as mock_config,
        ):
            # Gateway healthy, config unhealthy
            mock_gateway.return_value = HealthCheckResult(
                status=HealthStatus.HEALTHY,
                component="gateway_connection",
                message="Gateway connection successful",
            )
            mock_config.return_value = HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                component="configuration",
                message="Configuration invalid",
            )

            result = health_check.check_all()

            assert result.status == HealthStatus.UNHEALTHY
            assert len(result.components) == 2
            assert result.components[0].status == HealthStatus.HEALTHY
            assert result.components[1].status == HealthStatus.UNHEALTHY
