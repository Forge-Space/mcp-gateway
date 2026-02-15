"""Prompt templates for AI-powered tool selection."""

TOOL_SELECTION_PROMPT = """You are a tool selection assistant for an MCP (Model Context Protocol) gateway.

Your task: Given a user's task description and a list of available tools, select the BEST matching tool.

User's task:
{task}

Available tools:
{tool_list}

Instructions:
1. Analyze the task carefully to understand what the user wants to accomplish
2. Review each tool's name and description
3. Select the single best tool that matches the task
4. Provide your confidence level (0.0 to 1.0)
5. Briefly explain why this tool is the best match

Respond with ONLY valid JSON in this exact format:
{{
  "tool_name": "<exact tool name from the list>",
  "confidence": <number between 0.0 and 1.0>,
  "reasoning": "<brief explanation in one sentence>"
}}

Important:
- tool_name MUST exactly match one of the tool names provided
- confidence should be high (>0.7) for clear matches, lower (<0.5) for uncertain matches
- reasoning should be concise (max 100 characters)
- Return ONLY the JSON object, no other text"""


def format_tool_list(tools: list[dict]) -> str:
    """Format tools into a readable list for the prompt.

    Args:
        tools: List of tool dictionaries with 'name' and 'description' keys

    Returns:
        Formatted string listing all tools
    """
    formatted_tools = []
    for idx, tool in enumerate(tools, 1):
        name = tool.get("name", "unknown")
        description = tool.get("description", "No description")
        # Truncate long descriptions to keep prompt size manageable
        if len(description) > 150:
            description = description[:147] + "..."
        formatted_tools.append(f"{idx}. {name}: {description}")

    return "\n".join(formatted_tools)


def build_selection_prompt(task: str, tools: list[dict]) -> str:
    """Build the complete prompt for tool selection.

    Args:
        task: User's task description
        tools: List of available tools

    Returns:
        Complete formatted prompt
    """
    tool_list = format_tool_list(tools)
    # Escape braces in user input to prevent KeyError
    escaped_task = task.replace("{", "{{").replace("}", "}}")
    escaped_tool_list = tool_list.replace("{", "{{").replace("}", "}}")
    return TOOL_SELECTION_PROMPT.format(task=escaped_task, tool_list=escaped_tool_list)
