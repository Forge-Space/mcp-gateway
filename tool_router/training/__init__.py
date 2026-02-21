"""Training module for specialist AI agents.

Provides comprehensive training infrastructure including:
- Data extraction from public sources
- Knowledge base management
- Pattern recognition and categorization
- Training pipeline orchestration
- Evaluation and continuous learning
"""

from __future__ import annotations

from .data_extraction import PatternExtractor, DataSource
from .knowledge_base import KnowledgeBase, PatternCategory
from .training_pipeline import TrainingPipeline
from .evaluation import SpecialistEvaluator, EvaluationMetric

__all__ = [
    "PatternExtractor",
    "DataSource",
    "KnowledgeBase",
    "PatternCategory",
    "TrainingPipeline",
    "SpecialistEvaluator",
    "EvaluationMetric",
]
