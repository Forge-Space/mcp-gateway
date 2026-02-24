"""Simple HTTP server for tool router health checks."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Tool Router HTTP API",
    description="HTTP interface for Tool Router MCP Gateway",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "timestamp": "2025-02-20T21:10:00Z",
        "version": "1.0.0",
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"ready": True, "timestamp": "2025-02-20T21:10:00Z"}


@app.get("/live")
async def liveness_check():
    """Liveness check endpoint."""
    return {"alive": True, "timestamp": "2025-02-20T21:10:00Z"}


def main() -> None:
    """Run the HTTP server."""
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Tool Router HTTP server on port 8030")

    uvicorn.run(app, host="0.0.0.0", port=8030, log_level="info")


if __name__ == "__main__":
    main()
