"""Context learning from feedback for AI tool selection."""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tempfile import gettempdir


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


@dataclass
class ToolStats:
    """Aggregated success statistics for a tool."""

    tool_name: str
    success_count: int = 0
    failure_count: int = 0

    @property
    def total(self) -> int:
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.5  # neutral prior
        return self.success_count / self.total


class FeedbackStore:
    """Persistent store for tool selection feedback enabling context learning.

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
        self._load()

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
        """Record the outcome of a tool selection."""
        entry = FeedbackEntry(
            task=task,
            selected_tool=selected_tool,
            success=success,
            context=context,
            confidence=confidence,
        )
        self._entries.append(entry)

        if selected_tool not in self._stats:
            self._stats[selected_tool] = ToolStats(selected_tool)
        stats = self._stats[selected_tool]
        if success:
            stats.success_count += 1
        else:
            stats.failure_count += 1

        # Trim to avoid unbounded growth
        if len(self._entries) > _MAX_ENTRIES:
            self._entries = self._entries[-_MAX_ENTRIES:]

        self._persist()
        logger.debug(
            "Feedback recorded: tool=%s success=%s rate=%.2f",
            selected_tool,
            success,
            stats.success_rate,
        )

    def get_boost(self, tool_name: str) -> float:
        """Return a score multiplier in [0.5, 1.5] based on historical success.

        A tool with no history returns 1.0 (neutral).
        A tool with 100% success returns up to 1.5.
        A tool with 0% success returns 0.5.
        """
        stats = self._stats.get(tool_name)
        if stats is None or stats.total < 3:
            return 1.0  # not enough data
        # Map success_rate [0, 1] -> boost [0.5, 1.5]
        return 0.5 + stats.success_rate

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
