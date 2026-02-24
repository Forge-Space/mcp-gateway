"""Tests for enhanced matcher functions."""

from unittest.mock import Mock, patch

import pytest

from tool_router.scoring.matcher import (
    select_top_matching_tools_enhanced,
    select_top_matching_tools_hybrid,
)


@pytest.fixture
def sample_tools():
    """Sample tools for testing."""
    return [
        {
            "name": "web_search",
            "description": "Search the web for information",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
        {
            "name": "file_reader",
            "description": "Read contents from local files",
            "inputSchema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    ]


class TestHybridSelection:
    """Test hybrid tool selection with AI integration."""

    def test_select_top_matching_tools_hybrid_basic(self, sample_tools):
        """Test basic hybrid selection without AI."""
        result = select_top_matching_tools_hybrid(
            tools=sample_tools,
            task="search the web",
            context="find information",
            top_n=2,
            ai_selector=None,
            ai_weight=0.7,
            feedback_store=None,
        )

        assert len(result) <= 2
        assert all(tool in sample_tools for tool in result)

    def test_select_top_matching_tools_hybrid_with_ai(self, sample_tools):
        """Test hybrid selection with AI selector."""
        mock_ai_selector = Mock()
        mock_ai_selector.select_tool.return_value = {
            "tool_name": "web_search",
            "confidence": 0.9,
        }

        result = select_top_matching_tools_hybrid(
            tools=sample_tools,
            task="search the web",
            context="find information",
            top_n=1,
            ai_selector=mock_ai_selector,
            ai_weight=0.7,
            feedback_store=None,
        )

        assert len(result) == 1
        assert result[0]["name"] == "web_search"
        mock_ai_selector.select_tool.assert_called_once()

    def test_select_top_matching_tools_hybrid_ai_failure(self, sample_tools):
        """Test hybrid selection when AI fails."""
        mock_ai_selector = Mock()
        mock_ai_selector.select_tool.side_effect = Exception("AI failed")

        result = select_top_matching_tools_hybrid(
            tools=sample_tools,
            task="search the web",
            context="find information",
            top_n=1,
            ai_selector=mock_ai_selector,
            ai_weight=0.7,
            feedback_store=None,
        )

        # Should still return results based on keyword matching
        assert isinstance(result, list)

    def test_select_top_matching_tools_hybrid_with_feedback(self, sample_tools):
        """Test hybrid selection with feedback store."""
        mock_feedback_store = Mock()
        mock_feedback_store.similar_task_tools.return_value = ["web_search"]
        mock_feedback_store.get_comprehensive_boost.return_value = 1.2

        result = select_top_matching_tools_hybrid(
            tools=sample_tools,
            task="search the web",
            context="find information",
            top_n=1,
            ai_selector=None,
            ai_weight=0.7,
            feedback_store=mock_feedback_store,
        )

        assert isinstance(result, list)
        mock_feedback_store.similar_task_tools.assert_called_once_with("search the web")

    def test_select_top_matching_tools_hybrid_empty_tools(self):
        """Test hybrid selection with empty tools list."""
        result = select_top_matching_tools_hybrid(
            tools=[],
            task="search the web",
            context="find information",
            top_n=1,
            ai_selector=None,
            ai_weight=0.7,
            feedback_store=None,
        )

        assert result == []


class TestEnhancedSelection:
    """Test enhanced tool selection with NLP and learning."""

    def test_select_top_matching_tools_enhanced_basic(self, sample_tools):
        """Test basic enhanced selection."""
        result = select_top_matching_tools_enhanced(
            tools=sample_tools,
            task="search the web",
            context="find information",
            top_n=2,
            ai_selector=None,
            ai_weight=0.6,
            feedback_store=None,
            use_nlp_hints=False,
        )

        assert len(result) <= 2
        assert all(tool in sample_tools for tool in result)

    def test_select_top_matching_tools_enhanced_with_nlp(self, sample_tools):
        """Test enhanced selection with NLP hints."""
        mock_feedback_store = Mock()
        mock_feedback_store.get_adaptive_hints.return_value = ["search", "web"]
        mock_feedback_store.similar_task_tools.return_value = ["web_search"]
        mock_feedback_store.get_learning_insights.return_value = {"web_search": 0.8}
        mock_feedback_store.get_comprehensive_boost.return_value = 1.1

        result = select_top_matching_tools_enhanced(
            tools=sample_tools,
            task="search the web",
            context="find information",
            top_n=1,
            ai_selector=None,
            ai_weight=0.6,
            feedback_store=mock_feedback_store,
            use_nlp_hints=True,
        )

        assert isinstance(result, list)
        mock_feedback_store.get_adaptive_hints.assert_called_once_with("search the web")
        mock_feedback_store.similar_task_tools.assert_called_once_with("search the web")
        mock_feedback_store.get_learning_insights.assert_called_once_with(
            "search the web"
        )

    def test_select_top_matching_tools_enhanced_with_ai(self, sample_tools):
        """Test enhanced selection with AI."""
        mock_ai_selector = Mock()
        mock_ai_selector.select_tool.return_value = {
            "tool_name": "web_search",
            "confidence": 0.85,
        }

        result = select_top_matching_tools_enhanced(
            tools=sample_tools,
            task="search the web",
            context="find information",
            top_n=1,
            ai_selector=mock_ai_selector,
            ai_weight=0.6,
            feedback_store=None,
            use_nlp_hints=False,
        )

        assert len(result) == 1
        assert result[0]["name"] == "web_search"

    def test_select_top_matching_tools_enhanced_learning_insights(self, sample_tools):
        """Test enhanced selection with learning insights."""
        mock_feedback_store = Mock()
        mock_feedback_store.get_learning_insights.return_value = {
            "web_search": 0.9,
            "file_reader": 0.3,
        }
        mock_feedback_store.get_comprehensive_boost.return_value = 1.15

        result = select_top_matching_tools_enhanced(
            tools=sample_tools,
            task="search the web",
            context="find information",
            top_n=1,
            ai_selector=None,
            ai_weight=0.6,
            feedback_store=mock_feedback_store,
            use_nlp_hints=False,
        )

        assert isinstance(result, list)
        # Should prioritize web_search due to higher learning insight

    def test_select_top_matching_tools_enhanced_empty_tools(self):
        """Test enhanced selection with empty tools list."""
        result = select_top_matching_tools_enhanced(
            tools=[],
            task="search the web",
            context="find information",
            top_n=1,
            ai_selector=None,
            ai_weight=0.6,
            feedback_store=None,
            use_nlp_hints=False,
        )

        assert result == []

    @patch("tool_router.scoring.matcher.logger")
    def test_select_top_matching_tools_enhanced_ai_exception(
        self, mock_logger, sample_tools
    ):
        """Test enhanced selection when AI raises exception."""
        mock_ai_selector = Mock()
        mock_ai_selector.select_tool.side_effect = Exception("AI service unavailable")

        result = select_top_matching_tools_enhanced(
            tools=sample_tools,
            task="search the web",
            context="find information",
            top_n=1,
            ai_selector=mock_ai_selector,
            ai_weight=0.6,
            feedback_store=None,
            use_nlp_hints=False,
        )

        assert isinstance(result, list)
        mock_logger.warning.assert_called_once()
