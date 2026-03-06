"""HTTP transport for MCP communication (existing behavior extracted)."""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from functools import partial
from typing import Any

from .transport import Transport


class HttpTransport(Transport):
    """MCP transport over HTTP for remote spokes."""

    def __init__(
        self,
        base_url: str,
        jwt: str,
        timeout_ms: int = 120_000,
        max_retries: int = 3,
        retry_delay_ms: int = 1000,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.jwt = jwt
        self._timeout = timeout_ms / 1000
        self._max_retries = max_retries
        self._retry_delay = retry_delay_ms / 1000
        self._connected = False

    async def start(self) -> None:
        self._connected = True

    async def stop(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    async def send(self, message: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/rpc"
        headers = {
            "Authorization": f"Bearer {self.jwt}",
            "Content-Type": "application/json",
        }
        data = json.dumps(message).encode()
        req = urllib.request.Request(url, headers=headers, method="POST", data=data)

        loop = asyncio.get_running_loop()
        last_error = None
        for attempt in range(self._max_retries):
            try:
                result = await loop.run_in_executor(
                    None,
                    partial(self._sync_request, req),
                )
                return result
            except urllib.error.HTTPError as e:
                if e.code >= 500 and attempt < self._max_retries - 1:
                    last_error = f"HTTP {e.code}"
                    await asyncio.sleep(self._retry_delay * (2**attempt))
                    continue
                try:
                    body = e.read().decode("utf-8")
                except (OSError, UnicodeDecodeError):
                    body = "<unreadable>"
                msg = f"HTTP {e.code}: {body}"
                raise ValueError(msg) from e
            except (
                urllib.error.URLError,
                TimeoutError,
            ) as e:
                last_error = str(e)
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2**attempt))
                    continue

        msg = f"Failed after {self._max_retries} attempts: {last_error}"
        raise ConnectionError(msg)

    def _sync_request(self, req: urllib.request.Request) -> dict[str, Any]:
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            return json.loads(resp.read().decode())
