"""Accessibility contracts for terminal compact receipt rails."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CompactReceiptAccessibilityTests(unittest.TestCase):
    def test_terminal_outcome_rails_mark_recorded_step_current_in_both_locales(self) -> None:
        for module_name in (
            "render_private_recruiter_conversion_outcome",
            "render_private_recruiter_followthrough_checkpoint",
        ):
            module = _load(module_name)
            for locale in ("es", "en"):
                with self.subTest(module=module_name, locale=locale):
                    rail = module._terminal_rail(locale)
                    self.assertIn('data-terminal="true"', rail)
                    self.assertEqual(1, rail.count('aria-current="step"'))
                    self.assertIn('data-state="recorded" aria-current="step"', rail)

    def test_pending_marker_is_visibly_distinct_in_normal_and_forced_colors(self) -> None:
        for filename in (
            "private-recruiter-conversion-outcome-v1.css",
            "private-recruiter-followthrough-checkpoint-v1.css",
        ):
            with self.subTest(filename=filename):
                css = (ROOT / "assets" / filename).read_text(encoding="utf-8")
                self.assertRegex(
                    css,
                    r"\.continuity-step--pending::before\s*\{[^}]*background:\s*var\(--accent\);[^}]*border-color:\s*var\(--accent\);[^}]*color:\s*var\(--surface\);",
                )
                self.assertRegex(
                    css,
                    r"@media \(forced-colors: active\).*?\.continuity-step--pending::before\s*\{[^}]*background:\s*Highlight;[^}]*border-color:\s*CanvasText;[^}]*color:\s*HighlightText;",
                )


if __name__ == "__main__":
    unittest.main()
