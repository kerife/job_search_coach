import copy
import datetime as dt
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
from validate_dossier_recruiter_practice_handoff import validate_handoff
from private_prose_safety import is_safe_prose_text
from validate_private_recruiter_reply_triage import validate_triage
from validate_recruiter_practice_session import validate_session


V2_READY_ES_SNAPSHOT = (
    "snap-triage-sha256-"
    "74720a33a8bfc5e085767831e741b7cce97d45b1bb2d76b47d3ee203a2b5d6e8"
)


class PrivateSchemaConformanceTests(unittest.TestCase):
    def _schema(self, name):
        return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))

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
