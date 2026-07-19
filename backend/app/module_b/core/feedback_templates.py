"""Stage 6.2: the deterministic template fallback — built before any LLM code exists.

`compose_template` is the guaranteed-available coaching text: it can never invent a claim
and can never change the grade, because it is assembled purely from the already-graded
`StructuredFeedback` and the taxonomy's own English tag messages (`tags.py`'s
`TagSpec.message` — the same English text the frontend also carries via i18n
`moduleB.tag_*`, deliberately duplicated per Stage 6.2's own note in that file). No network
call, no randomness, no external state: same input -> same output, always.

This is the GATE (task.md Stage 6.2): the whole report must be provably complete with the
LLM disabled before any API-client code is written — see
`test_module_b_feedback_templates.py`'s `TemplateGateTests`.
"""

from __future__ import annotations

from app.module_b.core.feedback import StructuredFeedback

# Bump whenever the i18n disclaimer copy (`report.nonDiagnosticReminder` and friends)
# changes, so `feedback_texts.disclaimer_version` gives audit-grade traceability of which
# disclaimer wording a stored report was shown alongside (rules.md #19), without storing
# a duplicate copy of the text itself (Stage 6.5).
CURRENT_DISCLAIMER_VERSION = "v1"

# Stage 5.11: squat's stored band value stays "Poor"; the UI relabels it "Needs
# Improvement" for display. The template mirrors that exact relabel so stored/rewritten
# text never contradicts what the report shows (X5-adjacent: text and grade must agree).
_BAND_LABELS = {"Good": "Good", "Poor": "Needs Improvement", "Fair": "Fair"}

_NO_TAGS_MESSAGE = "No specific issues were flagged for this set."

# How many ranked tags the template quotes. `StructuredFeedback.tags` is already ranked
# severity-first (Stage 6.1), so the first N are always the most important.
_MAX_TAG_MESSAGES = 2


def compose_template(structured: StructuredFeedback) -> str:
    """ "Grade: {band}. {top_tag_message}. {second_tag_message}" — deterministic, no LLM."""
    sentences = [f"Grade: {_band_label(structured.band)}."]
    tag_messages = _top_tag_messages(structured)
    sentences.extend(tag_messages)
    if not tag_messages:
        sentences.append(_NO_TAGS_MESSAGE)
    return " ".join(sentences)


def _band_label(band: str | None) -> str:
    if band is None:
        return "Unavailable"
    return _BAND_LABELS.get(band, band)


def _top_tag_messages(structured: StructuredFeedback) -> list[str]:
    """Up to `_MAX_TAG_MESSAGES` messages, in the existing severity-first tag order.

    A tag missing an English `message` (should not happen post Stage 6.2, but the
    taxonomy is external state) is skipped rather than surfacing a blank sentence.
    """
    messages: list[str] = []
    for tag in structured.tags:
        if not tag.message:
            continue
        messages.append(tag.message)
        if len(messages) >= _MAX_TAG_MESSAGES:
            break
    return messages
