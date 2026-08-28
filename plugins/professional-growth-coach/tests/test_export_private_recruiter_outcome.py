"""TDD contracts for the explicit recruiter-receipt CSV export boundary."""

from __future__ import annotations

import copy
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "private-recruiter-conversion-outcome"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from export_private_recruiter_outcome import ExportError, export_row, write_export  # noqa: E402


def _receipt(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class PrivateRecruiterOutcomeExportTests(unittest.TestCase):
    def test_reply_received_maps_only_to_response_date_without_private_source_id(self) -> None:
        row = export_row(
            _receipt("reply-received-en.json"),
            candidate_id="candidate-001",
            application_id="app-001",
            application_date="2026-08-01",
            as_of="2026-08-08",
        )
        self.assertEqual("2026-08-08", row["response_date"])
        self.assertEqual("", row["interview_date"])
        self.assertTrue(row["intervention_id"].startswith("recruiter-receipt-sha256-"))
        self.assertNotIn("D-102", row["intervention_id"])
        self.assertEqual("recruiter_private_receipt", row["source"])

    def test_source_artifact_id_contributes_to_replay_fingerprint(self) -> None:
        first = _receipt("reply-received-en.json")
        second = copy.deepcopy(first)
        second["source_artifact_id"] = "D-999"
        first_row = export_row(
            first,
            candidate_id="candidate-001",
            application_id="app-001",
            application_date="2026-08-01",
            as_of="2026-08-08",
        )
        second_row = export_row(
            second,
            candidate_id="candidate-001",
            application_id="app-001",
            application_date="2026-08-01",
            as_of="2026-08-08",
        )
        self.assertNotEqual(first_row["intervention_id"], second_row["intervention_id"])

    def test_screen_requested_is_rejected_instead_of_becoming_an_interview(self) -> None:
        with self.assertRaisesRegex(ExportError, "event_type is not exportable"):
            export_row(
                _receipt("screen-requested-en.json"),
                candidate_id="candidate-001",
                application_id="app-001",
                application_date="2026-08-01",
                as_of="2026-08-08",
            )

    def test_application_context_is_required(self) -> None:
        with self.assertRaisesRegex(ExportError, "application_id is required"):
            export_row(
                _receipt("reply-received-en.json"),
                candidate_id="candidate-001",
                application_id="",
                application_date="2026-08-01",
                as_of="2026-08-08",
            )

    def test_replay_is_idempotent_for_existing_output(self) -> None:
        receipt = _receipt("reply-received-en.json")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "outcomes.csv"
            first = write_export(
                receipt,
                candidate_id="candidate-001",
                application_id="app-001",
                application_date="2026-08-01",
                as_of="2026-08-08",
                output=output,
            )
            before = output.read_bytes()
            second = write_export(
                copy.deepcopy(receipt),
                candidate_id="candidate-001",
                application_id="app-001",
                application_date="2026-08-01",
                as_of="2026-08-08",
                output=output,
            )
            self.assertEqual("written", first["status"])
            self.assertEqual("already_present", second["status"])
            self.assertEqual(before, output.read_bytes())
            with output.open(newline="", encoding="utf-8") as handle:
                self.assertEqual(1, sum(1 for _ in csv.DictReader(handle)))

    def test_force_preserves_distinct_existing_application_rows(self) -> None:
        receipt = _receipt("reply-received-en.json")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "outcomes.csv"
            write_export(
                receipt,
                candidate_id="candidate-001",
                application_id="app-001",
                application_date="2026-08-01",
                as_of="2026-08-08",
                output=output,
            )
            write_export(
                receipt,
                candidate_id="candidate-001",
                application_id="app-002",
                application_date="2026-08-02",
                as_of="2026-08-08",
                output=output,
                force=True,
            )
            with output.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual({"app-001", "app-002"}, {row["application_id"] for row in rows})

    def test_cli_rejects_non_exportable_event_without_echoing_arguments(self) -> None:
        script = SCRIPTS / "export_private_recruiter_outcome.py"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "screen.json"
            source.write_text(json.dumps(_receipt("screen-requested-en.json")), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable, str(script), "--receipt", str(source),
                    "--output", str(Path(directory) / "out.csv"),
                    "--candidate-id", "candidate-private", "--application-id", "app-private",
                    "--application-date", "2026-08-01", "--as-of", "2026-08-08",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertEqual('{"error":{"code":"export_failed"}}\n', result.stderr)
            self.assertNotIn("candidate-private", result.stderr)

    def test_rejects_symlink_output_before_reading_existing_csv(self) -> None:
        receipt = _receipt("reply-received-en.json")
        with tempfile.TemporaryDirectory() as directory:
            real = Path(directory) / "real.csv"
            write_export(
                receipt,
                candidate_id="candidate-001",
                application_id="app-001",
                application_date="2026-08-01",
                as_of="2026-08-08",
                output=real,
            )
            link = Path(directory) / "out.csv"
            link.symlink_to(real)
            with self.assertRaisesRegex(ExportError, "output target is not a regular file"):
                write_export(
                    receipt,
                    candidate_id="candidate-001",
                    application_id="app-001",
                    application_date="2026-08-01",
                    as_of="2026-08-08",
                    output=link,
                )

    def test_rejects_spreadsheet_formula_values_in_optional_prose_fields(self) -> None:
        with self.assertRaisesRegex(ExportError, "role is invalid"):
            export_row(
                _receipt("reply-received-en.json"),
                candidate_id="candidate-001",
                application_id="app-001",
                application_date="2026-08-01",
                as_of="2026-08-08",
                role="=HYPERLINK(\"https://example.invalid\")",
            )

    def test_rejects_symlink_output_parent(self) -> None:
        receipt = _receipt("reply-received-en.json")
        with tempfile.TemporaryDirectory() as directory:
            real_parent = Path(directory) / "real"
            real_parent.mkdir()
            alias = Path(directory) / "alias"
            alias.symlink_to(real_parent, target_is_directory=True)
            with self.assertRaisesRegex(ExportError, "output parent is unavailable"):
                write_export(
                    receipt,
                    candidate_id="candidate-001",
                    application_id="app-001",
                    application_date="2026-08-01",
                    as_of="2026-08-08",
                    output=alias / "outcomes.csv",
                )


if __name__ == "__main__":
    unittest.main()
