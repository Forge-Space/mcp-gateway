"""AI-powered tool selector using Ollama local LLM."""

from __future__ import annotations

import json
import logging
from typing import Any

import requests

from tool_router.ai.prompts import build_selection_prompt


logger = logging.getLogger(__name__)


class AIToolSelector:
    """Selects best tool using Ollama LLM with structured prompting.

    This selector queries a local Ollama instance to intelligently match
    user tasks to available tools using natural language understanding.
    """

    def __init__(
        self,
        endpoint: str = "http://ollama:11434",
        model: str = "llama3.2:3b",
        timeout_ms: int = 2000,
    ):
        """Initialize AI tool selector.

        Args:
            endpoint: Ollama API endpoint URL
            model: Model name to use (e.g., llama3.2:3b, mistral:7b)
            timeout_ms: Request timeout in milliseconds
        """
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_ms / 1000.0
        self.api_url = f"{self.endpoint}/api/generate"

    def select_tool(self, task: str, tools: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Select best matching tool using AI.

        Args:
            task: User's task description
            tools: List of available tools with 'name' and 'description'

        Returns:
            Dictionary with selected tool info:
            {
                "tool_name": str,
                "confidence": float (0.0-1.0),
                "reasoning": str
            }
            Returns None if selection fails or times out.
        """
        if not tools:
            logger.warning("No tools provided for AI selection")
            return None

        if len(tools) > 100:
            logger.warning(f"Too many tools ({len(tools)}) for AI selection, limiting to first 100")
            tools = tools[:100]

        try:
            prompt = build_selection_prompt(task, tools)
            response = self._call_ollama(prompt)

            if response is None:
                return None

            return self._parse_response(response, tools)

        except requests.Timeout:
            logger.warning(f"AI selection timeout ({self.timeout_seconds}s) for task: {task[:50]}")
            return None
        except requests.RequestException as e:
            logger.warning(f"AI selection request failed: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error in AI selection: {e}")
            return None

    def _call_ollama(self, prompt: str) -> str | None:
        """Call Ollama API with the prompt.

        Args:
            prompt: Complete prompt for the model

        Returns:
            Model's response text, or None on failure
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for consistent selection
                "top_p": 0.9,
                "num_predict": 200,  # Limit tokens for speed
            },
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout_seconds,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Model {self.model} not found. Pull it with: ollama pull {self.model}")  # noqa: TRY400
            else:
                logger.exception("Ollama HTTP error")
            return None

    def _parse_response(self, response: str, tools: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Parse and validate AI response.

        Args:
            response: Raw model response
            tools: Available tools for validation

        Returns:
            Parsed selection dict, or None if invalid
        """
        try:
            # Extract JSON from response (model might add extra text)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                logger.warning("No JSON found in AI response")
                return None

            json_str = response[json_start:json_end]
            selection = json.loads(json_str)

            # Validate required fields
            tool_name = selection.get("tool_name")
            confidence = selection.get("confidence")
            reasoning = selection.get("reasoning", "")

            if not tool_name or confidence is None:
                logger.warning("Missing required fields in AI response")
                return None

            # Validate tool_name exists in available tools
            tool_names = {tool.get("name") for tool in tools}
            if tool_name not in tool_names:
                logger.warning(f"AI selected non-existent tool: {tool_name}. Available: {tool_names}")
                return None

            # Validate confidence range
            try:
                confidence_float = float(confidence)
                if not 0.0 <= confidence_float <= 1.0:
                    logger.warning(f"Confidence out of range: {confidence_float}")
                    confidence_float = max(0.0, min(1.0, confidence_float))
            except (ValueError, TypeError):
                logger.warning(f"Invalid confidence value: {confidence}")
                return None

            return {
                "tool_name": tool_name,
                "confidence": confidence_float,
                "reasoning": reasoning[:200],  # Limit reasoning length
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response was: {response[:500]}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error parsing AI response: {e}")
            return None

    def is_available(self) -> bool:
        """Check if Ollama service is reachable.

        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(f"{self.endpoint}/api/tags", timeout=2.0)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def pull_model(self) -> bool:
        """Attempt to pull the configured model.

        Returns:
            True if model pull succeeded, False otherwise
        """
        try:
            logger.info(f"Pulling model {self.model}...")
            response = requests.post(
                f"{self.endpoint}/api/pull",
                json={"name": self.model},
                timeout=300.0,  # Model pull can take time
            )
            return response.status_code == 200
        except requests.RequestException:
            logger.exception("Failed to pull model")
            return False
