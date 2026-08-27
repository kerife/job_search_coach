from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "plugins" / "professional-growth-coach" / "scripts" / "validate_design_tokens.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("validate_design_tokens", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DesignTokenContractTests(unittest.TestCase):
    def test_recruiter_review_family_covers_the_complete_review_flow(self):
        checker = load_checker()

        expected = {
            "assets/recruiter-target-shortlist-v1.css",
            "assets/recruiter-target-decision-gate-v1.css",
            "assets/recruiter-target-screen-intake-v1.css",
            "assets/private-recruiter-screen-debrief-v1.css",
            "assets/private-recruiter-next-stage-review-v1.css",
        }
        self.assertEqual(expected, set(checker.FAMILY_ASSETS["recruiter_review"]))

    def test_recruiter_review_assets_are_represented_in_superdesign_theme(self):
        checker = load_checker()
        theme = (ROOT / ".superdesign" / "init" / "theme.md").read_text(encoding="utf-8")

        for asset in checker.FAMILY_ASSETS["recruiter_review"]:
            with self.subTest(asset=asset):
                self.assertIn(asset, theme)

    def test_dossier_family_includes_the_v2_extension(self):
        checker = load_checker()

        self.assertIn(
            "assets/executive-career-dossier-v2.css",
            checker.FAMILY_ASSETS["dossier"],
        )

    def test_canonical_assets_pass_their_declared_family_allowlist(self):
        checker = load_checker()

        self.assertEqual([], checker.validate_palette_assets(ROOT / "plugins" / "professional-growth-coach"))

    def test_unapproved_color_is_rejected_without_echoing_css(self):
        checker = load_checker()

        errors = checker.validate_css_text(
            ".artifact { color: #123456; }",
            "practice_triage",
            "synthetic.css",
        )

        self.assertEqual(
            ["practice_triage synthetic.css uses unapproved color #123456"],
            errors,
        )

    def test_family_mismatch_is_rejected(self):
        checker = load_checker()

        errors = checker.validate_css_text(
            ".artifact { color: #315bd6; }",
            "practice_triage",
            "synthetic.css",
        )

        self.assertEqual(
            ["practice_triage synthetic.css uses unapproved color #315bd6"],
            errors,
        )

    def test_three_digit_hex_is_normalized_and_declared(self):
        checker = load_checker()

        self.assertEqual([], checker.validate_css_text(".x { color: #fff; }", "compact_receipt", "synthetic.css"))


if __name__ == "__main__":
    unittest.main()
