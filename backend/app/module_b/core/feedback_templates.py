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

**Stage 5.17 shape change:** returns a `feedback_contract.RewrittenFeedback` (summary +
tips), not a single string — the same shape the LLM path (`llm_client.py`) now produces,
so the report always renders one thing regardless of which layer wrote it. The caller
(`core/router.py`) serializes it via `feedback_contract.serialize` before storing.
"""

from __future__ import annotations

from app.module_b.core.feedback import StructuredFeedback
from app.module_b.core.feedback_contract import RewrittenFeedback

# Bump whenever the i18n disclaimer copy (`report.nonDiagnosticReminder` and friends)
# changes, so `feedback_texts.disclaimer_version` gives audit-grade traceability of which
# disclaimer wording a stored report was shown alongside (rules.md #19), without storing
# a duplicate copy of the text itself (Stage 6.5).
CURRENT_DISCLAIMER_VERSION = "v1"

# Stage 5.11: squat's stored band value stays "Poor"; the UI relabels it "Needs
# Improvement" for display. The template mirrors that exact relabel so stored/rewritten
# text never contradicts what the report shows (X5-adjacent: text and grade must agree).
# Public (Stage 5.17): also reused by llm_client.py so the LLM is given the same display
# word the user sees, rather than the internal "Poor" value (never leak the internal name).
BAND_LABELS = {"Good": "Good", "Poor": "Needs Improvement", "Fair": "Fair"}

_NO_TAGS_MESSAGE = "No specific issues were flagged for this set."

# How many ranked tags the template quotes. `StructuredFeedback.tags` is already ranked
# severity-first (Stage 6.1), so the first N are always the most important.
_MAX_TAG_MESSAGES = 2


def compose_template(structured: StructuredFeedback) -> RewrittenFeedback:
    """`{"summary": "Grade: {band}.", "tips": [...]}` — deterministic, no LLM.

    Falls back to a single explanatory tip when no tag fired, so `tips` is never empty —
    the frontend can then always render at least one list item.
    """
    summary = f"Grade: {band_label(structured.band)}."
    tag_messages = _top_tag_messages(structured)
    return RewrittenFeedback(
        summary=summary,
        tips=tuple(tag_messages) if tag_messages else (_NO_TAGS_MESSAGE,),
    )


def band_label(band: str | None) -> str:
    if band is None:
        return "Unavailable"
    return BAND_LABELS.get(band, band)


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
