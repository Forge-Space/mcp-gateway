"""Tests for GET /features endpoint.

Verifies:
- Response structure (features list, total, enabled_count)
- RBAC enforcement (AUDIT_READ / SYSTEM_ADMIN required)
- Feature flag resolution from environment variables
- Source field (env vs default)
- Category values
- All 11 expected features present
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tool_router.api.dependencies import get_security_context
from tool_router.api.features import router as features_router
from tool_router.security.security_middleware import SecurityContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_app(security_context: SecurityContext | None) -> FastAPI:
    app = FastAPI()
    app.include_router(features_router)

    if security_context is not None:

        async def _mock_ctx() -> SecurityContext:
            return security_context

        app.dependency_overrides[get_security_context] = _mock_ctx

    return app


def _make_ctx(role: str) -> SecurityContext:
    return SecurityContext(
        user_id="user-test",
        session_id="sess-test",
        ip_address="127.0.0.1",
        user_agent="test-agent",
        request_id="req-test-1",
        endpoint="/features",
        authentication_method="jwt",
        user_role=role,
    )


# ---------------------------------------------------------------------------
# RBAC tests
# ---------------------------------------------------------------------------


def test_get_features_requires_authentication() -> None:
    """Returns 403 when no security context provided."""
    app = _make_app(None)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/features")
    assert response.status_code in (401, 403, 422)


def test_get_features_forbidden_for_user_role() -> None:
    """user role cannot access feature flags (no AUDIT_READ)."""
    app = _make_app(_make_ctx("user"))
    client = TestClient(app)
    response = client.get("/features")
    assert response.status_code == 403


def test_get_features_allowed_for_developer_role() -> None:
    """developer role can access feature flags (has AUDIT_READ)."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    response = client.get("/features")
    assert response.status_code == 200


def test_get_features_allowed_for_system_admin_role() -> None:
    """SYSTEM_ADMIN role can access feature flags."""
    app = _make_app(_make_ctx("admin"))
    client = TestClient(app)
    response = client.get("/features")
    assert response.status_code == 200


def test_get_features_forbidden_for_guest_role() -> None:
    """guest role cannot access feature flags (minimal perms)."""
    app = _make_app(_make_ctx("guest"))
    client = TestClient(app)
    response = client.get("/features")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Response structure tests
# ---------------------------------------------------------------------------


def test_get_features_response_has_required_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Response includes features, total, enabled_count."""
    monkeypatch.delenv("DEBUG", raising=False)
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    data = client.get("/features").json()
    assert "features" in data
    assert "total" in data
    assert "enabled_count" in data


def test_get_features_total_matches_features_list_length(monkeypatch: pytest.MonkeyPatch) -> None:
    """total field equals len(features)."""
    monkeypatch.delenv("DEBUG", raising=False)
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    data = client.get("/features").json()
    assert data["total"] == len(data["features"])


def test_get_features_returns_11_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exactly 11 feature flags are returned."""
    monkeypatch.delenv("DEBUG", raising=False)
    monkeypatch.delenv("BETA_FEATURES", raising=False)
    monkeypatch.delenv("ENHANCED_LOGGING", raising=False)
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    data = client.get("/features").json()
    assert data["total"] == 11


def test_get_features_each_flag_has_required_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each flag has name, description, enabled, category, source."""
    monkeypatch.delenv("DEBUG", raising=False)
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    features = client.get("/features").json()["features"]
    for flag in features:
        assert "name" in flag
        assert "description" in flag
        assert "enabled" in flag
        assert "category" in flag
        assert "source" in flag
        assert isinstance(flag["enabled"], bool)


# ---------------------------------------------------------------------------
# Category and naming tests
# ---------------------------------------------------------------------------


def test_get_features_valid_categories(monkeypatch: pytest.MonkeyPatch) -> None:
    """All flags have a valid category value."""
    monkeypatch.delenv("DEBUG", raising=False)
    valid_categories = {"global", "mcp-gateway", "uiforge-mcp", "uiforge-webapp"}
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    features = client.get("/features").json()["features"]
    for flag in features:
        assert flag["category"] in valid_categories, f"Invalid category: {flag['category']}"


def test_get_features_expected_flag_names_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """Specific expected feature names are present."""
    monkeypatch.delenv("DEBUG", raising=False)
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    names = {f["name"] for f in client.get("/features").json()["features"]}
    expected = {
        "global.debug-mode",
        "global.beta-features",
        "global.enhanced-logging",
        "mcp-gateway.rate-limiting",
        "mcp-gateway.security-headers",
        "mcp-gateway.performance-monitoring",
        "mcp-gateway.cache-layer",
        "uiforge-mcp.ai-chat",
        "uiforge-mcp.template-management",
        "uiforge-webapp.dark-mode",
        "uiforge-webapp.advanced-analytics",
    }
    assert names == expected


# ---------------------------------------------------------------------------
# Source resolution tests
# ---------------------------------------------------------------------------


def test_get_features_source_is_env_when_var_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """When env var is explicitly set, source is 'env'."""
    monkeypatch.setenv("DEBUG", "1")
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    features = client.get("/features").json()["features"]
    debug_flag = next(f for f in features if f["name"] == "global.debug-mode")
    assert debug_flag["source"] == "env"
    assert debug_flag["enabled"] is True


def test_get_features_source_is_default_when_var_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """When env var is not set, source is 'default'."""
    monkeypatch.delenv("DEBUG", raising=False)
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    features = client.get("/features").json()["features"]
    debug_flag = next(f for f in features if f["name"] == "global.debug-mode")
    assert debug_flag["source"] == "default"
    assert debug_flag["enabled"] is False


def test_get_features_debug_false_when_env_is_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setting DEBUG=false results in enabled=False."""
    monkeypatch.setenv("DEBUG", "false")
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    features = client.get("/features").json()["features"]
    debug_flag = next(f for f in features if f["name"] == "global.debug-mode")
    assert debug_flag["enabled"] is False
    assert debug_flag["source"] == "env"


def test_get_features_beta_features_enabled_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """BETA_FEATURES=true enables global.beta-features."""
    monkeypatch.setenv("BETA_FEATURES", "true")
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    features = client.get("/features").json()["features"]
    beta_flag = next(f for f in features if f["name"] == "global.beta-features")
    assert beta_flag["enabled"] is True
    assert beta_flag["source"] == "env"


# ---------------------------------------------------------------------------
# Enabled count tests
# ---------------------------------------------------------------------------


def test_get_features_enabled_count_matches_sum(monkeypatch: pytest.MonkeyPatch) -> None:
    """enabled_count equals sum of enabled flags."""
    monkeypatch.delenv("DEBUG", raising=False)
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    data = client.get("/features").json()
    actual_count = sum(1 for f in data["features"] if f["enabled"])
    assert data["enabled_count"] == actual_count


def test_get_features_enabled_count_increases_when_env_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enabling a previously-disabled flag increases enabled_count."""
    monkeypatch.delenv("DEBUG", raising=False)
    monkeypatch.delenv("BETA_FEATURES", raising=False)
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    count_before = client.get("/features").json()["enabled_count"]

    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.setenv("BETA_FEATURES", "1")
    app2 = _make_app(_make_ctx("developer"))
    client2 = TestClient(app2)
    count_after = client2.get("/features").json()["enabled_count"]

    assert count_after == count_before + 2


def test_get_features_enabled_count_is_non_negative(monkeypatch: pytest.MonkeyPatch) -> None:
    """enabled_count is always >= 0."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    data = client.get("/features").json()
    assert data["enabled_count"] >= 0


# ---------------------------------------------------------------------------
# Source values tests
# ---------------------------------------------------------------------------


def test_get_features_source_values_are_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    """All source values are either 'env' or 'default'."""
    monkeypatch.delenv("DEBUG", raising=False)
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    features = client.get("/features").json()["features"]
    for flag in features:
        assert flag["source"] in ("env", "default"), f"Unexpected source: {flag['source']}"
