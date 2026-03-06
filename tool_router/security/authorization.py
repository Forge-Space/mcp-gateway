"""RBAC authorization evaluator for MCP Gateway."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


logger = logging.getLogger(__name__)


class Role(StrEnum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"
    GUEST = "guest"


class Permission(StrEnum):
    COMPONENT_READ = "component:read"
    COMPONENT_CREATE = "component:create"
    COMPONENT_UPDATE = "component:update"
    COMPONENT_DELETE = "component:delete"
    TEMPLATE_READ = "template:read"
    TEMPLATE_CREATE = "template:create"
    TEMPLATE_UPDATE = "template:update"
    TEMPLATE_DELETE = "template:delete"
    SYSTEM_READ = "system:read"
    SYSTEM_ADMIN = "system:admin"
    USER_MANAGE = "user:manage"
    AUDIT_READ = "audit:read"
    POLICY_READ = "policy:read"
    POLICY_WRITE = "policy:write"
    SCORECARD_READ = "scorecard:read"
    TOOL_EXECUTE = "tool:execute"


ROLE_PERMISSIONS: dict[Role, list[Permission]] = {
    Role.ADMIN: list(Permission),
    Role.DEVELOPER: [
        Permission.COMPONENT_READ,
        Permission.COMPONENT_CREATE,
        Permission.COMPONENT_UPDATE,
        Permission.TEMPLATE_READ,
        Permission.TEMPLATE_CREATE,
        Permission.SYSTEM_READ,
        Permission.AUDIT_READ,
        Permission.POLICY_READ,
        Permission.SCORECARD_READ,
        Permission.TOOL_EXECUTE,
    ],
    Role.USER: [
        Permission.COMPONENT_READ,
        Permission.COMPONENT_CREATE,
        Permission.COMPONENT_UPDATE,
        Permission.TEMPLATE_READ,
        Permission.SCORECARD_READ,
        Permission.TOOL_EXECUTE,
    ],
    Role.GUEST: [
        Permission.COMPONENT_READ,
        Permission.TEMPLATE_READ,
    ],
}

RESOURCE_ACTION_MAP: dict[str, Permission] = {
    "tools/call": Permission.TOOL_EXECUTE,
    "tools/list": Permission.COMPONENT_READ,
    "audit/events": Permission.AUDIT_READ,
    "policies/read": Permission.POLICY_READ,
    "policies/write": Permission.POLICY_WRITE,
    "scorecards/read": Permission.SCORECARD_READ,
    "system/admin": Permission.SYSTEM_ADMIN,
    "users/manage": Permission.USER_MANAGE,
}


class AuthorizationError(Exception):
    """Raised when RBAC check fails."""

    def __init__(self, message: str, status_code: int = 403):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class AuthzResult:
    """Result of an authorization check."""

    allowed: bool
    role: Role
    required_permission: Permission | None = None
    reason: str | None = None


class RBACEvaluator:
    """Role-based access control evaluator."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.enabled = True
        if config:
            self.enabled = config.get("enabled", True)

    def resolve_role(self, role_str: str | None) -> Role:
        """Resolve a string role to the Role enum, defaulting to GUEST."""
        if not role_str:
            return Role.GUEST
        try:
            return Role(role_str.lower())
        except ValueError:
            logger.warning("Unknown role '%s', defaulting to GUEST", role_str)
            return Role.GUEST

    def check_permission(
        self,
        user_role: Role,
        permission: Permission,
    ) -> bool:
        """Check if a role has the given permission."""
        if not self.enabled:
            return True
        allowed_permissions = ROLE_PERMISSIONS.get(user_role, [])
        return permission in allowed_permissions

    def check_resource_access(
        self,
        user_role: Role,
        resource: str,
        action: str | None = None,
    ) -> AuthzResult:
        """Check access to a resource/action pair."""
        if not self.enabled:
            return AuthzResult(allowed=True, role=user_role)

        lookup_key = f"{resource}/{action}" if action else resource
        required = RESOURCE_ACTION_MAP.get(lookup_key)

        if required is None:
            required = RESOURCE_ACTION_MAP.get(resource)

        if required is None:
            return AuthzResult(
                allowed=True,
                role=user_role,
                reason="No permission mapping for resource",
            )

        allowed = self.check_permission(user_role, required)
        return AuthzResult(
            allowed=allowed,
            role=user_role,
            required_permission=required,
            reason=None if allowed else f"Role {user_role.value} lacks {required.value}",
        )

    def require_permission(
        self,
        user_role: Role,
        permission: Permission,
    ) -> None:
        """Raise AuthorizationError if permission check fails."""
        if not self.check_permission(user_role, permission):
            raise AuthorizationError(f"Insufficient permissions: {permission.value} required")

    def require_resource_access(
        self,
        user_role: Role,
        resource: str,
        action: str | None = None,
    ) -> None:
        """Raise AuthorizationError if resource access check fails."""
        result = self.check_resource_access(user_role, resource, action)
        if not result.allowed:
            raise AuthorizationError(result.reason or "Access denied")
