"""High-quality tests for tool_router/scoring/matcher.py."""

import pytest
from tool_router.scoring.matcher import (
    _extract_normalized_tokens,
    _enrich_tokens_with_synonyms,
    _calculate_substring_match_score,
    calculate_tool_relevance_score,
    select_top_matching_tools,
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
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "file_reader",
            "description": "Read contents from local files",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "encoding": {"type": "string", "enum": ["utf-8", "latin-1"]}
                },
                "required": ["path"]
            }
        },
        {
            "name": "database_query",
            "description": "Query database for information",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100}
                },
                "required": ["sql"]
            }
        }
    ]


@pytest.fixture
def sample_task():
    """Sample task for testing."""
    return "search for python programming tutorials"


@pytest.fixture
def sample_context():
    """Sample context for testing."""
    return "user wants to find learning resources"


class TestTokenExtraction:
    """Test token extraction functionality."""

    def test_extract_normalized_tokens_basic(self):
        """Test basic token extraction with valid input."""
        text = "Python programming tutorials search"
        result = _extract_normalized_tokens(text)

        assert isinstance(result, set)
        assert len(result) > 0
        assert all(isinstance(token, str) for token in result)
        assert all(token.islower() for token in result)  # Should be normalized

    def test_extract_normalized_tokens_empty_input(self):
        """Test token extraction with empty input."""
        result = _extract_normalized_tokens("")

        assert isinstance(result, set)
        assert len(result) == 0

    def test_extract_normalized_tokens_with_special_chars(self):
        """Test token extraction with special characters."""
        text = "python! programming? tutorials."
        result = _extract_normalized_tokens(text)

        assert isinstance(result, set)
        assert all(not token.endswith(('.', '!', '?')) for token in result)


class TestTokenEnrichment:
    """Test token enrichment functionality."""

    def test_enrich_tokens_with_synonyms(self):
        """Test token enrichment with synonyms."""
        tokens = {"search", "find"}
        result = _enrich_tokens_with_synonyms(tokens)

        assert isinstance(result, set)
        assert len(result) > len(tokens)  # Should have added synonyms
        assert "lookup" in result
        assert "query" in result

    def test_enrich_tokens_empty(self):
        """Test token enrichment with empty set."""
        result = _enrich_tokens_with_synonyms(set())

        assert isinstance(result, set)
        assert len(result) == 0


class TestSubstringMatching:
    """Test substring matching functionality."""

    def test_calculate_substring_match_score(self):
        """Test substring match score calculation."""
        query_tokens = {"python", "search"}
        target_text = "Search for python programming tutorials"

        score = _calculate_substring_match_score(query_tokens, target_text)

        assert isinstance(score, int)
        assert score >= 0
        assert score <= 100  # Should be percentage-based

    def test_calculate_substring_match_score_no_match(self):
        """Test substring match score with no matches."""
        query_tokens = {"xyz", "abc"}
        target_text = "Search for python programming tutorials"

        score = _calculate_substring_match_score(query_tokens, target_text)

        assert score == 0


class TestToolRelevanceScoring:
    """Test tool relevance scoring functionality."""

    def test_calculate_tool_relevance_score(self, sample_task, sample_context):
        """Test tool relevance score calculation."""
        tool = {
            "name": "web_search",
            "description": "Search the web for information",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }

        score = calculate_tool_relevance_score(sample_task, sample_context, tool)

        assert isinstance(score, float)
        assert score >= 0.0  # Score can be any positive value

    def test_calculate_tool_relevance_score_irrelevant_tool(self, sample_task, sample_context):
        """Test tool relevance score with irrelevant tool."""
        tool = {
            "name": "delete_file",
            "description": "Delete files from filesystem",
            "inputSchema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        }

        score = calculate_tool_relevance_score(sample_task, sample_context, tool)

        assert isinstance(score, float)
        assert score < 0.5  # Should be low for irrelevant tool


class TestToolSelection:
    """Test tool selection functionality."""

    def test_select_top_matching_tools(self, sample_tools, sample_task, sample_context):
        """Test selecting top matching tools."""
        results = select_top_matching_tools(sample_tools, sample_task, sample_context, top_n=2)

        assert isinstance(results, list)
        assert len(results) <= 2
        assert all(isinstance(tool, dict) for tool in results)
        assert all("name" in tool for tool in results)

    def test_select_top_matching_tools_single(self, sample_tools, sample_task, sample_context):
        """Test selecting single top matching tool."""
        results = select_top_matching_tools(sample_tools, sample_task, sample_context, top_n=1)

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["name"] == "web_search"  # Should match search task

    def test_select_top_matching_tools_empty_list(self, sample_task, sample_context):
        """Test selecting tools from empty list."""
        results = select_top_matching_tools([], sample_task, sample_context)

        assert isinstance(results, list)
        assert len(results) == 0


class TestIntegration:
    """Integration tests for the matcher system."""

    def test_end_to_end_matching(self, sample_tools, sample_task, sample_context):
        """Test end-to-end tool matching workflow."""
        # Step 1: Extract tokens from task
        task_tokens = _extract_normalized_tokens(sample_task)
        assert len(task_tokens) > 0

        # Step 2: Enrich tokens with synonyms
        enriched_tokens = _enrich_tokens_with_synonyms(task_tokens)
        assert len(enriched_tokens) >= len(task_tokens)

        # Step 3: Calculate relevance scores for all tools
        scores = []
        for tool in sample_tools:
            score = calculate_tool_relevance_score(sample_task, sample_context, tool)
            scores.append((tool, score))

        # Step 4: Select top tools
        top_tools = select_top_matching_tools(sample_tools, sample_task, sample_context, top_n=2)

        assert isinstance(top_tools, list)
        assert len(top_tools) == 2
        # Verify that the selected tools have positive scores
        for tool in top_tools:
            tool_score = calculate_tool_relevance_score(sample_task, sample_context, tool)
            assert tool_score > 0

    def test_search_task_prioritizes_search_tools(self, sample_tools):
        """Test that search tasks prioritize search-related tools."""
        search_task = "find information about python"
        search_context = "user wants to learn python programming"

        results = select_top_matching_tools(sample_tools, search_task, search_context, top_n=1)

        assert len(results) == 1
        assert "search" in results[0]["name"].lower() or "find" in results[0]["description"].lower()
