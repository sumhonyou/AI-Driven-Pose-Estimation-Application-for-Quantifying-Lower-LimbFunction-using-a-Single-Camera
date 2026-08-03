"""The one shared list of forbidden clinical-claim phrases (rules.md #3).

PhysioFit is a non-diagnostic self-check tool. Neither the frontend's static i18n copy
nor any backend-generated text may state a clinical conclusion (e.g. "your balance is
normal") or a diagnosis. Allowed: band statements like "your holding time was in the
Good/Fair/Poor band" and negated statements like "not a medical diagnosis" — only
affirmative clinical claims are forbidden.

This list is imported by both `backend/tests/test_frontend_disclaimers.py` (which scans
the frontend's static i18n source) and `backend/app/module_b/core/feedback_safety.py`
(which scans LLM-generated text before it is stored or shown).
"""

FORBIDDEN_PHRASES: tuple[str, ...] = (
    "your balance is normal",
    "your balance is healthy",
    "your ankle is healthy",
    "your ankles are healthy",
    "you have poor balance",
    "you have good balance",
    "clinically diagnosed",
    "medically diagnosed",
    "diagnosed with",
    "this diagnoses",
    "this confirms you have",
)
