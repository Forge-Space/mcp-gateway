"""Generate-review-refine loop for improving AI-generated code.

Runs quality gates after generation, then iteratively refines
code that fails gates by feeding issues back to the AI provider.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from tool_router.api.quality_gates import QualityReport, run_quality_gates


logger = logging.getLogger(__name__)


@dataclass
class RefinementResult:
    original_code: str
    final_code: str
    iterations: int
    initial_score: float
    final_score: float
    score_delta: float
    total_ms: int
    history: list[dict] = field(default_factory=list)


@dataclass
class RefinementConfig:
    max_iterations: int = 3
    min_score_improvement: float = 0.05
    target_score: float = 1.0


def build_refinement_prompt(
    code: str,
    quality_report: QualityReport,
    original_task: str,
) -> str:
    issues = []
    for result in quality_report.results:
        if not result.passed:
            for issue in result.issues:
                issues.append(f"- [{result.gate}] {issue}")

    issues_text = "\n".join(issues) if issues else "No specific issues"

    return (
        f"The following code was generated for: {original_task}\n\n"
        f"```\n{code}\n```\n\n"
        f"Quality gate score: {quality_report.score:.2f}/1.0\n"
        f"Issues found:\n{issues_text}\n\n"
        "Fix ALL issues above. Output ONLY the corrected code, "
        "no explanations."
    )


def should_refine(
    report: QualityReport,
    config: RefinementConfig,
    iteration: int,
    prev_score: float,
) -> bool:
    if report.score >= config.target_score:
        return False
    if iteration >= config.max_iterations:
        return False
    if iteration > 0:
        delta = report.score - prev_score
        if delta < config.min_score_improvement:
            return False
    return not report.passed


def refine_code(
    code: str,
    task: str,
    generate_fn,
    config: RefinementConfig | None = None,
) -> RefinementResult:
    cfg = config or RefinementConfig()
    start = time.monotonic()

    initial_report = run_quality_gates(code)
    history = [
        {
            "iteration": 0,
            "score": initial_report.score,
            "passed": initial_report.passed,
        }
    ]

    current_code = code
    current_report = initial_report
    prev_score = 0.0

    for i in range(1, cfg.max_iterations + 1):
        if not should_refine(current_report, cfg, i - 1, prev_score):
            break

        prev_score = current_report.score
        prompt = build_refinement_prompt(current_code, current_report, task)

        try:
            refined = generate_fn(prompt)
            if not refined or len(refined.strip()) < 20:
                break
            current_code = refined
        except Exception:
            logger.warning("Refinement iteration %d failed", i)
            break

        current_report = run_quality_gates(current_code)
        history.append(
            {
                "iteration": i,
                "score": current_report.score,
                "passed": current_report.passed,
            }
        )

        logger.info(
            "Refinement iteration %d: score %.2f → %.2f",
            i,
            prev_score,
            current_report.score,
        )

    elapsed = int((time.monotonic() - start) * 1000)

    return RefinementResult(
        original_code=code,
        final_code=current_code,
        iterations=len(history) - 1,
        initial_score=initial_report.score,
        final_score=current_report.score,
        score_delta=current_report.score - initial_report.score,
        total_ms=elapsed,
        history=history,
    )
