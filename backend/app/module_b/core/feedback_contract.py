"""JSON contract for Module B coaching text.

Both template and LLM feedback use `{"summary": "...", "tips": ["...", ...]}`. This
module validates shape only. Content policy checks, such as forbidden wording or grade
integrity, belong in `feedback_safety.py`.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass

_CODE_FENCE_RE = re.compile(r"^```[a-zA-Z]*\n?|\n?```$")


@dataclass(frozen=True)
class RewrittenFeedback:
    """A validated `{summary, tips}` pair with no blank strings."""

    summary: str
    tips: tuple[str, ...]


def serialize(feedback: RewrittenFeedback) -> str:
    """Canonical JSON encoding written to feedback DB rows."""
    return json.dumps(
        {"summary": feedback.summary, "tips": list(feedback.tips)}, ensure_ascii=False
    )


def build(summary: str, tips: Sequence[str]) -> RewrittenFeedback:
    """Construct + serialize in one step for callers that don't need the dataclass."""
    return RewrittenFeedback(summary=summary, tips=tuple(tips))


def parse(candidate: str) -> RewrittenFeedback | None:
    """Parse and shape-validate; `None` on any violation (never raises).

    Strips a wrapping ```-fence first, since LLMs routinely add one despite being told
        not to. Markdown inside the actual text is checked by `feedback_safety`.
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
