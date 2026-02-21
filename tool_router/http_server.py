#!/usr/bin/env python3
"""
HTTP Server for Tool Router
Provides HTTP endpoints for tool routing functionality
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Tool Router Service",
    description="HTTP API for tool routing and selection",
    version="1.0.0"
)

# Pydantic models
class TaskRequest(BaseModel):
    task: str
    context: str | None = ""

class ToolResponse(BaseModel):
    success: bool
    result: str | None = None
    error: str | None = None

class ToolInfo(BaseModel):
    name: str
    description: str
    gateway: str

# Mock data for now (will be replaced with actual gateway calls)
MOCK_TOOLS = [
    {
        "name": "sequential-thinking",
        "description": "Sequential thinking and problem analysis",
        "gateway": "sequential-thinking"
    },
    {
        "name": "web-search",
        "description": "Search the web for information",
        "gateway": "brave-search"
    },
    {
        "name": "file-operations",
        "description": "File system operations and management",
        "gateway": "filesystem"
    }
]

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "tool-router",
        "version": "1.0.0"
    }

@app.get("/")
async def root() -> dict[str, object]:
    """Root endpoint"""
    return {
        "service": "Tool Router",
        "status": "running",
        "endpoints": [
            "/health",
            "/tools",
            "/execute",
            "/search"
        ]
    }

@app.get("/tools", response_model=list[ToolInfo])
async def list_tools() -> list[ToolInfo]:
    """List all available tools"""
    try:
        tools = [
            ToolInfo(name=tool["name"], description=tool["description"], gateway=tool["gateway"])
            for tool in MOCK_TOOLS
        ]
    except Exception as e:
        logger.exception("Error listing tools: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        return tools

@app.post("/execute", response_model=ToolResponse)
async def execute_task(request: TaskRequest) -> ToolResponse:
    """Execute a task using the best matching tool"""
    try:
        best_tool = MOCK_TOOLS[0]  # Pick first tool as mock
        result = ToolResponse(
            success=True,
            result=f"Executed '{best_tool['name']}' for task: {request.task}"
        )
    except Exception as e:
        logger.exception("Error executing task: %s", e)
        return ToolResponse(success=False, error=str(e))
    else:
        return result

@app.post("/search", response_model=list[ToolInfo])
async def search_tools(query: str) -> list[ToolInfo]:
    """Search for tools matching the query"""
    try:
        query_lower = query.lower()
        matching_tools = [
            ToolInfo(name=tool["name"], description=tool["description"], gateway=tool["gateway"])
            for tool in MOCK_TOOLS
            if query_lower in tool["name"].lower() or query_lower in tool["description"].lower()
        ]
    except Exception as e:
        logger.exception("Error searching tools: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        return matching_tools

if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8030"))

    logger.info("Starting Tool Router HTTP server on %s:%d", host, port)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
