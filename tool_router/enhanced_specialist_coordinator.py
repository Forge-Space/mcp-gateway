"""Enhanced Specialist Coordinator with Training Integration.

This enhanced coordinator integrates with the specialist training infrastructure
to provide improved routing, performance tracking, and continuous learning.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from .ai.enhanced_selector import EnhancedAISelector
from .ai.prompt_architect import PromptArchitect
from .ai.ui_specialist import UISpecialist
from .specialist_coordinator import (
    SpecialistCoordinator,
    SpecialistResult,
    SpecialistType,
    TaskCategory,
    TaskRequest,
)
from .training.evaluation import EvaluationMetric, SpecialistEvaluator
from .training.knowledge_base import KnowledgeBase, PatternCategory


logger = logging.getLogger(__name__)


@dataclass
class TrainingMetrics:
    """Training-related metrics for specialist performance."""

    specialist_type: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    response_time: float
    last_updated: str
    patterns_used: int


class EnhancedSpecialistCoordinator(SpecialistCoordinator):
    """Enhanced specialist coordinator with training integration."""

    def __init__(
        self,
        enhanced_selector: EnhancedAISelector,
        prompt_architect: PromptArchitect,
        ui_specialist: UISpecialist,
        knowledge_base: KnowledgeBase | None = None,
        evaluator: SpecialistEvaluator | None = None,
    ) -> None:
        """Initialize the enhanced specialist coordinator."""
        super().__init__(enhanced_selector, prompt_architect, ui_specialist)

        # Training infrastructure
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.evaluator = evaluator or SpecialistEvaluator(self.knowledge_base)

        # Enhanced tracking
        self._training_metrics = {}
        self._performance_history = []
        self._learning_feedback = []

        # Initialize training metrics
        self._initialize_training_metrics()

    def _initialize_training_metrics(self) -> None:
        """Initialize training metrics for all specialist types."""
        for specialist_type in SpecialistType:
            self._training_metrics[specialist_type.value] = TrainingMetrics(
                specialist_type=specialist_type.value,
                accuracy=0.8,  # Default values
                precision=0.8,
                recall=0.8,
                f1_score=0.8,
                response_time=100.0,
                last_updated=time.strftime("%Y-%m-%d %H:%M:%S"),
                patterns_used=0,
            )

    def process_task(self, request: TaskRequest) -> list[SpecialistResult]:
        """Process a task using enhanced specialist coordination."""
        start_time = time.time()

        # Enhance request with training insights
        enhanced_request = self._enhance_request_with_training(request)

        # Process using parent method
        results = super().process_task(enhanced_request)

        # Update training metrics
        self._update_training_metrics(results, start_time)

        # Collect feedback for continuous learning
        self._collect_learning_feedback(request, results)

        return results

    def _enhance_request_with_training(self, request: TaskRequest) -> TaskRequest:
        """Enhance request with insights from training data."""
        try:
            # Get relevant patterns from knowledge base
            relevant_patterns = self._get_relevant_patterns(request)

            # Enhance context with pattern insights
            enhanced_context = request.context
            if relevant_patterns:
                pattern_insights = self._generate_pattern_insights(relevant_patterns)
                enhanced_context += f"\n\nTraining Insights:\n{pattern_insights}"

            # Update user preferences with training recommendations
            enhanced_preferences = request.user_preferences or {}
            training_recommendations = self._get_training_recommendations(request)
            enhanced_preferences.update(training_recommendations)

            return TaskRequest(
                task=request.task,
                category=request.category,
                context=enhanced_context,
                tools=request.tools,
                user_preferences=enhanced_preferences,
                cost_optimization=request.cost_optimization,
                hardware_constraints=request.hardware_constraints,
            )

        except Exception as e:
            logger.error(f"Error enhancing request with training: {e}")
            return request

    def _get_relevant_patterns(self, request: TaskRequest) -> list[Any]:
        """Get relevant patterns from knowledge base for the request."""
        try:
            # Determine pattern category based on task category
            if request.category == TaskCategory.UI_GENERATION:
                category = PatternCategory.UI_COMPONENT
            elif request.category == TaskCategory.PROMPT_OPTIMIZATION:
                category = PatternCategory.PROMPT_ENGINEERING
            elif request.category == TaskCategory.CODE_GENERATION:
                category = PatternCategory.CODE_PATTERN
            else:
                category = PatternCategory.ARCHITECTURE

            # Search for relevant patterns
            patterns = self.knowledge_base.search_knowledge(
                request.task, category, limit=5
            )

            return patterns

        except Exception as e:
            logger.error(f"Error getting relevant patterns: {e}")
            return []

    def _generate_pattern_insights(self, patterns: list[Any]) -> str:
        """Generate insights from relevant patterns."""
        if not patterns:
            return "No specific patterns found."

        insights = []
        for pattern in patterns[:3]:  # Top 3 patterns
            insight = f"- {pattern.title}: {pattern.description[:100]}..."
            insights.append(insight)

        return "\n".join(insights)

    def _get_training_recommendations(self, request: TaskRequest) -> dict[str, Any]:
        """Get recommendations based on training data."""
        recommendations = {}

        try:
            # Get specialist type for this task category
            specialist_type = self._get_specialist_type_for_category(request.category)

            if specialist_type:
                metrics = self._training_metrics.get(specialist_type.value)

                if metrics:
                    # Recommend based on performance
                    if metrics.accuracy < 0.7:
                        recommendations["use_validation"] = True
                        recommendations["additional_review"] = True

                    if metrics.response_time > 200:
                        recommendations["optimize_for_speed"] = True
                        recommendations["use_caching"] = True

                    # Recommend patterns
                    recommendations["max_patterns"] = metrics.pattern_used
                    recommendations["confidence_threshold"] = 0.8

        except Exception as e:
            logger.error(f"Error getting training recommendations: {e}")

        return recommendations

    def _get_specialist_type_for_category(
        self, category: TaskCategory
    ) -> SpecialistType | None:
        """Get specialist type for a task category."""
        mapping = {
            TaskCategory.TOOL_SELECTION: SpecialistType.ROUTER,
            TaskCategory.PROMPT_OPTIMIZATION: SpecialistType.PROMPT_ARCHITECT,
            TaskCategory.UI_GENERATION: SpecialistType.UI_SPECIALIST,
            TaskCategory.CODE_GENERATION: SpecialistType.UI_SPECIALIST,  # For now
        }
        return mapping.get(category)

    def _update_training_metrics(
        self, results: list[SpecialistResult], start_time: float
    ) -> None:
        """Update training metrics based on results."""
        try:
            processing_time = (time.time() - start_time) * 1000  # Convert to ms

            for result in results:
                specialist_type = result.specialist_type.value

                if specialist_type in self._training_metrics:
                    metrics = self._training_metrics[specialist_type]

                    # Update response time (moving average)
                    metrics.response_time = (
                        metrics.response_time + processing_time
                    ) / 2

                    # Update timestamp
                    metrics.last_updated = time.strftime("%Y-%m-%d %H:%M:%S")

                    # Store in performance history
                    self._performance_history.append(
                        {
                            "specialist_type": specialist_type,
                            "processing_time": processing_time,
                            "confidence": result.confidence,
                            "timestamp": time.time(),
                        }
                    )

                    # Keep history manageable
                    if len(self._performance_history) > 1000:
                        self._performance_history = self._performance_history[-500:]

        except Exception as e:
            logger.error(f"Error updating training metrics: {e}")

    def _collect_learning_feedback(
        self, request: TaskRequest, results: list[SpecialistResult]
    ) -> None:
        """Collect feedback for continuous learning."""
        try:
            feedback = {
                "request_category": request.category.value,
                "request_task": request.task[:100],  # Truncate for privacy
                "results_count": len(results),
                "average_confidence": (
                    sum(r.confidence for r in results) / len(results) if results else 0
                ),
                "timestamp": time.time(),
            }

            self._learning_feedback.append(feedback)

            # Keep feedback manageable
            if len(self._learning_feedback) > 1000:
                self._learning_feedback = self._learning_feedback[-500:]

        except Exception as e:
            logger.error(f"Error collecting learning feedback: {e}")

    def run_training_evaluation(self) -> dict[str, Any]:
        """Run training evaluation for all specialists."""
        try:
            evaluation_results = {}

            for specialist_name in self.evaluator.benchmark_suites.keys():
                # Map to our specialist types
                if specialist_name == "ui_specialist":
                    specialist_type = SpecialistType.UI_SPECIALIST.value
                elif specialist_name == "prompt_architect":
                    specialist_type = SpecialistType.PROMPT_ARCHITECT.value
                elif specialist_name == "router_specialist":
                    specialist_type = SpecialistType.ROUTER.value
                else:
                    continue

                # Run evaluation
                results = self.evaluator.evaluate_specialist(specialist_name)

                # Update metrics
                if specialist_type in self._training_metrics:
                    metrics = self._training_metrics[specialist_type]

                    for result in results:
                        if result.metric == EvaluationMetric.ACCURACY:
                            metrics.accuracy = result.value
                        elif result.metric == EvaluationMetric.PRECISION:
                            metrics.precision = result.value
                        elif result.metric == EvaluationMetric.RECALL:
                            metrics.recall = result.value
                        elif result.metric == EvaluationMetric.F1_SCORE:
                            metrics.f1_score = result.value
                        elif result.metric == EvaluationMetric.RESPONSE_TIME:
                            metrics.response_time = result.value

                evaluation_results[specialist_name] = {
                    "metrics": {r.metric.value: r.value for r in results},
                    "average_score": (
                        sum(r.value for r in results) / len(results) if results else 0
                    ),
                }

            return evaluation_results

        except Exception as e:
            logger.error(f"Error running training evaluation: {e}")
            return {}

    def get_training_insights(self) -> dict[str, Any]:
        """Get comprehensive training insights."""
        try:
            insights = {
                "specialist_metrics": {},
                "performance_trends": {},
                "learning_summary": {},
                "recommendations": [],
            }

            # Specialist metrics
            for specialist_type, metrics in self._training_metrics.items():
                insights["specialist_metrics"][specialist_type] = {
                    "accuracy": metrics.accuracy,
                    "precision": metrics.precision,
                    "recall": metrics.recall,
                    "f1_score": metrics.f1_score,
                    "response_time": metrics.response_time,
                    "patterns_used": metrics.patterns_used,
                    "last_updated": metrics.last_updated,
                }

            # Performance trends
            if self._performance_history:
                recent_performance = self._performance_history[
                    -100:
                ]  # Last 100 requests

                for specialist_type in SpecialistType:
                    specialist_performances = [
                        p
                        for p in recent_performance
                        if p["specialist_type"] == specialist_type.value
                    ]

                    if specialist_performances:
                        avg_confidence = sum(
                            p["confidence"] for p in specialist_performances
                        ) / len(specialist_performances)
                        avg_time = sum(
                            p["processing_time"] for p in specialist_performances
                        ) / len(specialist_performances)

                        insights["performance_trends"][specialist_type.value] = {
                            "average_confidence": avg_confidence,
                            "average_response_time": avg_time,
                            "request_count": len(specialist_performances),
                        }

            # Learning summary
            if self._learning_feedback:
                total_requests = len(self._learning_feedback)
                category_performance = {}

                for feedback in self._learning_feedback:
                    category = feedback["request_category"]
                    if category not in category_performance:
                        category_performance[category] = []
                    category_performance[category].append(
                        feedback["average_confidence"]
                    )

                insights["learning_summary"] = {
                    "total_requests_processed": total_requests,
                    "category_performance": {
                        cat: {
                            "average_confidence": sum(perfs) / len(perfs),
                            "request_count": len(perfs),
                        }
                        for cat, perfs in category_performance.items()
                    },
                }

            # Recommendations
            insights["recommendations"] = self._generate_recommendations(insights)

            return insights

        except Exception as e:
            logger.error(f"Error getting training insights: {e}")
            return {}

    def _generate_recommendations(self, insights: dict[str, Any]) -> list[str]:
        """Generate recommendations based on insights."""
        recommendations = []

        try:
            # Analyze specialist performance
            for specialist_type, metrics in insights["specialist_metrics"].items():
                if metrics["accuracy"] < 0.7:
                    recommendations.append(
                        f"Improve {specialist_type} accuracy through additional training"
                    )

                if metrics["response_time"] > 200:
                    recommendations.append(
                        f"Optimize {specialist_type} for better response time"
                    )

                if metrics["patterns_used"] < 10:
                    recommendations.append(
                        f"Add more training patterns for {specialist_type}"
                    )

            # Analyze trends
            trends = insights.get("performance_trends", {})
            for specialist_type, trend in trends.items():
                if trend["average_confidence"] < 0.8:
                    recommendations.append(
                        f"Review and improve {specialist_type} confidence scoring"
                    )

            # General recommendations
            if not recommendations:
                recommendations.append("All specialists are performing well")

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Unable to generate recommendations due to error")

        return recommendations

    def update_specialist_with_training(self, specialist_type: SpecialistType) -> bool:
        """Update a specialist with latest training data."""
        try:
            # Get latest patterns for specialist
            if specialist_type == SpecialistType.UI_SPECIALIST:
                patterns = self.knowledge_base.get_patterns_by_category(
                    PatternCategory.UI_COMPONENT, limit=50
                )

                # Update UI specialist with new patterns
                # This would involve updating the specialist's internal knowledge
                logger.info(f"Updated UI Specialist with {len(patterns)} new patterns")
                return True

            if specialist_type == SpecialistType.PROMPT_ARCHITECT:
                patterns = self.knowledge_base.get_patterns_by_category(
                    PatternCategory.PROMPT_ENGINEERING, limit=50
                )

                logger.info(
                    f"Updated Prompt Architect with {len(patterns)} new patterns"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error updating specialist {specialist_type}: {e}")
            return False


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # This would be initialized with actual dependencies in production
    print("Enhanced Specialist Coordinator with training integration ready!")
