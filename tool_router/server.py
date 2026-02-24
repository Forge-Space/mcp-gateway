from __future__ import annotations

from tool_router.args import build_arguments
from tool_router.gateway_client import call_tool, get_tools
from tool_router.scoring import pick_best_tools

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    msg = "Install the MCP SDK: pip install mcp"
    raise ImportError(msg) from None

mcp = FastMCP("tool-router", json_response=True)


@mcp.tool()
def execute_task(task: str, context: str = "") -> str:
    """Run the best matching gateway tool for the given task. Describe what you want (e.g. 'search the web for X', 'list files in /tmp'). Optional context can narrow the choice."""
    try:
        tools = get_tools()
    except (ValueError, ConnectionError) as e:
        return f"Failed to list tools: {e}"
    except (OSError, RuntimeError) as e:
        return f"Unexpected error listing tools: {type(e).__name__}: {e}"

    if not tools:
        return "No tools registered in the gateway."

    try:
        best = pick_best_tools(tools, task, context, top_n=1)
    except (ValueError, KeyError, TypeError) as e:
        return f"Error selecting tool: {type(e).__name__}: {e}"

    if not best:
        return "No matching tool found; try describing the task differently."

    tool = best[0]
    name = tool.get("name") or ""
    if not name:
        return "Chosen tool has no name."

    try:
        args = build_arguments(tool, task)
    except (ValueError, KeyError, TypeError) as e:
        return f"Error building arguments: {type(e).__name__}: {e}"

    return call_tool(name, args)


@mcp.tool()
def search_tools(query: str) -> str:
    """List gateway tools whose name or description matches the query. Use this to discover tools before calling execute_task."""
    try:
        tools = get_tools()
    except (ValueError, ConnectionError) as e:
        return f"Failed to list tools: {e}"
    except (OSError, RuntimeError) as e:
        return f"Unexpected error listing tools: {type(e).__name__}: {e}"

    if not tools:
        return "No tools registered in the gateway."

    try:
        best = pick_best_tools(tools, query, "", top_n=10)
    except (ValueError, KeyError, TypeError) as e:
        return f"Error searching tools: {type(e).__name__}: {e}"

    if not best:
        return "No tools match the query."

    lines = []
    for t in best:
        name = t.get("name", "")
        desc = (t.get("description") or "")[:80]
        gw = t.get("gatewaySlug") or t.get("gateway_slug") or ""
        lines.append(f"- {name} ({gw}): {desc}")
    return "\n".join(lines)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
