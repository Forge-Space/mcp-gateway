"""Abstract transport interface for MCP communication."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any


class TransportMode(StrEnum):
    HTTP = "http"
    STDIO = "stdio"


class Transport(ABC):
    """Abstract transport for MCP message exchange."""

    @abstractmethod
    async def send(self, message: dict[str, Any]) -> dict[str, Any]:
        """Send a JSON-RPC message and return the response."""

    @abstractmethod
    async def start(self) -> None:
        """Initialize the transport connection."""

    @abstractmethod
    async def stop(self) -> None:
        """Shut down the transport connection."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the transport is active."""
