"""Unit tests for scoring matcher to improve coverage."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from tool_router.scoring.matcher import (
    calculate_hybrid_score,
    select_top_matching_tools,
    select_top_matching_tools_with_ai,
    calculate_tool_relevance_score
)


class TestScoringMatcher:
    """Tests for scoring matcher functions."""

    def test_calculate_hybrid_score_clamping(self) -> None:
        """Test calculate_hybrid_score clamps inputs to valid range."""
        # Test AI confidence clamping
        score = calculate_hybrid_score(
            {"name": "test"}, "task", "context",
            ai_confidence=1.5,  # Above 1.0
            ai_weight=0.5
        )
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

        # Test AI confidence negative
        score = calculate_hybrid_score(
            {"name": "test"}, "task", "context",
            ai_confidence=-0.5,  # Below 0.0
            ai_weight=0.5
        )
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

        # Test AI weight clamping
        score = calculate_hybrid_score(
            {"name": "test"}, "task", "context",
            ai_confidence=0.8,
            ai_weight=1.5  # Above 1.0
        )
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

        # Test AI weight negative
        score = calculate_hybrid_score(
            {"name": "test"}, "task", "context",
            ai_confidence=0.8,
            ai_weight=-0.5  # Below 0.0
        )
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_calculate_hybrid_score_edge_cases(self, mocker) -> None:
        """Test calculate_hybrid_score with edge cases."""
        mock_keyword_score = mocker.patch("tool_router.scoring.matcher.calculate_tool_relevance_score")
        mock_keyword_score.return_value = 25.0  # Mid-range score

        # Test with zero AI weight (pure keyword)
        score = calculate_hybrid_score(
            {"name": "test"}, "task", "context",
            ai_confidence=0.8,
            ai_weight=0.0
        )
        expected = 0.5  # 25.0 / 50.0 = 0.5
        assert score == expected

        # Test with full AI weight (pure AI)
        score = calculate_hybrid_score(
            {"name": "test"}, "task", "context",
            ai_confidence=0.9,
            ai_weight=1.0
        )
        expected = 0.9  # Pure AI confidence
        assert score == expected

        # Test with balanced weights
        score = calculate_hybrid_score(
            {"name": "test"}, "task", "context",
            ai_confidence=0.8,
            ai_weight=0.5
        )
        expected = (0.8 * 0.5) + (0.5 * 0.5)  # 0.4 + 0.25 = 0.65
        assert score == expected

    def test_calculate_hybrid_score_keyword_normalization(self, mocker) -> None:
        """Test calculate_hybrid_score normalizes keyword scores."""
        mock_keyword_score = mocker.patch("tool_router.scoring.matcher.calculate_tool_relevance_score")

        # Test high keyword score gets clamped
        mock_keyword_score.return_value = 100.0  # Above 50.0
        score = calculate_hybrid_score(
            {"name": "test"}, "task", "context",
            ai_confidence=0.5,
            ai_weight=0.5
        )
        expected = (0.5 * 0.5) + (1.0 * 0.5)  # Normalized to 1.0
        assert score == expected

        # Test low keyword score
        mock_keyword_score.return_value = 10.0  # Below 50.0
        score = calculate_hybrid_score(
            {"name": "test"}, "task", "context",
            ai_confidence=0.5,
            ai_weight=0.5
        )
        expected = (0.5 * 0.5) + (0.2 * 0.5)  # 10.0 / 50.0 = 0.2
        assert score == expected

    def test_select_top_matching_tools_empty_list(self) -> None:
        """Test select_top_matching_tools_with_ai when the list of tools is empty."""
        result = select_top_matching_tools_with_ai(
            [], "task", "context",
            ai_selected_tool=None, ai_confidence=0.0, top_n=3
        )

        assert result == []

    def test_select_top_matching_tools_ai_selected(self, mocker) -> None:
        """Test select_top_matching_tools_with_ai when AI selects a tool."""
        tools = [
            {"name": "tool1", "description": "First tool"},
            {"name": "tool2", "description": "Second tool"},
            {"name": "tool3", "description": "Third tool"}
        ]

        mock_hybrid_score = mocker.patch("tool_router.scoring.matcher.calculate_hybrid_score")
        mock_hybrid_score.return_value = 0.8

        mock_keyword_score = mocker.patch("tool_router.scoring.matcher.calculate_tool_relevance_score")
        mock_keyword_score.return_value = 40.0  # High enough to pass the positive score filter

        result = select_top_matching_tools_with_ai(
            tools, "task", "context",
            ai_selected_tool="tool1",
            ai_confidence=0.9,
            ai_weight=0.7,
            top_n=2
        )

        # Should return top 2 tools (both with positive scores)
        assert len(result) == 2
        assert result[0]["name"] == "tool1"  # AI selected tool should be first

        # Verify hybrid score was called for AI selected tool
        mock_hybrid_score.assert_called_once_with(
            tools[0], "task", "context", 0.9, 0.7
        )

    def test_select_top_matching_tools_no_ai_selection(self, mocker) -> None:
        """Test select_top_matching_tools_with_ai when AI doesn't select any tool."""
        tools = [
            {"name": "tool1", "description": "First tool"},
            {"name": "tool2", "description": "Second tool"}
        ]

        mock_keyword_score = mocker.patch("tool_router.scoring.matcher.calculate_tool_relevance_score")
        mock_keyword_score.side_effect = [30.0, 20.0]  # Different scores for each tool

        result = select_top_matching_tools_with_ai(
            tools, "task", "context",
            ai_selected_tool=None,
            ai_confidence=0.0,
            ai_weight=0.5,
            top_n=2
        )

        # Should return both tools sorted by score
        assert len(result) == 2
        assert result[0]["name"] == "tool1"  # Higher score
        assert result[1]["name"] == "tool2"

    def test_select_top_matching_tools_mixed_selection(self, mocker) -> None:
        """Test select_top_matching_tools_with_ai with mixed AI and keyword scoring."""
        tools = [
            {"name": "tool1", "description": "First tool"},
            {"name": "tool2", "description": "Second tool"},
            {"name": "tool3", "description": "Third tool"}
        ]

        mock_hybrid_score = mocker.patch("tool_router.scoring.matcher.calculate_hybrid_score")
        mock_hybrid_score.return_value = 0.7

        mock_keyword_score = mocker.patch("tool_router.scoring.matcher.calculate_tool_relevance_score")
        mock_keyword_score.return_value = 25.0

        result = select_top_matching_tools_with_ai(
            tools, "task", "context",
            ai_selected_tool="tool1",  # AI selects tool1
            ai_confidence=0.8,
            ai_weight=0.6,
            top_n=3
        )

        # Should return all tools, with tool1 first (AI selected)
        assert len(result) == 3
        assert result[0]["name"] == "tool1"

        # Verify correct scoring methods were called
        mock_hybrid_score.assert_called_once_with(
            tools[0], "task", "context", 0.8, 0.6
        )
        # Keyword score should be called for non-AI selected tools
        assert mock_keyword_score.call_count == 2

    def test_select_top_matching_tools_filter_positive_scores(self, mocker) -> None:
        """Test select_top_matching_tools_with_ai filters out zero or negative scores."""
        tools = [
            {"name": "tool1", "description": "First tool"},
            {"name": "tool2", "description": "Second tool"},
            {"name": "tool3", "description": "Third tool"}
        ]

        mock_keyword_score = mocker.patch("tool_router.scoring.matcher.calculate_tool_relevance_score")
        mock_keyword_score.side_effect = [30.0, 0.0, -10.0]  # One positive, one zero, one negative

        result = select_top_matching_tools_with_ai(
            tools, "task", "context",
            ai_selected_tool=None,
            ai_confidence=0.0,
            ai_weight=0.5,
            top_n=5
        )

        # Should only return tools with positive scores
        assert len(result) == 1
        assert result[0]["name"] == "tool1"

    def test_select_top_matching_tools_top_n_limiting(self, mocker) -> None:
        """Test select_top_matching_tools_with_ai respects top_n parameter."""
        tools = [
            {"name": "tool1", "description": "First tool"},
            {"name": "tool2", "description": "Second tool"},
            {"name": "tool3", "description": "Third tool"},
            {"name": "tool4", "description": "Fourth tool"}
        ]

        mock_keyword_score = mocker.patch("tool_router.scoring.matcher.calculate_tool_relevance_score")
        mock_keyword_score.side_effect = [40.0, 30.0, 20.0, 10.0]  # Different scores

        result = select_top_matching_tools_with_ai(
            tools, "task", "context",
            ai_selected_tool=None,
            ai_confidence=0.0,
            ai_weight=0.5,
            top_n=2
        )

        # Should only return top 2
        assert len(result) == 2
        assert result[0]["name"] == "tool1"
        assert result[1]["name"] == "tool2"

    def test_select_top_matching_tools_tool_without_name(self, mocker) -> None:
        """Test select_top_matching_tools_with_ai handles tools without name field."""
        tools = [
            {"description": "Tool without name"},
            {"name": "tool2", "description": "Tool with name"}
        ]

        mock_keyword_score = mocker.patch("tool_router.scoring.matcher.calculate_tool_relevance_score")
        mock_keyword_score.return_value = 20.0

        result = select_top_matching_tools_with_ai(
            tools, "task", "context",
            ai_selected_tool=None,
            ai_confidence=0.0,
            ai_weight=0.5,
            top_n=2
        )

        # Should handle tools without name gracefully
        assert len(result) == 2  # Both tools should be returned
        # Check that the tool with name is included
        assert any(tool.get("name") == "tool2" for tool in result)
        # Check that the tool without name is also included (no "name" key)
        assert any("name" not in tool and tool.get("description") == "Tool without name" for tool in result)

    def test_select_top_matching_tools_default_top_n(self, mocker) -> None:
        """Test select_top_matching_tools_with_ai uses default top_n=1."""
        tools = [
            {"name": "tool1", "description": "First tool"},
            {"name": "tool2", "description": "Second tool"}
        ]

        mock_keyword_score = mocker.patch("tool_router.scoring.matcher.calculate_tool_relevance_score")
        mock_keyword_score.side_effect = [30.0, 20.0]

        result = select_top_matching_tools_with_ai(
            tools, "task", "context",
            ai_selected_tool=None,
            ai_confidence=0.0,
            ai_weight=0.5
        )

        # Should return only 1 tool (default)
        assert len(result) == 1
        assert result[0]["name"] == "tool1"

    def test_calculate_hybrid_score_with_zero_keyword_score(self, mocker) -> None:
        """Test calculate_hybrid_score when keyword score is zero."""
        mock_keyword_score = mocker.patch("tool_router.scoring.matcher.calculate_tool_relevance_score")
        mock_keyword_score.return_value = 0.0

        score = calculate_hybrid_score(
            {"name": "test"}, "task", "context",
            ai_confidence=0.7,
            ai_weight=0.6
        )

        expected = (0.7 * 0.6) + (0.0 * 0.4)  # Only AI component
        assert score == expected

    def test_calculate_hybrid_score_extreme_values(self, mocker) -> None:
        """Test calculate_hybrid_score with extreme values."""
        mock_keyword_score = mocker.patch("tool_router.scoring.matcher.calculate_tool_relevance_score")
        mock_keyword_score.return_value = 1000.0  # Very high score

        score = calculate_hybrid_score(
            {"name": "test"}, "task", "context",
            ai_confidence=0.0,  # Zero AI confidence
            ai_weight=0.0   # Zero AI weight
        )

        # Should be clamped to 1.0
        assert score == 1.0
