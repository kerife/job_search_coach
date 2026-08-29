"""Contracts for the private recruiter target shortlist artifact."""

from __future__ import annotations

import copy
import datetime as dt
import json
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_recruiter_target_shortlist import _write_private_json, build_shortlist  # noqa: E402
from build_recruiter_target_decision_gate import build_decision_gate  # noqa: E402
from render_recruiter_target_shortlist import _cli as render_cli, render_shortlist_html, write_shortlist_html  # noqa: E402
from validate_recruiter_target_shortlist import validate_shortlist  # noqa: E402


from route_recruiter_target_shortlist import route_recruiter_request, route_recruiter_screen_intake  # noqa: E402


def valid_plan() -> dict[str, object]:
    return {
        "network_goal": "Review context-qualified recruiter paths for platform roles.",
        "target_segments": ["named_recruiter", "warm_referral", "technical_peer"],
        "source_queries": ["platform recruiter visible specialty", "alumni platform engineering", "site reliability peer"],
        "warm_path_first": True,
        "context_quality_gate": "named target plus visible specialty, shared context, supported proof, and no contact risk",
        "outreach_batch_limit": 3,
        "candidate_time_budget": "45 minutes weekly",
        "stop_condition": "Stop when context is missing, declined, closed, unsafe, or authorization is absent.",
    }


def valid_targets() -> list[dict[str, object]]:
    return [
        {
            "target_label": "Named platform recruiter",
            "contact_category": "named_recruiter",
            "company_or_specialty": "Platform engineering",
            "context_source": "Visible platform specialty and role context",
            "context_state": "named_context",
            "relationship_warmth": "cold_contextual",
            "target_theme": "Reliability and delivery systems",
            "supported_fact_ids": ["F-001"],
            "missing_context": "none",
            "priority_score": 92,
            "decision": "advance",
            "decision_reason": "Named specialty and supported proof fit the target theme.",
            "personalization_trigger": "Visible platform specialty",
            "recommended_draft_type": "recruiter_interest",
            "contactability_status": "contactable",
            "do_not_contact_reason": "none",
            "next_safe_action": "draft_only_review",
        },
        {
            "target_label": "Alumni referral path",
            "contact_category": "warm_referral",
            "company_or_specialty": "Reliability community",
            "context_source": "Candidate-provided alumni bridge",
            "context_state": "named_context",
            "relationship_warmth": "warm",
            "target_theme": "Operational resilience",
            "supported_fact_ids": ["F-002"],
            "missing_context": "Confirm current role scope before drafting.",
            "priority_score": 81,
            "decision": "clarify",
            "decision_reason": "The bridge is useful but current scope needs confirmation.",
            "personalization_trigger": "Alumni connection",
            "recommended_draft_type": "referral_request",
            "contactability_status": "context_needed",
            "do_not_contact_reason": "missing_context",
            "next_safe_action": "collect_recipient_context",
        },
        {
            "target_label": "Community technical peer",
            "contact_category": "technical_peer",
            "company_or_specialty": "Cloud operations",
            "context_source": "Community topic only",
            "context_state": "context_needed",
            "relationship_warmth": "unknown",
            "target_theme": "Cloud operations",
            "supported_fact_ids": [],
            "missing_context": "Need a named shared context and supported proof.",
            "priority_score": 45,
            "decision": "pause",
            "decision_reason": "Topic overlap alone is insufficient for a useful draft.",
            "personalization_trigger": "none",
            "recommended_draft_type": "connection_note",
            "contactability_status": "context_needed",
            "do_not_contact_reason": "no_context",
            "next_safe_action": "record_observation_only",
        },
    ]


class RecruiterTargetShortlistTests(unittest.TestCase):
    def test_screen_intake_router_fails_closed_for_deeply_nested_context(self) -> None:
        gate = build_decision_gate(build_shortlist("en", "2026-08-27", valid_plan(), valid_targets()))
        nested: object = {}
        for _ in range(500):
            nested = {"nested": nested}
        routed = route_recruiter_screen_intake(gate, "T-001", {"nested": nested})
        self.assertEqual("recruiter_target_screen_intake", routed["route_kind"])
        self.assertEqual("needs_intake", routed["case_state"])
        self.assertIsNone(routed["artifact"])

    def test_builder_returns_deterministic_closed_private_artifact(self) -> None:
        built = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
        self.assertEqual([], validate_shortlist(built, as_of=date(2026, 8, 27)))
        self.assertEqual("recruiter-target-shortlist-v1", built["schema_version"])
        self.assertEqual("T-001", built["targets"][0]["target_id"])
        self.assertEqual("advance", built["batch_decision"])
        self.assertEqual("T-001", built["top_priority_target_id"])
        self.assertFalse(built["delivery"]["no_message_action"] is False)

    def test_priority_card_has_legacy_background_fallback_before_color_mix(self) -> None:
        css = (ROOT / "plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.shortlist-priority-card\s*\{[^}]*background:\s*var\(--surface\);[^}]*background:\s*color-mix\(")

    def test_validator_blocks_advance_without_context_or_supported_proof(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        value["targets"][0]["context_state"] = "context_needed"
        value["targets"][0]["supported_fact_ids"] = []
        errors = validate_shortlist(value, as_of=date(2026, 8, 27))
        self.assertIn("targets[0].advance requires named context, supported facts, and no missing context", errors)

    def test_validator_reconciles_non_advance_contactability_and_reason(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        value["targets"][1]["contactability_status"] = "contactable"
        value["targets"][1]["do_not_contact_reason"] = "missing_context"
        value["targets"][2]["contactability_status"] = "do_not_contact"
        value["targets"][2]["do_not_contact_reason"] = "none"
        errors = validate_shortlist(value, as_of=date(2026, 8, 27))
        self.assertIn("targets[1].contactability_status cannot be contactable for clarify", errors)
        self.assertIn("targets[1].contactability_status requires do_not_contact_reason=none", errors)
        self.assertIn("targets[2].do_not_contact_reason must name a reason when contactability is do_not_contact", errors)

    def test_validator_rejects_future_evaluation_date(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        self.assertIn("as_of cannot be in the future", validate_shortlist(value, as_of=date.today() + dt.timedelta(days=1)))

    def test_validator_rejects_unhashable_fact_ids_without_traceback(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        value["targets"][0]["supported_fact_ids"] = [["F-001"]]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPTS / "validate_recruiter_target_shortlist.py"), str(path), "--as-of", "2026-08-27"],
                capture_output=True,
                text=True,
            )
        self.assertEqual(2, result.returncode)
        self.assertEqual('{"error":{"code":"invalid_shortlist"}}\n', result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_validator_rejects_target_identity_material_and_unapproved_action(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        value["targets"][0]["context_source"] = "https://private.example/profile"
        value["targets"][0]["next_safe_action"] = "send_message"
        errors = validate_shortlist(value, as_of=date(2026, 8, 27))
        self.assertTrue(any("restricted material" in error for error in errors))
        self.assertIn("targets[0].next_safe_action has invalid value", errors)

    def test_builder_rejects_phone_credential_marker_and_generic_local_path(self) -> None:
        for value in (
            "Call me at +52 55 1234 5678",
            "bearer abcdefghijklmnopqrstuvwxyz123456",
            "/tmp/candidate.txt",
            "person&amp;#64;example.com",
            "https:&amp;#x2F;&amp;#x2F;linkedin.com&amp;#x2F;in&amp;#x2F;synthetic",
        ):
            targets = copy.deepcopy(valid_targets())
            targets[0]["context_source"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_shortlist("en", "2026-08-27", valid_plan(), targets)

    def test_renderer_is_bilingual_compact_and_never_exposes_target_ids(self) -> None:
        value = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
        rendered = render_shortlist_html(value)
        self.assertIn("Objetivos de reclutamiento", rendered)
        self.assertIn("No contactar todavía", rendered)
        self.assertIn("Named platform recruiter", rendered)
        self.assertNotIn("T-001", rendered)
        self.assertNotIn("F-001", rendered)
        self.assertIn("class=\"target-shortlist-card target-shortlist-card--advance\"", rendered)
        english = copy.deepcopy(value)
        english["locale"] = "en"
        english_rendered = render_shortlist_html(english)
        self.assertIn("Recruiter target shortlist", english_rendered)
        self.assertIn("Do not contact yet", english_rendered)

    def test_renderer_promotes_localized_date_and_batch_next_step(self) -> None:
        value = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
        rendered = render_shortlist_html(value)
        self.assertIn("Revisado al", rendered)
        self.assertIn('<time datetime="2026-08-27">2026-08-27</time>', rendered)
        self.assertIn('class="shortlist-next-step shortlist-next-step--advance"', rendered)
        self.assertIn("Revisar el borrador localmente antes de cualquier contacto.", rendered)
        self.assertEqual(1, rendered.count('class="shortlist-next-step '))
        english = copy.deepcopy(value)
        english["locale"] = "en"
        english_rendered = render_shortlist_html(english)
        self.assertIn("Reviewed on", english_rendered)
        self.assertIn('<time datetime="2026-08-27">2026-08-27</time>', english_rendered)
        self.assertIn("Review the draft locally before any contact.", english_rendered)

    def test_renderer_frames_context_priority_as_manual_ordering_not_prediction(self) -> None:
        value = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
        rendered = render_shortlist_html(value)
        self.assertIn("Solo ordena la revisión; no predice respuesta", rendered)
        self.assertEqual(4, rendered.count("Solo ordena la revisión; no predice respuesta"))
        self.assertIn('class="shortlist-priority-score"', rendered)
        self.assertIn('class="target-shortlist-score-note"', rendered)
        english = copy.deepcopy(value)
        english["locale"] = "en"
        english_rendered = render_shortlist_html(english)
        self.assertIn("Orders manual review only; does not predict a response", english_rendered)
        self.assertEqual(4, english_rendered.count("Orders manual review only; does not predict a response"))
        for forbidden in ("probabilidad", "probability", "chance", "likelihood"):
            self.assertNotIn(forbidden, rendered.lower() + english_rendered.lower())

    def test_priority_score_note_has_cross_media_accessibility_contract(self) -> None:
        css = (ROOT / "plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.shortlist-priority-score\s*\{[^}]*display:\s*flex")
        self.assertIn(".target-shortlist-score-note", css)
        forced_colors = css.split("@media (forced-colors: active)", 1)[1]
        self.assertIn(".target-shortlist-score-note", forced_colors)
        print_css = css.split("@media print", 1)[1]
        self.assertIn(".target-shortlist-score-note", print_css)

    def test_validator_rejects_restricted_or_unbounded_target_segments(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        value["network_plan"]["target_segments"] = ["https://private.example/profile"]
        errors = validate_shortlist(value, as_of=dt.date(2026, 8, 27))
        self.assertIn("network_plan.target_segments[0] contains restricted material", errors)

    def test_validator_rejects_encoded_unicode_controls_in_bounded_prose(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        for path, encoded in (
            ("network_plan.network_goal", "safe&#x0a;injected"),
            ("targets[0].target_label", "safe&amp;#x0a;injected"),
            ("targets[0].decision_reason", "safe%0ainjected"),
        ):
            mutated = copy.deepcopy(value)
            if path.startswith("network_plan"):
                mutated["network_plan"]["network_goal"] = encoded
            elif path.endswith("target_label"):
                mutated["targets"][0]["target_label"] = encoded
            else:
                mutated["targets"][0]["decision_reason"] = encoded
            with self.subTest(path=path):
                self.assertIn(
                    f"{path} contains restricted material",
                    validate_shortlist(mutated, as_of=dt.date(2026, 8, 27)),
                )

    def test_builder_rejects_future_as_of_date(self) -> None:
        with self.assertRaises(ValueError):
            build_shortlist("en", "2999-01-01", valid_plan(), valid_targets())

    def test_recruiter_dates_require_canonical_calendar_form(self) -> None:
        for value in ("2026-W32-1", "2026-08-03T00:00:00"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    build_shortlist("en", value, valid_plan(), valid_targets())
        built = build_shortlist("en", "2026-08-03", valid_plan(), valid_targets())
        built["as_of_date"] = "2026-W32-1"
        self.assertIn(
            "as_of_date must be an ISO date",
            validate_shortlist(built, as_of=date(2026, 8, 27)),
        )

    def test_renderer_localizes_safe_actions_and_shows_decision_counts(self) -> None:
        value = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
        rendered = render_shortlist_html(value)
        self.assertIn("Revisar borrador", rendered)
        self.assertIn("Recopilar contexto", rendered)
        self.assertIn("Avanzar", rendered)
        self.assertNotIn("draft_only_review", rendered)
        self.assertNotIn("collect_recipient_context", rendered)
        self.assertIn("shortlist-decision-counts", rendered)

    def test_renderer_hides_internal_segment_and_missing_context_enums(self) -> None:
        value = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
        rendered = render_shortlist_html(value)
        self.assertIn("Reclutador identificado", rendered)
        self.assertIn("Referido o vínculo cálido", rendered)
        self.assertIn("Par técnico o de comunidad", rendered)
        self.assertIn("Sin contexto adicional", rendered)
        for internal in ("named_recruiter", "warm_referral", "technical_peer", ">none<"):
            self.assertNotIn(internal, rendered)

        english = copy.deepcopy(value)
        english["locale"] = "en"
        english_rendered = render_shortlist_html(english)
        self.assertIn("Named recruiter", english_rendered)
        self.assertIn("Warm referral or connection", english_rendered)
        self.assertIn("Technical or community peer", english_rendered)
        self.assertIn("No additional context", english_rendered)
        for internal in ("named_recruiter", "warm_referral", "technical_peer", ">none<"):
            self.assertNotIn(internal, english_rendered)

    def test_renderer_explains_non_advance_contact_boundary_without_internal_reason_tokens(self) -> None:
        reason_copy = {
            "no_context": ("Falta contexto", "Context is missing"),
            "missing_context": ("Falta confirmar el contexto", "Context needs confirmation"),
            "no_consent": ("No hay consentimiento", "Consent has not been granted"),
            "confidentiality_risk": ("Riesgo de confidencialidad", "Confidentiality risk"),
            "unsupported_claim": ("Afirmación sin respaldo", "Unsupported claim"),
            "closed_role": ("Rol cerrado", "Role is closed"),
            "missing_authorization": ("Falta autorización", "Authorization is missing"),
        }
        for reason, (spanish, english) in reason_copy.items():
            value = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
            value["targets"][1]["do_not_contact_reason"] = reason
            rendered = render_shortlist_html(value)
            self.assertIn("Límite de contacto", rendered)
            self.assertIn(spanish, rendered)
            self.assertNotIn(reason, rendered)

            value["locale"] = "en"
            english_rendered = render_shortlist_html(value)
            self.assertIn("Contact boundary", english_rendered)
            self.assertIn(english, english_rendered)
            self.assertNotIn(reason, english_rendered)

        baseline = render_shortlist_html(build_shortlist("es", "2026-08-27", valid_plan(), valid_targets()))
        self.assertNotIn("Límite de contacto", baseline.split("Named platform recruiter", 1)[0])

    def test_contact_boundary_copy_has_cross_media_accessibility_contract(self) -> None:
        css = (ROOT / "plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.css").read_text(encoding="utf-8")
        self.assertIn(".target-shortlist-no-contact", css)
        self.assertRegex(css, r"\.target-shortlist-no-contact\s*\{[^}]*border")
        self.assertIn(".target-shortlist-no-contact", css.split("@media (prefers-contrast: more)", 1)[1])
        self.assertIn(".target-shortlist-no-contact", css.split("@media (forced-colors: active)", 1)[1])
        self.assertIn(".target-shortlist-no-contact", css.split("@media print", 1)[1])

    def test_print_layout_keeps_target_cards_and_privacy_boundary_together(self) -> None:
        css = (ROOT / "plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.css").read_text(encoding="utf-8")
        self.assertIn("@page", css)
        print_css = css.split("@media print", 1)[1]
        for selector in (".target-shortlist-card", ".shortlist-footer"):
            block = re.search(rf"{re.escape(selector)}\s*\{{.*?\}}", print_css, re.S)
            self.assertIsNotNone(block)
            self.assertIn("break-inside: avoid", block.group(0))
            self.assertIn("page-break-inside: avoid", block.group(0))

    def test_renderer_exposes_keyboard_and_ordered_list_accessibility_contract(self) -> None:
        rendered = render_shortlist_html(build_shortlist("es", "2026-08-27", valid_plan(), valid_targets()))
        self.assertIn('href="#main-content"', rendered)
        self.assertIn('id="main-content" tabindex="-1"', rendered)
        self.assertIn('aria-labelledby="targets-title"', rendered)
        self.assertIn('<h2 id="targets-title">Objetivos revisados</h2>', rendered)
        self.assertEqual(3, rendered.count('<li class="target-shortlist-item">'))
        self.assertEqual(1, rendered.count('aria-current="location"'))
        self.assertIn("Ruta de revisión recruiter", rendered)
        self.assertIn("Superficie actual de revisión", rendered)
        css = (ROOT / "plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.css").read_text(encoding="utf-8")
        self.assertIn(":focus-visible", css)
        self.assertIn("@media (prefers-contrast: more)", css)
        self.assertIn("@media (forced-colors: active)", css)

    def test_batch_next_step_has_print_and_forced_color_contract(self) -> None:
        css = (ROOT / "plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.css").read_text(encoding="utf-8")
        self.assertIn(".shortlist-next-step", css)
        self.assertIn(".shortlist-next-step--advance", css)
        forced_colors = css.split("@media (forced-colors: active)", 1)[1]
        self.assertIn(".shortlist-next-step", forced_colors)
        print_css = css.split("@media print", 1)[1]
        self.assertRegex(print_css, r"\.shortlist-next-step\s*\{[^}]*break-inside: avoid")

    def test_shortlist_forced_colors_pin_system_surface_and_text(self) -> None:
        css = (ROOT / "plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.css").read_text(encoding="utf-8")
        forced_colors = css.split("@media (forced-colors: active)", 1)[1]
        block = re.search(r"\.shortlist-card, \.shortlist-next-step\s*\{([^}]*)\}", forced_colors, re.S)
        self.assertIsNotNone(block)
        self.assertIn("background: Canvas", block.group(1))
        self.assertIn("color: CanvasText", block.group(1))

    def test_batch_next_step_has_legacy_background_fallback_before_color_mix(self) -> None:
        css = (ROOT / "plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.shortlist-next-step\s*\{[^}]*background:\s*var\(--surface\);[^}]*background:\s*color-mix\(")

    def test_priority_card_has_explicit_forced_colors_tokens(self) -> None:
        css = (ROOT / "plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.css").read_text(encoding="utf-8")
        forced_colors = css.split("@media (forced-colors: active)", 1)[1]
        self.assertRegex(
            forced_colors,
            r"\.shortlist-priority-card\s*\{[^}]*background:\s*Canvas;[^}]*color:\s*CanvasText;[^}]*border-color:\s*CanvasText;",
        )

    def test_root_route_builds_ready_artifact_or_one_intake_question(self) -> None:
        ready = route_recruiter_request(
            "Quiero expandir mi red de recruiters para conseguir un primer filtro.",
            locale="en",
            as_of_date="2026-08-27",
            network_plan=valid_plan(),
            targets=valid_targets(),
        )
        self.assertEqual("recruiter_target_shortlist", ready["route_kind"])
        self.assertEqual("ready", ready["case_state"])
        self.assertIsNotNone(ready["artifact"])
        intake = route_recruiter_request("Quiero buscar recruiters.", locale="es", as_of_date="2026-08-27")
        self.assertEqual("needs_intake", intake["case_state"])
        self.assertEqual("ask_one_intake_question", intake["next_action"])
        self.assertIsNone(intake["artifact"])

    def test_root_route_recovers_from_non_string_locale_without_traceback(self) -> None:
        for locale in (None, [], {}, 7):
            with self.subTest(locale=locale):
                result = route_recruiter_request(
                    "How do I network with recruiters?",
                    locale=locale,
                    as_of_date="2026-08-27",
                )
                self.assertEqual("needs_intake", result["case_state"])
                self.assertEqual("ask_one_intake_question", result["next_action"])
                self.assertIsNone(result["artifact"])
                self.assertIn("intake_question", result)

    def test_root_route_preserves_external_action_authorization_in_ready_and_intake(self) -> None:
        ready = route_recruiter_request(
            "Quiero expandir mi red de recruiters y enviar mensajes a los objetivos.",
            locale="es",
            as_of_date="2026-08-27",
            network_plan=valid_plan(),
            targets=valid_targets(),
        )
        self.assertTrue(ready["authorization_required"])
        self.assertTrue(ready["artifact"]["delivery"]["authorization_required"])

        intake = route_recruiter_request(
            "Quiero buscar recruiters y agendar una llamada.",
            locale="es",
            as_of_date="2026-08-27",
        )
        self.assertEqual("needs_intake", intake["case_state"])
        self.assertTrue(intake["authorization_required"])

    def test_root_route_keeps_analysis_only_networking_without_authorization(self) -> None:
        routed = route_recruiter_request(
            "How do I network with recruiters?",
            locale="en",
            as_of_date="2026-08-27",
        )
        self.assertFalse(routed["authorization_required"])

    def test_root_route_intake_question_is_actionable_and_bounded(self) -> None:
        for request, locale, markers in (
            (
                "Quiero buscar recruiters.",
                "es",
                ("3–6", "segmentos", "3–5", "tiempo semanal", "condición de pausa"),
            ),
            (
                "How do I network with recruiters?",
                "en",
                ("3–6", "segments", "3–5", "weekly time", "stop condition"),
            ),
        ):
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-27")
            with self.subTest(locale=locale):
                for marker in markers:
                    self.assertIn(marker, routed["intake_question"])

    def test_root_route_renders_private_surface_before_returning_ready(self) -> None:
        ready = route_recruiter_request(
            "Quiero expandir mi red de recruiters para conseguir un primer filtro.",
            locale="es",
            as_of_date="2026-08-27",
            network_plan=valid_plan(),
            targets=valid_targets(),
        )
        self.assertEqual("ready", ready["case_state"])
        self.assertIn("Objetivos de reclutamiento", ready["rendered_html"])
        self.assertNotIn("{{", ready["rendered_html"])
        self.assertNotIn("T-001", ready["rendered_html"])
        self.assertNotIn("draft_only_review", ready["rendered_html"])
        self.assertEqual("review_recruiter_target_shortlist", ready["next_action"])

    def test_root_route_requires_compound_recruiter_intent(self) -> None:
        for request in (
            "Necesito un Network Engineer para mi CV.",
            "Quiero trabajar en mi network de datos.",
            "Ayúdame a preparar una entrevista técnica.",
        ):
            routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("ordinary_professional_growth", routed["route_kind"])

    def test_root_route_accepts_natural_english_recruiter_intent(self) -> None:
        for request in (
            "How do I network with recruiters?",
            "Prepare me for a first interview with a recruiter.",
            "I want to contact recruiters",
            "I want to contact a technical recruiter",
            "Help me reach out to recruiters",
            "Help me reach out to a senior recruiter",
            "How do I reach a recruiter?",
            "How do I connect with recruiters?",
            "Necesito prepararme para mi primera entrevista con un reclutador.",
            "Quiero contactar a reclutadores",
            "Necesito una entrevista técnica con un reclutador",
            "Prepare me for a recruiter technical interview",
            "Quiero una entrevista con un recruiter",
            "Quiero contactar a un recruiter para hablar de oportunidades",
            "Quiero hacer networking con recruiters.",
            "Quiero ampliar mi red profesional con reclutadores.",
        ):
            locale = "es" if request.startswith("Quiero") else "en"
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("recruiter_target_shortlist", routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertEqual("ask_one_intake_question", routed["next_action"])

    def test_root_route_accepts_explicit_recruiter_outreach_variants(self) -> None:
        for request in (
            "I want recruiter outreach",
            "Help me with recruiter networking",
            "I need recruiter connections",
        ):
            routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("recruiter_target_shortlist", routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertEqual("ask_one_intake_question", routed["next_action"])

    def test_root_route_accepts_defined_recruiter_articles_in_english_and_spanish(self) -> None:
        for request, locale in (
            ("Prepare me for a first interview with the recruiter.", "en"),
            ("Prepárame para mi primera entrevista con el reclutador.", "es"),
            ("Prepárame para mi primera entrevista con la reclutadora.", "es"),
            ("I have an interview with the recruiter; help me prepare.", "en"),
            ("Tengo una entrevista con la reclutadora; ayúdame a prepararme.", "es"),
        ):
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("recruiter_target_shortlist", routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertEqual("ask_one_intake_question", routed["next_action"])

    def test_root_route_accepts_initial_recruiter_conversation_variants(self) -> None:
        for request, locale in (
            ("Prepare me for an initial interview with the recruiter.", "en"),
            ("Help me prepare for my first call with a recruiter.", "en"),
            ("Prepárame para una entrevista inicial con el reclutador.", "es"),
            ("Necesito practicar mi primera llamada con la reclutadora.", "es"),
        ):
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("recruiter_target_shortlist", routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertEqual("ask_one_intake_question", routed["next_action"])

    def test_root_route_sends_completed_recruiter_screens_to_the_correct_artifact_free_handoff(self) -> None:
        cases = (
            ("I had a recruiter screen today; help me debrief.", "private_recruiter_screen_debrief", "track-career-outcomes"),
            ("How do I debrief my recruiter interview and prepare for the next stage?", "private_recruiter_screen_debrief", "track-career-outcomes"),
            ("I completed the recruiter screen and want to prepare for the hiring manager stage.", "private_recruiter_screen_debrief", "track-career-outcomes"),
            ("I completed a recruiter interview and need a debrief.", "private_recruiter_screen_debrief", "track-career-outcomes"),
            ("I completed a recruiter interview today.", "private_recruiter_screen_debrief", "track-career-outcomes"),
            ("Ayúdame a hacer el debrief de mi entrevista con el reclutador.", "private_recruiter_screen_debrief", "track-career-outcomes"),
            ("Quiero revisar mi entrevista con el reclutador y saber cuál es la siguiente etapa.", "private_recruiter_screen_debrief", "track-career-outcomes"),
            ("I need to prepare for the next stage after a recruiter screen.", "private_recruiter_next_stage_review", "prepare-role-interviews"),
        )
        for request, route_kind, selected_module in cases:
            routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual(route_kind, routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertEqual(selected_module, routed["selected_module"])
                self.assertEqual("collect_debrief_context", routed["next_action"])
                self.assertIsNone(routed["artifact"])
                self.assertNotRegex(routed["intake_question"], r"(?:T-\d{3}|D-\d{3}|F-\d{3}|https?://)")

    def test_root_route_recognizes_recruiter_calls_and_conversations_as_post_screen_context(self) -> None:
        cases = (
            ("I had a recruiter call today; help me debrief.", "private_recruiter_screen_debrief"),
            ("I spoke with a recruiter yesterday and want to review it.", "private_recruiter_screen_debrief"),
            ("Tuve una llamada con el reclutador y quiero hacer el debrief.", "private_recruiter_screen_debrief"),
            ("Después de una llamada con un reclutador, ¿cuál es el siguiente paso?", "private_recruiter_next_stage_review"),
            ("After a recruiter conversation, what comes next?", "private_recruiter_next_stage_review"),
        )
        for request, route_kind in cases:
            routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual(route_kind, routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertEqual("collect_debrief_context", routed["next_action"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_recognizes_screening_as_recruiter_screen_context(self) -> None:
        cases = (
            (
                "I completed my recruiter screening and need a debrief.",
                "private_recruiter_screen_debrief",
                "track-career-outcomes",
                "collect_debrief_context",
            ),
            (
                "After the recruiter screening, what comes next?",
                "private_recruiter_next_stage_review",
                "prepare-role-interviews",
                "collect_debrief_context",
            ),
            (
                "I have a recruiter screening next week; help me prepare.",
                "recruiter_target_screen_intake",
                "prepare-role-interviews",
                "collect_screen_intake",
            ),
            (
                "Completé el screening con el reclutador; ¿qué sigue?",
                "private_recruiter_next_stage_review",
                "prepare-role-interviews",
                "collect_debrief_context",
            ),
            (
                "Tengo un screening con el reclutador la próxima semana; ayúdame a prepararme.",
                "recruiter_target_screen_intake",
                "prepare-role-interviews",
                "collect_screen_intake",
            ),
            (
                "No asistí al screening con el reclutador; ¿qué sigue?",
                "recruiter_target_screen_intake",
                "prepare-role-interviews",
                "collect_screen_intake",
            ),
        )
        for request, route_kind, selected_module, next_action in cases:
            routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual(route_kind, routed["route_kind"])
                self.assertEqual(selected_module, routed["selected_module"])
                self.assertEqual(next_action, routed["next_action"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_keeps_generic_technical_screening_outside_recruiter_flow(self) -> None:
        for request in (
            "I have a technical screening next week; help me prepare.",
            "I completed a technical screening and need a debrief.",
        ):
            routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("ordinary_professional_growth", routed["route_kind"])
                self.assertEqual("continue_normal_routing", routed["next_action"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_sends_recruiter_alias_actions_to_reply_triage(self) -> None:
        cases = (
            "Can you email recruiting about my application?",
            "Please reply to recruiting about the role.",
            "Send a follow-up to talent acquisition.",
            "Help me contact a sourcer for opportunities.",
            "Quiero escribirle a reclutamiento sobre la vacante.",
        )
        for request in cases:
            routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("optimize-professional-profile", routed["selected_module"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertTrue(routed["authorization_required"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_keeps_hiring_manager_action_outside_recruiter_triage(self) -> None:
        routed = route_recruiter_request(
            "Can you email the hiring manager about my application?",
            locale="en",
            as_of_date="2026-08-27",
        )
        self.assertEqual("ordinary_professional_growth", routed["route_kind"])
        self.assertEqual("continue_normal_routing", routed["next_action"])
        self.assertIsNone(routed["artifact"])

    def test_root_route_recognizes_common_next_step_wording_after_recruiter_screen(self) -> None:
        for request in (
            "After a recruiter screen, what comes next?",
            "What do I do next after a recruiter interview?",
            "¿Cuál es el siguiente paso después de mi entrevista con el reclutador?",
        ):
            routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("private_recruiter_next_stage_review", routed["route_kind"])
                self.assertEqual("prepare-role-interviews", routed["selected_module"])
                self.assertEqual("collect_debrief_context", routed["next_action"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_keeps_future_or_negated_recruiter_screens_out_of_post_screen_debrief(self) -> None:
        cases = (
            "I have not had a recruiter interview yet; help me prepare.",
            "I had no recruiter screen yet; what should I prepare?",
            "I have no recruiter interview yet; help me prepare.",
            "I had a recruiter interview scheduled for next week; help me prepare.",
            "I had not attended the recruiter screen; what should I do next?",
            "I didn't attend the recruiter screen; what should I do next?",
            "I did not complete the recruiter interview; help me prepare.",
            "I never had a recruiter screen; help me prepare.",
            "I never completed the recruiter interview; help me prepare.",
            "I never went to the recruiter interview; help me prepare.",
            "I didn't go to the recruiter screen; help me prepare.",
            "I never went through the recruiter screen; help me prepare.",
            "I never spoke with a recruiter; help me prepare.",
            "I have a recruiter screen on September 2; help me prepare.",
            "My recruiter screen is this Friday; help me prepare.",
            "Tengo una entrevista con la reclutadora el viernes; ayúdame a prepararme.",
            "No he tenido el filtro con el reclutador; ¿qué sigue?",
            "No asistí al filtro con el reclutador; ¿qué sigue?",
            "No tuve la entrevista con el reclutador; ayúdame a prepararme.",
            "Nunca tuve la entrevista con el reclutador; ayúdame a prepararme.",
            "Nunca asistí al filtro con el reclutador; ¿qué hago?",
            "Nunca fui a la entrevista con el reclutador; ayúdame a prepararme.",
            "No fui a la entrevista con el reclutador; ¿qué hago?",
            "No me presenté al filtro con el reclutador; ¿qué hago?",
            "Nunca pasé por un filtro con el reclutador; ayúdame a prepararme.",
            "No hablé con el reclutador; ayúdame a preparar.",
            "Todavía no terminé la entrevista con el reclutador; ¿qué hago después?",
        )
        for request in cases:
            routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("recruiter_target_screen_intake", routed["route_kind"])
                self.assertEqual("prepare-role-interviews", routed["selected_module"])
                self.assertEqual("collect_screen_intake", routed["next_action"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_does_not_treat_post_screen_no_trouble_or_questions_as_negation(self) -> None:
        cases = (
            ("I had no trouble during my recruiter screen; help me debrief.", "private_recruiter_screen_debrief"),
            ("I had no questions after the recruiter interview; what comes next?", "private_recruiter_next_stage_review"),
        )
        for request, route_kind in cases:
            routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual(route_kind, routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertEqual("collect_debrief_context", routed["next_action"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_does_not_treat_completed_screen_dates_as_future_intent(self) -> None:
        routed = route_recruiter_request(
            "I completed a recruiter screen on Tuesday; help me debrief.",
            locale="en",
            as_of_date="2026-08-27",
        )
        self.assertEqual("private_recruiter_screen_debrief", routed["route_kind"])
        self.assertEqual("track-career-outcomes", routed["selected_module"])
        self.assertEqual("collect_debrief_context", routed["next_action"])
        self.assertIsNone(routed["artifact"])

    def test_root_route_scopes_future_dates_to_the_recruiter_event(self) -> None:
        for request in (
            "I completed a recruiter screen last week and I have a dentist appointment on Friday; help me debrief.",
            "I completed a recruiter screen; I have a follow-up on Friday; help me debrief.",
        ):
            routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("private_recruiter_screen_debrief", routed["route_kind"])
                self.assertEqual("collect_debrief_context", routed["next_action"])

    def test_root_route_does_not_treat_unrelated_invitation_as_nonattendance(self) -> None:
        cases = (
            ("I completed a recruiter screen and was invited to a panel; help me debrief.", "private_recruiter_screen_debrief"),
            ("I had a recruiter screen and was invited to the next stage; what comes next?", "private_recruiter_next_stage_review"),
        )
        for request, route_kind in cases:
            routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual(route_kind, routed["route_kind"])
                self.assertEqual("collect_debrief_context", routed["next_action"])

    def test_root_route_recognizes_future_recruiter_invites_and_relative_dates(self) -> None:
        for request in (
            "My recruiter screen is Monday; help me prepare.",
            "My recruiter screen is next Monday; help me prepare.",
            "My recruiter screen is on Monday; help me prepare.",
            "My recruiter screen is scheduled Monday; help me prepare.",
            "Recruiter screen tomorrow; help me prepare.",
            "I have a recruiter screen in two days; help me prepare.",
            "I was invited to a recruiter screen; help me prepare.",
            "I have been invited to interview with a recruiter; help me prepare.",
            "The recruiter screen was rescheduled; help me prepare.",
            "The recruiter screen got rescheduled; help me prepare.",
            "I could not attend the recruiter screen; help me prepare.",
            "I could not make the recruiter screen; help me prepare.",
            "I was not able to attend the recruiter screen; help me prepare.",
            "I declined the recruiter screen invitation; help me prepare.",
            "I will attend a recruiter screen on Monday; help me prepare.",
            "I am attending a recruiter screen Monday; help me prepare.",
            "I haven't done a recruiter screen; help me prepare.",
            "No he hecho el filtro con el reclutador; ayúdame a prepararme.",
        ):
            locale = "es" if request.startswith("No he") else "en"
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("recruiter_target_screen_intake", routed["route_kind"])
                self.assertEqual("collect_screen_intake", routed["next_action"])

    def test_root_route_recognizes_plain_preparation_language_for_upcoming_recruiter_screens(self) -> None:
        for request, locale in (
            ("I have an upcoming recruiter call, help me prepare", "en"),
            ("My recruiter call is coming up", "en"),
            ("I am getting ready for a recruiter screen", "en"),
            ("I need to prepare to talk to the recruiter", "en"),
            ("Necesito preparar una llamada con un reclutador", "es"),
            ("Necesito prepararme para una entrevista con un reclutador", "es"),
            ("Mi llamada con el recruiter es la próxima semana", "es"),
        ):
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual("recruiter_target_screen_intake", routed["route_kind"])
                self.assertEqual("prepare-role-interviews", routed["selected_module"])
                self.assertEqual("collect_screen_intake", routed["next_action"])
                self.assertEqual("needs_intake", routed["case_state"])

    def test_spanish_first_interview_preparation_with_recruiter_aliases_enters_screen_intake(self) -> None:
        for request in (
            "Necesito prepararme para una primera entrevista con adquisición de talento",
            "Tengo una entrevista inicial con reclutamiento",
            "Prepararme para hablar con un sourcer",
            "Necesito prepararme para una entrevista con un headhunter",
            "Quiero preparar la primera llamada con la reclutadora",
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-28")
                self.assertEqual("recruiter_target_screen_intake", routed["route_kind"])
                self.assertEqual("collect_screen_intake", routed["next_action"])
                self.assertFalse(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_first_interview_networking_and_technical_language_keep_boundaries(self) -> None:
        cases = (
            ("Quiero hacer networking con sourcers", "recruiter_target_shortlist"),
            ("Quiero conectar con headhunters", "recruiter_target_shortlist"),
            ("Necesito prepararme para una entrevista técnica", "ordinary_professional_growth"),
        )
        for request, expected_route in cases:
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-28")
                self.assertEqual(expected_route, routed["route_kind"])
                self.assertIsNone(routed["artifact"])

    def test_spanish_talent_acquisition_invitation_and_availability_keep_triage_boundaries(self) -> None:
        cases = (
            ("Me invitó adquisición de talento a una entrevista", "recruiter_target_screen_intake", False),
            ("Adquisición de talento me pidió disponibilidad", "private_recruiter_reply_triage", True),
        )
        for request, expected_route, expected_authorization in cases:
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-28")
                self.assertEqual(expected_route, routed["route_kind"])
                self.assertEqual(expected_authorization, routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_upcoming_recruiting_domain_language_stays_ordinary(self) -> None:
        for request in (
            "I have an upcoming recruiting systems audit.",
            "I have an upcoming recruitment pipeline review.",
            "I have an upcoming talent acquisition metrics meeting.",
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-28")
                self.assertEqual("ordinary_professional_growth", routed["route_kind"])
                self.assertEqual("continue_normal_routing", routed["next_action"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_recognizes_recruiting_aliases_for_post_screen_followthrough(self) -> None:
        for request, locale, expected_route in (
            ("I talked with the recruiter and want next steps", "en", "private_recruiter_next_stage_review"),
            ("I interviewed with recruiting; next steps?", "en", "private_recruiter_next_stage_review"),
            ("After the recruiter call, what should I do?", "en", "private_recruiter_next_stage_review"),
            ("Después de hablar con reclutamiento, ¿qué sigue?", "es", "private_recruiter_next_stage_review"),
            ("Tuve una llamada con reclutamiento, ¿qué sigue?", "es", "private_recruiter_next_stage_review"),
            ("No me han respondido después de la llamada con reclutamiento", "es", "private_recruiter_screen_debrief"),
        ):
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual(expected_route, routed["route_kind"])
                self.assertEqual("collect_debrief_context", routed["next_action"])
                self.assertEqual("needs_intake", routed["case_state"])

    def test_root_route_recognizes_relationship_and_visibility_network_language(self) -> None:
        for request in (
            "How can I build relationships with recruiters?",
            "I want to grow my network of recruiters",
            "I want to connect with more recruiters",
            "I want to get on recruiters’ radar",
            "Quiero conectar con reclutadores",
            "Quiero construir relaciones con reclutadores",
            "Quiero aumentar mi visibilidad ante reclutadores",
        ):
            locale = "es" if request.startswith("Quiero") else "en"
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual("recruiter_target_shortlist", routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertEqual("ask_one_intake_question", routed["next_action"])

    def test_root_route_recognizes_recruiter_network_word_order_variants(self) -> None:
        for request, locale in (
            ("How do I expand my recruiter network?", "en"),
            ("I want to grow my recruiter network", "en"),
            ("I want to build recruiter relationships", "en"),
            ("Necesito referidos de reclutadores", "es"),
            ("Quiero conocer reclutadores", "es"),
        ):
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual("recruiter_target_shortlist", routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertEqual("ask_one_intake_question", routed["next_action"])

    def test_root_route_keeps_generic_network_growth_outside_recruiter_shortlist(self) -> None:
        for request in (
            "How do I expand my network?",
            "I want to grow my network",
            "I need to build relationships in a technical network",
        ):
            routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual("ordinary_professional_growth", routed["route_kind"])
                self.assertEqual("not_applicable", routed["case_state"])

    def test_root_route_recognizes_recruiting_inbound_contact_without_message_verb(self) -> None:
        for request, locale in (
            ("Recruiting reached out about a role", "en"),
            ("Recruitment emailed me about a role", "en"),
            ("Me contactó reclutamiento por una vacante", "es"),
            ("Reclutamiento me pidió disponibilidad", "es"),
        ):
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_recognizes_recruiter_actor_aliases_and_natural_preparation(self) -> None:
        for request, locale in (
            ("I need to prepare for a talent acquisition call", "en"),
            ("How can I build relationships with talent acquisition?", "en"),
            ("I want to connect with talent acquisition", "en"),
            ("I want to network with people who recruit engineers", "en"),
            ("I need to prep for a recruiter screen", "en"),
            ("I have a recruiter screen soon", "en"),
            ("I need recruiter screen prep", "en"),
            ("Tengo una llamada de reclutador pronto", "es"),
        ):
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
            with self.subTest(request=request):
                expected = "recruiter_target_screen_intake" if any(marker in request.lower() for marker in ("prep", "prepare", "prepar", "screen soon", "llamada")) else "recruiter_target_shortlist"
                self.assertEqual(expected, routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])

    def test_root_route_recognizes_passive_and_called_inbound_recruiter_contact(self) -> None:
        for request in (
            "I was contacted by a recruiter about a role",
            "A recruiter got in touch with me",
            "Recruiter called me about a role",
            "Me llamó el reclutador por una vacante",
        ):
            locale = "es" if request.startswith("Me ") else "en"
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertTrue(routed["authorization_required"])

    def test_root_route_recognizes_plain_post_screen_waiting_and_thanks_language(self) -> None:
        for request in (
            "Recruiter has not gotten back to me after the screen",
            "No update after recruiter interview",
            "Still waiting after recruiter screen",
            "I have not heard anything after my recruiter call",
            "After the recruiter screen, should I thank them?",
        ):
            routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual("private_recruiter_screen_debrief", routed["route_kind"])
                self.assertEqual("collect_debrief_context", routed["next_action"])

    def test_root_route_recognizes_negative_post_screen_outcomes(self) -> None:
        for request, locale in (
            ("I got rejected after talking to the recruiter", "en"),
            ("The recruiter rejected me after the interview", "en"),
            ("I failed the recruiter screen; what should I learn?", "en"),
            ("El reclutador me rechazó, ¿qué sigue?", "es"),
        ):
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual("private_recruiter_screen_debrief", routed["route_kind"])
                self.assertEqual("track-career-outcomes", routed["selected_module"])
                self.assertEqual("collect_debrief_context", routed["next_action"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_keeps_nonattendance_out_of_negative_outcome_debrief(self) -> None:
        for request, locale in (
            ("I did not attend the recruiter screen; help me prepare.", "en"),
            ("Nunca pasé por un filtro con el reclutador; ayúdame a prepararme.", "es"),
        ):
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual("recruiter_target_screen_intake", routed["route_kind"])
                self.assertEqual("collect_screen_intake", routed["next_action"])

    def test_root_route_recognizes_indirect_negative_post_screen_outcomes(self) -> None:
        for request, locale in (
            ("Me rechazaron después de hablar con el reclutador.", "es"),
            ("Me descartaron después del filtro con el reclutador.", "es"),
            ("I got a rejection after the recruiter screen.", "en"),
            ("The recruiter said they went with another candidate after my screen.", "en"),
            ("The recruiter screen was unsuccessful.", "en"),
            ("La reclutadora decidió seguir con otra persona después del filtro.", "es"),
        ):
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual("private_recruiter_screen_debrief", routed["route_kind"])
                self.assertEqual("track-career-outcomes", routed["selected_module"])
                self.assertEqual("collect_debrief_context", routed["next_action"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_keeps_negative_screening_paraphrases_before_next_stage(self) -> None:
        for request, locale in (
            ("I failed the recruiter screening.", "en"),
            ("I didn't get past the recruiter screen.", "en"),
            ("The recruiter moved forward with another candidate.", "en"),
            ("I got a no from recruiting after the screen; what should I do?", "en"),
            ("No pasé el filtro con el reclutador.", "es"),
            ("La reclutadora siguió con otra persona después del filtro.", "es"),
        ):
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual("private_recruiter_screen_debrief", routed["route_kind"])
                self.assertEqual("track-career-outcomes", routed["selected_module"])
                self.assertEqual("collect_debrief_context", routed["next_action"])
            self.assertIsNone(routed["artifact"])

    def test_root_route_classifies_received_recruiter_messages_as_private_triage(self) -> None:
        cases = (
            ("I got a recruiter message and want to understand the role.", "en", True),
            ("I got a recruiter email and want to understand the role.", "en", True),
            ("Me llegó un mensaje del recruiter y quiero entender el rol.", "es", True),
            ("Me llegó un correo del recruiter y quiero entender la vacante.", "es", True),
        )
        for request, locale, authorization_required in cases:
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertIsNone(routed["artifact"])
                self.assertEqual(authorization_required, routed["authorization_required"])

        ordinary = route_recruiter_request("I got a message and want to understand the role.", locale="en", as_of_date="2026-08-28")
        self.assertEqual("ordinary_professional_growth", ordinary["route_kind"])

    def test_fallback_recruiter_action_synonyms_preserve_authorization_requirement(self) -> None:
        for request in (
            "Can you write back to the recruiter?",
            "Ping the recruiter about my application.",
            "DM the recruiter about the role.",
            "Contéstale al reclutador.",
            "Respóndele al recruiter.",
            "Escríbele al recruiter.",
            "Quiero escribirle al recruiter.",
            "Envíale un correo al reclutador.",
        ):
            routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_recognizes_common_invitation_and_booking_language(self) -> None:
        cases = (
            ("I got invited to interview with the recruiter; help me prepare.", False),
            ("I received an invitation to interview with a recruiter; help me prepare.", False),
            ("I was asked to interview with a recruiter; help me prepare.", False),
            ("I have a pending recruiter screen; help me prepare.", False),
            ("The recruiter invited me to interview; help me prepare.", False),
            ("I am scheduled to speak with the recruiter tomorrow; help me prepare.", True),
            ("I have a recruiter screen booked for Friday; help me prepare.", False),
            ("Tengo una entrevista con un recruiter la próxima semana; ayúdame a prepararme.", False),
        )
        for request, requires_authorization in cases:
            locale = "es" if request.startswith("Tengo") else "en"
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("recruiter_target_screen_intake", routed["route_kind"])
                self.assertEqual("collect_screen_intake", routed["next_action"])
                self.assertEqual(requires_authorization, routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_organizational_recruiter_alias_invitations_enter_screen_intake(self) -> None:
        cases = (
            ("I received a talent acquisition interview invitation; help me prepare.", "en"),
            ("Recruiting invited me to a call; help me prepare.", "en"),
            ("A sourcer invited me to a recruiter screen; help me prepare.", "en"),
        )
        for request, locale in cases:
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual("recruiter_target_screen_intake", routed["route_kind"])
                self.assertEqual("collect_screen_intake", routed["next_action"])
                self.assertFalse(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_organizational_recruiter_alias_invitation_action_enters_private_triage(self) -> None:
        routed = route_recruiter_request(
            "Recruiting invited me to a call; please confirm it.",
            locale="en",
            as_of_date="2026-08-28",
        )
        self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
        self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
        self.assertTrue(routed["authorization_required"])
        self.assertIsNone(routed["artifact"])

    def test_technical_interview_invitation_without_recruiter_context_stays_ordinary(self) -> None:
        routed = route_recruiter_request(
            "I received a technical interview invitation",
            locale="en",
            as_of_date="2026-08-28",
        )
        self.assertEqual("ordinary_professional_growth", routed["route_kind"])
        self.assertEqual("continue_normal_routing", routed["next_action"])
        self.assertFalse(routed["authorization_required"])
        self.assertIsNone(routed["artifact"])

    def test_recruiter_screen_invitation_word_order_enters_screen_intake(self) -> None:
        for request in (
            "I received a recruiter screen invitation",
            "A recruiter invited me to a screen",
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-28")
                self.assertEqual("recruiter_target_screen_intake", routed["route_kind"])
                self.assertEqual("collect_screen_intake", routed["next_action"])
                self.assertFalse(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_recruiter_requested_confirmation_or_acceptance_enters_private_triage(self) -> None:
        for request in (
            "Recruiter asked me to confirm the interview",
            "The recruiter wants me to accept the interview",
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_spanish_recruiter_requested_confirmation_or_acceptance_enters_private_triage(self) -> None:
        for request in (
            "El reclutador me pidió confirmar la entrevista",
            "La reclutadora quiere que acepte la entrevista",
            "Reclutamiento me pidió confirmar la entrevista",
            "La adquisición de talento me pidió confirmar la entrevista",
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_technical_confirmation_without_recruiter_actor_stays_ordinary(self) -> None:
        routed = route_recruiter_request(
            "I want to confirm my technical interview",
            locale="en",
            as_of_date="2026-08-28",
        )
        self.assertEqual("ordinary_professional_growth", routed["route_kind"])
        self.assertEqual("continue_normal_routing", routed["next_action"])
        self.assertTrue(routed["authorization_required"])
        self.assertIsNone(routed["artifact"])

    def test_passive_recruiter_cancellation_enters_screen_intake(self) -> None:
        for request in (
            "The recruiter screen was canceled",
            "The recruiter screen got canceled",
            "I canceled my recruiter screen",
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-28")
                self.assertEqual("recruiter_target_screen_intake", routed["route_kind"])
                self.assertEqual("collect_screen_intake", routed["next_action"])
                self.assertFalse(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_passive_recruiter_rejection_enters_private_debrief(self) -> None:
        routed = route_recruiter_request(
            "I was not selected after the recruiter screen",
            locale="en",
            as_of_date="2026-08-28",
        )
        self.assertEqual("private_recruiter_screen_debrief", routed["route_kind"])
        self.assertEqual("collect_debrief_context", routed["next_action"])
        self.assertFalse(routed["authorization_required"])
        self.assertIsNone(routed["artifact"])

    def test_passive_spanish_recruiter_rejections_enter_private_debrief(self) -> None:
        for request in (
            "No fui seleccionado después de la entrevista con el reclutador",
            "El reclutador eligió a otra persona después de la entrevista",
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_screen_debrief", routed["route_kind"])
                self.assertEqual("collect_debrief_context", routed["next_action"])
                self.assertFalse(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_passive_spanish_recruiter_cancellation_enters_screen_intake(self) -> None:
        routed = route_recruiter_request(
            "La entrevista con el reclutador fue cancelada",
            locale="es",
            as_of_date="2026-08-28",
        )
        self.assertEqual("recruiter_target_screen_intake", routed["route_kind"])
        self.assertEqual("collect_screen_intake", routed["next_action"])
        self.assertFalse(routed["authorization_required"])
        self.assertIsNone(routed["artifact"])

    def test_passive_spanish_recruiter_rescheduling_enters_screen_intake(self) -> None:
        for request in (
            "La entrevista con el reclutador fue reprogramada",
            "La entrevista con el reclutador se reprogramó",
            "La entrevista con reclutamiento fue reprogramada",
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-28")
                self.assertEqual("recruiter_target_screen_intake", routed["route_kind"])
                self.assertEqual("collect_screen_intake", routed["next_action"])
                self.assertFalse(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_passive_spanish_technical_outcomes_stay_ordinary(self) -> None:
        for request in (
            "No fui seleccionado después de la entrevista técnica",
            "La entrevista técnica fue cancelada",
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-28")
                self.assertEqual("ordinary_professional_growth", routed["route_kind"])
                self.assertEqual("continue_normal_routing", routed["next_action"])
                self.assertFalse(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_passive_technical_rejection_without_recruiter_actor_stays_ordinary(self) -> None:
        routed = route_recruiter_request(
            "I was not selected for a technical interview",
            locale="en",
            as_of_date="2026-08-28",
        )
        self.assertEqual("ordinary_professional_growth", routed["route_kind"])
        self.assertEqual("continue_normal_routing", routed["next_action"])
        self.assertFalse(routed["authorization_required"])
        self.assertIsNone(routed["artifact"])

    def test_invitation_with_reply_or_accept_request_enters_private_triage_boundary(self) -> None:
        for request, locale in (
            ("I was invited to a recruiter screen; can you help me respond?", "en"),
            ("I received an invitation to interview with the recruiter; please confirm it.", "en"),
            ("Me invitaron a una entrevista con el reclutador; ayúdame a contestar.", "es"),
            ("Tengo un filtro pendiente con la reclutadora; quiero aceptar.", "es"),
        ):
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("optimize-professional-profile", routed["selected_module"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])
                self.assertNotRegex(routed["intake_question"], r"(?:T-\d{3}|D-\d{3}|F-\d{3}|https?://)")

    def test_follow_up_action_wording_preserves_authorization_requirement(self) -> None:
        for request in (
            "Follow up with the recruiter about my application.",
            "Can you send a follow-up to the recruiter?",
            "Quiero dar seguimiento al reclutador.",
            "Mándale un seguimiento al recruiter.",
        ):
            routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_inbound_recruiter_contact_without_interview_language_enters_private_triage(self) -> None:
        cases = (
            ("A recruiter messaged me about a role; help me reply.", "en"),
            ("A recruiter emailed me about a role; help me answer.", "en"),
            ("A recruiter reached out on LinkedIn; what should I say back?", "en"),
            ("The recruiter asked about my availability; what should I say?", "en"),
            ("Could you help me formulate a response to the recruiter?", "en"),
            ("Me escribió un reclutador sobre una vacante; ayúdame a contestar.", "es"),
            ("La reclutadora me contactó por LinkedIn; ¿qué le digo?", "es"),
            ("Me preguntó el reclutador por mi disponibilidad.", "es"),
        )
        for request, locale in cases:
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_additional_calendar_and_availability_contact_language_enters_private_triage(self) -> None:
        cases = (
            ("The recruiter sent me a calendar link", "en"),
            ("The recruiter sent over some times for a call", "en"),
            ("The recruiter asked me when I am free", "en"),
            ("I need to tell the recruiter my availability", "en"),
            ("What do I tell the recruiter?", "en"),
            ("Help me respond to recruiter about the role", "en"),
            ("Me llegó correo de un reclutador", "es"),
            ("El reclutador quiere agendar una llamada", "es"),
            ("La reclutadora me envió un enlace de calendario", "es"),
        )
        for request, locale in cases:
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_organizational_recruiter_alias_calendar_language_enters_private_triage(self) -> None:
        cases = (
            ("Recruiting asked me to schedule a call", "en"),
            ("Talent acquisition asked me to choose a time", "en"),
            ("A sourcer sent me a calendar link", "en"),
            ("Reclutamiento me pidió elegir un horario", "es"),
        )
        for request, locale in cases:
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_organizational_recruiter_alias_contact_language_enters_private_triage(self) -> None:
        cases = (
            ("Talent acquisition contacted me about a role", "en"),
            ("A headhunter reached out about a role", "en"),
            ("Sourcers emailed me about a role", "en"),
            ("Reclutamiento me contactó sobre una vacante", "es"),
            ("La adquisición de talento me contactó sobre una vacante", "es"),
        )
        for request, locale in cases:
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_spanish_talent_acquisition_domain_language_stays_ordinary(self) -> None:
        routed = route_recruiter_request(
            "La adquisición de talento de la empresa necesita rediseño",
            locale="es",
            as_of_date="2026-08-28",
        )
        self.assertEqual("ordinary_professional_growth", routed["route_kind"])
        self.assertEqual("continue_normal_routing", routed["next_action"])
        self.assertFalse(routed["authorization_required"])
        self.assertIsNone(routed["artifact"])

    def test_passive_organizational_recruiter_contact_enters_private_triage(self) -> None:
        cases = (
            ("I was contacted by talent acquisition about a role", "en"),
            ("I was emailed by a sourcer about a role", "en"),
            ("I was messaged by a headhunter about a role", "en"),
        )
        for request, locale in cases:
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_spanish_recruiter_alias_contact_order_enters_private_triage(self) -> None:
        cases = (
            "Me contactó un sourcer sobre una vacante",
            "Me llamó un sourcer sobre una vacante",
            "Fui contactado por un sourcer sobre una vacante",
            "Me contactó talent acquisition sobre una vacante",
        )
        for request in cases:
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_organizational_alias_system_language_stays_outside_inbound_triage(self) -> None:
        for request in (
            "Talent acquisition systems need redesign.",
            "Headhunter algorithm research is on the roadmap.",
            "I was contacted by an employer about a role.",
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-28")
                self.assertEqual("ordinary_professional_growth", routed["route_kind"])
                self.assertEqual("continue_normal_routing", routed["next_action"])
                self.assertFalse(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_technical_recruiting_alias_language_stays_outside_inbound_triage(self) -> None:
        routed = route_recruiter_request(
            "Our recruiting systems schedule technical interviews automatically.",
            locale="en",
            as_of_date="2026-08-28",
        )
        self.assertEqual("ordinary_professional_growth", routed["route_kind"])
        self.assertEqual("continue_normal_routing", routed["next_action"])
        self.assertIsNone(routed["artifact"])

    def test_post_screen_followthrough_language_enters_private_debrief(self) -> None:
        cases = (
            ("I want to follow up with the recruiter after the screen.", "en", True),
            ("How do I follow up after the recruiter interview?", "en", True),
            ("Can you draft a thank-you note after my recruiter screen?", "en", False),
            ("No response from recruiter after interview.", "en", False),
            ("I have been ghosted by the recruiter after the screen.", "en", False),
            ("¿Cómo doy seguimiento después de la entrevista con el reclutador?", "es", True),
            ("¿Debo mandar un agradecimiento después del filtro?", "es", True),
            ("Me dejaron en visto después de la entrevista con el reclutador.", "es", False),
        )
        for request, locale, authorization_required in cases:
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_screen_debrief", routed["route_kind"])
                self.assertEqual("collect_debrief_context", routed["next_action"])
                self.assertEqual(authorization_required, routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_post_screen_followthrough_preserves_reply_and_pre_screen_precedence(self) -> None:
        for request, locale, expected_route in (
            (
                "How should I respond to a recruiter after my interview?",
                "en",
                "private_recruiter_reply_triage",
            ),
            (
                "¿Cómo respondo al reclutador después de la entrevista?",
                "es",
                "private_recruiter_reply_triage",
            ),
            (
                "My recruiter screen is scheduled next week; should I follow up before it?",
                "en",
                "recruiter_target_screen_intake",
            ),
            (
                "I haven't had the recruiter screen yet; should I follow up?",
                "en",
                "recruiter_target_screen_intake",
            ),
            (
                "I want to follow up with the hiring manager after my interview.",
                "en",
                "ordinary_professional_growth",
            ),
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual(expected_route, routed["route_kind"])
                self.assertIsNone(routed["artifact"])

    def test_post_screen_no_reply_and_speaking_variants_keep_private_debrief(self) -> None:
        for request, locale, expected_route, authorization_required in (
            ("The recruiter has not replied after my screen.", "en", "private_recruiter_screen_debrief", False),
            ("The recruiter never replied after my interview.", "en", "private_recruiter_screen_debrief", False),
            ("El reclutador no respondió después de la entrevista.", "es", "private_recruiter_screen_debrief", False),
            ("After speaking to the recruiter, should I send a thank-you?", "en", "private_recruiter_screen_debrief", True),
            ("Después de hablar con el reclutador, debo enviar agradecimiento", "es", "private_recruiter_screen_debrief", True),
            ("Después de la llamada del recruiter, ¿qué le escribo?", "es", "private_recruiter_reply_triage", True),
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual(expected_route, routed["route_kind"])
                self.assertEqual(authorization_required, routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_negative_get_back_wording_keeps_post_screen_debrief_precedence(self) -> None:
        routed = route_recruiter_request(
            "The recruiter didn't get back to me after the screen.",
            locale="en",
            as_of_date="2026-08-27",
        )
        self.assertEqual("private_recruiter_screen_debrief", routed["route_kind"])
        self.assertEqual("collect_debrief_context", routed["next_action"])
        self.assertFalse(routed["authorization_required"])

    def test_additional_recruiter_schedule_and_received_message_language_enters_private_triage(self) -> None:
        for request, locale in (
            ("Recruiter asked me to book a slot.", "en"),
            ("Recruiter sent over some times for a call.", "en"),
            ("El recruiter me compartió horarios.", "es"),
            ("I received a recruiter email; what should I do?", "en"),
            ("I received a LinkedIn message from a recruiter.", "en"),
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_common_recruiter_contact_and_schedule_variants_enter_private_triage(self) -> None:
        for request, locale in (
            ("I got a message from a recruiter", "en"),
            ("A recruiter sent me a LinkedIn message", "en"),
            ("I received an email from the recruiter", "en"),
            ("Recruiter asked me to choose a slot", "en"),
            ("Recruiter asked to set up a call", "en"),
            ("Recruiter shared a few times", "en"),
            ("La reclutadora me envió horarios", "es"),
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_post_screen_conversation_and_interviewed_variants_preserve_precedence(self) -> None:
        for request, locale, expected_route, authorization_required in (
            ("Should I follow up after talking with the recruiter?", "en", "private_recruiter_screen_debrief", True),
            ("I spoke to recruiter and want to send a thank-you", "en", "private_recruiter_screen_debrief", True),
            ("Después de mi llamada con el recruiter no recibí respuesta", "es", "private_recruiter_screen_debrief", False),
            ("I interviewed with the recruiter and have not heard back", "en", "private_recruiter_screen_debrief", False),
            ("What comes after the recruiter call?", "en", "private_recruiter_next_stage_review", False),
            ("I passed my recruiter interview, what next?", "en", "private_recruiter_next_stage_review", False),
            ("I need to get ready for my recruiter phone screen", "en", "recruiter_target_screen_intake", False),
            ("I haven't had the recruiter phone screen yet", "en", "recruiter_target_screen_intake", False),
        ):
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual(expected_route, routed["route_kind"])
                self.assertEqual(authorization_required, routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_recruiter_preparation_without_inbound_contact_stays_preparation_only(self) -> None:
        routed = route_recruiter_request(
            "Help me prepare for a recruiter interview next week.",
            locale="en",
            as_of_date="2026-08-28",
        )
        self.assertEqual("recruiter_target_screen_intake", routed["route_kind"])
        self.assertFalse(routed["authorization_required"])

    def test_recruiter_schedule_and_reply_language_enters_private_triage(self) -> None:
        cases = (
            ("The recruiter wants to schedule a phone screen; what should I reply?", "en"),
            ("The recruiter asked me to choose a time for an interview.", "en"),
            ("I need to reply to a recruiter about interview availability.", "en"),
            ("El reclutador me pidió disponibilidad para una entrevista.", "es"),
            ("Me llegó una invitación del reclutador para agendar una llamada.", "es"),
        )
        for request, locale in cases:
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
                self.assertEqual("private_recruiter_reply_triage", routed["route_kind"])
                self.assertEqual("collect_recruiter_reply_triage_context", routed["next_action"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_keeps_readiness_negation_after_completed_screen_in_next_stage_flow(self) -> None:
        routed = route_recruiter_request(
            "I had a recruiter screen but I am not yet ready for the next stage.",
            locale="en",
            as_of_date="2026-08-27",
        )
        self.assertEqual("private_recruiter_next_stage_review", routed["route_kind"])
        self.assertEqual("prepare-role-interviews", routed["selected_module"])
        self.assertEqual("collect_debrief_context", routed["next_action"])
        self.assertFalse(routed["authorization_required"])
        self.assertIsNone(routed["artifact"])

    def test_root_route_recognizes_post_screen_progression_to_hiring_manager(self) -> None:
        for request in (
            "I passed the recruiter screen; prepare me for the hiring manager.",
            "I moved forward to the hiring manager interview after the recruiter screen.",
            "Ya pasé el filtro y ahora sigue la entrevista con el hiring manager.",
        ):
            routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual("private_recruiter_next_stage_review", routed["route_kind"])
                self.assertEqual("prepare-role-interviews", routed["selected_module"])
                self.assertEqual("collect_debrief_context", routed["next_action"])
                self.assertFalse(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_post_screen_progression_requires_completed_context_and_rejects_negation(self) -> None:
        for request in (
            "I advanced to the next round after a recruiter screen.",
            "The recruiter said I am progressing to the hiring manager stage.",
            "Avancé a la siguiente ronda después del filtro con el reclutador.",
        ):
            locale = "es" if request.startswith("Avancé") else "en"
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual("private_recruiter_next_stage_review", routed["route_kind"])
        for request, expected_route in (
            ("I haven't passed the recruiter screen yet; help me prepare.", "recruiter_target_screen_intake"),
            ("I did not clear the recruiter screen; help me prepare.", "recruiter_target_screen_intake"),
            ("I advanced to the hiring manager stage.", "ordinary_professional_growth"),
        ):
            routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-28")
            with self.subTest(request=request):
                self.assertEqual(expected_route, routed["route_kind"])

    def test_root_route_keeps_recruiter_network_and_generic_technical_interview_precedence(self) -> None:
        shortlist = route_recruiter_request("How do I network with recruiters?", locale="en", as_of_date="2026-08-27")
        ordinary = route_recruiter_request("Help me prepare for a technical interview.", locale="en", as_of_date="2026-08-27")
        self.assertEqual("recruiter_target_shortlist", shortlist["route_kind"])
        self.assertEqual("ordinary_professional_growth", ordinary["route_kind"])

    def test_common_preparation_followthrough_and_spanish_networking_variants_keep_route_precedence(self) -> None:
        cases = (
            ("I need to get ready for a recruiter phone screen.", "recruiter_target_screen_intake"),
            ("I am preparing for a recruiter interview.", "recruiter_target_screen_intake"),
            ("I talked with the recruiter and have not heard back.", "private_recruiter_screen_debrief"),
            ("What happens after talking to a recruiter?", "private_recruiter_next_stage_review"),
            ("¿Qué viene después de hablar con un reclutador?", "private_recruiter_next_stage_review"),
            ("Quiero hacer networking con reclutadores.", "recruiter_target_shortlist"),
        )
        for request, expected_route in cases:
            with self.subTest(request=request):
                routed = route_recruiter_request(request, locale="es", as_of_date="2026-08-28")
                self.assertEqual(expected_route, routed["route_kind"])
                self.assertIsNone(routed["artifact"])

    def test_natural_recruiter_debrief_action_request_preserves_authorization_boundary(self) -> None:
        routed = route_recruiter_request(
            "I completed a recruiter screen; send a follow-up and help me debrief.",
            locale="en",
            as_of_date="2026-08-27",
        )
        self.assertEqual("private_recruiter_screen_debrief", routed["route_kind"])
        self.assertTrue(routed["authorization_required"])
        self.assertIsNone(routed["artifact"])

    def test_natural_recruiter_contact_requests_preserve_authorization_boundary(self) -> None:
        for request in (
            "Help me reach out to recruiters",
            "Quiero contactar a un recruiter para hablar de oportunidades",
        ):
            routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("recruiter_target_shortlist", routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_fallback_recruiter_action_requests_never_drop_authorization_requirement(self) -> None:
        for request in (
            "I want to send a message to the recruiter after the screen",
            "Please schedule an interview with the recruiter",
            "Quiero enviar mensaje al reclutador después del filtro",
            "Quiero agendar una entrevista con el reclutador",
            "Can you respond to the recruiter?",
            "Email the recruiter.",
            "¿Puedes contestar al reclutador?",
            "Mándale un correo al reclutador.",
        ):
            routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertTrue(routed["authorization_required"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_rejects_non_sequence_targets_without_uncaught_errors(self) -> None:
        for invalid in (1, object(), iter(()), "abc"):
            with self.subTest(invalid_type=type(invalid).__name__):
                routed = route_recruiter_request(
                    "Quiero buscar recruiters.",
                    locale="es",
                    as_of_date="2026-08-27",
                    network_plan=valid_plan(),
                    targets=invalid,
                )
                self.assertEqual("recruiter_target_shortlist", routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertEqual("ask_one_intake_question", routed["next_action"])
                self.assertIsNone(routed["artifact"])

    def test_root_route_rejects_recursively_nested_plan_without_traceback(self) -> None:
        nested: dict[str, object] = {}
        for _ in range(500):
            nested = {"nested": nested}
        plan = valid_plan()
        plan["nested"] = nested
        routed = route_recruiter_request(
            "Necesito prepararme para mi primera entrevista con un reclutador.",
            locale="es",
            as_of_date="2026-08-27",
            network_plan=plan,
            targets=valid_targets(),
        )
        self.assertEqual("recruiter_target_shortlist", routed["route_kind"])
        self.assertEqual("needs_intake", routed["case_state"])
        self.assertIsNone(routed["artifact"])

    def test_renderer_rejects_symlinked_output_parent(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        with tempfile.TemporaryDirectory() as directory:
            real_parent = Path(directory) / "real"
            real_parent.mkdir()
            link_parent = Path(directory) / "link"
            link_parent.symlink_to(real_parent, target_is_directory=True)
            with self.assertRaises(OSError):
                write_shortlist_html(value, link_parent / "artifact.html")
            self.assertFalse((real_parent / "artifact.html").exists())

    def test_renderer_cli_rejects_oversized_and_duplicate_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            oversized = Path(directory) / "oversized.json"
            oversized.write_text("{" + "\"x\":\"" + ("a" * 70_000) + "\"}", encoding="utf-8")
            self.assertEqual(3, render_cli([str(oversized), str(Path(directory) / "out.html")]))
            duplicate = Path(directory) / "duplicate.json"
            duplicate.write_text('{"locale":"en","locale":"es"}', encoding="utf-8")
            self.assertEqual(3, render_cli([str(duplicate), str(Path(directory) / "duplicate.html")]))

    def test_shortlist_clis_keep_invalid_argument_values_out_of_stderr(self) -> None:
        build = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "build_recruiter_target_shortlist.py"), "--PRIVATE-SENTINEL"],
            capture_output=True,
            text=True,
        )
        render = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "render_recruiter_target_shortlist.py"), "--PRIVATE-SENTINEL"],
            capture_output=True,
            text=True,
        )
        for result in (build, render):
            self.assertEqual(3, result.returncode)
            self.assertEqual('{"error":{"code":"invalid_arguments"}}\n', result.stderr)
            self.assertEqual("", result.stdout)
            self.assertNotIn("PRIVATE-SENTINEL", result.stderr)

    def test_validator_rejects_non_http_uri_schemes_in_private_prose(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        for uri in ("file:///private/notes", "ssh://internal/role", "javascript:alert(1)"):
            value["targets"][0]["context_source"] = uri
            errors = validate_shortlist(value, as_of=date(2026, 8, 27))
            with self.subTest(uri=uri):
                self.assertIn("targets[0].context_source contains restricted material", errors)

    def test_renderer_rejects_future_date_even_when_called_directly(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        value["as_of_date"] = "2999-01-01"
        with self.assertRaises(ValueError):
            render_shortlist_html(value)

    def test_builder_writer_rejects_symlinked_output_parent(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            victim = root / "victim"
            victim.mkdir()
            alias = root / "alias"
            alias.symlink_to(victim, target_is_directory=True)
            with self.assertRaises(OSError):
                _write_private_json(alias / "artifact.json", value)
            self.assertFalse((victim / "artifact.json").exists())

    def test_renderer_rejects_symlinked_template_asset(self) -> None:
        import render_recruiter_target_shortlist as renderer

        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        with tempfile.TemporaryDirectory() as directory:
            external = Path(directory) / "external.html"
            external.write_text("<script>external</script>", encoding="utf-8")
            original = renderer.TEMPLATE_PATH
            renderer.TEMPLATE_PATH = Path(directory) / "template.html"
            renderer.TEMPLATE_PATH.symlink_to(external)
            try:
                with self.assertRaises((OSError, ValueError)):
                    render_shortlist_html(value)
            finally:
                renderer.TEMPLATE_PATH = original
