"""Tests for training knowledge base module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

import pytest

from tool_router.training.knowledge_base import (
    KnowledgeStatus,
    KnowledgeItem,
    KnowledgeBase,
    KnowledgeIndexer,
)
from tool_router.training.data_extraction import ExtractedPattern, PatternCategory


class TestKnowledgeStatus:
    """Test cases for KnowledgeStatus enum."""

    def test_status_values(self):
        """Test that all expected status values are present."""
        expected_statuses = {
            "active",
            "pending",
            "deprecated",
            "archived"
        }

        actual_statuses = {status.value for status in KnowledgeStatus}
        assert actual_statuses == expected_statuses


class TestKnowledgeItem:
    """Test cases for KnowledgeItem dataclass."""

    def test_knowledge_item_creation_minimal(self):
        """Test creating KnowledgeItem with minimal required fields."""
        item = KnowledgeItem(
            id="test-1",
            category=PatternCategory.UI_COMPONENT,
            title="Test Item",
            description="Test description",
            content="Test content"
        )

        assert item.id == "test-1"
        assert item.category == PatternCategory.UI_COMPONENT
        assert item.title == "Test Item"
        assert item.description == "Test description"
        assert item.content == "Test content"
        assert item.code_example is None
        assert item.tags == []
        assert item.confidence_score == 1.0
        assert item.status == KnowledgeStatus.ACTIVE
        assert item.source_url is None
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)
        assert item.usage_count == 0
        assert item.user_ratings == []
        assert item.metadata == {}

    def test_knowledge_item_creation_full(self):
        """Test creating KnowledgeItem with all fields."""
        created_time = datetime.now(timezone.utc)
        updated_time = created_time + timedelta(days=1)

        item = KnowledgeItem(
            id="test-2",
            category=PatternCategory.REACT_PATTERN,
            title="Test Item Full",
            description="Test description with details",
            content="Test content with details",
            code_example="const [state, setState] = useState(null)",
            tags=["react", "hooks", "state"],
            confidence_score=0.9,
            status=KnowledgeStatus.DEPRECATED,
            source_url="https://example.com/react",
            created_at=created_time,
            updated_at=updated_time,
            usage_count=10,
            user_ratings=[4.5, 5.0, 4.0],
            metadata={
                "author": "test_author",
                "version": "1.0",
                "source": "test_source"
            }
        )

        assert item.id == "test-2"
        assert item.category == PatternCategory.REACT_PATTERN
        assert item.title == "Test Item Full"
        assert item.description == "Test description with details"
        assert item.content == "Test content with details"
        assert item.code_example == "const [state, setState] = useState(null)"
        assert item.tags == ["react", "hooks", "state"]
        assert item.confidence_score == 0.9
        assert item.status == KnowledgeStatus.DEPRECATED
        assert item.source_url == "https://example.com/react"
        assert item.created_at == created_time
        assert item.updated_at == updated_time
        assert item.usage_count == 10
        assert item.user_ratings == [4.5, 5.0, 4.0]
        assert item.metadata["author"] == "test_author"

    def test_knowledge_item_post_init_string_timestamps(self):
        """Test post_init with string timestamps."""
        item = KnowledgeItem(
            id="test-3",
            category=PatternCategory.ACCESSIBILITY,
            title="Test Item",
            description="Test description",
            content="Test content",
            created_at="2023-01-01T12:00:00+00:00",
            updated_at="2023-01-02T12:00:00+00:00"
        )

        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)
        assert item.created_at.year == 2023
        assert item.created_at.month == 1
        assert item.created_at.day == 1
        assert item.updated_at.year == 2023
        assert item.updated_at.month == 1
        assert item.updated_at.day == 2

    def test_average_rating_property(self):
        """Test average rating calculation."""
        # No ratings
        item = KnowledgeItem(
            id="test-4",
            category=PatternCategory.UI_COMPONENT,
            title="Test Item",
            description="Test description",
            content="Test content",
            user_ratings=[]
        )
        assert item.average_rating == 0.0

        # With ratings
        item_with_ratings = KnowledgeItem(
            id="test-5",
            category=PatternCategory.UI_COMPONENT,
            title="Test Item",
            description="Test description",
            content="Test content",
            user_ratings=[4.0, 5.0, 3.0]
        )
        assert item_with_ratings.average_rating == 4.0

    def test_effectiveness_score_property(self):
        """Test effectiveness score calculation."""
        item = KnowledgeItem(
            id="test-6",
            category=PatternCategory.UI_COMPONENT,
            title="Test Item",
            description="Test description",
            content="Test content",
            user_ratings=[4.0, 5.0],  # Average 4.5/5 = 0.9
            usage_count=50,  # 50/100 = 0.5
            confidence_score=0.8
        )

        # rating_score = 0.9 * 0.6 = 0.54
        # usage_score = 0.5 * 0.3 = 0.15
        # confidence_score = 0.8 * 0.1 = 0.08
        # total = 0.54 + 0.15 + 0.08 = 0.77
        expected_score = 0.54 + 0.15 + 0.08
        assert abs(item.effectiveness_score - expected_score) < 0.01

    def test_effectiveness_score_no_ratings(self):
        """Test effectiveness score with no user ratings."""
        item = KnowledgeItem(
            id="test-7",
            category=PatternCategory.UI_COMPONENT,
            title="Test Item",
            description="Test description",
            content="Test content",
            user_ratings=[],
            usage_count=25,
            confidence_score=0.9
        )

        # rating_score = 0.0 * 0.6 = 0.0
        # usage_score = 0.25 * 0.3 = 0.075
        # confidence_score = 0.9 * 0.1 = 0.09
        # total = 0.0 + 0.075 + 0.09 = 0.165
        expected_score = 0.0 + 0.075 + 0.09
        assert abs(item.effectiveness_score - expected_score) < 0.01

    def test_effectiveness_score_max_usage(self):
        """Test effectiveness score with max usage count."""
        item = KnowledgeItem(
            id="test-8",
            category=PatternCategory.UI_COMPONENT,
            title="Test Item",
            description="Test description",
            content="Test content",
            user_ratings=[5.0],
            usage_count=150,  # Should be capped at 100
            confidence_score=0.7
        )

        # rating_score = 1.0 * 0.6 = 0.6
        # usage_score = 1.0 * 0.3 = 0.3 (capped)
        # confidence_score = 0.7 * 0.1 = 0.07
        # total = 0.6 + 0.3 + 0.07 = 0.97
        expected_score = 0.6 + 0.3 + 0.07
        assert abs(item.effectiveness_score - expected_score) < 0.01


class TestKnowledgeBase:
    """Test cases for KnowledgeBase."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "knowledge.db"
        self.knowledge_base = KnowledgeBase(self.db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test knowledge base initialization."""
        assert self.knowledge_base.db_path == self.db_path
        assert self.db_path.exists()

    def test_initialization_without_path(self):
        """Test knowledge base initialization without path."""
        kb = KnowledgeBase()

        # Should create default path
        assert kb.db_path is not None
        assert kb.db_path.name == "knowledge_base.db"

    def test_add_pattern(self):
        """Test adding pattern to knowledge base."""
        pattern = ExtractedPattern(
            category=PatternCategory.REACT_PATTERN,
            title="React Hook",
            description="Test React hook",
            code_example="useState(0)",
            confidence_score=0.8,
            tags=["react", "hooks"]
        )

        item_id = self.knowledge_base.add_pattern(pattern)

        assert isinstance(item_id, str)
        assert len(item_id) == 16  # SHA256 hash truncated

        # Verify item was added
        retrieved = self.knowledge_base.get_knowledge_item(item_id)
        assert retrieved is not None
        assert retrieved.title == "React Hook"
        assert retrieved.category == PatternCategory.REACT_PATTERN

    def test_add_knowledge_item(self):
        """Test adding knowledge item directly."""
        item = KnowledgeItem(
            id="test-item",
            category=PatternCategory.UI_COMPONENT,
            title="Test Component",
            description="Test component description",
            content="Test component content"
        )

        item_id = self.knowledge_base.add_knowledge_item(item)

        assert item_id == "test-item"

        # Verify item was added
        retrieved = self.knowledge_base.get_knowledge_item(item_id)
        assert retrieved is not None
        assert retrieved.title == "Test Component"

    def test_get_knowledge_item_not_found(self):
        """Test getting non-existent knowledge item."""
        result = self.knowledge_base.get_knowledge_item("nonexistent")
        assert result is None

    def test_search_knowledge(self):
        """Test searching knowledge base."""
        # Add test items
        item1 = KnowledgeItem(
            id="item-1",
            category=PatternCategory.REACT_PATTERN,
            title="React useState Hook",
            description="State management hook",
            content="React useState for state management",
            tags=["react", "hooks", "state"]
        )
        item2 = KnowledgeItem(
            id="item-2",
            category=PatternCategory.UI_COMPONENT,
            title="Button Component",
            description="Reusable button",
            content="Button component for UI",
            tags=["ui", "component", "button"]
        )

        self.knowledge_base.add_knowledge_item(item1)
        self.knowledge_base.add_knowledge_item(item2)

        # Search by query
        results = self.knowledge_base.search_knowledge("react")
        assert len(results) == 1
        assert results[0].id == "item-1"

        # Search with category filter
        results = self.knowledge_base.search_knowledge("component", PatternCategory.UI_COMPONENT)
        assert len(results) == 1
        assert results[0].id == "item-2"

    def test_search_patterns_alias(self):
        """Test search_patterns alias method."""
        item = KnowledgeItem(
            id="item-1",
            category=PatternCategory.REACT_PATTERN,
            title="React Pattern",
            description="Test pattern",
            content="Test content"
        )

        self.knowledge_base.add_knowledge_item(item)

        results = self.knowledge_base.search_patterns("react")
        assert len(results) == 1
        assert results[0].id == "item-1"

    def test_get_patterns_by_category(self):
        """Test getting patterns by category."""
        # Add items from different categories
        item1 = KnowledgeItem(
            id="item-1",
            category=PatternCategory.REACT_PATTERN,
            title="React Pattern 1",
            description="Test",
            content="Test"
        )
        item2 = KnowledgeItem(
            id="item-2",
            category=PatternCategory.REACT_PATTERN,
            title="React Pattern 2",
            description="Test",
            content="Test"
        )
        item3 = KnowledgeItem(
            id="item-3",
            category=PatternCategory.UI_COMPONENT,
            title="UI Pattern",
            description="Test",
            content="Test"
        )

        self.knowledge_base.add_knowledge_item(item1)
        self.knowledge_base.add_knowledge_item(item2)
        self.knowledge_base.add_knowledge_item(item3)

        react_patterns = self.knowledge_base.get_patterns_by_category(PatternCategory.REACT_PATTERN)
        ui_patterns = self.knowledge_base.get_patterns_by_category(PatternCategory.UI_COMPONENT)

        assert len(react_patterns) == 2
        assert len(ui_patterns) == 1
        assert all(item.category == PatternCategory.REACT_PATTERN for item in react_patterns)
        assert ui_patterns[0].category == PatternCategory.UI_COMPONENT

    def test_get_top_patterns(self):
        """Test getting top patterns by effectiveness."""
        # Add items with different effectiveness scores
        item1 = KnowledgeItem(
            id="item-1",
            category=PatternCategory.REACT_PATTERN,
            title="High Effectiveness",
            description="Test",
            content="Test",
            user_ratings=[5.0, 5.0],  # High rating
            usage_count=80
        )
        item2 = KnowledgeItem(
            id="item-2",
            category=PatternCategory.UI_COMPONENT,
            title="Low Effectiveness",
            description="Test",
            content="Test",
            user_ratings=[2.0, 3.0],  # Low rating
            usage_count=5
        )

        self.knowledge_base.add_knowledge_item(item1)
        self.knowledge_base.add_knowledge_item(item2)

        top_patterns = self.knowledge_base.get_top_patterns(limit=2)

        assert len(top_patterns) == 2
        # Should be ordered by effectiveness score (high first)
        assert top_patterns[0].id == "item-1"
        assert top_patterns[1].id == "item-2"

    def test_update_usage_count(self):
        """Test updating usage count."""
        item = KnowledgeItem(
            id="item-1",
            category=PatternCategory.REACT_PATTERN,
            title="Test Item",
            description="Test",
            content="Test",
            usage_count=5
        )

        self.knowledge_base.add_knowledge_item(item)

        # Update usage count
        self.knowledge_base.update_usage_count("item-1")

        # Verify count was incremented
        updated_item = self.knowledge_base.get_knowledge_item("item-1")
        assert updated_item.usage_count == 6

    def test_add_user_rating(self):
        """Test adding user rating."""
        item = KnowledgeItem(
            id="item-1",
            category=PatternCategory.REACT_PATTERN,
            title="Test Item",
            description="Test",
            content="Test",
            user_ratings=[4.0]
        )

        self.knowledge_base.add_knowledge_item(item)

        # Add rating
        self.knowledge_base.add_user_rating("item-1", 5.0)

        # Verify rating was added
        updated_item = self.knowledge_base.get_knowledge_item("item-1")
        assert 5.0 in updated_item.user_ratings
        assert len(updated_item.user_ratings) == 2

    def test_get_statistics(self):
        """Test getting knowledge base statistics."""
        # Add test items
        item1 = KnowledgeItem(
            id="item-1",
            category=PatternCategory.REACT_PATTERN,
            title="React Item",
            description="Test",
            content="Test",
            user_ratings=[4.0, 5.0],
            usage_count=10
        )
        item2 = KnowledgeItem(
            id="item-2",
            category=PatternCategory.UI_COMPONENT,
            title="UI Item",
            description="Test",
            content="Test",
            user_ratings=[3.0],
            usage_count=5
        )

        self.knowledge_base.add_knowledge_item(item1)
        self.knowledge_base.add_knowledge_item(item2)

        stats = self.knowledge_base.get_statistics()

        assert stats["total_items"] == 2
        assert "react_pattern" in stats["by_category"]
        assert "ui_component" in stats["by_category"]
        assert stats["by_category"]["react_pattern"] == 1
        assert stats["by_category"]["ui_component"] == 1
        assert "average_effectiveness" in stats
        assert "most_used" in stats
        assert len(stats["most_used"]) == 2

    def test_export_knowledge(self):
        """Test exporting knowledge base."""
        # Add test item
        item = KnowledgeItem(
            id="item-1",
            category=PatternCategory.REACT_PATTERN,
            title="Test Item",
            description="Test description",
            content="Test content",
            tags=["test"]
        )

        self.knowledge_base.add_knowledge_item(item)

        export_path = Path(self.temp_dir) / "export.json"
        self.knowledge_base.export_knowledge(export_path)

        assert export_path.exists()

        # Verify exported content
        with export_path.open("r") as f:
            exported_data = json.load(f)

        assert len(exported_data) == 1
        assert exported_data[0]["id"] == "item-1"
        assert exported_data[0]["title"] == "Test Item"

    def test_import_knowledge(self):
        """Test importing knowledge from file."""
        # Create import data
        import_data = [
            {
                "id": "imported-1",
                "category": "react_pattern",
                "title": "Imported Item",
                "description": "Imported description",
                "content": "Imported content",
                "tags": ["imported"],
                "confidence_score": 0.8,
                "usage_count": 5,
                "user_ratings": [4.0, 5.0],
                "metadata": {"imported": True}
            }
        ]

        import_path = Path(self.temp_dir) / "import.json"
        with import_path.open("w") as f:
            json.dump(import_data, f)

        # Import knowledge
        imported_count = self.knowledge_base.import_knowledge(import_path)

        assert imported_count == 1

        # Verify imported item
        imported_item = self.knowledge_base.get_knowledge_item("imported-1")
        assert imported_item is not None
        assert imported_item.title == "Imported Item"
        assert imported_item.category == PatternCategory.REACT_PATTERN

    def test_import_knowledge_with_invalid_data(self):
        """Test importing knowledge with invalid data."""
        # Create import data with invalid item
        import_data = [
            {
                "id": "invalid-1",
                "category": "invalid_category",  # Invalid category
                "title": "Invalid Item",
                "description": "Invalid description",
                "content": "Invalid content"
            },
            {
                "id": "valid-1",
                "category": "react_pattern",
                "title": "Valid Item",
                "description": "Valid description",
                "content": "Valid content"
            }
        ]

        import_path = Path(self.temp_dir) / "import.json"
        with import_path.open("w") as f:
            json.dump(import_data, f)

        # Import knowledge (should skip invalid item)
        imported_count = self.knowledge_base.import_knowledge(import_path)

        assert imported_count == 1  # Only valid item imported

        # Verify valid item was imported
        valid_item = self.knowledge_base.get_knowledge_item("valid-1")
        assert valid_item is not None
        assert valid_item.title == "Valid Item"
        assert valid_item.category == PatternCategory.REACT_PATTERN

    def test_generate_item_id(self):
        """Test item ID generation."""
        pattern = ExtractedPattern(
            category=PatternCategory.REACT_PATTERN,
            title="React Hook",
            description="State management hook",
            confidence_score=0.8
        )

        item_id = self.knowledge_base._generate_item_id(pattern)

        assert isinstance(item_id, str)
        assert len(item_id) == 16  # SHA256 hash truncated

        # Same pattern should generate same ID
        item_id2 = self.knowledge_base._generate_item_id(pattern)
        assert item_id == item_id2

    def test_row_to_knowledge_item(self):
        """Test converting database row to KnowledgeItem."""
        # Mock database row
        row = (
            "test-id",  # id
            "react_pattern",  # category
            "Test Title",  # title
            "Test Description",  # description
            "Test Content",  # content
            "const [state, setState] = useState(null)",  # code_example
            '["react", "hooks"]',  # tags (JSON)
            0.9,  # confidence_score
            "active",  # status
            "https://example.com",  # source_url
            "2023-01-01T12:00:00+00:00",  # created_at
            "2023-01-02T12:00:00+00:00",  # updated_at
            10,  # usage_count
            '[4.0, 5.0]',  # user_ratings (JSON)
            '{"key": "value"}'  # metadata (JSON)
        )

        item = self.knowledge_base._row_to_knowledge_item(row)

        assert item.id == "test-id"
        assert item.category == PatternCategory.REACT_PATTERN
        assert item.title == "Test Title"
        assert item.description == "Test Description"
        assert item.content == "Test Content"
        assert item.code_example == "const [state, setState] = useState(null)"
        assert item.tags == ["react", "hooks"]
        assert item.confidence_score == 0.9
        assert item.status == KnowledgeStatus.ACTIVE
        assert item.source_url == "https://example.com"
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)
        assert item.usage_count == 10
        assert item.user_ratings == [4.0, 5.0]
        assert item.metadata == {"key": "value"}


class TestKnowledgeIndexer:
    """Test cases for KnowledgeIndexer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "knowledge.db"
        self.knowledge_base = KnowledgeBase(self.db_path)

        # Add test items
        self.item1 = KnowledgeItem(
            id="item-1",
            category=PatternCategory.REACT_PATTERN,
            title="React Hook Pattern",
            description="State management hook",
            content="React useState for state management",
            tags=["react", "hooks", "state"]
        )
        self.item2 = KnowledgeItem(
            id="item-2",
            category=PatternCategory.UI_COMPONENT,
            title="Button Component",
            description="Reusable button",
            content="Button component for UI",
            tags=["ui", "component", "button"]
        )

        self.knowledge_base.add_knowledge_item(self.item1)
        self.knowledge_base.add_knowledge_item(self.item2)

        self.indexer = KnowledgeIndexer(self.knowledge_base)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test indexer initialization."""
        assert self.indexer.knowledge_base == self.knowledge_base
        assert isinstance(self.indexer.tag_index, dict)
        assert isinstance(self.indexer.category_index, dict)
        assert isinstance(self.indexer.keyword_index, dict)

    def test_build_indexes(self):
        """Test building indexes."""
        # Indexer should build indexes during initialization
        assert len(self.indexer.category_index) > 0
        assert len(self.indexer.tag_index) > 0
        assert len(self.indexer.keyword_index) > 0

        # Check that our test items were indexed
        assert PatternCategory.REACT_PATTERN in self.indexer.category_index
        assert "item-1" in self.indexer.category_index[PatternCategory.REACT_PATTERN]
        assert "react" in self.indexer.tag_index
        assert "item-1" in self.indexer.tag_index["react"]

    def test_find_by_tags(self):
        """Test finding items by tags."""
        # Find by single tag
        results = self.indexer.find_by_tags(["react"])
        assert "item-1" in results

        # Find by multiple tags
        results = self.indexer.find_by_tags(["react", "ui"])
        assert "item-1" in results
        assert "item-2" in results

        # Find by non-existent tag
        results = self.indexer.find_by_tags(["nonexistent"])
        assert len(results) == 0

    def test_find_by_category(self):
        """Test finding items by category."""
        results = self.indexer.find_by_category(PatternCategory.REACT_PATTERN)
        assert "item-1" in results

        results = self.indexer.find_by_category(PatternCategory.UI_COMPONENT)
        assert "item-2" in results

        results = self.indexer.find_by_category(PatternCategory.ACCESSIBILITY)
        assert len(results) == 0

    def test_find_by_keywords(self):
        """Test finding items by keywords."""
        # Find by single keyword
        results = self.indexer.find_by_keywords(["hook"])
        assert "item-1" in results

        # Find by multiple keywords
        results = self.indexer.find_by_keywords(["react", "button"])
        assert "item-1" in results
        assert "item-2" in results

        # Find by non-existent keyword
        results = self.indexer.find_by_keywords(["nonexistent"])
        assert len(results) == 0

    def test_get_related_items(self):
        """Test getting related items."""
        related = self.indexer.get_related_items("item-1")

        # Should find item-2 (shares no tags, but this is expected behavior)
        assert isinstance(related, list)

        # Test with non-existent item
        related = self.indexer.get_related_items("nonexistent")
        assert related == []

    def test_get_related_items_with_shared_tags(self):
        """Test getting related items with shared tags."""
        # Add item with shared tags
        item3 = KnowledgeItem(
            id="item-3",
            category=PatternCategory.REACT_PATTERN,
            title="Another React Pattern",
            description="Another React pattern",
            content="React content",
            tags=["react", "hooks"]  # Shares tags with item-1
        )

        self.knowledge_base.add_knowledge_item(item3)

        # Rebuild indexer to include new item
        self.indexer = KnowledgeIndexer(self.knowledge_base)

        related = self.indexer.get_related_items("item-1")

        # Should find item-3 (shares tags)
        assert "item-3" in related

    def test_get_related_items_empty_result(self):
        """Test getting related items with no shared tags."""
        # Item with no tags
        item4 = KnowledgeItem(
            id="item-4",
            category=PatternCategory.ACCESSIBILITY,
            title="Accessibility Pattern",
            description="Test accessibility",
            content="Test content",
            tags=[]
        )

        self.knowledge_base.add_knowledge_item(item4)

        related = self.indexer.get_related_items("item-4")
        assert related == []


class TestKnowledgeBaseIntegration:
    """Integration tests for knowledge base system."""

    def test_end_to_end_workflow(self):
        """Test end-to-end knowledge base workflow."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "knowledge.db"

        try:
            # Create knowledge base
            kb = KnowledgeBase(db_path)

            # Add patterns
            patterns = [
                ExtractedPattern(
                    category=PatternCategory.REACT_PATTERN,
                    title="React useState Hook",
                    description="State management hook",
                    code_example="useState(0)",
                    confidence_score=0.8,
                    tags=["react", "hooks", "state"]
                ),
                ExtractedPattern(
                    category=PatternCategory.UI_COMPONENT,
                    title="Button Component",
                    description="Reusable button component",
                    code_example="<button>Click</button>",
                    confidence_score=0.9,
                    tags=["ui", "component", "button"]
                )
            ]

            item_ids = []
            for pattern in patterns:
                item_id = kb.add_pattern(pattern)
                item_ids.append(item_id)

            # Search knowledge base
            react_results = kb.search_knowledge("react")
            ui_results = kb.search_knowledge("button")

            assert len(react_results) == 1
            assert len(ui_results) == 1

            # Get statistics
            stats = kb.get_statistics()
            assert stats["total_items"] == 2
            assert "react_pattern" in stats["by_category"]
            assert "ui_component" in stats["by_category"]

            # Create indexer
            indexer = KnowledgeIndexer(kb)

            # Test indexer functionality
            react_items = indexer.find_by_category(PatternCategory.REACT_PATTERN)
            assert len(react_items) == 1

            # Export and import
            export_path = Path(temp_dir) / "export.json"
            kb.export_knowledge(export_path)

            # Clear and re-import
            new_kb = KnowledgeBase(db_path)
            imported_count = new_kb.import_knowledge(export_path)

            assert imported_count == 2

            # Verify data integrity
            for item_id in item_ids:
                item = new_kb.get_knowledge_item(item_id)
                assert item is not None

        finally:
            import shutil
            shutil.rmtree(temp_dir)

    def test_concurrent_access_simulation(self):
        """Test concurrent access simulation."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "knowledge.db"

        try:
            kb = KnowledgeBase(db_path)

            # Add multiple items
            for i in range(10):
                item = KnowledgeItem(
                    id=f"item-{i}",
                    category=PatternCategory.REACT_PATTERN,
                    title=f"React Pattern {i}",
                    description=f"Test pattern {i}",
                    content=f"Test content {i}"
                )
                kb.add_knowledge_item(item)

            # Simulate concurrent searches
            search_results_1 = kb.search_knowledge("react")
            search_results_2 = kb.search_knowledge("pattern")

            # Results should be consistent
            assert len(search_results_1) == 10
            assert len(search_results_2) == 10

            # Update usage counts
            for i in range(5):
                kb.update_usage_count(f"item-{i}")

            # Verify updates
            updated_item = kb.get_knowledge_item("item-0")
            assert updated_item.usage_count == 6

        finally:
            import shutil
            shutil.rmtree(temp_dir)

    def test_large_dataset_performance(self):
        """Test performance with large dataset."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "knowledge.db"

        try:
            kb = KnowledgeBase(db_path)

            # Add many items
            start_time = datetime.now()
            for i in range(100):
                item = KnowledgeItem(
                    id=f"item-{i}",
                    category=PatternCategory.REACT_PATTERN,
                    title=f"React Pattern {i}",
                    description=f"Test pattern {i}",
                    content=f"Test content {i}",
                    tags=[f"tag-{j}" for j in range(3)]
                )
                kb.add_knowledge_item(item)

            add_time = (datetime.now() - start_time).total_seconds()

            # Should complete reasonably quickly
            assert add_time < 5.0  # 5 seconds max for 100 items

            # Test search performance
            start_time = datetime.now()
            results = kb.search_knowledge("react", limit=50)
            search_time = (datetime.now() - start_time).total_seconds()

            assert search_time < 1.0  # 1 second max for search
            assert len(results) == 50

            # Test statistics performance
            start_time = datetime.now()
            stats = kb.get_statistics()
            stats_time = (datetime.now() - start_time).total_seconds()

            assert stats_time < 0.5  # 0.5 seconds max for statistics
            assert stats["total_items"] == 100

        finally:
            import shutil
            shutil.rmtree(temp_dir)


class TestDefaultTrainingSources:
    """Test default training sources configuration."""

    def test_default_training_sources_structure(self):
        """Test that default training sources have required structure."""
        from tool_router.training.training_pipeline import DEFAULT_TRAINING_SOURCES

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
        from tool_router.training.training_pipeline import DEFAULT_TRAINING_SOURCES

        categories = {source["category"] for source in DEFAULT_TRAINING_SOURCES}

        expected_categories = [
            "react_patterns",
            "design_systems",
            "accessibility",
            "prompt_engineering"
        ]

        for category in expected_categories:
            assert category in categories, f"Missing category: {category}"

    def test_default_training_sources_urls(self):
        """Test that default source URLs are valid."""
        for source in DEFAULT_TRAINING_SOURCES:
            url = source["url"]
            assert url.startswith("https://")
            assert "." in url  # Domain name present
