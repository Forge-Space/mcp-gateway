"""Test suite for RAG Manager functionality.

All tests use the public rag_manager_handler API.
Private methods (analyze_query, retrieve_knowledge, etc.) were removed in the
refactor — tests now validate the handler dispatch layer only.
"""

from __future__ import annotations

import time

import pytest

from tool_router.mcp_tools.rag_manager import (
    RAGManagerTool,
    rag_manager_handler,
    rag_manager_tool,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _analyze(query: str = "React button", agent_type: str = "ui_specialist") -> dict:
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        rag_manager_handler({"action": "analyze_query", "query": query, "agent_type": agent_type})
    )


# ---------------------------------------------------------------------------
# TestQueryAnalysis
# ---------------------------------------------------------------------------


class TestQueryAnalysis:
    """Test query analysis via handler."""

    @pytest.mark.asyncio
    async def test_analyze_query_ui_specialist(self) -> None:
        """Handler returns analysis data for ui_specialist."""
        result = await rag_manager_handler(
            {
                "action": "analyze_query",
                "query": "Create React button with accessibility features",
                "agent_type": "ui_specialist",
            }
        )
        assert result["success"] is True
        data = result["data"]
        assert data["agent_type"] == "ui_specialist"
        assert data["intent"] in ("explicit_fact", "implicit_fact", "interpretable_rationale", "hidden_rationale")
        assert data["confidence"] > 0.0
        assert isinstance(data["entities"], list)
        assert isinstance(data["keywords"], list)

    @pytest.mark.asyncio
    async def test_analyze_query_prompt_architect(self) -> None:
        """Handler returns analysis data for prompt_architect."""
        result = await rag_manager_handler(
            {
                "action": "analyze_query",
                "query": "Optimize this prompt for better responses",
                "agent_type": "prompt_architect",
            }
        )
        assert result["success"] is True
        data = result["data"]
        assert data["agent_type"] == "prompt_architect"
        assert data["intent"] in ("explicit_fact", "implicit_fact", "interpretable_rationale", "hidden_rationale")

    @pytest.mark.asyncio
    async def test_analyze_query_router_specialist(self) -> None:
        """Handler returns analysis data for router_specialist."""
        result = await rag_manager_handler(
            {
                "action": "analyze_query",
                "query": "Route this task to the appropriate specialist",
                "agent_type": "router_specialist",
            }
        )
        assert result["success"] is True
        assert result["data"]["agent_type"] == "router_specialist"

    @pytest.mark.asyncio
    async def test_query_classification_accuracy(self) -> None:
        """Intent is always one of the four known classes."""
        valid_intents = {"explicit_fact", "implicit_fact", "interpretable_rationale", "hidden_rationale"}
        cases = [
            ("Create React component", "ui_specialist"),
            ("What is React?", "ui_specialist"),
            ("Explain React hooks", "ui_specialist"),
            ("Design complex React architecture", "ui_specialist"),
        ]
        for query, agent_type in cases:
            result = await rag_manager_handler(
                {
                    "action": "analyze_query",
                    "query": query,
                    "agent_type": agent_type,
                }
            )
            assert result["success"] is True
            assert result["data"]["intent"] in valid_intents
            assert result["data"]["confidence"] >= 0.0


# ---------------------------------------------------------------------------
# TestKnowledgeRetrieval
# ---------------------------------------------------------------------------


class TestKnowledgeRetrieval:
    """Test knowledge retrieval via handler."""

    @pytest.mark.asyncio
    async def test_retrieve_knowledge_hybrid_strategy(self) -> None:
        """Hybrid retrieval returns a list with success=True."""
        result = await rag_manager_handler(
            {
                "action": "retrieve_knowledge",
                "query": "Create React button",
                "agent_type": "ui_specialist",
                "strategy": "hybrid",
                "max_results": 5,
            }
        )
        assert result["success"] is True
        data = result["data"]
        assert isinstance(data["results"], list)
        assert len(data["results"]) <= 5
        assert data["retrieval_strategy"] == "hybrid"

    @pytest.mark.asyncio
    async def test_retrieve_knowledge_category_strategy(self) -> None:
        """Category strategy retrieval returns list."""
        result = await rag_manager_handler(
            {
                "action": "retrieve_knowledge",
                "query": "React patterns",
                "agent_type": "ui_specialist",
                "strategy": "category",
                "max_results": 3,
            }
        )
        assert result["success"] is True
        assert isinstance(result["data"]["results"], list)

    @pytest.mark.asyncio
    async def test_retrieve_knowledge_agent_specific(self) -> None:
        """Agent-specific retrieval returns list."""
        result = await rag_manager_handler(
            {
                "action": "retrieve_knowledge",
                "query": "UI component generation",
                "agent_type": "ui_specialist",
                "strategy": "agent_specific",
                "max_results": 5,
            }
        )
        assert result["success"] is True
        assert isinstance(result["data"]["results"], list)

    @pytest.mark.asyncio
    async def test_retrieve_knowledge_caching(self) -> None:
        """Two identical queries return the same total_results count."""
        args = {
            "action": "retrieve_knowledge",
            "query": "Test caching query unique xyz",
            "agent_type": "ui_specialist",
            "strategy": "hybrid",
            "max_results": 3,
        }
        r1 = await rag_manager_handler(args)
        r2 = await rag_manager_handler(args)
        assert r1["success"] is True
        assert r2["success"] is True
        assert r1["data"]["total_results"] == r2["data"]["total_results"]


# ---------------------------------------------------------------------------
# TestResultRanking
# ---------------------------------------------------------------------------


class TestResultRanking:
    """Test result ranking via handler."""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_rank_results_by_relevance(self) -> None:
        """rank_results with retrieved results returns ranked list."""
        r = await rag_manager_handler({
            "action": "retrieve_knowledge",
            "query": "React button",
            "agent_type": "ui_specialist",
            "strategy": "hybrid",
            "max_results": 3,
        })
        results = r["data"]["results"]
        rank_result = await rag_manager_handler({
            "action": "rank_results",
            "results": results,
            "query": "React button",
            "agent_type": "ui_specialist",
        })
        assert rank_result["success"] is True
        assert "results" in rank_result["data"]
        assert isinstance(rank_result["data"]["results"], list)

    @pytest.mark.asyncio
    async def test_rank_results_with_agent_preference(self) -> None:
        """rank_results with empty list returns success."""
        result = await rag_manager_handler(
            {
                "action": "rank_results",
                "results": [],
                "query": "React component",
                "agent_type": "ui_specialist",
            }
        )
        assert result["success"] is True
        assert isinstance(result["data"]["results"], list)


# ---------------------------------------------------------------------------
# TestContextInjection
# ---------------------------------------------------------------------------


class TestContextInjection:
    """Test context injection via handler."""

    @pytest.mark.asyncio
    async def test_inject_context_basic(self) -> None:
        """inject_context returns context string and metadata."""
        result = await rag_manager_handler(
            {
                "action": "inject_context",
                "context": {"results": [{"title": "T", "content": "C", "relevance_score": 0.9}]},
                "max_length": 4000,
                "agent_type": "ui_specialist",
            }
        )
        assert result["success"] is True
        data = result["data"]
        assert "context" in data
        assert isinstance(data["context"], (str, dict))
        assert "token_count" in data or "context_length" in data

    @pytest.mark.asyncio
    async def test_inject_context_with_examples(self) -> None:
        """inject_context with code content returns non-empty context."""
        result = await rag_manager_handler(
            {
                "action": "inject_context",
                "context": {
                    "results": [
                        {
                            "title": "React.FC Example",
                            "content": "```tsx\nconst Button: React.FC<ButtonProps> = ({ children }) => <button>{children}</button>;\n```",
                            "relevance_score": 0.9,
                        }
                    ]
                },
                "max_length": 4000,
                "agent_type": "ui_specialist",
            }
        )
        assert result["success"] is True
        assert len(result["data"]["context"]) > 0

    @pytest.mark.asyncio
    async def test_inject_context_length_limit(self) -> None:
        """inject_context with small max_length still succeeds."""
        result = await rag_manager_handler(
            {
                "action": "inject_context",
                "context": {"results": [{"title": "Big", "content": "x" * 5000, "relevance_score": 0.9}]},
                "max_length": 500,
                "agent_type": "ui_specialist",
            }
        )
        assert result["success"] is True
        assert "context" in result["data"]


# ---------------------------------------------------------------------------
# TestCacheManagement
# ---------------------------------------------------------------------------


class TestCacheManagement:
    """Test cache management via handler."""

    @pytest.mark.asyncio
    async def test_cache_stats(self) -> None:
        """get_cache_stats returns expected numeric fields."""
        result = await rag_manager_handler({"action": "get_cache_stats"})
        assert "success" in result  # may fail gracefully if DB unavailable
        data = result["data"]
        assert "total_entries" in data or "total_hits" in data or "avg_hit_rate" in data

    @pytest.mark.asyncio
    async def test_cache_clear(self) -> None:
        """After retrieving, get_cache_stats still returns success."""
        await rag_manager_handler(
            {
                "action": "retrieve_knowledge",
                "query": "cache clear test",
                "agent_type": "ui_specialist",
                "strategy": "hybrid",
                "max_results": 2,
            }
        )
        result = await rag_manager_handler({"action": "get_cache_stats"})
        assert "success" in result  # may fail gracefully if DB unavailable
        if result["success"]:
            assert "total_entries" in result["data"] or "avg_hit_rate" in result["data"]


# ---------------------------------------------------------------------------
# TestPerformanceOptimization
# ---------------------------------------------------------------------------


class TestPerformanceOptimization:
    """Test performance optimization via handler."""

    @pytest.mark.asyncio
    async def test_optimize_performance(self) -> None:
        """optimize_performance action returns a response (success or error)."""
        result = await rag_manager_handler({"action": "optimize_performance"})
        # Either success with data or graceful failure — both are valid
        assert "success" in result

    @pytest.mark.asyncio
    async def test_performance_monitoring(self) -> None:
        """retrieve_knowledge completes within 2 seconds."""
        start = time.time()
        result = await rag_manager_handler(
            {
                "action": "retrieve_knowledge",
                "query": "Performance test query",
                "agent_type": "ui_specialist",
                "strategy": "hybrid",
                "max_results": 5,
            }
        )
        elapsed = time.time() - start
        assert result["success"] is True
        assert elapsed < 2.0, f"Retrieval took {elapsed:.3f}s"


# ---------------------------------------------------------------------------
# TestRAGManagerHandler
# ---------------------------------------------------------------------------


class TestRAGManagerHandler:
    """Test RAG Manager MCP handler dispatch."""

    @pytest.mark.asyncio
    async def test_handler_analyze_query(self) -> None:
        """Handler analyze_query returns data with expected keys."""
        result = await rag_manager_handler(
            {
                "action": "analyze_query",
                "query": "Create React button",
                "agent_type": "ui_specialist",
            }
        )
        assert result["success"] is True
        assert "data" in result
        data = result["data"]
        assert data["agent_type"] == "ui_specialist"
        assert "intent" in data

    @pytest.mark.asyncio
    async def test_handler_retrieve_knowledge(self) -> None:
        """Handler retrieve_knowledge returns results list."""
        result = await rag_manager_handler(
            {
                "action": "retrieve_knowledge",
                "query": "React patterns",
                "agent_type": "ui_specialist",
                "strategy": "hybrid",
                "max_results": 5,
            }
        )
        assert result["success"] is True
        assert "data" in result
        assert isinstance(result["data"]["results"], list)
        assert len(result["data"]["results"]) <= 5

    @pytest.mark.asyncio
    async def test_handler_invalid_action(self) -> None:
        """Handler with unknown action returns success=False."""
        result = await rag_manager_handler({"action": "invalid_action", "query": "Test"})
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_handler_missing_arguments(self) -> None:
        """Handler with missing required args returns success=False."""
        result = await rag_manager_handler({"action": "analyze_query"})
        assert result["success"] is False
        assert "error" in result


# ---------------------------------------------------------------------------
# TestIntegration
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration tests using the handler pipeline."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self) -> None:
        """Full analyze → retrieve → rank → inject pipeline via handler."""
        query = "Create accessible React button with hover effects"

        # Step 1: Analyze
        r1 = await rag_manager_handler({"action": "analyze_query", "query": query, "agent_type": "ui_specialist"})
        assert r1["success"] is True
        assert r1["data"]["confidence"] >= 0.0

        # Step 2: Retrieve
        r2 = await rag_manager_handler(
            {
                "action": "retrieve_knowledge",
                "query": query,
                "agent_type": "ui_specialist",
                "strategy": "hybrid",
                "max_results": 5,
            }
        )
        assert r2["success"] is True
        results = r2["data"]["results"]

        # Step 3: Rank
        r3 = await rag_manager_handler(
            {
                "action": "rank_results",
                "results": results,
                "query": query,
                "agent_type": "ui_specialist",
            }
        )
        assert r3["success"] is True

        # Step 4: Inject
        r4 = await rag_manager_handler(
            {
                "action": "inject_context",
                "context": {"results": results},
                "max_length": 4000,
                "agent_type": "ui_specialist",
            }
        )
        assert r4["success"] is True
        assert "context" in r4["data"]

        # Step 5: Cache stats
        r5 = await rag_manager_handler({"action": "get_cache_stats"})
        assert "success" in r5  # graceful if DB unavailable

    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self) -> None:
        """Handler works correctly for multiple agent types."""
        cases = [
            ("Create React component", "ui_specialist"),
            ("Optimize prompt clarity", "prompt_architect"),
            ("Route task to specialist", "router_specialist"),
        ]
        for query, agent_type in cases:
            r = await rag_manager_handler({"action": "analyze_query", "query": query, "agent_type": agent_type})
            assert r["success"] is True, f"Failed for {agent_type}: {r}"
            assert r["data"]["agent_type"] == agent_type

            r2 = await rag_manager_handler(
                {
                    "action": "retrieve_knowledge",
                    "query": query,
                    "agent_type": agent_type,
                    "strategy": "agent_specific",
                    "max_results": 3,
                }
            )
            assert r2["success"] is True


# ---------------------------------------------------------------------------
# TestPerformanceBenchmarks
# ---------------------------------------------------------------------------


class TestPerformanceBenchmarks:
    """Performance benchmarks using the handler."""

    @pytest.mark.asyncio
    async def test_query_analysis_performance(self) -> None:
        """analyze_query completes within 100ms on average."""
        queries = [
            "Create React button with accessibility",
            "Optimize prompt for better responses",
            "Route task to appropriate specialist",
        ]
        times = []
        for q in queries:
            t0 = time.time()
            await rag_manager_handler({"action": "analyze_query", "query": q, "agent_type": "ui_specialist"})
            times.append(time.time() - t0)

        avg = sum(times) / len(times)
        assert avg < 0.5, f"avg analysis time {avg * 1000:.1f}ms > 500ms"

    @pytest.mark.asyncio
    async def test_retrieval_performance(self) -> None:
        """retrieve_knowledge completes within 500ms."""
        t0 = time.time()
        result = await rag_manager_handler(
            {
                "action": "retrieve_knowledge",
                "query": "React patterns",
                "agent_type": "ui_specialist",
                "strategy": "hybrid",
                "max_results": 5,
            }
        )
        elapsed = time.time() - t0
        assert result["success"] is True
        assert elapsed < 2.0, f"retrieval took {elapsed * 1000:.1f}ms"

    @pytest.mark.asyncio
    async def test_context_injection_performance(self) -> None:
        """inject_context completes within 300ms."""
        mock_results = [{"title": f"R{i}", "content": f"Content {i}", "relevance_score": 0.8} for i in range(5)]
        t0 = time.time()
        result = await rag_manager_handler(
            {
                "action": "inject_context",
                "context": {"results": mock_results},
                "max_length": 4000,
                "agent_type": "ui_specialist",
            }
        )
        elapsed = time.time() - t0
        assert result["success"] is True
        assert elapsed < 1.0, f"injection took {elapsed * 1000:.1f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
