import copy, datetime as dt, os, stat, subprocess, sys, tempfile, unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_private_recruiter_conversion_outcome import load_outcome
from render_private_recruiter_conversion_outcome import (
    OutcomeRenderValidationError, render_outcome_html, write_outcome_html,
)

FIXTURES = ROOT / "tests/fixtures/private-recruiter-conversion-outcome"


class ConversionOutcomeRendererTests(unittest.TestCase):
    def test_cli_normalizes_invalid_as_of_to_input_error(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "out.html"
            result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/render_private_recruiter_conversion_outcome.py"), str(FIXTURES / "contact-received-en.json"), "--output", str(output), "--as-of", "bad"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 3)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())

    def test_cli_normalizes_missing_required_output_to_input_error(self):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/render_private_recruiter_conversion_outcome.py"), str(FIXTURES / "contact-received-en.json"), "--as-of", "2026-08-09"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 3)
        self.assertNotIn("Traceback", result.stderr)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "out.html"
            missing_as_of = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/render_private_recruiter_conversion_outcome.py"), str(FIXTURES / "contact-received-en.json"), "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(missing_as_of.returncode, 3)
            self.assertFalse(output.exists())
    def test_six_events_have_fixed_localized_labels_and_actions(self):
        actions = {
            "contact_received": "Clarify context before replying",
            "reply_received": "Clarify context before replying",
            "referral_received": "Prepare a fact-checked summary",
            "screen_requested": "Route to interview preparation",
            "interview_requested": "Route to interview preparation",
            "stop_decision": "Record the stop decision",
        }
        seen = set()
        for path in FIXTURES.glob("*.json"):
            item = load_outcome(path)
            html = render_outcome_html(item, today=dt.date(2026, 8, 9))
            expected = actions[item["event_type"]] if item["locale"] == "en" else {"referral_received": "Prepara un resumen verificado", "interview_requested": "Dirige a preparación de entrevista"}[item["event_type"]]
            self.assertIn(expected, html)
            self.assertIn(item["event_date"], html)
            self.assertIn("Evidence count" if item["locale"] == "en" else "Evidencia", html)
            seen.add(item["event_type"])
        self.assertEqual(set(actions), seen)

    def test_localized_skip_link_targets_main_content(self):
        expected = {
            "en": ("Skip to main content", "Private observation receipt"),
            "es": ("Saltar al contenido principal", "Recibo privado de observación"),
        }
        for path in FIXTURES.glob("*.json"):
            item = load_outcome(path)
            rendered = render_outcome_html(item, today=dt.date(2026, 8, 9))
            skip, kicker = expected[item["locale"]]
            self.assertIn(
                f'<a class="skip-link" href="#main-content">{skip}</a>',
                rendered,
            )
            self.assertIn('<main id="main-content" class="outcome-shell" tabindex="-1">', rendered)
            self.assertIn(f'<p class="outcome-kicker">{kicker}</p>', rendered)
            anchor = rendered.split('<a class="skip-link"', 1)[1].split("</a>", 1)[0]
            self.assertNotIn(kicker, anchor)

    def test_evidence_count_uses_natural_localized_singular_and_plural_copy(self):
        cases = (
            ("contact-received-en.json", "en", "1 candidate-supplied fact"),
            ("contact-received-en.json", "es", "1 hecho reportado por la persona"),
            ("referral-received-es.json", "en", "2 candidate-supplied facts"),
            ("referral-received-es.json", "es", "2 hechos reportados por la persona"),
        )
        for fixture, locale, expected in cases:
            with self.subTest(fixture=fixture, locale=locale):
                item = load_outcome(FIXTURES / fixture)
                item["locale"] = locale
                rendered = render_outcome_html(item, today=dt.date(2026, 8, 9))
                self.assertIn(expected, rendered)
                self.assertNotIn("fact(s)", rendered)
                self.assertNotIn("hecho(s)", rendered)

    def test_spanish_copy_and_ids_raw_fields_and_interactivity_are_omitted(self):
        item = load_outcome(FIXTURES / "referral-received-es.json")
        item["raw_event"] = "ignored if not validated"
        with self.assertRaises(OutcomeRenderValidationError):
            render_outcome_html(item, today=dt.date(2026, 8, 9))
        item = load_outcome(FIXTURES / "referral-received-es.json")
        rendered = render_outcome_html(item, today=dt.date(2026, 8, 9))
        self.assertIn("Recibimos una referencia", rendered)
        self.assertIn("Evidencia", rendered)
        for identifier in (item["source_artifact_id"], *item["fact_ids"]):
            self.assertNotIn(identifier, rendered)
        self.assertNotRegex(rendered, r"<(?:(?:button|form))\\b|\\bonclick=")
        self.assertNotRegex(rendered, r'href="(?!#main-content)')
        self.assertNotIn("reply_received", rendered)

    def test_invalid_data_is_fail_closed(self):
        item = load_outcome(FIXTURES / "contact-received-en.json")
        item["next_safe_action"] = "send_message"
        with self.assertRaises(OutcomeRenderValidationError):
            render_outcome_html(item, today=dt.date(2026, 8, 9))

    def test_malformed_fact_ids_fail_closed_without_renderer_crash(self):
        item = load_outcome(FIXTURES / "contact-received-en.json")
        for value in ([{}], ["F-101", {}]):
            bad = copy.deepcopy(item)
            bad["fact_ids"] = value
            with self.assertRaises(OutcomeRenderValidationError):
                render_outcome_html(bad, today=dt.date(2026, 8, 9))

    def test_private_atomic_non_overwrite_and_symlink_safe_write(self):
        item = load_outcome(FIXTURES / "stop-decision-en.json")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "receipt.html"
            receipt = write_outcome_html(item, output, today=dt.date(2026, 8, 9))
            self.assertEqual(output, receipt.artifact_path)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                write_outcome_html(item, output, today=dt.date(2026, 8, 9))
            target = Path(directory) / "target.html"
            target.write_text("safe", encoding="utf-8")
            link = Path(directory) / "link.html"
            link.symlink_to(target)
            with self.assertRaises(OSError):
                write_outcome_html(item, link, today=dt.date(2026, 8, 9))


if __name__ == "__main__":
    unittest.main()
