from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

DEFAULT_TIMEOUT = 30


def _headers(jwt: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
    }


def get_tools() -> list[dict[str, Any]]:
    base = os.environ.get("GATEWAY_URL", "http://gateway:4444").rstrip("/")
    jwt = os.environ.get("GATEWAY_JWT", "")
    if not jwt:
        raise ValueError("GATEWAY_JWT is not set")
    url = f"{base}/tools?limit=0&include_pagination=false"
    req = urllib.request.Request(url, headers=_headers(jwt), method="GET")
    with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
        data = json.loads(resp.read().decode())
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "tools" in data:
        return data["tools"]
    return []


def call_tool(name: str, arguments: dict[str, Any]) -> str:
    base = os.environ.get("GATEWAY_URL", "http://gateway:4444").rstrip("/")
    jwt = os.environ.get("GATEWAY_JWT", "")
    if not jwt:
        raise ValueError("GATEWAY_JWT is not set")
    url = f"{base}/rpc"
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers=_headers(jwt),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
        out = json.loads(resp.read().decode())
    if "error" in out:
        return f"Gateway error: {out['error']}"
    content = out.get("result", {}).get("content", [])
    texts = [c.get("text", "") for c in content if isinstance(c, dict) and "text" in c]
    return "\n".join(texts) if texts else json.dumps(out.get("result", {}))
