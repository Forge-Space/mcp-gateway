"""Unit tests for tool_router/mcp_tools/knowledge_base_tool.py module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tool_router.mcp_tools.knowledge_base_tool import KNOWLEDGE_BASE_SCHEMA, KnowledgeBaseTool, knowledge_base_handler
from tool_router.training.knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeStatus, PatternCategory


class TestKnowledgeBaseTool:
    """Test cases for KnowledgeBaseTool."""

    def test_initialization(self) -> None:
        """Test KnowledgeBaseTool initialization."""
        tool = KnowledgeBaseTool()

        # Business logic: tool should initialize with knowledge base
        assert tool.knowledge_base is not None
        assert isinstance(tool.knowledge_base, KnowledgeBase)

    def test_add_pattern_success(self) -> None:
        """Test successful pattern addition."""
        tool = KnowledgeBaseTool()

        with patch.object(tool.knowledge_base, "add_knowledge_item") as mock_add:
            mock_add.return_value = "test_id_123"

            result = tool.add_pattern(
                title="Test Pattern",
                description="Test description",
                category="react_patterns",
                content="Test content",
                confidence=0.9,
                effectiveness=0.8,
                metadata={"source": "test"},
            )

        # Business logic: successful addition should return success response
        assert result["item_id"] == "test_id_123"
        assert result["title"] == "Test Pattern"
        assert result["category"] == "react_patterns"
        assert result["confidence"] == 0.9
        assert result["effectiveness"] == 0.8
        assert result["message"] == "Pattern added successfully"
        assert "error" not in result

    def test_add_pattern_invalid_category(self) -> None:
        """Test pattern addition with invalid category."""
        tool = KnowledgeBaseTool()

        result = tool.add_pattern(
            title="Test Pattern", description="Test description", category="invalid_category", content="Test content"
        )

        # Business logic: invalid category should return error with valid categories
        assert "error" in result
        assert "Invalid category" in result["error"]
        assert "Valid categories" in result["message"]
        assert all(cat.value in result["message"] for cat in PatternCategory)

    def test_add_pattern_database_error(self) -> None:
        """Test pattern addition with database error."""
        tool = KnowledgeBaseTool()

        with patch.object(tool.knowledge_base, "add_knowledge_item") as mock_add:
            mock_add.side_effect = Exception("Database connection failed")

            result = tool.add_pattern(
                title="Test Pattern", description="Test description", category="react_patterns", content="Test content"
            )

        # Business logic: database errors should be caught and reported
        assert "error" in result
        assert "Database connection failed" in result["error"]
        assert "Failed to add pattern" in result["message"]

    def test_add_pattern_id_generation(self) -> None:
        """Test that unique IDs are generated for patterns."""
        tool = KnowledgeBaseTool()

        with patch.object(tool.knowledge_base, "add_knowledge_item") as mock_add:
            mock_add.return_value = "generated_id"

            result = tool.add_pattern(
                title="Test Pattern", description="Test description", category="react_patterns", content="Test content"
            )

        # Business logic: ID should be generated consistently
        mock_add.assert_called_once()
        call_args = mock_add.call_args[0][0]  # First argument (KnowledgeItem)
        assert call_args.id is not None
        assert len(call_args.id) == 16  # MD5 hash truncated to 16 chars
        assert call_args.title == "Test Pattern"
        assert call_args.description == "Test description"
        assert call_args.category == PatternCategory.REACT_PATTERNS
        assert call_args.content == "Test content"
        assert call_args.confidence_score == 0.8  # Default value

    def test_search_patterns_success(self) -> None:
        """Test successful pattern search."""
        tool = KnowledgeBaseTool()

        # Mock knowledge items
        mock_item1 = MagicMock(spec=KnowledgeItem)
        mock_item1.id = "item1"
        mock_item1.title = "React Hook Pattern"
        mock_item1.description = "Use hooks for state management"
        mock_item1.category = PatternCategory.REACT_PATTERNS
        mock_item1.confidence_score = 0.9
        mock_item1.effectiveness_score = 0.85
        mock_item1.created_at = "2024-01-01T00:00:00"
        mock_item1.usage_count = 5

        mock_item2 = MagicMock(spec=KnowledgeItem)
        mock_item2.id = "item2"
        mock_item2.title = "Component Pattern"
        mock_item2.description = "Reusable component design"
        mock_item2.category = PatternCategory.REACT_PATTERNS
        mock_item2.confidence_score = 0.7
        mock_item2.effectiveness_score = 0.8
        mock_item2.created_at = "2024-01-02T00:00:00"
        mock_item2.usage_count = 3

        with patch.object(tool.knowledge_base, "search_knowledge") as mock_search:
            mock_search.return_value = [mock_item1, mock_item2]

            result = tool.search_patterns(query="react hooks", category="react_patterns", limit=10, min_confidence=0.8)

        # Business logic: search should return formatted results
        assert result["total_found"] == 1  # Only item1 meets confidence threshold
        assert result["query"] == "react hooks"
        assert result["category"] == "react_patterns"
        assert len(result["results"]) == 1

        found_item = result["results"][0]
        assert found_item["id"] == "item1"
        assert found_item["title"] == "React Hook Pattern"
        assert found_item["confidence"] == 0.9
        assert found_item["effectiveness"] == 0.85

    def test_search_patterns_invalid_category(self) -> None:
        """Test pattern search with invalid category."""
        tool = KnowledgeBaseTool()

        result = tool.search_patterns(query="test", category="invalid_category")

        # Business logic: invalid category should return error
        assert "error" in result
        assert "Invalid category" in result["error"]
        assert "Valid categories" in result["message"]

    def test_search_patterns_confidence_filtering(self) -> None:
        """Test pattern search with confidence filtering."""
        tool = KnowledgeBaseTool()

        # Mock items with different confidence scores
        low_confidence_item = MagicMock(spec=KnowledgeItem)
        low_confidence_item.confidence_score = 0.5

        high_confidence_item = MagicMock(spec=KnowledgeItem)
        high_confidence_item.confidence_score = 0.9

        with patch.object(tool.knowledge_base, "search_knowledge") as mock_search:
            mock_search.return_value = [low_confidence_item, high_confidence_item]

            result = tool.search_patterns(query="test", min_confidence=0.8)

        # Business logic: should filter by confidence threshold
        assert result["total_found"] == 1  # Only high confidence item
        mock_search.assert_called_once_with(query="test", category=None, limit=10)

    def test_get_pattern_success(self) -> None:
        """Test successful pattern retrieval."""
        tool = KnowledgeBaseTool()

        mock_item = MagicMock(spec=KnowledgeItem)
        mock_item.id = "item123"
        mock_item.title = "Test Pattern"
        mock_item.description = "Test description"
        mock_item.category = PatternCategory.REACT_PATTERNS
        mock_item.content = "Test content"
        mock_item.confidence_score = 0.9
        mock_item.effectiveness_score = 0.85
        mock_item.status = KnowledgeStatus.ACTIVE
        mock_item.created_at = "2024-01-01T00:00:00"
        mock_item.updated_at = "2024-01-01T00:00:00"
        mock_item.usage_count = 5
        mock_item.metadata = {"source": "test"}

        with patch.object(tool.knowledge_base, "get_knowledge_item") as mock_get:
            mock_get.return_value = mock_item

            result = tool.get_pattern("item123")

        # Business logic: should return complete pattern details
        assert result["id"] == "item123"
        assert result["title"] == "Test Pattern"
        assert result["category"] == "react_patterns"
        assert result["confidence"] == 0.9
        assert result["effectiveness"] == 0.85
        assert result["status"] == "active"
        assert result["message"] == "Pattern retrieved successfully"

    def test_get_pattern_not_found(self) -> None:
        """Test pattern retrieval for non-existent pattern."""
        tool = KnowledgeBaseTool()

        with patch.object(tool.knowledge_base, "get_knowledge_item") as mock_get:
            mock_get.return_value = None

            result = tool.get_pattern("nonexistent")

        # Business logic: non-existent pattern should return error
        assert "error" in result
        assert "Pattern with ID nonexistent not found" in result["error"]
        assert "Invalid pattern ID" in result["message"]

    def test_update_pattern_success(self) -> None:
        """Test successful pattern update."""
        tool = KnowledgeBaseTool()

        mock_item = MagicMock(spec=KnowledgeItem)
        mock_item.id = "item123"

        with (
            patch.object(tool.knowledge_base, "get_knowledge_item") as mock_get,
            patch.object(tool.knowledge_base, "update_knowledge") as mock_update,
        ):
            mock_get.return_value = mock_item
            mock_update.return_value = True

            result = tool.update_pattern(item_id="item123", title="Updated Title", confidence=0.95)

        # Business logic: successful update should return confirmation
        assert result["item_id"] == "item123"
        assert "title" in result["updated_fields"]
        assert "confidence" in result["updated_fields"]
        assert result["message"] == "Pattern updated successfully"

        # Verify correct update data passed
        mock_update.assert_called_once_with("item123", {"title": "Updated Title", "confidence": 0.95})

    def test_update_pattern_not_found(self) -> None:
        """Test pattern update for non-existent pattern."""
        tool = KnowledgeBaseTool()

        with patch.object(tool.knowledge_base, "get_knowledge_item") as mock_get:
            mock_get.return_value = None

            result = tool.update_pattern(item_id="nonexistent", title="Updated Title")

        # Business logic: non-existent pattern should return error
        assert "error" in result
        assert "Pattern with ID nonexistent not found" in result["error"]

    def test_update_pattern_update_failure(self) -> None:
        """Test pattern update when database update fails."""
        tool = KnowledgeBaseTool()

        mock_item = MagicMock(spec=KnowledgeItem)
        mock_item.id = "item123"

        with (
            patch.object(tool.knowledge_base, "get_knowledge_item") as mock_get,
            patch.object(tool.knowledge_base, "update_knowledge") as mock_update,
        ):
            mock_get.return_value = mock_item
            mock_update.return_value = False

            result = tool.update_pattern(item_id="item123", title="Updated Title")

        # Business logic: update failure should return error
        assert "error" in result
        assert "Update failed" in result["error"]
        assert "Failed to update pattern" in result["message"]

    def test_delete_pattern_success(self) -> None:
        """Test successful pattern deletion."""
        tool = KnowledgeBaseTool()

        mock_item = MagicMock(spec=KnowledgeItem)
        mock_item.id = "item123"
        mock_item.title = "Test Pattern"

        with (
            patch.object(tool.knowledge_base, "get_knowledge_item") as mock_get,
            patch.object(tool.knowledge_base, "delete_knowledge") as mock_delete,
        ):
            mock_get.return_value = mock_item
            mock_delete.return_value = True

            result = tool.delete_pattern("item123")

        # Business logic: successful deletion should return confirmation
        assert result["item_id"] == "item123"
        assert result["title"] == "Test Pattern"
        assert result["message"] == "Pattern deleted successfully"
        mock_delete.assert_called_once_with("item123")

    def test_delete_pattern_not_found(self) -> None:
        """Test pattern deletion for non-existent pattern."""
        tool = KnowledgeBaseTool()

        with patch.object(tool.knowledge_base, "get_knowledge_item") as mock_get:
            mock_get.return_value = None

            result = tool.delete_pattern("nonexistent")

        # Business logic: non-existent pattern should return error
        assert "error" in result
        assert "Pattern with ID nonexistent not found" in result["error"]

    def test_get_patterns_by_category_success(self) -> None:
        """Test successful category-based pattern retrieval."""
        tool = KnowledgeBaseTool()

        mock_item = MagicMock(spec=KnowledgeItem)
        mock_item.id = "item1"
        mock_item.title = "React Pattern"
        mock_item.description = "A React pattern"
        mock_item.confidence_score = 0.9
        mock_item.effectiveness_score = 0.85
        mock_item.created_at = "2024-01-01T00:00:00"
        mock_item.usage_count = 5

        with patch.object(tool.knowledge_base, "get_patterns_by_category") as mock_get:
            mock_get.return_value = [mock_item]

            result = tool.get_patterns_by_category(category="react_patterns", limit=20)

        # Business logic: should return formatted patterns for category
        assert result["category"] == "react_patterns"
        assert result["total_found"] == 1
        assert len(result["patterns"]) == 1

        pattern = result["patterns"][0]
        assert pattern["id"] == "item1"
        assert pattern["title"] == "React Pattern"
        assert pattern["confidence"] == 0.9
        assert pattern["effectiveness"] == 0.85

        mock_get.assert_called_once_with(PatternCategory.REACT_PATTERNS, 20)

    def test_get_patterns_by_category_invalid_category(self) -> None:
        """Test category-based retrieval with invalid category."""
        tool = KnowledgeBaseTool()

        result = tool.get_patterns_by_category("invalid_category")

        # Business logic: invalid category should return error
        assert "error" in result
        assert "Invalid category" in result["error"]

    def test_get_knowledge_base_statistics_success(self) -> None:
        """Test successful statistics retrieval."""
        tool = KnowledgeBaseTool()

        mock_stats = {
            "total_items": 100,
            "by_category": {"react_patterns": 50, "accessibility": 30},
            "average_effectiveness": 0.85,
        }

        with patch.object(tool.knowledge_base, "get_statistics") as mock_get:
            mock_get.return_value = mock_stats

            result = tool.get_knowledge_base_statistics()

        # Business logic: should return statistics from knowledge base
        assert result["statistics"] == mock_stats
        assert result["message"] == "Knowledge base statistics retrieved successfully"

    def test_get_categories_success(self) -> None:
        """Test successful categories retrieval."""
        tool = KnowledgeBaseTool()

        result = tool.get_categories()

        # Business logic: should return all available categories
        assert "categories" in result
        assert result["total_categories"] == len(PatternCategory)

        categories = result["categories"]
        for category in PatternCategory:
            category_data = next(cat for cat in categories if cat["value"] == category.value)
            assert category_data["name"] == category.value.replace("_", " ").title()

        assert result["message"] == "Categories retrieved successfully"

    def test_get_categories_error(self) -> None:
        """Test categories retrieval with error."""
        tool = KnowledgeBaseTool()

        with patch.object(PatternCategory, "__iter__") as mock_iter:
            mock_iter.side_effect = Exception("Enumeration failed")

            result = tool.get_categories()

        # Business logic: errors should be caught and reported
        assert "error" in result
        assert "Enumeration failed" in result["error"]
        assert "Failed to get categories" in result["message"]


class TestKnowledgeBaseSchema:
    """Test cases for KNOWLEDGE_BASE_SCHEMA."""

    def test_schema_structure(self) -> None:
        """Test that schema has correct structure."""
        assert KNOWLEDGE_BASE_SCHEMA["type"] == "object"
        assert "properties" in KNOWLEDGE_BASE_SCHEMA
        assert "action" in KNOWLEDGE_BASE_SCHEMA["properties"]

        # Business logic: action should be required
        assert "action" in KNOWLEDGE_BASE_SCHEMA.get("required", [])

    def test_schema_actions(self) -> None:
        """Test that all valid actions are in schema."""
        actions = KNOWLEDGE_BASE_SCHEMA["properties"]["action"]["enum"]
        expected_actions = [
            "add_pattern",
            "search_patterns",
            "get_pattern",
            "update_pattern",
            "delete_pattern",
            "get_patterns_by_category",
            "get_statistics",
            "get_categories",
        ]

        # Business logic: all expected actions should be present
        for action in expected_actions:
            assert action in actions

    def test_schema_field_validation(self) -> None:
        """Test schema field validation rules."""
        properties = KNOWLEDGE_BASE_SCHEMA["properties"]

        # Business logic: confidence and effectiveness should be bounded
        if "confidence" in properties:
            assert properties["confidence"]["minimum"] == 0
            assert properties["confidence"]["maximum"] == 1

        if "effectiveness" in properties:
            assert properties["effectiveness"]["minimum"] == 0
            assert properties["effectiveness"]["maximum"] == 1

        # Business logic: limit should have reasonable bounds
        if "limit" in properties:
            assert properties["limit"]["minimum"] == 1
            assert properties["limit"]["maximum"] == 100


class TestKnowledgeBaseHandler:
    """Test cases for knowledge_base_handler function."""

    def test_handler_add_pattern_success(self) -> None:
        """Test handler with successful add_pattern action."""
        args = {
            "action": "add_pattern",
            "title": "Test Pattern",
            "description": "Test description",
            "category": "react_patterns",
            "content": "Test content",
        }

        with patch.object(KnowledgeBaseTool, "add_pattern") as mock_add:
            mock_add.return_value = {"message": "Pattern added successfully"}

            result = knowledge_base_handler(args)

        # Business logic: handler should call appropriate method
        mock_add.assert_called_once()
        assert result["message"] == "Pattern added successfully"

    def test_handler_add_pattern_missing_fields(self) -> None:
        """Test handler with missing required fields for add_pattern."""
        args = {
            "action": "add_pattern",
            "title": "Test Pattern",
            # Missing description, category, content
        }

        result = knowledge_base_handler(args)

        # Business logic: missing required fields should return error
        assert "error" in result
        assert "Missing required field" in result["error"]

    def test_handler_search_patterns_success(self) -> None:
        """Test handler with successful search_patterns action."""
        args = {"action": "search_patterns", "query": "react hooks"}

        with patch.object(KnowledgeBaseTool, "search_patterns") as mock_search:
            mock_search.return_value = {"results": [], "total_found": 0}

            result = knowledge_base_handler(args)

        # Business logic: handler should call search with query
        mock_search.assert_called_once_with(query="react hooks", category=None, limit=10, min_confidence=None)

    def test_handler_search_patterns_missing_query(self) -> None:
        """Test handler with missing query for search_patterns."""
        args = {
            "action": "search_patterns"
            # Missing query
        }

        result = knowledge_base_handler(args)

        # Business logic: missing query should return error
        assert "error" in result
        assert "Missing required field: query" in result["error"]

    def test_handler_get_pattern_success(self) -> None:
        """Test handler with successful get_pattern action."""
        args = {"action": "get_pattern", "item_id": 123}

        with patch.object(KnowledgeBaseTool, "get_pattern") as mock_get:
            mock_get.return_value = {"id": 123, "title": "Test"}

            result = knowledge_base_handler(args)

        # Business logic: handler should call get with item_id
        mock_get.assert_called_once_with(123)

    def test_handler_get_pattern_missing_id(self) -> None:
        """Test handler with missing item_id for get_pattern."""
        args = {
            "action": "get_pattern"
            # Missing item_id
        }

        result = knowledge_base_handler(args)

        # Business logic: missing item_id should return error
        assert "error" in result
        assert "Missing required field: item_id" in result["error"]

    def test_handler_unknown_action(self) -> None:
        """Test handler with unknown action."""
        args = {"action": "unknown_action"}

        result = knowledge_base_handler(args)

        # Business logic: unknown action should return error
        assert "error" in result
        assert "Unknown action" in result["error"]
        assert "Invalid action specified" in result["message"]

    def test_handler_exception_handling(self) -> None:
        """Test handler exception handling."""
        args = {"action": "get_categories"}

        with patch.object(KnowledgeBaseTool, "get_categories") as mock_get:
            mock_get.side_effect = Exception("Tool initialization failed")

            result = knowledge_base_handler(args)

        # Business logic: exceptions should be caught and reported
        assert "error" in result
        assert "Tool initialization failed" in result["error"]
        assert "Knowledge base operation failed" in result["message"]

    def test_handler_default_values(self) -> None:
        """Test handler uses default values correctly."""
        args = {"action": "search_patterns", "query": "test"}

        with patch.object(KnowledgeBaseTool, "search_patterns") as mock_search:
            mock_search.return_value = {"results": []}

            result = knowledge_base_handler(args)

        # Business logic: default values should be applied
        mock_search.assert_called_once_with(
            query="test",
            category=None,
            limit=10,  # Default limit
            min_confidence=None,
        )

    def test_handler_update_pattern_partial_update(self) -> None:
        """Test handler with partial pattern update."""
        args = {
            "action": "update_pattern",
            "item_id": 123,
            "title": "New Title",
            # Only updating title, not other fields
        }

        with patch.object(KnowledgeBaseTool, "update_pattern") as mock_update:
            mock_update.return_value = {"message": "Updated successfully"}

            result = knowledge_base_handler(args)

        # Business logic: only provided fields should be updated
        mock_update.assert_called_once_with(
            item_id=123,
            title="New Title",
            description=None,
            content=None,
            confidence=None,
            effectiveness=None,
            metadata=None,
        )
