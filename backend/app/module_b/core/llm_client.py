"""Optional after-set LLM rewrite for Module B feedback.

The LLM may rewrite wording only. It never decides grades, tags, faults, or scores.
The caller always has deterministic template feedback to fall back to, and every LLM
response must pass `feedback_safety.check_llm_feedback` before storage.

This client is reached only from `/api/module-b/analyze`, after the full set has already
been scored.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

from app.module_b.core.feedback import StructuredFeedback
from app.module_b.core.feedback_contract import parse as parse_feedback_contract
from app.module_b.core.feedback_contract import serialize as serialize_feedback_contract
from app.module_b.core.feedback_templates import band_label

# Re-verified against https://console.groq.com/docs/models and
# https://console.groq.com/docs/rate-limits on 2026-07-19 (task.md Q7 -- free tiers
# drift; see docs/groq_model_verification.md for the full record). Free tier at that
# date: 30 RPM / 1,000 RPD / 12,000 TPM / 100,000 TPD for this exact model id.
#
# This is only the DEFAULT -- `core/router.py` actually passes `settings.llm_model`
# (env var `LLM_MODEL`) into `GroqClient`, so a developer can point at a different
# Groq-hosted model by editing `.env`, no code change needed. Kept here as the
# fallback for direct `GroqClient(...)` construction (e.g. in tests) with no model
# argument.
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

_TIMEOUT_S = 8.0
_MAX_ATTEMPTS = 2  # one try plus one retry

_SYSTEM_PROMPT = (
    "You rewrite a movement-quality coaching report for readability only. "
    "Rules: do not add any medical claim or diagnosis; do not use a clinical or "
    "diagnostic verb (e.g. never say something is 'normal', 'healthy', or "
    "'diagnosed'); do not introduce a fault, tag, or coaching cue that is not "
    "already given in the input tags below -- if no tags are given, write general "
    "encouragement only, with no specific technique advice; keep it brief, "
    "plain-language, and encouraging. Use the exact band word given in the input -- "
    "never invent a different one, and never restate it as a different word.\n\n"
    "Never state a numeric score, fraction (like '8/10'), or percentage anywhere in "
    "your reply, even approximately -- the exact number is already shown elsewhere in "
    "the report, so restating it risks stating the wrong one. Describe overall "
    "performance in words only (e.g. 'strong set', 'a good effort', 'room to grow').\n\n"
    "Reply with ONLY a JSON object of this exact shape -- no markdown, no code fences, "
    "no preamble or explanation before or after it:\n"
    '{"summary": "<one short sentence stating the band and overall impression, with '
    'no numbers>", "tips": ["<short plain-text tip>", "..."]}\n'
    "Each tip must be plain prose: no asterisks, no bullet characters, no bold/italic "
    "markup, no numbering."
)


@dataclass(frozen=True)
class LlmRewriteResult:
    """`text=None` means the call failed (timeout/error/429) -- always safe to ignore
    and fall back to the template; `text` being present does NOT mean it is safe to
    show as-is, `feedback_safety.check_llm_feedback` still has to approve it."""

    text: str | None
    provider: str
    model_version: str
    error: str | None = None


class LlmClient(Protocol):
    """The shape any provider adapter must implement (provider-agnostic per the plan)."""

    provider: str
    model_version: str

    def rewrite_feedback(
        self, *, structured: StructuredFeedback
    ) -> LlmRewriteResult: ...


class GroqClient:
    """OpenAI-compatible chat-completion client for Groq's hosted Llama 3.3 70B."""

    provider = "groq"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = GROQ_MODEL,
        base_url: str = GROQ_BASE_URL,
        timeout_s: float = _TIMEOUT_S,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._timeout_s = timeout_s

    @property
    def model_version(self) -> str:
        return self._model

    def rewrite_feedback(self, *, structured: StructuredFeedback) -> LlmRewriteResult:
        payload = _chat_payload(self._model, structured)
        last_error: str | None = None
        for _attempt in range(_MAX_ATTEMPTS):
            try:
                response = httpx.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    timeout=self._timeout_s,
                )
                response.raise_for_status()
                raw_text = _extract_text(response.json())
                if raw_text:
                    # Malformed replies are retried once, then treated as a safe
                    # template fallback.
                    parsed = parse_feedback_contract(raw_text)
                    if parsed is not None:
                        return LlmRewriteResult(
                            text=serialize_feedback_contract(parsed),
                            provider=self.provider,
                            model_version=self._model,
                        )
                    last_error = "invalid_json"
                else:
                    last_error = "empty_response"
            except httpx.HTTPStatusError as exc:
                last_error = f"http_{exc.response.status_code}"
                if exc.response.status_code != 429:
                    break  # only 429 is worth a retry; other 4xx/5xx won't self-resolve
            except httpx.TimeoutException:
                # Caught ahead of the generic HTTPError below (TimeoutException is a
                # subclass of it) so a slow Groq response is distinguishable in
                # fallback_reason telemetry from a connection-level transport error.
                last_error = "timeout"
            except httpx.HTTPError as exc:
                last_error = f"transport_error:{exc}"
        return LlmRewriteResult(
            text=None,
            provider=self.provider,
            model_version=self._model,
            error=last_error,
        )


def _chat_payload(model: str, structured: StructuredFeedback) -> dict:
    """Metrics + tags only -- never raw video, never health records (the app persists
    only metrics anyway; see `StructuredFeedback`, which never carries frames)."""
    user_content = {
        # Prompt with the display label, not the internal stored band name.
        "band": band_label(structured.band),
        "score": structured.score,
        "confidence": structured.confidence,
        "rep_count": structured.rep_count,
        "tags": [
            {"tag": tag.tag, "severity": tag.severity, "message": tag.message}
            for tag in structured.tags
        ],
    }
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": str(user_content)},
        ],
        "temperature": 0.3,
        "max_tokens": 200,
    }


def _extract_text(response_json: dict) -> str | None:
    choices = response_json.get("choices") or []
    if not choices:
        return None
    content = choices[0].get("message", {}).get("content")
    return content.strip() if isinstance(content, str) else None
