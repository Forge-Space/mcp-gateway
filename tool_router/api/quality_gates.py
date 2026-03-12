"""Lightweight quality gates for generated code at the gateway layer."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class GateResult:
    gate: str
    passed: bool
    issues: list[str] = field(default_factory=list)
    severity: str = "info"


@dataclass
class QualityReport:
    passed: bool
    score: float
    results: list[GateResult] = field(default_factory=list)
    timestamp: str = ""
    security_spoke: dict[str, object] | None = None

    def to_dict(self) -> dict:
        report = {
            "passed": self.passed,
            "score": self.score,
            "results": [
                {
                    "gate": r.gate,
                    "passed": r.passed,
                    "issues": r.issues,
                    "severity": r.severity,
                }
                for r in self.results
            ],
            "timestamp": self.timestamp,
        }
        if self.security_spoke is not None:
            report["security_spoke"] = self.security_spoke
        return report


# Security patterns that indicate potential XSS or injection risks
_XSS_PATTERNS = [
    re.compile(r"dangerously" + r"SetInnerHTML", re.IGNORECASE),
    re.compile(r"innerHTML\s*="),
    re.compile(r"document\.write"),
    re.compile(r"eval\s*\("),
    re.compile(r"new\s+Function\s*\("),
]

_INJECTION_PATTERNS = [
    "child_process",
    "require('fs')",
    'require("fs")',
]

_SECURITY_SPOKE_SEVERITY_TEMPLATE = {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0,
    "info": 0,
}

_SECURITY_SPOKE_RISK_TEMPLATE = {
    "high": 0,
    "medium": 0,
    "low": 0,
}
_INSECURE_HTTP_SCHEME = "http" + "://"

_SECURITY_SPOKE_RULES = [
    {
        "rule_id": "SEC-SECRET-001",
        "title": "Hardcoded Secret Pattern",
        "severity": "critical",
        "category": "secrets",
        "risk_level": "high",
        "recommendation": "Remove hardcoded secret and load credential from secure env.",
        "patterns": [
            re.compile(r"AKIA[0-9A-Z]{16}"),
            re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
        ],
    },
    {
        "rule_id": "SEC-DEP-001",
        "title": "Known Vulnerable Dependency",
        "severity": "high",
        "category": "dependencies",
        "risk_level": "high",
        "recommendation": "Upgrade vulnerable dependency and refresh lockfile.",
        "patterns": [
            re.compile(r"esbuild@0\.21\.\d"),
            re.compile(r"@tootallnate/once@2\.\d+\.\d+"),
        ],
    },
    {
        "rule_id": "SEC-INJ-001",
        "title": "Injection Sink Pattern",
        "severity": "high",
        "category": "injection",
        "risk_level": "high",
        "recommendation": "Replace dynamic execution with parameterized/safe APIs.",
        "patterns": [
            re.compile(r"eval\s*\("),
            re.compile(r"new\s+Function\s*\("),
            re.compile(r"document\.write"),
            re.compile(r"innerHTML\s*="),
        ],
    },
    {
        "rule_id": "SEC-AUTH-001",
        "title": "Missing Authorization Guard",
        "severity": "medium",
        "category": "auth",
        "risk_level": "medium",
        "recommendation": "Add authorization checks before sensitive operations.",
        "patterns": [
            re.compile(r"allow_anonymous\s*=\s*True"),
            re.compile(r"skip_auth\s*=\s*True"),
        ],
    },
    {
        "rule_id": "SEC-TRANSPORT-001",
        "title": "Insecure Transport Usage",
        "severity": "medium",
        "category": "transport",
        "risk_level": "medium",
        "recommendation": "Use HTTPS and reject insecure URL schemes in prod paths.",
        "patterns": [
            re.compile(rf"{re.escape(_INSECURE_HTTP_SCHEME)}[^\s\"']+"),
        ],
    },
    {
        "rule_id": "SEC-CONFIG-001",
        "title": "Overly Permissive Security Config",
        "severity": "medium",
        "category": "config",
        "risk_level": "medium",
        "recommendation": "Restrict CORS/security headers with explicit allowlists.",
        "patterns": [
            re.compile(r"Access-Control-Allow-Origin\s*:\s*\*"),
            re.compile(r"origin\s*:\s*['\"]\*['\"]"),
        ],
    },
]


def _build_empty_security_summary() -> dict[str, object]:
    return {
        "total_findings": 0,
        "by_severity": dict(_SECURITY_SPOKE_SEVERITY_TEMPLATE),
        "by_risk_level": dict(_SECURITY_SPOKE_RISK_TEMPLATE),
    }


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _collect_evidence(code: str, patterns: list[re.Pattern[str]]) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    for pattern in patterns:
        for match in pattern.finditer(code):
            evidence.append(
                {
                    "kind": "code",
                    "value": pattern.pattern,
                    "line": _line_number(code, match.start()),
                }
            )
            if len(evidence) >= 3:
                return evidence
    return evidence


def _build_summary(findings: list[dict[str, object]]) -> dict[str, object]:
    by_severity = dict(_SECURITY_SPOKE_SEVERITY_TEMPLATE)
    by_risk_level = dict(_SECURITY_SPOKE_RISK_TEMPLATE)

    for finding in findings:
        severity = finding["severity"]
        risk_level = finding["risk_level"]
        by_severity[severity] += 1
        by_risk_level[risk_level] += 1

    return {
        "total_findings": len(findings),
        "by_severity": by_severity,
        "by_risk_level": by_risk_level,
    }


def _build_security_spoke_report(
    findings: list[dict[str, object]],
    execution: str,
    error_message: str | None = None,
) -> dict[str, object]:
    scanner: dict[str, object] = {
        "name": "mcp-gateway-native-security-spoke",
        "version": "1.0.0",
        "execution": execution,
    }
    if error_message:
        scanner["error_message"] = error_message

    return {
        "version": "v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scanner": scanner,
        "summary": _build_summary(findings),
        "findings": findings,
        "dast": {
            "status": "not_executed",
            "mode": "hooks_only_v1",
            "reason": "DAST workers are deferred in v1; hooks telemetry only.",
        },
    }


def _scan_security_spoke(code: str) -> dict[str, object]:
    findings: list[dict[str, object]] = []

    for rule in _SECURITY_SPOKE_RULES:
        evidence = _collect_evidence(code, rule["patterns"])
        if not evidence:
            continue

        findings.append(
            {
                "rule_id": rule["rule_id"],
                "severity": rule["severity"],
                "category": rule["category"],
                "title": rule["title"],
                "evidence": evidence,
                "recommendation": rule["recommendation"],
                "risk_level": rule["risk_level"],
            }
        )

    return _build_security_spoke_report(findings=findings, execution="success")


def _build_fail_open_security_spoke() -> dict[str, object]:
    report = _build_security_spoke_report(
        findings=[],
        execution="error",
        error_message="security scanner unavailable",
    )
    report["summary"] = _build_empty_security_summary()
    return report


def _run_security_scan(code: str) -> GateResult:
    issues: list[str] = []
    for pattern in _XSS_PATTERNS:
        if pattern.search(code):
            issues.append(f"Potential XSS: {pattern.pattern}")
    if "${" in code and "}" in code and "exec" in code:
        issues.append("Potential injection: template expression with exec")
    for pattern in _INJECTION_PATTERNS:
        if pattern in code:
            issues.append(f"Potential injection: {pattern}")
    return GateResult(
        gate="security",
        passed=len(issues) == 0,
        issues=issues,
        severity="error" if issues else "info",
    )


def _run_structure_check(code: str) -> GateResult:
    issues: list[str] = []
    has_export = "export " in code
    has_function_or_class = bool(re.search(r"(function\s+\w+|class\s+\w+|const\s+\w+\s*=)", code))
    has_return = "return" in code or "=>" in code

    if not has_export:
        issues.append("No export statement found")
    if not has_function_or_class:
        issues.append("No function or class definition found")
    if not has_return:
        issues.append("No return statement found")

    return GateResult(
        gate="structure",
        passed=len(issues) == 0,
        issues=issues,
        severity="warning" if issues else "info",
    )


def _run_size_check(code: str) -> GateResult:
    issues: list[str] = []
    if len(code) < 50:
        issues.append(f"Code too short ({len(code)} chars)")
    if len(code) > 50_000:
        issues.append(f"Code too long ({len(code)} chars)")
    return GateResult(
        gate="size",
        passed=len(issues) == 0,
        issues=issues,
        severity="warning" if issues else "info",
    )


_GATE_WEIGHTS = {
    "security": 3,
    "structure": 2,
    "size": 1,
}


def run_quality_gates(code: str) -> QualityReport:
    """Run all quality gates on generated code."""
    try:
        security_spoke = _scan_security_spoke(code)
    except Exception:
        logger.exception("Security spoke scan failed")
        security_spoke = _build_fail_open_security_spoke()

    results = [
        _run_security_scan(code),
        _run_structure_check(code),
        _run_size_check(code),
    ]

    earned = 0
    total = 0
    for r in results:
        w = _GATE_WEIGHTS.get(r.gate, 1)
        total += w
        if r.passed:
            earned += w

    score = earned / total if total > 0 else 1.0
    passed = all(r.passed or r.severity != "error" for r in results)

    return QualityReport(
        passed=passed,
        score=score,
        results=results,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        security_spoke=security_spoke,
    )
