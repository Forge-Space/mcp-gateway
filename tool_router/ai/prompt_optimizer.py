"""Automatic prompt optimization loop.

Enriches generation prompts with feedback-derived insights,
entity hints, and historical success patterns.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    original_prompt: str
    optimized_prompt: str
    additions: list[str] = field(default_factory=list)
    strategy: str = "none"


_VAGUE_TERMS = {
    "nice": "polished and visually refined",
    "cool": "modern with subtle animations",
    "simple": "clean and minimal with clear hierarchy",
    "fancy": "sophisticated with layered visual effects",
    "good": "well-structured and maintainable",
    "pretty": "aesthetically pleasing with consistent spacing",
    "basic": "fundamental with proper semantic structure",
}

_COMPONENT_HINTS = {
    "form": "Include validation, error states, and submit handling",
    "table": "Include sorting, pagination, and responsive overflow",
    "modal": "Trap focus, handle Escape, restore focus on close",
    "nav": "Use aria-current, landmark roles, and skip links",
    "card": "Include hover state, consistent padding, and alt text",
    "chart": "Include accessible labels and color-blind patterns",
    "dashboard": "Use grid layout with stat cards and responsive breakpoints",
    "button": "Include loading, disabled states, and aria-label",
}


class PromptOptimizer:
    """Enriches prompts with learned patterns and best practices."""

    def __init__(
        self,
        feedback_store: Any = None,
        enable_learning: bool = True,
    ) -> None:
        self._feedback = feedback_store
        self._enable_learning = enable_learning

    def optimize(
        self,
        prompt: str,
        task_type: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> OptimizationResult:
        additions: list[str] = []
        optimized = prompt
        strategy_parts: list[str] = []

        expanded, vague_additions = self._expand_vague_terms(optimized)
        if vague_additions:
            optimized = expanded
            additions.extend(vague_additions)
            strategy_parts.append("vague_expansion")

        hint = self._add_component_hints(optimized)
        if hint:
            optimized = f"{optimized}. {hint}"
            additions.append(f"Component hint: {hint}")
            strategy_parts.append("component_hint")

        a11y_add = self._ensure_accessibility(optimized)
        if a11y_add:
            optimized = f"{optimized}. {a11y_add}"
            additions.append(f"A11y: {a11y_add}")
            strategy_parts.append("a11y")

        responsive_add = self._ensure_responsive(optimized)
        if responsive_add:
            optimized = f"{optimized}. {responsive_add}"
            additions.append(f"Responsive: {responsive_add}")
            strategy_parts.append("responsive")

        if self._enable_learning and self._feedback:
            learning_adds = self._apply_learning_insights(optimized, task_type)
            if learning_adds:
                additions.extend(learning_adds)
                strategy_parts.append("learning")

        strategy = "+".join(strategy_parts) if strategy_parts else "none"

        return OptimizationResult(
            original_prompt=prompt,
            optimized_prompt=optimized,
            additions=additions,
            strategy=strategy,
        )

    def _expand_vague_terms(self, prompt: str) -> tuple[str, list[str]]:
        expanded = prompt
        additions = []
        lower = prompt.lower()
        for vague, replacement in _VAGUE_TERMS.items():
            pattern = re.compile(rf"\b{re.escape(vague)}\b", re.IGNORECASE)
            if pattern.search(lower):
                expanded = pattern.sub(replacement, expanded)
                additions.append(f"Expanded '{vague}' → '{replacement}'")
        return expanded, additions

    def _add_component_hints(self, prompt: str) -> str | None:
        lower = prompt.lower()
        for component, hint in _COMPONENT_HINTS.items():
            if component in lower and hint.lower().split()[0] not in lower:
                return hint
        return None

    def _ensure_accessibility(self, prompt: str) -> str | None:
        lower = prompt.lower()
        a11y_keywords = ["aria", "accessible", "a11y", "wcag", "screen reader"]
        if any(k in lower for k in a11y_keywords):
            return None
        return "Include ARIA labels and keyboard navigation support"

    def _ensure_responsive(self, prompt: str) -> str | None:
        lower = prompt.lower()
        responsive_keywords = ["responsive", "mobile", "breakpoint", "sm:", "md:"]
        if any(k in lower for k in responsive_keywords):
            return None
        return "Responsive across mobile, tablet, and desktop"

    def _apply_learning_insights(self, prompt: str, _task_type: str | None) -> list[str]:
        additions = []
        try:
            if hasattr(self._feedback, "get_learning_insights"):
                insights = self._feedback.get_learning_insights(prompt)
                if insights.get("recommended_tools"):
                    tools = insights["recommended_tools"][:3]
                    tool_names = [t["tool"] for t in tools if "tool" in t]
                    if tool_names:
                        additions.append(f"Recommended tools: {', '.join(tool_names)}")
        except Exception:
            logger.debug("Failed to fetch learning insights")
        return additions
