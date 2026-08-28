"""Contracts for the shared recruiter-flow orientation rail."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from recruiter_continuity_rail import render_continuity_rail  # noqa: E402


class RecruiterContinuityRailTests(unittest.TestCase):
    def test_current_marker_is_named_as_review_surface_not_completed_progress(self) -> None:
        expected = {
            "es": "Superficie actual de revisión",
            "en": "Current review surface",
        }
        for locale, marker in expected.items():
            with self.subTest(locale=locale):
                _label, rail = render_continuity_rail(locale, "decision_gate")
                self.assertIn(marker, rail)

    def test_rail_labels_orientation_boundary_without_claiming_progress(self) -> None:
        for locale, marker in (("es", "no indica avance ni contacto realizado"), ("en", "does not track progress or contact")):
            with self.subTest(locale=locale):
                label, rail = render_continuity_rail(locale, "decision_gate")
                self.assertIn(marker, label)
                self.assertEqual(1, rail.count('aria-current="location"'))
                self.assertNotIn('aria-current="step"', rail)
                self.assertEqual(5, rail.count('class="continuity-rail__marker"'))

    def test_labels_are_candidate_facing_and_not_internal_jargon(self) -> None:
        expected = {
            "es": ("Elegir objetivos", "Revisar la decisión", "Preparar la pantalla", "Revisar la pantalla", "Preparar la siguiente etapa"),
            "en": ("Choose targets", "Review decision", "Prepare the screen", "Review the screen", "Prepare the next stage"),
        }
        for locale, labels in expected.items():
            with self.subTest(locale=locale):
                _label, rail = render_continuity_rail(locale, "decision_gate")
                for label in labels:
                    self.assertIn(f"<strong>{label}</strong>", rail)
                for jargon in ("Shortlist", "Intake", "Debrief", "Gate"):
                    self.assertNotIn(jargon, rail)

    def test_all_recruiter_surfaces_keep_orientation_note_accessibility_css(self) -> None:
        for filename in (
            "recruiter-target-shortlist-v1.css",
            "recruiter-target-decision-gate-v1.css",
            "recruiter-target-screen-intake-v1.css",
            "private-recruiter-screen-debrief-v1.css",
            "private-recruiter-next-stage-review-v1.css",
        ):
            with self.subTest(filename=filename):
                css = (ROOT / "plugins/professional-growth-coach/assets" / filename).read_text(encoding="utf-8")
                self.assertIn(".continuity-rail__label", css)
                self.assertIn("@media print", css)
                self.assertIn("@media (forced-colors: active)", css)
