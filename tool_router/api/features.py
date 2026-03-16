"""Feature flags API — exposes runtime feature states derived from environment configuration."""

from __future__ import annotations

import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from tool_router.security.authorization import Permission, RBACEvaluator, Role
from tool_router.security.security_middleware import SecurityContext

from .dependencies import get_security_context


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/features", tags=["features"])

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
            detail=f"Role '{role.value}' does not have permission to view feature flags.",
        )
    return ctx


class FeatureFlag(BaseModel):
    name: str = Field(description="Feature flag identifier (e.g. mcp-gateway.rate-limiting)")
    description: str = Field(description="Human-readable description of the feature")
    enabled: bool = Field(description="Whether the feature is currently enabled")
    category: str = Field(description="Feature category: global, mcp-gateway, uiforge-mcp, uiforge-webapp")
    source: str = Field(description="Config source: env, default")


class FeaturesResponse(BaseModel):
    """Feature flags for the Admin UI."""

    features: list[FeatureFlag] = Field(description="List of all feature flags with current state")
    total: int = Field(description="Total number of feature flags")
    enabled_count: int = Field(description="Number of enabled feature flags")


def _resolve_features() -> list[FeatureFlag]:
    """Derive feature flag states from environment variables and defaults."""

    def env_bool(key: str, default: bool = False) -> tuple[bool, str]:
        val = os.getenv(key)
        if val is None:
            return default, "default"
        return val.lower() in ("1", "true", "yes", "on"), "env"

    flags_config = [
        (
            "global.debug-mode",
            "Enable debug logging and monitoring",
            "global",
            "DEBUG",
            False,
        ),
        (
            "global.beta-features",
            "Enable beta functionality across all services",
            "global",
            "BETA_FEATURES",
            False,
        ),
        (
            "global.enhanced-logging",
            "Enable detailed structured logging",
            "global",
            "ENHANCED_LOGGING",
            True,
        ),
        (
            "mcp-gateway.rate-limiting",
            "Request rate limiting via Redis",
            "mcp-gateway",
            "RATE_LIMITING_ENABLED",
            bool(os.getenv("REDIS_URL")),
        ),
        (
            "mcp-gateway.security-headers",
            "Security headers middleware (CORS, CSP, HSTS)",
            "mcp-gateway",
            "SECURITY_HEADERS_ENABLED",
            True,
        ),
        (
            "mcp-gateway.performance-monitoring",
            "OpenTelemetry performance monitoring",
            "mcp-gateway",
            "OTEL_ENABLED",
            bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or os.getenv("OTEL_SERVICE_NAME")),
        ),
        (
            "mcp-gateway.cache-layer",
            "Multi-tier caching layer (memory + Redis)",
            "mcp-gateway",
            "CACHE_ENABLED",
            True,
        ),
        (
            "uiforge-mcp.ai-chat",
            "AI-powered chat functionality in UIForge MCP",
            "uiforge-mcp",
            "AI_CHAT_ENABLED",
            False,
        ),
        (
            "uiforge-mcp.template-management",
            "Virtual server template management",
            "uiforge-mcp",
            "TEMPLATE_MANAGEMENT_ENABLED",
            True,
        ),
        (
            "uiforge-webapp.dark-mode",
            "Dark mode theme support in the Admin UI",
            "uiforge-webapp",
            "DARK_MODE_ENABLED",
            False,
        ),
        (
            "uiforge-webapp.advanced-analytics",
            "Advanced analytics dashboard with gateway metrics",
            "uiforge-webapp",
            "ADVANCED_ANALYTICS_ENABLED",
            True,
        ),
    ]

    result: list[FeatureFlag] = []
    for name, description, category, env_key, default in flags_config:
        enabled, source = env_bool(env_key, default)
        result.append(
            FeatureFlag(
                name=name,
                description=description,
                enabled=enabled,
                category=category,
                source=source,
            )
        )
    return result


@router.get(
    "",
    response_model=FeaturesResponse,
    summary="Get feature flags",
    description=(
        "Returns all feature flags with their current state derived from environment variables "
        "and default configuration. Requires AUDIT_READ or SYSTEM_ADMIN permission."
    ),
)
async def get_features(
    _ctx: Annotated[SecurityContext, Depends(_require_audit_read)],
) -> FeaturesResponse:
    features = _resolve_features()
    return FeaturesResponse(
        features=features,
        total=len(features),
        enabled_count=sum(1 for f in features if f.enabled),
    )
