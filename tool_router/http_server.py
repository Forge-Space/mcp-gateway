"""HTTP server for tool router with JSON-RPC endpoint."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tool_router.api.rpc_handler import init_rpc_security
from tool_router.api.rpc_handler import router as rpc_router


logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Tool Router HTTP API",
    description="HTTP interface for Tool Router MCP Gateway",
    version="1.0.0",
)

# Add CORS middleware
allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register JSON-RPC endpoint
app.include_router(rpc_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Tool Router HTTP API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "tool-router",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "1.0.0",
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"ready": True, "timestamp": datetime.now(UTC).isoformat()}


@app.get("/live")
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
