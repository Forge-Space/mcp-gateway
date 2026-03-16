"""Unit tests for tool_router/cloud/provider.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tool_router.cloud.provider import CloudProvider, CloudProviderMetrics, CloudProviderStatus
from tool_router.core.config import GatewayConfig


def _make_config() -> GatewayConfig:
    return GatewayConfig(url="http://localhost:4444", jwt="test-jwt")


def _make_provider(**kwargs) -> CloudProvider:
    defaults = {
        "name": "aws-us-east-1",
        "cloud_type": "aws",
        "region": "us-east-1",
        "config": _make_config(),
    }
    defaults.update(kwargs)
    with patch("tool_router.cloud.provider.HTTPGatewayClient"), patch("tool_router.cloud.provider.CircuitBreaker"):
        return CloudProvider(**defaults)


# ---------------------------------------------------------------------------
# CloudProviderMetrics
# ---------------------------------------------------------------------------


class TestCloudProviderMetrics:
    def test_initial_values(self):
        m = CloudProviderMetrics()
        assert m.total_requests == 0
        assert m.total_failures == 0
        assert m.consecutive_failures == 0
        assert m.consecutive_successes == 0

    def test_error_rate_zero_requests(self):
        m = CloudProviderMetrics()
        assert m.error_rate == 0.0

    def test_error_rate_with_failures(self):
        m = CloudProviderMetrics(total_requests=10, total_failures=3)
        assert abs(m.error_rate - 0.3) < 1e-9

    def test_avg_latency_no_successful(self):
        m = CloudProviderMetrics(total_requests=2, total_failures=2)
        assert m.avg_latency_ms == 0.0

    def test_avg_latency_with_data(self):
        m = CloudProviderMetrics(total_requests=2, total_failures=0, total_latency_ms=300.0)
        assert m.avg_latency_ms == 150.0

    def test_record_success(self):
        m = CloudProviderMetrics()
        m.consecutive_failures = 2
        m.record_success(100.0)
        assert m.total_requests == 1
        assert m.total_failures == 0
        assert m.total_latency_ms == 100.0
        assert m.consecutive_failures == 0
        assert m.consecutive_successes == 1
        assert m.last_success_time > 0

    def test_record_failure(self):
        m = CloudProviderMetrics()
        m.consecutive_successes = 3
        m.record_failure()
        assert m.total_requests == 1
        assert m.total_failures == 1
        assert m.consecutive_failures == 1
        assert m.consecutive_successes == 0
        assert m.last_failure_time > 0

    def test_multiple_records(self):
        m = CloudProviderMetrics()
        m.record_success(50.0)
        m.record_success(100.0)
        m.record_failure()
        assert m.total_requests == 3
        assert m.total_failures == 1
        assert m.consecutive_failures == 1
        assert m.consecutive_successes == 0


# ---------------------------------------------------------------------------
# CloudProviderStatus logic
# ---------------------------------------------------------------------------


class TestCloudProviderStatus:
    def test_disabled_is_unhealthy(self):
        p = _make_provider(enabled=False)
        assert p.status == CloudProviderStatus.UNHEALTHY

    def test_zero_requests_is_unknown(self):
        p = _make_provider()
        assert p.status == CloudProviderStatus.UNKNOWN

    def test_three_consecutive_failures_is_unhealthy(self):
        p = _make_provider()
        p._metrics.total_requests = 3
        p._metrics.total_failures = 3
        p._metrics.consecutive_failures = 3
        assert p.status == CloudProviderStatus.UNHEALTHY

    def test_high_error_rate_is_unhealthy(self):
        p = _make_provider()
        p._metrics.total_requests = 10
        p._metrics.total_failures = 6
        assert p.status == CloudProviderStatus.UNHEALTHY

    def test_moderate_error_rate_is_degraded(self):
        p = _make_provider()
        p._metrics.total_requests = 10
        p._metrics.total_failures = 2
        assert p.status == CloudProviderStatus.DEGRADED

    def test_one_consecutive_failure_is_degraded(self):
        p = _make_provider()
        p._metrics.total_requests = 5
        p._metrics.consecutive_failures = 1
        assert p.status == CloudProviderStatus.DEGRADED

    def test_healthy_with_good_metrics(self):
        p = _make_provider()
        p._metrics.total_requests = 10
        p._metrics.total_failures = 0
        p._metrics.consecutive_failures = 0
        assert p.status == CloudProviderStatus.HEALTHY


# ---------------------------------------------------------------------------
# CloudProvider methods
# ---------------------------------------------------------------------------


class TestCloudProviderMethods:
    def test_metrics_property(self):
        p = _make_provider()
        assert p.metrics is p._metrics

    def test_get_tools_success(self):
        p = _make_provider()
        p._client.get_tools = MagicMock(return_value=[{"name": "tool1"}])
        tools = p.get_tools()
        assert tools == [{"name": "tool1"}]
        assert p._metrics.total_requests == 1
        assert p._metrics.total_failures == 0

    def test_get_tools_records_failure_on_valueerror(self):
        p = _make_provider()
        p._client.get_tools = MagicMock(side_effect=ValueError("bad"))
        with pytest.raises(ValueError, match="bad"):
            p.get_tools()
        assert p._metrics.total_failures == 1

    def test_get_tools_records_failure_on_connectionerror(self):
        p = _make_provider()
        p._client.get_tools = MagicMock(side_effect=ConnectionError("down"))
        with pytest.raises(ConnectionError):
            p.get_tools()
        assert p._metrics.total_failures == 1

    def test_call_tool_success(self):
        p = _make_provider()
        p._client.call_tool = MagicMock(return_value='{"result": "ok"}')
        result = p.call_tool("my_tool", {"arg": "val"})
        assert result == '{"result": "ok"}'
        assert p._metrics.total_requests == 1
        assert p._metrics.total_failures == 0

    def test_call_tool_records_failure(self):
        p = _make_provider()
        p._client.call_tool = MagicMock(side_effect=ConnectionError("no conn"))
        with pytest.raises(ConnectionError):
            p.call_tool("tool", {})
        assert p._metrics.total_failures == 1

    def test_health_check_structure(self):
        p = _make_provider()
        hc = p.health_check()
        assert hc["name"] == "aws-us-east-1"
        assert hc["cloud_type"] == "aws"
        assert hc["region"] == "us-east-1"
        assert hc["enabled"] is True
        assert hc["status"] == "unknown"
        assert "metrics" in hc
        assert "total_requests" in hc["metrics"]
        assert "error_rate" in hc["metrics"]
        assert "avg_latency_ms" in hc["metrics"]

    def test_to_dict_structure(self):
        p = _make_provider()
        d = p.to_dict()
        assert d["name"] == "aws-us-east-1"
        assert d["cloud_type"] == "aws"
        assert d["region"] == "us-east-1"
        assert d["url"] == "http://localhost:4444"
        assert d["enabled"] is True
        assert "status" in d
        assert "tags" in d

    def test_provider_tags(self):
        p = _make_provider(tags={"env": "prod", "team": "platform"})
        d = p.to_dict()
        assert d["tags"] == {"env": "prod", "team": "platform"}

    def test_provider_priority_and_weight(self):
        p = _make_provider(priority=2, weight=0.5)
        assert p.priority == 2
        assert p.weight == 0.5
