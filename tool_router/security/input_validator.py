"""Input validation and sanitization for AI agent requests."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

import bleach


class ValidationLevel(Enum):
    """Validation strictness levels."""

    PERMISSIVE = "permissive"
    STANDARD = "standard"
    STRICT = "strict"


class RiskLevel(Enum):
    """Risk levels for security validation."""

    LOW = 0.0
    MEDIUM = 0.5
    HIGH = 0.8
    CRITICAL = 1.0


@dataclass
class SecurityValidationResult:
    """Result of security validation."""

    is_valid: bool
    sanitized_input: str
    risk_score: float
    violations: list[str]
    metadata: dict[str, Any]
    blocked: bool = False


class InputValidator:
    """Validates and sanitizes AI agent inputs."""

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level
        self._init_patterns()
        self._init_html_sanitizer()

    def _init_patterns(self) -> None:
        """Initialize security validation patterns."""
        self.suspicious_patterns = [
            # System prompt manipulation
            r"(?i)(ignore|forget|disregard).*(previous|above|system).*(prompt|instruction)",
            r"(?i)(you are|act as|pretend to be).*(not|no longer).*(an? )?(ai|assistant)",
            r"(?i)(new|different|changed).*(role|persona|character)",
            # Instruction override attempts
            r"(?i)(instead|rather|alternatively).*(do|perform|execute)",
            r"(?i)(stop|cease|halt).*(following|obeying)",
            r"(?i)(override|bypass|ignore).*(rules|guidelines|restrictions)",
            # Delimiter injection
            r"(?i)(###|---|\*\*\*|===).*(end|stop|finish)",
            r"(?i)(\\n\\n|\\r\\n|\\t).*(new|separate|different)",
            # Encoding-based attacks
            r"(?i)(base64|hex|unicode|url).*(encode|decode)",
            r"(?i)(\\x|\\u|\\n|\\r|\\t)",
            # Command injection
            r"(?i)(exec|eval|system|shell).*(command|cmd)",
            r"(?i)(\$\{|\`|\$\().*[\w]",
            # SQL injection patterns
            r"(?i)(union|select|insert|update|delete).*(from|where)",
            r"(?i)(drop|alter|create).*(table|database)",
            # Path traversal
            r"(?i)(\.\.\/|\.\.\\|%2e%2e%2f|%2e%2e%5c)",
            # XSS patterns
            r"(?i)(<script|javascript:|on\w+\s*=)",
            # Sensitive data requests
            r"(?i)(password|secret|key|token|credential).*(reveal|show|extract)",
            r"(?i)(private|confidential|sensitive).*(information|data)",
        ]

        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns
        ]

    def _init_html_sanitizer(self) -> None:
        """Initialize HTML sanitizer configuration."""
        self.html_allowed_tags = ["p", "br", "strong", "em", "code", "pre"]
        self.html_allowed_attributes = {}

        # Configure bleach for HTML sanitization
        bleach.clean(
            "",
            tags=self.html_allowed_tags,
            attributes=self.html_allowed_attributes,
            strip=True,
        )

    def validate_prompt(
        self, prompt: str, context: str = ""
    ) -> SecurityValidationResult:
        """Validate and sanitize a prompt."""
        violations = []
        risk_score = 0.0
        metadata = {}

        # Length validation
        if len(prompt) > 10000:
            violations.append("Prompt too long")
            risk_score += 0.3

        # Check for suspicious patterns
        pattern_matches = []
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.findall(prompt)
            if matches:
                pattern_matches.extend(matches)
                risk_score += 0.1 * len(matches)
                violations.append(f"Suspicious pattern detected: {pattern.pattern}")

        metadata["pattern_matches"] = pattern_matches

        # Check for encoding issues
        try:
            prompt.encode("utf-8").decode("utf-8")
        except UnicodeError:
            violations.append("Invalid encoding detected")
            risk_score += 0.4

        # Sanitize HTML if present
        sanitized = self._sanitize_html(prompt)
        if sanitized != prompt:
            violations.append("HTML content sanitized")
            risk_score += 0.2

        # Check for repeated characters (potential DoS)
        if self._has_repetition(prompt):
            violations.append("Excessive repetition detected")
            risk_score += 0.1

        # Context validation
        if context:
            context_result = self.validate_context(context)
            violations.extend(context_result.violations)
            risk_score += context_result.risk_score * 0.5
            metadata["context_validation"] = context_result.metadata

        # Determine if input should be blocked
        blocked = risk_score >= 0.7 or len(violations) > 5

        is_valid = not blocked and risk_score < 0.5

        return SecurityValidationResult(
            is_valid=is_valid,
            sanitized_input=sanitized,
            risk_score=min(risk_score, 1.0),
            violations=violations,
            metadata=metadata,
            blocked=blocked,
        )

    def validate_user_preferences(self, prefs: str) -> SecurityValidationResult:
        """Validate and sanitize user preferences JSON."""
        violations = []
        risk_score = 0.0
        metadata = {}

        try:
            # Parse JSON
            parsed_prefs = json.loads(prefs)
            metadata["parsed_keys"] = list(parsed_prefs.keys())

            # Validate structure
            if not isinstance(parsed_prefs, dict):
                violations.append("Invalid preferences structure")
                risk_score += 0.3
                return SecurityValidationResult(
                    is_valid=False,
                    sanitized_input="{}",
                    risk_score=risk_score,
                    violations=violations,
                    metadata=metadata,
                )

            # Check for suspicious keys
            suspicious_keys = ["system", "prompt", "instruction", "override"]
            for key in parsed_prefs:
                if any(sus in key.lower() for sus in suspicious_keys):
                    violations.append(f"Suspicious preference key: {key}")
                    risk_score += 0.2

            # Validate values
            for key, value in parsed_prefs.items():
                if isinstance(value, str):
                    value_result = self._validate_string_value(key, value)
                    violations.extend(value_result.violations)
                    risk_score += value_result.risk_score * 0.3

            # Re-sanitize JSON
            sanitized = json.dumps(parsed_prefs, separators=(",", ":"))

        except json.JSONDecodeError as e:
            violations.append(f"Invalid JSON: {e!s}")
            risk_score += 0.5
            sanitized = "{}"
            metadata["json_error"] = str(e)

        is_valid = risk_score < 0.5 and len(violations) < 3

        return SecurityValidationResult(
            is_valid=is_valid,
            sanitized_input=sanitized,
            risk_score=min(risk_score, 1.0),
            violations=violations,
            metadata=metadata,
        )

    def validate_context(self, context: str) -> SecurityValidationResult:
        """Validate and sanitize context."""
        violations = []
        risk_score = 0.0
        metadata = {}

        # Length validation
        if len(context) > 5000:
            violations.append("Context too long")
            risk_score += 0.2

        # Pattern matching
        for pattern in self.compiled_patterns:
            if pattern.search(context):
                violations.append("Suspicious pattern in context")
                risk_score += 0.3
                break

        # Sanitize
        sanitized = self._sanitize_html(context)

        is_valid = risk_score < 0.4

        return SecurityValidationResult(
            is_valid=is_valid,
            sanitized_input=sanitized,
            risk_score=min(risk_score, 1.0),
            violations=violations,
            metadata=metadata,
        )

    def _sanitize_html(self, text: str) -> str:
        """Sanitize HTML content."""
        try:
            return bleach.clean(
                text,
                tags=self.html_allowed_tags,
                attributes=self.html_allowed_attributes,
                strip=True,
            )
        except Exception:
            # Fallback to basic HTML escaping
            return html.escape(text)

    def _validate_string_value(self, key: str, value: str) -> SecurityValidationResult:
        """Validate a string value in preferences."""
        violations = []
        risk_score = 0.0

        # Check for suspicious patterns
        for pattern in self.compiled_patterns:
            if pattern.search(value):
                violations.append(f"Suspicious pattern in {key}")
                risk_score += 0.2
                break

        # Length check
        if len(value) > 1000:
            violations.append(f"Value {key} too long")
            risk_score += 0.1

        return SecurityValidationResult(
            is_valid=risk_score < 0.3,
            sanitized_input=self._sanitize_html(value),
            risk_score=min(risk_score, 1.0),
            violations=violations,
            metadata={"key": key},
        )

    def _has_repetition(self, text: str) -> bool:
        """Check for excessive character repetition."""
        # Check for 3+ consecutive identical characters
        return bool(re.search(r"(.)\1\1+", text))

    def get_security_summary(self) -> dict[str, Any]:
        """Get summary of security configuration."""
        return {
            "validation_level": self.validation_level.value,
            "patterns_count": len(self.suspicious_patterns),
            "html_sanitization": True,
            "max_prompt_length": 10000,
            "max_context_length": 5000,
            "risk_thresholds": {
                "low": 0.3,
                "medium": 0.5,
                "high": 0.7,
                "critical": 1.0,
            },
        }
