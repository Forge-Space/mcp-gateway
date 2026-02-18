"""Enhanced context learning from feedback for AI tool selection."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tempfile import gettempdir
from typing import Any


logger = logging.getLogger(__name__)

_FEEDBACK_FILE_ENV = "ROUTER_FEEDBACK_FILE"
_DEFAULT_FEEDBACK_FILE = str(Path(gettempdir()) / "tool_router_feedback.json")
_MAX_ENTRIES = 1000


@dataclass
class FeedbackEntry:
    """A single feedback record for a tool selection."""

    task: str
    selected_tool: str
    success: bool
    timestamp: float = field(default_factory=time.time)
    context: str = ""
    confidence: float = 0.0
    task_type: str = ""  # Classified task type
    intent_category: str = ""  # Intent category (create, read, update, delete, search)
    entities: list[str] = field(default_factory=list)  # Extracted entities


@dataclass
class ToolStats:
    """Aggregated success statistics for a tool."""

    tool_name: str
    success_count: int = 0
    failure_count: int = 0
    avg_confidence: float = 0.0
    task_types: dict[str, int] = field(default_factory=dict)  # Task type frequency
    intent_categories: dict[str, int] = field(default_factory=dict)  # Intent frequency
    recent_success_rate: float = 0.0  # Success rate for recent entries (last 50)

    @property
    def total(self) -> int:
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.5  # neutral prior
        return self.success_count / self.total

    @property
    def confidence_score(self) -> float:
        """Combined score considering success rate and confidence."""
        return (self.success_rate * 0.7) + (self.avg_confidence * 0.3)


@dataclass
class TaskPattern:
    """Learned patterns for task types."""

    task_type: str
    preferred_tools: dict[str, float] = field(default_factory=dict)  # Tool -> success rate
    common_entities: list[str] = field(default_factory=list)
    avg_confidence: float = 0.0
    total_occurrences: int = 0


class FeedbackStore:
    """Enhanced persistent store for tool selection feedback enabling context learning.

    Feedback is used to boost or penalise tools based on historical success
    rates, providing a lightweight learning signal without requiring a full
    ML pipeline.
    """

    def __init__(self, feedback_file: str | None = None) -> None:
        self._file = Path(
            feedback_file
            or os.getenv(_FEEDBACK_FILE_ENV, _DEFAULT_FEEDBACK_FILE)
        )
        self._entries: list[FeedbackEntry] = []
        self._stats: dict[str, ToolStats] = {}
        self._patterns: dict[str, TaskPattern] = {}
        self._load()

    @staticmethod
    def _classify_task_type(task: str) -> str:
        """Classify task into semantic categories."""
        task_lower = task.lower()

        # File operations
        if any(word in task_lower for word in ["file", "read", "write", "create", "delete", "open"]):
            return "file_operations"

        # Search operations
        if any(word in task_lower for word in ["search", "find", "lookup", "query", "search"]):
            return "search_operations"

        # Code operations
        if any(word in task_lower for word in ["code", "edit", "modify", "refactor", "syntax"]):
            return "code_operations"

        # Database operations
        if any(word in task_lower for word in ["database", "db", "sql", "query", "table"]):
            return "database_operations"

        # Network operations
        if any(word in task_lower for word in ["http", "api", "request", "fetch", "web"]):
            return "network_operations"

        # System operations
        if any(word in task_lower for word in ["system", "process", "command", "terminal", "shell"]):
            return "system_operations"

        return "general_operations"

    @staticmethod
    def _classify_intent(task: str) -> str:
        """Classify user intent."""
        task_lower = task.lower()

        # Create intent
        if any(word in task_lower for word in ["create", "make", "add", "new", "generate", "build"]):
            return "create"

        # Read intent
        if any(word in task_lower for word in ["read", "get", "fetch", "retrieve", "show", "display", "list"]):
            return "read"

        # Update intent
        if any(word in task_lower for word in ["update", "modify", "change", "edit", "alter", "adjust"]):
            return "update"

        # Delete intent
        if any(word in task_lower for word in ["delete", "remove", "destroy", "clear", "clean"]):
            return "delete"

        # Search intent
        if any(word in task_lower for word in ["search", "find", "lookup", "query", "seek"]):
            return "search"

        return "unknown"

    @staticmethod
    def _extract_entities(task: str) -> list[str]:
        """Extract key entities from task text."""
        # Simple entity extraction - look for file paths, URLs, and quoted strings
        entities = []

        # File paths
        path_pattern = r'[/\\]?[\w\-./\\]+'
        paths = re.findall(path_pattern, task)
        entities.extend([p for p in paths if len(p) > 2])

        # Quoted strings
        quote_pattern = r'"([^"]+)"|\'([^\']+)\''
        quotes = re.findall(quote_pattern, task)
        entities.extend([q[0] or q[1] for q in quotes])

        # URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, task)
        entities.extend(urls)

        return list(set(entities))  # Remove duplicates

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(
        self,
        task: str,
        selected_tool: str,
        success: bool,
        context: str = "",
        confidence: float = 0.0,
    ) -> None:
        """Record the outcome of a tool selection with enhanced learning."""
        # Classify task for learning
        task_type = self._classify_task_type(task)
        intent_category = self._classify_intent(task)
        entities = self._extract_entities(task)

        entry = FeedbackEntry(
            task=task,
            selected_tool=selected_tool,
            success=success,
            context=context,
            confidence=confidence,
            task_type=task_type,
            intent_category=intent_category,
            entities=entities,
        )
        self._entries.append(entry)

        # Update tool statistics
        if selected_tool not in self._stats:
            self._stats[selected_tool] = ToolStats(selected_tool)
        stats = self._stats[selected_tool]
        if success:
            stats.success_count += 1
        else:
            stats.failure_count += 1

        # Update confidence tracking
        total_entries = len([e for e in self._entries if e.selected_tool == selected_tool])
        if total_entries > 0:
            confidences = [e.confidence for e in self._entries if e.selected_tool == selected_tool]
            stats.avg_confidence = sum(confidences) / len(confidences)

        # Update task type tracking
        if task_type not in stats.task_types:
            stats.task_types[task_type] = 0
        stats.task_types[task_type] += 1

        # Update intent tracking
        if intent_category not in stats.intent_categories:
            stats.intent_categories[intent_category] = 0
        stats.intent_categories[intent_category] += 1

        # Update recent success rate (last 50 entries)
        recent_entries = [e for e in self._entries[-50:] if e.selected_tool == selected_tool]
        if recent_entries:
            recent_successes = sum(1 for e in recent_entries if e.success)
            stats.recent_success_rate = recent_successes / len(recent_entries)

        # Update task patterns
        if task_type not in self._patterns:
            self._patterns[task_type] = TaskPattern(task_type)
        pattern = self._patterns[task_type]
        pattern.total_occurrences += 1

        # Update pattern tool preferences
        if selected_tool not in pattern.preferred_tools:
            pattern.preferred_tools[selected_tool] = 0.0

        # Calculate success rate for this tool in this task type
        task_type_entries = [e for e in self._entries if e.task_type == task_type and e.selected_tool == selected_tool]
        if task_type_entries:
            success_rate = sum(1 for e in task_type_entries if e.success) / len(task_type_entries)
            pattern.preferred_tools[selected_tool] = success_rate

        # Update pattern entities
        for entity in entities:
            if entity not in pattern.common_entities:
                pattern.common_entities.append(entity)

        # Calculate average confidence for this task type
        task_type_confidences = [e.confidence for e in self._entries if e.task_type == task_type]
        if task_type_confidences:
            pattern.avg_confidence = sum(task_type_confidences) / len(task_type_confidences)

        # Trim to avoid unbounded growth
        if len(self._entries) > _MAX_ENTRIES:
            self._entries = self._entries[-_MAX_ENTRIES:]

        self._persist()
        logger.debug(
            "Enhanced feedback recorded: tool=%s success=%s task_type=%s rate=%.2f",
            selected_tool,
            success,
            task_type,
            stats.success_rate,
        )

    def get_boost(self, tool_name: str) -> float:
        """Return an enhanced score multiplier based on comprehensive learning."""
        stats = self._stats.get(tool_name)
        if stats is None or stats.total < 3:
            return 1.0  # not enough data

        # Enhanced boost calculation considering multiple factors
        base_boost = 0.5 + stats.success_rate  # Historical success rate
        confidence_boost = (stats.avg_confidence - 0.5) * 0.3  # Confidence factor
        recent_boost = (stats.recent_success_rate - 0.5) * 0.2  # Recent performance

        # Combine factors
        enhanced_boost = base_boost + confidence_boost + recent_boost

        # Clamp to reasonable range
        return max(0.3, min(1.7, enhanced_boost))

    def get_task_type_boost(self, tool_name: str, task_type: str) -> float:
        """Get boost based on task type performance."""
        pattern = self._patterns.get(task_type)
        if not pattern or tool_name not in pattern.preferred_tools:
            return 1.0

        success_rate = pattern.preferred_tools[tool_name]
        # Map success rate to boost multiplier
        return 0.7 + (success_rate * 0.6)  # Range: 0.7 to 1.3

    def get_intent_boost(self, tool_name: str, intent_category: str) -> float:
        """Get boost based on intent category performance."""
        stats = self._stats.get(tool_name)
        if not stats or intent_category not in stats.intent_categories:
            return 1.0

        # Calculate success rate for this specific intent
        intent_entries = [e for e in self._entries if e.selected_tool == tool_name and e.intent_category == intent_category]
        if not intent_entries:
            return 1.0

        success_rate = sum(1 for e in intent_entries if e.success) / len(intent_entries)
        return 0.8 + (success_rate * 0.4)  # Range: 0.8 to 1.2

    def get_comprehensive_boost(self, tool_name: str, task: str) -> float:
        """Get comprehensive boost considering all factors."""
        task_type = self._classify_task_type(task)
        intent_category = self._classify_intent(task)

        # Combine different boost factors
        base_boost = self.get_boost(tool_name)
        task_type_boost = self.get_task_type_boost(tool_name, task_type)
        intent_boost = self.get_intent_boost(tool_name, intent_category)

        # Weighted combination
        comprehensive_boost = (
            base_boost * 0.5 +  # Historical performance
            task_type_boost * 0.3 +  # Task type performance
            intent_boost * 0.2  # Intent performance
        )

        return comprehensive_boost

    def get_learning_insights(self, task: str) -> dict[str, Any]:
        """Get learning insights for a given task."""
        task_type = self._classify_task_type(task)
        intent_category = self._classify_intent(task)
        entities = self._extract_entities(task)

        insights = {
            "task_type": task_type,
            "intent_category": intent_category,
            "entities": entities,
            "pattern": None,
            "recommended_tools": [],
            "confidence_factors": {},
        }

        # Get pattern insights
        pattern = self._patterns.get(task_type)
        if pattern:
            insights["pattern"] = {
                "total_occurrences": pattern.total_occurrences,
                "avg_confidence": pattern.avg_confidence,
                "common_entities": pattern.common_entities,
            }

            # Sort tools by success rate
            sorted_tools = sorted(
                pattern.preferred_tools.items(),
                key=lambda x: x[1],
                reverse=True
            )
            insights["recommended_tools"] = [
                {"tool": tool, "success_rate": rate}
                for tool, rate in sorted_tools[:3]
            ]

        return insights

    def get_adaptive_hints(self, task: str) -> list[str]:
        """Generate adaptive hints based on learning."""
        task_type = self._classify_task_type(task)
        insights = self.get_learning_insights(task)

        hints = []

        # Task type specific hints
        if insights["pattern"]:
            pattern = insights["pattern"]
            if pattern["avg_confidence"] > 0.8:
                hints.append(f"High confidence patterns found for {task_type} tasks")
            elif pattern["avg_confidence"] < 0.5:
                hints.append(f"Low confidence for {task_type} tasks, consider manual selection")

        # Entity-based hints
        if insights["entities"]:
            hints.append(f"Detected entities: {', '.join(insights['entities'][:3])}")

        # Tool recommendation hints
        if insights["recommended_tools"]:
            top_tool = insights["recommended_tools"][0]
            if top_tool["success_rate"] > 0.8:
                hints.append(f"Consider {top_tool['tool']} with {top_tool['success_rate']:.1%} success rate")

        return hints

    def get_stats(self, tool_name: str) -> ToolStats | None:
        """Return raw stats for a tool, or None if no data."""
        return self._stats.get(tool_name)

    def get_all_stats(self) -> dict[str, ToolStats]:
        """Return stats for all tools that have received feedback."""
        return dict(self._stats)

    def similar_task_tools(self, task: str, top_n: int = 3) -> list[str]:
        """Return tool names that succeeded on similar past tasks.

        Uses simple token overlap as a lightweight similarity measure.
        """
        task_tokens = set(task.lower().split())
        candidates: list[tuple[str, float]] = []

        for entry in reversed(self._entries):
            if not entry.success:
                continue
            entry_tokens = set(entry.task.lower().split())
            overlap = len(task_tokens & entry_tokens)
            if overlap > 0:
                similarity = overlap / max(len(task_tokens), len(entry_tokens))
                candidates.append((entry.selected_tool, similarity))

        # Deduplicate, keeping highest similarity per tool
        best: dict[str, float] = {}
        for tool_name, sim in candidates:
            if tool_name not in best or sim > best[tool_name]:
                best[tool_name] = sim

        sorted_tools = sorted(best.items(), key=lambda x: -x[1])
        return [t for t, _ in sorted_tools[:top_n]]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist(self) -> None:
        """Write entries to disk (best-effort)."""
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "entries": [asdict(e) for e in self._entries],
                "stats": {
                    name: asdict(s) for name, s in self._stats.items()
                },
            }
            self._file.write_text(json.dumps(data, indent=2))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not persist feedback: %s", exc)

    def _load(self) -> None:
        """Load entries from disk (best-effort)."""
        if not self._file.exists():
            return
        try:
            data = json.loads(self._file.read_text())
            self._entries = [
                FeedbackEntry(**e) for e in data.get("entries", [])
            ]
            self._stats = {
                name: ToolStats(**s)
                for name, s in data.get("stats", {}).items()
            }
            logger.debug(
                "Loaded %d feedback entries from %s",
                len(self._entries),
                self._file,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not load feedback: %s", exc)
            self._entries = []
            self._stats = {}
