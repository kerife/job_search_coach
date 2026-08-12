import importlib.util
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


if __name__ == "__main__":
    unittest.main()
