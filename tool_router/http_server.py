"""HTTP server for tool router with JSON-RPC endpoint."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tool_router.api.audit import router as audit_router
from tool_router.api.health import router as health_router
from tool_router.api.performance import router as performance_router
from tool_router.api.rpc_handler import init_rpc_security
from tool_router.api.rpc_handler import router as rpc_router


logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Forge Space MCP Gateway",
    description=(
        "Central hub for the Forge Space IDP ecosystem. "
        "Provides JSON-RPC routing to MCP spokes, "
        "JWT authentication, RBAC, audit logging, "
        "and quality gates for AI-generated code."
    ),
    version="1.8.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "rpc", "description": "JSON-RPC 2.0 endpoints for MCP tool execution"},
        {"name": "audit", "description": "Audit trail for auth and tool call events"},
        {"name": "health", "description": "Health, readiness, and liveness probes"},
        {"name": "monitoring", "description": "Performance metrics and system stats"},
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

# Register routers
app.include_router(rpc_router)
app.include_router(audit_router)
app.include_router(health_router)
app.include_router(performance_router)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint with links to API documentation."""
    return {
        "service": "Forge Space MCP Gateway",
        "version": "1.8.1",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "tool-router",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "1.0.0",
    }


@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness check endpoint."""
    return {"ready": True, "timestamp": datetime.now(UTC).isoformat()}


@app.get("/live", tags=["health"])
async def liveness_check():
    """Liveness check endpoint."""
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
