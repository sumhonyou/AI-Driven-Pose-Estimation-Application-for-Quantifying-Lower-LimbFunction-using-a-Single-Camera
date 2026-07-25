# Groq Model + Free-Tier Verification (Stage 6.4, Q7)

**Retrieval date:** 2026-07-19
**Sources:** `https://console.groq.com/docs/models`, `https://console.groq.com/docs/rate-limits`

task.md flags that Groq's free-tier limits and model list have drifted before (a
documented May–June 2026 model-list purge is precedent) and asks to re-verify at build
time rather than trust the plan's original `llama-3.3-70b` shorthand.

---

## Table of Contents

- [Model id](#model-id)
- [Free-tier limits, as of the retrieval date](#free-tier-limits-as-of-the-retrieval-date)
- [What this means for the implementation](#what-this-means-for-the-implementation)

---

## Model id

The production model id is **`llama-3.3-70b-versatile`** (not the bare `llama-3.3-70b`
the plan doc used as shorthand). This exact string is what `GROQ_MODEL` in
`backend/app/module_b/core/llm_client.py` uses — a stale/wrong model id would throw on
every call rather than silently degrade, which is exactly why this file records the
verification instead of trusting the plan doc's shorthand.

- Context window: 131,072 tokens; max completion: 32,768 tokens.
- Pricing (irrelevant to the free tier, recorded for completeness): $0.59 / M input
  tokens, $0.79 / M output tokens.

## Free-tier limits, as of the retrieval date

| Limit                     | Value   |
| ------------------------- | ------- |
| Requests per minute (RPM) | 30      |
| Requests per day (RPD)    | 1,000   |
| Tokens per minute (TPM)   | 12,000  |
| Tokens per day (TPD)      | 100,000 |

Limits apply at the organization level, not per-user. Whichever limit is hit first
triggers rate limiting — for this app's per-set, after-set-only usage pattern (one
short rewrite call per analyzed set, capped at `max_tokens=200` in the request), the
1,000 RPD / 100,000 TPD ceilings are the ones most likely to matter under classroom-scale
demo traffic, not the per-minute ones.

## What this means for the implementation

- The template fallback (Stage 6.2) means a future silent model deletion, or the free
  tier being fully exhausted mid-demo, degrades to the template — it cannot break the
  report. `GroqClient` retries once on a 429 (rate limit) specifically because that is
  the one failure mode this app's own traffic could plausibly trigger.
- A wrong/stale model id is a _different_ failure mode from rate limiting: it throws a
  4xx immediately (not a 429), which `GroqClient` does not retry (only 429 is retried,
  since other 4xx/5xx won't self-resolve) — it falls straight back to the template. Pin
  and re-check this file's model id before any future deploy, per Q7.
