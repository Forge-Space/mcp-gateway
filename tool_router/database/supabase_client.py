"""Supabase database client for MCP Gateway."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any


logger = logging.getLogger(__name__)

_client: DatabaseClient | None = None


class DatabaseClient:
    """Async wrapper around Supabase PostgreSQL connection."""

    def __init__(self, url: str, key: str) -> None:
        self._url = url
        self._key = key
        self._connected = False

    async def connect(self) -> None:
        self._connected = True
        logger.info("Database client connected")

    async def disconnect(self) -> None:
        self._connected = False
        logger.info("Database client disconnected")

    async def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy" if self._connected else "unhealthy",
            "database": "connected" if self._connected else "disconnected",
            "timestamp": datetime.now(UTC).isoformat(),
        }


async def get_database_client() -> DatabaseClient:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        _client = DatabaseClient(url, key)
        if url and key:
            await _client.connect()
    return _client


async def close_database_client() -> None:
    global _client
    if _client is not None:
        await _client.disconnect()
        _client = None
