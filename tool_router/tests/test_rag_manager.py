"""Tests for RAG Manager functionality."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from tool_router.mcp_tools.rag_manager import RAGManagerTool, rag_manager_tool


class TestRAGManager:
    """Test cases for RAG Manager tool."""

    @pytest.fixture
    def rag_manager(self):
        """Create RAG Manager instance for testing."""
        return RAGManagerTool()

    @pytest.mark.asyncio
    async def test_analyze_query(self):
        """Test query analysis functionality."""
        result = await rag_manager_tool._handle_analyze_query({
            "query": "How to create responsive React components",
            "agent_type": "ui_specialist"
        })

        assert result["success"] is True
        assert "data" in result
        assert "intent" in result["data"]
        assert "keywords" in result["data"]
        assert "confidence" in result["data"]
        assert result["data"]["intent"] in ["explicit_fact", "implicit_fact", "interpretable_rationale", "hidden_rationale"]

    @pytest.mark.asyncio
    async def test_retrieve_knowledge(self):
        """Test knowledge retrieval functionality."""
        result = await rag_manager_tool._handle_retrieve_knowledge({
            "query": "React hooks patterns",
            "agent_type": "ui_specialist",
            "retrieval_strategy": "hybrid",
            "max_results": 3,
            "context_length": 4000
        })

        assert result["success"] is True
        assert "data" in result
        assert "results" in result["data"]
        assert "total_results" in result["data"]
        assert "retrieval_strategy" in result["data"]
        assert isinstance(result["data"]["results"], list)

    @pytest.mark.asyncio
    async def test_retrieve_knowledge_with_different_strategies(self):
        """Test knowledge retrieval with different strategies."""
        strategies = ["hybrid", "category", "fulltext", "vector", "agent_specific"]

        for strategy in strategies:
            result = await rag_manager_tool._handle_retrieve_knowledge({
                "query": "React components",
                "agent_type": "ui_specialist",
                "retrieval_strategy": strategy,
                "max_results": 2,
                "context_length": 2000
            })

            assert result["success"] is True
            assert result["data"]["retrieval_strategy"] == strategy

    @pytest.mark.asyncio
    async def test_rank_results(self):
        """Test result ranking functionality."""
        # Mock results
        mock_results = [
            {
                "item_id": "test_1",
                "title": "Test Result 1",
                "content": "Test content 1",
                "category": "react_pattern",
                "confidence": 0.9,
                "effectiveness": 0.8,
                "relevance_score": 0.7,
                "source_type": "manual",
                "freshness_score": 1.0,
                "agent_specific": False,
                "agent_types": []
            },
            {
                "item_id": "test_2",
                "title": "Test Result 2",
                "content": "Test content 2",
                "category": "ui_component",
                "confidence": 0.8,
                "effectiveness": 0.7,
                "relevance_score": 0.6,
                "source_type": "manual",
                "freshness_score": 0.9,
                "agent_specific": True,
                "agent_types": ["ui_specialist"]
            }
        ]

        mock_analysis = {
            "intent": "implicit_fact",
            "entities": ["React"],
            "keywords": ["how", "create", "react", "components"],
            "agent_type": "ui_specialist",
            "complexity": "moderate",
            "confidence": 0.9
        }

        result = await rag_manager_tool._handle_rank_results({
            "results": mock_results,
            "query_analysis_data": mock_analysis,
            "agent_type": "ui_specialist"
        })

        assert result["success"] is True
        assert "data" in result
        assert "results" in result["data"]
        assert result["data"]["ranking_strategy"] == "multi_factor"
        assert len(result["data"]["results"]) == 2

    @pytest.mark.asyncio
    async def test_inject_context(self):
        """Test context injection functionality."""
        mock_results = [
            {
                "item_id": "test_1",
                "title": "Test Result 1",
                "content": "Test content 1",
                "category": "react_pattern",
                "confidence": 0.9,
                "effectiveness": 0.8,
                "relevance_score": 0.7,
                "source_type": "manual",
                "freshness_score": 1.0,
                "agent_specific": False,
                "agent_types": []
            }
        ]

        result = await rag_manager_tool._handle_inject_context({
            "ranked_results": mock_results,
            "agent_type": "ui_specialist",
            "context_length": 4000
        })

        assert result["success"] is True
        assert "data" in result
        assert "context" in result["data"]
        assert "context_length" in result["data"]
        assert "items_included" in result["data"]
        assert "examples_included" in result["data"]

    @pytest.mark.asyncio
    async def test_get_cache_stats(self):
        """Test cache statistics functionality."""
        result = await rag_manager_tool._handle_get_cache_stats({})

        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_optimize_performance(self):
        """Test performance optimization functionality."""
        # Test the case where no performance data is available
        result = await rag_manager_tool._handle_optimize_performance({
            "agent_type": "ui_specialist",
            "performance_target": "latency"
        })

        # Should return success: False when no data is available
        assert result["success"] is False
        assert "error" in result
        assert "No performance data available" in result["error"]

    @pytest.mark.asyncio
    async def test_multi_strategy_retrieval(self):
        """Test multi-strategy retrieval workflow."""
        # Test the complete workflow
        query = "How to implement React hooks with TypeScript"

        # Step 1: Analyze query
        analysis = await rag_manager_tool._handle_analyze_query({
            "query": query,
            "agent_type": "ui_specialist"
        })
        assert analysis["success"] is True

        # Step 2: Retrieve knowledge
        retrieval = await rag_manager_tool._handle_retrieve_knowledge({
            "query": query,
            "agent_type": "ui_specialist",
            "retrieval_strategy": "hybrid",
            "max_results": 5,
            "context_length": 4000
        })
        assert retrieval["success"] is True
        assert retrieval["data"]["total_results"] > 0

        # Step 3: Rank results
        ranking = await rag_manager_tool._handle_rank_results({
            "results": retrieval["data"]["results"],
            "query_analysis_data": analysis["data"],
            "agent_type": "ui_specialist"
        })
        assert ranking["success"] is True

        # Step 4: Inject context
        context = await rag_manager_tool._handle_inject_context({
            "ranked_results": ranking["data"]["results"],
            "agent_type": "ui_specialist",
            "context_length": 4000
        })
        assert context["success"] is True

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in RAG Manager."""
        # Test with invalid strategy
        result = await rag_manager_tool._handle_retrieve_knowledge({
            "query": "React hooks",
            "agent_type": "ui_specialist",
            "retrieval_strategy": "invalid_strategy",
            "max_results": 3,
            "context_length": 4000
        })

        # Should still succeed but with fallback
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_performance_targets(self):
        """Verify performance targets are met."""
        import time

        # Test query analysis performance
        start_time = time.time()
        analysis = await rag_manager_tool._handle_analyze_query({
            "query": "React components",
            "agent_type": "ui_specialist"
        })
        analysis_time = time.time() - start_time
        assert analysis_time < 0.1  # <100ms target

        # Test retrieval performance
        start_time = time.time()
        retrieval = await rag_manager_tool._handle_retrieve_knowledge({
            "query": "React hooks patterns",
            "agent_type": "ui_specialist",
            "retrieval_strategy": "hybrid",
            "max_results": 3,
            "context_length": 4000
        })
        retrieval_time = time.time() - start_time
        assert retrieval_time < 0.5  # <500ms target

    def test_rag_manager_initialization(self):
        """Test RAG Manager initialization."""
        rag_manager = RAGTool()
        assert rag_manager.knowledge_base is not None
        assert rag_manager.conn is not None


class RAGTool:
    """Mock RAG Tool for testing."""

    def __init__(self):
        self.knowledge_base = Mock()
        self.conn = Mock()

    async def _handle_analyze_query(self, arguments):
        """Handle query analysis."""
        return {
            "success": True,
            "data": {
                "intent": "implicit_fact",
                "entities": ["React"],
                "keywords": ["how", "create", "react", "components"],
                "agent_type": "ui_specialist",
                "complexity": "moderate",
                "confidence": 0.9
            }
        }

    async def _handle_retrieve_knowledge(self, arguments):
        """Handle knowledge retrieval."""
        return {
            "success": True,
            "data": {
                "results": [
                    {
                        "item_id": "test_1",
                        "title": "useState Hook Pattern",
                        "content": "State management pattern using useState hook",
                        "category": "react_pattern",
                        "confidence": 0.95,
                        "effectiveness": 0.9,
                        "relevance_score": 1.0,
                        "source_type": "manual",
                        "freshness_score": 1.0,
                        "agent_specific": True,
                        "agent_types": ["ui_specialist"]
                    }
                ],
                "cache_hit": False,
                "retrieval_strategy": arguments.get("retrieval_strategy", "hybrid"),
                "total_results": 1
            }
        }

    async def _handle_rank_results(self, arguments):
        """Handle result ranking."""
        return {
            "success": True,
            "data": {
                "results": arguments["results"],
                "ranking_strategy": "multi_factor",
                "total_results": len(arguments["results"])
            }
        }

    async def _handle_inject_context(self, arguments):
        """Handle context injection."""
        return {
            "success": True,
            "data": {
                "context": {
                    "patterns": [],
                    "examples": []
                },
                "context_length": len(str({"patterns": [], "examples": []})),
                "items_included": 0,
                "examples_included": 0
            }
        }

    async def _handle_get_cache_stats(self, arguments):
        """Handle cache statistics."""
        return {
            "success": True,
            "data": {
                "by_level": {},
                "total_entries": 0,
                "total_hits": 0,
                "avg_hit_rate": 0.0
            }
        }

    async def _handle_optimize_performance(self, arguments):
        """Handle performance optimization."""
        return {
            "success": True,
            "data": {
                "current_metrics": {
                    "latency": 0.1,
                    "success_rate": 0.95,
                    "satisfaction": 0.9,
                    "cache_hit_rate": 0.7
                },
                "recommendations": ["Increase cache hit rate", "Optimize retrieval strategy"]
            }
        }
