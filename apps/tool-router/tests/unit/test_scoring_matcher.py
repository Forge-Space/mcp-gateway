"""Unit tests for scoring matcher."""

from __future__ import annotations

from tool_router.scoring.matcher import (
    _calculate_substring_match_score,
    _enrich_tokens_with_synonyms,
    _extract_normalized_tokens,
    calculate_tool_relevance_score,
)


class TestTokenExtraction:
    """Tests for token extraction."""

    def test_extract_normalized_tokens_basic(self):
        """Test basic token extraction."""
        tokens = _extract_normalized_tokens("Hello World")
        assert tokens == {"hello", "world"}

    def test_extract_normalized_tokens_special_chars(self):
        """Test token extraction with special characters."""
        tokens = _extract_normalized_tokens("file-system_test.py")
        assert "file" in tokens
        assert "system" in tokens
        assert "test" in tokens
        assert "py" in tokens

    def test_extract_normalized_tokens_empty(self):
        """Test empty string."""
        tokens = _extract_normalized_tokens("")
        assert tokens == set()


class TestSynonymEnrichment:
    """Tests for synonym enrichment."""

    def test_enrich_with_synonyms(self):
        """Test synonym expansion."""
        tokens = {"search"}
        enriched = _enrich_tokens_with_synonyms(tokens)
        assert "search" in enriched
        assert "find" in enriched
        assert "lookup" in enriched

    def test_enrich_no_synonyms(self):
        """Test tokens without synonyms."""
        tokens = {"unique", "token"}
        enriched = _enrich_tokens_with_synonyms(tokens)
        assert enriched == tokens


class TestSubstringMatching:
    """Tests for substring matching."""

    def test_substring_match_found(self):
        """Test substring match scoring."""
        tokens = {"file"}
        score = _calculate_substring_match_score(tokens, "filesystem")
        assert score > 0

    def test_substring_match_not_found(self):
        """Test no substring match."""
        tokens = {"xyz"}
        score = _calculate_substring_match_score(tokens, "filesystem")
        assert score == 0

    def test_substring_match_short_token(self):
        """Test short tokens are ignored."""
        tokens = {"ab"}
        score = _calculate_substring_match_score(tokens, "abstract")
        assert score == 0


class TestToolRelevanceScore:
    """Tests for tool relevance scoring."""

    def test_exact_name_match(self):
        """Test exact tool name match."""
        tool = {
            "name": "search_files",
            "description": "Search for files",
            "gatewaySlug": "filesystem",
        }
        score = calculate_tool_relevance_score("search files", "", tool)
        assert score > 0

    def test_description_match(self):
        """Test description matching."""
        tool = {
            "name": "tool1",
            "description": "Search and find files",
            "gatewaySlug": "fs",
        }
        score = calculate_tool_relevance_score("search", "", tool)
        assert score > 0

    def test_gateway_match(self):
        """Test gateway slug matching."""
        tool = {
            "name": "list",
            "description": "List items",
            "gatewaySlug": "github",
        }
        score = calculate_tool_relevance_score("github", "", tool)
        assert score > 0

    def test_empty_query(self):
        """Test empty query returns zero score."""
        tool = {"name": "test", "description": "Test tool"}
        score = calculate_tool_relevance_score("", "", tool)
        assert score == 0.0

    def test_context_included(self):
        """Test context is included in scoring."""
        tool = {
            "name": "create_file",
            "description": "Create a new file",
        }
        score = calculate_tool_relevance_score("create", "filesystem", tool)
        assert score > 0

    def test_synonym_matching(self):
        """Test synonym-based matching."""
        tool = {
            "name": "find_files",
            "description": "Find files in directory",
        }
        # "search" is a synonym of "find"
        score = calculate_tool_relevance_score("search", "", tool)
        assert score > 0
