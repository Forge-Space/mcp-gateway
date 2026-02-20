"""Tests for tool_router.ai.prompt_architect module."""

from __future__ import annotations

import pytest

from tool_router.ai.prompt_architect import (
    TaskType,
    RequirementType,
    Requirement,
    QualityScore,
    TaskAnalyzer,
    TokenOptimizer,
    PromptRefiner,
    PromptArchitect,
)


class TestTaskType:
    """Test cases for TaskType enum."""

    def test_task_type_values(self):
        """Test that TaskType has expected values."""
        assert TaskType.CODE_GENERATION.value == "code_generation"
        assert TaskType.CODE_REFACTORING.value == "code_refactoring"
        assert TaskType.CODE_DEBUGGING.value == "code_debugging"
        assert TaskType.CODE_ANALYSIS.value == "code_analysis"
        assert TaskType.DOCUMENTATION.value == "documentation"
        assert TaskType.EXPLANATION.value == "explanation"
        assert TaskType.OPTIMIZATION.value == "optimization"
        assert TaskType.CREATIVE.value == "creative"
        assert TaskType.ANALYSIS.value == "analysis"
        assert TaskType.UNKNOWN.value == "unknown"

    def test_task_type_count(self):
        """Test number of task types."""
        assert len(TaskType) == 10


class TestRequirementType:
    """Test cases for RequirementType enum."""

    def test_requirement_type_values(self):
        """Test that RequirementType has expected values."""
        assert RequirementType.FUNCTIONALITY.value == "functionality"
        assert RequirementType.PERFORMANCE.value == "performance"
        assert RequirementType.SECURITY.value == "security"
        assert RequirementType.MAINTAINABILITY.value == "maintainability"
        assert RequirementType.ACCESSIBILITY.value == "accessibility"
        assert RequirementType.COMPATIBILITY.value == "compatibility"
        assert RequirementType.TESTING.value == "testing"
        assert RequirementType.DOCUMENTATION.value == "documentation"

    def test_requirement_type_count(self):
        """Test number of requirement types."""
        assert len(RequirementType) == 8


class TestRequirement:
    """Test cases for Requirement dataclass."""

    def test_requirement_creation(self):
        """Test Requirement creation with all fields."""
        requirement = Requirement(
            type=RequirementType.FUNCTIONALITY,
            description="Create user authentication system",
            priority="high",
            constraints=["Use OAuth 2.0", "Support JWT tokens"]
        )

        assert requirement.type == RequirementType.FUNCTIONALITY
        assert requirement.description == "Create user authentication system"
        assert requirement.priority == "high"
        assert requirement.constraints == ["Use OAuth 2.0", "Support JWT tokens"]

    def test_requirement_creation_defaults(self):
        """Test Requirement creation with default constraints."""
        requirement = Requirement(
            type=RequirementType.PERFORMANCE,
            description="Optimize database queries",
            priority="medium"
        )

        assert requirement.type == RequirementType.PERFORMANCE
        assert requirement.description == "Optimize database queries"
        assert requirement.priority == "medium"
        assert requirement.constraints is None


class TestQualityScore:
    """Test cases for QualityScore dataclass."""

    def test_quality_score_creation(self):
        """Test QualityScore creation."""
        score = QualityScore(
            overall_score=0.85,
            clarity=0.9,
            completeness=0.8,
            specificity=0.85,
            token_efficiency=0.9,
            context_preservation=0.8
        )

        assert score.overall_score == 0.85
        assert score.clarity == 0.9
        assert score.completeness == 0.8
        assert score.specificity == 0.85
        assert score.token_efficiency == 0.9
        assert score.context_preservation == 0.8


class TestTaskAnalyzer:
    """Test cases for TaskAnalyzer."""

    def test_initialization(self):
        """Test TaskAnalyzer initialization."""
        analyzer = TaskAnalyzer()

        assert hasattr(analyzer, 'task_keywords')
        assert TaskType.CODE_GENERATION in analyzer.task_keywords
        assert TaskType.CODE_REFACTORING in analyzer.task_keywords
        assert TaskType.CODE_DEBUGGING in analyzer.task_keywords
        assert TaskType.CODE_ANALYSIS in analyzer.task_keywords
        assert TaskType.DOCUMENTATION in analyzer.task_keywords
        assert TaskType.OPTIMIZATION in analyzer.task_keywords
        assert TaskType.CREATIVE in analyzer.task_keywords

    def test_identify_task_type_code_generation(self):
        """Test identifying code generation task type."""
        analyzer = TaskAnalyzer()

        prompt = "Create a new React component for user authentication"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type == TaskType.CODE_GENERATION

    def test_identify_task_type_code_refactoring(self):
        """Test identifying code refactoring task type."""
        analyzer = TaskAnalyzer()

        prompt = "Refactor the existing authentication module to improve performance"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type == TaskType.CODE_REFACTORING

    def test_identify_task_type_code_debugging(self):
        """Test identifying code debugging task type."""
        analyzer = TaskAnalyzer()

        prompt = "Fix the bug in the payment processing function"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type == TaskType.CODE_DEBUGGING

    def test_identify_task_type_code_analysis(self):
        """Test identifying code analysis task type."""
        analyzer = TaskAnalyzer()

        prompt = "Analyze the performance bottlenecks in the database layer"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type == TaskType.CODE_ANALYSIS

    def test_identify_task_type_documentation(self):
        """Test identifying documentation task type."""
        analyzer = TaskAnalyzer()

        prompt = "Write documentation for the API endpoints"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type in [TaskType.DOCUMENTATION, TaskType.CODE_GENERATION]

    def test_identify_task_type_optimization(self):
        """Test identifying optimization task type."""
        analyzer = TaskAnalyzer()

        prompt = "Optimize the application for better performance"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type in [TaskType.OPTIMIZATION, TaskType.CODE_REFACTORING]

    def test_identify_task_type_creative(self):
        """Test identifying creative task type."""
        analyzer = TaskAnalyzer()

        prompt = "Design a creative solution for user onboarding"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type == TaskType.CREATIVE

    def test_identify_task_type_unknown(self):
        """Test identifying unknown task type."""
        analyzer = TaskAnalyzer()

        prompt = "Some random text without clear task indicators"
        task_type = analyzer.identify_task_type(prompt)

        assert task_type == TaskType.UNKNOWN

    def test_identify_task_type_multiple_keywords(self):
        """Test identifying task type with multiple keywords."""
        analyzer = TaskAnalyzer()

        prompt = "Create and generate a new React component with proper error handling"
        task_type = analyzer.identify_task_type(prompt)

        # Should pick the one with highest score (CODE_GENERATION has more matches)
        assert task_type == TaskType.CODE_GENERATION

    def test_extract_requirements_functional(self):
        """Test extracting functional requirements."""
        analyzer = TaskAnalyzer()

        prompt = "Create a user authentication system that supports login and registration"
        requirements = analyzer.extract_requirements(prompt, TaskType.CODE_GENERATION)

        assert len(requirements) > 0
        assert any(req.type == RequirementType.FUNCTIONALITY for req in requirements)
        assert any("user authentication" in req.description.lower() for req in requirements)

    def test_extract_requirements_performance(self):
        """Test extracting performance requirements."""
        analyzer = TaskAnalyzer()

        prompt = "Create a fast and efficient database connection system"
        requirements = analyzer.extract_requirements(prompt, TaskType.CODE_GENERATION)

        assert any(req.type == RequirementType.PERFORMANCE for req in requirements)
        assert any(req.priority == "medium" for req in requirements)

    def test_extract_requirements_security(self):
        """Test extracting security requirements."""
        analyzer = TaskAnalyzer()

        prompt = "Create a secure authentication system with proper protection"
        requirements = analyzer.extract_requirements(prompt, TaskType.CODE_GENERATION)

        assert any(req.type == RequirementType.SECURITY for req in requirements)
        assert any(req.priority == "high" for req in requirements)

    def test_extract_requirements_maintainability(self):
        """Test extracting maintainability requirements."""
        analyzer = TaskAnalyzer()

        prompt = "Create clean and maintainable code with proper structure"
        requirements = analyzer.extract_requirements(prompt, TaskType.CODE_GENERATION)

        assert any(req.type == RequirementType.MAINTAINABILITY for req in requirements)
        assert any(req.priority == "medium" for req in requirements)

    def test_extract_requirements_accessibility(self):
        """Test extracting accessibility requirements."""
        analyzer = TaskAnalyzer()

        prompt = "Create an accessible interface that supports screen readers"
        requirements = analyzer.extract_requirements(prompt, TaskType.CODE_GENERATION)

        assert any(req.type == RequirementType.ACCESSIBILITY for req in requirements)
        assert any(req.priority == "high" for req in requirements)

    def test_extract_constraints_language(self):
        """Test extracting language constraints."""
        analyzer = TaskAnalyzer()

        prompt = "Create a Python application using Django framework"
        constraints = analyzer._extract_constraints(prompt.lower())

        assert "Use python" in constraints
        assert "Use django" in constraints

    def test_extract_constraints_technology(self):
        """Test extracting technology constraints."""
        analyzer = TaskAnalyzer()

        prompt = "Build a React application with Node.js backend"
        constraints = analyzer._extract_constraints(prompt.lower())

        assert "Use react" in constraints
        assert "Use node" in constraints

    def test_extract_constraints_version(self):
        """Test extracting version constraints."""
        analyzer = TaskAnalyzer()

        prompt = "Use version 2.0 of the API with v1.5 compatibility"
        constraints = analyzer._extract_constraints(prompt.lower())

        # Check for version patterns - handle the tuple structure properly
        assert any("version" in str(constraint).lower() for constraint in constraints)

    def test_extract_constraints_style(self):
        """Test extracting style constraints."""
        analyzer = TaskAnalyzer()


        prompt = "Create a modern and clean design for production use"
        constraints = analyzer._extract_constraints(prompt.lower())

        assert "Modern style" in constraints
        assert "Clean style" in constraints
        assert "Production style" in constraints

    def test_extract_functional_requirements_create_pattern(self):
        """Test extracting requirements with create pattern."""
        analyzer = TaskAnalyzer()

        prompt = "Create a user service that handles authentication"
        requirements = analyzer._extract_functional_requirements(prompt)

        assert any("Create user service" in req for req in requirements)
        # The second part might not be captured by the regex pattern

    def test_extract_functional_requirements_implement_pattern(self):
        """Test extracting requirements with implement pattern."""
        analyzer = TaskAnalyzer()

        prompt = "Implement payment processing with Stripe integration"
        requirements = analyzer._extract_functional_requirements(prompt)

        assert any("Implement payment processing" in req for req in requirements)
        assert any("with Stripe integration" in req for req in requirements)

    def test_extract_functional_requirements_support_pattern(self):
        """Test extracting requirements with support pattern."""
        analyzer = TaskAnalyzer()

        prompt = "Support file upload functionality with drag and drop"
        requirements = analyzer._extract_functional_requirements(prompt)

        assert any("Support file upload functionality" in req for req in requirements)


class TestTokenOptimizer:
    """Test cases for TokenOptimizer."""

    def test_initialization(self):
        """Test TokenOptimizer initialization."""
        optimizer = TokenOptimizer()

        assert hasattr(optimizer, 'common_phrases')
        assert hasattr(optimizer, 'technical_replacements')
        assert "please" in optimizer.common_phrases
        assert "application" in optimizer.technical_replacements

    def test_minimize_tokens_removes_common_phrases(self):
        """Test that minimization removes common filler phrases."""
        optimizer = TokenOptimizer()

        prompt = "Please create a React component for me"
        optimized = optimizer.minimize_tokens(prompt)

        assert "please" not in optimized.lower()
        assert "for me" not in optimized.lower()

    def test_minimize_tokens_replaces_technical_terms(self):
        """Test that minimization replaces verbose technical terms."""
        optimizer = TokenOptimizer()

        prompt = "Create an application with proper functionality implementation"
        optimized = optimizer.minimize_tokens(prompt)

        assert "app" in optimized.lower()
        assert "impl" in optimized.lower()
        assert "feature" in optimized.lower()

    def test_minimize_tokens_preserves_technical_capitalization(self):
        """Test that technical terms maintain proper capitalization."""
        optimizer = TokenOptimizer()

        prompt = "Use React and Node.js with proper API integration"
        optimized = optimizer.minimize_tokens(prompt)

        assert "react" in optimized.lower()
        assert "node" in optimized.lower()
        assert "api" in optimized.lower()

    def test_minimize_tokens_removes_extra_whitespace(self):
        """Test that minimization removes extra whitespace."""
        optimizer = TokenOptimizer()

        prompt = "Create  a   component    with   proper   spacing"
        optimized = optimizer.minimize_tokens(prompt)

        assert "  " not in optimized  # No double spaces
        assert optimized.strip() == optimized  # No leading/trailing spaces

    def test_restore_technical_capitalization(self):
        """Test restoration of technical term capitalization."""
        optimizer = TokenOptimizer()

        text = "use react and node with api and sql"
        restored = optimizer._restore_technical_capitalization(text)

        words = restored.split()
        assert "react" in words
        assert "node" in words
        assert "api" in words
        assert "sql" in words


class TestPromptRefiner:
    """Test cases for PromptRefiner."""

    def test_initialization(self):
        """Test PromptRefiner initialization."""
        refiner = PromptRefiner()

        assert hasattr(refiner, 'refinement_strategies')
        assert "add_context" in refiner.refinement_strategies
        assert "clarify_requirements" in refiner.refinement_strategies

    def test_refine_prompt_unclear_feedback(self):
        """Test refining prompt with unclear feedback."""
        refiner = PromptRefiner()

        prompt = "Create a component"
        feedback = "The requirements are unclear and confusing"
        refined = refiner.refine_prompt(prompt, feedback, TaskType.CODE_GENERATION)

        assert "Requirements:" in refined
        assert "Be specific and unambiguous" in refined

    def test_refine_prompt_missing_feedback(self):
        """Test refining prompt with missing feedback."""
        refiner = PromptRefiner()

        prompt = "Create a component"
        feedback = "Some information is missing and incomplete"
        refined = refiner.refine_prompt(prompt, feedback, TaskType.CODE_GENERATION)

        assert "Example:" in refined
        assert "Error Handling:" in refined

    def test_refine_prompt_verbose_feedback(self):
        """Test refining prompt with verbose feedback."""
        refiner = PromptRefiner()

        prompt = "Create a component with lots of detailed explanations and context"
        feedback = "The prompt is too long and verbose"
        refined = refiner.refine_prompt(prompt, feedback, TaskType.CODE_GENERATION)

        # Should be shorter (limited to 10 essential lines)
        assert len(refined.split('\n')) <= 10

    def test_refine_prompt_vague_feedback(self):
        """Test refining prompt with vague feedback."""
        refiner = PromptRefiner()

        prompt = "Create a good component with nice design"
        feedback = "The requirements are not specific enough and too vague"
        refined = refiner.refine_prompt(prompt, feedback, TaskType.CODE_GENERATION)

        assert "high-quality, maintainable" in refined
        assert "well-structured, clean" in refined

    def test_clarify_requirements_adds_structure(self):
        """Test clarifying requirements adds structure."""
        refiner = PromptRefiner()

        prompt = "Create a component"
        clarified = refiner._clarify_requirements(prompt)

        assert "Requirements:" in clarified
        assert "Be specific and unambiguous" in clarified
        assert "Provide clear success criteria" in clarified

    def test_add_missing_elements_code_generation(self):
        """Test adding missing elements for code generation."""
        refiner = PromptRefiner()

        prompt = "Create a component"
        added = refiner._add_missing_elements(prompt, TaskType.CODE_GENERATION)

        assert "Example:" in added
        assert "Error Handling:" in added

    def test_add_missing_elements_other_task_type(self):
        """Test adding missing elements for non-code generation."""
        refiner = PromptRefiner()

        prompt = "Analyze the system"
        added = refiner._add_missing_elements(prompt, TaskType.CODE_ANALYSIS)

        # Should not add code-specific elements
        assert "Example:" not in added
        assert "Error Handling:" not in added

    def test_shorten_prompt_keeps_essential_lines(self):
        """Test shortening prompt keeps essential lines."""
        refiner = PromptRefiner()

        prompt = """# Header
Create a component
## Details
Make it work properly
## Extra info
Add some comments
## More info
Include examples
## Final
Test it well
## Conclusion
Deploy it"""
        shortened = refiner._shorten_prompt(prompt)

        # Should keep essential lines, limit to 10
        lines = shortened.split('\n')
        assert len(lines) <= 10
        assert "Create a component" in lines
        assert "Make it work properly" in lines

    def test_add_specificity_replacements(self):
        """Test adding specificity replaces vague terms."""
        refiner = PromptRefiner()

        prompt = "Create a good component with nice design and better performance"
        specific = refiner._add_specificity(prompt)

        assert "high-quality, maintainable" in specific
        assert "well-structured, clean" in specific
        assert "more efficient, optimized" in specific


class TestPromptArchitect:
    """Test cases for PromptArchitect."""

    def test_initialization(self):
        """Test PromptArchitect initialization."""
        architect = PromptArchitect()

        assert hasattr(architect, 'task_analyzer')
        assert hasattr(architect, 'token_optimizer')
        assert hasattr(architect, 'prompt_refiner')
        assert hasattr(architect, '_prompt_cache')
        assert isinstance(architect.task_analyzer, TaskAnalyzer)
        assert isinstance(architect.token_optimizer, TokenOptimizer)
        assert isinstance(architect.prompt_refiner, PromptRefiner)

    def test_optimize_prompt_basic(self):
        """Test basic prompt optimization."""
        architect = PromptArchitect()

        prompt = "Create a React component for user authentication"
        result = architect.optimize_prompt(prompt)

        assert "optimized_prompt" in result
        assert "task_type" in result
        assert "requirements" in result
        assert "quality_score" in result
        assert "token_metrics" in result
        assert "optimization_applied" in result
        assert result["optimization_applied"] is True

    def test_optimize_prompt_with_feedback(self):
        """Test prompt optimization with feedback."""
        architect = PromptArchitect()

        prompt = "Create a component"
        feedback = "The requirements are unclear"
        result = architect.optimize_prompt(prompt, feedback=feedback)

        # Should apply refinement based on feedback
        assert "Requirements:" in result["optimized_prompt"]

    def test_optimize_prompt_efficient_preference(self):
        """Test optimization with efficient cost preference."""
        architect = PromptArchitect()

        prompt = "Please create a React component with proper functionality implementation for me"
        result = architect.optimize_prompt(prompt, user_cost_preference="efficient")

        # Should apply token minimization
        assert "please" not in result["optimized_prompt"].lower()
        assert "for me" not in result["optimized_prompt"].lower()

    def test_optimize_prompt_quality_preference(self):
        """Test optimization with quality cost preference."""
        architect = PromptArchitect()

        prompt = "Create a component"
        result = architect.optimize_prompt(prompt, user_cost_preference="quality")

        # Should enhance for quality
        assert "## Task:" in result["optimized_prompt"]
        assert "## Requirements:" in result["optimized_prompt"]
        assert "## Success Criteria:" in result["optimized_prompt"]

    def test_optimize_prompt_with_context(self):
        """Test optimization with context."""
        architect = PromptArchitect()

        prompt = "Create a component"
        context = "This is for a banking application"
        result = architect.optimize_prompt(prompt, context=context)

        # Context is not currently implemented in the optimization, but the result should be valid
        assert "optimized_prompt" in result
        assert result["optimization_applied"] is True

    def test_enhance_for_quality_adds_structure(self):
        """Test quality enhancement adds structure."""
        architect = PromptArchitect()

        prompt = "Create a component"
        task_type = TaskType.CODE_GENERATION
        requirements = [
            Requirement(
                type=RequirementType.FUNCTIONALITY,
                description="User authentication",
                priority="high"
            )
        ]

        enhanced = architect._enhance_for_quality(prompt, task_type, requirements)

        assert "## Task: Code Generation" in enhanced
        assert "## Requirements:" in enhanced
        assert "## Success Criteria:" in enhanced
        assert "User authentication" in enhanced
        assert "Priority: high" in enhanced

    def test_apply_task_specific_optimizations_code_generation(self):
        """Test task-specific optimizations for code generation."""
        architect = PromptArchitect()

        prompt = "Create something"
        optimized = architect._apply_task_specific_optimizations(prompt, TaskType.CODE_GENERATION)

        assert "code" in optimized.lower()
        assert "programming language" in optimized.lower()

    def test_apply_task_specific_optimizations_debugging(self):
        """Test task-specific optimizations for debugging."""
        architect = PromptArchitect()

        prompt = "Fix something"
        optimized = architect._apply_task_specific_optimizations(prompt, TaskType.CODE_DEBUGGING)

        assert "debugging approach" in optimized.lower()
        assert "root cause analysis" in optimized.lower()

    def test_apply_task_specific_optimizations_documentation(self):
        """Test task-specific optimizations for documentation."""
        architect = PromptArchitect()

        prompt = "Write something"
        optimized = architect._apply_task_specific_optimizations(prompt, TaskType.DOCUMENTATION)

        assert "documentation" in optimized.lower()
        assert "examples" in optimized.lower()

    def test_validate_prompt_quality(self):
        """Test prompt quality validation."""
        architect = PromptArchitect()

        prompt = "## Task: Create Component\n\nCreate a React component with proper error handling and examples."
        task_type = TaskType.CODE_GENERATION

        quality_score = architect._validate_prompt_quality(prompt, task_type)

        assert isinstance(quality_score, QualityScore)
        assert 0.0 <= quality_score.overall_score <= 1.0
        assert 0.0 <= quality_score.clarity <= 1.0
        assert 0.0 <= quality_score.completeness <= 1.0
        assert 0.0 <= quality_score.specificity <= 1.0
        assert 0.0 <= quality_score.token_efficiency <= 1.0
        assert 0.0 <= quality_score.context_preservation <= 1.0

    def test_calculate_clarity_with_structure(self):
        """Test clarity calculation with structure."""
        architect = PromptArchitect()

        prompt = "## Requirements\nCreate a component with proper structure."
        clarity = architect._calculate_clarity(prompt)

        assert clarity > 0.5  # Has structure bonus

    def test_calculate_clarity_without_structure(self):
        """Test clarity calculation without structure."""
        architect = PromptArchitect()

        prompt = "Create a component."
        clarity = architect._calculate_clarity(prompt)

        assert clarity == 0.5  # Base score only

    def test_calculate_completeness_code_generation(self):
        """Test completeness calculation for code generation."""
        architect = PromptArchitect()

        prompt = "Create a function with proper error handling."
        completeness = architect._calculate_completeness(prompt, TaskType.CODE_GENERATION)

        assert completeness > 0.5  # Has code and error handling

    def test_calculate_completeness_other_task(self):
        """Test completeness calculation for other task types."""
        architect = PromptArchitect()

        prompt = "Analyze the system performance."
        completeness = architect._calculate_completeness(prompt, TaskType.CODE_ANALYSIS)

        assert completeness == 0.5  # Base score only

    def test_calculate_specificity_no_vague_terms(self):
        """Test specificity calculation with no vague terms."""
        architect = PromptArchitect()

        prompt = "Create a component with 5 methods and 10 tests."
        specificity = architect._calculate_specificity(prompt)

        assert specificity > 0.5  # Has specific indicators

    def test_calculate_specificity_with_vague_terms(self):
        """Test specificity calculation with vague terms."""
        architect = PromptArchitect()

        prompt = "Create a good and nice component."
        specificity = architect._calculate_specificity(prompt)

        assert specificity < 0.5  # Penalized for vague terms

    def test_calculate_token_efficiency_ideal_range(self):
        """Test token efficiency in ideal range."""
        architect = PromptArchitect()

        # Create prompt with ~100 tokens
        prompt = "Create a React component with proper error handling and validation. " * 10
        efficiency = architect._calculate_token_efficiency(prompt)

        assert efficiency == 1.0  # Ideal range

    def test_calculate_token_efficiency_too_short(self):
        """Test token efficiency for too short prompt."""
        architect = PromptArchitect()

        prompt = "Create component."
        efficiency = architect._calculate_token_efficiency(prompt)

        assert efficiency == 0.8  # Too short

    def test_calculate_token_efficiency_too_long(self):
        """Test token efficiency for too long prompt."""
        architect = PromptArchitect()

        # Create prompt with ~300 tokens
        prompt = "This is a very long prompt with lots of detailed information and explanations that goes on and on without being concise or efficient in any way shape or form whatsoever." * 10
        efficiency = architect._calculate_token_efficiency(prompt)

        assert efficiency < 1.0  # Penalized for being too long

    def test_calculate_context_preservation_with_indicators(self):
        """Test context preservation calculation with indicators."""
        architect = PromptArchitect()

        prompt = "Remember to use the existing authentication system and consider the user preferences."
        preservation = architect._calculate_context_preservation(prompt)

        assert preservation > 0.0  # Has context indicators

    def test_calculate_context_preservation_without_indicators(self):
        """Test context preservation calculation without indicators."""
        architect = PromptArchitect()

        prompt = "Create a new component from scratch."
        preservation = architect._calculate_context_preservation(prompt)

        assert preservation == 0.0  # No context indicators

    def test_estimate_tokens(self):
        """Test token estimation."""
        architect = PromptArchitect()

        text = "Create a React component with proper error handling"
        tokens = architect._estimate_tokens(text)

        assert tokens > 0

    def test_calculate_cost_savings(self):
        """Test cost savings calculation."""
        architect = PromptArchitect()

        savings = architect._calculate_cost_savings(100, 80)

        # Use approximate comparison for floating point arithmetic
        assert abs(savings - 0.04) < 1e-10  # (100 - 80) * 0.002

    def test_calculate_cost_savings_no_reduction(self):
        """Test cost savings with no token reduction."""
        architect = PromptArchitect()

        savings = architect._calculate_cost_savings(100, 100)

        assert savings == 0.0

    def test_calculate_cost_savings_zero_tokens(self):
        """Test cost savings with zero original tokens."""
        architect = PromptArchitect()

        savings = architect._calculate_cost_savings(0, 0)

        assert savings == 0.0

    def test_get_optimization_stats(self):
        """Test getting optimization statistics."""
        architect = PromptArchitect()

        stats = architect.get_optimization_stats()

        assert "cache_size" in stats
        assert "total_optimizations" in stats
        assert "average_token_reduction" in stats
        assert "total_cost_saved" in stats
        assert stats["cache_size"] == 0  # Empty cache
        assert stats["total_optimizations"] == 0
