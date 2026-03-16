"""Tests for GET /security/stats endpoint.

Verifies:
- Response structure (vulnerabilities, compliance_score, policies, last_updated)
- RBAC enforcement (AUDIT_READ / SYSTEM_ADMIN required)
- Compliance score aggregation logic
- Policy status derivation from env
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tool_router.api.dependencies import get_security_context
from tool_router.api.security_stats import router as security_stats_router
from tool_router.security.security_middleware import SecurityContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_app(security_context: SecurityContext | None) -> FastAPI:
    app = FastAPI()
    app.include_router(security_stats_router)

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
        endpoint="/security/stats",
        authentication_method="jwt",
        user_role=role,
    )


def _mock_audit_summary() -> dict[str, Any]:
    return {
        "period_hours": 24,
        "total_events": 5,
        "blocked_requests": 1,
        "high_risk_events": 2,
        "critical_events": 1,
        "top_event_types": [],
        "top_ip_addresses": [],
        "risk_trends": [],
    }


def _patched_client(role: str, summary: dict[str, Any] | None = None) -> TestClient:
    app = _make_app(_make_ctx(role))
    audit_mock = MagicMock(get_security_summary=MagicMock(return_value=summary or _mock_audit_summary()))
    app.state._audit_mock = audit_mock
    return TestClient(app, raise_server_exceptions=False), audit_mock


# ---------------------------------------------------------------------------
# Tests: RBAC enforcement
# ---------------------------------------------------------------------------


class TestSecurityStatsAuth:
    """RBAC permission checks on GET /security/stats."""

    def test_admin_returns_200(self) -> None:
        app = _make_app(_make_ctx("admin"))
        client = TestClient(app, raise_server_exceptions=False)
        with patch(
            "tool_router.api.security_stats._get_audit_logger",
            return_value=MagicMock(get_security_summary=MagicMock(return_value=_mock_audit_summary())),
        ):
            resp = client.get("/security/stats")
        assert resp.status_code == 200, resp.text

    def test_developer_returns_200(self) -> None:
        """Developer has AUDIT_READ — should succeed."""
        app = _make_app(_make_ctx("developer"))
        client = TestClient(app, raise_server_exceptions=False)
        with patch(
            "tool_router.api.security_stats._get_audit_logger",
            return_value=MagicMock(get_security_summary=MagicMock(return_value=_mock_audit_summary())),
        ):
            resp = client.get("/security/stats")
        assert resp.status_code == 200, resp.text

    def test_user_returns_403(self) -> None:
        """USER lacks AUDIT_READ and SYSTEM_ADMIN — must be 403."""
        app = _make_app(_make_ctx("user"))
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/security/stats")
        assert resp.status_code == 403

    def test_guest_returns_403(self) -> None:
        """GUEST lacks required permissions — must be 403."""
        app = _make_app(_make_ctx("guest"))
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/security/stats")
        assert resp.status_code == 403

    def test_no_auth_returns_401_or_403(self) -> None:
        """Without dependency override, real JWT auth rejects unauthenticated requests."""
        app = FastAPI()
        app.include_router(security_stats_router)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/security/stats")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    def test_unknown_role_returns_403(self) -> None:
        """Unknown roles default to guest and are denied."""
        app = _make_app(_make_ctx("superuser"))
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/security/stats")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Tests: Response structure
# ---------------------------------------------------------------------------


class TestSecurityStatsResponseStructure:
    """Validate the shape and field types of the response."""

    def _get_stats(self, summary: dict[str, Any] | None = None) -> dict[str, Any]:
        app = _make_app(_make_ctx("admin"))
        client = TestClient(app, raise_server_exceptions=False)
        with patch(
            "tool_router.api.security_stats._get_audit_logger",
            return_value=MagicMock(get_security_summary=MagicMock(return_value=summary or _mock_audit_summary())),
        ):
            resp = client.get("/security/stats")
        assert resp.status_code == 200, resp.text
        return resp.json()

    def test_response_has_vulnerabilities_key(self) -> None:
        data = self._get_stats()
        assert "vulnerabilities" in data

    def test_vulnerabilities_has_all_severity_keys(self) -> None:
        data = self._get_stats()
        vuln = data["vulnerabilities"]
        for key in ("critical", "high", "medium", "low"):
            assert key in vuln, f"Missing key: {key}"

    def test_response_has_compliance_score(self) -> None:
        data = self._get_stats()
        assert "compliance_score" in data
        assert isinstance(data["compliance_score"], (int, float))

    def test_compliance_score_in_valid_range(self) -> None:
        data = self._get_stats()
        assert 0 <= data["compliance_score"] <= 100

    def test_response_has_policies_list(self) -> None:
        data = self._get_stats()
        assert "policies" in data
        assert isinstance(data["policies"], list)

    def test_policies_have_required_fields(self) -> None:
        data = self._get_stats()
        for policy in data["policies"]:
            for field in ("name", "status", "description", "last_updated"):
                assert field in policy, f"Policy missing field: {field}"

    def test_policies_status_is_active_or_inactive(self) -> None:
        data = self._get_stats()
        for policy in data["policies"]:
            assert policy["status"] in ("active", "inactive")

    def test_response_has_last_updated(self) -> None:
        data = self._get_stats()
        assert "last_updated" in data
        assert isinstance(data["last_updated"], str)
        assert len(data["last_updated"]) > 0

    def test_vulnerability_counts_map_from_audit_summary(self) -> None:
        summary = _mock_audit_summary()
        data = self._get_stats(summary=summary)
        assert data["vulnerabilities"]["critical"] == summary["critical_events"]
        assert data["vulnerabilities"]["high"] == summary["high_risk_events"]


# ---------------------------------------------------------------------------
# Tests: Compliance score aggregation
# ---------------------------------------------------------------------------


class TestComplianceScoreAggregation:
    """Validate compliance_score = active_policies / total_policies * 100."""

    def test_all_policies_active_gives_100(self) -> None:
        app = _make_app(_make_ctx("admin"))
        client = TestClient(app, raise_server_exceptions=False)

        active_policies = [
            {"name": "P1", "status": "active", "description": "d", "last_updated": "2026-01-01T00:00:00+00:00"},
            {"name": "P2", "status": "active", "description": "d", "last_updated": "2026-01-01T00:00:00+00:00"},
            {"name": "P3", "status": "active", "description": "d", "last_updated": "2026-01-01T00:00:00+00:00"},
        ]
        with (
            patch(
                "tool_router.api.security_stats._get_audit_logger",
                return_value=MagicMock(get_security_summary=MagicMock(return_value=_mock_audit_summary())),
            ),
            patch(
                "tool_router.api.security_stats._derive_policy_status",
                return_value=active_policies,
            ),
        ):
            resp = client.get("/security/stats")

        assert resp.status_code == 200
        data = resp.json()
        assert data["compliance_score"] == 100.0

    def test_no_active_policies_gives_0(self) -> None:
        app = _make_app(_make_ctx("admin"))
        client = TestClient(app, raise_server_exceptions=False)

        inactive_policies = [
            {"name": "P1", "status": "inactive", "description": "d", "last_updated": "2026-01-01T00:00:00+00:00"},
            {"name": "P2", "status": "inactive", "description": "d", "last_updated": "2026-01-01T00:00:00+00:00"},
        ]
        with (
            patch(
                "tool_router.api.security_stats._get_audit_logger",
                return_value=MagicMock(get_security_summary=MagicMock(return_value=_mock_audit_summary())),
            ),
            patch(
                "tool_router.api.security_stats._derive_policy_status",
                return_value=inactive_policies,
            ),
        ):
            resp = client.get("/security/stats")

        assert resp.status_code == 200
        data = resp.json()
        assert data["compliance_score"] == 0.0

    def test_partial_active_policies_gives_correct_score(self) -> None:
        app = _make_app(_make_ctx("admin"))
        client = TestClient(app, raise_server_exceptions=False)

        mixed_policies = [
            {"name": "P1", "status": "active", "description": "d", "last_updated": "2026-01-01T00:00:00+00:00"},
            {"name": "P2", "status": "inactive", "description": "d", "last_updated": "2026-01-01T00:00:00+00:00"},
            {"name": "P3", "status": "inactive", "description": "d", "last_updated": "2026-01-01T00:00:00+00:00"},
            {"name": "P4", "status": "active", "description": "d", "last_updated": "2026-01-01T00:00:00+00:00"},
        ]
        with (
            patch(
                "tool_router.api.security_stats._get_audit_logger",
                return_value=MagicMock(get_security_summary=MagicMock(return_value=_mock_audit_summary())),
            ),
            patch(
                "tool_router.api.security_stats._derive_policy_status",
                return_value=mixed_policies,
            ),
        ):
            resp = client.get("/security/stats")

        assert resp.status_code == 200
        data = resp.json()
        assert data["compliance_score"] == 50.0


# ---------------------------------------------------------------------------
# Tests: _require_security_read dependency unit tests
# ---------------------------------------------------------------------------


class TestRequireSecurityReadDependency:
    """Unit test the _require_security_read guard directly."""

    def test_admin_passes_through(self) -> None:
        from tool_router.api.security_stats import _require_security_read

        ctx = _make_ctx("admin")
        result = _require_security_read(ctx)
        assert result is ctx

    def test_developer_passes_through(self) -> None:
        from tool_router.api.security_stats import _require_security_read

        ctx = _make_ctx("developer")
        result = _require_security_read(ctx)
        assert result is ctx

    def test_user_raises_403(self) -> None:
        from fastapi import HTTPException

        from tool_router.api.security_stats import _require_security_read

        ctx = _make_ctx("user")
        with pytest.raises(HTTPException) as exc_info:
            _require_security_read(ctx)
        assert exc_info.value.status_code == 403

    def test_guest_raises_403(self) -> None:
        from fastapi import HTTPException

        from tool_router.api.security_stats import _require_security_read

        ctx = _make_ctx("guest")
        with pytest.raises(HTTPException) as exc_info:
            _require_security_read(ctx)
        assert exc_info.value.status_code == 403
