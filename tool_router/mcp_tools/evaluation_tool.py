"""Evaluation MCP Tool.

Provides MCP server tool functionality for evaluating specialist AI agents,
including running evaluations, getting results, and managing evaluation metrics.
"""

from __future__ import annotations

import logging
from typing import Any

from ..training.evaluation import EvaluationMetric, SpecialistEvaluator
from ..training.knowledge_base import KnowledgeBase


logger = logging.getLogger(__name__)


class EvaluationTool:
    """MCP tool for managing specialist AI evaluation operations."""

    def __init__(self) -> None:
        """Initialize the evaluation tool."""
        self.knowledge_base = KnowledgeBase()
        self.evaluator = SpecialistEvaluator(self.knowledge_base)

    def run_evaluation(
        self,
        specialist_name: str,
        benchmark_suite: str | None = None,
        test_cases: int | None = None,
    ) -> dict[str, Any]:
        """Run evaluation for a specialist.

        Args:
            specialist_name: Name of the specialist to evaluate
            benchmark_suite: Optional specific benchmark suite
            test_cases: Optional number of test cases to run

        Returns:
            Evaluation results
        """
        try:
            # Check if specialist exists
            if specialist_name not in self.evaluator.benchmark_suites:
                available_specialists = list(self.evaluator.benchmark_suites.keys())
                return {
                    "error": f"Unknown specialist: {specialist_name}",
                    "message": f"Available specialists: {available_specialists}",
                }

            # Run evaluation
            results = self.evaluator.evaluate_specialist(
                specialist_name=specialist_name,
                benchmark_suite=benchmark_suite,
                test_cases=test_cases,
            )

            # Format results
            formatted_results = []
            total_score = 0
            test_count = 0
            passed_count = 0

            for result in results:
                formatted_results.append(
                    {
                        "metric": result.metric.value,
                        "value": result.value,
                        "test_cases": result.test_cases,
                        "passed_cases": result.passed_cases,
                        "timestamp": result.timestamp,
                        "details": result.details,
                    }
                )

                total_score += result.value
                test_count += result.test_cases
                passed_count += result.passed_cases

            average_score = total_score / len(results) if results else 0
            pass_rate = (passed_count / test_count * 100) if test_count > 0 else 0

            logger.info(
                f"Completed evaluation for {specialist_name}: {len(results)} metrics"
            )

            return {
                "specialist_name": specialist_name,
                "results": formatted_results,
                "summary": {
                    "average_score": round(average_score, 2),
                    "total_test_cases": test_count,
                    "passed_test_cases": passed_count,
                    "pass_rate": round(pass_rate, 2),
                    "metrics_evaluated": len(results),
                },
                "message": "Evaluation completed successfully",
            }

        except Exception as e:
            logger.error(f"Error running evaluation: {e}")
            return {"error": str(e), "message": "Failed to run evaluation"}

    def get_evaluation_history(
        self, specialist_name: str | None = None, limit: int = 50
    ) -> dict[str, Any]:
        """Get evaluation history.

        Args:
            specialist_name: Optional specialist name filter
            limit: Maximum number of results

        Returns:
            Evaluation history
        """
        try:
            # Get evaluation results
            if specialist_name:
                if specialist_name not in self.evaluator.benchmark_suites:
                    available_specialists = list(self.evaluator.benchmark_suites.keys())
                    return {
                        "error": f"Unknown specialist: {specialist_name}",
                        "message": f"Available specialists: {available_specialists}",
                    }

                # Get specific specialist results
                results = self.evaluator.get_evaluation_results(specialist_name, limit)
            else:
                # Get all results
                results = []
                for spec_name in self.evaluator.benchmark_suites.keys():
                    spec_results = self.evaluator.get_evaluation_results(
                        spec_name, limit
                    )
                    results.extend(spec_results)

                # Sort by timestamp and limit
                results.sort(key=lambda x: x.timestamp, reverse=True)
                results = results[:limit]

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "specialist_name": result.specialist_type,
                        "metric": result.metric.value,
                        "value": result.value,
                        "test_cases": result.test_cases,
                        "passed_cases": result.passed_cases,
                        "timestamp": result.timestamp,
                        "details": result.details,
                    }
                )

            return {
                "results": formatted_results,
                "total_results": len(formatted_results),
                "specialist_filter": specialist_name,
                "message": f"Retrieved {len(formatted_results)} evaluation results",
            }

        except Exception as e:
            logger.error(f"Error getting evaluation history: {e}")
            return {"error": str(e), "message": "Failed to get evaluation history"}

    def get_available_specialists(self) -> dict[str, Any]:
        """Get list of available specialists for evaluation.

        Returns:
            Available specialists and their benchmark suites
        """
        try:
            specialists = []

            for specialist_name, suite in self.evaluator.benchmark_suites.items():
                specialists.append(
                    {
                        "name": specialist_name,
                        "description": suite.description,
                        "test_cases_count": len(suite.test_cases),
                        "metrics": [metric.value for metric in suite.metrics],
                    }
                )

            return {
                "specialists": specialists,
                "total_specialists": len(specialists),
                "message": "Available specialists retrieved successfully",
            }

        except Exception as e:
            logger.error(f"Error getting available specialists: {e}")
            return {"error": str(e), "message": "Failed to get available specialists"}

    def get_evaluation_metrics(self) -> dict[str, Any]:
        """Get available evaluation metrics.

        Returns:
            Available evaluation metrics
        """
        try:
            metrics = []

            for metric in EvaluationMetric:
                metrics.append(
                    {
                        "name": metric.value,
                        "description": self._get_metric_description(metric),
                    }
                )

            return {
                "metrics": metrics,
                "total_metrics": len(metrics),
                "message": "Evaluation metrics retrieved successfully",
            }

        except Exception as e:
            logger.error(f"Error getting evaluation metrics: {e}")
            return {"error": str(e), "message": "Failed to get evaluation metrics"}

    def _get_metric_description(self, metric: EvaluationMetric) -> str:
        """Get description for an evaluation metric."""
        descriptions = {
            EvaluationMetric.ACCURACY: "Measures the correctness of specialist outputs",
            EvaluationMetric.PRECISION: "Measures the relevance of positive predictions",
            EvaluationMetric.RECALL: "Measures the ability to find all relevant instances",
            EvaluationMetric.F1_SCORE: "Harmonic mean of precision and recall",
            EvaluationMetric.RESPONSE_TIME: "Measures the speed of specialist responses",
            EvaluationMetric.USER_SATISFACTION: "Measures user satisfaction with outputs",
            EvaluationMetric.CODE_QUALITY: "Measures the quality of generated code",
            EvaluationMetric.ACCESSIBILITY_SCORE: "Measures accessibility compliance",
            EvaluationMetric.PERFORMANCE_SCORE: "Measures overall performance",
            EvaluationMetric.SECURITY_SCORE: "Measures security compliance",
        }
        return descriptions.get(metric, "No description available")

    def compare_specialists(
        self, specialist_names: list[str], metric: str | None = None
    ) -> dict[str, Any]:
        """Compare multiple specialists.

        Args:
            specialist_names: List of specialist names to compare
            metric: Optional specific metric to compare

        Returns:
            Comparison results
        """
        try:
            # Validate specialists
            invalid_specialists = []
            for name in specialist_names:
                if name not in self.evaluator.benchmark_suites:
                    invalid_specialists.append(name)

            if invalid_specialists:
                available_specialists = list(self.evaluator.benchmark_suites.keys())
                return {
                    "error": f"Unknown specialists: {invalid_specialists}",
                    "message": f"Available specialists: {available_specialists}",
                }

            # Get latest results for each specialist
            comparison_data = {}

            for specialist_name in specialist_names:
                results = self.evaluator.get_evaluation_results(specialist_name, 10)

                # Filter by metric if specified
                if metric:
                    try:
                        metric_enum = EvaluationMetric(metric.lower())
                        results = [r for r in results if r.metric == metric_enum]
                    except ValueError:
                        return {
                            "error": f"Unknown metric: {metric}",
                            "message": f"Available metrics: {[m.value for m in EvaluationMetric]}",
                        }

                # Calculate averages
                if results:
                    avg_score = sum(r.value for r in results) / len(results)
                    latest_result = results[0]  # Most recent

                    comparison_data[specialist_name] = {
                        "average_score": round(avg_score, 2),
                        "latest_score": latest_result.value,
                        "latest_timestamp": latest_result.timestamp,
                        "evaluation_count": len(results),
                    }
                else:
                    comparison_data[specialist_name] = {
                        "average_score": 0,
                        "latest_score": 0,
                        "latest_timestamp": None,
                        "evaluation_count": 0,
                    }

            # Sort by average score
            sorted_specialists = sorted(
                comparison_data.items(),
                key=lambda x: x[1]["average_score"],
                reverse=True,
            )

            return {
                "comparison": dict(sorted_specialists),
                "ranking": [item[0] for item in sorted_specialists],
                "metric_filter": metric,
                "message": f"Comparison completed for {len(specialist_names)} specialists",
            }

        except Exception as e:
            logger.error(f"Error comparing specialists: {e}")
            return {"error": str(e), "message": "Failed to compare specialists"}

    def get_evaluation_summary(self) -> dict[str, Any]:
        """Get overall evaluation summary.

        Returns:
            Evaluation summary across all specialists
        """
        try:
            summary = {
                "total_evaluations": 0,
                "specialist_performance": {},
                "metric_averages": {},
                "recent_activity": [],
            }

            # Get results for all specialists
            all_results = []
            for specialist_name in self.evaluator.benchmark_suites.keys():
                results = self.evaluator.get_evaluation_results(specialist_name, 100)
                all_results.extend(results)

            summary["total_evaluations"] = len(all_results)

            # Calculate specialist performance
            specialist_scores = {}
            for result in all_results:
                if result.specialist_type not in specialist_scores:
                    specialist_scores[result.specialist_type] = []
                specialist_scores[result.specialist_type].append(result.value)

            for specialist, scores in specialist_scores.items():
                summary["specialist_performance"][specialist] = {
                    "average_score": round(sum(scores) / len(scores), 2),
                    "evaluation_count": len(scores),
                    "best_score": max(scores),
                    "worst_score": min(scores),
                }

            # Calculate metric averages
            metric_scores = {}
            for result in all_results:
                if result.metric.value not in metric_scores:
                    metric_scores[result.metric.value] = []
                metric_scores[result.metric.value].append(result.value)

            for metric, scores in metric_scores.items():
                summary["metric_averages"][metric] = round(sum(scores) / len(scores), 2)

            # Get recent activity
            all_results.sort(key=lambda x: x.timestamp, reverse=True)
            recent_results = all_results[:10]

            for result in recent_results:
                summary["recent_activity"].append(
                    {
                        "specialist": result.specialist_type,
                        "metric": result.metric.value,
                        "score": result.value,
                        "timestamp": result.timestamp,
                    }
                )

            return {
                "summary": summary,
                "message": "Evaluation summary retrieved successfully",
            }

        except Exception as e:
            logger.error(f"Error getting evaluation summary: {e}")
            return {"error": str(e), "message": "Failed to get evaluation summary"}


# Tool schema for MCP integration
EVALUATION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "run_evaluation",
                "get_history",
                "get_specialists",
                "get_metrics",
                "compare_specialists",
                "get_summary",
            ],
            "description": "The evaluation action to perform",
        },
        "specialist_name": {
            "type": "string",
            "description": "Name of the specialist (for run_evaluation, get_history)",
        },
        "specialist_names": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of specialist names (for compare_specialists)",
        },
        "benchmark_suite": {
            "type": "string",
            "description": "Specific benchmark suite to use",
        },
        "test_cases": {
            "type": "integer",
            "minimum": 1,
            "description": "Number of test cases to run",
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "description": "Maximum number of results",
        },
        "metric": {"type": "string", "description": "Specific metric to compare"},
    },
    "required": ["action"],
}


def evaluation_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handler for evaluation MCP tool.

    Args:
        args: Tool arguments including action and parameters

    Returns:
        Tool execution result
    """
    try:
        tool = EvaluationTool()
        action = args.get("action")

        if action == "run_evaluation":
            specialist_name = args.get("specialist_name")
            if not specialist_name:
                return {
                    "error": "Missing required field: specialist_name",
                    "message": "Field 'specialist_name' is required for run_evaluation action",
                }

            return tool.run_evaluation(
                specialist_name=specialist_name,
                benchmark_suite=args.get("benchmark_suite"),
                test_cases=args.get("test_cases"),
            )

        if action == "get_history":
            return tool.get_evaluation_history(
                specialist_name=args.get("specialist_name"), limit=args.get("limit", 50)
            )

        if action == "get_specialists":
            return tool.get_available_specialists()

        if action == "get_metrics":
            return tool.get_evaluation_metrics()

        if action == "compare_specialists":
            specialist_names = args.get("specialist_names")
            if not specialist_names:
                return {
                    "error": "Missing required field: specialist_names",
                    "message": "Field 'specialist_names' is required for compare_specialists action",
                }

            return tool.compare_specialists(
                specialist_names=specialist_names, metric=args.get("metric")
            )

        if action == "get_summary":
            return tool.get_evaluation_summary()

        return {
            "error": f"Unknown action: {action}",
            "message": "Invalid action specified",
        }

    except Exception as e:
        logger.error(f"Error in evaluation handler: {e}")
        return {"error": str(e), "message": "Evaluation operation failed"}
