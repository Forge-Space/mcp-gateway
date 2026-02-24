from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2


def _headers(jwt: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
    }


def _make_request(url: str, jwt: str, method: str = "GET", data: bytes | None = None) -> dict[str, Any]:
    """Make HTTP request with retry logic for transient failures."""
    req = urllib.request.Request(url, headers=_headers(jwt), method=method)
    if data:
        req.data = data

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code >= 500:
                last_error = f"Gateway server error (HTTP {e.code})"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
            else:
                msg = f"Gateway HTTP error {e.code}: {e.read().decode()}"
                raise ValueError(msg)
        except urllib.error.URLError as e:
            last_error = f"Network error: {e.reason}"
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
        except TimeoutError:
            last_error = f"Request timeout after {DEFAULT_TIMEOUT}s"
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON response from gateway: {e}"
            raise ValueError(msg)

    msg = f"Failed after {MAX_RETRIES} attempts. Last error: {last_error}"
    raise ConnectionError(msg)


def get_tools() -> list[dict[str, Any]]:
    base = os.environ.get("GATEWAY_URL", "http://gateway:4444").rstrip("/")
    jwt = os.environ.get("GATEWAY_JWT", "")
    if not jwt:
        msg = "GATEWAY_JWT is not set"
        raise ValueError(msg)
    url = f"{base}/tools?limit=0&include_pagination=false"

    try:
        data = _make_request(url, jwt, method="GET")
    except (ValueError, ConnectionError) as e:
        msg = f"Failed to fetch tools: {e}"
        raise ValueError(msg) from e

    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "tools" in data:
        return data["tools"]
    return []


def call_tool(name: str, arguments: dict[str, Any]) -> str:
    base = os.environ.get("GATEWAY_URL", "http://gateway:4444").rstrip("/")
    jwt = os.environ.get("GATEWAY_JWT", "")
    if not jwt:
        msg = "GATEWAY_JWT is not set"
        raise ValueError(msg)
    url = f"{base}/rpc"
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }

    try:
        out = _make_request(url, jwt, method="POST", data=json.dumps(body).encode())
    except (ValueError, ConnectionError) as e:
        return f"Failed to call tool: {e}"

    if "error" in out:
        return f"Gateway error: {out['error']}"
    content = out.get("result", {}).get("content", [])
    texts = [c.get("text", "") for c in content if isinstance(c, dict) and "text" in c]
    return "\n".join(texts) if texts else json.dumps(out.get("result", {}))
