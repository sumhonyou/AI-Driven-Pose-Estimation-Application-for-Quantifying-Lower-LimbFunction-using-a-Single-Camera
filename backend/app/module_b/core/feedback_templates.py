"""Deterministic fallback coaching text for Module B reports.

`compose_template` builds a `RewrittenFeedback` object from the already-graded
`StructuredFeedback` and taxonomy tag messages. It uses no network, randomness, or
external state, so the report remains complete when LLM rewriting is disabled.
"""

from __future__ import annotations

from app.module_b.core.feedback import StructuredFeedback
from app.module_b.core.feedback_contract import RewrittenFeedback

# Bump when report disclaimer copy changes.
CURRENT_DISCLAIMER_VERSION = "v1"

# Display labels used by both template and LLM prompts.
BAND_LABELS = {"Good": "Good", "Poor": "Needs Improvement", "Fair": "Fair"}

_NO_TAGS_MESSAGE = "No specific issues were flagged for this set."

# Quote only the top-ranked tags.
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

    Tags without an English message are skipped rather than shown as blank tips.
    """
    messages: list[str] = []
    for tag in structured.tags:
        if not tag.message:
            continue
        messages.append(tag.message)
        if len(messages) >= _MAX_TAG_MESSAGES:
            break
    return messages
