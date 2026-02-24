"""Enhanced AI selector supporting multiple models and providers with hardware-aware routing."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

import httpx

from tool_router.ai.prompts import PromptTemplates

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Supported AI providers."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AIModel(Enum):
    """Supported AI models with hardware requirements."""

    # Ollama models (optimized for N100)
    LLAMA32_3B = "llama3.2:3b"  # Primary: 4GB RAM, 5-15 tok/s
    LLAMA32_1B = "llama3.2:1b"  # Fast: 1.5GB RAM, 15-25 tok/s
    QWEN_2_5_3B = "qwen2.5:3b"  # Good: 4GB RAM, 5-14 tok/s
    GEMMA2_2B = "gemma2:2b"  # Ultra-fast: 2GB RAM, 8-18 tok/s
    PHI_3_MINI = "phi-3-mini"  # Alternative: 4GB RAM, 4-12 tok/s
    TINYLLAMA = "tinyllama"  # Ultra-fast: 1.5GB RAM, 15-25 tok/s

    # OpenAI models (BYOK for enterprise)
    GPT4O_MINI = "gpt-4o-mini"
    GPT4O = "gpt-4o"
    GPT35_TURBO = "gpt-3.5-turbo"

    # Anthropic models (BYOK for enterprise)
    CLAUDE_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_SONNET = "claude-3-5-sonnet-20241022"

    # Google models (BYOK for enterprise)
    GEMINI_FLASH = "gemini-1.5-flash"
    GEMINI_PRO = "gemini-1.5-pro"

    # XAI models (BYOK for enterprise)
    GROK_MINI = "grok-beta"

    @classmethod
    def get_hardware_requirements(cls, model: str) -> dict[str, Any]:
        """Get hardware requirements for a model."""
        requirements = {
            cls.LLAMA32_3B.value: {
                "ram_gb": 4,
                "tokens_per_sec": 10,
                "hardware_tier": "n100_optimal",
            },
            cls.LLAMA32_1B.value: {
                "ram_gb": 2,
                "tokens_per_sec": 20,
                "hardware_tier": "n100_fast",
            },
            cls.QWEN_2_5_3B.value: {
                "ram_gb": 4,
                "tokens_per_sec": 10,
                "hardware_tier": "n100_good",
            },
            cls.GEMMA2_2B.value: {
                "ram_gb": 2,
                "tokens_per_sec": 13,
                "hardware_tier": "n100_ultra_fast",
            },
            cls.PHI_3_MINI.value: {
                "ram_gb": 4,
                "tokens_per_sec": 8,
                "hardware_tier": "n100_alternative",
            },
            cls.TINYLLAMA.value: {
                "ram_gb": 1.5,
                "tokens_per_sec": 20,
                "hardware_tier": "n100_ultra_fast",
            },
        }
        return requirements.get(
            model, {"ram_gb": 8, "tokens_per_sec": 5, "hardware_tier": "unknown"}
        )

    @classmethod
    def get_cost_per_million_tokens(cls, model: str) -> dict[str, float]:
        """Get cost per million tokens for different providers."""
        # Estimated costs for 2025
        costs = {
            # OpenAI costs
            cls.GPT4O_MINI.value: {"input": 0.15, "output": 0.60},
            cls.GPT4O.value: {"input": 2.50, "output": 10.0},
            cls.GPT35_TURBO.value: {"input": 0.30, "output": 1.20},
            # Anthropic costs
            cls.CLAUDE_HAIKU.value: {"input": 0.25, "output": 1.25},
            cls.CLAUDE_SONNET.value: {"input": 3.00, "output": 15.00},
            # Google costs
            cls.GEMINI_FLASH.value: {"input": 0.075, "output": 0.30},
            cls.GEMINI_PRO.value: {"input": 1.25, "output": 5.00},
            # XAI costs
            cls.GROK_MINI.value: {"input": 0.50, "output": 2.00},
        }
        return costs.get(model, {"input": 0.0, "output": 0.0})  # Free for local models

    @classmethod
    def is_local_model(cls, model: str) -> bool:
        """Check if model is locally hosted (free)."""
        local_models = [
            cls.LLAMA32_3B.value,
            cls.LLAMA32_1B.value,
            cls.QWEN_2_5_3B.value,
            cls.GEMMA2_2B.value,
            cls.PHI_3_MINI.value,
            cls.TINYLLAMA.value,
        ]
        return model in local_models

    @classmethod
    def get_model_tier(cls, model: str) -> str:
        """Get model tier for routing decisions."""
        if model in [cls.TINYLLAMA.value, cls.GEMMA2_2B.value]:
            return "ultra_fast"
        if model in [cls.LLAMA32_1B.value, cls.PHI_3_MINI.value]:
            return "fast"
        if model in [cls.LLAMA32_3B.value, cls.QWEN_2_5_3B.value]:
            return "balanced"
        if model in [
            cls.GPT4O_MINI.value,
            cls.CLAUDE_HAIKU.value,
            cls.GEMINI_FLASH.value,
        ]:
            return "premium"
        if model in [
            cls.GPT4O.value,
            cls.GPT35_TURBO.value,
            cls.CLAUDE_SONNET.value,
            cls.GEMINI_PRO.value,
            cls.GROK_MINI.value,
        ]:
            return "enterprise"
        return "unknown"


class BaseAISelector(ABC):
    """Base class for AI selectors."""

    def __init__(
        self,
        model: str,
        timeout: int = 2000,
        min_confidence: float = 0.3,
    ) -> None:
        """Initialize the AI selector.

        Args:
            model: Model name
            timeout: Timeout in milliseconds
            min_confidence: Minimum confidence to accept an AI result
        """
        self.model = model
        self.timeout_ms = timeout
        self.timeout_s = timeout / 1000.0
        self.min_confidence = min_confidence

    @abstractmethod
    def select_tool(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        similar_tools: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Select the best tool for a given task using AI."""

    @abstractmethod
    def select_tools_multi(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        max_tools: int = 3,
    ) -> dict[str, Any] | None:
        """Select multiple tools for multi-step orchestration."""


class OllamaSelector(BaseAISelector):
    """Ollama-based AI selector (existing implementation)."""

    def __init__(
        self,
        endpoint: str,
        model: str = AIModel.LLAMA32_3B.value,
        timeout: int = 2000,
        min_confidence: float = 0.3,
    ) -> None:
        """Initialize the Ollama selector."""
        super().__init__(model, timeout, min_confidence)
        self.endpoint = endpoint.rstrip("/")

    def select_tool(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        similar_tools: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Select the best tool for a given task using Ollama."""
        if not tools:
            return None

        tool_list = "\n".join(
            f"- {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}"
            for tool in tools
        )
        prompt = PromptTemplates.create_tool_selection_prompt(
            task=task,
            tool_list=tool_list,
            context=context,
            similar_tools=similar_tools,
        )

        response = self._call_ollama(prompt)
        if not response:
            return None

        result = self._parse_response(response)
        if result is None:
            return None

        if result["confidence"] < self.min_confidence:
            logger.info(
                "AI result discarded: confidence %.2f below threshold %.2f",
                result["confidence"],
                self.min_confidence,
            )
            return None

        return result

    def select_tools_multi(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        max_tools: int = 3,
    ) -> dict[str, Any] | None:
        """Select multiple tools for multi-step orchestration."""
        if not tools:
            return None

        tool_list = "\n".join(
            f"- {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}"
            for tool in tools
        )
        prompt = PromptTemplates.create_multi_tool_selection_prompt(
            task=task,
            tool_list=tool_list,
            context=context,
            max_tools=max_tools,
        )

        response = self._call_ollama(prompt)
        if not response:
            return None

        result = self._parse_multi_response(response, tools)
        if result is None:
            return None

        if result["confidence"] < self.min_confidence:
            logger.info(
                "Multi-tool AI result discarded: confidence %.2f below threshold %.2f",
                result["confidence"],
                self.min_confidence,
            )
            return None

        return result

    def _call_ollama(self, prompt: str) -> str | None:
        """Call the Ollama API."""
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.post(
                    f"{self.endpoint}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 200,
                        },
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        except httpx.TimeoutException:
            logger.warning("Ollama request timed out after %dms", self.timeout_ms)
            return None
        except httpx.HTTPStatusError as e:
            logger.warning("Ollama HTTP error: %s", e)
            return None
        except Exception as e:
            logger.warning("Ollama request failed: %s", e)
            return None

    def _parse_response(self, response: str) -> dict[str, Any] | None:
        """Parse the single-tool JSON response from Ollama."""
        try:
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx == -1 or end_idx == 0:
                logger.warning("No JSON found in Ollama response")
                return None

            result = json.loads(response[start_idx:end_idx])

            if not all(
                key in result for key in ["tool_name", "confidence", "reasoning"]
            ):
                logger.warning("Missing required fields in AI response")
                return None

            confidence = result["confidence"]
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                logger.warning("Invalid confidence value: %s", confidence)
                return None

        except json.JSONDecodeError as e:
            logger.warning("Failed to parse AI response as JSON: %s", e)
            return None
        except Exception as e:
            logger.warning("Error parsing AI response: %s", e)
            return None
        else:
            return result

    def _parse_multi_response(
        self, response: str, available_tools: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Parse the multi-tool JSON response from Ollama."""
        try:
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx == -1 or end_idx == 0:
                logger.warning("No JSON found in Ollama multi-tool response")
                return None

            result = json.loads(response[start_idx:end_idx])

            if not all(key in result for key in ["tools", "confidence", "reasoning"]):
                logger.warning("Missing required fields in AI multi-tool response")
                return None

            if not isinstance(result["tools"], list) or not result["tools"]:
                logger.warning("AI multi-tool response has empty or invalid tools list")
                return None

            confidence = result["confidence"]
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                logger.warning(
                    "Invalid confidence value in multi-tool response: %s", confidence
                )
                return None

            valid_names = {t.get("name", "") for t in available_tools}
            valid_tools = [t for t in result["tools"] if t in valid_names]
            if not valid_tools:
                logger.warning("No valid tool names in AI multi-tool response")
                return None

            result["tools"] = valid_tools
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse AI multi-tool response as JSON: %s", e)
            return None
        except Exception as e:
            logger.warning("Error parsing AI multi-tool response: %s", e)
            return None
        else:
            return result


class CostTracker:
    """Track cost and performance metrics."""

    def __init__(self) -> None:
        self.total_requests = 0
        self.total_cost_saved = 0.0
        self.average_response_time = 0.0
        self.model_usage_stats = {}
        self._response_times = []

    def track_selection(
        self,
        model: str,
        task_complexity: str,
        estimated_tokens: dict[str, int],
    ) -> None:
        """Track model selection for analytics."""
        self.total_requests += 1

        # Update model usage stats
        if model not in self.model_usage_stats:
            self.model_usage_stats[model] = {
                "usage_count": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
            }

        self.model_usage_stats[model]["usage_count"] += 1
        self.model_usage_stats[model]["total_tokens"] += estimated_tokens["total"]

        # Calculate cost savings from using local vs premium models
        if AIModel.is_local_model(model):
            # Calculate what it would have cost with premium model
            premium_model = AIModel.GPT4O_MINI.value  # Mid-tier paid model
            premium_costs = AIModel.get_cost_per_million_tokens(premium_model)
            estimated_premium_cost = (
                estimated_tokens["input"] / 1_000_000
            ) * premium_costs["input"] + (
                estimated_tokens["output"] / 1_000_000
            ) * premium_costs[
                "output"
            ]
            self.total_cost_saved += estimated_premium_cost
            self.model_usage_stats[model]["total_cost"] = 0.0  # Local models are free
        else:
            costs = AIModel.get_cost_per_million_tokens(model)
            actual_cost = (estimated_tokens["input"] / 1_000_000) * costs["input"] + (
                estimated_tokens["output"] / 1_000_000
            ) * costs["output"]
            self.model_usage_stats[model]["total_cost"] += actual_cost

    def record_response_time(self, response_time_ms: float) -> None:
        """Record response time for performance tracking."""
        self._response_times.append(response_time_ms)
        if self._response_times:
            self.average_response_time = sum(self._response_times) / len(
                self._response_times
            )


class EnhancedAISelector:
    """Enhanced AI selector with hardware-aware routing and cost optimization."""

    def __init__(
        self,
        providers: list[BaseAISelector],
        primary_weight: float = 0.7,
        fallback_weight: float = 0.3,
        timeout: int = 5000,
        min_confidence: float = 0.3,
        hardware_constraints: dict | None = None,
        cost_optimization: bool = True,
    ) -> None:
        """Initialize the enhanced AI selector with hardware and cost awareness.

        Args:
            providers: List of AI selectors in priority order
            primary_weight: Weight for primary provider results
            fallback_weight: Weight for fallback provider results
            timeout: Overall timeout in milliseconds
            min_confidence: Minimum confidence to accept results
            hardware_constraints: Hardware limitations (RAM, CPU, etc.)
            cost_optimization: Enable cost-aware routing
        """
        self.providers = providers
        self.primary_weight = primary_weight
        self.fallback_weight = fallback_weight
        self.timeout_ms = timeout
        self.min_confidence = min_confidence
        self.hardware_constraints = (
            hardware_constraints or self._get_default_hardware_constraints()
        )
        self.cost_optimization = cost_optimization
        self._performance_cache = {}
        self._cost_tracker = CostTracker()

    def _get_default_hardware_constraints(self) -> dict:
        """Get default hardware constraints for Celeron N100."""
        return {
            "ram_available_gb": 16,
            "cpu_cores": 4,
            "max_model_ram_gb": 8,  # Reserve 8GB for system
            "network_speed_mbps": 1000,
            "hardware_tier": "n100",
        }

    def select_optimal_model(
        self,
        task_complexity: str,
        user_cost_preference: str = "balanced",  # "efficient", "balanced", "quality"
        available_models: list[str] | None = None,
    ) -> str:
        """Select the optimal model based on hardware constraints and user preference."""
        if available_models is None:
            available_models = [model.value for model in AIModel]

        # Filter models by hardware constraints
        suitable_models = []
        for model in available_models:
            requirements = AIModel.get_hardware_requirements(model)
            if requirements["ram_gb"] <= self.hardware_constraints["max_model_ram_gb"]:
                suitable_models.append((model, requirements))

        if not suitable_models:
            # Fallback to smallest model
            return AIModel.TINYLLAMA.value

        # Sort by user preference
        if user_cost_preference == "efficient":
            # Prioritize speed and low resource usage
            suitable_models.sort(
                key=lambda x: (
                    AIModel.get_model_tier(x[0]) == "ultra_fast",
                    x[1]["tokens_per_sec"],
                    -x[1]["ram_gb"],
                )
            )
        elif user_cost_preference == "quality":
            # Prioritize capability (but still within hardware constraints)
            suitable_models.sort(
                key=lambda x: (
                    AIModel.get_model_tier(x[0]) in ["premium", "enterprise"],
                    x[1]["tokens_per_sec"],
                    x[1]["ram_gb"],
                )
            )
        else:  # "balanced"
            # Prioritize balanced performance
            suitable_models.sort(
                key=lambda x: (
                    AIModel.get_model_tier(x[0]) == "balanced",
                    x[1]["tokens_per_sec"],
                    -x[1]["ram_gb"],
                )
            )

        return suitable_models[0][0]

    def estimate_request_cost(
        self,
        model: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int,
    ) -> dict[str, float]:
        """Estimate cost for a request."""
        costs = AIModel.get_cost_per_million_tokens(model)

        input_cost = (estimated_input_tokens / 1_000_000) * costs["input"]
        output_cost = (estimated_output_tokens / 1_000_000) * costs["output"]

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
            "cost_per_million_tokens": costs["input"] + costs["output"],
        }

    def select_tool_with_cost_optimization(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        similar_tools: list[str] | None = None,
        user_cost_preference: str = "balanced",
        max_cost_per_request: float | None = None,
    ) -> dict[str, Any] | None:
        """Select tool with cost optimization and hardware awareness."""
        if not tools or not self.providers:
            return None

        # Analyze task complexity
        task_complexity = self._analyze_task_complexity(task)

        # Select optimal model for this task
        optimal_model = self.select_optimal_model(task_complexity, user_cost_preference)

        # Estimate token usage
        estimated_tokens = self._estimate_token_usage(task, tools, context)

        # Check cost constraints
        if max_cost_per_request:
            cost_estimate = self.estimate_request_cost(
                optimal_model, estimated_tokens["input"], estimated_tokens["output"]
            )
            if cost_estimate["total_cost"] > max_cost_per_request:
                # Fall back to cheaper model
                cheaper_model = self.select_optimal_model(task_complexity, "efficient")
                optimal_model = cheaper_model

        # Track cost for analytics
        self._cost_tracker.track_selection(
            optimal_model, task_complexity, estimated_tokens
        )

        # Use the optimal model for routing
        enhanced_providers = []
        for provider in self.providers:
            if hasattr(provider, "model") and provider.model == optimal_model:
                enhanced_providers.append(provider)
                break

        # If no provider matches the optimal model, create one
        if not enhanced_providers:
            # Find the provider that can use the optimal model
            for provider in self.providers:
                if isinstance(provider, OllamaSelector):
                    provider.model = optimal_model
                    enhanced_providers.append(provider)
                    break

        if not enhanced_providers:
            logger.warning("No provider available for optimal model %s", optimal_model)
            return None

        # Use the first (and only) enhanced provider
        provider = enhanced_providers[0]

        result = provider.select_tool(task, tools, context, similar_tools)
        if result:
            # Add cost and hardware info
            result["model_used"] = optimal_model
            result["model_tier"] = AIModel.get_model_tier(optimal_model)
            result["hardware_requirements"] = AIModel.get_hardware_requirements(
                optimal_model
            )
            result["estimated_cost"] = self.estimate_request_cost(
                optimal_model, estimated_tokens["input"], estimated_tokens["output"]
            )
            result["user_cost_preference"] = user_cost_preference
            result["task_complexity"] = task_complexity

        return result

    def select_tools_multi_with_cost_optimization(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        max_tools: int = 3,
        user_cost_preference: str = "balanced",
        max_cost_per_request: float | None = None,
    ) -> dict[str, Any] | None:
        """Select multiple tools with cost optimization."""
        if not tools or not self.providers:
            return None

        # Similar to single tool selection but for multi-tool
        task_complexity = self._analyze_task_complexity(task)
        optimal_model = self.select_optimal_model(task_complexity, user_cost_preference)

        estimated_tokens = self._estimate_token_usage(task, tools, context, max_tools)

        if max_cost_per_request:
            cost_estimate = self.estimate_request_cost(
                optimal_model, estimated_tokens["input"], estimated_tokens["output"]
            )
            if cost_estimate["total_cost"] > max_cost_per_request:
                cheaper_model = self.select_optimal_model(task_complexity, "efficient")
                optimal_model = cheaper_model

        # Use enhanced provider for optimal model
        enhanced_providers = []
        for provider in self.providers:
            if hasattr(provider, "model") and provider.model == optimal_model:
                enhanced_providers.append(provider)
                break

        if not enhanced_providers:
            for provider in self.providers:
                if isinstance(provider, OllamaSelector):
                    provider.model = optimal_model
                    enhanced_providers.append(provider)
                    break

        if not enhanced_providers:
            return None

        provider = enhanced_providers[0]
        result = provider.select_tools_multi(task, tools, context, max_tools)

        if result:
            result["model_used"] = optimal_model
            result["model_tier"] = AIModel.get_model_tier(optimal_model)
            result["hardware_requirements"] = AIModel.get_hardware_requirements(
                optimal_model
            )
            result["estimated_cost"] = self.estimate_request_cost(
                optimal_model, estimated_tokens["input"], estimated_tokens["output"]
            )
            result["user_cost_preference"] = user_cost_preference
            result["task_complexity"] = task_complexity

        return result

    def _analyze_task_complexity(self, task: str) -> str:
        """Analyze task complexity for model selection."""
        task_lower = task.lower().strip()

        # Simple heuristic based on task characteristics
        if len(task_lower) < 50 or any(
            keyword in task_lower
            for keyword in ["what is", "how to", "explain", "define"]
        ):
            return "simple"
        if any(
            keyword in task_lower
            for keyword in ["create", "generate", "build", "implement", "develop"]
        ):
            return "complex"
        if any(
            keyword in task_lower
            for keyword in ["analyze", "optimize", "refactor", "debug", "test"]
        ):
            return "moderate"
        return "unknown"

    def _estimate_token_usage(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        max_tools: int = 3,
    ) -> dict[str, int]:
        """Estimate token usage for a request."""
        # Rough estimation based on content length
        task_tokens = len(task.split()) * 1.3  # Average 1.3 tokens per word
        context_tokens = len(context.split()) * 1.3 if context else 0
        tool_list_tokens = len(tools) * 50  # Average 50 tokens per tool description

        # For multi-tool, account for orchestration overhead
        orchestration_overhead = max_tools * 20

        total_input = (
            task_tokens + context_tokens + tool_list_tokens + orchestration_overhead
        )

        # Estimate output tokens (typically 2-3x input for generation tasks)
        output_tokens = int(total_input * 2.5)

        return {
            "input": total_input,
            "output": output_tokens,
            "total": total_input + output_tokens,
        }

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance and cost metrics."""
        return {
            "cache_hit_rate": len(self._performance_cache)
            / max(1, len(self._performance_cache)),
            "total_requests": self._cost_tracker.total_requests,
            "total_cost_saved": self._cost_tracker.total_cost_saved,
            "average_response_time": self._cost_tracker.average_response_time,
            "model_usage_stats": self._cost_tracker.model_usage_stats,
            "cost_optimization_enabled": self.cost_optimization,
            "hardware_constraints": self.hardware_constraints,
        }

    def clear_cache(self) -> None:
        """Clear the performance cache."""
        self._performance_cache.clear()

    # Legacy methods for backward compatibility
    def select_tool(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        similar_tools: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Legacy method - delegates to cost-optimized version."""
        return self.select_tool_with_cost_optimization(
            task, tools, context, similar_tools
        )

    def select_tools_multi(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        max_tools: int = 3,
    ) -> dict[str, Any] | None:
        """Legacy method - delegates to cost-optimized version."""
        return self.select_tools_multi_with_cost_optimization(
            task, tools, context, max_tools
        )
