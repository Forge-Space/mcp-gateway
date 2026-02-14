from __future__ import annotations

import re
from typing import Any

# Common synonyms for better matching
SYNONYMS = {
    "search": {"find", "lookup", "query", "seek"},
    "find": {"search", "lookup", "locate"},
    "list": {"show", "display", "get"},
    "create": {"make", "add", "new"},
    "delete": {"remove", "destroy"},
    "update": {"modify", "change", "edit"},
    "read": {"get", "fetch", "retrieve"},
    "write": {"save", "store", "put"},
}


def _tokens(s: str) -> set[str]:
    """Extract tokens from string, including single-char tokens for better matching."""
    normalized = re.sub(r"[^a-z0-9\s]", " ", s.lower())
    return {w for w in normalized.split() if w}


def _expand_with_synonyms(tokens: set[str]) -> set[str]:
    """Expand token set with synonyms for better matching."""
    expanded = set(tokens)
    for token in tokens:
        if token in SYNONYMS:
            expanded.update(SYNONYMS[token])
    return expanded


def _partial_match_score(query_tokens: set[str], target: str) -> int:
    """Score partial matches (e.g., 'file' matches 'filesystem')."""
    target_lower = target.lower()
    score = 0
    for token in query_tokens:
        if len(token) >= 3 and token in target_lower:
            score += 2
    return score


def score_tool(task: str, context: str, tool: dict[str, Any]) -> float:
    """Score a tool's relevance to the task with weighted components."""
    task_tokens = _tokens(task)
    context_tokens = _tokens(context) if context else set()
    combined = task_tokens | context_tokens

    if not combined:
        return 0.0

    # Expand with synonyms for better matching
    expanded_query = _expand_with_synonyms(combined)

    name = (tool.get("name") or "").lower()
    desc = (tool.get("description") or "").lower()
    gateway = (tool.get("gatewaySlug") or tool.get("gateway_slug") or "").lower()

    name_tokens = _tokens(name)
    desc_tokens = _tokens(desc)
    gateway_tokens = _tokens(gateway)

    # Weighted scoring: name matches are most important
    name_exact = len(expanded_query & name_tokens) * 10
    desc_exact = len(expanded_query & desc_tokens) * 3
    gateway_exact = len(expanded_query & gateway_tokens) * 2

    # Partial matches for substring matching
    name_partial = _partial_match_score(combined, name) * 5
    desc_partial = _partial_match_score(combined, desc) * 1

    total_score = name_exact + desc_exact + gateway_exact + name_partial + desc_partial

    return float(total_score)


def pick_best_tools(
    tools: list[dict[str, Any]], task: str, context: str, top_n: int = 1
) -> list[dict[str, Any]]:
    """Select the best matching tools based on task and context."""
    if not tools:
        return []

    scored = [(t, score_tool(task, context or "", t)) for t in tools]
    scored.sort(key=lambda x: -x[1])

    # Only return tools with positive scores
    best = [t for t, s in scored if s > 0][:top_n]
    return best
