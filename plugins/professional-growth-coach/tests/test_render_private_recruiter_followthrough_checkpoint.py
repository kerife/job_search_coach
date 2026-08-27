import copy
import datetime as dt
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_private_recruiter_followthrough_checkpoint.py"
FIXTURE = ROOT / "tests/fixtures/private-recruiter-conversion-outcome/screen-requested-en.json"

spec = importlib.util.spec_from_file_location("checkpoint_renderer", SCRIPT)
renderer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(renderer)


class FollowthroughCheckpointRendererTests(unittest.TestCase):
    def test_interview_requested_uses_neutral_observed_request_label_in_both_locales(self):
        expected = {
            "en": "Interview request observed",
            "es": "Solicitud de entrevista observada",
        }
        for locale, label in expected.items():
            with self.subTest(locale=locale):
                item = copy.deepcopy(self.item)
                item.update(
                    locale=locale,
                    action_state="completed",
                    next_measurement_event="interview_requested",
                    next_safe_action="route_to_prepare-role-interviews",
                )
                rendered = renderer.render_checkpoint_html(item, self.receipt, as_of=dt.date(2026, 8, 8))
                self.assertIn(label, rendered)
                self.assertNotIn("Solicitaron entrevista", rendered)

    def test_action_rail_is_selected_by_closed_next_safe_action_copy(self):
        expected = {
            "manual_reenter_private_prep": "Re-enter private preparation manually.",
            "clarify_context_before_reply": "Clarify only the missing context before replying.",
            "route_to_prepare-role-interviews": "Re-enter private preparation manually to review the reported next step.",
            "debrief_after_screen": "Record what was discussed and what remains unknown, privately.",
        }
        for action, expected_copy in expected.items():
            with self.subTest(action=action):
                item = copy.deepcopy(self.item)
                item.update(
                    action_state="accepted" if action == "manual_reenter_private_prep" else "deferred" if action == "clarify_context_before_reply" else "completed",
                    next_measurement_event="unknown" if action in {"manual_reenter_private_prep", "clarify_context_before_reply"} else "screen_attended" if action == "debrief_after_screen" else "screen_prepared",
                    next_safe_action=action,
                )
                rendered = renderer.render_checkpoint_html(item, self.receipt, as_of=dt.date(2026, 8, 8))
                self.assertIn(expected_copy, rendered)
                self.assertEqual(rendered.count('class="continuity-rail"'), 1)

    def test_screen_attended_uses_private_debrief_action_and_never_promises_follow_up(self):
        expected = {
            "en": (
                "Debrief the screen privately",
                "Record what was discussed and what remains unknown, privately.",
                "Review the debrief before any follow-up.",
            ),
            "es": (
                "Haz un debrief privado del filtro",
                "Registra en privado lo que se habló y lo que sigue desconocido.",
                "Revisa el debrief antes de cualquier seguimiento.",
            ),
        }
        for locale, copy_set in expected.items():
            with self.subTest(locale=locale):
                item = copy.deepcopy(self.item)
                item.update(
                    locale=locale,
                    action_state="completed",
                    next_measurement_event="screen_attended",
                    next_safe_action="debrief_after_screen",
                )
                rendered = renderer.render_checkpoint_html(item, self.receipt, as_of=dt.date(2026, 8, 8))
                for text in copy_set:
                    self.assertIn(text, rendered)
                self.assertNotIn("Clarify context before replying", rendered)
                self.assertNotRegex(rendered, r"(?i)send|schedule|calendar|auto-start|contact")

    def test_stop_action_uses_terminal_recorded_rail_without_continuation_copy(self):
        stop_receipt = json.loads(
            (ROOT / "tests/fixtures/private-recruiter-conversion-outcome/stop-decision-en.json").read_text(
                encoding="utf-8"
            )
        )
        item = copy.deepcopy(self.item)
        item.update(
            action_state="completed",
            next_measurement_event="stop_decision",
            next_safe_action="record_stop_decision",
            source_receipt={
                "id": stop_receipt["source_artifact_id"],
                "source_version": stop_receipt["source_version"],
                "event_type": stop_receipt["event_type"],
            },
        )
        for locale in ("en", "es"):
            with self.subTest(locale=locale):
                localized = copy.deepcopy(item)
                localized["locale"] = locale
                rendered = renderer.render_checkpoint_html(localized, stop_receipt, as_of=dt.date(2026, 8, 8))
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
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(ROOT / "tests/fixtures/private-recruiter-followthrough-checkpoint/accepted-en.json"), "--receipt", str(FIXTURE), "--output", str(output), "--as-of", "bad"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 3)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())

    def test_cli_normalizes_missing_required_receipt_to_input_error(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(ROOT / "tests/fixtures/private-recruiter-followthrough-checkpoint/accepted-en.json"), "--output", "/tmp/unwritten-checkpoint.html", "--as-of", "2026-08-08"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 3)
        self.assertNotIn("Traceback", result.stderr)
    def setUp(self):
        self.receipt = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.item = {
            "schema_version": "private-recruiter-followthrough-checkpoint-v1",
            "artifact_kind": "private_recruiter_followthrough_checkpoint",
            "locale": "en",
            "source_receipt": {"id": "D-104", "source_version": "draft-v1", "event_type": "screen_requested"},
            "target_binding": {"target_id": "T-001", "source_gate_snapshot": "snap-shortlist-sha256-17d0733532d3e2a724bf38ba60a6cf9dbade133d71e8923e7dffce1e24a734f7"},
            "action_state": "completed", "observed_date": "2026-08-08",
            "next_measurement_event": "screen_prepared",
            "next_safe_action": "route_to_prepare-role-interviews",
            "delivery": {"draft_only": True, "external_actions_authorized": False, "no_message_action": True, "no_calendar_action": True, "raw_event_retained": False, "local_save_mode": "disabled"},
        }

    def test_all_states_and_locales_use_fixed_labels_and_omit_private_values(self):
        mapping = [("accepted", "unknown", "manual_reenter_private_prep"), ("deferred", "unknown", "clarify_context_before_reply"), ("declined", "unknown", "record_stop_decision"), ("completed", "screen_prepared", "route_to_prepare-role-interviews"), ("completed", "screen_attended", "debrief_after_screen")]
        for locale in ("en", "es"):
            for state, event, action in mapping:
                item = copy.deepcopy(self.item); item.update(locale=locale, action_state=state, next_measurement_event=event, next_safe_action=action)
                html = renderer.render_checkpoint_html(item, self.receipt, as_of=dt.date(2026, 8, 8))
                self.assertIn(f'<html lang="{locale}">', html)
                self.assertNotIn("D-104", html); self.assertNotIn("F-105", html); self.assertNotIn("screen_requested", html)
                self.assertNotIn("<form", html.lower()); self.assertNotIn("<button", html.lower()); self.assertNotIn("javascript:", html.lower())

    def test_stop_decision_copy_preserves_employment_continuity_in_english_and_spanish(self):
        stop_receipt = json.loads(
            (ROOT / "tests/fixtures/private-recruiter-conversion-outcome/stop-decision-en.json").read_text(
                encoding="utf-8"
            )
        )
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
        item = copy.deepcopy(self.item)
        item.update(
            action_state="completed",
            next_measurement_event="stop_decision",
            next_safe_action="record_stop_decision",
            source_receipt={
                "id": stop_receipt["source_artifact_id"],
                "source_version": stop_receipt["source_version"],
                "event_type": stop_receipt["event_type"],
            },
        )
        for locale in ("en", "es"):
            with self.subTest(locale=locale):
                localized = copy.deepcopy(item)
                localized["locale"] = locale
                rendered = renderer.render_checkpoint_html(
                    localized, stop_receipt, as_of=dt.date(2026, 8, 8)
                )
                self.assertIn(expected[locale]["action"], rendered)
                self.assertIn(expected[locale]["boundary"], rendered)
                self.assertNotIn('class="checkpoint-employment-boundary"', rendered)

        declined = copy.deepcopy(self.item)
        declined.update(
            action_state="declined",
            next_measurement_event="unknown",
            next_safe_action="record_stop_decision",
            source_receipt={
                "id": stop_receipt["source_artifact_id"],
                "source_version": stop_receipt["source_version"],
                "event_type": stop_receipt["event_type"],
            },
        )
        for locale in ("en", "es"):
            with self.subTest(locale=f"declined-{locale}"):
                declined["locale"] = locale
                rendered = renderer.render_checkpoint_html(
                    declined, stop_receipt, as_of=dt.date(2026, 8, 8)
                )
                self.assertIn(expected[locale]["action"], rendered)
                self.assertIn(expected[locale]["boundary"], rendered)

    def test_normal_checkpoints_show_employment_continuity_once_in_english_and_spanish(self):
        employment_boundary = {
            "en": "This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.",
            "es": "Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
        }
        checkpoint_boundary = {
            "en": "Candidate-supplied checkpoint only. No external action was taken.",
            "es": "Solo punto de control reportado por la persona. No se realizó ninguna acción externa.",
        }
        normal_states = (
            ("accepted", "unknown", "manual_reenter_private_prep"),
            ("deferred", "unknown", "clarify_context_before_reply"),
            ("completed", "screen_prepared", "route_to_prepare-role-interviews"),
        )
        for state, event, action in normal_states:
            for locale in ("en", "es"):
                with self.subTest(state=state, locale=locale):
                    item = copy.deepcopy(self.item)
                    item.update(
                        locale=locale,
                        action_state=state,
                        next_measurement_event=event,
                        next_safe_action=action,
                    )
                    rendered = renderer.render_checkpoint_html(
                        item, self.receipt, as_of=dt.date(2026, 8, 8)
                    )
                    self.assertEqual(rendered.count(employment_boundary[locale]), 1)
                    self.assertEqual(
                        rendered.count(checkpoint_boundary[locale]),
                        1,
                    )
                    self.assertIn('class="checkpoint-employment-boundary"', rendered)
                    self.assertNotIn("no-print", rendered)

    def test_css_accessibility_hooks_and_deterministic_render(self):
        first = renderer.render_checkpoint_html(self.item, self.receipt, as_of=dt.date(2026, 8, 8))
        second = renderer.render_checkpoint_html(self.item, self.receipt, as_of=dt.date(2026, 8, 8))
        self.assertEqual(first, second)
        self.assertIn('<main id="main-content" class="checkpoint-shell" tabindex="-1">', first)
        self.assertIn("main:focus-visible", first)
        for hook in ("@media print", "prefers-reduced-motion", "forced-colors", "@media (min-width"):
            self.assertIn(hook, first)

    def test_continuity_rail_connects_receipt_checkpoint_and_manual_route(self):
        rendered = renderer.render_checkpoint_html(self.item, self.receipt, as_of=dt.date(2026, 8, 8))
        self.assertEqual(rendered.count('class="continuity-rail"'), 1)
        self.assertEqual(rendered.count('class="continuity-step continuity-step--'), 3)
        self.assertIn('data-stage="receipt" data-state="recorded"', rendered)
        self.assertIn('data-stage="safe-step" data-state="pending"', rendered)
        self.assertIn('data-stage="review" data-state="blocked"', rendered)
        self.assertEqual(1, rendered.count('aria-current="step"'))
        self.assertNotIn("D-104", rendered)
        self.assertNotIn("screen_requested", rendered)

    def test_prefers_contrast_more_reinforces_card_facts_and_boundary(self):
        rendered = renderer.render_checkpoint_html(self.item, self.receipt, as_of=dt.date(2026, 8, 8))
        self.assertRegex(
            rendered,
            r"(?s)@media \(prefers-contrast: more\).*?\.checkpoint-card\s*\{[^}]*border:\s*2px solid var\(--ink\);[^}]*box-shadow:\s*none;",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(prefers-contrast: more\).*?\.checkpoint-facts div\s*\{[^}]*border-top:\s*2px solid var\(--ink\);",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(prefers-contrast: more\).*?\.checkpoint-boundary\s*\{[^}]*border-left-width:\s*\.5rem;[^}]*color:\s*var\(--ink\);",
        )
        self.assertLess(
            rendered.index("@media (prefers-contrast: more)"),
            rendered.index("@media (forced-colors: active)"),
        )

    def test_dark_mode_is_explicit_and_screen_only(self):
        for locale in ("en", "es"):
            with self.subTest(locale=locale):
                item = copy.deepcopy(self.item)
                item["locale"] = locale
                rendered = renderer.render_checkpoint_html(
                    item, self.receipt, as_of=dt.date(2026, 8, 8)
                )
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

    def test_print_keeps_checkpoint_card_atomic(self):
        rendered = renderer.render_checkpoint_html(self.item, self.receipt, as_of=dt.date(2026, 8, 8))
        self.assertRegex(
            rendered,
            r"(?s)@media print.*?\.checkpoint-card\s*\{[^}]*break-inside:\s*avoid;[^}]*page-break-inside:\s*avoid;",
        )

    def test_print_uses_deterministic_page_margins(self):
        rendered = renderer.render_checkpoint_html(self.item, self.receipt, as_of=dt.date(2026, 8, 8))
        self.assertIn("@page { size: auto; margin: 14mm; }", rendered)

    def test_forced_colors_preserves_checkpoint_boundary_marker(self):
        rendered = renderer.render_checkpoint_html(self.item, self.receipt, as_of=dt.date(2026, 8, 8))
        self.assertRegex(
            rendered,
            r"(?s)@media \(forced-colors: active\).*?\.checkpoint-boundary\s*\{[^}]*border:\s*1px solid CanvasText;[^}]*border-left-width:\s*\.25rem;",
        )

    def test_forced_colors_uses_explicit_system_color_surfaces(self):
        rendered = renderer.render_checkpoint_html(self.item, self.receipt, as_of=dt.date(2026, 8, 8))
        self.assertRegex(
            rendered,
            r"(?s)@media \(forced-colors: active\).*?\.checkpoint-card\s*\{[^}]*background:\s*Canvas;[^}]*color:\s*CanvasText;",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(forced-colors: active\).*?\.checkpoint-boundary\s*\{[^}]*color:\s*CanvasText;",
        )

    def test_route_checkpoints_render_one_localized_manual_next_step_without_private_or_interactive_data(self):
        expected = {
            "en": (
                "Manual next step",
                "Return to the private Codex conversation and re-enter preparation manually to review the reported request. This receipt does not contact, send, or schedule anything.",
            ),
            "es": (
                "Siguiente paso manual",
                "Regresa a la conversación privada de Codex y vuelve a entrar manualmente a la preparación para revisar la solicitud reportada. Este recibo no contacta, envía ni agenda nada.",
            ),
        }
        for locale, (heading, body) in expected.items():
            with self.subTest(locale=locale):
                item = copy.deepcopy(self.item)
                item["locale"] = locale
                rendered = renderer.render_checkpoint_html(
                    item, self.receipt, as_of=dt.date(2026, 8, 8)
                )
                self.assertEqual(rendered.count('class="checkpoint-manual-next-step"'), 1)
                self.assertIn(
                    '<section class="checkpoint-manual-next-step" aria-labelledby="checkpoint-manual-next-step-heading">',
                    rendered,
                )
                self.assertIn(
                    f'<h2 id="checkpoint-manual-next-step-heading">{heading}</h2>',
                    rendered,
                )
                self.assertEqual(rendered.count(body), 1)
                self.assertNotIn("route_to_prepare-role-interviews", rendered)
                for identifier in (item["source_receipt"]["id"], "F-105"):
                    self.assertNotIn(identifier, rendered)
                self.assertNotRegex(rendered, r"<(?:button|form)\b|\bonclick\s*=")
                self.assertNotRegex(rendered, r'href="(?!#main-content)')
                self.assertNotRegex(
                    rendered,
                    r"(?:file:|/tmp/|/Users/|[A-Za-z]:\\|\\\\[^\\\s]+\\[^\\\s]+)",
                )

    def test_manual_next_step_is_omitted_for_manual_clarify_and_stop_checkpoints_in_both_locales(self):
        states = (
            ("accepted", "unknown", "manual_reenter_private_prep"),
            ("deferred", "unknown", "clarify_context_before_reply"),
        )
        for locale in ("en", "es"):
            for state, event, action in states:
                with self.subTest(locale=locale, state=state):
                    item = copy.deepcopy(self.item)
                    item.update(
                        locale=locale,
                        action_state=state,
                        next_measurement_event=event,
                        next_safe_action=action,
                    )
                    rendered = renderer.render_checkpoint_html(
                        item, self.receipt, as_of=dt.date(2026, 8, 8)
                    )
                    self.assertNotIn('class="checkpoint-manual-next-step"', rendered)

    def test_manual_next_step_preserves_320px_print_contrast_and_forced_color_contracts(self):
        first = renderer.render_checkpoint_html(self.item, self.receipt, as_of=dt.date(2026, 8, 8))
        second = renderer.render_checkpoint_html(self.item, self.receipt, as_of=dt.date(2026, 8, 8))
        self.assertEqual(first, second)
        self.assertRegex(
            first,
            r"\.checkpoint-manual-next-step\s*\{[^}]*min-width:\s*0;[^}]*overflow-wrap:\s*anywhere;",
        )
        self.assertRegex(
            first,
            r"(?s)@media print.*?\.checkpoint-manual-next-step\s*\{[^}]*break-inside:\s*avoid;[^}]*page-break-inside:\s*avoid;",
        )
        self.assertRegex(
            first,
            r"(?s)@media \(prefers-contrast: more\).*?\.checkpoint-manual-next-step\s*\{[^}]*border-left-width:\s*\.5rem;[^}]*color:\s*var\(--ink\);",
        )
        self.assertRegex(
            first,
            r"(?s)@media \(forced-colors: active\).*?\.checkpoint-manual-next-step\s*\{[^}]*border:\s*1px solid CanvasText;[^}]*border-left-width:\s*\.25rem;[^}]*color:\s*CanvasText;",
        )

    def test_atomic_private_write_mode_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "checkpoint.html"
            renderer.write_checkpoint_html(self.item, self.receipt, output, as_of=dt.date(2026, 8, 8))
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError): renderer.write_checkpoint_html(self.item, self.receipt, output, as_of=dt.date(2026, 8, 8))
            renderer.write_checkpoint_html(self.item, self.receipt, output, as_of=dt.date(2026, 8, 8), force=True)
            self.assertFalse(any(path.name.startswith(".checkpoint.html.tmp-") for path in Path(directory).iterdir()))

    def test_invalid_receipt_is_rejected_before_render(self):
        bad = copy.deepcopy(self.receipt); bad["source_artifact_id"] = "D-999"
        with self.assertRaises(renderer.CheckpointRenderValidationError): renderer.render_checkpoint_html(self.item, bad, as_of=dt.date(2026, 8, 8))


if __name__ == "__main__": unittest.main()
