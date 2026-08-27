import copy
import datetime as dt
import importlib.util
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_private_schema_conformance import (
    validate_checkpoint_for_test,
    validate_outcome_for_test,
    validate_private_fixture_semantics,
    validate_schema_instance,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_dossier_recruiter_practice_handoff import build_handoff
from build_recruiter_target_decision_gate import build_decision_gate
from build_recruiter_target_shortlist import build_shortlist
from build_recruiter_target_screen_intake import build_screen_intake
from build_private_recruiter_screen_debrief import build_screen_debrief
from build_private_recruiter_next_stage_review import build_next_stage_review
from validate_dossier_recruiter_practice_handoff import validate_handoff
from private_prose_safety import is_safe_prose_text
from validate_private_recruiter_reply_triage import validate_triage
from validate_recruiter_practice_session import validate_session
from tests.test_recruiter_target_shortlist import valid_plan, valid_targets


def _load_v2_dossier_helper():
    path = ROOT.parent.parent / "tests" / "test_executive_career_dossier_v2.py"
    specification = importlib.util.spec_from_file_location("v2_dossier_test_helper", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("v2 dossier test helper is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


V2_READY_ES_SNAPSHOT = (
    "snap-triage-sha256-"
    "74720a33a8bfc5e085767831e741b7cce97d45b1bb2d76b47d3ee203a2b5d6e8"
)
V2_TRIAGE_PRACTICE_SNAPSHOT = (
    "snap-triage-sha256-"
    "85ad96e9cab8b222315a01a85d4a6f61f0d5a38650a1286773bc8e1664c15ebd"
)


class PrivateSchemaConformanceTests(unittest.TestCase):
    def _schema(self, name):
        return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))

    def test_recruiter_decision_gate_schema_matches_runtime(self):
        shortlist = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
        gate = build_decision_gate(shortlist)
        schema = self._schema("recruiter-target-decision-gate-v1.schema.json")
        self.assertEqual([], validate_schema_instance(gate, schema))
        invalid = copy.deepcopy(gate)
        invalid["source_shortlist"] = {}
        self.assertTrue(validate_schema_instance(invalid, schema))

    def test_recruiter_target_screen_intake_schema_matches_runtime(self):
        shortlist = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
        gate = build_decision_gate(shortlist)
        intake = build_screen_intake(gate, "T-001", {
            "stated_stage": "recruiter_screen",
            "vacancy_requirements": ["V-001: Platform reliability scope."],
            "candidate_fact_ids": ["F-001"],
            "company_evidence_state": "verified",
            "source_date": "2026-08-27",
            "checks": [
                {"check": "target_context", "status": "pass", "evidence_note": "Named context supplied."},
                {"check": "proof_packet", "status": "pass", "evidence_note": "Supported fact mapped."},
                {"check": "low_friction_ask", "status": "pass", "evidence_note": "Process question only."},
                {"check": "screen_readiness", "status": "pass", "evidence_note": "Stage is explicit."},
            ],
        })
        schema = self._schema("recruiter-target-screen-intake-v1.schema.json")
        self.assertEqual([], validate_schema_instance(intake, schema))
        invalid = copy.deepcopy(intake)
        del invalid["source_gate"]
        self.assertTrue(validate_schema_instance(invalid, schema))

    def test_private_recruiter_screen_debrief_schema_matches_runtime(self):
        shortlist = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
        gate = build_decision_gate(shortlist)
        intake = build_screen_intake(gate, "T-001", {
            "stated_stage": "recruiter_screen",
            "vacancy_requirements": ["V-001: Platform reliability scope."],
            "candidate_fact_ids": ["F-001"],
            "company_evidence_state": "verified",
            "source_date": "2026-08-27",
            "checks": [
                {"check": "target_context", "status": "pass", "evidence_note": "Named context supplied."},
                {"check": "proof_packet", "status": "pass", "evidence_note": "Supported fact mapped."},
                {"check": "low_friction_ask", "status": "pass", "evidence_note": "Process question only."},
                {"check": "screen_readiness", "status": "pass", "evidence_note": "Stage is explicit."},
            ],
        })
        receipt = json.loads((ROOT / "tests/fixtures/private-recruiter-conversion-outcome/screen-requested-en.json").read_text(encoding="utf-8"))
        checkpoint = {
            "schema_version": "private-recruiter-followthrough-checkpoint-v1",
            "artifact_kind": "private_recruiter_followthrough_checkpoint",
            "locale": "en",
            "source_receipt": {"id": "D-104", "source_version": "draft-v1", "event_type": "screen_requested"},
            "action_state": "completed",
            "observed_date": "2026-08-27",
            "next_measurement_event": "screen_attended",
            "next_safe_action": "debrief_after_screen",
            "delivery": {"draft_only": True, "external_actions_authorized": False, "no_message_action": True, "no_calendar_action": True, "raw_event_retained": False, "local_save_mode": "disabled"},
        }
        debrief = build_screen_debrief(checkpoint, receipt, intake, {
            "observed_date": "2026-08-27",
            "coverage": [
                {"topic": "requirement", "status": "discussed", "note": "Role scope was discussed."},
                {"topic": "scope", "status": "discussed", "note": "Success expectations were discussed."},
                {"topic": "team_context", "status": "discussed", "note": "Team context was discussed."},
            ],
            "unknown_topics": [], "facts_used": ["F-001"], "decision": "continue_review",
        })
        schema = self._schema("private-recruiter-screen-debrief-v1.schema.json")
        self.assertEqual([], validate_schema_instance(debrief, schema))
        invalid = copy.deepcopy(debrief)
        invalid["handoff"]["next_safe_action"] = "route_to_prepare-role-interviews"
        self.assertTrue(validate_schema_instance(invalid, schema))
        for field in ("source_receipt", "source_checkpoint", "source_intake"):
            empty_source = copy.deepcopy(debrief)
            empty_source[field] = {}
            self.assertTrue(validate_schema_instance(empty_source, schema))

    def test_private_recruiter_next_stage_review_schema_matches_runtime(self):
        shortlist = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
        gate = build_decision_gate(shortlist)
        intake = build_screen_intake(gate, "T-001", {
            "stated_stage": "recruiter_screen", "vacancy_requirements": ["V-001: Platform reliability scope."],
            "candidate_fact_ids": ["F-001"], "company_evidence_state": "verified", "source_date": "2026-08-27",
            "checks": [
                {"check": "target_context", "status": "pass", "evidence_note": "Named context supplied."},
                {"check": "proof_packet", "status": "pass", "evidence_note": "Supported fact mapped."},
                {"check": "low_friction_ask", "status": "pass", "evidence_note": "Process question only."},
                {"check": "screen_readiness", "status": "pass", "evidence_note": "Stage is explicit."},
            ],
        })
        receipt = json.loads((ROOT / "tests/fixtures/private-recruiter-conversion-outcome/screen-requested-en.json").read_text(encoding="utf-8"))
        checkpoint = {"schema_version": "private-recruiter-followthrough-checkpoint-v1", "artifact_kind": "private_recruiter_followthrough_checkpoint", "locale": "en", "source_receipt": {"id": "D-104", "source_version": "draft-v1", "event_type": "screen_requested"}, "action_state": "completed", "observed_date": "2026-08-27", "next_measurement_event": "screen_attended", "next_safe_action": "debrief_after_screen", "delivery": {"draft_only": True, "external_actions_authorized": False, "no_message_action": True, "no_calendar_action": True, "raw_event_retained": False, "local_save_mode": "disabled"}}
        debrief = build_screen_debrief(checkpoint, receipt, intake, {"observed_date": "2026-08-27", "coverage": [{"topic": "requirement", "status": "discussed", "note": "Requirements discussed."}, {"topic": "scope", "status": "discussed", "note": "Scope discussed."}, {"topic": "team_context", "status": "discussed", "note": "Team context discussed."}], "unknown_topics": [], "facts_used": ["F-001"], "decision": "continue_review"})
        review = build_next_stage_review(debrief, receipt, intake, checkpoint, "first_interview")
        schema = self._schema("private-recruiter-next-stage-review-v1.schema.json")
        self.assertEqual([], validate_schema_instance(review, schema))
        invalid = copy.deepcopy(review)
        invalid["source_debrief"] = {}
        self.assertTrue(validate_schema_instance(invalid, schema))

    def test_next_stage_taxonomy_schema_accepts_forward_hiring_manager_transition(self):
        shortlist = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
        gate = build_decision_gate(shortlist)
        intake = build_screen_intake(gate, "T-001", {
            "stated_stage": "technical_screen", "vacancy_requirements": ["V-001: Platform reliability scope."],
            "candidate_fact_ids": ["F-001"], "company_evidence_state": "verified", "source_date": "2026-08-27",
            "checks": [
                {"check": "target_context", "status": "pass", "evidence_note": "Named context supplied."},
                {"check": "proof_packet", "status": "pass", "evidence_note": "Supported fact mapped."},
                {"check": "low_friction_ask", "status": "pass", "evidence_note": "Process question only."},
                {"check": "screen_readiness", "status": "pass", "evidence_note": "Stage is explicit."},
            ],
        })
        receipt = json.loads((ROOT / "tests/fixtures/private-recruiter-conversion-outcome/screen-requested-en.json").read_text(encoding="utf-8"))
        checkpoint = json.loads((ROOT / "tests/fixtures/private-recruiter-followthrough-checkpoint/completed-screen-attended-en.json").read_text(encoding="utf-8"))
        debrief = build_screen_debrief(checkpoint, receipt, intake, {
            "observed_date": "2026-08-27",
            "coverage": [
                {"topic": "requirement", "status": "discussed", "note": "Requirements discussed."},
                {"topic": "scope", "status": "discussed", "note": "Scope discussed."},
                {"topic": "team_context", "status": "discussed", "note": "Team context discussed."},
            ],
            "unknown_topics": [], "facts_used": ["F-001"], "decision": "continue_review",
        })
        review = build_next_stage_review(debrief, receipt, intake, checkpoint, "hiring_manager")
        schema = self._schema("private-recruiter-next-stage-review-v1.schema.json")
        self.assertEqual([], validate_schema_instance(review, schema))
        invalid = copy.deepcopy(review)
        invalid["next_stage"] = "not_a_stage"
        self.assertTrue(validate_schema_instance(invalid, schema))

    def test_dossier_methodology_categories_keep_schema_runtime_and_registry_in_lockstep(self):
        helper = _load_v2_dossier_helper()
        validator = helper.load_validator()
        expected = {
            "ai_hiring_agents",
            "cover_image",
            "featured_section",
            "good_profile",
            "job_match",
            "job_seeker_hirer_connection",
            "profile_photo",
            "skills",
        }
        registry = json.loads(
            (ROOT / "scripts" / "linkedin_source_registry.json").read_text(encoding="utf-8")
        )
        self.assertEqual(expected, set(validator._v1.METHOD_CATEGORIES))
        self.assertEqual(expected, set(registry["official_categories"]))

        cases = (
            (
                "executive-career-dossier-v1.schema.json",
                helper.load_v1_fixture("scenario-a-es.json"),
                validator._v1.validate_dossier,
            ),
            (
                "executive-career-dossier-v2.schema.json",
                helper.make_v2_dossier(),
                validator.validate_dossier,
            ),
        )
        for schema_name, dossier, validate_dossier in cases:
            with self.subTest(schema=schema_name):
                schema = self._schema(schema_name)
                enum = schema["properties"]["methodology_source_categories"]["items"]["enum"]
                self.assertEqual(expected, set(enum))
                self.assertEqual([], validate_schema_instance(dossier, schema))

                invalid = copy.deepcopy(dossier)
                invalid["methodology_source_categories"] = ["not_a_real_category"]
                self.assertTrue(validate_schema_instance(invalid, schema))
                self.assertTrue(validate_dossier(invalid))

    def test_dossier_market_source_urls_keep_https_boundary_in_schema_and_runtime(self):
        helper = _load_v2_dossier_helper()
        validator = helper.load_validator()
        cases = (
            (
                "executive-career-dossier-v1.schema.json",
                helper.load_v1_fixture("scenario-market-en.json"),
                validator._v1.validate_dossier,
            ),
            (
                "executive-career-dossier-v2.schema.json",
                helper.make_market_v2_dossier("en"),
                validator.validate_dossier,
            ),
        )
        for schema_name, dossier, validate_dossier in cases:
            with self.subTest(schema=schema_name):
                schema = self._schema(schema_name)
                self.assertEqual([], validate_schema_instance(dossier, schema))
                for unsafe_url in ("javascript:alert(1)", "http://example.com/source"):
                    invalid = copy.deepcopy(dossier)
                    invalid["market_context"]["public_sources"][0]["url"] = unsafe_url
                    self.assertTrue(validate_schema_instance(invalid, schema))
                    self.assertTrue(validate_dossier(invalid))

    def test_executive_dossier_v2_schema_accepts_ledger_and_closes_new_fields(self):
        helper = _load_v2_dossier_helper()
        dossier = helper.make_v2_dossier()
        schema = self._schema("executive-career-dossier-v2.schema.json")
        self.assertEqual([], validate_schema_instance(dossier, schema))
        missing_ledger = copy.deepcopy(dossier)
        del missing_ledger["section_coverage"]
        self.assertTrue(validate_schema_instance(missing_ledger, schema))
        missing_request = copy.deepcopy(dossier)
        del missing_request["section_coverage"][2]["inspection_request"]
        self.assertTrue(validate_schema_instance(missing_request, schema))
        missing_priority = copy.deepcopy(dossier)
        del missing_priority["priorities"][0]["client_template"]
        self.assertTrue(validate_schema_instance(missing_priority, schema))
        inherited_v1 = copy.deepcopy(dossier)
        inherited_v1["focus"] = {}
        self.assertTrue(validate_schema_instance(inherited_v1, schema))
        for reason, decision in (
            ("authorization_required", "declined_for_session"),
            ("inspection_declined", "authorized_inspection_failed"),
            ("authorized_inspection_failed", "pending_response"),
        ):
            mismatched = copy.deepcopy(dossier)
            mismatched["section_coverage"][10]["reason"] = reason
            mismatched["section_coverage"][10]["inspection_request"]["decision"] = decision
            self.assertTrue(validate_schema_instance(mismatched, schema))

    def test_schema_diagnostics_redact_absolute_field_names(self):
        cases = [
            (
                {},
                {"type": "object", "required": [r"\\server\share\profile.json"]},
                r"\\server\share\profile.json",
            ),
            (
                {"/opt/private/profile.json": "x"},
                {"type": "object", "properties": {}, "additionalProperties": False},
                "/opt/private/profile.json",
            ),
            (
                {"/Applications/private/profile.json": "x"},
                {"type": "object", "properties": {}, "additionalProperties": False},
                "/Applications/private/profile.json",
            ),
        ]
        for value, schema, sentinel in cases:
            with self.subTest(sentinel=sentinel):
                errors = validate_schema_instance(value, schema)
                self.assertIn("<redacted-field>", "\n".join(errors))
                self.assertNotIn(sentinel, "\n".join(errors))

        nested_key = "/opt/private/nested.json"
        nested_errors = validate_schema_instance(
            {nested_key: 123},
            {
                "type": "object",
                "properties": {nested_key: {"type": "string"}},
                "additionalProperties": False,
            },
        )
        self.assertIn("$.<redacted-field>: type mismatch", nested_errors)
        self.assertNotIn(nested_key, "\n".join(nested_errors))

        ordinary_errors = validate_schema_instance(
            {"extra": "x"},
            {"type": "object", "properties": {}, "additionalProperties": False},
        )
        self.assertIn("$: unsupported field extra", ordinary_errors)

    def test_all_private_conversion_and_followthrough_fixtures_conform(self):
        cases = [
            ("private-recruiter-conversion-outcome-v1.schema.json", ROOT / "tests/fixtures/private-recruiter-conversion-outcome"),
            ("private-recruiter-followthrough-checkpoint-v1.schema.json", ROOT / "tests/fixtures/private-recruiter-followthrough-checkpoint"),
        ]
        for schema_name, directory in cases:
            schema = self._schema(schema_name)
            for path in directory.glob("*.json"):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual([], validate_schema_instance(value, schema), (schema_name, path.name))

    def test_target_vacancy_research_fixtures_conform_to_closed_schema(self):
        schema = self._schema("target-vacancy-research-v1.schema.json")
        fixture_dir = ROOT.parent.parent / "tests/evals/with-skill/fixtures/target-vacancy-research"
        for path in sorted(fixture_dir.glob("*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual([], validate_schema_instance(value, schema), path.name)
        invalid = json.loads((fixture_dir / "complete-five-es.json").read_text(encoding="utf-8"))
        invalid["vacancies"].append(copy.deepcopy(invalid["vacancies"][-1]))
        self.assertTrue(validate_schema_instance(invalid, schema))

    def test_learning_option_research_fixtures_conform_to_closed_schema(self):
        schema = self._schema("learning-option-research-v1.schema.json")
        fixture_dir = ROOT.parent.parent / "tests/evals/with-skill/fixtures/learning-option-research"
        for path in sorted(fixture_dir.glob("*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual([], validate_schema_instance(value, schema), path.name)
        invalid = json.loads((fixture_dir / "complete-five-es.json").read_text(encoding="utf-8"))
        invalid["options"][0]["unexpected"] = True
        self.assertTrue(validate_schema_instance(invalid, schema))

    def test_market_learning_v2_fixtures_conform_to_closed_schema(self):
        schema = self._schema("career-market-learning-dossier-v2.schema.json")
        fixture_dir = ROOT.parent.parent / "tests/evals/with-skill/fixtures/career-market-learning-dossier-v2"
        for path in sorted(fixture_dir.glob("*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual([], validate_schema_instance(value, schema), path.name)
        invalid = json.loads((fixture_dir / "project-first-five-es.json").read_text(encoding="utf-8"))
        invalid["learning_decisions"][0]["unexpected"] = True
        self.assertTrue(validate_schema_instance(invalid, schema))

    def test_market_learning_schemas_and_fixtures_conform(self):
        fixture_dir = ROOT.parent.parent / "tests/evals/with-skill/fixtures/career-market-learning-dossier"
        market_schema = self._schema("career-market-learning-dossier-v1.schema.json")
        for path in sorted(fixture_dir.glob("*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual([], validate_schema_instance(value, market_schema), path.name)
        alignment_schema = self._schema("candidate-market-alignment-v1.schema.json")
        invalid = {
            "schema_version": "candidate-market-alignment-v1",
            "research_snapshot": "snap-market-sha256-" + "0" * 64,
            "executive_dossier_snapshot": "snap-dossier-sha256-" + "0" * 64,
            "signal_bindings": [],
            "privacy_boundary": "identity_free_evidence_references_only",
        }
        self.assertEqual([], validate_schema_instance(invalid, alignment_schema))
        invalid["unexpected"] = "x"
        self.assertTrue(validate_schema_instance(invalid, alignment_schema))

    def test_market_learning_fixtures_and_alignment_schema_are_closed(self):
        alignment_schema = self._schema("candidate-market-alignment-v1.schema.json")
        alignment = {
            "schema_version": "candidate-market-alignment-v1",
            "research_snapshot": "snap-market-sha256-" + "0" * 64,
            "executive_dossier_snapshot": "snap-dossier-sha256-" + "0" * 64,
            "signal_bindings": [],
            "privacy_boundary": "identity_free_evidence_references_only",
        }
        self.assertEqual([], validate_schema_instance(alignment, alignment_schema))
        alignment["unexpected"] = True
        self.assertTrue(validate_schema_instance(alignment, alignment_schema))

        market_schema = self._schema("career-market-learning-dossier-v1.schema.json")
        fixture_dir = ROOT.parent.parent / "tests/evals/with-skill/fixtures/career-market-learning-dossier"
        for path in sorted(fixture_dir.glob("*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual([], validate_schema_instance(value, market_schema), path.name)

    def test_mutations_fail_closed_for_date_closure_and_invariants(self):
        schema = self._schema("private-recruiter-followthrough-checkpoint-v1.schema.json")
        source = json.loads((ROOT / "tests/fixtures/private-recruiter-followthrough-checkpoint/accepted-en.json").read_text(encoding="utf-8"))
        mutations = []
        bad = copy.deepcopy(source); bad["observed_date"] = "2026-02-30"; mutations.append(bad)
        bad = copy.deepcopy(source); bad["unexpected"] = True; mutations.append(bad)
        bad = copy.deepcopy(source); bad["next_safe_action"] = "record_stop_decision"; mutations.append(bad)
        bad = copy.deepcopy(source); bad["next_measurement_event"] = "screen_prepared"; mutations.append(bad)
        for value in mutations:
            self.assertTrue(validate_schema_instance(value, schema), value)

    def test_conversion_mutations_fail_closed_for_date_closure_and_action(self):
        schema = self._schema("private-recruiter-conversion-outcome-v1.schema.json")
        source = json.loads((ROOT / "tests/fixtures/private-recruiter-conversion-outcome/screen-requested-en.json").read_text(encoding="utf-8"))
        mutations = []
        bad = copy.deepcopy(source); bad["event_date"] = "2026-02-30"; mutations.append(bad)
        bad = copy.deepcopy(source); bad["unexpected"] = True; mutations.append(bad)
        bad = copy.deepcopy(source); bad["next_safe_action"] = "record_stop_decision"; mutations.append(bad)
        for value in mutations:
            self.assertTrue(validate_schema_instance(value, schema), value)

    def test_semantic_validators_cover_all_private_fixtures(self):
        self.assertEqual([], validate_private_fixture_semantics(ROOT, as_of=dt.date(2026, 8, 9)))

    def test_triage_schema_uses_canonical_screen_opening_scope(self):
        schema = self._schema("private-recruiter-reply-triage-v1.schema.json")
        fixture = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json"
            ).read_text(encoding="utf-8")
        )
        canonical = copy.deepcopy(fixture)
        canonical["handoff"]["packet"]["prep_scope"] = "screen_opening"
        canonical["handoff"]["reentry_packet"]["prep_scope"] = "screen_opening"
        self.assertEqual([], validate_schema_instance(canonical, schema))

        for field in ("packet", "reentry_packet"):
            with self.subTest(field=field):
                removed_alias = copy.deepcopy(canonical)
                removed_alias["handoff"][field]["prep_scope"] = "recruiter_screen_opening"
                self.assertIn(
                    f"$.handoff.{field}.prep_scope: enum mismatch",
                    validate_schema_instance(removed_alias, schema),
                )

    def test_triage_v2_schema_accepts_independent_ui_and_content_locales(self):
        fixture = json.loads(
            (ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json").read_text(encoding="utf-8")
        )
        fixture["schema_version"] = "private-recruiter-reply-triage-v2"
        fixture["ui_locale"] = "en"
        fixture["content_locale"] = "es"
        del fixture["locale"]
        fixture["handoff"]["packet"]["source_snapshot"] = V2_READY_ES_SNAPSHOT
        fixture["handoff"]["reentry_packet"]["source_snapshot"] = V2_READY_ES_SNAPSHOT
        schema = self._schema("private-recruiter-reply-triage-v2.schema.json")
        self.assertEqual([], validate_triage(fixture))
        self.assertEqual([], validate_schema_instance(fixture, schema))

        missing = copy.deepcopy(fixture)
        del missing["content_locale"]
        self.assertTrue(validate_schema_instance(missing, schema))

    def test_triage_v2_snapshot_binding_rejects_content_drift(self):
        fixture = json.loads(
            (ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json").read_text(encoding="utf-8")
        )
        fixture["schema_version"] = "private-recruiter-reply-triage-v2"
        fixture["ui_locale"] = "en"
        fixture["content_locale"] = "es"
        del fixture["locale"]
        fixture["handoff"]["packet"]["source_snapshot"] = V2_READY_ES_SNAPSHOT
        fixture["handoff"]["reentry_packet"]["source_snapshot"] = V2_READY_ES_SNAPSHOT
        self.assertEqual([], validate_triage(fixture))
        changed = "A different safe summary with altered role constraints."
        fixture["safe_context"]["summary"] = changed
        fixture["handoff"]["packet"]["context_summary"] = changed
        fixture["handoff"]["reentry_packet"]["context_summary"] = changed
        self.assertTrue(validate_triage(fixture))

    def test_triage_identifier_patterns_require_json_strings_in_v1_and_v2(self):
        source = json.loads(
            (ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-en.json").read_text(encoding="utf-8")
        )
        versions = []
        v1 = (copy.deepcopy(source), self._schema("private-recruiter-reply-triage-v1.schema.json"))
        versions.append(v1)
        v2 = copy.deepcopy(source)
        v2["schema_version"] = "private-recruiter-reply-triage-v2"
        v2["ui_locale"] = "en"
        v2["content_locale"] = "es"
        del v2["locale"]
        versions.append((v2, self._schema("private-recruiter-reply-triage-v2.schema.json")))
        mutations = (
            ("facts", 0, "id"),
            ("question", "id"),
            ("question", "fact_ids", 0),
            ("handoff", "packet", "source_snapshot"),
            ("handoff", "packet", "fact_id"),
            ("handoff", "packet", "question_id"),
            ("handoff", "reentry_packet", "source_snapshot"),
            ("handoff", "reentry_packet", "fact_id"),
            ("handoff", "reentry_packet", "question_id"),
        )
        for version_index, (fixture, schema) in enumerate(versions):
            for path in mutations:
                with self.subTest(version=version_index, path=path):
                    mutated = copy.deepcopy(fixture)
                    target = mutated
                    for key in path[:-1]:
                        target = target[key]
                    target[path[-1]] = 123
                    self.assertTrue(validate_triage(mutated))
                    self.assertTrue(validate_schema_instance(mutated, schema))

    def test_practice_schema_binds_source_to_snapshot_prefix(self):
        schema = self._schema("recruiter-practice-session-v1.schema.json")
        fixture = json.loads((ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json").read_text(encoding="utf-8"))
        dossier_snapshot = copy.deepcopy(fixture)
        dossier_snapshot["handoff_context"]["source_snapshot"] = "snap-triage-001"
        self.assertTrue(validate_schema_instance(dossier_snapshot, schema), "dossier source must reject triage snapshot")
        triage_snapshot = copy.deepcopy(fixture)
        triage_snapshot["handoff_context"]["source"] = "private_recruiter_reply_triage"
        triage_snapshot["handoff_context"]["source_snapshot"] = "snap-dossier-001"
        triage_snapshot["handoff_context"].pop("claim_ids")
        triage_snapshot["handoff_context"].pop("evidence_ids")
        self.assertTrue(validate_schema_instance(triage_snapshot, schema), "triage source must reject dossier snapshot")
        triage_snapshot["handoff_context"]["source_snapshot"] = "snap-triage-001"
        self.assertEqual([], validate_schema_instance(triage_snapshot, schema))

    def test_practice_v2_schema_accepts_independent_ui_and_content_locales(self):
        fixture = json.loads(
            (ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json").read_text(encoding="utf-8")
        )
        fixture["schema_version"] = "recruiter-practice-session-v2"
        fixture["ui_locale"] = "en"
        fixture["content_locale"] = "es"
        del fixture["locale"]

        self.assertEqual([], validate_session(fixture))
        self.assertEqual(
            [],
            validate_schema_instance(
                fixture,
                self._schema("recruiter-practice-session-v2.schema.json"),
            ),
        )

    def test_practice_v2_accepts_triage_content_bound_snapshot_and_v1_rejects_it(self):
        fixture = json.loads(
            (ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json").read_text(encoding="utf-8")
        )
        fixture["schema_version"] = "recruiter-practice-session-v2"
        fixture["ui_locale"] = "en"
        fixture["content_locale"] = "es"
        del fixture["locale"]
        fixture["handoff_context"]["source"] = "private_recruiter_reply_triage"
        fixture["handoff_context"]["source_snapshot"] = V2_TRIAGE_PRACTICE_SNAPSHOT
        fixture["handoff_context"].pop("claim_ids")
        fixture["handoff_context"].pop("evidence_ids")
        schema = self._schema("recruiter-practice-session-v2.schema.json")
        self.assertEqual([], validate_session(fixture))
        self.assertEqual([], validate_schema_instance(fixture, schema))

        v1 = copy.deepcopy(fixture)
        v1["schema_version"] = "recruiter-practice-session-v1"
        v1["locale"] = "es"
        del v1["ui_locale"]
        del v1["content_locale"]
        self.assertTrue(validate_session(v1))
        self.assertTrue(validate_schema_instance(v1, self._schema("recruiter-practice-session-v1.schema.json")))

    def test_practice_question_rank_custom_validator_matches_schema_for_boolean_values(self):
        schema = self._schema("recruiter-practice-session-v1.schema.json")
        fixture = json.loads((ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json").read_text(encoding="utf-8"))
        for invalid_rank in (True, False):
            with self.subTest(question_rank=repr(invalid_rank)):
                mutated = copy.deepcopy(fixture)
                mutated["handoff_context"]["question_rank"] = invalid_rank
                self.assertTrue(validate_session(mutated))
                self.assertTrue(validate_schema_instance(mutated, schema))

        self.assertEqual([], validate_session(fixture))
        self.assertEqual([], validate_schema_instance(fixture, schema))

    def test_practice_question_rank_custom_validator_accepts_json_numeric_one(self):
        fixture = json.loads((ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json").read_text(encoding="utf-8"))
        fixture["handoff_context"]["question_rank"] = 1.0
        self.assertEqual([], validate_session(fixture))

    def test_schema_prose_mutations_match_custom_unicode_boundary(self):
        controls = ("\u200b", "\u202e", "\u2066", "\ufeff")
        cases = (
            (
                "private-recruiter-reply-triage-v1.schema.json",
                ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json",
                ("facts", 0, "summary"),
                validate_triage,
            ),
            (
                "recruiter-practice-session-v1.schema.json",
                ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json",
                ("facts", 0, "summary"),
                validate_session,
            ),
        )
        for schema_name, fixture_path, field_path, custom_validator in cases:
            schema = self._schema(schema_name)
            canonical = json.loads(fixture_path.read_text(encoding="utf-8"))
            self.assertEqual([], validate_schema_instance(canonical, schema))
            for control in controls:
                with self.subTest(schema=schema_name, code_point=f"U+{ord(control):04X}"):
                    mutated = copy.deepcopy(canonical)
                    target = mutated
                    for part in field_path[:-1]:
                        target = target[part]
                    target[field_path[-1]] = f"Safe prefix{control} hidden"
                    custom_errors = custom_validator(mutated)
                    schema_errors = validate_schema_instance(mutated, schema)
                    self.assertFalse(is_safe_prose_text(target[field_path[-1]]))
                    self.assertTrue(custom_errors)
                    self.assertTrue(schema_errors)
                    for error in custom_errors + schema_errors:
                        self.assertLess(len(error), 240)
                        self.assertNotIn(target[field_path[-1]], error)

    def test_dossier_schema_prose_mutations_match_custom_unicode_boundary(self):
        fixture = json.loads(
            (ROOT / "tests/fixtures/dossier-recruiter-practice-handoff/valid-es.json").read_text(
                encoding="utf-8"
            )
        )
        dossier = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/executive-career-dossier"
                / fixture["base_dossier_fixture"]
            ).read_text(encoding="utf-8")
        )
        dossier["screen_bridge"] = fixture["dossier_overrides"]["screen_bridge"]
        dossier["questions"][0]["linked_copy_category"] = fixture["dossier_overrides"]["question_linked_copy_category"]
        dossier["copy_blocks"][1].update(fixture["dossier_overrides"]["about_opening"])
        practice = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json"
            ).read_text(encoding="utf-8")
        )
        handoff = build_handoff(dossier, fixture["vacancy"], fixture["source_snapshot"])
        schema = self._schema("dossier-recruiter-practice-handoff-v1.schema.json")
        self.assertEqual([], validate_schema_instance(handoff, schema))
        for control in ("\u200b", "\u202e", "\u2066", "\ufeff"):
            with self.subTest(code_point=f"U+{ord(control):04X}"):
                mutated = copy.deepcopy(handoff)
                mutated["dossier_projection"]["fact_summary"] = f"Safe prefix{control} hidden"
                custom_errors = validate_handoff(mutated, dossier, fixture["vacancy"], practice)
                schema_errors = validate_schema_instance(mutated, schema)
                self.assertFalse(is_safe_prose_text(mutated["dossier_projection"]["fact_summary"]))
                self.assertTrue(custom_errors)
                self.assertTrue(schema_errors)
                for error in custom_errors + schema_errors:
                    self.assertLess(len(error), 240)
                    self.assertNotIn(mutated["dossier_projection"]["fact_summary"], error)

    def test_dossier_handoff_rejects_unlabelled_person_name_source_fact(self):
        fixture = json.loads(
            (ROOT / "tests/fixtures/dossier-recruiter-practice-handoff/valid-es.json").read_text(
                encoding="utf-8"
            )
        )
        dossier = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/executive-career-dossier"
                / fixture["base_dossier_fixture"]
            ).read_text(encoding="utf-8")
        )
        dossier["screen_bridge"] = fixture["dossier_overrides"]["screen_bridge"]
        dossier["questions"][0]["linked_copy_category"] = fixture["dossier_overrides"]["question_linked_copy_category"]
        dossier["copy_blocks"][1].update(fixture["dossier_overrides"]["about_opening"])
        handoff = build_handoff(dossier, fixture["vacancy"], fixture["source_snapshot"])
        practice = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json"
            ).read_text(encoding="utf-8")
        )
        target = "Ana López reports Terraform experience."
        mutated = copy.deepcopy(handoff)
        mutated["dossier_projection"]["fact_summary"] = target
        mutated["practice_projection"]["facts"][0]["summary"] = target
        custom_errors = validate_handoff(mutated, dossier, fixture["vacancy"], practice)
        schema_errors = validate_schema_instance(mutated, self._schema("dossier-recruiter-practice-handoff-v1.schema.json"))
        self.assertTrue(custom_errors)
        self.assertTrue(schema_errors)
        for error in custom_errors + schema_errors:
            self.assertLess(len(error), 240)
            self.assertNotIn(target, error)

    def test_handoff_pair_rejects_an_unrelated_shape_valid_projection(self):
        fixture = json.loads(
            (ROOT / "tests/fixtures/dossier-recruiter-practice-handoff/valid-es.json").read_text(
                encoding="utf-8"
            )
        )
        dossier = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/executive-career-dossier"
                / fixture["base_dossier_fixture"]
            ).read_text(encoding="utf-8")
        )
        dossier["screen_bridge"] = fixture["dossier_overrides"]["screen_bridge"]
        dossier["questions"][0]["linked_copy_category"] = fixture["dossier_overrides"]["question_linked_copy_category"]
        dossier["copy_blocks"][1].update(fixture["dossier_overrides"]["about_opening"])
        handoff = build_handoff(dossier, fixture["vacancy"], fixture["source_snapshot"])
        practice = json.loads(
            (
                ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json"
            ).read_text(encoding="utf-8")
        )

        unrelated = copy.deepcopy(handoff)
        projection = unrelated["practice_projection"]
        projection["handoff_context"].update(
            {
                "claim_ids": ["C-001"],
                "evidence_ids": ["E-001"],
            }
        )
        unrelated["dossier_projection"].update(
            {
                "claim_ids": ["C-001"],
                "evidence_ids": ["E-001"],
                "question_evidence_ids": ["E-001"],
                "source_fact_evidence_id": "E-001",
            }
        )
        practice.update(copy.deepcopy(projection))

        schema = self._schema("dossier-recruiter-practice-handoff-v1.schema.json")
        self.assertEqual([], validate_schema_instance(unrelated, schema))
        errors = validate_handoff(unrelated, dossier, fixture["vacancy"], practice)
        self.assertIn(
            "handoff.dossier_projection.claim_ids must match dossier source projection",
            errors,
        )
        self.assertIn(
            "handoff.practice_projection.handoff_context.claim_ids must match expected practice projection",
            errors,
        )

    def test_semantic_mutations_fail_closed_with_deterministic_errors(self):
        outcome = json.loads((ROOT / "tests/fixtures/private-recruiter-conversion-outcome/screen-requested-en.json").read_text(encoding="utf-8"))
        checkpoint = json.loads((ROOT / "tests/fixtures/private-recruiter-followthrough-checkpoint/accepted-en.json").read_text(encoding="utf-8"))
        receipt = outcome
        mutations = []
        bad = copy.deepcopy(outcome); bad["event_date"] = "2026-08-10"; mutations.append(("outcome", bad, "event_date"))
        bad = copy.deepcopy(checkpoint); bad["source_receipt"]["event_type"] = "stop_decision"; mutations.append(("checkpoint", bad, "source_receipt.event_type"))
        bad = copy.deepcopy(checkpoint); bad["delivery"]["external_actions_authorized"] = True; mutations.append(("checkpoint", bad, "delivery.external_actions_authorized"))
        bad = copy.deepcopy(outcome); bad["next_safe_action"] = "record_stop_decision"; mutations.append(("outcome", bad, "next_safe_action"))
        for kind, value, expected in mutations:
            if kind == "outcome":
                errors = validate_outcome_for_test(value, as_of=dt.date(2026, 8, 9))
            else:
                errors = validate_checkpoint_for_test(value, receipt, as_of=dt.date(2026, 8, 9))
            self.assertTrue(any(expected in error for error in errors), (kind, expected, errors))

    def test_dependency_free_checker_enforces_string_lengths_and_combinators(self):
        schema = {
            "type": "object",
            "properties": {
                "label": {"type": "string", "minLength": 2, "maxLength": 4},
                "mode": {
                    "oneOf": [{"const": "draft"}, {"const": "published"}],
                    "not": {"const": "blocked"},
                },
                "signal": {"anyOf": [{"const": "email"}, {"const": "screen"}]},
            },
            "required": ["label", "mode", "signal"],
        }
        self.assertEqual([], validate_schema_instance({"label": "ok", "mode": "draft", "signal": "email"}, schema))
        for value, expected in (
            ({"label": "x", "mode": "draft", "signal": "email"}, "string too short"),
            ({"label": "toolong", "mode": "draft", "signal": "email"}, "string too long"),
            ({"label": "ok", "mode": "other", "signal": "email"}, "oneOf mismatch"),
            ({"label": "ok", "mode": "blocked", "signal": "email"}, "not mismatch"),
            ({"label": "ok", "mode": "draft", "signal": "chat"}, "anyOf mismatch"),
        ):
            self.assertTrue(any(expected in error for error in validate_schema_instance(value, schema)), (value, expected))

    def test_dependency_free_checker_bounds_nested_combinator_evaluations(self):
        schema = {"const": "ok"}
        for _ in range(13):
            schema = {"oneOf": [schema, copy.deepcopy(schema)]}

        errors = validate_schema_instance("not-ok", schema)

        self.assertIn("schema validation exceeds safe evaluation limit", errors)

    def test_dependency_free_checker_bounds_cyclic_schema_references(self):
        schema = {"$defs": {}}
        schema["$defs"]["loop"] = {"$ref": "#/$defs/loop"}
        schema["$ref"] = "#/$defs/loop"

        errors = validate_schema_instance({}, schema)

        self.assertIn("schema validation exceeds safe evaluation limit", errors)

    def test_dependency_free_checker_rejects_missing_schema_references(self):
        errors = validate_schema_instance({}, {"$ref": "#/missing"})

        self.assertIn("schema reference is invalid", errors)

        errors = validate_schema_instance(
            {}, {"$defs": {"scalar": "not a schema"}, "$ref": "#/$defs/scalar"}
        )
        self.assertIn("schema reference is invalid", errors)

    def test_dependency_free_checker_rejects_non_object_combinator_branches(self):
        malformed_schemas = (
            {"oneOf": [None]},
            {"anyOf": ["invalid"]},
            {"allOf": [None]},
            {"if": None},
            {"not": None},
        )
        for schema in malformed_schemas:
            with self.subTest(schema=schema):
                errors = validate_schema_instance({}, schema)
                self.assertIn("schema branch is invalid", errors)

    def test_dependency_free_checker_rejects_malformed_keyword_shapes(self):
        malformed_schemas = (
            ({}, {"type": "object", "properties": None}),
            ({}, {"type": "object", "required": None}),
            ({}, {"enum": None}),
            (1, {"type": "number", "minimum": "a"}),
            ([1], {"type": "array", "minItems": "a"}),
        )
        for value, schema in malformed_schemas:
            with self.subTest(schema=schema):
                errors = validate_schema_instance(value, schema)
                self.assertIn("schema keyword is invalid", errors)

    def test_dependency_free_checker_rejects_invalid_regex_patterns(self):
        for pattern in ("[", "(?", r"\K"):
            with self.subTest(pattern=pattern):
                errors = validate_schema_instance("x", {"pattern": pattern})
                self.assertIn("schema pattern is invalid", errors)

    def test_dependency_free_checker_rejects_nested_unbounded_regex(self):
        errors = validate_schema_instance(
            "a" * 22 + "!", {"type": "string", "pattern": "(a+)+$"}
        )

        self.assertIn("schema pattern exceeds safe complexity limit", errors)

    def test_dependency_free_checker_rejects_cyclic_json_values_without_recursion_error(self):
        value = []
        value.append(value)

        errors = validate_schema_instance(value, {"const": value})

        self.assertEqual([], errors)

    def test_dependency_free_checker_enforces_numeric_and_array_bounds(self):
        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number", "minimum": 1, "maximum": 5},
                "fact_ids": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 2,
                    "uniqueItems": True,
                    "items": {"type": "string"},
                },
            },
            "required": ["score", "fact_ids"],
        }
        valid = {"score": 3.5, "fact_ids": ["F-1", "F-2"]}
        self.assertEqual([], validate_schema_instance(valid, schema))
        for value, expected in (
            ({"score": 0, "fact_ids": ["F-1"]}, "number below minimum"),
            ({"score": 6, "fact_ids": ["F-1"]}, "number above maximum"),
            ({"score": 3, "fact_ids": []}, "too few items"),
            ({"score": 3, "fact_ids": ["F-1", "F-2", "F-3"]}, "too many items"),
            ({"score": 3, "fact_ids": ["F-1", "F-1"]}, "duplicate items"),
        ):
            self.assertTrue(any(expected in error for error in validate_schema_instance(value, schema)), (value, expected))

    def test_dependency_free_checker_rejects_non_finite_numbers_and_bounds(self):
        import math

        number_schema = {"type": "number", "minimum": 0, "maximum": 5}
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                self.assertTrue(validate_schema_instance(value, number_schema))
        for boundary in (math.nan, math.inf, -math.inf):
            with self.subTest(boundary=boundary):
                self.assertIn(
                    "schema keyword is invalid",
                    validate_schema_instance(3, {"type": "number", "minimum": boundary}),
                )

    def test_dependency_free_checker_enforces_strict_json_types_and_const(self):
        self.assertEqual(
            [], validate_schema_instance(1, {"type": "integer", "const": 1})
        )
        for value, schema in (
            (True, {"type": "integer", "const": 1}),
            (0, {"type": "boolean", "const": False}),
            (17, {"type": ["string", "null"]}),
        ):
            with self.subTest(value=value, schema=schema):
                self.assertTrue(validate_schema_instance(value, schema))

        for value in (None, "x"):
            with self.subTest(value=value):
                self.assertEqual(
                    [], validate_schema_instance(value, {"type": ["string", "null"]})
                )

    def test_dependency_free_checker_applies_pattern_only_to_strings(self):
        nullable_pattern = {"type": ["string", "null"], "pattern": "^CAP-[0-9]{3}$"}
        self.assertEqual([], validate_schema_instance(None, nullable_pattern))
        self.assertEqual([], validate_schema_instance("CAP-001", nullable_pattern))
        self.assertTrue(
            any(
                "pattern mismatch" in error
                for error in validate_schema_instance("E-001", nullable_pattern)
            )
        )

    def test_dependency_free_checker_uses_json_schema_pattern_search_semantics(self):
        self.assertEqual(
            [],
            validate_schema_instance(
                "prefix-abc-suffix", {"type": "string", "pattern": "abc"}
            ),
        )
        self.assertTrue(
            any(
                "pattern mismatch" in error
                for error in validate_schema_instance(
                    "prefix-CAP-001-suffix",
                    {"type": "string", "pattern": "^CAP-[0-9]{3}$"},
                )
            )
        )
        string_only_pattern = {"type": "string", "pattern": "^CAP-[0-9]{3}$"}
        self.assertTrue(
            any(
                "type mismatch" in error
                for error in validate_schema_instance(None, string_only_pattern)
            )
        )

        schema = self._schema("executive-career-dossier-v1.schema.json")
        dossier = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/executive-career-dossier/scenario-a-es.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual([], validate_schema_instance(dossier, schema))

    def test_dependency_free_checker_enforces_contains_and_if_then_else(self):
        schema = {
            "type": "object",
            "properties": {
                "kind": {"type": "string"},
                "tags": {
                    "type": "array",
                    "contains": {"const": "priority"},
                },
                "note": {"type": "string"},
            },
            "required": ["kind", "tags", "note"],
            "if": {"properties": {"kind": {"const": "urgent"}}},
            "then": {"properties": {"note": {"const": "escalate"}}},
            "else": {"properties": {"note": {"const": "queue"}}},
        }
        self.assertEqual([], validate_schema_instance({"kind": "urgent", "tags": ["normal", "priority"], "note": "escalate"}, schema))
        self.assertEqual([], validate_schema_instance({"kind": "normal", "tags": ["priority"], "note": "queue"}, schema))
        for value, expected in (
            ({"kind": "urgent", "tags": ["normal"], "note": "escalate"}, "contains mismatch"),
            ({"kind": "urgent", "tags": ["priority"], "note": "queue"}, "const mismatch"),
            ({"kind": "normal", "tags": ["priority"], "note": "escalate"}, "const mismatch"),
        ):
            self.assertTrue(any(expected in error for error in validate_schema_instance(value, schema)), (value, expected))


if __name__ == "__main__":
    unittest.main()
