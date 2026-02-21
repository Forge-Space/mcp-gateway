"""Tests for tool_router.ai.ui_specialist module."""

from __future__ import annotations

import pytest

from tool_router.ai.ui_specialist import (
    UIFramework,
    DesignSystem,
    ComponentType,
    AccessibilityLevel,
    UIRequirement,
    ComponentSpec,
    UIStandardsCompliance,
    ComponentGenerator,
)


class TestUIFramework:
    """Test cases for UIFramework enum."""

    def test_ui_framework_values(self):
        """Test that UIFramework has expected values."""
        assert UIFramework.REACT.value == "react"
        assert UIFramework.VUE.value == "vue"
        assert UIFramework.ANGULAR.value == "angular"
        assert UIFramework.SVELTE.value == "svelte"
        assert UIFramework.NEXT_JS.value == "nextjs"
        assert UIFramework.HTML_CSS.value == "html_css"
        assert UIFramework.TAILWIND.value == "tailwind"
        assert UIFramework.BOOTSTRAP.value == "bootstrap"
        assert UIFramework.MATERIAL_UI.value == "material_ui"
        assert UIFramework.CHAKRA_UI.value == "chakra_ui"

    def test_ui_framework_count(self):
        """Test number of UI frameworks."""
        assert len(UIFramework) == 10


class TestDesignSystem:
    """Test cases for DesignSystem enum."""

    def test_design_system_values(self):
        """Test that DesignSystem has expected values."""
        assert DesignSystem.MATERIAL_DESIGN.value == "material_design"
        assert DesignSystem.ANT_DESIGN.value == "ant_design"
        assert DesignSystem.BOOTSTRAP.value == "bootstrap"
        assert DesignSystem.TAILWIND_UI.value == "tailwind_ui"
        assert DesignSystem.CHAKRA_UI.value == "chakra_ui"
        assert DesignSystem.MANTINE.value == "mantine"
        assert DesignSystem.SEMANTIC_UI.value == "semantic_ui"
        assert DesignSystem.CUSTOM.value == "custom"

    def test_design_system_count(self):
        """Test number of design systems."""
        assert len(DesignSystem) == 8


class TestComponentType:
    """Test cases for ComponentType enum."""

    def test_component_type_values(self):
        """Test that ComponentType has expected values."""
        assert ComponentType.FORM.value == "form"
        assert ComponentType.TABLE.value == "table"
        assert ComponentType.CHART.value == "chart"
        assert ComponentType.MODAL.value == "modal"
        assert ComponentType.NAVIGATION.value == "navigation"
        assert ComponentType.CARD.value == "card"
        assert ComponentType.BUTTON.value == "button"
        assert ComponentType.INPUT.value == "input"
        assert ComponentType.LAYOUT.value == "layout"
        assert ComponentType.DASHBOARD.value == "dashboard"
        assert ComponentType.LANDING.value == "landing"
        assert ComponentType.AUTH.value == "auth"
        assert ComponentType.SETTINGS.value == "settings"

    def test_component_type_count(self):
        """Test number of component types."""
        assert len(ComponentType) == 13


class TestAccessibilityLevel:
    """Test cases for AccessibilityLevel enum."""

    def test_accessibility_level_values(self):
        """Test that AccessibilityLevel has expected values."""
        assert AccessibilityLevel.AA.value == "aa"
        assert AccessibilityLevel.AAA.value == "aaa"
        assert AccessibilityLevel.MINIMAL.value == "minimal"

    def test_accessibility_level_count(self):
        """Test number of accessibility levels."""
        assert len(AccessibilityLevel) == 3


class TestUIRequirement:
    """Test cases for UIRequirement dataclass."""

    def test_ui_requirement_creation(self):
        """Test UIRequirement creation with all fields."""
        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA,
            responsive=True,
            dark_mode=False,
            animations=True,
            custom_styling=True
        )

        assert requirement.component_type == ComponentType.FORM
        assert requirement.framework == UIFramework.REACT
        assert requirement.design_system == DesignSystem.MATERIAL_DESIGN
        assert requirement.accessibility_level == AccessibilityLevel.AA
        assert requirement.responsive is True
        assert requirement.dark_mode is False
        assert requirement.animations is True
        assert requirement.custom_styling is True

    def test_ui_requirement_defaults(self):
        """Test UIRequirement with default values."""
        requirement = UIRequirement(
            component_type=ComponentType.BUTTON,
            framework=UIFramework.VUE,
            design_system=DesignSystem.TAILWIND_UI,
            accessibility_level=AccessibilityLevel.MINIMAL
        )

        assert requirement.responsive is True  # Default
        assert requirement.dark_mode is False  # Default
        assert requirement.animations is False  # Default
        assert requirement.custom_styling is False  # Default


class TestComponentSpec:
    """Test cases for ComponentSpec dataclass."""

    def test_component_spec_creation(self):
        """Test ComponentSpec creation."""
        spec = ComponentSpec(
            name="LoginForm",
            type=ComponentType.FORM,
            props={"username": "string", "password": "string"},
            styling={"padding": "16px", "borderRadius": "8px"},
            accessibility_features=["keyboard_navigation", "focus_indicators"],
            responsive_breakpoints=["mobile", "tablet", "desktop"]
        )

        assert spec.name == "LoginForm"
        assert spec.type == ComponentType.FORM
        assert spec.props == {"username": "string", "password": "string"}
        assert spec.styling == {"padding": "16px", "borderRadius": "8px"}
        assert spec.accessibility_features == ["keyboard_navigation", "focus_indicators"]
        assert spec.responsive_breakpoints == ["mobile", "tablet", "desktop"]


class TestUIStandardsCompliance:
    """Test cases for UIStandardsCompliance."""

    def test_initialization(self):
        """Test UIStandardsCompliance initialization."""
        compliance = UIStandardsCompliance()

        assert hasattr(compliance, 'wcag_guidelines')
        assert hasattr(compliance, 'framework_best_practices')
        assert AccessibilityLevel.AA in compliance.wcag_guidelines
        assert AccessibilityLevel.AAA in compliance.wcag_guidelines
        assert AccessibilityLevel.MINIMAL in compliance.wcag_guidelines
        assert UIFramework.REACT in compliance.framework_best_practices
        assert UIFramework.VUE in compliance.framework_best_practices
        assert UIFramework.ANGULAR in compliance.framework_best_practices

    def test_wcag_guidelines_content(self):
        """Test WCAG guidelines content."""
        compliance = UIStandardsCompliance()

        aa_guidelines = compliance.wcag_guidelines[AccessibilityLevel.AA]
        assert "color_contrast_4_5" in aa_guidelines
        assert "keyboard_navigation" in aa_guidelines
        assert "focus_indicators" in aa_guidelines
        assert "screen_reader_support" in aa_guidelines
        assert "alt_text_for_images" in aa_guidelines
        assert "semantic_html" in aa_guidelines

        aaa_guidelines = compliance.wcag_guidelines[AccessibilityLevel.AAA]
        assert "color_contrast_7_1" in aaa_guidelines
        assert "no_reflow" in aaa_guidelines
        assert "text_spacing" in aaa_guidelines
        assert "pointer_gestures" in aaa_guidelines
        assert "orientation" in aaa_guidelines

    def test_framework_best_practices_content(self):
        """Test framework best practices content."""
        compliance = UIStandardsCompliance()

        react_practices = compliance.framework_best_practices[UIFramework.REACT]
        assert "functional_components" in react_practices
        assert "hooks_usage" in react_practices
        assert "prop_types" in react_practices
        assert "accessibility_attrs" in react_practices
        assert "error_boundaries" in react_practices

        vue_practices = compliance.framework_best_practices[UIFramework.VUE]
        assert "composition_api" in vue_practices
        assert "template_syntax" in vue_practices
        assert "props_validation" in vue_practices
        assert "accessibility_directives" in vue_practices

    def test_validate_component_complete(self):
        """Test complete component validation."""
        compliance = UIStandardsCompliance()

        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA,
            responsive=True
        )

        spec = ComponentSpec(
            name="TestForm",
            type=ComponentType.FORM,
            props={"functional_components": "enabled"},
            styling={"material": "true"},
            accessibility_features=["color_contrast_4_5", "keyboard_navigation"],
            responsive_breakpoints=["mobile", "desktop"]
        )

        result = compliance.validate_component(spec, requirement)

        assert "compliance_score" in result
        assert "accessibility_score" in result
        assert "framework_score" in result
        assert "responsive_score" in result
        assert "design_score" in result
        assert "issues" in result
        assert "recommendations" in result
        assert 0.0 <= result["compliance_score"] <= 1.0

    def test_validate_component_minimal_accessibility(self):
        """Test component validation with minimal accessibility."""
        compliance = UIStandardsCompliance()

        requirement = UIRequirement(
            component_type=ComponentType.BUTTON,
            framework=UIFramework.VUE,
            design_system=DesignSystem.TAILWIND_UI,
            accessibility_level=AccessibilityLevel.MINIMAL,
            responsive=False
        )

        spec = ComponentSpec(
            name="TestButton",
            type=ComponentType.BUTTON,
            props={"composition_api": "enabled"},
            styling={"tailwind": "true"},
            accessibility_features=["basic_keyboard_access"],
            responsive_breakpoints=[]
        )

        result = compliance.validate_component(spec, requirement)

        assert result["accessibility_score"] > 0.0
        assert result["framework_score"] > 0.0
        assert result["responsive_score"] == 1.0  # Not required

    def test_check_accessibility_compliance_perfect(self):
        """Test perfect accessibility compliance."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[
                "color_contrast_4_5",
                "keyboard_navigation",
                "focus_indicators",
                "screen_reader_support",
                "alt_text_for_images",
                "semantic_html"
            ],
            responsive_breakpoints=[]
        )

        score = compliance._check_accessibility_compliance(spec, AccessibilityLevel.AA)
        assert score == 1.0

    def test_check_accessibility_compliance_partial(self):
        """Test partial accessibility compliance."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=["color_contrast_4_5", "keyboard_navigation"],  # Only 2 of 6
            responsive_breakpoints=[]
        )

        score = compliance._check_accessibility_compliance(spec, AccessibilityLevel.AA)
        assert score == 2.0 / 6.0

    def test_check_accessibility_compliance_empty(self):
        """Test accessibility compliance with empty required features."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        score = compliance._check_accessibility_compliance(spec, AccessibilityLevel.MINIMAL)
        assert score == 0.0  # No features present, so 0 compliance

    def test_check_framework_compliance_react(self):
        """Test React framework compliance."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={"functional_components": "enabled"},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        score = compliance._check_framework_compliance(spec, UIFramework.REACT)
        assert score == 0.9

    def test_check_framework_compliance_react_missing(self):
        """Test React framework compliance missing best practices."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},  # Missing functional_components
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        score = compliance._check_framework_compliance(spec, UIFramework.REACT)
        assert score == 0.7

    def test_check_framework_compliance_vue(self):
        """Test Vue framework compliance."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={"composition_api": "enabled"},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        score = compliance._check_framework_compliance(spec, UIFramework.VUE)
        assert score == 0.9

    def test_check_framework_compliance_angular(self):
        """Test Angular framework compliance."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={"standalone_components": "enabled"},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        score = compliance._check_framework_compliance(spec, UIFramework.ANGULAR)
        assert score == 0.9

    def test_check_framework_compliance_unknown(self):
        """Test unknown framework compliance."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        score = compliance._check_framework_compliance(spec, UIFramework.SVELTE)
        assert score == 0.8  # Default score

    def test_check_responsive_compliance_required(self):
        """Test responsive compliance when required."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=["mobile", "tablet", "desktop"]
        )

        score = compliance._check_responsive_compliance(spec, True)
        assert score == 1.0

    def test_check_responsive_compliance_required_missing(self):
        """Test responsive compliance when required but missing breakpoints."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        score = compliance._check_responsive_compliance(spec, True)
        assert score == 0.6  # Partial credit

    def test_check_responsive_compliance_not_required(self):
        """Test responsive compliance when not required."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        score = compliance._check_responsive_compliance(spec, False)
        assert score == 1.0

    def test_check_design_system_compliance_tailwind(self):
        """Test Tailwind design system compliance."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={"tailwind": "true"},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        score = compliance._check_design_system_compliance(spec, DesignSystem.TAILWIND_UI)
        assert score == 0.9

    def test_check_design_system_compliance_material(self):
        """Test Material design system compliance."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={"material": "true"},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        score = compliance._check_design_system_compliance(spec, DesignSystem.MATERIAL_DESIGN)
        assert score == 0.9

    def test_check_design_system_compliance_bootstrap(self):
        """Test Bootstrap design system compliance."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={"bootstrap": "true"},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        score = compliance._check_design_system_compliance(spec, DesignSystem.BOOTSTRAP)
        assert score == 0.9

    def test_check_design_system_compliance_unknown(self):
        """Test unknown design system compliance."""
        compliance = UIStandardsCompliance()

        spec = ComponentSpec(
            name="TestComponent",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        score = compliance._check_design_system_compliance(spec, DesignSystem.CUSTOM)
        assert score == 0.8  # Default score


class TestComponentGenerator:
    """Test cases for ComponentGenerator."""

    def test_initialization(self):
        """Test ComponentGenerator initialization."""
        generator = ComponentGenerator()

        assert hasattr(generator, 'templates')
        assert ComponentType.FORM in generator.templates
        assert ComponentType.TABLE in generator.templates
        assert ComponentType.CHART in generator.templates
        assert ComponentType.MODAL in generator.templates
        assert ComponentType.NAVIGATION in generator.templates
        assert ComponentType.CARD in generator.templates
        assert ComponentType.BUTTON in generator.templates
        assert ComponentType.INPUT in generator.templates
        assert ComponentType.LAYOUT in generator.templates
        assert ComponentType.DASHBOARD in generator.templates
        assert ComponentType.LANDING in generator.templates
        assert ComponentType.AUTH in generator.templates
        assert ComponentType.SETTINGS in generator.templates

    def test_generate_component_form_react(self):
        """Test generating a React form component."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="LoginForm",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        result = generator.generate_component(requirement, spec)

        assert "component_code" in result
        assert "component_spec" in result
        assert "requirement" in result
        assert "generated_features" in result
        assert "token_estimate" in result
        assert "LoginForm" in result["component_code"]
        assert "import React" in result["component_code"]
        assert "useForm" in result["component_code"]

    def test_generate_component_unsupported_type(self):
        """Test generating component with unsupported type."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        # Create spec with invalid type by manually setting
        spec = ComponentSpec(
            name="InvalidComponent",
            type=ComponentType.FORM,  # Valid type but we'll mock the templates dict
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        # Temporarily remove the form template to test error handling
        original_template = generator.templates[ComponentType.FORM]
        del generator.templates[ComponentType.FORM]

        with pytest.raises(ValueError, match="Unsupported component type"):
            generator.generate_component(requirement, spec)

        # Restore template
        generator.templates[ComponentType.FORM] = original_template

    def test_generate_form_template_react(self):
        """Test React form template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="ContactForm",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_form_template(requirement, spec)

        assert "ContactForm" in template
        assert "import React" in template
        assert "useForm" in template
        assert "role=\"form\"" in template
        assert "className=\"form-container\"" in template

    def test_generate_form_template_non_react(self):
        """Test form template generation for non-React framework."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.VUE,  # Not React
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="ContactForm",
            type=ComponentType.FORM,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_form_template(requirement, spec)

        assert "ContactForm" in template
        assert "<!-- Form component for ContactForm -->" in template

    def test_generate_table_template(self):
        """Test table template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.TABLE,
            framework=UIFramework.HTML_CSS,
            design_system=DesignSystem.BOOTSTRAP,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="DataTable",
            type=ComponentType.TABLE,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_table_template(requirement, spec)

        assert "DataTable" in template
        assert "role=\"region\"" in template
        assert "aria-label=\"Data table\"" in template
        assert "<table" in template
        assert "<thead>" in template
        assert "<tbody>" in template

    def test_generate_chart_template(self):
        """Test chart template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.CHART,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="SalesChart",
            type=ComponentType.CHART,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_chart_template(requirement, spec)

        assert "SalesChart" in template
        assert "role=\"img\"" in template
        assert "aria-label=\"Data visualization\"" in template

    def test_generate_modal_template(self):
        """Test modal template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.MODAL,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="ConfirmDialog",
            type=ComponentType.MODAL,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_modal_template(requirement, spec)

        assert "ConfirmDialog" in template
        assert "role=\"dialog\"" in template
        assert "aria-modal=\"true\"" in template

    def test_generate_navigation_template(self):
        """Test navigation template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.NAVIGATION,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="MainMenu",
            type=ComponentType.NAVIGATION,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_navigation_template(requirement, spec)

        assert "MainMenu" in template
        assert "role=\"navigation\"" in template
        assert "aria-label=\"Main navigation\"" in template
        assert "<nav " in template

    def test_generate_card_template(self):
        """Test card template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.CARD,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="ProfileCard",
            type=ComponentType.CARD,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_card_template(requirement, spec)

        assert "ProfileCard" in template
        assert "role=\"article\"" in template
