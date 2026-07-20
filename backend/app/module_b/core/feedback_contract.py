"""Stage 5.17 (Phase 6 continuation): the JSON shape every composed or rewritten
Module B coaching text must satisfy -- `{"summary": "...", "tips": ["...", ...]}`.

Used on both sides of the LLM boundary: `feedback_templates.compose_template` produces
it deterministically, `llm_client.GroqClient.rewrite_feedback` parses a model's raw reply
against it, and `crud.feedback_summary` parses a stored row back into it for the frontend
to render as a real list. This module only validates SHAPE (is it a JSON object with the
right keys and types) -- it deliberately knows nothing about markdown characters, grade
integrity, or forbidden phrases; those are content-policy concerns and stay owned by
`feedback_safety.py`, the one existing gate for LLM output policy.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass

_CODE_FENCE_RE = re.compile(r"^```[a-zA-Z]*\n?|\n?```$")


@dataclass(frozen=True)
class RewrittenFeedback:
    """A validated `{summary, tips}` pair -- never constructed with empty/blank strings."""

    summary: str
    tips: tuple[str, ...]


def serialize(feedback: RewrittenFeedback) -> str:
    """Canonical JSON encoding -- the one shape ever written to a DB row."""
    return json.dumps(
        {"summary": feedback.summary, "tips": list(feedback.tips)}, ensure_ascii=False
    )


def build(summary: str, tips: Sequence[str]) -> RewrittenFeedback:
    """Construct + serialize in one step for callers that don't need the dataclass."""
    return RewrittenFeedback(summary=summary, tips=tuple(tips))


def parse(candidate: str) -> RewrittenFeedback | None:
    """Parse and shape-validate; `None` on any violation (never raises).

    Strips a wrapping ```-fence first, since LLMs routinely add one despite being told
    not to -- accepting it costs nothing here and only genuine markdown CONTENT is
    still `feedback_safety`'s job to reject, not this function's.
    """
    try:
        data = json.loads(_CODE_FENCE_RE.sub("", candidate.strip()).strip())
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None

    summary = data.get("summary")
    tips = data.get("tips")
    if not isinstance(summary, str) or not summary.strip():
        return None
    if not isinstance(tips, list) or not all(
        isinstance(tip, str) and tip.strip() for tip in tips
    ):
        return None

    return RewrittenFeedback(
        summary=summary.strip(), tips=tuple(tip.strip() for tip in tips)
    )


def joined_text(feedback: RewrittenFeedback) -> str:
    """Flatten to plain text for content-policy checks that scan for a phrase/number."""
    return " ".join([feedback.summary, *feedback.tips])
