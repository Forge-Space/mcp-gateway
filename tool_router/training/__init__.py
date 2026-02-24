"""Training module for specialist AI agents.

Provides comprehensive training infrastructure including:
- Data extraction from public sources
- Knowledge base management
- Pattern recognition and categorization
- Training pipeline orchestration
- Evaluation and continuous learning
"""

from __future__ import annotations

from .data_extraction import DataSource, PatternExtractor
from .evaluation import EvaluationMetric, SpecialistEvaluator
from .knowledge_base import KnowledgeBase, PatternCategory
from .training_pipeline import TrainingPipeline

__all__ = [
    "DataSource",
    "EvaluationMetric",
    "KnowledgeBase",
    "PatternCategory",
    "PatternExtractor",
    "SpecialistEvaluator",
    "TrainingPipeline",
]
