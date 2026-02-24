"""
RAG Manager Tool
Provides comprehensive retrieval-augmented generation capabilities for specialist AI agents.
Implements query analysis, multi-strategy retrieval, result ranking, and context injection.
"""

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from tool_router.training.data_extraction import PatternCategory

# Import existing knowledge base
from tool_router.training.knowledge_base import KnowledgeBase


@dataclass
class QueryAnalysis:
    """Results of query analysis"""

    intent: str  # explicit_fact, implicit_fact, interpretable_rationale, hidden_rationale
    entities: list[str]
    keywords: list[str]
    agent_type: str
    complexity: str  # simple, moderate, complex
    confidence: float


@dataclass
class RetrievalResult:
    """Single retrieval result with metadata"""

    item_id: int
    title: str
    content: str
    category: str
    confidence: float
    effectiveness: float
    relevance_score: float
    source_type: str
    freshness_score: float
    agent_specific: bool
    agent_types: list[str]
    agent_type: str = ""  # Add missing field


@dataclass
class RetrievalContext:
    """Context for retrieval operations"""

    query: str
    query_analysis: QueryAnalysis
    agent_type: str
    retrieval_strategy: str
    max_results: int
    context_length: int
    filters: dict[str, Any]


class RAGManagerError(Exception):
    """Custom exception for RAG Manager operations"""


class RAGManagerTool:
    """RAG Manager for specialist AI agents"""

    def __init__(self) -> None:
        self.knowledge_base = KnowledgeBase()
        self.conn = None
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database connection"""
        try:
            self.conn = sqlite3.connect("data/knowledge_base.db")
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            error_msg = f"Database connection failed: {e}"
            raise RAGManagerError(error_msg) from e

    async def _get_query_analysis(self, query: str, agent_type: str) -> QueryAnalysis:
        """Analyze query to determine intent and extract entities"""
        # Simple intent classification based on keywords and patterns
        intent = self._classify_intent(query, agent_type)
        entities = self._extract_entities(query)
        keywords = self._extract_keywords(query)
        complexity = self._assess_complexity(query)
        confidence = self._calculate_confidence(query, intent, entities)

        return QueryAnalysis(
            intent=intent,
            entities=entities,
            keywords=keywords,
            agent_type=agent_type,
            complexity=complexity,
            confidence=confidence,
        )

    def _classify_intent(self, query: str, agent_type: str) -> str:
        """Classify query intent based on research-backed categories"""
        query_lower = query.lower()

        # UI Specialist patterns
        if agent_type == "ui_specialist":
            if any(word in query_lower for word in ["create", "generate", "build", "make"]):
                return "implicit_fact"  # Component creation requires reasoning
            if any(word in query_lower for word in ["how to", "why", "what is", "explain"]):
                return "interpretable_rationale"
            if any(word in query_lower for word in ["fix", "debug", "error", "problem"]):
                return "hidden_rationale"
            return "explicit_fact"

        # Prompt Architect patterns
        if agent_type == "prompt_architect":
            if any(word in query_lower for word in ["optimize", "improve", "enhance"]):
                return "interpretable_rationale"
            if any(word in query_lower for word in ["template", "pattern", "structure"]):
                return "implicit_fact"
            if any(word in query_lower for word in ["technique", "method", "approach"]):
                return "hidden_rationale"
            return "explicit_fact"

        # Router Specialist patterns
        if agent_type == "router_specialist":
            if any(word in query_lower for word in ["route", "assign", "delegate"]):
                return "interpretable_rationale"
            if any(word in query_lower for word in ["performance", "optimize", "speed"]):
                return "hidden_rationale"
            if any(word in query_lower for word in ["specialist", "agent", "service"]):
                return "implicit_fact"
            return "explicit_fact"

        # Default classification
        return "explicit_fact"

    def _extract_entities(self, query: str) -> list[str]:
        """Extract entities from query using simple patterns"""
        # Extract React components, frameworks, libraries
        entities = []

        # React patterns
        react_patterns = [
            r"\bReact\.",
            r"\buseState\.",
            r"\buseEffect\.",
            r"\bButton\.",
            r"\bInput\.",
            r"\bForm\.",
            r"\bComponent\.",
            r"\bHook\.",
            r"\bTailwind\.",
            r"\bMaterial-UI\.",
            r"\bChakra-UI\.",
        ]

        for pattern in react_patterns:
            matches = re.findall(pattern, query)
            entities.extend(matches)

        # Remove duplicates and return
        return list(set(entities))

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract keywords from query"""
        # Simple keyword extraction
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        words = re.findall(r"\b\w+\b", query.lower())
        return [word for word in words if word not in stop_words and len(word) > 2]

    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity"""
        word_count = len(re.findall(r"\b\w+\b", query))

        if word_count <= 5:
            return "simple"
        if word_count <= 15:
            return "moderate"
        return "complex"

    def _calculate_confidence(self, query: str, intent: str, entities: list[str]) -> float:
        """Calculate confidence score for query analysis"""
        confidence = 0.5  # Base confidence

        # Increase confidence for clear intent indicators
        if intent == "explicit_fact":
            confidence += 0.3
        elif intent == "implicit_fact":
            confidence += 0.2
        elif intent == "interpretable_rationale":
            confidence += 0.1

        # Increase confidence for entity extraction
        if entities:
            confidence += min(0.3, len(entities) * 0.1)

        # Increase confidence for keyword richness
        keywords = self._extract_keywords(query)
        if keywords:
            confidence += min(0.2, len(keywords) * 0.05)

        return min(confidence, 1.0)

    async def _retrieve_knowledge_multi_strategy(self, context: RetrievalContext) -> list[RetrievalResult]:
        """Retrieve knowledge using multiple strategies"""
        results = []

        # Strategy 1: Category-based filtering
        category_results = await self._retrieve_by_category(context)
        results.extend(category_results)

        # Strategy 2: Full-text search
        fts_results = await self._retrieve_fulltext(context)
        results.extend(fts_results)

        # Strategy 3: Agent-specific filtering
        if context.agent_type:
            agent_results = await self._retrieve_by_agent(context)
            results.extend(agent_results)

        # Strategy 4: Vector search (if available)
        vector_results = await self._retrieve_vector(context)
        results.extend(vector_results)

        # Remove duplicates and rank
        unique_results = self._deduplicate_results(results)
        ranked_results = self._rank_results(unique_results, context)

        return ranked_results[: context.max_results]

    async def _retrieve_by_category(self, context: RetrievalContext) -> list[RetrievalResult]:
        """Retrieve knowledge by category"""
        try:
            # Determine relevant categories based on agent type and query
            categories = self._get_relevant_categories(context.agent_type, context.query)

            results = []
            for category in categories:
                items = self.knowledge_base.get_patterns_by_category(category)
                for item in items:
                    result = RetrievalResult(
                        item_id=item.id,
                        title=item.title,
                        content=item.content,
                        category=(item.category.value if hasattr(item.category, "value") else str(item.category)),
                        confidence=item.confidence_score,
                        effectiveness=item.effectiveness_score,
                        relevance_score=0.8,  # Base relevance for category match
                        source_type=getattr(item, "source_type", "manual"),
                        freshness_score=getattr(item, "freshness_score", 1.0),
                        agent_specific=getattr(item, "agent_specific", False),
                        agent_types=getattr(item, "agent_types", []),
                        agent_type=context.agent_type,
                    )
                    results.append(result)

            return results
        except Exception as e:
            print(f"Error in _retrieve_by_category: {e}")
            import traceback

            traceback.print_exc()
            return []

    async def _retrieve_fulltext(self, context: RetrievalContext) -> list[RetrievalResult]:
        """Retrieve knowledge using full-text search"""
        try:
            # Use existing knowledge base search
            items = self.knowledge_base.search_patterns(context.query, limit=context.max_results)

            results = []
            for item in items:
                result = RetrievalResult(
                    item_id=item.id,
                    title=item.title,
                    content=item.content,
                    category=(item.category.value if hasattr(item.category, "value") else str(item.category)),
                    confidence=item.confidence_score,
                    effectiveness=getattr(item, "effectiveness_score", 0.7),
                    relevance_score=0.7,  # Base relevance for FTS
                    source_type=getattr(item, "source_type", "manual"),
                    freshness_score=getattr(item, "freshness_score", 1.0),
                    agent_specific=getattr(item, "agent_specific", False),
                    agent_types=getattr(item, "agent_types", []),
                    agent_type=context.agent_type,
                )
                results.append(result)

            return results
        except Exception:
            return []

    async def _retrieve_by_agent(self, context: RetrievalContext) -> list[RetrievalResult]:
        """Retrieve agent-specific knowledge"""
        try:
            # Get items marked as agent-specific
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM knowledge_items
                WHERE agent_specific = 1 AND (
                    agent_types LIKE ? OR
                    agent_types IS NULL
                )
            """,
                (f"%{context.agent_type}%",),
            )

            rows = cursor.fetchall()
            results = []
            for row in rows:
                try:
                    agent_types = json.loads(row["agent_types"] or "[]")
                except json.JSONDecodeError:
                    agent_types = []

                result = RetrievalResult(
                    item_id=row[0],  # id
                    title=row[2],  # title
                    content=row[4],  # content
                    category=row[1],  # category
                    confidence=row[7],  # confidence_score
                    effectiveness=(row[22] if len(row) > 22 else 0.8),  # effectiveness_score
                    relevance_score=0.9,  # High relevance for agent-specific
                    source_type=row[20] if len(row) > 20 else "manual",  # source_type
                    freshness_score=(row[21] if len(row) > 21 else 1.0),  # freshness_score
                    agent_specific=(bool(row[18]) if len(row) > 18 else False),  # agent_specific
                    agent_types=agent_types,
                    agent_type=context.agent_type,
                )
                results.append(result)

            return results
        except Exception:
            return []

    async def _retrieve_vector(self, _context: RetrievalContext) -> list[RetrievalResult]:
        """Retrieve knowledge using vector search"""
        try:
            # This would integrate with a vector database
            # For now, return empty list as vector search requires additional setup
            # In a full implementation, this would use embeddings and similarity search
            return []
        except Exception:
            return []

    def _get_relevant_categories(self, agent_type: str, _query: str) -> list:
        """Get relevant categories based on agent type and query"""
        categories = []

        # Base categories for all agents
        categories.extend([PatternCategory.UI_COMPONENT, PatternCategory.REACT_PATTERN])

        # Agent-specific categories
        if agent_type == "ui_specialist":
            categories.extend([PatternCategory.ACCESSIBILITY])
        elif agent_type == "prompt_architect":
            categories.extend([PatternCategory.PROMPT_ENGINEERING])
        elif agent_type == "router_specialist":
            categories.extend([PatternCategory.PERFORMANCE])

        return categories

    def _deduplicate_results(self, results: list[RetrievalResult]) -> list[RetrievalResult]:
        """Remove duplicate results based on item_id"""
        seen_ids = set()
        unique_results = []

        for result in results:
            if result.item_id not in seen_ids:
                seen_ids.add(result.item_id)
                unique_results.append(result)

        return unique_results

    def _rank_results(self, results: list[RetrievalResult], context: RetrievalContext) -> list[RetrievalResult]:
        """Rank retrieval results based on relevance and context"""
        # Calculate final ranking score
        for result in results:
            # Base relevance score
            final_score = result.relevance_score

            # Boost for agent-specific items
            if result.agent_specific and result.agent_type == context.agent_type:
                final_score += 0.2

            # Boost for high confidence and effectiveness
            final_score += result.confidence * 0.1
            final_score += result.effectiveness * 0.1

            # Boost for freshness
            final_score += result.freshness_score * 0.05

            # Boost for keyword matches
            query_keywords = set(context.query_analysis.keywords)
            content_words = set(result.content.lower().split())
            keyword_matches = len(query_keywords.intersection(content_words))
            if keyword_matches > 0:
                final_score += keyword_matches * 0.02

            result.relevance_score = min(final_score, 1.0)

        # Sort by relevance score (descending)
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)

    async def _inject_context(self, ranked_results: list[RetrievalResult], context: RetrievalContext) -> dict[str, Any]:
        """Inject retrieved knowledge into context for generation"""
        # Select results that fit within context length limit
        selected_results = []
        current_length = 0

        for result in ranked_results:
            if current_length + len(result.content) <= context.context_length:
                selected_results.append(result)
                current_length += len(result.content)
            else:
                break

        # Build context structure
        context_data = {"patterns": [], "examples": []}

        # Add patterns
        for result in selected_results:
            context_data["patterns"].append(
                {
                    "title": result.title,
                    "content": result.content,
                    "confidence": result.confidence,
                    "effectiveness": result.effectiveness,
                    "source": result.source_type,
                    "category": result.category,
                    "relevance_score": result.relevance_score,
                }
            )

        # Add examples if available (simplified for now)
        for result in selected_results[:3]:  # Top 3 results
            # Extract code examples from content if present
            code_examples = self._extract_code_examples(result.content)
            for example in code_examples:
                context_data["examples"].append(
                    {
                        "code": example,
                        "description": f"Example from {result.title}",
                        "source": result.source_type,
                    }
                )

        return context_data

    def _extract_code_examples(self, content: str) -> list[str]:
        """Extract code examples from content"""
        # Simple code extraction using patterns
        code_patterns = [
            r"```(?:python|javascript|typescript|jsx|tsx)\n(.*?)\n```",
            r"`([^`\n]+)`",
            r"(?:const|let|var|function)\s+\w+\s*=\s*([^;{]+)",
            r"(?:class|interface)\s+\w+\s*(?:extends\s+\w+\s*)?\{[^}]*\}",
            r"(?:import|export)\s+.*?from\s+['\"][^'\"]+['\"];",
        ]

        examples = []
        for pattern in code_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            examples.extend(matches)

        return examples

    async def _update_performance_metrics(
        self,
        query: str,
        agent_type: str,
        context_data: dict[str, Any],
        performance_data: dict[str, Any],
    ) -> None:
        """Update performance metrics for continuous learning"""
        try:
            # Calculate performance metrics
            latency = performance_data.get("latency", 0.0)
            cache_hit = performance_data.get("cache_hit", False)
            user_feedback = performance_data.get("user_feedback", {})

            # Update or create performance record
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO agent_performance
                (agent_type, query_pattern, retrieval_strategy, performance_metrics,
                 avg_latency, success_rate, user_satisfaction, knowledge_utilization,
                 cache_hit_rate, relevance_score, total_queries, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime("now"), datetime("now"))
            """,
                (
                    agent_type,
                    self._generate_query_pattern(query),
                    context_data.get("metadata", {}).get("retrieval_strategy", "hybrid"),
                    json.dumps(performance_data),
                    latency,
                    1.0 if performance_data.get("success", True) else 0.0,
                    user_feedback.get("satisfaction", 0.5),
                    0.8,  # Knowledge utilization estimate
                    1.0 if cache_hit else 0.0,
                    context_data.get("metadata", {}).get("relevance_score", 0.8),
                    1,
                    datetime.UTC,
                    datetime.UTC,
                ),
            )

            self.conn.commit()
        except Exception:
            pass

    def _generate_query_pattern(self, query: str) -> str:
        """Generate a normalized query pattern for tracking"""
        # Remove common words and normalize
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        words = re.findall(r"\b\w+\b", query.lower())
        normalized_words = [word for word in words if word not in stop_words]

        return " ".join(normalized_words[:5])  # First 5 significant words

    async def _check_cache(self, cache_key: str) -> dict[str, Any] | None:
        """Check cache for existing results"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT retrieved_items, query_hash, timestamp, hit_count, ttl, cache_level
                FROM retrieval_cache
                WHERE cache_key = ? AND timestamp > datetime("now", "-ttl seconds")
            """,
                (cache_key,),
            )

            row = cursor.fetchone()
            if row:
                return {
                    "retrieved_items": json.loads(row["retrieved_items"]),
                    "query_hash": row["query_hash"],
                    "timestamp": row["timestamp"],
                    "hit_count": row["hit_count"],
                    "ttl": row["ttl"],
                    "cache_level": row["cache_level"],
                }
            return None
        except Exception:
            return None

    async def _set_cache(
        self,
        cache_key: str,
        retrieved_items: list[int],
        ttl: int = 3600,
        cache_level: str = "memory",
    ) -> None:
        """Set cache entry"""
        try:
            cursor = self.conn.cursor()
            query_hash = hashlib.sha256(cache_key.encode()).hexdigest()

            cursor.execute(
                """
                INSERT OR REPLACE INTO retrieval_cache
                (cache_key, retrieved_items, query_hash, timestamp, hit_count, ttl,
                 cache_level, size_bytes, created_at, updated_at)
                VALUES (?, ?, ?, datetime("now"), 1, ?, ?, ?, datetime("now"), datetime("now"))
            """,
                (
                    cache_key,
                    json.dumps(retrieved_items),
                    query_hash,
                    ttl,
                    cache_level,
                    len(json.dumps(retrieved_items)),
                ),
            )

            self.conn.commit()
        except Exception:
            pass

    # MCP Tool Handler
    async def rag_manager_handler(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Main handler for RAG Manager MCP tool"""
        action = arguments.get("action")

        try:
            if action == "analyze_query":
                return await self._handle_analyze_query(arguments)
            if action == "retrieve_knowledge":
                return await self._handle_retrieve_knowledge(arguments)
            if action == "rank_results":
                return await self._handle_rank_results(arguments)
            if action == "inject_context":
                return await self._handle_inject_context(arguments)
            if action == "get_cache_stats":
                return await self._handle_get_cache_stats(arguments)
            if action == "optimize_performance":
                return await self._handle_optimize_performance(arguments)
            error_msg = f"Unknown action: {action}"
            raise ValueError(error_msg)
        except Exception:
            return {
                "success": False,
                "error": "An error occurred",
                "details": f"RAG Manager {action} failed",
            }

    async def _handle_analyze_query(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle query analysis"""
        query = arguments.get("query")
        agent_type = arguments.get("agent_type", "ui_specialist")

        analysis = await self._get_query_analysis(query, agent_type)

        return {
            "success": True,
            "data": {
                "intent": analysis.intent,
                "entities": analysis.entities,
                "keywords": analysis.keywords,
                "agent_type": analysis.agent_type,
                "complexity": analysis.complexity,
                "confidence": analysis.confidence,
            },
        }

    async def _handle_retrieve_knowledge(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle knowledge retrieval"""
        query = arguments.get("query")
        agent_type = arguments.get("agent_type", "ui_specialist")
        retrieval_strategy = arguments.get("retrieval_strategy", "hybrid")
        max_results = arguments.get("max_results", 10)

        context = RetrievalContext(
            query=query,
            query_analysis=await self._get_query_analysis(query, agent_type),
            agent_type=agent_type,
            retrieval_strategy=retrieval_strategy,
            max_results=max_results,
            context_length=4000,
            filters={},
        )

        # Check cache first
        cache_key = f"{agent_type}:{query}:{retrieval_strategy}:{max_results}"
        cached_result = await self._check_cache(cache_key)

        if cached_result:
            # Return cached results
            item_ids = cached_result["retrieved_items"]
            results = []
            for item_id in item_ids:
                item = self.knowledge_base.get_pattern(item_id)
                if item:
                    results.append(
                        RetrievalResult(
                            item_id=item.id,
                            title=item.title,
                            content=item.content,
                            category=item.category,
                            confidence=item.confidence_score,
                            effectiveness=item.effectiveness_score,
                            relevance_score=0.8,  # Cached relevance
                            source_type=item.source_type or "manual",
                            freshness_score=1.0,
                            agent_specific=item.agent_specific or False,
                            agent_types=[],
                        )
                    )

            return {
                "success": True,
                "data": {
                    "results": [self._result_to_dict(result) for result in results],
                    "cache_hit": True,
                    "retrieval_strategy": retrieval_strategy,
                    "total_results": len(results),
                },
            }

        # Perform retrieval
        results = await self._retrieve_knowledge_multi_strategy(context)

        # Cache the results
        if results:
            item_ids = [result.item_id for result in results]
            await self._set_cache(cache_key, item_ids, ttl=3600, cache_level="memory")

        return {
            "success": True,
            "data": {
                "results": [self._result_to_dict(result) for result in results],
                "cache_hit": False,
                "retrieval_strategy": retrieval_strategy,
                "total_results": len(results),
            },
        }

    async def _handle_rank_results(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle result ranking"""
        results_data = arguments.get("results", [])
        query_analysis_data = arguments.get("query_analysis", {})

        # Convert to RetrievalResult objects
        results = []
        for result_data in results_data:
            result = RetrievalResult(
                item_id=result_data["item_id"],
                title=result_data["title"],
                content=result_data["content"],
                category=result_data["category"],
                confidence=result_data["confidence"],
                effectiveness=result_data["effectiveness"],
                relevance_score=result_data["relevance_score"],
                source_type=result_data["source_type"],
                freshness_score=result_data["freshness_score"],
                agent_specific=result_data["agent_specific"],
                agent_types=result_data["agent_types"],
            )
            results.append(result)

        # Create context for ranking
        context = RetrievalContext(
            query="",  # Not needed for ranking
            query_analysis=QueryAnalysis(
                intent=query_analysis_data.get("intent", "explicit_fact"),
                entities=query_analysis_data.get("entities", []),
                keywords=query_analysis_data.get("keywords", []),
                agent_type=query_analysis_data.get("agent_type", "ui_specialist"),
                complexity=query_analysis_data.get("complexity", "simple"),
                confidence=query_analysis_data.get("confidence", 0.5),
            ),
            agent_type=query_analysis_data.get("agent_type", "ui_specialist"),
            retrieval_strategy="hybrid",
            max_results=10,
            context_length=4000,
            filters={},
        )

        ranked_results = self._rank_results(results, context)

        return {
            "success": True,
            "data": {
                "results": [self._result_to_dict(result) for result in ranked_results],
                "ranking_strategy": "multi_factor",
                "total_results": len(ranked_results),
            },
        }

    async def _handle_inject_context(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle context injection"""
        ranked_results_data = arguments.get("ranked_results", [])
        agent_type = arguments.get("agent_type", "ui_specialist")
        context_length = arguments.get("context_length", 4000)

        # Convert to RetrievalResult objects
        ranked_results = []
        for result_data in ranked_results_data:
            result = RetrievalResult(
                item_id=result_data["item_id"],
                title=result_data["title"],
                content=result_data["content"],
                category=result_data["category"],
                confidence=result_data["confidence"],
                effectiveness=result_data["effectiveness"],
                relevance_score=result_data["relevance_score"],
                source_type=result_data["source_type"],
                freshness_score=result_data["freshness_score"],
                agent_specific=result_data["agent_specific"],
                agent_types=result_data["agent_types"],
            )
            ranked_results.append(result)

        context = RetrievalContext(
            query="",  # Not needed for context injection
            query_analysis=None,  # Not needed for context injection
            agent_type=agent_type,
            retrieval_strategy="hybrid",
            max_results=10,
            context_length=context_length,
            filters={},
        )

        context_data = await self._inject_context(ranked_results, context)

        return {
            "success": True,
            "data": {
                "context": context_data,
                "context_length": len(str(context_data)),
                "items_included": len(context_data["patterns"]),
                "examples_included": len(context_data["examples"]),
            },
        }

    async def _handle_get_cache_stats(self, _arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle cache statistics"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT cache_level, COUNT(*) as entries,
                       AVG(hit_count) as avg_hits,
                       SUM(hit_count) as total_hits,
                       AVG(ttl) as avg_ttl
                FROM retrieval_cache
                GROUP BY cache_level
            """)

            rows = cursor.fetchall()

            stats = {}
            for row in rows:
                stats[row["cache_level"]] = {
                    "entries": row["entries"],
                    "avg_hits": row["avg_hits"],
                    "total_hits": row["total_hits"],
                    "avg_ttl": row["avg_ttl"],
                }

            # Get overall cache performance
            cursor.execute("""
                SELECT COUNT(*) as total_entries,
                       SUM(hit_count) as total_hits,
                       AVG(hit_count) as avg_hit_rate
                FROM retrieval_cache
            """)

            overall = cursor.fetchone()

            return {
                "success": True,
                "data": {
                    "by_level": stats,
                    "total_entries": overall["total_entries"],
                    "total_hits": overall["total_hits"],
                    "avg_hit_rate": overall["avg_hit_rate"],
                },
            }
        except Exception:
            return {
                "success": False,
                "error": "An error occurred",
                "details": "Cache statistics retrieval failed",
            }

    async def _handle_optimize_performance(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle performance optimization"""
        agent_type = arguments.get("agent_type", "ui_specialist")
        performance_target = arguments.get("performance_target", "latency")

        try:
            # Get performance data for the agent
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT AVG(avg_latency) as current_latency,
                       AVG(success_rate) as current_success_rate,
                       AVG(user_satisfaction) as current_satisfaction,
                       AVG(cache_hit_rate) as current_cache_hit_rate
                FROM agent_performance
                WHERE agent_type = ?
                GROUP BY agent_type
            """,
                (agent_type,),
            )

            row = cursor.fetchone()

            if not row:
                return {
                    "success": False,
                    "error": "No performance data available for optimization",
                }

            current_metrics = {
                "latency": row["current_latency"],
                "success_rate": row["current_success_rate"],
                "satisfaction": row["current_satisfaction"],
                "cache_hit_rate": row["current_cache_hit_rate"],
            }

            # Generate optimization recommendations
            recommendations = []

            if performance_target == "latency" and current_metrics["latency"] > 1.0:
                recommendations.append("Increase cache hit rate")
                recommendations.append("Optimize retrieval strategy")
                recommendations.append("Pre-compute frequent queries")

            if current_metrics["success_rate"] < 0.8:
                recommendations.append("Improve query analysis")
                recommendations.append("Expand knowledge base")
                recommendations.append("Refine ranking algorithm")

            if current_metrics["cache_hit_rate"] < 0.7:
                recommendations.append("Increase cache TTL")
                recommendations.append("Implement prefetching")
                recommendations.append("Optimize cache keys")

            return {
                "success": True,
                "data": {
                    "current_metrics": current_metrics,
                    "recommendations": recommendations,
                    "optimization_target": performance_target,
                    "agent_type": agent_type,
                },
            }
        except Exception:
            return {
                "success": False,
                "error": "An error occurred",
                "details": "Performance optimization analysis failed",
            }

    def _result_to_dict(self, result: RetrievalResult) -> dict[str, Any]:
        """Convert RetrievalResult to dictionary"""
        return {
            "item_id": result.item_id,
            "title": result.title,
            "content": result.content,
            "category": result.category,
            "confidence": result.confidence,
            "effectiveness": result.effectiveness,
            "relevance_score": result.relevance_score,
            "source_type": result.source_type,
            "freshness_score": result.freshness_score,
            "agent_specific": result.agent_specific,
            "agent_types": result.agent_types,
        }


# MCP Tool Schema
RAG_MANAGER_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "analyze_query",
                "retrieve_knowledge",
                "rank_results",
                "inject_context",
                "get_cache_stats",
                "optimize_performance",
            ],
            "description": "The RAG operation to perform",
        },
        "query": {
            "type": "string",
            "description": "The query to analyze or retrieve knowledge for",
        },
        "agent_type": {
            "type": "string",
            "enum": ["ui_specialist", "prompt_architect", "router_specialist"],
            "default": "ui_specialist",
            "description": "The type of specialist agent",
        },
        "retrieval_strategy": {
            "type": "string",
            "enum": ["hybrid", "category", "fulltext", "vector", "agent_specific"],
            "default": "hybrid",
            "description": "The retrieval strategy to use",
        },
        "max_results": {
            "type": "integer",
            "default": 10,
            "minimum": 1,
            "maximum": 50,
            "description": "Maximum number of results to retrieve",
        },
        "context_length": {
            "type": "integer",
            "default": 4000,
            "minimum": 1000,
            "maximum": 8000,
            "description": "Maximum context length in tokens",
        },
        "performance_target": {
            "type": "string",
            "enum": ["latency", "success_rate", "satisfaction", "cache_hit_rate"],
            "default": "latency",
            "description": "Performance optimization target",
        },
    },
    "required": ["action"],
    "description": "RAG Manager tool for specialist AI agents",
}

# Global instance
rag_manager_tool = RAGManagerTool()
