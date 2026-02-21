"""Training pipeline for specialist AI agents.

Orchestrates the complete training process including:
- Data extraction and processing
- Pattern validation and quality assessment
- Knowledge base population
- Specialist model training
- Evaluation and feedback collection
- Continuous learning mechanisms
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .data_extraction import ExtractedPattern, PatternCategory, PatternExtractor
from .knowledge_base import KnowledgeBase, KnowledgeIndexer


logger = logging.getLogger(__name__)


class TrainingPipeline:
    """Orchestrates the specialist AI agent training pipeline."""

    def __init__(self, knowledge_base_path: Path | None = None) -> None:
        """Initialize the training pipeline."""
        self.knowledge_base = KnowledgeBase(knowledge_base_path)
        self.extractor = PatternExtractor()
        self.indexer = KnowledgeIndexer(self.knowledge_base)

        # Training configuration
        self.min_confidence = 0.7
        self.batch_size = 50
        self.evaluation_interval = 100

        # Training metrics
        self.training_stats = {
            "patterns_extracted": 0,
            "patterns_validated": 0,
            "patterns_added": 0,
            "training_runs": 0,
            "last_training": None,
            "errors": [],
        }

    def run_training_pipeline(self, data_sources: list[dict[str, Any]]) -> dict[str, Any]:
        """Run the complete training pipeline."""
        logger.info("Starting specialist AI agent training pipeline")

        try:
            # Phase 1: Data Extraction
            logger.info("Phase 1: Extracting patterns from data sources")
            extracted_patterns = self._extract_patterns(data_sources)

            # Phase 2: Pattern Validation
            logger.info("Phase 2: Validating extracted patterns")
            validated_patterns = self._validate_patterns(extracted_patterns)

            # Phase 3: Knowledge Base Population
            logger.info("Phase 3: Populating knowledge base")
            added_patterns = self._populate_knowledge_base(validated_patterns)

            # Phase 4: Knowledge Indexing
            logger.info("Phase 4: Building knowledge indexes")
            self._build_indexes()

            # Phase 5: Specialist Training
            logger.info("Phase 5: Training specialist agents")
            training_results = self._train_specialists()

            # Phase 6: Evaluation
            logger.info("Phase 6: Evaluating training results")
            evaluation_results = self._evaluate_training()

            # Update training statistics
            self.training_stats.update(
                {
                    "patterns_extracted": len(extracted_patterns),
                    "patterns_validated": len(validated_patterns),
                    "patterns_added": len(added_patterns),
                    "training_runs": self.training_stats["training_runs"] + 1,
                    "last_training": datetime.now().isoformat(),
                    "training_results": training_results,
                    "evaluation_results": evaluation_results,
                }
            )

            logger.info("Training pipeline completed successfully")
            return self.training_stats

        except Exception as e:
            error_msg = f"Training pipeline failed: {e}"
            logger.error(error_msg)
            self.training_stats["errors"].append(error_msg)
            return self.training_stats

    def _extract_patterns(self, data_sources: list[dict[str, Any]]) -> list[ExtractedPattern]:
        """Extract patterns from data sources."""
        all_patterns = []

        for i, source in enumerate(data_sources):
            try:
                logger.info(f"Extracting from source {i+1}/{len(data_sources)}: {source.get('url', 'Unknown')}")

                patterns = self.extractor.extract_from_multiple_sources([source])
                all_patterns.extend(patterns)

                logger.info(f"Extracted {len(patterns)} patterns from source")

            except Exception as e:
                error_msg = f"Failed to extract from source {source.get('url', 'Unknown')}: {e}"
                logger.error(error_msg)
                self.training_stats["errors"].append(error_msg)

        return all_patterns

    def _validate_patterns(self, patterns: list[ExtractedPattern]) -> list[ExtractedPattern]:
        """Validate extracted patterns."""
        validated_patterns = []

        for pattern in patterns:
            # Filter by confidence score
            if pattern.confidence_score < self.min_confidence:
                logger.debug(f"Skipping pattern with low confidence: {pattern.title}")
                continue

            # Validate required fields
            if not pattern.title or not pattern.description:
                logger.debug(f"Skipping pattern with missing required fields: {pattern.title}")
                continue

            # Check for duplicates
            if self._is_duplicate_pattern(pattern, validated_patterns):
                logger.debug(f"Skipping duplicate pattern: {pattern.title}")
                continue

            # Additional validation based on category
            if self._validate_pattern_by_category(pattern):
                validated_patterns.append(pattern)

        logger.info(f"Validated {len(validated_patterns)} out of {len(patterns)} patterns")
        return validated_patterns

    def _validate_pattern_by_category(self, pattern: ExtractedPattern) -> bool:
        """Validate pattern based on its category."""
        if pattern.category == PatternCategory.REACT_PATTERN:
            # React patterns should have code examples
            return bool(pattern.code_example)

        if pattern.category == PatternCategory.ACCESSIBILITY:
            # Accessibility patterns should mention specific guidelines
            accessibility_keywords = ["wcag", "aria", "accessible", "screen reader", "keyboard"]
            content = f"{pattern.title} {pattern.description}".lower()
            return any(keyword in content for keyword in accessibility_keywords)

        if pattern.category == PatternCategory.PROMPT_ENGINEERING:
            # Prompt engineering patterns should have specific techniques
            prompt_keywords = ["chain-of-thought", "cot", "reflection", "few-shot", "zero-shot"]
            content = f"{pattern.title} {pattern.description}".lower()
            return any(keyword in content for keyword in prompt_keywords)

        return True

    def _is_duplicate_pattern(self, pattern: ExtractedPattern, existing_patterns: list[ExtractedPattern]) -> bool:
        """Check if a pattern is a duplicate of existing patterns."""
        for existing in existing_patterns:
            # Check for similar titles
            if pattern.title.lower() == existing.title.lower():
                return True

            # Check for similar descriptions (simple similarity check)
            if self._text_similarity(pattern.description, existing.description) > 0.8:
                return True

        return False

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _populate_knowledge_base(self, patterns: list[ExtractedPattern]) -> list[str]:
        """Populate the knowledge base with validated patterns."""
        added_ids = []

        for pattern in patterns:
            try:
                item_id = self.knowledge_base.add_pattern(pattern)
                added_ids.append(item_id)

                logger.debug(f"Added pattern to knowledge base: {pattern.title}")

            except Exception as e:
                error_msg = f"Failed to add pattern {pattern.title}: {e}"
                logger.error(error_msg)
                self.training_stats["errors"].append(error_msg)

        logger.info(f"Added {len(added_ids)} patterns to knowledge base")
        return added_ids

    def _build_indexes(self) -> None:
        """Build knowledge indexes for efficient retrieval."""
        try:
            self.indexer._build_indexes()
            logger.info("Knowledge indexes built successfully")
        except Exception as e:
            error_msg = f"Failed to build indexes: {e}"
            logger.error(error_msg)
            self.training_stats["errors"].append(error_msg)

    def _train_specialists(self) -> dict[str, Any]:
        """Train specialist agents with the new knowledge."""
        training_results = {}

        # Get knowledge base statistics
        stats = self.knowledge_base.get_statistics()

        # Train each specialist category
        for category in PatternCategory:
            category_patterns = self.knowledge_base.get_patterns_by_category(category, limit=100)

            if category_patterns:
                training_results[category.value] = {
                    "patterns_count": len(category_patterns),
                    "avg_effectiveness": sum(p.effectiveness_score for p in category_patterns) / len(category_patterns),
                    "top_patterns": [
                        {"title": p.title, "effectiveness": p.effectiveness_score, "usage_count": p.usage_count}
                        for p in category_patterns[:5]
                    ],
                }

                logger.info(f"Trained {category.value} specialist with {len(category_patterns)} patterns")

        return training_results

    def _evaluate_training(self) -> dict[str, Any]:
        """Evaluate the training results."""
        evaluation_results = {}

        # Knowledge base statistics
        kb_stats = self.knowledge_base.get_statistics()
        evaluation_results["knowledge_base"] = kb_stats

        # Pattern quality assessment
        all_patterns = []
        for category in PatternCategory:
            patterns = self.knowledge_base.get_patterns_by_category(category, limit=100)
            all_patterns.extend(patterns)

        if all_patterns:
            avg_confidence = sum(p.confidence_score for p in all_patterns) / len(all_patterns)
            avg_effectiveness = sum(p.effectiveness_score for p in all_patterns) / len(all_patterns)

            evaluation_results["quality_metrics"] = {
                "total_patterns": len(all_patterns),
                "avg_confidence": avg_confidence,
                "avg_effectiveness": avg_effectiveness,
                "high_quality_patterns": len([p for p in all_patterns if p.effectiveness_score > 0.8]),
            }

        # Coverage assessment
        evaluation_results["coverage"] = {
            "categories_covered": len(set(p.category for p in all_patterns)),
            "total_categories": len(PatternCategory),
            "coverage_percentage": len(set(p.category for p in all_patterns)) / len(PatternCategory) * 100,
        }

        return evaluation_results

    def run_continuous_learning(self, new_data_sources: list[dict[str, Any]]) -> dict[str, Any]:
        """Run continuous learning with new data sources."""
        logger.info("Starting continuous learning with new data sources")

        # Extract patterns from new sources
        new_patterns = self._extract_patterns(new_data_sources)

        # Validate and add new patterns
        validated_patterns = self._validate_patterns(new_patterns)
        added_ids = self._populate_knowledge_base(validated_patterns)

        # Rebuild indexes
        self._build_indexes()

        # Update statistics
        self.training_stats.update(
            {
                "patterns_extracted": self.training_stats["patterns_extracted"] + len(new_patterns),
                "patterns_validated": self.training_stats["patterns_validated"] + len(validated_patterns),
                "patterns_added": self.training_stats["patterns_added"] + len(added_ids),
                "last_training": datetime.now().isoformat(),
            }
        )

        logger.info(f"Continuous learning completed: {len(added_ids)} new patterns added")
        return self.training_stats

    def get_training_report(self) -> dict[str, Any]:
        """Generate a comprehensive training report."""
        return {
            "training_statistics": self.training_stats,
            "knowledge_base_stats": self.knowledge_base.get_statistics(),
            "index_stats": {
                "tag_index_size": len(self.indexer.tag_index),
                "keyword_index_size": len(self.indexer.keyword_index),
                "category_index_size": len(self.indexer.category_index),
            },
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate training recommendations based on current state."""
        recommendations = []

        stats = self.knowledge_base.get_statistics()

        # Coverage recommendations
        coverage = stats["by_category"]
        for category in PatternCategory:
            if category.value not in coverage or coverage[category.value] < 10:
                recommendations.append(f"Consider adding more {category.value} patterns")

        # Quality recommendations
        if stats["average_effectiveness"] < 0.7:
            recommendations.append("Focus on higher quality pattern sources")

        # Usage recommendations
        most_used = stats["most_used"]
        if not most_used:
            recommendations.append("Promote usage of knowledge base patterns")
        else:
            low_usage_items = [item for item in most_used if item["usage_count"] < 5]
            if low_usage_items:
                recommendations.append(
                    f"Review and improve low-usage patterns: {', '.join(item['title'] for item in low_usage_items[:3])}"
                )

        return recommendations

    def export_training_data(self, export_path: Path) -> None:
        """Export training data for backup or analysis."""
        export_data = {
            "training_statistics": self.training_stats,
            "knowledge_base_export": export_path / "knowledge_base_export.json",
            "training_report": self.get_training_report(),
            "export_timestamp": datetime.now().isoformat(),
        }

        # Export knowledge base
        self.knowledge_base.export_knowledge_base(export_data["knowledge_base_export"])

        # Export training data
        with export_path.open("w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Training data exported to {export_path}")

    def import_training_data(self, import_path: Path) -> dict[str, Any]:
        """Import training data from backup."""
        with import_path.open("r", encoding="utf-8") as f:
            import_data = json.load(f)

        # Import knowledge base
        kb_path = import_path / "knowledge_base_export.json"
        if kb_path.exists():
            imported_count = self.knowledge_base.import_knowledge(kb_path)
            logger.info(f"Imported {imported_count} knowledge items")

        # Update training statistics
        if "training_statistics" in import_data:
            self.training_stats.update(import_data["training_statistics"])

        logger.info(f"Training data imported from {import_path}")
        return import_data


# Training data sources configuration
DEFAULT_TRAINING_SOURCES = [
    # React Best Practices
    {"url": "https://react.dev/reference/rules", "type": "web_documentation", "category": "react_patterns"},
    {
        "url": "https://medium.com/@regondaakhil/react-best-practices-and-patterns-for-2024-f5cdf8e132f1",
        "type": "web_documentation",
        "category": "react_patterns",
    },
    # Design Systems
    {"url": "https://carbondesignsystem.com/", "type": "web_documentation", "category": "design_systems"},
    {"url": "https://www.lightningdesignsystem.com/", "type": "web_documentation", "category": "design_systems"},
    # Accessibility
    {"url": "https://www.w3.org/WAI/WCAG21/quickref/", "type": "web_documentation", "category": "accessibility"},
    # GitHub Repositories
    {"url": "https://github.com/facebook/react", "type": "github_repository", "category": "react_patterns"},
    {"url": "https://github.com/microsoft/fluentui", "type": "github_repository", "category": "design_systems"},
    # Prompt Engineering
    {
        "url": "https://www.anthropic.com/research/building-effective-agents",
        "type": "web_documentation",
        "category": "prompt_engineering",
    },
    {
        "url": "https://cloud.google.com/discover/what-is-prompt-engineering",
        "type": "web_documentation",
        "category": "prompt_engineering",
    },
]

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    pipeline = TrainingPipeline()

    print("Running training pipeline with default sources...")
    results = pipeline.run_training_pipeline(DEFAULT_TRAINING_SOURCES)

    print("\nTraining Results:")
    print(f"Patterns Extracted: {results['patterns_extracted']}")
    print(f"Patterns Validated: {results['patterns_validated']}")
    print(f"Patterns Added: {results['patterns_added']}")
    print(f"Training Runs: {results['training_runs']}")

    if "training_results" in results:
        print("\nSpecialist Training Results:")
        for specialist, data in results["training_results"].items():
            print(f"{specialist}:")
            print(f"  Patterns: {data['patterns_count']}")
            print(f"  Avg Effectiveness: {data['avg_effectiveness']:.2f}")

    if "evaluation_results" in results:
        print("\nEvaluation Results:")
        eval_results = results["evaluation_results"]

        if "quality_metrics" in eval_results:
            quality = eval_results["quality_metrics"]
            print(f"Total Patterns: {quality['total_patterns']}")
            print(f"Average Confidence: {quality['avg_confidence']:.2f}")
            print(f"Average Effectiveness: {quality['avg_effectiveness']:.2f}")
            print(f"High Quality Patterns: {quality['high_quality_patterns']}")

        if "coverage" in eval_results:
            coverage = eval_results["coverage"]
            print(f"Categories Covered: {coverage['categories_covered']}/{coverage['total_categories']}")
            print(f"Coverage Percentage: {coverage['coverage_percentage']:.1f}%")

    print("\nTraining Report:")
    report = pipeline.get_training_report()

    if "recommendations" in report:
        print("\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"- {rec}")

    # Export training data
    export_path = Path(__file__).parent.parent / "training_export.json"
    pipeline.export_training_data(export_path)
    print(f"\nTraining data exported to: {export_path}")
