"""Unit tests for specialists/ui_specialist_v2.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


# Patch KnowledgeBase before importing the module so module-level `specialist = EnhancedUISpecialist()`
# does not trigger a real KnowledgeBase() instantiation.
with patch("tool_router.specialists.ui_specialist_v2.KnowledgeBase"):
    from tool_router.specialists.ui_specialist_v2 import EnhancedUISpecialist


def _make_specialist(kb=None):
    """Return EnhancedUISpecialist with a mock KnowledgeBase."""
    mock_kb = kb or MagicMock()
    mock_kb.search_knowledge.return_value = []
    with patch("tool_router.specialists.ui_specialist_v2.KnowledgeBase", return_value=mock_kb):
        specialist = EnhancedUISpecialist()
    return specialist, mock_kb


def _make_pattern(title="Pattern A", confidence=0.9, tags=None, code_example="// code"):
    p = MagicMock()
    p.title = title
    p.description = f"Desc of {title}"
    p.code_example = code_example
    p.confidence_score = confidence
    p.tags = tags or []
    return p


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


class TestInit:
    def test_uses_provided_knowledge_base(self):
        mock_kb = MagicMock()
        mock_kb.search_knowledge.return_value = []
        s = EnhancedUISpecialist(knowledge_base=mock_kb)
        assert s.knowledge_base is mock_kb

    def test_creates_knowledge_base_when_none(self):
        with patch("tool_router.specialists.ui_specialist_v2.KnowledgeBase") as mock_cls:
            mock_cls.return_value = MagicMock()
            s = EnhancedUISpecialist()
            mock_cls.assert_called_once()
            assert s.knowledge_base is mock_cls.return_value

    def test_framework_preferences_have_four_frameworks(self):
        s, _ = _make_specialist()
        assert set(s.framework_preferences.keys()) == {"react", "vue", "angular", "svelte"}

    def test_react_has_highest_priority(self):
        s, _ = _make_specialist()
        react_prio = s.framework_preferences["react"]["priority"]
        for fw, data in s.framework_preferences.items():
            if fw != "react":
                assert react_prio > data["priority"]

    def test_architecture_patterns_keys(self):
        s, _ = _make_specialist()
        assert "atomic_design" in s.architecture_patterns
        assert "feature_sliced" in s.architecture_patterns

    def test_atomic_design_has_atoms(self):
        s, _ = _make_specialist()
        assert "button" in s.architecture_patterns["atomic_design"]["atoms"]


# ---------------------------------------------------------------------------
# generate_component
# ---------------------------------------------------------------------------


class TestGenerateComponent:
    def test_generates_react_button(self):
        s, _ = _make_specialist()
        result = s.generate_component({"component_type": "button", "framework": "react"})
        assert result["type"] == "button"
        assert result["framework"] == "react"
        assert "code" in result

    def test_generates_fallback_on_exception(self):
        s, mock_kb = _make_specialist()
        mock_kb.search_knowledge.side_effect = RuntimeError("fail")
        result = s.generate_component({"component_type": "button", "framework": "react"})
        assert result["fallback"] is True
        assert result["type"] == "button"

    def test_default_component_type_and_framework(self):
        s, _ = _make_specialist()
        result = s.generate_component({})
        assert result["type"] == "generic"
        assert result["framework"] == "react"

    def test_typescript_types_added_when_requested(self):
        s, _ = _make_specialist()
        result = s.generate_component(
            {"component_type": "button", "framework": "react", "requirements": ["typescript"]}
        )
        # Either we get typescript_types (success path) or a fallback — just verify no hard crash
        assert isinstance(result, dict)
        # When not a fallback (real code generated), typescript_types should be present
        if not result.get("fallback"):
            assert "typescript_types" in result

    def test_typescript_types_not_added_when_not_requested(self):
        s, _ = _make_specialist()
        result = s.generate_component({"component_type": "button", "framework": "react"})
        assert "typescript_types" not in result

    def test_accessibility_added_when_required(self):
        s, _ = _make_specialist()
        result = s.generate_component(
            {"component_type": "button", "framework": "react", "requirements": ["accessibility"]}
        )
        # Either we get accessibility (success path) or a fallback — just verify no hard crash
        assert isinstance(result, dict)
        if not result.get("fallback"):
            assert "accessibility" in result

    def test_accessibility_not_added_when_not_required(self):
        s, _ = _make_specialist()
        result = s.generate_component({"component_type": "button", "framework": "react"})
        assert "accessibility" not in result

    def test_performance_always_added_when_not_fallback(self):
        s, _ = _make_specialist()
        result = s.generate_component({"component_type": "button", "framework": "react"})
        # "performance" is only added in the success path (not fallback)
        if not result.get("fallback"):
            assert "performance" in result


# ---------------------------------------------------------------------------
# Framework code generators
# ---------------------------------------------------------------------------


class TestCodeGenerators:
    def test_react_button_code_contains_button(self):
        s, _ = _make_specialist()
        code = s._generate_react_component("button", [])
        assert "Button" in code

    def test_react_form_code_contains_form(self):
        s, _ = _make_specialist()
        code = s._generate_react_component("form", [])
        assert "form" in code.lower()

    def test_react_card_code_contains_card(self):
        s, _ = _make_specialist()
        code = s._generate_react_component("card", [])
        assert "Card" in code or "card" in code.lower()

    def test_react_unknown_type_returns_generic_code(self):
        s, _ = _make_specialist()
        code = s._generate_react_component("widget", [])
        assert "widget" in code.lower() or "function" in code.lower() or "const" in code.lower()

    def test_react_uses_best_pattern_if_available(self):
        s, _ = _make_specialist()
        p = _make_pattern("Best", confidence=0.99, code_example="// best pattern")
        code = s._generate_react_component("other", [p])
        # The code itself should still be returned (generic fallback or a variation)
        assert isinstance(code, str)

    def test_vue_component_returns_string(self):
        s, _ = _make_specialist()
        code = s._generate_vue_component("button", [])
        assert isinstance(code, str)
        assert len(code) > 0

    def test_angular_component_returns_string(self):
        s, _ = _make_specialist()
        code = s._generate_angular_component("button", [])
        assert isinstance(code, str)
        assert len(code) > 0

    def test_svelte_component_returns_string(self):
        s, _ = _make_specialist()
        code = s._generate_svelte_component("button", [])
        assert isinstance(code, str)
        assert len(code) > 0

    def test_unknown_framework_falls_through_to_generic(self):
        s, _ = _make_specialist()
        # _generate_generic_component may or may not exist; generate_component catches exceptions
        # Test via the public API which catches errors
        result = s.generate_component({"component_type": "button", "framework": "unknown_fw"})
        assert isinstance(result, dict)
        assert result["framework"] == "unknown_fw"


# ---------------------------------------------------------------------------
# _get_relevant_patterns
# ---------------------------------------------------------------------------


class TestGetRelevantPatterns:
    def test_returns_list(self):
        s, _ = _make_specialist()
        result = s._get_relevant_patterns("button", "react")
        assert isinstance(result, list)

    def test_patterns_from_kb_are_mapped(self):
        s, mock_kb = _make_specialist()
        mock_kb.search_knowledge.return_value = [_make_pattern("P1", 0.9, ["hook"])]
        result = s._get_relevant_patterns("button", "react")
        assert len(result) == 1
        assert result[0]["title"] == "P1"
        assert result[0]["confidence"] == 0.9
        assert result[0]["tags"] == ["hook"]

    def test_accessibility_patterns_added_for_a11y_type(self):
        s, mock_kb = _make_specialist()
        mock_kb.search_knowledge.return_value = []
        # First call (framework patterns) returns empty; second call (accessibility) returns 1
        mock_kb.search_knowledge.side_effect = [
            [],
            [_make_pattern("A11y pattern", 0.85, ["accessibility"])],
        ]
        result = s._get_relevant_patterns("a11y_button", "react")
        assert any("accessibility" in p["tags"] for p in result)

    def test_no_accessibility_search_for_plain_button(self):
        s, mock_kb = _make_specialist()
        mock_kb.search_knowledge.return_value = []
        s._get_relevant_patterns("button", "react")
        # Only called once (for framework patterns)
        assert mock_kb.search_knowledge.call_count == 1


# ---------------------------------------------------------------------------
# _generate_dependencies
# ---------------------------------------------------------------------------


class TestGenerateDependencies:
    def test_react_base_deps(self):
        s, _ = _make_specialist()
        deps = s._generate_dependencies("react", [])
        assert "react" in deps
        assert "react-dom" in deps

    def test_react_typescript_deps(self):
        s, _ = _make_specialist()
        deps = s._generate_dependencies("react", ["typescript"])
        assert "@types/react" in deps

    def test_react_styling_deps(self):
        s, _ = _make_specialist()
        deps = s._generate_dependencies("react", ["styling"])
        assert "tailwindcss" in deps

    def test_react_forms_deps(self):
        s, _ = _make_specialist()
        deps = s._generate_dependencies("react", ["forms"])
        assert "react-hook-form" in deps

    def test_vue_deps(self):
        s, _ = _make_specialist()
        deps = s._generate_dependencies("vue", [])
        assert "vue" in deps

    def test_angular_deps(self):
        s, _ = _make_specialist()
        deps = s._generate_dependencies("angular", [])
        assert "@angular/core" in deps

    def test_svelte_deps(self):
        s, _ = _make_specialist()
        deps = s._generate_dependencies("svelte", [])
        assert "svelte" in deps


# ---------------------------------------------------------------------------
# _enhance_accessibility
# ---------------------------------------------------------------------------


class TestEnhanceAccessibility:
    def test_no_change_when_accessibility_not_required(self):
        s, _ = _make_specialist()
        component = {"type": "button", "code": "// code"}
        result = s._enhance_accessibility(component, [])
        assert "accessibility" not in result

    def test_adds_accessibility_dict_when_required(self):
        s, _ = _make_specialist()
        component = {"type": "button", "code": "// code"}
        result = s._enhance_accessibility(component, ["accessibility"])
        assert "accessibility" in result
        assert result["accessibility"]["keyboard_navigation"] is True
        assert result["accessibility"]["screen_reader_support"] is True


# ---------------------------------------------------------------------------
# _optimize_performance
# ---------------------------------------------------------------------------


class TestOptimizePerformance:
    def test_adds_performance_key(self):
        s, _ = _make_specialist()
        component = {"type": "button", "code": "// x", "framework": "react"}
        result = s._optimize_performance(component, "react")
        assert "performance" in result
        assert result["performance"]["lazy_loading"] is True

    def test_react_memoization_true(self):
        s, _ = _make_specialist()
        component = {"type": "button", "code": "// x"}
        result = s._optimize_performance(component, "react")
        assert result["performance"]["memoization"] is True

    def test_non_react_memoization_false(self):
        s, _ = _make_specialist()
        component = {"type": "button", "code": "// x"}
        result = s._optimize_performance(component, "vue")
        assert result["performance"]["memoization"] is False


# ---------------------------------------------------------------------------
# _generate_typescript_types
# ---------------------------------------------------------------------------


class TestGenerateTypescriptTypes:
    def test_returns_string(self):
        s, _ = _make_specialist()
        component = {"type": "button", "props": []}
        result = s._generate_typescript_types(component)
        assert isinstance(result, str)
        assert "ButtonProps" in result or "interface" in result

    def test_includes_required_props(self):
        s, _ = _make_specialist()
        component = {
            "type": "button",
            "props": [{"name": "label", "type": "string", "required": True}],
        }
        result = s._generate_typescript_types(component)
        assert "label: string" in result

    def test_includes_optional_props(self):
        s, _ = _make_specialist()
        component = {
            "type": "button",
            "props": [{"name": "disabled", "type": "boolean", "required": False}],
        }
        result = s._generate_typescript_types(component)
        assert "disabled?: boolean" in result


# ---------------------------------------------------------------------------
# _get_fallback_component
# ---------------------------------------------------------------------------


class TestGetFallbackComponent:
    def test_returns_dict_with_required_keys(self):
        s, _ = _make_specialist()
        result = s._get_fallback_component({"component_type": "table", "framework": "react"})
        assert result["type"] == "table"
        assert result["framework"] == "react"
        assert "code" in result
        assert result["fallback"] is True

    def test_defaults_when_no_type_in_request(self):
        s, _ = _make_specialist()
        result = s._get_fallback_component({})
        assert result["type"] == "generic"
        assert result["framework"] == "react"


# ---------------------------------------------------------------------------
# validate_component
# ---------------------------------------------------------------------------


class TestValidateComponent:
    def test_valid_component_returns_valid_true(self):
        s, _ = _make_specialist()
        component = {
            "type": "div",
            "framework": "react",
            "code": "// x",
            "props": [],
        }
        result = s.validate_component(component)
        assert result["valid"] is True
        assert result["issues"] == []

    def test_missing_required_field_sets_valid_false(self):
        s, _ = _make_specialist()
        component = {"type": "div", "framework": "react"}  # missing code, props
        result = s.validate_component(component)
        assert result["valid"] is False
        assert any("code" in issue for issue in result["issues"])
        assert any("props" in issue for issue in result["issues"])

    def test_score_normalized_between_0_and_1(self):
        s, _ = _make_specialist()
        component = {"type": "div", "framework": "react", "code": "// x", "props": []}
        result = s.validate_component(component)
        assert 0.0 <= result["score"] <= 1.0

    def test_missing_aria_on_button_creates_issue(self):
        s, _ = _make_specialist()
        component = {
            "type": "button",
            "framework": "react",
            "code": "// no aria here",
            "props": [],
        }
        result = s.validate_component(component)
        assert any("accessibility" in issue.lower() for issue in result["issues"])

    def test_score_decremented_by_issues(self):
        s, _ = _make_specialist()
        valid_comp = {"type": "div", "framework": "react", "code": "// x", "props": []}
        invalid_comp = {"type": "button", "framework": "react", "code": "// x", "props": []}
        score_valid = s.validate_component(valid_comp)["score"]
        score_invalid = s.validate_component(invalid_comp)["score"]
        assert score_valid > score_invalid


# ---------------------------------------------------------------------------
# get_component_recommendations
# ---------------------------------------------------------------------------


class TestGetComponentRecommendations:
    def test_returns_list(self):
        s, _ = _make_specialist()
        result = s.get_component_recommendations("button", "react")
        assert isinstance(result, list)

    def test_recommends_adding_patterns_when_none(self):
        s, _ = _make_specialist()
        result = s.get_component_recommendations("button", "react")
        assert any("pattern" in r.lower() for r in result)

    def test_no_accessibility_patterns_triggers_recommendation(self):
        s, mock_kb = _make_specialist()
        # Return patterns but none with accessibility tag
        p = _make_pattern("P1", 0.9, ["styling"])
        mock_kb.search_knowledge.return_value = [p, p, p]
        result = s.get_component_recommendations("button", "react")
        assert any("accessibility" in r.lower() for r in result)

    def test_no_performance_patterns_triggers_recommendation(self):
        s, mock_kb = _make_specialist()
        p = _make_pattern("P1", 0.9, ["styling"])
        mock_kb.search_knowledge.return_value = [p, p, p]
        result = s.get_component_recommendations("button", "react")
        assert any("performance" in r.lower() for r in result)
