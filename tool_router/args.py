from typing import Any


# Common parameter names that typically accept task descriptions
TASK_PARAM_NAMES = [
    "query",
    "q",
    "search",
    "task",
    "prompt",
    "question",
    "input",
    "text",
    "message",
    "command",
]


def build_arguments(tool: dict[str, Any], task: str) -> dict[str, Any]:
    """Build arguments for a tool call based on its schema and the task description.

    Attempts to intelligently map the task to the most appropriate parameter.
    For tools with multiple required parameters, only the primary task parameter is filled.
    """
    schema = tool.get("inputSchema") or tool.get("input_schema") or {}
    props = schema.get("properties") or {}
    required = schema.get("required") or []
    args: dict[str, Any] = {}

    # Try to find a common task parameter name in order of preference
    for param_name in TASK_PARAM_NAMES:
        if param_name in props or param_name in required:
            args[param_name] = task
            return args

    # If no common parameter found, use the first required parameter if it accepts strings
    if required:
        first = required[0]
        first_prop = props.get(first, {})
        prop_type = first_prop.get("type", "string")

        # Only use first required param if it's a string type
        if prop_type in ("string", "text") or not prop_type:
            args[first] = task
            return args

    # Fallback: use "task" as parameter name
    args["task"] = task
    return args
