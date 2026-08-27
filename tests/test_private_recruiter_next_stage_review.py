"""Contracts for the private next-stage review handoff."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_private_recruiter_next_stage_review import build_next_stage_review  # noqa: E402
from build_private_recruiter_screen_debrief import build_screen_debrief  # noqa: E402
from build_recruiter_target_shortlist import build_shortlist  # noqa: E402
from render_private_recruiter_next_stage_review import _cli as render_cli  # noqa: E402
from render_private_recruiter_next_stage_review import render_next_stage_review_html  # noqa: E402
from route_recruiter_target_shortlist import route_recruiter_next_stage_review  # noqa: E402
from validate_private_recruiter_next_stage_review import validate_next_stage_review  # noqa: E402
from tests.test_private_recruiter_screen_debrief import RECEIPT, valid_checkpoint, valid_debrief  # noqa: E402
from tests.test_recruiter_target_decision_gate import RecruiterTargetDecisionGateTests  # noqa: E402
from tests.test_recruiter_target_shortlist import valid_plan, valid_targets  # noqa: E402
from tests.test_recruiter_target_screen_intake import valid_screen_intake  # noqa: E402
from build_recruiter_target_decision_gate import build_decision_gate  # noqa: E402
from build_recruiter_target_screen_intake import build_screen_intake  # noqa: E402


class PrivateRecruiterNextStageReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        shortlist = RecruiterTargetDecisionGateTests().shortlist()
        self.gate = build_decision_gate(shortlist)
        self.intake = build_screen_intake(self.gate, "T-001", valid_screen_intake())
        self.debrief = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, valid_debrief())

    def test_complete_debrief_creates_ready_first_interview_review(self) -> None:
        artifact = build_next_stage_review(self.debrief, RECEIPT, self.intake, valid_checkpoint(), "first_interview")
        self.assertEqual([], validate_next_stage_review(artifact, self.debrief, RECEIPT, self.intake, valid_checkpoint(), as_of=date(2026, 8, 27)))
        self.assertEqual("ready", artifact["review_state"])
        self.assertEqual("manual_prepare_next_stage_review", artifact["handoff"]["next_safe_action"])
        self.assertEqual("candidate_with_coach_review", artifact["review_owner"])

    def test_incomplete_or_stopped_debrief_is_blocked(self) -> None:
        paused = valid_debrief()
        paused["decision"] = "pause"
        paused["unknown_topics"] = ["Decision criteria remain unknown."]
        paused["coverage"][0]["status"] = "unclear"
        debrief = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, paused)
        artifact = build_next_stage_review(debrief, RECEIPT, self.intake, valid_checkpoint(), "technical_screen")
        self.assertEqual("blocked", artifact["review_state"])
        self.assertEqual("collect_debrief_context", artifact["handoff"]["next_safe_action"])
        self.assertEqual([], validate_next_stage_review(artifact, debrief, RECEIPT, self.intake, valid_checkpoint(), as_of=date(2026, 8, 27)))

    def test_blocked_renderer_explains_structured_topics_to_clarify(self) -> None:
        paused = valid_debrief()
        paused["decision"] = "pause"
        paused["unknown_topics"] = ["Decision criteria remain unknown."]
        paused["coverage"][1]["status"] = "unclear"
        debrief = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, paused)
        artifact = build_next_stage_review(debrief, RECEIPT, self.intake, valid_checkpoint(), "technical_screen")
        rendered = render_next_stage_review_html(artifact, debrief, RECEIPT, self.intake, valid_checkpoint())
        self.assertIn("Aclara estos temas", rendered)
        self.assertIn("Alcance y éxito", rendered)
        self.assertNotIn("Decision criteria remain unknown", rendered)
        self.assertIn("next-stage-summary--blocked", rendered)

    def test_stage_must_be_explicit_and_next_stage_only(self) -> None:
        with self.assertRaises(ValueError):
            build_next_stage_review(self.debrief, RECEIPT, self.intake, valid_checkpoint(), "recruiter_screen")

    def test_source_drift_and_replay_mutation_fail_closed(self) -> None:
        artifact = build_next_stage_review(self.debrief, RECEIPT, self.intake, valid_checkpoint(), "first_interview")
        tampered = copy.deepcopy(artifact)
        tampered["source_debrief"]["decision"] = "pause"
        self.assertTrue(validate_next_stage_review(tampered, self.debrief, RECEIPT, self.intake, valid_checkpoint(), as_of=date(2026, 8, 27)))
        changed = copy.deepcopy(artifact)
        changed["next_stage"] = "technical_screen"
        from validate_private_recruiter_next_stage_review import replay_fingerprint
        changed["replay_fingerprint"] = replay_fingerprint(changed)
        self.assertNotEqual(artifact["replay_fingerprint"], changed["replay_fingerprint"])

    def test_review_date_cannot_precede_source_debrief(self) -> None:
        artifact = build_next_stage_review(self.debrief, RECEIPT, self.intake, valid_checkpoint(), "first_interview")
        artifact["observed_date"] = "2026-08-26"
        from validate_private_recruiter_next_stage_review import replay_fingerprint
        artifact["replay_fingerprint"] = replay_fingerprint(artifact)
        self.assertTrue(validate_next_stage_review(artifact, self.debrief, RECEIPT, self.intake, valid_checkpoint(), as_of=date(2026, 8, 27)))

    def test_same_current_and_next_stage_is_rejected(self) -> None:
        context = valid_screen_intake()
        context["stated_stage"] = "first_interview"
        intake = build_screen_intake(self.gate, "T-001", context)
        debrief = build_screen_debrief(valid_checkpoint(), RECEIPT, intake, valid_debrief())
        with self.assertRaises(ValueError):
            build_next_stage_review(debrief, RECEIPT, intake, valid_checkpoint(), "first_interview")

    def test_technical_screen_can_handoff_to_hiring_manager_with_transition_copy(self) -> None:
        context = valid_screen_intake()
        context["stated_stage"] = "technical_screen"
        intake = build_screen_intake(self.gate, "T-001", context)
        debrief = build_screen_debrief(valid_checkpoint(), RECEIPT, intake, valid_debrief())
        review = build_next_stage_review(debrief, RECEIPT, intake, valid_checkpoint(), "hiring_manager")
        self.assertEqual([], validate_next_stage_review(review, debrief, RECEIPT, intake, valid_checkpoint(), as_of=date(2026, 8, 27)))
        rendered = render_next_stage_review_html(review, debrief, RECEIPT, intake, valid_checkpoint())
        self.assertIn("Filtro técnico", rendered)
        self.assertIn("Entrevista con hiring manager", rendered)
        self.assertIn("→", rendered)

    def test_unsupported_backward_stage_transition_is_rejected(self) -> None:
        context = valid_screen_intake()
        context["stated_stage"] = "technical_screen"
        intake = build_screen_intake(self.gate, "T-001", context)
        debrief = build_screen_debrief(valid_checkpoint(), RECEIPT, intake, valid_debrief())
        with self.assertRaises(ValueError):
            build_next_stage_review(debrief, RECEIPT, intake, valid_checkpoint(), "first_interview")

    def test_source_debrief_fingerprint_is_part_of_review_replay(self) -> None:
        artifact = build_next_stage_review(self.debrief, RECEIPT, self.intake, valid_checkpoint(), "first_interview")
        changed_debrief = copy.deepcopy(self.debrief)
        changed_debrief["coverage"][0]["note"] = "Requirements and scope were discussed."
        from validate_private_recruiter_screen_debrief import replay_fingerprint as debrief_fingerprint
        changed_debrief["replay_fingerprint"] = debrief_fingerprint(changed_debrief)
        changed = copy.deepcopy(artifact)
        changed["source_debrief"] = changed_debrief
        from validate_private_recruiter_next_stage_review import replay_fingerprint
        changed["replay_fingerprint"] = replay_fingerprint(changed)
        self.assertTrue(validate_next_stage_review(changed, self.debrief, RECEIPT, self.intake, valid_checkpoint(), as_of=date(2026, 8, 27)))

    def test_non_hashable_facts_return_validation_errors(self) -> None:
        artifact = build_next_stage_review(self.debrief, RECEIPT, self.intake, valid_checkpoint(), "first_interview")
        artifact["facts_used"] = [{}]
        self.assertTrue(validate_next_stage_review(artifact, self.debrief, RECEIPT, self.intake, valid_checkpoint(), as_of=date(2026, 8, 27)))

    def test_checklist_status_must_match_source_debrief(self) -> None:
        artifact = build_next_stage_review(self.debrief, RECEIPT, self.intake, valid_checkpoint(), "first_interview")
        artifact["checklist"][0]["status"] = "needs_clarification"
        self.assertTrue(validate_next_stage_review(artifact, self.debrief, RECEIPT, self.intake, valid_checkpoint(), as_of=date(2026, 8, 27)))

    def test_renderer_localizes_and_hides_private_identifiers_and_notes(self) -> None:
        artifact = build_next_stage_review(self.debrief, RECEIPT, self.intake, valid_checkpoint(), "first_interview")
        rendered = render_next_stage_review_html(artifact, self.debrief, RECEIPT, self.intake, valid_checkpoint())
        self.assertIn("Revisión de la siguiente etapa", rendered)
        for token in ("T-001", "F-001", "V-001", "D-104", "Role scope was discussed"):
            self.assertNotIn(token, rendered)
        english_gate = build_decision_gate(build_shortlist("en", "2026-08-27", valid_plan(), valid_targets()))
        english_intake = build_screen_intake(english_gate, "T-001", valid_screen_intake())
        english_debrief = build_screen_debrief(valid_checkpoint(), RECEIPT, english_intake, valid_debrief())
        english = build_next_stage_review(english_debrief, RECEIPT, english_intake, valid_checkpoint(), "first_interview")
        self.assertIn("Next-stage review", render_next_stage_review_html(english, english_debrief, RECEIPT, english_intake, valid_checkpoint()))

    def test_renderer_shows_selected_next_stage_in_localized_summary(self) -> None:
        first = build_next_stage_review(self.debrief, RECEIPT, self.intake, valid_checkpoint(), "first_interview")
        first_html = render_next_stage_review_html(first, self.debrief, RECEIPT, self.intake, valid_checkpoint())
        self.assertIn("Primera entrevista", first_html)
        technical = build_next_stage_review(self.debrief, RECEIPT, self.intake, valid_checkpoint(), "technical_screen")
        technical_html = render_next_stage_review_html(technical, self.debrief, RECEIPT, self.intake, valid_checkpoint())
        self.assertIn("Filtro técnico", technical_html)

    def test_cli_unknown_arguments_are_opaque(self) -> None:
        from validate_private_recruiter_next_stage_review import _cli

        self.assertEqual(3, _cli(["--private-token-value"]))

    def test_renderer_cli_rejects_duplicate_json_keys(self) -> None:
        artifact = build_next_stage_review(self.debrief, RECEIPT, self.intake, valid_checkpoint(), "first_interview")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "review.json"
            duplicate = json.dumps(artifact, ensure_ascii=False)
            duplicate = duplicate.replace("{\"schema_version\":", "{\"schema_version\":\"forged\",\"schema_version\":", 1)
            input_path.write_text(duplicate, encoding="utf-8")
            paths = {}
            for name, value in (("debrief", self.debrief), ("receipt", RECEIPT), ("intake", self.intake), ("checkpoint", valid_checkpoint())):
                path = root / f"{name}.json"
                path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
                paths[name] = path
            output = root / "review.html"
            result = render_cli([str(input_path), "--debrief", str(paths["debrief"]), "--receipt", str(paths["receipt"]), "--intake", str(paths["intake"]), "--checkpoint", str(paths["checkpoint"]), "--output", str(output)])
            self.assertEqual(3, result)
            self.assertFalse(output.exists())

    def test_route_exposes_only_manual_or_blocked_states(self) -> None:
        routed = route_recruiter_next_stage_review(self.debrief, RECEIPT, self.intake, valid_checkpoint(), "first_interview")
        self.assertEqual("ready", routed["case_state"])
        self.assertEqual("manual_prepare_next_stage_review", routed["next_action"])
        self.assertIn("Revisión de la siguiente etapa", routed["rendered_html"])
        self.assertNotIn("F-001", routed["rendered_html"])

        stopped = valid_debrief()
        stopped["decision"] = "stop"
        stopped_debrief = build_screen_debrief(valid_checkpoint(), RECEIPT, self.intake, stopped)
        routed = route_recruiter_next_stage_review(stopped_debrief, RECEIPT, self.intake, valid_checkpoint(), "first_interview")
        self.assertEqual("stopped", routed["case_state"])
        self.assertEqual("record_stop_decision", routed["next_action"])
        self.assertIn("Revisión de la siguiente etapa", routed["rendered_html"])


if __name__ == "__main__":
    unittest.main()
