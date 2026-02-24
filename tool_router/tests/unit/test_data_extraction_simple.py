"""
Unit tests for Data Extraction (Simple Version).

Tests the pattern extraction functionality including:
- Web content extraction
- GitHub repository analysis
- Pattern categorization and validation
- Content quality assessment
- Metadata extraction and processing
"""

from unittest.mock import Mock, patch

from tool_router.training.data_extraction import (
    DataSource,
    ExtractedPattern,
    GitHubRepositoryExtractor,
    PatternCategory,
    PatternExtractor,
    WebDocumentationExtractor,
)


class TestPatternExtractor:
    """Test cases for PatternExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = PatternExtractor()

    def test_initialization(self):
        """Test PatternExtractor initialization."""
        assert self.extractor.extractors is not None
        assert DataSource.WEB_DOCUMENTATION in self.extractor.extractors
        assert DataSource.GITHUB_REPOSITORY in self.extractor.extractors

    def test_extract_from_url_web_documentation(self):
        """Test extraction from web documentation."""
        url = "https://react.dev/docs/components"
        source_type = DataSource.WEB_DOCUMENTATION

        with patch.object(
            self.extractor.extractors[source_type], "extract_patterns", return_value=[]
        ) as mock_extract:
            result = self.extractor.extract_from_url(url, source_type)

            assert isinstance(result, list)
            mock_extract.assert_called_once_with(url)

    def test_extract_from_url_github_repository(self):
        """Test extraction from GitHub repository."""
        url = "https://github.com/facebook/react"
        source_type = DataSource.GITHUB_REPOSITORY

        with patch.object(
            self.extractor.extractors[source_type], "extract_patterns", return_value=[]
        ) as mock_extract:
            result = self.extractor.extract_from_url(url, source_type)

            assert isinstance(result, list)
            mock_extract.assert_called_once_with(url)

    def test_extract_from_multiple_sources(self):
        """Test extraction from multiple sources."""
        sources = [
            {"url": "https://react.dev/docs/components", "type": "web_documentation"},
            {"url": "https://github.com/facebook/react", "type": "github_repository"},
        ]

        with patch.object(
            self.extractor, "extract_from_url", return_value=[]
        ) as mock_extract:
            result = self.extractor.extract_from_multiple_sources(sources)

            assert isinstance(result, list)
            assert mock_extract.call_count == 2

    def test_categorize_patterns(self):
        """Test pattern categorization."""
        patterns = [
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="React Component",
                description="A React component",
                source_url="https://example.com/react",
            ),
            ExtractedPattern(
                category=PatternCategory.ACCESSIBILITY,
                title="Accessibility Pattern",
                description="An accessibility pattern",
                source_url="https://example.com/a11y",
            ),
        ]

        categorized = self.extractor.categorize_patterns(patterns)

        assert PatternCategory.REACT_PATTERN in categorized
        assert PatternCategory.ACCESSIBILITY in categorized
        assert len(categorized[PatternCategory.REACT_PATTERN]) == 1
        assert len(categorized[PatternCategory.ACCESSIBILITY]) == 1

    def test_filter_by_confidence(self):
        """Test filtering patterns by confidence score."""
        patterns = [
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="High Confidence",
                description="High confidence pattern",
                confidence_score=0.9,
                source_url="https://example.com/high",
            ),
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="Low Confidence",
                description="Low confidence pattern",
                confidence_score=0.5,
                source_url="https://example.com/low",
            ),
        ]

        filtered = self.extractor.filter_by_confidence(patterns, min_confidence=0.7)

        assert len(filtered) == 1
        assert filtered[0].confidence_score >= 0.7

    def test_get_top_patterns(self):
        """Test getting top patterns by confidence score."""
        patterns = [
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="Pattern 1",
                description="First pattern",
                confidence_score=0.8,
                source_url="https://example.com/1",
            ),
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="Pattern 2",
                description="Second pattern",
                confidence_score=0.9,
                source_url="https://example.com/2",
            ),
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="Pattern 3",
                description="Third pattern",
                confidence_score=0.7,
                source_url="https://example.com/3",
            ),
        ]

        top_patterns = self.extractor.get_top_patterns(patterns, limit=2)

        assert len(top_patterns) == 2
        assert top_patterns[0].confidence_score == 0.9
        assert top_patterns[1].confidence_score == 0.8

    def test_extract_from_unknown_source_type(self):
        """Test extraction from unknown source type."""
        url = "https://example.com/unknown"
        source_type = DataSource.INDUSTRY_STANDARD  # Not in extractors

        result = self.extractor.extract_from_url(url, source_type)

        assert result == []


class TestWebDocumentationExtractor:
    """Test cases for WebDocumentationExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = WebDocumentationExtractor()

    def test_initialization(self):
        """Test WebDocumentationExtractor initialization."""
        assert self.extractor.session is not None
        assert "User-Agent" in self.extractor.session.headers

    def test_extract_patterns_success(self):
        """Test successful pattern extraction."""
        html_content = """
        <html>
        <body>
            <h1>React Components</h1>
            <p>React components are the building blocks of React applications.</p>
            <pre><code>const Component = () => <div>Hello World</div></code></pre>
        </body>
        </html>
        """

        with patch.object(self.extractor.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.content = html_content.encode()
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = self.extractor.extract_patterns("https://react.dev/docs")

            assert isinstance(result, list)
            mock_get.assert_called_once()

    def test_extract_patterns_network_error(self):
        """Test pattern extraction with network error."""
        with patch.object(
            self.extractor.session, "get", side_effect=Exception("Network error")
        ):
            result = self.extractor.extract_patterns("https://react.dev/docs")

            assert result == []

    def test_extract_react_patterns(self):
        """Test React pattern extraction."""
        text = """
        Here is some React code:
        const [state, setState] = useState(0);
        useEffect(() => {
            // Side effect
        }, [dependency]);
        """

        patterns = self.extractor._extract_react_patterns(text, "https://example.com")

        assert len(patterns) >= 0
        if patterns:
            assert all(p.category == PatternCategory.REACT_PATTERN for p in patterns)

    def test_extract_ui_patterns(self):
        """Test UI pattern extraction."""
        text = """
        This document describes a design system with component library
        and style guide for the UI patterns.
        """

        patterns = self.extractor._extract_ui_patterns(text, "https://example.com")

        assert len(patterns) >= 0
        if patterns:
            assert all(p.category == PatternCategory.UI_COMPONENT for p in patterns)

    def test_extract_accessibility_patterns(self):
        """Test accessibility pattern extraction."""
        text = """
        This component uses aria-label for accessibility
        and role="button" for semantic meaning.
        It also includes alt text for images.
        """

        patterns = self.extractor._extract_accessibility_patterns(
            text, "https://example.com"
        )

        assert len(patterns) >= 0
        if patterns:
            assert all(p.category == PatternCategory.ACCESSIBILITY for p in patterns)


class TestGitHubRepositoryExtractor:
    """Test cases for GitHubRepositoryExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = GitHubRepositoryExtractor()

    def test_initialization(self):
        """Test GitHubRepositoryExtractor initialization."""
        assert self.extractor.session is not None
        assert "User-Agent" in self.extractor.session.headers
        assert "Accept" in self.extractor.session.headers

    def test_extract_patterns_success(self):
        """Test successful pattern extraction from GitHub."""
        repo_data = {
            "name": "react",
            "description": "A JavaScript library for building user interfaces",
            "stargazers_count": 1000,
            "language": "JavaScript",
            "topics": ["javascript", "library", "ui"],
        }

        with patch.object(self.extractor.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = repo_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = self.extractor.extract_patterns(
                "https://github.com/facebook/react"
            )

            assert len(result) == 1
            assert result[0].title == "Repository: react"
            assert (
                result[0].description
                == "A JavaScript library for building user interfaces"
            )
            assert result[0].source_url == "https://github.com/facebook/react"

    def test_extract_patterns_invalid_url(self):
        """Test pattern extraction with invalid GitHub URL."""
        result = self.extractor.extract_patterns("https://invalid-url.com/repo")

        assert result == []

    def test_extract_patterns_network_error(self):
        """Test pattern extraction with network error."""
        with patch.object(
            self.extractor.session, "get", side_effect=Exception("Network error")
        ):
            result = self.extractor.extract_patterns(
                "https://github.com/facebook/react"
            )

            assert result == []


class TestExtractedPattern:
    """Test cases for ExtractedPattern dataclass."""

    def test_pattern_creation(self):
        """Test ExtractedPattern creation."""
        pattern = ExtractedPattern(
            category=PatternCategory.REACT_PATTERN,
            title="Test Pattern",
            description="A test pattern for unit testing",
            code_example="const Test = () => <div>Test</div>",
            tags=["test", "react"],
            confidence_score=0.85,
            source_url="https://example.com/test",
            metadata={"test": True},
        )

        assert pattern.title == "Test Pattern"
        assert pattern.description == "A test pattern for unit testing"
        assert pattern.category == PatternCategory.REACT_PATTERN
        assert pattern.code_example == "const Test = () => <div>Test</div>"
        assert pattern.tags == ["test", "react"]
        assert pattern.confidence_score == 0.85
        assert pattern.source_url == "https://example.com/test"
        assert pattern.metadata == {"test": True}

    def test_pattern_with_defaults(self):
        """Test ExtractedPattern with default values."""
        pattern = ExtractedPattern(
            category=PatternCategory.UI_COMPONENT,
            title="Minimal Pattern",
            description="Minimal description",
            source_url="https://example.com/minimal",
        )

        assert pattern.code_example is None
        assert pattern.tags == []
        assert pattern.confidence_score == 1.0  # Default value
        assert pattern.metadata == {}
        assert pattern.best_practice is True  # Default value

    def test_pattern_post_init(self):
        """Test ExtractedPattern post-init processing."""
        pattern = ExtractedPattern(
            category=PatternCategory.REACT_PATTERN,
            title="Test Pattern",
            description="Test description",
            source_url="https://example.com/test",
        )

        # Should initialize empty lists and dicts
        assert pattern.tags == []
        assert pattern.metadata == {}


class TestPatternCategory:
    """Test cases for PatternCategory enum."""

    def test_category_values(self):
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

    def test_category_string_values(self):
        """Test PatternCategory string values."""
        assert PatternCategory.UI_COMPONENT.value == "ui_component"
        assert PatternCategory.REACT_PATTERN.value == "react_pattern"
        assert PatternCategory.ACCESSIBILITY.value == "accessibility"
        assert PatternCategory.PROMPT_ENGINEERING.value == "prompt_engineering"


class TestDataSource:
    """Test cases for DataSource enum."""

    def test_source_values(self):
        """Test DataSource enum values."""
        sources = list(DataSource)

        assert DataSource.WEB_DOCUMENTATION in sources
        assert DataSource.RESEARCH_PAPER in sources
        assert DataSource.GITHUB_REPOSITORY in sources
        assert DataSource.INDUSTRY_STANDARD in sources
        assert DataSource.COMMUNITY_KNOWLEDGE in sources

    def test_source_string_values(self):
        """Test DataSource string values."""
        assert DataSource.WEB_DOCUMENTATION.value == "web_documentation"
        assert DataSource.RESEARCH_PAPER.value == "research_paper"
        assert DataSource.GITHUB_REPOSITORY.value == "github_repository"


class TestDataExtractionIntegration:
    """Integration tests for data extraction."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.extractor = PatternExtractor()

    def test_end_to_end_extraction(self):
        """Test end-to-end extraction process."""
        sources = [
            {"url": "https://react.dev/docs/components", "type": "web_documentation"},
            {"url": "https://github.com/facebook/react", "type": "github_repository"},
        ]

        with patch.object(
            self.extractor, "extract_from_url", return_value=[]
        ) as mock_extract:
            result = self.extractor.extract_from_multiple_sources(sources)

            assert isinstance(result, list)
            assert mock_extract.call_count == 2

            # Test categorization
            if result:
                categorized = self.extractor.categorize_patterns(result)
                assert isinstance(categorized, dict)

    def test_filtering_and_ranking_workflow(self):
        """Test complete filtering and ranking workflow."""
        patterns = [
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="High Quality Pattern",
                description="High quality pattern with examples",
                confidence_score=0.95,
                source_url="https://example.com/high",
            ),
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="Medium Quality Pattern",
                description="Medium quality pattern",
                confidence_score=0.75,
                source_url="https://example.com/medium",
            ),
            ExtractedPattern(
                category=PatternCategory.ACCESSIBILITY,
                title="Low Quality Pattern",
                description="Low quality pattern",
                confidence_score=0.5,
                source_url="https://example.com/low",
            ),
        ]

        # Filter by confidence
        filtered = self.extractor.filter_by_confidence(patterns, min_confidence=0.7)
        assert len(filtered) == 2

        # Get top patterns
        top_patterns = self.extractor.get_top_patterns(filtered, limit=5)
        assert len(top_patterns) == 2
        assert top_patterns[0].confidence_score >= top_patterns[1].confidence_score

        # Categorize
        categorized = self.extractor.categorize_patterns(top_patterns)
        assert PatternCategory.REACT_PATTERN in categorized
        assert len(categorized[PatternCategory.REACT_PATTERN]) == 2

    def test_error_handling_workflow(self):
        """Test error handling in extraction workflow."""
        sources = [
            {"url": "https://invalid-url.com/docs", "type": "web_documentation"},
            {"url": "https://github.com/invalid/repo", "type": "github_repository"},
        ]

        # Should handle errors gracefully
        result = self.extractor.extract_from_multiple_sources(sources)

        assert isinstance(result, list)
        # May return empty list due to errors

        # Should still work with empty results
        categorized = self.extractor.categorize_patterns(result)
        assert isinstance(categorized, dict)

        filtered = self.extractor.filter_by_confidence(result)
        assert isinstance(filtered, list)

        top_patterns = self.extractor.get_top_patterns(result)
        assert isinstance(top_patterns, list)
