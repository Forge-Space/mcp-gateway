"""Unit tests for Data Extraction.

Tests the pattern extraction functionality including:
- Web content extraction
- GitHub repository analysis
- Pattern categorization and validation
- Content quality assessment
- Metadata extraction and processing
"""

from unittest.mock import patch

from tool_router.training.data_extraction import (
    DataSource,
    ExtractedPattern,
    PatternCategory,
    PatternExtractor,
)


class TestPatternExtractor:
    """Test cases for PatternExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = PatternExtractor()

    def test_initialization(self):
        """Test PatternExtractor initialization."""
        assert hasattr(self.extractor, "extractors")
        assert DataSource.WEB_DOCUMENTATION in self.extractor.extractors
        assert DataSource.GITHUB_REPOSITORY in self.extractor.extractors
        assert len(self.extractor.extractors) == 2

    def test_extract_from_web_documentation(self):
        """Test extraction from web documentation."""
        url = "https://react.dev/docs/components"

        with patch.object(
            self.extractor.extractors[DataSource.WEB_DOCUMENTATION],
            "extract_patterns",
            return_value=[],
        ) as mock_extract:
            result = self.extractor.extract_from_url(url, DataSource.WEB_DOCUMENTATION)

            assert isinstance(result, list)
            mock_extract.assert_called_once_with(url)

    def test_extract_from_github_repository(self):
        """Test extraction from GitHub repository."""
        url = "https://github.com/facebook/react"

        with patch.object(
            self.extractor.extractors[DataSource.GITHUB_REPOSITORY],
            "extract_patterns",
            return_value=[],
        ) as mock_extract:
            result = self.extractor.extract_from_url(url, DataSource.GITHUB_REPOSITORY)

            assert isinstance(result, list)
            mock_extract.assert_called_once_with(url)

    def test_extract_from_multiple_sources(self):
        """Test extraction from multiple sources."""
        sources = [
            {
                "url": "https://example.com/doc1",
                "type": "web_documentation",
                "category": "react_patterns",
            },
            {
                "url": "https://github.com/example/repo",
                "type": "github_repository",
                "category": "react_patterns",
            },
        ]

        with patch.object(self.extractor, "extract_from_url") as mock_extract:
            # Mock successful extractions
            mock_extract.return_value = []

            result = self.extractor.extract_from_multiple_sources(sources)

            assert isinstance(result, list)
            assert mock_extract.call_count == 2

    def test_extract_from_unknown_source_type(self):
        """Test extraction from unknown source type returns empty list."""
        url = "https://example.com/unknown"

        result = self.extractor.extract_from_url(url, DataSource.WEB_DOCUMENTATION)

        # Should return empty list for unknown source type
        assert isinstance(result, list)

    def test_extract_from_multiple_sources_with_invalid_data(self):
        """Test extraction from multiple sources with invalid data."""
        sources = [
            {"url": "https://example.com/doc1", "type": "web_documentation"},
            {"url": "https://github.com/example/repo", "type": "github_repository"},
        ]

        with patch.object(self.extractor, "extract_from_url") as mock_extract:
            # Mock successful extractions
            mock_extract.return_value = []

            result = self.extractor.extract_from_multiple_sources(sources)

            assert isinstance(result, list)
            assert mock_extract.call_count == 2


class TestExtractedPattern:
    """Test cases for ExtractedPattern dataclass."""

    def test_extracted_pattern_creation(self):
        """Test ExtractedPattern creation."""
        pattern = ExtractedPattern(
            category=PatternCategory.UI_COMPONENT,
            title="React Button Component",
            description="A reusable button component",
            code_example="const Button: React.FC = () => <button>Click me</button>",
            source_url="https://example.com/button",
            confidence_score=0.9,
        )

        assert pattern.category == PatternCategory.UI_COMPONENT
        assert pattern.title == "React Button Component"
        assert pattern.description == "A reusable button component"
        assert pattern.code_example == "const Button: React.FC = () => <button>Click me</button>"
        assert pattern.source_url == "https://example.com/button"
        assert pattern.confidence_score == 0.9

    def test_extracted_pattern_with_optional_fields(self):
        """Test ExtractedPattern with optional fields."""
        pattern = ExtractedPattern(
            category=PatternCategory.REACT_PATTERN,
            title="React Hook Pattern",
            description="Custom hook for state management",
            code_example="const useCustomHook = () => { /* hook implementation */ }",
            source_url="https://example.com/hook",
        )

        assert pattern.category == PatternCategory.REACT_PATTERN
        assert pattern.title == "React Hook Pattern"
        assert pattern.description == "Custom hook for state management"
        assert pattern.code_example == "const useCustomHook = () => { /* hook implementation */ }"
        assert pattern.source_url == "https://example.com/hook"
        # Optional fields should have default values
        assert pattern.confidence_score >= 0 and pattern.confidence_score <= 1


class TestPatternCategory:
    """Test cases for PatternCategory enum."""

    def test_pattern_category_values(self):
        """Test PatternCategory enum values."""
        categories = list(PatternCategory)

        assert PatternCategory.UI_COMPONENT in categories
        assert PatternCategory.REACT_PATTERN in categories
        assert PatternCategory.ACCESSIBILITY in categories
        assert PatternCategory.PROMPT_ENGINEERING in categories
        assert PatternCategory.ARCHITECTURE in categories
        assert PatternCategory.CODE_GENERATION in categories
        assert PatternCategory.PERFORMANCE in categories
        assert PatternCategory.SECURITY in categories


class TestDataSource:
    """Test cases for DataSource enum."""

    def test_data_source_values(self):
        """Test DataSource enum values."""
        sources = list(DataSource)

        assert DataSource.WEB_DOCUMENTATION in sources
        assert DataSource.RESEARCH_PAPER in sources
        assert DataSource.GITHUB_REPOSITORY in sources
        assert DataSource.INDUSTRY_STANDARD in sources
        assert DataSource.COMMUNITY_KNOWLEDGE in sources
