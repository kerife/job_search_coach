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
    "private-recruiter-followthrough-checkpoint-v1.css",
    "private-recruiter-conversion-outcome-v1.css",
)
EXPECTED_THEME_ASSET_NAMES = {
    "executive-career-dossier-v1.css",
    "recruiter-practice-session-v1.css",
    "private-recruiter-reply-triage-v1.css",
    "private-recruiter-followthrough-checkpoint-v1.css",
    "private-recruiter-conversion-outcome-v1.css",
}


def _theme_asset_names() -> set[str]:
    text = THEME.read_text(encoding="utf-8")
    return set(
        re.findall(
            r"^### `plugins/professional-growth-coach/assets/([^`]+\.css)`$",
            text,
            re.MULTILINE,
        )
    )


def _theme_dump(name: str) -> str:
    text = THEME.read_text(encoding="utf-8")
    heading = f"### `plugins/professional-growth-coach/assets/{name}`"
    start = text.index(heading)
    fence_start = text.index("```css\n", start) + len("```css\n")
    fence_end = text.index("\n```", fence_start)
    return text[fence_start:fence_end] + "\n"


class SuperdesignThemeAssetParityTests(unittest.TestCase):
    def test_compact_facts_keep_one_column_through_640px(self):
        for name, selector in (
            ("private-recruiter-followthrough-checkpoint-v1.css", ".checkpoint-facts"),
            ("private-recruiter-conversion-outcome-v1.css", ".outcome-facts"),
        ):
            with self.subTest(name=name):
                css = (ASSETS / name).read_text(encoding="utf-8")
                match = re.search(
                    rf"@media \(min-width:\s*([^)]+)\)\s*\{{\s*{re.escape(selector)}\s*\{{\s*grid-template-columns:\s*1fr 1fr;",
                    css,
                )
                self.assertIsNotNone(match)
                breakpoint = match.group(1).strip()
                self.assertEqual(breakpoint, "641px")

    def test_theme_dump_set_covers_every_shipped_css_asset(self):
        self.assertEqual(
            _theme_asset_names(),
            EXPECTED_THEME_ASSET_NAMES,
        )
        self.assertEqual(set(ASSET_NAMES), EXPECTED_THEME_ASSET_NAMES)
        self.assertEqual(
            {path.name for path in ASSETS.glob("*.css")},
            EXPECTED_THEME_ASSET_NAMES,
        )

    def test_private_css_dumps_match_shipped_assets(self):
        for name in ASSET_NAMES:
            with self.subTest(name=name):
                self.assertEqual((ASSETS / name).read_text(encoding="utf-8"), _theme_dump(name))


if __name__ == "__main__":
    unittest.main()
