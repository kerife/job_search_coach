import copy
import datetime as dt
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "validate_private_recruiter_followthrough_checkpoint.py"
SCHEMA = ROOT / "schemas" / "private-recruiter-followthrough-checkpoint-v1.schema.json"
OUTCOME_SCRIPT = ROOT / "scripts" / "validate_private_recruiter_conversion_outcome.py"
FIXTURES = ROOT / "tests" / "fixtures" / "private-recruiter-conversion-outcome"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checkpoint = _load(SCRIPT, "checkpoint_validator")
outcome = _load(OUTCOME_SCRIPT, "outcome_validator")


class FollowthroughCheckpointContractTests(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads((FIXTURES / "screen-requested-en.json").read_text())
        self.valid = {
            "schema_version": "private-recruiter-followthrough-checkpoint-v1",
            "artifact_kind": "private_recruiter_followthrough_checkpoint",
            "locale": "en",
            "source_receipt": {"id": "D-104", "source_version": "draft-v1", "event_type": "screen_requested"},
            "action_state": "accepted",
            "observed_date": "2026-08-08",
            "next_measurement_event": "unknown",
            "next_safe_action": "manual_reenter_private_prep",
            "delivery": {
                "draft_only": True,
                "external_actions_authorized": False,
                "no_message_action": True,
                "no_calendar_action": True,
                "raw_event_retained": False,
                "local_save_mode": "disabled",
            },
        }

    def test_invalid_utf8_input_is_reported_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_bytes(b"\xff")

            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPT),
                    str(path),
                    "--receipt",
                    str(FIXTURES / "screen-requested-en.json"),
                    "--as-of",
                    "2026-08-08",
                ],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stderr, "checkpoint input is not valid JSON\n")
        self.assertNotIn("Traceback", result.stderr)

    def test_valid_en_and_es_and_all_mapping_branches(self):
        for state, event, action in [
            ("accepted", "unknown", "manual_reenter_private_prep"),
            ("deferred", "unknown", "clarify_context_before_reply"),
            ("declined", "unknown", "record_stop_decision"),
            ("completed", "screen_prepared", "route_to_prepare-role-interviews"),
            ("completed", "interview_requested", "route_to_prepare-role-interviews"),
            ("completed", "stop_decision", "record_stop_decision"),
            ("completed", "screen_attended", "debrief_after_screen"),
        ]:
            item = copy.deepcopy(self.valid)
            item.update(action_state=state, next_measurement_event=event, next_safe_action=action)
            item["locale"] = "es" if state in {"deferred", "completed"} else "en"
            if event == "screen_attended":
                item["target_binding"] = {"target_id": "T-001", "source_gate_snapshot": "snap-shortlist-sha256-" + "0" * 64}
            receipt = copy.deepcopy(self.receipt)
            receipt["locale"] = item["locale"]
            self.assertEqual([], checkpoint.validate_checkpoint(item, receipt, as_of=dt.date(2026, 8, 8)), (state, event))

    def test_attended_screen_requires_requested_screen_receipt_and_matching_locale(self):
        for filename in ("contact-received-en.json", "reply-received-en.json", "referral-received-es.json"):
            receipt = json.loads((FIXTURES / filename).read_text())
            item = copy.deepcopy(self.valid)
            item.update(action_state="completed", next_measurement_event="screen_attended", next_safe_action="debrief_after_screen")
            item["target_binding"] = {"target_id": "T-001", "source_gate_snapshot": "snap-shortlist-sha256-" + "0" * 64}
            item["source_receipt"] = {
                "id": receipt["source_artifact_id"],
                "source_version": receipt["source_version"],
                "event_type": receipt["event_type"],
            }
            item["locale"] = receipt["locale"]
            errors = checkpoint.validate_checkpoint(item, receipt, as_of=dt.date(2026, 8, 8))
            self.assertTrue(any("screen_attended" in error for error in errors), filename)

        receipt = copy.deepcopy(self.receipt)
        item = copy.deepcopy(self.valid)
        item.update(action_state="completed", next_measurement_event="screen_attended", next_safe_action="debrief_after_screen")
        item["target_binding"] = {"target_id": "T-001", "source_gate_snapshot": "snap-shortlist-sha256-" + "0" * 64}
        item["locale"] = "es"
        errors = checkpoint.validate_checkpoint(item, receipt, as_of=dt.date(2026, 8, 8))
        self.assertIn("locale does not match receipt", errors)

    def test_completed_screen_prepared_branch(self):
        item = copy.deepcopy(self.valid)
        item.update(action_state="completed", next_measurement_event="screen_prepared", next_safe_action="route_to_prepare-role-interviews")
        self.assertEqual([], checkpoint.validate_checkpoint(item, self.receipt, as_of=dt.date(2026, 8, 8)))

    def test_replay_fingerprint_is_stable_and_changes_when_pair_semantics_change(self):
        first = checkpoint.replay_fingerprint(self.valid, self.receipt)
        second = checkpoint.replay_fingerprint(copy.deepcopy(self.valid), copy.deepcopy(self.receipt))
        self.assertRegex(first, r"^replay-sha256-[0-9a-f]{64}$")
        self.assertEqual(first, second)

        changed_checkpoint = copy.deepcopy(self.valid)
        changed_checkpoint["action_state"] = "deferred"
        changed_checkpoint["next_safe_action"] = "clarify_context_before_reply"
        self.assertNotEqual(first, checkpoint.replay_fingerprint(changed_checkpoint, self.receipt))

        changed_receipt = copy.deepcopy(self.receipt)
        changed_receipt["source_version"] = "draft-v2"
        self.assertNotEqual(first, checkpoint.replay_fingerprint(self.valid, changed_receipt))

    def test_symlink_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.json"
            link = Path(directory) / "link.json"
            target.write_text(json.dumps(self.valid), encoding="utf-8")
            link.symlink_to(target)
            with self.assertRaises(checkpoint.CheckpointLoadError):
                checkpoint.load_checkpoint(link)

    def test_checkpoint_and_receipt_loaders_reject_depth_over_12(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            deep = json.dumps({"x": [[[[[[[[[[[[[1]]]]]]]]]]]]]})
            checkpoint_path = root / "checkpoint.json"
            receipt_path = root / "receipt.json"
            checkpoint_path.write_text(deep, encoding="utf-8")
            receipt_path.write_text(deep, encoding="utf-8")
            with self.assertRaises(checkpoint.CheckpointLoadError):
                checkpoint.load_checkpoint(checkpoint_path)
            with self.assertRaises(checkpoint.CheckpointLoadError):
                checkpoint.load_receipt(receipt_path)

    def test_receipt_is_required_and_validated_first(self):
        self.assertTrue(any("receipt" in e for e in checkpoint.validate_checkpoint(self.valid, None, as_of=dt.date(2026, 8, 8))))
        bad = copy.deepcopy(self.receipt)
        bad["next_safe_action"] = "record_stop_decision"
        self.assertTrue(any("receipt" in e for e in checkpoint.validate_checkpoint(self.valid, bad, as_of=dt.date(2026, 8, 8))))

    def test_source_receipt_must_match_exactly(self):
        for key, value in (("id", "D-999"), ("source_version", "other-v1"), ("event_type", "stop_decision")):
            item = copy.deepcopy(self.valid); item["source_receipt"][key] = value
            self.assertTrue(any("source_receipt" in e for e in checkpoint.validate_checkpoint(item, self.receipt, as_of=dt.date(2026, 8, 8))))

    def test_dates_and_as_of_are_strict(self):
        for field, value in (("observed_date", "2026-02-30"), ("observed_date", "2026-08-09"), ("observed_date", "not-date")):
            item = copy.deepcopy(self.valid); item[field] = value
            self.assertTrue(any("date" in e for e in checkpoint.validate_checkpoint(item, self.receipt, as_of=dt.date(2026, 8, 8))))

    def test_chronology_and_noncompleted_event_boundaries(self):
        item = copy.deepcopy(self.valid); item["observed_date"] = "2026-08-07"
        self.assertTrue(any("receipt date" in e for e in checkpoint.validate_checkpoint(item, self.receipt, as_of=dt.date(2026, 8, 8))))
        for state in ("accepted", "deferred", "declined"):
            item = copy.deepcopy(self.valid); item.update(action_state=state, next_measurement_event="screen_prepared")
            item["next_safe_action"] = {"accepted": "manual_reenter_private_prep", "deferred": "clarify_context_before_reply", "declined": "record_stop_decision"}[state]
            self.assertTrue(any("unknown" in e for e in checkpoint.validate_checkpoint(item, self.receipt, as_of=dt.date(2026, 8, 8))))

    def test_source_stop_event_is_only_compatible_with_terminal_states(self):
        receipt = copy.deepcopy(self.receipt); receipt["event_type"] = "stop_decision"; receipt["next_safe_action"] = "record_stop_decision"
        for state in ("accepted", "deferred"):
            item = copy.deepcopy(self.valid); item["source_receipt"]["event_type"] = "stop_decision"
            self.assertTrue(any("stop" in e for e in checkpoint.validate_checkpoint(item, receipt, as_of=dt.date(2026, 8, 8))))

    def test_stop_receipt_precedes_preparation_action_and_measurement(self):
        receipt = json.loads((FIXTURES / "stop-decision-en.json").read_text())
        item = copy.deepcopy(self.valid)
        item["source_receipt"] = {
            "id": receipt["source_artifact_id"],
            "source_version": receipt["source_version"],
            "event_type": receipt["event_type"],
        }
        item.update(action_state="completed", next_measurement_event="screen_prepared", next_safe_action="route_to_prepare-role-interviews")
        errors = checkpoint.validate_checkpoint(item, receipt, as_of=dt.date(2026, 8, 8))
        self.assertTrue(any("record_stop_decision" in error for error in errors))
        self.assertTrue(any("preparation" in error for error in errors))

    def test_stop_receipt_accepts_terminal_record_action(self):
        receipt = json.loads((FIXTURES / "stop-decision-en.json").read_text())
        item = copy.deepcopy(self.valid)
        item["source_receipt"] = {
            "id": receipt["source_artifact_id"],
            "source_version": receipt["source_version"],
            "event_type": receipt["event_type"],
        }
        item.update(action_state="completed", next_measurement_event="stop_decision", next_safe_action="record_stop_decision")
        self.assertEqual([], checkpoint.validate_checkpoint(item, receipt, as_of=dt.date(2026, 8, 8)))

    def test_closed_types_and_forbidden_content(self):
        for key, value in [("extra", True), ("source_receipt", "D-104"), ("candidate_id", "C-001"), ("raw_event", "raw"), ("answer", "send this"), ("outcome", "guaranteed offer"), ("score", 99)]:
            item = copy.deepcopy(self.valid); item[key] = value
            self.assertTrue(checkpoint.validate_checkpoint(item, self.receipt, as_of=dt.date(2026, 8, 8)), key)

    def test_closed_diagnostics_redact_suspicious_unknown_keys(self):
        for key in ("person@example.invalid", "/Users/synthetic/private-case.json", "token_sk_live_SYNTHETIC"):
            item = copy.deepcopy(self.valid); item[key] = True
            errors = checkpoint.validate_checkpoint(item, self.receipt, as_of=dt.date(2026, 8, 8))
            rendered = "\n".join(errors)
            self.assertIn("checkpoint has unsupported fields", rendered)
            self.assertIn("<redacted-field>", rendered)
            self.assertNotIn(key, rendered)

    def test_delivery_is_immutable(self):
        for key, value in [("draft_only", False), ("external_actions_authorized", True), ("no_message_action", False), ("no_calendar_action", False), ("raw_event_retained", True), ("local_save_mode", "enabled")]:
            item = copy.deepcopy(self.valid); item["delivery"][key] = value
            self.assertTrue(any("delivery" in e for e in checkpoint.validate_checkpoint(item, self.receipt, as_of=dt.date(2026, 8, 8))), key)

        for key, value in (("draft_only", 1), ("external_actions_authorized", 0),
                           ("no_message_action", 0), ("no_calendar_action", 0),
                           ("raw_event_retained", 0)):
            item = copy.deepcopy(self.valid); item["delivery"][key] = value
            self.assertTrue(any("delivery" in e for e in checkpoint.validate_checkpoint(item, self.receipt, as_of=dt.date(2026, 8, 8))), key)

    def test_cli_normalizes_parse_errors_and_preserves_help(self):
        item_path = ROOT / "tests/fixtures/private-recruiter-followthrough-checkpoint/accepted-en.json"
        receipt_path = FIXTURES / "screen-requested-en.json"
        invalid = subprocess.run([sys.executable, "-B", str(SCRIPT), str(item_path), "--receipt", str(receipt_path), "--as-of", "bad"], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 3)
        self.assertNotIn("Traceback", invalid.stderr)
        missing = subprocess.run([sys.executable, "-B", str(SCRIPT), str(item_path), "--as-of", "2026-08-08"], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 3)
        help_result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)

    def test_cli_caps_many_unknown_field_diagnostics(self):
        item = copy.deepcopy(self.valid)
        item.update({f"unknown_field_{index:04d}_long": True for index in range(1200)})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unknown-fields.json"
            path.write_text(json.dumps(item), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPT),
                    str(path),
                    "--receipt",
                    str(FIXTURES / "screen-requested-en.json"),
                    "--as-of",
                    "2026-08-08",
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertLessEqual(len(result.stderr.encode("utf-8")), 16_384)
        self.assertIn("validation diagnostics truncated; additional errors omitted\n", result.stderr)
        self.assertNotIn("unknown_field_1199_long", result.stderr)

    def test_cli_preserves_short_diagnostic_output(self):
        item = copy.deepcopy(self.valid)
        item["extra"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "extra.json"
            path.write_text(json.dumps(item), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPT),
                    str(path),
                    "--receipt",
                    str(FIXTURES / "screen-requested-en.json"),
                    "--as-of",
                    "2026-08-08",
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "checkpoint has unsupported fields: extra\n")

    def test_locale_enum_rejects_non_string_json_values_without_crashing(self):
        for value in ({}, []):
            with self.subTest(value=value):
                item = copy.deepcopy(self.valid)
                item["locale"] = value
                errors = checkpoint.validate_checkpoint(item, self.receipt, as_of=dt.date(2026, 8, 8))
                self.assertTrue(any("locale has invalid value" in error for error in errors), value)

    def test_schema_declares_cross_field_action_invariants(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        branches = schema.get("allOf", [])
        self.assertGreaterEqual(len(branches), 7)
        serialized = json.dumps(branches, sort_keys=True)
        for state, action in (("accepted", "manual_reenter_private_prep"), ("deferred", "clarify_context_before_reply"), ("declined", "record_stop_decision"), ("completed", "route_to_prepare-role-interviews")):
            self.assertIn(state, serialized)
            self.assertIn(action, serialized)
        self.assertIn("debrief_after_screen", serialized)
        self.assertIn("unknown", serialized)

    def test_schema_dates_declare_format_date(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual("date", schema["properties"]["observed_date"]["format"])


if __name__ == "__main__":
    unittest.main()
