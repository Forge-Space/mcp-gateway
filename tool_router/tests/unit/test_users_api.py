"""Tests for GET /users endpoint.

Verifies:
- Response structure (roles list, total_roles, total_permissions)
- RBAC enforcement (AUDIT_READ / SYSTEM_ADMIN required)
- Role catalog completeness (4 roles: admin, developer, user, guest)
- Permission sets per role
- RoleEntry fields (role, display_name, description, permissions, permission_count, is_privileged)
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tool_router.api.dependencies import get_security_context
from tool_router.api.users import router as users_router
from tool_router.security.security_middleware import SecurityContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_app(security_context: SecurityContext | None) -> FastAPI:
    app = FastAPI()
    app.include_router(users_router)

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
        endpoint="/users",
        authentication_method="jwt",
        user_role=role,
    )


# ---------------------------------------------------------------------------
# RBAC tests
# ---------------------------------------------------------------------------


def test_get_users_requires_authentication() -> None:
    """Returns 403 when no security context provided."""
    app = _make_app(None)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/users")
    assert response.status_code in (401, 403, 422)


def test_get_users_forbidden_for_user_role() -> None:
    """user role cannot access role catalog (no AUDIT_READ)."""
    app = _make_app(_make_ctx("user"))
    client = TestClient(app)
    response = client.get("/users")
    assert response.status_code == 403


def test_get_users_forbidden_for_guest_role() -> None:
    """guest role cannot access role catalog (minimal perms)."""
    app = _make_app(_make_ctx("guest"))
    client = TestClient(app)
    response = client.get("/users")
    assert response.status_code == 403


def test_get_users_allowed_for_developer_role() -> None:
    """developer role can access role catalog (has AUDIT_READ)."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    response = client.get("/users")
    assert response.status_code == 200


def test_get_users_allowed_for_admin_role() -> None:
    """admin role can access role catalog (has SYSTEM_ADMIN)."""
    app = _make_app(_make_ctx("admin"))
    client = TestClient(app)
    response = client.get("/users")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Response structure tests
# ---------------------------------------------------------------------------


def test_get_users_response_has_required_fields() -> None:
    """Response includes roles, total_roles, total_permissions."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    data = client.get("/users").json()
    assert "roles" in data
    assert "total_roles" in data
    assert "total_permissions" in data


def test_get_users_returns_4_roles() -> None:
    """Exactly 4 roles are returned (admin, developer, user, guest)."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    data = client.get("/users").json()
    assert data["total_roles"] == 4
    assert len(data["roles"]) == 4


def test_get_users_total_roles_matches_list_length() -> None:
    """total_roles equals len(roles)."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    data = client.get("/users").json()
    assert data["total_roles"] == len(data["roles"])


def test_get_users_total_permissions_is_positive() -> None:
    """total_permissions is > 0."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    data = client.get("/users").json()
    assert data["total_permissions"] > 0


# ---------------------------------------------------------------------------
# Role entry field tests
# ---------------------------------------------------------------------------


def test_get_users_each_role_has_required_fields() -> None:
    """Each role entry has all required fields."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    roles = client.get("/users").json()["roles"]
    for role in roles:
        assert "role" in role
        assert "display_name" in role
        assert "description" in role
        assert "permissions" in role
        assert "permission_count" in role
        assert "is_privileged" in role
        assert isinstance(role["permissions"], list)
        assert isinstance(role["permission_count"], int)
        assert isinstance(role["is_privileged"], bool)


def test_get_users_permission_count_matches_permissions_list() -> None:
    """permission_count equals len(permissions) for each role."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    roles = client.get("/users").json()["roles"]
    for role in roles:
        assert role["permission_count"] == len(role["permissions"])


def test_get_users_expected_roles_present() -> None:
    """All four expected roles are present."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    role_ids = {r["role"] for r in client.get("/users").json()["roles"]}
    assert role_ids == {"admin", "developer", "user", "guest"}


# ---------------------------------------------------------------------------
# Role-specific permission tests
# ---------------------------------------------------------------------------


def test_get_users_admin_has_all_permissions() -> None:
    """admin role has the most permissions (all system permissions)."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    roles = {r["role"]: r for r in client.get("/users").json()["roles"]}
    admin = roles["admin"]
    assert admin["permission_count"] > roles["developer"]["permission_count"]
    assert "system:admin" in admin["permissions"]
    assert "user:manage" in admin["permissions"]


def test_get_users_developer_has_audit_read() -> None:
    """developer role has audit:read permission."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    roles = {r["role"]: r for r in client.get("/users").json()["roles"]}
    assert "audit:read" in roles["developer"]["permissions"]


def test_get_users_user_lacks_audit_read() -> None:
    """user role does not have audit:read permission."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    roles = {r["role"]: r for r in client.get("/users").json()["roles"]}
    assert "audit:read" not in roles["user"]["permissions"]


def test_get_users_guest_has_minimal_permissions() -> None:
    """guest role has only component:read and template:read."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    roles = {r["role"]: r for r in client.get("/users").json()["roles"]}
    guest = roles["guest"]
    assert guest["permission_count"] == 2
    assert "component:read" in guest["permissions"]
    assert "template:read" in guest["permissions"]


# ---------------------------------------------------------------------------
# Privileged flag tests
# ---------------------------------------------------------------------------


def test_get_users_admin_and_developer_are_privileged() -> None:
    """admin and developer roles are marked as privileged."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    roles = {r["role"]: r for r in client.get("/users").json()["roles"]}
    assert roles["admin"]["is_privileged"] is True
    assert roles["developer"]["is_privileged"] is True


def test_get_users_user_and_guest_are_not_privileged() -> None:
    """user and guest roles are not privileged."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    roles = {r["role"]: r for r in client.get("/users").json()["roles"]}
    assert roles["user"]["is_privileged"] is False
    assert roles["guest"]["is_privileged"] is False


def test_get_users_display_names_are_non_empty() -> None:
    """All roles have non-empty display_name and description."""
    app = _make_app(_make_ctx("developer"))
    client = TestClient(app)
    roles = client.get("/users").json()["roles"]
    for role in roles:
        assert role["display_name"].strip() != ""
        assert role["description"].strip() != ""
