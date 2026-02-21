#!/usr/bin/env python3
"""Basic test for specialist training infrastructure."""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all training modules can be imported."""
    print("🔍 Testing imports...")

    try:
        from tool_router.training.knowledge_base import KnowledgeBase, PatternCategory
        print("✅ KnowledgeBase imported successfully")

        from tool_router.training.data_extraction import PatternExtractor, DataSource
        print("✅ PatternExtractor imported successfully")

        from tool_router.training.training_pipeline import TrainingPipeline
        print("✅ TrainingPipeline imported successfully")

        from tool_router.training.evaluation import SpecialistEvaluator, EvaluationMetric
        print("✅ SpecialistEvaluator imported successfully")

        return True

    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_knowledge_base():
    """Test basic knowledge base functionality."""
    print("\n📚 Testing KnowledgeBase...")

    try:
        from tool_router.training.knowledge_base import KnowledgeBase, PatternCategory

        # Create knowledge base
        kb = KnowledgeBase()
        print("✅ KnowledgeBase created")

        # Get statistics
        stats = kb.get_statistics()
        print(f"✅ Statistics: {stats['total_items']} items")

        return True

    except Exception as e:
        print(f"❌ KnowledgeBase error: {e}")
        return False

def test_pattern_extraction():
    """Test basic pattern extraction."""
    print("\n🔍 Testing Pattern Extraction...")

    try:
        from tool_router.training.data_extraction import PatternExtractor, DataSource

        # Create extractor
        extractor = PatternExtractor()
        print("✅ PatternExtractor created")

        # Test with a simple web source
        test_source = DataSource(
            name="test",
            type="web",
            url="https://react.dev",
            category=PatternCategory.REACT_PATTERN
        )
        print("✅ Test source created")

        return True

    except Exception as e:
        print(f"❌ Pattern extraction error: {e}")
        return False

def test_training_pipeline():
    """Test training pipeline initialization."""
    print("\n🔄 Testing Training Pipeline...")

    try:
        from tool_router.training.training_pipeline import TrainingPipeline

        # Create pipeline
        pipeline = TrainingPipeline()
        print("✅ TrainingPipeline created")

        return True

    except Exception as e:
        print(f"❌ Training pipeline error: {e}")
        return False

def test_evaluation():
    """Test evaluation framework."""
    print("\n📊 Testing Evaluation Framework...")

    try:
        from tool_router.training.evaluation import SpecialistEvaluator, EvaluationMetric
        from tool_router.training.knowledge_base import KnowledgeBase

        # Create evaluator
        kb = KnowledgeBase()
        evaluator = SpecialistEvaluator(kb)
        print("✅ SpecialistEvaluator created")

        # Check benchmark suites
        print(f"✅ Benchmark suites: {list(evaluator.benchmark_suites.keys())}")

        return True

    except Exception as e:
        print(f"❌ Evaluation error: {e}")
        return False

def main():
    """Run all basic tests."""
    print("🚀 Running Basic Training Infrastructure Tests")
    print("=" * 50)

    tests = [
        test_imports,
        test_knowledge_base,
        test_pattern_extraction,
        test_training_pipeline,
        test_evaluation
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Training infrastructure is ready.")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
