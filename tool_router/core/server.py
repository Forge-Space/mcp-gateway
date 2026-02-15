from __future__ import annotations

from tool_router.ai.selector import AIToolSelector
from tool_router.args.builder import build_arguments
from tool_router.core.config import ToolRouterConfig
from tool_router.gateway.client import call_tool, get_tools
from tool_router.observability import get_logger, get_metrics
from tool_router.observability.metrics import TimingContext
from tool_router.scoring.matcher import (
    select_top_matching_tools,
    select_top_matching_tools_with_ai,
)


try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    msg = "Install the MCP SDK: pip install mcp"
    raise ImportError(msg) from None

mcp = FastMCP("tool-router", json_response=True)
logger = get_logger(__name__)
metrics = get_metrics()

# Configuration and AI selector will be initialized in main()
config = None
ai_selector = None


@mcp.tool()
def execute_task(task: str, context: str = "") -> str:
    """Run the best matching gateway tool for the given task. Describe what you want (e.g. 'search the web for X', 'list files in /tmp'). Optional context can narrow the choice."""
    if config is None:
        return "Service not initialized. Please wait for startup to complete."

    logger.info(f"Executing task: {task[:100]}")
    metrics.increment_counter("execute_task.calls")

    with TimingContext("execute_task.total_duration"):
        try:
            with TimingContext("execute_task.get_tools"):
                tools = get_tools()
        except (ValueError, ConnectionError) as error:
            logger.exception(f"Failed to list tools: {error}")
            metrics.increment_counter("execute_task.errors.get_tools")
            return f"Failed to list tools: {error}"
        except Exception as unexpected_error:
            logger.exception(f"Unexpected error listing tools: {type(unexpected_error).__name__}: {unexpected_error}")
            metrics.increment_counter("execute_task.errors.unexpected")
            return f"Unexpected error listing tools: {type(unexpected_error).__name__}: {unexpected_error}"

        if not tools:
            logger.warning("No tools registered in gateway")
            metrics.increment_counter("execute_task.no_tools")
            return "No tools registered in the gateway."

        # Try AI selection first if enabled, with fallback to keyword matching
        best_matching_tools = []
        selection_method = "keyword"

        if ai_selector:
            try:
                with TimingContext("execute_task.ai_selection"):
                    ai_result = ai_selector.select_tool(task, tools)

                if ai_result and ai_result.get("confidence", 0.0) > config.ai.min_confidence:
                    # AI selection successful with reasonable confidence
                    ai_tool_name = ai_result["tool_name"]
                    ai_confidence = ai_result["confidence"]
                    ai_reasoning = ai_result.get("reasoning", "")

                    logger.info("AI selected: %s (confidence: %.2f) - %s", ai_tool_name, ai_confidence, ai_reasoning)
                    metrics.increment_counter("execute_task.ai_selection.success")
                    metrics.record_gauge("execute_task.ai_confidence", ai_confidence)

                    # Use hybrid scoring
                    with TimingContext("execute_task.hybrid_scoring"):
                        best_matching_tools = select_top_matching_tools_with_ai(
                            tools=tools,
                            task=task,
                            context=context,
                            ai_selected_tool=ai_tool_name,
                            ai_confidence=ai_confidence,
                            ai_weight=config.ai.weight,
                            top_n=1,
                        )
                    selection_method = "hybrid_ai"
                else:
                    logger.info("AI selection confidence too low, falling back to keyword matching")
                    metrics.increment_counter("execute_task.ai_selection.low_confidence")

            except Exception as ai_error:
                logger.warning("AI selection failed: %s, falling back to keyword matching", ai_error, exc_info=True)
                metrics.increment_counter("execute_task.ai_selection.error")

        # Fallback to keyword matching if AI not used or failed
        if not best_matching_tools:
            try:
                with TimingContext("execute_task.keyword_selection"):
                    best_matching_tools = select_top_matching_tools(tools, task, context, top_n=1)
                metrics.increment_counter("execute_task.keyword_selection")
            except Exception as selection_error:
                logger.exception(f"Error picking tool: {type(selection_error).__name__}: {selection_error}")
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

        logger.info(f"Selected tool: {name} (method: {selection_method})")
        metrics.increment_counter(f"execute_task.tool_selected.{name}")
        metrics.increment_counter(f"execute_task.selection_method.{selection_method}")

        try:
            with TimingContext("execute_task.build_arguments"):
                tool_arguments = build_arguments(tool, task)
        except Exception as build_error:
            logger.exception(f"Error building arguments: {type(build_error).__name__}: {build_error}")
            metrics.increment_counter("execute_task.errors.build_args")
            return f"Error building arguments: {type(build_error).__name__}: {build_error}"

        with TimingContext("execute_task.call_tool"):
            result = call_tool(name, tool_arguments)

        logger.info(f"Task completed successfully with tool: {name}")
        metrics.increment_counter("execute_task.success")
        return result


@mcp.tool()
def search_tools(query: str, limit: int = 10) -> str:
    """Search available tools by name or description. Returns a list of matching tools with their details."""
    if config is None:
        return "Service not initialized. Please wait for startup to complete."

    logger.info(f"Searching tools: {query[:100]}")
    metrics.increment_counter("search_tools.calls")

    with TimingContext("search_tools.total_duration"):
        try:
            with TimingContext("search_tools.get_tools"):
                tools = get_tools()
        except (ValueError, ConnectionError) as error:
            logger.exception(f"Failed to list tools: {error}")
            metrics.increment_counter("search_tools.errors.get_tools")
            return f"Failed to list tools: {error}"
        except Exception as unexpected_error:
            logger.exception(f"Unexpected error listing tools: {type(unexpected_error).__name__}: {unexpected_error}")
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
            logger.exception(f"Error searching tools: {type(search_error).__name__}: {search_error}")
            metrics.increment_counter("search_tools.errors.search")
            return f"Error searching tools: {type(search_error).__name__}: {search_error}"

        if not matching_tools:
            logger.info(f"No tools found matching: {query}")
            metrics.increment_counter("search_tools.no_matches")
            return f"No tools found matching '{query}'."

        logger.info(f"Found {len(matching_tools)} matching tools")
        metrics.increment_counter("search_tools.success")

        lines = [f"Found {len(matching_tools)} matching tool(s):"]
        for index, tool in enumerate(matching_tools, 1):
            name = tool.get("name", "unknown")
            description = tool.get("description", "No description")
            lines.append(f"{index}. {name}: {description}")

        return "\n".join(lines)


def main() -> None:
    global config, ai_selector

    # Initialize configuration and AI selector at startup
    try:
        config = ToolRouterConfig.load_from_environment()
    except Exception as e:
        logger.exception("Failed to load configuration: %s", e)
        raise

    if config.ai.enabled:
        try:
            ai_selector = AIToolSelector(
                endpoint=config.ai.endpoint,
                model=config.ai.model,
                timeout_ms=config.ai.timeout_ms,
            )
            if ai_selector.is_available():
                logger.info("AI selector initialized with model: %s", config.ai.model)
                metrics.increment_counter("ai_selector.initialized")
            else:
                logger.warning(
                    "Ollama service not available at %s, using keyword matching fallback", config.ai.endpoint
                )
                metrics.increment_counter("ai_selector.unavailable")
                ai_selector = None
        except Exception as e:
            logger.warning("Failed to initialize AI selector: %s, using keyword matching fallback", e)
            metrics.increment_counter("ai_selector.init_error")
            ai_selector = None
    else:
        logger.info("AI selector disabled, using keyword matching only")
        metrics.increment_counter("ai_selector.disabled")

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
