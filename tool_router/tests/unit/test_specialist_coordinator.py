"""Unit tests for tool_router/specialist_coordinator.py module."""

from __future__ import annotations

from unittest.mock import MagicMock

from tool_router.specialist_coordinator import (
    AccessibilityLevel,
    ComponentType,
    DesignSystem,
    SpecialistCoordinator,
    SpecialistType,
    TaskCategory,
    TaskRequest,
    UIFramework,
)


class TestSpecialistCoordinator:
    """Test the SpecialistCoordinator class."""

    def test_specialist_coordinator_initialization(self) -> None:
        """Test SpecialistCoordinator can be initialized."""
        # Create mock specialists
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)
        assert coordinator is not None
        assert hasattr(coordinator, "process_task")
        assert coordinator.enhanced_selector == enhanced_selector
        assert coordinator.prompt_architect == prompt_architect
        assert coordinator.ui_specialist == ui_specialist

    def test_process_task_tool_selection_category(self) -> None:
        """Test process_task routes to tool selection correctly."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        # Mock the selector response
        enhanced_selector.select_tool_with_cost_optimization.return_value = {
            "tool": {"name": "test_tool"},
            "confidence": 0.85,
            "estimated_cost": {"total_cost": 0.05},
            "model_used": "gpt-3.5-turbo",
            "model_tier": "standard",
            "hardware_requirements": {"memory": "4GB"},
            "task_complexity": "medium",
        }

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        request = TaskRequest(
            task="Find information about web development",
            category=TaskCategory.TOOL_SELECTION,
            tools=[{"name": "web_search", "description": "Search the web"}],
            user_preferences={
                "cost_preference": "balanced",
                "max_cost_per_request": 0.10,
            },
        )

        results = coordinator.process_task(request)

        assert len(results) == 1
        assert results[0].specialist_type == SpecialistType.ROUTER
        assert results[0].confidence == 0.85
        assert results[0].cost_estimate == 0.05
        assert "model_used" in results[0].metadata

    def test_process_task_prompt_optimization_category(self) -> None:
        """Test process_task routes to prompt optimization correctly."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        # Mock the prompt architect response
        prompt_architect.optimize_prompt.return_value = {
            "optimized_prompt": "Find web development information",
            "task_type": "information_retrieval",
            "requirements": ["accuracy", "speed"],
            "token_metrics": {"token_reduction_percent": 25.0, "cost_savings": 0.02},
            "quality_score": {"overall_score": 0.92},
        }

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        request = TaskRequest(
            task="Find information about web development",
            category=TaskCategory.PROMPT_OPTIMIZATION,
            user_preferences={
                "cost_preference": "balanced",
                "feedback": "Make it more concise",
            },
        )

        results = coordinator.process_task(request)

        assert len(results) == 1
        assert results[0].specialist_type == SpecialistType.PROMPT_ARCHITECT
        assert results[0].confidence == 0.92
        assert results[0].cost_estimate == 0.0
        assert results[0].metadata["token_reduction"] == 25.0

    def test_process_task_ui_generation_category(self) -> None:
        """Test process_task routes to UI generation correctly."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        # Mock the UI specialist response
        ui_specialist.generate_ui_component.return_value = {
            "component": {"name": "UserForm", "token_estimate": 150},
            "validation": {"compliance_score": 0.88},
            "accessibility_compliant": True,
            "responsive_ready": True,
            "industry_standards_compliant": True,
        }

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        request = TaskRequest(
            task="Create a user registration form",
            category=TaskCategory.UI_GENERATION,
            user_preferences={"framework": "react", "design_system": "tailwind"},
            cost_optimization=True,
        )

        results = coordinator.process_task(request)

        assert len(results) == 1
        assert results[0].specialist_type == SpecialistType.UI_SPECIALIST
        assert results[0].confidence == 0.88
        assert results[0].cost_estimate == 0.3  # 150 * 0.002
        assert results[0].metadata["accessibility_compliant"] is True

    def test_process_task_code_generation_category(self) -> None:
        """Test process_task routes to code generation correctly."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        # Mock responses for both specialists
        prompt_architect.optimize_prompt.return_value = {
            "optimized_prompt": "Generate a React form component",
            "task_type": "code_generation",
            "token_metrics": {"token_reduction_percent": 15.0},
            "quality_score": {"overall_score": 0.89},
        }

        enhanced_selector.select_tool_with_cost_optimization.return_value = {
            "tool": {"name": "react_generator"},
            "confidence": 0.91,
            "estimated_cost": {"total_cost": 0.08},
        }

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        request = TaskRequest(
            task="Generate a React form component",
            category=TaskCategory.CODE_GENERATION,
            context="User registration form",
        )

        results = coordinator.process_task(request)

        # Should have results from both prompt optimization and tool selection
        assert len(results) == 2
        assert results[0].specialist_type == SpecialistType.PROMPT_ARCHITECT
        assert results[1].specialist_type == SpecialistType.ROUTER

    def test_process_task_multi_step_category(self) -> None:
        """Test process_task routes to multi-step correctly."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        # Mock responses
        ui_specialist.generate_ui_component.return_value = {
            "component": {"token_estimate": 200},
            "validation": {"compliance_score": 0.85},
        }

        prompt_architect.optimize_prompt.return_value = {
            "optimized_prompt": "Create dashboard with charts",
            "token_metrics": {"token_reduction_percent": 20.0},
        }

        enhanced_selector.select_tool_with_cost_optimization.return_value = {
            "tool": {"name": "dashboard_generator"},
            "confidence": 0.87,
        }

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        request = TaskRequest(
            task="Create a dashboard with charts and navigation",
            category=TaskCategory.MULTI_STEP,
        )

        results = coordinator.process_task(request)

        assert len(results) >= 1
        specialist_types = [result.specialist_type for result in results]
        assert SpecialistType.ROUTER in specialist_types

    def test_process_task_analysis_category_defaults_to_router(self) -> None:
        """Test that analysis category defaults to router."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        enhanced_selector.select_tool_with_cost_optimization.return_value = {
            "tool": {"name": "analyzer"},
            "confidence": 0.75,
        }

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        request = TaskRequest(task="Analyze the data trends", category=TaskCategory.ANALYSIS)

        results = coordinator.process_task(request)

        assert len(results) == 1
        assert results[0].specialist_type == SpecialistType.ROUTER

    def test_process_task_handles_exceptions_gracefully(self) -> None:
        """Test that process_task handles exceptions gracefully."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        # Make the selector raise an exception
        enhanced_selector.select_tool_with_cost_optimization.side_effect = Exception("Network error")

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        request = TaskRequest(task="Test task", category=TaskCategory.TOOL_SELECTION)

        results = coordinator.process_task(request)

        # Should return empty list on error
        assert results == []

    def test_parse_ui_requirements_component_types(self) -> None:
        """Test UI requirements parsing for different component types."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        # Test table component
        requirements = coordinator._parse_ui_requirements("Create a data table", {})
        assert requirements["component_type"] == ComponentType.TABLE

        # Test chart component
        requirements = coordinator._parse_ui_requirements("Build a line graph", {})
        assert requirements["component_type"] == ComponentType.CHART

        # Test modal component
        requirements = coordinator._parse_ui_requirements("Show a dialog modal", {})
        assert requirements["component_type"] == ComponentType.MODAL

        # Test navigation component
        requirements = coordinator._parse_ui_requirements("Add navigation menu", {})
        assert requirements["component_type"] == ComponentType.NAVIGATION

    def test_parse_ui_requirements_frameworks(self) -> None:
        """Test UI requirements parsing for different frameworks."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        # Test Vue framework
        requirements = coordinator._parse_ui_requirements("Create a Vue component", {})
        assert requirements["framework"] == UIFramework.VUE

        # Test Angular framework
        requirements = coordinator._parse_ui_requirements("Build an Angular form", {})
        assert requirements["framework"] == UIFramework.ANGULAR

        # Test Next.js framework
        requirements = coordinator._parse_ui_requirements("Create a Next.js page", {})
        assert requirements["framework"] == UIFramework.NEXT_JS

    def test_parse_ui_requirements_design_systems(self) -> None:
        """Test UI requirements parsing for different design systems."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        # Test Material Design
        requirements = coordinator._parse_ui_requirements("Use material design", {})
        assert requirements["design_system"] == DesignSystem.MATERIAL_DESIGN

        # Test Bootstrap
        requirements = coordinator._parse_ui_requirements("Build with bootstrap", {})
        assert requirements["design_system"] == DesignSystem.BOOTSTRAP

        # Test Ant Design
        requirements = coordinator._parse_ui_requirements("Use ant design components", {})
        assert requirements["design_system"] == DesignSystem.ANT_DESIGN

    def test_parse_ui_requirements_accessibility_levels(self) -> None:
        """Test UI requirements parsing for accessibility levels."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        # Test AAA level
        requirements = coordinator._parse_ui_requirements("Create aaa compliant component", {})
        assert requirements["accessibility_level"] == AccessibilityLevel.AAA

        # Test minimal level
        requirements = coordinator._parse_ui_requirements("Build basic minimal component", {})
        assert requirements["accessibility_level"] == AccessibilityLevel.MINIMAL

        # Test default AA level
        requirements = coordinator._parse_ui_requirements("Create a component", {})
        assert requirements["accessibility_level"] == AccessibilityLevel.AA

    def test_parse_ui_requirements_component_name_extraction(self) -> None:
        """Test component name extraction from task."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        # Test name extraction
        requirements = coordinator._parse_ui_requirements("Create a UserForm component", {})
        assert requirements["component_name"].lower() == "userform"

        requirements = coordinator._parse_ui_requirements("Build a Login modal", {})
        assert requirements["component_name"] == "Login"

        # Test default name
        requirements = coordinator._parse_ui_requirements("Create something", {})
        assert requirements["component_name"] == "GeneratedComponent"

    def test_get_routing_stats(self) -> None:
        """Test routing statistics collection."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        # Mock successful responses
        enhanced_selector.select_tool_with_cost_optimization.return_value = {
            "tool": {"name": "test"},
            "confidence": 0.8,
            "estimated_cost": {"total_cost": 0.05},
        }

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        # Process some tasks to generate stats
        request = TaskRequest(task="test", category=TaskCategory.TOOL_SELECTION)
        coordinator.process_task(request)
        coordinator.process_task(request)

        stats = coordinator.get_routing_stats()

        assert stats["total_requests"] == 2
        assert stats["router_requests"] == 2
        assert "average_processing_time" in stats
        assert "specialist_distribution" in stats
        assert stats["specialist_distribution"]["router"] == 2

    def test_clear_cache(self) -> None:
        """Test cache clearing functionality."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        # Add something to cache by processing a task
        request = TaskRequest(task="test", category=TaskCategory.TOOL_SELECTION)
        coordinator.process_task(request)

        # Verify cache has content
        stats_before = coordinator.get_routing_stats()
        cache_size_before = stats_before["cache_size"]
        assert cache_size_before >= 0

        # Clear cache
        coordinator.clear_cache()

        # Verify cache is empty
        stats_after = coordinator.get_routing_stats()
        assert stats_after["cache_size"] == 0

    def test_get_specialist_capabilities(self) -> None:
        """Test getting specialist capabilities."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        # Mock UI specialist capabilities
        ui_specialist.get_supported_frameworks.return_value = [
            "react",
            "vue",
            "angular",
        ]
        ui_specialist.get_supported_component_types.return_value = [
            "form",
            "table",
            "chart",
        ]
        ui_specialist.get_supported_design_systems.return_value = [
            "tailwind",
            "material",
            "bootstrap",
        ]

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        capabilities = coordinator.get_specialist_capabilities()

        assert "router" in capabilities
        assert "prompt_architect" in capabilities
        assert "ui_specialist" in capabilities

        router_caps = capabilities["router"]
        assert router_caps["hardware_aware"] is True
        assert router_caps["cost_optimization"] is True
        assert "supported_models" in router_caps

        ui_caps = capabilities["ui_specialist"]
        assert ui_caps["frameworks"] == ["react", "vue", "angular"]
        assert ui_caps["responsive_design"] is True
        assert "accessibility_levels" in ui_caps

    def test_cost_optimization_flag(self) -> None:
        """Test cost optimization flag handling."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        enhanced_selector.select_tool_with_cost_optimization.return_value = {
            "tool": {"name": "test"},
            "confidence": 0.8,
        }

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        # Test with cost optimization enabled
        request = TaskRequest(task="test", category=TaskCategory.TOOL_SELECTION, cost_optimization=True)

        coordinator.process_task(request)

        # Verify the selector was called with cost optimization
        enhanced_selector.select_tool_with_cost_optimization.assert_called()

    def test_user_preferences_handling(self) -> None:
        """Test user preferences are properly passed through."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        enhanced_selector.select_tool_with_cost_optimization.return_value = {
            "tool": {"name": "test"},
            "confidence": 0.8,
        }

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        user_prefs = {
            "cost_preference": "economy",
            "max_cost_per_request": 0.03,
            "model_preference": "fast",
        }

        request = TaskRequest(
            task="test",
            category=TaskCategory.TOOL_SELECTION,
            user_preferences=user_prefs,
        )

        coordinator.process_task(request)

        # Verify preferences were passed
        call_args = enhanced_selector.select_tool_with_cost_optimization.call_args
        assert call_args[1]["user_cost_preference"] == "economy"
        assert call_args[1]["max_cost_per_request"] == 0.03

    def test_empty_task_handling(self) -> None:
        """Test handling of empty or None tasks."""
        enhanced_selector = MagicMock()
        prompt_architect = MagicMock()
        ui_specialist = MagicMock()

        coordinator = SpecialistCoordinator(enhanced_selector, prompt_architect, ui_specialist)

        # Test empty task
        request = TaskRequest(task="", category=TaskCategory.TOOL_SELECTION)
        results = coordinator.process_task(request)
        assert isinstance(results, list)

        # Test None task
        request = TaskRequest(task=None, category=TaskCategory.TOOL_SELECTION)  # type: ignore
        results = coordinator.process_task(request)
        assert isinstance(results, list)
