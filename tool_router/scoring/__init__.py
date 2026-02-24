"""Scoring module for tool matching and selection."""

from tool_router.scoring.matcher import (
    calculate_tool_relevance_score,
    select_top_matching_tools,
)


# Backward compatibility aliases
score_tool = calculate_tool_relevance_score
pick_best_tools = select_top_matching_tools

__all__ = [
    "calculate_tool_relevance_score",
    "pick_best_tools",
    "score_tool",
    "select_top_matching_tools",
]
