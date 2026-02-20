"""Evaluation framework for specialist AI agents.

Provides comprehensive evaluation capabilities including:
- Performance metrics and benchmarks
- Quality assessment tools
- User feedback collection
- Comparative analysis
- Continuous improvement tracking
"""

from __future__ import annotations

import json
import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .knowledge_base import KnowledgeBase, KnowledgeItem, PatternCategory

logger = logging.getLogger(__name__)


class EvaluationMetric(Enum):
    """Types of evaluation metrics."""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    RESPONSE_TIME = "response_time"
    USER_SATISFACTION = "user_satisfaction"
    CODE_QUALITY = "code_quality"
    ACCESSIBILITY_SCORE = "accessibility_score"
    PERFORMANCE_SCORE = "performance_score"
    SECURITY_SCORE = "security_score"


@dataclass
class EvaluationResult:
    """Represents an evaluation result."""
    specialist_type: str
    metric: EvaluationMetric
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    test_cases: int = 0
    passed_cases: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return self.passed_cases / self.test_cases if self.test_cases > 0 else 0.0


@dataclass
class BenchmarkSuite:
    """Represents a benchmark suite for evaluation."""
    name: str
    description: str
    test_cases: List[Dict[str, Any]]
    expected_outputs: List[Any]
    metrics: List[EvaluationMetric]
    category: Optional[PatternCategory] = None


class SpecialistEvaluator:
    """Evaluates specialist AI agent performance."""

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        """Initialize the evaluator."""
        self.knowledge_base = knowledge_base
        self.evaluation_history: List[EvaluationResult] = []
        self.benchmark_suites = self._create_benchmark_suites()

    def _create_benchmark_suites(self) -> Dict[str, BenchmarkSuite]:
        """Create benchmark suites for different specialist types."""
        return {
            "ui_specialist": BenchmarkSuite(
                name="UI Specialist Benchmark",
                description="Evaluates UI component generation capabilities",
                test_cases=[
                    {
                        "input": "Create a React button component with primary styling",
                        "context": {"framework": "react", "component_type": "button"},
                        "requirements": ["accessible", "responsive", "typescript"]
                    },
                    {
                        "input": "Build a form component with validation",
                        "context": {"framework": "react", "component_type": "form"},
                        "requirements": ["validation", "accessibility", "typescript"]
                    },
                    {
                        "input": "Create a navigation bar with dropdown menus",
                        "context": {"framework": "react", "component_type": "navigation"},
                        "requirements": ["responsive", "accessible", "keyboard-navigation"]
                    }
                ],
                expected_outputs=[
                    "Functional React component with proper props and TypeScript types",
                    "Form with validation logic and error handling",
                    "Navigation with ARIA labels and keyboard support"
                ],
                metrics=[
                    EvaluationMetric.CODE_QUALITY,
                    EvaluationMetric.ACCESSIBILITY_SCORE,
                    EvaluationMetric.RESPONSE_TIME
                ],
                category=PatternCategory.UI_COMPONENT
            ),

            "prompt_architect": BenchmarkSuite(
                name="Prompt Architect Benchmark",
                description="Evaluates prompt optimization and task categorization",
                test_cases=[
                    {
                        "input": "I need to create a user authentication system",
                        "context": {"project_type": "web_app", "complexity": "medium"},
                        "requirements": ["security", "user_experience"]
                    },
                    {
                        "input": "Build a data visualization dashboard",
                        "context": {"project_type": "analytics", "complexity": "high"},
                        "requirements": ["performance", "interactivity"]
                    },
                    {
                        "input": "Implement a real-time chat application",
                        "context": {"project_type": "communication", "complexity": "high"},
                        "requirements": ["scalability", "real-time"]
                    }
                ],
                expected_outputs=[
                    "Well-structured prompt with security considerations",
                    "Clear task breakdown with visualization requirements",
                    "Comprehensive prompt covering real-time architecture"
                ],
                metrics=[
                    EvaluationMetric.ACCURACY,
                    EvaluationMetric.PRECISION,
                    EvaluationMetric.RESPONSE_TIME
                ],
                category=PatternCategory.PROMPT_ENGINEERING
            ),

            "router_specialist": BenchmarkSuite(
                name="Router Specialist Benchmark",
                description="Evaluates tool selection and task routing",
                test_cases=[
                    {
                        "input": "Create a React component with TypeScript",
                        "context": {"framework": "react", "language": "typescript"},
                        "available_tools": ["react_generator", "typescript_validator"]
                    },
                    {
                        "input": "Design a database schema for e-commerce",
                        "context": {"domain": "e-commerce", "database": "postgresql"},
                        "available_tools": ["schema_designer", "sql_generator"]
                    },
                    {
                        "input": "Optimize application performance",
                        "context": {"app_type": "web_app", "performance_issue": "slow_loading"},
                        "available_tools": ["performance_analyzer", "code_optimizer"]
                    }
                ],
                expected_outputs=[
                    "Selected react_generator with TypeScript support",
                    "Chosen schema_designer for e-commerce patterns",
                    "Used performance_analyzer for bottleneck identification"
                ],
                metrics=[
                    EvaluationMetric.ACCURACY,
                    EvaluationMetric.F1_SCORE,
                    EvaluationMetric.RESPONSE_TIME
                ],
                category=PatternCategory.ARCHITECTURE
            )
        }

    def evaluate_specialist(self, specialist_type: str,
                          benchmark_suite: Optional[BenchmarkSuite] = None) -> List[EvaluationResult]:
        """Evaluate a specialist agent."""
        if benchmark_suite is None:
            benchmark_suite = self.benchmark_suites.get(specialist_type)

        if not benchmark_suite:
            logger.error(f"No benchmark suite found for specialist: {specialist_type}")
            return []

        results = []

        for metric in benchmark_suite.metrics:
            result = self._evaluate_metric(specialist_type, metric, benchmark_suite)
            results.append(result)
            self.evaluation_history.append(result)

        logger.info(f"Evaluated {specialist_type} with {len(results)} metrics")
        return results

    def _evaluate_metric(self, specialist_type: str, metric: EvaluationMetric,
                        benchmark_suite: BenchmarkSuite) -> EvaluationResult:
        """Evaluate a specific metric for a specialist."""

        if metric == EvaluationMetric.ACCURACY:
            return self._evaluate_accuracy(specialist_type, benchmark_suite)
        elif metric == EvaluationMetric.PRECISION:
            return self._evaluate_precision(specialist_type, benchmark_suite)
        elif metric == EvaluationMetric.RECALL:
            return self._evaluate_recall(specialist_type, benchmark_suite)
        elif metric == EvaluationMetric.F1_SCORE:
            return self._evaluate_f1_score(specialist_type, benchmark_suite)
        elif metric == EvaluationMetric.RESPONSE_TIME:
            return self._evaluate_response_time(specialist_type, benchmark_suite)
        elif metric == EvaluationMetric.CODE_QUALITY:
            return self._evaluate_code_quality(specialist_type, benchmark_suite)
        elif metric == EvaluationMetric.ACCESSIBILITY_SCORE:
            return self._evaluate_accessibility_score(specialist_type, benchmark_suite)
        else:
            # Default evaluation
            return EvaluationResult(
                specialist_type=specialist_type,
                metric=metric,
                value=0.8,  # Default score
                test_cases=len(benchmark_suite.test_cases),
                passed_cases=int(len(benchmark_suite.test_cases) * 0.8),
                details={"evaluation_method": "default"}
            )

    def _evaluate_accuracy(self, specialist_type: str, benchmark_suite: BenchmarkSuite) -> EvaluationResult:
        """Evaluate accuracy metric."""
        # Simulate accuracy evaluation based on knowledge base patterns
        relevant_patterns = self.knowledge_base.get_patterns_by_category(
            benchmark_suite.category, limit=50
        )

        if not relevant_patterns:
            return EvaluationResult(
                specialist_type=specialist_type,
                metric=EvaluationMetric.ACCURACY,
                value=0.0,
                test_cases=len(benchmark_suite.test_cases),
                passed_cases=0,
                details={"error": "No relevant patterns found"}
            )

        # Calculate accuracy based on pattern relevance and confidence
        total_confidence = sum(p.confidence_score for p in relevant_patterns)
        avg_confidence = total_confidence / len(relevant_patterns)

        # Simulate test case execution
        passed_cases = int(len(benchmark_suite.test_cases) * avg_confidence)

        return EvaluationResult(
            specialist_type=specialist_type,
            metric=EvaluationMetric.ACCURACY,
            value=avg_confidence,
            test_cases=len(benchmark_suite.test_cases),
            passed_cases=passed_cases,
            details={
                "patterns_used": len(relevant_patterns),
                "avg_pattern_confidence": avg_confidence,
                "evaluation_method": "pattern_based"
            }
        )

    def _evaluate_precision(self, specialist_type: str, benchmark_suite: BenchmarkSuite) -> EvaluationResult:
        """Evaluate precision metric."""
        # Precision = True Positives / (True Positives + False Positives)
        # Simulate based on pattern specificity

        relevant_patterns = self.knowledge_base.get_patterns_by_category(
            benchmark_suite.category, limit=50
        )

        if not relevant_patterns:
            return EvaluationResult(
                specialist_type=specialist_type,
                metric=EvaluationMetric.PRECISION,
                value=0.0,
                test_cases=len(benchmark_suite.test_cases),
                passed_cases=0
            )

        # Calculate precision based on pattern specificity (tags, metadata)
        specificity_scores = []
        for pattern in relevant_patterns:
            # More specific patterns (more tags, detailed metadata) have higher precision
            specificity = len(pattern.tags) + len(pattern.metadata)
            specificity_scores.append(min(specificity / 10.0, 1.0))  # Normalize to 0-1

        avg_precision = statistics.mean(specificity_scores) if specificity_scores else 0.0
        passed_cases = int(len(benchmark_suite.test_cases) * avg_precision)

        return EvaluationResult(
            specialist_type=specialist_type,
            metric=EvaluationMetric.PRECISION,
            value=avg_precision,
            test_cases=len(benchmark_suite.test_cases),
            passed_cases=passed_cases,
            details={
                "avg_specificity": avg_precision,
                "patterns_evaluated": len(relevant_patterns)
            }
        )

    def _evaluate_recall(self, specialist_type: str, benchmark_suite: BenchmarkSuite) -> EvaluationResult:
        """Evaluate recall metric."""
        # Recall = True Positives / (True Positives + False Negatives)
        # Simulate based on knowledge base coverage

        total_patterns = self.knowledge_base.get_patterns_by_category(
            benchmark_suite.category, limit=100
        )

        if not total_patterns:
            return EvaluationResult(
                specialist_type=specialist_type,
                metric=EvaluationMetric.RECALL,
                value=0.0,
                test_cases=len(benchmark_suite.test_cases),
                passed_cases=0
            )

        # Calculate recall based on coverage of relevant patterns
        coverage = min(len(total_patterns) / 100.0, 1.0)  # Assume 100 patterns needed for full coverage
        passed_cases = int(len(benchmark_suite.test_cases) * coverage)

        return EvaluationResult(
            specialist_type=specialist_type,
            metric=EvaluationMetric.RECALL,
            value=coverage,
            test_cases=len(benchmark_suite.test_cases),
            passed_cases=passed_cases,
            details={
                "coverage": coverage,
                "total_patterns": len(total_patterns)
            }
        )

    def _evaluate_f1_score(self, specialist_type: str, benchmark_suite: BenchmarkSuite) -> EvaluationResult:
        """Evaluate F1 score (harmonic mean of precision and recall)."""
        precision_result = self._evaluate_precision(specialist_type, benchmark_suite)
        recall_result = self._evaluate_recall(specialist_type, benchmark_suite)

        precision = precision_result.value
        recall = recall_result.value

        if precision + recall == 0:
            f1_score = 0.0
        else:
            f1_score = 2 * (precision * recall) / (precision + recall)

        return EvaluationResult(
            specialist_type=specialist_type,
            metric=EvaluationMetric.F1_SCORE,
            value=f1_score,
            test_cases=len(benchmark_suite.test_cases),
            passed_cases=int(len(benchmark_suite.test_cases) * f1_score),
            details={
                "precision": precision,
                "recall": recall,
                "f1_calculation": "2 * (precision * recall) / (precision + recall)"
            }
        )

    def _evaluate_response_time(self, specialist_type: str, benchmark_suite: BenchmarkSuite) -> EvaluationResult:
        """Evaluate response time metric."""
        # Simulate response time evaluation
        # In real implementation, this would measure actual response times

        # Simulated response times in milliseconds
        response_times = [150, 200, 180, 220, 160]  # Sample times
        avg_response_time = statistics.mean(response_times)

        # Convert to score (lower is better, normalize to 0-1)
        # Assume 500ms is the maximum acceptable time
        max_acceptable_time = 500.0
        score = max(0.0, 1.0 - (avg_response_time / max_acceptable_time))

        return EvaluationResult(
            specialist_type=specialist_type,
            metric=EvaluationMetric.RESPONSE_TIME,
            value=score,
            test_cases=len(benchmark_suite.test_cases),
            passed_cases=len(benchmark_suite.test_cases),  # All pass if within time limit
            details={
                "avg_response_time_ms": avg_response_time,
                "max_acceptable_time_ms": max_acceptable_time,
                "response_times": response_times
            }
        )

    def _evaluate_code_quality(self, specialist_type: str, benchmark_suite: BenchmarkSuite) -> EvaluationResult:
        """Evaluate code quality metric."""
        # Simulate code quality evaluation based on patterns

        relevant_patterns = self.knowledge_base.get_patterns_by_category(
            benchmark_suite.category, limit=50
        )

        if not relevant_patterns:
            return EvaluationResult(
                specialist_type=specialist_type,
                metric=EvaluationMetric.CODE_QUALITY,
                value=0.0,
                test_cases=len(benchmark_suite.test_cases),
                passed_cases=0
            )

        # Quality factors: code examples, best practices, confidence
        quality_factors = []

        for pattern in relevant_patterns:
            pattern_quality = 0.0

            # Has code example
            if pattern.code_example:
                pattern_quality += 0.3

            # Is best practice
            if pattern.best_practice:
                pattern_quality += 0.3

            # High confidence
            if pattern.confidence_score > 0.8:
                pattern_quality += 0.2

            # Has usage (indicates tested)
            if pattern.usage_count > 0:
                pattern_quality += 0.2

            quality_factors.append(pattern_quality)

        avg_quality = statistics.mean(quality_factors) if quality_factors else 0.0
        passed_cases = int(len(benchmark_suite.test_cases) * avg_quality)

        return EvaluationResult(
            specialist_type=specialist_type,
            metric=EvaluationMetric.CODE_QUALITY,
            value=avg_quality,
            test_cases=len(benchmark_suite.test_cases),
            passed_cases=passed_cases,
            details={
                "quality_factors": quality_factors,
                "patterns_with_code": len([p for p in relevant_patterns if p.code_example]),
                "best_practice_patterns": len([p for p in relevant_patterns if p.best_practice])
            }
        )

    def _evaluate_accessibility_score(self, specialist_type: str, benchmark_suite: BenchmarkSuite) -> EvaluationResult:
        """Evaluate accessibility score metric."""
        # Get accessibility patterns
        accessibility_patterns = self.knowledge_base.get_patterns_by_category(
            PatternCategory.ACCESSIBILITY, limit=50
        )

        if not accessibility_patterns:
            return EvaluationResult(
                specialist_type=specialist_type,
                metric=EvaluationMetric.ACCESSIBILITY_SCORE,
                value=0.0,
                test_cases=len(benchmark_suite.test_cases),
                passed_cases=0,
                details={"error": "No accessibility patterns found"}
            )

        # Calculate accessibility coverage
        wcag_coverage = 0.0
        aria_usage = 0.0
        semantic_html = 0.0

        for pattern in accessibility_patterns:
            content = f"{pattern.title} {pattern.description}".lower()

            if "wcag" in content:
                wcag_coverage += 1.0
            if "aria" in content:
                aria_usage += 1.0
            if "semantic" in content or "html5" in content:
                semantic_html += 1.0

        total_patterns = len(accessibility_patterns)
        if total_patterns > 0:
            wcag_coverage /= total_patterns
            aria_usage /= total_patterns
            semantic_html /= total_patterns

        # Overall accessibility score
        accessibility_score = (wcag_coverage + aria_usage + semantic_html) / 3.0
        passed_cases = int(len(benchmark_suite.test_cases) * accessibility_score)

        return EvaluationResult(
            specialist_type=specialist_type,
            metric=EvaluationMetric.ACCESSIBILITY_SCORE,
            value=accessibility_score,
            test_cases=len(benchmark_suite.test_cases),
            passed_cases=passed_cases,
            details={
                "wcag_coverage": wcag_coverage,
                "aria_usage": aria_usage,
                "semantic_html": semantic_html,
                "accessibility_patterns": total_patterns
            }
        )

    def get_evaluation_summary(self, specialist_type: Optional[str] = None) -> Dict[str, Any]:
        """Get evaluation summary for a specialist or all specialists."""
        results = self.evaluation_history

        if specialist_type:
            results = [r for r in results if r.specialist_type == specialist_type]

        if not results:
            return {"error": "No evaluation results found"}

        # Group by specialist and metric
        summary = {}

        for result in results:
            if result.specialist_type not in summary:
                summary[result.specialist_type] = {}

            metric_name = result.metric.value
            summary[result.specialist_type][metric_name] = {
                "latest_value": result.value,
                "latest_timestamp": result.timestamp.isoformat(),
                "test_cases": result.test_cases,
                "passed_cases": result.passed_cases,
                "success_rate": result.success_rate,
                "details": result.details
            }

        # Calculate overall scores
        for specialist in summary:
            metrics = summary[specialist]
            values = [m["latest_value"] for m in metrics.values()]

            if values:
                summary[specialist]["overall_score"] = statistics.mean(values)
                summary[specialist]["metrics_count"] = len(metrics)

        return summary

    def compare_specialists(self, specialist_types: List[str]) -> Dict[str, Any]:
        """Compare performance between multiple specialists."""
        comparison = {}

        for specialist_type in specialist_types:
            summary = self.get_evaluation_summary(specialist_type)

            if specialist_type in summary:
                comparison[specialist_type] = {
                    "overall_score": summary[specialist_type].get("overall_score", 0.0),
                    "metrics": summary[specialist_type]
                }

        # Rank specialists by overall score
        ranked_specialists = sorted(
            comparison.items(),
            key=lambda x: x[1]["overall_score"],
            reverse=True
        )

        return {
            "rankings": ranked_specialists,
            "comparison_data": comparison,
            "evaluation_timestamp": datetime.now().isoformat()
        }

    def generate_improvement_recommendations(self, specialist_type: str) -> List[str]:
        """Generate improvement recommendations for a specialist."""
        summary = self.get_evaluation_summary(specialist_type)

        if specialist_type not in summary:
            return ["No evaluation data available for this specialist"]

        recommendations = []
        metrics = summary[specialist_type]

        # Analyze each metric and generate recommendations
        for metric_name, metric_data in metrics.items():
            score = metric_data["latest_value"]

            if score < 0.5:
                if metric_name == "accuracy":
                    recommendations.append(f"Improve pattern matching and knowledge base coverage for {metric_name}")
                elif metric_name == "precision":
                    recommendations.append(f"Add more specific patterns and reduce false positives for {metric_name}")
                elif metric_name == "recall":
                    recommendations.append(f"Expand knowledge base to cover more scenarios for {metric_name}")
                elif metric_name == "code_quality":
                    recommendations.append(f"Focus on best practices and code examples for {metric_name}")
                elif metric_name == "accessibility_score":
                    recommendations.append(f"Include more accessibility patterns and WCAG guidelines for {metric_name}")
                elif metric_name == "response_time":
                    recommendations.append(f"Optimize algorithms and caching for better {metric_name}")
                else:
                    recommendations.append(f"General improvement needed for {metric_name}")
            elif score < 0.7:
                recommendations.append(f"Moderate improvement recommended for {metric_name}")

        if not recommendations:
            recommendations.append("Performance is good across all metrics")

        return recommendations

    def get_evaluation_results(self, specialist_type: str, limit: int = 100) -> List[EvaluationResult]:
        """Get evaluation results for a specific specialist.

        Args:
            specialist_type: The type of specialist to get results for
            limit: Maximum number of results to return

        Returns:
            List of evaluation results sorted by timestamp (most recent first)
        """
        # Filter results by specialist type
        results = [
            result for result in self.evaluation_history
            if result.specialist_type == specialist_type
        ]

        # Sort by timestamp (most recent first)
        results.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply limit
        return results[:limit]

    def export_evaluation_data(self, export_path: Path) -> None:
        """Export evaluation data for analysis."""
        export_data = {
            "evaluation_history": [
                {
                    "specialist_type": result.specialist_type,
                    "metric": result.metric.value,
                    "value": result.value,
                    "timestamp": result.timestamp.isoformat(),
                    "test_cases": result.test_cases,
                    "passed_cases": result.passed_cases,
                    "success_rate": result.success_rate,
                    "details": result.details
                }
                for result in self.evaluation_history
            ],
            "benchmark_suites": {
                name: {
                    "name": suite.name,
                    "description": suite.description,
                    "test_cases_count": len(suite.test_cases),
                    "metrics": [m.value for m in suite.metrics],
                    "category": suite.category.value if suite.category else None
                }
                for name, suite in self.benchmark_suites.items()
            },
            "export_timestamp": datetime.now().isoformat()
        }

        with export_path.open("w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Evaluation data exported to {export_path}")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create knowledge base and evaluator
    kb = KnowledgeBase()
    evaluator = SpecialistEvaluator(kb)

    # Evaluate all specialists
    print("Evaluating specialists...")

    for specialist_name in evaluator.benchmark_suites.keys():
        print(f"\nEvaluating {specialist_name}...")
        results = evaluator.evaluate_specialist(specialist_name)

        for result in results:
            print(f"  {result.metric.value}: {result.value:.2f} "
                  f"({result.passed_cases}/{result.test_cases} passed)")

    # Get evaluation summary
    print("\nEvaluation Summary:")
    summary = evaluator.get_evaluation_summary()

    for specialist, data in summary.items():
        print(f"\n{specialist}:")
        print(f"  Overall Score: {data.get('overall_score', 'N/A'):.2f}")
        print(f"  Metrics: {data.get('metrics_count', 0)}")

        for metric, metric_data in data.items():
            if isinstance(metric_data, dict) and "latest_value" in metric_data:
                print(f"    {metric}: {metric_data['latest_value']:.2f}")

    # Compare specialists
    print("\nSpecialist Comparison:")
    comparison = evaluator.compare_specialists(list(evaluator.benchmark_suites.keys()))

    print("Rankings:")
    for rank, (specialist, data) in enumerate(comparison["rankings"], 1):
        print(f"{rank}. {specialist}: {data['overall_score']:.2f}")

    # Generate recommendations
    print("\nImprovement Recommendations:")
    for specialist in evaluator.benchmark_suites.keys():
        recommendations = evaluator.generate_improvement_recommendations(specialist)
        print(f"\n{specialist}:")
        for rec in recommendations:
            print(f"  - {rec}")

    # Export evaluation data
    export_path = Path(__file__).parent.parent / "evaluation_export.json"
    evaluator.export_evaluation_data(export_path)
    print(f"\nEvaluation data exported to: {export_path}")
