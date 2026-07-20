"""Make the app's own `logger.info(...)` calls actually reach the terminal.

Without this, Python's root logger defaults to WARNING with no handlers, so every
`logger.info(...)` in the codebase -- including the two that explain exactly why a
report fell back to the template (`module-b feedback llm_failed` / `llm_rejected` in
`module_b/core/router.py`) -- is discarded before it is ever written. The diagnostics
were being produced and then silently dropped, which is why a misconfigured LLM_MODEL
could degrade every report for hours with nothing visible anywhere.

Uvicorn configures only its own `uvicorn.*` loggers, never the root logger, so
configuring root here does not fight it: `app.*` records propagate to root and get
emitted alongside uvicorn's request lines.

Level is env-configurable via LOG_LEVEL (default INFO) so a noisy debugging session can
opt into DEBUG without a code change.
"""

from __future__ import annotations

import logging
import sys

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s | %(message)s"
_DATE_FORMAT = "%H:%M:%S"


def configure_logging(level: str) -> None:
    """Attach a stdout handler to the root logger, once, at `level`.

    Idempotent under `uvicorn --reload`: a reload re-imports `app.main`, and adding a
    second handler each time would duplicate every line, so an existing handler tagged
    by this function is reused rather than stacked.
    """
    root = logging.getLogger()
    resolved = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(resolved)

    for handler in root.handlers:
        if getattr(handler, "_fyp_configured", False):
            handler.setLevel(resolved)
            return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT))
    handler.setLevel(resolved)
    handler._fyp_configured = True  # type: ignore[attr-defined]
    root.addHandler(handler)

    # httpx logs one INFO line per outbound request, which would narrate every Groq
    # call on its own. The app's own llm_failed/llm_rejected lines already say what
    # matters, with the session id attached; keep httpx at WARNING so real transport
    # errors still surface without the per-request noise.
    logging.getLogger("httpx").setLevel(logging.WARNING)
