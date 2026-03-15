"""HTTP server for tool router with JSON-RPC endpoint."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from scalar_fastapi import get_scalar_api_reference

from tool_router.api.ai_performance import router as ai_performance_router
from tool_router.api.audit import router as audit_router
from tool_router.api.cache_dashboard import router as cache_dashboard_router
from tool_router.api.cloud import router as cloud_router
from tool_router.api.health import router as health_router
from tool_router.api.metrics_export import metrics
from tool_router.api.metrics_export import router as metrics_router
from tool_router.api.performance import router as performance_router
from tool_router.api.rpc_handler import init_rpc_security
from tool_router.api.rpc_handler import router as rpc_router
from tool_router.api.server_mgmt import ide_router
from tool_router.api.server_mgmt import router as server_mgmt_router
from tool_router.api.streamable_http import router as mcp_router
from tool_router.middleware.request_logger import RequestLoggingMiddleware
from tool_router.observability.otel_setup import init_otel, instrument_fastapi


logger = logging.getLogger(__name__)

# Single-source the package version from pyproject.toml metadata
try:
    _SERVICE_VERSION = pkg_version("forge-mcp-gateway")
except PackageNotFoundError:
    _SERVICE_VERSION = "dev"

# Bootstrap OpenTelemetry (no-op when packages are absent)
init_otel()

# Create FastAPI app
app = FastAPI(
    title="Forge Space MCP Gateway",
    description=(
        "Central hub for the Forge Space IDP ecosystem. "
        "Provides JSON-RPC routing to MCP spokes, "
        "JWT authentication, RBAC, audit logging, "
        "and quality gates for AI-generated code."
    ),
    version=_SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "rpc", "description": "JSON-RPC 2.0 endpoints for MCP tool execution"},
        {"name": "audit", "description": "Audit trail for auth and tool call events"},
        {"name": "health", "description": "Health, readiness, and liveness probes"},
        {"name": "monitoring", "description": "Performance metrics and system stats"},
        {"name": "metrics", "description": "Prometheus-compatible metrics export"},
        {"name": "cache-dashboard", "description": "Cache performance analytics and alerts"},
        {"name": "Server Management", "description": "Virtual server enable/disable and listing"},
        {"name": "IDE Detection", "description": "Detect installed IDEs and their config paths"},
        {"name": "Multi-Cloud", "description": "Multi-cloud provider registry and routing strategy"},
        {"name": "AI Performance", "description": "AI selector performance metrics and provider analytics"},
    ],
)

# Add CORS middleware
_cors_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
allowed_origins = [o.strip() for o in _cors_env.split(",") if o.strip()] if _cors_env else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=bool(allowed_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register request logging middleware (before routers, toggled via REQUEST_LOGGING env)
app.add_middleware(RequestLoggingMiddleware)

# Instrument FastAPI with OpenTelemetry (no-op when packages are absent)
instrument_fastapi(app)

# Register routers
app.include_router(rpc_router)
app.include_router(audit_router)
app.include_router(health_router)
app.include_router(performance_router)
app.include_router(metrics_router)
app.include_router(mcp_router)
app.include_router(cache_dashboard_router)
app.include_router(server_mgmt_router)
app.include_router(ide_router)
app.include_router(cloud_router)
app.include_router(ai_performance_router)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    import time as _time

    start = _time.monotonic()
    response = await call_next(request)
    duration = _time.monotonic() - start
    metrics.record_request(request.method, request.url.path, response.status_code, duration)
    return response


class ServiceInfoResponse(BaseModel):
    """Service metadata and documentation links."""

    service: str = Field(description="Service name")
    version: str = Field(description="Semantic version")
    docs: str = Field(description="Path to Swagger UI")
    redoc: str = Field(description="Path to ReDoc UI")
    scalar: str = Field(description="Path to Scalar API reference")
    openapi: str = Field(description="Path to OpenAPI JSON spec")


class SimpleHealthResponse(BaseModel):
    """Quick health check result."""

    status: str = Field(description="Service status")
    service: str = Field(description="Service identifier")
    timestamp: str = Field(description="ISO 8601 timestamp")
    version: str = Field(description="Service version")


class ReadyResponse(BaseModel):
    """Readiness probe result."""

    ready: bool = Field(description="Whether the service is ready")
    timestamp: str = Field(description="ISO 8601 timestamp")


class AliveResponse(BaseModel):
    """Liveness probe result."""

    alive: bool = Field(description="Whether the service is alive")
    timestamp: str = Field(description="ISO 8601 timestamp")


@app.get("/api-docs", include_in_schema=False)
async def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


@app.get(
    "/",
    tags=["health"],
    response_model=ServiceInfoResponse,
    summary="Service info",
    description="Returns service metadata and documentation links.",
)
async def root():
    return {
        "service": "Forge Space MCP Gateway",
        "version": _SERVICE_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "scalar": "/api-docs",
        "openapi": "/openapi.json",
    }


@app.get(
    "/health",
    tags=["health"],
    response_model=SimpleHealthResponse,
    summary="Quick health check",
)
async def health_check():
    return {
        "status": "healthy",
        "service": "tool-router",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": _SERVICE_VERSION,
    }


@app.get(
    "/ready",
    tags=["health"],
    response_model=ReadyResponse,
    summary="Readiness probe",
)
async def readiness_check():
    return {"ready": True, "timestamp": datetime.now(UTC).isoformat()}


@app.get(
    "/live",
    tags=["health"],
    response_model=AliveResponse,
    summary="Liveness probe",
)
async def liveness_check():
    return {"alive": True, "timestamp": datetime.now(UTC).isoformat()}


@app.on_event("startup")
async def startup_init_security() -> None:
    from tool_router.security.audit_logger import SecurityAuditLogger
    from tool_router.security.security_middleware import SecurityMiddleware

    security_config = {
        "enabled": os.getenv("SECURITY_ENABLED", "true").lower() == "true",
        "strict_mode": os.getenv("SECURITY_STRICT", "false").lower() == "true",
        "validation_level": os.getenv("SECURITY_VALIDATION_LEVEL", "standard"),
        "rate_limiting": {
            "use_redis": bool(os.getenv("REDIS_URL")),
            "redis_url": os.getenv("REDIS_URL"),
        },
    }
    middleware = SecurityMiddleware(security_config)
    audit_logger = SecurityAuditLogger(enable_console=True)
    init_rpc_security(middleware, audit_logger)
    logger.info("RPC security middleware initialized")


def main() -> None:
    """Run the HTTP server."""
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Tool Router HTTP server on port 8030")

    uvicorn.run(app, host="0.0.0.0", port=8030, log_level="info")


if __name__ == "__main__":
    main()
