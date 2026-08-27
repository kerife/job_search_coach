"""Black-box and library contracts for bounded private JSON loaders."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage"
PLUGIN_FIXTURES = ROOT / "tests" / "fixtures"
OVERSIZED_INTEGER_FIXTURE = PLUGIN_FIXTURES / "private-json" / "oversized-integer.json"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str):
    path = SCRIPTS / f"{name}.py"
    specification = importlib.util.spec_from_file_location(f"loader_hardening_{name}", path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


REPLY_TRIAGE = _load("validate_private_recruiter_reply_triage")
HANDOFF_BUILDER = _load("build_private_recruiter_triage_practice_handoff")
HANDOFF_VALIDATOR = _load("validate_private_recruiter_triage_practice_handoff")
CHECKPOINT = _load("validate_private_recruiter_followthrough_checkpoint")
PRACTICE = _load("validate_recruiter_practice_session")
DOSSIER_V1 = _load("validate_executive_career_dossier")
DOSSIER_V2 = _load("validate_executive_career_dossier_v2")


def _ready_triage() -> dict[str, object]:
    value = json.loads((FIXTURES / "ready-en.json").read_text(encoding="utf-8"))
    value["schema_version"] = "private-recruiter-reply-triage-v2"
    value["ui_locale"] = "en"
    value["content_locale"] = "en"
    del value["locale"]
    snapshot = HANDOFF_BUILDER.snapshot_for_triage(value)
    value["handoff"]["packet"]["source_snapshot"] = snapshot
    value["handoff"]["reentry_packet"]["source_snapshot"] = snapshot
    return value


class PrivateJsonLoaderHardeningTests(unittest.TestCase):
    PRIVATE_SENTINELS = ("RAW_PRIVATE_JSON_SENTINEL", "opaque-private-input")

    def _deep_json(self) -> str:
        nested: object = "RAW_PRIVATE_JSON_SENTINEL"
        for _ in range(13):
            nested = [nested]
        return json.dumps({"raw": "RAW_PRIVATE_JSON_SENTINEL", "nested": nested})

    def _oversized_integer_json(self) -> str:
        maximum = getattr(sys, "get_int_max_str_digits", lambda: 640)()
        fixture = OVERSIZED_INTEGER_FIXTURE.read_text(encoding="utf-8")
        if maximum <= 0 or len(fixture.split('"integer":', 1)[1].split(",", 1)[0]) > maximum:
            return fixture
        return '{"integer":' + ("9" * (max(maximum, 640) + 1)) + ',"raw":"RAW_PRIVATE_JSON_SENTINEL"}'

    def _write(self, directory: Path, name: str, raw: str) -> Path:
        path = directory / name
        path.write_text(raw, encoding="utf-8")
        return path

    def _private_loader_cases(self, directory: Path) -> dict[str, Path]:
        """Return deliberately unsafe files without making their contents public."""
        sentinel = "RAW_PRIVATE_JSON_SENTINEL"
        duplicate = self._write(
            directory,
            "duplicate.json",
            '{"raw":"' + sentinel + '","raw":"second"}',
        )
        target = self._write(directory, "target.json", '{"raw":"' + sentinel + '"}')
        symlink = directory / "symlink.json"
        symlink.symlink_to(target)
        oversized = directory / "oversized.json"
        oversized.write_bytes((b" " * 64_000) + sentinel.encode("ascii"))
        invalid_utf8 = directory / "invalid-utf8.json"
        invalid_utf8.write_bytes(b'{"raw":"' + sentinel.encode("ascii") + b'"}\xff')
        return {
            "duplicate": duplicate,
            "symlink": symlink,
            "oversized": oversized,
            "invalid_utf8": invalid_utf8,
        }

    def _loaders(self):
        return (
            (REPLY_TRIAGE.load_triage, REPLY_TRIAGE.TriageLoadError),
            (HANDOFF_BUILDER.load_triage, HANDOFF_BUILDER.TriageInputError),
            (HANDOFF_VALIDATOR.load_handoff, HANDOFF_VALIDATOR.HandoffLoadError),
            (CHECKPOINT.load_checkpoint, CHECKPOINT.CheckpointLoadError),
            (PRACTICE.load_session, PRACTICE.SessionLoadError),
            (DOSSIER_V1.load_dossier, DOSSIER_V1.DossierLoadError),
            (DOSSIER_V2.load_dossier, DOSSIER_V2.DossierLoadError),
        )

    def _commands(self):
        return (
            (SCRIPTS / "validate_private_recruiter_reply_triage.py", lambda path, directory: [str(path)]),
            (SCRIPTS / "build_private_recruiter_triage_practice_handoff.py", lambda path, directory: ["--input", str(path), "--output", str(directory / "handoff.json")]),
            (SCRIPTS / "validate_private_recruiter_triage_practice_handoff.py", lambda path, directory: [str(path)]),
            (SCRIPTS / "validate_private_recruiter_followthrough_checkpoint.py", lambda path, directory: [str(path), "--receipt", str(path), "--as-of", "2026-08-27"]),
            (SCRIPTS / "validate_recruiter_practice_session.py", lambda path, directory: [str(path)]),
            (SCRIPTS / "validate_executive_career_dossier.py", lambda path, directory: [str(path)]),
            (SCRIPTS / "validate_executive_career_dossier_v2.py", lambda path, directory: [str(path)]),
        )

    def test_new_validator_fixtures_remain_loadable(self) -> None:
        session_path = ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json"
        dossier_v1_path = ROOT.parent.parent / "tests/evals/with-skill/fixtures/executive-career-dossier/scenario-c-en.json"
        dossier_v2_path = ROOT.parent.parent / "tests/evals/with-skill/fixtures/executive-career-dossier-v2/scenario-c-en.json"
        checkpoint_path = PLUGIN_FIXTURES / "private-recruiter-followthrough-checkpoint/accepted-en.json"
        receipt_path = PLUGIN_FIXTURES / "private-recruiter-conversion-outcome/screen-requested-en.json"
        self.assertIsInstance(PRACTICE.load_session(session_path), dict)
        self.assertIsInstance(DOSSIER_V1.load_dossier(dossier_v1_path), dict)
        self.assertIsInstance(DOSSIER_V2.load_dossier(dossier_v2_path), dict)
        self.assertIsInstance(CHECKPOINT.load_checkpoint(checkpoint_path), dict)
        self.assertIsInstance(CHECKPOINT.load_receipt(receipt_path), dict)

    def test_valid_fixtures_remain_loadable(self) -> None:
        triage = _ready_triage()
        handoff = HANDOFF_BUILDER.build_handoff(triage)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            triage_path = self._write(directory, "triage.json", json.dumps(triage))
            handoff_path = self._write(directory, "handoff.json", json.dumps(handoff))

            self.assertEqual(triage, REPLY_TRIAGE.load_triage(triage_path))
            self.assertEqual(triage, HANDOFF_BUILDER.load_triage(triage_path))
            self.assertEqual(handoff, HANDOFF_VALIDATOR.load_handoff(handoff_path))

    def test_library_loaders_map_oversized_integer_to_typed_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self._write(Path(temporary), "integer.json", self._oversized_integer_json())
            for loader, error_type in self._loaders():
                with self.subTest(loader=loader.__module__):
                    with self.assertRaises(error_type) as raised:
                        loader(path)
                    for sentinel in self.PRIVATE_SENTINELS:
                        self.assertNotIn(sentinel, str(raised.exception))

    def test_library_loaders_reject_excessive_depth_with_typed_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self._write(Path(temporary), "deep.json", self._deep_json())
            for loader, error_type in self._loaders():
                with self.subTest(loader=loader.__module__):
                    with self.assertRaises(error_type) as raised:
                        loader(path)
                    self.assertNotIn("RAW_PRIVATE_JSON_SENTINEL", str(raised.exception))

    def test_cli_loaders_reject_extreme_json_without_traceback_or_echo(self) -> None:
        payloads = (("integer", self._oversized_integer_json()), ("deep", self._deep_json()))
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for label, raw in payloads:
                path = self._write(directory, f"{label}.json", raw)
                for script, arguments in self._commands():
                    with self.subTest(payload=label, script=script.name):
                        result = subprocess.run(
                            [sys.executable, "-B", str(script), *arguments(path, directory)],
                            text=True,
                            capture_output=True,
                            check=False,
                        )
                        self.assertEqual(3, result.returncode, result.stderr)
                        self.assertEqual("", result.stdout)
                        self.assertNotIn("Traceback", result.stderr)
                        for sentinel in self.PRIVATE_SENTINELS:
                            self.assertNotIn(sentinel, result.stderr)

    def test_every_loader_rejects_common_private_boundary_cases_without_echo(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for label, path in self._private_loader_cases(directory).items():
                for loader, error_type in self._loaders():
                    with self.subTest(case=label, loader=loader.__module__):
                        with self.assertRaises(error_type) as raised:
                            loader(path)
                        rendered = str(raised.exception)
                        for sentinel in self.PRIVATE_SENTINELS:
                            self.assertNotIn(sentinel, rendered)
                        self.assertNotIn(str(path), rendered)

    def test_every_cli_rejects_common_private_boundary_cases_opaquely(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for label, path in self._private_loader_cases(directory).items():
                for script, arguments in self._commands():
                    with self.subTest(case=label, script=script.name):
                        result = subprocess.run(
                            [sys.executable, "-B", str(script), *arguments(path, directory)],
                            text=True,
                            capture_output=True,
                            check=False,
                        )
                        self.assertEqual(3, result.returncode, result.stderr)
                        self.assertEqual("", result.stdout)
                        self.assertNotIn("Traceback", result.stderr)
                        for sentinel in self.PRIVATE_SENTINELS:
                            self.assertNotIn(sentinel, result.stderr)
                        self.assertNotIn(str(path), result.stderr)


if __name__ == "__main__":
    unittest.main()
