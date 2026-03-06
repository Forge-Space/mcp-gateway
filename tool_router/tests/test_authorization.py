"""Tests for RBACEvaluator."""

from __future__ import annotations

import pytest

from tool_router.security.authorization import (
    ROLE_PERMISSIONS,
    AuthorizationError,
    AuthzResult,
    Permission,
    RBACEvaluator,
    Role,
)


@pytest.fixture
def evaluator() -> RBACEvaluator:
    """Create an enabled RBACEvaluator instance."""
    return RBACEvaluator(config={"enabled": True})


@pytest.fixture
def disabled_evaluator() -> RBACEvaluator:
    """Create a disabled RBACEvaluator instance."""
    return RBACEvaluator(config={"enabled": False})


def test_admin_has_all_permissions(evaluator: RBACEvaluator):
    """Test that admin role has all permissions."""
    admin_permissions = ROLE_PERMISSIONS[Role.ADMIN]
    assert len(admin_permissions) == len(Permission)

    for permission in Permission:
        assert evaluator.check_permission(Role.ADMIN, permission)


def test_developer_permissions(evaluator: RBACEvaluator):
    """Test developer role permissions."""
    assert evaluator.check_permission(Role.DEVELOPER, Permission.COMPONENT_READ)
    assert evaluator.check_permission(Role.DEVELOPER, Permission.COMPONENT_CREATE)
    assert evaluator.check_permission(Role.DEVELOPER, Permission.COMPONENT_UPDATE)
    assert evaluator.check_permission(Role.DEVELOPER, Permission.TEMPLATE_READ)
    assert evaluator.check_permission(Role.DEVELOPER, Permission.TEMPLATE_CREATE)
    assert evaluator.check_permission(Role.DEVELOPER, Permission.SYSTEM_READ)
    assert evaluator.check_permission(Role.DEVELOPER, Permission.AUDIT_READ)
    assert evaluator.check_permission(Role.DEVELOPER, Permission.POLICY_READ)
    assert evaluator.check_permission(Role.DEVELOPER, Permission.SCORECARD_READ)
    assert evaluator.check_permission(Role.DEVELOPER, Permission.TOOL_EXECUTE)

    assert not evaluator.check_permission(Role.DEVELOPER, Permission.COMPONENT_DELETE)
    assert not evaluator.check_permission(Role.DEVELOPER, Permission.TEMPLATE_DELETE)
    assert not evaluator.check_permission(Role.DEVELOPER, Permission.SYSTEM_ADMIN)
    assert not evaluator.check_permission(Role.DEVELOPER, Permission.USER_MANAGE)
    assert not evaluator.check_permission(Role.DEVELOPER, Permission.POLICY_WRITE)


def test_user_permissions(evaluator: RBACEvaluator):
    """Test user role permissions."""
    assert evaluator.check_permission(Role.USER, Permission.COMPONENT_READ)
    assert evaluator.check_permission(Role.USER, Permission.COMPONENT_CREATE)
    assert evaluator.check_permission(Role.USER, Permission.COMPONENT_UPDATE)
    assert evaluator.check_permission(Role.USER, Permission.TEMPLATE_READ)
    assert evaluator.check_permission(Role.USER, Permission.SCORECARD_READ)
    assert evaluator.check_permission(Role.USER, Permission.TOOL_EXECUTE)

    assert not evaluator.check_permission(Role.USER, Permission.COMPONENT_DELETE)
    assert not evaluator.check_permission(Role.USER, Permission.TEMPLATE_CREATE)
    assert not evaluator.check_permission(Role.USER, Permission.TEMPLATE_UPDATE)
    assert not evaluator.check_permission(Role.USER, Permission.SYSTEM_READ)
    assert not evaluator.check_permission(Role.USER, Permission.AUDIT_READ)
    assert not evaluator.check_permission(Role.USER, Permission.POLICY_READ)


def test_guest_only_read_permissions(evaluator: RBACEvaluator):
    """Test that guest role only has read permissions."""
    assert evaluator.check_permission(Role.GUEST, Permission.COMPONENT_READ)
    assert evaluator.check_permission(Role.GUEST, Permission.TEMPLATE_READ)

    assert not evaluator.check_permission(Role.GUEST, Permission.COMPONENT_CREATE)
    assert not evaluator.check_permission(Role.GUEST, Permission.COMPONENT_UPDATE)
    assert not evaluator.check_permission(Role.GUEST, Permission.COMPONENT_DELETE)
    assert not evaluator.check_permission(Role.GUEST, Permission.TEMPLATE_CREATE)
    assert not evaluator.check_permission(Role.GUEST, Permission.TEMPLATE_UPDATE)
    assert not evaluator.check_permission(Role.GUEST, Permission.TEMPLATE_DELETE)
    assert not evaluator.check_permission(Role.GUEST, Permission.SYSTEM_READ)
    assert not evaluator.check_permission(Role.GUEST, Permission.SYSTEM_ADMIN)
    assert not evaluator.check_permission(Role.GUEST, Permission.USER_MANAGE)
    assert not evaluator.check_permission(Role.GUEST, Permission.AUDIT_READ)
    assert not evaluator.check_permission(Role.GUEST, Permission.POLICY_READ)
    assert not evaluator.check_permission(Role.GUEST, Permission.POLICY_WRITE)
    assert not evaluator.check_permission(Role.GUEST, Permission.SCORECARD_READ)
    assert not evaluator.check_permission(Role.GUEST, Permission.TOOL_EXECUTE)


def test_resolve_role_valid(evaluator: RBACEvaluator):
    """Test resolve_role with valid role strings."""
    assert evaluator.resolve_role("admin") == Role.ADMIN
    assert evaluator.resolve_role("developer") == Role.DEVELOPER
    assert evaluator.resolve_role("user") == Role.USER
    assert evaluator.resolve_role("guest") == Role.GUEST


def test_resolve_role_unknown_defaults_to_guest(evaluator: RBACEvaluator):
    """Test that unknown role defaults to GUEST."""
    assert evaluator.resolve_role("unknown") == Role.GUEST
    assert evaluator.resolve_role("invalid_role") == Role.GUEST
    assert evaluator.resolve_role("") == Role.GUEST
    assert evaluator.resolve_role(None) == Role.GUEST


def test_require_permission_success(evaluator: RBACEvaluator):
    """Test require_permission does not raise when permission granted."""
    evaluator.require_permission(Role.ADMIN, Permission.SYSTEM_ADMIN)
    evaluator.require_permission(Role.DEVELOPER, Permission.COMPONENT_READ)
    evaluator.require_permission(Role.USER, Permission.TOOL_EXECUTE)


def test_require_permission_raises_authorization_error(evaluator: RBACEvaluator):
    """Test require_permission raises AuthorizationError on failure."""
    with pytest.raises(AuthorizationError) as exc_info:
        evaluator.require_permission(Role.GUEST, Permission.TOOL_EXECUTE)

    assert "Insufficient permissions" in str(exc_info.value)
    assert "tool:execute" in str(exc_info.value)
    assert exc_info.value.status_code == 403


def test_check_resource_access_tools_call(evaluator: RBACEvaluator):
    """Test check_resource_access for tools/call."""
    result = evaluator.check_resource_access(Role.DEVELOPER, "tools", "call")
    assert result.allowed
    assert result.role == Role.DEVELOPER
    assert result.required_permission == Permission.TOOL_EXECUTE

    result_guest = evaluator.check_resource_access(Role.GUEST, "tools", "call")
    assert not result_guest.allowed
    assert result_guest.role == Role.GUEST
    assert result_guest.required_permission == Permission.TOOL_EXECUTE
    assert "lacks tool:execute" in result_guest.reason


def test_check_resource_access_audit_events(evaluator: RBACEvaluator):
    """Test check_resource_access for audit/events."""
    result = evaluator.check_resource_access(Role.DEVELOPER, "audit", "events")
    assert result.allowed
    assert result.required_permission == Permission.AUDIT_READ

    result_user = evaluator.check_resource_access(Role.USER, "audit", "events")
    assert not result_user.allowed
    assert "lacks audit:read" in result_user.reason


def test_check_resource_access_policies_write(evaluator: RBACEvaluator):
    """Test check_resource_access for policies/write."""
    result = evaluator.check_resource_access(Role.ADMIN, "policies", "write")
    assert result.allowed
    assert result.required_permission == Permission.POLICY_WRITE

    result_dev = evaluator.check_resource_access(Role.DEVELOPER, "policies", "write")
    assert not result_dev.allowed
    assert "lacks policy:write" in result_dev.reason


def test_check_resource_access_unmapped_resource(evaluator: RBACEvaluator):
    """Test check_resource_access for unmapped resource allows access."""
    result = evaluator.check_resource_access(Role.GUEST, "unknown", "action")
    assert result.allowed
    assert result.required_permission is None
    assert "No permission mapping" in result.reason


def test_disabled_evaluator_allows_everything(disabled_evaluator: RBACEvaluator):
    """Test that disabled evaluator allows all permissions."""
    assert disabled_evaluator.check_permission(Role.GUEST, Permission.SYSTEM_ADMIN)
    assert disabled_evaluator.check_permission(Role.USER, Permission.USER_MANAGE)

    result = disabled_evaluator.check_resource_access(Role.GUEST, "tools", "call")
    assert result.allowed

    disabled_evaluator.require_permission(Role.GUEST, Permission.SYSTEM_ADMIN)


def test_require_resource_access_success(evaluator: RBACEvaluator):
    """Test require_resource_access does not raise when access granted."""
    evaluator.require_resource_access(Role.ADMIN, "policies", "write")
    evaluator.require_resource_access(Role.DEVELOPER, "tools", "call")


def test_require_resource_access_raises_authorization_error(evaluator: RBACEvaluator):
    """Test require_resource_access raises AuthorizationError on failure."""
    with pytest.raises(AuthorizationError) as exc_info:
        evaluator.require_resource_access(Role.GUEST, "tools", "call")

    assert "lacks tool:execute" in str(exc_info.value)
    assert exc_info.value.status_code == 403


def test_authz_result_structure():
    """Test AuthzResult dataclass structure."""
    result = AuthzResult(
        allowed=True,
        role=Role.DEVELOPER,
        required_permission=Permission.COMPONENT_READ,
        reason="Success",
    )

    assert result.allowed is True
    assert result.role == Role.DEVELOPER
    assert result.required_permission == Permission.COMPONENT_READ
    assert result.reason == "Success"


def test_all_roles_against_all_permissions(evaluator: RBACEvaluator):
    """Comprehensive test of all roles against all permissions."""
    test_cases = [
        (Role.ADMIN, Permission.COMPONENT_READ, True),
        (Role.ADMIN, Permission.COMPONENT_CREATE, True),
        (Role.ADMIN, Permission.COMPONENT_UPDATE, True),
        (Role.ADMIN, Permission.COMPONENT_DELETE, True),
        (Role.ADMIN, Permission.TEMPLATE_READ, True),
        (Role.ADMIN, Permission.TEMPLATE_CREATE, True),
        (Role.ADMIN, Permission.TEMPLATE_UPDATE, True),
        (Role.ADMIN, Permission.TEMPLATE_DELETE, True),
        (Role.ADMIN, Permission.SYSTEM_READ, True),
        (Role.ADMIN, Permission.SYSTEM_ADMIN, True),
        (Role.ADMIN, Permission.USER_MANAGE, True),
        (Role.ADMIN, Permission.AUDIT_READ, True),
        (Role.ADMIN, Permission.POLICY_READ, True),
        (Role.ADMIN, Permission.POLICY_WRITE, True),
        (Role.ADMIN, Permission.SCORECARD_READ, True),
        (Role.ADMIN, Permission.TOOL_EXECUTE, True),
        (Role.DEVELOPER, Permission.COMPONENT_DELETE, False),
        (Role.DEVELOPER, Permission.TEMPLATE_DELETE, False),
        (Role.DEVELOPER, Permission.SYSTEM_ADMIN, False),
        (Role.DEVELOPER, Permission.USER_MANAGE, False),
        (Role.DEVELOPER, Permission.POLICY_WRITE, False),
        (Role.USER, Permission.COMPONENT_DELETE, False),
        (Role.USER, Permission.TEMPLATE_CREATE, False),
        (Role.USER, Permission.SYSTEM_READ, False),
        (Role.USER, Permission.AUDIT_READ, False),
        (Role.USER, Permission.POLICY_READ, False),
        (Role.GUEST, Permission.COMPONENT_CREATE, False),
        (Role.GUEST, Permission.TOOL_EXECUTE, False),
        (Role.GUEST, Permission.SYSTEM_ADMIN, False),
    ]

    for role, permission, expected in test_cases:
        result = evaluator.check_permission(role, permission)
        assert result == expected, f"Expected {role.value} to {'have' if expected else 'not have'} {permission.value}"


def test_check_resource_access_without_action(evaluator: RBACEvaluator):
    """Test check_resource_access with only resource (no action)."""
    result = evaluator.check_resource_access(Role.DEVELOPER, "tools/call")
    assert result.allowed
    assert result.required_permission == Permission.TOOL_EXECUTE


def test_default_config_enables_evaluator():
    """Test that evaluator is enabled by default."""
    evaluator = RBACEvaluator()
    assert evaluator.enabled

    evaluator_none_config = RBACEvaluator(config=None)
    assert evaluator_none_config.enabled


def test_case_insensitive_role_resolution(evaluator: RBACEvaluator):
    """Test that role resolution is case insensitive."""
    assert evaluator.resolve_role("ADMIN") == Role.ADMIN
    assert evaluator.resolve_role("Admin") == Role.ADMIN
    assert evaluator.resolve_role("DeVeLoPeR") == Role.DEVELOPER
    assert evaluator.resolve_role("USER") == Role.USER
    assert evaluator.resolve_role("Guest") == Role.GUEST
