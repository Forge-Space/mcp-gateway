"""MCP Server Integration for Specialist Training Tools.

This module integrates the specialist training infrastructure with the MCP Gateway
server, providing tools for training management, knowledge base operations, and evaluation.
"""

from __future__ import annotations

import logging
from typing import Any

from .evaluation_tool import EVALUATION_SCHEMA, EvaluationTool, evaluation_handler
from .knowledge_base_tool import KNOWLEDGE_BASE_SCHEMA, KnowledgeBaseTool, knowledge_base_handler
from .training_manager import TRAINING_MANAGER_SCHEMA, TrainingManagerTool, training_manager_handler


logger = logging.getLogger(__name__)


class SpecialistTrainingMCPServer:
    """MCP Server integration for specialist training infrastructure."""

    def __init__(self) -> None:
        """Initialize the MCP server integration."""
        self.training_manager = TrainingManagerTool()
        self.knowledge_base = KnowledgeBaseTool()
        self.evaluator = EvaluationTool()

        # Tool registry
        self.tools = {
            "training_manager": {"schema": TRAINING_MANAGER_SCHEMA, "handler": training_manager_handler},
            "knowledge_base": {"schema": KNOWLEDGE_BASE_SCHEMA, "handler": knowledge_base_handler},
            "evaluation": {"schema": EVALUATION_SCHEMA, "handler": evaluation_handler},
        }

        logger.info("Specialist Training MCP Server initialized with 3 tools")

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get all tool definitions for MCP server registration.

        Returns:
            List of tool definitions
        """
        tool_definitions = []

        for tool_name, tool_config in self.tools.items():
            tool_definitions.append(
                {
                    "name": tool_name,
                    "description": self._get_tool_description(tool_name),
                    "schema": tool_config["schema"],
                }
            )

        return tool_definitions

    def _get_tool_description(self, tool_name: str) -> str:
        """Get description for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool description
        """
        descriptions = {
            "training_manager": "Manage specialist AI training pipeline operations including starting training runs, monitoring progress, and managing training configurations",
            "knowledge_base": "Manage the specialist AI knowledge base including adding patterns, searching, and managing knowledge items",
            "evaluation": "Evaluate specialist AI agents including running evaluations, getting results, and managing evaluation metrics",
        }

        return descriptions.get(tool_name, "Specialist training tool")

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool with given arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        try:
            if tool_name not in self.tools:
                return {"error": f"Unknown tool: {tool_name}", "message": f"Available tools: {list(self.tools.keys())}"}

            tool_config = self.tools[tool_name]
            handler = tool_config["handler"]

            # Execute the tool handler
            result = handler(arguments)

            logger.info(f"Executed tool '{tool_name}' successfully")
            return result

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return {"error": str(e), "message": f"Tool execution failed: {tool_name}"}

    def get_server_info(self) -> dict[str, Any]:
        """Get server information and capabilities.

        Returns:
            Server information
        """
        return {
            "name": "Specialist Training MCP Server",
            "version": "1.0.0",
            "description": "MCP server for managing specialist AI training infrastructure",
            "tools": list(self.tools.keys()),
            "capabilities": [
                "Training pipeline management",
                "Knowledge base operations",
                "Specialist evaluation",
                "Pattern management",
                "Performance monitoring",
            ],
            "supported_specialists": ["ui_specialist", "prompt_architect", "router_specialist"],
            "supported_categories": [
                "react_pattern",
                "ui_component",
                "accessibility",
                "prompt_engineering",
                "architecture",
                "code_pattern",
                "best_practice",
            ],
        }

    def health_check(self) -> dict[str, Any]:
        """Perform health check on all components.

        Returns:
            Health check results
        """
        try:
            health_status = {"status": "healthy", "timestamp": "2026-02-19T12:00:00Z", "components": {}}

            # Check training manager
            try:
                stats = self.training_manager.get_training_statistics()
                health_status["components"]["training_manager"] = {
                    "status": "healthy",
                    "total_runs": stats.get("total_runs", 0),
                }
            except Exception as e:
                health_status["components"]["training_manager"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"

            # Check knowledge base
            try:
                kb_stats = self.knowledge_base.get_knowledge_base_statistics()
                health_status["components"]["knowledge_base"] = {
                    "status": "healthy",
                    "total_items": kb_stats.get("statistics", {}).get("total_items", 0),
                }
            except Exception as e:
                health_status["components"]["knowledge_base"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"

            # Check evaluator
            try:
                specialists = self.evaluator.get_available_specialists()
                health_status["components"]["evaluation"] = {
                    "status": "healthy",
                    "available_specialists": specialists.get("total_specialists", 0),
                }
            except Exception as e:
                health_status["components"]["evaluation"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"

            return health_status

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e), "timestamp": "2026-02-19T12:00:00Z"}


# Global server instance
_server_instance: Optional[SpecialistTrainingMCPServer] = None


def get_server_instance() -> SpecialistTrainingMCPServer:
    """Get or create the global server instance.

    Returns:
        Server instance
    """
    global _server_instance

    if _server_instance is None:
        _server_instance = SpecialistTrainingMCPServer()

    return _server_instance


def register_tools_with_mcp_server(mcp_server) -> None:
    """Register all training tools with an MCP server.

    Args:
        mcp_server: The MCP server instance to register tools with
    """
    try:
        training_server = get_server_instance()
        tool_definitions = training_server.get_tool_definitions()

        for tool_def in tool_definitions:
            # Register tool with MCP server
            # This would depend on the specific MCP server implementation
            # For now, we'll just log the registration
            logger.info(f"Registering tool: {tool_def['name']}")

        logger.info(f"Registered {len(tool_definitions)} training tools with MCP server")

    except Exception as e:
        logger.error(f"Failed to register tools with MCP server: {e}")


# Export main components
__all__ = ["SpecialistTrainingMCPServer", "get_server_instance", "register_tools_with_mcp_server"]
