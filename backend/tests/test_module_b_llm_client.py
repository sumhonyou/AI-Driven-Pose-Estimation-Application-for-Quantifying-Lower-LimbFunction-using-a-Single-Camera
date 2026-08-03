"""Groq feedback rewrite adapter tests."""

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
        # Stage 5.17: the model must reply with the {summary, tips} JSON contract.
        ok_response = _FakeResponse(
            200,
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {"summary": "Nice set, keep it up.", "tips": []}
                            )
                        }
                    }
                ]
            },
        )
        with patch(
            "app.module_b.core.llm_client.httpx.post", return_value=ok_response
        ) as post:
            client = GroqClient(api_key="test-key")
            result = client.rewrite_feedback(structured=_structured())

        self.assertEqual(
            json.loads(result.text), {"summary": "Nice set, keep it up.", "tips": []}
        )
        self.assertEqual(result.provider, "groq")
        self.assertEqual(result.model_version, GROQ_MODEL)
        self.assertEqual(post.call_count, 1)  # no retry needed on success

    def test_a_wrapping_code_fence_is_tolerated(self) -> None:
        """LLMs routinely wrap JSON in ```-fences despite being told not to; the parser
        strips it rather than treating a cosmetic habit as a contract violation."""
        fenced = (
            "```json\n" + json.dumps({"summary": "Good set.", "tips": []}) + "\n```"
        )
        ok_response = _FakeResponse(
            200, {"choices": [{"message": {"content": fenced}}]}
        )
        with patch("app.module_b.core.llm_client.httpx.post", return_value=ok_response):
            client = GroqClient(api_key="test-key")
            result = client.rewrite_feedback(structured=_structured())

        self.assertEqual(json.loads(result.text), {"summary": "Good set.", "tips": []})


class GroqClientFailureTests(unittest.TestCase):
    def test_timeout_retries_once_then_fails(self) -> None:
        # UAT remediation (Stage R3): a timeout is now its own distinct error label
        # (was folded into "transport_error:..." before), so router.py's
        # fallback_reason telemetry can tell a slow API apart from a dead connection.
        with patch(
            "app.module_b.core.llm_client.httpx.post",
            side_effect=httpx.TimeoutException("timed out"),
        ) as post:
            client = GroqClient(api_key="test-key")
            result = client.rewrite_feedback(structured=_structured())

        self.assertIsNone(result.text)
        self.assertEqual(result.error, "timeout")
        self.assertEqual(post.call_count, 2)  # one try + one retry

    def test_connection_error_is_reported_as_transport_error(self) -> None:
        with patch(
            "app.module_b.core.llm_client.httpx.post",
            side_effect=httpx.ConnectError("connection refused"),
        ) as post:
            client = GroqClient(api_key="test-key")
            result = client.rewrite_feedback(structured=_structured())

        self.assertIsNone(result.text)
        self.assertIn("transport_error", result.error)
        self.assertEqual(post.call_count, 2)

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

    def test_malformed_json_is_retried_then_treated_as_failure(self) -> None:
        """Stage 5.17: a reply that ignores the JSON contract is treated exactly like a
        timeout -- retried once, then surfaced as a failure, never shown half-parsed."""
        prose_response = _FakeResponse(
            200,
            {"choices": [{"message": {"content": "Great set! Keep it up."}}]},
        )
        with patch(
            "app.module_b.core.llm_client.httpx.post", return_value=prose_response
        ) as post:
            client = GroqClient(api_key="test-key")
            result = client.rewrite_feedback(structured=_structured())

        self.assertIsNone(result.text)
        self.assertEqual(result.error, "invalid_json")
        self.assertEqual(post.call_count, 2)  # retried, still malformed both times

    def test_valid_json_missing_the_tips_key_is_treated_as_failure(self) -> None:
        wrong_shape = _FakeResponse(
            200, {"choices": [{"message": {"content": json.dumps({"summary": "Ok."})}}]}
        )
        with patch(
            "app.module_b.core.llm_client.httpx.post", return_value=wrong_shape
        ) as post:
            client = GroqClient(api_key="test-key")
            result = client.rewrite_feedback(structured=_structured())

        self.assertIsNone(result.text)
        self.assertEqual(result.error, "invalid_json")
        self.assertEqual(post.call_count, 2)


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
        # Stage 5.17: the DISPLAY label goes to the model, never the internal "Poor"
        # value -- otherwise nothing stops it writing "the Poor band" verbatim, which
        # then contradicts the UI's own relabelling.
        self.assertIn("Needs Improvement", user_message)
        self.assertNotIn("'Poor'", user_message)
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
