"""Tests for training pipeline module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from tool_router.training.data_extraction import ExtractedPattern, PatternCategory
from tool_router.training.training_pipeline import (
    DEFAULT_TRAINING_SOURCES,
    TrainingPipeline,
)


class TestTrainingPipeline:
    """Test cases for TrainingPipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "knowledge.json"
        self.pipeline = TrainingPipeline(self.db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test pipeline initialization."""
        assert self.pipeline.knowledge_base is not None
        assert self.pipeline.extractor is not None
        assert self.pipeline.indexer is not None
        assert self.pipeline.min_confidence == 0.7
        assert self.pipeline.batch_size == 50
        assert self.pipeline.evaluation_interval == 100
        assert isinstance(self.pipeline.training_stats, dict)
        assert "patterns_extracted" in self.pipeline.training_stats
        assert "patterns_validated" in self.pipeline.training_stats
        assert "patterns_added" in self.pipeline.training_stats

    def test_initialization_without_path(self):
        """Test pipeline initialization without path."""
        pipeline = TrainingPipeline()

        assert pipeline.knowledge_base is not None
        assert pipeline.extractor is not None
        assert pipeline.indexer is not None

    def test_run_training_pipeline_success(self):
        """Test successful training pipeline execution."""
        data_sources = [
            {"url": "https://example.com/react", "type": "web_documentation"},
            {"url": "https://example.com/vue", "type": "web_documentation"},
        ]

        with (
            patch.object(self.pipeline, "_extract_patterns") as mock_extract,
            patch.object(self.pipeline, "_validate_patterns") as mock_validate,
            patch.object(self.pipeline, "_populate_knowledge_base") as mock_populate,
            patch.object(self.pipeline, "_build_indexes") as mock_indexes,
            patch.object(self.pipeline, "_train_specialists") as mock_train,
            patch.object(self.pipeline, "_evaluate_training") as mock_evaluate,
        ):

            # Mock successful phase results
            mock_extract.return_value = [
                ExtractedPattern(
                    category=PatternCategory.REACT_PATTERN,
                    title="React Pattern",
                    description="Test React pattern",
                    confidence_score=0.8,
                )
            ]
            mock_validate.return_value = mock_extract.return_value
            mock_populate.return_value = ["pattern-1", "pattern-2"]
            mock_train.return_value = {"react_pattern": {"patterns_count": 5}}
            mock_evaluate.return_value = {"quality_metrics": {"total_patterns": 10}}

            result = self.pipeline.run_training_pipeline(data_sources)

            assert result["patterns_extracted"] == 1
            assert result["patterns_validated"] == 1
            assert result["patterns_added"] == 2
            assert result["training_runs"] == 1
            assert "training_results" in result
            assert "evaluation_results" in result
            assert "last_training" in result

    def test_run_training_pipeline_with_errors(self):
        """Test training pipeline with errors."""
        data_sources = [
            {"url": "https://example.com/error", "type": "web_documentation"}
        ]

        with patch.object(self.pipeline, "_extract_patterns") as mock_extract:
            mock_extract.side_effect = Exception("Extraction failed")

            result = self.pipeline.run_training_pipeline(data_sources)

            assert len(result["errors"]) > 0
            assert "Extraction failed" in result["errors"][0]

    def test_extract_patterns(self):
        """Test pattern extraction from data sources."""
        data_sources = [
            {"url": "https://example.com/react", "type": "web_documentation"},
            {"url": "https://github.com/user/repo", "type": "github_repository"},
        ]

        with patch.object(
            self.pipeline.extractor, "extract_from_multiple_sources"
        ) as mock_extract:
            mock_extract.return_value = [
                ExtractedPattern(
                    category=PatternCategory.REACT_PATTERN,
                    title="React Hook",
                    description="Test hook",
                    confidence_score=0.9,
                )
            ]

            patterns = self.pipeline._extract_patterns(data_sources)

            assert len(patterns) == 1
            assert patterns[0].category == PatternCategory.REACT_PATTERN
            assert mock_extract.call_count == 2

    def test_extract_patterns_with_error(self):
        """Test pattern extraction with error handling."""
        data_sources = [
            {"url": "https://example.com/good", "type": "web_documentation"},
            {"url": "https://example.com/bad", "type": "web_documentation"},
        ]

        with patch.object(
            self.pipeline.extractor, "extract_from_multiple_sources"
        ) as mock_extract:
            mock_extract.side_effect = [
                [
                    ExtractedPattern(
                        category=PatternCategory.UI_COMPONENT,
                        title="UI",
                        description="Test",
                        confidence_score=0.8,
                    )
                ],
                Exception("Network error"),
            ]

            patterns = self.pipeline._extract_patterns(data_sources)

            assert len(patterns) == 1  # Only successful extraction
            assert len(self.pipeline.training_stats["errors"]) == 1
            assert "Network error" in self.pipeline.training_stats["errors"][0]

    def test_validate_patterns(self):
        """Test pattern validation."""
        patterns = [
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="React Hook",
                description="Test hook",
                code_example="useState(0)",
                confidence_score=0.8,
            ),
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="Another Hook",
                description="Another test",
                code_example="useEffect(() => {})",
                confidence_score=0.6,  # Below min_confidence
            ),
            ExtractedPattern(
                category=PatternCategory.UI_COMPONENT,
                title="UI Component",
                description="",  # Missing description
                confidence_score=0.9,
            ),
        ]

        validated = self.pipeline._validate_patterns(patterns)

        # Should only validate patterns with sufficient confidence and required fields
        assert len(validated) == 1
        assert validated[0].title == "React Hook"

    def test_validate_pattern_by_category_react(self):
        """Test React pattern validation."""
        # React pattern with code example - should pass
        pattern_with_code = ExtractedPattern(
            category=PatternCategory.REACT_PATTERN,
            title="React Hook",
            description="Test hook",
            code_example="useState(0)",
        )

        assert self.pipeline._validate_pattern_by_category(pattern_with_code) is True

        # React pattern without code example - should fail
        pattern_without_code = ExtractedPattern(
            category=PatternCategory.REACT_PATTERN,
            title="React Hook",
            description="Test hook",
        )

        assert (
            self.pipeline._validate_pattern_by_category(pattern_without_code) is False
        )

    def test_validate_pattern_by_category_accessibility(self):
        """Test accessibility pattern validation."""
        # Accessibility pattern with WCAG keywords - should pass
        pattern_with_wcag = ExtractedPattern(
            category=PatternCategory.ACCESSIBILITY,
            title="WCAG Guidelines",
            description="Following WCAG 2.1 standards for accessibility",
        )

        assert self.pipeline._validate_pattern_by_category(pattern_with_wcag) is True

        # Accessibility pattern without accessibility keywords - should fail
        pattern_without_keywords = ExtractedPattern(
            category=PatternCategory.ACCESSIBILITY,
            title="Random Pattern",
            description="Just a random pattern",
        )

        assert (
            self.pipeline._validate_pattern_by_category(pattern_without_keywords)
            is False
        )

    def test_validate_pattern_by_category_prompt_engineering(self):
        """Test prompt engineering pattern validation."""
        # Prompt engineering pattern with CoT keywords - should pass
        pattern_with_cot = ExtractedPattern(
            category=PatternCategory.PROMPT_ENGINEERING,
            title="Chain of Thought",
            description="Using chain-of-thought reasoning for better responses",
        )

        assert self.pipeline._validate_pattern_by_category(pattern_with_cot) is True

        # Prompt engineering pattern without prompt keywords - should fail
        pattern_without_keywords = ExtractedPattern(
            category=PatternCategory.PROMPT_ENGINEERING,
            title="Generic Pattern",
            description="Just a generic pattern",
        )

        assert (
            self.pipeline._validate_pattern_by_category(pattern_without_keywords)
            is False
        )

    def test_is_duplicate_pattern(self):
        """Test duplicate pattern detection."""
        existing_patterns = [
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="React Hook",
                description="Test hook for React",
            ),
            ExtractedPattern(
                category=PatternCategory.UI_COMPONENT,
                title="Button Component",
                description="Reusable button component",
            ),
        ]

        # Same title - should be duplicate
        same_title = ExtractedPattern(
            category=PatternCategory.REACT_PATTERN,
            title="React Hook",
            description="Different description",
        )

        assert (
            self.pipeline._is_duplicate_pattern(same_title, existing_patterns) is True
        )

        # Similar description - should be duplicate
        similar_desc = ExtractedPattern(
            category=PatternCategory.UI_COMPONENT,
            title="Button",
            description="Reusable button component",
        )

        assert (
            self.pipeline._is_duplicate_pattern(similar_desc, existing_patterns) is True
        )

        # Different pattern - should not be duplicate
        different = ExtractedPattern(
            category=PatternCategory.ACCESSIBILITY,
            title="ARIA Label",
            description="Accessibility label pattern",
        )

        assert (
            self.pipeline._is_duplicate_pattern(different, existing_patterns) is False
        )

    def test_text_similarity(self):
        """Test text similarity calculation."""
        # Identical text
        assert self.pipeline._text_similarity("hello world", "hello world") == 1.0

        # Completely different text
        assert self.pipeline._text_similarity("hello", "world") == 0.0

        # Some overlap
        similarity = self.pipeline._text_similarity(
            "hello world test", "hello universe test"
        )
        # Common words: hello, test = 2/4 = 0.5
        assert abs(similarity - 0.5) < 0.01

    def test_populate_knowledge_base(self):
        """Test populating knowledge base with patterns."""
        patterns = [
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="React Hook",
                description="Test hook",
                confidence_score=0.8,
            ),
            ExtractedPattern(
                category=PatternCategory.UI_COMPONENT,
                title="Button Component",
                description="Test button",
                confidence_score=0.9,
            ),
        ]

        with patch.object(self.pipeline.knowledge_base, "add_pattern") as mock_add:
            mock_add.side_effect = ["pattern-1", "pattern-2"]

            added_ids = self.pipeline._populate_knowledge_base(patterns)

            assert len(added_ids) == 2
            assert added_ids == ["pattern-1", "pattern-2"]
            assert mock_add.call_count == 2

    def test_populate_knowledge_base_with_error(self):
        """Test populating knowledge base with error."""
        patterns = [
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="React Hook",
                description="Test hook",
                confidence_score=0.8,
            )
        ]

        with patch.object(self.pipeline.knowledge_base, "add_pattern") as mock_add:
            mock_add.side_effect = Exception("Failed to add pattern")

            added_ids = self.pipeline._populate_knowledge_base(patterns)

            assert len(added_ids) == 0
            assert len(self.pipeline.training_stats["errors"]) == 1
            assert "Failed to add pattern" in self.pipeline.training_stats["errors"][0]

    def test_build_indexes(self):
        """Test building knowledge indexes."""
        with patch.object(self.pipeline.indexer, "_build_indexes") as mock_build:
            self.pipeline._build_indexes()

            mock_build.assert_called_once()

    def test_build_indexes_with_error(self):
        """Test building indexes with error."""
        with patch.object(self.pipeline.indexer, "_build_indexes") as mock_build:
            mock_build.side_effect = Exception("Index build failed")

            self.pipeline._build_indexes()

            assert len(self.pipeline.training_stats["errors"]) == 1
            assert "Index build failed" in self.pipeline.training_stats["errors"][0]

    def test_train_specialists(self):
        """Test training specialist agents."""
        with (
            patch.object(self.pipeline.knowledge_base, "get_statistics") as mock_stats,
            patch.object(
                self.pipeline.knowledge_base, "get_patterns_by_category"
            ) as mock_patterns,
        ):

            mock_stats.return_value = {"total_items": 10}
            mock_patterns.return_value = [
                MagicMock(effectiveness_score=0.8, usage_count=5, title="Test Pattern")
                for _ in range(3)
            ]

            results = self.pipeline._train_specialists()

            assert isinstance(results, dict)
            assert len(results) > 0
            mock_patterns.assert_called()

    def test_evaluate_training(self):
        """Test training evaluation."""
        with (
            patch.object(self.pipeline.knowledge_base, "get_statistics") as mock_stats,
            patch.object(
                self.pipeline.knowledge_base, "get_patterns_by_category"
            ) as mock_patterns,
        ):

            mock_stats.return_value = {"total_items": 10, "average_effectiveness": 0.75}
            mock_patterns.return_value = [
                MagicMock(
                    confidence_score=0.8,
                    effectiveness_score=0.9,
                    category=PatternCategory.REACT_PATTERN,
                )
                for _ in range(5)
            ]

            results = self.pipeline._evaluate_training()

            assert "knowledge_base" in results
            assert "quality_metrics" in results
            assert "coverage" in results
            assert results["quality_metrics"]["total_patterns"] == 5
            assert results["quality_metrics"]["avg_confidence"] == 0.8
            assert results["quality_metrics"]["avg_effectiveness"] == 0.9

    def test_run_continuous_learning(self):
        """Test continuous learning with new data."""
        new_sources = [{"url": "https://example.com/new", "type": "web_documentation"}]

        with (
            patch.object(self.pipeline, "_extract_patterns") as mock_extract,
            patch.object(self.pipeline, "_validate_patterns") as mock_validate,
            patch.object(self.pipeline, "_populate_knowledge_base") as mock_populate,
            patch.object(self.pipeline, "_build_indexes") as mock_indexes,
        ):

            mock_extract.return_value = [
                ExtractedPattern(
                    category=PatternCategory.REACT_PATTERN,
                    title="New Pattern",
                    description="New test pattern",
                    confidence_score=0.8,
                )
            ]
            mock_validate.return_value = mock_extract.return_value
            mock_populate.return_value = ["new-pattern-1"]

            result = self.pipeline.run_continuous_learning(new_sources)

            assert result["patterns_extracted"] > 0
            assert result["patterns_validated"] > 0
            assert result["patterns_added"] > 0
            assert "last_training" in result

    def test_get_training_report(self):
        """Test generating training report."""
        with (
            patch.object(self.pipeline.knowledge_base, "get_statistics") as mock_stats,
            patch.object(
                self.pipeline, "_generate_recommendations"
            ) as mock_recommendations,
        ):

            mock_stats.return_value = {
                "total_items": 10,
                "average_effectiveness": 0.8,
                "by_category": {"react_pattern": 5, "ui_component": 3},
                "most_used": [],
            }
            mock_recommendations.return_value = ["Add more patterns", "Improve quality"]

            report = self.pipeline.get_training_report()

            assert "training_statistics" in report
            assert "knowledge_base_stats" in report
            assert "index_stats" in report
            assert "recommendations" in report
            assert len(report["recommendations"]) == 2

    def test_generate_recommendations(self):
        """Test generating training recommendations."""
        # Mock knowledge base stats
        with patch.object(self.pipeline.knowledge_base, "get_statistics") as mock_stats:
            mock_stats.return_value = {
                "average_effectiveness": 0.6,  # Below threshold
                "by_category": {
                    "react_pattern": 5,
                    "ui_component": 2,
                },  # Missing some categories
                "most_used": [],  # No usage
            }

            recommendations = self.pipeline._generate_recommendations()

            assert isinstance(recommendations, list)
            assert len(recommendations) > 0
            # Should recommend adding more patterns for missing categories
            assert any("add more" in rec.lower() for rec in recommendations)
            # Should recommend focusing on quality
            assert any("quality" in rec.lower() for rec in recommendations)

    def test_export_training_data(self):
        """Test exporting training data."""
        export_path = Path(self.temp_dir) / "export.json"

        with (
            patch.object(
                self.pipeline.knowledge_base, "export_knowledge_base"
            ) as mock_export,
            patch.object(self.pipeline, "get_training_report") as mock_report,
        ):

            mock_export.return_value = None
            mock_report.return_value = {"test": "report"}

            self.pipeline.export_training_data(export_path)

            assert export_path.exists()
            mock_export.assert_called_once()
            mock_report.assert_called_once()

    def test_import_training_data(self):
        """Test importing training data."""
        # Create test import data
        import_data = {
            "training_statistics": {
                "patterns_extracted": 10,
                "patterns_validated": 8,
                "patterns_added": 6,
            },
            "knowledge_base_export": "kb_export.json",
        }

        import_path = Path(self.temp_dir) / "import.json"
        with import_path.open("w") as f:
            json.dump(import_data, f)

        # Create mock knowledge base export file
        kb_export_path = Path(self.temp_dir) / "kb_export.json"
        kb_export_path.write_text("{}")

        with patch.object(
            self.pipeline.knowledge_base, "import_knowledge"
        ) as mock_import:
            mock_import.return_value = 5

            result = self.pipeline.import_training_data(import_path)

            assert result["training_statistics"]["patterns_extracted"] == 10
            assert self.pipeline.training_stats["patterns_extracted"] == 10
            mock_import.assert_called_once_with(kb_export_path)

    def test_text_similarity_edge_cases(self):
        """Test text similarity edge cases."""
        # Empty strings
        assert self.pipeline._text_similarity("", "") == 0.0
        assert self.pipeline._text_similarity("hello", "") == 0.0
        assert self.pipeline._text_similarity("", "world") == 0.0

        # Single word
        assert self.pipeline._text_similarity("hello", "hello") == 1.0
        assert self.pipeline._text_similarity("hello", "world") == 0.0

    def test_validate_patterns_empty_list(self):
        """Test validating empty pattern list."""
        result = self.pipeline._validate_patterns([])

        assert result == []

    def test_validate_patterns_all_invalid(self):
        """Test validating all invalid patterns."""
        patterns = [
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="",  # Empty title
                description="Test",
                confidence_score=0.8,
            ),
            ExtractedPattern(
                category=PatternCategory.UI_COMPONENT,
                title="Test",
                description="",  # Empty description
                confidence_score=0.8,
            ),
            ExtractedPattern(
                category=PatternCategory.ACCESSIBILITY,
                title="Test",
                description="Test",
                confidence_score=0.5,  # Below threshold
            ),
        ]

        result = self.pipeline._validate_patterns(patterns)

        assert result == []


class TestTrainingPipelineIntegration:
    """Integration tests for training pipeline."""

    def test_end_to_end_training_workflow(self):
        """Test end-to-end training workflow."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "knowledge.json"

        try:
            pipeline = TrainingPipeline(db_path)

            # Mock all external dependencies
            with (
                patch.object(pipeline, "_extract_patterns") as mock_extract,
                patch.object(pipeline, "_validate_patterns") as mock_validate,
                patch.object(pipeline, "_populate_knowledge_base") as mock_populate,
                patch.object(pipeline, "_build_indexes") as mock_indexes,
                patch.object(pipeline, "_train_specialists") as mock_train,
                patch.object(pipeline, "_evaluate_training") as mock_evaluate,
            ):

                # Mock successful phase results
                mock_extract.return_value = [
                    ExtractedPattern(
                        category=PatternCategory.REACT_PATTERN,
                        title="React Hook",
                        description="Test hook",
                        code_example="useState(0)",
                        confidence_score=0.8,
                    ),
                    ExtractedPattern(
                        category=PatternCategory.UI_COMPONENT,
                        title="Button Component",
                        description="Test button",
                        confidence_score=0.9,
                    ),
                ]
                mock_validate.return_value = mock_extract.return_value
                mock_populate.return_value = ["pattern-1", "pattern-2"]
                mock_train.return_value = {
                    "react_pattern": {"patterns_count": 1, "avg_effectiveness": 0.8},
                    "ui_component": {"patterns_count": 1, "avg_effectiveness": 0.9},
                }
                mock_evaluate.return_value = {
                    "quality_metrics": {"total_patterns": 2, "avg_confidence": 0.85},
                    "coverage": {"categories_covered": 2, "total_categories": 8},
                }

                # Run pipeline
                data_sources = [
                    {"url": "https://example.com/react", "type": "web_documentation"},
                    {"url": "https://example.com/ui", "type": "web_documentation"},
                ]

                result = pipeline.run_training_pipeline(data_sources)

                # Verify results
                assert result["patterns_extracted"] == 2
                assert result["patterns_validated"] == 2
                assert result["patterns_added"] == 2
                assert result["training_runs"] == 1
                assert "training_results" in result
                assert "evaluation_results" in result

                # Verify training results
                training_results = result["training_results"]
                assert "react_pattern" in training_results
                assert "ui_component" in training_results

                # Verify evaluation results
                eval_results = result["evaluation_results"]
                assert eval_results["quality_metrics"]["total_patterns"] == 2
                assert eval_results["coverage"]["categories_covered"] == 2

        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_continuous_learning_integration(self):
        """Test continuous learning integration."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "knowledge.json"

        try:
            pipeline = TrainingPipeline(db_path)

            # Initial training
            with (
                patch.object(pipeline, "_extract_patterns") as mock_extract,
                patch.object(pipeline, "_validate_patterns") as mock_validate,
                patch.object(pipeline, "_populate_knowledge_base") as mock_populate,
            ):

                mock_extract.return_value = [
                    ExtractedPattern(
                        category=PatternCategory.REACT_PATTERN,
                        title="Initial Pattern",
                        description="Initial test",
                        confidence_score=0.8,
                    )
                ]
                mock_validate.return_value = mock_extract.return_value
                mock_populate.return_value = ["initial-pattern"]

                # Run initial training
                initial_sources = [
                    {"url": "https://example.com/initial", "type": "web_documentation"}
                ]
                initial_result = pipeline.run_training_pipeline(initial_sources)

                assert initial_result["patterns_added"] == 1

                # Continuous learning with new data
                new_patterns = [
                    ExtractedPattern(
                        category=PatternCategory.UI_COMPONENT,
                        title="New Pattern",
                        description="New test",
                        confidence_score=0.9,
                    )
                ]
                mock_extract.return_value = new_patterns
                mock_validate.return_value = new_patterns
                mock_populate.return_value = ["new-pattern"]

                new_sources = [
                    {"url": "https://example.com/new", "type": "web_documentation"}
                ]
                continuous_result = pipeline.run_continuous_learning(new_sources)

                # Should have added new patterns to existing count
                assert (
                    continuous_result["patterns_added"]
                    > initial_result["patterns_added"]
                )
                assert (
                    continuous_result["patterns_extracted"]
                    > initial_result["patterns_extracted"]
                )

        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_error_recovery_integration(self):
        """Test error recovery in training pipeline."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "knowledge.json"

        try:
            pipeline = TrainingPipeline(db_path)

            # Mock extraction failure
            with (
                patch.object(pipeline, "_extract_patterns") as mock_extract,
                patch.object(pipeline, "_validate_patterns") as mock_validate,
                patch.object(pipeline, "_populate_knowledge_base") as mock_populate,
            ):

                # First source fails, second succeeds
                mock_extract.side_effect = [
                    Exception("First source failed"),
                    [
                        ExtractedPattern(
                            category=PatternCategory.REACT_PATTERN,
                            title="Working Pattern",
                            description="Test pattern",
                            confidence_score=0.8,
                        )
                    ],
                ]
                mock_validate.return_value = mock_extract.return_value
                mock_populate.return_value = ["working-pattern"]

                # Run pipeline with mixed sources
                data_sources = [
                    {"url": "https://example.com/failing", "type": "web_documentation"},
                    {"url": "https://example.com/working", "type": "web_documentation"},
                ]

                result = pipeline.run_training_pipeline(data_sources)

                # Should have processed the working source despite the failure
                assert result["patterns_extracted"] == 1
                assert result["patterns_validated"] == 1
                assert result["patterns_added"] == 1
                assert len(result["errors"]) == 1
                assert "First source failed" in result["errors"][0]

        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_training_report_integration(self):
        """Test training report generation integration."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "knowledge.json"

        try:
            pipeline = TrainingPipeline(db_path)

            # Mock knowledge base with various statistics
            with patch.object(pipeline.knowledge_base, "get_statistics") as mock_stats:
                mock_stats.return_value = {
                    "total_items": 15,
                    "average_effectiveness": 0.72,
                    "by_category": {
                        "react_pattern": 8,
                        "ui_component": 4,
                        "accessibility": 2,
                        "prompt_engineering": 1,
                    },
                    "most_used": [
                        {"title": "Popular Pattern", "usage_count": 10},
                        {"title": "Unused Pattern", "usage_count": 2},
                    ],
                }

                report = pipeline.get_training_report()

                # Verify report structure
                assert "training_statistics" in report
                assert "knowledge_base_stats" in report
                assert "index_stats" in report
                assert "recommendations" in report

                # Verify recommendations based on stats
                recommendations = report["recommendations"]
                assert isinstance(recommendations, list)
                assert len(recommendations) > 0

                # Should recommend adding patterns for categories with low counts
                category_recommendations = [
                    r for r in recommendations if "add more" in r.lower()
                ]
                assert len(category_recommendations) > 0

                # Should recommend improving quality due to low effectiveness
                quality_recommendations = [
                    r for r in recommendations if "quality" in r.lower()
                ]
                assert len(quality_recommendations) > 0

        finally:
            import shutil

            shutil.rmtree(temp_dir)


class TestDefaultTrainingSources:
    """Test default training sources configuration."""

    def test_default_training_sources_structure(self):
        """Test that default training sources have required structure."""
        assert isinstance(DEFAULT_TRAINING_SOURCES, list)
        assert len(DEFAULT_TRAINING_SOURCES) > 0

        for source in DEFAULT_TRAINING_SOURCES:
            assert "url" in source
            assert "type" in source
            assert "category" in source
            assert source["url"].startswith("http")
            assert source["type"] in ["web_documentation", "github_repository"]

    def test_default_training_sources_categories(self):
        """Test that default sources cover expected categories."""
        categories = {source["category"] for source in DEFAULT_TRAINING_SOURCES}

        expected_categories = [
            "react_patterns",
            "design_systems",
            "accessibility",
            "prompt_engineering",
        ]

        for category in expected_categories:
            assert category in categories, f"Missing category: {category}"

    def test_default_training_sources_urls(self):
        """Test that default source URLs are valid."""
        for source in DEFAULT_TRAINING_SOURCES:
            url = source["url"]
            assert url.startswith("https://")
            assert "." in url  # Domain name present
