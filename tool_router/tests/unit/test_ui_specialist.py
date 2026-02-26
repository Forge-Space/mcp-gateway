"""Unit tests for tool_router/ai/ui_specialist.py module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tool_router.ai.ui_specialist import (
    AccessibilityLevel,
    ComponentGenerator,
    ComponentSpec,
    ComponentType,
    DesignSystem,
    UIFramework,
    UIRequirement,
    UISpecialist,
    UIStandardsCompliance,
)


class TestUIFramework:
    """Test cases for UIFramework enum."""

    def test_framework_values(self) -> None:
        """Test that all expected framework values are present."""
        expected_frameworks = [
            "react",
            "vue",
            "angular",
            "svelte",
            "nextjs",
            "html_css",
            "tailwind",
            "bootstrap",
            "material_ui",
            "chakra_ui",
        ]

        actual_frameworks = [framework.value for framework in UIFramework]

        # Business logic: all expected frameworks should be available
        for framework in expected_frameworks:
            assert framework in actual_frameworks

    def test_framework_count(self) -> None:
        """Test framework count matches expectations."""
        # Business logic: should have 10 supported frameworks
        assert len(UIFramework) == 10

    def test_framework_uniqueness(self) -> None:
        """Test that framework values are unique."""
        values = [framework.value for framework in UIFramework]

        # Business logic: framework values should be unique
        assert len(values) == len(set(values))


class TestDesignSystem:
    """Test cases for DesignSystem enum."""

    def test_design_system_values(self) -> None:
        """Test that all expected design system values are present."""
        expected_systems = [
            "material_design",
            "ant_design",
            "bootstrap",
            "tailwind_ui",
            "chakra_ui",
            "mantine",
            "semantic_ui",
            "custom",
        ]

        actual_systems = [system.value for system in DesignSystem]

        # Business logic: all expected design systems should be available
        for system in expected_systems:
            assert system in actual_systems

    def test_design_system_count(self) -> None:
        """Test design system count matches expectations."""
        # Business logic: should have 8 supported design systems
        assert len(DesignSystem) == 8


class TestComponentType:
    """Test cases for ComponentType enum."""

    def test_component_type_values(self) -> None:
        """Test that all expected component type values are present."""
        expected_types = [
            "form",
            "table",
            "chart",
            "modal",
            "navigation",
            "card",
            "button",
            "input",
            "layout",
            "dashboard",
            "landing",
            "auth",
            "settings",
        ]

        actual_types = [component_type.value for component_type in ComponentType]

        # Business logic: all expected component types should be available
        for component_type in expected_types:
            assert component_type in actual_types

    def test_component_type_count(self) -> None:
        """Test component type count matches expectations."""
        # Business logic: should have 13 supported component types
        assert len(ComponentType) == 13


class TestAccessibilityLevel:
    """Test cases for AccessibilityLevel enum."""

    def test_accessibility_values(self) -> None:
        """Test that all expected accessibility values are present."""
        expected_levels = ["aa", "aaa", "minimal"]

        actual_levels = [level.value for level in AccessibilityLevel]

        # Business logic: all expected accessibility levels should be available
        for level in expected_levels:
            assert level in actual_levels

    def test_accessibility_count(self) -> None:
        """Test accessibility level count matches expectations."""
        # Business logic: should have 3 accessibility levels
        assert len(AccessibilityLevel) == 3


class TestUIRequirement:
    """Test cases for UIRequirement dataclass."""

    def test_ui_requirement_creation_with_defaults(self) -> None:
        """Test UIRequirement creation with default values."""
        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA,
        )

        # Business logic: default values should be applied correctly
        assert requirement.component_type == ComponentType.FORM
        assert requirement.framework == UIFramework.REACT
        assert requirement.design_system == DesignSystem.MATERIAL_DESIGN
        assert requirement.accessibility_level == AccessibilityLevel.AA
        assert requirement.responsive is True  # Default
        assert requirement.dark_mode is False  # Default
        assert requirement.animations is False  # Default
        assert requirement.custom_styling is False  # Default

    def test_ui_requirement_creation_with_all_fields(self) -> None:
        """Test UIRequirement creation with all fields specified."""
        requirement = UIRequirement(
            component_type=ComponentType.DASHBOARD,
            framework=UIFramework.VUE,
            design_system=DesignSystem.TAILWIND_UI,
            accessibility_level=AccessibilityLevel.AAA,
            responsive=False,
            dark_mode=True,
            animations=True,
            custom_styling=True,
        )

        # Business logic: all fields should be set correctly
        assert requirement.component_type == ComponentType.DASHBOARD
        assert requirement.framework == UIFramework.VUE
        assert requirement.design_system == DesignSystem.TAILWIND_UI
        assert requirement.accessibility_level == AccessibilityLevel.AAA
        assert requirement.responsive is False
        assert requirement.dark_mode is True
        assert requirement.animations is True
        assert requirement.custom_styling is True


class TestComponentSpec:
    """Test cases for ComponentSpec dataclass."""

    def test_component_spec_creation(self) -> None:
        """Test ComponentSpec creation."""
        spec = ComponentSpec(
            name="TestForm",
            type=ComponentType.FORM,
            props={"validation": True},
            styling={"padding": "16px"},
            accessibility_features=["keyboard_navigation", "screen_reader_support"],
            responsive_breakpoints=["sm", "md", "lg"],
        )

        # Business logic: all fields should be set correctly
        assert spec.name == "TestForm"
        assert spec.type == ComponentType.FORM
        assert spec.props == {"validation": True}
        assert spec.styling == {"padding": "16px"}
        assert len(spec.accessibility_features) == 2
        assert len(spec.responsive_breakpoints) == 3


class TestUIStandardsCompliance:
    """Test cases for UIStandardsCompliance."""

    def test_initialization(self) -> None:
        """Test UIStandardsCompliance initialization."""
        compliance = UIStandardsCompliance()

        # Business logic: should initialize with guidelines and practices
        assert hasattr(compliance, "wcag_guidelines")
        assert hasattr(compliance, "framework_best_practices")
        assert AccessibilityLevel.AA in compliance.wcag_guidelines
        assert UIFramework.REACT in compliance.framework_best_practices

    def test_validate_component_high_compliance(self) -> None:
        """Test validation with high compliance score."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={"functional_components": True},
            styling={"tailwind": True},
            accessibility_features=[
                "color_contrast_4_5",
                "keyboard_navigation",
                "focus_indicators",
                "screen_reader_support",
                "alt_text_for_images",
                "semantic_html",
            ],
            responsive_breakpoints=["sm", "md", "lg"],
        )

        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.TAILWIND_UI,
            accessibility_level=AccessibilityLevel.AA,
            responsive=True,
        )

        result = compliance.validate_component(spec, requirement)

        # Business logic: high compliance should yield high scores
        assert result["compliance_score"] >= 0.8
        assert result["accessibility_score"] >= 0.8
        assert result["framework_score"] >= 0.8
        assert result["responsive_score"] == 1.0  # Responsive with breakpoints
        assert result["design_score"] >= 0.8

    def test_validate_component_low_compliance(self) -> None:
        """Test validation with low compliance score."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},  # Missing framework best practices
            styling={},  # Missing design system styling
            accessibility_features=["basic_keyboard_access"],  # Minimal features
            responsive_breakpoints=[],  # No responsive breakpoints
        )

        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA,
            responsive=True,
        )

        result = compliance.validate_component(spec, requirement)

        # Business logic: low compliance should yield lower scores
        assert result["compliance_score"] < 0.8
        assert result["accessibility_score"] < 0.8
        assert result["framework_score"] < 0.8
        assert result["responsive_score"] < 1.0  # Missing breakpoints
        assert result["design_score"] < 0.8

    def test_validate_component_no_responsive_requirement(self) -> None:
        """Test validation when responsive is not required."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[],
        )

        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.MINIMAL,
            responsive=False,
        )

        result = compliance.validate_component(spec, requirement)

        # Business logic: responsive score should be perfect when not required
        assert result["responsive_score"] == 1.0

    def test_check_accessibility_compliance_aaa(self) -> None:
        """Test accessibility compliance checking for AAA level."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[
                "color_contrast_7_1",
                "no_reflow",
                "text_spacing",
                "pointer_gestures",
                "orientation",
                "color_contrast_4_5",
                "keyboard_navigation",
                "focus_indicators",
                "screen_reader_support",
                "alt_text_for_images",
                "semantic_html",
            ],
            responsive_breakpoints=[],
        )

        score = compliance._check_accessibility_compliance(spec, AccessibilityLevel.AAA)

        # Business logic: full AAA compliance should yield perfect score
        assert score == 1.0

    def test_check_framework_compliance_unsupported_framework(self) -> None:
        """Test framework compliance for unsupported framework."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[],
        )

        score = compliance._check_framework_compliance(spec, UIFramework.SVELTE)

        # Business logic: unsupported framework should get default score
        assert score == 0.8

    def test_check_design_system_compliance_custom(self) -> None:
        """Test design system compliance for custom design system."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[],
        )

        score = compliance._check_design_system_compliance(spec, DesignSystem.CUSTOM)

        # Business logic: custom design system should get default score
        assert score == 0.8


class TestComponentGenerator:
    """Test cases for ComponentGenerator."""

    def test_initialization(self) -> None:
        """Test ComponentGenerator initialization."""
        generator = ComponentGenerator()

        # Business logic: should initialize with templates for all component types
        assert hasattr(generator, "templates")
        assert len(generator.templates) == len(ComponentType)
        assert ComponentType.FORM in generator.templates
        assert ComponentType.DASHBOARD in generator.templates

    def test_generate_component_success(self) -> None:
        """Test successful component generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA,
        )

        spec = ComponentSpec(
            name="TestForm",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=["keyboard_navigation"],
            responsive_breakpoints=["sm", "md"],
        )

        result = generator.generate_component(requirement, spec)

        # Business logic: should return complete generation result
        assert "component_code" in result
        assert "component_spec" in result
        assert "requirement" in result
        assert "generated_features" in result
        assert "token_estimate" in result
        assert result["component_spec"] == spec
        assert result["requirement"] == requirement

    def test_generate_component_unsupported_type(self) -> None:
        """Test component generation with unsupported type."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA,
        )

        # Create spec with invalid type by modifying directly
        spec = MagicMock(spec=ComponentSpec)
        spec.type = "unsupported_type"

        # Business logic: unsupported type should raise ValueError
        with pytest.raises(ValueError, match="Unsupported component type"):
            generator.generate_component(requirement, spec)

    def test_generate_form_template(self) -> None:
        """Test form template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA,
        )

        spec = ComponentSpec(
            name="TestForm",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[],
        )

        template = generator._generate_form_template(requirement, spec)

        # Business logic: form template should contain form elements
        assert "form" in template.lower()
        assert spec.name in template

    def test_apply_framework_enhancements_react(self) -> None:
        """Test framework enhancements for React."""
        generator = ComponentGenerator()

        code = "<!-- React component -->"
        enhanced = generator._apply_framework_enhancements(code, UIFramework.REACT)

        # Business logic: React comments should be converted
        assert "{/*" in enhanced
        assert "*/}" in enhanced

    def test_apply_framework_enhancements_vue(self) -> None:
        """Test framework enhancements for Vue."""
        generator = ComponentGenerator()

        code = "<!-- Vue component -->"
        enhanced = generator._apply_framework_enhancements(code, UIFramework.VUE)

        # Business logic: Vue comments should be preserved
        assert "<!--" in enhanced
        assert "-->" in enhanced

    def test_apply_responsive_design_true(self) -> None:
        """Test responsive design application when responsive is true."""
        generator = ComponentGenerator()

        code = '<div class="container">'
        enhanced = generator._apply_responsive_design(code, True)

        # Business logic: responsive classes should be added
        assert "responsive-" in enhanced

    def test_apply_responsive_design_false(self) -> None:
        """Test responsive design application when responsive is false."""
        generator = ComponentGenerator()

        code = '<div class="container">'
        enhanced = generator._apply_responsive_design(code, False)

        # Business logic: responsive classes should not be added
        assert "responsive-" not in enhanced

    def test_apply_styling_tailwind(self) -> None:
        """Test styling application for Tailwind."""
        generator = ComponentGenerator()

        code = '<div class="container">'
        styled = generator._apply_styling(code, DesignSystem.TAILWIND_UI, False)

        # Business logic: Tailwind classes should be added
        assert "tw-" in styled

    def test_apply_styling_dark_mode(self) -> None:
        """Test styling application with dark mode."""
        generator = ComponentGenerator()

        code = '<div class="container">'
        styled = generator._apply_styling(code, DesignSystem.TAILWIND_UI, True)

        # Business logic: dark mode classes should be added
        assert "dark-" in styled

    def test_extract_features(self) -> None:
        """Test feature extraction from code."""
        generator = ComponentGenerator()

        code = """
        <div role="main" class="responsive-container dark-mode">
            <button aria-label="Submit">Submit</button>
        </div>
        """

        features = generator._extract_features(code)

        # Business logic: should extract all present features
        assert "semantic_roles" in features
        assert "aria_labels" in features
        assert "responsive_design" in features
        assert "dark_mode" in features

    def test_estimate_component_tokens(self) -> None:
        """Test token estimation for component."""
        generator = ComponentGenerator()

        code = '<div class="container"><p>Hello World</p></div>'
        tokens = generator._estimate_component_tokens(code)

        # Business logic: tokens should be estimated based on word count
        assert tokens > 0
        assert isinstance(tokens, (int, float))

    def test_generate_all_component_types(self) -> None:
        """Test generation of all supported component types."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.HTML_CSS,
            design_system=DesignSystem.CUSTOM,
            accessibility_level=AccessibilityLevel.MINIMAL,
        )

        spec = ComponentSpec(
            name="Test",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[],
        )

        # Business logic: all component types should be generatable
        for component_type in ComponentType:
            spec.type = component_type
            requirement.component_type = component_type

            try:
                result = generator.generate_component(requirement, spec)
                assert "component_code" in result
            except Exception as e:
                pytest.fail(f"Failed to generate {component_type.value}: {e}")


class TestUISpecialist:
    """Test cases for UISpecialist."""

    def test_initialization(self) -> None:
        """Test UISpecialist initialization."""
        specialist = UISpecialist()

        # Business logic: should initialize with compliance checker and generator
        assert hasattr(specialist, "compliance_checker")
        assert hasattr(specialist, "component_generator")
        assert hasattr(specialist, "_component_cache")
        assert isinstance(specialist.compliance_checker, UIStandardsCompliance)
        assert isinstance(specialist.component_generator, ComponentGenerator)

    def test_generate_ui_component_success(self) -> None:
        """Test successful UI component generation."""
        specialist = UISpecialist()

        result = specialist.generate_ui_component(
            component_name="TestForm",
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA,
        )

        # Business logic: should return complete generation result
        assert "component" in result
        assert "validation" in result
        assert "requirement" in result
        assert "spec" in result
        assert result["optimization_applied"] is True  # Default
        assert result["industry_standards_compliant"] is True
        assert result["accessibility_compliant"] is True
        assert result["responsive_ready"] is True
        assert "design_system_compliant" in result

    def test_generate_ui_component_with_preferences(self) -> None:
        """Test UI component generation with user preferences."""
        specialist = UISpecialist()

        user_preferences = {
            "responsive": False,
            "dark_mode": True,
            "animations": True,
            "custom_styling": True,
            "props": {"validation": True},
            "styling": {"padding": "20px"},
        }

        result = specialist.generate_ui_component(
            component_name="TestForm",
            component_type=ComponentType.FORM,
            framework=UIFramework.VUE,
            design_system=DesignSystem.TAILWIND_UI,
            accessibility_level=AccessibilityLevel.AAA,
            user_preferences=user_preferences,
        )

        # Business logic: user preferences should be applied
        assert result["responsive_ready"] is False
        assert result["requirement"].responsive is False
        assert result["requirement"].dark_mode is True
        assert result["requirement"].animations is True
        assert result["requirement"].custom_styling is True

    def test_generate_ui_component_cost_optimization(self) -> None:
        """Test UI component generation with cost optimization."""
        specialist = UISpecialist()

        result = specialist.generate_ui_component(
            component_name="TestForm",
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA,
            cost_optimization=True,
        )

        # Business logic: cost optimization should be applied
        assert result["optimization_applied"] is True
        assert "token_reduction" in result["component"]
        assert result["component"]["token_reduction"] >= 0

    def test_generate_ui_component_no_optimization(self) -> None:
        """Test UI component generation without cost optimization."""
        specialist = UISpecialist()

        result = specialist.generate_ui_component(
            component_name="TestForm",
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA,
            cost_optimization=False,
        )

        # Business logic: cost optimization should not be applied
        assert result["optimization_applied"] is False
        assert "token_reduction" not in result["component"]

    def test_get_required_accessibility_features_aa(self) -> None:
        """Test getting required accessibility features for AA level."""
        specialist = UISpecialist()

        features = specialist._get_required_accessibility_features(AccessibilityLevel.AA)

        # Business logic: should return all AA level features
        expected_features = [
            "color_contrast_4_5",
            "keyboard_navigation",
            "focus_indicators",
            "screen_reader_support",
            "alt_text_for_images",
            "semantic_html",
        ]

        for feature in expected_features:
            assert feature in features

    def test_get_required_accessibility_features_minimal(self) -> None:
        """Test getting required accessibility features for minimal level."""
        specialist = UISpecialist()

        features = specialist._get_required_accessibility_features(AccessibilityLevel.MINIMAL)

        # Business logic: should return minimal features only
        expected_features = [
            "basic_keyboard_access",
            "alt_text_important",
            "semantic_structure",
        ]

        for feature in expected_features:
            assert feature in features
        assert len(features) == 3

    def test_get_supported_frameworks(self) -> None:
        """Test getting supported frameworks."""
        specialist = UISpecialist()

        frameworks = specialist.get_supported_frameworks()

        # Business logic: should return all framework values
        assert len(frameworks) == len(UIFramework)
        for framework in UIFramework:
            assert framework.value in frameworks

    def test_get_supported_component_types(self) -> None:
        """Test getting supported component types."""
        specialist = UISpecialist()

        types = specialist.get_supported_component_types()

        # Business logic: should return all component type values
        assert len(types) == len(ComponentType)
        for component_type in ComponentType:
            assert component_type.value in types

    def test_get_supported_design_systems(self) -> None:
        """Test getting supported design systems."""
        specialist = UISpecialist()

        systems = specialist.get_supported_design_systems()

        # Business logic: should return all design system values
        assert len(systems) == len(DesignSystem)
        for design_system in DesignSystem:
            assert design_system.value in systems

    def test_get_specialist_stats(self) -> None:
        """Test getting specialist statistics."""
        specialist = UISpecialist()

        stats = specialist.get_specialist_stats()

        # Business logic: should return comprehensive statistics
        assert "cache_size" in stats
        assert "supported_frameworks" in stats
        assert "supported_components" in stats
        assert "supported_design_systems" in stats
        assert "accessibility_levels" in stats

        assert stats["supported_frameworks"] == len(UIFramework)
        assert stats["supported_components"] == len(ComponentType)
        assert stats["supported_design_systems"] == len(DesignSystem)
        assert stats["accessibility_levels"] == len(AccessibilityLevel)

    def test_generate_component_complex_scenario(self) -> None:
        """Test component generation with complex requirements."""
        specialist = UISpecialist()

        user_preferences = {
            "responsive": True,
            "dark_mode": True,
            "animations": True,
            "props": {"validation": True, "auto_save": True},
            "styling": {"padding": "24px", "border_radius": "8px"},
        }

        result = specialist.generate_ui_component(
            component_name="ComplexDashboard",
            component_type=ComponentType.DASHBOARD,
            framework=UIFramework.NEXT_JS,
            design_system=DesignSystem.CHAKRA_UI,
            accessibility_level=AccessibilityLevel.AAA,
            user_preferences=user_preferences,
            cost_optimization=True,
        )

        # Business logic: complex scenario should handle all requirements
        assert result["industry_standards_compliant"] is True
        assert result["accessibility_compliant"] is True
        assert result["responsive_ready"] is True
        assert result["design_system_compliant"] is True
        assert result["component"]["token_estimate"] > 0

    def test_optimize_for_cost(self) -> None:
        """Test cost optimization functionality."""
        specialist = UISpecialist()

        generation_result = {
            "component_code": "<!-- Comment -->\n<div class='container'>\n  <p>Content</p>\n</div>\n<!-- End comment -->",
            "token_estimate": 100,
        }

        optimized = specialist._optimize_for_cost(generation_result)

        # Business logic: optimization should reduce tokens and remove comments
        assert optimized["token_estimate"] <= generation_result["token_estimate"]
        assert "<!--" not in optimized["component_code"]
        assert "-->" not in optimized["component_code"]
        assert "token_reduction" in optimized
        assert optimized["token_reduction"] > 0
