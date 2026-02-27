"""Tests for tool_router/scoring/matcher.py module."""

import pytest

from tool_router.scoring.matcher import (
    _calculate_substring_match_score,
    _enrich_tokens_with_synonyms,
    _extract_normalized_tokens,
    calculate_tool_relevance_score,
    select_top_matching_tools,
)


class TestTokenExtraction:
    """Test token extraction functionality."""

    def test_extract_normalized_tokens_basic(self) -> None:
        """Test basic token extraction."""
        tokens = _extract_normalized_tokens("search the web for information")
        assert "search" in tokens
        assert "web" in tokens
        assert "information" in tokens
        # _extract_normalized_tokens doesn't filter stop words
        assert "the" in tokens
        assert "for" in tokens

    def test_extract_normalized_tokens_with_punctuation(self) -> None:
        """Test token extraction with punctuation."""
        tokens = _extract_normalized_tokens("read file.txt, then write to output.json!")
        assert "read" in tokens
        # Punctuation is replaced with spaces, so "file.txt" becomes "file" and "txt"
        assert "file" in tokens
        assert "txt" in tokens
        assert "write" in tokens
        assert "output" in tokens
        assert "json" in tokens

    def test_extract_normalized_tokens_empty(self) -> None:
        """Test token extraction with empty string."""
        tokens = _extract_normalized_tokens("")
        assert tokens == set()

    def test_extract_normalized_tokens_case_insensitive(self) -> None:
        """Test token extraction is case insensitive."""
        tokens1 = _extract_normalized_tokens("Search the Web")
        tokens2 = _extract_normalized_tokens("search the web")
        assert tokens1 == tokens2

    def test_extract_normalized_tokens_with_numbers(self) -> None:
        """Test token extraction with numbers."""
        tokens = _extract_normalized_tokens("create 5 files and 10 directories")
        assert "create" in tokens
        assert "5" in tokens
        assert "files" in tokens
        assert "10" in tokens
        assert "directories" in tokens


class TestSynonymEnrichment:
    """Test synonym enrichment functionality."""

    def test_enrich_tokens_with_synonyms_basic(self) -> None:
        """Test basic synonym enrichment."""
        original_tokens = {"search", "find"}
        enriched = _enrich_tokens_with_synonyms(original_tokens)

        assert "search" in enriched
        assert "find" in enriched
        # SYNONYMS["search"] = {"find", "lookup", "query", "seek"}
        # SYNONYMS["find"] = {"search", "lookup", "locate"}
        assert "lookup" in enriched
        assert "locate" in enriched

    def test_enrich_tokens_with_synonyms_file_operations(self) -> None:
        """Test synonym enrichment for file operations."""
        original_tokens = {"read", "file"}
        enriched = _enrich_tokens_with_synonyms(original_tokens)

        assert "read" in enriched
        assert "file" in enriched
        # SYNONYMS["read"] = {"get", "fetch", "retrieve"}
        assert "get" in enriched
        assert "fetch" in enriched

    def test_enrich_tokens_with_synonyms_empty(self) -> None:
        """Test synonym enrichment with empty tokens."""
        enriched = _enrich_tokens_with_synonyms(set())
        assert enriched == set()

    def test_enrich_tokens_with_synonyms_no_matches(self) -> None:
        """Test synonym enrichment with no matching synonyms."""
        original_tokens = {"xyz", "abc123"}
        enriched = _enrich_tokens_with_synonyms(original_tokens)

        assert "xyz" in enriched
        assert "abc123" in enriched
        assert len(enriched) == 2  # No additional synonyms


class TestSubstringMatching:
    """Test substring matching functionality."""

    def test_calculate_substring_match_score_exact(self) -> None:
        """Test exact substring match."""
        tokens = {"search", "web"}
        text = "search the web"
        score = _calculate_substring_match_score(tokens, text)
        assert score > 0

    def test_calculate_substring_match_score_partial(self) -> None:
        """Test partial substring match."""
        tokens = {"search", "web"}
        text = "web searching tool"
        score = _calculate_substring_match_score(tokens, text)
        assert score > 0

    def test_calculate_substring_match_score_no_match(self) -> None:
        """Test no substring match."""
        tokens = {"search", "web"}
        text = "database query tool"
        score = _calculate_substring_match_score(tokens, text)
        assert score == 0

    def test_calculate_substring_match_score_empty_tokens(self) -> None:
        """Test substring match with empty tokens."""
        score = _calculate_substring_match_score(set(), "any text")
        assert score == 0

    def test_calculate_substring_match_score_empty_text(self) -> None:
        """Test substring match with empty text."""
        tokens = {"search", "web"}
        score = _calculate_substring_match_score(tokens, "")
        assert score == 0


class TestToolRelevanceScoring:
    """Test tool relevance scoring functionality."""

    def test_calculate_tool_relevance_score_perfect_match(self) -> None:
        """Test perfect tool relevance match."""
        tool = {
            "name": "web_search",
            "description": "Search the web for information",
            "gatewaySlug": "search_tools",
        }
        score = calculate_tool_relevance_score("search web", "", tool)
        assert score > 0

    def test_calculate_tool_relevance_score_partial_match(self) -> None:
        """Test partial tool relevance match."""
        tool = {
            "name": "file_reader",
            "description": "Read contents from local files",
            "gatewaySlug": "file_tools",
        }
        score = calculate_tool_relevance_score("read file", "", tool)
        assert score > 0

    def test_calculate_tool_relevance_score_no_match(self) -> None:
        """Test no tool relevance match."""
        tool = {
            "name": "database_query",
            "description": "Query database for information",
            "gatewaySlug": "db_tools",
        }
        score = calculate_tool_relevance_score("create image", "", tool)
        assert score == 0

    def test_calculate_tool_relevance_score_with_context(self) -> None:
        """Test tool relevance with context."""
        tool = {
            "name": "web_search",
            "description": "Search the web for information",
            "gatewaySlug": "search_tools",
        }
        score = calculate_tool_relevance_score("search", "web information", tool)
        assert score > 0

    def test_calculate_tool_relevance_score_empty_tool(self) -> None:
        """Test tool relevance with empty tool."""
        tool = {}
        score = calculate_tool_relevance_score("search web", "", tool)
        assert score == 0

    def test_calculate_tool_relevance_score_empty_task(self) -> None:
        """Test tool relevance with empty task."""
        tool = {
            "name": "web_search",
            "description": "Search the web for information",
            "gatewaySlug": "search_tools",
        }
        score = calculate_tool_relevance_score("", "", tool)
        assert score == 0


class TestToolSelection:
    """Test tool selection functionality."""

    @pytest.fixture
    def sample_tools(self) -> list[dict]:
        """Sample tools for testing."""
        return [
            {
                "name": "web_search",
                "description": "Search the web for information",
                "gatewaySlug": "search_tools",
            },
            {
                "name": "file_reader",
                "description": "Read contents from local files",
                "gatewaySlug": "file_tools",
            },
            {
                "name": "database_query",
                "description": "Query database for information",
                "gatewaySlug": "db_tools",
            },
        ]

    def test_select_top_matching_tools_basic(self, sample_tools) -> None:
        """Test basic tool selection."""
        result = select_top_matching_tools(sample_tools, "search web", "", top_n=2)
        assert len(result) == 2
        assert result[0]["name"] == "web_search"
        assert result[1]["name"] in ["file_reader", "database_query"]

    def test_select_top_matching_tools_empty_tools(self) -> None:
        """Test tool selection with empty tools list."""
        result = select_top_matching_tools([], "search web", "", top_n=2)
        assert result == []

    def test_select_top_matching_tools_top_n_zero(self, sample_tools) -> None:
        """Test tool selection with top_n=0."""
        result = select_top_matching_tools(sample_tools, "search web", "", top_n=0)
        assert result == []

    def test_select_top_matching_tools_top_n_greater_than_available(self, sample_tools) -> None:
        """Test tool selection with top_n greater than available tools."""
        result = select_top_matching_tools(sample_tools, "search web", "", top_n=10)
        # Only returns tools with positive scores (web_search matches "search")
        assert len(result) <= 3

    def test_select_top_matching_tools_scoring_order(self, sample_tools) -> None:
        """Test that tools are returned in order of relevance score."""
        result = select_top_matching_tools(sample_tools, "search web", "", top_n=3)

        # First should be web_search (perfect match)
        assert result[0]["name"] == "web_search"

        # Scores should be in descending order
        scores = [calculate_tool_relevance_score("search web", "", tool) for tool in result]
        assert scores == sorted(scores, reverse=True)

    def test_select_top_matching_tools_with_context(self, sample_tools) -> None:
        """Test tool selection with context."""
        result = select_top_matching_tools(sample_tools, "search", "web information", top_n=2)
        assert len(result) == 2
        assert result[0]["name"] == "web_search"

    def test_select_top_matching_tools_complex_query(self, sample_tools) -> None:
        """Test tool selection with complex query."""
        result = select_top_matching_tools(sample_tools, "find information online", "", top_n=1)
        assert len(result) == 1
        assert result[0]["name"] == "web_search"

    def test_select_top_matching_tools_tie_breaking(self, sample_tools) -> None:
        """Test tool selection when scores are tied."""
        # Add a tool with identical score
        sample_tools.append(
            {
                "name": "internet_search",
                "description": "Search the internet for data",
                "gatewaySlug": "search_tools",
            }
        )

        result = select_top_matching_tools(sample_tools, "search web", "", top_n=2)
        assert len(result) == 2
        # Both web_search and internet_search should be top contenders
        top_names = [tool["name"] for tool in result[:2]]
        assert "web_search" in top_names
        assert "internet_search" in top_names
