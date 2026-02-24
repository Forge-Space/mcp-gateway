"""Training Manager MCP Tool.

Provides MCP server tool functionality for managing the specialist AI training
pipeline, including starting training runs, monitoring progress, and managing
training configurations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..training.evaluation import SpecialistEvaluator
from ..training.knowledge_base import KnowledgeBase
from ..training.training_pipeline import DEFAULT_TRAINING_SOURCES, TrainingPipeline

logger = logging.getLogger(__name__)


class TrainingStatus(Enum):
    """Training pipeline status."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class TrainingRun:
    """Represents a training run."""

    run_id: str
    status: TrainingStatus
    started_at: str
    completed_at: str | None = None
    results: dict[str, Any] | None = None
    error: str | None = None


class TrainingManagerTool:
    """MCP tool for managing specialist AI training operations."""

    def __init__(self) -> None:
        """Initialize the training manager tool."""
        self.knowledge_base = KnowledgeBase()
        self.training_pipeline = TrainingPipeline()
        self.evaluator = SpecialistEvaluator(self.knowledge_base)
        self.active_runs: dict[str, TrainingRun] = {}
        self.run_counter = 0

    def start_training_run(
        self,
        sources: list[dict[str, Any]] | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Start a new training run.

        Args:
            sources: Optional list of data sources for training
            config: Optional training configuration

        Returns:
            Training run information including run ID and status
        """
        try:
            # Generate run ID
            self.run_counter += 1
            run_id = f"training_run_{self.run_counter}"

            # Use default sources if none provided
            training_sources = sources or DEFAULT_TRAINING_SOURCES

            # Create training run record
            import time

            run = TrainingRun(
                run_id=run_id,
                status=TrainingStatus.RUNNING,
                started_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            )

            self.active_runs[run_id] = run

            logger.info(f"Starting training run {run_id} with {len(training_sources)} sources")

            # Start training in background (simplified for demo)
            try:
                results = self.training_pipeline.run_training_pipeline(training_sources)

                # Update run with results
                run.status = TrainingStatus.COMPLETED
                run.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")
                run.results = results

                logger.info(f"Training run {run_id} completed successfully")

                return {
                    "run_id": run_id,
                    "status": run.status.value,
                    "started_at": run.started_at,
                    "completed_at": run.completed_at,
                    "results": results,
                    "message": "Training completed successfully",
                }

            except Exception as e:
                # Update run with error
                run.status = TrainingStatus.FAILED
                run.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")
                run.error = str(e)

                logger.error(f"Training run {run_id} failed: {e}")

                return {
                    "run_id": run_id,
                    "status": run.status.value,
                    "started_at": run.started_at,
                    "completed_at": run.completed_at,
                    "error": run.error,
                    "message": "Training failed",
                }

        except Exception as e:
            logger.error(f"Error starting training run: {e}")
            return {"error": str(e), "message": "Failed to start training run"}

    def get_training_status(self, run_id: str) -> dict[str, Any]:
        """Get the status of a training run.

        Args:
            run_id: ID of the training run

        Returns:
            Training run status information
        """
        try:
            if run_id not in self.active_runs:
                return {
                    "error": f"Training run {run_id} not found",
                    "message": "Invalid run ID",
                }

            run = self.active_runs[run_id]

            response = {
                "run_id": run.run_id,
                "status": run.status.value,
                "started_at": run.started_at,
                "message": f"Training run is {run.status.value}",
            }

            if run.completed_at:
                response["completed_at"] = run.completed_at

            if run.results:
                response["results"] = run.results

            if run.error:
                response["error"] = run.error

            return response

        except Exception as e:
            logger.error(f"Error getting training status: {e}")
            return {"error": str(e), "message": "Failed to get training status"}

    def list_training_runs(self) -> dict[str, Any]:
        """List all training runs.

        Returns:
            List of training runs with their status
        """
        try:
            runs = []
            for run_id, run in self.active_runs.items():
                run_info = {
                    "run_id": run_id,
                    "status": run.status.value,
                    "started_at": run.started_at,
                }

                if run.completed_at:
                    run_info["completed_at"] = run.completed_at

                if run.error:
                    run_info["error"] = run.error

                if run.results:
                    run_info["has_results"] = True

                runs.append(run_info)

            return {
                "runs": runs,
                "total_runs": len(runs),
                "active_runs": len([r for r in runs if r["status"] == "running"]),
                "message": f"Found {len(runs)} training runs",
            }

        except Exception as e:
            logger.error(f"Error listing training runs: {e}")
            return {"error": str(e), "message": "Failed to list training runs"}

    def get_training_statistics(self) -> dict[str, Any]:
        """Get training statistics and metrics.

        Returns:
            Training statistics including success rates and performance metrics
        """
        try:
            runs = list(self.active_runs.values())

            if not runs:
                return {
                    "total_runs": 0,
                    "success_rate": 0.0,
                    "average_duration": 0.0,
                    "message": "No training runs found",
                }

            # Calculate statistics
            completed_runs = [r for r in runs if r.status == TrainingStatus.COMPLETED]
            failed_runs = [r for r in runs if r.status == TrainingStatus.FAILED]

            success_rate = len(completed_runs) / len(runs) * 100 if runs else 0

            # Calculate average duration for completed runs
            durations = []
            for run in completed_runs:
                if run.completed_at and run.started_at:
                    start = time.mktime(time.strptime(run.started_at, "%Y-%m-%d %H:%M:%S"))
                    end = time.mktime(time.strptime(run.completed_at, "%Y-%m-%d %H:%M:%S"))
                    durations.append(end - start)

            avg_duration = sum(durations) / len(durations) if durations else 0

            # Get knowledge base statistics
            kb_stats = self.knowledge_base.get_statistics()

            return {
                "total_runs": len(runs),
                "completed_runs": len(completed_runs),
                "failed_runs": len(failed_runs),
                "success_rate": round(success_rate, 2),
                "average_duration_seconds": round(avg_duration, 2),
                "knowledge_base": kb_stats,
                "message": "Training statistics retrieved successfully",
            }

        except Exception as e:
            logger.error(f"Error getting training statistics: {e}")
            return {"error": str(e), "message": "Failed to get training statistics"}

    def cancel_training_run(self, run_id: str) -> dict[str, Any]:
        """Cancel a training run.

        Args:
            run_id: ID of the training run to cancel

        Returns:
            Cancellation result
        """
        try:
            if run_id not in self.active_runs:
                return {
                    "error": f"Training run {run_id} not found",
                    "message": "Invalid run ID",
                }

            run = self.active_runs[run_id]

            if run.status != TrainingStatus.RUNNING:
                return {
                    "run_id": run_id,
                    "status": run.status.value,
                    "message": f"Cannot cancel run in {run.status.value} status",
                }

            # Mark as failed (cancellation)
            run.status = TrainingStatus.FAILED
            run.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")
            run.error = "Cancelled by user"

            logger.info(f"Training run {run_id} cancelled")

            return {
                "run_id": run_id,
                "status": run.status.value,
                "completed_at": run.completed_at,
                "message": "Training run cancelled successfully",
            }

        except Exception as e:
            logger.error(f"Error cancelling training run: {e}")
            return {"error": str(e), "message": "Failed to cancel training run"}

    def get_training_configuration(self) -> dict[str, Any]:
        """Get current training configuration.

        Returns:
            Training configuration including default sources and settings
        """
        try:
            return {
                "default_sources": DEFAULT_TRAINING_SOURCES,
                "knowledge_base_path": str(self.knowledge_base.db_path),
                "supported_categories": [
                    "react_pattern",
                    "ui_component",
                    "accessibility",
                    "prompt_engineering",
                    "architecture",
                    "code_pattern",
                    "best_practice",
                ],
                "message": "Training configuration retrieved successfully",
            }

        except Exception as e:
            logger.error(f"Error getting training configuration: {e}")
            return {"error": str(e), "message": "Failed to get training configuration"}


# Tool schema for MCP integration
TRAINING_MANAGER_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "start_training",
                "get_status",
                "list_runs",
                "get_statistics",
                "cancel_run",
                "get_configuration",
            ],
            "description": "The training management action to perform",
        },
        "run_id": {
            "type": "string",
            "description": "ID of the training run (for status, cancel operations)",
        },
        "sources": {
            "type": "array",
            "items": {"type": "object"},
            "description": "List of data sources for training (for start_training)",
        },
        "config": {"type": "object", "description": "Training configuration options"},
    },
    "required": ["action"],
}


def training_manager_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handler for training manager MCP tool.

    Args:
        args: Tool arguments including action and parameters

    Returns:
        Tool execution result
    """
    try:
        manager = TrainingManagerTool()
        action = args.get("action")

        if action == "start_training":
            return manager.start_training_run(sources=args.get("sources"), config=args.get("config"))

        if action == "get_status":
            run_id = args.get("run_id")
            if not run_id:
                return {
                    "error": "run_id is required for get_status action",
                    "message": "Missing required parameter",
                }
            return manager.get_training_status(run_id)

        if action == "list_runs":
            return manager.list_training_runs()

        if action == "get_statistics":
            return manager.get_training_statistics()

        if action == "cancel_run":
            run_id = args.get("run_id")
            if not run_id:
                return {
                    "error": "run_id is required for cancel_run action",
                    "message": "Missing required parameter",
                }
            return manager.cancel_training_run(run_id)

        if action == "get_configuration":
            return manager.get_training_configuration()

        return {
            "error": f"Unknown action: {action}",
            "message": "Invalid action specified",
        }

    except Exception as e:
        logger.error(f"Error in training manager handler: {e}")
        return {"error": str(e), "message": "Training manager operation failed"}
