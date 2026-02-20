"""
Database Health Check for MCP Gateway
Provides health check endpoints for Supabase PostgreSQL connection.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from tool_router.database.supabase_client import get_database_client, close_database_client


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str
    database: str
    timestamp: str
    details: Dict[str, Any] = {}


class DatabaseHealthResponse(BaseModel):
    """Database health check response model."""
    
    status: str
    connection: str
    timestamp: str
    error: str | None = None


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.
    Returns overall system health status.
    """
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
                "connection": "connected" if db_health["database"] == "connected" else "disconnected"
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            database="disconnected",
            timestamp="unknown",
            details={"error": str(e)}
        )


@router.get("/database", response_model=DatabaseHealthResponse)
async def database_health() -> DatabaseHealthResponse:
    """
    Database-specific health check endpoint.
    Returns detailed database connection status.
    """
    try:
        db_client = await get_database_client()
        health = await db_client.health_check()
        
        return DatabaseHealthResponse(
            status=health["status"],
            connection=health["database"],
            timestamp=health["timestamp"],
            error=health.get("error")
        )
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Database health check failed: {str(e)}"
        )


@router.get("/readiness")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.
    Indicates if the service is ready to accept traffic.
    """
    try:
        db_client = await get_database_client()
        health = await db_client.health_check()
        
        is_ready = health["status"] == "healthy"
        
        return {
            "ready": is_ready,
            "checks": {
                "database": health["status"] == "healthy",
                "connection": health["database"] == "connected"
            },
            "timestamp": health["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "checks": {
                "database": False,
                "connection": False
            },
            "timestamp": "unknown",
            "error": str(e)
        }


@router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint.
    Indicates if the service is alive.
    """
    return {
        "alive": True,
        "timestamp": "2025-01-20T00:00:00Z"  # Will be updated with actual timestamp
    }


@router.post("/close")
async def close_connections() -> Dict[str, str]:
    """
    Close database connections.
    Useful for graceful shutdown.
    """
    try:
        await close_database_client()
        return {"status": "connections_closed"}
    except Exception as e:
        logger.error(f"Failed to close connections: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to close connections: {str(e)}"
        )
