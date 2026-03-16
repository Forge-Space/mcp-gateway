"""Security statistics API — aggregates audit and policy data for Admin UI."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from tool_router.security.authorization import Permission, RBACEvaluator, Role
from tool_router.security.security_middleware import SecurityContext

from .dependencies import get_security_context


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["security"])

_rbac = RBACEvaluator()


def _require_security_read(
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
) -> SecurityContext:
    """Validate that the caller has AUDIT_READ or SYSTEM_ADMIN permission.

    Args:
        ctx: Resolved security context from the JWT bearer token.

    Returns:
        The validated SecurityContext when permission is granted.

    Raises:
        HTTPException(403): When the caller's role lacks the required permission.
        HTTPException(401): When no valid JWT is present.
    """
    role: Role = _rbac.resolve_role(ctx.user_role)
    has_audit_read = _rbac.check_permission(role, Permission.AUDIT_READ)
    has_system_admin = _rbac.check_permission(role, Permission.SYSTEM_ADMIN)
    if not (has_audit_read or has_system_admin):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role.value}' does not have permission to view security stats.",
        )
    return ctx


def _get_audit_logger():
    """Get the SecurityAuditLogger singleton."""
    from tool_router.security.audit_logger import SecurityAuditLogger

    return SecurityAuditLogger()


def _derive_policy_status() -> list[dict[str, Any]]:
    """Derive security policy statuses from environment/config."""
    now = datetime.now(UTC).isoformat()

    jwt_secret = os.getenv("JWT_SECRET") or os.getenv("SUPABASE_JWT_SECRET") or os.getenv("SUPABASE_URL")
    jwt_active = bool(jwt_secret)

    redis_url = os.getenv("REDIS_URL")
    rate_limit_active = bool(redis_url)

    encryption_key = os.getenv("ENCRYPTION_KEY") or os.getenv("DATA_ENCRYPTION_KEY")
    encryption_active = bool(encryption_key)

    return [
        {
            "name": "JWT Authentication",
            "status": "active" if jwt_active else "inactive",
            "description": "JWT-based authentication for API requests",
            "last_updated": now,
        },
        {
            "name": "Rate Limiting",
            "status": "active" if rate_limit_active else "inactive",
            "description": "Redis-backed rate limiting to prevent abuse",
            "last_updated": now,
        },
        {
            "name": "Data Encryption",
            "status": "active" if encryption_active else "inactive",
            "description": "Encryption at rest for sensitive data",
            "last_updated": now,
        },
    ]


class VulnerabilityCounts(BaseModel):
    critical: int = Field(default=0, description="Critical severity vulnerability count")
    high: int = Field(default=0, description="High severity vulnerability count")
    medium: int = Field(default=0, description="Medium severity vulnerability count")
    low: int = Field(default=0, description="Low severity vulnerability count")


class SecurityPolicy(BaseModel):
    name: str = Field(description="Policy name")
    status: str = Field(description="Policy status: active or inactive")
    description: str = Field(description="Policy description")
    last_updated: str = Field(description="ISO 8601 timestamp of last update")


class SecurityStatsResponse(BaseModel):
    """Aggregated security statistics for the Admin UI."""

    vulnerabilities: VulnerabilityCounts = Field(description="Vulnerability counts by severity")
    compliance_score: float = Field(description="Compliance score 0-100 based on active policies")
    policies: list[SecurityPolicy] = Field(description="Security policy statuses")
    last_updated: str = Field(description="ISO 8601 timestamp of this response")


@router.get(
    "/stats",
    response_model=SecurityStatsResponse,
    summary="Get security statistics",
    description=(
        "Aggregates audit summary and security policy statuses. Requires AUDIT_READ or SYSTEM_ADMIN permission."
    ),
)
async def get_security_stats(
    _ctx: Annotated[SecurityContext, Depends(_require_security_read)],
) -> SecurityStatsResponse:
    audit_logger = _get_audit_logger()

    try:
        summary: dict[str, Any] = audit_logger.get_security_summary()
    except Exception as exc:
        logger.error("Failed to retrieve security summary: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve security summary",
        ) from exc

    vulnerabilities = VulnerabilityCounts(
        critical=summary.get("critical_events", 0),
        high=summary.get("high_risk_events", 0),
        medium=0,
        low=0,
    )

    policies_raw = _derive_policy_status()
    policies = [SecurityPolicy(**p) for p in policies_raw]

    total = len(policies)
    active = sum(1 for p in policies if p.status == "active")
    compliance_score = round((active / total) * 100, 2) if total > 0 else 0.0

    return SecurityStatsResponse(
        vulnerabilities=vulnerabilities,
        compliance_score=compliance_score,
        policies=policies,
        last_updated=datetime.now(UTC).isoformat(),
    )
