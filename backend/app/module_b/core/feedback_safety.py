"""Stage 6.3: the safety filter applied to LLM output before it is stored or shown.

`StructuredFeedback` (Stage 6.1) is the trusted source; any LLM rewrite (Stage 6.4) is
only a readability layer over it. This module is the gate between the two: it never lets
a rewrite past that could change what the user believes about their grade, mention a
fault that was never detected, make a forbidden clinical claim, or run unbounded length.
Any single failed check discards the whole candidate — the caller falls back to
`feedback_templates.compose_template` (X5: the grade shown to the user must always match
what was actually computed).

This module has no dependency on Stage 6.4's `llm_client` — it only checks plain text
against a `StructuredFeedback`, so it is fully testable (and was fully built) before any
LLM code exists.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.safety_phrases import FORBIDDEN_PHRASES
from app.module_b.core.feedback import StructuredFeedback
from app.module_b.squat.tags import SQUAT_TAG_TAXONOMY

# Generous enough for a short coaching paragraph, tight enough to block a runaway or
# injected wall of text. Matches the "Length cap" bullet in task.md Stage 6.3.
MAX_REWRITE_LENGTH = 600

# Band words the model could plausibly use, including the squat UI's Stage 5.11 relabel
# ("Poor" is displayed and could be rewritten as "Needs Improvement"). Matched
# case-insensitively as whole words/phrases so "good form overall" doesn't false-positive
# on "form".
_BAND_WORDS: dict[str, tuple[str, ...]] = {
    "Good": ("good",),
    "Fair": ("fair",),
    "Poor": ("poor", "needs improvement"),
}

_SCORE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:/\s*10\b|out of 10\b)", re.IGNORECASE)
_SCORE_TOLERANCE = 0.05


@dataclass(frozen=True)
class SafetyCheckResult:
    """`accepted=False` always means: discard the candidate, use the template instead."""

    accepted: bool
    reason: str | None = None


def check_llm_feedback(
    candidate: str, *, structured: StructuredFeedback
) -> SafetyCheckResult:
    """Run every Stage 6.3 check; the first failure rejects the whole candidate."""
    if not candidate or not candidate.strip():
        return SafetyCheckResult(accepted=False, reason="empty")
    if len(candidate) > MAX_REWRITE_LENGTH:
        return SafetyCheckResult(accepted=False, reason="too_long")

    lowered = candidate.lower()

    forbidden = _find_forbidden_phrase(lowered)
    if forbidden is not None:
        return SafetyCheckResult(accepted=False, reason=f"forbidden_phrase:{forbidden}")

    if _contradicts_band(lowered, structured.band):
        return SafetyCheckResult(accepted=False, reason="grade_mismatch_band")

    if _contradicts_score(lowered, structured.score):
        return SafetyCheckResult(accepted=False, reason="grade_mismatch_score")

    invented_tag = _find_invented_tag(lowered, structured)
    if invented_tag is not None:
        return SafetyCheckResult(accepted=False, reason=f"invented_tag:{invented_tag}")

    return SafetyCheckResult(accepted=True)


def _find_forbidden_phrase(lowered_text: str) -> str | None:
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered_text:
            return phrase
    return None


def _contradicts_band(lowered_text: str, true_band: str | None) -> bool:
    """True if the text asserts a band other than the true one (X5, grade integrity)."""
    if true_band is None:
        return False
    for band, words in _BAND_WORDS.items():
        if band == true_band:
            continue
        for word in words:
            if _contains_word(lowered_text, word):
                return True
    return False


def _contradicts_score(lowered_text: str, true_score: float | None) -> bool:
    """True if the text states a numeric "X/10" score that disagrees with the real one."""
    if true_score is None:
        return False
    for match in _SCORE_RE.finditer(lowered_text):
        stated = float(match.group(1))
        if abs(stated - true_score) > _SCORE_TOLERANCE:
            return True
    return False


def _find_invented_tag(lowered_text: str, structured: StructuredFeedback) -> str | None:
    """True if the text names a *known taxonomy* tag that was not actually flagged.

    Only checks tags the taxonomy knows about (so it can compare against their message/
    tag-code text); this is what "a tag not in the structured input" concretely means for
    a closed, small taxonomy (Stage 6.1) rather than open-ended hallucination detection.
    """
    present = {tag.tag for tag in structured.tags}
    for tag_code, spec in SQUAT_TAG_TAXONOMY.items():
        if tag_code in present:
            continue
        if _contains_word(lowered_text, tag_code.replace("_", " ")):
            return tag_code
        if spec.message and spec.message.rstrip(".").lower() in lowered_text:
            return tag_code
    return None


def _contains_word(text: str, phrase: str) -> bool:
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None
