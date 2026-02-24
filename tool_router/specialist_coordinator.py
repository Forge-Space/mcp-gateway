"""Specialist Coordinator - Orchestrates specialist agents for optimal task routing."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from tool_router.ai.enhanced_selector import AIModel, EnhancedAISelector
from tool_router.ai.prompt_architect import PromptArchitect
from tool_router.ai.ui_specialist import (
    AccessibilityLevel,
    ComponentType,
    DesignSystem,
    UIFramework,
    UISpecialist,
)

logger = logging.getLogger(__name__)


class SpecialistType(Enum):
    """Types of specialist agents."""

    ROUTER = "router"
    PROMPT_ARCHITECT = "prompt_architect"
    UI_SPECIALIST = "ui_specialist"


class TaskCategory(Enum):
    """Categories of tasks for specialist routing."""

    TOOL_SELECTION = "tool_selection"
    PROMPT_OPTIMIZATION = "prompt_optimization"
    UI_GENERATION = "ui_generation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    MULTI_STEP = "multi_step"


@dataclass
class TaskRequest:
    """Task request for specialist coordination."""

    task: str
    category: TaskCategory
    context: str = ""
    tools: list[dict[str, Any]] | None = None
    user_preferences: dict[str, Any] | None = None
    cost_optimization: bool = True
    hardware_constraints: dict[str, Any] | None = None


@dataclass
class SpecialistResult:
    """Result from specialist agent."""

    specialist_type: SpecialistType
    result: dict[str, Any]
    confidence: float
    processing_time_ms: float
    cost_estimate: float
    metadata: dict[str, Any]


class SpecialistCoordinator:
    """Coordinates specialist agents for optimal task execution."""

    def __init__(
        self,
        enhanced_selector: EnhancedAISelector,
        prompt_architect: PromptArchitect,
        ui_specialist: UISpecialist,
    ) -> None:
        """Initialize the specialist coordinator."""
        self.enhanced_selector = enhanced_selector
        self.prompt_architect = prompt_architect
        self.ui_specialist = ui_specialist
        self._performance_cache = {}
        self._routing_stats = {
            "total_requests": 0,
            "router_requests": 0,
            "prompt_architect_requests": 0,
            "ui_specialist_requests": 0,
            "multi_specialist_requests": 0,
            "average_processing_time": 0.0,
            "total_cost_saved": 0.0,
        }

    def process_task(self, request: TaskRequest) -> list[SpecialistResult]:
        """Process a task using appropriate specialist agents."""
        import time

        start_time = time.time()

        self._routing_stats["total_requests"] += 1
        results = []

        try:
            # Route to appropriate specialists based on task category
            if request.category == TaskCategory.TOOL_SELECTION:
                results = self._handle_tool_selection(request)
            elif request.category == TaskCategory.PROMPT_OPTIMIZATION:
                results = self._handle_prompt_optimization(request)
            elif request.category == TaskCategory.UI_GENERATION:
                results = self._handle_ui_generation(request)
            elif request.category == TaskCategory.CODE_GENERATION:
                results = self._handle_code_generation(request)
            elif request.category == TaskCategory.MULTI_STEP:
                results = self._handle_multi_step_task(request)
            else:
                # Default to router for analysis tasks
                results = self._handle_tool_selection(request)

            # Update performance metrics
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_stats(processing_time, results)

            return results

        except Exception as e:
            logger.error("Error processing task: %s", e)
            return []

    def _handle_tool_selection(self, request: TaskRequest) -> list[SpecialistResult]:
        """Handle tool selection using Router Agent."""
        self._routing_stats["router_requests"] += 1

        import time

        start_time = time.time()

        # Get user preferences
        user_prefs = request.user_preferences or {}
        cost_preference = user_prefs.get("cost_preference", "balanced")
        max_cost = user_prefs.get("max_cost_per_request")

        # Use enhanced selector with cost optimization
        result = self.enhanced_selector.select_tool_with_cost_optimization(
            task=request.task,
            tools=request.tools or [],
            context=request.context,
            user_cost_preference=cost_preference,
            max_cost_per_request=max_cost,
        )

        processing_time = (time.time() - start_time) * 1000

        if result:
            # Calculate cost estimate
            cost_estimate = result.get("estimated_cost", {}).get("total_cost", 0.0)

            specialist_result = SpecialistResult(
                specialist_type=SpecialistType.ROUTER,
                result=result,
                confidence=result.get("confidence", 0.0),
                processing_time_ms=processing_time,
                cost_estimate=cost_estimate,
                metadata={
                    "model_used": result.get("model_used"),
                    "model_tier": result.get("model_tier"),
                    "hardware_requirements": result.get("hardware_requirements"),
                    "task_complexity": result.get("task_complexity"),
                },
            )
            return [specialist_result]

        return []

    def _handle_prompt_optimization(
        self, request: TaskRequest
    ) -> list[SpecialistResult]:
        """Handle prompt optimization using Prompt Architect."""
        self._routing_stats["prompt_architect_requests"] += 1

        import time

        start_time = time.time()

        # Get user preferences
        user_prefs = request.user_preferences or {}
        cost_preference = user_prefs.get("cost_preference", "balanced")
        feedback = user_prefs.get("feedback")

        # Use prompt architect for optimization
        result = self.prompt_architect.optimize_prompt(
            prompt=request.task,
            user_cost_preference=cost_preference,
            context=request.context,
            feedback=feedback,
        )

        processing_time = (time.time() - start_time) * 1000

        # Calculate cost savings from token reduction
        token_metrics = result.get("token_metrics", {})
        cost_savings = token_metrics.get("cost_savings", 0.0)

        specialist_result = SpecialistResult(
            specialist_type=SpecialistType.PROMPT_ARCHITECT,
            result=result,
            confidence=result.get("quality_score", {}).get("overall_score", 0.0),
            processing_time_ms=processing_time,
            cost_estimate=0.0,  # Prompt optimization is internal
            metadata={
                "task_type": result.get("task_type"),
                "requirements": result.get("requirements"),
                "token_reduction": token_metrics.get("token_reduction_percent", 0.0),
                "quality_score": result.get("quality_score"),
            },
        )

        # Update cost savings
        self._routing_stats["total_cost_saved"] += cost_savings

        return [specialist_result]

    def _handle_ui_generation(self, request: TaskRequest) -> list[SpecialistResult]:
        """Handle UI generation using UI Specialist."""
        self._routing_stats["ui_specialist_requests"] += 1

        import time

        start_time = time.time()

        # Parse UI generation requirements from task
        ui_requirements = self._parse_ui_requirements(
            request.task, request.user_preferences or {}
        )

        # Use UI specialist for component generation
        result = self.ui_specialist.generate_ui_component(
            component_name=ui_requirements.get("component_name", "GeneratedComponent"),
            component_type=ui_requirements.get("component_type", ComponentType.FORM),
            framework=ui_requirements.get("framework", UIFramework.REACT),
            design_system=ui_requirements.get(
                "design_system", DesignSystem.TAILWIND_UI
            ),
            accessibility_level=ui_requirements.get(
                "accessibility_level", AccessibilityLevel.AA
            ),
            user_preferences=ui_requirements.get("preferences", {}),
            cost_optimization=request.cost_optimization,
        )

        processing_time = (time.time() - start_time) * 1000

        # Extract component information
        component_data = result.get("component", {})
        validation_data = result.get("validation", {})

        specialist_result = SpecialistResult(
            specialist_type=SpecialistType.UI_SPECIALIST,
            result=result,
            confidence=validation_data.get("compliance_score", 0.0),
            processing_time_ms=processing_time,
            cost_estimate=component_data.get("token_estimate", 0)
            * 0.002,  # $0.002 per token
            metadata={
                "component_type": ui_requirements.get("component_type"),
                "framework": ui_requirements.get("framework"),
                "design_system": ui_requirements.get("design_system"),
                "accessibility_compliant": result.get("accessibility_compliant", False),
                "responsive_ready": result.get("responsive_ready", False),
                "industry_standards_compliant": result.get(
                    "industry_standards_compliant", False
                ),
            },
        )

        return [specialist_result]

    def _handle_code_generation(self, request: TaskRequest) -> list[SpecialistResult]:
        """Handle code generation using multiple specialists."""
        self._routing_stats["multi_specialist_requests"] += 1
        results = []

        # Step 1: Optimize the prompt using Prompt Architect
        prompt_request = TaskRequest(
            task=request.task,
            category=TaskCategory.PROMPT_OPTIMIZATION,
            context=request.context,
            user_preferences=request.user_preferences,
            cost_optimization=request.cost_optimization,
        )

        prompt_results = self._handle_prompt_optimization(prompt_request)
        results.extend(prompt_results)

        # Step 2: Use optimized prompt for tool selection
        if prompt_results:
            optimized_prompt = prompt_results[0].result.get(
                "optimized_prompt", request.task
            )

            tool_request = TaskRequest(
                task=optimized_prompt,
                category=TaskCategory.TOOL_SELECTION,
                context=request.context,
                tools=request.tools,
                user_preferences=request.user_preferences,
                cost_optimization=request.cost_optimization,
            )

            tool_results = self._handle_tool_selection(tool_request)
            results.extend(tool_results)

        return results

    def _handle_multi_step_task(self, request: TaskRequest) -> list[SpecialistResult]:
        """Handle multi-step tasks requiring multiple specialists."""
        self._routing_stats["multi_specialist_requests"] += 1
        results = []

        # Analyze task to determine required specialists
        task_lower = request.task.lower()

        # Check if UI generation is needed
        if any(
            keyword in task_lower
            for keyword in ["ui", "component", "interface", "form", "button"]
        ):
            ui_results = self._handle_ui_generation(request)
            results.extend(ui_results)

        # Check if prompt optimization could help
        if (
            len(request.task) > 200
            or "optimize" in task_lower
            or "improve" in task_lower
        ):
            prompt_results = self._handle_prompt_optimization(request)
            results.extend(prompt_results)

        # Always include tool selection for core functionality
        tool_results = self._handle_tool_selection(request)
        results.extend(tool_results)

        return results

    def _parse_ui_requirements(
        self, task: str, user_preferences: dict[str, Any]
    ) -> dict[str, Any]:
        """Parse UI generation requirements from task."""
        task_lower = task.lower()

        # Determine component type
        component_type = ComponentType.FORM  # Default
        if "table" in task_lower:
            component_type = ComponentType.TABLE
        elif "chart" in task_lower or "graph" in task_lower:
            component_type = ComponentType.CHART
        elif "modal" in task_lower or "dialog" in task_lower:
            component_type = ComponentType.MODAL
        elif "navigation" in task_lower or "nav" in task_lower:
            component_type = ComponentType.NAVIGATION
        elif "card" in task_lower:
            component_type = ComponentType.CARD
        elif "button" in task_lower:
            component_type = ComponentType.BUTTON
        elif "dashboard" in task_lower:
            component_type = ComponentType.DASHBOARD
        elif "landing" in task_lower or "home" in task_lower:
            component_type = ComponentType.LANDING
        elif "auth" in task_lower or "login" in task_lower:
            component_type = ComponentType.AUTH
        elif "settings" in task_lower or "config" in task_lower:
            component_type = ComponentType.SETTINGS

        # Determine framework
        framework = UIFramework.REACT  # Default
        if "vue" in task_lower:
            framework = UIFramework.VUE
        elif "angular" in task_lower:
            framework = UIFramework.ANGULAR
        elif "svelte" in task_lower:
            framework = UIFramework.SVELTE
        elif "next" in task_lower:
            framework = UIFramework.NEXT_JS
        elif "html" in task_lower and "css" in task_lower:
            framework = UIFramework.HTML_CSS

        # Determine design system
        design_system = DesignSystem.TAILWIND_UI  # Default
        if "material" in task_lower:
            design_system = DesignSystem.MATERIAL_DESIGN
        elif "bootstrap" in task_lower:
            design_system = DesignSystem.BOOTSTRAP
        elif "ant" in task_lower:
            design_system = DesignSystem.ANT_DESIGN
        elif "chakra" in task_lower:
            design_system = DesignSystem.CHAKRA_UI

        # Determine accessibility level
        accessibility_level = AccessibilityLevel.AA  # Default
        if "aaa" in task_lower or "enhanced" in task_lower:
            accessibility_level = AccessibilityLevel.AAA
        elif "minimal" in task_lower or "basic" in task_lower:
            accessibility_level = AccessibilityLevel.MINIMAL

        # Extract component name
        component_name = "GeneratedComponent"
        words = task.split()
        for i, word in enumerate(words):
            if word.lower() in ["component", "form", "table", "button", "modal"]:
                if i > 0:
                    component_name = words[i - 1].title()
                break

        return {
            "component_name": component_name,
            "component_type": component_type,
            "framework": framework,
            "design_system": design_system,
            "accessibility_level": accessibility_level,
            "preferences": user_preferences,
        }

    def _update_performance_stats(
        self, processing_time: float, results: list[SpecialistResult]
    ) -> None:
        """Update performance statistics."""
        # Update average processing time
        current_avg = self._routing_stats["average_processing_time"]
        total_requests = self._routing_stats["total_requests"]

        self._routing_stats["average_processing_time"] = (
            current_avg * (total_requests - 1) + processing_time
        ) / total_requests

        # Update cost savings
        for result in results:
            if result.specialist_type == SpecialistType.PROMPT_ARCHITECT:
                cost_savings = (
                    result.metadata.get("token_reduction", 0) * 0.001
                )  # Rough estimate
                self._routing_stats["total_cost_saved"] += cost_savings

    def get_routing_stats(self) -> dict[str, Any]:
        """Get routing and performance statistics."""
        return {
            **self._routing_stats,
            "cache_size": len(self._performance_cache),
            "specialist_distribution": {
                "router": self._routing_stats["router_requests"],
                "prompt_architect": self._routing_stats["prompt_architect_requests"],
                "ui_specialist": self._routing_stats["ui_specialist_requests"],
                "multi_specialist": self._routing_stats["multi_specialist_requests"],
            },
        }

    def clear_cache(self) -> None:
        """Clear the performance cache."""
        self._performance_cache.clear()

    def get_specialist_capabilities(self) -> dict[str, Any]:
        """Get capabilities of all specialists."""
        return {
            "router": {
                "hardware_aware": True,
                "cost_optimization": True,
                "supported_models": [model.value for model in AIModel],
                "token_estimation": True,
            },
            "prompt_architect": {
                "task_analysis": True,
                "token_optimization": True,
                "quality_scoring": True,
                "iterative_refinement": True,
            },
            "ui_specialist": {
                "frameworks": self.ui_specialist.get_supported_frameworks(),
                "component_types": self.ui_specialist.get_supported_component_types(),
                "design_systems": self.ui_specialist.get_supported_design_systems(),
                "accessibility_levels": ["minimal", "aa", "aaa"],
                "responsive_design": True,
            },
        }
