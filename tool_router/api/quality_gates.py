"""Lightweight quality gates for generated code at the gateway layer."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field


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

    def to_dict(self) -> dict:
        return {
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
    )
