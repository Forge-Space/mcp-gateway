"""Tests for audit API endpoints — RBAC enforcement.

Verifies that /audit/events and /audit/summary:
- Return 401/403/422 when no Authorization header is present
- Return 403 when the caller has a role without AUDIT_READ (user, guest)
- Return 200 when the caller has AUDIT_READ (admin, developer)

Per ROLE_PERMISSIONS in authorization.py:
  ADMIN     → all permissions (including AUDIT_READ)
  DEVELOPER → includes AUDIT_READ
  USER      → no AUDIT_READ → 403
  GUEST     → no AUDIT_READ → 403
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tool_router.api.audit import router as audit_router
from tool_router.api.dependencies import get_security_context
from tool_router.security.security_middleware import SecurityContext


# ---------------------------------------------------------------------------
# Test app wiring
# ---------------------------------------------------------------------------


def _make_app(security_context: SecurityContext | None) -> FastAPI:
    """Build a test FastAPI app that overrides get_security_context."""
    app = FastAPI()
    app.include_router(audit_router)

    if security_context is not None:
        # Override the dependency so we can control role
        async def _mock_ctx() -> SecurityContext:
            return security_context

        app.dependency_overrides[get_security_context] = _mock_ctx
    # If None → no override → real dependency runs → will 401 (no JWT configured)

    return app


def _make_ctx(role: str) -> SecurityContext:
    return SecurityContext(
        user_id="user-test",
        session_id="sess-test",
        ip_address="127.0.0.1",
        user_agent="test-agent",
        request_id="req-test-1",
        endpoint="/audit",
        authentication_method="jwt",
        user_role=role,
    )


def _mock_summary() -> dict[str, Any]:
    return {
        "total_events": 2,
        "events_by_type": {"request": 2},
        "events_by_severity": {"info": 2},
        "recent_events": [
            {
                "timestamp": "2026-03-15T00:00:00Z",
                "event_type": "request",
                "severity": "info",
                "user_id": "user-abc",
                "request_id": "req-1",
                "ip_address": "1.2.3.4",
                "details": {},
            }
        ],
    }


# ---------------------------------------------------------------------------
# Tests: /audit/events
# ---------------------------------------------------------------------------


class TestAuditEventsAuth:
    """RBAC enforcement on GET /audit/events."""

    def test_admin_role_returns_200(self) -> None:
        app = _make_app(_make_ctx("admin"))
        client = TestClient(app, raise_server_exceptions=False)
        with patch(
            "tool_router.api.audit._get_audit_logger",
            return_value=MagicMock(get_security_summary=MagicMock(return_value=_mock_summary())),
        ):
            resp = client.get("/audit/events")
        assert resp.status_code == 200, resp.text

    def test_developer_role_returns_200(self) -> None:
        """Developer has AUDIT_READ per ROLE_PERMISSIONS — should succeed."""
        app = _make_app(_make_ctx("developer"))
        client = TestClient(app, raise_server_exceptions=False)
        with patch(
            "tool_router.api.audit._get_audit_logger",
            return_value=MagicMock(get_security_summary=MagicMock(return_value=_mock_summary())),
        ):
            resp = client.get("/audit/events")
        assert resp.status_code == 200, resp.text

    def test_user_role_returns_403(self) -> None:
        """USER has no AUDIT_READ — must be 403."""
        app = _make_app(_make_ctx("user"))
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/audit/events")
        assert resp.status_code == 403

    def test_guest_role_returns_403(self) -> None:
        """GUEST has no AUDIT_READ — must be 403."""
        app = _make_app(_make_ctx("guest"))
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/audit/events")
        assert resp.status_code == 403

    def test_no_auth_returns_401_or_403(self) -> None:
        """Without dependency override, real auth runs and should reject."""
        app = FastAPI()
        app.include_router(audit_router)
        client = TestClient(app, raise_server_exceptions=False)
        # Real get_security_context requires a JWT — missing header → 401/403
        resp = client.get("/audit/events")
        assert resp.status_code in (401, 403), f"Expected 401/403 got {resp.status_code}"

    def test_admin_events_are_paginated(self) -> None:
        app = _make_app(_make_ctx("admin"))
        client = TestClient(app, raise_server_exceptions=False)
        # Inject 3 events and request page_size=2
        summary = _mock_summary()
        summary["recent_events"] = summary["recent_events"] * 3
        with patch(
            "tool_router.api.audit._get_audit_logger",
            return_value=MagicMock(get_security_summary=MagicMock(return_value=summary)),
        ):
            resp = client.get("/audit/events?page_size=2&page=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page_size"] == 2
        assert data["page"] == 1
        assert len(data["events"]) <= 2


# ---------------------------------------------------------------------------
# Tests: /audit/summary
# ---------------------------------------------------------------------------


class TestAuditSummaryAuth:
    """RBAC enforcement on GET /audit/summary."""

    def test_admin_role_returns_200(self) -> None:
        app = _make_app(_make_ctx("admin"))
        client = TestClient(app, raise_server_exceptions=False)
        with patch(
            "tool_router.api.audit._get_audit_logger",
            return_value=MagicMock(get_security_summary=MagicMock(return_value=_mock_summary())),
        ):
            resp = client.get("/audit/summary")
        assert resp.status_code == 200

    def test_developer_role_returns_200(self) -> None:
        """Developer has AUDIT_READ — should succeed."""
        app = _make_app(_make_ctx("developer"))
        client = TestClient(app, raise_server_exceptions=False)
        with patch(
            "tool_router.api.audit._get_audit_logger",
            return_value=MagicMock(get_security_summary=MagicMock(return_value=_mock_summary())),
        ):
            resp = client.get("/audit/summary")
        assert resp.status_code == 200

    def test_user_role_returns_403(self) -> None:
        """USER has no AUDIT_READ — must be 403."""
        app = _make_app(_make_ctx("user"))
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/audit/summary")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Tests: _require_audit_read dependency
# ---------------------------------------------------------------------------


class TestRequireAuditReadDependency:
    """Unit test the _require_audit_read guard directly."""

    def test_admin_passes_through(self) -> None:
        from tool_router.api.audit import _require_audit_read

        ctx = _make_ctx("admin")
        result = _require_audit_read(ctx)
        assert result is ctx

    def test_developer_passes_through(self) -> None:
        """Developer has AUDIT_READ — no exception."""
        from tool_router.api.audit import _require_audit_read

        ctx = _make_ctx("developer")
        result = _require_audit_read(ctx)
        assert result is ctx

    def test_guest_raises_403(self) -> None:
        from fastapi import HTTPException

        from tool_router.api.audit import _require_audit_read

        ctx = _make_ctx("guest")
        with pytest.raises(HTTPException) as exc_info:
            _require_audit_read(ctx)
        assert exc_info.value.status_code == 403

    def test_none_role_raises_403(self) -> None:
        """Unknown/None role defaults to guest → no AUDIT_READ."""
        from fastapi import HTTPException

        from tool_router.api.audit import _require_audit_read

        ctx = _make_ctx("unknown-role")
        with pytest.raises(HTTPException) as exc_info:
            _require_audit_read(ctx)
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Tests: filter branches (lines 126, 128, 130) and error paths (107-109, 157-159)
# ---------------------------------------------------------------------------


class TestAuditEventsFilters:
    """Cover event_type, severity, user_id filter branches and 500 error."""

    def _summary_with_events(self) -> dict[str, Any]:
        return {
            "total_events": 3,
            "recent_events": [
                {
                    "timestamp": "2026-01-01T00:00:00Z",
                    "event_type": "request",
                    "severity": "info",
                    "user_id": "user-abc",
                    "request_id": "req-1",
                    "ip_address": "1.2.3.4",
                    "details": {},
                },
                {
                    "timestamp": "2026-01-02T00:00:00Z",
                    "event_type": "security",
                    "severity": "warning",
                    "user_id": "user-xyz",
                    "request_id": "req-2",
                    "ip_address": "5.6.7.8",
                    "details": {},
                },
            ],
        }

    @pytest.mark.parametrize(
        ("filter_key", "filter_value", "expected_field", "expected_value", "expected_count"),
        [
            ("event_type", "request", "event_type", "request", 1),
            ("severity", "warning", "severity", "warning", 1),
            ("user_id", "user-abc", "user_id", "user-abc", 1),
        ],
    )
    def test_filter_excludes_non_matching(
        self,
        filter_key: str,
        filter_value: str,
        expected_field: str,
        expected_value: str,
        expected_count: int,
    ) -> None:
        """Lines 126-130: filter params exclude non-matching events."""
        app = _make_app(_make_ctx("admin"))
        client = TestClient(app, raise_server_exceptions=False)
        with patch(
            "tool_router.api.audit._get_audit_logger",
            return_value=MagicMock(get_security_summary=MagicMock(return_value=self._summary_with_events())),
        ):
            resp = client.get(f"/audit/events?{filter_key}={filter_value}")
        assert resp.status_code == 200
        data = resp.json()
        events = data["events"]
        assert len(events) == expected_count
        assert all(e[expected_field] == expected_value for e in events)

    def test_events_500_on_exception(self) -> None:
        """Lines 107-109: except clause → 500."""
        app = _make_app(_make_ctx("admin"))
        client = TestClient(app, raise_server_exceptions=False)
        with patch(
            "tool_router.api.audit._get_audit_logger",
            return_value=MagicMock(get_security_summary=MagicMock(side_effect=RuntimeError("DB failure"))),
        ):
            resp = client.get("/audit/events")
        assert resp.status_code == 500

    def test_summary_500_on_exception(self) -> None:
        """Lines 157-159: except clause in get_audit_summary → 500."""
        app = _make_app(_make_ctx("admin"))
        client = TestClient(app, raise_server_exceptions=False)
        with patch(
            "tool_router.api.audit._get_audit_logger",
            return_value=MagicMock(get_security_summary=MagicMock(side_effect=RuntimeError("failure"))),
        ):
            resp = client.get("/audit/summary")
        assert resp.status_code == 500


class TestAuditLoggerFactoryCoverage:
    """Cover direct _get_audit_logger() import-and-return branch."""

    def test_get_audit_logger_returns_security_audit_logger_instance(self) -> None:
        from tool_router.api.audit import _get_audit_logger

        sentinel = MagicMock(name="security_audit_logger")
        with patch("tool_router.security.SecurityAuditLogger", return_value=sentinel) as mock_cls:
            logger_instance = _get_audit_logger()

        assert logger_instance is sentinel
        mock_cls.assert_called_once_with()
