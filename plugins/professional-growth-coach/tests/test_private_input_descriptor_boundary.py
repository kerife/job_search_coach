import contextlib
import io
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


OUTCOME = _load("validate_private_recruiter_conversion_outcome")
CHECKPOINT = _load("validate_private_recruiter_followthrough_checkpoint")
TRIAGE = _load("validate_private_recruiter_reply_triage")
PRACTICE = _load("validate_recruiter_practice_session")
DOSSIER = _load("validate_executive_career_dossier")
PRIVATE_INPUT = _load("private_input_loader")


LOAD_CASES = (
    ("outcome", OUTCOME.load_outcome, ROOT / "tests/fixtures/private-recruiter-conversion-outcome/contact-received-en.json"),
    ("checkpoint", CHECKPOINT.load_checkpoint, ROOT / "tests/fixtures/private-recruiter-followthrough-checkpoint/accepted-en.json"),
    ("receipt", CHECKPOINT.load_receipt, ROOT / "tests/fixtures/private-recruiter-conversion-outcome/screen-requested-en.json"),
    ("triage", TRIAGE.load_triage, REPO / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage/clarify-en.json"),
    ("practice", PRACTICE.load_session, REPO / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json"),
    ("dossier", DOSSIER.load_dossier, REPO / "tests/evals/with-skill/fixtures/executive-career-dossier/scenario-c-en.json"),
)


def _decoder_recursion_fixture() -> str:
    return "[" * 1_000 + "0" + "]" * 1_000


# CPython 3.11 raises RecursionError while decoding this fixture, which is the
# regression this guard closes. Newer decoders can finish loading it, so the
# same bounded input then reaches each loader's existing depth/object check.
def _expected_decoder_or_post_decode_messages(
    decoder_message: str, *post_decode_messages: str
) -> frozenset[str]:
    try:
        json.loads(_decoder_recursion_fixture())
    except RecursionError:
        return frozenset((decoder_message,))
    return frozenset(post_decode_messages)


DIRECT_RECURSION_CASES = (
    (
        "outcome",
        OUTCOME.load_outcome,
        OUTCOME.OutcomeLoadError,
        _expected_decoder_or_post_decode_messages(
            "outcome input is not valid JSON", "outcome input nesting exceeds safe limit"
        ),
    ),
    (
        "checkpoint",
        CHECKPOINT.load_checkpoint,
        CHECKPOINT.CheckpointLoadError,
        _expected_decoder_or_post_decode_messages(
            "checkpoint input is not valid JSON",
            "checkpoint input nesting exceeds safe limit",
        ),
    ),
    (
        "receipt",
        CHECKPOINT.load_receipt,
        CHECKPOINT.CheckpointLoadError,
        _expected_decoder_or_post_decode_messages(
            "receipt input is not valid JSON", "checkpoint input nesting exceeds safe limit"
        ),
    ),
    (
        "triage",
        TRIAGE.load_triage,
        TRIAGE.TriageLoadError,
        _expected_decoder_or_post_decode_messages(
            "triage input is not valid JSON", "JSON nesting exceeds safe limit"
        ),
    ),
    (
        "practice",
        PRACTICE.load_session,
        PRACTICE.SessionLoadError,
        _expected_decoder_or_post_decode_messages(
            "session input is not valid JSON", "JSON nesting exceeds safe limit"
        ),
    ),
    (
        "dossier",
        DOSSIER.load_dossier,
        DOSSIER.DossierLoadError,
        _expected_decoder_or_post_decode_messages(
            "dossier must be valid UTF-8 JSON", "dossier must be a JSON object"
        ),
    ),
)


CLI_RECURSION_CASES = (
    (
        "outcome",
        OUTCOME._cli,
        ("{input}", "--as-of", "2026-08-13"),
        _expected_decoder_or_post_decode_messages(
            "outcome input is not valid JSON", "outcome input nesting exceeds safe limit"
        ),
        3,
    ),
    (
        "checkpoint",
        CHECKPOINT._cli,
        ("{input}", "--receipt", "{receipt}", "--as-of", "2026-08-13"),
        _expected_decoder_or_post_decode_messages(
            "checkpoint input is not valid JSON",
            "checkpoint input nesting exceeds safe limit",
        ),
        3,
    ),
    (
        "triage",
        TRIAGE._cli,
        ("{input}",),
        _expected_decoder_or_post_decode_messages(
            "triage input is not valid JSON", "JSON nesting exceeds safe limit"
        ),
        3,
    ),
    (
        "practice",
        PRACTICE._cli,
        ("{input}",),
        frozenset({"{\"error\":{\"code\":\"invalid_input\"}}"}),
        3,
    ),
    (
        "dossier",
        DOSSIER._cli,
        ("{input}",),
        _expected_decoder_or_post_decode_messages(
            "dossier must be valid UTF-8 JSON", "dossier must be a JSON object"
        ),
        2,
    ),
)


class PrivateInputDescriptorBoundaryTests(unittest.TestCase):
    def test_regular_file_parent_is_reported_as_safe_unavailable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent_file = root / "not-a-directory"
            parent_file.write_text("not a directory", encoding="utf-8")

            with self.assertRaises(PRIVATE_INPUT.PrivateInputError) as raised:
                PRIVATE_INPUT.read_bounded_bytes(
                    parent_file / "input.json", 256 * 1024
                )

            self.assertEqual(raised.exception.reason, "unavailable")

    def test_intermediate_parent_symlink_is_rejected_by_every_private_loader(self):
        for label, loader, fixture in LOAD_CASES:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                external = root / "external"
                alias = root / "alias"
                external.mkdir()
                target = external / "input.json"
                target.write_bytes(fixture.read_bytes())
                alias.symlink_to(external, target_is_directory=True)

                with self.assertRaises((OSError, ValueError)):
                    loader(alias / target.name)

    def test_regular_file_remains_accepted_by_every_private_loader(self):
        for label, loader, fixture in LOAD_CASES:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "input.json"
                path.write_bytes(fixture.read_bytes())
                self.assertIsInstance(loader(path), dict)

    def test_decoder_recursion_is_normalized_at_every_loader_boundary(self):
        for label, loader, error_type, messages in DIRECT_RECURSION_CASES:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "input.json"
                path.write_text(_decoder_recursion_fixture(), encoding="utf-8")

                with self.assertRaises(error_type) as raised:
                    loader(path)
                self.assertIn(str(raised.exception), messages)

    def test_cli_decoder_recursion_returns_safe_loader_error(self):
        for label, cli, argument_template, messages, exit_code in CLI_RECURSION_CASES:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                input_path = root / "input.json"
                receipt_path = root / "receipt.json"
                input_path.write_text(_decoder_recursion_fixture(), encoding="utf-8")
                receipt_path.write_text("{}", encoding="utf-8")
                arguments = tuple(
                    part.format(input=input_path, receipt=receipt_path)
                    for part in argument_template
                )
                stderr = io.StringIO()

                with contextlib.redirect_stderr(stderr):
                    result = cli(arguments)

                self.assertNotEqual(0, result)
                self.assertEqual(exit_code, result)
                self.assertIn(stderr.getvalue().rstrip("\n"), messages)
                self.assertEqual(1, stderr.getvalue().count("\n"))
                self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
