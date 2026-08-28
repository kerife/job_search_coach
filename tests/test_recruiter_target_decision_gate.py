"""Contracts for the private recruiter target decision gate."""

from __future__ import annotations

import copy
import datetime as dt
import importlib.util
import json
import os
import subprocess
import tempfile
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_recruiter_target_shortlist import build_shortlist  # noqa: E402
from build_recruiter_target_decision_gate import build_decision_gate  # noqa: E402
from render_recruiter_target_decision_gate import render_decision_gate_html  # noqa: E402
from validate_recruiter_target_decision_gate import validate_decision_gate  # noqa: E402
from route_recruiter_target_shortlist import (  # noqa: E402
    route_recruiter_decision_gate,
    route_recruiter_next_stage_review,
    route_recruiter_screen_debrief,
    route_recruiter_screen_intake,
)
_schema_spec = importlib.util.spec_from_file_location(
    "decision_gate_schema_conformance",
    ROOT / "plugins" / "professional-growth-coach" / "tests" / "validate_private_schema_conformance.py",
)
if _schema_spec is None or _schema_spec.loader is None:
    raise RuntimeError("private schema conformance helper unavailable")
_schema_module = importlib.util.module_from_spec(_schema_spec)
_schema_spec.loader.exec_module(_schema_module)
validate_schema_instance = _schema_module.validate_schema_instance

from tests.test_recruiter_target_shortlist import valid_plan, valid_targets  # noqa: E402


class RecruiterTargetDecisionGateTests(unittest.TestCase):
    def test_root_discovery_keeps_same_named_private_test_in_root_suite(self) -> None:
        probe = (
            "import importlib.util, sys; "
            "sys.path.insert(0, 'tests'); "
            "import test_recruiter_target_decision_gate; "
            "spec = importlib.util.find_spec('test_private_recruiter_reply_triage'); "
            "assert spec and spec.origin and spec.origin.endswith('/tests/test_private_recruiter_reply_triage.py'), spec"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", probe],
            cwd=ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def shortlist(self) -> dict[str, object]:
        return build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())

    def test_builder_reconciles_counts_and_binds_full_shortlist_snapshot(self) -> None:
        shortlist = self.shortlist()
        gate = build_decision_gate(shortlist)
        self.assertEqual([], validate_decision_gate(gate, as_of=date(2026, 8, 27)))
        self.assertEqual("recruiter-target-decision-gate-v1", gate["schema_version"])
        self.assertEqual({"advance": 1, "clarify": 1, "pause": 1, "stop": 0}, gate["decision_counts"])
        self.assertEqual(shortlist, gate["source_shortlist"])
        self.assertEqual("collect_screen_context", gate["handoff"]["next_safe_action"])

    def test_builder_rejects_future_dated_shortlist(self) -> None:
        shortlist = self.shortlist()
        shortlist["as_of_date"] = "2999-01-01"
        with self.assertRaises(ValueError):
            build_decision_gate(shortlist)

    def test_validator_rejects_future_evaluation_date(self) -> None:
        gate = build_decision_gate(self.shortlist())
        self.assertIn("as_of cannot be in the future", validate_decision_gate(gate, as_of=date.today() + dt.timedelta(days=1)))

    def test_validator_rejects_gate_date_drift_from_source_shortlist(self) -> None:
        shortlist = build_shortlist("en", "2026-01-01", valid_plan(), valid_targets())
        gate = build_decision_gate(shortlist)
        gate["as_of_date"] = "2026-08-27"
        self.assertIn(
            "as_of_date must match source_shortlist.as_of_date",
            validate_decision_gate(gate, as_of=date(2026, 8, 27)),
        )

    def test_validator_rejects_tampered_source_snapshot_and_counts(self) -> None:
        gate = build_decision_gate(self.shortlist())
        tampered = copy.deepcopy(gate)
        tampered["source_shortlist"]["targets"][0]["decision"] = "stop"
        self.assertIn("source_shortlist snapshot does not match source_snapshot", validate_decision_gate(tampered))
        tampered = copy.deepcopy(gate)
        tampered["decision_counts"]["advance"] = 2
        self.assertIn("decision_counts do not reconcile with decision rows", validate_decision_gate(tampered))

    def test_validator_rejects_decision_rows_that_drift_from_source_target(self) -> None:
        gate = build_decision_gate(self.shortlist())
        mutations = {
            "decision_reason": "Changed reason",
            "contactability_status": "do_not_contact",
            "missing_context": "Changed context",
            "recommended_draft_type": "none",
            "next_safe_action": "record_observation_only",
        }
        for field, value in mutations.items():
            tampered = copy.deepcopy(gate)
            tampered["decision_rows"][0][field] = value
            with self.subTest(field=field):
                self.assertIn(
                    f"decision_rows[0].{field} must match source shortlist",
                    validate_decision_gate(tampered),
                )

    def test_validator_rejects_derived_strategy_drift(self) -> None:
        gate = build_decision_gate(self.shortlist())
        for field in ("first_contact_strategy", "warm_intro_readiness"):
            tampered = copy.deepcopy(gate)
            tampered["decision_rows"][0][field] = "Different recommendation"
            with self.subTest(field=field):
                self.assertIn(
                    f"decision_rows[0].{field} must match locale and decision",
                    validate_decision_gate(tampered),
                )

    def test_validator_rejects_restricted_decision_prose(self) -> None:
        gate = build_decision_gate(self.shortlist())
        for field, value in {
            "decision_reason": "jane.doe@example.com",
            "missing_context": "/Users/example/private.txt",
            "first_contact_strategy": "https://example.invalid/role",
            "warm_intro_readiness": "javascript:alert(1)",
        }.items():
            tampered = copy.deepcopy(gate)
            tampered["decision_rows"][0][field] = value
            with self.subTest(field=field):
                self.assertIn(
                    f"decision_rows[0].{field} must be bounded safe text",
                    validate_decision_gate(tampered),
                )

    def test_validator_rejects_unbound_decision_rows(self) -> None:
        gate = build_decision_gate(self.shortlist())
        tampered = copy.deepcopy(gate)
        extra = copy.deepcopy(tampered["decision_rows"][0])
        extra["target_id"] = "T-999"
        tampered["decision_rows"].append(extra)
        tampered["decision_counts"]["advance"] += 1
        self.assertIn("decision_rows must preserve source target count", validate_decision_gate(tampered))

    def test_confirmed_screen_context_enables_manual_interview_handoff_only(self) -> None:
        gate = build_decision_gate(
            self.shortlist(),
            screen_context={
                "vacancy_summary": "Platform reliability role with an initial recruiter screen.",
                "confirmed_fact_summary": "Candidate supplied a verified delivery outcome.",
            },
        )
        self.assertEqual([], validate_decision_gate(gate, as_of=date(2026, 8, 27)))
        self.assertEqual("prepare_role_interviews_review", gate["handoff"]["next_safe_action"])
        self.assertTrue(gate["handoff"]["manual_review_required"])
        self.assertFalse(gate["delivery"]["external_actions_authorized"])

    def test_renderer_localizes_next_decision_and_omits_private_ids(self) -> None:
        gate = build_decision_gate(self.shortlist())
        rendered = render_decision_gate_html(gate)
        self.assertIn("Siguiente decisión", rendered)
        self.assertIn("Recopilar contexto de pantalla", rendered)
        self.assertIn("Avanzar", rendered)
        self.assertNotIn("T-001", rendered)
        self.assertNotIn("F-001", rendered)
        english = copy.deepcopy(gate)
        english["locale"] = "en"
        english_rendered = render_decision_gate_html(english)
        self.assertIn("Next decision", english_rendered)
        self.assertIn("Collect screen context", english_rendered)
        self.assertEqual(1, rendered.count('aria-current="step"'))
        self.assertIn("Ruta de revisión recruiter", rendered)
        self.assertIn("Recruiter review path", english_rendered)

    def test_gate_rejects_external_action_authorization(self) -> None:
        gate = build_decision_gate(self.shortlist())
        gate["delivery"]["external_actions_authorized"] = True
        errors = validate_decision_gate(gate)
        self.assertIn("delivery.external_actions_authorized has immutable value", errors)

    def test_screen_context_rejects_contact_and_path_shaped_text(self) -> None:
        for value in (
            "jane.doe@example.com",
            "+52 55 1234 5678",
            "/Users/example/private.txt",
            "ssh://host/private",
            "javascript:alert(1)",
            "data:text/plain,private",
            "~/private.txt",
            "../private.txt",
            "www.example.com",
            "linkedin.com/in/example",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    build_decision_gate(
                        self.shortlist(),
                        screen_context={
                            "vacancy_summary": value,
                            "confirmed_fact_summary": "Bounded platform reliability context.",
                        },
                    )
        gate = build_decision_gate(
            self.shortlist(),
            screen_context={
                "vacancy_summary": "Platform reliability role with an initial recruiter screen.",
                "confirmed_fact_summary": "Candidate supplied a verified delivery outcome.",
            },
        )
        for value in (
            "jane.doe@example.com",
            "+52 55 1234 5678",
            "/Users/example/private.txt",
            "ssh://host/private",
            "javascript:alert(1)",
            "data:text/plain,private",
            "~/private.txt",
            "../private.txt",
            "www.example.com",
            "linkedin.com/in/example",
        ):
            invalid = copy.deepcopy(gate)
            invalid["screen_context"]["confirmed_fact_summary"] = value
            with self.subTest(validator_value=value):
                self.assertIn("screen_context.confirmed_fact_summary must be bounded safe context", validate_decision_gate(invalid))

    def test_schema_is_closed_at_the_gate_boundary(self) -> None:
        gate = build_decision_gate(self.shortlist())
        schema = json.loads(
            (ROOT / "plugins/professional-growth-coach/schemas/recruiter-target-decision-gate-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual([], validate_schema_instance(gate, schema))
        invalid = copy.deepcopy(gate)
        invalid["source_shortlist"] = {}
        self.assertTrue(validate_schema_instance(invalid, schema))

    def test_cli_rejects_duplicate_json_keys(self) -> None:
        from build_recruiter_target_decision_gate import _cli

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "shortlist.json"
            output = Path(directory) / "gate.json"
            source.write_text('{"schema_version":"x","schema_version":"y"}', encoding="utf-8")
            self.assertEqual(3, _cli([str(source), str(output)]))

    def test_route_hands_off_only_to_manual_gate_or_collects_context(self) -> None:
        ready = route_recruiter_decision_gate(self.shortlist())
        self.assertEqual("recruiter_target_decision_gate", ready["route_kind"])
        self.assertEqual("ready", ready["case_state"])
        self.assertEqual("collect_screen_context", ready["next_action"])
        self.assertIn("Siguiente decisión", ready["rendered_html"])
        self.assertNotIn("T-001", ready["rendered_html"])
        self.assertNotIn("F-001", ready["rendered_html"])
        intake = route_recruiter_decision_gate({})
        self.assertEqual("needs_intake", intake["case_state"])
        self.assertEqual("collect_screen_context", intake["next_action"])
        self.assertNotIn("rendered_html", intake)

    def test_artifact_free_handoffs_explain_the_next_intake_step(self) -> None:
        cases = (
            route_recruiter_decision_gate(
                {},
                screen_context={"vacancy_summary": "bounded", "confirmed_fact_summary": "bounded"},
            ),
            route_recruiter_screen_intake({}, "T-001", {}),
            route_recruiter_screen_debrief({}, {}, {}, {}),
            route_recruiter_next_stage_review({}, {}, {}, {}, "first_interview"),
        )
        for result in cases:
            with self.subTest(route=result["route_kind"]):
                self.assertEqual("needs_intake", result["case_state"])
                self.assertIsNone(result["artifact"])
                self.assertTrue(result["evidence_gaps"])
                self.assertIsInstance(result["intake_question"], str)
                self.assertNotIn("T-001", result["intake_question"])

    def test_artifact_free_handoffs_use_route_specific_recovery_copy(self) -> None:
        cases = (
            (
                route_recruiter_decision_gate({}),
                ("shortlist", "3–6"),
            ),
            (
                route_recruiter_decision_gate({}, screen_context={"vacancy_summary": "bounded", "confirmed_fact_summary": "bounded"}),
                ("etapa", "V-"),
            ),
            (route_recruiter_screen_intake({}, "T-001", {}), ("etapa", "V-")),
            (route_recruiter_screen_debrief({}, {}, {}, {}), ("checkpoint", "receipt")),
            (route_recruiter_next_stage_review({}, {}, {}, {}, "first_interview"), ("debrief", "etapa posterior")),
        )
        for result, markers in cases:
            with self.subTest(route=result["route_kind"]):
                self.assertTrue(all(marker.lower() in result["intake_question"].lower() for marker in markers))
                self.assertNotIn("red de recruiters", result["intake_question"].lower())

    def test_transition_recovery_names_allowed_forward_stages_without_artifact(self) -> None:
        from tests.test_private_recruiter_next_stage_review import valid_checkpoint, valid_debrief
        from tests.test_recruiter_target_screen_intake import valid_screen_intake

        shortlist = self.shortlist()
        gate = build_decision_gate(shortlist)
        intake = __import__("build_recruiter_target_screen_intake", fromlist=["build_screen_intake"]).build_screen_intake(
            gate, "T-001", valid_screen_intake()
        )
        debrief = __import__("build_private_recruiter_screen_debrief", fromlist=["build_screen_debrief"]).build_screen_debrief(
            valid_checkpoint(),
            __import__("tests.test_private_recruiter_screen_debrief", fromlist=["RECEIPT"]).RECEIPT,
            intake,
            valid_debrief(),
        )
        routed = route_recruiter_next_stage_review(
            debrief,
            __import__("tests.test_private_recruiter_screen_debrief", fromlist=["RECEIPT"]).RECEIPT,
            intake,
            valid_checkpoint(),
            "recruiter_screen",
        )
        self.assertEqual("needs_intake", routed["case_state"])
        self.assertEqual("select_forward_stage", routed["next_action"])
        self.assertEqual(["first_interview", "technical_screen"], routed["allowed_next_stages"])
        self.assertIn("forward_stage_transition", routed["evidence_gaps"])
        self.assertIsNone(routed["artifact"])

    def test_route_specific_recovery_copy_is_localized_in_english(self) -> None:
        cases = (
            route_recruiter_decision_gate({"locale": "en"}),
            route_recruiter_screen_intake({"locale": "en"}, "T-001", {}),
            route_recruiter_screen_debrief({"locale": "en"}, {}, {"locale": "en"}, {}),
            route_recruiter_next_stage_review({"locale": "en"}, {}, {}, {}, "first_interview"),
        )
        for result in cases:
            with self.subTest(route=result["route_kind"]):
                self.assertNotIn("Comparte", result["intake_question"])
                self.assertIn("Share", result["intake_question"])


if __name__ == "__main__":
    unittest.main()
