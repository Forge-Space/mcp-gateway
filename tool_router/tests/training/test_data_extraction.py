"""Tests for training data extraction module."""

from unittest.mock import MagicMock, patch

import requests

from tool_router.training.data_extraction import (
    DataSource,
    ExtractedPattern,
    GitHubRepositoryExtractor,
    PatternCategory,
    PatternExtractor,
    WebDocumentationExtractor,
)


class TestDataSource:
    """Test cases for DataSource enum."""

    def test_source_values(self):
        """Test that all expected source values are present."""
        expected_sources = {
            "web_documentation",
            "research_paper",
            "github_repository",
            "industry_standard",
            "community_knowledge",
        }

        actual_sources = {source.value for source in DataSource}
        assert actual_sources == expected_sources


class TestPatternCategory:
    """Test cases for PatternCategory enum."""

    def test_category_values(self):
        """Test that all expected category values are present."""
        expected_categories = {
            "ui_component",
            "react_pattern",
            "accessibility",
            "prompt_engineering",
            "architecture",
            "code_generation",
            "performance",
            "security",
        }

        actual_categories = {category.value for category in PatternCategory}
        assert actual_categories == expected_categories


class TestExtractedPattern:
    """Test cases for ExtractedPattern dataclass."""

    def test_extracted_pattern_creation_minimal(self):
        """Test creating ExtractedPattern with minimal required fields."""
        pattern = ExtractedPattern(
            category=PatternCategory.UI_COMPONENT,
            title="Test Pattern",
            description="Test description",
        )

        assert pattern.category == PatternCategory.UI_COMPONENT
        assert pattern.title == "Test Pattern"
        assert pattern.description == "Test description"
        assert pattern.code_example is None
        assert pattern.best_practice is True
        assert pattern.confidence_score == 1.0
        assert pattern.source_url is None
        assert pattern.tags == []
        assert pattern.metadata == {}

    def test_extracted_pattern_creation_full(self):
        """Test creating ExtractedPattern with all fields."""
        pattern = ExtractedPattern(
            category=PatternCategory.REACT_PATTERN,
            title="React Hook Pattern",
            description="Using React hooks effectively",
            code_example="const [state, setState] = useState(null)",
            best_practice=True,
            confidence_score=0.9,
            source_url="https://example.com/react-hooks",
            tags=["react", "hooks", "state"],
            metadata={"complexity": "medium", "usage": "common"},
        )

        assert pattern.category == PatternCategory.REACT_PATTERN
        assert pattern.title == "React Hook Pattern"
        assert pattern.code_example == "const [state, setState] = useState(null)"
        assert pattern.best_practice is True
        assert pattern.confidence_score == 0.9
        assert pattern.source_url == "https://example.com/react-hooks"
        assert pattern.tags == ["react", "hooks", "state"]
        assert pattern.metadata == {"complexity": "medium", "usage": "common"}

    def test_extracted_pattern_post_init(self):
        """Test post_init initialization of default values."""
        pattern = ExtractedPattern(
            category=PatternCategory.ACCESSIBILITY,
            title="ARIA Pattern",
            description="Accessible rich internet applications",
        )

        # Should initialize empty lists and dicts
        assert pattern.tags == []
        assert pattern.metadata == {}

        # Should not override provided values
        pattern_with_values = ExtractedPattern(
            category=PatternCategory.ACCESSIBILITY,
            title="ARIA Pattern",
            description="Accessible rich internet applications",
            tags=["accessibility", "aria"],
            metadata={"wcag": "AA"},
        )

        assert pattern_with_values.tags == ["accessibility", "aria"]
        assert pattern_with_values.metadata == {"wcag": "AA"}


class TestWebDocumentationExtractor:
    """Test cases for WebDocumentationExtractor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = WebDocumentationExtractor()

    def test_initialization(self):
        """Test extractor initialization."""
        assert self.extractor.session is not None
        assert "User-Agent" in self.extractor.session.headers

    @patch("requests.Session.get")
    def test_extract_patterns_success(self, mock_get):
        """Test successful pattern extraction from web documentation."""
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.content = b"""
        <html>
        <body>
        <h1>React Hooks Documentation</h1>
        <p>Learn about useState and useEffect hooks</p>
        <pre>const [count, setCount] = useState(0)</pre>
        <pre>useEffect(() => { console.log('mounted') }, [])</pre>
        <script>console.log('script should be ignored')</script>
        </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        patterns = self.extractor.extract_patterns("https://example.com/react-hooks")

        assert len(patterns) > 0
        mock_get.assert_called_once_with("https://example.com/react-hooks", timeout=30)

        # Check that React patterns were extracted
        react_patterns = [p for p in patterns if p.category == PatternCategory.REACT_PATTERN]
        assert len(react_patterns) > 0

    @patch("requests.Session.get")
    def test_extract_patterns_http_error(self, mock_get):
        """Test handling of HTTP errors during extraction."""
        mock_get.side_effect = requests.RequestException("Network error")

        patterns = self.extractor.extract_patterns("https://example.com/error")

        assert patterns == []

    @patch("requests.Session.get")
    def test_extract_patterns_timeout(self, mock_get):
        """Test handling of timeout during extraction."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        patterns = self.extractor.extract_patterns("https://example.com/slow")

        assert patterns == []

    def test_extract_react_patterns(self):
        """Test React pattern extraction from text."""
        text = """
        Here's some React code:
        const [count, setCount] = useState(0);
        useEffect(() => { document.title = count }, [count]);
        useContext(MyContext);
        const memoized = useMemo(() => expensiveCalc(a, b), [a, b]);
        """

        patterns = self.extractor._extract_react_patterns(text, "https://example.com")

        # Should extract multiple React patterns
        assert len(patterns) >= 3

        # Verify pattern structure
        for pattern in patterns:
            assert pattern.category == PatternCategory.REACT_PATTERN
            assert pattern.source_url == "https://example.com"
            assert pattern.code_example is not None
            assert "hooks" in pattern.tags

    def test_extract_ui_patterns(self):
        """Test UI pattern extraction from text."""
        text = """
        This documentation covers our design system and component library.
        We use design tokens for consistency across the UI.
        """

        patterns = self.extractor._extract_ui_patterns(text, "https://example.com")

        # Should extract UI patterns
        assert len(patterns) > 0

        for pattern in patterns:
            assert pattern.category == PatternCategory.UI_COMPONENT
            assert pattern.source_url == "https://example.com"

    def test_extract_accessibility_patterns(self):
        """Test accessibility pattern extraction from text."""
        text = """
        Accessibility examples:
        <button aria-label="Close dialog">×</button>
        <img alt="Description of image" src="image.jpg">
        <div role="navigation" aria-label="Main menu">
        """

        patterns = self.extractor._extract_accessibility_patterns(text, "https://example.com")

        # Should extract accessibility patterns
        assert len(patterns) > 0

        for pattern in patterns:
            assert pattern.category == PatternCategory.ACCESSIBILITY
            assert pattern.source_url == "https://example.com"

    def test_extract_patterns_no_matches(self):
        """Test extraction when no patterns are found."""
        text = "Just plain text with no code patterns or specific terminology."

        react_patterns = self.extractor._extract_react_patterns(text, "https://example.com")
        ui_patterns = self.extractor._extract_ui_patterns(text, "https://example.com")
        a11y_patterns = self.extractor._extract_accessibility_patterns(text, "https://example.com")

        assert react_patterns == []
        assert ui_patterns == []
        assert a11y_patterns == []


class TestGitHubRepositoryExtractor:
    """Test cases for GitHubRepositoryExtractor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = GitHubRepositoryExtractor()

    @patch("requests.Session.get")
    def test_extract_patterns_from_readme(self, mock_get):
        """Test pattern extraction from GitHub README."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "test-repo",
            "description": "A test repository",
            "language": "Python",
            "stargazers_count": 100,
            "topics": ["python", "testing"],
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        patterns = self.extractor.extract_patterns("https://github.com/owner/repo")

        assert isinstance(patterns, list)
        assert len(patterns) == 1
        assert patterns[0].title == "Repository: test-repo"
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_extract_patterns_api_error(self, mock_get):
        """Test handling of GitHub API errors."""
        mock_get.side_effect = requests.RequestException("API Error")

        patterns = self.extractor.extract_patterns("https://github.com/owner/repo")

        assert patterns == []


class TestPatternExtractor:
    """Test cases for PatternExtractor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = PatternExtractor()

    def test_initialization(self):
        """Test extractor initialization."""
        assert self.extractor.extractors is not None
        assert DataSource.WEB_DOCUMENTATION in self.extractor.extractors
        assert DataSource.GITHUB_REPOSITORY in self.extractor.extractors

    def test_extract_from_url_web(self):
        """Test extracting patterns from web URL."""
        with patch.object(self.extractor.extractors[DataSource.WEB_DOCUMENTATION], "extract_patterns") as mock_extract:
            mock_patterns = [
                ExtractedPattern(
                    category=PatternCategory.REACT_PATTERN,
                    title="useState Hook",
                    description="State management hook",
                    code_example="useState(0)",
                )
            ]
            mock_extract.return_value = mock_patterns

            patterns = self.extractor.extract_from_url("https://example.com", DataSource.WEB_DOCUMENTATION)

            assert len(patterns) == 1
            assert patterns[0].category == PatternCategory.REACT_PATTERN
            assert patterns[0].title == "useState Hook"

    def test_extract_from_url_github(self):
        """Test extracting patterns from GitHub URL."""
        with patch.object(self.extractor.extractors[DataSource.GITHUB_REPOSITORY], "extract_patterns") as mock_extract:
            mock_patterns = [
                ExtractedPattern(
                    category=PatternCategory.UI_COMPONENT,
                    title="Button Component",
                    description="Reusable button component",
                    code_example="<button>Click</button>",
                )
            ]
            mock_extract.return_value = mock_patterns

            patterns = self.extractor.extract_from_url("https://github.com/owner/repo", DataSource.GITHUB_REPOSITORY)

            assert len(patterns) == 1
            assert patterns[0].category == PatternCategory.UI_COMPONENT
            assert patterns[0].title == "Button Component"

    def test_extract_from_multiple_sources(self):
        """Test extracting patterns from multiple sources."""
        with (
            patch.object(self.extractor.extractors[DataSource.WEB_DOCUMENTATION], "extract_patterns") as mock_web,
            patch.object(self.extractor.extractors[DataSource.GITHUB_REPOSITORY], "extract_patterns") as mock_github,
        ):
            mock_web.return_value = [
                ExtractedPattern(
                    category=PatternCategory.REACT_PATTERN,
                    title="Web Pattern",
                    description="From web docs",
                )
            ]
            mock_github.return_value = [
                ExtractedPattern(
                    category=PatternCategory.UI_COMPONENT,
                    title="GitHub Pattern",
                    description="From GitHub",
                )
            ]

            sources = [
                {"url": "https://example.com", "type": "web_documentation"},
                {"url": "https://github.com/owner/repo", "type": "github_repository"},
            ]

            patterns = self.extractor.extract_from_multiple_sources(sources)

            assert len(patterns) == 2
            categories = {p.category for p in patterns}
            assert PatternCategory.REACT_PATTERN in categories
            assert PatternCategory.UI_COMPONENT in categories

    def test_categorize_patterns(self):
        """Test categorizing patterns by category."""
        patterns = [
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="React Pattern",
                description="React pattern",
            ),
            ExtractedPattern(
                category=PatternCategory.UI_COMPONENT,
                title="UI Pattern",
                description="UI pattern",
            ),
            ExtractedPattern(
                category=PatternCategory.ACCESSIBILITY,
                title="A11y Pattern",
                description="Accessibility pattern",
            ),
        ]

        categorized = self.extractor.categorize_patterns(patterns)

        assert len(categorized) == 3
        assert PatternCategory.REACT_PATTERN in categorized
        assert PatternCategory.UI_COMPONENT in categorized
        assert len(categorized[PatternCategory.REACT_PATTERN]) == 1
        assert len(categorized[PatternCategory.UI_COMPONENT]) == 1

    def test_filter_by_confidence(self):
        """Test filtering patterns by confidence score."""
        patterns = [
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="High Confidence",
                description="High confidence pattern",
                confidence_score=0.9,
            ),
            ExtractedPattern(
                category=PatternCategory.UI_COMPONENT,
                title="Low Confidence",
                description="Low confidence pattern",
                confidence_score=0.3,
            ),
            ExtractedPattern(
                category=PatternCategory.ACCESSIBILITY,
                title="Medium Confidence",
                description="Medium confidence pattern",
                confidence_score=0.6,
            ),
        ]

        high_confidence = self.extractor.filter_by_confidence(patterns, 0.7)
        medium_confidence = self.extractor.filter_by_confidence(patterns, 0.5)

        assert len(high_confidence) == 1
        assert len(medium_confidence) == 2
        assert high_confidence[0].confidence_score == 0.9

    def test_get_top_patterns(self):
        """Test getting top patterns by confidence score."""
        patterns = [
            ExtractedPattern(
                category=PatternCategory.REACT_PATTERN,
                title="High Confidence",
                description="High confidence pattern",
                confidence_score=0.9,
            ),
            ExtractedPattern(
                category=PatternCategory.UI_COMPONENT,
                title="Medium Confidence",
                description="Medium confidence pattern",
                confidence_score=0.6,
            ),
            ExtractedPattern(
                category=PatternCategory.ACCESSIBILITY,
                title="Low Confidence",
                description="Low confidence pattern",
                confidence_score=0.3,
            ),
        ]

        top_patterns = self.extractor.get_top_patterns(patterns, limit=2)

        assert len(top_patterns) == 2
        assert top_patterns[0].confidence_score == 0.9
        assert top_patterns[1].confidence_score == 0.6


class TestDataExtractionIntegration:
    """Integration tests for data extraction system."""

    def test_end_to_end_extraction(self):
        """Test end-to-end pattern extraction workflow."""
        extractor = PatternExtractor()

        with (
            patch.object(extractor.extractors[DataSource.WEB_DOCUMENTATION], "extract_patterns") as mock_web,
            patch.object(extractor.extractors[DataSource.GITHUB_REPOSITORY], "extract_patterns") as mock_github,
        ):
            mock_web.return_value = [
                ExtractedPattern(
                    category=PatternCategory.REACT_PATTERN,
                    title="Web React Pattern",
                    description="From web documentation",
                )
            ]
            mock_github.return_value = [
                ExtractedPattern(
                    category=PatternCategory.UI_COMPONENT,
                    title="GitHub UI Pattern",
                    description="From GitHub repository",
                )
            ]

            sources = [
                {"url": "https://react.dev/docs", "type": "web_documentation"},
                {"url": "https://github.com/facebook/react", "type": "github_repository"},
            ]

            patterns = extractor.extract_from_multiple_sources(sources)

            # Verify extraction
            assert len(patterns) == 2
            categories = {p.category for p in patterns}
            assert PatternCategory.REACT_PATTERN in categories
            assert PatternCategory.UI_COMPONENT in categories

            # Verify all patterns have required fields
            for pattern in patterns:
                assert pattern.title
                assert pattern.description
                assert pattern.category in PatternCategory

    def test_batch_extraction(self):
        """Test batch extraction from multiple sources."""
        extractor = PatternExtractor()

        sources = [
            {"url": "https://example1.com", "type": "web_documentation"},
            {"url": "https://example2.com", "type": "web_documentation"},
            {"url": "https://github.com/owner/repo1", "type": "github_repository"},
            {"url": "https://github.com/owner/repo2", "type": "github_repository"},
        ]

        with (
            patch.object(extractor.extractors[DataSource.WEB_DOCUMENTATION], "extract_patterns") as mock_web,
            patch.object(extractor.extractors[DataSource.GITHUB_REPOSITORY], "extract_patterns") as mock_github,
        ):
            mock_web.return_value = [
                ExtractedPattern(
                    category=PatternCategory.REACT_PATTERN,
                    title="Web Pattern",
                    description="Web pattern",
                )
            ]
            mock_github.return_value = [
                ExtractedPattern(
                    category=PatternCategory.UI_COMPONENT,
                    title="GitHub Pattern",
                    description="GitHub pattern",
                )
            ]

            patterns = extractor.extract_from_multiple_sources(sources)

            # Should extract from all sources
            assert len(patterns) == 4
            web_patterns = [p for p in patterns if p.category == PatternCategory.REACT_PATTERN]
            github_patterns = [p for p in patterns if p.category == PatternCategory.UI_COMPONENT]
            assert len(web_patterns) == 2
            assert len(github_patterns) == 2
