import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from private_prose_safety import (
    contains_unicode_controls,
    format_bounded_diagnostics,
    is_safe_prose_text,
    safe_diagnostic_field_name,
)


class PrivateProseSafetyTests(unittest.TestCase):
    def test_contains_unicode_controls_rejects_unicode_format_controls(self):
        for character in ("\u200b", "\u202e", "\u2066", "\ufeff"):
            with self.subTest(code_point=f"U+{ord(character):04X}"):
                self.assertTrue(contains_unicode_controls(f"visible{character}text"))

    def test_contains_unicode_controls_rejects_ascii_control_characters(self):
        self.assertTrue(contains_unicode_controls("visible\u0000text"))

    def test_contains_unicode_controls_accepts_visible_whitespace(self):
        self.assertFalse(contains_unicode_controls("  Visible prose with whitespace  "))

    def test_is_safe_prose_text_rejects_non_strings(self):
        for value in (None, 7, {"text": "visible"}):
            with self.subTest(value_type=type(value).__name__):
                self.assertFalse(is_safe_prose_text(value))

    def test_is_safe_prose_text_rejects_unicode_controls(self):
        for character in ("\u200b", "\u202e", "\u2066", "\ufeff"):
            with self.subTest(code_point=f"U+{ord(character):04X}"):
                self.assertFalse(is_safe_prose_text(f"visible{character}text"))

    def test_is_safe_prose_text_accepts_normal_visible_prose_and_whitespace(self):
        self.assertTrue(is_safe_prose_text("  Visible prose with whitespace  "))

    def test_safe_diagnostic_field_name_redacts_suspicious_names_only(self):
        cases = {
            "extra": "extra",
            "person@example.invalid": "<redacted-field>",
            "/Users/synthetic/private-case.json": "<redacted-field>",
            "~/synthetic/private-case.json": "<redacted-field>",
            "../synthetic/profile.json": "<redacted-field>",
            "www.example.invalid/profile": "<redacted-field>",
            "linkedin.com/in/synthetic": "<redacted-field>",
            "+52 55 1234 5678": "<redacted-field>",
            "555-123-4567": "<redacted-field>",
            "token_sk_live_SYNTHETIC": "<redacted-field>",
            "candidate\u200bpath": "<redacted-field>",
            "candidate\u202eprofile": "<redacted-field>",
            "candidate\nprofile": "<redacted-field>",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(expected, safe_diagnostic_field_name(value))

    def test_format_bounded_diagnostics_preserves_short_messages(self):
        self.assertEqual(
            "first diagnostic\nsecond diagnostic\n",
            format_bounded_diagnostics(["first diagnostic", "second diagnostic"]),
        )
        message = "x" * 20
        marker = "validation diagnostics truncated; additional errors omitted\n"
        budget = len(marker.encode("utf-8")) + len(message)
        self.assertEqual(message + "\n", format_bounded_diagnostics([message], max_bytes=budget))

    def test_format_bounded_diagnostics_caps_utf8_output_with_marker(self):
        rendered = format_bounded_diagnostics(["campo-ñ-" + ("x" * 100) for _ in range(400)])
        self.assertLessEqual(len(rendered.encode("utf-8")), 16_384)
        self.assertTrue(rendered.endswith("validation diagnostics truncated; additional errors omitted\n"))


if __name__ == "__main__":
    unittest.main()
