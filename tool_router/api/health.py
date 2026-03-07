"""
Database Health Check for MCP Gateway
Provides health check endpoints for Supabase PostgreSQL connection.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tool_router.database.supabase_client import (
    close_database_client,
    get_database_client,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Overall system health status."""

    status: str = Field(description="System status: healthy or unhealthy")
    database: str = Field(description="Database connection: connected or disconnected")
    timestamp: str = Field(description="ISO 8601 timestamp")
    details: dict[str, Any] = Field(default_factory=dict, description="Component-level status details")


class DatabaseHealthResponse(BaseModel):
    """Database connection health details."""

    status: str = Field(description="Database status: healthy or unhealthy")
    connection: str = Field(description="Connection state: connected or disconnected")
    timestamp: str = Field(description="ISO 8601 timestamp")
    error: str | None = Field(default=None, description="Error message if unhealthy")


class ReadinessResponse(BaseModel):
    """Service readiness for accepting traffic."""

    ready: bool = Field(description="Whether the service is ready")
    checks: dict[str, bool] = Field(description="Individual readiness checks")
    timestamp: str = Field(description="ISO 8601 timestamp")
    error: str | None = Field(default=None, description="Error message if not ready")


class LivenessResponse(BaseModel):
    """Service liveness probe."""

    alive: bool = Field(default=True, description="Always true if the process is running")
    timestamp: str = Field(description="ISO 8601 timestamp")


class ConnectionStatusResponse(BaseModel):
    """Database connection close result."""

    status: str = Field(description="Result: connections_closed")


@router.get(
    "/",
    response_model=HealthResponse,
    summary="System health check",
    description="Returns overall health including database connectivity.",
)
async def health_check() -> HealthResponse:
    try:
        # Check database connection
        db_client = await get_database_client()
        db_health = await db_client.health_check()

        return HealthResponse(
            status="healthy" if db_health["status"] == "healthy" else "unhealthy",
            database=db_health["database"],
            timestamp=db_health["timestamp"],
            details={
                "database_status": db_health["status"],
                "connection": ("connected" if db_health["database"] == "connected" else "disconnected"),
            },
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            database="disconnected",
            timestamp="unknown",
            details={"error": str(e)},
        )


@router.get(
    "/database",
    response_model=DatabaseHealthResponse,
    summary="Database health check",
    description="Returns detailed database connection status.",
    responses={503: {"description": "Database connection failed"}},
)
async def database_health() -> DatabaseHealthResponse:
    try:
        db_client = await get_database_client()
        health = await db_client.health_check()

        return DatabaseHealthResponse(
            status=health["status"],
            connection=health["database"],
            timestamp=health["timestamp"],
            error=health.get("error"),
        )

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database health check failed: {e!s}")


@router.get(
    "/readiness",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Indicates if the service is ready to accept traffic. Used by orchestrators.",
)
async def readiness_check() -> dict[str, Any]:
    try:
        db_client = await get_database_client()
        health = await db_client.health_check()

        is_ready = health["status"] == "healthy"

        return {
            "ready": is_ready,
            "checks": {
                "database": health["status"] == "healthy",
                "connection": health["database"] == "connected",
            },
            "timestamp": health["timestamp"],
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "checks": {"database": False, "connection": False},
            "timestamp": "unknown",
            "error": str(e),
        }


@router.get(
    "/liveness",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description="Indicates if the process is alive. Used by orchestrators for restart decisions.",
)
async def liveness_check() -> dict[str, Any]:
    return {
        "alive": True,
        "timestamp": "2025-01-20T00:00:00Z",  # Will be updated with actual timestamp
    }


@router.post(
    "/close",
    response_model=ConnectionStatusResponse,
    summary="Close database connections",
    description="Gracefully close all database connections. Used during shutdown.",
    responses={500: {"description": "Failed to close connections"}},
)
async def close_connections() -> dict[str, str]:
    try:
        await close_database_client()
        return {"status": "connections_closed"}
    except Exception as e:
        logger.error(f"Failed to close connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to close connections: {e!s}")
