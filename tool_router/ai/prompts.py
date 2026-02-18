"""Prompt templates for AI tool selection."""

from __future__ import annotations


class PromptTemplates:
    """Prompt templates for AI tool selection."""

    TOOL_SELECTION_TEMPLATE = """You are a precise tool selection assistant for an MCP (Model Context Protocol) gateway.
Your job is to select the single best tool for the given task from the available tools.

Task: {task}{context_section}{history_section}

Available tools:
{tool_list}

Rules:
- Select ONLY from the tools listed above using the exact tool name.
- Prefer tools whose name or description closely matches the task intent.
- If multiple tools match, choose the most specific one.
- Set confidence between 0.0 (no match) and 1.0 (perfect match).

Respond with valid JSON only, no extra text:
{{
  "tool_name": "<exact tool name from the list>",
  "confidence": <0.0-1.0>,
  "reasoning": "<one sentence explanation>"
}}"""

    MULTI_TOOL_SELECTION_TEMPLATE = """You are a precise tool selection assistant for an MCP (Model Context Protocol) gateway.
Your job is to select up to {max_tools} tools that together best accomplish the given task.

Task: {task}{context_section}

Available tools:
{tool_list}

Rules:
- Select ONLY from the tools listed above using exact tool names.
- Order tools by execution sequence (first tool first).
- Only include tools that are genuinely needed; fewer is better.
- Set overall confidence between 0.0 and 1.0.

Respond with valid JSON only, no extra text:
{{
  "tools": ["<tool_name_1>", "<tool_name_2>"],
  "confidence": <0.0-1.0>,
  "reasoning": "<one sentence explanation of the sequence>"
}}"""

    @staticmethod
    def create_tool_selection_prompt(
        task: str,
        tool_list: str,
        context: str = "",
        similar_tools: list[str] | None = None,
    ) -> str:
        """Create a context-aware tool selection prompt.

        Args:
            task: The task description
            tool_list: Formatted list of available tools
            context: Optional context to narrow selection
            similar_tools: Tool names that succeeded on similar past tasks

        Returns:
            Complete prompt string
        """
        context_section = f"\nContext: {context}" if context else ""

        history_section = ""
        if similar_tools:
            history_section = (
                "\nHistorically successful tools for similar tasks: "
                + ", ".join(similar_tools)
            )

        return PromptTemplates.TOOL_SELECTION_TEMPLATE.format(
            task=task,
            tool_list=tool_list,
            context_section=context_section,
            history_section=history_section,
        )

    @staticmethod
    def create_multi_tool_selection_prompt(
        task: str,
        tool_list: str,
        context: str = "",
        max_tools: int = 3,
    ) -> str:
        """Create a prompt for selecting multiple tools for orchestration.

        Args:
            task: The task description
            tool_list: Formatted list of available tools
            context: Optional context to narrow selection
            max_tools: Maximum number of tools to select

        Returns:
            Complete prompt string
        """
        context_section = f"\nContext: {context}" if context else ""

        return PromptTemplates.MULTI_TOOL_SELECTION_TEMPLATE.format(
            task=task,
            tool_list=tool_list,
            context_section=context_section,
            max_tools=max_tools,
        )
