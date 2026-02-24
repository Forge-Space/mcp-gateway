from __future__ import annotations

from typing import Any

# Common parameter names that typically accept task descriptions
COMMON_TASK_PARAMETER_NAMES = [
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
    schema_properties = schema.get("properties") or {}
    required_parameters = schema.get("required") or []
    tool_arguments: dict[str, Any] = {}

    # Try to find a common task parameter name in order of preference
    for param_name in COMMON_TASK_PARAMETER_NAMES:
        if param_name in schema_properties or param_name in required_parameters:
            tool_arguments[param_name] = task
            return tool_arguments

    # If no common parameter found, use the first required parameter if it accepts strings
    if required_parameters:
        first_required_parameter = required_parameters[0]
        first_parameter_definition = schema_properties.get(first_required_parameter, {})
        parameter_type = first_parameter_definition.get("type", "string")

        # Only use first required param if it's a string type
        if parameter_type in ("string", "text") or not parameter_type:
            tool_arguments[first_required_parameter] = task
            return tool_arguments

    # Fallback: use "task" as parameter name
    tool_arguments["task"] = task
    return tool_arguments
