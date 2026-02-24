"""Data extraction module for training specialist AI agents.

Extracts patterns and best practices from public data sources including:
- Web documentation and articles
- Research papers and publications
- Open source repositories
- Industry standards and guidelines
- Community knowledge bases
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

import requests
from bs4 import BeautifulSoup


class DataSource(Enum):
    """Types of data sources for pattern extraction."""
    WEB_DOCUMENTATION = "web_documentation"
    RESEARCH_PAPER = "research_paper"
    GITHUB_REPOSITORY = "github_repository"
    INDUSTRY_STANDARD = "industry_standard"
    COMMUNITY_KNOWLEDGE = "community_knowledge"


class PatternCategory(Enum):
    """Categories of patterns for specialist training."""
    UI_COMPONENT = "ui_component"
    REACT_PATTERN = "react_pattern"
    ACCESSIBILITY = "accessibility"
    PROMPT_ENGINEERING = "prompt_engineering"
    ARCHITECTURE = "architecture"
    CODE_GENERATION = "code_generation"
    PERFORMANCE = "performance"
    SECURITY = "security"


@dataclass
class ExtractedPattern:
    """Represents an extracted pattern from training data."""
    category: PatternCategory
    title: str
    description: str
    code_example: str | None = None
    best_practice: bool = True
    confidence_score: float = 1.0
    source_url: str | None = None
    tags: list[str] = None
    metadata: dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


class DataExtractor(ABC):
    """Abstract base class for data extractors."""

    @abstractmethod
    def extract_patterns(self, source: str) -> list[ExtractedPattern]:
        """Extract patterns from a data source."""


class WebDocumentationExtractor(DataExtractor):
    """Extracts patterns from web documentation and articles."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MCP-Gateway-Training/1.0"
        })

    def extract_patterns(self, url: str) -> list[ExtractedPattern]:
        """Extract patterns from web documentation."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()
            patterns = []

            # Detect React patterns
            if "react" in url.lower() or "react" in text.lower():
                patterns.extend(self._extract_react_patterns(text, url))

            # Detect UI patterns
            if any(term in url.lower() for term in ["ui", "component", "design"]):
                patterns.extend(self._extract_ui_patterns(text, url))

            # Detect accessibility patterns
            if any(term in url.lower() for term in ["accessibility", "a11y", "wcag"]):
                patterns.extend(self._extract_accessibility_patterns(text, url))

            return patterns

        except Exception as e:
            print(f"Error extracting from {url}: {e}")
            return []

    def _extract_react_patterns(self, text: str, source_url: str) -> list[ExtractedPattern]:
        """Extract React-specific patterns."""
        patterns = []

        # React hooks patterns
        hooks_patterns = [
            (r"useState\([^)]+\)", "useState Hook", "State management with functional components"),
            (r"useEffect\([^)]+\)", "useEffect Hook", "Side effects in functional components"),
            (r"useContext\([^)]+\)", "useContext Hook", "Context consumption in functional components"),
            (r"useReducer\([^)]+\)", "useReducer Hook", "Complex state management"),
            (r"useMemo\([^)]+\)", "useMemo Hook", "Memoization for performance"),
            (r"useCallback\([^)]+\)", "useCallback Hook", "Function memoization"),
        ]

        for pattern, title, description in hooks_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                patterns.append(ExtractedPattern(
                    category=PatternCategory.REACT_PATTERN,
                    title=title,
                    description=description,
                    code_example=matches[0] if matches else None,
                    source_url=source_url,
                    tags=["hooks", "functional-components"],
                    metadata={"usage_count": len(matches)}
                ))

        # Component patterns
        component_patterns = [
            (r"const\s+\w+\s*=\s*\([^)]+\)\s*=>\s*{", "Functional Component", "Arrow function component syntax"),
            (r"export\s+default\s+function\s+\w+", "Named Function Component", "Named function export"),
            (r"export\s+default\s+const\s+\w+", "Const Component", "Const component declaration"),
            (r"React\.memo\([^)]+\)", "React.memo", "Component memoization"),
            (r"React\.forwardRef\([^)]+\)", "forwardRef", "Ref forwarding"),
        ]

        for pattern, title, description in component_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                patterns.append(ExtractedPattern(
                    category=PatternCategory.REACT_PATTERN,
                    title=title,
                    description=description,
                    code_example=matches[0] if matches else None,
                    source_url=source_url,
                    tags=["components", "syntax"],
                    metadata={"usage_count": len(matches)}
                ))

        return patterns

    def _extract_ui_patterns(self, text: str, source_url: str) -> list[ExtractedPattern]:
        """Extract UI design patterns."""
        patterns = []

        # Design system patterns
        design_patterns = [
            (r"design\s+system", "Design System", "Systematic approach to UI design"),
            (r"component\s+library", "Component Library", "Reusable UI components"),
            (r"design\s+token", "Design Token", "Design variables and constants"),
            (r"style\s+guide", "Style Guide", "Visual design guidelines"),
            (r"pattern\s+library", "Pattern Library", "UI pattern collection"),
        ]

        for pattern, title, description in design_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                patterns.append(ExtractedPattern(
                    category=PatternCategory.UI_COMPONENT,
                    title=title,
                    description=description,
                    source_url=source_url,
                    tags=["design-system", "ui"],
                    metadata={"mentioned": True}
                ))

        return patterns

    def _extract_accessibility_patterns(self, text: str, source_url: str) -> list[ExtractedPattern]:
        """Extract accessibility patterns."""
        patterns = []

        # Accessibility patterns
        a11y_patterns = [
            (r"aria-[a-z]+", "ARIA Attributes", "Accessibility attributes for screen readers"),
            (r"role=[\"'][^\"']+[\"']", "Semantic Roles", "HTML5 semantic roles"),
            (r"tabindex", "Tab Navigation", "Keyboard navigation support"),
            (r"alt=[\"'][^\"']+[\"']", "Alt Text", "Alternative text for images"),
            (r"wcag\s*2\.[0-9]", "WCAG Guidelines", "Web Content Accessibility Guidelines"),
        ]

        for pattern, title, description in a11y_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                patterns.append(ExtractedPattern(
                    category=PatternCategory.ACCESSIBILITY,
                    title=title,
                    description=description,
                    code_example=matches[0] if matches else None,
                    source_url=source_url,
                    tags=["accessibility", "a11y"],
                    metadata={"usage_count": len(matches)}
                ))

        return patterns


class GitHubRepositoryExtractor(DataExtractor):
    """Extracts patterns from GitHub repositories."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MCP-Gateway-Training/1.0",
            "Accept": "application/vnd.github.v3+json"
        })

    def extract_patterns(self, repo_url: str) -> list[ExtractedPattern]:
        """Extract patterns from a GitHub repository."""
        try:
            # Extract owner and repo name from URL
            match = re.match(r"https?://github\.com/([^/]+)/([^/]+)", repo_url)
            if not match:
                return []

            owner, repo = match.groups()

            # Get repository contents
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()

            repo_data = response.json()

            patterns = []

            # Add repository as a pattern source
            patterns.append(ExtractedPattern(
                category=PatternCategory.UI_COMPONENT,
                title=f"Repository: {repo_data['name']}",
                description=repo_data.get("description", ""),
                source_url=repo_url,
                tags=["repository", "open-source"],
                metadata={
                    "stars": repo_data.get("stargazers_count", 0),
                    "language": repo_data.get("language", ""),
                    "topics": repo_data.get("topics", [])
                }
            ))

            return patterns

        except Exception as e:
            print(f"Error extracting from GitHub repo {repo_url}: {e}")
            return []


class PatternExtractor:
    """Main pattern extraction coordinator."""

    def __init__(self) -> None:
        self.extractors = {
            DataSource.WEB_DOCUMENTATION: WebDocumentationExtractor(),
            DataSource.GITHUB_REPOSITORY: GitHubRepositoryExtractor(),
        }

    def extract_from_url(self, url: str, source_type: DataSource) -> list[ExtractedPattern]:
        """Extract patterns from a URL."""
        extractor = self.extractors.get(source_type)
        if not extractor:
            print(f"No extractor available for source type: {source_type}")
            return []

        return extractor.extract_patterns(url)

    def extract_from_multiple_sources(self, sources: list[dict[str, Any]]) -> list[ExtractedPattern]:
        """Extract patterns from multiple sources."""
        all_patterns = []

        for source in sources:
            url = source.get("url")
            source_type = DataSource(source.get("type"))

            if url and source_type:
                patterns = self.extract_from_url(url, source_type)
                all_patterns.extend(patterns)

        return all_patterns

    def categorize_patterns(self, patterns: list[ExtractedPattern]) -> dict[PatternCategory, list[ExtractedPattern]]:
        """Categorize patterns by type."""
        categorized = {}

        for pattern in patterns:
            category = pattern.category
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(pattern)

        return categorized

    def filter_by_confidence(self, patterns: list[ExtractedPattern], min_confidence: float = 0.7) -> list[ExtractedPattern]:
        """Filter patterns by confidence score."""
        return [p for p in patterns if p.confidence_score >= min_confidence]

    def get_top_patterns(self, patterns: list[ExtractedPattern], limit: int = 10) -> list[ExtractedPattern]:
        """Get top patterns by confidence score."""
        return sorted(patterns, key=lambda p: p.confidence_score, reverse=True)[:limit]


# Example usage and training data sources
TRAINING_DATA_SOURCES = [
    # React Best Practices
    {
        "url": "https://react.dev/reference/rules",
        "type": "web_documentation",
        "category": "react_patterns"
    },
    {
        "url": "https://medium.com/@regondaakhil/react-best-practices-and-patterns-for-2024-f5cdf8e132f1",
        "type": "web_documentation",
        "category": "react_patterns"
    },

    # Design Systems
    {
        "url": "https://carbondesignsystem.com/",
        "type": "web_documentation",
        "category": "design_systems"
    },
    {
        "url": "https://www.lightningdesignsystem.com/",
        "type": "web_documentation",
        "category": "design_systems"
    },

    # Accessibility
    {
        "url": "https://www.w3.org/WAI/WCAG21/quickref/",
        "type": "web_documentation",
        "category": "accessibility"
    },

    # GitHub Repositories
    {
        "url": "https://github.com/facebook/react",
        "type": "github_repository",
        "category": "react_patterns"
    },
    {
        "url": "https://github.com/microsoft/fluentui",
        "type": "github_repository",
        "category": "design_systems"
    },
]

if __name__ == "__main__":
    # Example usage
    extractor = PatternExtractor()

    print("Extracting patterns from training sources...")
    patterns = extractor.extract_from_multiple_sources(TRAINING_DATA_SOURCES)

    print(f"Extracted {len(patterns)} patterns")

    # Categorize patterns
    categorized = extractor.categorize_patterns(patterns)

    for category, category_patterns in categorized.items():
        print(f"\n{category.value}: {len(category_patterns)} patterns")
        for pattern in category_patterns[:3]:  # Show first 3
            print(f"  - {pattern.title}: {pattern.description[:50]}...")

    # Get top patterns
    top_patterns = extractor.get_top_patterns(patterns, limit=5)
    print("\nTop 5 patterns:")
    for i, pattern in enumerate(top_patterns, 1):
        print(f"{i}. {pattern.title} (confidence: {pattern.confidence_score})")
