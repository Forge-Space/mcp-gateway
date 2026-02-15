"""Health check API endpoints for AI router."""

from __future__ import annotations

from typing import Any

from tool_router.ai.selector import AIToolSelector
from tool_router.core.config import ToolRouterConfig
from tool_router.observability.health import HealthStatus


def get_ai_router_health(
    config: ToolRouterConfig | None = None, ai_selector: AIToolSelector | None = None
) -> dict[str, Any]:
    """Get AI router health status.

    Args:
        config: Tool router configuration (optional, loads from env if not provided)
        ai_selector: AI selector instance (optional, checks availability if provided)

    Returns:
        Dictionary containing health status:
        - status: "healthy", "degraded", or "unhealthy"
        - ai_enabled: Whether AI router is enabled
        - ollama_available: Whether Ollama service is reachable
        - configuration: Current AI router settings
        - issues: List of any detected issues
    """
    if config is None:
        config = ToolRouterConfig.load_from_environment()

    health_status = {
        "status": HealthStatus.HEALTHY.value,
        "ai_enabled": config.ai.enabled,
        "configuration": {
            "provider": config.ai.provider,
            "model": config.ai.model,
            "endpoint": config.ai.endpoint,
            "timeout_ms": config.ai.timeout_ms,
            "weight": config.ai.weight,
            "min_confidence": config.ai.min_confidence,
        },
        "issues": [],
    }

    # Check Ollama availability if AI is enabled
    if config.ai.enabled:
        if ai_selector is None:
            # Create temporary selector for health check
            ai_selector = AIToolSelector(
                endpoint=config.ai.endpoint,
                model=config.ai.model,
                timeout_ms=config.ai.timeout_ms,
            )

        ollama_available = ai_selector.is_available()
        health_status["ollama_available"] = ollama_available

        if not ollama_available:
            health_status["status"] = HealthStatus.DEGRADED.value
            health_status["issues"].append(
                f"Ollama service not available at {config.ai.endpoint}. Falling back to keyword matching."
            )
    else:
        health_status["ollama_available"] = None
        health_status["issues"].append("AI router is disabled. Using keyword matching only.")

    return health_status
