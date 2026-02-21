#!/usr/bin/env python3
"""Demo script for specialist AI agent training.

This script demonstrates the complete training pipeline:
1. Data extraction from public sources
2. Knowledge base population
3. Pattern validation and quality assessment
4. Specialist agent training
5. Evaluation and performance metrics
"""

import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from tool_router.training.training_pipeline import TrainingPipeline, DEFAULT_TRAINING_SOURCES
from tool_router.training.evaluation import SpecialistEvaluator
from tool_router.training.knowledge_base import KnowledgeBase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run the specialist training demo."""
    print("🚀 Starting Specialist AI Agent Training Demo")
    print("=" * 50)
    
    try:
        # Initialize training pipeline
        print("\n📚 Initializing Training Pipeline...")
        pipeline = TrainingPipeline()
        
        # Run the complete training pipeline
        print("\n🔄 Running Training Pipeline...")
        results = pipeline.run_training_pipeline(DEFAULT_TRAINING_SOURCES)
        
        # Display training results
        print("\n📊 Training Results:")
        print(f"Patterns Extracted: {results['patterns_extracted']}")
        print(f"Patterns Validated: {results['patterns_validated']}")
        print(f"Patterns Added: {results['patterns_added']}")
        print(f"Training Runs: {results['training_runs']}")
        
        if "training_results" in results:
            print("\n🎯 Specialist Training Results:")
            for specialist, data in results["training_results"].items():
                print(f"\n{specialist.title()} Specialist:")
                print(f"  Patterns: {data['patterns_count']}")
                print(f"  Avg Effectiveness: {data['avg_effectiveness']:.2f}")
                
                if "top_patterns" in data:
                    print("  Top Patterns:")
                    for pattern in data["top_patterns"]:
                        print(f"    - {pattern['title']} (effectiveness: {pattern['effectiveness']:.2f})")
        
        if "evaluation_results" in results:
            print("\n📈 Evaluation Results:")
            eval_results = results["evaluation_results"]
            
            if "quality_metrics" in eval_results:
                quality = eval_results["quality_metrics"]
                print(f"  Total Patterns: {quality['total_patterns']}")
                print(f"  Average Confidence: {quality['avg_confidence']:.2f}")
                print(f"  Average Effectiveness: {quality['avg_effectiveness']:.2f}")
                print(f"  High Quality Patterns: {quality['high_quality_patterns']}")
            
            if "coverage" in eval_results:
                coverage = eval_results["coverage"]
                print(f"  Categories Covered: {coverage['categories_covered']}/{coverage['total_categories']}")
                print(f"  Coverage Percentage: {coverage['coverage_percentage']:.1f}%")
        
        # Get knowledge base statistics
        print("\n📚 Knowledge Base Statistics:")
        kb_stats = pipeline.knowledge_base.get_statistics()
        
        print(f"Total Items: {kb_stats['total_items']}")
        print(f"Average Effectiveness: {kb_stats['average_effectiveness']:.2f}")
        
        if "by_category" in kb_stats:
            print("Items by Category:")
            for category, count in kb_stats["by_category"].items():
                print(f"  {category}: {count}")
        
        # Run evaluation
        print("\n🔍 Running Specialist Evaluation...")
        evaluator = SpecialistEvaluator(pipeline.knowledge_base)
        
        # Evaluate all specialists
        for specialist_name in evaluator.benchmark_suites.keys():
            print(f"\nEvaluating {specialist_name}...")
            eval_results = evaluator.evaluate_specialist(specialist_name)
            
            for result in eval_results:
                print(f"  {result.metric.value}: {result.value:.2f} "
                      f"({result.passed_cases}/{result.test_cases} passed)")
        
        # Get evaluation summary
        print("\n📋 Evaluation Summary:")
        summary = evaluator.get_evaluation_summary()
        
        for specialist, data in summary.items():
            if "overall_score" in data:
                print(f"\n{specialist}:")
                print(f"  Overall Score: {data['overall_score']:.2f}")
                print(f"  Metrics Count: {data['metrics_count']}")
        
        # Generate training report
        print("\n📄 Generating Training Report...")
        report = pipeline.get_training_report()
        
        print("\n📊 Training Report:")
        print(f"Training Statistics: {report['training_statistics']}")
        
        if "recommendations" in report:
            print("\n💡 Recommendations:")
            for rec in report["recommendations"]:
                print(f"  - {rec}")
        
        # Export training data
        export_path = Path(__file__).parent / "training_export.json"
        pipeline.export_training_data(export_path)
        print(f"\n💾 Training data exported to: {export_path}")
        
        print("\n✅ Training Demo Completed Successfully!")
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"Training demo failed: {e}")
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
