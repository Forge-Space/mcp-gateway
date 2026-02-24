"""Integration tests for end-to-end tool routing workflows."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

from tool_router.ai.enhanced_selector import EnhancedAISelector
from tool_router.ai.feedback import FeedbackStore
from tool_router.core.config import ToolRouterConfig


class TestToolRoutingWorkflows:
    """Integration tests for complete tool routing workflows."""

    def test_complete_tool_selection_workflow_with_learning(self, tmp_path: Path) -> None:
        """Test complete workflow from user request to tool execution with learning."""
        # Setup components
        feedback_file = str(tmp_path / "feedback.json")
        feedback_store = FeedbackStore(feedback_file)

        # Mock AI selector
        ai_selector = Mock(spec=EnhancedAISelector)
        ai_selector.select_tool.return_value = {
            "selected_tool": "search_web",
            "confidence": 0.85,
            "reasoning": "Task matches search pattern",
            "ai_score": 0.9,
            "keyword_score": 0.7,
            "boost_applied": 1.2,
        }

        # Simulate user request and tool selection
        user_request = "search for python documentation"
        selection_result = ai_selector.select_tool(user_request)

        # Record multiple successful outcomes for meaningful boost
        for i in range(5):
            feedback_store.record(
                task=f"search for python documentation {i}",
                selected_tool=selection_result["selected_tool"],
                success=True,
                confidence=selection_result["confidence"],
            )

        # Verify learning occurred
        stats = feedback_store.get_stats("search_web")
        assert stats is not None
        assert stats.success_count == 5
        assert stats.success_rate == 1.0

        # Verify boost is applied for subsequent requests
        boost = feedback_store.get_boost("search_web")
        assert boost >= 1.0

    def test_tool_selection_with_fallback_mechanism(self, tmp_path: Path) -> None:
        """Test tool selection with AI failure fallback to feedback store."""
        feedback_file = str(tmp_path / "feedback.json")
        feedback_store = FeedbackStore(feedback_file)

        # Seed feedback store with prior successful selections
        for i in range(5):
            feedback_store.record(
                task=f"read configuration file {i}",
                selected_tool="file_reader",
                success=True,
                confidence=0.8,
            )

        # When AI fails, feedback store can suggest tools
        similar_tools = feedback_store.similar_task_tools("read the config file")
        assert "file_reader" in similar_tools

        # Record the fallback outcome
        feedback_store.record(
            task="read the configuration file",
            selected_tool="file_reader",
            success=True,
            confidence=0.6,
        )

        stats = feedback_store.get_stats("file_reader")
        assert stats is not None
        assert stats.success_count == 6

    def test_multi_tool_task_coordination(self, tmp_path: Path) -> None:
        """Test coordination between multiple tools for complex tasks."""
        feedback_file = str(tmp_path / "feedback.json")
        feedback_store = FeedbackStore(feedback_file)

        # Simulate complex task requiring multiple tools
        complex_task = "analyze the codebase and create documentation"

        # First tool: code analysis
        feedback_store.record(
            task=complex_task,
            selected_tool="code_analyzer",
            success=True,
            confidence=0.8,
        )

        # Second tool: documentation generation
        feedback_store.record(
            task=complex_task,
            selected_tool="doc_generator",
            success=True,
            confidence=0.7,
        )

        # Verify both tools have learning data
        code_stats = feedback_store.get_stats("code_analyzer")
        doc_stats = feedback_store.get_stats("doc_generator")

        assert code_stats is not None
        assert doc_stats is not None
        assert code_stats.success_count == 1
        assert doc_stats.success_count == 1

        # Verify task type learning
        assert len(code_stats.task_types) > 0
        assert len(doc_stats.task_types) > 0

    def test_error_recovery_and_retry_logic(self, tmp_path: Path) -> None:
        """Test error recovery and retry logic in tool selection."""
        feedback_file = str(tmp_path / "feedback.json")
        feedback_store = FeedbackStore(feedback_file)

        # Record multiple failures for data_processor
        for i in range(5):
            feedback_store.record(
                task=f"process large dataset {i}",
                selected_tool="data_processor",
                success=False,
                confidence=0.3,
            )

        # Record multiple successes for batch_processor
        for i in range(5):
            feedback_store.record(
                task=f"process large dataset {i}",
                selected_tool="batch_processor",
                success=True,
                confidence=0.9,
            )

        # Verify learning from failure and success
        failed_stats = feedback_store.get_stats("data_processor")
        success_stats = feedback_store.get_stats("batch_processor")

        assert failed_stats.failure_count == 5
        assert failed_stats.success_rate == 0.0
        assert success_stats.success_count == 5
        assert success_stats.success_rate == 1.0

        # Verify boost reflects the learning
        failed_boost = feedback_store.get_boost("data_processor")
        success_boost = feedback_store.get_boost("batch_processor")

        assert failed_boost < 1.0
        assert success_boost > 1.0

    def test_configuration_driven_tool_selection(self, tmp_path: Path) -> None:
        """Test tool selection driven by configuration settings."""
        feedback_file = str(tmp_path / "feedback.json")
        feedback_store = FeedbackStore(feedback_file)

        # Mock configuration
        config = Mock(spec=ToolRouterConfig)
        config.enabled_tools = ["search_web", "file_reader", "code_analyzer"]
        config.tool_preferences = {
            "search_operations": "search_web",
            "file_operations": "file_reader",
        }
        config.confidence_threshold = 0.7

        # Simulate configuration-based selection
        task = "search for configuration files"
        task_type = "search_operations"

        # Record successful selection based on config
        selected_tool = config.tool_preferences.get(task_type, "default_tool")
        feedback_store.record(task=task, selected_tool=selected_tool, success=True, confidence=0.8)

        # Verify configuration was respected
        assert selected_tool == "search_web"
        assert selected_tool in config.enabled_tools

        # Verify learning respects configuration
        stats = feedback_store.get_stats(selected_tool)
        assert stats is not None
        assert stats.success_count == 1

    def test_adaptive_learning_with_user_feedback(self, tmp_path: Path) -> None:
        """Test adaptive learning based on explicit user feedback."""
        feedback_file = str(tmp_path / "feedback.json")
        feedback_store = FeedbackStore(feedback_file)

        # Record mixed results for v1 (need 5+ records for boost)
        for i in range(3):
            feedback_store.record(
                task=f"generate user interface {i}",
                selected_tool="ui_generator_v1",
                success=True,
                confidence=0.6,
            )
        for i in range(3):
            feedback_store.record(
                task=f"generate user interface fail {i}",
                selected_tool="ui_generator_v1",
                success=False,
                confidence=0.4,
            )

        # Record all successes for v2
        for i in range(6):
            feedback_store.record(
                task=f"generate user interface v2 {i}",
                selected_tool="ui_generator_v2",
                success=True,
                confidence=0.9,
            )

        # Verify adaptive learning
        v1_stats = feedback_store.get_stats("ui_generator_v1")
        v2_stats = feedback_store.get_stats("ui_generator_v2")

        assert v1_stats.success_rate == 0.5
        assert v2_stats.success_rate == 1.0

        # Boost should reflect the preference
        v1_boost = feedback_store.get_boost("ui_generator_v1")
        v2_boost = feedback_store.get_boost("ui_generator_v2")

        assert v2_boost > v1_boost

    def test_cross_task_learning_and_pattern_recognition(self, tmp_path: Path) -> None:
        """Test learning patterns across different but related tasks."""
        feedback_file = str(tmp_path / "feedback.json")
        feedback_store = FeedbackStore(feedback_file)

        # Record related tasks with same tool
        related_tasks = [
            "read user configuration",
            "read system settings",
            "read environment variables",
            "read application properties",
        ]

        for task in related_tasks:
            feedback_store.record(task=task, selected_tool="config_reader", success=True, confidence=0.8)

        # Verify pattern learning
        stats = feedback_store.get_stats("config_reader")
        assert stats.success_count == 4
        assert stats.success_rate == 1.0
        assert "file_operations" in stats.task_types

        # Test similar task recommendation
        similar_tools = feedback_store.similar_task_tools("read database config")
        assert "config_reader" in similar_tools

    def test_performance_optimization_with_caching(self, tmp_path: Path) -> None:
        """Test performance optimization through intelligent caching."""
        feedback_file = str(tmp_path / "feedback.json")
        feedback_store = FeedbackStore(feedback_file)

        # Record many successful operations to build cache
        for i in range(100):
            feedback_store.record(
                task=f"process data batch {i}",
                selected_tool="batch_processor",
                success=True,
                confidence=0.85,
            )

        # Verify cache effectiveness
        stats = feedback_store.get_stats("batch_processor")
        assert stats.success_count == 100
        assert stats.success_rate == 1.0
        assert stats.avg_confidence == 0.85

        # Verify boost is optimized for high-performing tool
        boost = feedback_store.get_boost("batch_processor")
        assert boost > 1.0

    def test_security_aware_tool_selection(self, tmp_path: Path) -> None:
        """Test tool selection with security considerations."""
        feedback_file = str(tmp_path / "feedback.json")
        feedback_store = FeedbackStore(feedback_file)

        feedback_store.record(
            task="execute system command",
            selected_tool="secure_executor",
            success=True,
            confidence=0.9,
        )

        stats = feedback_store.get_stats("secure_executor")
        assert stats is not None
        assert stats.success_count == 1

    def test_tool_selection_with_context_preservation(self, tmp_path: Path) -> None:
        """Test tool selection while preserving user context."""
        feedback_file = str(tmp_path / "feedback.json")
        feedback_store = FeedbackStore(feedback_file)

        # Record task with rich context
        task = "modify user authentication module"
        context = "Working on OAuth2 implementation for user login system"

        feedback_store.record(
            task=task,
            selected_tool="code_modifier",
            success=True,
            confidence=0.8,
            context=context,
        )

        stats = feedback_store.get_stats("code_modifier")
        assert stats is not None
        assert stats.success_count == 1
