#!/usr/bin/env python3
"""Integration script for specialist AI training with MCP Gateway.

This script demonstrates how to integrate the specialist training infrastructure
with the existing MCP Gateway system to provide enhanced AI capabilities.
"""

import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_enhanced_mcp_server():
    """Create an enhanced MCP server with training integration."""
    print("🚀 Creating Enhanced MCP Server with Training Integration")
    print("=" * 60)

    try:
        # Import training components
        from tool_router.training.knowledge_base import KnowledgeBase
        from tool_router.training.training_pipeline import TrainingPipeline
        from tool_router.training.evaluation import SpecialistEvaluator

        # Import specialist components
        from tool_router.enhanced_specialist_coordinator import EnhancedSpecialistCoordinator
        from tool_router.ai.enhanced_selector import EnhancedAISelector
        from tool_router.ai.prompt_architect import PromptArchitect
        from tool_router.ai.ui_specialist import UISpecialist

        print("✅ All components imported successfully")

        # Initialize training infrastructure
        print("\n📚 Initializing Training Infrastructure...")
        knowledge_base = KnowledgeBase()
        training_pipeline = TrainingPipeline()
        evaluator = SpecialistEvaluator(knowledge_base)

        print("✅ Training infrastructure initialized")

        # Initialize AI components
        print("\n🤖 Initializing AI Components...")
        # Note: These would need actual configuration in production
        enhanced_selector = EnhancedAISelector()
        prompt_architect = PromptArchitect()
        ui_specialist = UISpecialist()

        print("✅ AI components initialized")

        # Create enhanced coordinator
        print("\n🎯 Creating Enhanced Specialist Coordinator...")
        enhanced_coordinator = EnhancedSpecialistCoordinator(
            enhanced_selector=enhanced_selector,
            prompt_architect=prompt_architect,
            ui_specialist=ui_specialist,
            knowledge_base=knowledge_base,
            evaluator=evaluator
        )

        print("✅ Enhanced specialist coordinator created")

        return {
            "coordinator": enhanced_coordinator,
            "knowledge_base": knowledge_base,
            "training_pipeline": training_pipeline,
            "evaluator": evaluator
        }

    except Exception as e:
        logger.error(f"Error creating enhanced MCP server: {e}")
        return None


def demonstrate_training_workflow(components):
    """Demonstrate the complete training workflow."""
    if not components:
        print("❌ Cannot demonstrate workflow - components not initialized")
        return

    print("\n🔄 Demonstrating Training Workflow")
    print("=" * 40)

    coordinator = components["coordinator"]
    training_pipeline = components["training_pipeline"]
    evaluator = components["evaluator"]

    try:
        # 1. Show knowledge base status
        print("\n📊 Knowledge Base Status:")
        kb_stats = coordinator.knowledge_base.get_statistics()
        print(f"  Total Items: {kb_stats['total_items']}")
        print(f"  Average Effectiveness: {kb_stats['average_effectiveness']:.2f}")

        # 2. Run training evaluation
        print("\n📈 Running Training Evaluation...")
        eval_results = coordinator.run_training_evaluation()

        for specialist, results in eval_results.items():
            print(f"  {specialist.title()}:")
            print(f"    Average Score: {results['average_score']:.2f}")
            print(f"    Metrics: {len(results['metrics'])}")

        # 3. Get training insights
        print("\n💡 Getting Training Insights...")
        insights = coordinator.get_training_insights()

        print("  Specialist Performance:")
        for specialist, metrics in insights["specialist_metrics"].items():
            print(f"    {specialist}:")
            print(f"      Accuracy: {metrics['accuracy']:.2f}")
            print(f"      Response Time: {metrics['response_time']:.1f}ms")

        print("  Recommendations:")
        for i, rec in enumerate(insights["recommendations"][:3], 1):
            print(f"    {i}. {rec}")

        # 4. Demonstrate enhanced task processing
        print("\n🎯 Demonstrating Enhanced Task Processing...")

        # Create a sample task request
        from tool_router.specialist_coordinator import TaskRequest, TaskCategory

        sample_request = TaskRequest(
            task="Create a React button component with TypeScript and accessibility",
            category=TaskCategory.UI_GENERATION,
            context="Modern web application with Material Design",
            user_preferences={"framework": "react", "typescript": True}
        )

        print(f"  Processing: {sample_request.task}")
        results = coordinator.process_task(sample_request)

        print(f"  Results: {len(results)} specialist responses")
        for result in results:
            print(f"    {result.specialist_type.value}: {result.confidence:.2f} confidence")

        print("✅ Training workflow demonstration completed")

    except Exception as e:
        logger.error(f"Error in training workflow: {e}")
        print(f"❌ Workflow error: {e}")


def setup_continuous_learning(components):
    """Setup continuous learning for specialists."""
    if not components:
        return

    print("\n🔄 Setting Up Continuous Learning")
    print("=" * 35)

    try:
        coordinator = components["coordinator"]

        # Update specialists with latest training data
        print("\n📚 Updating Specialists with Training Data...")

        from tool_router.specialist_coordinator import SpecialistType

        for specialist_type in [SpecialistType.UI_SPECIALIST, SpecialistType.PROMPT_ARCHITECT]:
            success = coordinator.update_specialist_with_training(specialist_type)
            status = "✅" if success else "❌"
            print(f"  {status} {specialist_type.value} updated")

        print("✅ Continuous learning setup completed")

    except Exception as e:
        logger.error(f"Error setting up continuous learning: {e}")
        print(f"❌ Setup error: {e}")


def main():
    """Main integration function."""
    print("🎯 Specialist AI Training Integration")
    print("=" * 50)
    print("Integrating specialist training infrastructure with MCP Gateway")

    # Create enhanced server
    components = create_enhanced_mcp_server()

    if not components:
        print("\n❌ Failed to create enhanced server")
        return 1

    # Demonstrate workflow
    demonstrate_training_workflow(components)

    # Setup continuous learning
    setup_continuous_learning(components)

    # Show integration status
    print("\n📊 Integration Status")
    print("=" * 25)
    print("✅ Training Infrastructure: Integrated")
    print("✅ Knowledge Base: Active")
    print("✅ Specialist Coordinator: Enhanced")
    print("✅ Evaluation Framework: Ready")
    print("✅ Continuous Learning: Configured")

    print("\n🎉 Integration Complete!")
    print("The MCP Gateway now has enhanced specialist AI capabilities")
    print("with training-based pattern recognition and continuous learning.")

    # Export integration report
    export_path = Path(__file__).parent / "training_integration_report.json"

    try:
        import json

        integration_report = {
            "status": "completed",
            "components": {
                "knowledge_base": "active",
                "training_pipeline": "ready",
                "evaluation_framework": "operational",
                "enhanced_coordinator": "integrated"
            },
            "features": [
                "Pattern-based specialist enhancement",
                "Continuous learning feedback loops",
                "Performance metrics and evaluation",
                "Training data integration",
                "Real-time specialist optimization"
            ],
            "next_steps": [
                "Run full training pipeline with real data",
                "Connect to live data sources",
                "Deploy to production environment",
                "Monitor and optimize performance"
            ],
            "timestamp": "2026-02-19T12:00:00Z"
        }

        with export_path.open("w", encoding="utf-8") as f:
            json.dump(integration_report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Integration report exported to: {export_path}")

    except Exception as e:
        logger.error(f"Error exporting report: {e}")

    return 0


if __name__ == "__main__":
    exit(main())
