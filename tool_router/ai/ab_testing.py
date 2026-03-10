"""A/B testing for generation quality.

Assigns users to experiment variants deterministically (consistent
hashing), tracks outcomes, and reports variant performance.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class Variant:
    name: str
    weight: float = 1.0
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class Experiment:
    id: str
    variants: list[Variant]
    description: str = ""
    active: bool = True


@dataclass
class ExperimentOutcome:
    experiment_id: str
    variant_name: str
    user_id: str
    quality_score: float
    latency_ms: int
    success: bool
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class ABTestManager:
    """Manages A/B test experiments with deterministic assignment."""

    def __init__(
        self,
        experiments: list[Experiment] | None = None,
        storage_path: str | None = None,
    ) -> None:
        self._experiments: dict[str, Experiment] = {}
        self._outcomes: list[ExperimentOutcome] = []
        self._storage = Path(storage_path) if storage_path else None

        for exp in experiments or []:
            self._experiments[exp.id] = exp

        if self._storage and self._storage.exists():
            self._load_outcomes()

    def register(self, experiment: Experiment) -> None:
        self._experiments[experiment.id] = experiment

    def assign_variant(self, user_id: str, experiment_id: str) -> Variant | None:
        exp = self._experiments.get(experiment_id)
        if not exp or not exp.active or not exp.variants:
            return None

        hash_bytes = hashlib.sha256(f"{user_id}:{experiment_id}".encode()).digest()
        hash_val = int.from_bytes(hash_bytes[:4], "big")

        total_weight = sum(v.weight for v in exp.variants)
        if total_weight <= 0:
            return exp.variants[0]

        target = (hash_val % 10000) / 10000.0 * total_weight
        cumulative = 0.0
        for variant in exp.variants:
            cumulative += variant.weight
            if target < cumulative:
                return variant

        return exp.variants[-1]

    def record_outcome(self, outcome: ExperimentOutcome) -> None:
        self._outcomes.append(outcome)
        if len(self._outcomes) % 50 == 0:
            self._persist_outcomes()

    def get_variant_stats(self, experiment_id: str) -> dict[str, dict[str, Any]]:
        relevant = [o for o in self._outcomes if o.experiment_id == experiment_id]
        if not relevant:
            return {}

        by_variant: dict[str, list[ExperimentOutcome]] = {}
        for o in relevant:
            by_variant.setdefault(o.variant_name, []).append(o)

        stats: dict[str, dict[str, Any]] = {}
        for name, outcomes in by_variant.items():
            scores = [o.quality_score for o in outcomes]
            latencies = [o.latency_ms for o in outcomes]
            successes = sum(1 for o in outcomes if o.success)

            stats[name] = {
                "count": len(outcomes),
                "avg_score": sum(scores) / len(scores),
                "avg_latency_ms": sum(latencies) / len(latencies),
                "success_rate": successes / len(outcomes),
                "min_score": min(scores),
                "max_score": max(scores),
            }

        return stats

    def get_winner(self, experiment_id: str, min_samples: int = 20) -> str | None:
        stats = self.get_variant_stats(experiment_id)
        eligible = {k: v for k, v in stats.items() if v["count"] >= min_samples}
        if not eligible:
            return None
        return max(eligible, key=lambda k: eligible[k]["avg_score"])

    def _persist_outcomes(self) -> None:
        if not self._storage:
            return
        try:
            data = [
                {
                    "experiment_id": o.experiment_id,
                    "variant_name": o.variant_name,
                    "user_id": o.user_id,
                    "quality_score": o.quality_score,
                    "latency_ms": o.latency_ms,
                    "success": o.success,
                    "timestamp": o.timestamp,
                }
                for o in self._outcomes[-500:]
            ]
            self._storage.write_text(json.dumps(data, indent=2))
        except OSError:
            logger.warning("Failed to persist A/B test outcomes")

    def _load_outcomes(self) -> None:
        if not self._storage or not self._storage.exists():
            return
        try:
            data = json.loads(self._storage.read_text())
            for item in data:
                self._outcomes.append(
                    ExperimentOutcome(
                        experiment_id=item["experiment_id"],
                        variant_name=item["variant_name"],
                        user_id=item["user_id"],
                        quality_score=item["quality_score"],
                        latency_ms=item["latency_ms"],
                        success=item["success"],
                        timestamp=item.get("timestamp", 0),
                    )
                )
        except (json.JSONDecodeError, KeyError, OSError):
            logger.warning("Failed to load A/B test outcomes")
