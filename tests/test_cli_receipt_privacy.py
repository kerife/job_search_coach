"""CLI receipts avoid disclosing local artifact paths unless explicitly requested."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
V1_DOSSIER = ROOT / "tests/evals/with-skill/fixtures/executive-career-dossier/scenario-c-en.json"
V2_DOSSIER = ROOT / "tests/evals/with-skill/fixtures/executive-career-dossier-v2/scenario-c-en.json"
V1_VALIDATOR = SCRIPTS / "validate_executive_career_dossier.py"
V2_VALIDATOR = SCRIPTS / "validate_executive_career_dossier_v2.py"
LINKEDIN_REPORT_VALIDATOR = SCRIPTS / "validate_linkedin_client_report.py"
LINKEDIN_REPORT = ROOT / "tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-a-es.md"
LINKEDIN_BUNDLE = ROOT / "tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-a.json"
TRIAGE = ROOT / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-en.json"
OUTCOME = ROOT / "plugins/professional-growth-coach/tests/fixtures/private-recruiter-conversion-outcome/contact-received-en.json"
CHECKPOINT = ROOT / "plugins/professional-growth-coach/tests/fixtures/private-recruiter-followthrough-checkpoint/completed-screen-attended-en.json"
CHECKPOINT_RECEIPT = ROOT / "plugins/professional-growth-coach/tests/fixtures/private-recruiter-conversion-outcome/screen-requested-en.json"


class CliReceiptPrivacyTests(unittest.TestCase):
    def test_readme_documents_the_safe_receipt_default(self) -> None:
        readme = (ROOT / "plugins/professional-growth-coach/README.md").read_text(encoding="utf-8")
        self.assertIn("omit its absolute local\npath", readme)
        self.assertIn("--include-artifact-path", readme)

    def _run(self, script: Path, arguments: list[str]) -> tuple[subprocess.CompletedProcess[str], Path]:
        directory = Path(tempfile.mkdtemp(prefix="pgc-receipt-"))
        output = directory / "artifact.html"
        result = subprocess.run(
            [sys.executable, "-B", str(script), *arguments, "--output", str(output)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return result, output

    def test_default_receipts_omit_absolute_artifact_paths(self) -> None:
        cases = (
            (SCRIPTS / "render_executive_career_dossier.py", [str(V1_DOSSIER)]),
            (SCRIPTS / "render_executive_career_dossier_v2.py", [str(V2_DOSSIER)]),
            (SCRIPTS / "render_private_recruiter_reply_triage.py", [str(TRIAGE)]),
            (SCRIPTS / "render_private_recruiter_followthrough_checkpoint.py", [str(CHECKPOINT), "--receipt", str(CHECKPOINT_RECEIPT), "--as-of", "2026-08-27"]),
            (SCRIPTS / "render_private_recruiter_conversion_outcome.py", [str(OUTCOME), "--as-of", "2026-08-27"]),
        )
        for script, arguments in cases:
            with self.subTest(script=script.name):
                result, output = self._run(script, arguments)
                self.assertEqual(0, result.returncode, result.stderr)
                receipt = json.loads(result.stdout)
                self.assertNotIn("artifact_path", receipt)
                self.assertTrue(output.is_file())
                self.assertNotIn(str(output), result.stdout)

    def test_artifact_path_requires_explicit_opt_in(self) -> None:
        result, output = self._run(
            SCRIPTS / "render_private_recruiter_conversion_outcome.py",
            [str(OUTCOME), "--as-of", "2026-08-27", "--include-artifact-path"],
        )
        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(str(output), receipt["artifact_path"])

    def test_triage_missing_input_preserves_opaque_loader_failure_contract(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="pgc-triage-missing-"))
        missing = directory / "missing-private-triage.json"
        output = directory / "artifact.html"
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPTS / "render_private_recruiter_reply_triage.py"),
                str(missing),
                "--output",
                str(output),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(3, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertEqual("cannot load private recruiter triage input\n", result.stderr)
        self.assertFalse(output.exists())

    def test_unknown_arguments_never_echo_private_values(self) -> None:
        sentinel = "/private/hidden/candidate-record.json"
        cases = (
            (SCRIPTS / "render_executive_career_dossier.py", [str(V1_DOSSIER)]),
            (SCRIPTS / "render_executive_career_dossier_v2.py", [str(V2_DOSSIER)]),
            (SCRIPTS / "render_private_recruiter_reply_triage.py", [str(TRIAGE)]),
            (SCRIPTS / "render_private_recruiter_followthrough_checkpoint.py", [str(CHECKPOINT), "--receipt", str(CHECKPOINT_RECEIPT), "--as-of", "2026-08-27"]),
            (SCRIPTS / "render_private_recruiter_conversion_outcome.py", [str(OUTCOME), "--as-of", "2026-08-27"]),
        )
        for script, arguments in cases:
            with self.subTest(script=script.name):
                result, output = self._run(script, [*arguments, "--private-context", sentinel])
                self.assertNotEqual(0, result.returncode)
                self.assertNotIn(sentinel, result.stdout)
                self.assertNotIn(sentinel, result.stderr)
                self.assertFalse(output.exists())

    def test_private_validators_return_opaque_unknown_argument_errors(self) -> None:
        sentinel = "PRIVATE_ARGUMENT_SENTINEL"
        cases = (
            (
                SCRIPTS / "validate_private_recruiter_reply_triage.py",
                [str(TRIAGE)],
            ),
            (
                SCRIPTS / "validate_private_recruiter_followthrough_checkpoint.py",
                [str(CHECKPOINT), "--receipt", str(CHECKPOINT_RECEIPT), "--as-of", "2026-08-27"],
            ),
            (
                SCRIPTS / "validate_private_recruiter_conversion_outcome.py",
                [str(OUTCOME), "--as-of", "2026-08-27"],
            ),
        )
        for script, arguments in cases:
            with self.subTest(script=script.name):
                result = subprocess.run(
                    [sys.executable, "-B", str(script), *arguments, "--unexpected", sentinel],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(3, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertEqual('{"error":{"code":"invalid_arguments"}}\n', result.stderr)
                self.assertNotIn(sentinel, result.stderr)

    def test_dossier_validators_return_opaque_unknown_argument_errors(self) -> None:
        sentinel = "PRIVATE_DOSSIER_ARGUMENT_SENTINEL"
        for script, dossier in ((V1_VALIDATOR, V1_DOSSIER), (V2_VALIDATOR, V2_DOSSIER)):
            with self.subTest(script=script.name):
                result = subprocess.run(
                    [sys.executable, "-B", str(script), str(dossier), "--unexpected", sentinel],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(3, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertEqual('{"error":{"code":"invalid_arguments"}}\n', result.stderr)
                self.assertNotIn(sentinel, result.stderr)

    def test_linkedin_report_validator_returns_opaque_unknown_argument_errors(self) -> None:
        sentinel = "/private/hidden/linkedin-bundle.json"
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(LINKEDIN_REPORT_VALIDATOR),
                str(LINKEDIN_REPORT),
                str(LINKEDIN_BUNDLE),
                "--unexpected",
                sentinel,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(3, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertEqual('{"error":{"code":"invalid_arguments"}}\n', result.stderr)
        self.assertNotIn(sentinel, result.stderr)

    def test_triage_renderer_imports_without_pythonpath_setup(self) -> None:
        code = (
            "import importlib.util, sys; "
            f"spec=importlib.util.spec_from_file_location('isolated_triage_renderer', {str(SCRIPTS / 'render_private_recruiter_reply_triage.py')!r}); "
            "module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_private_receipt_renderers_import_without_pythonpath_setup(self) -> None:
        for script in (
            SCRIPTS / "render_private_recruiter_reply_triage.py",
            SCRIPTS / "render_private_recruiter_followthrough_checkpoint.py",
            SCRIPTS / "render_private_recruiter_conversion_outcome.py",
        ):
            with self.subTest(script=script.name):
                code = (
                    "import importlib.util, sys; "
                    f"spec=importlib.util.spec_from_file_location('isolated_renderer', {str(script)!r}); "
                    "module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)"
                )
                result = subprocess.run(
                    [sys.executable, "-B", "-c", code],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
