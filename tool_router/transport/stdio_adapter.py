"""Stdio transport for MCP communication via stdin/stdout."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from .transport import Transport


logger = logging.getLogger(__name__)


class StdioTransport(Transport):
    """MCP transport over stdin/stdout for subprocess spokes."""

    def __init__(
        self,
        command: list[str],
        env: dict[str, str] | None = None,
        cwd: str | None = None,
    ) -> None:
        if not command or not command[0]:
            msg = "Command list must not be empty"
            raise ValueError(msg)
        self.command = command
        self.env = env
        self.cwd = cwd
        self._process: asyncio.subprocess.Process | None = None
        self._request_id = 0
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env,
            cwd=self.cwd,
        )
        logger.info(
            "Stdio transport started: %s (pid=%s)",
            " ".join(self.command),
            self._process.pid,
        )

    async def stop(self) -> None:
        if self._process and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except TimeoutError:
                self._process.kill()
                await self._process.wait()
            logger.info("Stdio transport stopped")
        self._process = None

    def is_connected(self) -> bool:
        return self._process is not None and self._process.returncode is None

    async def send(self, message: dict[str, Any]) -> dict[str, Any]:
        if not self._process or not self._process.stdin or not self._process.stdout:
            msg = "Stdio transport not started"
            raise ConnectionError(msg)

        async with self._lock:
            self._request_id += 1
            if "id" not in message:
                message["id"] = self._request_id

            payload = json.dumps(message) + "\n"
            self._process.stdin.write(payload.encode())
            await self._process.stdin.drain()

            line = await asyncio.wait_for(
                self._process.stdout.readline(),
                timeout=120.0,
            )

            if not line:
                msg = "Spoke process closed stdout"
                raise ConnectionError(msg)

            return json.loads(line.decode())
