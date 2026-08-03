"""Safety checks for LLM-rewritten Module B feedback.

`StructuredFeedback` is the trusted source. A rewrite is accepted only if it keeps the
same grade, avoids invented faults, avoids forbidden clinical wording, and stays within
the length and formatting limits.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.safety_phrases import FORBIDDEN_PHRASES
from app.module_b.core.feedback import StructuredFeedback
from app.module_b.core.feedback_contract import joined_text
from app.module_b.core.feedback_contract import parse as parse_feedback_contract
from app.module_b.squat.tags import SQUAT_TAG_TAXONOMY

# Reject markdown formatting and leading bullets in generated prose.
_MARKDOWN_CHARS_RE = re.compile(r"[*_#`]")
_LEADING_BULLET_RE = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+")

# Long enough for short coaching text; short enough to block runaway output.
MAX_REWRITE_LENGTH = 600

# Band words matched as whole words so unrelated wording does not false-positive.
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
    """Run all safety checks; the first failure rejects the whole candidate."""
    if not candidate or not candidate.strip():
        return SafetyCheckResult(accepted=False, reason="empty")

    parsed = parse_feedback_contract(candidate)
    if parsed is None:
        return SafetyCheckResult(accepted=False, reason="invalid_json")

    full_text = joined_text(parsed)
    if len(full_text) > MAX_REWRITE_LENGTH:
        return SafetyCheckResult(accepted=False, reason="too_long")

    if _contains_markdown(parsed):
        return SafetyCheckResult(accepted=False, reason="markdown_formatting")

    lowered = full_text.lower()

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


def _contains_markdown(parsed) -> bool:
    """True if the summary or any tip carries markdown formatting or a leading bullet.

    Checked here, not in `feedback_contract.parse` -- that module validates JSON SHAPE
    only; whether the CONTENT is acceptable prose is a content-policy question, and this
    module is where every other content policy (forbidden phrases, grade/tag integrity)
    already lives.
    """
    if _MARKDOWN_CHARS_RE.search(parsed.summary):
        return True
    for tip in parsed.tips:
        if _MARKDOWN_CHARS_RE.search(tip) or _LEADING_BULLET_RE.match(tip):
            return True
    return False


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
    a closed, small taxonomy rather than open-ended hallucination detection.
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
