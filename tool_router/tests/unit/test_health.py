"""Unit tests for observability health module."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

from tool_router.observability.health import (
    ComponentHealth,
    HealthCheck,
    HealthCheckResult,
    HealthStatus,
)


class TestHealthStatus:
    """Test HealthStatus enum."""

    def test_health_status_values(self) -> None:
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"


class TestComponentHealth:
    """Test ComponentHealth dataclass."""

    def test_component_health_creation_minimal(self) -> None:
        """Test ComponentHealth creation with minimal fields."""
        component = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
        )
        assert component.name == "test"
        assert component.status == HealthStatus.HEALTHY
        assert component.message is None
        assert component.latency_ms is None
        assert component.metadata is None

    def test_component_health_creation_all_fields(self) -> None:
        """Test ComponentHealth creation with all fields."""
        component = ComponentHealth(
            name="test",
            status=HealthStatus.DEGRADED,
            message="Test message",
            latency_ms=150.5,
            metadata={"key": "value"},
        )
        assert component.name == "test"
        assert component.status == HealthStatus.DEGRADED
        assert component.message == "Test message"
        assert component.latency_ms == 150.5
        assert component.metadata == {"key": "value"}


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass."""

    def test_health_check_result_creation(self) -> None:
        """Test HealthCheckResult creation."""
        components = [
            ComponentHealth("test1", HealthStatus.HEALTHY),
            ComponentHealth("test2", HealthStatus.DEGRADED),
        ]
        result = HealthCheckResult(
            status=HealthStatus.DEGRADED,
            components=components,
            timestamp=time.time(),
            version="2.0.0",
        )
        assert result.status == HealthStatus.DEGRADED
        assert len(result.components) == 2
        assert result.version == "2.0.0"
        assert isinstance(result.timestamp, float)

    def test_to_dict_conversion(self) -> None:
        """Test HealthCheckResult to_dict conversion."""
        components = [
            ComponentHealth(
                name="gateway",
                status=HealthStatus.HEALTHY,
                message="OK",
                latency_ms=100.0,
                metadata={"tool_count": 5},
            ),
            ComponentHealth(
                name="config",
                status=HealthStatus.HEALTHY,
                message="Valid",
                latency_ms=None,
                metadata=None,
            ),
        ]
        result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            components=components,
            timestamp=1234567890.0,
            version="1.0.0",
        )

        expected = {
            "status": "healthy",
            "timestamp": 1234567890.0,
            "version": "1.0.0",
            "components": [
                {
                    "name": "gateway",
                    "status": "healthy",
                    "message": "OK",
                    "latency_ms": 100.0,
                    "metadata": {"tool_count": 5},
                },
                {
                    "name": "config",
                    "status": "healthy",
                    "message": "Valid",
                    "latency_ms": None,
                    "metadata": None,
                },
            ],
        }

        assert result.to_dict() == expected


class TestHealthCheck:
    """Test HealthCheck class."""

    def test_initialization_with_config(self) -> None:
        """Test HealthCheck initialization with provided config."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token")
        health_check = HealthCheck(config)
        assert health_check.config == config

    def test_initialization_without_config(self) -> None:
        """Test HealthCheck initialization without config (loads from env)."""
        with patch("tool_router.observability.health.GatewayConfig.load_from_environment") as mock_load:
            mock_config = MagicMock()
            mock_config.url = "http://env.com"
            mock_config.jwt = "env-token"
            mock_load.return_value = mock_config

            health_check = HealthCheck()
            assert health_check.config == mock_config
            mock_load.assert_called_once()

    def test_initialization_config_load_failure(self) -> None:
        """Test HealthCheck initialization when config loading fails."""
        with patch("tool_router.observability.health.GatewayConfig.load_from_environment") as mock_load:
            mock_load.side_effect = ValueError("No config found")

            health_check = HealthCheck()
            assert health_check.config.url == "http://localhost:4444"
            assert health_check.config.jwt == ""

    def test_check_gateway_connection_success(self) -> None:
        """Test successful gateway connection check."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token")
        health_check = HealthCheck(config)

        with patch("tool_router.observability.health.HTTPGatewayClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.get_tools.return_value = [{"name": "tool1"}, {"name": "tool2"}]

            result = health_check.check_gateway_connection()

            assert result.name == "gateway"
            assert result.status == HealthStatus.HEALTHY
            assert result.message == "Gateway connection successful"
            assert result.latency_ms is not None
            assert result.latency_ms >= 0
            assert result.metadata == {"tool_count": 2}

    def test_check_gateway_connection_no_tools(self) -> None:
        """Test gateway connection when no tools available."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token")
        health_check = HealthCheck(config)

        with patch("tool_router.observability.health.HTTPGatewayClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.get_tools.return_value = []

            result = health_check.check_gateway_connection()

            assert result.name == "gateway"
            assert result.status == HealthStatus.DEGRADED
            assert result.message == "Gateway reachable but no tools available"
            assert result.metadata == {"tool_count": 0}

    def test_check_gateway_connection_value_error(self) -> None:
        """Test gateway connection with ValueError."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token")
        health_check = HealthCheck(config)

        with patch("tool_router.observability.health.HTTPGatewayClient") as mock_client_class:
            mock_client_class.side_effect = ValueError("Invalid token")

            result = health_check.check_gateway_connection()

            assert result.name == "gateway"
            assert result.status == HealthStatus.UNHEALTHY
            assert "Gateway error: Invalid token" in result.message
            assert result.latency_ms is not None

    def test_check_gateway_connection_os_error(self) -> None:
        """Test gateway connection with OSError."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token")
        health_check = HealthCheck(config)

        with patch("tool_router.observability.health.HTTPGatewayClient") as mock_client_class:
            mock_client_class.side_effect = OSError("Connection refused")

            result = health_check.check_gateway_connection()

            assert result.name == "gateway"
            assert result.status == HealthStatus.UNHEALTHY
            assert "Unexpected error: OSError: Connection refused" in result.message
            assert result.latency_ms is not None

    def test_check_gateway_connection_runtime_error(self) -> None:
        """Test gateway connection with RuntimeError."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token")
        health_check = HealthCheck(config)

        with patch("tool_router.observability.health.HTTPGatewayClient") as mock_client_class:
            mock_client_class.side_effect = RuntimeError("Service unavailable")

            result = health_check.check_gateway_connection()

            assert result.name == "gateway"
            assert result.status == HealthStatus.UNHEALTHY
            assert "Unexpected error: RuntimeError: Service unavailable" in result.message
            assert result.latency_ms is not None

    def test_check_configuration_valid(self) -> None:
        """Test configuration check with valid config."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token", timeout_ms=5000, max_retries=3)
        health_check = HealthCheck(config)

        result = health_check.check_configuration()

        assert result.name == "configuration"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Configuration valid"
        assert result.metadata == {
            "url": "http://test.com",
            "timeout_ms": 5000,
            "max_retries": 3,
        }

    def test_check_configuration_missing_url(self) -> None:
        """Test configuration check with missing URL."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="", jwt="test-token")
        health_check = HealthCheck(config)

        result = health_check.check_configuration()

        assert result.name == "configuration"
        assert result.status == HealthStatus.UNHEALTHY
        assert result.message == "Gateway URL not configured"

    def test_check_configuration_missing_jwt(self) -> None:
        """Test configuration check with missing JWT."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="")
        health_check = HealthCheck(config)

        result = health_check.check_configuration()

        assert result.name == "configuration"
        assert result.status == HealthStatus.UNHEALTHY
        assert result.message == "JWT token not configured"

    def test_check_configuration_timeout_too_low(self) -> None:
        """Test configuration check with timeout too low."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token", timeout_ms=500)
        health_check = HealthCheck(config)

        result = health_check.check_configuration()

        assert result.name == "configuration"
        assert result.status == HealthStatus.DEGRADED
        assert "Timeout 500ms outside recommended range" in result.message
        assert result.metadata == {
            "timeout_ms": 500,
            "max_retries": 3,  # default value
        }

    def test_check_configuration_timeout_too_high(self) -> None:
        """Test configuration check with timeout too high."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token", timeout_ms=500000)
        health_check = HealthCheck(config)

        result = health_check.check_configuration()

        assert result.name == "configuration"
        assert result.status == HealthStatus.DEGRADED
        assert "Timeout 500000ms outside recommended range" in result.message
        assert result.metadata == {
            "timeout_ms": 500000,
            "max_retries": 3,  # default value
        }

    def test_check_configuration_timeout_valid_range(self) -> None:
        """Test configuration check with timeout in valid range."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token", timeout_ms=10000)
        health_check = HealthCheck(config)

        result = health_check.check_configuration()

        assert result.name == "configuration"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Configuration valid"

    def test_check_configuration_attribute_error(self) -> None:
        """Test configuration check with AttributeError."""
        config = MagicMock()
        config.url = "http://test.com"
        config.jwt = "test-token"
        # Simulate missing timeout_ms attribute
        del config.timeout_ms

        health_check = HealthCheck(config)

        result = health_check.check_configuration()

        assert result.name == "configuration"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Configuration error:" in result.message

    def test_check_all_healthy(self) -> None:
        """Test check_all with all components healthy."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token", timeout_ms=5000)
        health_check = HealthCheck(config)

        with patch("tool_router.observability.health.HTTPGatewayClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.get_tools.return_value = [{"name": "tool1"}]

            result = health_check.check_all()

            assert result.status == HealthStatus.HEALTHY
            assert len(result.components) == 2
            assert result.timestamp is not None

    def test_check_all_degraded(self) -> None:
        """Test check_all with one component degraded."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token", timeout_ms=500)  # Too low
        health_check = HealthCheck(config)

        with patch("tool_router.observability.health.HTTPGatewayClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.get_tools.return_value = [{"name": "tool1"}]

            result = health_check.check_all()

            assert result.status == HealthStatus.DEGRADED
            assert len(result.components) == 2

    def test_check_all_unhealthy(self) -> None:
        """Test check_all with one component unhealthy."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="", jwt="test-token")  # Missing URL
        health_check = HealthCheck(config)

        result = health_check.check_all()

        assert result.status == HealthStatus.UNHEALTHY
        assert len(result.components) == 2

    def test_check_readiness_healthy(self) -> None:
        """Test check_readiness returns True for healthy service."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token", timeout_ms=5000)
        health_check = HealthCheck(config)

        with patch("tool_router.observability.health.HTTPGatewayClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.get_tools.return_value = [{"name": "tool1"}]

            result = health_check.check_readiness()
            assert result is True

    def test_check_readiness_degraded(self) -> None:
        """Test check_readiness returns True for degraded service."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token", timeout_ms=500)  # Too low
        health_check = HealthCheck(config)

        with patch("tool_router.observability.health.HTTPGatewayClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.get_tools.return_value = [{"name": "tool1"}]

            result = health_check.check_readiness()
            assert result is True  # Degraded is still ready

    def test_check_readiness_unhealthy(self) -> None:
        """Test check_readiness returns False for unhealthy service."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="", jwt="test-token")  # Missing URL
        health_check = HealthCheck(config)

        result = health_check.check_readiness()
        assert result is False

    def test_check_liveness_healthy(self) -> None:
        """Test check_liveness returns True for healthy config."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token", timeout_ms=5000)
        health_check = HealthCheck(config)

        result = health_check.check_liveness()
        assert result is True

    def test_check_liveness_degraded(self) -> None:
        """Test check_liveness returns True for degraded config."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://test.com", jwt="test-token", timeout_ms=500)  # Too low
        health_check = HealthCheck(config)

        result = health_check.check_liveness()
        assert result is True  # Degraded is still alive

    def test_check_liveness_unhealthy(self) -> None:
        """Test check_liveness returns False for unhealthy config."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="", jwt="test-token")  # Missing URL
        health_check = HealthCheck(config)

        result = health_check.check_liveness()
        assert result is False
