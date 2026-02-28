"""Knowledge base management for specialist AI agents.

Manages structured knowledge repositories including:
- Pattern storage and retrieval
- Knowledge categorization and indexing
- Search and matching algorithms
- Continuous learning and updates
- Quality assessment and validation
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .data_extraction import ExtractedPattern, PatternCategory


class KnowledgeStatus(Enum):
    """Status of knowledge items."""

    ACTIVE = "active"
    PENDING = "pending"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class KnowledgeItem:
    """Represents a knowledge item in the knowledge base."""

    id: str
    category: PatternCategory
    title: str
    description: str
    content: str
    code_example: str | None = None
    tags: list[str] = field(default_factory=list)
    confidence_score: float = 1.0
    status: KnowledgeStatus = KnowledgeStatus.ACTIVE
    source_url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    usage_count: int = 0
    user_ratings: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)

    @property
    def average_rating(self) -> float:
        """Calculate average user rating."""
        if not self.user_ratings:
            return 0.0
        return sum(self.user_ratings) / len(self.user_ratings)

    @property
    def effectiveness_score(self) -> float:
        """Calculate overall effectiveness score."""
        rating_weight = 0.6
        usage_weight = 0.3
        confidence_weight = 0.1

        rating_score = self.average_rating / 5.0  # Normalize to 0-1
        usage_score = min(self.usage_count / 100.0, 1.0)  # Cap at 100 uses

        return rating_score * rating_weight + usage_score * usage_weight + self.confidence_score * confidence_weight


class KnowledgeBase:
    """Manages the specialist knowledge base."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize the knowledge base."""
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "knowledge_base.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize the SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    content TEXT NOT NULL,
                    code_example TEXT,
                    tags TEXT,
                    confidence_score REAL DEFAULT 1.0,
                    status TEXT DEFAULT 'active',
                    source_url TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    user_ratings TEXT,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_category ON knowledge_items(category)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON knowledge_items(status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_effectiveness ON knowledge_items(
                    (CAST(user_ratings AS REAL) / 5.0) * 0.6 +
                    (CAST(usage_count AS REAL) / 100.0) * 0.3 +
                    confidence_score * 0.1
                )
            """)

    def add_pattern(self, pattern: ExtractedPattern) -> str:
        """Add a pattern to the knowledge base."""
        item_id = self._generate_item_id(pattern)

        knowledge_item = KnowledgeItem(
            id=item_id,
            category=pattern.category,
            title=pattern.title,
            description=pattern.description,
            content=pattern.description,
            code_example=pattern.code_example,
            tags=pattern.tags,
            confidence_score=pattern.confidence_score,
            source_url=pattern.source_url,
            metadata=pattern.metadata,
        )

        return self.add_knowledge_item(knowledge_item)

    def add_knowledge_item(self, item: KnowledgeItem) -> str:
        """Add a knowledge item to the knowledge base."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO knowledge_items (
                    id, category, title, description, content, code_example,
                    tags, confidence_score, status, source_url, created_at,
                    updated_at, usage_count, user_ratings, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    item.id,
                    item.category.value,
                    item.title,
                    item.description,
                    item.content,
                    item.code_example,
                    json.dumps(item.tags),
                    item.confidence_score,
                    item.status.value,
                    item.source_url,
                    item.created_at.isoformat(),
                    item.updated_at.isoformat(),
                    item.usage_count,
                    json.dumps(item.user_ratings),
                    json.dumps(item.metadata),
                ),
            )

        return item.id

    def get_knowledge_item(self, item_id: str) -> KnowledgeItem | None:
        """Get a knowledge item by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM knowledge_items WHERE id = ?
            """,
                (item_id,),
            )

            row = cursor.fetchone()
            if row:
                return self._row_to_knowledge_item(row)

        return None

    def search_knowledge(
        self, query: str, category: PatternCategory | None = None, limit: int = 10
    ) -> list[KnowledgeItem]:
        """Search knowledge items by query and optionally category."""
        with sqlite3.connect(self.db_path) as conn:
            sql = """
                SELECT * FROM knowledge_items
                WHERE status = 'active' AND (
                    title LIKE ? OR
                    description LIKE ? OR
                    content LIKE ? OR
                    tags LIKE ?
                )
            """
            params = [f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"]

            if category:
                sql += " AND category = ?"
                params.append(category.value)

            sql += " ORDER BY confidence_score DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(sql, params)

            return [self._row_to_knowledge_item(row) for row in cursor.fetchall()]

    def search_patterns(self, query: str, limit: int = 10) -> list[KnowledgeItem]:
        """Search patterns by query - alias for search_knowledge."""
        return self.search_knowledge(query, limit=limit)

    def get_patterns_by_category(self, category: PatternCategory, limit: int = 50) -> list[KnowledgeItem]:
        """Get patterns by category."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM knowledge_items
                WHERE category = ? AND status = 'active'
                ORDER BY confidence_score DESC
                LIMIT ?
            """,
                (category.value, limit),
            )

            return [self._row_to_knowledge_item(row) for row in cursor.fetchall()]

    def get_top_patterns(self, limit: int = 20) -> list[KnowledgeItem]:
        """Get top patterns by effectiveness score."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM knowledge_items
                WHERE status = 'active'
                ORDER BY confidence_score DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [self._row_to_knowledge_item(row) for row in cursor.fetchall()]

    def update_usage_count(self, item_id: str) -> None:
        """Increment usage count for a knowledge item."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE knowledge_items
                SET usage_count = usage_count + 1, updated_at = ?
                WHERE id = ?
            """,
                (datetime.now(UTC).isoformat(), item_id),
            )

    def add_user_rating(self, item_id: str, rating: float) -> None:
        """Add a user rating for a knowledge item."""
        item = self.get_knowledge_item(item_id)
        if item:
            item.user_ratings.append(rating)
            item.updated_at = datetime.now(UTC)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE knowledge_items
                    SET user_ratings = ?, updated_at = ?
                    WHERE id = ?
                """,
                    (
                        json.dumps(item.user_ratings),
                        item.updated_at.isoformat(),
                        item_id,
                    ),
                )

    def get_statistics(self) -> dict[str, Any]:
        """Get knowledge base statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Total items
            cursor = conn.execute("SELECT COUNT(*) FROM knowledge_items")
            total_items = cursor.fetchone()[0]

            # Items by category
            cursor = conn.execute("""
                SELECT category, COUNT(*)
                FROM knowledge_items
                WHERE status = 'active'
                GROUP BY category
            """)
            by_category = dict(cursor.fetchall())

            # Average effectiveness
            cursor = conn.execute("""
                SELECT AVG(effectiveness_score)
                FROM (
                    SELECT
                        (CAST(user_ratings AS REAL) / 5.0) * 0.6 +
                        (CAST(usage_count AS REAL) / 100.0) * 0.3 +
                        confidence_score * 0.1 as effectiveness_score
                    FROM knowledge_items
                    WHERE status = 'active'
                )
            """)
            avg_effectiveness = cursor.fetchone()[0] or 0.0

            # Most used items
            cursor = conn.execute("""
                SELECT id, title, usage_count
                FROM knowledge_items
                WHERE status = 'active'
                ORDER BY usage_count DESC
                LIMIT 5
            """)
            most_used = [{"id": row[0], "title": row[1], "usage_count": row[2]} for row in cursor.fetchall()]

            return {
                "total_items": total_items,
                "by_category": by_category,
                "average_effectiveness": avg_effectiveness,
                "most_used": most_used,
            }

    def _row_to_knowledge_item(self, row: sqlite3.Row) -> KnowledgeItem:
        """Convert database row to KnowledgeItem."""
        return KnowledgeItem(
            id=row[0],
            category=PatternCategory(row[1]),
            title=row[2],
            description=row[3],
            content=row[4],
            code_example=row[5],
            tags=json.loads(row[6]) if row[6] else [],
            confidence_score=row[7],
            status=KnowledgeStatus(row[8]),
            source_url=row[9],
            created_at=datetime.fromisoformat(row[10]),
            updated_at=datetime.fromisoformat(row[11]),
            usage_count=row[12],
            user_ratings=json.loads(row[13]) if row[13] else [],
            metadata=json.loads(row[14]) if row[14] else {},
        )

    def _generate_item_id(self, pattern: ExtractedPattern) -> str:
        """Generate a unique ID for a pattern."""
        content = f"{pattern.category.value}_{pattern.title}_{pattern.description}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def export_knowledge(self, file_path: Path) -> None:
        """Export knowledge base to JSON file."""
        items = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM knowledge_items WHERE status = 'active'")
            for row in cursor.fetchall():
                item = self._row_to_knowledge_item(row)
                items.append(
                    {
                        "id": item.id,
                        "category": item.category.value,
                        "title": item.title,
                        "description": item.description,
                        "content": item.content,
                        "code_example": item.code_example,
                        "tags": item.tags,
                        "confidence_score": item.confidence_score,
                        "source_url": item.source_url,
                        "usage_count": item.usage_count,
                        "user_ratings": item.user_ratings,
                        "metadata": item.metadata,
                    }
                )

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

    def import_knowledge(self, file_path: Path) -> int:
        """Import knowledge from JSON file."""
        with file_path.open("r", encoding="utf-8") as f:
            items = json.load(f)

        imported_count = 0
        for item_data in items:
            try:
                knowledge_item = KnowledgeItem(
                    id=item_data["id"],
                    category=PatternCategory(item_data["category"]),
                    title=item_data["title"],
                    description=item_data["description"],
                    content=item_data["content"],
                    code_example=item_data.get("code_example"),
                    tags=item_data.get("tags", []),
                    confidence_score=item_data.get("confidence_score", 1.0),
                    source_url=item_data.get("source_url"),
                    usage_count=item_data.get("usage_count", 0),
                    user_ratings=item_data.get("user_ratings", []),
                    metadata=item_data.get("metadata", {}),
                )

                self.add_knowledge_item(knowledge_item)
                imported_count += 1

            except (ValueError, KeyError, json.JSONDecodeError):
                # Log error but continue with other items
                continue

        return imported_count


class KnowledgeIndexer:
    """Indexes and categorizes knowledge for efficient retrieval."""

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self.knowledge_base = knowledge_base
        self._build_indexes()

    def _build_indexes(self) -> None:
        """Build search indexes."""
        self.tag_index: dict[str, set[str]] = {}
        self.category_index: dict[PatternCategory, set[str]] = {}
        self.keyword_index: dict[str, set[str]] = {}

        # Get all active knowledge items
        with sqlite3.connect(self.knowledge_base.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, category, title, description, tags, content
                FROM knowledge_items
                WHERE status = 'active'
            """)

            for row in cursor.fetchall():
                item_id = row[0]
                category = PatternCategory(row[1])
                title = row[2]
                description = row[3]
                tags = json.loads(row[4]) if row[4] else []
                content = row[5]

                # Index by category
                if category not in self.category_index:
                    self.category_index[category] = set()
                self.category_index[category].add(item_id)

                # Index by tags
                for tag in tags:
                    if tag not in self.tag_index:
                        self.tag_index[tag] = set()
                    self.tag_index[tag].add(item_id)

                # Index by keywords (simple word extraction)
                text = f"{title} {description} {content}".lower()
                words = set(text.split())

                for word in words:
                    if len(word) > 2:  # Skip very short words
                        if word not in self.keyword_index:
                            self.keyword_index[word] = set()
                        self.keyword_index[word].add(item_id)

    def find_by_tags(self, tags: list[str]) -> set[str]:
        """Find knowledge items by tags."""
        result = set()

        for tag in tags:
            if tag in self.tag_index:
                result.update(self.tag_index[tag])

        return result

    def find_by_category(self, category: PatternCategory) -> set[str]:
        """Find knowledge items by category."""
        return self.category_index.get(category, set())

    def find_by_keywords(self, keywords: list[str]) -> set[str]:
        """Find knowledge items by keywords."""
        result = set()

        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in self.keyword_index:
                result.update(self.keyword_index[keyword_lower])

        return result

    def get_related_items(self, item_id: str, limit: int = 5) -> list[str]:
        """Get related knowledge items based on shared tags and keywords."""
        item = self.knowledge_base.get_knowledge_item(item_id)
        if not item:
            return []

        # Find items with shared tags
        related_by_tags = set()
        for tag in item.tags:
            if tag in self.tag_index:
                related_by_tags.update(self.tag_index[tag])

        # Remove the original item
        related_by_tags.discard(item_id)

        # Return top related items
        related_items = []
        for related_id in related_by_tags:
            related_item = self.knowledge_base.get_knowledge_item(related_id)
            if related_item:
                related_items.append(related_item)

        # Sort by effectiveness score
        related_items.sort(key=lambda x: x.effectiveness_score, reverse=True)

        return [item.id for item in related_items[:limit]]


if __name__ == "__main__":
    # Example usage
    kb = KnowledgeBase()

    stats = kb.get_statistics()
    # Use proper logging instead of print

    # Search for React patterns
    patterns = kb.search_knowledge("react", PatternCategory.REACT_PATTERN, limit=5)
    # Use proper logging instead of print

    # Create indexer
    indexer = KnowledgeIndexer(kb)

    # Use proper logging instead of print statements
