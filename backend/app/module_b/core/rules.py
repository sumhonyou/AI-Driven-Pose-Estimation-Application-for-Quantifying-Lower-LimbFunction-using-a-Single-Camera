"""Shared, exercise-agnostic rule sub-score containers and aggregation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SubScore:
    """One explainable 0–10 rule component; ``None`` means unavailable.

    ``metrics`` carries report-only numeric measurements that must NEVER
    contribute to ``RuleScores.score`` (e.g. lunge's cross-rep symmetry index,
    Stage 4.4 Lunge) -- keep ``score=None`` on any sub-score that only reports.
    """

    code: str
    score: float | None
    notes: tuple[str, ...] = ()
    metrics: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("SubScore.code must not be empty")
        if self.score is not None and not 0.0 <= self.score <= 10.0:
            raise ValueError("SubScore.score must be between 0 and 10")
        if any(not math.isfinite(value) for value in self.metrics.values()):
            raise ValueError("SubScore.metrics values must be finite")


@dataclass(frozen=True)
class RuleScores:
    """Named rule components with an equal-weight mean over available scores."""

    sub_scores: tuple[SubScore, ...]

    def __post_init__(self) -> None:
        codes = tuple(sub_score.code for sub_score in self.sub_scores)
        if len(set(codes)) != len(codes):
            raise ValueError("RuleScores requires unique sub-score codes")

    @property
    def score(self) -> float | None:
        """Return the 0–10 equal-weight mean, excluding unavailable components."""
        available = [
            sub_score.score
            for sub_score in self.sub_scores
            if sub_score.score is not None
        ]
        return sum(available) / len(available) if available else None

    def by_code(self) -> dict[str, SubScore]:
        """Return sub-scores by their stable, exercise-defined code."""
        return {sub_score.code: sub_score for sub_score in self.sub_scores}


def assemble_rule_scores(*sub_scores: SubScore) -> RuleScores:
    """Assemble an exercise's named components into its fusion-ready rule score."""
    return RuleScores(sub_scores=tuple(sub_scores))
