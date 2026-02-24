"""Prompt Architect Specialist - Expert prompt optimization and enhancement."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Task types for prompt optimization."""

    CODE_GENERATION = "code_generation"
    CODE_REFACTORING = "code_refactoring"
    CODE_DEBUGGING = "code_debugging"
    CODE_ANALYSIS = "code_analysis"
    DOCUMENTATION = "documentation"
    EXPLANATION = "explanation"
    OPTIMIZATION = "optimization"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    UNKNOWN = "unknown"


class RequirementType(Enum):
    """Types of requirements extracted from prompts."""

    FUNCTIONALITY = "functionality"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    ACCESSIBILITY = "accessibility"
    COMPATIBILITY = "compatibility"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


@dataclass
class Requirement:
    """Extracted requirement from a prompt."""

    type: RequirementType
    description: str
    priority: str  # "high", "medium", "low"
    constraints: list[str] | None = None


@dataclass
class QualityScore:
    """Quality score for a prompt."""

    overall_score: float
    clarity: float
    completeness: float
    specificity: float
    token_efficiency: float
    context_preservation: float


class TaskAnalyzer:
    """Analyze task type and extract requirements from prompts."""

    def __init__(self) -> None:
        self.task_keywords = {
            TaskType.CODE_GENERATION: [
                "create",
                "generate",
                "build",
                "implement",
                "write",
                "develop",
                "make",
                "construct",
                "design",
                "code",
                "function",
                "class",
                "component",
            ],
            TaskType.CODE_REFACTORING: [
                "refactor",
                "improve",
                "optimize",
                "clean up",
                "restructure",
                "reorganize",
                "simplify",
                "modernize",
                "update",
            ],
            TaskType.CODE_DEBUGGING: [
                "debug",
                "fix",
                "error",
                "issue",
                "problem",
                "bug",
                "broken",
                "not working",
                "fail",
                "crash",
                "exception",
            ],
            TaskType.CODE_ANALYSIS: [
                "analyze",
                "review",
                "examine",
                "inspect",
                "check",
                "audit",
                "evaluate",
                "assess",
                "understand",
                "explain",
            ],
            TaskType.DOCUMENTATION: [
                "document",
                "explain",
                "describe",
                "comment",
                "readme",
                "guide",
                "manual",
                "tutorial",
                "instruction",
                "help",
            ],
            TaskType.OPTIMIZATION: [
                "optimize",
                "improve performance",
                "speed up",
                "enhance",
                "boost",
                "make faster",
                "reduce",
                "minimize",
                "streamline",
            ],
            TaskType.CREATIVE: [
                "design",
                "create",
                "imagine",
                "brainstorm",
                "innovate",
                "invent",
                "conceptualize",
                "visualize",
                "artistic",
                "creative",
            ],
        }

    def identify_task_type(self, prompt: str) -> TaskType:
        """Identify the primary task type from a prompt."""
        prompt_lower = prompt.lower()

        # Score each task type based on keyword matches
        task_scores = {}
        for task_type, keywords in self.task_keywords.items():
            score = sum(1 for keyword in keywords if keyword in prompt_lower)
            if score > 0:
                task_scores[task_type] = score

        if not task_scores:
            return TaskType.UNKNOWN

        # Return the task type with the highest score
        return max(task_scores, key=task_scores.get)

    def extract_requirements(
        self, prompt: str, task_type: TaskType
    ) -> list[Requirement]:
        """Extract specific requirements from the prompt."""
        requirements = []
        prompt_lower = prompt.lower()

        # Extract constraints and specifications
        constraints = self._extract_constraints(prompt_lower)

        # Extract functional requirements
        functional_reqs = self._extract_functional_requirements(prompt_lower)
        for req in functional_reqs:
            requirements.append(
                Requirement(
                    type=RequirementType.FUNCTIONALITY,
                    description=req,
                    priority="high",
                    constraints=constraints,
                )
            )

        # Extract performance requirements
        if any(
            keyword in prompt_lower
            for keyword in ["fast", "performance", "speed", "optimize", "efficient"]
        ):
            requirements.append(
                Requirement(
                    type=RequirementType.PERFORMANCE,
                    description="Performance optimization required",
                    priority="medium",
                    constraints=constraints,
                )
            )

        # Extract security requirements
        if any(
            keyword in prompt_lower
            for keyword in ["secure", "security", "safe", "protect", "authenticate"]
        ):
            requirements.append(
                Requirement(
                    type=RequirementType.SECURITY,
                    description="Security considerations required",
                    priority="high",
                    constraints=constraints,
                )
            )

        # Extract maintainability requirements
        if any(
            keyword in prompt_lower
            for keyword in [
                "maintainable",
                "clean",
                "readable",
                "organized",
                "structured",
            ]
        ):
            requirements.append(
                Requirement(
                    type=RequirementType.MAINTAINABILITY,
                    description="Code maintainability required",
                    priority="medium",
                    constraints=constraints,
                )
            )

        # Extract accessibility requirements
        if any(
            keyword in prompt_lower
            for keyword in ["accessible", "a11y", "screen reader", "keyboard", "wcag"]
        ):
            requirements.append(
                Requirement(
                    type=RequirementType.ACCESSIBILITY,
                    description="Accessibility compliance required",
                    priority="high",
                    constraints=constraints,
                )
            )

        return requirements

    def _extract_constraints(self, prompt: str) -> list[str]:
        """Extract constraints from the prompt."""
        constraints = []

        # Look for specific constraint patterns
        import re

        # Language/framework constraints
        if re.search(
            r"\b(javascript|typescript|python|java|go|rust|cpp|c\+\+)\b",
            prompt,
            re.IGNORECASE,
        ):
            matches = re.findall(
                r"\b(javascript|typescript|python|java|go|rust|cpp|c\+\+)\b",
                prompt,
                re.IGNORECASE,
            )
            constraints.extend([f"Use {match}" for match in matches])

        # Technology constraints
        if re.search(
            r"\b(react|vue|angular|node|express|flask|django)\b", prompt, re.IGNORECASE
        ):
            matches = re.findall(
                r"\b(react|vue|angular|node|express|flask|django)\b",
                prompt,
                re.IGNORECASE,
            )
            constraints.extend([f"Use {match}" for match in matches])

        # Version constraints
        version_matches = re.findall(
            r"\b(version\s+\d+|v\d+|\d+\.\d+(\.\d+)?)\b", prompt, re.IGNORECASE
        )
        constraints.extend(version_matches)

        # Style constraints
        if re.search(
            r"\b(modern|clean|simple|minimal|enterprise|production)\b",
            prompt,
            re.IGNORECASE,
        ):
            matches = re.findall(
                r"\b(modern|clean|simple|minimal|enterprise|production)\b",
                prompt,
                re.IGNORECASE,
            )
            constraints.extend([f"{match.capitalize()} style" for match in matches])

        return constraints

    def _extract_functional_requirements(self, prompt: str) -> list[str]:
        """Extract functional requirements from the prompt."""
        requirements = []

        # Look for action-result patterns
        import re

        # "Create X that does Y" pattern
        create_patterns = re.findall(
            r"create\s+(?:a\s+)?(\w+(?:\s+\w+)*)\s+(?:that\s+)?(?:should\s+)?(?:will\s+)?(?:must\s+)?(\w+(?:\s+\w+)*)",
            prompt,
            re.IGNORECASE,
        )
        for subject, action in create_patterns:
            requirements.append(f"Create {subject} that {action}")

        # "Implement X with Y" pattern
        implement_patterns = re.findall(
            r"implement\s+(\w+(?:\s+\w+)*)\s+(?:with|using|for)\s+(\w+(?:\s+\w+)*)",
            prompt,
            re.IGNORECASE,
        )
        for subject, feature in implement_patterns:
            requirements.append(f"Implement {subject} with {feature}")

        # "Support X functionality" pattern
        support_patterns = re.findall(
            r"support\s+(\w+(?:\s+\w+)*)\s+(?:functionality|feature|capability)",
            prompt,
            re.IGNORECASE,
        )
        for feature in support_patterns:
            requirements.append(f"Support {feature} functionality")

        return requirements


class TokenOptimizer:
    """Optimize prompts for token efficiency."""

    def __init__(self) -> None:
        self.common_phrases = {
            "please": "",
            "could you": "",
            "would you": "",
            "i would like": "",
            "i need": "",
            "we need": "",
            "which": "",
            "who": "",
            "where": "",
            "when": "",
            "why": "",
            "how": "",
            "can you": "",
            "i want": "",
            "help me": "",
            "for me": "",
            "the following": "",
            "as follows": "",
            "in order to": "",
            "make sure": "",
            "ensure that": "",
            "don't forget": "",
            "remember to": "",
        }

        self.technical_replacements = {
            "application": "app",
            "functionality": "feature",
            "implementation": "impl",
            "development": "dev",
            "optimization": "opt",
            "configuration": "config",
            "documentation": "docs",
            "parameter": "param",
            "variable": "var",
            "constant": "const",
            "component": "comp",
            "interface": "iface",
            "class": "cls",
        }

    def minimize_tokens(self, prompt: str) -> str:
        """Minimize token usage while preserving meaning."""
        # Convert to lowercase for processing
        processed = prompt.lower()

        # Remove common filler phrases
        for phrase, replacement in self.common_phrases.items():
            processed = processed.replace(phrase, replacement)

        # Replace verbose terms with concise alternatives
        for term, replacement in self.technical_replacements.items():
            processed = processed.replace(term, replacement)

        # Remove extra whitespace
        processed = " ".join(processed.split())

        # Preserve proper capitalization for technical terms
        processed = self._restore_technical_capitalization(processed)

        return processed.strip()

    def _restore_technical_capitalization(self, text: str) -> str:
        """Restore proper capitalization for technical terms."""
        # Common technical terms that should be capitalized
        tech_terms = [
            "react",
            "vue",
            "angular",
            "node",
            "express",
            "flask",
            "django",
            "javascript",
            "typescript",
            "python",
            "java",
            "go",
            "rust",
            "cpp",
            "api",
            "rest",
            "graphql",
            "sql",
            "nosql",
            "json",
            "xml",
            "html",
            "css",
            "ui",
            "ux",
            "mvc",
            "mvp",
            "solid",
            "dry",
            "kiss",
            "yagni",
        ]

        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in tech_terms:
                words[i] = word.lower()

        return " ".join(words)


class PromptRefiner:
    """Iterative prompt refinement based on feedback."""

    def __init__(self) -> None:
        self.refinement_strategies = {
            "add_context": "Add relevant context and background information",
            "clarify_requirements": "Make requirements more specific and unambiguous",
            "add_examples": "Include examples of desired output format",
            "specify_constraints": "Clearly specify all constraints and limitations",
            "improve_structure": "Organize prompt with clear sections",
            "add_success_criteria": "Define what constitutes a successful response",
        }

    def refine_prompt(self, prompt: str, feedback: str, task_type: TaskType) -> str:
        """Refine prompt based on feedback."""
        refined_prompt = prompt

        # Analyze feedback to determine refinement strategy
        if "unclear" in feedback.lower() or "confusing" in feedback.lower():
            refined_prompt = self._clarify_requirements(refined_prompt)

        if "missing" in feedback.lower() or "incomplete" in feedback.lower():
            refined_prompt = self._add_missing_elements(refined_prompt, task_type)

        if "too long" in feedback.lower() or "verbose" in feedback.lower():
            refined_prompt = self._shorten_prompt(refined_prompt)

        if "not specific" in feedback.lower() or "vague" in feedback.lower():
            refined_prompt = self._add_specificity(refined_prompt)

        return refined_prompt

    def _clarify_requirements(self, prompt: str) -> str:
        """Add clarity to prompt requirements."""
        # Add structure section
        if "requirements:" not in prompt.lower():
            prompt += "\n\nRequirements:\n- Be specific and unambiguous\n- Provide clear success criteria"

        return prompt

    def _add_missing_elements(self, prompt: str, task_type: TaskType) -> str:
        """Add missing elements based on task type."""
        if task_type == TaskType.CODE_GENERATION:
            if "example" not in prompt.lower():
                prompt += "\n\nExample: Include code examples for clarity"
            if "error handling" not in prompt.lower():
                prompt += "\n\nError Handling: Include appropriate error handling"

        return prompt

    def _shorten_prompt(self, prompt: str) -> str:
        """Shorten prompt while preserving key information."""
        lines = prompt.split("\n")
        # Keep only essential lines
        essential_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and len(line) > 10:
                essential_lines.append(line)

        return "\n".join(essential_lines[:10])  # Limit to 10 essential lines

    def _add_specificity(self, prompt: str) -> str:
        """Add specificity to vague statements."""
        # Replace vague terms with specific ones
        replacements = {
            "good": "high-quality, maintainable",
            "nice": "well-structured, clean",
            "better": "more efficient, optimized",
            "proper": "following best practices",
            "simple": "minimal, easy to understand",
        }

        for vague, specific in replacements.items():
            prompt = prompt.replace(vague, specific)

        return prompt


class PromptArchitect:
    """Main Prompt Architect Specialist - Expert prompt optimization."""

    def __init__(self) -> None:
        self.task_analyzer = TaskAnalyzer()
        self.token_optimizer = TokenOptimizer()
        self.prompt_refiner = PromptRefiner()
        self._prompt_cache = {}

    def optimize_prompt(
        self,
        prompt: str,
        user_cost_preference: str = "balanced",
        context: str = "",
        feedback: str | None = None,
    ) -> dict[str, Any]:
        """Optimize a prompt for token efficiency and effectiveness."""
        # Analyze the task
        task_type = self.task_analyzer.identify_task_type(prompt)
        requirements = self.task_analyzer.extract_requirements(prompt, task_type)

        # Start optimization process
        optimized_prompt = prompt

        # Step 1: Apply iterative refinement if feedback provided
        if feedback:
            optimized_prompt = self.prompt_refiner.refine_prompt(
                optimized_prompt, feedback, task_type
            )

        # Step 2: Optimize for tokens based on user preference
        if user_cost_preference == "efficient":
            optimized_prompt = self.token_optimizer.minimize_tokens(optimized_prompt)
        elif user_cost_preference == "quality":
            # Add more detail and context for quality
            optimized_prompt = self._enhance_for_quality(
                optimized_prompt, task_type, requirements
            )

        # Step 3: Add task-specific optimizations
        optimized_prompt = self._apply_task_specific_optimizations(
            optimized_prompt, task_type
        )

        # Step 4: Validate quality
        quality_score = self._validate_prompt_quality(optimized_prompt, task_type)

        # Step 5: Calculate token savings
        original_tokens = self._estimate_tokens(prompt)
        optimized_tokens = self._estimate_tokens(optimized_prompt)
        token_reduction = (
            ((original_tokens - optimized_tokens) / original_tokens) * 100
            if original_tokens > 0
            else 0
        )

        return {
            "optimized_prompt": optimized_prompt,
            "task_type": task_type.value,
            "requirements": [req.__dict__ for req in requirements],
            "quality_score": quality_score.__dict__,
            "token_metrics": {
                "original_tokens": original_tokens,
                "optimized_tokens": optimized_tokens,
                "token_reduction_percent": token_reduction,
                "cost_savings": self._calculate_cost_savings(
                    original_tokens, optimized_tokens
                ),
            },
            "optimization_applied": True,
        }

    def _enhance_for_quality(
        self, prompt: str, task_type: TaskType, requirements: list[Requirement]
    ) -> str:
        """Enhance prompt for higher quality output."""
        enhanced_prompt = prompt

        # Add structured format
        if "##" not in enhanced_prompt:
            enhanced_prompt = f"\n## Task: {task_type.value.replace('_', ' ').title()}\n\n{enhanced_prompt}"

        # Add requirements section
        if requirements:
            enhanced_prompt += "\n\n## Requirements:\n"
            for req in requirements:
                enhanced_prompt += f"- {req.description} (Priority: {req.priority})\n"
                if req.constraints:
                    for constraint in req.constraints:
                        enhanced_prompt += f"  - {constraint}\n"

        # Add success criteria
        if "success criteria" not in enhanced_prompt.lower():
            enhanced_prompt += "\n\n## Success Criteria:\n- Response meets all specified requirements\n- Code follows best practices\n- Solution is complete and functional"

        return enhanced_prompt

    def _apply_task_specific_optimizations(
        self, prompt: str, task_type: TaskType
    ) -> str:
        """Apply task-specific optimizations."""
        if task_type == TaskType.CODE_GENERATION:
            return self._optimize_for_code_generation(prompt)
        if task_type == TaskType.CODE_DEBUGGING:
            return self._optimize_for_debugging(prompt)
        if task_type == TaskType.DOCUMENTATION:
            return self._optimize_for_documentation(prompt)
        return prompt

    def _optimize_for_code_generation(self, prompt: str) -> str:
        """Optimize prompt for code generation tasks."""
        # Add code-specific guidance
        if "code" not in prompt.lower():
            prompt += (
                "\n\nGenerate clean, well-structured code with proper error handling."
            )

        # Add language/framework hints if not present
        if not any(
            lang in prompt.lower()
            for lang in ["javascript", "typescript", "python", "java"]
        ):
            prompt += (
                "\n\nSpecify the programming language and framework if applicable."
            )

        return prompt

    def _optimize_for_debugging(self, prompt: str) -> str:
        """Optimize prompt for debugging tasks."""
        # Add debugging-specific guidance
        if "debug" not in prompt.lower():
            prompt += (
                "\n\nProvide systematic debugging approach with root cause analysis."
            )

        return prompt

    def _optimize_for_documentation(self, prompt: str) -> str:
        """Optimize prompt for documentation tasks."""
        # Add documentation-specific guidance
        if "document" not in prompt.lower():
            prompt += "\n\nCreate clear, comprehensive documentation with examples."

        return prompt

    def _validate_prompt_quality(
        self, prompt: str, task_type: TaskType
    ) -> QualityScore:
        """Validate the quality of an optimized prompt."""
        # Calculate quality metrics
        clarity = self._calculate_clarity(prompt)
        completeness = self._calculate_completeness(prompt, task_type)
        specificity = self._calculate_specificity(prompt)
        token_efficiency = self._calculate_token_efficiency(prompt)
        context_preservation = self._calculate_context_preservation(prompt)

        # Calculate overall score
        overall_score = (
            clarity
            + completeness
            + specificity
            + token_efficiency
            + context_preservation
        ) / 5

        return QualityScore(
            overall_score=overall_score,
            clarity=clarity,
            completeness=completeness,
            specificity=specificity,
            token_efficiency=token_efficiency,
            context_preservation=context_preservation,
        )

    def _calculate_clarity(self, prompt: str) -> float:
        """Calculate prompt clarity score."""
        # Check for clear structure and organization
        has_structure = any(
            marker in prompt for marker in ["##", "---", "Requirements:", "Example:"]
        )
        has_clear_instructions = len(prompt.split(".")) >= 3  # At least 3 sentences

        clarity_score = 0.5
        if has_structure:
            clarity_score += 0.3
        if has_clear_instructions:
            clarity_score += 0.2

        return min(clarity_score, 1.0)

    def _calculate_completeness(self, prompt: str, task_type: TaskType) -> float:
        """Calculate prompt completeness score."""
        completeness_score = 0.5  # Base score

        # Check for essential elements based on task type
        if task_type == TaskType.CODE_GENERATION:
            if any(
                keyword in prompt.lower()
                for keyword in ["function", "class", "method", "code"]
            ):
                completeness_score += 0.3
            if any(
                keyword in prompt.lower()
                for keyword in ["error", "exception", "handling"]
            ):
                completeness_score += 0.2

        return min(completeness_score, 1.0)

    def _calculate_specificity(self, prompt: str) -> float:
        """Calculate prompt specificity score."""
        # Avoid vague terms
        vague_terms = ["good", "nice", "better", "proper", "simple", "basic"]
        vague_count = sum(1 for term in vague_terms if term in prompt.lower())

        # Check for specific details
        specific_indicators = len(re.findall(r"\d+", prompt))  # Numbers
        specific_indicators += len(re.findall(r"[A-Z][a-z]+[A-Z]", prompt))  # CamelCase

        specificity_score = 0.5
        specificity_score -= vague_count * 0.1
        specificity_score += min(specific_indicators * 0.05, 0.5)

        return max(0.0, min(specificity_score, 1.0))

    def _calculate_token_efficiency(self, prompt: str) -> float:
        """Calculate token efficiency score."""
        tokens = self._estimate_tokens(prompt)
        # Ideal prompt length is 50-200 tokens
        if 50 <= tokens <= 200:
            return 1.0
        if tokens < 50:
            return 0.8  # Might be too brief
        return max(0.3, 1.0 - (tokens - 200) / 500)  # Penalty for long prompts

    def _calculate_context_preservation(self, prompt: str) -> float:
        """Calculate how well context is preserved."""
        # Check for context preservation indicators
        context_indicators = [
            "remember",
            "keep in mind",
            "based on",
            "considering",
            "given",
        ]
        context_count = sum(
            1 for indicator in context_indicators if indicator in prompt.lower()
        )

        return min(context_count * 0.2, 1.0)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Rough estimation: ~1.3 tokens per word
        return int(len(text.split()) * 1.3)

    def _calculate_cost_savings(
        self, original_tokens: int, optimized_tokens: int
    ) -> float:
        """Calculate cost savings from token reduction."""
        if original_tokens == 0:
            return 0.0

        # Assume average cost of $0.002 per token
        cost_per_token = 0.002
        original_cost = original_tokens * cost_per_token
        optimized_cost = optimized_tokens * cost_per_token

        return original_cost - optimized_cost

    def get_optimization_stats(self) -> dict[str, Any]:
        """Get optimization statistics."""
        return {
            "cache_size": len(self._prompt_cache),
            "total_optimizations": len(self._prompt_cache),
            "average_token_reduction": 0.0,  # Would be calculated from cache
            "total_cost_saved": 0.0,  # Would be calculated from cache
        }
