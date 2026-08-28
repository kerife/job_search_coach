"""Black-box contract tests for the private triage-to-practice CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_private_recruiter_triage_practice_handoff.py"
FIXTURES = (
    ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage"
)
sys.path.insert(0, str(ROOT / "scripts"))

from triage_snapshot import snapshot_for_triage  # noqa: E402


class PrivateRecruiterTriagePracticeHandoffCliTests(unittest.TestCase):
    def _ready_triage(self, locale: str) -> dict[str, object]:
        value = json.loads((FIXTURES / f"ready-{locale}.json").read_text(encoding="utf-8"))
        value["schema_version"] = "private-recruiter-reply-triage-v2"
        value["ui_locale"] = locale
        value["content_locale"] = locale
        del value["locale"]
        snapshot = snapshot_for_triage(value)
        value["handoff"]["packet"]["source_snapshot"] = snapshot
        value["handoff"]["reentry_packet"]["source_snapshot"] = snapshot
        return value

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=False,
            text=True,
            capture_output=True,
        )

    def _write_json(self, directory: Path, name: str, value: object) -> Path:
        path = directory / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def _error(self, result: subprocess.CompletedProcess[str]) -> dict[str, object]:
        self.assertEqual("", result.stdout)
        return json.loads(result.stderr)

    def test_writes_canonical_valid_handoffs_for_es_and_en(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for locale in ("es", "en"):
                with self.subTest(locale=locale):
                    source = self._write_json(directory, f"triage-{locale}.json", self._ready_triage(locale))
                    output = directory / f"handoff-{locale}.json"

                    result = self._run("--input", str(source), "--output", str(output))

                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual("", result.stderr)
                    self.assertEqual(
                        {"artifact_kind": "private_recruiter_triage_practice_handoff", "schema_version": "private-recruiter-triage-practice-handoff-v2"},
                        json.loads(result.stdout),
                    )
                    encoded = output.read_bytes()
                    self.assertTrue(encoded.endswith(b"\n"))
                    self.assertEqual(encoded, json.dumps(json.loads(encoded), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")

    def test_rejects_malformed_and_duplicate_json_without_echoing_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            cases = {
                "malformed": '{"unsafe":"RAW_REPLY_SENTINEL"',
                "duplicate": '{"schema_version":"a","schema_version":"b","raw":"RAW_REPLY_SENTINEL"}',
            }
            for label, raw in cases.items():
                with self.subTest(label=label):
                    source = directory / f"{label}.json"
                    source.write_text(raw, encoding="utf-8")
                    result = self._run("--input", str(source), "--output", str(directory / f"{label}-out.json"))
                    error = self._error(result)
                    self.assertEqual(3, result.returncode)
                    self.assertEqual("invalid_input", error["error"]["code"])
                    self.assertNotIn("RAW_REPLY_SENTINEL", result.stderr)

    def test_rejects_symlink_and_oversized_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._write_json(directory, "source.json", self._ready_triage("en"))
            link = directory / "link.json"
            link.symlink_to(source)
            oversized = directory / "oversized.json"
            oversized.write_bytes(b" " * 64_001)
            for label, input_path in (("symlink", link), ("oversized", oversized)):
                with self.subTest(label=label):
                    result = self._run("--input", str(input_path), "--output", str(directory / f"{label}-out.json"))
                    error = self._error(result)
                    self.assertEqual(3, result.returncode)
                    self.assertEqual("invalid_input", error["error"]["code"])

    def test_rejects_v1_and_does_not_create_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "v1.json"
            source.write_text((FIXTURES / "ready-es.json").read_text(encoding="utf-8"), encoding="utf-8")
            output = directory / "handoff.json"

            result = self._run("--input", str(source), "--output", str(output))

            error = self._error(result)
            self.assertEqual(2, result.returncode)
            self.assertEqual("validation_failed", error["error"]["code"])
            self.assertFalse(output.exists())

    def test_rejects_unsafe_output_target_and_preserves_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._write_json(directory, "triage.json", self._ready_triage("es"))
            protected = directory / "protected.json"
            protected.write_text("preserve", encoding="utf-8")
            output = directory / "handoff.json"
            output.symlink_to(protected)

            result = self._run("--input", str(source), "--output", str(output))

            error = self._error(result)
            self.assertEqual(3, result.returncode)
            self.assertEqual("unsafe_output", error["error"]["code"])
            self.assertEqual("preserve", protected.read_text(encoding="utf-8"))

    def test_requires_force_to_overwrite_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._write_json(directory, "triage.json", self._ready_triage("en"))
            output = directory / "handoff.json"
            output.write_text("existing", encoding="utf-8")

            blocked = self._run("--input", str(source), "--output", str(output))
            error = self._error(blocked)
            self.assertEqual(3, blocked.returncode)
            self.assertEqual("output_exists", error["error"]["code"])
            self.assertEqual("existing", output.read_text(encoding="utf-8"))

            allowed = self._run("--input", str(source), "--output", str(output), "--force")
            self.assertEqual(0, allowed.returncode, allowed.stderr)
            self.assertEqual("private-recruiter-triage-practice-handoff-v2", json.loads(output.read_text(encoding="utf-8"))["schema_version"])

    def test_rejects_unknown_arguments_without_reflecting_supplied_prose(self) -> None:
        result = self._run("--unknown", "RAW_REPLY_SENTINEL")

        error = self._error(result)
        self.assertEqual(3, result.returncode)
        self.assertEqual("invalid_arguments", error["error"]["code"])
        self.assertNotIn("RAW_REPLY_SENTINEL", result.stdout)
        self.assertNotIn("RAW_REPLY_SENTINEL", result.stderr)


if __name__ == "__main__":
    unittest.main()
