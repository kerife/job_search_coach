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
from render_recruiter_target_shortlist import _cli as render_cli, render_shortlist_html, write_shortlist_html  # noqa: E402
from validate_recruiter_target_shortlist import validate_shortlist  # noqa: E402


from route_recruiter_target_shortlist import route_recruiter_request  # noqa: E402


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
        for value in ("Call me at +52 55 1234 5678", "bearer abcdefghijklmnopqrstuvwxyz123456", "/tmp/candidate.txt"):
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

    def test_validator_rejects_restricted_or_unbounded_target_segments(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        value["network_plan"]["target_segments"] = ["https://private.example/profile"]
        errors = validate_shortlist(value, as_of=dt.date(2026, 8, 27))
        self.assertIn("network_plan.target_segments[0] contains restricted material", errors)

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
        self.assertEqual(1, rendered.count('aria-current="step"'))
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
            "Necesito prepararme para una entrevista con un reclutador",
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
        ):
            routed = route_recruiter_request(request, locale="en", as_of_date="2026-08-28")
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
