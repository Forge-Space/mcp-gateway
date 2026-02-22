#!/usr/bin/env python3
"""
Production Health Check Service for Forge MCP Gateway
Monitors all services and provides aggregated health status.
"""

import asyncio
import aiohttp
import argparse
import json
import logging
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class HealthCheckResult:
    """Health check result for a service."""
    service_name: str
    status: str  # "healthy", "unhealthy", "unknown"
    response_time_ms: float
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class HealthStatus(BaseModel):
    """Health status response model."""
    overall_status: str
    timestamp: datetime
    services: List[HealthCheckResult]
    uptime_seconds: float
    version: str = "1.0.0"

class HealthChecker:
    """Health checker for Forge MCP Gateway services."""

    def __init__(self):
        self.start_time = time.time()
        self.services = {
            "gateway": os.getenv("GATEWAY_URL", "http://gateway:8000"),
            "service_manager": os.getenv("SERVICE_MANAGER_URL", "http://service-manager:8000"),
            "tool_router": os.getenv("TOOL_ROUTER_URL", "http://tool-router:8000"),
            "postgres": os.getenv("POSTGRES_URL", "postgresql://forge_user:password@postgres:5432/forge_mcp_prod"),
            "redis": os.getenv("REDIS_URL", "redis://:password@redis:6379")
        }
        self.check_interval = int(os.getenv("CHECK_INTERVAL", "30"))
        self.timeout = int(os.getenv("HEALTH_CHECK_TIMEOUT", "10"))

    async def check_http_service(self, name: str, url: str) -> HealthCheckResult:
        """Check HTTP service health."""
        start_time = time.time()

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{url}/health") as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        return HealthCheckResult(
                            service_name=name,
                            status="healthy",
                            response_time_ms=response_time
                        )
                    else:
                        return HealthCheckResult(
                            service_name=name,
                            status="unhealthy",
                            response_time_ms=response_time,
                            error_message=f"HTTP {response.status}"
                        )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=name,
                status="unhealthy",
                response_time_ms=response_time,
                error_message=str(e)
            )

    async def check_postgres(self, name: str, url: str) -> HealthCheckResult:
        """Check PostgreSQL health."""
        start_time = time.time()

        try:
            # Simple connection test using psycopg2 if available
            import psycopg2

            response_time = (time.time() - start_time) * 1000

            conn = psycopg2.connect(url)
            conn.close()

            return HealthCheckResult(
                service_name=name,
                status="healthy",
                response_time_ms=response_time
            )
        except ImportError:
            # Fallback to netcat if psycopg2 not available
            try:
                import socket

                # Parse URL to get host and port
                if "@" in url:
                    url = url.split("@")[1]
                host, port = url.split(":")
                port = int(port)

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                result = sock.connect_ex((host, port))
                sock.close()

                response_time = (time.time() - start_time) * 1000

                if result == 0:
                    return HealthCheckResult(
                        service_name=name,
                        status="healthy",
                        response_time_ms=response_time
                    )
                else:
                    return HealthCheckResult(
                        service_name=name,
                        status="unhealthy",
                        response_time_ms=response_time,
                        error_message="Connection refused"
                    )
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return HealthCheckResult(
                    service_name=name,
                    status="unhealthy",
                    response_time_ms=response_time,
                    error_message=str(e)
                )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=name,
                status="unhealthy",
                response_time_ms=response_time,
                error_message=str(e)
            )

    async def check_redis(self, name: str, url: str) -> HealthCheckResult:
        """Check Redis health."""
        start_time = time.time()

        try:
            import redis

            response_time = (time.time() - start_time) * 1000

            r = redis.from_url(url)
            r.ping()

            return HealthCheckResult(
                service_name=name,
                status="healthy",
                response_time_ms=response_time
            )
        except ImportError:
            # Fallback to netcat if redis not available
            try:
                import socket

                # Parse URL to get host and port
                if "@" in url:
                    url = url.split("@")[1]
                if "://" in url:
                    url = url.split("://")[1]
                host, port = url.split(":")
                port = int(port)

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                result = sock.connect_ex((host, port))
                sock.close()

                response_time = (time.time() - start_time) * 1000

                if result == 0:
                    return HealthCheckResult(
                        service_name=name,
                        status="healthy",
                        response_time_ms=response_time
                    )
                else:
                    return HealthCheckResult(
                        service_name=name,
                        status="unhealthy",
                        response_time_ms=response_time,
                        error_message="Connection refused"
                    )
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return HealthCheckResult(
                    service_name=name,
                    status="unhealthy",
                    response_time_ms=response_time,
                    error_message=str(e)
                )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=name,
                status="unhealthy",
                response_time_ms=response_time,
                error_message=str(e)
            )

    async def check_service(self, name: str, url: str) -> HealthCheckResult:
        """Check service health based on service type."""
        if name in ["gateway", "service_manager", "tool_router"]:
            return await self.check_http_service(name, url)
        elif name == "postgres":
            return await self.check_postgres(name, url)
        elif name == "redis":
            return await self.check_redis(name, url)
        else:
            return HealthCheckResult(
                service_name=name,
                status="unknown",
                response_time_ms=0.0,
                error_message="Unknown service type"
            )

    async def check_all_services(self) -> List[HealthCheckResult]:
        """Check all services health."""
        tasks = []

        for name, url in self.services.items():
            tasks.append(self.check_service(name, url))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to health check results
        health_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = list(self.services.keys())[i]
                health_results.append(HealthCheckResult(
                    service_name=service_name,
                    status="unhealthy",
                    response_time_ms=0.0,
                    error_message=str(result)
                ))
            else:
                health_results.append(result)

        return health_results

    def get_overall_status(self, results: List[HealthCheckResult]) -> str:
        """Get overall system status."""
        if not results:
            return "unknown"

        healthy_count = sum(1 for r in results if r.status == "healthy")
        total_count = len(results)

        if healthy_count == total_count:
            return "healthy"
        elif healthy_count > 0:
            return "degraded"
        else:
            return "unhealthy"

# FastAPI application
app = FastAPI(title="Forge MCP Gateway Health Check", version="1.0.0")
health_checker = HealthChecker()

@app.get("/health")
async def health_check():
    """Get overall system health."""
    try:
        results = await health_checker.check_all_services()
        overall_status = health_checker.get_overall_status(results)
        uptime = time.time() - health_checker.start_time

        return HealthStatus(
            overall_status=overall_status,
            timestamp=datetime.utcnow(),
            services=results,
            uptime_seconds=uptime
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/{service_name}")
async def service_health_check(service_name: str):
    """Get health status for a specific service."""
    if service_name not in health_checker.services:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    try:
        result = await health_checker.check_service(
            service_name,
            health_checker.services[service_name]
        )
        return result
    except Exception as e:
        logger.error(f"Service health check failed for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Get health check metrics."""
    results = await health_checker.check_all_services()

    metrics = {
        "total_services": len(results),
        "healthy_services": sum(1 for r in results if r.status == "healthy"),
        "unhealthy_services": sum(1 for r in results if r.status == "unhealthy"),
        "average_response_time_ms": sum(r.response_time_ms for r in results) / len(results) if results else 0,
        "uptime_seconds": time.time() - health_checker.start_time,
        "timestamp": datetime.utcnow().isoformat()
    }

    return metrics

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Forge MCP Gateway Health Check",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "service_health": "/health/{service_name}",
            "metrics": "/metrics"
        }
    }

async def self_check():
    """Self health check."""
    try:
        # Test basic functionality
        results = await health_checker.check_all_services()
        return len(results) > 0
    except Exception:
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Forge MCP Gateway Health Check Service")
    parser.add_argument("--server", action="store_true", help="Run as HTTP server")
    parser.add_argument("--check", action="store_true", help="Run health check once")
    parser.add_argument("--self-check", action="store_true", help="Run self health check")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP server")
    parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP server")

    args = parser.parse_args()

    if args.self_check:
        # Run self check
        result = asyncio.run(self_check())
        sys.exit(0 if result else 1)

    elif args.check:
        # Run health check once
        async def run_check():
            results = await health_checker.check_all_services()
            overall_status = health_checker.get_overall_status(results)

            print(f"\n{'='*50}")
            print(f"Forge MCP Gateway Health Check Results")
            print(f"{'='*50}")
            print(f"Overall Status: {overall_status.upper()}")
            print(f"Timestamp: {datetime.utcnow().isoformat()}")
            print(f"\nServices:")

            for result in results:
                status_icon = "✅" if result.status == "healthy" else "❌"
                print(f"  {status_icon} {result.service_name}: {result.status}")
                if result.error_message:
                    print(f"    Error: {result.error_message}")
                print(f"    Response Time: {result.response_time_ms:.1f}ms")

            print(f"\nSummary:")
            print(f"  Total Services: {len(results)}")
            print(f"  Healthy: {sum(1 for r in results if r.status == 'healthy')}")
            print(f"  Unhealthy: {sum(1 for r in results if r.status == 'unhealthy')}")
            print(f"{'='*50}")

            return overall_status == "healthy"

        success = asyncio.run(run_check())
        sys.exit(0 if success else 1)

    elif args.server:
        # Run HTTP server
        logger.info(f"Starting health check server on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
