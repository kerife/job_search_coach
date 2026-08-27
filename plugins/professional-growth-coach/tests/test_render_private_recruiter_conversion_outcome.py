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
    def test_interview_requested_uses_neutral_observed_request_label_in_both_locales(self):
        expected = {
            "en": "Interview request observed",
            "es": "Solicitud de entrevista observada",
        }
        source = load_outcome(FIXTURES / "interview-requested-es.json")
        for locale, label in expected.items():
            with self.subTest(locale=locale):
                item = copy.deepcopy(source)
                item["locale"] = locale
                rendered = render_outcome_html(item, today=dt.date(2026, 8, 9))
                self.assertIn(label, rendered)
                self.assertNotIn("Solicitaron una entrevista", rendered)

    def test_action_rail_is_selected_by_closed_next_safe_action_copy(self):
        expected = {
            "clarify_context_before_reply": "Clarify only the missing context before replying.",
            "prepare_fact_checked_summary": "Prepara un resumen verificado solo con hechos reportados.",
            "route_to_prepare-role-interviews": "Re-enter private preparation manually to review the reported next step.",
        }
        fixtures = {
            "clarify_context_before_reply": "contact-received-en.json",
            "prepare_fact_checked_summary": "referral-received-es.json",
            "route_to_prepare-role-interviews": "screen-requested-en.json",
        }
        for action, fixture in fixtures.items():
            with self.subTest(action=action):
                rendered = render_outcome_html(
                    load_outcome(FIXTURES / fixture), today=dt.date(2026, 8, 9)
                )
                self.assertIn(expected[action], rendered)
                self.assertEqual(rendered.count('class="continuity-rail"'), 1)
                self.assertNotIn("continuation", rendered.lower())

    def test_action_rail_exposes_one_current_pending_step(self):
        rendered = render_outcome_html(
            load_outcome(FIXTURES / "screen-requested-en.json"), today=dt.date(2026, 8, 9)
        )
        self.assertIn('data-stage="observation" data-state="recorded"', rendered)
        self.assertIn('data-stage="safe-step" data-state="pending" aria-current="step"', rendered)
        self.assertIn('data-stage="review" data-state="blocked"', rendered)
        self.assertEqual(1, rendered.count('aria-current="step"'))

    def test_stop_action_uses_terminal_recorded_rail_without_continuation_copy(self):
        source = load_outcome(FIXTURES / "stop-decision-en.json")
        for locale in ("en", "es"):
            with self.subTest(locale=locale):
                item = copy.deepcopy(source)
                item["locale"] = locale
                rendered = render_outcome_html(item, today=dt.date(2026, 8, 9))
                body = rendered.split("</style>", 1)[1]
                self.assertEqual(body.count('class="continuity-rail"'), 1)
                self.assertEqual(body.count('data-terminal="true"'), 1)
                self.assertEqual(body.count("continuity-step--recorded"), 1)
                self.assertIn("Recorded" if locale == "en" else "Registrado", rendered)
                self.assertIn("recorded privately" if locale == "en" else "queda registrado en privado", rendered)
                self.assertNotRegex(rendered, r"(?i)continuation|continue|manual action|continúa|acción manual")
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

    def test_cli_normalizes_malformed_json_to_input_error(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "malformed.json"
            output = Path(directory) / "out.html"
            input_path.write_text("{", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts/render_private_recruiter_conversion_outcome.py"), str(input_path), "--output", str(output), "--as-of", "2026-08-09"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 3)
            self.assertIn("cannot render private recruiter outcome", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())
    def test_six_events_have_fixed_localized_labels_and_actions(self):
        actions = {
            "en": {
                "contact_received": "Clarify context before replying",
                "reply_received": "Clarify context before replying",
                "referral_received": "Prepare a fact-checked summary",
                "screen_requested": "Route to interview preparation",
                "interview_requested": "Route to interview preparation",
                "stop_decision": "Record this recruiter-process outcome privately.",
            },
            "es": {
                "contact_received": "Aclara el contexto antes de responder",
                "reply_received": "Aclara el contexto antes de responder",
                "referral_received": "Prepara un resumen verificado",
                "screen_requested": "Dirige a preparación de entrevista",
                "interview_requested": "Dirige a preparación de entrevista",
                "stop_decision": "Registra en privado el resultado de este proceso de reclutamiento.",
            },
        }
        seen = set()
        for path in FIXTURES.glob("*.json"):
            item = load_outcome(path)
            html = render_outcome_html(item, today=dt.date(2026, 8, 9))
            expected = actions[item["locale"]][item["event_type"]]
            self.assertIn(expected, html)
            self.assertIn(item["event_date"], html)
            self.assertIn("Evidence count" if item["locale"] == "en" else "Evidencia", html)
            seen.add(item["event_type"])
        self.assertEqual(set(actions["en"]), seen)

    def test_stop_decision_copy_preserves_employment_continuity_in_english_and_spanish(self):
        item = load_outcome(FIXTURES / "stop-decision-en.json")
        expected = {
            "en": {
                "action": "Record this recruiter-process outcome privately.",
                "boundary": "Scope: this records one recruiter-process outcome only. It is not advice to resign, leave a job, or stop your job search; you decide what comes next.",
            },
            "es": {
                "action": "Registra en privado el resultado de este proceso de reclutamiento.",
                "boundary": "Alcance: esto solo registra un resultado de este proceso de reclutamiento. No es una recomendación de renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
            },
        }
        for locale in ("en", "es"):
            with self.subTest(locale=locale):
                localized = copy.deepcopy(item)
                localized["locale"] = locale
                rendered = render_outcome_html(localized, today=dt.date(2026, 8, 9))
                self.assertIn(expected[locale]["action"], rendered)
                self.assertIn(expected[locale]["boundary"], rendered)
                self.assertNotIn('class="outcome-employment-boundary"', rendered)

    def test_normal_receipts_show_employment_continuity_once_in_english_and_spanish(self):
        employment_boundary = {
            "en": "This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.",
            "es": "Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
        }
        observation_boundary = {
            "en": "Candidate-supplied observation only. No external action was taken.",
            "es": "Solo observación reportada por la persona. No se realizó ninguna acción externa.",
        }
        normal_fixtures = sorted(
            path for path in FIXTURES.glob("*.json") if path.name != "stop-decision-en.json"
        )
        for path in normal_fixtures:
            item = load_outcome(path)
            for locale in ("en", "es"):
                with self.subTest(fixture=path.name, locale=locale):
                    localized = copy.deepcopy(item)
                    localized["locale"] = locale
                    rendered = render_outcome_html(localized, today=dt.date(2026, 8, 9))
                    self.assertEqual(rendered.count(employment_boundary[locale]), 1)
                    self.assertEqual(
                        rendered.count(observation_boundary[locale]),
                        1,
                    )
                    self.assertIn('class="outcome-employment-boundary"', rendered)
                    self.assertNotIn("no-print", rendered)

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

    def test_skip_target_has_visible_keyboard_focus_contract(self):
        rendered = render_outcome_html(
            load_outcome(FIXTURES / "contact-received-en.json"), today=dt.date(2026, 8, 9)
        )
        self.assertIn("main:focus-visible", rendered)

    def test_continuity_rail_makes_manual_route_explicit_without_private_values(self):
        rendered = render_outcome_html(
            load_outcome(FIXTURES / "contact-received-en.json"), today=dt.date(2026, 8, 9)
        )
        self.assertEqual(rendered.count('class="continuity-rail"'), 1)
        self.assertEqual(rendered.count('class="continuity-step continuity-step--'), 3)
        self.assertIn('data-stage="observation" data-state="recorded"', rendered)
        self.assertIn('data-stage="safe-step" data-state="pending"', rendered)
        self.assertIn('data-stage="review" data-state="blocked"', rendered)
        self.assertNotIn("D-104", rendered)
        self.assertNotIn("contact_received", rendered)

    def test_prefers_contrast_more_reinforces_card_facts_and_boundary(self):
        rendered = render_outcome_html(
            load_outcome(FIXTURES / "contact-received-en.json"), today=dt.date(2026, 8, 9)
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(prefers-contrast: more\).*?\.outcome-card\s*\{[^}]*border:\s*2px solid var\(--ink\);[^}]*box-shadow:\s*none;",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(prefers-contrast: more\).*?\.outcome-facts div\s*\{[^}]*border-top:\s*2px solid var\(--ink\);",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(prefers-contrast: more\).*?\.outcome-boundary\s*\{[^}]*border-left-width:\s*\.5rem;[^}]*color:\s*var\(--ink\);",
        )
        self.assertLess(
            rendered.index("@media (prefers-contrast: more)"),
            rendered.index("@media (forced-colors: active)"),
        )

    def test_dark_mode_is_explicit_and_screen_only(self):
        item = load_outcome(FIXTURES / "contact-received-en.json")
        for locale in ("en", "es"):
            with self.subTest(locale=locale):
                localized = copy.deepcopy(item)
                localized["locale"] = locale
                rendered = render_outcome_html(localized, today=dt.date(2026, 8, 9))
                self.assertRegex(
                    rendered,
                    r"(?s)@media screen and \(prefers-color-scheme: dark\).*?"
                    r":root\s*\{[^}]*color-scheme:\s*dark;[^}]*--ink:\s*#f3f6ff;[^}]*--muted:\s*#b8c4d8;"
                    r"[^}]*--surface:\s*#182235;[^}]*--accent:\s*#8eb2ff;"
                    r"[^}]*--line:\s*#5f718e;",
                )
                self.assertLess(
                    rendered.index("prefers-color-scheme: dark"),
                    rendered.index("@media print"),
                )

    def test_print_keeps_outcome_card_atomic(self):
        rendered = render_outcome_html(
            load_outcome(FIXTURES / "contact-received-en.json"), today=dt.date(2026, 8, 9)
        )
        self.assertRegex(
            rendered,
            r"(?s)@media print.*?\.outcome-card\s*\{[^}]*break-inside:\s*avoid;[^}]*page-break-inside:\s*avoid;",
        )

    def test_print_uses_deterministic_page_margins(self):
        rendered = render_outcome_html(
            load_outcome(FIXTURES / "contact-received-en.json"), today=dt.date(2026, 8, 9)
        )
        self.assertIn("@page { size: auto; margin: 14mm; }", rendered)

    def test_forced_colors_preserves_outcome_boundary_marker(self):
        rendered = render_outcome_html(
            load_outcome(FIXTURES / "contact-received-en.json"), today=dt.date(2026, 8, 9)
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(forced-colors: active\).*?\.outcome-boundary\s*\{[^}]*border:\s*1px solid CanvasText;[^}]*border-left-width:\s*\.25rem;",
        )

    def test_forced_colors_uses_explicit_system_color_surfaces(self):
        rendered = render_outcome_html(
            load_outcome(FIXTURES / "contact-received-en.json"), today=dt.date(2026, 8, 9)
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(forced-colors: active\).*?\.outcome-card\s*\{[^}]*background:\s*Canvas;[^}]*color:\s*CanvasText;",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(forced-colors: active\).*?\.outcome-boundary\s*\{[^}]*color:\s*CanvasText;",
        )

    def test_route_outcomes_render_one_localized_manual_next_step_without_private_or_interactive_data(self):
        expected = {
            "screen-requested-en.json": (
                "Manual next step",
                "Return to the private Codex conversation and re-enter preparation manually to review the reported request. This receipt does not contact, send, or schedule anything.",
            ),
            "interview-requested-es.json": (
                "Siguiente paso manual",
                "Regresa a la conversación privada de Codex y vuelve a entrar manualmente a la preparación para revisar la solicitud reportada. Este recibo no contacta, envía ni agenda nada.",
            ),
        }
        for fixture, (heading, body) in expected.items():
            with self.subTest(fixture=fixture):
                item = load_outcome(FIXTURES / fixture)
                rendered = render_outcome_html(item, today=dt.date(2026, 8, 9))
                self.assertEqual(rendered.count('class="outcome-manual-next-step"'), 1)
                self.assertIn(
                    '<section class="outcome-manual-next-step" aria-labelledby="outcome-manual-next-step-heading">',
                    rendered,
                )
                self.assertIn(
                    f'<h2 id="outcome-manual-next-step-heading">{heading}</h2>',
                    rendered,
                )
                self.assertEqual(rendered.count(body), 1)
                self.assertNotIn("route_to_prepare-role-interviews", rendered)
                for identifier in (item["source_artifact_id"], *item["fact_ids"]):
                    self.assertNotIn(identifier, rendered)
                self.assertNotRegex(rendered, r"<(?:button|form)\b|\bonclick\s*=")
                self.assertNotRegex(rendered, r'href="(?!#main-content)')
                self.assertNotRegex(
                    rendered,
                    r"(?:file:|/tmp/|/Users/|[A-Za-z]:\\|\\\\[^\\\s]+\\[^\\\s]+)",
                )

    def test_manual_next_step_is_omitted_for_clarify_stop_and_manual_outcomes_in_both_locales(self):
        fixtures = (
            "contact-received-en.json",
            "stop-decision-en.json",
            "referral-received-es.json",
        )
        for fixture in fixtures:
            source = load_outcome(FIXTURES / fixture)
            for locale in ("en", "es"):
                with self.subTest(fixture=fixture, locale=locale):
                    item = copy.deepcopy(source)
                    item["locale"] = locale
                    rendered = render_outcome_html(item, today=dt.date(2026, 8, 9))
                    self.assertNotIn('class="outcome-manual-next-step"', rendered)

    def test_manual_next_step_preserves_320px_print_contrast_and_forced_color_contracts(self):
        rendered = render_outcome_html(
            load_outcome(FIXTURES / "screen-requested-en.json"), today=dt.date(2026, 8, 9)
        )
        self.assertEqual(
            rendered,
            render_outcome_html(
                load_outcome(FIXTURES / "screen-requested-en.json"), today=dt.date(2026, 8, 9)
            ),
        )
        self.assertRegex(
            rendered,
            r"\.outcome-manual-next-step\s*\{[^}]*min-width:\s*0;[^}]*overflow-wrap:\s*anywhere;",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media print.*?\.outcome-manual-next-step\s*\{[^}]*break-inside:\s*avoid;[^}]*page-break-inside:\s*avoid;",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(prefers-contrast: more\).*?\.outcome-manual-next-step\s*\{[^}]*border-left-width:\s*\.5rem;[^}]*color:\s*var\(--ink\);",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(forced-colors: active\).*?\.outcome-manual-next-step\s*\{[^}]*border:\s*1px solid CanvasText;[^}]*border-left-width:\s*\.25rem;[^}]*color:\s*CanvasText;",
        )

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
