"""Contracts for the private post-screen debrief bridge."""

from __future__ import annotations

import copy
import json
import re
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_recruiter_target_decision_gate import build_decision_gate  # noqa: E402
from build_recruiter_target_shortlist import build_shortlist  # noqa: E402
from build_recruiter_target_screen_intake import build_screen_intake  # noqa: E402
from build_private_recruiter_screen_debrief import build_screen_debrief  # noqa: E402
from render_private_recruiter_screen_debrief import render_screen_debrief_html  # noqa: E402
from route_recruiter_target_shortlist import route_recruiter_screen_debrief, route_recruiter_screen_debrief_intake  # noqa: E402
from validate_private_recruiter_screen_debrief import validate_screen_debrief  # noqa: E402
from validate_recruiter_target_screen_intake import validate_screen_intake  # noqa: E402
from tests.test_recruiter_target_decision_gate import RecruiterTargetDecisionGateTests  # noqa: E402
from tests.test_recruiter_target_shortlist import valid_plan, valid_targets  # noqa: E402
from tests.test_recruiter_target_screen_intake import valid_screen_intake  # noqa: E402


RECEIPT = json.loads(
    (ROOT / "plugins/professional-growth-coach/tests/fixtures/private-recruiter-conversion-outcome/screen-requested-en.json").read_text(encoding="utf-8")
)


def valid_checkpoint() -> dict[str, object]:
    return {
        "schema_version": "private-recruiter-followthrough-checkpoint-v1",
        "artifact_kind": "private_recruiter_followthrough_checkpoint",
        "locale": "en",
        "source_receipt": {"id": "D-104", "source_version": "draft-v1", "event_type": "screen_requested"},
        "target_binding": {
            "target_id": "T-001",
            "source_gate_snapshot": "snap-shortlist-sha256-17d0733532d3e2a724bf38ba60a6cf9dbade133d71e8923e7dffce1e24a734f7",
        },
        "action_state": "completed",
        "observed_date": "2026-08-27",
        "next_measurement_event": "screen_attended",
        "next_safe_action": "debrief_after_screen",
        "delivery": {
            "draft_only": True,
            "external_actions_authorized": False,
            "no_message_action": True,
            "no_calendar_action": True,
            "raw_event_retained": False,
            "local_save_mode": "disabled",
        },
    }


def valid_debrief() -> dict[str, object]:
    return {
        "observed_date": "2026-08-27",
        "coverage": [
            {"topic": "requirement", "status": "discussed", "note": "Role scope was discussed."},
            {"topic": "scope", "status": "discussed", "note": "Success expectations were discussed."},
            {"topic": "team_context", "status": "discussed", "note": "Team context was discussed."},
        ],
        "unknown_topics": [],
        "facts_used": ["F-001"],
        "decision": "continue_review",
    }


class PrivateRecruiterScreenDebriefTests(unittest.TestCase):
    def setUp(self) -> None:
        shortlist = RecruiterTargetDecisionGateTests().shortlist()
        self.gate = build_decision_gate(shortlist)
        self.intake = build_screen_intake(self.gate, "T-001", valid_screen_intake())

    def test_high_contrast_styles_reinforce_cards_and_coverage_boundaries(self) -> None:
        for filename, selectors in (
            ("recruiter-target-screen-intake-v1.css", (".screen-card", ".screen-check")),
            ("private-recruiter-screen-debrief-v1.css", (".debrief-card", ".debrief-coverage")),
        ):
            css = (ROOT / "plugins/professional-growth-coach/assets" / filename).read_text(encoding="utf-8")
            match = re.search(r"@media\s*\(prefers-contrast\s*:\s*more\s*\)", css)
            self.assertIsNotNone(match)
            block = css[match.end():].split("@media", 1)[0]
            with self.subTest(filename=filename):
                for selector in selectors:
                    self.assertIn(selector, block)
                self.assertRegex(block, r"border-width\s*:\s*2px")
                self.assertRegex(block, r"border-left-width\s*:\s*\.5rem")

    def test_attended_screen_starts_artifact_free_debrief_intake(self) -> None:
        receipt = copy.deepcopy(RECEIPT)
        receipt["locale"] = self.intake["locale"]
        checkpoint = valid_checkpoint()
        checkpoint["locale"] = self.intake["locale"]
        routed = route_recruiter_screen_debrief_intake(checkpoint, receipt, self.intake)
        self.assertEqual("private_recruiter_screen_debrief", routed["route_kind"])
        self.assertEqual("needs_intake", routed["case_state"])
        self.assertEqual("collect_debrief_context", routed["next_action"])
        self.assertFalse(routed["authorization_required"])
        self.assertIsNone(routed["artifact"])
        self.assertEqual(["structured_debrief_context"], routed["evidence_gaps"])
        self.assertIn("Filtro atendido", routed["intake_question"])
        self.assertNotRegex(routed["intake_question"], r"(?:T-\\d{3}|D-\\d{3}|F-\\d{3}|https?://)")

    def test_validator_rejects_future_evaluation_date(self) -> None:
        artifact = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, valid_debrief())
        self.assertIn(
            "as_of cannot be in the future",
            validate_screen_debrief(artifact, RECEIPT, self.intake, as_of=date.today() + timedelta(days=1)),
        )

    def test_debrief_intake_recovery_is_specific_and_artifact_free(self) -> None:
        for checkpoint, receipt, intake in (
            ({}, RECEIPT, self.intake),
            (valid_checkpoint(), {}, self.intake),
            (valid_checkpoint(), RECEIPT, {}),
        ):
            with self.subTest(input=(checkpoint, receipt, intake)):
                routed = route_recruiter_screen_debrief_intake(checkpoint, receipt, intake)
                self.assertEqual("collect_debrief_context", routed["next_action"])
                self.assertIsNone(routed["artifact"])
                self.assertNotIn("recruiter_target_shortlist", routed["intake_question"])

    def test_debrief_intake_rejects_locale_or_stage_drift(self) -> None:
        mismatched_checkpoint = valid_checkpoint()
        mismatched_checkpoint["locale"] = "es"
        self.assertIsNone(route_recruiter_screen_debrief_intake(mismatched_checkpoint, RECEIPT, self.intake)["artifact"])
        mismatched_intake = copy.deepcopy(self.intake)
        mismatched_intake["intake"]["stated_stage"] = "technical_screen"
        self.assertIsNone(route_recruiter_screen_debrief_intake(valid_checkpoint(), RECEIPT, mismatched_intake)["artifact"])
        mixed_locale = copy.deepcopy(self.intake)
        mixed_locale["locale"] = "es"
        self.assertEqual(
            ["validated_screen_checkpoint_receipt_intake"],
            route_recruiter_screen_debrief_intake(valid_checkpoint(), RECEIPT, mixed_locale)["evidence_gaps"],
        )

    def test_debrief_intake_accepts_matching_target_binding(self) -> None:
        receipt = copy.deepcopy(RECEIPT)
        receipt["locale"] = self.intake["locale"]
        checkpoint = valid_checkpoint()
        checkpoint["locale"] = self.intake["locale"]
        checkpoint["target_binding"] = {
            "target_id": self.intake["target_id"],
            "source_gate_snapshot": self.intake["source_gate_snapshot"],
        }
        routed = route_recruiter_screen_debrief_intake(checkpoint, receipt, self.intake)
        self.assertEqual(["structured_debrief_context"], routed["evidence_gaps"])
        mismatched = copy.deepcopy(checkpoint)
        mismatched["target_binding"]["target_id"] = "T-002"
        self.assertEqual(
            ["validated_screen_checkpoint_receipt_intake"],
            route_recruiter_screen_debrief_intake(mismatched, receipt, self.intake)["evidence_gaps"],
        )
        legacy = copy.deepcopy(checkpoint)
        del legacy["target_binding"]
        self.assertEqual(
            ["validated_screen_checkpoint_receipt_intake"],
            route_recruiter_screen_debrief_intake(legacy, receipt, self.intake)["evidence_gaps"],
        )

    def test_debrief_builder_rejects_target_binding_drift(self) -> None:
        receipt = copy.deepcopy(RECEIPT)
        receipt["locale"] = self.intake["locale"]
        checkpoint = valid_checkpoint()
        checkpoint["locale"] = self.intake["locale"]
        checkpoint["target_binding"]["target_id"] = "T-002"
        with self.assertRaises(ValueError):
            build_screen_debrief(checkpoint, receipt, self.intake, valid_debrief())

    def test_interview_requested_debrief_intake_preserves_event_context(self) -> None:
        receipt = copy.deepcopy(RECEIPT)
        receipt["event_type"] = "interview_requested"
        receipt["next_safe_action"] = "route_to_prepare-role-interviews"
        checkpoint = valid_checkpoint()
        checkpoint["source_receipt"]["event_type"] = "interview_requested"
        receipt["locale"] = self.intake["locale"]
        checkpoint["locale"] = self.intake["locale"]
        routed = route_recruiter_screen_debrief_intake(checkpoint, receipt, self.intake)
        self.assertEqual("collect_debrief_context", routed["next_action"])
        self.assertIsNone(routed["artifact"])
        self.assertIn("Entrevista registrada", routed["intake_question"])
        english_gate = build_decision_gate(build_shortlist("en", "2026-08-27", valid_plan(), valid_targets()))
        english_intake = build_screen_intake(english_gate, "T-001", valid_screen_intake())
        english_checkpoint = valid_checkpoint()
        english_checkpoint["source_receipt"]["event_type"] = "interview_requested"
        english = route_recruiter_screen_debrief_intake(english_checkpoint, receipt, english_intake)
        self.assertIn("Interview request recorded", english["intake_question"])

    def test_complete_debrief_allows_manual_next_stage_review(self) -> None:
        artifact = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, valid_debrief())
        self.assertEqual([], validate_screen_debrief(artifact, RECEIPT, self.intake, as_of=date(2026, 8, 27)))
        self.assertEqual("manual_prepare_next_stage_review", artifact["handoff"]["next_safe_action"])
        self.assertEqual("continue_review", artifact["decision"])

    def test_incomplete_debrief_never_prepares(self) -> None:
        debrief = valid_debrief()
        debrief["coverage"][1]["status"] = "unclear"
        debrief["unknown_topics"] = ["Decision criteria remain unknown."]
        debrief["decision"] = "pause"
        artifact = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, debrief)
        self.assertEqual("collect_debrief_context", artifact["handoff"]["next_safe_action"])
        self.assertEqual([], validate_screen_debrief(artifact, RECEIPT, self.intake, as_of=date(2026, 8, 27)))

    def test_debrief_rejects_paths_and_credential_shaped_notes(self) -> None:
        for value in (
            "/tmp/candidate.txt",
            "bearer abcdefghijklmnopqrstuvwxyz123456",
            "secret=abcdEFGH1234",
            "person&amp;#64;example.com",
            "https:&amp;#x2F;&amp;#x2F;linkedin.com&amp;#x2F;in&amp;#x2F;synthetic",
        ):
            debrief = valid_debrief()
            debrief["coverage"][0]["note"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, debrief)

    def test_stop_is_terminal_and_blocks_next_stage(self) -> None:
        debrief = valid_debrief()
        debrief["decision"] = "stop"
        artifact = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, debrief)
        self.assertEqual("record_stop_decision", artifact["handoff"]["next_safe_action"])
        self.assertEqual("stop_decision", artifact["measurement_event"])

    def test_invalid_decision_fails_closed(self) -> None:
        debrief = valid_debrief()
        debrief["decision"] = "advance"
        with self.assertRaises(ValueError):
            build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, debrief)

    def test_source_checkpoint_and_intake_drift_fail_closed(self) -> None:
        artifact = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, valid_debrief())
        tampered_checkpoint = copy.deepcopy(artifact["source_checkpoint"])
        tampered_checkpoint["next_safe_action"] = "route_to_prepare-role-interviews"
        tampered = copy.deepcopy(artifact)
        tampered["source_checkpoint"] = tampered_checkpoint
        self.assertTrue(validate_screen_debrief(tampered, RECEIPT, self.intake, as_of=date(2026, 8, 27)))
        tampered = copy.deepcopy(artifact)
        tampered["source_intake"]["source_gate_snapshot"] = "snap-shortlist-sha256-" + "0" * 64
        self.assertTrue(validate_screen_debrief(tampered, RECEIPT, self.intake, as_of=date(2026, 8, 27)))

    def test_target_fact_ownership_is_required(self) -> None:
        tampered = copy.deepcopy(self.intake)
        tampered["intake"]["candidate_fact_ids"] = ["F-999"]
        intake_errors = validate_screen_intake(tampered, source_gate=self.gate, as_of=date(2026, 8, 27))
        self.assertIn("intake.candidate_fact_ids are not supported by target", intake_errors)
        self.assertTrue(validate_screen_debrief(
            build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, valid_debrief()),
            RECEIPT,
            tampered,
            as_of=date(2026, 8, 27),
        ))

    def test_receipt_must_represent_a_requested_screen(self) -> None:
        receipt = copy.deepcopy(RECEIPT)
        receipt["event_type"] = "contact_received"
        receipt["next_safe_action"] = "clarify_context_before_reply"
        checkpoint = valid_checkpoint()
        checkpoint["source_receipt"]["event_type"] = "contact_received"
        with self.assertRaises(ValueError):
            build_screen_debrief(checkpoint, receipt, self.intake, valid_debrief())

    def test_future_observed_date_is_rejected(self) -> None:
        debrief = valid_debrief()
        debrief["observed_date"] = "2099-01-01"
        with self.assertRaises(ValueError):
            build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, debrief)

    def test_renderer_does_not_fallback_from_an_explicit_empty_checkpoint(self) -> None:
        artifact = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, valid_debrief())
        with self.assertRaises(ValueError):
            render_screen_debrief_html(artifact, RECEIPT, self.intake, checkpoint={})

    def test_replay_fingerprint_is_stable_and_changes_on_semantic_mutation(self) -> None:
        first = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, valid_debrief())
        second = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, valid_debrief())
        self.assertEqual(first["replay_fingerprint"], second["replay_fingerprint"])
        changed = valid_debrief()
        changed["coverage"][0]["note"] = "Role scope and requirements were discussed."
        third = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, changed)
        self.assertNotEqual(first["replay_fingerprint"], third["replay_fingerprint"])

    def test_renderer_localizes_and_hides_all_internal_ids_and_notes(self) -> None:
        artifact = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, valid_debrief())
        rendered = render_screen_debrief_html(artifact, RECEIPT, self.intake)
        self.assertIn("Debrief privado del filtro", rendered)
        for token in ("T-001", "F-001", "V-001", "D-104", "Role scope was discussed"):
            self.assertNotIn(token, rendered)
        english_gate = build_decision_gate(build_shortlist("en", "2026-08-27", valid_plan(), valid_targets()))
        english_intake = build_screen_intake(english_gate, "T-001", valid_screen_intake())
        english_checkpoint = valid_checkpoint()
        english_checkpoint["target_binding"]["source_gate_snapshot"] = english_intake["source_gate_snapshot"]
        english = build_screen_debrief(english_checkpoint, RECEIPT, english_intake, valid_debrief())
        english_rendered = render_screen_debrief_html(english, RECEIPT, english_intake)
        self.assertIn("Private screen debrief", english_rendered)
        self.assertEqual(1, rendered.count('aria-current="step"'))
        self.assertEqual(1, english_rendered.count('aria-current="step"'))
        self.assertIn("Debrief de pantalla", rendered)
        self.assertIn("Screen debrief", english_rendered)

    def test_renderer_covers_every_supported_stage_in_both_locales(self) -> None:
        stage_labels = {
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
        english_gate = build_decision_gate(build_shortlist("en", "2026-08-27", valid_plan(), valid_targets()))
        for stage, (spanish_label, english_label) in stage_labels.items():
            context = valid_screen_intake()
            context["stated_stage"] = stage
            spanish_intake = build_screen_intake(self.gate, "T-001", context)
            spanish_artifact = build_screen_debrief(valid_checkpoint(), RECEIPT, spanish_intake, valid_debrief())
            self.assertIn(spanish_label, render_screen_debrief_html(spanish_artifact, RECEIPT, spanish_intake))

            english_intake = build_screen_intake(english_gate, "T-001", context)
            english_checkpoint = valid_checkpoint()
            english_checkpoint["target_binding"]["source_gate_snapshot"] = english_intake["source_gate_snapshot"]
            english_artifact = build_screen_debrief(english_checkpoint, RECEIPT, english_intake, valid_debrief())
            rendered = render_screen_debrief_html(english_artifact, RECEIPT, english_intake)
            self.assertIn(english_label, rendered)
            self.assertNotIn(f">{stage}<", rendered)

    def test_cli_unknown_arguments_are_opaque(self) -> None:
        from validate_private_recruiter_screen_debrief import _cli

        self.assertEqual(3, _cli(["--private-token-value"]))

    def test_route_exposes_only_manual_or_context_collection_states(self) -> None:
        routed = route_recruiter_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, valid_debrief())
        self.assertEqual("ready", routed["case_state"])
        self.assertEqual("manual_prepare_next_stage_review", routed["next_action"])
        self.assertIn("Debrief privado del filtro", routed["rendered_html"])
        self.assertNotIn("F-001", routed["rendered_html"])
        paused = valid_debrief()
        paused["decision"] = "pause"
        paused["unknown_topics"] = ["Decision criteria remain unknown."]
        paused["coverage"][0]["status"] = "unclear"
        routed = route_recruiter_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, paused)
        self.assertEqual("needs_intake", routed["case_state"])
        self.assertEqual("collect_debrief_context", routed["next_action"])
        self.assertIn("Debrief privado del filtro", routed["rendered_html"])

        stopped = valid_debrief()
        stopped["decision"] = "stop"
        routed = route_recruiter_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, stopped)
        self.assertEqual("stopped", routed["case_state"])
        self.assertEqual("record_stop_decision", routed["next_action"])
        self.assertIn("Debrief privado del filtro", routed["rendered_html"])


if __name__ == "__main__":
    unittest.main()
