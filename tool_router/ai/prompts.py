"""Enhanced prompt templates for AI tool selection with improved NLP."""

from __future__ annotations


class PromptTemplates:
    """Enhanced prompt templates for AI tool selection."""
    
    # Enhanced single-tool selection template with better NLP
    TOOL_SELECTION_TEMPLATE = """You are an expert tool selection assistant for an MCP (Model Context Protocol) gateway.
Your role is to analyze user intent and select the most appropriate tool from the available options.

## Task Analysis
User request: "{task}"
{context_section}
{history_section}

## Available Tools
{tool_list}

## Selection Criteria
1. **Intent Matching**: Analyze the user's core intent and primary goal
2. **Semantic Relevance**: Consider tool names, descriptions, and functionality
3. **Specificity**: Choose the most specific tool for the task (avoid overly general tools)
4. **Context Awareness**: Consider any provided context or previous interactions
5. **Tool Capabilities**: Match the tool's actual capabilities to the required actions

## Decision Process
1. Extract key action verbs and objects from the task
2. Map these to tool functionality
3. Consider tool specificity and appropriateness
4. Evaluate confidence based on match quality

## Response Format
Respond with valid JSON only, no additional text:
{{
  "tool_name": "<exact tool name from the list>",
  "confidence": <0.0-1.0>,
  "reasoning": "<brief explanation of why this tool matches the task intent>",
  "intent_analysis": "<key actions and objects identified in the task>"
}}"""

    # Enhanced multi-tool selection template
    MULTI_TOOL_SELECTION_TEMPLATE = """You are an expert workflow orchestration assistant for an MCP (Model Context Protocol) gateway.
Your role is to analyze complex tasks and select a sequence of tools that work together effectively.

## Task Analysis
User request: "{task}"
{context_section}

## Available Tools
{tool_list}

## Orchestration Principles
1. **Logical Sequence**: Order tools by execution dependency (prerequisites first)
2. **Task Decomposition**: Break complex tasks into logical steps
3. **Tool Synergy**: Select tools that complement each other
4. **Efficiency**: Minimize the number of tools while achieving the goal
5. **No Redundancy**: Avoid selecting tools with overlapping functionality

## Selection Guidelines
- Maximum {max_tools} tools unless absolutely necessary
- Each tool should add unique value to the workflow
- Consider data flow and dependencies between tools
- Prioritize tools that handle different aspects of the task

## Response Format
Respond with valid JSON only, no additional text:
{{
  "tools": ["<tool_name_1>", "<tool_name_2>"],
  "confidence": <0.0-1.0>,
  "reasoning": "<explanation of the workflow and why these tools in sequence>",
  "workflow_steps": "<brief description of what each tool accomplishes>",
  "dependencies": "<any dependencies between the tools>"
}}"""

    # Context-aware enhancement template
    CONTEXT_ENHANCED_TEMPLATE = """You are an intelligent tool selection assistant with contextual awareness for MCP (Model Context Protocol) gateway.
Your role is to understand the user's intent, consider the conversation context, and select the optimal tool.

## Contextual Information
{context_section}

## Conversation History
{history_section}

## Current Task
User request: "{task}"

## Available Tools
{tool_list}

## Enhanced Analysis
1. **Intent Recognition**: Identify the user's primary goal and any implicit requirements
2. **Context Integration**: Leverage conversation history and previous selections
3. **Pattern Recognition**: Recognize common task patterns and user preferences
4. **Adaptive Selection**: Adjust based on previous successes/failures
5. **Semantic Understanding**: Go beyond keyword matching to understand meaning

## Selection Strategy
- Consider what the user has tried before
- Look for patterns in similar previous tasks
- Account for any stated preferences or constraints
- Balance between familiar tools and optimal solutions
- Consider learning from feedback and success rates

## Response Format
Respond with valid JSON only, no additional text:
{{
  "tool_name": "<exact tool name from the list>",
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation considering context and history>",
  "context_factors": "<key contextual elements that influenced the decision>",
  "learning_insights": "<any patterns or preferences identified>"
}}"""

    @classmethod
    def create_tool_selection_prompt(
        cls,
        task: str,
        tool_list: str,
        context: str = "",
        similar_tools: list[str] | None = None,
        enhanced: bool = True,
    ) -> str:
        """Create a tool selection prompt with optional enhancements."""
        context_section = ""
        if context:
            context_section = f"\n\n## Context\n{context}"
        
        history_section = ""
        if similar_tools:
            history_section = f"\n\n## Similar Successful Tools\nPreviously successful for similar tasks: {', '.join(similar_tools)}"
        
        if enhanced:
            template = cls.CONTEXT_ENHANCED_TEMPLATE
        else:
            template = cls.TOOL_SELECTION_TEMPLATE
        
        return template.format(
            task=task,
            tool_list=tool_list,
            context_section=context_section,
            history_section=history_section,
        )
    
    @classmethod
    def create_multi_tool_selection_prompt(
        cls,
        task: str,
        tool_list: str,
        context: str = "",
        max_tools: int = 3,
        enhanced: bool = True,
    ) -> str:
        """Create a multi-tool selection prompt with optional enhancements."""
        context_section = ""
        if context:
            context_section = f"\n\n## Context\n{context}"
        
        if enhanced:
            # Add workflow analysis section
            context_section += "\n\n## Workflow Considerations\nConsider the logical flow and dependencies between tools."
        
        return cls.MULTI_TOOL_SELECTION_TEMPLATE.format(
            task=task,
            tool_list=tool_list,
            context_section=context_section,
            max_tools=max_tools,
        )
    
    @classmethod
    def create_context_aware_prompt(
        cls,
        task: str,
        tool_list: str,
        context: str = "",
        history: list[dict[str, Any]] | None = None,
        similar_tools: list[str] | None = None,
    ) -> str:
        """Create a context-aware prompt with full history."""
        context_section = ""
        if context:
            context_section = f"\n\n## Current Context\n{context}"
        
        history_section = ""
        if history:
            history_items = []
            for i, item in enumerate(history[-5:], 1):  # Last 5 interactions
                history_items.append(f"{i}. Task: '{item.get('task', 'Unknown')}' -> Tool: '{item.get('tool', 'None')}' (Success: {item.get('success', 'Unknown')})")
            history_section = f"\n\n## Recent History\n" + "\n".join(history_items)
        
        similar_tools_section = ""
        if similar_tools:
            similar_tools_section = f"\n\n## Similar Successful Tools\n{', '.join(similar_tools)}"
        
        return cls.CONTEXT_ENHANCED_TEMPLATE.format(
            task=task,
            tool_list=tool_list,
            context_section=context_section,
            history_section=history_section + similar_tools_section,
        )
    
    @classmethod
    def create_nlp_enhanced_prompt(
        cls,
        task: str,
        tool_list: str,
        context: str = "",
        intent_hints: list[str] | None = None,
    ) -> str:
        """Create an NLP-enhanced prompt with intent hints."""
        context_section = ""
        if context:
            context_section = f"\n\n## Context\n{context}"
        
        hints_section = ""
        if intent_hints:
            hints_section = f"\n\n## Intent Hints\nConsider these aspects: {', '.join(intent_hints)}"
        
        # Enhanced template with NLP focus
        template = """You are an advanced NLP-powered tool selection assistant for MCP (Model Context Protocol) gateway.
Your role is to perform deep semantic analysis of user requests and select the most appropriate tool.

## Linguistic Analysis
User request: "{task}"
{context_section}
{hints_section}

## Semantic Analysis Framework
1. **Action Extraction**: Identify primary verbs and action words
2. **Entity Recognition**: Extract key entities, objects, and concepts
3. **Intent Classification**: Categorize the user's intent (create, read, update, delete, search, etc.)
4. **Semantic Similarity**: Compute semantic similarity between task and tool descriptions
5. **Contextual Relevance**: Consider how context modifies or clarifies the intent

## Available Tools
{tool_list}

## Selection Methodology
- Perform semantic matching rather than just keyword matching
- Consider the full meaning and nuance of the request
- Evaluate tool capabilities against user requirements
- Account for contextual modifiers and constraints
- Use confidence scoring based on semantic alignment

## Response Format
Respond with valid JSON only, no additional text:
{{
  "tool_name": "<exact tool name from the list>",
  "confidence": <0.0-1.0>,
  "reasoning": "<semantic analysis explanation>",
  "intent_type": "<classified intent category>",
  "key_entities": "<main entities identified>",
  "semantic_score": <0.0-1.0>
}}"""
        
        return template.format(
            task=task,
            tool_list=tool_list,
            context_section=context_section,
            hints_section=hints_section,
        )