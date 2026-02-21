"""AI-powered tool selection using Ollama."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

<<<<<<< Updated upstream
from tool_router.ai.prompts import PromptTemplates

=======
>>>>>>> Stashed changes

logger = logging.getLogger(__name__)


class OllamaSelector:
    """AI-powered tool selector using Ollama LLM."""

<<<<<<< Updated upstream
    def __init__(
        self,
        endpoint: str,
        model: str,
        timeout: int = 2000,
        min_confidence: float = 0.3,
    ) -> None:
        """Initialize the Ollama selector.

        Args:
            endpoint: Ollama API endpoint (e.g., http://localhost:11434)
            model: Model name (e.g., llama3.2:3b)
            timeout: Timeout in milliseconds
            min_confidence: Minimum confidence to accept an AI result
        """
=======
    def __init__(self, endpoint: str, model: str, timeout: int = 2000) -> None:
>>>>>>> Stashed changes
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout_ms = timeout
        self.timeout_s = timeout / 1000.0
        self.min_confidence = min_confidence

<<<<<<< Updated upstream
    def select_tool(
        self,
        task: str,
        tools: list[dict[str, Any]],
        context: str = "",
        similar_tools: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Select the best tool for a given task using AI.

        Args:
            task: The task description
            tools: List of available tools with name and description
            context: Optional context to narrow selection
            similar_tools: Tool names that succeeded on similar past tasks

        Returns:
            Dictionary with tool_name, confidence, and reasoning, or None if
            failed or confidence below threshold
        """
        if not tools:
=======
    def select_tool(self, task: str, tools: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Select the best tool for a given task using AI."""
        try:
            tool_list = "
".join(
                f"- {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}"
                for tool in tools
            )
            prompt = self._create_prompt(task, tool_list)
            response = self._call_ollama(prompt)
            if not response:
                return None
        except Exception as e:  # noqa: BLE001
            logger.warning("AI selector failed: %s", e)
>>>>>>> Stashed changes
            return None
        else:
            return self._parse_response(response)

        tool_list = "\n".join(
            f"- {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}" for tool in tools
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
        """Select multiple tools for multi-step orchestration.

        Args:
            task: The task description
            tools: List of available tools with name and description
            context: Optional context to narrow selection
            max_tools: Maximum number of tools to select

        Returns:
            Dictionary with tools (list), confidence, and reasoning, or None
        """
        if not tools:
            return None

        tool_list = "\n".join(
            f"- {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}" for tool in tools
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_prompt(self, task: str, tool_list: str) -> str:
<<<<<<< Updated upstream
        """Create the prompt for Ollama (kept for backward compatibility)."""
        return PromptTemplates.create_tool_selection_prompt(task=task, tool_list=tool_list)
=======
        """Create the prompt for Ollama."""
        header = "You are a tool selection assistant. Select the best tool for the task."
        body = f"Task: {task}

Available tools:
{tool_list}"
        footer = 'Respond with JSON: {"tool_name": "<name>", "confidence": 0.9, "reasoning": "<why>"}'
        return f"{header}

{body}

{footer}"
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 200,
                        },
=======
                        "options": {"temperature": 0.1, "max_tokens": 150},
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream

            result = json.loads(response[start_idx:end_idx])

            if not all(key in result for key in ["tool_name", "confidence", "reasoning"]):
                logger.warning("Missing required fields in AI response")
                return None

=======
            result = json.loads(response[start_idx:end_idx])
            if not all(key in result for key in ["tool_name", "confidence", "reasoning"]):
                logger.warning("Missing required fields in AI response")
                return None
>>>>>>> Stashed changes
            confidence = result["confidence"]
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                logger.warning("Invalid confidence value: %s", confidence)
                return None
<<<<<<< Updated upstream

        except json.JSONDecodeError as e:
            logger.warning("Failed to parse AI response as JSON: %s", e)
            return None
        except Exception as e:  # noqa: BLE001
            logger.warning("Error parsing AI response: %s", e)
            return None
        else:
            return result

    def _parse_multi_response(self, response: str, available_tools: list[dict[str, Any]]) -> dict[str, Any] | None:
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
=======
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse AI response as JSON: %s", e)
            return None
        except Exception as e:  # noqa: BLE001
            logger.warning("Error parsing AI response: %s", e)
>>>>>>> Stashed changes
            return None
        else:
            return result
