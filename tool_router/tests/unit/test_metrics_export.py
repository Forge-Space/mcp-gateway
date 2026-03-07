"""Tests for Prometheus metrics export endpoint."""

from __future__ import annotations

import pytest

from tool_router.api.metrics_export import MetricsCollector


@pytest.fixture
def collector():
    return MetricsCollector()


class TestMetricsCollector:
    def test_initial_state(self, collector):
        output = collector.format_prometheus()
        assert "gateway_uptime_seconds" in output
        assert "gateway_requests_total 0" in output
        assert "gateway_errors_total 0" in output

    def test_record_request(self, collector):
        collector.record_request("GET", "/health", 200, 0.05)
        output = collector.format_prometheus()
        assert "gateway_requests_total 1" in output
        assert 'route="GET_/health"' in output

    def test_record_error(self, collector):
        collector.record_request("POST", "/rpc", 500, 0.1)
        output = collector.format_prometheus()
        assert "gateway_errors_total 1" in output
        assert 'route="POST_/rpc"' in output

    def test_duration_tracking(self, collector):
        collector.record_request("GET", "/health", 200, 0.05)
        collector.record_request("GET", "/health", 200, 0.15)
        output = collector.format_prometheus()
        assert "gateway_request_duration_seconds_sum" in output
        assert "gateway_request_duration_seconds_count" in output

    def test_multiple_routes(self, collector):
        collector.record_request("GET", "/health", 200, 0.01)
        collector.record_request("POST", "/rpc", 200, 0.5)
        collector.record_request("POST", "/rpc", 400, 0.1)
        output = collector.format_prometheus()
        assert "gateway_requests_total 3" in output
        assert "gateway_errors_total 1" in output

    def test_prometheus_format(self, collector):
        output = collector.format_prometheus()
        assert output.startswith("# HELP")
        assert output.strip().endswith("# EOF")
        for line in output.strip().split("\n"):
            if line and not line.startswith("#"):
                parts = line.split(" ")
                assert len(parts) >= 2


class TestMetricsEndpointIntegration:
    def test_metrics_endpoint_registered(self):
        """Verify endpoint is importable and registered."""
        from tool_router.api.metrics_export import router

        routes = [r.path for r in router.routes]
        assert "/metrics" in routes
