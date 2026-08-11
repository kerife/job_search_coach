import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from private_prose_safety import (
    contains_unicode_controls,
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
            "token_sk_live_SYNTHETIC": "<redacted-field>",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(expected, safe_diagnostic_field_name(value))


if __name__ == "__main__":
    unittest.main()
