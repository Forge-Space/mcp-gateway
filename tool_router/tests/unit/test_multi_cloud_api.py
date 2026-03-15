"""Tests for multi-cloud provider management API endpoints.

Covers:
  GET    /cloud/providers              — list providers (admin only)
  GET    /cloud/providers/{name}       — get provider with health metrics
  POST   /cloud/providers              — register new provider
  DELETE /cloud/providers/{name}       — remove provider
  PATCH  /cloud/providers/{name}/enabled — toggle enabled
  GET    /cloud/health                 — aggregated health summary
  PATCH  /cloud/strategy               — change routing strategy

Also covers:
  CloudProvider health metrics and status transitions
  MultiCloudRouter strategy selection
  MultiCloudConfig environment loading
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import tool_router.api.cloud as cloud_module
from tool_router.api.cloud import (
    router,
)
from tool_router.api.dependencies import get_security_context
from tool_router.cloud.provider import CloudProvider, CloudProviderMetrics, CloudProviderStatus
from tool_router.cloud.router import MultiCloudRouter, NoHealthyProviderError, RoutingStrategy
from tool_router.core.config import CloudProviderConfig, GatewayConfig, MultiCloudConfig
from tool_router.security.security_middleware import SecurityContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ctx(role: str) -> SecurityContext:
    return SecurityContext(
        user_id="u-test",
        session_id="s-test",
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-1",
        endpoint="/cloud/providers",
        authentication_method="jwt",
        user_role=role,
    )


def _make_app(role: str | None = "admin") -> FastAPI:
    """Build isolated test app with fresh router state."""
    app = FastAPI()
    app.include_router(router)

    # Fresh MultiCloudRouter per test
    fresh_router = MultiCloudRouter()
    cloud_module._multi_cloud_router = fresh_router

    if role is not None:
        ctx = _make_ctx(role)
        app.dependency_overrides[get_security_context] = lambda: ctx

    return app


def _make_provider(
    name: str = "aws-us-east",
    cloud_type: str = "aws",
    region: str = "us-east-1",
    priority: int = 0,
    enabled: bool = True,
) -> CloudProvider:
    """Create a CloudProvider with a mock HTTPGatewayClient."""
    cfg = GatewayConfig(url="http://fake-gateway:8080", jwt="test-jwt")
    provider = CloudProvider(
        name=name,
        cloud_type=cloud_type,
        region=region,
        config=cfg,
        priority=priority,
        enabled=enabled,
    )
    # Replace internal client with mock to avoid real HTTP calls
    provider._client = MagicMock()
    return provider


# ---------------------------------------------------------------------------
# GET /cloud/providers
# ---------------------------------------------------------------------------


class TestListCloudProviders:
    def test_empty_list(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.get("/cloud/providers")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["providers"] == []

    def test_lists_registered_providers(self) -> None:
        app = _make_app()
        cloud_module._multi_cloud_router.add_provider(_make_provider("aws-east"))
        cloud_module._multi_cloud_router.add_provider(_make_provider("azure-west", cloud_type="azure", region="westus"))
        with TestClient(app) as client:
            resp = client.get("/cloud/providers")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        names = {p["name"] for p in data["providers"]}
        assert names == {"aws-east", "azure-west"}

    def test_requires_admin(self) -> None:
        app = _make_app(role="user")
        with TestClient(app) as client:
            resp = client.get("/cloud/providers")
        assert resp.status_code == 403

    def test_unauthenticated_rejected(self) -> None:
        app = _make_app(role=None)
        with TestClient(app) as client:
            resp = client.get("/cloud/providers")
        assert resp.status_code in (401, 403, 422)

    def test_response_excludes_jwt(self) -> None:
        app = _make_app()
        cloud_module._multi_cloud_router.add_provider(_make_provider("aws-east"))
        with TestClient(app) as client:
            resp = client.get("/cloud/providers")
        provider = resp.json()["providers"][0]
        assert "jwt" not in provider


# ---------------------------------------------------------------------------
# GET /cloud/providers/{name}
# ---------------------------------------------------------------------------


class TestGetCloudProvider:
    def test_returns_provider_with_metrics(self) -> None:
        app = _make_app()
        cloud_module._multi_cloud_router.add_provider(_make_provider("aws-east"))
        with TestClient(app) as client:
            resp = client.get("/cloud/providers/aws-east")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "aws-east"
        assert "metrics" in data
        assert "status" in data

    def test_404_for_unknown_provider(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.get("/cloud/providers/nonexistent")
        assert resp.status_code == 404

    def test_requires_admin(self) -> None:
        app = _make_app(role="user")
        with TestClient(app) as client:
            resp = client.get("/cloud/providers/any")
        assert resp.status_code == 403

    def test_metrics_structure(self) -> None:
        app = _make_app()
        cloud_module._multi_cloud_router.add_provider(_make_provider("aws-east"))
        with TestClient(app) as client:
            resp = client.get("/cloud/providers/aws-east")
        metrics = resp.json()["metrics"]
        assert "total_requests" in metrics
        assert "error_rate" in metrics
        assert "avg_latency_ms" in metrics
        assert "consecutive_failures" in metrics


# ---------------------------------------------------------------------------
# POST /cloud/providers
# ---------------------------------------------------------------------------


class TestRegisterCloudProvider:
    def _payload(self, name: str = "new-provider", **kwargs) -> dict:
        return {
            "name": name,
            "cloud_type": "aws",
            "region": "us-east-1",
            "url": "http://gateway:8080",
            **kwargs,
        }

    def test_registers_provider(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.post("/cloud/providers", json=self._payload())
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "new-provider"
        assert data["cloud_type"] == "aws"
        assert data["region"] == "us-east-1"

    def test_409_on_duplicate(self) -> None:
        app = _make_app()
        cloud_module._multi_cloud_router.add_provider(_make_provider("existing"))
        with TestClient(app) as client:
            resp = client.post("/cloud/providers", json=self._payload("existing"))
        assert resp.status_code == 409

    def test_requires_admin(self) -> None:
        app = _make_app(role="user")
        with TestClient(app) as client:
            resp = client.post("/cloud/providers", json=self._payload())
        assert resp.status_code == 403

    def test_invalid_cloud_type_rejected(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.post("/cloud/providers", json=self._payload(cloud_type="oracle"))
        assert resp.status_code == 422

    def test_missing_url_rejected(self) -> None:
        app = _make_app()
        payload = {"name": "p", "cloud_type": "aws", "region": "us-east-1"}
        with TestClient(app) as client:
            resp = client.post("/cloud/providers", json=payload)
        assert resp.status_code == 422

    def test_custom_priority_and_weight(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.post("/cloud/providers", json=self._payload(priority=5, weight=2.5))
        assert resp.status_code == 201
        data = resp.json()
        assert data["priority"] == 5
        assert data["weight"] == 2.5

    def test_tags_stored(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.post("/cloud/providers", json=self._payload(tags={"env": "prod"}))
        assert resp.status_code == 201
        assert resp.json()["tags"] == {"env": "prod"}

    def test_provider_added_to_router(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            client.post("/cloud/providers", json=self._payload("new-one"))
        assert cloud_module._multi_cloud_router.get_provider("new-one") is not None


# ---------------------------------------------------------------------------
# DELETE /cloud/providers/{name}
# ---------------------------------------------------------------------------


class TestRemoveCloudProvider:
    def test_removes_provider(self) -> None:
        app = _make_app()
        cloud_module._multi_cloud_router.add_provider(_make_provider("to-remove"))
        with TestClient(app) as client:
            resp = client.delete("/cloud/providers/to-remove")
        assert resp.status_code == 204
        assert cloud_module._multi_cloud_router.get_provider("to-remove") is None

    def test_404_for_unknown(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.delete("/cloud/providers/ghost")
        assert resp.status_code == 404

    def test_requires_admin(self) -> None:
        app = _make_app(role="user")
        with TestClient(app) as client:
            resp = client.delete("/cloud/providers/any")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /cloud/providers/{name}/enabled
# ---------------------------------------------------------------------------


class TestToggleCloudProvider:
    def test_disable_provider(self) -> None:
        app = _make_app()
        cloud_module._multi_cloud_router.add_provider(_make_provider("aws-east", enabled=True))
        with TestClient(app) as client:
            resp = client.patch("/cloud/providers/aws-east/enabled", json={"enabled": False})
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False
        assert cloud_module._multi_cloud_router.get_provider("aws-east").enabled is False

    def test_enable_provider(self) -> None:
        app = _make_app()
        cloud_module._multi_cloud_router.add_provider(_make_provider("aws-east", enabled=False))
        with TestClient(app) as client:
            resp = client.patch("/cloud/providers/aws-east/enabled", json={"enabled": True})
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    def test_404_for_unknown(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.patch("/cloud/providers/ghost/enabled", json={"enabled": False})
        assert resp.status_code == 404

    def test_requires_admin(self) -> None:
        app = _make_app(role="user")
        with TestClient(app) as client:
            resp = client.patch("/cloud/providers/any/enabled", json={"enabled": False})
        assert resp.status_code == 403

    def test_missing_body_rejected(self) -> None:
        app = _make_app()
        cloud_module._multi_cloud_router.add_provider(_make_provider("aws-east"))
        with TestClient(app) as client:
            resp = client.patch("/cloud/providers/aws-east/enabled", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /cloud/health
# ---------------------------------------------------------------------------


class TestCloudHealth:
    def test_empty_health(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.get("/cloud/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_providers"] == 0
        assert data["overall"] == "unhealthy"

    def test_health_with_providers(self) -> None:
        app = _make_app()
        cloud_module._multi_cloud_router.add_provider(_make_provider("aws-east"))
        with TestClient(app) as client:
            resp = client.get("/cloud/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_providers"] == 1
        assert "strategy" in data
        assert "providers" in data

    def test_requires_admin(self) -> None:
        app = _make_app(role="user")
        with TestClient(app) as client:
            resp = client.get("/cloud/health")
        assert resp.status_code == 403

    def test_health_counts(self) -> None:
        app = _make_app()
        cloud_module._multi_cloud_router.add_provider(_make_provider("p1"))
        cloud_module._multi_cloud_router.add_provider(_make_provider("p2"))
        with TestClient(app) as client:
            resp = client.get("/cloud/health")
        data = resp.json()
        assert data["total_providers"] == 2
        # Both are UNKNOWN (no requests yet) — counted as neither healthy nor unhealthy
        assert data["healthy"] == 0
        assert data["unhealthy"] == 0


# ---------------------------------------------------------------------------
# PATCH /cloud/strategy
# ---------------------------------------------------------------------------


class TestUpdateStrategy:
    def test_change_to_round_robin(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.patch("/cloud/strategy", json={"strategy": "round_robin"})
        assert resp.status_code == 200
        assert resp.json()["strategy"] == "round_robin"

    def test_change_to_latency_weighted(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.patch("/cloud/strategy", json={"strategy": "latency_weighted"})
        assert resp.status_code == 200

    def test_change_to_random(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.patch("/cloud/strategy", json={"strategy": "random"})
        assert resp.status_code == 200

    def test_change_to_failover(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.patch("/cloud/strategy", json={"strategy": "failover"})
        assert resp.status_code == 200

    def test_invalid_strategy_rejected(self) -> None:
        app = _make_app()
        with TestClient(app) as client:
            resp = client.patch("/cloud/strategy", json={"strategy": "magic"})
        assert resp.status_code == 422

    def test_requires_admin(self) -> None:
        app = _make_app(role="user")
        with TestClient(app) as client:
            resp = client.patch("/cloud/strategy", json={"strategy": "failover"})
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# CloudProviderMetrics unit tests
# ---------------------------------------------------------------------------


class TestCloudProviderMetrics:
    def test_initial_state(self) -> None:
        m = CloudProviderMetrics()
        assert m.total_requests == 0
        assert m.error_rate == 0.0
        assert m.avg_latency_ms == 0.0

    def test_record_success(self) -> None:
        m = CloudProviderMetrics()
        m.record_success(100.0)
        assert m.total_requests == 1
        assert m.total_failures == 0
        assert m.consecutive_successes == 1
        assert m.consecutive_failures == 0
        assert m.avg_latency_ms == 100.0

    def test_record_failure(self) -> None:
        m = CloudProviderMetrics()
        m.record_failure()
        assert m.total_requests == 1
        assert m.total_failures == 1
        assert m.error_rate == 1.0
        assert m.consecutive_failures == 1

    def test_error_rate_calculation(self) -> None:
        m = CloudProviderMetrics()
        m.record_success(50.0)
        m.record_failure()
        assert m.error_rate == pytest.approx(0.5)

    def test_consecutive_reset_on_success(self) -> None:
        m = CloudProviderMetrics()
        m.record_failure()
        m.record_failure()
        m.record_success(10.0)
        assert m.consecutive_failures == 0
        assert m.consecutive_successes == 1

    def test_consecutive_reset_on_failure(self) -> None:
        m = CloudProviderMetrics()
        m.record_success(10.0)
        m.record_success(20.0)
        m.record_failure()
        assert m.consecutive_successes == 0
        assert m.consecutive_failures == 1


# ---------------------------------------------------------------------------
# CloudProvider status transitions
# ---------------------------------------------------------------------------


class TestCloudProviderStatus:
    def test_unknown_when_no_requests(self) -> None:
        p = _make_provider()
        assert p.status == CloudProviderStatus.UNKNOWN

    def test_healthy_after_successes(self) -> None:
        p = _make_provider()
        p._metrics.record_success(50.0)
        p._metrics.record_success(60.0)
        assert p.status == CloudProviderStatus.HEALTHY

    def test_unhealthy_after_3_consecutive_failures(self) -> None:
        p = _make_provider()
        p._metrics.record_failure()
        p._metrics.record_failure()
        p._metrics.record_failure()
        assert p.status == CloudProviderStatus.UNHEALTHY

    def test_unhealthy_when_disabled(self) -> None:
        p = _make_provider(enabled=False)
        assert p.status == CloudProviderStatus.UNHEALTHY

    def test_degraded_after_1_failure(self) -> None:
        p = _make_provider()
        p._metrics.record_success(50.0)
        p._metrics.record_failure()
        assert p.status == CloudProviderStatus.DEGRADED

    def test_unhealthy_on_high_error_rate(self) -> None:
        p = _make_provider()
        for _ in range(3):
            p._metrics.record_failure()
        for _ in range(2):
            p._metrics.record_success(10.0)
        # 3/5 = 60% error rate → UNHEALTHY
        assert p.status == CloudProviderStatus.UNHEALTHY

    def test_health_check_dict_structure(self) -> None:
        p = _make_provider()
        h = p.health_check()
        assert h["name"] == p.name
        assert h["cloud_type"] == p.cloud_type
        assert h["region"] == p.region
        assert "metrics" in h
        assert "status" in h

    def test_to_dict_excludes_jwt(self) -> None:
        p = _make_provider()
        d = p.to_dict()
        assert "jwt" not in d
        assert d["name"] == p.name


# ---------------------------------------------------------------------------
# MultiCloudRouter unit tests
# ---------------------------------------------------------------------------


class TestMultiCloudRouter:
    def test_add_and_list_providers(self) -> None:
        r = MultiCloudRouter()
        r.add_provider(_make_provider("p1"))
        r.add_provider(_make_provider("p2"))
        assert len(r.list_providers()) == 2

    def test_duplicate_provider_raises(self) -> None:
        r = MultiCloudRouter()
        r.add_provider(_make_provider("p1"))
        with pytest.raises(ValueError, match="already registered"):
            r.add_provider(_make_provider("p1"))

    def test_remove_provider(self) -> None:
        r = MultiCloudRouter()
        r.add_provider(_make_provider("p1"))
        removed = r.remove_provider("p1")
        assert removed is True
        assert r.get_provider("p1") is None

    def test_remove_nonexistent_returns_false(self) -> None:
        r = MultiCloudRouter()
        assert r.remove_provider("ghost") is False

    def test_get_provider_by_name(self) -> None:
        r = MultiCloudRouter()
        p = _make_provider("p1")
        r.add_provider(p)
        assert r.get_provider("p1") is p

    def test_get_nonexistent_returns_none(self) -> None:
        r = MultiCloudRouter()
        assert r.get_provider("ghost") is None

    def test_set_strategy(self) -> None:
        r = MultiCloudRouter()
        r.set_strategy(RoutingStrategy.ROUND_ROBIN)
        assert r._strategy == RoutingStrategy.ROUND_ROBIN

    def test_health_summary_empty(self) -> None:
        r = MultiCloudRouter()
        summary = r.health_summary()
        assert summary["total_providers"] == 0
        assert summary["overall"] == "unhealthy"

    def test_health_summary_with_providers(self) -> None:
        r = MultiCloudRouter()
        r.add_provider(_make_provider("p1"))
        summary = r.health_summary()
        assert summary["total_providers"] == 1
        assert "providers" in summary

    def test_failover_strategy_orders_by_priority(self) -> None:
        r = MultiCloudRouter(strategy=RoutingStrategy.FAILOVER)
        r.add_provider(_make_provider("low-pri", priority=10))
        r.add_provider(_make_provider("high-pri", priority=0))
        ordered = r._ordered_providers()
        assert ordered[0].name == "high-pri"

    def test_no_healthy_provider_error(self) -> None:
        r = MultiCloudRouter()
        p = _make_provider("p1")
        # Force unhealthy metrics AND make client raise
        for _ in range(3):
            p._metrics.record_failure()
        p._client.get_tools.side_effect = ConnectionError("p1 down")
        r.add_provider(p)
        with pytest.raises(NoHealthyProviderError):
            r.get_tools()

    def test_get_tools_succeeds_via_provider(self) -> None:
        r = MultiCloudRouter()
        p = _make_provider("p1")
        p._client.get_tools.return_value = [{"name": "tool1"}]
        r.add_provider(p)
        tools = r.get_tools()
        assert tools == [{"name": "tool1"}]

    def test_call_tool_succeeds_via_provider(self) -> None:
        r = MultiCloudRouter()
        p = _make_provider("p1")
        p._client.call_tool.return_value = "result"
        r.add_provider(p)
        result = r.call_tool("tool1", {"arg": "val"})
        assert result == "result"

    def test_failover_to_second_provider(self) -> None:
        r = MultiCloudRouter(strategy=RoutingStrategy.FAILOVER)
        p1 = _make_provider("p1", priority=0)
        p2 = _make_provider("p2", priority=1)
        p1._client.get_tools.side_effect = ConnectionError("p1 down")
        p2._client.get_tools.return_value = [{"name": "tool2"}]
        r.add_provider(p1)
        r.add_provider(p2)
        tools = r.get_tools()
        assert tools == [{"name": "tool2"}]

    def test_round_robin_cycles_providers(self) -> None:
        r = MultiCloudRouter(strategy=RoutingStrategy.ROUND_ROBIN)
        p1 = _make_provider("p1")
        p2 = _make_provider("p2")
        p1._client.get_tools.return_value = [{"name": "t1"}]
        p2._client.get_tools.return_value = [{"name": "t2"}]
        r.add_provider(p1)
        r.add_provider(p2)
        # First call
        r.get_tools()
        # Second call should use different provider (round-robin)
        r.get_tools()
        # Both providers should have been called
        total_calls = p1._client.get_tools.call_count + p2._client.get_tools.call_count
        assert total_calls == 2


# ---------------------------------------------------------------------------
# CloudProviderConfig and MultiCloudConfig
# ---------------------------------------------------------------------------


class TestCloudProviderConfig:
    def test_to_gateway_config(self) -> None:
        cfg = CloudProviderConfig(
            name="test",
            cloud_type="aws",
            region="us-east-1",
            url="http://gateway:8080",
            jwt="secret",
            timeout_ms=5000,
            max_retries=2,
            retry_delay_ms=1000,
        )
        gw = cfg.to_gateway_config()
        assert isinstance(gw, GatewayConfig)
        assert gw.url == "http://gateway:8080"
        assert gw.jwt == "secret"
        assert gw.timeout_ms == 5000

    def test_defaults(self) -> None:
        cfg = CloudProviderConfig(
            name="test",
            cloud_type="custom",
            region="us-east-1",
            url="http://gateway:8080",
        )
        assert cfg.priority == 0
        assert cfg.weight == 1.0
        assert cfg.enabled is True
        assert cfg.timeout_ms == 30000


class TestMultiCloudConfig:
    def test_defaults(self) -> None:
        cfg = MultiCloudConfig()
        assert cfg.enabled is False
        assert cfg.strategy == "failover"
        assert cfg.providers == []

    def test_load_from_environment_disabled(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MULTI_CLOUD_ENABLED", None)
            cfg = MultiCloudConfig.load_from_environment()
        assert cfg.enabled is False

    def test_load_from_environment_enabled(self) -> None:
        env = {
            "MULTI_CLOUD_ENABLED": "true",
            "MULTI_CLOUD_STRATEGY": "round_robin",
            "CLOUD_PROVIDER_0_NAME": "aws-east",
            "CLOUD_PROVIDER_0_TYPE": "aws",
            "CLOUD_PROVIDER_0_REGION": "us-east-1",
            "CLOUD_PROVIDER_0_URL": "http://aws-gateway:8080",
            "CLOUD_PROVIDER_0_JWT": "aws-jwt",
            "CLOUD_PROVIDER_0_PRIORITY": "0",
            "CLOUD_PROVIDER_0_WEIGHT": "2.0",
        }
        with patch.dict(os.environ, env):
            cfg = MultiCloudConfig.load_from_environment()
        assert cfg.enabled is True
        assert cfg.strategy == "round_robin"
        assert len(cfg.providers) == 1
        assert cfg.providers[0].name == "aws-east"
        assert cfg.providers[0].cloud_type == "aws"
        assert cfg.providers[0].weight == 2.0

    def test_load_multiple_providers(self) -> None:
        env = {
            "MULTI_CLOUD_ENABLED": "true",
            "CLOUD_PROVIDER_0_NAME": "p0",
            "CLOUD_PROVIDER_0_TYPE": "aws",
            "CLOUD_PROVIDER_0_REGION": "us-east-1",
            "CLOUD_PROVIDER_0_URL": "http://p0:8080",
            "CLOUD_PROVIDER_1_NAME": "p1",
            "CLOUD_PROVIDER_1_TYPE": "azure",
            "CLOUD_PROVIDER_1_REGION": "westus",
            "CLOUD_PROVIDER_1_URL": "http://p1:8080",
        }
        with patch.dict(os.environ, env):
            cfg = MultiCloudConfig.load_from_environment()
        assert len(cfg.providers) == 2
        assert cfg.providers[0].name == "p0"
        assert cfg.providers[1].name == "p1"

    def test_stops_at_missing_name(self) -> None:
        env = {
            "MULTI_CLOUD_ENABLED": "true",
            "CLOUD_PROVIDER_0_NAME": "p0",
            "CLOUD_PROVIDER_0_TYPE": "aws",
            "CLOUD_PROVIDER_0_REGION": "us-east-1",
            "CLOUD_PROVIDER_0_URL": "http://p0:8080",
            # No CLOUD_PROVIDER_1_NAME — should stop here
            "CLOUD_PROVIDER_2_NAME": "p2",
            "CLOUD_PROVIDER_2_TYPE": "gcp",
            "CLOUD_PROVIDER_2_REGION": "us-central1",
            "CLOUD_PROVIDER_2_URL": "http://p2:8080",
        }
        with patch.dict(os.environ, env):
            cfg = MultiCloudConfig.load_from_environment()
        assert len(cfg.providers) == 1
