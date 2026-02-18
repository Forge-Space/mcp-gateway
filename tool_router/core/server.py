from __future__ import annotations

from tool_router.ai.feedback import FeedbackStore
from tool_router.ai.selector import OllamaSelector
from tool_router.args.builder import build_arguments
from tool_router.core.config import ToolRouterConfig
from tool_router.gateway.client import call_tool, get_tools
from tool_router.observability import get_logger, get_metrics
from tool_router.observability.metrics import TimingContext
from tool_router.scoring.matcher import select_top_matching_tools, select_top_matching_tools_hybrid


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
_feedback_store: FeedbackStore | None = None
_config: ToolRouterConfig | None = None


def initialize_ai(config: ToolRouterConfig) -> None:
    """Initialize AI selector and feedback store."""
    global _ai_selector, _feedback_store, _config  # noqa: PLW0603
    _config = config
    _feedback_store = FeedbackStore()

    if config.ai.enabled:
        try:
            _ai_selector = OllamaSelector(
                endpoint=config.ai.endpoint,
                model=config.ai.model,
                timeout=config.ai.timeout_ms,
                min_confidence=config.ai.min_confidence,
            )
            logger.info(
                "AI selector initialized with model %s at %s (min_confidence=%.2f)",
                config.ai.model,
                config.ai.endpoint,
                config.ai.min_confidence,
            )
        except Exception as e:
            logger.exception("Failed to initialize AI selector: %s", e)
            _ai_selector = None
    else:
        logger.info("AI selector disabled")
        _ai_selector = None


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
            logger.exception("Unexpected error listing tools: %s: %s", type(unexpected_error).__name__, unexpected_error)
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
                        tools, task, context, top_n=1,
                        ai_selector=_ai_selector,
                        ai_weight=_config.ai.weight,
                        feedback_store=_feedback_store,
                    )
                    metrics.increment_counter("execute_task.ai_selection_attempt")
                else:
                    best_matching_tools = select_top_matching_tools(tools, task, context, top_n=1)
                    metrics.increment_counter("execute_task.keyword_only_selection")
        except Exception as selection_error:
            logger.exception("Error picking tool: %s: %s", type(selection_error).__name__, selection_error)
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
            logger.exception("Error building arguments: %s: %s", type(build_error).__name__, build_error)
            metrics.increment_counter("execute_task.errors.build_args")
            return f"Error building arguments: {type(build_error).__name__}: {build_error}"

        with TimingContext("execute_task.call_tool"):
            result = call_tool(name, tool_arguments)

        # Record feedback (success = no error string returned)
        if _feedback_store:
            success = not result.startswith("Error") and not result.startswith("Failed")
            _feedback_store.record(task=task, selected_tool=name, success=success, context=context)

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
                    logger.info("AI selected tools for orchestration: %s", selected_names)
            except Exception as e:  # noqa: BLE001
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

            logger.info("Orchestration step %d/%d: %s", step_num, len(selected_names), tool_name)
            metrics.increment_counter(f"execute_tasks.step.{tool_name}")

            try:
                tool_arguments = build_arguments(tool, task)
            except Exception as build_error:  # noqa: BLE001
                logger.warning("Error building arguments for %s: %s", tool_name, build_error)
                results.append(f"[{tool_name}] Error building arguments: {build_error}")
                if _feedback_store:
                    _feedback_store.record(task=task, selected_tool=tool_name, success=False, context=accumulated_context)
                continue

            step_result = call_tool(tool_name, tool_arguments)
            results.append(f"[{tool_name}] {step_result}")

            step_success = not step_result.startswith("Error") and not step_result.startswith("Failed")
            if _feedback_store:
                _feedback_store.record(
                    task=task,
                    selected_tool=tool_name,
                    success=step_success,
                    context=accumulated_context,
                )

            # Accumulate context for next step
            accumulated_context = f"{accumulated_context}\nPrevious result: {step_result[:200]}"

        if not results:
            return "No tools were executed."

        metrics.increment_counter("execute_tasks.success")
        return "\n\n".join(results)


@mcp.tool()
def record_feedback(tool_name: str, task: str, success: bool, context: str = "") -> str:
    """Record explicit feedback on a tool selection outcome for context learning."""
    if _feedback_store is None:
        return "Feedback store not initialized."
    _feedback_store.record(task=task, selected_tool=tool_name, success=success, context=context)
    stats = _feedback_store.get_stats(tool_name)
    rate = stats.success_rate if stats else 0.5
    logger.info("Feedback recorded: tool=%s success=%s rate=%.2f", tool_name, success, rate)
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
            logger.exception("Unexpected error listing tools: %s: %s", type(unexpected_error).__name__, unexpected_error)
            metrics.increment_counter("search_tools.errors.unexpected")
            return f"Unexpected error listing tools: {type(unexpected_error).__name__}: {unexpected_error}"

        if not tools:
            logger.warning("No tools registered in gateway")
            metrics.increment_counter("search_tools.no_tools")
            return "No tools registered in the gateway."

        try:
            with TimingContext("search_tools.pick_best_tools"):
                matching_tools = select_top_matching_tools(tools, query, "", top_n=limit)
        except Exception as search_error:
            logger.exception("Error searching tools: %s: %s", type(search_error).__name__, search_error)
            metrics.increment_counter("search_tools.errors.search")
            return f"Error searching tools: {type(search_error).__name__}: {search_error}"

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


def main() -> None:
    """Initialize and run the MCP server."""
    config = ToolRouterConfig.load_from_environment()
    initialize_ai(config)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
