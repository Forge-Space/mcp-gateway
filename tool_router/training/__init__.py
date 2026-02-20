"""Training module for AI specialist agents.

This module provides the foundational data layer for the AI training system,
including knowledge base management, pattern extraction, and data models.
"""

from .data_extraction import DataSource, ExtractedPattern, PatternCategory
from .knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeStatus


__all__ = [
    "DataSource",
    "ExtractedPattern",
    "KnowledgeBase",
    "KnowledgeItem",
    "KnowledgeStatus",
    "PatternCategory",
]
