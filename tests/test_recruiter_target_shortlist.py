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

    def test_validator_rejects_restricted_or_unbounded_target_segments(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        value["network_plan"]["target_segments"] = ["https://private.example/profile"]
        errors = validate_shortlist(value, as_of=dt.date(2026, 8, 27))
        self.assertIn("network_plan.target_segments[0] contains restricted material", errors)

    def test_builder_rejects_future_as_of_date(self) -> None:
        with self.assertRaises(ValueError):
            build_shortlist("en", "2999-01-01", valid_plan(), valid_targets())

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
        self.assertIn("Paso actual", rendered)
        css = (ROOT / "plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.css").read_text(encoding="utf-8")
        self.assertIn(":focus-visible", css)
        self.assertIn("@media (prefers-contrast: more)", css)
        self.assertIn("@media (forced-colors: active)", css)

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
            "Necesito prepararme para mi primera entrevista con un reclutador.",
            "Quiero hacer networking con recruiters.",
            "Quiero ampliar mi red profesional con reclutadores.",
        ):
            locale = "es" if request.startswith("Quiero") else "en"
            routed = route_recruiter_request(request, locale=locale, as_of_date="2026-08-27")
            with self.subTest(request=request):
                self.assertEqual("recruiter_target_shortlist", routed["route_kind"])
                self.assertEqual("needs_intake", routed["case_state"])
                self.assertEqual("ask_one_intake_question", routed["next_action"])

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
