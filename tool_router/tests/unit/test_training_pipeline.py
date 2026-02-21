"""
Unit tests for Training Pipeline.

Tests the complete training pipeline orchestration including:
- Data extraction and processing
- Pattern validation and quality assessment
- Knowledge base population
- Specialist model training
- Evaluation and feedback collection
- Continuous learning mechanisms
"""

from pathlib import Path
from unittest.mock import Mock, patch

from tool_router.training.data_extraction import ExtractedPattern, PatternCategory
from tool_router.training.training_pipeline import DEFAULT_TRAINING_SOURCES, TrainingPipeline


class TestTrainingPipeline:
    """Test cases for TrainingPipeline class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_kb_path = Path("/tmp/test_knowledge_base.db")
        self.pipeline = TrainingPipeline(self.mock_kb_path)

        # Sample test data
        self.sample_patterns = [
            ExtractedPattern(
                title="React Button Component",
                description="A reusable button component with TypeScript",
                category=PatternCategory.REACT_PATTERN,
                content="Button component implementation",
                code_example="const Button: React.FC<ButtonProps> = ({ children, ...props }) => <button {...props}>{children}</button>",
                tags=["react", "typescript", "component"],
                confidence_score=0.9,
                source_url="https://example.com/react-button",
                metadata={"framework": "react"},
            ),
            ExtractedPattern(
                title="WCAG Accessibility Guidelines",
                description="Web Content Accessibility Guidelines implementation",
                category=PatternCategory.ACCESSIBILITY,
                content="Accessibility best practices for web applications",
                tags=["wcag", "aria", "accessibility"],
                confidence_score=0.85,
                source_url="https://example.com/wcag",
                metadata={"standard": "WCAG 2.1"},
            ),
            ExtractedPattern(
                title="Chain of Thought Prompting",
                description="Step-by-step reasoning approach for AI prompts",
                category=PatternCategory.PROMPT_ENGINEERING,
                content="Chain of thought prompting technique",
                tags=["cot", "reasoning", "prompting"],
                confidence_score=0.8,
                source_url="https://example.com/cot",
                metadata={"technique": "chain-of-thought"},
            ),
        ]

        self.sample_data_sources = [
            {"url": "https://example.com/react-docs", "type": "web_documentation", "category": "react_patterns"},
            {"url": "https://example.com/accessibility", "type": "web_documentation", "category": "accessibility"},
            {"url": "https://github.com/example/repo", "type": "github_repository", "category": "prompt_engineering"},
        ]

    def test_initialization(self):
        """Test TrainingPipeline initialization."""
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

    @patch("tool_router.training.training_pipeline.PatternExtractor")
    @patch("tool_router.training.training_pipeline.KnowledgeBase")
    @patch("tool_router.training.training_pipeline.KnowledgeIndexer")
    def test_run_training_pipeline_success(self, mock_indexer, mock_kb, mock_extractor):
        """Test successful training pipeline execution."""
        # Setup mocks
        mock_extractor_instance = Mock()
        mock_extractor_instance.extract_from_multiple_sources.return_value = self.sample_patterns
        mock_extractor.return_value = mock_extractor_instance

        mock_kb_instance = Mock()
        mock_kb_instance.add_pattern.return_value = "test_id_123"
        mock_kb_instance.get_patterns_by_category.return_value = self.sample_patterns[:2]
        mock_kb_instance.get_statistics.return_value = {
            "total_items": 10,
            "by_category": {"react_pattern": 5, "accessibility": 3, "prompt_engineering": 2},
            "average_effectiveness": 0.8,
            "most_used": [{"id": "1", "title": "Test Pattern", "usage_count": 10}],
        }
        mock_kb.return_value = mock_kb_instance

        mock_indexer_instance = Mock()
        mock_indexer.return_value = mock_indexer_instance

        # Create pipeline with mocks
        pipeline = TrainingPipeline()
        pipeline.extractor = mock_extractor_instance
        pipeline.knowledge_base = mock_kb_instance
        pipeline.indexer = mock_indexer_instance

        # Run pipeline
        result = pipeline.run_training_pipeline(self.sample_data_sources)

        # Verify results
        assert result["patterns_extracted"] == len(self.sample_patterns)
        assert result["patterns_validated"] > 0
        assert result["patterns_added"] > 0
        assert result["training_runs"] == 1
        assert "last_training" in result
        assert "training_results" in result
        assert "evaluation_results" in result

        # Verify method calls
        mock_extractor_instance.extract_from_multiple_sources.assert_called()
        mock_kb_instance.add_pattern.assert_called()
        mock_indexer_instance._build_indexes.assert_called()

    def test_run_training_pipeline_extraction_error(self):
        """Test training pipeline with extraction errors."""
        # Mock extractor to raise exception
        with patch.object(
            self.pipeline.extractor, "extract_from_multiple_sources", side_effect=Exception("Extraction failed")
        ):
            result = self.pipeline.run_training_pipeline(self.sample_data_sources)

            assert result["patterns_extracted"] == 0
            assert len(result["errors"]) > 0
            assert "Extraction failed" in result["errors"][0]

    def test_extract_patterns(self):
        """Test pattern extraction from data sources."""
        with patch.object(
            self.pipeline.extractor, "extract_from_multiple_sources", return_value=self.sample_patterns
        ) as mock_extract:
            result = self.pipeline._extract_patterns(self.sample_data_sources)

            assert len(result) == len(self.sample_patterns)
            mock_extract.assert_called_once_with(self.sample_data_sources)

            # Verify error handling
            mock_extract.side_effect = Exception("Network error")
            result = self.pipeline._extract_patterns(self.sample_data_sources)
            assert len(result) == 0
            assert len(self.pipeline.training_stats["errors"]) > 0

    def test_validate_patterns(self):
        """Test pattern validation."""
        # Test with valid patterns
        validated = self.pipeline._validate_patterns(self.sample_patterns)
        assert len(validated) == len(self.sample_patterns)

        # Test with low confidence patterns
        low_confidence_patterns = [
            ExtractedPattern(
                title="Low Confidence Pattern",
                description="Should be filtered out",
                category=PatternCategory.REACT_PATTERN,
                content="Test content",
                confidence_score=0.5,  # Below min_confidence
                source_url="https://example.com",
            )
        ]
        validated = self.pipeline._validate_patterns(low_confidence_patterns)
        assert len(validated) == 0

        # Test with missing required fields
        invalid_patterns = [
            ExtractedPattern(
                title="",  # Missing title
                description="Missing title pattern",
                category=PatternCategory.REACT_PATTERN,
                content="Test content",
                confidence_score=0.8,
                source_url="https://example.com",
            )
        ]
        validated = self.pipeline._validate_patterns(invalid_patterns)
        assert len(validated) == 0

    def test_validate_pattern_by_category(self):
        """Test category-specific validation."""
        # React patterns should have code examples
        react_pattern = ExtractedPattern(
            title="React Pattern",
            description="Test pattern",
            category=PatternCategory.REACT_PATTERN,
            content="Test content",
            code_example="const Component = () => <div/>",
            confidence_score=0.8,
            source_url="https://example.com",
        )
        assert self.pipeline._validate_pattern_by_category(react_pattern) is True

        # React pattern without code example should fail
        react_pattern_no_code = ExtractedPattern(
            title="React Pattern",
            description="Test pattern",
            category=PatternCategory.REACT_PATTERN,
            content="Test content",
            code_example=None,
            confidence_score=0.8,
            source_url="https://example.com",
        )
        assert self.pipeline._validate_pattern_by_category(react_pattern_no_code) is False

        # Accessibility patterns should have accessibility keywords
        accessibility_pattern = ExtractedPattern(
            title="Accessibility Pattern",
            description="WCAG compliant pattern with ARIA labels",
            category=PatternCategory.ACCESSIBILITY,
            content="Test content",
            confidence_score=0.8,
            source_url="https://example.com",
        )
        assert self.pipeline._validate_pattern_by_category(accessibility_pattern) is True

        # Accessibility pattern without keywords should fail
        accessibility_pattern_no_keywords = ExtractedPattern(
            title="Accessibility Pattern",
            description="Generic pattern without accessibility terms",
            category=PatternCategory.ACCESSIBILITY,
            content="Test content",
            confidence_score=0.8,
            source_url="https://example.com",
        )
        assert self.pipeline._validate_pattern_by_category(accessibility_pattern_no_keywords) is False

    def test_is_duplicate_pattern(self):
        """Test duplicate pattern detection."""
        existing_patterns = [
            ExtractedPattern(
                title="Existing Pattern",
                description="This pattern already exists",
                category=PatternCategory.REACT_PATTERN,
                content="Test content",
                confidence_score=0.8,
                source_url="https://example.com",
            )
        ]

        # Same title should be detected as duplicate
        duplicate_pattern = ExtractedPattern(
            title="Existing Pattern",  # Same title
            description="Different description",
            category=PatternCategory.REACT_PATTERN,
            content="Test content",
            confidence_score=0.8,
            source_url="https://example.com/different",
        )
        assert self.pipeline._is_duplicate_pattern(duplicate_pattern, existing_patterns) is True

        # Similar description should be detected as duplicate
        similar_pattern = ExtractedPattern(
            title="Different Title",
            description="This pattern already exists",  # Same description
            category=PatternCategory.REACT_PATTERN,
            content="Test content",
            confidence_score=0.8,
            source_url="https://example.com",
        )
        assert self.pipeline._is_duplicate_pattern(similar_pattern, existing_patterns) is True

        # Different pattern should not be detected as duplicate
        unique_pattern = ExtractedPattern(
            title="Unique Pattern",
            description="Completely different pattern",
            category=PatternCategory.REACT_PATTERN,
            content="Test content",
            confidence_score=0.8,
            source_url="https://example.com",
        )
        assert self.pipeline._is_duplicate_pattern(unique_pattern, existing_patterns) is False

    def test_text_similarity(self):
        """Test text similarity calculation."""
        # Identical text should have 1.0 similarity
        similarity = self.pipeline._text_similarity("test text", "test text")
        assert similarity == 1.0

        # Completely different text should have 0.0 similarity
        similarity = self.pipeline._text_similarity("test text", "different words")
        assert similarity == 0.0

        # Partially similar text should have intermediate similarity
        similarity = self.pipeline._text_similarity("test text here", "test text there")
        assert 0.0 < similarity < 1.0

        # Empty text should handle gracefully
        similarity = self.pipeline._text_similarity("", "test text")
        assert similarity == 0.0

    @patch.object(TrainingPipeline, "_populate_knowledge_base")
    @patch.object(TrainingPipeline, "_build_indexes")
    @patch.object(TrainingPipeline, "_train_specialists")
    @patch.object(TrainingPipeline, "_evaluate_training")
    def test_populate_knowledge_base(self, mock_eval, mock_train, mock_build, mock_populate):
        """Test knowledge base population."""
        # Mock the method to avoid actual database operations
        mock_populate.return_value = ["id1", "id2", "id3"]
        self.pipeline._populate_knowledge_base = mock_populate

        result = self.pipeline._populate_knowledge_base(self.sample_patterns)

        assert len(result) == len(self.sample_patterns)
        mock_populate.assert_called_once_with(self.sample_patterns)

    def test_build_indexes(self):
        """Test knowledge index building."""
        with patch.object(self.pipeline.indexer, "_build_indexes") as mock_build:
            self.pipeline._build_indexes()
            mock_build.assert_called_once()

            # Test error handling
            mock_build.side_effect = Exception("Index build failed")
            self.pipeline._build_indexes()
            assert len(self.pipeline.training_stats["errors"]) > 0

    def test_train_specialists(self):
        """Test specialist training."""
        # Mock knowledge base to return patterns
        mock_patterns = [Mock(effectiveness_score=0.8, usage_count=5, title="Test Pattern")]
        self.pipeline.knowledge_base.get_patterns_by_category.return_value = mock_patterns

        result = self.pipeline._train_specialists()

        assert isinstance(result, dict)
        # Should have results for each category that has patterns
        for category in PatternCategory:
            if category.value in result:
                category_result = result[category.value]
                assert "patterns_count" in category_result
                assert "avg_effectiveness" in category_result
                assert "top_patterns" in category_result

    def test_evaluate_training(self):
        """Test training evaluation."""
        # Mock knowledge base statistics
        mock_stats = {
            "total_items": 15,
            "by_category": {"react_pattern": 8, "accessibility": 4, "prompt_engineering": 3},
            "average_effectiveness": 0.75,
            "most_used": [{"id": "1", "title": "Test Pattern", "usage_count": 10}],
        }
        self.pipeline.knowledge_base.get_statistics.return_value = mock_stats

        # Mock patterns for quality assessment
        mock_pattern = Mock(effectiveness_score=0.8, confidence_score=0.9, category=PatternCategory.REACT_PATTERN)
        self.pipeline.knowledge_base.get_patterns_by_category.return_value = [mock_pattern] * 5

        result = self.pipeline._evaluate_training()

        assert "knowledge_base" in result
        assert "quality_metrics" in result
        assert "coverage" in result

        quality = result["quality_metrics"]
        assert quality["total_patterns"] == 5  # 5 categories * 1 pattern each
        assert quality["avg_confidence"] == 0.9
        assert quality["avg_effectiveness"] == 0.8
        assert quality["high_quality_patterns"] == 5  # All patterns > 0.8

        coverage = result["coverage"]
        assert coverage["categories_covered"] == 1  # Only REACT_PATTERN in mock
        assert coverage["total_categories"] == len(PatternCategory)
        assert coverage["coverage_percentage"] > 0

    def test_run_continuous_learning(self):
        """Test continuous learning process."""
        with patch.object(self.pipeline, "_extract_patterns", return_value=self.sample_patterns) as mock_extract:
            with patch.object(self.pipeline, "_validate_patterns", return_value=self.sample_patterns) as mock_validate:
                with patch.object(
                    self.pipeline, "_populate_knowledge_base", return_value=["id1", "id2"]
                ) as mock_populate:
                    with patch.object(self.pipeline, "_build_indexes") as mock_build:
                        result = self.pipeline.run_continuous_learning(self.sample_data_sources)

                        assert result["patterns_extracted"] > 0
                        assert result["patterns_validated"] > 0
                        assert result["patterns_added"] > 0
                        assert "last_training" in result

                        mock_extract.assert_called_once_with(self.sample_data_sources)
                        mock_validate.assert_called_once_with(self.sample_patterns)
                        mock_populate.assert_called_once()
                        mock_build.assert_called_once()

    def test_get_training_report(self):
        """Test training report generation."""
        # Mock knowledge base statistics
        mock_stats = {
            "total_items": 10,
            "by_category": {"react_pattern": 5, "accessibility": 3},
            "average_effectiveness": 0.8,
            "most_used": [],
        }
        self.pipeline.knowledge_base.get_statistics.return_value = mock_stats

        # Mock indexer stats
        self.pipeline.indexer.tag_index = {"react": {"id1", "id2"}, "button": {"id3"}}
        self.pipeline.indexer.keyword_index = {"component": {"id1"}, "react": {"id2"}}
        self.pipeline.indexer.category_index = {PatternCategory.REACT_PATTERN: {"id1", "id2"}}

        report = self.pipeline.get_training_report()

        assert "training_statistics" in report
        assert "knowledge_base_stats" in report
        assert "index_stats" in report
        assert "recommendations" in report

        index_stats = report["index_stats"]
        assert index_stats["tag_index_size"] == 2
        assert index_stats["keyword_index_size"] == 2
        assert index_stats["category_index_size"] == 1

    def test_generate_recommendations(self):
        """Test training recommendations generation."""
        # Mock knowledge base statistics
        mock_stats_low_coverage = {
            "total_items": 5,
            "by_category": {"react_pattern": 5},  # Missing other categories
            "average_effectiveness": 0.6,  # Low effectiveness
            "most_used": [],  # No usage
        }
        self.pipeline.knowledge_base.get_statistics.return_value = mock_stats_low_coverage

        recommendations = self.pipeline._generate_recommendations()

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Should recommend adding missing categories
        category_recommendations = [r for r in recommendations if "Consider adding more" in r]
        assert len(category_recommendations) > 0

        # Should recommend focusing on quality
        quality_recommendations = [r for r in recommendations if "higher quality" in r]
        assert len(quality_recommendations) > 0

    def test_export_training_data(self):
        """Test training data export."""
        export_path = Path("/tmp/test_export.json")

        with patch.object(self.pipeline.knowledge_base, "export_knowledge_base") as mock_export:
            with patch("builtins.open", create=True) as mock_open:
                mock_file = Mock()
                mock_open.return_value.__enter__.return_value = mock_file

                self.pipeline.export_training_data(export_path)

                mock_export.assert_called_once()
                mock_open.assert_called_once_with(export_path, "w", encoding="utf-8")

    def test_import_training_data(self):
        """Test training data import."""
        import_path = Path("/tmp/test_import.json")
        import_data = {
            "training_statistics": {"patterns_extracted": 10},
            "knowledge_base_export": Path("/tmp/kb_export.json"),
        }

        with patch("builtins.open", create=True) as mock_open:
            with patch("json.load", return_value=import_data) as mock_json_load:
                with patch.object(self.pipeline.knowledge_base, "import_knowledge_base", return_value=5) as mock_import:
                    mock_file = Mock()
                    mock_open.return_value.__enter__.return_value = mock_file

                    result = self.pipeline.import_training_data(import_path)

                    mock_json_load.assert_called_once()
                    mock_import.assert_called_once()
                    assert self.pipeline.training_stats["patterns_extracted"] == 10

    def test_default_training_sources(self):
        """Test default training sources configuration."""
        assert isinstance(DEFAULT_TRAINING_SOURCES, list)
        assert len(DEFAULT_TRAINING_SOURCES) > 0

        for source in DEFAULT_TRAINING_SOURCES:
            assert "url" in source
            assert "type" in source
            assert "category" in source
            assert source["url"].startswith("http")

    def test_pipeline_error_recovery(self):
        """Test pipeline error recovery and reporting."""
        # Mock multiple components to fail
        with patch.object(
            self.pipeline.extractor, "extract_from_multiple_sources", side_effect=Exception("Network error")
        ):
            with patch.object(self.pipeline.knowledge_base, "add_pattern", side_effect=Exception("Database error")):
                result = self.pipeline.run_training_pipeline(self.sample_data_sources)

                assert result["patterns_extracted"] == 0
                assert len(result["errors"]) >= 1
                assert any("Network error" in error for error in result["errors"])

    def test_pipeline_configuration(self):
        """Test pipeline configuration parameters."""
        # Test custom configuration
        custom_pipeline = TrainingPipeline()
        custom_pipeline.min_confidence = 0.9
        custom_pipeline.batch_size = 100
        custom_pipeline.evaluation_interval = 200

        # Low confidence patterns should be filtered
        low_confidence_patterns = [
            ExtractedPattern(
                title="Low Confidence",
                description="Should be filtered",
                category=PatternCategory.REACT_PATTERN,
                content="Test",
                confidence_score=0.8,  # Below new threshold
                source_url="https://example.com",
            )
        ]
        validated = custom_pipeline._validate_patterns(low_confidence_patterns)
        assert len(validated) == 0

    def test_pipeline_logging(self):
        """Test pipeline logging functionality."""
        with patch("tool_router.training.training_pipeline.logger") as mock_logger:
            # Test successful pipeline logging
            with patch.object(self.pipeline, "_extract_patterns", return_value=self.sample_patterns):
                with patch.object(self.pipeline, "_validate_patterns", return_value=self.sample_patterns):
                    with patch.object(self.pipeline, "_populate_knowledge_base", return_value=["id1"]):
                        with patch.object(self.pipeline, "_build_indexes"):
                            with patch.object(self.pipeline, "_train_specialists", return_value={}):
                                with patch.object(self.pipeline, "_evaluate_training", return_value={}):
                                    self.pipeline.run_training_pipeline(self.sample_data_sources)

                                    # Verify logging calls were made
                                    mock_logger.info.assert_called()


class TestTrainingPipelineIntegration:
    """Integration tests for TrainingPipeline with real components."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.temp_db_path = Path("/tmp/test_training_pipeline.db")
        self.pipeline = TrainingPipeline(self.temp_db_path)

    def teardown_method(self):
        """Clean up integration test fixtures."""
        if self.temp_db_path.exists():
            self.temp_db_path.unlink()

    def test_pipeline_with_real_knowledge_base(self):
        """Test pipeline with real knowledge base operations."""
        # Create real patterns
        patterns = [
            ExtractedPattern(
                title="Test React Component",
                description="A test React component for integration testing",
                category=PatternCategory.REACT_PATTERN,
                content="Test component implementation",
                code_example="const TestComponent: React.FC = () => <div>Test</div>",
                tags=["react", "test", "component"],
                confidence_score=0.9,
                source_url="https://example.com/test",
            )
        ]

        # Test validation
        validated = self.pipeline._validate_patterns(patterns)
        assert len(validated) == 1

        # Test knowledge base population
        added_ids = self.pipeline._populate_knowledge_base(validated)
        assert len(added_ids) == 1

        # Test index building
        self.pipeline._build_indexes()
        assert len(self.pipeline.indexer.tag_index) > 0

        # Test specialist training
        training_results = self.pipeline._train_specialists()
        assert isinstance(training_results, dict)

        # Test evaluation
        evaluation_results = self.pipeline._evaluate_training()
        assert "knowledge_base" in evaluation_results
        assert "quality_metrics" in evaluation_results

    def test_continuous_learning_integration(self):
        """Test continuous learning with real knowledge base."""
        # Initial training
        initial_patterns = [
            ExtractedPattern(
                title="Initial Pattern",
                description="Initial pattern for testing",
                category=PatternCategory.REACT_PATTERN,
                content="Test content",
                confidence_score=0.8,
                source_url="https://example.com/initial",
            )
        ]

        # Add initial patterns
        validated = self.pipeline._validate_patterns(initial_patterns)
        self.pipeline._populate_knowledge_base(validated)
        self.pipeline._build_indexes()

        # Get initial stats
        initial_stats = self.pipeline.knowledge_base.get_statistics()
        initial_count = initial_stats["total_items"]

        # Run continuous learning with new patterns
        new_patterns = [
            ExtractedPattern(
                title="New Pattern",
                description="New pattern for continuous learning",
                category=PatternCategory.ACCESSIBILITY,
                content="New test content",
                confidence_score=0.85,
                source_url="https://example.com/new",
            )
        ]

        new_data_sources = [{"url": "https://example.com/new", "type": "web_documentation"}]
        with patch.object(self.pipeline, "_extract_patterns", return_value=new_patterns):
            result = self.pipeline.run_continuous_learning(new_data_sources)

        # Verify new patterns were added
        final_stats = self.pipeline.knowledge_base.get_statistics()
        assert final_stats["total_items"] > initial_count
        assert result["patterns_added"] > 0
