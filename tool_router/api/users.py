"""Users API — exposes RBAC role catalog and permission matrix for the Admin UI."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from tool_router.security.authorization import ROLE_PERMISSIONS, Permission, RBACEvaluator, Role
from tool_router.security.security_middleware import SecurityContext

from .dependencies import get_security_context


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

_rbac = RBACEvaluator()


def _require_audit_read(
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
) -> SecurityContext:
    """Require AUDIT_READ or SYSTEM_ADMIN permission."""
    role: Role = _rbac.resolve_role(ctx.user_role)
    has_audit_read = _rbac.check_permission(role, Permission.AUDIT_READ)
    has_system_admin = _rbac.check_permission(role, Permission.SYSTEM_ADMIN)
    if not (has_audit_read or has_system_admin):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role.value}' does not have permission to view user roles.",
        )
    return ctx


class RoleEntry(BaseModel):
    """A gateway RBAC role with its associated permissions."""

    role: str = Field(description="Role identifier (admin, developer, user, guest)")
    display_name: str = Field(description="Human-readable role name")
    description: str = Field(description="What this role is intended for")
    permissions: list[str] = Field(description="List of permission strings granted to this role")
    permission_count: int = Field(description="Number of permissions granted")
    is_privileged: bool = Field(description="True for admin/developer roles with elevated access")


class UsersResponse(BaseModel):
    """RBAC role catalog for the Admin UI."""

    roles: list[RoleEntry] = Field(description="All configured roles with their permissions")
    total_roles: int = Field(description="Number of defined roles")
    total_permissions: int = Field(description="Total number of distinct permissions in the system")


_ROLE_META: dict[Role, tuple[str, str]] = {
    Role.ADMIN: (
        "Administrator",
        "Full system access. Can manage all resources, users, and configuration.",
    ),
    Role.DEVELOPER: (
        "Developer",
        "Read-only access to audit logs, policies, and monitoring data. Can execute tools.",
    ),
    Role.USER: (
        "User",
        "Standard user with component management and tool execution. No audit or policy access.",
    ),
    Role.GUEST: (
        "Guest",
        "Minimal read-only access to components and templates only.",
    ),
}

_PRIVILEGED_ROLES: frozenset[Role] = frozenset({Role.ADMIN, Role.DEVELOPER})


def _build_roles() -> list[RoleEntry]:
    entries: list[RoleEntry] = []
    for role in Role:
        display_name, description = _ROLE_META[role]
        perms = [p.value for p in ROLE_PERMISSIONS.get(role, [])]
        entries.append(
            RoleEntry(
                role=role.value,
                display_name=display_name,
                description=description,
                permissions=perms,
                permission_count=len(perms),
                is_privileged=role in _PRIVILEGED_ROLES,
            )
        )
    return entries


@router.get(
    "",
    response_model=UsersResponse,
    summary="Get RBAC role catalog",
    description=(
        "Returns all defined gateway roles with their permission sets. "
        "Use this endpoint to populate the access-control overview in the Admin UI. "
        "Requires AUDIT_READ or SYSTEM_ADMIN permission."
    ),
)
async def get_users(
    _ctx: Annotated[SecurityContext, Depends(_require_audit_read)],
) -> UsersResponse:
    roles = _build_roles()
    all_permissions = set(p.value for p in Permission)
    return UsersResponse(
        roles=roles,
        total_roles=len(roles),
        total_permissions=len(all_permissions),
    )
