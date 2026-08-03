"""Squat error-tag taxonomy.

Only tags observable from a single side-view camera are included:

- fault-gate tags: `insufficient_depth`, `excessive_forward_lean`, `heel_lift`
- soft coaching tag: `inconsistent_tempo`
- system tags: `low_confidence`, `low_capture_quality`, `retry_camera_placement`

Tags explain the result; they do not feed the squat score directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.module_b.core.crud import ErrorTagWrite
from app.module_b.squat.config import SQUAT_CONFIG
from app.module_b.squat.rules import TEMPO_CODE

if TYPE_CHECKING:
    from app.module_b.core.rules import RuleScores
    from app.module_b.squat.fault_gates import FaultGateResult


@dataclass(frozen=True)
class TagSpec:
    """Display metadata for one tag. `message` is the English fallback; the UI renders
    the i18n key `moduleB.{i18n_key}` and only falls back to `message` if it is missing.
    """

    tag: str
    severity: str  # "high" | "medium" | "low"
    source: str  # "rule" | "system"
    kind: str  # "fault" | "soft" | "system"
    i18n_key: str
    message: str | None = None


# Gate messages live in SQUAT_CONFIG (the gate reads them), so the taxonomy references them
# there rather than re-declaring — one message per fault, one place to edit.
_GATES = SQUAT_CONFIG["fault_gates"]

# The five kept tags plus the three fusion system flags, keyed by tag code.
SQUAT_TAG_TAXONOMY: dict[str, TagSpec] = {
    "insufficient_depth": TagSpec(
        tag="insufficient_depth",
        severity="high",
        source="rule",
        kind="fault",
        i18n_key="tag_insufficient_depth",
        message=_GATES["depth"]["message"],
    ),
    "excessive_forward_lean": TagSpec(
        tag="excessive_forward_lean",
        severity="high",
        source="rule",
        kind="fault",
        i18n_key="tag_excessive_forward_lean",
        message=_GATES["lean"]["message"],
    ),
    "heel_lift": TagSpec(
        tag="heel_lift",
        severity="high",
        source="rule",
        kind="fault",
        i18n_key="tag_heel_lift",
        message=_GATES["heel_rise"]["message"],
    ),
    "inconsistent_tempo": TagSpec(
        tag="inconsistent_tempo",
        severity="low",
        source="rule",
        kind="soft",
        i18n_key="tag_inconsistent_tempo",
        message="Aim for a steadier pace across your reps.",
    ),
    "low_confidence": TagSpec(
        tag="low_confidence",
        severity="medium",
        source="system",
        kind="system",
        i18n_key="tag_low_confidence",
        # Backend fallback; frontend i18n owns the displayed copy when available.
        message="Model confidence was low for this set.",
    ),
    "low_capture_quality": TagSpec(
        tag="low_capture_quality",
        severity="medium",
        source="system",
        kind="system",
        i18n_key="tag_low_capture_quality",
        message="Capture quality was too low to fully trust this result.",
    ),
    "retry_camera_placement": TagSpec(
        tag="retry_camera_placement",
        severity="medium",
        source="system",
        kind="system",
        i18n_key="tag_retry_camera_placement",
        message="Try adjusting your camera placement next time.",
    ),
}


def build_squat_error_tags(
    *,
    fusion_flags: tuple[str, ...],
    gate_result: FaultGateResult | None,
    rule_scores: RuleScores,
) -> list[ErrorTagWrite]:
    """Assemble every squat tag for one analyzed set, using the taxonomy for metadata.

    System flags, fault-gate failures, and the soft tempo tag are added in a stable order.
    """
    tags: list[ErrorTagWrite] = []
    tags.extend(_system_tags(fusion_flags))
    tags.extend(_fault_gate_tags(gate_result))
    tempo = _tempo_tag(rule_scores)
    if tempo is not None:
        tags.append(tempo)
    return tags


def _system_tags(fusion_flags: tuple[str, ...]) -> list[ErrorTagWrite]:
    """Carry fusion's capture/confidence flags through as system tags. Unknown flags are
    still surfaced (severity None) so a new fusion flag is never silently swallowed."""
    out: list[ErrorTagWrite] = []
    for flag in fusion_flags:
        spec = SQUAT_TAG_TAXONOMY.get(flag)
        out.append(
            ErrorTagWrite(
                tag=flag,
                severity=spec.severity if spec else None,
                source="system",
                message=spec.message if spec else None,
            )
        )
    return out


def _fault_gate_tags(gate_result: FaultGateResult | None) -> list[ErrorTagWrite]:
    """One tag per failed gate kind (deduped, sorted), reason taken from the gate check."""
    if gate_result is None or gate_result.all_passed:
        return []
    seen: dict[str, str] = {}
    for check in gate_result.failed:
        seen.setdefault(check.tag, check.message)
    out: list[ErrorTagWrite] = []
    for tag, message in sorted(seen.items()):
        spec = SQUAT_TAG_TAXONOMY.get(tag)
        out.append(
            ErrorTagWrite(
                tag=tag,
                severity=spec.severity if spec else "high",
                source="rule",
                message=message,
            )
        )
    return out


def _tempo_tag(rule_scores: RuleScores) -> ErrorTagWrite | None:
    """Emit the soft tempo tag when duration CV crosses the moderate threshold.

    Reuses the CV already computed by `tempo_subscore` (attached to the tempo sub-score's
    `metrics`), so it is never recomputed and it only fires once a set has ≥2 reps (a
    one-rep set leaves the CV absent). Low severity — this never overrides the band.
    """
    cv = _tempo_cv(rule_scores)
    if cv is None:
        return None
    threshold = SQUAT_CONFIG["rules"]["tempo"]["moderate_consistency_cv_max"]
    if cv < threshold:
        return None
    spec = SQUAT_TAG_TAXONOMY["inconsistent_tempo"]
    return ErrorTagWrite(
        tag=spec.tag, severity=spec.severity, source=spec.source, message=spec.message
    )


def _tempo_cv(rule_scores: RuleScores) -> float | None:
    for sub_score in rule_scores.sub_scores:
        if sub_score.code == TEMPO_CODE:
            return sub_score.metrics.get("cv")
    return None
