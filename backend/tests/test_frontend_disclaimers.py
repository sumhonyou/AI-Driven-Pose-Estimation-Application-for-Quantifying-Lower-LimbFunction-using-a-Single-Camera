"""Guards against over-claiming clinical language in the frontend's user-facing copy.

PhysioFit is a non-diagnostic self-check tool (rules.md #3). Report/live/dashboard
strings must never state a clinical conclusion (e.g. "your balance is normal").
Allowed: "your holding time was in the Good/Fair/Poor band" and negated statements
like "not a medical diagnosis" -- this test only flags affirmative clinical claims.

There is no JS test runner configured in this project (no vitest/jest in
frontend/package.json), so this reads the i18n source files as plain text rather
than importing/parsing them as TypeScript.
"""

import re
import unittest
from pathlib import Path

FRONTEND_I18N_DIR = Path(__file__).resolve().parents[2] / "frontend" / "src" / "i18n"

FORBIDDEN_PHRASES = [
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
]

STRING_LITERAL_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def _extract_string_literals(text: str) -> list[str]:
    return STRING_LITERAL_RE.findall(text)


class FrontendDisclaimerTests(unittest.TestCase):
    def test_i18n_files_exist(self):
        self.assertTrue(FRONTEND_I18N_DIR.is_dir(), f"missing {FRONTEND_I18N_DIR}")

    def test_no_forbidden_clinical_phrases_in_any_locale(self):
        locale_files = sorted(FRONTEND_I18N_DIR.glob("*.ts"))
        self.assertTrue(locale_files, "no i18n locale files found")

        violations = []
        for path in locale_files:
            text = path.read_text(encoding="utf-8")
            for literal in _extract_string_literals(text):
                lowered = literal.lower()
                for phrase in FORBIDDEN_PHRASES:
                    if phrase in lowered:
                        violations.append(f"{path.name}: '{phrase}' in {literal!r}")

        self.assertEqual(
            violations,
            [],
            "Forbidden clinical-claim phrasing found:\n" + "\n".join(violations),
        )

    def test_sls_report_has_non_diagnostic_disclaimer(self):
        en_text = (FRONTEND_I18N_DIR / "en.ts").read_text(encoding="utf-8")
        self.assertIn("functional self-check", en_text.lower())
        self.assertIn("not a clinical diagnosis", en_text.lower())

    def test_module_b_i18n_blocks_are_covered_by_the_safety_scan(self):
        """Keep squat and Module B copy inside the non-diagnostic locale guard."""
        for locale in ("en.ts", "zh.ts", "ms.ts"):
            text = (FRONTEND_I18N_DIR / locale).read_text(encoding="utf-8")
            self.assertIn("squat: {", text, f"{locale} is missing squat copy")
            self.assertIn("moduleB: {", text, f"{locale} is missing Module B copy")
            self.assertIn(
                "moduleBPlaceholderNotice",
                text,
                f"{locale} is missing the placeholder-model notice",
            )

            literals = _extract_string_literals(text)
            for phrase in FORBIDDEN_PHRASES:
                self.assertFalse(
                    any(phrase in literal.lower() for literal in literals),
                    f"{locale} Module B safety scan found '{phrase}'",
                )


if __name__ == "__main__":
    unittest.main()
