from __future__ import annotations

from typing import Any


def build_arguments(tool: dict[str, Any], task: str) -> dict[str, Any]:
    schema = tool.get("inputSchema") or tool.get("input_schema") or {}
    props = schema.get("properties") or {}
    required = schema.get("required") or []
    args: dict[str, Any] = {}
    if "query" in props or "query" in required:
        args["query"] = task
    elif "q" in props or "q" in required:
        args["q"] = task
    elif "search" in props or "search" in required:
        args["search"] = task
    elif required:
        first = required[0]
        args[first] = task
    else:
        args["task"] = task
    return args
