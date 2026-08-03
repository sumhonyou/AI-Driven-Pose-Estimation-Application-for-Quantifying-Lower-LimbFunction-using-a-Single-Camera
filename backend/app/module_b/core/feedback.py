"""Build deterministic after-set feedback data for Module B.

This layer reads the persisted result snapshot only: band, score, rule sub-scores,
confidence, and stored tags. It never re-derives a grade, so downstream text layers
cannot change the result.

Tags are ranked severity-first (high → medium → low). "Magnitude" ordering within a
severity, which the plan mentions, is not available here because the per-tag metric value
is not persisted on the tag row; a stable tag-name tiebreak is used instead so the ranking
is fully deterministic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

# High is most important. Unknown/None severities sort last but stay deterministic.
_SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


@dataclass(frozen=True)
class FeedbackSubScore:
    """One rule sub-score as shown in the report (decision-inert for squat, w_rule=0)."""

    code: str
    score: float | None


@dataclass(frozen=True)
class FeedbackTag:
    """One ranked tag with the metadata needed to render or rewrite it."""

    tag: str
    severity: str | None
    source: str | None
    message: str | None


@dataclass(frozen=True)
class StructuredFeedback:
    """The deterministic feedback payload the template/LLM layers compose from."""

    band: str | None
    score: float | None
    confidence: float | None
    rep_count: int
    sub_scores: tuple[FeedbackSubScore, ...]
    tags: tuple[FeedbackTag, ...]


def build_structured_feedback(summary: Mapping[str, Any]) -> StructuredFeedback:
    """Build ranked feedback from the same summary shape returned by the API."""
    metrics = summary.get("metrics") or {}
    sub_scores = tuple(
        FeedbackSubScore(code=item.get("code"), score=item.get("score"))
        for item in metrics.get("rule_subscores", [])
    )
    rep_count = len(metrics.get("per_rep_summaries", []))
    tags = _rank_tags(summary.get("error_tags", []))
    return StructuredFeedback(
        band=summary.get("band"),
        score=summary.get("score"),
        confidence=summary.get("confidence"),
        rep_count=rep_count,
        sub_scores=sub_scores,
        tags=tags,
    )


def _rank_tags(raw_tags: Sequence[Mapping[str, Any]]) -> tuple[FeedbackTag, ...]:
    """Order tags by severity, then tag name for a stable, deterministic result."""
    ranked = sorted(
        (
            FeedbackTag(
                tag=item.get("tag"),
                severity=item.get("severity"),
                source=item.get("source"),
                message=item.get("message"),
            )
            for item in raw_tags
        ),
        key=lambda tag: (
            _SEVERITY_RANK.get(tag.severity, len(_SEVERITY_RANK)),
            tag.tag,
        ),
    )
    return tuple(ranked)
