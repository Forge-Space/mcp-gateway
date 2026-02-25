"""Tests for observability health monitoring functionality."""

from __future__ import annotations

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
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestComponentHealth:
    """Test ComponentHealth dataclass."""

    def test_component_health_creation(self) -> None:
        comp = ComponentHealth(
            name="gateway",
            status=HealthStatus.HEALTHY,
            message="OK",
            latency_ms=50.0,
            metadata={"tool_count": 5},
        )
        assert comp.name == "gateway"
        assert comp.status == HealthStatus.HEALTHY
        assert comp.message == "OK"
        assert comp.latency_ms == 50.0
        assert comp.metadata == {"tool_count": 5}

    def test_component_health_defaults(self) -> None:
        comp = ComponentHealth(name="test", status=HealthStatus.HEALTHY)
        assert comp.message is None
        assert comp.latency_ms is None
        assert comp.metadata is None


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass."""

    def test_result_creation(self) -> None:
        components = [
            ComponentHealth(name="gateway", status=HealthStatus.HEALTHY, message="OK"),
            ComponentHealth(name="config", status=HealthStatus.HEALTHY, message="OK"),
        ]
        result = HealthCheckResult(status=HealthStatus.HEALTHY, components=components, timestamp=1234567890.0)
        assert result.status == HealthStatus.HEALTHY
        assert len(result.components) == 2
        assert result.version == "1.0.0"

    def test_result_to_dict(self) -> None:
        components = [
            ComponentHealth(
                name="gateway",
                status=HealthStatus.HEALTHY,
                message="OK",
                latency_ms=50.0,
                metadata={"tool_count": 5},
            )
        ]
        result = HealthCheckResult(status=HealthStatus.HEALTHY, components=components, timestamp=1234567890.0)
        d = result.to_dict()
        assert d["status"] == "healthy"
        assert d["timestamp"] == 1234567890.0
        assert d["version"] == "1.0.0"
        assert len(d["components"]) == 1
        assert d["components"][0]["name"] == "gateway"
        assert d["components"][0]["status"] == "healthy"
        assert d["components"][0]["latency_ms"] == 50.0


class TestHealthCheck:
    """Test HealthCheck coordinator."""

    def test_initialization_with_config(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://localhost:4444", jwt="test-token")
        hc = HealthCheck(config=config)
        assert hc.config.url == "http://localhost:4444"
        assert hc.config.jwt == "test-token"

    def test_initialization_default_config(self) -> None:
        hc = HealthCheck()
        assert hc.config is not None

    def test_check_gateway_connection_success(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://localhost:4444", jwt="test-token")
        hc = HealthCheck(config=config)

        with patch("tool_router.observability.health.HTTPGatewayClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_tools.return_value = [{"name": "tool1"}, {"name": "tool2"}]
            mock_client_cls.return_value = mock_client

            result = hc.check_gateway_connection()

            assert isinstance(result, ComponentHealth)
            assert result.status == HealthStatus.HEALTHY
            assert result.name == "gateway"
            assert result.metadata["tool_count"] == 2

    def test_check_gateway_connection_no_tools(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://localhost:4444", jwt="test-token")
        hc = HealthCheck(config=config)

        with patch("tool_router.observability.health.HTTPGatewayClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_tools.return_value = []
            mock_client_cls.return_value = mock_client

            result = hc.check_gateway_connection()

            assert result.status == HealthStatus.DEGRADED
            assert "no tools" in result.message.lower()

    def test_check_gateway_connection_value_error(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://localhost:4444", jwt="test-token")
        hc = HealthCheck(config=config)

        with patch("tool_router.observability.health.HTTPGatewayClient") as mock_client_cls:
            mock_client_cls.side_effect = ValueError("Bad config")

            result = hc.check_gateway_connection()

            assert result.status == HealthStatus.UNHEALTHY
            assert "Bad config" in result.message

    def test_check_gateway_connection_os_error(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://localhost:4444", jwt="test-token")
        hc = HealthCheck(config=config)

        with patch("tool_router.observability.health.HTTPGatewayClient") as mock_client_cls:
            mock_client_cls.side_effect = OSError("Connection refused")

            result = hc.check_gateway_connection()

            assert result.status == HealthStatus.UNHEALTHY
            assert "Connection refused" in result.message

    def test_check_configuration_valid(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://localhost:4444", jwt="test-token")
        hc = HealthCheck(config=config)

        result = hc.check_configuration()

        assert result.status == HealthStatus.HEALTHY
        assert result.name == "configuration"

    def test_check_configuration_no_url(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="", jwt="test-token")
        hc = HealthCheck(config=config)

        result = hc.check_configuration()

        assert result.status == HealthStatus.UNHEALTHY
        assert "URL" in result.message

    def test_check_configuration_no_jwt(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://localhost:4444", jwt="")
        hc = HealthCheck(config=config)

        result = hc.check_configuration()

        assert result.status == HealthStatus.UNHEALTHY
        assert "JWT" in result.message

    def test_check_all_healthy(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://localhost:4444", jwt="test-token")
        hc = HealthCheck(config=config)

        with (
            patch.object(hc, "check_configuration") as mock_config,
            patch.object(hc, "check_gateway_connection") as mock_gw,
        ):
            mock_config.return_value = ComponentHealth(name="configuration", status=HealthStatus.HEALTHY, message="OK")
            mock_gw.return_value = ComponentHealth(name="gateway", status=HealthStatus.HEALTHY, message="OK")

            result = hc.check_all()

            assert isinstance(result, HealthCheckResult)
            assert result.status == HealthStatus.HEALTHY
            assert len(result.components) == 2

    def test_check_all_degraded(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://localhost:4444", jwt="test-token")
        hc = HealthCheck(config=config)

        with (
            patch.object(hc, "check_configuration") as mock_config,
            patch.object(hc, "check_gateway_connection") as mock_gw,
        ):
            mock_config.return_value = ComponentHealth(name="configuration", status=HealthStatus.HEALTHY, message="OK")
            mock_gw.return_value = ComponentHealth(name="gateway", status=HealthStatus.DEGRADED, message="No tools")

            result = hc.check_all()

            assert result.status == HealthStatus.DEGRADED

    def test_check_all_unhealthy(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://localhost:4444", jwt="test-token")
        hc = HealthCheck(config=config)

        with (
            patch.object(hc, "check_configuration") as mock_config,
            patch.object(hc, "check_gateway_connection") as mock_gw,
        ):
            mock_config.return_value = ComponentHealth(
                name="configuration", status=HealthStatus.UNHEALTHY, message="Bad"
            )
            mock_gw.return_value = ComponentHealth(name="gateway", status=HealthStatus.HEALTHY, message="OK")

            result = hc.check_all()

            assert result.status == HealthStatus.UNHEALTHY

    def test_check_readiness_healthy(self) -> None:
        hc = HealthCheck()
        with patch.object(hc, "check_all") as mock_all:
            mock_all.return_value = HealthCheckResult(status=HealthStatus.HEALTHY, components=[], timestamp=0.0)
            assert hc.check_readiness() is True

    def test_check_readiness_unhealthy(self) -> None:
        hc = HealthCheck()
        with patch.object(hc, "check_all") as mock_all:
            mock_all.return_value = HealthCheckResult(status=HealthStatus.UNHEALTHY, components=[], timestamp=0.0)
            assert hc.check_readiness() is False

    def test_check_liveness_healthy(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://localhost:4444", jwt="test-token")
        hc = HealthCheck(config=config)
        assert hc.check_liveness() is True

    def test_check_liveness_no_jwt(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://localhost:4444", jwt="")
        hc = HealthCheck(config=config)
        assert hc.check_liveness() is False
