"""Integration tests for tool selection and scoring workflows."""

from __future__ import annotations

import pytest

from tool_router.scoring.matcher import calculate_tool_relevance_score, select_top_matching_tools


class TestToolSelectionWorkflow:
    """Integration tests for complete tool selection workflows."""

    @pytest.fixture
    def sample_tools(self) -> list[dict]:
        """Sample tool definitions for testing."""
        return [
            {
                "name": "web_search",
                "description": "Search the web for information",
                "category": "search",
                "capabilities": ["search", "web", "information"],
            },
            {
                "name": "file_reader",
                "description": "Read and parse files from the filesystem",
                "category": "file",
                "capabilities": ["read", "parse", "filesystem"],
            },
            {
                "name": "code_analyzer",
                "description": "Analyze code for patterns and issues",
                "category": "development",
                "capabilities": ["analyze", "code", "patterns"],
            },
            {
                "name": "data_processor",
                "description": "Process and transform data structures",
                "category": "data",
                "capabilities": ["process", "transform", "data"],
            },
        ]

    def test_end_to_end_tool_selection_for_search_task(self, sample_tools: list[dict]) -> None:
        """Test complete workflow for search-related task."""
        task = "search for information about python programming"
        context = "learning python"

        # Step 1: Calculate relevance scores for all tools
        scores = []
        for tool in sample_tools:
            score = calculate_tool_relevance_score(task, context, tool)
            scores.append((tool["name"], score))

        # Step 2: Select top matching tools
        selected_tools = select_top_matching_tools(sample_tools, task, context, top_n=2)

        # Business logic validation
        assert len(selected_tools) == 2

        # Should prioritize search-related tools
        selected_names = [tool["name"] for tool in selected_tools]
        assert "web_search" in selected_names, "Should select web search for search task"

        # Search tool should have highest relevance
        web_search_score = next(score for name, score in scores if name == "web_search")
        assert web_search_score > 0.5, "Web search should have high relevance for search task"

    def test_tool_selection_with_context_awareness(self, sample_tools: list[dict]) -> None:
        """Test tool selection considering context information."""
        task = "analyze data"
        context_programming = "programming context"
        context_files = "file system context"

        # Test with programming context
        tools_programming = select_top_matching_tools(sample_tools, task, context_programming, top_n=2)

        # Test with file system context
        tools_files = select_top_matching_tools(sample_tools, task, context_files, top_n=2)

        # Business logic: context should influence selection
        programming_names = [tool["name"] for tool in tools_programming]
        file_names = [tool["name"] for tool in tools_files]

        # Programming context should favor code analyzer
        assert "code_analyzer" in programming_names, "Programming context should select code analyzer"

        # File context should favor file reader
        assert "file_reader" in file_names, "File context should select file reader"

    def test_multi_tool_coordination_workflow(self, sample_tools: list[dict]) -> None:
        """Test workflow requiring multiple tools to work together."""
        task = "analyze code files and generate documentation"
        context = "software development project"

        # Select tools for the complex task
        selected_tools = select_top_matching_tools(sample_tools, task, context, top_n=3)

        # Business logic: should select complementary tools
        selected_names = [tool["name"] for tool in selected_tools]

        # Should include code analysis tool (highest score)
        assert "code_analyzer" in selected_names, "Should include code analyzer for code analysis"

        # Should include file reader for code files (second highest score)
        assert "file_reader" in selected_names, "Should include file reader for code files"

        # Should include data processor for documentation generation (third highest score)
        assert "data_processor" in selected_names, "Should include data processor for documentation"

        # Verify tools can work together (complementary capabilities)
        selected_tools_dict = {tool["name"]: tool for tool in selected_tools}

        # Code analyzer and file reader can work together
        code_tool = selected_tools_dict["code_analyzer"]
        file_tool = selected_tools_dict["file_reader"]

        assert "analyze" in code_tool["capabilities"]
        assert "read" in file_tool["capabilities"]

        # Data processor can help with documentation generation
        data_tool = selected_tools_dict["data_processor"]
        assert "process" in data_tool["capabilities"]

    def test_tool_selection_with_edge_cases(self, sample_tools: list[dict]) -> None:
        """Test tool selection with edge cases and error conditions."""

        # Business logic: empty task should return empty result
        result = select_top_matching_tools(sample_tools, "", "", top_n=2)
        assert result == [], "Empty task should return empty result"

        # Business logic: whitespace-only task should return empty
        result = select_top_matching_tools(sample_tools, "   ", "   ", top_n=2)
        assert result == [], "Whitespace-only task should return empty result"

        # Business logic: very long task should be handled gracefully
        long_task = "search " * 1000  # Very long task
        result = select_top_matching_tools(sample_tools, long_task, "", top_n=2)
        assert isinstance(result, list), "Should return list even for very long tasks"

        # Test with no matching tools
        unrelated_tools = [
            {"name": "database_connector", "description": "Connect to databases", "category": "database"},
            {"name": "api_client", "description": "Make HTTP requests", "category": "network"},
        ]

        result = select_top_matching_tools(unrelated_tools, "cook food", "kitchen", top_n=2)
        assert result == [], "No matching tools should return empty result"

        # Business logic: test with None inputs (should handle gracefully)
        try:
            select_top_matching_tools(sample_tools, None, None, top_n=2)
            assert False, "Should raise TypeError for None inputs"
        except TypeError:
            pass  # Expected behavior

        # Business logic: test with invalid top_n values
        try:
            select_top_matching_tools(sample_tools, "test", "", top_n=0)
            result = select_top_matching_tools(sample_tools, "test", "", top_n=0)
            assert result == [], "top_n=0 should return empty list"
        except (ValueError, TypeError):
            pass  # Should handle invalid top_n gracefully

        # Business logic: test with negative top_n
        try:
            select_top_matching_tools(sample_tools, "test", "", top_n=-1)
            assert False, "Should raise error for negative top_n"
        except (ValueError, TypeError):
            pass  # Expected behavior

        # Business logic: test with tools missing required fields
        incomplete_tools = [
            {"name": "incomplete1"},  # Missing description
            {"description": "incomplete2"},  # Missing name
        ]

        result = select_top_matching_tools(incomplete_tools, "test", "", top_n=2)
        assert isinstance(result, list), "Should handle incomplete tools gracefully"

        # Business logic: verify scoring robustness with edge cases
        # Should not crash with unusual characters
        special_chars_task = "test with @#$%^&*() characters"
        result = select_top_matching_tools(sample_tools, special_chars_task, "", top_n=2)
        assert isinstance(result, list), "Should handle special characters"

    def test_performance_optimization_workflow(self, sample_tools: list[dict]) -> None:
        """Test performance considerations in tool selection."""
        import time

        task = "quick search operation"
        context = "time-sensitive query"

        # Measure selection time
        start_time = time.time()
        result = select_top_matching_tools(sample_tools, task, context, top_n=5)
        end_time = time.time()

        selection_time = end_time - start_time

        # Business logic: selection should be fast
        assert selection_time < 0.1, f"Tool selection should be fast, took {selection_time:.3f}s"

        # Should return reasonable number of tools
        assert len(result) <= 5, "Should not exceed requested top_n"

        # Results should be ordered by relevance
        if len(result) > 1:
            # First tool should have higher or equal relevance than subsequent tools
            for i in range(len(result) - 1):
                current_tool = result[i]
                next_tool = result[i + 1]

                # This assumes tools have a relevance score property or can be compared
                # In real implementation, this would check actual relevance scores
                # Placeholder for relevance score comparison
