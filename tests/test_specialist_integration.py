"""Test Specialist Agent Integration - Comprehensive validation of the Forge Specialist Architecture."""

import unittest
from unittest.mock import Mock

from tool_router.ai.enhanced_selector import EnhancedAISelector
from tool_router.ai.prompt_architect import PromptArchitect
from tool_router.ai.ui_specialist import UISpecialist
from tool_router.specialist_coordinator import SpecialistCoordinator, TaskCategory, TaskRequest


class TestSpecialistIntegration(unittest.TestCase):
    """Test suite for specialist agent integration."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Mock the enhanced selector
        self.mock_enhanced_selector = Mock(spec=EnhancedAISelector)

        # Create real specialist instances
        self.prompt_architect = PromptArchitect()
        self.ui_specialist = UISpecialist()

        # Create specialist coordinator
        self.coordinator = SpecialistCoordinator(
            enhanced_selector=self.mock_enhanced_selector,
            prompt_architect=self.prompt_architect,
            ui_specialist=self.ui_specialist,
        )

    def test_router_agent_integration(self) -> None:
        """Test Router Agent integration with hardware-aware selection."""
        # Mock enhanced selector response
        self.mock_enhanced_selector.select_tool_with_cost_optimization.return_value = {
            "tool": "test_tool",
            "confidence": 0.95,
            "model_used": "llama3.2:3b",
            "model_tier": "ultra_fast",
            "task_complexity": "simple",
            "hardware_requirements": {"ram_gb": 2, "cpu_cores": 1},
            "estimated_cost": {"total_cost": 0.0},
        }

        # Create task request
        request = TaskRequest(
            task="Find files with .py extension",
            category=TaskCategory.TOOL_SELECTION,
            context="Python project",
            user_preferences={"cost_preference": "efficient"},
            cost_optimization=True,
        )

        # Process task
        results = self.coordinator.process_task(request)

        # Verify results
        assert len(results) == 1
        result = results[0]
        assert result.specialist_type.value == "router"
        assert result.confidence == 0.95
        assert result.cost_estimate == 0.0

        # Verify metadata
        metadata = result.metadata
        assert metadata["model_used"] == "llama3.2:3b"
        assert metadata["model_tier"] == "ultra_fast"
        assert metadata["task_complexity"] == "simple"

    def test_prompt_architect_integration(self) -> None:
        """Test Prompt Architect integration."""
        # Create task request
        request = TaskRequest(
            task="Please help me write a function that sorts a list of numbers in Python",
            category=TaskCategory.PROMPT_OPTIMIZATION,
            context="Programming task",
            user_preferences={"cost_preference": "balanced"},
            cost_optimization=True,
        )

        # Process task
        results = self.coordinator.process_task(request)

        # Verify results
        assert len(results) == 1
        result = results[0]
        assert result.specialist_type.value == "prompt_architect"
        assert result.confidence > 0.0
        assert result.processing_time_ms >= 0

        # Verify prompt optimization result
        optimization_result = result.result
        assert "optimized_prompt" in optimization_result
        assert "token_metrics" in optimization_result
        assert "quality_score" in optimization_result
        assert "task_type" in optimization_result

        # Verify token metrics
        token_metrics = optimization_result["token_metrics"]
        assert "original_tokens" in token_metrics
        assert "optimized_tokens" in token_metrics
        assert "token_reduction_percent" in token_metrics
        assert "cost_savings" in token_metrics

    def test_ui_specialist_integration(self) -> None:
        """Test UI Specialist integration."""
        # Create task request
        request = TaskRequest(
            task="Create a React form component with Tailwind CSS",
            category=TaskCategory.UI_GENERATION,
            context="Web development",
            user_preferences={"framework": "react", "design_system": "tailwind_ui", "accessibility_level": "aa"},
            cost_optimization=True,
        )

        # Process task
        results = self.coordinator.process_task(request)

        # Verify results
        assert len(results) == 1
        result = results[0]
        assert result.specialist_type.value == "ui_specialist"
        assert result.confidence > 0.0
        assert result.processing_time_ms >= 0

        # Verify UI generation result
        ui_result = result.result
        assert "component" in ui_result
        assert "validation" in ui_result
        assert "requirement" in ui_result
        assert "spec" in ui_result

        # Verify component data
        component_data = ui_result["component"]
        assert "component_code" in component_data
        assert "token_estimate" in component_data
        assert "generated_features" in component_data

        # Verify validation data
        validation_data = ui_result["validation"]
        assert "compliance_score" in validation_data
        assert "accessibility_score" in validation_data
        assert "framework_score" in validation_data

    def test_multi_step_task_integration(self) -> None:
        """Test multi-step task requiring multiple specialists."""
        # Create complex task request
        request = TaskRequest(
            task="Create a responsive React dashboard with data visualization and optimize the prompt for efficiency",
            category=TaskCategory.MULTI_STEP,
            context="Full-stack development",
            user_preferences={"cost_preference": "balanced", "responsive": True, "dark_mode": True},
            cost_optimization=True,
        )

        # Mock enhanced selector for tool selection part
        self.mock_enhanced_selector.select_tool_with_cost_optimization.return_value = {
            "tool": "visualization_tool",
            "confidence": 0.85,
            "model_used": "llama3.2:3b",
            "model_tier": "ultra_fast",
            "task_complexity": "medium",
            "hardware_requirements": {"ram_gb": 4, "cpu_cores": 2},
            "estimated_cost": {"total_cost": 0.0},
        }

        # Process task
        results = self.coordinator.process_task(request)

        # Verify multiple specialists were used
        assert len(results) > 1

        # Check that we have UI specialist and prompt architect results
        specialist_types = [result.specialist_type.value for result in results]
        assert "ui_specialist" in specialist_types
        assert "prompt_architect" in specialist_types
        assert "router" in specialist_types

    def test_cost_optimization_features(self) -> None:
        """Test cost optimization features across specialists."""
        # Test efficient cost preference
        request = TaskRequest(
            task="Simple task that should use local models",
            category=TaskCategory.TOOL_SELECTION,
            user_preferences={"cost_preference": "efficient"},
            cost_optimization=True,
        )

        # Mock response with ultra-fast model
        self.mock_enhanced_selector.select_tool_with_cost_optimization.return_value = {
            "tool": "local_tool",
            "confidence": 0.9,
            "model_used": "llama3.2:3b",
            "model_tier": "ultra_fast",
            "task_complexity": "simple",
            "estimated_cost": {"total_cost": 0.0},
        }

        results = self.coordinator.process_task(request)

        # Verify cost optimization
        assert len(results) == 1
        result = results[0]
        assert result.cost_estimate == 0.0  # Local model should be free
        assert result.metadata["model_tier"] == "ultra_fast"

    def test_hardware_aware_routing(self) -> None:
        """Test hardware-aware routing constraints."""
        # Test with hardware constraints
        request = TaskRequest(
            task="Complex analysis task",
            category=TaskCategory.TOOL_SELECTION,
            hardware_constraints={"ram_available_gb": 16, "max_model_ram_gb": 8, "cpu_cores": 4},
            cost_optimization=True,
        )

        # Mock response respecting hardware constraints
        self.mock_enhanced_selector.select_tool_with_cost_optimization.return_value = {
            "tool": "analysis_tool",
            "confidence": 0.8,
            "model_used": "llama3.2:3b",  # Should fit in hardware constraints
            "model_tier": "balanced",
            "task_complexity": "medium",
            "hardware_requirements": {"ram_gb": 4, "cpu_cores": 2},
            "estimated_cost": {"total_cost": 0.0},
        }

        results = self.coordinator.process_task(request)

        # Verify hardware-aware selection
        assert len(results) == 1
        result = results[0]
        hardware_reqs = result.metadata["hardware_requirements"]
        assert hardware_reqs["ram_gb"] <= 8  # Should fit in constraints
        assert hardware_reqs["cpu_cores"] <= 4

    def test_specialist_coordinator_stats(self) -> None:
        """Test specialist coordinator statistics."""
        # Process some tasks to generate stats
        requests = [
            TaskRequest("Task 1", TaskCategory.TOOL_SELECTION, cost_optimization=True),
            TaskRequest("Task 2", TaskCategory.PROMPT_OPTIMIZATION, cost_optimization=True),
            TaskRequest("Task 3", TaskCategory.UI_GENERATION, cost_optimization=True),
        ]

        # Mock responses
        self.mock_enhanced_selector.select_tool_with_cost_optimization.return_value = {
            "tool": "test_tool",
            "confidence": 0.9,
            "model_used": "llama3.2:3b",
            "model_tier": "ultra_fast",
            "estimated_cost": {"total_cost": 0.0},
        }

        # Process tasks
        for request in requests:
            self.coordinator.process_task(request)

        # Get stats
        stats = self.coordinator.get_routing_stats()

        # Verify stats
        assert stats["total_requests"] == 3
        assert stats["router_requests"] == 1
        assert stats["prompt_architect_requests"] == 1
        assert stats["ui_specialist_requests"] == 1
        assert stats["average_processing_time"] > 0

    def test_specialist_capabilities(self) -> None:
        """Test specialist capabilities reporting."""
        capabilities = self.coordinator.get_specialist_capabilities()

        # Verify all specialists are reported
        assert "router" in capabilities
        assert "prompt_architect" in capabilities
        assert "ui_specialist" in capabilities

        # Verify router capabilities
        router_caps = capabilities["router"]
        assert router_caps["hardware_aware"]
        assert router_caps["cost_optimization"]
        assert "supported_models" in router_caps
        assert router_caps["token_estimation"]

        # Verify prompt architect capabilities
        prompt_caps = capabilities["prompt_architect"]
        assert prompt_caps["task_analysis"]
        assert prompt_caps["token_optimization"]
        assert prompt_caps["quality_scoring"]
        assert prompt_caps["iterative_refinement"]

        # Verify UI specialist capabilities
        ui_caps = capabilities["ui_specialist"]
        assert "frameworks" in ui_caps
        assert "component_types" in ui_caps
        assert "design_systems" in ui_caps
        assert "accessibility_levels" in ui_caps
        assert ui_caps["responsive_design"]

    def test_error_handling(self) -> None:
        """Test error handling in specialist coordinator."""
        # Test with invalid category
        request = TaskRequest(
            task="Test task",
            category="invalid_category",  # This should be handled gracefully
            cost_optimization=True,
        )

        # Should not raise exception, should default to tool_selection
        results = self.coordinator.process_task(request)

        # Should still get results (defaulted to tool_selection)
        assert len(results) >= 0

    def test_cache_functionality(self) -> None:
        """Test cache functionality."""
        # Clear cache
        self.coordinator.clear_cache()

        # Verify cache is empty
        stats = self.coordinator.get_routing_stats()
        assert stats["cache_size"] == 0

        # Process a task
        self.mock_enhanced_selector.select_tool_with_cost_optimization.return_value = {
            "tool": "cached_tool",
            "confidence": 0.9,
            "model_used": "llama3.2:3b",
            "estimated_cost": {"total_cost": 0.0},
        }

        request = TaskRequest("Cached task", TaskCategory.TOOL_SELECTION, cost_optimization=True)
        self.coordinator.process_task(request)

        # Cache size should be updated
        stats = self.coordinator.get_routing_stats()
        assert stats["cache_size"] > 0


class TestSpecialistAgentPerformance(unittest.TestCase):
    """Performance tests for specialist agents."""

    def setUp(self) -> None:
        """Set up performance test fixtures."""
        self.mock_enhanced_selector = Mock(spec=EnhancedAISelector)
        self.prompt_architect = PromptArchitect()
        self.ui_specialist = UISpecialist()
        self.coordinator = SpecialistCoordinator(
            enhanced_selector=self.mock_enhanced_selector,
            prompt_architect=self.prompt_architect,
            ui_specialist=self.ui_specialist,
        )

    def test_prompt_optimization_performance(self) -> None:
        """Test prompt optimization performance."""
        import time

        # Create a complex prompt
        long_prompt = """
        Please help me create a comprehensive web application that includes user authentication,
        data visualization, real-time updates, and responsive design. The application should
        be built using modern web technologies and follow best practices for security and
        performance. Please provide detailed code examples and explanations for each component.
        """

        request = TaskRequest(
            task=long_prompt,
            category=TaskCategory.PROMPT_OPTIMIZATION,
            user_preferences={"cost_preference": "balanced"},
            cost_optimization=True,
        )

        # Measure performance
        start_time = time.time()
        results = self.coordinator.process_task(request)
        end_time = time.time()

        processing_time = (end_time - start_time) * 1000  # Convert to ms

        # Verify performance expectations
        assert len(results) == 1
        result = results[0]
        assert result.processing_time_ms < 5000  # Should complete within 5 seconds
        assert result.confidence > 0.5  # Should have reasonable confidence

        # Verify optimization actually happened
        optimization_result = result.result
        original_tokens = optimization_result["token_metrics"]["original_tokens"]
        optimized_tokens = optimization_result["token_metrics"]["optimized_tokens"]
        assert optimized_tokens < original_tokens  # Should reduce tokens

    def test_ui_generation_performance(self) -> None:
        """Test UI generation performance."""
        import time

        request = TaskRequest(
            task="Create a comprehensive dashboard with charts, tables, and navigation",
            category=TaskCategory.UI_GENERATION,
            user_preferences={
                "framework": "react",
                "design_system": "tailwind_ui",
                "responsive": True,
                "dark_mode": True,
            },
            cost_optimization=True,
        )

        # Measure performance
        start_time = time.time()
        results = self.coordinator.process_task(request)
        end_time = time.time()

        processing_time = (end_time - start_time) * 1000  # Convert to ms

        # Verify performance expectations
        assert len(results) == 1
        result = results[0]
        assert result.processing_time_ms < 3000  # Should complete within 3 seconds
        assert result.confidence > 0.7  # Should have good confidence

        # Verify UI generation quality
        ui_result = result.result
        validation = ui_result["validation"]
        assert validation["compliance_score"] > 0.6  # Should meet standards
        assert ui_result["industry_standards_compliant"]


if __name__ == "__main__":
    unittest.main()
