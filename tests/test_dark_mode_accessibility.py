"""Static dark-mode contract for long Professional Growth Coach surfaces."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "plugins" / "professional-growth-coach" / "assets"

SURFACES = {
    "executive-career-dossier-v1.css": (".dossier-document", "--gold: #f2c970;"),
    "recruiter-practice-session-v1.css": (".recruiter-practice-document", "--decision-term: #f5d68a;"),
    "private-recruiter-reply-triage-v1.css": (".private-recruiter-triage-document", "--decision-term: #f5d68a;"),
}

TOKENS = {
    "--paper": "#101521",
    "--surface": "#182235",
    "--ink": "#f3f6ff",
    "--muted": "#b8c4d8",
    "--line": "#5f718e",
    "--forest": "#8fc9b0",
    "--coral": "#ff9f8d",
}


def _relative_luminance(hex_color: str) -> float:
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    light = max(_relative_luminance(first), _relative_luminance(second))
    dark = min(_relative_luminance(first), _relative_luminance(second))
    return (light + 0.05) / (dark + 0.05)


class DarkModeAccessibilityTests(unittest.TestCase):
    def test_long_surfaces_have_screen_only_dark_contract_before_print(self) -> None:
        for filename, (scope, extra_token) in SURFACES.items():
            with self.subTest(filename=filename):
                css = (ASSETS / filename).read_text(encoding="utf-8")
                dark_marker = "@media screen and (prefers-color-scheme: dark)"
                self.assertIn(dark_marker, css)
                dark_start = css.index(dark_marker)
                print_start = css.index("@media print")
                self.assertLess(dark_start, print_start)
                dark_block = css[dark_start:print_start]
                self.assertIn("color-scheme: dark", dark_block)
                self.assertIn(scope, dark_block)
                for token, value in TOKENS.items():
                    self.assertIn(f"{token}: {value};", dark_block)
                self.assertIn(extra_token, dark_block)
                self.assertRegex(css[print_start:], r"background:\s*#(?:fff|ffffff)")

    def test_dark_palette_meets_contrast_floor(self) -> None:
        for foreground in (TOKENS["--ink"], TOKENS["--muted"], TOKENS["--forest"], TOKENS["--coral"]):
            with self.subTest(foreground=foreground):
                self.assertGreaterEqual(_contrast(foreground, TOKENS["--surface"]), 4.5)
        self.assertGreaterEqual(_contrast(TOKENS["--line"], TOKENS["--surface"]), 3.0)

    def test_forced_colors_keeps_footer_boundary_readable(self) -> None:
        selectors = {
            "executive-career-dossier-v1.css": ".footer",
            "recruiter-practice-session-v1.css": ".practice-footer",
            "private-recruiter-reply-triage-v1.css": ".triage-footer",
        }
        for filename, selector in selectors.items():
            with self.subTest(filename=filename):
                css = (ASSETS / filename).read_text(encoding="utf-8")
                forced_start = css.index("@media (forced-colors: active)")
                forced = css[forced_start:]
                self.assertIn(selector, forced)
                self.assertIn("color: CanvasText", forced)
                self.assertIn("border-color: CanvasText", forced)

