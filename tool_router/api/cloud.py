"""Multi-cloud provider management API endpoints.

Phase 4 Multi-Cloud:
  GET    /cloud/providers              — list all registered cloud providers
  GET    /cloud/providers/{name}       — get a single provider with health metrics
  POST   /cloud/providers              — register a new cloud provider
  DELETE /cloud/providers/{name}       — remove a cloud provider
  PATCH  /cloud/providers/{name}/enabled — toggle provider enabled/disabled
  GET    /cloud/health                 — aggregated health across all providers
  PATCH  /cloud/strategy               — change the routing strategy at runtime
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Path as FastAPIPath
from pydantic import BaseModel, Field

from tool_router.cloud.provider import CloudProvider
from tool_router.cloud.router import MultiCloudRouter, RoutingStrategy
from tool_router.core.config import CloudProviderConfig
from tool_router.security.authorization import Permission, RBACEvaluator, Role
from tool_router.security.security_middleware import SecurityContext

from .dependencies import get_security_context


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cloud", tags=["Multi-Cloud"])

_rbac = RBACEvaluator()

# Module-level router instance (shared across requests)
_multi_cloud_router = MultiCloudRouter()


# ── Auth dependency ───────────────────────────────────────────────────────────


def _require_admin(
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
) -> SecurityContext:
    """Require SYSTEM_ADMIN permission."""
    role: Role = _rbac.resolve_role(ctx.user_role)
    if not _rbac.check_permission(role, Permission.SYSTEM_ADMIN):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role.value}' does not have system admin permission.",
        )
    return ctx


# ── Models ────────────────────────────────────────────────────────────────────


class CloudProviderRequest(BaseModel):
    """Request body for registering a new cloud provider."""

    name: str = Field(..., min_length=1, max_length=64)
    cloud_type: str = Field(default="custom", pattern="^(aws|azure|gcp|custom)$")
    region: str = Field(default="us-east-1", min_length=1, max_length=64)
    url: str = Field(..., min_length=1)
    jwt: str | None = Field(default=None)
    priority: int = Field(default=0, ge=0, le=100)
    weight: float = Field(default=1.0, gt=0.0, le=100.0)
    enabled: bool = Field(default=True)
    timeout_ms: int = Field(default=30000, ge=100, le=300000)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_ms: int = Field(default=2000, ge=0, le=60000)
    tags: dict[str, str] = Field(default_factory=dict)


class CloudProviderResponse(BaseModel):
    """Response for a single cloud provider (no secrets)."""

    name: str
    cloud_type: str
    region: str
    url: str
    enabled: bool
    priority: int
    weight: float
    status: str
    tags: dict[str, str]


class CloudProviderHealthResponse(BaseModel):
    """Response for a provider with full health metrics."""

    name: str
    cloud_type: str
    region: str
    enabled: bool
    status: str
    priority: int
    weight: float
    metrics: dict[str, Any]
    tags: dict[str, str]


class CloudHealthSummaryResponse(BaseModel):
    """Aggregated health across all providers."""

    overall: str
    strategy: str
    total_providers: int
    healthy: int
    degraded: int
    unhealthy: int
    providers: list[dict[str, Any]]


class EnabledPatchRequest(BaseModel):
    enabled: bool


class StrategyPatchRequest(BaseModel):
    strategy: str = Field(..., pattern="^(failover|round_robin|latency_weighted|random)$")


class CloudProviderListResponse(BaseModel):
    providers: list[CloudProviderResponse]
    total: int


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_router() -> MultiCloudRouter:
    """Return the module-level MultiCloudRouter (injectable for tests)."""
    return _multi_cloud_router


def _provider_to_response(provider: CloudProvider) -> CloudProviderResponse:
    d = provider.to_dict()
    return CloudProviderResponse(**d)


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/providers", response_model=CloudProviderListResponse)
async def list_cloud_providers(
    _ctx: Annotated[SecurityContext, Depends(_require_admin)],
) -> CloudProviderListResponse:
    """List all registered cloud providers."""
    cloud_router = _get_router()
    providers = [_provider_to_response(p) for p in cloud_router.list_providers()]
    return CloudProviderListResponse(providers=providers, total=len(providers))


@router.get("/providers/{name}", response_model=CloudProviderHealthResponse)
async def get_cloud_provider(
    name: Annotated[str, FastAPIPath(min_length=1, max_length=64)],
    _ctx: Annotated[SecurityContext, Depends(_require_admin)],
) -> CloudProviderHealthResponse:
    """Get a single cloud provider with full health metrics."""
    cloud_router = _get_router()
    provider = cloud_router.get_provider(name)
    if provider is None:
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found.")
    health = provider.health_check()
    return CloudProviderHealthResponse(**health)


@router.post("/providers", response_model=CloudProviderResponse, status_code=201)
async def register_cloud_provider(
    body: CloudProviderRequest,
    _ctx: Annotated[SecurityContext, Depends(_require_admin)],
) -> CloudProviderResponse:
    """Register a new cloud provider endpoint."""
    cloud_router = _get_router()

    # Check for duplicate
    if cloud_router.get_provider(body.name) is not None:
        raise HTTPException(status_code=409, detail=f"Provider '{body.name}' already registered.")

    cfg = CloudProviderConfig(
        name=body.name,
        cloud_type=body.cloud_type,
        region=body.region,
        url=body.url,
        jwt=body.jwt,
        priority=body.priority,
        weight=body.weight,
        enabled=body.enabled,
        timeout_ms=body.timeout_ms,
        max_retries=body.max_retries,
        retry_delay_ms=body.retry_delay_ms,
        tags=body.tags,
    )
    gateway_config = cfg.to_gateway_config()

    provider = CloudProvider(
        name=body.name,
        cloud_type=body.cloud_type,
        region=body.region,
        config=gateway_config,
        priority=body.priority,
        weight=body.weight,
        enabled=body.enabled,
        tags=body.tags,
    )

    try:
        cloud_router.add_provider(provider)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    logger.info("Registered cloud provider via API: %s", body.name)
    return _provider_to_response(provider)


@router.delete("/providers/{name}", status_code=204)
async def remove_cloud_provider(
    name: Annotated[str, FastAPIPath(min_length=1, max_length=64)],
    _ctx: Annotated[SecurityContext, Depends(_require_admin)],
) -> None:
    """Remove a cloud provider from the registry."""
    cloud_router = _get_router()
    removed = cloud_router.remove_provider(name)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found.")
    logger.info("Removed cloud provider via API: %s", name)


@router.patch("/providers/{name}/enabled", response_model=CloudProviderResponse)
async def toggle_cloud_provider(
    name: Annotated[str, FastAPIPath(min_length=1, max_length=64)],
    body: EnabledPatchRequest,
    _ctx: Annotated[SecurityContext, Depends(_require_admin)],
) -> CloudProviderResponse:
    """Enable or disable a cloud provider."""
    cloud_router = _get_router()
    provider = cloud_router.get_provider(name)
    if provider is None:
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found.")
    provider.enabled = body.enabled
    logger.info("Provider '%s' enabled=%s via API", name, body.enabled)
    return _provider_to_response(provider)


@router.get("/health", response_model=CloudHealthSummaryResponse)
async def cloud_health(
    _ctx: Annotated[SecurityContext, Depends(_require_admin)],
) -> CloudHealthSummaryResponse:
    """Return aggregated health across all cloud providers."""
    cloud_router = _get_router()
    summary = cloud_router.health_summary()
    return CloudHealthSummaryResponse(**summary)


@router.patch("/strategy", response_model=dict)
async def update_routing_strategy(
    body: StrategyPatchRequest,
    _ctx: Annotated[SecurityContext, Depends(_require_admin)],
) -> dict[str, str]:
    """Change the routing strategy at runtime."""
    cloud_router = _get_router()
    strategy = RoutingStrategy(body.strategy)
    cloud_router.set_strategy(strategy)
    logger.info("Routing strategy changed to '%s' via API", body.strategy)
    return {"strategy": body.strategy, "status": "updated"}
