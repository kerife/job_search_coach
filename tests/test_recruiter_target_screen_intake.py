"""Contracts for the target-specific recruiter screen intake bridge."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_recruiter_target_decision_gate import build_decision_gate  # noqa: E402
from build_recruiter_target_screen_intake import build_screen_intake  # noqa: E402
from build_recruiter_target_shortlist import build_shortlist  # noqa: E402
from render_recruiter_target_screen_intake import render_screen_intake_html  # noqa: E402
from route_recruiter_target_shortlist import route_recruiter_decision_gate, route_recruiter_screen_intake  # noqa: E402
from validate_recruiter_target_screen_intake import validate_screen_intake  # noqa: E402

from tests.test_recruiter_target_shortlist import valid_plan, valid_targets  # noqa: E402
from tests.test_recruiter_target_decision_gate import RecruiterTargetDecisionGateTests  # noqa: E402


def valid_screen_intake() -> dict[str, object]:
    return {
        "stated_stage": "recruiter_screen",
        "vacancy_requirements": [
            "V-001: Platform reliability ownership and incident response scope.",
            "V-002: Evidence-backed delivery expectation for the role.",
        ],
        "candidate_fact_ids": ["F-001"],
        "company_evidence_state": "verified",
        "source_date": "2026-08-27",
        "checks": [
            {"check": "target_context", "status": "pass", "evidence_note": "Named platform specialty is supplied."},
            {"check": "proof_packet", "status": "pass", "evidence_note": "Two candidate facts are mapped."},
            {"check": "low_friction_ask", "status": "pass", "evidence_note": "The first question asks for process context only."},
            {"check": "screen_readiness", "status": "pass", "evidence_note": "The recruiter-screen stage is explicit."},
        ],
    }


class RecruiterTargetScreenIntakeTests(unittest.TestCase):
    def gate(self) -> dict[str, object]:
        shortlist = RecruiterTargetDecisionGateTests().shortlist()
        return build_decision_gate(shortlist)

    def test_builder_requires_advance_target_and_four_passing_checks_for_manual_handoff(self) -> None:
        intake = build_screen_intake(self.gate(), "T-001", valid_screen_intake())
        self.assertEqual([], validate_screen_intake(intake, as_of=date(2026, 8, 27)))
        self.assertEqual("ready", intake["readiness_decision"])
        self.assertEqual("manual_prepare_role_interviews_review", intake["handoff"]["next_safe_action"])
        self.assertEqual("screen_context_submitted", intake["measurement_event"])
        self.assertFalse(intake["delivery"]["external_actions_authorized"])

    def test_non_advance_target_can_never_prepare(self) -> None:
        context = valid_screen_intake()
        context["candidate_fact_ids"] = ["F-002"]
        intake = build_screen_intake(self.gate(), "T-002", context)
        self.assertEqual("clarify_first", intake["readiness_decision"])
        self.assertEqual("collect_screen_intake", intake["handoff"]["next_safe_action"])
        self.assertEqual([], validate_screen_intake(intake, source_gate=self.gate(), as_of=date(2026, 8, 27)))

    def test_missing_or_unclear_context_stays_in_intake(self) -> None:
        context = valid_screen_intake()
        context["checks"][2]["status"] = "clarify"
        intake = build_screen_intake(self.gate(), "T-001", context)
        self.assertEqual("clarify_first", intake["readiness_decision"])
        self.assertEqual("collect_screen_intake", intake["handoff"]["next_safe_action"])
        self.assertEqual("clarify_context", intake["measurement_event"])

    def test_snapshot_and_target_mutation_are_rejected(self) -> None:
        intake = build_screen_intake(self.gate(), "T-001", valid_screen_intake())
        tampered = copy.deepcopy(intake)
        tampered["source_gate_snapshot"] = "snap-shortlist-sha256-" + "0" * 64
        self.assertIn("source_gate_snapshot does not match source gate", validate_screen_intake(tampered, source_gate=self.gate()))
        tampered = copy.deepcopy(intake)
        tampered["target_decision"] = "stop"
        self.assertIn("target_decision does not match source gate", validate_screen_intake(tampered, source_gate=self.gate()))
        tampered = copy.deepcopy(intake)
        tampered["source_gate"]["locale"] = "en"
        self.assertIn("embedded source gate does not match source gate", validate_screen_intake(tampered, source_gate=self.gate()))
        tampered = copy.deepcopy(intake)
        tampered["source_gate"]["decision_rows"][0]["decision_reason"] = "mutated"
        self.assertIn("embedded source gate does not match source gate", validate_screen_intake(tampered, source_gate=self.gate()))
        tampered = copy.deepcopy(intake)
        tampered["locale"] = "en"
        self.assertIn("locale does not match source gate", validate_screen_intake(tampered))

    def test_malformed_json_types_fail_closed_with_errors(self) -> None:
        intake = build_screen_intake(self.gate(), "T-001", valid_screen_intake())
        malformed = copy.deepcopy(intake)
        malformed["target_decision"] = []
        malformed["intake"]["candidate_fact_ids"] = [{}]
        malformed["checks"][0]["check"] = {}
        malformed["checks"][1]["status"] = []
        errors = validate_screen_intake(malformed)
        self.assertTrue(errors)
        self.assertTrue(all(isinstance(error, str) for error in errors))

    def test_forged_artifact_without_embedded_gate_or_with_uri_is_rejected(self) -> None:
        intake = build_screen_intake(self.gate(), "T-001", valid_screen_intake())
        forged = copy.deepcopy(intake)
        del forged["source_gate"]
        self.assertIn("source_gate must be an object", validate_screen_intake(forged))
        unsafe = valid_screen_intake()
        unsafe["vacancy_requirements"][0] = "V-001: https://example.invalid/role"
        with self.assertRaises(ValueError):
            build_screen_intake(self.gate(), "T-001", unsafe)

    def test_cli_unknown_arguments_return_opaque_error(self) -> None:
        from validate_recruiter_target_screen_intake import _cli

        self.assertEqual(3, _cli(["--private-secret-value"]))

    def test_renderer_is_bilingual_and_hides_internal_ids(self) -> None:
        intake = build_screen_intake(self.gate(), "T-001", valid_screen_intake())
        rendered = render_screen_intake_html(intake)
        self.assertIn("Preparar entrevista para revisión", rendered)
        self.assertNotIn("T-001", rendered)
        self.assertNotIn("F-001", rendered)
        english_gate = build_decision_gate(build_shortlist("en", "2026-08-27", valid_plan(), valid_targets()))
        english = build_screen_intake(english_gate, "T-001", valid_screen_intake())
        self.assertIn("Prepare interview for review", render_screen_intake_html(english))

    def test_renderer_localizes_internal_checks_company_state_and_stage(self) -> None:
        stages = {
            "recruiter_screen": ("Filtro con reclutador", "Recruiter screen"),
            "first_interview": ("Primera entrevista", "First interview"),
            "technical_screen": ("Filtro técnico", "Technical screen"),
            "hiring_manager": ("Entrevista con hiring manager", "Hiring manager interview"),
            "technical_deep_dive": ("Profundización técnica", "Technical deep dive"),
            "take_home": ("Ejercicio para casa", "Take-home exercise"),
            "system_design": ("Diseño de sistemas", "System design"),
            "behavioral_loop": ("Ronda conductual", "Behavioral loop"),
            "panel": ("Panel de entrevistas", "Interview panel"),
            "offer_stage": ("Etapa de oferta", "Offer stage"),
        }
        internal_tokens = ("target_context", "proof_packet", "low_friction_ask", "screen_readiness", "verified")
        for stage, (spanish_label, english_label) in stages.items():
            context = valid_screen_intake()
            context["stated_stage"] = stage
            rendered = render_screen_intake_html(build_screen_intake(self.gate(), "T-001", context))
            self.assertIn(spanish_label, rendered)
            self.assertNotIn(f">{stage}<", rendered)
            for token in internal_tokens:
                self.assertNotIn(f">{token}<", rendered)

            english_gate = build_decision_gate(build_shortlist("en", "2026-08-27", valid_plan(), valid_targets()))
            english = dict(context)
            english_rendered = render_screen_intake_html(build_screen_intake(english_gate, "T-001", english))
            self.assertIn(english_label, english_rendered)
            self.assertNotIn(f">{stage}<", english_rendered)

    def test_route_returns_manual_or_blocked_state_only(self) -> None:
        ready = route_recruiter_screen_intake(self.gate(), "T-001", valid_screen_intake())
        self.assertEqual("ready", ready["case_state"])
        self.assertEqual("manual_prepare_role_interviews_review", ready["next_action"])
        self.assertIn("Preparar entrevista para revisión", ready["rendered_html"])
        self.assertNotIn("T-001", ready["rendered_html"])
        self.assertNotIn("F-001", ready["rendered_html"])
        blocked = route_recruiter_screen_intake(self.gate(), "T-002", valid_screen_intake())
        self.assertEqual("needs_intake", blocked["case_state"])
        self.assertEqual("collect_screen_intake", blocked["next_action"])
        self.assertIsNone(blocked["artifact"])
        self.assertNotIn("rendered_html", blocked)

    def test_legacy_gate_route_cannot_bypass_target_specific_intake(self) -> None:
        shortlist = RecruiterTargetDecisionGateTests().shortlist()
        routed = route_recruiter_decision_gate(
            shortlist,
            screen_context={
                "vacancy_summary": "Platform reliability screen",
                "confirmed_fact_summary": "Incident response evidence",
            },
        )
        self.assertEqual("needs_intake", routed["case_state"])
        self.assertEqual("collect_screen_intake", routed["next_action"])
        self.assertIsNone(routed["artifact"])


if __name__ == "__main__":
    unittest.main()
