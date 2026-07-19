"""Stage 6.4: the Groq adapter -- provider-agnostic client, retry/timeout behaviour,
and proof that the live/pre-analyze pipeline never reaches it (after-set only)."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import httpx

from app.module_b.core.evaluation.replay_squat_session import (
    CORPUS_DIR,
    analyse_frames,
    load_frames_from_json,
)
from app.module_b.core.feedback import build_structured_feedback
from app.module_b.core.llm_client import GROQ_MODEL, GroqClient, _chat_payload


def _structured(tags=None):
    summary = {
        "band": "Poor",
        "score": 5.0,
        "confidence": 0.6,
        "metrics": {"rule_subscores": [], "per_rep_summaries": [{}, {}]},
        "error_tags": tags or [],
    }
    return build_structured_feedback(summary)


class _FakeResponse:
    def __init__(self, status_code: int, json_body: dict | None = None) -> None:
        self.status_code = status_code
        self._json_body = json_body or {}
        request = httpx.Request(
            "POST", "https://api.groq.com/openai/v1/chat/completions"
        )
        self.request = request

    def json(self) -> dict:
        return self._json_body

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"status {self.status_code}",
                request=self.request,
                response=httpx.Response(self.status_code, request=self.request),
            )


class GroqClientSuccessTests(unittest.TestCase):
    def test_successful_rewrite_returns_text(self) -> None:
        ok_response = _FakeResponse(
            200, {"choices": [{"message": {"content": "Nice set, keep it up."}}]}
        )
        with patch(
            "app.module_b.core.llm_client.httpx.post", return_value=ok_response
        ) as post:
            client = GroqClient(api_key="test-key")
            result = client.rewrite_feedback(structured=_structured())

        self.assertEqual(result.text, "Nice set, keep it up.")
        self.assertEqual(result.provider, "groq")
        self.assertEqual(result.model_version, GROQ_MODEL)
        self.assertEqual(post.call_count, 1)  # no retry needed on success


class GroqClientFailureTests(unittest.TestCase):
    def test_timeout_retries_once_then_fails(self) -> None:
        with patch(
            "app.module_b.core.llm_client.httpx.post",
            side_effect=httpx.TimeoutException("timed out"),
        ) as post:
            client = GroqClient(api_key="test-key")
            result = client.rewrite_feedback(structured=_structured())

        self.assertIsNone(result.text)
        self.assertIn("transport_error", result.error)
        self.assertEqual(post.call_count, 2)  # one try + one retry

    def test_429_retries_once(self) -> None:
        rate_limited = _FakeResponse(429)
        with patch(
            "app.module_b.core.llm_client.httpx.post", return_value=rate_limited
        ) as post:
            client = GroqClient(api_key="test-key")
            result = client.rewrite_feedback(structured=_structured())

        self.assertIsNone(result.text)
        self.assertEqual(result.error, "http_429")
        self.assertEqual(post.call_count, 2)

    def test_non_429_error_does_not_retry(self) -> None:
        server_error = _FakeResponse(500)
        with patch(
            "app.module_b.core.llm_client.httpx.post", return_value=server_error
        ) as post:
            client = GroqClient(api_key="test-key")
            result = client.rewrite_feedback(structured=_structured())

        self.assertIsNone(result.text)
        self.assertEqual(result.error, "http_500")
        self.assertEqual(
            post.call_count, 1
        )  # 4xx/5xx other than 429 won't self-resolve

    def test_empty_content_is_treated_as_failure(self) -> None:
        empty_response = _FakeResponse(200, {"choices": [{"message": {"content": ""}}]})
        with patch(
            "app.module_b.core.llm_client.httpx.post", return_value=empty_response
        ) as post:
            client = GroqClient(api_key="test-key")
            result = client.rewrite_feedback(structured=_structured())

        self.assertIsNone(result.text)
        self.assertEqual(post.call_count, 2)  # retried, still empty both times


class PayloadContentTests(unittest.TestCase):
    def test_payload_carries_only_metrics_and_tags_never_raw_frames(self) -> None:
        structured = _structured(
            tags=[
                {
                    "tag": "insufficient_depth",
                    "severity": "high",
                    "source": "rule",
                    "message": "Didn't reach enough depth.",
                }
            ]
        )
        payload = _chat_payload(GROQ_MODEL, structured)

        user_message = payload["messages"][1]["content"]
        self.assertIn("insufficient_depth", user_message)
        self.assertIn("Poor", user_message)
        # No landmark/frame-shaped keys can appear -- StructuredFeedback never carries
        # them in the first place, so this also guards against a future field addition.
        for forbidden in ("worldLandmarks", "timestampMs", "frames"):
            self.assertNotIn(forbidden, user_message)


class LiveLoopMakesNoLlmCallTests(unittest.TestCase):
    """The Stage 6.4 client is only ever called from `_build_and_save_feedback`, itself
    only reachable from `POST /analyze` after a set is fully scored. This proves the
    pre-analyze pipeline (quality/preprocessing/segmentation/features/rules/fusion/gates
    -- everything that would run during live capture) never touches the network."""

    def test_pre_analyze_pipeline_never_calls_the_network(self) -> None:
        manifest = json.loads((CORPUS_DIR / "labels.json").read_text())
        sample = manifest["samples"][0]
        frames = load_frames_from_json(str(CORPUS_DIR / sample["frames_file"]))

        def _fail_if_called(*_args, **_kwargs):
            raise AssertionError(
                "the pre-analyze/live pipeline must never make an HTTP call"
            )

        with patch("httpx.post", side_effect=_fail_if_called):
            result = analyse_frames(frames)

        self.assertIn("band", result)  # the real pipeline ran and produced a result


if __name__ == "__main__":
    unittest.main()
