"""MCP Tools for Specialist Training Infrastructure.

This module provides MCP server tools for managing specialist AI training,
including training pipeline management, knowledge base operations, and evaluation.
"""

from __future__ import annotations

from .evaluation_tool import EVALUATION_SCHEMA, EvaluationTool, evaluation_handler
from .knowledge_base_tool import (
    KNOWLEDGE_BASE_SCHEMA,
    KnowledgeBaseTool,
    knowledge_base_handler,
)
from .server_integration import (
    SpecialistTrainingMCPServer,
    get_server_instance,
    register_tools_with_mcp_server,
)
from .training_manager import (
    TRAINING_MANAGER_SCHEMA,
    TrainingManagerTool,
    training_manager_handler,
)


__all__ = [
    # Training Manager
    "TrainingManagerTool",
    "TRAINING_MANAGER_SCHEMA",
    "training_manager_handler",
    # Knowledge Base
    "KnowledgeBaseTool",
    "KNOWLEDGE_BASE_SCHEMA",
    "knowledge_base_handler",
    # Evaluation
    "EvaluationTool",
    "EVALUATION_SCHEMA",
    "evaluation_handler",
    # Server Integration
    "SpecialistTrainingMCPServer",
    "get_server_instance",
    "register_tools_with_mcp_server",
]
