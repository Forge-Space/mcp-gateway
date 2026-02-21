"""Unit tests for tool_router/mcp_tools/evaluation_tool.py module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tool_router.mcp_tools.evaluation_tool import EVALUATION_SCHEMA, EvaluationTool, evaluation_handler
from tool_router.training.evaluation import BenchmarkSuite, EvaluationMetric, EvaluationResult, SpecialistEvaluator


class TestEvaluationTool:
    """Test cases for EvaluationTool."""

    def test_initialization(self) -> None:
        """Test EvaluationTool initialization."""
        tool = EvaluationTool()

        # Business logic: tool should initialize with evaluator
        assert tool.evaluator is not None
        assert isinstance(tool.evaluator, SpecialistEvaluator)

    def test_run_evaluation_success(self) -> None:
        """Test successful evaluation run."""
        tool = EvaluationTool()

        # Mock evaluation results
        mock_result1 = MagicMock(spec=EvaluationResult)
        mock_result1.metric = EvaluationMetric.ACCURACY
        mock_result1.value = 0.95
        mock_result1.test_cases = 10
        mock_result1.passed_cases = 10
        mock_result1.details = {"accuracy": 0.95}
        mock_result1.timestamp = "2023-01-01T00:00:00"

        mock_result2 = MagicMock(spec=EvaluationResult)
        mock_result2.metric = EvaluationMetric.PERFORMANCE_SCORE
        mock_result2.value = 0.87
        mock_result2.test_cases = 8
        mock_result2.passed_cases = 7
        mock_result2.details = {"performance": 0.87}
        mock_result2.timestamp = "2023-01-01T00:00:00"

        with patch.object(tool.evaluator, "evaluate_specialist") as mock_evaluate:
            mock_evaluate.return_value = [mock_result1, mock_result2]

            result = tool.run_evaluation(specialist_name="ui_specialist", benchmark_suite=None)

        # Business logic: successful evaluation should return results
        assert "results" in result
        assert len(result["results"]) == 2
        assert result["summary"]["average_score"] == round((0.95 + 0.87) / 2, 2)
        assert result["summary"]["total_test_cases"] == 18  # 10 + 8
        assert result["summary"]["passed_test_cases"] == 17  # 10 + 7
        assert result["summary"]["pass_rate"] == round(17 / 18 * 100, 2)
        assert result["message"] == "Evaluation completed successfully"
        assert "error" not in result

    def test_run_evaluation_no_results(self) -> None:
        """Test evaluation run with no results."""
        tool = EvaluationTool()

        with patch.object(tool.evaluator, "evaluate_specialist") as mock_evaluate:
            mock_evaluate.return_value = []

            result = tool.run_evaluation("ui_specialist")

        # Business logic: no results should return empty evaluation
        assert result["results"] == []
        assert result["summary"]["average_score"] == 0.0
        assert result["summary"]["pass_rate"] == 0.0
        assert result["message"] == "Evaluation completed successfully"

    def test_run_evaluation_with_benchmark_suite(self) -> None:
        """Test evaluation run with custom benchmark suite."""
        tool = EvaluationTool()

        mock_suite = MagicMock(spec=BenchmarkSuite)
        mock_result = MagicMock(spec=EvaluationResult)
        mock_result.value = 0.9
        mock_result.passed_cases = 1
        mock_result.test_cases = 1
        mock_result.metric = EvaluationMetric.ACCURACY
        mock_result.timestamp = "2024-01-01T00:00:00Z"
        mock_result.details = {"test": "data"}

        with patch.object(tool.evaluator, "evaluate_specialist") as mock_evaluate:
            mock_evaluate.return_value = [mock_result]

            result = tool.run_evaluation(specialist_name="ui_specialist", benchmark_suite=mock_suite)

        # Business logic: should use provided benchmark suite
        mock_evaluate.assert_called_once_with(specialist_type="ui_specialist", benchmark_suite=mock_suite)
        assert result["summary"]["average_score"] == 0.9

    def test_run_evaluation_evaluation_error(self) -> None:
        """Test evaluation run with evaluation error."""
        tool = EvaluationTool()

        with patch.object(tool.evaluator, "evaluate_specialist") as mock_evaluate:
            mock_evaluate.side_effect = Exception("Evaluation failed")

            result = tool.run_evaluation("ui_specialist")

        # Business logic: evaluation errors should be caught and reported
        assert "error" in result
        assert "Evaluation failed" in result["error"]
        assert "Failed to run evaluation" in result["message"]

    def test_get_evaluation_history_success(self) -> None:
        """Test getting evaluation history successfully."""
        tool = EvaluationTool()

        mock_result1 = MagicMock()
        mock_result1.specialist_type = "ui_specialist"
        mock_result1.metric.value = "accuracy"
        mock_result1.value = 0.92
        mock_result1.test_cases = 10
        mock_result1.passed_cases = 9
        mock_result1.timestamp = "2024-01-01T00:00:00Z"
        mock_result1.details = {"test": "data"}

        mock_result2 = MagicMock()
        mock_result2.specialist_type = "ui_specialist"
        mock_result2.metric.value = "performance"
        mock_result2.value = 0.87
        mock_result2.test_cases = 10
        mock_result2.passed_cases = 8
        mock_result2.timestamp = "2024-01-01T00:00:00Z"
        mock_result2.details = {"test": "data"}

        with patch.object(tool.evaluator, "get_evaluation_results") as mock_get:
            mock_get.return_value = [mock_result1, mock_result2]

            result = tool.get_evaluation_history(specialist_name="ui_specialist", limit=10)

        assert len(result["results"]) == 2
        assert result["results"][0]["metric"] == "accuracy"
        assert result["results"][1]["metric"] == "performance"
        assert result["total_results"] == 2
        assert result["specialist_filter"] == "ui_specialist"
        assert "Retrieved 2 evaluation results" in result["message"]

        # Verify results are formatted correctly
        formatted_result1 = result["results"][0]
        assert formatted_result1["metric"] == "accuracy"
        assert formatted_result1["value"] == 0.92
        assert formatted_result1["specialist_name"] == "ui_specialist"

    def test_get_evaluation_history_empty(self) -> None:
        """Test evaluation history retrieval with no results."""
        tool = EvaluationTool()

        with patch.object(tool.evaluator, "get_evaluation_results") as mock_get:
            mock_get.return_value = []

            result = tool.get_evaluation_history("ui_specialist")

        assert len(result["results"]) == 0
        assert result["total_results"] == 0
        assert "Retrieved 0 evaluation results" in result["message"]
        assert result["specialist_filter"] == "ui_specialist"

    def test_get_evaluation_history_error(self) -> None:
        """Test evaluation history retrieval with error."""
        tool = EvaluationTool()

        with patch.object(tool.evaluator, "get_evaluation_results") as mock_get:
            mock_get.side_effect = Exception("Database error")

            result = tool.get_evaluation_history("ui_specialist")

        # Business logic: errors should be caught and reported
        assert "error" in result
        assert "Database error" in result["error"]
        assert "Failed to get evaluation history" in result["message"]

    def test_get_available_specialists_success(self) -> None:
        """Test successful available specialists retrieval."""
        tool = EvaluationTool()

        with patch.object(tool.evaluator, "benchmark_suites") as mock_suites:
            # Mock the benchmark suites data structure
            mock_suite1 = MagicMock()
            mock_suite1.description = "UI specialist for user interface patterns"
            mock_suite1.test_cases = ["test1", "test2"]
            mock_suite1.metrics = [MagicMock(value="accuracy"), MagicMock(value="performance")]

            mock_suite2 = MagicMock()
            mock_suite2.description = "Prompt architect for prompt engineering"
            mock_suite2.test_cases = ["test3", "test4"]
            mock_suite2.metrics = [MagicMock(value="creativity"), MagicMock(value="clarity")]

            mock_suites.items.return_value = [("ui_specialist", mock_suite1), ("prompt_architect", mock_suite2)]

            result = tool.get_available_specialists()

        # Business logic: should return list of available specialists
        assert "specialists" in result
        assert len(result["specialists"]) == 2
        assert result["specialists"][0]["name"] == "ui_specialist"
        assert result["specialists"][1]["name"] == "prompt_architect"
        assert result["total_specialists"] == 2
        assert "Available specialists retrieved successfully" in result["message"]

    def test_get_available_specialists_empty(self) -> None:
        """Test available specialists retrieval with no specialists."""
        tool = EvaluationTool()

        with patch.object(tool.evaluator, "benchmark_suites") as mock_suites:
            mock_suites.__contains__ = MagicMock(return_value=False)
            mock_suites.keys = MagicMock(return_value=[])

            result = tool.get_available_specialists()

        # Business logic: empty specialists should return empty list
        assert result["specialists"] == []
        assert result["total_specialists"] == 0

    def test_get_evaluation_metrics_success(self) -> None:
        """Test successful available metrics retrieval."""
        tool = EvaluationTool()

        result = tool.get_evaluation_metrics()

        # Business logic: should return all available metrics
        assert "metrics" in result
        assert len(result["metrics"]) >= 2  # At least accuracy and performance
        assert result["total_metrics"] == len(result["metrics"])
        assert "Evaluation metrics retrieved successfully" in result["message"]

        # Check that expected metrics are present
        metric_names = [metric["name"] for metric in result["metrics"]]
        assert "accuracy" in metric_names
        assert "performance_score" in metric_names

        # Check metric structure
        for metric in result["metrics"]:
            assert "name" in metric
            assert "description" in metric

    def test_get_evaluation_summary_success(self) -> None:
        """Test successful evaluation summary retrieval."""
        tool = EvaluationTool()

        # Mock evaluation results for summary
        mock_result1 = MagicMock()
        mock_result1.specialist_type = "ui_specialist"
        mock_result1.metric.value = "accuracy"
        mock_result1.value = 0.95
        mock_result1.test_cases = 10
        mock_result1.passed_cases = 10
        mock_result1.timestamp = "2024-01-01T00:00:00"
        mock_result1.details = {"test": "data"}

        mock_result2 = MagicMock()
        mock_result2.specialist_type = "ui_specialist"
        mock_result2.metric.value = "performance"
        mock_result2.value = 0.87
        mock_result2.test_cases = 10
        mock_result2.passed_cases = 9
        mock_result2.timestamp = "2024-01-02T00:00:00"
        mock_result2.details = {"test": "data"}

        mock_result3 = MagicMock()
        mock_result3.specialist_type = "ui_specialist"
        mock_result3.metric.value = "efficiency"
        mock_result3.value = 0.65
        mock_result3.test_cases = 10
        mock_result3.passed_cases = 6
        mock_result3.timestamp = "2024-01-03T00:00:00"
        mock_result3.details = {"test": "data"}

        with patch.object(tool.evaluator, "evaluation_history") as mock_history:
            mock_history.__iter__ = MagicMock(return_value=iter([mock_result1, mock_result2, mock_result3]))
            mock_history.__len__ = MagicMock(return_value=3)

            result = tool.get_evaluation_summary()

        # Business logic: should return comprehensive summary
        assert "summary" in result
        summary = result["summary"]
        assert summary["total_evaluations"] == 3
        assert "specialist_performance" in summary
        assert "metric_averages" in summary
        assert "recent_activity" in summary
        assert len(summary["recent_activity"]) == 3
        assert "Evaluation summary retrieved successfully" in result["message"]

    def test_get_evaluation_summary_empty(self) -> None:
        """Test evaluation summary with no evaluations."""
        tool = EvaluationTool()

        with patch.object(tool.evaluator, "evaluation_history") as mock_history:
            mock_history.__iter__ = MagicMock(return_value=iter([]))
            mock_history.__len__ = MagicMock(return_value=0)

            result = tool.get_evaluation_summary()

        # Business logic: empty history should return zero summary
        assert "summary" in result
        summary = result["summary"]
        assert summary["total_evaluations"] == 0
        assert summary["specialist_performance"] == {}
        assert summary["metric_averages"] == {}
        assert summary["recent_activity"] == []
        assert "Evaluation summary retrieved successfully" in result["message"]


class TestEvaluationSchema:
    """Test cases for EVALUATION_SCHEMA."""

    def test_schema_structure(self) -> None:
        """Test that schema has correct structure."""
        assert EVALUATION_SCHEMA["type"] == "object"
        assert "properties" in EVALUATION_SCHEMA
        assert "action" in EVALUATION_SCHEMA["properties"]

        # Business logic: action should be required
        assert "action" in EVALUATION_SCHEMA.get("required", [])

    def test_schema_actions(self) -> None:
        """Test that all valid actions are in schema."""
        actions = EVALUATION_SCHEMA["properties"]["action"]["enum"]
        expected_actions = ["run_evaluation", "get_history", "get_specialists", "get_metrics", "get_summary"]

        # Business logic: all expected actions should be present
        for action in expected_actions:
            assert action in actions


class TestEvaluationHandler:
    """Test cases for evaluation_handler function."""

    def test_handler_run_evaluation_success(self) -> None:
        """Test handler with successful run_evaluation action."""
        args = {"action": "run_evaluation", "specialist_name": "ui_specialist"}

        with patch.object(EvaluationTool, "run_evaluation") as mock_run:
            mock_run.return_value = {"message": "Evaluation completed"}

            result = evaluation_handler(args)

        # Business logic: handler should call appropriate method
        mock_run.assert_called_once_with(specialist_name="ui_specialist", benchmark_suite=None, test_cases=None)
        assert result["message"] == "Evaluation completed"

    def test_handler_run_evaluation_missing_specialist(self) -> None:
        """Test handler with missing specialist_name for run_evaluation."""
        args = {
            "action": "run_evaluation"
            # Missing specialist_name
        }

        result = evaluation_handler(args)

        # Business logic: missing required field should return error
        assert "error" in result
        assert "Missing required field: specialist_name" in result["error"]

    def test_handler_get_evaluation_history_success(self) -> None:
        """Test handler with successful get_history action."""
        args = {"action": "get_history", "specialist_name": "ui_specialist"}

        with patch.object(EvaluationTool, "get_evaluation_history") as mock_get:
            mock_get.return_value = {"results": []}

            result = evaluation_handler(args)

        # Business logic: handler should call get_history with specialist_name
        mock_get.assert_called_once_with(specialist_name="ui_specialist", limit=50)

    def test_handler_get_evaluation_history_with_limit(self) -> None:
        """Test handler with limit parameter for get_history."""
        args = {"action": "get_history", "specialist_name": "ui_specialist", "limit": 5}

        with patch.object(EvaluationTool, "get_evaluation_history") as mock_get:
            mock_get.return_value = {"results": []}

            result = evaluation_handler(args)

        # Business logic: limit should be passed through
        mock_get.assert_called_once_with(specialist_name="ui_specialist", limit=5)

    def test_handler_unknown_action(self) -> None:
        """Test handler with unknown action."""
        args = {"action": "unknown_action"}

        result = evaluation_handler(args)

        # Business logic: unknown action should return error
        assert "error" in result
        assert "Unknown action" in result["error"]
        assert "Invalid action specified" in result["message"]

    def test_handler_get_specialists_success(self) -> None:
        """Test handler with successful get_specialists action."""
        args = {"action": "get_specialists"}

        with patch.object(EvaluationTool, "get_available_specialists") as mock_get:
            mock_get.return_value = {"specialists": []}

            result = evaluation_handler(args)

        # Business logic: handler should call get_available_specialists
        mock_get.assert_called_once()

    def test_handler_get_metrics_success(self) -> None:
        """Test handler with successful get_metrics action."""
        args = {"action": "get_metrics"}

        with patch.object(EvaluationTool, "get_evaluation_metrics") as mock_get:
            mock_get.return_value = {"metrics": []}

            result = evaluation_handler(args)

        # Business logic: handler should call get_evaluation_metrics
        mock_get.assert_called_once()
