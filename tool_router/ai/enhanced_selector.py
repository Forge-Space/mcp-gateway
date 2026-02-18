"""Enhanced AI selector supporting multiple models and providers."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any
from enum import Enum

import httpx

from tool_router.ai.prompts import PromptTemplates

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Supported AI providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AIModel(Enum):
    """Supported AI models."""
    # Ollama models
    LLAMA32_3B = "llama3.2:3b"
    LLAMA32_1B = "llama3.2:1b"
    QWEN_2_5_7B = "qwen2.5:7b"
    
    # OpenAI models
    GPT4O_MINI = "gpt-4o-mini"
    GPT4O = "gpt-4o"
    GPT35_TURBO = "gpt-3.5-turbo"
    
    # Anthropic models
    CLAUDE_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_SONNET = "claude-3-5-sonnet-20241022"


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
        pass
    
    @abstractmethod
    def select_tools_multi(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        max_tools: int = 3,
    ) -> dict[str, Any] | None:
        """Select multiple tools for multi-step orchestration."""
        pass


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
        except Exception as e:  # noqa: BLE001
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

            if not all(key in result for key in ["tool_name", "confidence", "reasoning"]):
                logger.warning("Missing required fields in AI response")
                return None

            confidence = result["confidence"]
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                logger.warning("Invalid confidence value: %s", confidence)
                return None

        except json.JSONDecodeError as e:
            logger.warning("Failed to parse AI response as JSON: %s", e)
            return None
        except Exception as e:  # noqa: BLE001
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
                logger.warning("Invalid confidence value in multi-tool response: %s", confidence)
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
        except Exception as e:  # noqa: BLE001
            logger.warning("Error parsing AI multi-tool response: %s", e)
            return None
        else:
            return result


class OpenAISelector(BaseAISelector):
    """OpenAI GPT-based AI selector."""
    
    def __init__(
        self,
        api_key: str,
        model: str = AIModel.GPT4O_MINI.value,
        timeout: int = 5000,
        min_confidence: float = 0.3,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        """Initialize the OpenAI selector."""
        super().__init__(model, timeout, min_confidence)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
    
    def select_tool(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        similar_tools: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Select the best tool for a given task using OpenAI."""
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

        response = self._call_openai(prompt)
        if not response:
            return None

        result = self._parse_response(response)
        if result is None:
            return None

        if result["confidence"] < self.min_confidence:
            logger.info(
                "OpenAI result discarded: confidence %.2f below threshold %.2f",
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

        response = self._call_openai(prompt)
        if not response:
            return None

        result = self._parse_multi_response(response, tools)
        if result is None:
            return None

        if result["confidence"] < self.min_confidence:
            logger.info(
                "OpenAI multi-tool result discarded: confidence %.2f below threshold %.2f",
                result["confidence"],
                self.min_confidence,
            )
            return None

        return result
    
    def _call_openai(self, prompt: str) -> str | None:
        """Call the OpenAI API."""
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a precise tool selection assistant. Always respond with valid JSON only."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.1,
                        "max_tokens": 200,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except httpx.TimeoutException:
            logger.warning("OpenAI request timed out after %dms", self.timeout_ms)
            return None
        except httpx.HTTPStatusError as e:
            logger.warning("OpenAI HTTP error: %s", e)
            return None
        except Exception as e:  # noqa: BLE001
            logger.warning("OpenAI request failed: %s", e)
            return None
    
    def _parse_response(self, response: str) -> dict[str, Any] | None:
        """Parse the JSON response from OpenAI."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response:
                start_idx = response.find("```json") + 7
                end_idx = response.find("```", start_idx)
            else:
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning("No JSON found in OpenAI response")
                return None

            json_str = response[start_idx:end_idx]
            result = json.loads(json_str)

            if not all(key in result for key in ["tool_name", "confidence", "reasoning"]):
                logger.warning("Missing required fields in AI response")
                return None

            confidence = result["confidence"]
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                logger.warning("Invalid confidence value: %s", confidence)
                return None

        except json.JSONDecodeError as e:
            logger.warning("Failed to parse OpenAI response as JSON: %s", e)
            return None
        except Exception as e:  # noqa: BLE001
            logger.warning("Error parsing OpenAI response: %s", e)
            return None
        else:
            return result
    
    def _parse_multi_response(
        self, response: str, available_tools: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Parse the multi-tool JSON response from OpenAI."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response:
                start_idx = response.find("```json") + 7
                end_idx = response.find("```", start_idx)
            else:
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning("No JSON found in OpenAI multi-tool response")
                return None

            json_str = response[start_idx:end_idx]
            result = json.loads(json_str)

            if not all(key in result for key in ["tools", "confidence", "reasoning"]):
                logger.warning("Missing required fields in AI multi-tool response")
                return None

            if not isinstance(result["tools"], list) or not result["tools"]:
                logger.warning("AI multi-tool response has empty or invalid tools list")
                return None

            confidence = result["confidence"]
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                logger.warning("Invalid confidence value in multi-tool response: %s", confidence)
                return None

            valid_names = {t.get("name", "") for t in available_tools}
            valid_tools = [t for t in result["tools"] if t in valid_names]
            if not valid_tools:
                logger.warning("No valid tool names in AI multi-tool response")
                return None

            result["tools"] = valid_tools
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse OpenAI multi-tool response as JSON: %s", e)
            return None
        except Exception as e:  # noqa: BLE001
            logger.warning("Error parsing OpenAI multi-tool response: %s", e)
            return None
        else:
            return result


class AnthropicSelector(BaseAISelector):
    """Anthropic Claude-based AI selector."""
    
    def __init__(
        self,
        api_key: str,
        model: str = AIModel.CLAUDE_HAIKU.value,
        timeout: int = 5000,
        min_confidence: float = 0.3,
        base_url: str = "https://api.anthropic.com",
    ) -> None:
        """Initialize the Anthropic selector."""
        super().__init__(model, timeout, min_confidence)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
    
    def select_tool(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        similar_tools: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Select the best tool for a given task using Anthropic Claude."""
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

        response = self._call_anthropic(prompt)
        if not response:
            return None

        result = self._parse_response(response)
        if result is None:
            return None

        if result["confidence"] < self.min_confidence:
            logger.info(
                "Anthropic result discarded: confidence %.2f below threshold %.2f",
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

        response = self._call_anthropic(prompt)
        if not response:
            return None

        result = self._parse_multi_response(response, tools)
        if result is None:
            return None

        if result["confidence"] < self.min_confidence:
            logger.info(
                "Anthropic multi-tool result discarded: confidence %.2f below threshold %.2f",
                result["confidence"],
                self.min_confidence,
            )
            return None

        return result
    
    def _call_anthropic(self, prompt: str) -> str | None:
        """Call the Anthropic API."""
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.post(
                    f"{self.base_url}/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 200,
                        "temperature": 0.1,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["content"][0]["text"].strip()
        except httpx.TimeoutException:
            logger.warning("Anthropic request timed out after %dms", self.timeout_ms)
            return None
        except httpx.HTTPStatusError as e:
            logger.warning("Anthropic HTTP error: %s", e)
            return None
        except Exception as e:  # noqa: BLE001
            logger.warning("Anthropic request failed: %s", e)
            return None
    
    def _parse_response(self, response: str) -> dict[str, Any] | None:
        """Parse the JSON response from Anthropic."""
        # Similar to OpenAI parsing
        return OpenAISelector._parse_response(self, response)
    
    def _parse_multi_response(
        self, response: str, available_tools: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Parse the multi-tool JSON response from Anthropic."""
        # Similar to OpenAI parsing
        return OpenAISelector._parse_multi_response(self, response, available_tools)


class EnhancedAISelector:
    """Enhanced AI selector with multi-provider support and fallbacks."""
    
    def __init__(
        self,
        providers: list[BaseAISelector],
        primary_weight: float = 0.7,
        fallback_weight: float = 0.3,
        timeout: int = 5000,
        min_confidence: float = 0.3,
    ) -> None:
        """Initialize the enhanced AI selector.
        
        Args:
            providers: List of AI selectors in priority order
            primary_weight: Weight for primary provider results
            fallback_weight: Weight for fallback provider results
            timeout: Overall timeout in milliseconds
            min_confidence: Minimum confidence to accept results
        """
        self.providers = providers
        self.primary_weight = primary_weight
        self.fallback_weight = fallback_weight
        self.timeout_ms = timeout
        self.min_confidence = min_confidence
    
    def select_tool(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        similar_tools: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Select the best tool using multiple providers with fallbacks."""
        if not tools or not self.providers:
            return None
        
        results = []
        
        # Try each provider in order
        for i, provider in enumerate(self.providers):
            try:
                result = provider.select_tool(task, tools, context, similar_tools)
                if result:
                    weight = self.primary_weight if i == 0 else self.fallback_weight
                    results.append((result, weight, provider.__class__.__name__))
                    logger.info(
                        "Provider %s selected tool: %s with confidence: %.2f",
                        provider.__class__.__name__,
                        result.get("tool_name"),
                        result.get("confidence", 0.0),
                    )
                    break  # Use first successful result
            except Exception as e:  # noqa: BLE001
                logger.warning("Provider %s failed: %s", provider.__class__.__name__, e)
                continue
        
        if not results:
            logger.warning("All AI providers failed for tool selection")
            return None
        
        result, weight, provider_name = results[0]
        
        # Adjust confidence based on provider reliability
        adjusted_confidence = result["confidence"] * weight
        
        if adjusted_confidence < self.min_confidence:
            logger.info(
                "Result from %s discarded: adjusted confidence %.2f below threshold %.2f",
                provider_name,
                adjusted_confidence,
                self.min_confidence,
            )
            return None
        
        # Add provider info to result
        result["provider"] = provider_name
        result["adjusted_confidence"] = adjusted_confidence
        
        return result
    
    def select_tools_multi(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        max_tools: int = 3,
    ) -> dict[str, Any] | None:
        """Select multiple tools using multiple providers with fallbacks."""
        if not tools or not self.providers:
            return None
        
        results = []
        
        # Try each provider in order
        for i, provider in enumerate(self.providers):
            try:
                result = provider.select_tools_multi(task, tools, context, max_tools)
                if result:
                    weight = self.primary_weight if i == 0 else self.fallback_weight
                    results.append((result, weight, provider.__class__.__name__))
                    logger.info(
                        "Provider %s selected %d tools with confidence: %.2f",
                        provider.__class__.__name__,
                        len(result.get("tools", [])),
                        result.get("confidence", 0.0),
                    )
                    break  # Use first successful result
            except Exception as e:  # noqa: BLE001
                logger.warning("Provider %s failed for multi-tool selection: %s", provider.__class__.__name__, e)
                continue
        
        if not results:
            logger.warning("All AI providers failed for multi-tool selection")
            return None
        
        result, weight, provider_name = results[0]
        
        # Adjust confidence based on provider reliability
        adjusted_confidence = result["confidence"] * weight
        
        if adjusted_confidence < self.min_confidence:
            logger.info(
                "Multi-tool result from %s discarded: adjusted confidence %.2f below threshold %.2f",
                provider_name,
                adjusted_confidence,
                self.min_confidence,
            )
            return None
        
        # Add provider info to result
        result["provider"] = provider_name
        result["adjusted_confidence"] = adjusted_confidence
        
        return result
