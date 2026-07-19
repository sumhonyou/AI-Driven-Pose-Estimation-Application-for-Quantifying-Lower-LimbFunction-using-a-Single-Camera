import asyncio
import json
import unittest

from fastapi import HTTPException

from app.main import app
from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.exercise import ModuleBExercise
from app.module_b.core.registry import get_exercise, registered_exercise_codes
from app.seed import EXERCISES, LEGACY_MODULE_B_CODE


class ModuleBConfigTests(unittest.TestCase):
    def test_core_config_freezes_still_unresolved_stage_4_0_values(self):
        """Values Stage 5.6 did not touch — `w_rule_default`/`w_ml_default`/
        `confidence_low_threshold` moved to Stage 5.6 dataset-derived values below."""
        config = MODULE_B_CORE_CONFIG

        self.assertEqual(
            config["band_thresholds"],
            {
                "poor": {"min_inclusive": 0.0, "max_exclusive": 4.0},
                "fair": {"min_inclusive": 4.0, "max_exclusive": 7.0},
                "good": {"min_inclusive": 7.0, "max_inclusive": 10.0},
            },
        )
        self.assertEqual(config["w_rule_low_confidence"], 0.7)
        self.assertEqual(config["q_min"], 0.6)
        self.assertEqual(config["confidence_threshold"], 0.6)
        self.assertEqual(
            config["quality_bands"],
            {
                "good": {"min_inclusive": 0.85},
                "moderate": {
                    "min_inclusive": 0.70,
                    "max_exclusive": 0.85,
                },
                "poor": {"min_inclusive": 0.0, "max_exclusive": 0.70},
            },
        )
        self.assertEqual(config["feature_schema_version"], "1.0.0")
        self.assertEqual(config["interpolation_max_gap_frames"], 5)

    def test_core_config_stage_5_6_dataset_derived_fusion_values(self):
        """`w_rule_default`/`w_ml_default`/`confidence_low_threshold` are earned by
        Stage 5.6's iterated sweep (see ml/reports/SQUAT_FUSION_SWEEP.md), replacing
        the Stage 4.0 0.4/0.6/0.65 placeholders."""
        config = MODULE_B_CORE_CONFIG

        self.assertEqual(config["w_rule_default"], 0.2)
        self.assertEqual(config["w_ml_default"], 0.8)
        self.assertEqual(config["confidence_low_threshold"], 0.85)


class ModuleBRegistryTests(unittest.TestCase):
    def test_squat_plugin_implements_contract(self):
        exercise = get_exercise("squat")

        self.assertIsInstance(exercise, ModuleBExercise)
        self.assertEqual(exercise.code, "squat")
        self.assertEqual(exercise.required_view, "side_view")
        self.assertEqual(exercise.model_key, "squat")

    def test_registered_exercise_codes_lists_registered_plugins(self):
        # Leg Lunge was removed from the product (2026-07-19); squat is the only
        # registered Module B plugin.
        self.assertEqual(registered_exercise_codes(), ("squat",))

    def test_registry_never_defaults_an_unknown_code(self):
        with self.assertRaises(HTTPException) as raised:
            get_exercise("bogus")

        self.assertEqual(raised.exception.status_code, 404)

    def test_catalog_seed_replaces_module_b_placeholder_with_squat(self):
        codes = {item["code"] for item in EXERCISES}

        self.assertIn("squat", codes)
        self.assertNotIn(LEGACY_MODULE_B_CODE, codes)
        # Leg Lunge was removed from the product (2026-07-19).
        self.assertNotIn("lunge", codes)


class ModuleBRouterTests(unittest.TestCase):
    def _asgi_get(self, path):
        async def run_request():
            messages = []
            request_sent = False

            async def receive():
                nonlocal request_sent
                if request_sent:
                    return {"type": "http.disconnect"}
                request_sent = True
                return {
                    "type": "http.request",
                    "body": b"",
                    "more_body": False,
                }

            async def send(message):
                messages.append(message)

            scope = {
                "type": "http",
                "asgi": {"version": "3.0", "spec_version": "2.3"},
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": path,
                "raw_path": path.encode("ascii"),
                "query_string": b"",
                "headers": [],
                "client": ("testclient", 50000),
                "server": ("testserver", 80),
            }
            await app(scope, receive, send)
            return messages

        messages = asyncio.run(run_request())
        start = next(
            message for message in messages if message["type"] == "http.response.start"
        )
        body = b"".join(
            message.get("body", b"")
            for message in messages
            if message["type"] == "http.response.body"
        )
        return start["status"], json.loads(body)

    def test_main_registers_module_b_config_route(self):
        routes = {
            getattr(route, "path", None): getattr(route, "methods", set())
            for route in app.routes
        }

        self.assertIn("/api/module-b/{code}/config", routes)
        self.assertIn("GET", routes["/api/module-b/{code}/config"])

    def test_squat_config_endpoint_returns_registered_config(self):
        status_code, payload = self._asgi_get("/api/module-b/squat/config")

        self.assertEqual(status_code, 200)
        self.assertEqual(payload["exercise"]["exercise_code"], "squat")
        self.assertEqual(payload["exercise"]["required_view"], "side_view")
        self.assertEqual(payload["core"]["feature_schema_version"], "1.0.0")

    def test_unknown_config_endpoint_returns_404(self):
        status_code, payload = self._asgi_get("/api/module-b/bogus/config")

        self.assertEqual(status_code, 404)
        self.assertIn("bogus", payload["detail"])

    def test_retired_lunge_config_endpoint_returns_404(self):
        """Leg Lunge was removed from the product (2026-07-19); the code must 404
        like any other unregistered exercise, not silently resolve to something else."""
        status_code, payload = self._asgi_get("/api/module-b/lunge/config")

        self.assertEqual(status_code, 404)
        self.assertIn("lunge", payload["detail"])


if __name__ == "__main__":
    unittest.main()
