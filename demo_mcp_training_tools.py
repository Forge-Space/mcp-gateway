#!/usr/bin/env python3
"""Demo script for MCP Training Tools.

This script demonstrates how to use the MCP tools for specialist AI training
infrastructure, including training management, knowledge base operations, and evaluation.
"""

import logging
import sys
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def demo_training_manager():
    """Demonstrate training manager MCP tool."""
    print("\n🔧 Training Manager Tool Demo")
    print("=" * 40)

    try:
        from tool_router.mcp_tools.training_manager import training_manager_handler

        print("1. Starting a training run...")
        start_result = training_manager_handler({
            "action": "start_training",
            "sources": [
                {
                    "name": "react_docs",
                    "type": "web",
                    "url": "https://react.dev",
                    "category": "react_pattern"
                }
            ]
        })
        print(f"   Result: {start_result.get('message', 'Unknown')}")

        if "run_id" in start_result:
            run_id = start_result["run_id"]

            print(f"\n2. Getting training status for run {run_id}...")
            status_result = training_manager_handler({
                "action": "get_status",
                "run_id": run_id
            })
            print(f"   Status: {status_result.get('status', 'Unknown')}")

            print("\n3. Listing all training runs...")
            list_result = training_manager_handler({
                "action": "list_runs"
            })
            print(f"   Total runs: {list_result.get('total_runs', 0)}")

            print("\n4. Getting training statistics...")
            stats_result = training_manager_handler({
                "action": "get_statistics"
            })
            print(f"   Total runs: {stats_result.get('total_runs', 0)}")
            print(f"   Success rate: {stats_result.get('success_rate', 0)}%")

            print("\n5. Getting training configuration...")
            config_result = training_manager_handler({
                "action": "get_configuration"
            })
            print(f"   Default sources: {len(config_result.get('default_sources', []))}")

        print("✅ Training Manager demo completed")

    except Exception as e:
        logger.error(f"Training Manager demo failed: {e}")
        print(f"❌ Error: {e}")


def demo_knowledge_base():
    """Demonstrate knowledge base MCP tool."""
    print("\n📚 Knowledge Base Tool Demo")
    print("=" * 35)

    try:
        from tool_router.mcp_tools.knowledge_base_tool import knowledge_base_handler

        print("1. Getting available categories...")
        categories_result = knowledge_base_handler({
            "action": "get_categories"
        })
        print(f"   Categories: {len(categories_result.get('categories', []))}")

        print("\n2. Adding a new pattern...")
        add_result = knowledge_base_handler({
            "action": "add_pattern",
            "title": "React Hook Pattern",
            "description": "Modern React hook usage patterns",
            "category": "react_pattern",
            "content": "Use useState for state management, useEffect for side effects",
            "confidence": 0.9,
            "effectiveness": 0.85
        })
        print(f"   Result: {add_result.get('message', 'Unknown')}")

        if "item_id" in add_result:
            item_id = add_result["item_id"]

            print(f"\n3. Getting pattern details for ID {item_id}...")
            get_result = knowledge_base_handler({
                "action": "get_pattern",
                "item_id": item_id
            })
            print(f"   Title: {get_result.get('title', 'Unknown')}")
            print(f"   Category: {get_result.get('category', 'Unknown')}")

            print("\n4. Searching for patterns...")
            search_result = knowledge_base_handler({
                "action": "search_patterns",
                "query": "React hook",
                "limit": 5
            })
            print(f"   Found: {search_result.get('total_found', 0)} patterns")

            print("\n5. Getting patterns by category...")
            category_result = knowledge_base_handler({
                "action": "get_patterns_by_category",
                "category": "react_pattern",
                "limit": 10
            })
            print(f"   Found: {category_result.get('total_found', 0)} patterns")

            print("\n6. Getting knowledge base statistics...")
            stats_result = knowledge_base_handler({
                "action": "get_statistics"
            })
            stats = stats_result.get("statistics", {})
            print(f"   Total items: {stats.get('total_items', 0)}")
            print(f"   Average effectiveness: {stats.get('average_effectiveness', 0):.2f}")

        print("✅ Knowledge Base demo completed")

    except Exception as e:
        logger.error(f"Knowledge Base demo failed: {e}")
        print(f"❌ Error: {e}")


def demo_evaluation():
    """Demonstrate evaluation MCP tool."""
    print("\n📊 Evaluation Tool Demo")
    print("=" * 30)

    try:
        from tool_router.mcp_tools.evaluation_tool import evaluation_handler

        print("1. Getting available specialists...")
        specialists_result = evaluation_handler({
            "action": "get_specialists"
        })
        print(f"   Available specialists: {specialists_result.get('total_specialists', 0)}")

        print("\n2. Getting available metrics...")
        metrics_result = evaluation_handler({
            "action": "get_metrics"
        })
        print(f"   Available metrics: {metrics_result.get('total_metrics', 0)}")

        specialists = specialists_result.get("specialists", [])
        if specialists:
            specialist_name = specialists[0]["name"]

            print(f"\n3. Running evaluation for {specialist_name}...")
            eval_result = evaluation_handler({
                "action": "run_evaluation",
                "specialist_name": specialist_name,
                "test_cases": 5
            })
            print(f"   Result: {eval_result.get('message', 'Unknown')}")

            summary = eval_result.get("summary", {})
            print(f"   Average score: {summary.get('average_score', 0):.2f}")
            print(f"   Pass rate: {summary.get('pass_rate', 0):.2f}%")

            print("\n4. Getting evaluation history...")
            history_result = evaluation_handler({
                "action": "get_history",
                "specialist_name": specialist_name,
                "limit": 10
            })
            print(f"   History entries: {history_result.get('total_results', 0)}")

        print("\n5. Getting evaluation summary...")
        summary_result = evaluation_handler({
            "action": "get_summary"
        })
        summary = summary_result.get("summary", {})
        print(f"   Total evaluations: {summary.get('total_evaluations', 0)}")
        print(f"   Specialist performance: {len(summary.get('specialist_performance', {}))}")

        print("✅ Evaluation demo completed")

    except Exception as e:
        logger.error(f"Evaluation demo failed: {e}")
        print(f"❌ Error: {e}")


def demo_server_integration():
    """Demonstrate MCP server integration."""
    print("\n🌐 MCP Server Integration Demo")
    print("=" * 40)

    try:
        from tool_router.mcp_tools.server_integration import get_server_instance

        print("1. Getting server instance...")
        server = get_server_instance()
        print("   ✅ Server instance created")

        print("\n2. Getting server information...")
        server_info = server.get_server_info()
        print(f"   Name: {server_info.get('name')}")
        print(f"   Version: {server_info.get('version')}")
        print(f"   Tools: {server_info.get('tools')}")
        print(f"   Capabilities: {len(server_info.get('capabilities', []))}")

        print("\n3. Getting tool definitions...")
        tool_defs = server.get_tool_definitions()
        print(f"   Tool definitions: {len(tool_defs)}")

        for tool_def in tool_defs:
            print(f"   - {tool_def['name']}: {tool_def['description'][:50]}...")

        print("\n4. Performing health check...")
        health_result = server.health_check()
        print(f"   Status: {health_result.get('status')}")
        print(f"   Components: {len(health_result.get('components', {}))}")

        print("\n5. Testing tool execution...")
        if tool_defs:
            tool_name = tool_defs[0]["name"]
            print(f"   Testing tool: {tool_name}")

            # Test with a simple action
            if tool_name == "training_manager":
                result = server.execute_tool(tool_name, {"action": "get_configuration"})
                print(f"   Result: {result.get('message', 'Unknown')}")
            elif tool_name == "knowledge_base":
                result = server.execute_tool(tool_name, {"action": "get_categories"})
                print(f"   Result: {result.get('message', 'Unknown')}")
            elif tool_name == "evaluation":
                result = server.execute_tool(tool_name, {"action": "get_specialists"})
                print(f"   Result: {result.get('message', 'Unknown')}")

        print("✅ Server Integration demo completed")

    except Exception as e:
        logger.error(f"Server Integration demo failed: {e}")
        print(f"❌ Error: {e}")


def demo_complete_workflow():
    """Demonstrate complete workflow using all tools."""
    print("\n🔄 Complete Workflow Demo")
    print("=" * 35)
    print("Demonstrating end-to-end specialist training workflow")

    try:
        from tool_router.mcp_tools.server_integration import get_server_instance

        server = get_server_instance()

        print("\n1. 📊 Check system health...")
        health = server.health_check()
        print(f"   System status: {health.get('status')}")

        print("\n2. 📚 Add training patterns to knowledge base...")
        kb_tool = server.knowledge_base
        patterns_added = []

        # Add sample patterns
        sample_patterns = [
            {
                "title": "React Functional Components",
                "description": "Modern React functional component patterns",
                "category": "react_pattern",
                "content": "Use functional components with hooks for state and lifecycle",
                "confidence": 0.9,
                "effectiveness": 0.85
            },
            {
                "title": "UI Accessibility Best Practices",
                "description": "WCAG compliance patterns for UI components",
                "category": "accessibility",
                "content": "Include ARIA labels, keyboard navigation, and color contrast",
                "confidence": 0.95,
                "effectiveness": 0.9
            },
            {
                "title": "Prompt Engineering Techniques",
                "description": "Effective prompt engineering strategies",
                "category": "prompt_engineering",
                "content": "Use chain-of-thought, few-shot learning, and clear instructions",
                "confidence": 0.85,
                "effectiveness": 0.8
            }
        ]

        for pattern in sample_patterns:
            result = kb_tool.add_pattern(**pattern)
            if "item_id" in result:
                patterns_added.append(result["item_id"])

        print(f"   Added {len(patterns_added)} patterns to knowledge base")

        print("\n3. 🚀 Start training pipeline...")
        tm_tool = server.training_manager
        training_result = tm_tool.start_training_run()

        if "run_id" in training_result:
            run_id = training_result["run_id"]
            print(f"   Training run started: {run_id}")

            print("\n4. 📈 Run specialist evaluation...")
            eval_tool = server.evaluator
            specialists = eval_tool.get_available_specialists()

            if specialists["total_specialists"] > 0:
                specialist = specialists["specialists"][0]["name"]
                eval_result = eval_tool.run_evaluation(specialist)

                summary = eval_result.get("summary", {})
                print(f"   Evaluation completed for {specialist}")
                print(f"   Average score: {summary.get('average_score', 0):.2f}")
                print(f"   Pass rate: {summary.get('pass_rate', 0):.2f}%")

        print("\n5. 📊 Generate comprehensive report...")

        # Get final statistics
        kb_stats = kb_tool.get_knowledge_base_statistics()
        tm_stats = tm_tool.get_training_statistics()
        eval_summary = eval_tool.get_evaluation_summary()

        print(f"   Knowledge Base: {kb_stats.get('statistics', {}).get('total_items', 0)} items")
        print(f"   Training Runs: {tm_stats.get('total_runs', 0)} completed")
        print(f"   Evaluations: {eval_summary.get('summary', {}).get('total_evaluations', 0)} total")

        print("\n🎉 Complete workflow demo finished successfully!")

        # Export results
        export_data = {
            "demo_timestamp": "2026-02-19T12:00:00Z",
            "health_status": health.get("status"),
            "patterns_added": len(patterns_added),
            "training_runs": tm_stats.get("total_runs", 0),
            "evaluations_completed": eval_summary.get("summary", {}).get("total_evaluations", 0),
            "knowledge_base_items": kb_stats.get("statistics", {}).get("total_items", 0),
            "success": True
        }

        export_path = Path(__file__).parent / "mcp_tools_demo_results.json"
        with export_path.open("w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Results exported to: {export_path}")

    except Exception as e:
        logger.error(f"Complete workflow demo failed: {e}")
        print(f"❌ Error: {e}")


def main():
    """Run all MCP tool demos."""
    print("🚀 MCP Training Tools Demo")
    print("=" * 50)
    print("Demonstrating MCP tools for specialist AI training infrastructure")

    try:
        # Run individual demos
        demo_training_manager()
        demo_knowledge_base()
        demo_evaluation()
        demo_server_integration()
        demo_complete_workflow()

        print("\n🎊 All demos completed successfully!")
        print("The MCP training tools are ready for integration with the MCP Gateway.")

        return 0

    except Exception as e:
        logger.error(f"Demo execution failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
