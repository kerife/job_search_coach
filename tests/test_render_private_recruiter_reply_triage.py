"""Renderer tests for the private recruiter reply triage decision card."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RENDERER_PATH = (
    REPO_ROOT
    / "plugins"
    / "professional-growth-coach"
    / "scripts"
    / "render_private_recruiter_reply_triage.py"
)
FIXTURE_DIRECTORY = (
    REPO_ROOT
    / "tests"
    / "evals"
    / "with-skill"
    / "fixtures"
    / "private-recruiter-reply-triage"
)
V2_READY_EN_SNAPSHOT = (
    "snap-triage-sha256-"
    "85ad96e9cab8b222315a01a85d4a6f61f0d5a38650a1286773bc8e1664c15ebd"
)
V2_READY_ES_SNAPSHOT = (
    "snap-triage-sha256-"
    "74720a33a8bfc5e085767831e741b7cce97d45b1bb2d76b47d3ee203a2b5d6e8"
)


def load_fixture(name: str) -> dict[str, object]:
    value = json.loads((FIXTURE_DIRECTORY / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture must be a JSON object")
    return value


def load_renderer() -> object:
    specification = importlib.util.spec_from_file_location(
        "render_private_recruiter_reply_triage", RENDERER_PATH
    )
    assert specification is not None and specification.loader is not None
    renderer = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = renderer
    specification.loader.exec_module(renderer)
    return renderer


class PrivateRecruiterReplyTriageRendererTests(unittest.TestCase):
    def test_cli_normalizes_unknown_missing_and_help_args(self) -> None:
        fixture = FIXTURE_DIRECTORY / "ready-en.json"
        invalid = subprocess.run([sys.executable, "-B", str(RENDERER_PATH), str(fixture), "--output", "/tmp/triage.html", "--unknown"], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 3)
        missing = subprocess.run([sys.executable, "-B", str(RENDERER_PATH), str(fixture)], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 3)
        help_result = subprocess.run([sys.executable, "-B", str(RENDERER_PATH), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
    @classmethod
    def setUpClass(cls) -> None:
        cls.renderer = load_renderer()
        cls.fixtures = {
            name: load_fixture(name)
            for name in (
                "clarify-es.json",
                "clarify-en.json",
                "ready-es.json",
                "ready-en.json",
                "stop-es.json",
                "stop-en.json",
            )
        }

    def test_renders_each_locale_and_state_as_a_self_contained_decision_card(self) -> None:
        expected = {
            "clarify-es.json": ("Aclarar primero", "Qué sabemos", "Falta confirmar"),
            "clarify-en.json": ("Clarify first", "What we know", "Confirm next"),
            "ready-es.json": ("Lista para preparación privada", "Traspaso local", "Falta confirmar"),
            "ready-en.json": ("Ready for private preparation", "Local handoff", "Confirm next"),
            "stop-es.json": ("Detener este proceso de reclutamiento", "Qué sabemos", "No afirmar"),
            "stop-en.json": ("Stop this recruiter process", "What we know", "Do not assert"),
        }
        for name, triage in self.fixtures.items():
            with self.subTest(fixture=name):
                document = self.renderer.render_triage_html(triage)
                state_label, known_label, third_label = expected[name]
                self.assertIn(f'lang="{triage["locale"]}"', document)
                self.assertEqual(document.count('<main id="main-content" class="triage-shell" tabindex="-1">'), 1)
                self.assertIn(state_label, document)
                self.assertIn(known_label, document)
                self.assertIn(third_label, document)
                self.assertIn("No external action was taken." if triage["locale"] == "en" else "No se realizó ninguna acción externa.", document)
                self.assertIn(
                    "Nothing is saved on this device."
                    if triage["locale"] == "en"
                    else "No se guarda nada en este dispositivo.",
                    document,
                )
                self.assertIn("Content-Security-Policy", document)
                state_start = document.index('class="triage-state')
                state_end = document.index(">", state_start)
                self.assertNotIn("aria-live", document[state_start:state_end])
                self.assertNotIn("<link ", document)
                self.assertNotIn("<script", document)

    def test_save_boundary_is_plain_localized_copy_without_exposing_internal_enum(self) -> None:
        expected = {
            "en": "Nothing is saved on this device.",
            "es": "No se guarda nada en este dispositivo.",
        }
        old = {
            "en": "Local saving is disabled (local_save_mode=disabled).",
            "es": "El guardado local está deshabilitado (local_save_mode=disabled).",
        }
        for name, triage in self.fixtures.items():
            with self.subTest(fixture=name):
                self.assertEqual(triage["delivery"]["local_save_mode"], "disabled")
                document = self.renderer.render_triage_html(triage)
                self.assertEqual(document.count(expected[triage["locale"]]), 1)
                self.assertNotIn("local_save_mode=", document)
                self.assertNotIn(old[triage["locale"]], document)
                save_start = document.index(expected[triage["locale"]])
                self.assertNotIn("no-print", document[save_start - 300 : save_start + 300])

    def test_v2_uses_ui_locale_for_copy_and_content_locale_for_dynamic_prose(self) -> None:
        triage = copy.deepcopy(self.fixtures["ready-es.json"])
        triage["schema_version"] = "private-recruiter-reply-triage-v2"
        triage["ui_locale"] = "en"
        triage["content_locale"] = "es"
        del triage["locale"]
        triage["handoff"]["packet"]["source_snapshot"] = V2_READY_ES_SNAPSHOT
        triage["handoff"]["reentry_packet"]["source_snapshot"] = V2_READY_ES_SNAPSHOT
        document = self.renderer.render_triage_html(triage)
        self.assertIn('<html lang="en">', document)
        self.assertIn("Private triage", document)
        self.assertIn('<p lang="es">', document)
        self.assertIn('<dd lang="es">', document)
        self.assertEqual(document.count('lang="es"'), 7)
        self.assertEqual(document.count('<html lang="en">'), 1)
        self.assertNotIn('<p lang="en">', document)

    def test_v2_renderer_keeps_content_bound_snapshot_internal(self) -> None:
        triage = copy.deepcopy(self.fixtures["ready-en.json"])
        triage["schema_version"] = "private-recruiter-reply-triage-v2"
        triage["ui_locale"] = "en"
        triage["content_locale"] = "en"
        del triage["locale"]
        triage["handoff"]["packet"]["source_snapshot"] = V2_READY_EN_SNAPSHOT
        triage["handoff"]["reentry_packet"]["source_snapshot"] = V2_READY_EN_SNAPSHOT
        document = self.renderer.render_triage_html(triage)
        self.assertNotIn("source_snapshot", document)
        self.assertNotIn("snap-triage-sha256-", document)
        self.assertNotIn(V2_READY_EN_SNAPSHOT, document)

    def test_v1_does_not_gain_fragment_language_attributes(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-es.json"])
        self.assertEqual(document.count('lang="es"'), 1)

    def test_ready_is_the_only_state_that_renders_a_local_handoff_note(self) -> None:
        for name, triage in self.fixtures.items():
            with self.subTest(fixture=name):
                document = self.renderer.render_triage_html(triage)
                has_handoff = 'class="triage-section triage-handoff"' in document
                self.assertEqual(has_handoff, triage["state"] == "ready_for_private_prep")

    def test_next_safe_action_is_localized_for_every_state_and_stays_static(self) -> None:
        expected = {
            "clarify-en.json": "Clarify recruiter-screen context before private preparation.",
            "clarify-es.json": "Aclara el contexto del filtro inicial antes de la preparación privada.",
            "ready-en.json": "Re-enter private preparation manually.",
            "ready-es.json": "Vuelve a entrar manualmente a la preparación privada.",
            "stop-en.json": "Record this recruiter-process outcome privately; do not continue this preparation path.",
            "stop-es.json": "Registra en privado el resultado de este proceso; no continúes por esta vía de preparación.",
        }
        for name, phrase in expected.items():
            with self.subTest(fixture=name):
                document = self.renderer.render_triage_html(self.fixtures[name])
                action = document.split('triage-next-safe-action"', 1)[1].split("</section>", 1)[0]
                self.assertIn(phrase, action)
                self.assertIn('aria-labelledby="next-safe-action-title"', action)
                self.assertNotIn("<a ", action)
                self.assertNotIn("<button", action)
                self.assertNotIn("<form", action)

    def test_stop_copy_is_recruiter_scoped_and_preserves_candidate_agency_in_both_locales(self) -> None:
        expected = {
            "stop-en.json": {
                "action": "Record this recruiter-process outcome privately; do not continue this preparation path.",
                "scope": "Scope: this records one recruiter-process outcome only. It is not advice to resign, leave a job, or stop your job search; you decide what comes next.",
            },
            "stop-es.json": {
                "action": "Registra en privado el resultado de este proceso; no continúes por esta vía de preparación.",
                "scope": "Alcance: esto solo registra un resultado de este proceso de reclutamiento. No es una recomendación de renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
            },
        }
        for name, copy in expected.items():
            with self.subTest(fixture=name):
                document = self.renderer.render_triage_html(self.fixtures[name])
                action = document.split('triage-next-safe-action"', 1)[1].split("</section>", 1)[0]
                self.assertIn(copy["action"], action)
                self.assertIn(copy["scope"], document)
                self.assertNotIn(
                    "Record the stop decision privately; do not continue.", action
                )
                self.assertNotIn(
                    "Registra la decisión de detenerse en privado; no continúes.", action
                )

    def test_next_safe_action_precedes_state_specific_sections(self) -> None:
        for name, triage in self.fixtures.items():
            document = self.renderer.render_triage_html(triage)
            action_start = document.index('triage-next-safe-action"')
            known_start = document.index('id="known-title"')
            self.assertLess(action_start, known_start)
            if triage["state"] == "clarify_first":
                self.assertLess(action_start, document.index("triage-clarify-gate"))
            if triage["state"] == "ready_for_private_prep":
                self.assertLess(action_start, document.index('class="triage-section triage-handoff"'))

    def test_ready_surfaces_blocked_boundary_before_private_handoff(self) -> None:
        for name in ("ready-en.json", "ready-es.json"):
            with self.subTest(fixture=name):
                document = self.renderer.render_triage_html(self.fixtures[name])
                self.assertLess(
                    document.index('class="triage-section triage-next-safe-action"'),
                    document.index('class="triage-section triage-blocked"'),
                )
                self.assertLess(
                    document.index('class="triage-section triage-blocked"'),
                    document.index('class="triage-section triage-handoff"'),
                )
        for name in ("clarify-en.json", "clarify-es.json", "stop-en.json", "stop-es.json"):
            with self.subTest(fixture=name):
                document = self.renderer.render_triage_html(self.fixtures[name])
                self.assertEqual(document.count('class="triage-section triage-blocked"'), 1)
                self.assertNotIn('class="triage-section triage-handoff"', document)

    def test_next_safe_action_has_print_mobile_and_forced_colors_hooks(self) -> None:
        css = (REPO_ROOT / "plugins" / "professional-growth-coach" / "assets" / "private-recruiter-reply-triage-v1.css").read_text(encoding="utf-8")
        self.assertIn(".triage-next-safe-action", css)
        self.assertIn("@media print", css)
        self.assertIn("@media (max-width: 640px)", css)
        self.assertIn("@media (forced-colors: active)", css)

    def test_print_freezes_triage_entrance_motion(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        self.assertRegex(
            document,
            r"(?s)@media print.*?\.triage-card\s*\{[^}]*animation:\s*none !important;[^}]*transition:\s*none !important;[^}]*transform:\s*none !important;",
        )

    def test_triage_has_preferred_contrast_semantic_panel_hooks(self) -> None:
        css = (REPO_ROOT / "plugins" / "professional-growth-coach" / "assets" / "private-recruiter-reply-triage-v1.css").read_text(encoding="utf-8")
        self.assertIn("@media (prefers-contrast: more)", css)
        contrast = css.split("@media (prefers-contrast: more)", 1)[1]
        self.assertRegex(contrast, r"triage-state[^}]*border:\s*2px")
        self.assertRegex(contrast, r"triage-next-safe-action[^}]*border[^}]*2px")
        self.assertRegex(contrast, r"triage-blocked[^}]*border[^}]*2px")
        self.assertRegex(contrast, r"triage-state[^}]*text-decoration:\s*underline")
        self.assertRegex(contrast, r"triage-(?:next-safe-action|blocked) h2[^}]*text-decoration:\s*underline")

    def test_clarify_gate_maps_candidate_reported_fact_to_fixed_localized_reason(self) -> None:
        expected = {
            "clarify-en.json": "One verified fact is still needed before private preparation.",
            "clarify-es.json": "Falta un hecho confirmado antes de la preparación privada.",
        }
        for name, phrase in expected.items():
            triage = copy.deepcopy(self.fixtures[name])
            triage["facts"][0]["state"] = "candidate_reported"  # type: ignore[index]
            document = self.renderer.render_triage_html(triage)
            gate = document.split("triage-clarify-gate", 1)[1].split("</section>", 1)[0]
            self.assertIn(phrase, gate)

    def test_clarify_gate_maps_missing_context_and_generic_reason_without_blocker_prose(self) -> None:
        missing = copy.deepcopy(self.fixtures["clarify-en.json"])
        missing["facts"][0]["state"] = "verified"  # type: ignore[index]
        document = self.renderer.render_triage_html(missing)
        gate = document.split("triage-clarify-gate", 1)[1].split("</section>", 1)[0]
        self.assertIn("The minimum recruiter-screen context is still unconfirmed.", gate)

        generic = copy.deepcopy(missing)
        generic["safe_context"]["stage"] = "recruiter_screen"  # type: ignore[index]
        generic["safe_context"]["role_context"] = "confirmed"  # type: ignore[index]
        generic["safe_context"]["critical_constraints"] = "confirmed"  # type: ignore[index]
        document = self.renderer.render_triage_html(generic)
        gate = document.split("triage-clarify-gate", 1)[1].split("</section>", 1)[0]
        self.assertIn("One small clarification is still needed before private preparation.", gate)
        self.assertNotIn("candidate_reported", gate)
        self.assertNotIn("blocked_claims", gate)

    def test_clarify_gate_is_ordered_accessible_and_omitted_for_ready_or_stop(self) -> None:
        clarify = self.renderer.render_triage_html(self.fixtures["clarify-en.json"])
        self.assertIn('aria-labelledby="clarify-gate-title"', clarify)
        self.assertIn('id="clarify-gate-title"', clarify)
        self.assertLess(clarify.index("triage-clarify-gate"), clarify.index('id="known-title"'))
        self.assertEqual(clarify.count("?"), 1)
        for name in ("ready-en.json", "ready-es.json", "stop-en.json", "stop-es.json"):
            document = self.renderer.render_triage_html(self.fixtures[name])
            self.assertNotIn("triage-clarify-gate", document)

    def test_ready_handoff_cue_states_scope_and_manual_reentry(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        self.assertIn("One recruiter-screen question", document)
        self.assertIn("Re-enter preparation manually", document)
        self.assertNotIn("auto-start", document.casefold())
        self.assertIn("Calendar or contact details", document)
        self.assertNotIn("<button", document.casefold())
        for name in ("clarify-en.json", "stop-en.json"):
            document = self.renderer.render_triage_html(self.fixtures[name])
            self.assertNotIn("One recruiter-screen question", document)
            self.assertNotIn("Re-enter preparation manually", document)

    def test_ready_handoff_renders_one_identity_free_fact_and_question_preview(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        self.assertIn('class="triage-handoff-preview"', document)
        self.assertIn("Verified fact", document)
        self.assertIn("Safe question", document)
        self.assertIn("The candidate confirmed relevant experience for private preparation.", document)
        self.assertIn("Which supported example should be practiced first for this conversation?", document)
        self.assertEqual(document.count("The candidate confirmed relevant experience for private preparation."), 2)
        self.assertEqual(document.count("Which supported example should be practiced first for this conversation?"), 2)
        self.assertIn("<dl", document)
        self.assertIn("<dt>Verified fact</dt>", document)
        self.assertIn("<dt>Safe question</dt>", document)

    def test_ready_preview_explains_question_purpose_for_every_classification_and_locale(self) -> None:
        expected = {
            "screen_invite": ("Opens readiness", "Abre la preparación"),
            "request_for_proof": ("Selects one verified example", "Selecciona un ejemplo confirmado"),
            "eligibility_question": ("Clarifies the eligibility boundary", "Aclara el límite de elegibilidad"),
            "compensation_question": ("Clarifies the compensation boundary", "Aclara el límite de compensación"),
            "unknown": ("Finds the smallest missing detail", "Encuentra el detalle mínimo que falta"),
        }
        question_kinds = {
            "screen_invite": "screen_opening",
            "request_for_proof": "proof_example",
            "eligibility_question": "eligibility_boundary",
            "compensation_question": "compensation_boundary",
            "unknown": "missing_detail",
        }
        for classification, labels in expected.items():
            for locale, label in zip(("en", "es"), labels):
                with self.subTest(classification=classification, locale=locale):
                    triage = copy.deepcopy(self.fixtures[f"ready-{locale}.json"])
                    triage["classification"] = classification
                    triage["question"]["kind"] = question_kinds[classification]
                    triage["handoff"]["packet"]["prep_scope"] = {
                        "screen_opening": "screen_opening",
                        "proof_example": "proof_example",
                        "eligibility_boundary": "eligibility_boundary",
                        "compensation_boundary": "compensation_boundary",
                        "missing_detail": "missing_detail",
                    }[question_kinds[classification]]
                    triage["handoff"]["reentry_packet"]["prep_scope"] = triage["handoff"]["packet"]["prep_scope"]
                    document = self.renderer.render_triage_html(triage)
                    purpose = document.split('class="triage-handoff-preview"', 1)[1].split("</section>", 1)[0]
                    self.assertIn("Question purpose" if locale == "en" else "Propósito de la pregunta", purpose)
                    self.assertIn(label, purpose)

    def test_ready_preview_orders_purpose_between_fact_and_single_question(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        preview = document.split('class="triage-handoff-preview"', 1)[1].split("</section>", 1)[0]
        fact = preview.index("Verified fact")
        purpose = preview.index("Question purpose")
        question = preview.index("Safe question")
        self.assertLess(fact, purpose)
        self.assertLess(purpose, question)
        self.assertEqual(preview.count("?"), 1)

    def test_ready_preview_renders_localized_question_type_from_validated_kind(self) -> None:
        expected = {
            "screen_opening": ("Question type", "Screen opening", "Tipo de pregunta", "Apertura de filtro"),
            "proof_example": ("Question type", "Proof example", "Tipo de pregunta", "Ejemplo de evidencia"),
            "eligibility_boundary": ("Question type", "Eligibility boundary", "Tipo de pregunta", "Límite de elegibilidad"),
            "compensation_boundary": ("Question type", "Compensation boundary", "Tipo de pregunta", "Límite de compensación"),
            "missing_detail": ("Question type", "Missing detail", "Tipo de pregunta", "Detalle faltante"),
        }
        kind_classifications = {
            "screen_opening": "screen_invite",
            "proof_example": "request_for_proof",
            "eligibility_boundary": "eligibility_question",
            "compensation_boundary": "compensation_question",
            "missing_detail": "unknown",
        }
        for kind, labels in expected.items():
            for locale, fixture_name, label in (("en", "ready-en.json", labels[1]), ("es", "ready-es.json", labels[3])):
                with self.subTest(kind=kind, locale=locale):
                    triage = copy.deepcopy(self.fixtures[fixture_name])
                    triage["classification"] = kind_classifications[kind]
                    triage["question"]["kind"] = kind
                    triage["handoff"]["packet"]["prep_scope"] = {
                        "screen_opening": "screen_opening",
                        "proof_example": "proof_example",
                        "eligibility_boundary": "eligibility_boundary",
                        "compensation_boundary": "compensation_boundary",
                        "missing_detail": "missing_detail",
                    }[kind]
                    triage["handoff"]["reentry_packet"]["prep_scope"] = triage["handoff"]["packet"]["prep_scope"]
                    document = self.renderer.render_triage_html(triage)
                    preview = document.split('class="triage-handoff-preview"', 1)[1].split("</section>", 1)[0]
                    self.assertIn(labels[0] if locale == "en" else labels[2], preview)
                    self.assertIn(label, preview)
                    if kind == "screen_opening":
                        self.assertNotIn("screen_opening", document)
                        self.assertNotIn("recruiter_screen_opening", document)
                        self.assertIn('aria-labelledby="handoff-title"', document)
                        self.assertIn('aria-describedby="handoff-description"', document)

    def test_question_type_is_ready_only_and_precedes_purpose_without_unsafe_output(self) -> None:
        for name in ("clarify-en.json", "clarify-es.json", "stop-en.json", "stop-es.json"):
            document = self.renderer.render_triage_html(self.fixtures[name])
            self.assertNotIn("Question type", document)
            self.assertNotIn("Tipo de pregunta", document)
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        preview = document.split('class="triage-handoff-preview"', 1)[1].split("</section>", 1)[0]
        self.assertLess(preview.index("Question type"), preview.index("Question purpose"))
        self.assertEqual(preview.count("Question type"), 1)
        for forbidden in ("send", "contact", "calendar", "guarantee", "http", "score", "<script", "<button"):
            self.assertNotIn(forbidden, preview.casefold())

    def test_question_purpose_is_ready_only_and_has_no_question_mark_or_unsafe_prose(self) -> None:
        for name in ("clarify-en.json", "clarify-es.json", "stop-en.json", "stop-es.json"):
            with self.subTest(fixture=name):
                document = self.renderer.render_triage_html(self.fixtures[name])
                self.assertNotIn("Question purpose", document)
                self.assertNotIn("Propósito de la pregunta", document)
        ready = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        purpose = ready.split('class="triage-handoff-preview"', 1)[1].split("</section>", 1)[0]
        self.assertEqual(purpose.count("?"), 1)
        for forbidden in ("send", "contact", "calendar", "guarantee", "http", "score"):
            self.assertNotIn(forbidden, purpose.casefold())

    def test_handoff_preview_is_localized_and_ready_only(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-es.json"])
        self.assertIn("Hecho confirmado", document)
        self.assertIn("Pregunta segura", document)
        for name in ("clarify-en.json", "clarify-es.json", "stop-en.json", "stop-es.json"):
            with self.subTest(fixture=name):
                document = self.renderer.render_triage_html(self.fixtures[name])
                self.assertNotIn('<section class="triage-handoff-preview"', document)

    def test_ready_handoff_renders_fixed_classification_focus_in_both_locales(self) -> None:
        expected = {
            "screen_invite": ("Practice a concise opening", "Practica una apertura concisa"),
            "request_for_proof": ("Choose one verified example", "Elige un ejemplo confirmado"),
            "eligibility_question": ("Prepare the eligibility boundary question", "Prepara la pregunta límite de elegibilidad"),
            "compensation_question": ("Prepare the compensation boundary question", "Prepara la pregunta límite de compensación"),
            "decline": ("Stop: no private preparation handoff", "Detener: no hay traspaso a preparación privada"),
            "unknown": ("Clarify the smallest missing detail", "Aclara el detalle mínimo que falta"),
        }
        for classification, localized in expected.items():
            for fixture_name, expected_text in zip(("ready-en.json", "ready-es.json"), localized):
                triage = copy.deepcopy(self.fixtures[fixture_name])
                triage["classification"] = classification
                if classification != "decline":
                    triage["question"]["kind"] = {
                        "screen_invite": "screen_opening",
                        "request_for_proof": "proof_example",
                        "eligibility_question": "eligibility_boundary",
                        "compensation_question": "compensation_boundary",
                        "unknown": "missing_detail",
                    }[classification]
                    triage["handoff"]["packet"]["prep_scope"] = {
                        "screen_opening": "screen_opening",
                        "proof_example": "proof_example",
                        "eligibility_boundary": "eligibility_boundary",
                        "compensation_boundary": "compensation_boundary",
                        "missing_detail": "missing_detail",
                    }[triage["question"]["kind"]]
                    triage["handoff"]["reentry_packet"]["prep_scope"] = triage["handoff"]["packet"]["prep_scope"]
                with self.subTest(classification=classification, locale=fixture_name):
                    if classification == "decline":
                        with self.assertRaises(self.renderer.TriageValidationError):
                            self.renderer.render_triage_html(triage)
                        continue
                    document = self.renderer.render_triage_html(triage)
                    self.assertIn('class="triage-handoff-focus"', document)
                    self.assertIn(expected_text, document)

    def test_focus_and_split_readiness_are_ready_only_and_semantic(self) -> None:
        ready = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        self.assertIn('<dt>Stage</dt><dd>Recruiter screen</dd>', ready)
        self.assertIn('<dt>Role context</dt><dd>Confirmed</dd>', ready)
        self.assertIn('<dt>Critical constraints</dt><dd>Confirmed</dd>', ready)
        self.assertIn('<h3 id="handoff-focus-title">Preparation focus</h3>', ready)
        for name in ("clarify-en.json", "stop-en.json"):
            document = self.renderer.render_triage_html(self.fixtures[name])
            self.assertNotIn('class="triage-handoff-focus"', document)

    def test_renderer_rejects_contextual_identity_before_embedding_prose(self) -> None:
        triage = copy.deepcopy(self.fixtures["clarify-en.json"])
        triage["facts"][0]["summary"] = "Jordan Lee described incident response experience."
        with self.assertRaises(self.renderer.TriageValidationError) as captured:
            self.renderer.render_triage_html(triage)
        self.assertIn("unlabelled_identity", str(captured.exception.errors))
        self.assertNotIn("Jordan Lee", str(captured.exception.errors))

    def test_renderer_rejects_unsupported_script_before_embedding_prose(self) -> None:
        triage = copy.deepcopy(self.fixtures["clarify-en.json"])
        triage["facts"][0]["summary"] = "Алексей Иванов described incident response experience."
        with self.assertRaises(self.renderer.TriageValidationError) as captured:
            self.renderer.render_triage_html(triage)
        self.assertIn("unsupported_script", str(captured.exception.errors))
        self.assertNotIn("Алексей", str(captured.exception.errors))

    def test_ready_handoff_has_static_manual_next_step_after_focus_before_preview(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        focus_end = document.index("</section>", document.index('class="triage-handoff-focus"'))
        next_step_start = document.index('class="triage-handoff-next-step"')
        preview_start = document.index('class="triage-handoff-preview"')
        self.assertGreater(next_step_start, focus_end)
        self.assertLess(next_step_start, preview_start)
        self.assertIn("Manual next step", document)
        self.assertIn("Re-enter private preparation manually and answer the one safe question.", document)

    def test_ready_handoff_is_a_semantic_three_step_sequence_with_preview_nested_in_step_three(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        sequence = document.split('class="triage-handoff-sequence"', 1)[1].split("</ol>", 1)[0]
        self.assertIn("<ol", document)
        self.assertEqual(sequence.count('<li><span class="triage-handoff-step-label">'), 3)
        labels = ("01 Conditions", "02 Focus", "03 Manual re-entry")
        positions = [sequence.index(label) for label in labels]
        self.assertEqual(positions, sorted(positions))
        step_three = sequence.split("03 Manual re-entry", 1)[1]
        self.assertIn('class="triage-handoff-preview"', step_three)

    def test_handoff_sequence_is_ready_only_and_keeps_existing_accessibility_hooks(self) -> None:
        ready = self.renderer.render_triage_html(self.fixtures["ready-es.json"])
        self.assertIn('class="triage-handoff-sequence"', ready)
        for label in ("01 Condiciones", "02 Enfoque", "03 Reingreso manual"):
            self.assertIn(label, ready)
        for label in ("01 Conditions", "02 Focus", "03 Manual re-entry"):
            self.assertNotIn(label, ready)
        self.assertIn('aria-labelledby="handoff-readiness-title"', ready)
        self.assertIn('aria-labelledby="handoff-focus-title"', ready)
        self.assertIn('aria-labelledby="handoff-next-step-title"', ready)
        for name in ("clarify-en.json", "clarify-es.json", "stop-en.json", "stop-es.json"):
            document = self.renderer.render_triage_html(self.fixtures[name])
            self.assertNotIn('class="triage-handoff-sequence"', document)

    def test_handoff_sequence_has_responsive_print_and_forced_colors_hooks(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        self.assertIn("@media (forced-colors: active)", document)
        self.assertIn("triage-handoff-sequence", document)
        self.assertIn(".triage-handoff-sequence > li::before", document)
        self.assertIn("content: counter(handoff-step)", document)
        self.assertIn("break-inside: avoid", document)

    def test_next_step_is_localized_and_omitted_outside_ready(self) -> None:
        ready_es = self.renderer.render_triage_html(self.fixtures["ready-es.json"])
        self.assertIn("Siguiente paso manual", ready_es)
        self.assertIn("Vuelve a entrar manualmente a preparación privada y responde la única pregunta segura.", ready_es)
        for name in ("clarify-en.json", "clarify-es.json", "stop-en.json", "stop-es.json"):
            document = self.renderer.render_triage_html(self.fixtures[name])
            self.assertNotIn('class="triage-handoff-next-step"', document)

    def test_next_step_is_static_non_interactive_and_has_print_accessibility_hooks(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        next_step = document.split('class="triage-handoff-next-step"', 1)[1].split("</section>", 1)[0]
        self.assertIn('aria-labelledby="handoff-next-step-title"', next_step)
        self.assertIn('id="handoff-next-step-title"', next_step)
        for forbidden in ("<button", "<a ", "href=", "<form", "onclick=", "http://", "https://"):
            self.assertNotIn(forbidden, next_step.casefold())
        self.assertIn("break-inside: avoid", document)

    def test_handoff_preview_is_escaped_and_has_no_interactive_or_forbidden_output(self) -> None:
        triage = copy.deepcopy(self.fixtures["ready-en.json"])
        triage["facts"][0]["summary"] = "A <verified> & bounded fact."
        triage["question"]["text"] = "Which <example> should be practiced?"
        document = self.renderer.render_triage_html(triage)
        self.assertIn("A &lt;verified&gt; &amp; bounded fact.", document)
        self.assertIn("Which &lt;example&gt; should be practiced?", document)
        preview = document.split('<section class="triage-handoff-preview"', 1)[1].split("</section>", 1)[0]
        for forbidden in ("<button", "href=", "auto-start", "calendar", "http://", "https://"):
            self.assertNotIn(forbidden, preview.casefold())

    def test_ready_handoff_preview_has_localized_identity_free_context_first(self) -> None:
        expected = {
            "ready-en.json": ("Identity-free context", "Verified fact", "Question purpose", "Safe question"),
            "ready-es.json": ("Contexto sin identidad", "Hecho confirmado", "Propósito de la pregunta", "Pregunta segura"),
        }
        for name, labels in expected.items():
            with self.subTest(fixture=name):
                document = self.renderer.render_triage_html(self.fixtures[name])
                preview = document.split('<section class="triage-handoff-preview"', 1)[1].split("</section>", 1)[0]
                positions = [preview.index(f"<dt>{label}</dt>") for label in labels]
                self.assertEqual(positions, sorted(positions))
                self.assertEqual(preview.count("<dt>"), 6)
                self.assertEqual(preview.count("<dd>"), 6)

    def test_ready_handoff_context_preview_is_escaped_and_ready_only(self) -> None:
        triage = copy.deepcopy(self.fixtures["ready-en.json"])
        triage["safe_context"]["summary"] = "Role <context> & bounded summary."
        triage["handoff"]["packet"]["context_summary"] = triage["safe_context"]["summary"]
        triage["handoff"]["reentry_packet"]["context_summary"] = triage["safe_context"]["summary"]
        document = self.renderer.render_triage_html(triage)
        preview = document.split('<section class="triage-handoff-preview"', 1)[1].split("</section>", 1)[0]
        self.assertIn("Role &lt;context&gt; &amp; bounded summary.", preview)
        for name in ("clarify-en.json", "clarify-es.json", "stop-en.json", "stop-es.json"):
            document = self.renderer.render_triage_html(self.fixtures[name])
            self.assertNotIn("Identity-free context", document)
            self.assertNotIn("Contexto sin identidad", document)

    def test_handoff_preview_has_accessibility_and_print_hooks(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        self.assertIn('aria-labelledby="handoff-preview-title"', document)
        self.assertIn("handoff-preview-title", document)
        self.assertIn("break-inside: avoid", document)

    def test_ready_handoff_receipt_has_exact_localized_bring_and_do_not_bring_rows(self) -> None:
        expected = {
            "ready-en.json": (
                "Input receipt", "Bring", "Identity-free role/reply summary",
                "One verified fact", "Do not bring", "Raw recruiter text or identity",
                "Calendar or contact details", "Practice starts only after manual re-entry.",
            ),
            "ready-es.json": (
                "Recibo de entradas", "Traer", "Resumen del rol/respuesta sin identidad",
                "Un hecho confirmado", "No traer", "Texto o identidad sin resumir del reclutador",
                "Detalles de calendario o contacto", "La práctica comienza solo después del reingreso manual.",
            ),
        }
        for name, labels in expected.items():
            document = self.renderer.render_triage_html(self.fixtures[name])
            receipt = document.split('<section class="triage-handoff-receipt"', 1)[1].split("</section>", 1)[0]
            for label in labels:
                self.assertIn(label, receipt)
            self.assertEqual(receipt.count("<li>"), 4)
            self.assertNotIn("<dt>", receipt)
            self.assertNotIn("<dd>", receipt)

    def test_ready_handoff_places_safe_question_before_receipt(self) -> None:
        for name in ("ready-en.json", "ready-es.json"):
            with self.subTest(fixture=name):
                ready = self.renderer.render_triage_html(self.fixtures[name])
                self.assertLess(
                    ready.index('class="triage-handoff-next-step"'),
                    ready.index('class="triage-handoff-preview"'),
                )
                self.assertLess(
                    ready.index('class="triage-handoff-preview"'),
                    ready.index('class="triage-handoff-receipt"'),
                )
        for name in ("clarify-en.json", "clarify-es.json", "stop-en.json", "stop-es.json"):
            document = self.renderer.render_triage_html(self.fixtures[name])
            self.assertNotIn('class="triage-handoff-receipt"', document)

    def test_ready_handoff_renders_localized_packet_preparation_scope_and_ids(self) -> None:
        expected = {
            "ready-en.json": ("Preparation scope", "Eligibility boundary"),
            "ready-es.json": ("Alcance de preparación", "Apertura de filtro"),
        }
        for name, labels in expected.items():
            with self.subTest(fixture=name):
                document = self.renderer.render_triage_html(self.fixtures[name])
                preview = document.split('<section class="triage-handoff-preview"', 1)[1].split("</section>", 1)[0]
                for label in labels:
                    self.assertIn(label, preview)
                self.assertNotIn("F-001", preview)
                self.assertNotIn("Q-001", preview)
                self.assertNotIn("snap-triage-001", preview)

    def test_packet_scope_is_ready_only_and_static(self) -> None:
        ready = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        self.assertIn('class="triage-handoff-preview"', ready)
        for name in ("clarify-en.json", "clarify-es.json", "stop-en.json", "stop-es.json"):
            document = self.renderer.render_triage_html(self.fixtures[name])
            self.assertNotIn("Preparation scope", document)
            self.assertNotIn("Alcance de preparación", document)
        preview = ready.split('<section class="triage-handoff-preview"', 1)[1].split("</section>", 1)[0]
        for forbidden in ("<a ", "<button", "<form", "http://", "https://", "calendar", "contact"):
            self.assertNotIn(forbidden, preview.casefold())

    def test_handoff_description_links_scope_and_privacy_to_aside(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        self.assertIn('aria-describedby="handoff-description"', document)
        self.assertIn('id="handoff-description"', document)

    def test_handoff_receipt_is_static_and_keeps_responsive_print_hooks(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        receipt = document.split('<section class="triage-handoff-receipt"', 1)[1].split("</section>", 1)[0]
        for forbidden in ("<button", "<a ", "href=", "<form", "onclick=", "http://", "https://"):
            self.assertNotIn(forbidden, receipt.casefold())
        self.assertIn("triage-handoff-receipt", document)
        self.assertIn("break-inside: avoid", document)

    def test_ready_handoff_receipt_uses_two_explicit_labelled_groups(self) -> None:
        expected = {
            "ready-en.json": ("Bring", "Do not bring"),
            "ready-es.json": ("Traer", "No traer"),
        }
        for name, labels in expected.items():
            document = self.renderer.render_triage_html(self.fixtures[name])
            receipt = document.split('<section class="triage-handoff-receipt"', 1)[1].split("</section>", 1)[0]
            self.assertEqual(receipt.count('class="triage-handoff-receipt-group"'), 2)
            for label in labels:
                self.assertIn(label, receipt)
            self.assertIn('aria-labelledby="receipt-bring-title"', receipt)
            self.assertIn('aria-labelledby="receipt-do-not-bring-title"', receipt)
            self.assertIn('id="receipt-bring-title"', receipt)
            self.assertIn('id="receipt-do-not-bring-title"', receipt)
            self.assertEqual(receipt.count('class="triage-handoff-receipt-list"'), 2)
            self.assertIn('<ul class="triage-handoff-receipt-list" aria-labelledby="receipt-bring-title">', receipt)
            self.assertIn('<ul class="triage-handoff-receipt-list" aria-labelledby="receipt-do-not-bring-title">', receipt)

    def test_receipt_groups_keep_allowed_before_forbidden_and_two_list_items_each(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        receipt = document.split('<section class="triage-handoff-receipt"', 1)[1].split("</section>", 1)[0]
        bring_start = receipt.index('id="receipt-bring-title"')
        forbidden_start = receipt.index('id="receipt-do-not-bring-title"')
        self.assertLess(bring_start, forbidden_start)
        groups = receipt.split('class="triage-handoff-receipt-group"')[1:]
        self.assertEqual(len(groups), 2)
        for group in groups:
            self.assertEqual(group.count("<li>"), 2)
            self.assertNotIn("<dt>", group)
            self.assertNotIn("<dd>", group)

    def test_receipt_group_lists_are_accessibly_labelled_and_static(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        receipt = document.split('<section class="triage-handoff-receipt"', 1)[1].split("</section>", 1)[0]
        self.assertEqual(receipt.count('class="triage-handoff-receipt-group"'), 2)
        self.assertEqual(receipt.count('<ul class="triage-handoff-receipt-list"'), 2)
        for forbidden in ("<button", "<a ", "href=", "<form", "onclick="):
            self.assertNotIn(forbidden, receipt.casefold())

    def test_ready_handoff_explains_three_categorical_readiness_rows_and_follows_decision(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        handoff = document.split('<aside class="triage-section triage-handoff"', 1)[1]
        decision_end = document.index('</section>', document.index('id="decision-title"'))
        handoff_start = document.index('<aside class="triage-section triage-handoff"')
        self.assertGreater(handoff_start, decision_end)
        self.assertIn('aria-labelledby="handoff-readiness-title"', handoff)
        self.assertIn('id="handoff-readiness-title"', handoff)
        for label in ("Stage", "Recruiter screen", "Role context", "Confirmed", "Critical constraints"):
            self.assertIn(label, document)
        self.assertIn('class="triage-handoff-readiness"', document)
        self.assertIn('class="triage-handoff-readiness-row"', document)

    def test_readiness_rows_are_localized_and_omitted_for_clarify_or_stop(self) -> None:
        ready_es = self.renderer.render_triage_html(self.fixtures["ready-es.json"])
        for label in ("Etapa", "Filtro inicial", "Contexto del rol", "Confirmado", "Restricciones críticas"):
            self.assertIn(label, ready_es)
        for name in ("clarify-en.json", "clarify-es.json", "stop-en.json", "stop-es.json"):
            document = self.renderer.render_triage_html(self.fixtures[name])
            self.assertNotIn('<section class="triage-handoff-readiness"', document)

    def test_tampered_readiness_enum_is_rejected_before_render(self) -> None:
        triage = copy.deepcopy(self.fixtures["ready-en.json"])
        triage["safe_context"]["role_context"] = "confirmed-ish"  # type: ignore[index]
        with self.assertRaises(self.renderer.TriageValidationError):
            self.renderer.render_triage_html(triage)

    def test_escapes_safe_prose_and_keeps_state_updates_textual(self) -> None:
        triage = copy.deepcopy(self.fixtures["clarify-en.json"])
        triage["safe_context"]["summary"] = "A <private> & bounded summary."
        document = self.renderer.render_triage_html(triage)
        self.assertIn("A &lt;private&gt; &amp; bounded summary.", document)
        self.assertNotIn("A <private> & bounded summary.", document)
        state_start = document.index('class="triage-state')
        state_end = document.index(">", state_start)
        self.assertNotIn("aria-live", document[state_start:state_end])
        self.assertIn("Clarify first", document)

    def test_render_gate_rejects_sensitive_prose_in_each_rendered_field(self) -> None:
        mutations = {
            "identity": "The recruiter is Jordan Lee.",
            "company": "The employer is Acme Corporation.",
            "raw": "Quoted inbound content says to call.",
            "action": "Submit the reply externally.",
            "time": "A call at 2 pm is proposed.",
            "guarantee": "This will result in an offer.",
            "analytics": "A private dashboard has engagement metrics.",
        }
        prose_fields = (
            ("safe_context", "summary"),
            ("facts", 0, "summary"),
            ("question", "text"),
            ("blocked_claims", 0),
        )
        for violation, phrase in mutations.items():
            for path in prose_fields:
                with self.subTest(violation=violation, path=path):
                    triage = copy.deepcopy(self.fixtures["clarify-en.json"])
                    target: object = triage
                    for key in path[:-1]:
                        target = target[key]  # type: ignore[index]
                    target[path[-1]] = phrase  # type: ignore[index]
                    with self.assertRaises(self.renderer.TriageValidationError) as error:
                        self.renderer.render_triage_html(triage)
                    self.assertIn(f"session contains forbidden {violation} prose", error.exception.errors)

    def test_render_is_deterministic_and_scoped_for_mobile_print_and_reduced_motion(self) -> None:
        document = self.renderer.render_triage_html(self.fixtures["ready-en.json"])
        self.assertEqual(document, self.renderer.render_triage_html(self.fixtures["ready-en.json"]))
        for rule in (
            ".private-recruiter-triage-document",
            "@media (max-width: 640px)",
            "@media (prefers-reduced-motion: reduce)",
            "@media print",
        ):
            self.assertIn(rule, document)

    def test_cli_writes_mode_0600_deterministic_output_and_rejects_symlink_targets(self) -> None:
        fixture = FIXTURE_DIRECTORY / "ready-en.json"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = root / "first.html"
            second = root / "second.html"
            command = [sys.executable, "-B", str(RENDERER_PATH), str(fixture)]
            first_result = subprocess.run(
                [*command, "--output", str(first)],
                capture_output=True,
                text=True,
                check=False,
            )
            second_result = subprocess.run(
                [*command, "--output", str(second)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first_result.returncode, 0, first_result.stderr)
            self.assertEqual(second_result.returncode, 0, second_result.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(stat.S_IMODE(first.stat().st_mode), 0o600)

            target = root / "target.html"
            target.write_text("unchanged", encoding="utf-8")
            symlink = root / "link.html"
            os.symlink(target, symlink)
            unsafe_result = subprocess.run(
                [*command, "--output", str(symlink), "--force"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(unsafe_result.returncode, 3, unsafe_result.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), "unchanged")


if __name__ == "__main__":
    unittest.main()
