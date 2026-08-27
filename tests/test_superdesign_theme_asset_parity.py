"""Keep Superdesign raw CSS dumps synchronized with shipped assets."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / ".superdesign" / "init" / "theme.md"
COMPONENTS = ROOT / ".superdesign" / "init" / "components.md"
LAYOUTS = ROOT / ".superdesign" / "init" / "layouts.md"
ASSETS = ROOT / "plugins" / "professional-growth-coach" / "assets"
ASSET_NAMES = (
    "executive-career-dossier-v1.css",
    "executive-career-dossier-v2.css",
    "career-market-learning-dossier-v1.css",
    "recruiter-practice-session-v1.css",
    "private-recruiter-reply-triage-v1.css",
    "private-recruiter-followthrough-checkpoint-v1.css",
    "private-recruiter-conversion-outcome-v1.css",
    "recruiter-target-shortlist-v1.css",
    "recruiter-target-decision-gate-v1.css",
    "recruiter-target-screen-intake-v1.css",
    "private-recruiter-screen-debrief-v1.css",
    "private-recruiter-next-stage-review-v1.css",
)
EXPECTED_THEME_ASSET_NAMES = {
    "executive-career-dossier-v1.css",
    "executive-career-dossier-v2.css",
    "career-market-learning-dossier-v1.css",
    "recruiter-practice-session-v1.css",
    "private-recruiter-reply-triage-v1.css",
    "private-recruiter-followthrough-checkpoint-v1.css",
    "private-recruiter-conversion-outcome-v1.css",
    "recruiter-target-shortlist-v1.css",
    "recruiter-target-decision-gate-v1.css",
    "recruiter-target-screen-intake-v1.css",
    "private-recruiter-screen-debrief-v1.css",
    "private-recruiter-next-stage-review-v1.css",
}
HTML_ASSET_NAMES = (
    "executive-career-dossier-v1.html",
    "recruiter-practice-session-v1.html",
    "private-recruiter-reply-triage-v1.html",
    "private-recruiter-followthrough-checkpoint-v1.html",
    "private-recruiter-conversion-outcome-v1.html",
    "recruiter-target-shortlist-v1.html",
    "recruiter-target-decision-gate-v1.html",
    "recruiter-target-screen-intake-v1.html",
    "private-recruiter-screen-debrief-v1.html",
    "private-recruiter-next-stage-review-v1.html",
)
EXPECTED_LAYOUT_SOURCES = {
    f"plugins/professional-growth-coach/assets/{name}"
    for name in HTML_ASSET_NAMES
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


def _layout_sources() -> dict[str, bytes]:
    text = LAYOUTS.read_text(encoding="utf-8")
    sources = re.findall(
        r"^- Source: `([^`]+\.html)`$.*?\n```html\n(.*?)\n```",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return {source: (dump + "\n").encode("utf-8") for source, dump in sources}


class SuperdesignThemeAssetParityTests(unittest.TestCase):
    def test_superdesign_docs_describe_current_asset_inventory_and_tokens(self):
        components = COMPONENTS.read_text(encoding="utf-8")
        theme = THEME.read_text(encoding="utf-8")
        self.assertIn("twelve standalone CSS files", components)
        self.assertIn("--line #b8c7c0", theme)
        self.assertIn("--decision-term #dfbf70", theme)
        self.assertIn("--decision-term #f5d68a", theme)

    def test_next_version_bridge_keeps_the_responsive_accessibility_contract(self):
        css = (ASSETS / "recruiter-practice-session-v1.css").read_text(encoding="utf-8")
        selector = r"\.recruiter-practice-document \.practice-next-version"
        steps = r"\.recruiter-practice-document \.practice-next-version ol"

        self.assertRegex(
            css,
            selector
            + r"\s*\{[^}]*max-width: var\(--measure\);[^}]*border-left: 4px solid var\(--forest\);[^}]*background: var\(--forest-soft\);",
        )
        self.assertRegex(
            css,
            steps + r"\s*\{[^}]*grid-template-columns: repeat\(3, minmax\(0, 1fr\)\);",
        )
        self.assertRegex(
            css,
            r"(?s)@media screen and \(prefers-color-scheme: dark\).*?"
            + selector
            + r"\s*\{[^}]*background: var\(--forest-soft\);[^}]*color: var\(--ink\);",
        )
        self.assertRegex(
            css,
            r"(?s)@media \(max-width: 640px\).*?"
            + steps
            + r"\s*\{[^}]*grid-template-columns: 1fr;",
        )
        self.assertRegex(
            css,
            r"(?s)@media \(forced-colors: active\).*?"
            + selector
            + r"\s*\{[^}]*border-color: CanvasText;[^}]*background: Canvas;[^}]*color: CanvasText;",
        )
        self.assertRegex(
            css,
            r"(?s)@media \(prefers-contrast: more\).*?"
            + selector
            + r"\s*\{[^}]*border-width: 2px;[^}]*border-left-width: .5rem;",
        )
        self.assertRegex(
            css,
            r"(?s)@media print.*?"
            + selector
            + r"\s*\{[^}]*break-inside: avoid;[^}]*page-break-inside: avoid;",
        )
        self.assertRegex(
            css,
            r"(?s)@media \(prefers-reduced-motion: reduce\).*?"
            + selector
            + r"\s*\{[^}]*transition: none !important;",
        )

    def test_dossier_coverage_facts_keep_one_column_through_640px(self):
        css = (ASSETS / "executive-career-dossier-v2.css").read_text(encoding="utf-8")
        self.assertRegex(
            css,
            re.compile(
                r"@media screen and \(max-width: 640px\).*?\.section-coverage-facts\s*\{\s*grid-template-columns:\s*1fr;",
                re.DOTALL,
            ),
        )

    def test_market_extension_declares_light_theme_tokens_for_borders_and_text(self):
        base = (ASSETS / "executive-career-dossier-v1.css").read_text(encoding="utf-8")
        market = (ASSETS / "career-market-learning-dossier-v1.css").read_text(encoding="utf-8")
        self.assertRegex(base, r"--line:\s*#[0-9a-f]{6};")
        self.assertRegex(base, r"--muted-text:\s*#[0-9a-f]{6};")
        self.assertIn("color: var(--muted-text)", market)
        self.assertIn(".market-source-meta", market)

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

    def test_compact_action_rails_use_surface_and_non_color_recorded_state(self):
        for name in (
            "private-recruiter-followthrough-checkpoint-v1.css",
            "private-recruiter-conversion-outcome-v1.css",
        ):
            with self.subTest(name=name):
                css = (ASSETS / name).read_text(encoding="utf-8")
                self.assertRegex(
                    css,
                    r"\.continuity-step\s*\{[^}]*background:\s*var\(--surface\);",
                )
                self.assertNotRegex(
                    css,
                    r"\.continuity-step\s*\{[^}]*background:\s*#f4f6fa;",
                )
                self.assertRegex(
                    css,
                    r"\.continuity-step--recorded\s*\{[^}]*border-style:\s*double;",
                )
                contrast = css[css.index("@media (prefers-contrast: more)") :]
                forced = css[css.index("@media (forced-colors: active)") :]
                self.assertRegex(
                    contrast,
                    r"\.continuity-step--recorded\s*\{[^}]*border-color:\s*var\(--ink\);[^}]*color:\s*var\(--ink\);",
                )
                self.assertRegex(
                    forced,
                    r"\.continuity-step--recorded\s*\{[^}]*border-color:\s*CanvasText;[^}]*color:\s*CanvasText;[^}]*border-style:\s*double;",
                )

    def test_compact_blocked_rails_use_dashed_state_across_accessibility_modes(self):
        for name in (
            "private-recruiter-followthrough-checkpoint-v1.css",
            "private-recruiter-conversion-outcome-v1.css",
        ):
            with self.subTest(name=name):
                css = (ASSETS / name).read_text(encoding="utf-8")
                self.assertRegex(
                    css,
                    r"\.continuity-step--blocked\s*\{[^}]*border-left:\s*\.25rem dashed var\(--accent\);",
                )
                dark = css[css.index("@media screen and (prefers-color-scheme: dark)") : css.index("@page")]
                self.assertRegex(
                    dark,
                    r"\.continuity-step--blocked\s*\{[^}]*border-left-color:\s*var\(--accent\);[^}]*border-left-style:\s*dashed;",
                )
                contrast = css[css.index("@media (prefers-contrast: more)") :]
                self.assertRegex(
                    contrast,
                    r"\.continuity-step--blocked\s*\{[^}]*border-left:\s*\.5rem dashed var\(--ink\);",
                )
                forced = css[css.index("@media (forced-colors: active)") :]
                self.assertRegex(
                    forced,
                    r"\.continuity-step--blocked\s*\{[^}]*border-left:\s*\.25rem dashed CanvasText;",
                )

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

    def test_private_html_layout_dumps_match_shipped_assets(self):
        layout_sources = _layout_sources()
        self.assertEqual(set(layout_sources), EXPECTED_LAYOUT_SOURCES)
        for source in sorted(EXPECTED_LAYOUT_SOURCES):
            with self.subTest(source=source):
                self.assertEqual((ROOT / source).read_bytes(), layout_sources[source])

    def test_compact_receipt_layouts_keep_employment_boundary_token(self):
        layout_sources = _layout_sources()
        for source in (
            "plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html",
            "plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html",
        ):
            with self.subTest(source=source):
                self.assertIn(b"{{EMPLOYMENT_BOUNDARY}}", layout_sources[source])


if __name__ == "__main__":
    unittest.main()
