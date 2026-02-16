"""Integration tests for AI routing flow."""

from __future__ import annotations

import pytest

from tool_router.ai.selector import AIToolSelector
from tool_router.scoring.matcher import select_top_matching_tools_with_ai


@pytest.fixture
def tools():
    """Sample tools for integration testing."""
    return [
        {"name": "search_web", "description": "Search the web for information"},
        {"name": "list_files", "description": "List files in directory"},
    ]


class TestAIRoutingIntegration:
    """Integration tests for AI-powered routing."""

    def test_ai_selector_with_scoring(self, tools, mocker):
        """Test AI selector integrated with scoring."""
        selector = AIToolSelector()
        mocker.patch.object(
            selector,
            "select_tool",
            return_value={"tool_name": "search_web", "confidence": 0.9, "reasoning": "best"},
        )

        result = select_top_matching_tools_with_ai(
            tools=tools,
            task="find python docs",
            context="",
            ai_selected_tool="search_web",
            ai_confidence=0.9,
            ai_weight=0.7,
            top_n=1,
        )

        assert len(result) > 0
        assert result[0]["name"] == "search_web"
