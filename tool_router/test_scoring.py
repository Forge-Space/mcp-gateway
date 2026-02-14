from __future__ import annotations

from tool_router.scoring import pick_best_tools, score_tool


def test_score_tool_empty_task_returns_zero() -> None:
    tool = {"name": "search", "description": "Search the web"}
    assert score_tool("", "", tool) == 0


def test_score_tool_matching_name_scores_positive() -> None:
    tool = {"name": "search", "description": "Search the web"}
    assert score_tool("search the web", "", tool) > 0


def test_score_tool_matching_description_scores_positive() -> None:
    tool = {"name": "foo", "description": "search the web for things"}
    assert score_tool("search for things", "", tool) > 0


def test_score_tool_no_match_returns_zero() -> None:
    tool = {"name": "fetch", "description": "Fetch a URL"}
    assert score_tool("calculate sum", "", tool) == 0


def test_score_tool_uses_context_tokens() -> None:
    tool = {"name": "search", "description": "Search"}
    assert score_tool("do it", "search docs", tool) > 0


def test_pick_best_tools_empty_list_returns_empty() -> None:
    assert pick_best_tools([], "search", "") == []


def test_pick_best_tools_returns_best_match() -> None:
    tools = [
        {"name": "fetch", "description": "Fetch URL"},
        {"name": "search", "description": "Search the web"},
        {"name": "time", "description": "Get time"},
    ]
    best = pick_best_tools(tools, "search the web", "", top_n=1)
    assert len(best) == 1
    assert best[0]["name"] == "search"


def test_pick_best_tools_respects_top_n() -> None:
    tools = [
        {"name": "search", "description": "Search"},
        {"name": "web search", "description": "Search web"},
        {"name": "fetch", "description": "Fetch"},
    ]
    best = pick_best_tools(tools, "search web", "", top_n=2)
    assert len(best) == 2


def test_pick_best_tools_no_match_returns_empty() -> None:
    tools = [{"name": "fetch", "description": "Fetch URL"}]
    assert pick_best_tools(tools, "calculate", "", top_n=1) == []
