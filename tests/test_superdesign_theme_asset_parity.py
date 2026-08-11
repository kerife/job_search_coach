"""Keep Superdesign raw CSS dumps synchronized with shipped assets."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / ".superdesign" / "init" / "theme.md"
ASSETS = ROOT / "plugins" / "professional-growth-coach" / "assets"
ASSET_NAMES = (
    "executive-career-dossier-v1.css",
    "recruiter-practice-session-v1.css",
    "private-recruiter-reply-triage-v1.css",
)


def _theme_dump(name: str) -> str:
    text = THEME.read_text(encoding="utf-8")
    heading = f"### `plugins/professional-growth-coach/assets/{name}`"
    start = text.index(heading)
    fence_start = text.index("```css\n", start) + len("```css\n")
    fence_end = text.index("\n```", fence_start)
    return text[fence_start:fence_end] + "\n"


class SuperdesignThemeAssetParityTests(unittest.TestCase):
    def test_private_css_dumps_match_shipped_assets(self):
        for name in ASSET_NAMES:
            with self.subTest(name=name):
                self.assertEqual((ASSETS / name).read_text(encoding="utf-8"), _theme_dump(name))


if __name__ == "__main__":
    unittest.main()
