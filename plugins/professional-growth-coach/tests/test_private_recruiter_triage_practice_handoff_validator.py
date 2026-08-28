"""Contract tests for the standalone triage-practice handoff validator."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_private_recruiter_triage_practice_handoff import build_handoff  # noqa: E402
from triage_snapshot import snapshot_for_triage  # noqa: E402
from validate_private_recruiter_triage_practice_handoff import validate_handoff  # noqa: E402


def _ready_triage(locale: str) -> dict[str, object]:
    triage = json.loads((FIXTURES / f"ready-{locale}.json").read_text(encoding="utf-8"))
    triage["schema_version"] = "private-recruiter-reply-triage-v2"
    triage["ui_locale"] = locale
    triage["content_locale"] = locale
    del triage["locale"]
    snapshot = snapshot_for_triage(triage)
    triage["handoff"]["packet"]["source_snapshot"] = snapshot
    triage["handoff"]["reentry_packet"]["source_snapshot"] = snapshot
    return triage


class PrivateRecruiterTriagePracticeHandoffValidatorTests(unittest.TestCase):
    def _handoff(self, locale: str = "en") -> dict[str, object]:
        return build_handoff(_ready_triage(locale))

    def test_accepts_valid_es_and_en_handoffs(self) -> None:
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                self.assertEqual([], validate_handoff(self._handoff(locale)))

    def test_rejects_each_fixed_wrapper_invariant(self) -> None:
        mutations = {
            "source": lambda value: value.update({"source_artifact_kind": "other"}),
            "snapshot": lambda value: value.update({"source_snapshot": "snap-triage-sha256-" + "0" * 64}),
            "scope": lambda value: value.update({"prep_scope": "screen_opening" if value["prep_scope"] != "screen_opening" else "proof_example"}),
            "delivery": lambda value: value["delivery"].update({"auto_start": True}),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                value = copy.deepcopy(self._handoff())
                mutate(value)
                self.assertTrue(validate_handoff(value))

    def test_rejects_unsafe_prose_and_nested_projection_drift(self) -> None:
        unsafe = self._handoff()
        unsafe["practice_session"]["safe_context"]["summary"] = "Send a message to the recruiter now."
        self.assertTrue(validate_handoff(unsafe))

        drifted = self._handoff()
        drifted["practice_session"]["handoff_context"]["question_id"] = "Q-999"
        self.assertTrue(validate_handoff(drifted))

    def test_rejects_projected_prose_drift_when_source_snapshot_is_unchanged(self) -> None:
        handoff = self._handoff()
        self.assertRegex(handoff["projection_snapshot"], r"^snap-practice-sha256-[0-9a-f]{64}$")
        handoff["practice_session"]["facts"][0]["summary"] = "Verified migration outcome invented after handoff generation."
        errors = validate_handoff(handoff)
        self.assertIn("handoff.projection_snapshot must match practice_session content", errors)

    def test_accepts_legacy_v1_handoff_without_projection_snapshot(self) -> None:
        handoff = self._handoff()
        handoff["schema_version"] = "private-recruiter-triage-practice-handoff-v1"
        handoff.pop("projection_snapshot")
        self.assertEqual([], validate_handoff(handoff))

    def test_rejects_private_source_url_contact_and_path_prose_without_echoing_it(self) -> None:
        targets = {
            "safe_context.summary": ("safe_context", "summary"),
            "question.text": ("question", "text"),
            "facts[0].summary": ("facts", 0, "summary"),
        }
        sentinels = (
            "Read https://example.invalid/private before practice.",
            "Reply to person@example.invalid before practice.",
            "Read /private/tmp/private-note before practice.",
            "Review linkedin.com/in/private-profile before practice.",
            "Use api_key=private-value before practice.",
            "Use Bearer abc123 before practice.",
            "Authorization: Bearer abc123 before practice.",
        )
        for target_name, target_path in targets.items():
            for sentinel in sentinels:
                with self.subTest(target=target_name, sentinel_kind=sentinel.split()[1]):
                    value = copy.deepcopy(self._handoff())
                    target: object = value["practice_session"]
                    for segment in target_path[:-1]:
                        target = target[segment]  # type: ignore[index]
                    target[target_path[-1]] = sentinel  # type: ignore[index]
                    errors = validate_handoff(value)
                    self.assertTrue(errors)
                    self.assertNotIn(sentinel, "\n".join(errors))

    def test_cli_returns_zero_only_for_a_valid_wrapper(self) -> None:
        script = SCRIPTS / "validate_private_recruiter_triage_practice_handoff.py"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "handoff.json"
            path.write_text(json.dumps(self._handoff()), encoding="utf-8")
            valid = subprocess.run([sys.executable, str(script), str(path)], text=True, capture_output=True, check=False)
            self.assertEqual(0, valid.returncode)
            self.assertIn("valid private recruiter triage practice handoff", valid.stdout)

            path.write_text('{"schema_version":"wrong"}', encoding="utf-8")
            invalid = subprocess.run([sys.executable, str(script), str(path)], text=True, capture_output=True, check=False)
            self.assertEqual(2, invalid.returncode)
            self.assertNotIn("handoff.json", invalid.stderr)

    def test_cli_rejects_unknown_or_missing_arguments_without_usage_or_argument_echo(self) -> None:
        script = SCRIPTS / "validate_private_recruiter_triage_practice_handoff.py"
        private_sentinel = "--private-value=person@example.invalid"
        for label, arguments in (("unknown", [private_sentinel]), ("missing", [])):
            with self.subTest(label=label):
                result = subprocess.run(
                    [sys.executable, str(script), *arguments],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(3, result.returncode)
                self.assertEqual('{"error":{"code":"invalid_arguments"}}\n', result.stderr)
                self.assertEqual("", result.stdout)
                self.assertNotIn(private_sentinel, result.stderr)


if __name__ == "__main__":
    unittest.main()
