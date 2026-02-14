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


def _extract_normalized_tokens(text: str) -> set[str]:
    """Extract tokens from string, including single-char tokens for better matching."""
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return {word for word in normalized.split() if word}


def _enrich_tokens_with_synonyms(tokens: set[str]) -> set[str]:
    """Expand token set with synonyms for better matching."""
    enriched_tokens = set(tokens)
    for token in tokens:
        if token in SYNONYMS:
            enriched_tokens.update(SYNONYMS[token])
    return enriched_tokens


def _calculate_substring_match_score(query_tokens: set[str], target_text: str) -> int:
    """Score partial matches (e.g., 'file' matches 'filesystem')."""
    target_lower = target_text.lower()
    score = 0
    for token in query_tokens:
        if len(token) >= 3 and token in target_lower:
            score += 2
    return score


def calculate_tool_relevance_score(task: str, context: str, tool: dict[str, Any]) -> float:
    """Score a tool's relevance to the task with weighted components."""
    task_tokens = _extract_normalized_tokens(task)
    context_tokens = _extract_normalized_tokens(context) if context else set()
    combined_tokens = task_tokens | context_tokens

    if not combined_tokens:
        return 0.0

    # Expand with synonyms for better matching
    enriched_query_tokens = _enrich_tokens_with_synonyms(combined_tokens)

    tool_name = (tool.get("name") or "").lower()
    tool_description = (tool.get("description") or "").lower()
    gateway_slug = (tool.get("gatewaySlug") or tool.get("gateway_slug") or "").lower()

    name_tokens = _extract_normalized_tokens(tool_name)
    description_tokens = _extract_normalized_tokens(tool_description)
    gateway_tokens = _extract_normalized_tokens(gateway_slug)

    # Weighted scoring: name matches are most important
    name_exact_score = len(enriched_query_tokens & name_tokens) * 10
    description_exact_score = len(enriched_query_tokens & description_tokens) * 3
    gateway_exact_score = len(enriched_query_tokens & gateway_tokens) * 2

    # Partial matches for substring matching
    name_partial_score = _calculate_substring_match_score(combined_tokens, tool_name) * 5
    description_partial_score = _calculate_substring_match_score(combined_tokens, tool_description) * 1

    total_score = (
        name_exact_score
        + description_exact_score
        + gateway_exact_score
        + name_partial_score
        + description_partial_score
    )

    return float(total_score)


def select_top_matching_tools(
    tools: list[dict[str, Any]], task: str, context: str, top_n: int = 1
) -> list[dict[str, Any]]:
    """Select the best matching tools based on task and context."""
    if not tools:
        return []

    scored_tools = [(tool, calculate_tool_relevance_score(task, context or "", tool)) for tool in tools]
    scored_tools.sort(key=lambda x: -x[1])

    # Only return tools with positive scores
    return [tool for tool, score in scored_tools if score > 0][:top_n]
