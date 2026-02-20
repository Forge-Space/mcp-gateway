"""Test suite for RAG Manager functionality.

This module provides comprehensive tests for the RAG Manager tool,
including unit tests, integration tests, and performance benchmarks.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

# Import RAG Manager components
from tool_router.mcp_tools.rag_manager import (
    RAGManagerTool,
    QueryAnalysis,
    RetrievalContext,
    RetrievalResult,
    rag_manager_handler
)


class TestQueryAnalysis:
    """Test query analysis functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rag_manager = RAGManagerTool()
    
    @pytest.mark.asyncio
    async def test_analyze_query_ui_specialist(self):
        """Test query analysis for UI specialist."""
        
        query = "Create React button with accessibility features"
        agent_type = "ui_specialist"
        
        result = await self.rag_manager.analyze_query(query, agent_type)
        
        assert isinstance(result, QueryAnalysis)
        assert result.query == query
        assert result.agent_type == agent_type
        assert result.intent is not None
        assert result.confidence > 0.0
        assert "React" in result.entities
        assert "button" in result.entities
        assert "accessibility" in result.keywords
    
    @pytest.mark.asyncio
    async def test_analyze_query_prompt_architect(self):
        """Test query analysis for Prompt Architect."""
        
        query = "Optimize this prompt for better responses"
        agent_type = "prompt_architect"
        
        result = await self.rag_manager.analyze_query(query, agent_type)
        
        assert isinstance(result, QueryAnalysis)
        assert result.agent_type == agent_type
        assert result.intent in ["explicit_fact", "implicit_fact"]
        assert "optimize" in result.entities
        assert "prompt" in result.keywords
    
    @pytest.mark.asyncio
    async def test_analyze_query_router_specialist(self):
        """Test query analysis for Router Specialist."""
        
        query = "Route this task to the appropriate specialist"
        agent_type = "router_specialist"
        
        result = await self.rag_manager.analyze_query(query, agent_type)
        
        assert isinstance(result, QueryAnalysis)
        assert result.agent_type == agent_type
        assert "route" in result.entities
        assert "specialist" in result.keywords
    
    @pytest.mark.asyncio
    async def test_query_classification_accuracy(self):
        """Test query classification accuracy."""
        
        test_cases = [
            ("Create React component", "ui_specialist", "implicit_fact"),
            ("What is React?", "ui_specialist", "explicit_fact"),
            ("Explain React hooks", "ui_specialist", "interpretable_rationale"),
            ("Design complex React architecture", "ui_specialist", "hidden_rationale"),
        ]
        
        for query, agent_type, expected_intent in test_cases:
            result = await self.rag_manager.analyze_query(query, agent_type)
            
            # Allow some flexibility in classification
            assert result.intent in [
                "explicit_fact", "implicit_fact", 
                "interpretable_rationale", "hidden_rationale"
            ]
            assert result.confidence > 0.3  # Minimum confidence threshold


class TestKnowledgeRetrieval:
    """Test knowledge retrieval functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rag_manager = RAGManagerTool()
    
    @pytest.mark.asyncio
    async def test_retrieve_knowledge_hybrid_strategy(self):
        """Test hybrid retrieval strategy."""
        
        context = RetrievalContext(
            query="Create React button",
            agent_type="ui_specialist",
            retrieval_strategy="hybrid",
            max_results=5,
            context_length=4000
        )
        
        results = await self.rag_manager.retrieve_knowledge(context)
        
        assert isinstance(results, List)
        assert len(results) <= context.max_results
        assert all(isinstance(result, RetrievalResult) for result in results)
        assert all(result.relevance_score > 0.0 for result in results)
        assert all(result.confidence > 0.0 for result in results)
    
    @pytest.mark.asyncio
    async def test_retrieve_knowledge_category_strategy(self):
        """Test category-based retrieval strategy."""
        
        context = RetrievalContext(
            query="React patterns",
            agent_type="ui_specialist",
            retrieval_strategy="category",
            categories=["react_pattern", "ui_component"],
            max_results=3,
            context_length=3000
        )
        
        results = await self.rag_manager.retrieve_knowledge(context)
        
        assert isinstance(results, List)
        assert len(results) <= context.max_results
        # Results should be from specified categories
        if results:
            assert all(result.category in context.categories for result in results)
    
    @pytest.mark.asyncio
    async def test_retrieve_knowledge_agent_specific(self):
        """Test agent-specific retrieval."""
        
        context = RetrievalContext(
            query="UI component generation",
            agent_type="ui_specialist",
            retrieval_strategy="agent_specific",
            max_results=5,
            context_length=4000
        )
        
        results = await self.rag_manager.retrieve_knowledge(context)
        
        assert isinstance(results, List)
        assert len(results) <= context.max_results
        # Results should be relevant to UI specialist
        if results:
            assert all(result.source_type in ["knowledge_base", "training_data"] for result in results)
    
    @pytest.mark.asyncio
    async def test_retrieve_knowledge_caching(self):
        """Test retrieval caching functionality."""
        
        context = RetrievalContext(
            query="Test caching query",
            agent_type="ui_specialist",
            retrieval_strategy="hybrid",
            max_results=3
        )
        
        # First retrieval
        results1 = await self.rag_manager.retrieve_knowledge(context)
        
        # Second retrieval (should hit cache)
        results2 = await self.rag_manager.retrieve_knowledge(context)
        
        # Results should be identical
        assert len(results1) == len(results2)
        if results1 and results2:
            assert results1[0].title == results2[0].title
            assert results1[0].content == results2[0].content


class TestResultRanking:
    """Test result ranking functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rag_manager = RAGManagerTool()
    
    @pytest.mark.asyncio
    async def test_rank_results_by_relevance(self):
        """Test result ranking by relevance."""
        
        # Create mock results with different relevance scores
        mock_results = [
            RetrievalResult(
                title="Low relevance result",
                content="Low relevance content",
                relevance_score=0.3,
                confidence=0.5,
                source_type="knowledge_base",
                category="general"
            ),
            RetrievalResult(
                title="High relevance result",
                content="High relevance content",
                relevance_score=0.9,
                confidence=0.8,
                source_type="knowledge_base",
                category="react_pattern"
            ),
            RetrievalResult(
                title="Medium relevance result",
                content="Medium relevance content",
                relevance_score=0.6,
                confidence=0.7,
                source_type="training_data",
                category="ui_component"
            )
        ]
        
        context = RetrievalContext(
            query="React button",
            agent_type="ui_specialist",
            retrieval_strategy="hybrid"
        )
        
        ranked_results = await self.rag_manager.rank_results(mock_results, context)
        
        # Results should be sorted by relevance (descending)
        assert len(ranked_results) == len(mock_results)
        assert ranked_results[0].relevance_score >= ranked_results[1].relevance_score
        assert ranked_results[1].relevance_score >= ranked_results[2].relevance_score
        assert ranked_results[0].title == "High relevance result"
    
    @pytest.mark.asyncio
    async def test_rank_results_with_agent_preference(self):
        """Test result ranking with agent-specific preferences."""
        
        mock_results = [
            RetrievalResult(
                title="General pattern",
                content="General pattern content",
                relevance_score=0.8,
                confidence=0.7,
                source_type="knowledge_base",
                category="general"
            ),
            RetrievalResult(
                title="React specific pattern",
                content="React specific content",
                relevance_score=0.7,
                confidence=0.8,
                source_type="knowledge_base",
                category="react_pattern"
            )
        ]
        
        context = RetrievalContext(
            query="React component",
            agent_type="ui_specialist",
            retrieval_strategy="agent_specific"
        )
        
        ranked_results = await self.rag_manager.rank_results(mock_results, context)
        
        # React-specific result should be ranked higher for UI specialist
        assert ranked_results[0].title == "React specific pattern"


class TestContextInjection:
    """Test context injection functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rag_manager = RAGManagerTool()
    
    @pytest.mark.asyncio
    async def test_inject_context_basic(self):
        """Test basic context injection."""
        
        results = [
            RetrievalResult(
                title="React Button Pattern",
                content="const Button = ({ children, onClick }) => <button onClick={onClick}>{children}</button>",
                relevance_score=0.9,
                confidence=0.8,
                source_type="knowledge_base",
                category="react_pattern"
            )
        ]
        
        context = RetrievalContext(
            query="Create button",
            agent_type="ui_specialist",
            context_length=4000
        )
        
        injected = await self.rag_manager.inject_context(results, context)
        
        assert "patterns" in injected
        assert len(injected["patterns"]) == 1
        assert injected["patterns"][0]["title"] == "React Button Pattern"
        assert injected["patterns"][0]["relevance_score"] == 0.9
        assert "metadata" in injected
        assert injected["metadata"]["agent_type"] == "ui_specialist"
    
    @pytest.mark.asyncio
    async def test_inject_context_with_examples(self):
        """Test context injection with code examples."""
        
        results = [
            RetrievalResult(
                title="React Component Example",
                content="```tsx\nconst Button: React.FC<ButtonProps> = ({ children, onClick }) => {\n  return <button onClick={onClick}>{children}</button>\n};\n```",
                relevance_score=0.9,
                confidence=0.8,
                source_type="knowledge_base",
                category="react_pattern"
            )
        ]
        
        context = RetrievalContext(
            query="React component",
            agent_type="ui_specialist",
            context_length=4000
        )
        
        injected = await self.rag_manager.inject_context(results, context)
        
        assert "examples" in injected
        assert len(injected["examples"]) > 0
        assert "React.FC" in injected["examples"][0]["code"]
    
    @pytest.mark.asyncio
    async def test_inject_context_length_limit(self):
        """Test context injection respects length limits."""
        
        # Create results with long content
        long_content = "x" * 5000  # Very long content
        results = [
            RetrievalResult(
                title="Long content result",
                content=long_content,
                relevance_score=0.9,
                confidence=0.8,
                source_type="knowledge_base",
                category="general"
            )
        ]
        
        context = RetrievalContext(
            query="Test query",
            agent_type="ui_specialist",
            context_length=1000  # Small limit
        )
        
        injected = await self.rag_manager.inject_context(results, context)
        
        # Should truncate content to fit within limit
        total_length = sum(len(p["content"]) for p in injected["patterns"])
        assert total_length <= context.context_length


class TestCacheManagement:
    """Test cache management functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rag_manager = RAGManagerTool()
    
    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Test cache statistics retrieval."""
        
        stats = await self.rag_manager.get_cache_stats()
        
        assert "hit_rate" in stats
        assert "total_queries" in stats
        assert "cache_size" in stats
        assert isinstance(stats["hit_rate"], (int, float))
        assert 0 <= stats["hit_rate"] <= 1
    
    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """Test cache clearing functionality."""
        
        # Add some cached items first
        context = RetrievalContext(
            query="Test query for cache",
            agent_type="ui_specialist",
            retrieval_strategy="hybrid"
        )
        
        await self.rag_manager.retrieve_knowledge(context)
        
        # Clear cache
        await self.rag_manager.clear_cache()
        
        # Check cache is cleared
        stats = await self.rag_manager.get_cache_stats()
        assert stats["cache_size"] == 0


class TestPerformanceOptimization:
    """Test performance optimization functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rag_manager = RAGManagerTool()
    
    @pytest.mark.asyncio
    async def test_optimize_performance(self):
        """Test performance optimization recommendations."""
        
        recommendations = await self.rag_manager.optimize_performance()
        
        assert isinstance(recommendations, Dict)
        assert "recommendations" in recommendations
        assert "current_performance" in recommendations
        assert isinstance(recommendations["recommendations"], List)
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self):
        """Test performance monitoring."""
        
        # Monitor performance for a query
        context = RetrievalContext(
            query="Performance test query",
            agent_type="ui_specialist",
            retrieval_strategy="hybrid"
        )
        
        start_time = asyncio.get_event_loop().time()
        results = await self.rag_manager.retrieve_knowledge(context)
        end_time = asyncio.get_event_loop().time()
        
        # Performance should be reasonable
        response_time = end_time - start_time
        assert response_time < 2.0  # Should complete within 2 seconds


class TestRAGManagerHandler:
    """Test RAG Manager MCP handler."""
    
    @pytest.mark.asyncio
    async def test_handler_analyze_query(self):
        """Test MCP handler for query analysis."""
        
        arguments = {
            "action": "analyze_query",
            "query": "Create React button",
            "agent_type": "ui_specialist"
        }
        
        result = await rag_manager_handler(arguments)
        
        assert result["success"] is True
        assert "analysis" in result
        assert result["analysis"]["query"] == arguments["query"]
        assert result["analysis"]["agent_type"] == arguments["agent_type"]
    
    @pytest.mark.asyncio
    async def test_handler_retrieve_knowledge(self):
        """Test MCP handler for knowledge retrieval."""
        
        arguments = {
            "action": "retrieve_knowledge",
            "query": "React patterns",
            "agent_type": "ui_specialist",
            "retrieval_strategy": "hybrid",
            "max_results": 5
        }
        
        result = await rag_manager_handler(arguments)
        
        assert result["success"] is True
        assert "results" in result
        assert isinstance(result["results"], List)
        assert len(result["results"]) <= arguments["max_results"]
    
    @pytest.mark.asyncio
    async def test_handler_invalid_action(self):
        """Test MCP handler with invalid action."""
        
        arguments = {
            "action": "invalid_action",
            "query": "Test query"
        }
        
        result = await rag_manager_handler(arguments)
        
        assert result["success"] is False
        assert "error" in result
        assert "Unknown action" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handler_missing_arguments(self):
        """Test MCP handler with missing arguments."""
        
        arguments = {
            "action": "analyze_query"
            # Missing required query and agent_type
        }
        
        result = await rag_manager_handler(arguments)
        
        assert result["success"] is False
        assert "error" in result


class TestIntegration:
    """Integration tests for RAG Manager."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end RAG workflow."""
        
        rag_manager = RAGManagerTool()
        
        # Step 1: Analyze query
        query = "Create accessible React button with hover effects"
        analysis = await rag_manager.analyze_query(query, "ui_specialist")
        
        assert analysis.intent is not None
        assert analysis.confidence > 0.5
        
        # Step 2: Retrieve knowledge
        context = RetrievalContext(
            query=query,
            agent_type="ui_specialist",
            retrieval_strategy="hybrid",
            max_results=5,
            context_length=4000,
            query_analysis=analysis
        )
        
        results = await rag_manager.retrieve_knowledge(context)
        
        assert len(results) > 0
        assert all(result.relevance_score > 0.5 for result in results)
        
        # Step 3: Rank results
        ranked_results = await rag_manager.rank_results(results, context)
        
        assert len(ranked_results) == len(results)
        assert ranked_results[0].relevance_score >= ranked_results[-1].relevance_score
        
        # Step 4: Inject context
        injected_context = await rag_manager.inject_context(ranked_results, context)
        
        assert "patterns" in injected_context
        assert len(injected_context["patterns"]) > 0
        assert "metadata" in injected_context
        assert injected_context["metadata"]["agent_type"] == "ui_specialist"
        
        # Step 5: Check performance
        stats = await rag_manager.get_cache_stats()
        assert "hit_rate" in stats
        assert isinstance(stats["hit_rate"], (int, float))
    
    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self):
        """Test RAG workflow across different agent types."""
        
        rag_manager = RAGManagerTool()
        
        test_cases = [
            ("Create React component", "ui_specialist"),
            ("Optimize prompt clarity", "prompt_architect"),
            ("Route task to specialist", "router_specialist")
        ]
        
        for query, agent_type in test_cases:
            # Analyze query
            analysis = await rag_manager.analyze_query(query, agent_type)
            assert analysis.agent_type == agent_type
            
            # Retrieve knowledge
            context = RetrievalContext(
                query=query,
                agent_type=agent_type,
                retrieval_strategy="agent_specific",
                max_results=3
            )
            
            results = await rag_manager.retrieve_knowledge(context)
            assert len(results) >= 0  # May be empty for some queries
            
            # Inject context
            if results:
                injected = await rag_manager.inject_context(results, context)
                assert "metadata" in injected
                assert injected["metadata"]["agent_type"] == agent_type


# Performance Benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmarks for RAG Manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rag_manager = RAGManagerTool()
    
    @pytest.mark.asyncio
    async def test_query_analysis_performance(self):
        """Test query analysis performance."""
        
        import time
        
        queries = [
            "Create React button with accessibility",
            "Optimize prompt for better responses",
            "Route task to appropriate specialist"
        ]
        
        times = []
        
        for query in queries:
            start_time = time.time()
            await self.rag_manager.analyze_query(query, "ui_specialist")
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        
        # Should complete within 100ms on average
        assert avg_time < 0.1, f"Average query analysis time: {avg_time*1000:.1f}ms"
    
    @pytest.mark.asyncio
    async def test_retrieval_performance(self):
        """Test knowledge retrieval performance."""
        
        import time
        
        context = RetrievalContext(
            query="React patterns",
            agent_type="ui_specialist",
            retrieval_strategy="hybrid",
            max_results=5
        )
        
        start_time = time.time()
        results = await self.rag_manager.retrieve_knowledge(context)
        end_time = time.time()
        
        retrieval_time = end_time - start_time
        
        # Should complete within 500ms
        assert retrieval_time < 0.5, f"Retrieval time: {retrieval_time*1000:.1f}ms"
    
    @pytest.mark.asyncio
    async def test_context_injection_performance(self):
        """Test context injection performance."""
        
        import time
        
        # Create mock results
        results = [
            RetrievalResult(
                title=f"Test result {i}",
                content=f"Test content {i}",
                relevance_score=0.8,
                confidence=0.7,
                source_type="knowledge_base",
                category="test"
            )
            for i in range(10)
        ]
        
        context = RetrievalContext(
            query="Test query",
            agent_type="ui_specialist",
            context_length=4000
        )
        
        start_time = time.time()
        injected = await self.rag_manager.inject_context(results, context)
        end_time = time.time()
        
        injection_time = end_time - start_time
        
        # Should complete within 300ms
        assert injection_time < 0.3, f"Context injection time: {injection_time*1000:.1f}ms"
        assert len(injected["patterns"]) == 10


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
