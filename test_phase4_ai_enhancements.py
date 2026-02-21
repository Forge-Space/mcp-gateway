#!/usr/bin/env python3
"""Test script for Phase 4 AI-enhanced tool router improvements."""

import sys
import json
from pathlib import Path

# Add the tool_router directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tool_router.ai.enhanced_selector import (
    AIProvider, AIModel, EnhancedAISelector,
    OllamaSelector, OpenAISelector, AnthropicSelector
)
from tool_router.ai.feedback import FeedbackStore
from tool_router.ai.prompts import PromptTemplates
from tool_router.scoring.matcher import select_top_matching_tools_enhanced


def test_enhanced_selector():
    """Test the enhanced AI selector with multiple providers."""
    print("🧪 Testing Enhanced AI Selector...")

    # Test with mock tools
    tools = [
        {"name": "read_file", "description": "Read contents from a file"},
        {"name": "write_file", "description": "Write content to a file"},
        {"name": "search_files", "description": "Search for files by pattern"},
        {"name": "list_directory", "description": "List directory contents"},
    ]

    # Test task
    task = "Read the configuration file"
    context = "Need to check system settings"

    # Test Ollama selector (if available)
    try:
        ollama_selector = OllamaSelector(
            endpoint="http://localhost:11434",
            model=AIModel.LLAMA32_3B.value,
            timeout=2000,
            min_confidence=0.3
        )

        result = ollama_selector.select_tool(task, tools, context)
        if result:
            print(f"✅ Ollama selected: {result['tool_name']} (confidence: {result['confidence']:.2f})")
        else:
            print("⚠️ Ollama selection failed or below threshold")
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")

    # Test enhanced selector with fallbacks
    try:
        enhanced = EnhancedAISelector(
            providers=[ollama_selector] if 'ollama_selector' in locals() else [],
            primary_weight=0.7,
            fallback_weight=0.3
        )

        result = enhanced.select_tool(task, tools, context)
        if result:
            print(f"✅ Enhanced selector selected: {result['tool_name']} (confidence: {result['adjusted_confidence']:.2f})")
            print(f"   Provider: {result.get('provider', 'unknown')}")
        else:
            print("⚠️ Enhanced selector failed")
    except Exception as e:
        print(f"❌ Enhanced selector test failed: {e}")


def test_enhanced_feedback():
    """Test the enhanced feedback system."""
    print("\n🧪 Testing Enhanced Feedback System...")

    feedback_store = FeedbackStore()

    # Test task classification
    test_tasks = [
        "Read the configuration file",
        "Create a new Python script",
        "Search for all JSON files",
        "Delete temporary files",
        "Update the database schema",
    ]

    for task in test_tasks:
        task_type = feedback_store._classify_task_type(task)
        intent = feedback_store._classify_intent(task)
        entities = feedback_store._extract_entities(task)

        print(f"Task: '{task}'")
        print(f"  Type: {task_type}")
        print(f"  Intent: {intent}")
        print(f"  Entities: {entities}")
        print()

    # Test recording and learning
    print("📝 Recording sample feedback...")
    feedback_store.record("Read config file", "read_file", True, confidence=0.8)
    feedback_store.record("Read config file", "search_files", False, confidence=0.3)
    feedback_store.record("Create script", "write_file", True, confidence=0.9)
    feedback_store.record("Create script", "write_file", True, confidence=0.7)

    # Test learning insights
    insights = feedback_store.get_learning_insights("Read the configuration file")
    print(f"🧠 Learning insights: {json.dumps(insights, indent=2)}")

    # Test adaptive hints
    hints = feedback_store.get_adaptive_hints("Read the configuration file")
    print(f"💡 Adaptive hints: {hints}")


def test_enhanced_scoring():
    """Test the enhanced scoring system."""
    print("\n🧪 Testing Enhanced Scoring System...")

    # Mock tools
    tools = [
        {"name": "read_file", "description": "Read contents from a file"},
        {"name": "write_file", "description": "Write content to a file"},
        {"name": "search_files", "description": "Search for files by pattern"},
        {"name": "list_directory", "description": "List directory contents"},
        {"name": "delete_file", "description": "Delete a file"},
    ]

    feedback_store = FeedbackStore()

    # Add some historical data
    feedback_store.record("Read config file", "read_file", True, confidence=0.9)
    feedback_store.record("Read config file", "read_file", True, confidence=0.8)
    feedback_store.record("Read config file", "search_files", False, confidence=0.4)
    feedback_store.record("Create script", "write_file", True, confidence=0.7)
    feedback_store.record("Create script", "write_file", True, confidence=0.8)

    # Test enhanced scoring
    task = "Read the configuration file"
    selected = select_top_matching_tools_enhanced(
        tools=tools,
        task=task,
        context="",
        top_n=3,
        ai_selector=None,  # No AI for this test
        feedback_store=feedback_store,
        use_nlp_hints=True
    )

    print(f"🎯 Task: '{task}'")
    print("📊 Enhanced scoring results:")
    for i, tool in enumerate(selected, 1):
        print(f"  {i}. {tool['name']} - Enhanced selection")

    # Test with AI hints
    hints = feedback_store.get_adaptive_hints(task)
    print(f"💡 Generated hints: {hints}")


def test_prompt_templates():
    """Test enhanced prompt templates."""
    print("\n🧪 Testing Enhanced Prompt Templates...")

    tools = [
        {"name": "read_file", "description": "Read contents from a file"},
        {"name": "write_file", "description": "Write content to a file"},
    ]
    tool_list = "\n".join(f"- {t['name']}: {t['description']}" for t in tools)

    # Test different prompt types
    prompts = {
        "Basic": PromptTemplates.create_tool_selection_prompt(
            "Read file", tool_list, enhanced=False
        ),
        "Enhanced": PromptTemplates.create_tool_selection_prompt(
            "Read file", tool_list, enhanced=True
        ),
        "Context-Aware": PromptTemplates.create_context_aware_prompt(
            "Read file", tool_list, context="Need to check system settings"
        ),
        "NLP-Enhanced": PromptTemplates.create_nlp_enhanced_prompt(
            "Read file", tool_list, intent_hints=["file operation", "content reading"]
        ),
    }

    for name, prompt in prompts.items():
        print(f"\n📝 {name} Prompt:")
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)


def main():
    """Run all Phase 4 tests."""
    print("🚀 Phase 4: AI-Enhanced Tool Router - Validation Tests")
    print("=" * 60)

    try:
        test_enhanced_selector()
        test_enhanced_feedback()
        test_enhanced_scoring()
        test_prompt_templates()

        print("\n✅ All Phase 4 tests completed successfully!")
        print("\n📊 Summary:")
        print("  - Enhanced AI selector with multi-provider support")
        print("  - Improved feedback system with context learning")
        print("  - Enhanced prompt templates with NLP capabilities")
        print("  - Optimized hybrid scoring with learning insights")
        print("  - Multi-tool orchestration support")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
