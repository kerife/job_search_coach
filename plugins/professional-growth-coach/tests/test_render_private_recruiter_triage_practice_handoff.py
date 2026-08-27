"""Black-box coverage for rendering a closed triage-practice wrapper."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SCRIPT = SCRIPTS / "render_private_recruiter_triage_practice_handoff.py"
FIXTURES = ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage"
sys.path.insert(0, str(SCRIPTS))

from build_private_recruiter_triage_practice_handoff import build_handoff  # noqa: E402
from triage_snapshot import snapshot_for_triage  # noqa: E402


class PrivateRecruiterTriagePracticeHandoffRendererTests(unittest.TestCase):
    def _handoff(self, locale: str) -> dict[str, object]:
        triage = json.loads((FIXTURES / f"ready-{locale}.json").read_text(encoding="utf-8"))
        triage["schema_version"] = "private-recruiter-reply-triage-v2"
        triage["ui_locale"] = locale
        triage["content_locale"] = locale
        triage.pop("locale", None)
        snapshot = snapshot_for_triage(triage)
        triage["handoff"]["packet"]["source_snapshot"] = snapshot
        triage["handoff"]["reentry_packet"]["source_snapshot"] = snapshot
        return build_handoff(triage)

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-B", str(SCRIPT), *args], text=True, capture_output=True, check=False)

    def _write(self, directory: Path, name: str, value: object) -> Path:
        path = directory / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def test_valid_es_and_en_wrappers_render_static_delivery_status(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            for locale, status in (("es", "Borrador privado · Reingreso manual requerido"), ("en", "Private draft · Manual re-entry required")):
                with self.subTest(locale=locale):
                    source = self._write(directory, f"{locale}.json", self._handoff(locale))
                    output = directory / f"{locale}.html"
                    result = self._run(str(source), "--output", str(output))
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual({"artifact_type": "text/html", "schema_version": "private-recruiter-triage-practice-handoff-v1"}, json.loads(result.stdout))
                    rendered = output.read_text(encoding="utf-8")
                    self.assertIn(status, rendered)
                    self.assertNotIn("<form", rendered)
                    self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))

    def test_direct_session_render_does_not_gain_wrapper_status(self) -> None:
        from render_recruiter_practice_session import render_session_html

        session = self._handoff("en")["practice_session"]
        rendered = render_session_html(session)
        self.assertNotIn("Private draft · Manual re-entry required", rendered)
        with self.assertRaises(TypeError):
            render_session_html(session, handoff_delivery=self._handoff("en")["delivery"])

    def test_rejects_delivery_provenance_and_unsafe_prose_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            cases = []
            delivery = self._handoff("en")
            delivery["delivery"]["auto_start"] = True
            cases.append(delivery)
            provenance = self._handoff("en")
            provenance["practice_session"]["handoff_context"]["source_snapshot"] = "snap-triage-sha256-" + "0" * 64
            cases.append(provenance)
            unsafe = self._handoff("en")
            unsafe["practice_session"]["facts"][0]["summary"] = "RAW_REPLY_SENTINEL https://example.invalid"
            cases.append(unsafe)
            for index, value in enumerate(cases):
                source = self._write(directory, f"bad-{index}.json", value)
                output = directory / f"bad-{index}.html"
                result = self._run(str(source), "--output", str(output))
                self.assertEqual(2, result.returncode)
                self.assertEqual({"error": {"code": "validation_failed"}}, json.loads(result.stderr))
                self.assertNotIn("RAW_REPLY_SENTINEL", result.stderr)
                self.assertFalse(output.exists())

    def test_duplicate_deep_oversized_and_symlink_inputs_are_rejected_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            valid = self._write(directory, "valid.json", self._handoff("en"))
            duplicate = directory / "duplicate.json"
            duplicate.write_text('{"a": "RAW_REPLY_SENTINEL", "a": 2}', encoding="utf-8")
            deep = directory / "deep.json"
            deep.write_text("[" * 14 + "0" + "]" * 14, encoding="utf-8")
            oversized = directory / "oversized.json"
            oversized.write_bytes(b" " * 64_001)
            link = directory / "link.json"
            link.symlink_to(valid)
            for source in (duplicate, deep, oversized, link):
                result = self._run(str(source), "--output", str(directory / f"{source.stem}.html"))
                self.assertEqual(3, result.returncode)
                self.assertEqual({"error": {"code": "invalid_input"}}, json.loads(result.stderr))
                self.assertNotIn("RAW_REPLY_SENTINEL", result.stderr)

    def test_overwrite_requires_force_and_preserves_existing_content(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            source = self._write(directory, "handoff.json", self._handoff("en"))
            output = directory / "output.html"
            output.write_text("preserve", encoding="utf-8")
            blocked = self._run(str(source), "--output", str(output))
            self.assertEqual(3, blocked.returncode)
            self.assertEqual({"error": {"code": "output_exists"}}, json.loads(blocked.stderr))
            self.assertEqual("preserve", output.read_text(encoding="utf-8"))
            allowed = self._run(str(source), "--output", str(output), "--force")
            self.assertEqual(0, allowed.returncode, allowed.stderr)

    def test_unknown_arguments_are_redacted(self) -> None:
        result = self._run("--unknown", "RAW_REPLY_SENTINEL")
        self.assertEqual(3, result.returncode)
        self.assertEqual({"error": {"code": "invalid_arguments"}}, json.loads(result.stderr))
        self.assertNotIn("RAW_REPLY_SENTINEL", result.stderr)

    def test_parsed_but_invalid_wrapper_is_a_validation_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            source = self._write(directory, "invalid-wrapper.json", {"schema_version": "not-a-wrapper"})
            result = self._run(str(source), "--output", str(directory / "out.html"))
            self.assertEqual(2, result.returncode)
            self.assertEqual({"error": {"code": "validation_failed"}}, json.loads(result.stderr))
