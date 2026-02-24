"""Tests for tool_router.ai.ui_specialist module."""

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

        assert hasattr(compliance, "wcag_guidelines")
        assert hasattr(compliance, "framework_best_practices")
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

        assert hasattr(generator, "templates")
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
        assert 'role="form"' in template
        assert 'className="form-container"' in template

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
        assert 'role="region"' in template
        assert 'aria-label="Data table"' in template
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
        assert 'role="img"' in template
        assert 'aria-label="Data visualization"' in template

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
        assert 'role="dialog"' in template
        assert 'aria-modal="true"' in template

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
        assert 'role="navigation"' in template
        assert 'aria-label="Main navigation"' in template
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
        assert 'role="article"' in template


class TestUISpecialist:
    """Test cases for UISpecialist."""

    def test_initialization(self):
        """Test UISpecialist initialization."""
        specialist = UISpecialist()

        assert hasattr(specialist, "compliance_checker")
        assert hasattr(specialist, "component_generator")
        assert hasattr(specialist, "_component_cache")
        assert isinstance(specialist._component_cache, dict)

    def test_generate_ui_component_basic(self):
        """Test basic UI component generation."""
        specialist = UISpecialist()

        result = specialist.generate_ui_component(
            component_name="TestButton",
            component_type=ComponentType.BUTTON,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        assert "component" in result
        assert "validation" in result
        assert "requirement" in result
        assert "spec" in result
        assert "optimization_applied" in result
        assert result["optimization_applied"] is True
        # These depend on validation scores, so we check they exist rather than specific values
        assert "industry_standards_compliant" in result
        assert "accessibility_compliant" in result
        assert "responsive_ready" in result
        assert "design_system_compliant" in result

    def test_generate_ui_component_with_preferences(self):
        """Test UI component generation with user preferences."""
        specialist = UISpecialist()

        user_preferences = {
            "responsive": False,
            "dark_mode": True,
            "animations": True,
            "custom_styling": True,
            "props": {"variant": "outlined"},
            "styling": {"margin": "16px"}
        }

        result = specialist.generate_ui_component(
            component_name="CustomCard",
            component_type=ComponentType.CARD,
            framework=UIFramework.VUE,
            design_system=DesignSystem.TAILWIND_UI,
            accessibility_level=AccessibilityLevel.AAA,
            user_preferences=user_preferences,
            cost_optimization=False
        )

        assert result["optimization_applied"] is False
        assert result["responsive_ready"] is False
        assert result["spec"].props == {"variant": "outlined"}
        assert result["spec"].styling == {"margin": "16px"}

    def test_get_required_accessibility_features_aa(self):
        """Test AA level accessibility features."""
        specialist = UISpecialist()

        features = specialist._get_required_accessibility_features(AccessibilityLevel.AA)

        assert "color_contrast_4_5" in features
        assert "keyboard_navigation" in features
        assert "focus_indicators" in features
        assert "screen_reader_support" in features
        assert "alt_text_for_images" in features
        assert "semantic_html" in features
        assert len(features) == 6

    def test_get_required_accessibility_features_aaa(self):
        """Test AAA level accessibility features."""
        specialist = UISpecialist()

        features = specialist._get_required_accessibility_features(AccessibilityLevel.AAA)

        assert "color_contrast_7_1" in features
        assert "no_reflow" in features
        assert "text_spacing" in features
        assert "pointer_gestures" in features
        assert "orientation" in features
        assert "color_contrast_4_5" in features  # AA features included
        assert len(features) == 11

    def test_get_required_accessibility_features_minimal(self):
        """Test minimal accessibility features."""
        specialist = UISpecialist()

        features = specialist._get_required_accessibility_features(AccessibilityLevel.MINIMAL)

        assert "basic_keyboard_access" in features
        assert "alt_text_important" in features
        assert "semantic_structure" in features
        assert len(features) == 3

    def test_optimize_for_cost(self):
        """Test cost optimization."""
        specialist = UISpecialist()

        generation_result = {
            "component_code": "<!-- Comment -->\n<div class='container'>\n  <p>Content</p>\n</div><!-- End -->",
            "token_estimate": 100
        }

        optimized = specialist._optimize_for_cost(generation_result)

        assert optimized["component_code"] == "<div class='container'> <p>Content</p>"
        assert optimized["token_estimate"] <= generation_result["token_estimate"]
        assert "token_reduction" in optimized
        assert optimized["token_reduction"] >= 0

    def test_optimize_for_cost_no_tokens(self):
        """Test cost optimization with zero tokens."""
        specialist = UISpecialist()

        generation_result = {
            "component_code": "<div>Test</div>",
            "token_estimate": 0
        }

        optimized = specialist._optimize_for_cost(generation_result)

        assert optimized["token_reduction"] == 0


    def test_get_specialist_stats(self):
        """Test getting specialist statistics."""
        specialist = UISpecialist()

        stats = specialist.get_specialist_stats()

        assert "cache_size" in stats
        assert "supported_frameworks" in stats
        assert "supported_components" in stats
        assert "supported_design_systems" in stats
        assert "accessibility_levels" in stats
        assert stats["supported_frameworks"] == 10
        assert stats["supported_components"] == 13



class TestComponentGeneratorAdditional:
    """Additional test cases for ComponentGenerator."""

    def test_generate_button_template(self):
        """Test button template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.BUTTON,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="SubmitButton",
            type=ComponentType.BUTTON,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_button_template(requirement, spec)

        assert "SubmitButton" in template
        assert 'type="button"' in template
        assert 'aria-label="SubmitButton"' in template

    def test_generate_input_template(self):
        """Test input template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.INPUT,
            framework=UIFramework.HTML_CSS,
            design_system=DesignSystem.BOOTSTRAP,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="EmailInput",
            type=ComponentType.INPUT,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_input_template(requirement, spec)

        assert "EmailInput" in template
        assert 'type="text"' in template
        assert 'aria-label="EmailInput"' in template

    def test_generate_layout_template(self):
        """Test layout template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.LAYOUT,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="MainLayout",
            type=ComponentType.LAYOUT,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_layout_template(requirement, spec)

        assert "MainLayout" in template
        assert "layout-header" in template
        assert "layout-main" in template
        assert "layout-footer" in template

    def test_generate_dashboard_template(self):
        """Test dashboard template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.DASHBOARD,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="AnalyticsDashboard",
            type=ComponentType.DASHBOARD,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_dashboard_template(requirement, spec)

        assert "AnalyticsDashboard" in template
        assert 'role="main"' in template
        assert "dashboard-grid" in template

    def test_generate_landing_template(self):
        """Test landing page template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.LANDING,
            framework=UIFramework.HTML_CSS,
            design_system=DesignSystem.BOOTSTRAP,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="ProductLanding",
            type=ComponentType.LANDING,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_landing_template(requirement, spec)

        assert "ProductLanding" in template
        assert "hero" in template
        assert "features" in template
        assert "cta" in template

    def test_generate_auth_template(self):
        """Test authentication template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.AUTH,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="LoginForm",
            type=ComponentType.AUTH,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_auth_template(requirement, spec)

        assert "LoginForm" in template
        assert 'role="main"' in template
        assert "auth-form" in template

    def test_generate_settings_template(self):
        """Test settings template generation."""
        generator = ComponentGenerator()

        requirement = UIRequirement(
            component_type=ComponentType.SETTINGS,
            framework=UIFramework.VUE,
            design_system=DesignSystem.TAILWIND_UI,
            accessibility_level=AccessibilityLevel.AA
        )

        spec = ComponentSpec(
            name="UserSettings",
            type=ComponentType.SETTINGS,
            props={},
            styling={},
            accessibility_features=[],
            responsive_breakpoints=[]
        )

        template = generator._generate_settings_template(requirement, spec)

        assert "UserSettings" in template
        assert 'role="main"' in template
        assert "settings-form" in template

    def test_apply_framework_enhancements_react(self):
        """Test React framework enhancements."""
        generator = ComponentGenerator()

        code = "<!-- React comment -->"
        enhanced = generator._apply_framework_enhancements(code, UIFramework.REACT)

        assert enhanced == "{/* React comment */}"

    def test_apply_framework_enhancements_vue(self):
        """Test Vue framework enhancements."""
        generator = ComponentGenerator()

        code = "<!-- Vue comment -->"
        enhanced = generator._apply_framework_enhancements(code, UIFramework.VUE)

        assert enhanced == "<!-- Vue comment -->"

    def test_apply_framework_enhancements_default(self):
        """Test default framework enhancements."""
        generator = ComponentGenerator()

        code = "<!-- Default comment -->"
        enhanced = generator._apply_framework_enhancements(code, UIFramework.SVELTE)

        assert enhanced == "<!-- Default comment -->"

    def test_apply_accessibility_features_aa(self):
        """Test AA accessibility features."""
        generator = ComponentGenerator()

        code = "<div>Content</div>"
        enhanced = generator._apply_accessibility_features(code, AccessibilityLevel.AA)

        # Should return unchanged (implementation placeholder)
        assert enhanced == code

    def test_apply_accessibility_features_aaa(self):
        """Test AAA accessibility features."""
        generator = ComponentGenerator()

        code = "<div>Content</div>"
        enhanced = generator._apply_accessibility_features(code, AccessibilityLevel.AAA)

        # Should return unchanged (implementation placeholder)
        assert enhanced == code

    def test_apply_accessibility_features_minimal(self):
        """Test minimal accessibility features."""
        generator = ComponentGenerator()

        code = "<div>Content</div>"
        enhanced = generator._apply_accessibility_features(code, AccessibilityLevel.MINIMAL)

        # Should return unchanged (implementation placeholder)
        assert enhanced == code

    def test_apply_responsive_design_true(self):
        """Test responsive design application when enabled."""
        generator = ComponentGenerator()

        code = '<div class="container">Content</div>'
        enhanced = generator._apply_responsive_design(code, True)

        assert enhanced == '<div class="responsive-container">Content</div>'

    def test_apply_responsive_design_false(self):
        """Test responsive design application when disabled."""
        generator = ComponentGenerator()

        code = '<div class="container">Content</div>'
        enhanced = generator._apply_responsive_design(code, False)

        assert enhanced == code

    def test_apply_styling_tailwind(self):
        """Test Tailwind styling application."""
        generator = ComponentGenerator()

        code = '<div class="container">Content</div>'
        enhanced = generator._apply_styling(code, DesignSystem.TAILWIND_UI, False)

        assert enhanced == '<div class="tw-container">Content</div>'

    def test_apply_styling_material(self):
        """Test Material Design styling application."""
        generator = ComponentGenerator()

        code = '<div class="container">Content</div>'
        enhanced = generator._apply_styling(code, DesignSystem.MATERIAL_DESIGN, False)

        assert enhanced == '<div class="md-container">Content</div>'

    def test_apply_styling_bootstrap(self):
        """Test Bootstrap styling application."""
        generator = ComponentGenerator()

        code = '<div class="container">Content</div>'
        enhanced = generator._apply_styling(code, DesignSystem.BOOTSTRAP, False)

        assert enhanced == '<div class="bs-container">Content</div>'

    def test_apply_styling_dark_mode(self):
        """Test dark mode styling application."""
        generator = ComponentGenerator()

        code = '<div class="container">Content</div>'
        enhanced = generator._apply_styling(code, DesignSystem.MATERIAL_DESIGN, True)

        assert enhanced == '<div class="dark-md-container">Content</div>'

    def test_extract_features(self):
        """Test feature extraction from code."""
        generator = ComponentGenerator()

        code = '<div role="main" aria-label="main" class="responsive-dark-container">Content</div>'
        features = generator._extract_features(code)

        assert "semantic_roles" in features
        assert "aria_labels" in features
        assert "responsive_design" in features
        assert "dark_mode" in features

    def test_extract_features_empty(self):
        """Test feature extraction from code with no features."""
        generator = ComponentGenerator()

        code = '<div class="container">Content</div>'
        features = generator._extract_features(code)

        assert features == []

    def test_estimate_component_tokens(self):
        """Test component token estimation."""
        generator = ComponentGenerator()

        code = "div class container Content"
        tokens = generator._estimate_component_tokens(code)

        assert tokens == len(code.split()) * 1.3
        assert tokens == 5.2


class TestComponentGeneratorAdvanced:
    """Test advanced ComponentGenerator functionality."""

    def test_generate_component_all_types(self) -> None:
        """Test component generation for all component types."""
        generator = ComponentGenerator()
        requirement = UIRequirement(
            component_type=ComponentType.BUTTON,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        # Test each component type
        for component_type in ComponentType:
            if component_type in generator.templates:
                spec = ComponentSpec(
                    name=f"Test{component_type.value.title()}",
                    type=component_type,
                    props={},
                    styling={},
                    accessibility_features=[],
                    responsive_breakpoints=[]
                )

                result = generator.generate_component(requirement, spec)
                assert isinstance(result, dict)
                assert "component_code" in result
                assert "token_estimate" in result


class TestComponentGeneratorAdvanced:
    """Test advanced ComponentGenerator functionality."""

    def test_generate_component_all_types(self) -> None:
        """Test component generation for all component types."""
        generator = ComponentGenerator()
        requirement = UIRequirement(
            component_type=ComponentType.BUTTON,
            framework=UIFramework.REACT,
            design_system=DesignSystem.MATERIAL_DESIGN,
            accessibility_level=AccessibilityLevel.AA
        )

        # Test each component type
        for component_type in ComponentType:
            if component_type in generator.templates:
                spec = ComponentSpec(
                    name=f"Test{component_type.value.title()}",
                    type=component_type,
                    props={},
                    styling={},
                    accessibility_features=[],
                    responsive_breakpoints=[]
                )

                result = generator.generate_component(requirement, spec)
                assert isinstance(result, dict)
                assert "component_code" in result
                assert "token_estimate" in result

    def test_generate_component_vue_framework(self) -> None:
        """Test component generation for Vue framework."""
        generator = ComponentGenerator()
        requirement = UIRequirement(
            component_type=ComponentType.FORM,
            framework=UIFramework.VUE,
            design_system=DesignSystem.VUE_UI,
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
        assert isinstance(result, dict)
        assert "component_code" in result
        assert "token_estimate" in result
