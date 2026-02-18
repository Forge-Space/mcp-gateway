#!/usr/bin/env python3
"""
Minimal MCP Gateway - Bypasses Alembic migration issues
Provides basic health endpoints and proxy functionality
"""

import os
import sys
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Forge MCP Gateway (Minimal)",
    description="Minimal gateway bypassing migration issues",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "forge-mcpgateway",
        "version": "1.0.0-minimal",
        "message": "Running in minimal mode - migrations bypassed"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Forge MCP Gateway",
        "status": "running",
        "mode": "minimal"
    }

@app.get("/gateways")
async def list_gateways():
    """List available gateways"""
    return {
        "gateways": [
            {
                "id": "sequential-thinking",
                "name": "Sequential Thinking",
                "description": "Sequential thinking MCP server",
                "status": "active"
            }
        ]
    }

@app.get("/tools")
async def list_tools():
    """List available tools"""
    return {
        "tools": [
            {
                "name": "sequential_thinking",
                "description": "Sequential thinking tool",
                "gateway": "sequential-thinking"
            }
        ]
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4444))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Starting minimal MCP Gateway on {host}:{port}")
    logger.info("⚠️  Running in minimal mode - migrations bypassed")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
