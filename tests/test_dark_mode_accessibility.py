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
    def test_dossier_v2_extension_reuses_tokens_across_accessibility_modes(self) -> None:
        css = (ASSETS / "executive-career-dossier-v2.css").read_text(encoding="utf-8")
        dark = css[css.index("@media screen and (prefers-color-scheme: dark)"):css.index("@media (max-width: 480px)")]
        self.assertNotRegex(dark, r"#[0-9a-fA-F]{3,8}")
        for token in ("var(--surface)", "var(--paper)", "var(--ink)", "var(--forest)"):
            self.assertIn(token, dark)
        forced = css[css.index("@media (forced-colors: active)"):]
        for system_color in ("Canvas", "CanvasText", "Highlight"):
            self.assertIn(system_color, forced)
        contrast = css[css.index("@media (prefers-contrast: more)"):]
        self.assertIn("border-width: 2px", contrast)

    def test_dossier_v2_compact_contract_is_one_column_without_scroll_primitives(self) -> None:
        css = (ASSETS / "executive-career-dossier-v2.css").read_text(encoding="utf-8")
        compact = css[css.index("@media (max-width: 480px)"):css.index("@media (prefers-reduced-motion: reduce)")]
        self.assertIn(".section-coverage-facts { grid-template-columns: 1fr; }", compact)
        self.assertIn("min-width: 0", compact)
        self.assertNotRegex(css, r"overflow-x:\s*(?:auto|scroll)|white-space:\s*nowrap")

    def test_dossier_v2_unavailable_market_next_step_has_responsive_print_and_forced_color_contract(self) -> None:
        css = (ASSETS / "executive-career-dossier-v2.css").read_text(encoding="utf-8")
        self.assertIn(".market-next-investigation", css)
        self.assertIn(".market-next-investigation-facts", css)
        self.assertIn("@media screen and (max-width: 640px)", css)
        self.assertIn("grid-template-columns: 1fr", css)
        self.assertIn(".market-next-investigation", css[css.index("@media print"):])
        forced = css[css.index("@media (forced-colors: active)"):]
        self.assertIn(".market-next-investigation", forced)
        self.assertIn("Canvas", forced)
        contrast = css[css.index("@media (prefers-contrast: more)"):]
        self.assertIn(".market-next-investigation", contrast)

    def test_market_composition_is_non_scrollable_and_forced_color_readable(self) -> None:
        css = (ASSETS / "career-market-learning-dossier-v1.css").read_text(encoding="utf-8")
        self.assertIn("@media screen and (max-width: 680px)", css)
        self.assertIn(".market-matrix td::before", css)
        self.assertIn(".market-alignment-score, .market-recurrence-count", css)
        self.assertIn("font-variant-numeric: tabular-nums", css)
        self.assertIn("content: attr(data-label)", css)
        self.assertNotRegex(css, r"overflow-x:\s*(?:auto|scroll)|white-space:\s*nowrap")
        forced = css[css.index("@media (forced-colors: active)"):]
        for token in ("Canvas", "CanvasText", "Highlight"):
            self.assertIn(token, forced)

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

    def test_recruiter_continuity_markers_meet_dark_mode_contrast_floor(self) -> None:
        cases = (
            ("recruiter-target-shortlist-v1.css", "#75d2e4", "#10232a"),
            ("recruiter-target-decision-gate-v1.css", "#8eb2ff", "#101a35"),
        )
        for filename, accent, marker_ink in cases:
            with self.subTest(filename=filename):
                css = (ASSETS / filename).read_text(encoding="utf-8")
                dark = css[css.index("@media screen and (prefers-color-scheme: dark)"):css.index("@media print")]
                self.assertIn(f"--continuity-marker-ink: {marker_ink};", dark)
                self.assertIn("color: var(--continuity-marker-ink);", css)
                self.assertGreaterEqual(_contrast(accent, marker_ink), 4.5)

    def test_recruiter_continuity_rail_has_intermediate_and_print_layouts(self) -> None:
        surfaces = (
            "recruiter-target-shortlist-v1.css",
            "recruiter-target-decision-gate-v1.css",
            "recruiter-target-screen-intake-v1.css",
            "private-recruiter-screen-debrief-v1.css",
            "private-recruiter-next-stage-review-v1.css",
        )
        for filename in surfaces:
            with self.subTest(filename=filename):
                css = (ASSETS / filename).read_text(encoding="utf-8")
                self.assertIn("@media (min-width: 721px) and (max-width: 900px)", css)
                self.assertIn(".continuity-rail ol { grid-template-columns: repeat(3, minmax(0, 1fr)); }", css)
                self.assertIn("@media screen and (max-width: 420px)", css)
                self.assertIn(".continuity-rail ol { grid-template-columns: 1fr; }", css)
                self.assertIn(".continuity-rail ol { grid-template-columns: repeat(2, minmax(0, 1fr)); }", css[css.index("@media print"):])
                self.assertIn(".continuity-rail__copy strong { overflow-wrap: normal; hyphens: auto; }", css[css.index("@media print"):])

    def test_recruiter_continuity_rail_is_a_static_section_not_navigation(self) -> None:
        surfaces = (
            "recruiter-target-shortlist-v1.html",
            "recruiter-target-decision-gate-v1.html",
            "recruiter-target-screen-intake-v1.html",
            "private-recruiter-screen-debrief-v1.html",
            "private-recruiter-next-stage-review-v1.html",
        )
        for filename in surfaces:
            with self.subTest(filename=filename):
                html = (ASSETS / filename).read_text(encoding="utf-8")
                self.assertIn('<section class="continuity-rail"', html)
                self.assertNotIn('<nav class="continuity-rail"', html)
        css = (ASSETS / "private-recruiter-next-stage-review-v1.css").read_text(encoding="utf-8")
        self.assertIn("@media (prefers-contrast: more)", css)
        self.assertIn(".next-stage-card, .next-stage-guidance", css)

    def test_recruiter_dark_tokens_are_screen_only_and_print_resets_to_light(self) -> None:
        surfaces = (
            "recruiter-target-shortlist-v1.css",
            "recruiter-target-decision-gate-v1.css",
            "recruiter-target-screen-intake-v1.css",
            "private-recruiter-screen-debrief-v1.css",
            "private-recruiter-next-stage-review-v1.css",
        )
        for filename in surfaces:
            with self.subTest(filename=filename):
                css = (ASSETS / filename).read_text(encoding="utf-8")
                self.assertIn("@media screen and (prefers-color-scheme: dark)", css)
                print_css = css[css.index("@media print"):]
                self.assertRegex(print_css, r"color-scheme\s*:\s*light")
                self.assertRegex(print_css, r"background\s*:\s*#fff(?:fff)?")
                self.assertIn("page-break-inside: avoid", print_css)
                if filename in {"recruiter-target-shortlist-v1.css", "recruiter-target-decision-gate-v1.css"}:
                    self.assertIn("break-inside: avoid; page-break-inside: avoid", print_css)

    def test_all_recruiter_templates_block_indexing_and_referrers(self) -> None:
        templates = (
            "recruiter-target-shortlist-v1.html",
            "recruiter-target-decision-gate-v1.html",
            "recruiter-target-screen-intake-v1.html",
            "private-recruiter-screen-debrief-v1.html",
            "private-recruiter-next-stage-review-v1.html",
            "private-recruiter-followthrough-checkpoint-v1.html",
            "private-recruiter-conversion-outcome-v1.html",
            "private-recruiter-reply-triage-v1.html",
            "recruiter-practice-session-v1.html",
            "executive-career-dossier-v1.html",
        )
        for filename in templates:
            with self.subTest(filename=filename):
                html = (ASSETS / filename).read_text(encoding="utf-8")
                self.assertIn('<meta name="robots" content="noindex,nofollow,noarchive">', html)
                self.assertIn('<meta name="referrer" content="no-referrer">', html)

    def test_recruiter_intake_surfaces_share_keyboard_focus_contract(self) -> None:
        expected = {
            "recruiter-target-screen-intake-v1.css": "var(--screen-blue)",
            "private-recruiter-screen-debrief-v1.css": "var(--debrief-blue)",
            "recruiter-target-decision-gate-v1.css": "var(--accent)",
            "private-recruiter-next-stage-review-v1.css": "var(--next-accent)",
        }
        for filename, accent in expected.items():
            with self.subTest(filename=filename):
                css = (ASSETS / filename).read_text(encoding="utf-8")
                self.assertRegex(css, rf"\.skip-link:focus-visible,\s*main:focus-visible\s*\{{[^}}]*outline:\s*3px solid {re.escape(accent)};[^}}]*outline-offset:\s*3px;")
                forced = css[css.index("@media (forced-colors") :]
                self.assertRegex(forced, r"\.skip-link:focus-visible,\s*main:focus-visible\s*\{[^}]*outline:\s*3px solid Highlight;[^}]*outline-offset:\s*3px;")

    def test_screen_intake_dark_blue_meets_text_contrast_floor(self) -> None:
        css = (ASSETS / "recruiter-target-screen-intake-v1.css").read_text(encoding="utf-8")
        dark = css[css.index("@media screen and (prefers-color-scheme: dark)"):css.index("@media print")]
        self.assertIn("--screen-blue: #8eb2ff;", dark)

    def test_screen_and_debrief_dark_controls_keep_text_and_marker_contrast(self) -> None:
        cases = (
            ("recruiter-target-screen-intake-v1.css", "screen", "#1c2738", "#edf2fa", "#8eb2ff"),
            ("private-recruiter-screen-debrief-v1.css", "debrief", "#1c2738", "#edf2fa", "#8eb2ff"),
        )
        for filename, prefix, surface, ink, accent in cases:
            with self.subTest(filename=filename):
                css = (ASSETS / filename).read_text(encoding="utf-8")
                dark = css[css.index("@media screen and (prefers-color-scheme: dark)"):css.index("@media print")]
                self.assertRegex(dark, rf"--{prefix}-marker-ink\s*:\s*#101a35;")
                self.assertRegex(css, rf"color\s*:\s*var\(--{prefix}-surface\);")
                self.assertRegex(css, rf"color\s*:\s*var\(--{prefix}-marker-ink\);")
                self.assertGreaterEqual(_contrast(surface, ink), 4.5)
                self.assertGreaterEqual(_contrast(accent, "#101a35"), 4.5)
                forced = css[css.index("@media (forced-colors") : css.index("@media print")]
                self.assertRegex(forced, r"background\s*:\s*CanvasText")
                self.assertRegex(forced, r"color\s*:\s*Canvas")

    def test_recruiter_dark_high_contrast_borders_meet_non_text_floor(self) -> None:
        cases = (
            ("recruiter-target-shortlist-v1.css", "--line", "#adbac4", "#17212b"),
            ("recruiter-target-screen-intake-v1.css", "--screen-border", "#b9c5d8", "#1c2738"),
            ("private-recruiter-screen-debrief-v1.css", "--debrief-border", "#b9c5d8", "#1c2738"),
            ("private-recruiter-next-stage-review-v1.css", "--next-border", "#b4c0ca", "#18232d"),
        )
        for filename, token, border, surface in cases:
            with self.subTest(filename=filename):
                css = (ASSETS / filename).read_text(encoding="utf-8")
                combined = css[css.index("@media screen and (prefers-color-scheme: dark) and (prefers-contrast: more)"):]
                self.assertIn(f"{token}: {border};", combined)
                self.assertGreaterEqual(_contrast(border, surface), 3.0)

    def test_practice_readiness_grid_becomes_single_column_on_small_screens(self) -> None:
        css = (ASSETS / "recruiter-practice-session-v1.css").read_text(encoding="utf-8")
        self.assertIn("@media screen and (max-width: 420px)", css)
        compact = css[css.index("@media screen and (max-width: 420px)") :]
        self.assertIn(".recruiter-practice-document .screen-readiness-grid { grid-template-columns: 1fr; }", compact)

    def test_practice_readiness_copy_uses_themed_muted_token_in_dark_mode(self) -> None:
        css = (ASSETS / "recruiter-practice-session-v1.css").read_text(encoding="utf-8")
        self.assertIn(".recruiter-practice-document .screen-readiness-intro { max-width: var(--measure); margin: .45rem 0 0; color: var(--muted); }", css)
        self.assertIn(".recruiter-practice-document .screen-readiness-state { display: block; margin-top: .35rem; color: var(--muted);", css)
        self.assertNotIn(".screen-readiness-intro { max-width: var(--measure); margin: .45rem 0 0; color: #46534d; }", css)
        self.assertNotIn(".screen-readiness-state { display: block; margin-top: .35rem; color: #46534d;", css)
        dark = css[css.index("@media screen and (prefers-color-scheme: dark)") : css.index("@keyframes practice-enter")]
        self.assertIn("--muted: #b8c4d8;", dark)

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

    def test_forced_colors_keeps_skip_target_focus_visible(self) -> None:
        surfaces = (
            "executive-career-dossier-v1.css",
            "private-recruiter-followthrough-checkpoint-v1.css",
            "private-recruiter-conversion-outcome-v1.css",
            "recruiter-practice-session-v1.css",
            "private-recruiter-reply-triage-v1.css",
        )
        for filename in surfaces:
            with self.subTest(filename=filename):
                css = (ASSETS / filename).read_text(encoding="utf-8")
                forced_start = css.index("@media (forced-colors: active)")
                forced = css[forced_start:]
                self.assertRegex(
                    forced,
                    r"main:focus-visible\s*\{[^}]*outline-color:\s*Highlight;",
                )

    def test_compact_receipt_skip_link_forced_colors(self) -> None:
        surfaces = (
            "private-recruiter-conversion-outcome-v1.css",
            "private-recruiter-followthrough-checkpoint-v1.css",
        )
        for filename in surfaces:
            with self.subTest(filename=filename):
                css = (ASSETS / filename).read_text(encoding="utf-8")
                forced = css[css.index("@media (forced-colors: active)") :]
                self.assertRegex(
                    forced,
                    r"\.skip-link\s*\{[^}]*background:\s*Canvas;[^}]*border-color:\s*CanvasText;[^}]*color:\s*CanvasText;",
                )
                self.assertRegex(
                    forced,
                    r"\.skip-link:focus-visible\s*\{[^}]*outline:\s*2px solid Highlight;[^}]*outline-offset:\s*2px;",
                )

    def test_dossier_forced_colors_keeps_all_focusable_surfaces_visible(self) -> None:
        css = (ASSETS / "executive-career-dossier-v1.css").read_text(encoding="utf-8")
        forced = css[css.index("@media (forced-colors: active)"):]
        self.assertRegex(
            forced,
            r"a:focus-visible,\s*button:focus-visible,\s*summary:focus-visible,\s*main:focus-visible\s*\{[^}]*outline-color:\s*Highlight;",
        )

    def test_practice_confirm_feedback_has_dark_contrast(self) -> None:
        css = (ASSETS / "recruiter-practice-session-v1.css").read_text(encoding="utf-8")
        dark_start = css.index("@media screen and (prefers-color-scheme: dark)")
        print_start = css.index("@media print")
        dark_block = css[dark_start:print_start]
        self.assertIn(".feedback-item--confirm", dark_block)
        self.assertIn("background: var(--gold-soft)", dark_block)
        self.assertIn("border-left-color: var(--decision-term)", dark_block)
        self.assertIn(".feedback-label--confirm", dark_block)
        ink = re.search(r"--ink:\s*(#[0-9a-fA-F]{6});", dark_block)
        gold_soft = re.search(r"--gold-soft:\s*(#[0-9a-fA-F]{6});", dark_block)
        self.assertIsNotNone(ink)
        self.assertIsNotNone(gold_soft)
        self.assertGreaterEqual(_contrast(ink.group(1), gold_soft.group(1)), 4.5)

    def test_dossier_labels_have_dark_contrast(self) -> None:
        css = (ASSETS / "executive-career-dossier-v1.css").read_text(encoding="utf-8")
        dark_start = css.index("@media screen and (prefers-color-scheme: dark)")
        print_start = css.index("@media print")
        dark_block = css[dark_start:print_start]
        self.assertIn(".dossier-document .label", dark_block)
        self.assertIn("color: var(--muted)", dark_block)
        self.assertGreaterEqual(_contrast("#b8c4d8", "#182235"), 4.5)

    def test_dossier_progress_track_has_dark_non_text_contrast(self) -> None:
        css = (ASSETS / "executive-career-dossier-v1.css").read_text(encoding="utf-8")
        dark_start = css.index("@media screen and (prefers-color-scheme: dark)")
        print_start = css.index("@media print")
        dark_block = css[dark_start:print_start]
        self.assertIn(".dossier-document progress", dark_block)
        self.assertIn(
            ".dossier-document progress::-webkit-progress-bar", dark_block
        )
        self.assertIn(".dossier-document progress::-moz-progress-bar", dark_block)
        self.assertRegex(
            dark_block,
            r"\.dossier-document progress \{ background: var\(--forest-soft\); \}",
        )
        self.assertRegex(
            dark_block,
            r"\.dossier-document progress::-webkit-progress-bar \{ background: var\(--forest-soft\); \}",
        )
        self.assertRegex(
            dark_block,
            r"\.dossier-document progress::-moz-progress-bar \{ background: var\(--forest\); \}",
        )
        forest = re.search(r"--forest:\s*(#[0-9a-fA-F]{6});", dark_block)
        forest_soft = re.search(r"--forest-soft:\s*(#[0-9a-fA-F]{6});", dark_block)
        self.assertIsNotNone(forest)
        self.assertIsNotNone(forest_soft)
        self.assertGreaterEqual(_contrast(forest.group(1), forest_soft.group(1)), 3.0)

    def test_dossier_forced_colors_keep_progress_track_and_value_distinguishable(self) -> None:
        css = (ASSETS / "executive-career-dossier-v1.css").read_text(encoding="utf-8")
        forced = css[css.index("@media (forced-colors: active)"):]
        self.assertRegex(
            forced,
            r"\.dossier-document progress\s*\{[^}]*border:\s*1px solid CanvasText;[^}]*background:\s*Canvas;[^}]*color:\s*CanvasText;",
        )
        self.assertRegex(
            forced,
            r"\.dossier-document progress::-webkit-progress-bar\s*\{[^}]*background:\s*Canvas;",
        )
        self.assertRegex(
            forced,
            r"\.dossier-document progress::-webkit-progress-value\s*\{[^}]*background:\s*Highlight;",
        )
        self.assertRegex(
            forced,
            r"\.dossier-document progress::-moz-progress-bar\s*\{[^}]*background:\s*Highlight;",
        )
