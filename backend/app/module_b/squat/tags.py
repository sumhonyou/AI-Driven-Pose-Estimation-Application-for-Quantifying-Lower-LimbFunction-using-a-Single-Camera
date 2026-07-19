"""Stage 6.1: the squat error-tag taxonomy — one source of truth for every tag.

This reconciles Phase 6's original 7-row tag table with what Stages 5.11/5.12 actually
shipped. The taxonomy is deliberately trimmed to **five tags**, each observable from a
single monocular side view:

- Three interpretable fault gates already live since Stage 5.12 (`insufficient_depth`,
  `excessive_forward_lean`, `heel_lift`) — high severity, rule-derived, band-overriding.
- One soft consistency tag added here (`inconsistent_tempo`) — low severity, rule-derived,
  never changes the band or score (only the 3 fault gates can, Stage 5.12).
- The system capture/confidence tags carried by fusion (`low_confidence`,
  `low_capture_quality`, `retry_camera_placement`).

Two tags from the original table are **deliberately dropped** and recorded in
`docs/module_b_limitations.md` alongside knee valgus: `asymmetry` (left/right legs are
indistinguishable from one side view — Phase 5 finding 4, leg-diff vs mocap r≈−0.05) and
`feet_too_wide` (stance width is ill-posed in profile — in-sample AUC 0.37, inverts on
EC3D). Measuring either would fabricate a fault the camera cannot see.

`w_rule=0` for squat (Stage 5.11), so tags never feed the score — the ML sets the band, the
gates can only override it downward, and soft tags are explanation-only. This module is the
single place that knows each tag's severity/source/kind so the feedback and template layers
(Stages 6.2+) rank and render them consistently.
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
        # English fallback matches frontend/src/i18n/en.ts's moduleB.tag_low_confidence —
        # the two are deliberately duplicated (same precedent as the fault-gate messages
        # above), since the backend template composer (Stage 6.2) has no access to the
        # frontend's i18n bundle.
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

    System capture/confidence flags, the Stage 5.12 fault-gate failures, and the new soft
    tempo-consistency tag, in that fixed order (persistence re-sorts by tag, so order here
    only needs to be deterministic — X8).
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
