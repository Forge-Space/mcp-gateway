"""Knowledge Base MCP Tool.

Provides MCP server tool functionality for managing the specialist AI knowledge base,
including adding patterns, searching, and managing knowledge items.
"""

from __future__ import annotations

import logging
from typing import Any

from ..training.knowledge_base import KnowledgeBase, KnowledgeItem, PatternCategory


logger = logging.getLogger(__name__)


class KnowledgeBaseTool:
    """MCP tool for managing specialist AI knowledge base operations."""

    def __init__(self) -> None:
        """Initialize the knowledge base tool."""
        self.knowledge_base = KnowledgeBase()

    def add_pattern(
        self,
        title: str,
        description: str,
        category: str,
        content: str,
        confidence: float = 0.8,
        effectiveness: float = 0.8,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a new pattern to the knowledge base.

        Args:
            title: Pattern title
            description: Pattern description
            category: Pattern category
            content: Pattern content
            confidence: Confidence score (0-1)
            effectiveness: Effectiveness score (0-1)
            metadata: Additional metadata

        Returns:
            Result of adding the pattern
        """
        try:
            # Convert category string to enum
            try:
                pattern_category = PatternCategory(category.lower())
            except ValueError:
                return {
                    "error": f"Invalid category: {category}",
                    "message": f"Valid categories: {[c.value for c in PatternCategory]}",
                }

            # Create knowledge item
            knowledge_item = KnowledgeItem(
                title=title,
                description=description,
                category=pattern_category,
                content=content,
                confidence=confidence,
                effectiveness=effectiveness,
                metadata=metadata or {},
            )

            # Add to knowledge base
            item_id = self.knowledge_base.add_knowledge(knowledge_item)

            logger.info(f"Added pattern '{title}' with ID {item_id}")

            return {
                "item_id": item_id,
                "title": title,
                "category": category,
                "confidence": confidence,
                "effectiveness": effectiveness,
                "message": "Pattern added successfully",
            }

        except Exception as e:
            logger.error(f"Error adding pattern: {e}")
            return {"error": str(e), "message": "Failed to add pattern"}

    def search_patterns(
        self,
        query: str,
        category: str | None = None,
        limit: int = 10,
        min_confidence: float | None = None,
    ) -> dict[str, Any]:
        """Search for patterns in the knowledge base.

        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum number of results
            min_confidence: Minimum confidence score

        Returns:
            Search results
        """
        try:
            # Convert category if provided
            pattern_category = None
            if category:
                try:
                    pattern_category = PatternCategory(category.lower())
                except ValueError:
                    return {
                        "error": f"Invalid category: {category}",
                        "message": f"Valid categories: {[c.value for c in PatternCategory]}",
                    }

            # Search knowledge base
            results = self.knowledge_base.search_knowledge(query=query, category=pattern_category, limit=limit)

            # Filter by confidence if specified
            if min_confidence is not None:
                results = [item for item in results if item.confidence >= min_confidence]

            # Format results
            formatted_results = []
            for item in results:
                formatted_results.append(
                    {
                        "id": item.id,
                        "title": item.title,
                        "description": (
                            item.description[:100] + "..." if len(item.description) > 100 else item.description
                        ),
                        "category": item.category.value,
                        "confidence": item.confidence,
                        "effectiveness": item.effectiveness,
                        "created_at": item.created_at,
                        "usage_count": item.usage_count,
                    }
                )

            return {
                "results": formatted_results,
                "total_found": len(formatted_results),
                "query": query,
                "category": category,
                "message": f"Found {len(formatted_results)} patterns",
            }

        except Exception as e:
            logger.error(f"Error searching patterns: {e}")
            return {"error": str(e), "message": "Failed to search patterns"}

    def get_pattern(self, item_id: int) -> dict[str, Any]:
        """Get a specific pattern by ID.

        Args:
            item_id: ID of the pattern

        Returns:
            Pattern details
        """
        try:
            item = self.knowledge_base.get_knowledge_by_id(item_id)

            if not item:
                return {
                    "error": f"Pattern with ID {item_id} not found",
                    "message": "Invalid pattern ID",
                }

            return {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "category": item.category.value,
                "content": item.content,
                "confidence": item.confidence,
                "effectiveness": item.effectiveness,
                "status": item.status.value,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "usage_count": item.usage_count,
                "metadata": item.metadata,
                "message": "Pattern retrieved successfully",
            }

        except Exception as e:
            logger.error(f"Error getting pattern: {e}")
            return {"error": str(e), "message": "Failed to get pattern"}

    def update_pattern(
        self,
        item_id: int,
        title: str | None = None,
        description: str | None = None,
        content: str | None = None,
        confidence: float | None = None,
        effectiveness: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update an existing pattern.

        Args:
            item_id: ID of the pattern to update
            title: New title (optional)
            description: New description (optional)
            content: New content (optional)
            confidence: New confidence score (optional)
            effectiveness: New effectiveness score (optional)
            metadata: New metadata (optional)

        Returns:
            Update result
        """
        try:
            # Get existing item
            item = self.knowledge_base.get_knowledge_by_id(item_id)

            if not item:
                return {
                    "error": f"Pattern with ID {item_id} not found",
                    "message": "Invalid pattern ID",
                }

            # Update fields if provided
            updates = {}
            if title is not None:
                updates["title"] = title
            if description is not None:
                updates["description"] = description
            if content is not None:
                updates["content"] = content
            if confidence is not None:
                updates["confidence"] = confidence
            if effectiveness is not None:
                updates["effectiveness"] = effectiveness
            if metadata is not None:
                updates["metadata"] = metadata

            # Update in knowledge base
            success = self.knowledge_base.update_knowledge(item_id, updates)

            if success:
                logger.info(f"Updated pattern {item_id}")
                return {
                    "item_id": item_id,
                    "updated_fields": list(updates.keys()),
                    "message": "Pattern updated successfully",
                }
            return {"error": "Update failed", "message": "Failed to update pattern"}

        except Exception as e:
            logger.error(f"Error updating pattern: {e}")
            return {"error": str(e), "message": "Failed to update pattern"}

    def delete_pattern(self, item_id: int) -> dict[str, Any]:
        """Delete a pattern from the knowledge base.

        Args:
            item_id: ID of the pattern to delete

        Returns:
            Deletion result
        """
        try:
            # Check if pattern exists
            item = self.knowledge_base.get_knowledge_by_id(item_id)

            if not item:
                return {
                    "error": f"Pattern with ID {item_id} not found",
                    "message": "Invalid pattern ID",
                }

            # Delete from knowledge base
            success = self.knowledge_base.delete_knowledge(item_id)

            if success:
                logger.info(f"Deleted pattern {item_id}: {item.title}")
                return {
                    "item_id": item_id,
                    "title": item.title,
                    "message": "Pattern deleted successfully",
                }
            return {"error": "Delete failed", "message": "Failed to delete pattern"}

        except Exception as e:
            logger.error(f"Error deleting pattern: {e}")
            return {"error": str(e), "message": "Failed to delete pattern"}

    def get_patterns_by_category(self, category: str, limit: int = 20) -> dict[str, Any]:
        """Get patterns by category.

        Args:
            category: Pattern category
            limit: Maximum number of results

        Returns:
            Patterns in the specified category
        """
        try:
            # Convert category to enum
            try:
                pattern_category = PatternCategory(category.lower())
            except ValueError:
                return {
                    "error": f"Invalid category: {category}",
                    "message": f"Valid categories: {[c.value for c in PatternCategory]}",
                }

            # Get patterns by category
            patterns = self.knowledge_base.get_patterns_by_category(pattern_category, limit=limit)

            # Format results
            formatted_patterns = []
            for item in patterns:
                formatted_patterns.append(
                    {
                        "id": item.id,
                        "title": item.title,
                        "description": (
                            item.description[:100] + "..." if len(item.description) > 100 else item.description
                        ),
                        "confidence": item.confidence,
                        "effectiveness": item.effectiveness,
                        "usage_count": item.usage_count,
                        "created_at": item.created_at,
                    }
                )

            return {
                "category": category,
                "patterns": formatted_patterns,
                "total_found": len(formatted_patterns),
                "message": f"Found {len(formatted_patterns)} patterns in {category} category",
            }

        except Exception as e:
            logger.error(f"Error getting patterns by category: {e}")
            return {"error": str(e), "message": "Failed to get patterns by category"}

    def get_knowledge_base_statistics(self) -> dict[str, Any]:
        """Get knowledge base statistics.

        Returns:
            Knowledge base statistics
        """
        try:
            stats = self.knowledge_base.get_statistics()

            return {
                "statistics": stats,
                "message": "Knowledge base statistics retrieved successfully",
            }

        except Exception as e:
            logger.error(f"Error getting knowledge base statistics: {e}")
            return {
                "error": str(e),
                "message": "Failed to get knowledge base statistics",
            }

    def get_categories(self) -> dict[str, Any]:
        """Get all available pattern categories.

        Returns:
            List of available categories
        """
        try:
            categories = [
                {
                    "value": category.value,
                    "name": category.value.replace("_", " ").title(),
                }
                for category in PatternCategory
            ]

            return {
                "categories": categories,
                "total_categories": len(categories),
                "message": "Categories retrieved successfully",
            }

        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return {"error": str(e), "message": "Failed to get categories"}


# Tool schema for MCP integration
KNOWLEDGE_BASE_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "add_pattern",
                "search_patterns",
                "get_pattern",
                "update_pattern",
                "delete_pattern",
                "get_patterns_by_category",
                "get_statistics",
                "get_categories",
            ],
            "description": "The knowledge base action to perform",
        },
        "item_id": {
            "type": "integer",
            "description": "ID of the pattern (for get, update, delete operations)",
        },
        "title": {
            "type": "string",
            "description": "Pattern title (for add, update operations)",
        },
        "description": {
            "type": "string",
            "description": "Pattern description (for add, update operations)",
        },
        "category": {
            "type": "string",
            "description": "Pattern category (for add, search, get_by_category operations)",
        },
        "content": {
            "type": "string",
            "description": "Pattern content (for add, update operations)",
        },
        "query": {
            "type": "string",
            "description": "Search query (for search_patterns operation)",
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Confidence score (for add, update operations)",
        },
        "effectiveness": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Effectiveness score (for add, update operations)",
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "description": "Maximum number of results",
        },
        "metadata": {
            "type": "object",
            "description": "Additional metadata (for add, update operations)",
        },
    },
    "required": ["action"],
}


def knowledge_base_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handler for knowledge base MCP tool.

    Args:
        args: Tool arguments including action and parameters

    Returns:
        Tool execution result
    """
    try:
        tool = KnowledgeBaseTool()
        action = args.get("action")

        if action == "add_pattern":
            required_fields = ["title", "description", "category", "content"]
            for field in required_fields:
                if field not in args:
                    return {
                        "error": f"Missing required field: {field}",
                        "message": f"Field '{field}' is required for add_pattern action",
                    }

            return tool.add_pattern(
                title=args["title"],
                description=args["description"],
                category=args["category"],
                content=args["content"],
                confidence=args.get("confidence", 0.8),
                effectiveness=args.get("effectiveness", 0.8),
                metadata=args.get("metadata"),
            )

        if action == "search_patterns":
            query = args.get("query")
            if not query:
                return {
                    "error": "Missing required field: query",
                    "message": "Field 'query' is required for search_patterns action",
                }

            return tool.search_patterns(
                query=query,
                category=args.get("category"),
                limit=args.get("limit", 10),
                min_confidence=args.get("min_confidence"),
            )

        if action == "get_pattern":
            item_id = args.get("item_id")
            if item_id is None:
                return {
                    "error": "Missing required field: item_id",
                    "message": "Field 'item_id' is required for get_pattern action",
                }
            return tool.get_pattern(item_id)

        if action == "update_pattern":
            item_id = args.get("item_id")
            if item_id is None:
                return {
                    "error": "Missing required field: item_id",
                    "message": "Field 'item_id' is required for update_pattern action",
                }

            return tool.update_pattern(
                item_id=item_id,
                title=args.get("title"),
                description=args.get("description"),
                content=args.get("content"),
                confidence=args.get("confidence"),
                effectiveness=args.get("effectiveness"),
                metadata=args.get("metadata"),
            )

        if action == "delete_pattern":
            item_id = args.get("item_id")
            if item_id is None:
                return {
                    "error": "Missing required field: item_id",
                    "message": "Field 'item_id' is required for delete_pattern action",
                }
            return tool.delete_pattern(item_id)

        if action == "get_patterns_by_category":
            category = args.get("category")
            if not category:
                return {
                    "error": "Missing required field: category",
                    "message": "Field 'category' is required for get_patterns_by_category action",
                }

            return tool.get_patterns_by_category(category=category, limit=args.get("limit", 20))

        if action == "get_statistics":
            return tool.get_knowledge_base_statistics()

        if action == "get_categories":
            return tool.get_categories()

        return {
            "error": f"Unknown action: {action}",
            "message": "Invalid action specified",
        }

    except Exception as e:
        logger.error(f"Error in knowledge base handler: {e}")
        return {"error": str(e), "message": "Knowledge base operation failed"}
