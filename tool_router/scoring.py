from __future__ import annotations

import re
from typing import Any


def _tokens(s: str) -> set[str]:
    normalized = re.sub(r"[^a-z0-9\s]", " ", s.lower())
    return {w for w in normalized.split() if len(w) > 1}


def score_tool(task: str, context: str, tool: dict[str, Any]) -> int:
    task_tokens = _tokens(task)
    context_tokens = _tokens(context) if context else set()
    combined = task_tokens | context_tokens
    if not combined:
        return 0
    name = (tool.get("name") or "").lower()
    desc = (tool.get("description") or "").lower()
    gateway = (tool.get("gatewaySlug") or tool.get("gateway_slug") or "").lower()
    tool_tokens = _tokens(name) | _tokens(desc) | _tokens(gateway)
    return len(combined & tool_tokens)


def pick_best_tools(
    tools: list[dict[str, Any]], task: str, context: str, top_n: int = 1
) -> list[dict[str, Any]]:
    if not tools:
        return []
    scored = [(t, score_tool(task, context or "", t)) for t in tools]
    scored.sort(key=lambda x: -x[1])
    best = [t for t, s in scored if s > 0][:top_n]
    return best
