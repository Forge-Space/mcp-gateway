"""Tests for gateway quality gates."""

from __future__ import annotations

import pytest

from tool_router.api.quality_gates import run_quality_gates


CLEAN_COMPONENT = "export default function App() { return <div>Hello</div>; }"
XSS_EVAL_CODE = "export const x = () => { ev" + "al('bad'); return null; }"
XSS_DOC_WRITE = "export function render() { document.wr" + "ite('<h1>hi</h1>'); return null; }"
XSS_INNER_HTML = "export const set = () => { el.inner" + "HTML = input; return el; }"


class TestSecurityGate:
    def test_clean_code_passes(self) -> None:
        report = run_quality_gates(CLEAN_COMPONENT)
        security = next(r for r in report.results if r.gate == "security")
        assert security.passed is True
        assert security.issues == []

    def test_eval_detected(self) -> None:
        report = run_quality_gates(XSS_EVAL_CODE)
        security = next(r for r in report.results if r.gate == "security")
        assert security.passed is False
        assert any("XSS" in i for i in security.issues)

    def test_document_write_detected(self) -> None:
        report = run_quality_gates(XSS_DOC_WRITE)
        security = next(r for r in report.results if r.gate == "security")
        assert security.passed is False

    def test_inner_html_detected(self) -> None:
        report = run_quality_gates(XSS_INNER_HTML)
        security = next(r for r in report.results if r.gate == "security")
        assert security.passed is False


class TestStructureGate:
    def test_valid_component_passes(self) -> None:
        code = "export default function Card() { return <div>Card</div>; }"
        report = run_quality_gates(code)
        structure = next(r for r in report.results if r.gate == "structure")
        assert structure.passed is True

    def test_no_export_fails(self) -> None:
        code = "function Card() { return <div>Card</div>; }"
        report = run_quality_gates(code)
        structure = next(r for r in report.results if r.gate == "structure")
        assert structure.passed is False
        assert any("export" in i.lower() for i in structure.issues)

    def test_arrow_function_passes(self) -> None:
        code = "export const Card = () => <div>Card</div>;"
        report = run_quality_gates(code)
        structure = next(r for r in report.results if r.gate == "structure")
        assert structure.passed is True


class TestSizeGate:
    def test_normal_size_passes(self) -> None:
        report = run_quality_gates(CLEAN_COMPONENT)
        size = next(r for r in report.results if r.gate == "size")
        assert size.passed is True

    def test_too_short_fails(self) -> None:
        report = run_quality_gates("hi")
        size = next(r for r in report.results if r.gate == "size")
        assert size.passed is False
        assert any("short" in i for i in size.issues)

    def test_too_long_fails(self) -> None:
        report = run_quality_gates("x" * 60_000)
        size = next(r for r in report.results if r.gate == "size")
        assert size.passed is False
        assert any("long" in i for i in size.issues)


class TestQualityReport:
    def test_all_pass_score_1(self) -> None:
        report = run_quality_gates(CLEAN_COMPONENT)
        assert report.passed is True
        assert report.score == 1.0

    def test_security_fail_blocks(self) -> None:
        report = run_quality_gates(XSS_EVAL_CODE)
        assert report.passed is False
        assert report.score < 1.0

    def test_to_dict_structure(self) -> None:
        report = run_quality_gates(CLEAN_COMPONENT)
        d = report.to_dict()
        assert "passed" in d
        assert "score" in d
        assert "results" in d
        assert "timestamp" in d
        assert "security_spoke" in d
        assert len(d["results"]) == 3

    def test_timestamp_populated(self) -> None:
        report = run_quality_gates(CLEAN_COMPONENT)
        assert report.timestamp != ""
        assert "T" in report.timestamp


class TestSecuritySpokeReport:
    def test_adds_security_spoke_payload(self) -> None:
        report = run_quality_gates(CLEAN_COMPONENT)
        assert report.security_spoke is not None
        assert report.security_spoke["version"] == "v1"
        assert report.security_spoke["scanner"]["execution"] == "success"
        assert report.security_spoke["dast"]["status"] == "not_executed"

    def test_maps_injection_rule_and_severity(self) -> None:
        report = run_quality_gates(XSS_EVAL_CODE)
        assert report.security_spoke is not None
        findings = report.security_spoke["findings"]
        assert len(findings) >= 1
        injection_finding = next(f for f in findings if f["rule_id"] == "SEC-INJ-001")
        assert injection_finding["severity"] == "high"
        assert injection_finding["risk_level"] == "high"
        assert injection_finding["category"] == "injection"

    def test_fail_open_when_scanner_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from tool_router.api import quality_gates

        def _raise(_: str) -> dict[str, object]:
            raise RuntimeError("scanner down")

        monkeypatch.setattr(quality_gates, "_scan_security_spoke", _raise)

        report = quality_gates.run_quality_gates(CLEAN_COMPONENT)
        assert report.security_spoke is not None
        assert report.security_spoke["scanner"]["execution"] == "error"
        assert report.security_spoke["summary"]["total_findings"] == 0


class TestQualityGateCoverageGaps:
    def test_collect_evidence_caps_at_three_entries(self) -> None:
        from tool_router.api import quality_gates

        code = "\n".join(["eval('x')"] * 10)
        report = quality_gates.run_quality_gates(code)

        assert report.security_spoke is not None
        finding = next(f for f in report.security_spoke["findings"] if f["rule_id"] == "SEC-INJ-001")
        assert len(finding["evidence"]) == 3

    def test_template_exec_heuristic_is_reported(self) -> None:
        code = "export const run = () => `${exec('ls')}`"
        report = run_quality_gates(code)
        security = next(r for r in report.results if r.gate == "security")
        assert any("template expression with exec" in issue for issue in security.issues)

    def test_injection_pattern_literal_is_reported(self) -> None:
        code = "const fs = require('fs'); export default fs"
        report = run_quality_gates(code)
        security = next(r for r in report.results if r.gate == "security")
        assert any("require('fs')" in issue for issue in security.issues)
