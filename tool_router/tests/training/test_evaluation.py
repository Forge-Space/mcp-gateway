"""Tests for training evaluation module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

import pytest

from tool_router.training.evaluation import (
    EvaluationMetric,
    EvaluationResult,
    BenchmarkSuite,
    SpecialistEvaluator,
)
from tool_router.training.knowledge_base import KnowledgeBase, KnowledgeItem, PatternCategory


class TestEvaluationMetric:
    """Test cases for EvaluationMetric enum."""

    def test_metric_values(self):
        """Test that all expected metric values are present."""
        expected_metrics = {
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "response_time",
            "user_satisfaction",
            "code_quality",
            "accessibility_score",
            "performance_score",
            "security_score"
        }
        
        actual_metrics = {metric.value for metric in EvaluationMetric}
        assert actual_metrics == expected_metrics


class TestEvaluationResult:
    """Test cases for EvaluationResult dataclass."""

    def test_evaluation_result_creation_minimal(self):
        """Test creating EvaluationResult with minimal fields."""
        result = EvaluationResult(
            specialist_type="ui_specialist",
            metric=EvaluationMetric.ACCURACY,
            value=0.85
        )
        
        assert result.specialist_type == "ui_specialist"
        assert result.metric == EvaluationMetric.ACCURACY
        assert result.value == 0.85
        assert isinstance(result.timestamp, datetime)
        assert result.test_cases == 0
        assert result.passed_cases == 0
        assert result.details == {}

    def test_evaluation_result_creation_full(self):
        """Test creating EvaluationResult with all fields."""
        test_time = datetime.now(timezone.utc)
        result = EvaluationResult(
            specialist_type="ui_specialist",
            metric=EvaluationMetric.CODE_QUALITY,
            value=0.9,
            timestamp=test_time,
            test_cases=10,
            passed_cases=8,
            details={
                "code_examples": 5,
                "best_practices": 3,
                "test_coverage": 0.8
            }
        )
        
        assert result.specialist_type == "ui_specialist"
        assert result.metric == EvaluationMetric.CODE_QUALITY
        assert result.value == 0.9
        assert result.timestamp == test_time
        assert result.test_cases == 10
        assert result.passed_cases == 8
        assert result.details["code_examples"] == 5

    def test_success_rate_property(self):
        """Test success rate calculation."""
        # No test cases
        result = EvaluationResult(
            specialist_type="test",
            metric=EvaluationMetric.ACCURACY,
            value=0.8,
            test_cases=0,
            passed_cases=0
        )
        assert result.success_rate == 0.0
        
        # Normal case
        result2 = EvaluationResult(
            specialist_type="test",
            metric=EvaluationMetric.ACCURACY,
            value=0.8,
            test_cases=10,
            passed_cases=8
        )
        assert result2.success_rate == 0.8
        
        # All passed
        result3 = EvaluationResult(
            specialist_type="test",
            metric=EvaluationMetric.ACCURACY,
            value=1.0,
            test_cases=5,
            passed_cases=5
        )
        assert result3.success_rate == 1.0


class TestBenchmarkSuite:
    """Test cases for BenchmarkSuite dataclass."""

    def test_benchmark_suite_creation_minimal(self):
        """Test creating BenchmarkSuite with minimal required fields."""
        suite = BenchmarkSuite(
            name="Test Suite",
            description="Test description",
            test_cases=[{"input": "test"}],
            expected_outputs=["test output"],
            metrics=[EvaluationMetric.ACCURACY]
        )
        
        assert suite.name == "Test Suite"
        assert suite.description == "Test description"
        assert len(suite.test_cases) == 1
        assert len(suite.expected_outputs) == 1
        assert len(suite.metrics) == 1
        assert suite.category is None

    def test_benchmark_suite_creation_full(self):
        """Test creating BenchmarkSuite with all fields."""
        suite = BenchmarkSuite(
            name="React UI Suite",
            description="React component evaluation",
            test_cases=[
                {"input": "Create button", "context": {"framework": "react"}},
                {"input": "Create form", "context": {"framework": "react"}}
            ],
            expected_outputs=[
                "Button component",
                "Form component"
            ],
            metrics=[EvaluationMetric.CODE_QUALITY, EvaluationMetric.ACCESSIBILITY_SCORE],
            category=PatternCategory.UI_COMPONENT
        )
        
        assert suite.name == "React UI Suite"
        assert suite.category == PatternCategory.UI_COMPONENT
        assert len(suite.test_cases) == 2
        assert len(suite.metrics) == 2


class TestSpecialistEvaluator:
    """Test cases for SpecialistEvaluator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "knowledge.db"
        self.knowledge_base = KnowledgeBase(self.db_path)
        self.evaluator = SpecialistEvaluator(self.knowledge_base)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test evaluator initialization."""
        assert self.evaluator.knowledge_base == self.knowledge_base
        assert isinstance(self.evaluator.evaluation_history, list)
        assert isinstance(self.evaluator.benchmark_suites, dict)
        assert len(self.evaluator.benchmark_suites) > 0
        
        # Should have benchmark suites for different specialist types
        expected_specialists = ["ui_specialist", "prompt_architect", "router_specialist"]
        for specialist in expected_specialists:
            assert specialist in self.evaluator.benchmark_suites

    def test_create_benchmark_suites(self):
        """Test benchmark suite creation."""
        suites = self.evaluator.benchmark_suites
        
        # Check UI specialist suite
        ui_suite = suites["ui_specialist"]
        assert ui_suite.name == "UI Specialist Benchmark"
        assert ui_suite.category == PatternCategory.UI_COMPONENT
        assert len(ui_suite.test_cases) > 0
        assert len(ui_suite.expected_outputs) > 0
        assert EvaluationMetric.CODE_QUALITY in ui_suite.metrics
        assert EvaluationMetric.ACCESSIBILITY_SCORE in ui_suite.metrics
        
        # Check prompt architect suite
        prompt_suite = suites["prompt_architect"]
        assert prompt_suite.name == "Prompt Architect Benchmark"
        assert prompt_suite.category == PatternCategory.PROMPT_ENGINEERING
        assert EvaluationMetric.ACCURACY in prompt_suite.metrics
        assert EvaluationMetric.PRECISION in prompt_suite.metrics

    def test_evaluate_specialist_success(self):
        """Test successful specialist evaluation."""
        # Add test patterns to knowledge base
        pattern = KnowledgeItem(
            id="test-pattern",
            category=PatternCategory.UI_COMPONENT,
            title="React Button Pattern",
            description="Test button pattern",
            content="Test content",
            code_example="<button>Click</button>",
            tags=["react", "button"],
            confidence_score=0.8,
            usage_count=10
        )
        self.knowledge_base.add_knowledge_item(pattern)
        
        results = self.evaluator.evaluate_specialist("ui_specialist")
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(result, EvaluationResult) for result in results)
        assert all(result.specialist_type == "ui_specialist" for result in results)
        
        # Check that results were added to history
        assert len(self.evaluator.evaluation_history) >= len(results)

    def test_evaluate_specialist_with_custom_suite(self):
        """Test evaluating specialist with custom benchmark suite."""
        custom_suite = BenchmarkSuite(
            name="Custom Suite",
            description="Custom test suite",
            test_cases=[{"input": "test input"}],
            expected_outputs=["test output"],
            metrics=[EvaluationMetric.ACCURACY],
            category=PatternCategory.UI_COMPONENT
        )
        
        results = self.evaluator.evaluate_specialist("ui_specialist", custom_suite)
        
        assert len(results) == 1
        assert results[0].metric == EvaluationMetric.ACCURACY
        assert results[0].specialist_type == "ui_specialist"

    def test_evaluate_specialist_no_suite(self):
        """Test evaluating specialist with no benchmark suite."""
        results = self.evaluator.evaluate_specialist("nonexistent_specialist")
        
        assert results == []

    def test_evaluate_metric_accuracy(self):
        """Test accuracy metric evaluation."""
        # Add test patterns
        pattern = KnowledgeItem(
            id="test-pattern",
            category=PatternCategory.UI_COMPONENT,
            title="Test Pattern",
            description="Test description",
            content="Test content",
            confidence_score=0.8
        )
        self.knowledge_base.add_knowledge_item(pattern)
        
        suite = BenchmarkSuite(
            name="Test Suite",
            description="Test",
            test_cases=[{"input": "test"}],
            expected_outputs=["output"],
            metrics=[EvaluationMetric.ACCURACY],
            category=PatternCategory.UI_COMPONENT
        )
        
        result = self.evaluator._evaluate_metric("ui_specialist", EvaluationMetric.ACCURACY, suite)
        
        assert result.specialist_type == "ui_specialist"
        assert result.metric == EvaluationMetric.ACCURACY
        assert 0.0 <= result.value <= 1.0
        assert result.test_cases == 1
        assert "patterns_used" in result.details

    def test_evaluate_metric_precision(self):
        """Test precision metric evaluation."""
        # Add test patterns with different specificity
        pattern1 = KnowledgeItem(
            id="pattern-1",
            category=PatternCategory.UI_COMPONENT,
            title="Specific Pattern",
            description="Test pattern",
            content="Test content",
            tags=["react", "button", "accessible"],
            metadata={"framework": "react", "type": "button"}
        )
        pattern2 = KnowledgeItem(
            id="pattern-2",
            category=PatternCategory.UI_COMPONENT,
            title="Simple Pattern",
            description="Test pattern",
            content="Test content",
            tags=["react"],
            metadata={}
        )
        
        self.knowledge_base.add_knowledge_item(pattern1)
        self.knowledge_base.add_knowledge_item(pattern2)
        
        suite = BenchmarkSuite(
            name="Test Suite",
            description="Test",
            test_cases=[{"input": "test"}],
            expected_outputs=["output"],
            metrics=[EvaluationMetric.PRECISION],
            category=PatternCategory.UI_COMPONENT
        )
        
        result = self.evaluator._evaluate_metric("ui_specialist", EvaluationMetric.PRECISION, suite)
        
        assert result.metric == EvaluationMetric.PRECISION
        assert 0.0 <= result.value <= 1.0
        assert "avg_specificity" in result.details
        assert "patterns_evaluated" in result.details

    def test_evaluate_metric_recall(self):
        """Test recall metric evaluation."""
        # Add several patterns to test coverage
        for i in range(20):
            pattern = KnowledgeItem(
                id=f"pattern-{i}",
                category=PatternCategory.UI_COMPONENT,
                title=f"Pattern {i}",
                description="Test pattern",
                content="Test content"
            )
            self.knowledge_base.add_knowledge_item(pattern)
        
        suite = BenchmarkSuite(
            name="Test Suite",
            description="Test",
            test_cases=[{"input": "test"}],
            expected_outputs=["output"],
            metrics=[EvaluationMetric.RECALL],
            category=PatternCategory.UI_COMPONENT
        )
        
        result = self.evaluator._evaluate_metric("ui_specialist", EvaluationMetric.RECALL, suite)
        
        assert result.metric == EvaluationMetric.RECALL
        assert 0.0 <= result.value <= 1.0
        assert "coverage" in result.details
        assert "total_patterns" in result.details

    def test_evaluate_metric_f1_score(self):
        """Test F1 score metric evaluation."""
        suite = BenchmarkSuite(
            name="Test Suite",
            description="Test",
            test_cases=[{"input": "test"}],
            expected_outputs=["output"],
            metrics=[EvaluationMetric.F1_SCORE],
            category=PatternCategory.UI_COMPONENT
        )
        
        result = self.evaluator._evaluate_metric("ui_specialist", EvaluationMetric.F1_SCORE, suite)
        
        assert result.metric == EvaluationMetric.F1_SCORE
        assert 0.0 <= result.value <= 1.0
        assert "precision" in result.details
        assert "recall" in result.details
        assert "f1_calculation" in result.details

    def test_evaluate_metric_response_time(self):
        """Test response time metric evaluation."""
        suite = BenchmarkSuite(
            name="Test Suite",
            description="Test",
            test_cases=[{"input": "test"}],
            expected_outputs=["output"],
            metrics=[EvaluationMetric.RESPONSE_TIME],
            category=PatternCategory.UI_COMPONENT
        )
        
        result = self.evaluator._evaluate_metric("ui_specialist", EvaluationMetric.RESPONSE_TIME, suite)
        
        assert result.metric == EvaluationMetric.RESPONSE_TIME
        assert 0.0 <= result.value <= 1.0
        assert "avg_response_time_ms" in result.details
        assert "max_acceptable_time_ms" in result.details
        assert "response_times" in result.details

    def test_evaluate_metric_code_quality(self):
        """Test code quality metric evaluation."""
        # Add patterns with different quality factors
        high_quality = KnowledgeItem(
            id="high-quality",
            category=PatternCategory.UI_COMPONENT,
            title="High Quality Pattern",
            description="Test pattern",
            content="Test content",
            code_example="const Component = () => {}",
            confidence_score=0.9,
            usage_count=50
        )
        low_quality = KnowledgeItem(
            id="low-quality",
            category=PatternCategory.UI_COMPONENT,
            title="Low Quality Pattern",
            description="Test pattern",
            content="Test content",
            code_example=None,
            confidence_score=0.6,
            usage_count=0
        )
        
        self.knowledge_base.add_knowledge_item(high_quality)
        self.knowledge_base.add_knowledge_item(low_quality)
        
        suite = BenchmarkSuite(
            name="Test Suite",
            description="Test",
            test_cases=[{"input": "test"}],
            expected_outputs=["output"],
            metrics=[EvaluationMetric.CODE_QUALITY],
            category=PatternCategory.UI_COMPONENT
        )
        
        result = self.evaluator._evaluate_metric("ui_specialist", EvaluationMetric.CODE_QUALITY, suite)
        
        assert result.metric == EvaluationMetric.CODE_QUALITY
        assert 0.0 <= result.value <= 1.0
        assert "quality_factors" in result.details
        assert "patterns_with_code" in result.details
        assert "best_practice_patterns" in result.details

    def test_evaluate_metric_accessibility_score(self):
        """Test accessibility score metric evaluation."""
        # Add accessibility patterns
        wcag_pattern = KnowledgeItem(
            id="wcag-pattern",
            category=PatternCategory.ACCESSIBILITY,
            title="WCAG Pattern",
            description="WCAG 2.1 compliant pattern",
            content="WCAG guidelines for accessibility"
        )
        aria_pattern = KnowledgeItem(
            id="aria-pattern",
            category=PatternCategory.ACCESSIBILITY,
            title="ARIA Pattern",
            description="ARIA label pattern",
            content="ARIA labels for screen readers"
        )
        
        self.knowledge_base.add_knowledge_item(wcag_pattern)
        self.knowledge_base.add_knowledge_item(aria_pattern)
        
        suite = BenchmarkSuite(
            name="Test Suite",
            description="Test",
            test_cases=[{"input": "test"}],
            expected_outputs=["output"],
            metrics=[EvaluationMetric.ACCESSIBILITY_SCORE],
            category=PatternCategory.UI_COMPONENT
        )
        
        result = self.evaluator._evaluate_metric("ui_specialist", EvaluationMetric.ACCESSIBILITY_SCORE, suite)
        
        assert result.metric == EvaluationMetric.ACCESSIBILITY_SCORE
        assert 0.0 <= result.value <= 1.0
        assert "wcag_coverage" in result.details
        assert "aria_usage" in result.details
        assert "semantic_html" in result.details
        assert "accessibility_patterns" in result.details

    def test_evaluate_metric_default(self):
        """Test default metric evaluation."""
        suite = BenchmarkSuite(
            name="Test Suite",
            description="Test",
            test_cases=[{"input": "test"}],
            expected_outputs=["output"],
            metrics=[EvaluationMetric.USER_SATISFACTION],  # Not specifically handled
            category=PatternCategory.UI_COMPONENT
        )
        
        result = self.evaluator._evaluate_metric("ui_specialist", EvaluationMetric.USER_SATISFACTION, suite)
        
        assert result.metric == EvaluationMetric.USER_SATISFACTION
        assert result.value == 0.8  # Default score
        assert result.test_cases == 1
        assert result.passed_cases == 0  # 80% of 1 = 0.8, int() = 0
        assert result.details["evaluation_method"] == "default"

    def test_get_evaluation_summary_all(self):
        """Test getting evaluation summary for all specialists."""
        # Add some evaluation results
        result1 = EvaluationResult(
            specialist_type="ui_specialist",
            metric=EvaluationMetric.ACCURACY,
            value=0.8,
            test_cases=10,
            passed_cases=8
        )
        result2 = EvaluationResult(
            specialist_type="prompt_architect",
            metric=EvaluationMetric.PRECISION,
            value=0.9,
            test_cases=5,
            passed_cases=5
        )
        
        self.evaluator.evaluation_history.extend([result1, result2])
        
        summary = self.evaluator.get_evaluation_summary()
        
        assert "ui_specialist" in summary
        assert "prompt_architect" in summary
        assert summary["ui_specialist"]["accuracy"]["latest_value"] == 0.8
        assert summary["prompt_architect"]["precision"]["latest_value"] == 0.9
        assert summary["ui_specialist"]["overall_score"] == 0.8
        assert summary["prompt_architect"]["overall_score"] == 0.9

    def test_get_evaluation_summary_specialist(self):
        """Test getting evaluation summary for specific specialist."""
        # Add evaluation results for multiple specialists
        result1 = EvaluationResult(
            specialist_type="ui_specialist",
            metric=EvaluationMetric.ACCURACY,
            value=0.8,
            test_cases=10,
            passed_cases=8
        )
        result2 = EvaluationResult(
            specialist_type="prompt_architect",
            metric=EvaluationMetric.PRECISION,
            value=0.9,
            test_cases=5,
            passed_cases=5
        )
        
        self.evaluator.evaluation_history.extend([result1, result2])
        
        summary = self.evaluator.get_evaluation_summary("ui_specialist")
        
        assert "ui_specialist" in summary
        assert "prompt_architect" not in summary
        assert summary["ui_specialist"]["accuracy"]["latest_value"] == 0.8

    def test_get_evaluation_summary_no_results(self):
        """Test getting evaluation summary with no results."""
        summary = self.evaluator.get_evaluation_summary()
        
        assert "error" in summary
        assert "No evaluation results found" in summary["error"]

    def test_compare_specialists(self):
        """Test comparing multiple specialists."""
        # Add evaluation results
        results = [
            EvaluationResult(
                specialist_type="ui_specialist",
                metric=EvaluationMetric.ACCURACY,
                value=0.8,
                test_cases=10,
                passed_cases=8
            ),
            EvaluationResult(
                specialist_type="ui_specialist",
                metric=EvaluationMetric.CODE_QUALITY,
                value=0.9,
                test_cases=10,
                passed_cases=9
            ),
            EvaluationResult(
                specialist_type="prompt_architect",
                metric=EvaluationMetric.ACCURACY,
                value=0.7,
                test_cases=5,
                passed_cases=4
            ),
            EvaluationResult(
                specialist_type="prompt_architect",
                metric=EvaluationMetric.PRECISION,
                value=0.8,
                test_cases=5,
                passed_cases=4
            )
        ]
        
        self.evaluator.evaluation_history.extend(results)
        
        comparison = self.evaluator.compare_specialists(["ui_specialist", "prompt_architect"])
        
        assert "rankings" in comparison
        assert "comparison_data" in comparison
        assert "evaluation_timestamp" in comparison
        
        # Should be ranked by overall score (ui_specialist: 0.85, prompt_architect: 0.75)
        rankings = comparison["rankings"]
        assert len(rankings) == 2
        assert rankings[0][0] == "ui_specialist"  # Higher score
        assert rankings[1][0] == "prompt_architect"
        assert rankings[0][1]["overall_score"] > rankings[1][1]["overall_score"]

    def test_generate_improvement_recommendations(self):
        """Test generating improvement recommendations."""
        # Add evaluation results with low scores
        results = [
            EvaluationResult(
                specialist_type="ui_specialist",
                metric=EvaluationMetric.ACCURACY,
                value=0.4,  # Low score
                test_cases=10,
                passed_cases=4
            ),
            EvaluationResult(
                specialist_type="ui_specialist",
                metric=EvaluationMetric.CODE_QUALITY,
                value=0.6,  # Moderate score
                test_cases=10,
                passed_cases=6
            ),
            EvaluationResult(
                specialist_type="ui_specialist",
                metric=EvaluationMetric.ACCESSIBILITY_SCORE,
                value=0.9,  # High score
                test_cases=10,
                passed_cases=9
            )
        ]
        
        self.evaluator.evaluation_history.extend(results)
        
        recommendations = self.evaluator.generate_improvement_recommendations("ui_specialist")
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should recommend improvements for low scores
        rec_text = " ".join(recommendations).lower()
        assert "accuracy" in rec_text  # Low score recommendation
        assert "code_quality" in rec_text  # Moderate score recommendation
        # Should not recommend for high score
        assert "accessibility_score" not in rec_text

    def test_generate_improvement_recommendations_no_data(self):
        """Test generating recommendations with no evaluation data."""
        recommendations = self.evaluator.generate_improvement_recommendations("nonexistent")
        
        assert len(recommendations) == 1
        assert "No evaluation data available" in recommendations[0]

    def test_generate_improvement_recommendations_good_performance(self):
        """Test generating recommendations for good performance."""
        # Add evaluation results with high scores
        results = [
            EvaluationResult(
                specialist_type="ui_specialist",
                metric=EvaluationMetric.ACCURACY,
                value=0.9,
                test_cases=10,
                passed_cases=9
            ),
            EvaluationResult(
                specialist_type="ui_specialist",
                metric=EvaluationMetric.CODE_QUALITY,
                value=0.8,
                test_cases=10,
                passed_cases=8
            )
        ]
        
        self.evaluator.evaluation_history.extend(results)
        
        recommendations = self.evaluator.generate_improvement_recommendations("ui_specialist")
        
        assert len(recommendations) == 1
        assert "Performance is good" in recommendations[0]

    def test_export_evaluation_data(self):
        """Test exporting evaluation data."""
        # Add evaluation results
        results = [
            EvaluationResult(
                specialist_type="ui_specialist",
                metric=EvaluationMetric.ACCURACY,
                value=0.8,
                test_cases=10,
                passed_cases=8,
                details={"test": "data"}
            )
        ]
        
        self.evaluator.evaluation_history.extend(results)
        
        export_path = Path(self.temp_dir) / "evaluation_export.json"
        self.evaluator.export_evaluation_data(export_path)
        
        assert export_path.exists()
        
        # Verify exported content
        with export_path.open("r") as f:
            exported_data = json.load(f)
        
        assert "evaluation_history" in exported_data
        assert "benchmark_suites" in exported_data
        assert "export_timestamp" in exported_data
        
        assert len(exported_data["evaluation_history"]) == 1
        exported_result = exported_data["evaluation_history"][0]
        assert exported_result["specialist_type"] == "ui_specialist"
        assert exported_result["metric"] == "accuracy"
        assert exported_result["value"] == 0.8

    def test_export_evaluation_data_empty(self):
        """Test exporting evaluation data with no results."""
        export_path = Path(self.temp_dir) / "empty_export.json"
        self.evaluator.export_evaluation_data(export_path)
        
        assert export_path.exists()
        
        with export_path.open("r") as f:
            exported_data = json.load(f)
        
        assert exported_data["evaluation_history"] == []
        assert "benchmark_suites" in exported_data


class TestSpecialistEvaluatorIntegration:
    """Integration tests for specialist evaluator."""

    def test_end_to_end_evaluation_workflow(self):
        """Test end-to-end evaluation workflow."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "knowledge.db"
        
        try:
            # Create knowledge base with patterns
            kb = KnowledgeBase(db_path)
            
            # Add UI patterns
            ui_patterns = [
                KnowledgeItem(
                    id="ui-1",
                    category=PatternCategory.UI_COMPONENT,
                    title="React Button",
                    description="Accessible button component",
                    content="React button with ARIA labels",
                    code_example="<button aria-label='Click me'>Click</button>",
                    tags=["react", "button", "accessible"],
                    confidence_score=0.9,
                    usage_count=25
                ),
                KnowledgeItem(
                    id="ui-2",
                    category=PatternCategory.UI_COMPONENT,
                    title="React Form",
                    description="Form with validation",
                    content="React form component",
                    code_example="<form><input required /></form>",
                    tags=["react", "form", "validation"],
                    confidence_score=0.8,
                    usage_count=15
                )
            ]
            
            # Add accessibility patterns
            accessibility_patterns = [
                KnowledgeItem(
                    id="a11y-1",
                    category=PatternCategory.ACCESSIBILITY,
                    title="WCAG Guidelines",
                    description="WCAG 2.1 compliance",
                    content="Follow WCAG 2.1 guidelines for accessibility",
                    tags=["wcag", "guidelines", "compliance"]
                ),
                KnowledgeItem(
                    id="a11y-2",
                    category=PatternCategory.ACCESSIBILITY,
                    title="ARIA Labels",
                    description="ARIA label usage",
                    content="Use ARIA labels for screen readers",
                    tags=["aria", "labels", "screen-reader"]
                )
            ]
            
            for pattern in ui_patterns + accessibility_patterns:
                kb.add_knowledge_item(pattern)
            
            # Create evaluator
            evaluator = SpecialistEvaluator(kb)
            
            # Evaluate UI specialist
            ui_results = evaluator.evaluate_specialist("ui_specialist")
            
            assert len(ui_results) > 0
            assert all(result.specialist_type == "ui_specialist" for result in ui_results)
            
            # Verify specific metrics
            accuracy_result = next((r for r in ui_results if r.metric == EvaluationMetric.ACCURACY), None)
            code_quality_result = next((r for r in ui_results if r.metric == EvaluationMetric.CODE_QUALITY), None)
            accessibility_result = next((r for r in ui_results if r.metric == EvaluationMetric.ACCESSIBILITY_SCORE), None)
            
            assert accuracy_result is not None
            assert code_quality_result is not None
            assert accessibility_result is not None
            
            # Should have decent scores due to good patterns
            assert accuracy_result.value > 0.5
            assert code_quality_result.value > 0.5
            assert accessibility_result.value > 0.0  # Should have some accessibility patterns
            
            # Get evaluation summary
            summary = evaluator.get_evaluation_summary("ui_specialist")
            
            assert "ui_specialist" in summary
            assert "overall_score" in summary["ui_specialist"]
            assert summary["ui_specialist"]["metrics_count"] == len(ui_results)
            
            # Generate recommendations
            recommendations = evaluator.generate_improvement_recommendations("ui_specialist")
            
            assert isinstance(recommendations, list)
            
            # Export data
            export_path = Path(temp_dir) / "evaluation_export.json"
            evaluator.export_evaluation_data(export_path)
            
            assert export_path.exists()
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)

    def test_multi_specialist_comparison(self):
        """Test comparing multiple specialists."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "knowledge.db"
        
        try:
            # Create knowledge base with patterns for different categories
            kb = KnowledgeBase(db_path)
            
            # Add patterns for different categories
            patterns = [
                KnowledgeItem(
                    id="ui-1",
                    category=PatternCategory.UI_COMPONENT,
                    title="UI Pattern",
                    description="Test UI pattern",
                    content="UI content",
                    code_example="<div>UI</div>",
                    tags=["ui"],
                    confidence_score=0.8
                ),
                KnowledgeItem(
                    id="prompt-1",
                    category=PatternCategory.PROMPT_ENGINEERING,
                    title="Prompt Pattern",
                    description="Test prompt pattern",
                    content="Prompt content",
                    tags=["prompt"],
                    confidence_score=0.7
                ),
                KnowledgeItem(
                    id="arch-1",
                    category=PatternCategory.ARCHITECTURE,
                    title="Architecture Pattern",
                    description="Test architecture pattern",
                    content="Architecture content",
                    tags=["architecture"],
                    confidence_score=0.6
                )
            ]
            
            for pattern in patterns:
                kb.add_knowledge_item(pattern)
            
            # Create evaluator
            evaluator = SpecialistEvaluator(kb)
            
            # Evaluate all specialists
            specialist_types = ["ui_specialist", "prompt_architect", "router_specialist"]
            all_results = {}
            
            for specialist in specialist_types:
                results = evaluator.evaluate_specialist(specialist)
                all_results[specialist] = results
            
            # Compare specialists
            comparison = evaluator.compare_specialists(specialist_types)
            
            assert "rankings" in comparison
            assert len(comparison["rankings"]) == 3
            
            # Verify comparison structure
            rankings = comparison["rankings"]
            for specialist, data in rankings:
                assert specialist in specialist_types
                assert "overall_score" in data
                assert "metrics" in data
                assert 0.0 <= data["overall_score"] <= 1.0
            
            # Should be ranked by overall score
            scores = [data["overall_score"] for _, data in rankings]
            assert scores == sorted(scores, reverse=True)
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)

    def test_evaluation_error_handling(self):
        """Test evaluation error handling."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "knowledge.db"
        
        try:
            # Create empty knowledge base
            kb = KnowledgeBase(db_path)
            evaluator = SpecialistEvaluator(kb)
            
            # Evaluate with no patterns should still work but return low scores
            results = evaluator.evaluate_specialist("ui_specialist")
            
            assert len(results) > 0
            
            # Accuracy should be 0.0 with no relevant patterns
            accuracy_result = next((r for r in results if r.metric == EvaluationMetric.ACCURACY), None)
            assert accuracy_result is not None
            assert accuracy_result.value == 0.0
            assert "No relevant patterns found" in accuracy_result.details["error"]
            
            # Accessibility should also be 0.0 with no accessibility patterns
            accessibility_result = next((r for r in results if r.metric == EvaluationMetric.ACCESSIBILITY_SCORE), None)
            assert accessibility_result is not None
            assert accessibility_result.value == 0.0
            assert "No accessibility patterns found" in accessibility_result.details["error"]
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)

    def test_evaluation_consistency(self):
        """Test evaluation consistency across multiple runs."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "knowledge.db"
        
        try:
            # Create knowledge base with fixed patterns
            kb = KnowledgeBase(db_path)
            
            pattern = KnowledgeItem(
                id="fixed-pattern",
                category=PatternCategory.UI_COMPONENT,
                title="Fixed Pattern",
                description="Fixed description",
                content="Fixed content",
                code_example="const Component = () => {}",
                tags=["react"],
                confidence_score=0.8,
                usage_count=10
            )
            
            kb.add_knowledge_item(pattern)
            
            evaluator = SpecialistEvaluator(kb)
            
            # Run evaluation multiple times
            results1 = evaluator.evaluate_specialist("ui_specialist")
            results2 = evaluator.evaluate_specialist("ui_specialist")
            
            # Results should be consistent
            assert len(results1) == len(results2)
            
            for result1, result2 in zip(results1, results2):
                assert result1.metric == result2.metric
                assert result1.value == result2.value
                assert result1.test_cases == result2.test_cases
                assert result1.passed_cases == result2.passed_cases
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)