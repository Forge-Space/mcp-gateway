from __future__ import annotations

import json
import time
from pathlib import Path

import yaml

from tool_router.ai.enhanced_selector import EnhancedAISelector
from tool_router.ai.enhanced_selector import OllamaSelector as EnhancedOllamaSelector
from tool_router.ai.feedback import FeedbackStore
from tool_router.ai.prompt_architect import PromptArchitect
from tool_router.ai.selector import OllamaSelector
from tool_router.ai.ui_specialist import UISpecialist
from tool_router.args.builder import build_arguments
from tool_router.core.config import ToolRouterConfig
from tool_router.gateway.client import call_tool, get_tools
from tool_router.observability import get_logger, get_metrics
from tool_router.observability.metrics import TimingContext
from tool_router.scoring.matcher import (
    select_top_matching_tools,
    select_top_matching_tools_hybrid,
)
from tool_router.security import SecurityContext, SecurityMiddleware
from tool_router.specialist_coordinator import (
    SpecialistCoordinator,
    SpecialistType,
    TaskCategory,
    TaskRequest,
)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    msg = "Install the MCP SDK: pip install mcp"
    raise ImportError(msg) from None

mcp = FastMCP("tool-router", json_response=True)
logger = get_logger(__name__)
metrics = get_metrics()

# Global state (initialized at startup)
_ai_selector: OllamaSelector | None = None
_enhanced_ai_selector: EnhancedAISelector | None = None
_specialist_coordinator: SpecialistCoordinator | None = None
_feedback_store: FeedbackStore | None = None
_config: ToolRouterConfig | None = None
_security_middleware: SecurityMiddleware | None = None


def initialize_ai(config: ToolRouterConfig) -> None:
    """Initialize AI selector, specialist coordinator, feedback store, and security middleware."""
    global _ai_selector, _enhanced_ai_selector, _specialist_coordinator, _feedback_store, _config, _security_middleware
    _config = config
    _feedback_store = FeedbackStore()

    # Initialize security middleware
    security_config_path = (
        Path(__file__).parent.parent.parent / "config" / "security.yaml"
    )
    security_config = {}

    if security_config_path.exists():
        try:
            with security_config_path.open() as f:
                security_config = yaml.safe_load(f).get("security", {})
        except OSError as e:
            logger.warning(f"Failed to load security config: {e}")

    _security_middleware = SecurityMiddleware(security_config)

    if config.ai.enabled:
        try:
            # Initialize legacy selector for backward compatibility
            _ai_selector = OllamaSelector(
                endpoint=config.ai.endpoint,
                model=config.ai.model,
                timeout=config.ai.timeout_ms,
                min_confidence=config.ai.min_confidence,
            )

            # Initialize enhanced selector with hardware-aware routing
            ollama_provider = EnhancedOllamaSelector(
                endpoint=config.ai.endpoint,
                model=config.ai.model,
                timeout=config.ai.timeout_ms,
                min_confidence=config.ai.min_confidence,
            )

            _enhanced_ai_selector = EnhancedAISelector(
                providers=[ollama_provider],
                hardware_constraints={
                    "ram_available_gb": 16,
                    "cpu_cores": 4,
                    "max_model_ram_gb": 8,
                    "network_speed_mbps": 1000,
                    "hardware_tier": "n100",
                },
                cost_optimization=True,
            )

            # Initialize specialist agents
            prompt_architect = PromptArchitect()
            ui_specialist = UISpecialist()

            # Initialize specialist coordinator
            _specialist_coordinator = SpecialistCoordinator(
                enhanced_selector=_enhanced_ai_selector,
                prompt_architect=prompt_architect,
                ui_specialist=ui_specialist,
            )

            logger.info(
                "Enhanced AI system initialized with model %s at %s (min_confidence=%.2f)",
                config.ai.model,
                config.ai.endpoint,
                config.ai.min_confidence,
            )
            logger.info(
                "Specialist agents initialized: Router, Prompt Architect, UI Specialist"
            )
        except Exception as e:
            logger.exception("Failed to initialize AI system: %s", e)
            _ai_selector = None
            _enhanced_ai_selector = None
            _specialist_coordinator = None
    else:
        logger.info("AI system disabled")
        _ai_selector = None
        _enhanced_ai_selector = None
        _specialist_coordinator = None


@mcp.tool()
def execute_task(task: str, context: str = "") -> str:
    """Run the best matching gateway tool for the given task."""
    logger.info("Executing task: %s", task[:100])
    metrics.increment_counter("execute_task.calls")

    with TimingContext("execute_task.total_duration"):
        try:
            with TimingContext("execute_task.get_tools"):
                tools = get_tools()
        except (ValueError, ConnectionError) as error:
            logger.exception("Failed to list tools: %s", error)
            metrics.increment_counter("execute_task.errors.get_tools")
            return f"Failed to list tools: {error}"
        except Exception as unexpected_error:
            logger.exception(
                "Unexpected error listing tools: %s: %s",
                type(unexpected_error).__name__,
                unexpected_error,
            )
            metrics.increment_counter("execute_task.errors.unexpected")
            return f"Unexpected error listing tools: {type(unexpected_error).__name__}: {unexpected_error}"

        if not tools:
            logger.warning("No tools registered in gateway")
            metrics.increment_counter("execute_task.no_tools")
            return "No tools registered in the gateway."

        try:
            with TimingContext("execute_task.pick_best_tools"):
                if _ai_selector and _config:
                    best_matching_tools = select_top_matching_tools_hybrid(
                        tools,
                        task,
                        context,
                        top_n=1,
                        ai_selector=_ai_selector,
                        ai_weight=_config.ai.weight,
                        feedback_store=_feedback_store,
                    )
                    metrics.increment_counter("execute_task.ai_selection_attempt")
                else:
                    best_matching_tools = select_top_matching_tools(
                        tools, task, context, top_n=1
                    )
                    metrics.increment_counter("execute_task.keyword_only_selection")
        except Exception as selection_error:
            logger.exception(
                "Error picking tool: %s: %s",
                type(selection_error).__name__,
                selection_error,
            )
            metrics.increment_counter("execute_task.errors.pick_tools")
            return f"Error picking tool: {type(selection_error).__name__}: {selection_error}"

        if not best_matching_tools:
            logger.warning("No matching tool found for task")
            metrics.increment_counter("execute_task.no_match")
            return "No matching tool found; try describing the task differently."

        tool = best_matching_tools[0]
        name = tool.get("name") or ""
        if not name:
            logger.error("Chosen tool has no name")
            metrics.increment_counter("execute_task.errors.no_name")
            return "Chosen tool has no name."

        logger.info("Selected tool: %s", name)
        metrics.increment_counter(f"execute_task.tool_selected.{name}")

        try:
            with TimingContext("execute_task.build_arguments"):
                tool_arguments = build_arguments(tool, task)
        except Exception as build_error:
            logger.exception(
                "Error building arguments: %s: %s",
                type(build_error).__name__,
                build_error,
            )
            metrics.increment_counter("execute_task.errors.build_args")
            return (
                f"Error building arguments: {type(build_error).__name__}: {build_error}"
            )

        with TimingContext("execute_task.call_tool"):
            result = call_tool(name, tool_arguments)

        # Record feedback (success = no error string returned)
        if _feedback_store:
            success = not result.startswith("Error") and not result.startswith("Failed")
            _feedback_store.record(
                task=task, selected_tool=name, success=success, context=context
            )

        logger.info("Task completed successfully with tool: %s", name)
        metrics.increment_counter("execute_task.success")
        return result


@mcp.tool()
def execute_tasks(task: str, context: str = "", max_tools: int = 3) -> str:
    """Run multiple gateway tools in sequence to accomplish a complex task.

    Selects up to max_tools tools and chains their execution. Each tool's
    result is passed as context to the next selection step.
    """
    logger.info("Executing multi-tool task: %s (max_tools=%d)", task[:100], max_tools)
    metrics.increment_counter("execute_tasks.calls")

    with TimingContext("execute_tasks.total_duration"):
        try:
            tools = get_tools()
        except Exception as error:
            logger.exception("Failed to list tools: %s", error)
            return f"Failed to list tools: {error}"

        if not tools:
            return "No tools registered in the gateway."

        # Determine tool sequence via AI or keyword scoring
        selected_names: list[str] = []
        if _ai_selector:
            try:
                multi_result = _ai_selector.select_tools_multi(
                    task, tools, context=context, max_tools=max_tools
                )
                if multi_result:
                    selected_names = multi_result.get("tools", [])
                    logger.info(
                        "AI selected tools for orchestration: %s", selected_names
                    )
            except Exception as e:
                logger.warning("AI multi-tool selection failed: %s", e)

        if not selected_names:
            # Fallback: keyword scoring, pick top max_tools
            matched = select_top_matching_tools(tools, task, context, top_n=max_tools)
            selected_names = [t.get("name", "") for t in matched if t.get("name")]

        if not selected_names:
            return "No matching tools found; try describing the task differently."

        # Build a name→tool lookup
        tool_map = {t.get("name", ""): t for t in tools}

        results: list[str] = []
        accumulated_context = context

        for step_num, tool_name in enumerate(selected_names, 1):
            tool = tool_map.get(tool_name)
            if not tool:
                logger.warning("Orchestration: tool %s not found, skipping", tool_name)
                continue

            logger.info(
                "Orchestration step %d/%d: %s", step_num, len(selected_names), tool_name
            )
            metrics.increment_counter(f"execute_tasks.step.{tool_name}")

            try:
                tool_arguments = build_arguments(tool, task)
            except Exception as build_error:
                logger.warning(
                    "Error building arguments for %s: %s", tool_name, build_error
                )
                results.append(f"[{tool_name}] Error building arguments: {build_error}")
                if _feedback_store:
                    _feedback_store.record(
                        task=task,
                        selected_tool=tool_name,
                        success=False,
                        context=accumulated_context,
                    )
                continue

            step_result = call_tool(tool_name, tool_arguments)
            results.append(f"[{tool_name}] {step_result}")

            step_success = not step_result.startswith(
                "Error"
            ) and not step_result.startswith("Failed")
            if _feedback_store:
                _feedback_store.record(
                    task=task,
                    selected_tool=tool_name,
                    success=step_success,
                    context=accumulated_context,
                )

            # Accumulate context for next step
            accumulated_context = (
                f"{accumulated_context}\nPrevious result: {step_result[:200]}"
            )

        if not results:
            return "No tools were executed."

        metrics.increment_counter("execute_tasks.success")
        return "\n\n".join(results)


@mcp.tool()
def record_feedback(tool_name: str, task: str, success: bool, context: str = "") -> str:
    """Record explicit feedback on a tool selection outcome for context learning."""
    if _feedback_store is None:
        return "Feedback store not initialized."
    _feedback_store.record(
        task=task, selected_tool=tool_name, success=success, context=context
    )
    stats = _feedback_store.get_stats(tool_name)
    rate = stats.success_rate if stats else 0.5
    logger.info(
        "Feedback recorded: tool=%s success=%s rate=%.2f", tool_name, success, rate
    )
    return f"Feedback recorded for '{tool_name}'. Current success rate: {rate:.0%}"


@mcp.tool()
def search_tools(query: str, limit: int = 10) -> str:
    """Search available tools by name or description. Returns a list of matching tools with their details."""
    logger.info("Searching tools: %s", query[:100])
    metrics.increment_counter("search_tools.calls")

    with TimingContext("search_tools.total_duration"):
        try:
            with TimingContext("search_tools.get_tools"):
                tools = get_tools()
        except (ValueError, ConnectionError) as error:
            logger.exception("Failed to list tools: %s", error)
            metrics.increment_counter("search_tools.errors.get_tools")
            return f"Failed to list tools: {error}"
        except Exception as unexpected_error:
            logger.exception(
                "Unexpected error listing tools: %s: %s",
                type(unexpected_error).__name__,
                unexpected_error,
            )
            metrics.increment_counter("search_tools.errors.unexpected")
            return f"Unexpected error listing tools: {type(unexpected_error).__name__}: {unexpected_error}"

        if not tools:
            logger.warning("No tools registered in gateway")
            metrics.increment_counter("search_tools.no_tools")
            return "No tools registered in the gateway."

        try:
            with TimingContext("search_tools.pick_best_tools"):
                matching_tools = select_top_matching_tools(
                    tools, query, "", top_n=limit
                )
        except Exception as search_error:
            logger.exception(
                "Error searching tools: %s: %s",
                type(search_error).__name__,
                search_error,
            )
            metrics.increment_counter("search_tools.errors.search")
            return (
                f"Error searching tools: {type(search_error).__name__}: {search_error}"
            )

        if not matching_tools:
            logger.info("No tools found matching: %s", query)
            metrics.increment_counter("search_tools.no_matches")
            return f"No tools found matching '{query}'."

        logger.info("Found %d matching tools", len(matching_tools))
        metrics.increment_counter("search_tools.success")

        lines = [f"Found {len(matching_tools)} matching tool(s):"]
        for index, tool in enumerate(matching_tools, 1):
            name = tool.get("name", "unknown")
            description = tool.get("description", "No description")
            lines.append(f"{index}. {name}: {description}")

        return "\n".join(lines)


@mcp.tool()
def execute_specialist_task(
    task: str,
    category: str = "tool_selection",
    context: str = "",
    user_preferences: str = "{}",
    cost_optimization: bool = True,
) -> str:
    """Execute task using specialist agents with hardware-aware routing and cost optimization.

    Categories:
    - tool_selection: Use Router Agent for optimal tool selection
    - prompt_optimization: Use Prompt Architect for prompt enhancement
    - ui_generation: Use UI Specialist for component generation
    - code_generation: Use multiple specialists for code tasks
    - multi_step: Use multiple specialists for complex tasks

    User preferences (JSON format):
    - cost_preference: "efficient", "balanced", or "quality"
    - max_cost_per_request: Maximum cost in dollars
    - responsive: Boolean for responsive design
    - dark_mode: Boolean for dark mode support
    """
    if _specialist_coordinator is None:
        return "Specialist coordinator not initialized."

    # Security check
    if _security_middleware is None:
        return "Security middleware not initialized."

    logger.info("Executing specialist task: %s (category=%s)", task[:100], category)
    metrics.increment_counter("execute_specialist_task.calls")

    # Create security context (simplified for demo)
    security_context = SecurityContext(
        user_id=None,  # Would come from authentication
        session_id=None,
        ip_address=None,  # Would come from request
        user_agent=None,
        request_id=f"req_{int(time.time())}",
        endpoint="execute_specialist_task",
        authentication_method=None,
        user_role="user",
    )

    # Perform security checks
    security_result = _security_middleware.check_request_security(
        context=security_context,
        task=task,
        category=category,
        context_str=context,
        user_preferences=user_preferences,
    )

    if not security_result.allowed:
        logger.warning(
            "Request blocked by security: %s", security_result.blocked_reason
        )
        metrics.increment_counter("execute_specialist_task.blocked")
        return f"Request blocked: {security_result.blocked_reason}"

    # Use sanitized inputs
    sanitized_task = security_result.sanitized_inputs.get("task", task)
    sanitized_context = security_result.sanitized_inputs.get("context", context)
    sanitized_preferences = security_result.sanitized_inputs.get(
        "user_preferences", user_preferences
    )

    if security_result.risk_score > 0.5:
        logger.warning(
            "High risk request allowed: risk_score=%.2f, violations=%s",
            security_result.risk_score,
            len(security_result.violations),
        )

    try:
        # Parse category
        try:
            task_category = TaskCategory(category.lower())
        except ValueError:
            task_category = TaskCategory.TOOL_SELECTION
            logger.warning("Invalid category '%s', using tool_selection", category)

        # Parse user preferences
        try:
            prefs = json.loads(sanitized_preferences)
        except json.JSONDecodeError:
            prefs = {}
            logger.warning("Invalid user preferences JSON, using defaults")

        # Create task request with sanitized inputs
        task_request = TaskRequest(
            task=sanitized_task,
            category=task_category,
            context=sanitized_context,
            tools=None,  # Will be populated by coordinator
            user_preferences=prefs,
            cost_optimization=cost_optimization,
        )

        # Process with specialist coordinator
        with TimingContext("execute_specialist_task.total_duration"):
            results = _specialist_coordinator.process_task(task_request)

        if not results:
            return "No specialist could process this task."

        # Format results
        output_lines = [f"Processed by {len(results)} specialist(s):"]

        for i, result in enumerate(results, 1):
            specialist_name = result.specialist_type.value.replace("_", " ").title()
            output_lines.append(f"\n{i}. {specialist_name} Specialist:")
            output_lines.append(f"   Confidence: {result.confidence:.2f}")
            output_lines.append(
                f"   Processing time: {result.processing_time_ms:.1f}ms"
            )
            output_lines.append(f"   Cost estimate: ${result.cost_estimate:.4f}")

            # Add specialist-specific details
            if result.specialist_type == SpecialistType.ROUTER:
                metadata = result.metadata
                output_lines.append(
                    f"   Model used: {metadata.get('model_used', 'Unknown')}"
                )
                output_lines.append(
                    f"   Model tier: {metadata.get('model_tier', 'Unknown')}"
                )
                output_lines.append(
                    f"   Task complexity: {metadata.get('task_complexity', 'Unknown')}"
                )
            elif result.specialist_type == SpecialistType.PROMPT_ARCHITECT:
                metadata = result.metadata
                output_lines.append(
                    f"   Task type: {metadata.get('task_type', 'Unknown')}"
                )
                output_lines.append(
                    f"   Token reduction: {metadata.get('token_reduction', 0):.1f}%"
                )
                quality = metadata.get("quality_score", {})
                output_lines.append(
                    f"   Quality score: {quality.get('overall_score', 0):.2f}"
                )
            elif result.specialist_type == SpecialistType.UI_SPECIALIST:
                metadata = result.metadata
                output_lines.append(
                    f"   Component type: {metadata.get('component_type', 'Unknown')}"
                )
                output_lines.append(
                    f"   Framework: {metadata.get('framework', 'Unknown')}"
                )
                output_lines.append(
                    f"   Design system: {metadata.get('design_system', 'Unknown')}"
                )
                output_lines.append(
                    f"   Accessibility compliant: {metadata.get('accessibility_compliant', False)}"
                )
                output_lines.append(
                    f"   Responsive ready: {metadata.get('responsive_ready', False)}"
                )

        metrics.increment_counter("execute_specialist_task.success")
        return "\n".join(output_lines)

    except Exception as e:
        logger.exception("Error in specialist task execution: %s", e)
        metrics.increment_counter("execute_specialist_task.errors")
        return f"Error executing specialist task: {type(e).__name__}: {e}"


@mcp.tool()
def get_specialist_stats() -> str:
    """Get performance statistics and capabilities of specialist agents."""
    if _specialist_coordinator is None:
        return "Specialist coordinator not initialized."

    try:
        stats = _specialist_coordinator.get_routing_stats()
        capabilities = _specialist_coordinator.get_specialist_capabilities()

        output_lines = ["Specialist Agent Statistics:", ""]

        # Routing statistics
        output_lines.append("Routing Statistics:")
        output_lines.append(f"  Total requests: {stats['total_requests']}")
        output_lines.append(
            f"  Average processing time: {stats['average_processing_time']:.1f}ms"
        )
        output_lines.append(f"  Total cost saved: ${stats['total_cost_saved']:.4f}")
        output_lines.append(f"  Cache size: {stats['cache_size']}")
        output_lines.append("")

        # Specialist distribution
        output_lines.append("Specialist Distribution:")
        dist = stats["specialist_distribution"]
        output_lines.append(f"  Router Agent: {dist['router']} requests")
        output_lines.append(f"  Prompt Architect: {dist['prompt_architect']} requests")
        output_lines.append(f"  UI Specialist: {dist['ui_specialist']} requests")
        output_lines.append(f"  Multi-specialist: {dist['multi_specialist']} requests")
        output_lines.append("")

        # Capabilities
        output_lines.append("Specialist Capabilities:")
        for specialist, caps in capabilities.items():
            output_lines.append(f"  {specialist.title()}:")
            for capability, enabled in caps.items():
                status = "✓" if enabled else "✗"
                output_lines.append(
                    f"    {status} {capability.replace('_', ' ').title()}"
                )

        return "\n".join(output_lines)

    except Exception as e:
        logger.exception("Error getting specialist stats: %s", e)
        return f"Error getting specialist stats: {type(e).__name__}: {e}"


@mcp.tool()
def optimize_prompt(
    prompt: str,
    cost_preference: str = "balanced",
    context: str = "",
    feedback: str = "",
) -> str:
    """Optimize a prompt for token efficiency and effectiveness using the Prompt Architect.

    Cost preferences:
    - efficient: Minimize token usage
    - balanced: Balance quality and cost
    - quality: Prioritize response quality
    """
    if _specialist_coordinator is None:
        return "Specialist coordinator not initialized."

    logger.info(
        "Optimizing prompt: %s (cost_preference=%s)", prompt[:100], cost_preference
    )
    metrics.increment_counter("optimize_prompt.calls")

    try:
        # Create task request for prompt optimization
        task_request = TaskRequest(
            task=prompt,
            category=TaskCategory.PROMPT_OPTIMIZATION,
            context=context,
            user_preferences={
                "cost_preference": cost_preference,
                "feedback": feedback if feedback else None,
            },
            cost_optimization=True,
        )

        # Process with specialist coordinator
        with TimingContext("optimize_prompt.total_duration"):
            results = _specialist_coordinator.process_task(task_request)

        if not results:
            return "Prompt optimization failed."

        # Get the prompt architect result
        prompt_result = None
        for result in results:
            if result.specialist_type == SpecialistType.PROMPT_ARCHITECT:
                prompt_result = result.result
                break

        if not prompt_result:
            return "Prompt architect result not found."

        # Format optimization results
        output_lines = ["Prompt Optimization Results:", ""]

        # Original vs optimized
        original_tokens = prompt_result.get("token_metrics", {}).get(
            "original_tokens", 0
        )
        optimized_tokens = prompt_result.get("token_metrics", {}).get(
            "optimized_tokens", 0
        )
        token_reduction = prompt_result.get("token_metrics", {}).get(
            "token_reduction_percent", 0
        )
        cost_savings = prompt_result.get("token_metrics", {}).get("cost_savings", 0)

        output_lines.append(f"Original tokens: {original_tokens}")
        output_lines.append(f"Optimized tokens: {optimized_tokens}")
        output_lines.append(f"Token reduction: {token_reduction:.1f}%")
        output_lines.append(f"Cost savings: ${cost_savings:.4f}")
        output_lines.append("")

        # Quality scores
        quality = prompt_result.get("quality_score", {})
        output_lines.append("Quality Scores:")
        output_lines.append(f"  Overall: {quality.get('overall_score', 0):.2f}")
        output_lines.append(f"  Clarity: {quality.get('clarity', 0):.2f}")
        output_lines.append(f"  Completeness: {quality.get('completeness', 0):.2f}")
        output_lines.append(f"  Specificity: {quality.get('specificity', 0):.2f}")
        output_lines.append(
            f"  Token efficiency: {quality.get('token_efficiency', 0):.2f}"
        )
        output_lines.append("")

        # Task analysis
        output_lines.append("Task Analysis:")
        output_lines.append(f"  Task type: {prompt_result.get('task_type', 'Unknown')}")
        requirements = prompt_result.get("requirements", [])
        if requirements:
            output_lines.append(f"  Requirements identified: {len(requirements)}")
            for req in requirements[:3]:  # Show first 3 requirements
                req_type = req.get("type", "Unknown")
                priority = req.get("priority", "Unknown")
                output_lines.append(f"    - {req_type} (Priority: {priority})")

        output_lines.append("")
        output_lines.append("Optimized Prompt:")
        output_lines.append(prompt_result.get("optimized_prompt", prompt))

        metrics.increment_counter("optimize_prompt.success")
        return "\n".join(output_lines)

    except Exception as e:
        logger.exception("Error optimizing prompt: %s", e)
        metrics.increment_counter("optimize_prompt.errors")
        return f"Error optimizing prompt: {type(e).__name__}: {e}"


def main() -> None:
    """Initialize and run the MCP server."""
    config = ToolRouterConfig.load_from_environment()
    initialize_ai(config)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
