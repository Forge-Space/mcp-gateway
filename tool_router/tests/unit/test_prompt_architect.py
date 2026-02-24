"""Unit tests for AI prompt_architect module."""

from tool_router.ai.prompt_architect import (
    PromptArchitect,
    PromptRefiner,
    QualityScore,
    Requirement,
    RequirementType,
    TaskAnalyzer,
    TaskType,
    TokenOptimizer,
)


class TestTaskType:
    """Test TaskType enum."""

    def test_task_type_values(self) -> None:
        """Test TaskType enum values."""
        assert TaskType.CODE_GENERATION.value == "code_generation"
        assert TaskType.CODE_REFACTORING.value == "code_refactoring"
        assert TaskType.CODE_DEBUGGING.value == "code_debugging"
        assert TaskType.DOCUMENTATION.value == "documentation"
        assert TaskType.UNKNOWN.value == "unknown"


class TestRequirementType:
    """Test RequirementType enum."""

    def test_requirement_type_values(self) -> None:
        """Test RequirementType enum values."""
        assert RequirementType.FUNCTIONALITY == "functionality"
        assert RequirementType.PERFORMANCE == "performance"
        assert RequirementType.SECURITY == "security"
        assert RequirementType.MAINTAINABILITY == "maintainability"


class TestRequirement:
    """Test Requirement dataclass."""

    def test_requirement_creation(self) -> None:
        """Test Requirement creation with all fields."""
        req = Requirement(
            type=RequirementType.FUNCTIONALITY,
            description="Test requirement",
            priority="high",
            constraints=["constraint1", "constraint2"],
        )

        assert req.type == RequirementType.FUNCTIONALITY
        assert req.description == "Test requirement"
        assert req.priority == "high"
        assert req.constraints == ["constraint1", "constraint2"]

    def test_requirement_creation_minimal(self) -> None:
        """Test Requirement creation with minimal fields."""
        req = Requirement(type=RequirementType.PERFORMANCE, description="Performance requirement")

        assert req.type == RequirementType.PERFORMANCE
        assert req.description == "Performance requirement"
        assert req.priority == "medium"  # Default
        assert req.constraints is None  # Default


class TestQualityScore:
    """Test QualityScore dataclass."""

    def test_quality_score_creation(self) -> None:
        """Test QualityScore creation with all fields."""
        score = QualityScore(
            overall_score=0.8,
            clarity=0.9,
            completeness=0.7,
            specificity=0.8,
            token_efficiency=0.6,
            context_preservation=0.7,
        )

        assert score.overall_score == 0.8
        assert score.clarity == 0.9
        assert score.completeness == 0.7
        assert score.specificity == 0.8
        assert score.token_efficiency == 0.6
        assert score.context_preservation == 0.7


class TestTaskAnalyzer:
    """Test TaskAnalyzer class."""

    def test_initialization(self) -> None:
        """Test TaskAnalyzer initialization."""
        analyzer = TaskAnalyzer()

        assert analyzer.task_keywords is not None
        assert len(analyzer.task_keywords) > 0

    def test_identify_task_type_code_generation(self) -> None:
        """Test identifying code generation task type."""
        analyzer = TaskAnalyzer()

        prompt = "Create a new function for data processing"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type == TaskType.CODE_GENERATION

    def test_identify_task_type_refactoring(self) -> None:
        """Test identifying refactoring task type."""
        analyzer = TaskAnalyzer()

        prompt = "Refactor the existing code to improve performance"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type == TaskType.CODE_REFACTORING

    def test_identify_task_type_debugging(self) -> None:
        """Test identifying debugging task type."""
        analyzer = TaskAnalyzer()

        prompt = "Debug the error in the authentication module"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type == TaskType.CODE_DEBUGGING

    def test_identify_task_type_documentation(self) -> None:
        """Test identifying documentation task type."""
        analyzer = TaskAnalyzer()

        prompt = "Document the API endpoints with examples"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type == TaskType.DOCUMENTATION

    def test_identify_task_type_unknown(self) -> None:
        """Test identifying unknown task type."""
        analyzer = TaskAnalyzer()

        prompt = "Do something completely different"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type == TaskType.UNKNOWN

    def test_identify_task_type_multiple_keywords(self) -> None:
        """Test task type identification with multiple keywords."""
        analyzer = TaskAnalyzer()

        prompt = "Create and implement a new component"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type == TaskType.CODE_GENERATION

    def test_extract_requirements_code_generation(self) -> None:
        """Test extracting requirements from code generation prompt."""
        analyzer = TaskAnalyzer()

        prompt = "Create a user authentication system with secure login"
        task_type = TaskType.CODE_GENERATION

        requirements = analyzer.extract_requirements(prompt, task_type)

        assert len(requirements) > 0
        assert any(req.type == RequirementType.FUNCTIONALITY for req in requirements)
        assert any("authentication" in req.description.lower() for req in requirements)

    def test_extract_requirements_with_security(self) -> None:
        """Test extracting security requirements."""
        analyzer = TaskAnalyzer()

        prompt = "Create a secure payment processing system"
        task_type = TaskType.CODE_GENERATION

        requirements = analyzer.extract_requirements(prompt, task_type)

        security_reqs = [req for req in requirements if req.type == RequirementType.SECURITY]
        assert len(security_reqs) > 0
        assert security_reqs[0].description == "Security considerations required"

    def test_extract_requirements_with_performance(self) -> None:
        """Test extracting performance requirements."""
        analyzer = TaskAnalyzer()

        prompt = "Create a fast data processing system"
        task_type = TaskType.CODE_GENERATION

        requirements = analyzer.extract_requirements(prompt, task_type)

        perf_reqs = [req for req in requirements if req.type == RequirementType.PERFORMANCE]
        assert len(perf_reqs) > 0
        assert perf_reqs[0].description == "Performance optimization required"

    def test_extract_constraints_technology(self) -> None:
        """Test extracting technology constraints."""
        analyzer = TaskAnalyzer()

        prompt = "Create a React component using TypeScript"
        constraints = analyzer._extract_constraints(prompt)

        assert len(constraints) > 0
        assert any("react" in constraint.lower() for constraint in constraints)
        assert any("typescript" in constraint.lower() for constraint in constraints)

    def test_extract_constraints_version(self) -> None:
        """Test extracting version constraints."""
        analyzer = TaskAnalyzer()

        prompt = "Use version 2.0.0 of the library"
        constraints = analyzer._extract_constraints(prompt)

        assert len(constraints) > 0
        assert any("version 2.0.0" in constraint for constraint in constraints)

    def test_extract_constraints_style(self) -> None:
        """Test extracting style constraints."""
        analyzer = TaskAnalyzer()

        prompt = "Write clean, modern code following best practices"
        constraints = analyzer._extract_constraints(prompt)

        assert len(constraints) > 0
        assert any("clean" in constraint.lower() for constraint in constraints)

    def test_extract_functional_requirements(self) -> None:
        """Test extracting functional requirements."""
        analyzer = TaskAnalyzer()

        prompt = "Create a user management system that handles user registration"
        requirements = analyzer._extract_functional_requirements(prompt)

        assert len(requirements) > 0
        assert any("user management" in req for req in requirements)

    def test_extract_functional_requirements_implement_pattern(self) -> None:
        """Test extracting functional requirements with implement pattern."""
        analyzer = TaskAnalyzer()

        prompt = "Implement error handling for the API"
        requirements = analyzer._extract_functional_requirements(prompt)

        assert len(requirements) > 0
        assert any("error handling" in req for req in requirements)


class TestTokenOptimizer:
    """Test TokenOptimizer class."""

    def test_initialization(self) -> None:
        """Test TokenOptimizer initialization."""
        optimizer = TokenOptimizer()

        assert optimizer.common_phrases is not None
        assert optimizer.technical_replacements is not None

    def test_minimize_tokens_remove_fillers(self) -> None:
        """Test removing filler phrases."""
        optimizer = TokenOptimizer()

        original = "Please create a function that handles user authentication"
        optimized = optimizer.minimize_tokens(original)

        assert "please" not in optimized
        assert "create a function that handles user authentication" in optimized

    def test_minimize_tokens_technical_replacements(self) -> None:
        """Test technical term replacements."""
        optimizer = TokenOptimizer()

        original = "Create an application with functionality and implementation"
        optimized = optimizer.minimize_tokens(original)

        assert "application" not in optimized
        assert "app" in optimized
        assert "functionality" not in optimized
        assert "feature" in optimized
        assert "implementation" not in optimized
        assert "impl" in optimized

    def test_minimize_tokens_combined(self) -> None:
        """Test combined filler and technical replacements."""
        optimizer = TokenOptimizer()

        original = "Please create an application with clean functionality"
        optimized = optimizer.minimize_tokens(original)

        assert "please" not in optimized
        assert "application" not in optimized
        assert "app" in optimized
        assert "clean" in optimized
        assert "functionality" not in optimized
        assert "feature" in optimized


class TestPromptRefiner:
    """Test PromptRefiner class."""

    def test_initialization(self) -> None:
        """Test PromptRefiner initialization."""
        refiner = PromptRefiner()

        assert refiner.refinement_strategies is not None
        assert len(refiner.refinement_strategies) > 0

    def test_refine_prompt_add_examples(self) -> None:
        """Test prompt refinement by adding examples."""
        refiner = PromptRefiner()

        original = "Create a function"
        feedback = "Add examples for better understanding"

        refined = refiner.refine_prompt(original, feedback, TaskType.CODE_GENERATION)

        assert "Examples:" in refined
        assert "function" in refined

    def test_refine_prompt_clarification(self) -> None:
        """Test prompt refinement by clarification."""
        refiner = PromptRefiner()

        original = "Make it work"
        feedback = "Be more specific about what it should do"

        refined = refiner.refine_prompt(original, feedback, TaskType.CODE_GENERATION)

        assert "specifically" in refined or "clear" in refined
        assert len(refined) > len(original)

    def test_refine_prompt_error_handling(self) -> None:
        """Test prompt refinement for error handling."""
        refiner = PromptRefiner()

        original = "Create a function"
        feedback = "Add proper error handling"

        refined = refiner.refine_prompt(original, feedback, TaskType.CODE_GENERATION)

        assert "error" in refined and "handling" in refined

    def test_refine_prompt_security(self) -> None:
        """Test prompt refinement for security."""
        refiner = PromptRefiner()

        original = "Create a login system"
        feedback = "Add security measures"

        refined = refiner.refine_prompt(original, feedback, TaskType.CODE_GENERATION)

        assert "security" in refined or "secure" in refined

    def test_refine_prompt_performance(self) -> None:
        """Test prompt refinement for performance."""
        refiner = PromptRefiner()

        original = "Create a data processor"
        feedback = "Optimize for performance"

        refined = refiner.refine_prompt(original, feedback, TaskType.CODE_GENERATION)

        assert "performance" in refined or "optimize" in refined or "fast" in refined

    def test_refine_prompt_documentation(self) -> None:
        """Test prompt refinement for documentation."""
        refiner = PromptRefiner()

        original = "Explain the code"
        feedback = "Add comprehensive documentation"

        refined = refiner.refine_prompt(original, feedback, TaskType.DOCUMENTATION)

        assert "documentation" in refined or "docs" in refined

    def test_refine_prompt_unknown_task(self) -> None:
        """Test prompt refinement for unknown task type."""
        refiner = PromptRefiner()

        original = "Do something"
        feedback = "Be more specific"

        refined = refiner.refine_prompt(original, feedback, TaskType.UNKNOWN)

        assert len(refined) > len(original)


class TestPromptArchitect:
    """Test PromptArchitect class."""

    def test_initialization(self) -> None:
        """Test PromptArchitect initialization with proper component setup."""
        architect = PromptArchitect()

        # Should initialize all required components
        assert architect.task_analyzer is not None
        assert architect.token_optimizer is not None
        assert architect.prompt_refiner is not None

        # Should start with empty cache and default configuration
        assert architect._prompt_cache == {}

        # Components should be properly configured for interaction
        # This tests the dependency injection and component setup logic

    def test_optimize_prompt_basic(self) -> None:
        """Test basic prompt optimization."""
        architect = PromptArchitect()

        prompt = "Create a function"

        result = architect.optimize_prompt(prompt)

        assert "optimized_prompt" in result
        assert "task_type" in result
        assert "requirements" in result
        assert "quality_score" in result
        assert "token_metrics" in result
        assert "optimization_applied" in result

    def test_optimize_prompt_with_context(self) -> None:
        """Test prompt optimization with context."""
        architect = PromptArchitect()

        prompt = "Create a function for React"
        context = "Frontend development"

        result = architect.optimize_prompt(prompt, context=context)

        assert result["context"] == context

    def test_optimize_prompt_with_feedback(self) -> None:
        """Test prompt optimization with feedback."""
        architect = PromptArchitect()

        prompt = "Create a function"
        feedback = "Add error handling"

        result = architect.optimize_prompt(prompt, feedback=feedback)

        assert result["optimized_prompt"] != prompt  # Should be refined

    def test_optimize_prompt_cost_preference(self) -> None:
        """Test prompt optimization with cost preference."""
        architect = PromptArchitect()

        prompt = "Create a comprehensive system"

        # Efficient preference should minimize tokens
        result_efficient = architect.optimize_prompt(prompt, user_cost_preference="efficient")
        result_quality = architect.optimize_prompt(prompt, user_cost_preference="quality")

        assert len(result_efficient["optimized_prompt"]) <= len(result_quality["optimized_prompt"])

    def test_optimize_prompt_invalid_preference(self) -> None:
        """Test prompt optimization with invalid cost preference."""
        architect = PromptArchitect()

        prompt = "Create a function"

        # Should default to balanced
        result = architect.optimize_prompt(prompt, user_cost_preference="invalid")

        assert result["user_cost_preference"] == "balanced"

    def test_enhance_for_quality_code_generation(self) -> None:
        """Test quality enhancement for code generation."""
        architect = PromptArchitect()

        prompt = "Create a function"
        task_type = TaskType.CODE_GENERATION
        requirements = [
            Requirement(
                type=RequirementType.FUNCTIONALITY,
                description="Test requirement",
                priority="high",
            )
        ]

        enhanced = architect._enhance_for_quality(prompt, task_type, requirements)

        assert "## Task:" in enhanced
        assert "Requirements:" in enhanced
        assert "Success Criteria:" in enhanced

    def test_enhance_for_quality_documentation(self) -> None:
        """Test quality enhancement for documentation."""
        architect = PromptArchitect()

        prompt = "Explain the system"
        task_type = TaskType.DOCUMENTATION
        requirements = []

        enhanced = architect._enhance_for_quality(prompt, task_type, requirements)

        assert "## Task:" in enhanced
        assert "Success Criteria:" in enhanced

    def test_apply_task_specific_optimizations_code_generation(self) -> None:
        """Test code generation specific optimizations."""
        architect = PromptArchitect()

        prompt = "Create a function"
        optimized = architect._apply_task_specific_optimizations(prompt, TaskType.CODE_GENERATION)

        assert "code" in optimized.lower() or "function" in optimized.lower()

    def test_apply_task_specific_optimizations_debugging(self) -> None:
        """Test debugging specific optimizations."""
        architect = PromptArchitect()

        prompt = "Fix the bug"
        optimized = architect._apply_task_specific_optimizations(prompt, TaskType.CODE_DEBUGGING)

        assert "debug" in optimized.lower() or "error" in optimized.lower()

    def test_apply_task_specific_optimizations_documentation(self) -> None:
        """Test documentation specific optimizations."""
        architect = PromptArchitect()

        prompt = "Document the API"
        optimized = architect._apply_task_specific_optimizations(prompt, TaskType.DOCUMENTATION)

        assert "document" in optimized.lower() or "docs" in optimized.lower()

    def test_apply_task_specific_optimizations_unknown(self) -> None:
        """Test optimizations for unknown task type."""
        architect = PromptArchitect()

        prompt = "Do something"
        optimized = architect._apply_task_specific_optimizations(prompt, TaskType.UNKNOWN)

        # Should return unchanged
        assert optimized == prompt

    def test_validate_prompt_quality(self) -> None:
        """Test prompt quality validation."""
        architect = PromptArchitect()

        prompt = "Create a well-structured function with proper error handling and examples"

        quality_score = architect._validate_prompt_quality(prompt, TaskType.CODE_GENERATION)

        assert isinstance(quality_score, QualityScore)
        assert 0.0 <= quality_score.overall_score <= 1.0
        assert 0.0 <= quality_score.clarity <= 1.0
        assert 0.0 <= quality_score.completeness <= 1.0
        assert 0.0 <= quality_score.specificity <= 1.0
        assert 0.0 <= quality_score.token_efficiency <= 1.0
        assert 0.0 <= quality_score.context_preservation <= 1.0

    def test_calculate_clarity_high_score(self) -> None:
        """Test clarity calculation with high score."""
        architect = PromptArchitect()

        prompt = "## Task\n\nCreate a function with clear instructions.\n\n## Requirements\n\n- Function should handle errors."
        quality_score = architect._calculate_clarity(prompt)

        assert quality_score >= 0.8  # Has structure and clear instructions

    def test_calculate_clarity_low_score(self) -> None:
        """Test clarity calculation with low score."""
        architect = PromptArchitect()

        prompt = "make it work"
        quality_score = architect._calculate_clarity(prompt)

        assert quality_score <= 0.7  # No structure, vague instructions

    def test_calculate_completeness_code_generation(self) -> None:
        """Test completeness calculation for code generation."""
        architect = PromptArchitect()

        prompt = "Create a function with proper error handling"
        quality_score = architect._calculate_completeness(prompt, TaskType.CODE_GENERATION)

        assert quality_score >= 0.7  # Has error handling mentioned

    def test_calculate_completeness_no_code_generation(self) -> None:
        """Test completeness calculation without code generation keywords."""
        architect = PromptArchitect()

        prompt = "Explain the concept"
        quality_score = architect._calculate_completeness(prompt, TaskType.CODE_GENERATION)

        assert quality_score <= 0.5  # No code keywords

    def test_calculate_specificity_high_score(self) -> None:
        """Test specificity calculation with high score."""
        architect = PromptArchitect()

        prompt = (
            "Create UserAuthentication class with validateCredentials method that accepts string and returns boolean"
        )
        quality_score = architect._calculate_specificity(prompt)

        assert quality_score >= 0.7  # Has specific details

    def test_calculate_specificity_low_score(self) -> None:
        """Test specificity calculation with low score."""
        architect = PromptArchitect()

        prompt = "Create a good function"
        quality_score = architect._calculate_specificity(prompt)

        assert quality_score <= 0.5  # Vague description

    def test_calculate_token_efficiency_ideal_range(self) -> None:
        """Test token efficiency calculation in ideal range."""
        architect = PromptArchitect()

        quality_score = architect._calculate_token_efficiency("150 tokens")

        assert quality_score == 1.0  # Ideal range

    def test_calculate_token_efficiency_too_short(self) -> None:
        """Test token efficiency calculation for too short prompt."""
        architect = PromptArchitect()

        quality_score = architect._calculate_token_efficiency("10 tokens")

        assert quality_score == 0.8  # Too brief

    def test_calculate_token_efficiency_too_long(self) -> None:
        """Test token efficiency calculation for too long prompt."""
        architect = PromptArchitect()

        quality_score = architect._calculate_token_efficiency("500 tokens")

        assert quality_score < 1.0  # Penalty for long prompts

    def test_calculate_context_preservation_with_context(self) -> None:
        """Test context preservation calculation with context indicators."""
        architect = PromptArchitect()

        prompt = "Remember to use the existing patterns"
        quality_score = architect._calculate_context_preservation(prompt)

        assert quality_score > 0.0  # Has context indicators

    def test_calculate_context_preservation_no_context(self) -> None:
        """Test context preservation calculation without context indicators."""
        architect = PromptArchitect()

        prompt = "Create a function"
        quality_score = architect._calculate_context_preservation(prompt)

        assert quality_score == 0.0  # No context indicators

    def test_estimate_tokens(self) -> None:
        """Test token estimation."""
        architect = PromptArchitect()

        text = "This is a test prompt with multiple words"
        tokens = architect._estimate_tokens(text)

        assert tokens > 0
        assert isinstance(tokens, int)

    def test_estimate_tokens_empty(self) -> None:
        """Test token estimation for empty text."""
        architect = PromptArchitect()

        tokens = architect._estimate_tokens("")

        assert tokens == 0

    def test_get_optimization_stats(self) -> None:
        """Test optimization statistics."""
        architect = PromptArchitect()

        stats = architect.get_optimization_stats()

        assert "cache_size" in stats
        assert "total_optimizations" in stats
        assert "average_token_reduction" in stats
        assert "total_cost_saved" in stats

    def test_optimization_caching(self) -> None:
        """Test optimization caching functionality."""
        architect = PromptArchitect()

        # First call should not be cached
        result1 = architect.optimize_prompt("test prompt 1")
        assert len(architect._prompt_cache) == 1

        # Second call with same prompt should use cache
        result2 = architect.optimize_prompt("test prompt 1")
        assert len(architect._prompt_cache) == 1  # Same cache entry

        # Different prompt should add new cache entry
        result3 = architect.optimize_prompt("test prompt 2")
        assert len(architect._prompt_cache) == 2
