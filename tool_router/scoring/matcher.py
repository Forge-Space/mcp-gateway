from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from tool_router.ai.selector import OllamaSelector

if TYPE_CHECKING:
    from tool_router.ai.feedback import FeedbackStore


logger = logging.getLogger(__name__)


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


def select_top_matching_tools_hybrid(  # noqa: PLR0913
    tools: list[dict[str, Any]],
    task: str,
    context: str,
    top_n: int = 1,
    ai_selector: OllamaSelector | None = None,
    ai_weight: float = 0.7,
    feedback_store: FeedbackStore | None = None,
) -> list[dict[str, Any]]:
    """Select the best matching tools using hybrid AI + keyword scoring.

    When a feedback_store is provided, historical success rates are used to
    boost or penalise tool scores via a multiplier in [0.5, 1.5].
    """
    if not tools:
        return []

    # Get keyword scores for all tools
    keyword_scores = {}
    for tool in tools:
        keyword_scores[tool.get("name", "")] = calculate_tool_relevance_score(task, context or "", tool)

    # Retrieve similar tools from feedback history for the AI prompt
    similar_tools: list[str] = []
    if feedback_store:
        similar_tools = feedback_store.similar_task_tools(task)

    # Try AI selection if available and enabled
    ai_result = None
    ai_score = 0.0
    selected_tool_name = None

    if ai_selector:
        try:
            ai_result = ai_selector.select_tool(
                task, tools, context=context or "", similar_tools=similar_tools or None
            )
            if ai_result:
                selected_tool_name = ai_result.get("tool_name")
                ai_score = ai_result.get("confidence", 0.0)
                logger.info("AI selected tool: %s with confidence: %s", selected_tool_name, ai_score)
        except Exception as e:  # noqa: BLE001
            logger.warning("AI selection failed: %s", e)

    # Calculate hybrid scores
    hybrid_scores = []
    for tool in tools:
        tool_name = tool.get("name", "")
        keyword_score = keyword_scores.get(tool_name, 0.0)

        # Normalize keyword score to 0-1 range (assuming max possible score around 100)
        normalized_keyword_score = min(keyword_score / 100.0, 1.0)

        # If AI selected this tool, use hybrid scoring
        if selected_tool_name and tool_name == selected_tool_name:
            hybrid_score = (ai_score * ai_weight) + (normalized_keyword_score * (1 - ai_weight))
            logger.info(
                "Hybrid score for %s: AI=%.2f, Keyword=%.2f, Hybrid=%.2f",
                tool_name, ai_score, normalized_keyword_score, hybrid_score,
            )
        else:
            # For non-AI-selected tools, just use normalized keyword score
            hybrid_score = normalized_keyword_score * (1 - ai_weight)

        # Apply feedback boost multiplier
        if feedback_store:
            boost = feedback_store.get_boost(tool_name)
            hybrid_score *= boost

        hybrid_scores.append((tool, hybrid_score))

    # Sort by hybrid score and return top N
    hybrid_scores.sort(key=lambda x: -x[1])

    # Return tools with positive scores
    return [tool for tool, score in hybrid_scores if score > 0][:top_n]
