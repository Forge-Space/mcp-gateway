"""Unit tests for tool_router/ai/prompts.py module."""

from __future__ import annotations

from tool_router.ai.prompts import PromptTemplates


def test_prompt_templates_class_exists() -> None:
    """Test that PromptTemplates class exists and has expected attributes."""
    assert hasattr(PromptTemplates, "TOOL_SELECTION_TEMPLATE")
    assert hasattr(PromptTemplates, "MULTI_TOOL_SELECTION_TEMPLATE")
    assert hasattr(PromptTemplates, "CONTEXT_ENHANCED_TEMPLATE")
    assert callable(PromptTemplates.create_tool_selection_prompt)
    assert callable(PromptTemplates.create_multi_tool_selection_prompt)
    assert callable(PromptTemplates.create_context_aware_prompt)
    assert callable(PromptTemplates.create_nlp_enhanced_prompt)


def test_create_tool_selection_prompt_basic() -> None:
    """Test basic tool selection prompt creation."""
    task = "search the web"
    tool_list = "search: Search the web\nfetch: Get URL"

    prompt = PromptTemplates.create_tool_selection_prompt(
        task=task,
        tool_list=tool_list,
        context="",
        similar_tools=None,
        enhanced=False,
    )

    assert task in prompt
    assert tool_list in prompt
    assert "tool_name" in prompt
    assert "confidence" in prompt
    assert "reasoning" in prompt


def test_create_tool_selection_prompt_with_context() -> None:
    """Test tool selection prompt creation with context."""
    task = "search the web"
    tool_list = "search: Search the web"
    context = "Looking for recent news"

    prompt = PromptTemplates.create_tool_selection_prompt(
        task=task,
        tool_list=tool_list,
        context=context,
        similar_tools=None,
        enhanced=False,
    )

    assert task in prompt
    assert tool_list in prompt
    assert context in prompt
    assert "## Context" in prompt


def test_create_tool_selection_prompt_with_similar_tools() -> None:
    """Test tool selection prompt creation with similar tools."""
    task = "search the web"
    tool_list = "search: Search the web"
    similar_tools = ["web_search", "find"]

    prompt = PromptTemplates.create_tool_selection_prompt(
        task=task,
        tool_list=tool_list,
        context="",
        similar_tools=similar_tools,
        enhanced=False,
    )

    assert task in prompt
    assert tool_list in prompt
    assert "web_search" in prompt
    assert "find" in prompt
    assert "## Similar Successful Tools" in prompt


def test_create_tool_selection_prompt_enhanced() -> None:
    """Test enhanced tool selection prompt creation."""
    task = "search the web"
    tool_list = "search: Search the web"

    prompt = PromptTemplates.create_tool_selection_prompt(
        task=task,
        tool_list=tool_list,
        context="",
        similar_tools=None,
        enhanced=True,
    )

    assert task in prompt
    assert tool_list in prompt
    assert "context_factors" in prompt
    assert "learning_insights" in prompt
    assert "## Contextual Information" in prompt


def test_create_tool_selection_prompt_with_all_options() -> None:
    """Test tool selection prompt creation with all options."""
    task = "search the web"
    tool_list = "search: Search the web"
    context = "Looking for recent news"
    similar_tools = ["web_search"]

    prompt = PromptTemplates.create_tool_selection_prompt(
        task=task,
        tool_list=tool_list,
        context=context,
        similar_tools=similar_tools,
        enhanced=True,
    )

    assert task in prompt
    assert tool_list in prompt
    assert context in prompt
    assert "web_search" in prompt
    assert "## Contextual Information" in prompt
    assert "## Conversation History" in prompt


def test_create_multi_tool_selection_prompt_basic() -> None:
    """Test basic multi-tool selection prompt creation."""
    task = "analyze data and create report"
    tool_list = "analyze: Analyze data\nreport: Create report"

    prompt = PromptTemplates.create_multi_tool_selection_prompt(
        task=task,
        tool_list=tool_list,
        context="",
        max_tools=3,
        enhanced=False,
    )

    assert task in prompt
    assert tool_list in prompt
    assert "tools" in prompt
    assert "confidence" in prompt
    assert "reasoning" in prompt
    assert "workflow_steps" in prompt


def test_create_multi_tool_selection_prompt_with_context() -> None:
    """Test multi-tool selection prompt creation with context."""
    task = "analyze data and create report"
    tool_list = "analyze: Analyze data\nreport: Create report"
    context = "Sales data analysis"

    prompt = PromptTemplates.create_multi_tool_selection_prompt(
        task=task,
        tool_list=tool_list,
        context=context,
        max_tools=2,
        enhanced=False,
    )

    assert task in prompt
    assert tool_list in prompt
    assert context in prompt
    assert "## Context" in prompt


def test_create_multi_tool_selection_prompt_enhanced() -> None:
    """Test enhanced multi-tool selection prompt creation."""
    task = "analyze data and create report"
    tool_list = "analyze: Analyze data\nreport: Create report"

    prompt = PromptTemplates.create_multi_tool_selection_prompt(
        task=task,
        tool_list=tool_list,
        context="",
        max_tools=3,
        enhanced=True,
    )

    assert task in prompt
    assert tool_list in prompt
    assert "## Workflow Considerations" in prompt


def test_create_context_aware_prompt_basic() -> None:
    """Test basic context-aware prompt creation."""
    task = "search the web"
    tool_list = "search: Search the web"

    prompt = PromptTemplates.create_context_aware_prompt(
        task=task,
        tool_list=tool_list,
        context="",
        history=None,
        similar_tools=None,
    )

    assert task in prompt
    assert tool_list in prompt
    assert "## Current Context" not in prompt
    assert "## Recent History" not in prompt


def test_create_context_aware_prompt_with_context() -> None:
    """Test context-aware prompt creation with context."""
    task = "search the web"
    tool_list = "search: Search the web"
    context = "Looking for recent news"

    prompt = PromptTemplates.create_context_aware_prompt(
        task=task,
        tool_list=tool_list,
        context=context,
        history=None,
        similar_tools=None,
    )

    assert task in prompt
    assert tool_list in prompt
    assert context in prompt
    assert "## Current Context" in prompt


def test_create_context_aware_prompt_with_history() -> None:
    """Test context-aware prompt creation with history."""
    task = "search the web"
    tool_list = "search: Search the web"
    history = [
        {"task": "find information", "tool": "search", "success": True},
        {"task": "get data", "tool": "fetch", "success": False},
    ]

    prompt = PromptTemplates.create_context_aware_prompt(
        task=task,
        tool_list=tool_list,
        context="",
        history=history,
        similar_tools=None,
    )

    assert task in prompt
    assert tool_list in prompt
    assert "find information" in prompt
    assert "get data" in prompt
    assert "## Recent History" in prompt


def test_create_context_aware_prompt_with_similar_tools() -> None:
    """Test context-aware prompt creation with similar tools."""
    task = "search the web"
    tool_list = "search: Search the web"
    similar_tools = ["web_search", "find"]

    prompt = PromptTemplates.create_context_aware_prompt(
        task=task,
        tool_list=tool_list,
        context="",
        history=None,
        similar_tools=similar_tools,
    )

    assert task in prompt
    assert tool_list in prompt
    assert "web_search" in prompt
    assert "find" in prompt
    assert "## Similar Successful Tools" in prompt


def test_create_context_aware_prompt_with_all_options() -> None:
    """Test context-aware prompt creation with all options."""
    task = "search the web"
    tool_list = "search: Search the web"
    context = "Looking for recent news"
    history = [{"task": "find info", "tool": "search", "success": True}]
    similar_tools = ["web_search"]

    prompt = PromptTemplates.create_context_aware_prompt(
        task=task,
        tool_list=tool_list,
        context=context,
        history=history,
        similar_tools=similar_tools,
    )

    assert task in prompt
    assert tool_list in prompt
    assert context in prompt
    assert "find info" in prompt
    assert "web_search" in prompt
    assert "## Current Context" in prompt
    assert "## Recent History" in prompt
    assert "## Similar Successful Tools" in prompt


def test_create_nlp_enhanced_prompt_basic() -> None:
    """Test basic NLP-enhanced prompt creation."""
    task = "search the web"
    tool_list = "search: Search the web"

    prompt = PromptTemplates.create_nlp_enhanced_prompt(
        task=task,
        tool_list=tool_list,
        context="",
        intent_hints=None,
    )

    assert task in prompt
    assert tool_list in prompt
    assert "## Linguistic Analysis" in prompt
    assert "## Semantic Analysis Framework" in prompt
    assert "intent_type" in prompt
    assert "key_entities" in prompt
    assert "semantic_score" in prompt


def test_create_nlp_enhanced_prompt_with_context() -> None:
    """Test NLP-enhanced prompt creation with context."""
    task = "search the web"
    tool_list = "search: Search the web"
    context = "Looking for recent news"

    prompt = PromptTemplates.create_nlp_enhanced_prompt(
        task=task,
        tool_list=tool_list,
        context=context,
        intent_hints=None,
    )

    assert task in prompt
    assert tool_list in prompt
    assert context in prompt
    assert "## Context" in prompt


def test_create_nlp_enhanced_prompt_with_intent_hints() -> None:
    """Test NLP-enhanced prompt creation with intent hints."""
    task = "search the web"
    tool_list = "search: Search the web"
    intent_hints = ["information retrieval", "web search"]

    prompt = PromptTemplates.create_nlp_enhanced_prompt(
        task=task,
        tool_list=tool_list,
        context="",
        intent_hints=intent_hints,
    )

    assert task in prompt
    assert tool_list in prompt
    assert "information retrieval" in prompt
    assert "web search" in prompt
    assert "## Intent Hints" in prompt


def test_create_nlp_enhanced_prompt_with_all_options() -> None:
    """Test NLP-enhanced prompt creation with all options."""
    task = "search the web"
    tool_list = "search: Search the web"
    context = "Looking for recent news"
    intent_hints = ["information retrieval", "web search"]

    prompt = PromptTemplates.create_nlp_enhanced_prompt(
        task=task,
        tool_list=tool_list,
        context=context,
        intent_hints=intent_hints,
    )

    assert task in prompt
    assert tool_list in prompt
    assert context in prompt
    assert "information retrieval" in prompt
    assert "web search" in prompt
    assert "## Context" in prompt
    assert "## Intent Hints" in prompt


def test_tool_selection_template_structure() -> None:
    """Test that TOOL_SELECTION_TEMPLATE has expected structure."""
    template = PromptTemplates.TOOL_SELECTION_TEMPLATE
    assert "## Task Analysis" in template
    assert "## Available Tools" in template
    assert "## Selection Criteria" in template
    assert "## Decision Process" in template
    assert "## Response Format" in template
    assert "{task}" in template
    assert "{tool_list}" in template


def test_multi_tool_selection_template_structure() -> None:
    """Test that MULTI_TOOL_SELECTION_TEMPLATE has expected structure."""
    template = PromptTemplates.MULTI_TOOL_SELECTION_TEMPLATE
    assert "## Task Analysis" in template
    assert "## Available Tools" in template
    assert "## Orchestration Principles" in template
    assert "## Selection Guidelines" in template
    assert "## Response Format" in template
    assert "{task}" in template
    assert "{tool_list}" in template
    assert "{max_tools}" in template


def test_context_enhanced_template_structure() -> None:
    """Test that CONTEXT_ENHANCED_TEMPLATE has expected structure."""
    template = PromptTemplates.CONTEXT_ENHANCED_TEMPLATE
    assert "## Contextual Information" in template
    assert "## Conversation History" in template
    assert "## Current Task" in template
    assert "## Available Tools" in template
    assert "## Enhanced Analysis" in template
    assert "## Selection Strategy" in template
    assert "## Response Format" in template
    assert "{task}" in template
    assert "{tool_list}" in template
