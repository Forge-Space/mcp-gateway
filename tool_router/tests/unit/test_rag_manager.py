"""
Unit tests for tool_router/mcp_tools/rag_manager.py

The module instantiates RAGManagerTool() at import time (calls sqlite3.connect).
We patch sqlite3.connect before importing to avoid FS side-effects.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers to build a fresh RAGManagerTool with sqlite3 mocked
# ---------------------------------------------------------------------------


def _make_tool() -> Any:
    """Return a fresh RAGManagerTool with a mocked sqlite3 connection."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = MagicMock()
    mock_conn.row_factory = None

    mock_kb = MagicMock()
    mock_kb.get_patterns_by_category.return_value = []
    mock_kb.search_patterns.return_value = []
    mock_kb.get_pattern.return_value = None

    with (
        patch("tool_router.mcp_tools.rag_manager.sqlite3.connect", return_value=mock_conn),
        patch("tool_router.mcp_tools.rag_manager.KnowledgeBase", return_value=mock_kb),
    ):
        # Re-import to get a tool with fresh mocked deps
        import tool_router.mcp_tools.rag_manager as mod

        tool = mod.RAGManagerTool()
        tool.conn = mock_conn
        tool.knowledge_base = mock_kb
        return tool


def _make_result(**kwargs: Any) -> Any:
    """Build a RetrievalResult with sensible defaults."""
    import tool_router.mcp_tools.rag_manager as mod

    defaults = {
        "item_id": 1,
        "title": "Test Pattern",
        "content": "Some content",
        "category": "ui_component",
        "confidence": 0.8,
        "effectiveness": 0.7,
        "relevance_score": 0.75,
        "source_type": "manual",
        "freshness_score": 1.0,
        "agent_specific": False,
        "agent_types": [],
        "agent_type": "ui_specialist",
    }
    defaults.update(kwargs)
    return mod.RetrievalResult(**defaults)


def _make_context(keywords: list[str] | None = None) -> Any:
    """Build a RetrievalContext with a QueryAnalysis."""
    import tool_router.mcp_tools.rag_manager as mod

    qa = mod.QueryAnalysis(
        intent="explicit_fact",
        entities=[],
        keywords=keywords or ["component", "button"],
        agent_type="ui_specialist",
        complexity="simple",
        confidence=0.8,
    )
    return mod.RetrievalContext(
        query="Create a button component",
        query_analysis=qa,
        agent_type="ui_specialist",
        retrieval_strategy="hybrid",
        max_results=10,
        context_length=4000,
        filters={},
    )


# ---------------------------------------------------------------------------
# Patch the module-level singleton on import
# ---------------------------------------------------------------------------

# Ensure the module can be imported without hitting the FS
_mock_conn_global = MagicMock()
_mock_conn_global.cursor.return_value = MagicMock()
_mock_kb_global = MagicMock()
_mock_kb_global.get_patterns_by_category.return_value = []
_mock_kb_global.search_patterns.return_value = []

with (
    patch("tool_router.mcp_tools.rag_manager.sqlite3.connect", return_value=_mock_conn_global),
    patch("tool_router.mcp_tools.rag_manager.KnowledgeBase", return_value=_mock_kb_global),
):
    import tool_router.mcp_tools.rag_manager as rag_mod


# ---------------------------------------------------------------------------
# Dataclass tests
# ---------------------------------------------------------------------------


class TestQueryAnalysis:
    def test_basic_construction(self) -> None:
        qa = rag_mod.QueryAnalysis(
            intent="explicit_fact",
            entities=["React"],
            keywords=["button", "component"],
            agent_type="ui_specialist",
            complexity="simple",
            confidence=0.9,
        )
        assert qa.intent == "explicit_fact"
        assert qa.entities == ["React"]
        assert qa.confidence == 0.9

    def test_all_intent_values(self) -> None:
        for intent in ["explicit_fact", "implicit_fact", "interpretable_rationale", "hidden_rationale"]:
            qa = rag_mod.QueryAnalysis(
                intent=intent,
                entities=[],
                keywords=[],
                agent_type="ui_specialist",
                complexity="simple",
                confidence=0.5,
            )
            assert qa.intent == intent


class TestRetrievalResult:
    def test_defaults(self) -> None:
        r = _make_result()
        assert r.item_id == 1
        assert r.agent_type == "ui_specialist"
        assert r.agent_specific is False

    def test_agent_type_default_empty(self) -> None:
        r = rag_mod.RetrievalResult(
            item_id=2,
            title="T",
            content="C",
            category="cat",
            confidence=0.5,
            effectiveness=0.5,
            relevance_score=0.5,
            source_type="manual",
            freshness_score=1.0,
            agent_specific=False,
            agent_types=[],
        )
        assert r.agent_type == ""


class TestRAGManagerError:
    def test_is_exception(self) -> None:
        err = rag_mod.RAGManagerError("boom")
        assert isinstance(err, Exception)
        assert str(err) == "boom"


# ---------------------------------------------------------------------------
# RAGManagerTool lifecycle tests
# ---------------------------------------------------------------------------


class TestRAGManagerToolLifecycle:
    def test_init_connects_to_db(self) -> None:
        mock_conn = MagicMock()
        with (
            patch("tool_router.mcp_tools.rag_manager.sqlite3.connect", return_value=mock_conn) as mock_connect,
            patch("tool_router.mcp_tools.rag_manager.KnowledgeBase"),
        ):
            tool = rag_mod.RAGManagerTool()
            mock_connect.assert_called_once_with("data/knowledge_base.db")
            assert tool.conn is mock_conn

    def test_init_raises_rag_error_on_db_failure(self) -> None:
        with (
            patch("tool_router.mcp_tools.rag_manager.sqlite3.connect", side_effect=Exception("no db")),
            patch("tool_router.mcp_tools.rag_manager.KnowledgeBase"),
        ):
            with pytest.raises(rag_mod.RAGManagerError, match="Database connection failed"):
                rag_mod.RAGManagerTool()

    def test_close_sets_conn_to_none(self) -> None:
        tool = _make_tool()
        tool.close()
        assert tool.conn is None

    def test_close_safe_to_call_twice(self) -> None:
        tool = _make_tool()
        tool.close()
        tool.close()  # should not raise

    def test_context_manager(self) -> None:
        tool = _make_tool()
        with tool as t:
            assert t is tool
        assert tool.conn is None


# ---------------------------------------------------------------------------
# Sync helper tests
# ---------------------------------------------------------------------------


class TestClassifyIntent:
    def test_ui_specialist_create(self) -> None:
        tool = _make_tool()
        assert tool._classify_intent("create a button", "ui_specialist") == "implicit_fact"

    def test_ui_specialist_how_to(self) -> None:
        tool = _make_tool()
        assert tool._classify_intent("how to style a component", "ui_specialist") == "interpretable_rationale"

    def test_ui_specialist_debug(self) -> None:
        tool = _make_tool()
        assert tool._classify_intent("fix the error", "ui_specialist") == "hidden_rationale"

    def test_ui_specialist_default(self) -> None:
        tool = _make_tool()
        assert tool._classify_intent("list all components", "ui_specialist") == "explicit_fact"

    def test_prompt_architect_optimize(self) -> None:
        tool = _make_tool()
        assert tool._classify_intent("optimize my prompt", "prompt_architect") == "interpretable_rationale"

    def test_prompt_architect_template(self) -> None:
        tool = _make_tool()
        assert tool._classify_intent("use a template pattern", "prompt_architect") == "implicit_fact"

    def test_router_specialist_route(self) -> None:
        tool = _make_tool()
        assert tool._classify_intent("route this task", "router_specialist") == "interpretable_rationale"

    def test_unknown_agent_type_returns_explicit_fact(self) -> None:
        tool = _make_tool()
        assert tool._classify_intent("anything", "unknown_agent") == "explicit_fact"


class TestExtractKeywordsAndEntities:
    def test_extract_keywords_removes_stop_words(self) -> None:
        tool = _make_tool()
        keywords = tool._extract_keywords("the button component")
        assert "the" not in keywords
        assert "button" in keywords
        assert "component" in keywords

    def test_extract_keywords_min_length(self) -> None:
        tool = _make_tool()
        # "on" is a stop word, "do" has length 2 (excluded by >2)
        keywords = tool._extract_keywords("do on it")
        assert keywords == []

    def test_extract_entities_react(self) -> None:
        tool = _make_tool()
        entities = tool._extract_entities("Use React. and useState.")
        assert any("React" in e for e in entities)

    def test_extract_entities_empty(self) -> None:
        tool = _make_tool()
        entities = tool._extract_entities("plain query with no frameworks")
        assert entities == []


class TestAssessComplexity:
    def test_simple(self) -> None:
        tool = _make_tool()
        assert tool._assess_complexity("short query") == "simple"

    def test_moderate(self) -> None:
        tool = _make_tool()
        query = "create a button that handles click events and submits form data"
        assert tool._assess_complexity(query) == "moderate"

    def test_complex(self) -> None:
        tool = _make_tool()
        query = " ".join(["word"] * 20)
        assert tool._assess_complexity(query) == "complex"


class TestCalculateConfidence:
    def test_explicit_fact_boosts_confidence(self) -> None:
        tool = _make_tool()
        conf = tool._calculate_confidence("test", "explicit_fact", [])
        assert conf >= 0.8

    def test_capped_at_1(self) -> None:
        tool = _make_tool()
        # Many entities + explicit_fact + many keywords
        entities = ["React.", "useState.", "Button.", "Form.", "Input."]
        conf = tool._calculate_confidence("long query with many keywords and details here", "explicit_fact", entities)
        assert conf <= 1.0

    def test_implicit_fact_lower_than_explicit(self) -> None:
        tool = _make_tool()
        c1 = tool._calculate_confidence("test", "explicit_fact", [])
        c2 = tool._calculate_confidence("test", "implicit_fact", [])
        assert c1 > c2


class TestDeduplicateAndRank:
    def test_deduplicate_removes_duplicates(self) -> None:
        tool = _make_tool()
        r1 = _make_result(item_id=1)
        r2 = _make_result(item_id=1)  # same id
        r3 = _make_result(item_id=2)
        result = tool._deduplicate_results([r1, r2, r3])
        assert len(result) == 2
        assert {r.item_id for r in result} == {1, 2}

    def test_rank_results_sorts_by_score(self) -> None:
        tool = _make_tool()
        r1 = _make_result(item_id=1, relevance_score=0.5)
        r2 = _make_result(item_id=2, relevance_score=0.9)
        ctx = _make_context()
        ranked = tool._rank_results([r1, r2], ctx)
        assert ranked[0].item_id == 2  # higher score first

    def test_rank_results_mutates_relevance(self) -> None:
        tool = _make_tool()
        r = _make_result(item_id=1, relevance_score=0.5)
        ctx = _make_context()
        tool._rank_results([r], ctx)
        # score should be updated (boosted by confidence/effectiveness)
        assert r.relevance_score >= 0.5

    def test_rank_results_caps_at_1(self) -> None:
        tool = _make_tool()
        r = _make_result(item_id=1, relevance_score=1.0, confidence=1.0, effectiveness=1.0)
        ctx = _make_context()
        tool._rank_results([r], ctx)
        assert r.relevance_score <= 1.0


class TestExtractCodeExamples:
    def test_extracts_fenced_block(self) -> None:
        tool = _make_tool()
        content = "```typescript\nconst x = 1;\n```"
        examples = tool._extract_code_examples(content)
        assert any("const x = 1" in e for e in examples)

    def test_no_code_returns_empty(self) -> None:
        tool = _make_tool()
        examples = tool._extract_code_examples("plain text no code here")
        assert isinstance(examples, list)


class TestGenerateQueryPattern:
    def test_normalizes_to_five_words(self) -> None:
        tool = _make_tool()
        pattern = tool._generate_query_pattern("create a beautiful button component quickly efficiently now")
        words = pattern.split()
        assert len(words) <= 5

    def test_removes_stop_words(self) -> None:
        tool = _make_tool()
        pattern = tool._generate_query_pattern("the button in the form")
        assert "the" not in pattern


class TestResultToDict:
    def test_serializes_all_fields(self) -> None:
        tool = _make_tool()
        r = _make_result(item_id=42, title="My Title")
        d = tool._result_to_dict(r)
        assert d["item_id"] == 42
        assert d["title"] == "My Title"
        assert "relevance_score" in d
        assert "agent_types" in d

    def test_excludes_agent_type_field(self) -> None:
        tool = _make_tool()
        r = _make_result()
        d = tool._result_to_dict(r)
        assert "agent_type" not in d


# ---------------------------------------------------------------------------
# Async handler tests
# ---------------------------------------------------------------------------


class TestGetQueryAnalysis:
    @pytest.mark.asyncio
    async def test_returns_query_analysis(self) -> None:
        tool = _make_tool()
        analysis = await tool._get_query_analysis("create a button", "ui_specialist")
        assert isinstance(analysis, rag_mod.QueryAnalysis)
        assert analysis.agent_type == "ui_specialist"
        assert analysis.intent in {"implicit_fact", "explicit_fact", "interpretable_rationale", "hidden_rationale"}

    @pytest.mark.asyncio
    async def test_complexity_assessed(self) -> None:
        tool = _make_tool()
        analysis = await tool._get_query_analysis("small", "ui_specialist")
        assert analysis.complexity == "simple"


class TestRetrieveByCategory:
    @pytest.mark.asyncio
    async def test_returns_results_from_knowledge_base(self) -> None:
        tool = _make_tool()
        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.title = "T"
        mock_item.content = "C"
        mock_item.category = MagicMock()
        mock_item.category.value = "ui_component"
        mock_item.confidence_score = 0.8
        mock_item.effectiveness_score = 0.7
        tool.knowledge_base.get_patterns_by_category.return_value = [mock_item]

        ctx = _make_context()
        results = await tool._retrieve_by_category(ctx)
        assert len(results) >= 1
        assert results[0].item_id == 1

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self) -> None:
        tool = _make_tool()
        tool.knowledge_base.get_patterns_by_category.side_effect = RuntimeError("fail")
        ctx = _make_context()
        results = await tool._retrieve_by_category(ctx)
        assert results == []


class TestRetrieveFulltext:
    @pytest.mark.asyncio
    async def test_returns_results(self) -> None:
        tool = _make_tool()
        mock_item = MagicMock()
        mock_item.id = 5
        mock_item.title = "FTS Result"
        mock_item.content = "content here"
        mock_item.category = MagicMock()
        mock_item.category.value = "react_pattern"
        mock_item.confidence_score = 0.7
        tool.knowledge_base.search_patterns.return_value = [mock_item]

        ctx = _make_context()
        results = await tool._retrieve_fulltext(ctx)
        assert len(results) == 1
        assert results[0].item_id == 5

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self) -> None:
        tool = _make_tool()
        tool.knowledge_base.search_patterns.side_effect = RuntimeError("boom")
        ctx = _make_context()
        results = await tool._retrieve_fulltext(ctx)
        assert results == []


class TestRetrieveVector:
    @pytest.mark.asyncio
    async def test_always_returns_empty(self) -> None:
        tool = _make_tool()
        ctx = _make_context()
        results = await tool._retrieve_vector(ctx)
        assert results == []


class TestInjectContext:
    @pytest.mark.asyncio
    async def test_injects_patterns_and_examples(self) -> None:
        tool = _make_tool()
        result = _make_result(content="```typescript\nconst x = 1;\n```")
        ctx = _make_context()
        ctx_data = await tool._inject_context([result], ctx)
        assert "patterns" in ctx_data
        assert len(ctx_data["patterns"]) == 1

    @pytest.mark.asyncio
    async def test_respects_context_length(self) -> None:
        tool = _make_tool()
        # Make a result with very long content
        long_content = "x" * 5000
        r = _make_result(content=long_content)
        # context_length = 100 — result won't fit
        ctx = _make_context()
        ctx.context_length = 100
        ctx_data = await tool._inject_context([r], ctx)
        assert len(ctx_data["patterns"]) == 0

    @pytest.mark.asyncio
    async def test_examples_extracted_from_top_3(self) -> None:
        tool = _make_tool()
        results = [_make_result(item_id=i, content="```typescript\nconst x = 1;\n```") for i in range(5)]
        ctx = _make_context()
        ctx_data = await tool._inject_context(results, ctx)
        assert isinstance(ctx_data["examples"], list)


# ---------------------------------------------------------------------------
# Handler action tests
# ---------------------------------------------------------------------------


class TestHandleAnalyzeQuery:
    @pytest.mark.asyncio
    async def test_returns_success(self) -> None:
        tool = _make_tool()
        result = await tool.rag_manager_handler({"action": "analyze_query", "query": "create a button"})
        assert result["success"] is True
        data = result["data"]
        assert "intent" in data
        assert "keywords" in data
        assert "complexity" in data
        assert "confidence" in data

    @pytest.mark.asyncio
    async def test_default_agent_type(self) -> None:
        tool = _make_tool()
        result = await tool.rag_manager_handler({"action": "analyze_query", "query": "test"})
        assert result["data"]["agent_type"] == "ui_specialist"


class TestHandleRetrieveKnowledge:
    @pytest.mark.asyncio
    async def test_returns_success_no_results(self) -> None:
        tool = _make_tool()
        # Make _check_cache return None, retrieve returns []
        tool._check_cache = AsyncMock(return_value=None)
        result = await tool.rag_manager_handler(
            {"action": "retrieve_knowledge", "query": "button", "agent_type": "ui_specialist"}
        )
        assert result["success"] is True
        assert result["data"]["total_results"] == 0
        assert result["data"]["cache_hit"] is False

    @pytest.mark.asyncio
    async def test_returns_cached_results(self) -> None:
        tool = _make_tool()
        mock_cached = {
            "retrieved_items": [1],
            "query_hash": "abc",
            "timestamp": "now",
            "hit_count": 1,
            "ttl": 3600,
            "cache_level": "memory",
        }
        tool._check_cache = AsyncMock(return_value=mock_cached)

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.title = "T"
        mock_item.content = "C"
        mock_item.category = "cat"
        mock_item.confidence_score = 0.8
        mock_item.effectiveness_score = 0.7
        mock_item.source_type = "manual"
        mock_item.agent_specific = False
        tool.knowledge_base.get_pattern.return_value = mock_item

        result = await tool.rag_manager_handler({"action": "retrieve_knowledge", "query": "button"})
        assert result["success"] is True
        assert result["data"]["cache_hit"] is True


class TestHandleRankResults:
    @pytest.mark.asyncio
    async def test_ranks_provided_results(self) -> None:
        tool = _make_tool()
        results_data = [
            {
                "item_id": 1,
                "title": "T1",
                "content": "c1",
                "category": "cat",
                "confidence": 0.5,
                "effectiveness": 0.5,
                "relevance_score": 0.5,
                "source_type": "manual",
                "freshness_score": 1.0,
                "agent_specific": False,
                "agent_types": [],
            }
        ]
        result = await tool.rag_manager_handler(
            {"action": "rank_results", "results": results_data, "query_analysis": {}}
        )
        assert result["success"] is True
        assert result["data"]["ranking_strategy"] == "multi_factor"
        assert len(result["data"]["results"]) == 1

    @pytest.mark.asyncio
    async def test_empty_results(self) -> None:
        tool = _make_tool()
        result = await tool.rag_manager_handler({"action": "rank_results", "results": [], "query_analysis": {}})
        assert result["success"] is True
        assert result["data"]["total_results"] == 0


class TestHandleInjectContext:
    @pytest.mark.asyncio
    async def test_injects_context(self) -> None:
        tool = _make_tool()
        result = await tool.rag_manager_handler(
            {"action": "inject_context", "ranked_results": [], "agent_type": "ui_specialist"}
        )
        assert result["success"] is True
        assert "context" in result["data"]
        assert "items_included" in result["data"]

    @pytest.mark.asyncio
    async def test_with_results(self) -> None:
        tool = _make_tool()
        result_data = [
            {
                "item_id": 1,
                "title": "T",
                "content": "short content",
                "category": "cat",
                "confidence": 0.8,
                "effectiveness": 0.7,
                "relevance_score": 0.8,
                "source_type": "manual",
                "freshness_score": 1.0,
                "agent_specific": False,
                "agent_types": [],
            }
        ]
        result = await tool.rag_manager_handler(
            {"action": "inject_context", "ranked_results": result_data, "agent_type": "ui_specialist"}
        )
        assert result["success"] is True
        assert result["data"]["items_included"] >= 1


class TestHandleGetCacheStats:
    @pytest.mark.asyncio
    async def test_returns_empty_stats_when_no_table(self) -> None:
        tool = _make_tool()
        # Mock cursor to return None for sqlite_master check
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        tool.conn.cursor.return_value = mock_cursor

        result = await tool.rag_manager_handler({"action": "get_cache_stats"})
        assert result["success"] is True
        assert result["data"]["total_entries"] == 0
        assert result["data"]["by_level"] == {}

    @pytest.mark.asyncio
    async def test_returns_failure_on_exception(self) -> None:
        tool = _make_tool()
        tool.conn.cursor.side_effect = RuntimeError("cursor fail")
        result = await tool.rag_manager_handler({"action": "get_cache_stats"})
        assert result["success"] is False


class TestHandleOptimizePerformance:
    @pytest.mark.asyncio
    async def test_no_data_returns_false(self) -> None:
        tool = _make_tool()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        tool.conn.cursor.return_value = mock_cursor

        result = await tool.rag_manager_handler({"action": "optimize_performance", "agent_type": "ui_specialist"})
        assert result["success"] is False
        assert "No performance data" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_with_data_returns_recommendations(self) -> None:
        tool = _make_tool()
        mock_row = MagicMock()
        mock_row.__getitem__.side_effect = lambda k: {
            "current_latency": 2.0,
            "current_success_rate": 0.6,
            "current_satisfaction": 0.7,
            "current_cache_hit_rate": 0.5,
        }[k]
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = mock_row
        tool.conn.cursor.return_value = mock_cursor

        result = await tool.rag_manager_handler(
            {"action": "optimize_performance", "agent_type": "ui_specialist", "performance_target": "latency"}
        )
        assert result["success"] is True
        assert "recommendations" in result["data"]


class TestHandleUnknownAction:
    @pytest.mark.asyncio
    async def test_unknown_action_returns_failure(self) -> None:
        tool = _make_tool()
        result = await tool.rag_manager_handler({"action": "nonexistent_action"})
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_missing_action_returns_failure(self) -> None:
        tool = _make_tool()
        result = await tool.rag_manager_handler({})
        assert result["success"] is False


class TestCheckCacheAndSetCache:
    @pytest.mark.asyncio
    async def test_check_cache_returns_none_on_exception(self) -> None:
        tool = _make_tool()
        tool.conn.cursor.side_effect = RuntimeError("fail")
        result = await tool._check_cache("mykey")
        assert result is None

    @pytest.mark.asyncio
    async def test_check_cache_returns_none_on_no_row(self) -> None:
        tool = _make_tool()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        tool.conn.cursor.return_value = mock_cursor
        result = await tool._check_cache("mykey")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_cache_swallows_exceptions(self) -> None:
        tool = _make_tool()
        tool.conn.cursor.side_effect = RuntimeError("fail")
        # Should not raise
        await tool._set_cache("key", [1, 2, 3])


class TestUpdatePerformanceMetrics:
    @pytest.mark.asyncio
    async def test_swallows_exceptions(self) -> None:
        tool = _make_tool()
        tool.conn.cursor.side_effect = RuntimeError("db fail")
        # Should not raise
        await tool._update_performance_metrics("query", "ui_specialist", {}, {})


class TestGetRelevantCategories:
    def test_all_agents_get_base_categories(self) -> None:
        tool = _make_tool()
        cats = tool._get_relevant_categories("unknown", "")
        assert len(cats) >= 2  # UI_COMPONENT and REACT_PATTERN

    def test_ui_specialist_gets_accessibility(self) -> None:
        tool = _make_tool()
        cats = tool._get_relevant_categories("ui_specialist", "")
        cat_values = [getattr(c, "value", str(c)) for c in cats]
        assert any("accessibility" in str(v).lower() for v in cat_values)

    def test_prompt_architect_gets_prompt_engineering(self) -> None:
        tool = _make_tool()
        cats = tool._get_relevant_categories("prompt_architect", "")
        cat_values = [getattr(c, "value", str(c)) for c in cats]
        assert any("prompt" in str(v).lower() for v in cat_values)

    def test_router_specialist_gets_performance(self) -> None:
        tool = _make_tool()
        cats = tool._get_relevant_categories("router_specialist", "")
        cat_values = [getattr(c, "value", str(c)) for c in cats]
        assert any("performance" in str(v).lower() for v in cat_values)


class TestModuleLevelSchema:
    def test_schema_is_dict(self) -> None:
        assert isinstance(rag_mod.RAG_MANAGER_SCHEMA, dict)

    def test_schema_has_required_action(self) -> None:
        assert "action" in rag_mod.RAG_MANAGER_SCHEMA.get("required", [])

    def test_schema_has_action_enum(self) -> None:
        actions = rag_mod.RAG_MANAGER_SCHEMA["properties"]["action"]["enum"]
        assert "analyze_query" in actions
        assert "retrieve_knowledge" in actions
        assert "optimize_performance" in actions
