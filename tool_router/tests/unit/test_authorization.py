"""Tests for tool_router.security.authorization module."""

from __future__ import annotations

import pytest

from tool_router.security.authorization import (
    RESOURCE_ACTION_MAP,
    ROLE_PERMISSIONS,
    AuthorizationError,
    AuthzResult,
    Permission,
    RBACEvaluator,
    Role,
)


# ---------------------------------------------------------------------------
# Role enum
# ---------------------------------------------------------------------------


class TestRoleEnum:
    def test_values(self):
        assert Role.ADMIN == "admin"
        assert Role.DEVELOPER == "developer"
        assert Role.USER == "user"
        assert Role.GUEST == "guest"

    def test_is_str_enum(self):
        assert isinstance(Role.ADMIN, str)

    def test_all_roles_count(self):
        assert len(list(Role)) == 4


# ---------------------------------------------------------------------------
# Permission enum
# ---------------------------------------------------------------------------


class TestPermissionEnum:
    def test_values(self):
        assert Permission.AUDIT_READ == "audit:read"
        assert Permission.SYSTEM_ADMIN == "system:admin"
        assert Permission.TOOL_EXECUTE == "tool:execute"
        assert Permission.COMPONENT_READ == "component:read"

    def test_all_permissions_count(self):
        assert len(list(Permission)) == 16

    def test_is_str_enum(self):
        assert isinstance(Permission.AUDIT_READ, str)


# ---------------------------------------------------------------------------
# ROLE_PERMISSIONS mapping
# ---------------------------------------------------------------------------


class TestRolePermissions:
    def test_admin_has_all_permissions(self):
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        for perm in Permission:
            assert perm in admin_perms

    def test_developer_has_audit_read(self):
        assert Permission.AUDIT_READ in ROLE_PERMISSIONS[Role.DEVELOPER]

    def test_developer_lacks_system_admin(self):
        assert Permission.SYSTEM_ADMIN not in ROLE_PERMISSIONS[Role.DEVELOPER]

    def test_user_lacks_audit_read(self):
        assert Permission.AUDIT_READ not in ROLE_PERMISSIONS[Role.USER]

    def test_guest_only_has_two_permissions(self):
        guest_perms = ROLE_PERMISSIONS[Role.GUEST]
        assert Permission.COMPONENT_READ in guest_perms
        assert Permission.TEMPLATE_READ in guest_perms
        assert len(guest_perms) == 2

    def test_all_roles_in_mapping(self):
        for role in Role:
            assert role in ROLE_PERMISSIONS

    def test_developer_has_tool_execute(self):
        assert Permission.TOOL_EXECUTE in ROLE_PERMISSIONS[Role.DEVELOPER]

    def test_user_has_tool_execute(self):
        assert Permission.TOOL_EXECUTE in ROLE_PERMISSIONS[Role.USER]


# ---------------------------------------------------------------------------
# RESOURCE_ACTION_MAP
# ---------------------------------------------------------------------------


class TestResourceActionMap:
    def test_tools_call_requires_tool_execute(self):
        assert RESOURCE_ACTION_MAP["tools/call"] == Permission.TOOL_EXECUTE

    def test_audit_events_requires_audit_read(self):
        assert RESOURCE_ACTION_MAP["audit/events"] == Permission.AUDIT_READ

    def test_system_admin_requires_system_admin(self):
        assert RESOURCE_ACTION_MAP["system/admin"] == Permission.SYSTEM_ADMIN

    def test_known_keys(self):
        assert "tools/list" in RESOURCE_ACTION_MAP
        assert "policies/read" in RESOURCE_ACTION_MAP
        assert "policies/write" in RESOURCE_ACTION_MAP


# ---------------------------------------------------------------------------
# AuthorizationError
# ---------------------------------------------------------------------------


class TestAuthorizationError:
    def test_default_status_code(self):
        err = AuthorizationError("denied")
        assert err.status_code == 403
        assert str(err) == "denied"

    def test_custom_status_code(self):
        err = AuthorizationError("forbidden", status_code=401)
        assert err.status_code == 401

    def test_is_exception(self):
        with pytest.raises(AuthorizationError):
            raise AuthorizationError("boom")


# ---------------------------------------------------------------------------
# AuthzResult
# ---------------------------------------------------------------------------


class TestAuthzResult:
    def test_basic(self):
        result = AuthzResult(allowed=True, role=Role.ADMIN)
        assert result.allowed is True
        assert result.role == Role.ADMIN
        assert result.required_permission is None
        assert result.reason is None

    def test_with_all_fields(self):
        result = AuthzResult(
            allowed=False,
            role=Role.GUEST,
            required_permission=Permission.AUDIT_READ,
            reason="denied",
        )
        assert result.allowed is False
        assert result.required_permission == Permission.AUDIT_READ
        assert result.reason == "denied"


# ---------------------------------------------------------------------------
# RBACEvaluator.resolve_role
# ---------------------------------------------------------------------------


class TestResolveRole:
    def setup_method(self):
        self.rbac = RBACEvaluator()

    def test_known_roles(self):
        assert self.rbac.resolve_role("admin") == Role.ADMIN
        assert self.rbac.resolve_role("developer") == Role.DEVELOPER
        assert self.rbac.resolve_role("user") == Role.USER
        assert self.rbac.resolve_role("guest") == Role.GUEST

    def test_case_insensitive(self):
        assert self.rbac.resolve_role("ADMIN") == Role.ADMIN
        assert self.rbac.resolve_role("Developer") == Role.DEVELOPER

    def test_unknown_role_defaults_to_guest(self):
        assert self.rbac.resolve_role("superuser") == Role.GUEST

    def test_none_defaults_to_guest(self):
        assert self.rbac.resolve_role(None) == Role.GUEST

    def test_empty_string_defaults_to_guest(self):
        assert self.rbac.resolve_role("") == Role.GUEST


# ---------------------------------------------------------------------------
# RBACEvaluator.check_permission
# ---------------------------------------------------------------------------


class TestCheckPermission:
    def setup_method(self):
        self.rbac = RBACEvaluator()

    def test_admin_has_all_permissions(self):
        for perm in Permission:
            assert self.rbac.check_permission(Role.ADMIN, perm) is True

    def test_developer_has_audit_read(self):
        assert self.rbac.check_permission(Role.DEVELOPER, Permission.AUDIT_READ) is True

    def test_user_lacks_audit_read(self):
        assert self.rbac.check_permission(Role.USER, Permission.AUDIT_READ) is False

    def test_guest_lacks_tool_execute(self):
        assert self.rbac.check_permission(Role.GUEST, Permission.TOOL_EXECUTE) is False

    def test_guest_has_component_read(self):
        assert self.rbac.check_permission(Role.GUEST, Permission.COMPONENT_READ) is True

    def test_disabled_rbac_allows_all(self):
        rbac = RBACEvaluator(config={"enabled": False})
        assert rbac.check_permission(Role.GUEST, Permission.SYSTEM_ADMIN) is True

    def test_enabled_config(self):
        rbac = RBACEvaluator(config={"enabled": True})
        assert rbac.check_permission(Role.GUEST, Permission.SYSTEM_ADMIN) is False


# ---------------------------------------------------------------------------
# RBACEvaluator.check_resource_access
# ---------------------------------------------------------------------------


class TestCheckResourceAccess:
    def setup_method(self):
        self.rbac = RBACEvaluator()

    def test_admin_tools_call_allowed(self):
        result = self.rbac.check_resource_access(Role.ADMIN, "tools", "call")
        assert result.allowed is True
        assert result.role == Role.ADMIN

    def test_guest_audit_events_denied(self):
        result = self.rbac.check_resource_access(Role.GUEST, "audit", "events")
        assert result.allowed is False
        assert result.required_permission == Permission.AUDIT_READ
        assert result.reason is not None

    def test_unknown_resource_allowed(self):
        result = self.rbac.check_resource_access(Role.GUEST, "unknown/resource")
        assert result.allowed is True
        assert result.reason == "No permission mapping for resource"

    def test_disabled_rbac_allows_all_resources(self):
        rbac = RBACEvaluator(config={"enabled": False})
        result = rbac.check_resource_access(Role.GUEST, "system", "admin")
        assert result.allowed is True

    def test_resource_without_action(self):
        result = self.rbac.check_resource_access(Role.DEVELOPER, "tools/call")
        assert result.allowed is True

    def test_allowed_result_has_no_reason(self):
        result = self.rbac.check_resource_access(Role.ADMIN, "audit", "events")
        assert result.allowed is True
        assert result.reason is None


# ---------------------------------------------------------------------------
# RBACEvaluator.require_permission
# ---------------------------------------------------------------------------


class TestRequirePermission:
    def setup_method(self):
        self.rbac = RBACEvaluator()

    def test_passes_for_admin(self):
        self.rbac.require_permission(Role.ADMIN, Permission.SYSTEM_ADMIN)

    def test_raises_for_guest(self):
        with pytest.raises(AuthorizationError) as exc_info:
            self.rbac.require_permission(Role.GUEST, Permission.AUDIT_READ)
        assert "audit:read" in str(exc_info.value)

    def test_developer_has_audit_read_no_raise(self):
        self.rbac.require_permission(Role.DEVELOPER, Permission.AUDIT_READ)


# ---------------------------------------------------------------------------
# RBACEvaluator.require_resource_access
# ---------------------------------------------------------------------------


class TestRequireResourceAccess:
    def setup_method(self):
        self.rbac = RBACEvaluator()

    def test_passes_for_admin(self):
        self.rbac.require_resource_access(Role.ADMIN, "audit", "events")

    def test_raises_for_guest_on_audit(self):
        with pytest.raises(AuthorizationError):
            self.rbac.require_resource_access(Role.GUEST, "audit", "events")

    def test_unknown_resource_no_raise(self):
        self.rbac.require_resource_access(Role.GUEST, "nonexistent")

    def test_reason_in_error(self):
        with pytest.raises(AuthorizationError) as exc_info:
            self.rbac.require_resource_access(Role.USER, "system", "admin")
        assert str(exc_info.value)  # non-empty message
