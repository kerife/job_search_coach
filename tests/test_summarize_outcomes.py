"""Behavior tests for the deterministic job-search outcome CLI."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins" / "professional-growth-coach" / "scripts" / "summarize_outcomes.py"
CSV_FIELDS = (
    "application_id",
    "candidate_id",
    "application_date",
    "response_date",
    "interview_date",
    "interview_stage",
    "offer_date",
    "currency",
    "role",
    "geography",
    "source",
    "referral",
    "asset_version",
    "intervention_id",
    "confounders",
    "simultaneous_interventions",
    "benchmark_consent",
)
JSON_FIELDS = {
    "window_days",
    "applications",
    "responses",
    "interviews",
    "offers",
    "response_rate",
    "interview_rate",
    "offer_rate",
    "days_to_first_interview",
    "warnings",
}


def outcome_row(**overrides: str) -> dict[str, str]:
    row = {field: "" for field in CSV_FIELDS}
    row.update(
        {
            "application_id": "a-001",
            "candidate_id": "c-001",
            "application_date": "2026-08-01",
            "currency": "USD",
            "role": "Principal SRE",
            "geography": "Mexico",
            "source": "company-site",
            "referral": "false",
            "asset_version": "cv-v1",
            "simultaneous_interventions": "false",
            "benchmark_consent": "false",
        }
    )
    row.update(overrides)
    return row


def run_path(
    csv_path: Path,
    *,
    window: str = "30",
    as_of: str = "2026-08-06",
    candidate_id: str | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(SCRIPT),
        str(csv_path),
        "--window",
        window,
        "--as-of",
        as_of,
    ]
    if candidate_id is not None:
        command.extend(("--candidate-id", candidate_id))
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def run_summary(
    rows: list[dict[str, str]],
    *,
    window: str = "30",
    as_of: str = "2026-08-06",
    candidate_id: str | None = None,
    fieldnames: tuple[str, ...] = CSV_FIELDS,
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as temporary_directory:
        csv_path = Path(temporary_directory) / "outcomes.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        return run_path(
            csv_path,
            window=window,
            as_of=as_of,
            candidate_id=candidate_id,
        )


class SummarizeOutcomesTests(unittest.TestCase):
    maxDiff = None

    def parse_valid(self, result: subprocess.CompletedProcess[str]) -> dict[str, object]:
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        summary = json.loads(result.stdout)
        self.assertEqual(set(summary), JSON_FIELDS)
        return summary

    def assert_invalid(
        self,
        result: subprocess.CompletedProcess[str],
        expected_error: str,
    ) -> None:
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(json.loads(result.stderr), {"error": expected_error})

    def assert_empty_safety_summary(self, summary: dict[str, object]) -> None:
        for field in ("applications", "responses", "interviews", "offers"):
            self.assertEqual(summary[field], 0, field)
        for field in ("response_rate", "interview_rate", "offer_rate"):
            self.assertEqual(summary[field], 0, field)
        self.assertIsNone(summary["days_to_first_interview"])

    def assert_private_candidate_a_summary(
        self,
        result: subprocess.CompletedProcess[str],
        *,
        private_b_values: tuple[str, ...],
    ) -> None:
        summary = self.parse_valid(result)
        self.assertEqual(
            summary,
            {
                "window_days": 30,
                "applications": 1,
                "responses": 1,
                "interviews": 0,
                "offers": 0,
                "response_rate": 1.0,
                "interview_rate": 0.0,
                "offer_rate": 0.0,
                "days_to_first_interview": None,
                "warnings": [
                    "small sample: 1 applications in window; rates are descriptive"
                ],
            },
        )
        combined_output = result.stdout + result.stderr
        for private_value in private_b_values:
            self.assertNotIn(private_value, combined_output)

    def test_valid_output_has_exact_deterministic_json_contract(self) -> None:
        result = run_summary([])

        summary = self.parse_valid(result)
        self.assertEqual(
            summary,
            {
                "window_days": 30,
                "applications": 0,
                "responses": 0,
                "interviews": 0,
                "offers": 0,
                "response_rate": 0,
                "interview_rate": 0,
                "offer_rate": 0,
                "days_to_first_interview": None,
                "warnings": [
                    "small sample: 0 applications in window; rates are descriptive"
                ],
            },
        )
        self.assertEqual(
            result.stdout,
            json.dumps(summary, sort_keys=True, separators=(",", ":")) + "\n",
        )

    def test_windows_include_both_boundaries_and_support_14_30_60_90_days(self) -> None:
        rows = [
            outcome_row(
                application_id="a-start",
                application_date="2026-07-08",
                response_date="2026-07-09",
            ),
            outcome_row(
                application_id="a-end",
                application_date="2026-08-06",
                interview_date="2026-08-06",
                interview_stage="recruiter_screen",
            ),
            outcome_row(application_id="a-before", application_date="2026-07-07"),
            outcome_row(
                application_id="a-60",
                application_date="2026-06-08",
                offer_date="2026-06-20",
            ),
            outcome_row(application_id="a-90", application_date="2026-05-09"),
        ]

        summary_14 = self.parse_valid(run_summary(rows, window="14"))
        summary_30 = self.parse_valid(run_summary(rows, window="30"))
        summary_60 = self.parse_valid(run_summary(rows, window="60"))
        summary_90 = self.parse_valid(run_summary(rows, window="90"))

        self.assertEqual(summary_14["applications"], 1)
        self.assertEqual(summary_30["applications"], 2)
        self.assertEqual(summary_30["responses"], 1)
        self.assertEqual(summary_30["interviews"], 1)
        self.assertEqual(summary_30["days_to_first_interview"], 0)
        self.assertEqual(summary_60["applications"], 4)
        self.assertEqual(summary_60["offers"], 1)
        self.assertEqual(summary_90["applications"], 5)

    def test_malformed_dates_and_as_of_are_invalid_without_tracebacks(self) -> None:
        cases = (
            (
                run_summary([outcome_row(application_date="2026-02-30")]),
                "row 2: application_date must be empty or YYYY-MM-DD",
            ),
            (
                run_summary([outcome_row(response_date="06/08/2026")]),
                "row 2: response_date must be empty or YYYY-MM-DD",
            ),
            (
                run_summary([], as_of="2026-13-01"),
                "--as-of must be YYYY-MM-DD",
            ),
        )

        for result, expected_error in cases:
            with self.subTest(expected_error=expected_error):
                self.assert_invalid(result, expected_error)

    def test_missing_file_and_invalid_window_are_invalid_without_tracebacks(self) -> None:
        missing_path = Path("/tmp/task9-definitely-missing-outcomes.csv")

        self.assert_invalid(
            run_path(missing_path),
            "CSV file is unavailable",
        )
        self.assert_invalid(
            run_summary([], window="0"),
            "--window must be a positive integer",
        )
        self.assert_invalid(
            run_summary([], window="thirty"),
            "--window must be a positive integer",
        )

    def test_csv_input_rejects_direct_and_intermediate_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            external = root / "external"
            external.mkdir()
            target = external / "outcomes.csv"
            with target.open("w", newline="", encoding="utf-8") as handle:
                csv.DictWriter(handle, fieldnames=CSV_FIELDS).writeheader()

            parent_alias = root / "alias"
            parent_alias.symlink_to(external, target_is_directory=True)
            direct_alias = root / "direct.csv"
            direct_alias.symlink_to(target)

            for path in (parent_alias / "outcomes.csv", direct_alias):
                with self.subTest(path=path):
                    self.assert_invalid(run_path(path), "CSV file is unavailable")

    def test_csv_input_rejects_oversized_and_invalid_utf8_before_parse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            oversized = root / "oversized.csv"
            header = ",".join(CSV_FIELDS) + "\n"
            valid_row = ",".join(["x"] * len(CSV_FIELDS)) + "\n"
            oversized.write_bytes((header + valid_row).encode("utf-8") * 20000)
            invalid_utf8 = root / "invalid.csv"
            invalid_utf8.write_bytes(b"application_id,candidate_id\n\xff")

            self.assert_invalid(run_path(oversized), "CSV file exceeds safe size limit")
            self.assert_invalid(run_path(invalid_utf8), "CSV file is not valid UTF-8")

    def test_csv_input_errors_do_not_echo_path_or_candidate_identifier(self) -> None:
        missing_path = Path("/tmp/private-candidate-outcomes.csv")
        result = run_path(missing_path, candidate_id="private-candidate-123")
        self.assert_invalid(result, "CSV file is unavailable")
        self.assertNotIn(str(missing_path), result.stderr)

    def test_windows_beyond_the_as_of_date_range_are_invalid_without_tracebacks(self) -> None:
        expected_error = (
            "--window exceeds valid range for --as-of 2026-08-06; maximum is 739834"
        )

        boundary_summary = self.parse_valid(run_summary([], window="739834"))
        self.assertEqual(boundary_summary["window_days"], 739834)

        for window in ("739835", "9" * 5000):
            with self.subTest(window_length=len(window)):
                self.assert_invalid(run_summary([], window=window), expected_error)

    def test_required_headers_and_ids_are_validated(self) -> None:
        missing_headers = tuple(field for field in CSV_FIELDS if field != "application_id")
        result = run_summary([outcome_row()], fieldnames=missing_headers)
        self.assert_invalid(
            result,
            "missing required CSV headers: application_id",
        )

        for field in ("application_id", "candidate_id"):
            with self.subTest(field=field):
                result = run_summary([outcome_row(**{field: ""})])
                self.assert_invalid(result, f"row 2: {field} is required")

    def test_duplicate_application_ids_are_rejected_instead_of_double_counted(self) -> None:
        result = run_summary(
            [
                outcome_row(application_id="stable-1"),
                outcome_row(application_id="stable-1", response_date="2026-08-02"),
            ]
        )

        self.assert_invalid(
            result,
            "row 3: duplicate application_id; first seen on row 2",
        )

    def test_chronology_and_future_dates_are_rejected(self) -> None:
        cases = (
            (
                outcome_row(response_date="2026-07-31"),
                "row 2: response_date cannot precede application_date",
            ),
            (
                outcome_row(
                    response_date="2026-08-04",
                    interview_date="2026-08-03",
                    interview_stage="recruiter_screen",
                ),
                "row 2: interview_date cannot precede response_date",
            ),
            (
                outcome_row(
                    interview_date="2026-08-05",
                    interview_stage="recruiter_screen",
                    offer_date="2026-08-04",
                ),
                "row 2: offer_date cannot precede interview_date",
            ),
            (
                outcome_row(application_date="2026-08-07"),
                "row 2: application_date cannot be after --as-of 2026-08-06",
            ),
            (
                outcome_row(response_date="2026-08-07"),
                "row 2: response_date cannot be after --as-of 2026-08-06",
            ),
        )

        for row, expected_error in cases:
            with self.subTest(expected_error=expected_error):
                self.assert_invalid(run_summary([row]), expected_error)

    def test_missing_application_dates_are_ignored_with_a_data_quality_warning(self) -> None:
        result = run_summary(
            [
                outcome_row(application_id="a-missing", application_date=""),
                outcome_row(application_id="a-valid"),
            ]
        )

        summary = self.parse_valid(result)
        self.assertEqual(summary["applications"], 1)
        self.assertIn("missing application_date rows ignored: 1", summary["warnings"])

    def test_currency_and_intervention_warnings_only_use_rows_in_the_window(self) -> None:
        outside = outcome_row(
            application_id="a-outside",
            application_date="2026-06-01",
            currency="MXN",
            intervention_id="old-headline",
        )
        inside = outcome_row(application_id="a-inside", currency="USD")

        summary = self.parse_valid(run_summary([outside, inside]))
        self.assertNotIn("multiple currencies present; no conversion performed", summary["warnings"])
        self.assertNotIn(
            "interventions observed; summary is descriptive and does not prove causality",
            summary["warnings"],
        )

        mixed = outcome_row(application_id="a-mixed", currency="MXN")
        changed = outcome_row(application_id="a-changed", intervention_id="headline-v2")
        summary = self.parse_valid(run_summary([inside, mixed, changed]))
        self.assertIn("multiple currencies present; no conversion performed", summary["warnings"])
        self.assertIn(
            "interventions observed; summary is descriptive and does not prove causality",
            summary["warnings"],
        )

    def test_unknown_stage_small_sample_and_confounders_are_warned(self) -> None:
        result = run_summary(
            [
                outcome_row(
                    interview_date="2026-08-04",
                    interview_stage="unknown",
                    intervention_id="headline-v2",
                    confounders="referral;seasonality",
                    simultaneous_interventions="true",
                )
            ]
        )

        summary = self.parse_valid(result)
        for warning in (
            "small sample: 1 applications in window; rates are descriptive",
            "unknown interview_stage on in-window interview rows: 1",
            "confounders reported on in-window rows: 1; no causal attribution",
            "simultaneous interventions reported on in-window rows: 1; no causal attribution",
            "interventions observed; summary is descriptive and does not prove causality",
        ):
            self.assertIn(warning, summary["warnings"])

    def test_linkedin_outreach_rows_warn_that_measurement_events_are_descriptive(self) -> None:
        result = run_summary(
            [
                outcome_row(
                    application_id="li-001",
                    source="linkedin_outreach",
                    intervention_id="LI-FIRST-002",
                    response_date="2026-08-03",
                ),
                outcome_row(
                    application_id="li-002",
                    source="linkedin_outreach",
                    intervention_id="LI-FIRST-002",
                ),
            ]
        )

        summary = self.parse_valid(result)
        self.assertEqual(summary["applications"], 2)
        self.assertIn(
            "LinkedIn outreach measurement events observed; descriptive only, no causal attribution",
            summary["warnings"],
        )

    def test_linkedin_outreach_warning_does_not_echo_untrusted_intervention_ids(self) -> None:
        for sentinel in (
            "LI-/Users/private/profile.json",
            r"LI-D:\private\profile.json",
            r"LI-\\server\share\profile.json",
        ):
            with self.subTest(sentinel=sentinel):
                result = run_summary(
                    [
                        outcome_row(
                            source="linkedin_outreach",
                            intervention_id=sentinel,
                        )
                    ]
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertNotIn(sentinel, result.stdout)
                self.assertNotIn(sentinel, result.stderr)
                summary = self.parse_valid(result)
                self.assertIn(
                    "LinkedIn outreach measurement events observed; descriptive only, no causal attribution",
                    summary["warnings"],
                )

    def test_multiple_candidates_without_unanimous_consent_get_zero_safe_summary(self) -> None:
        result = run_summary(
            [
                outcome_row(application_id="a-1", candidate_id="c-1", benchmark_consent="true"),
                outcome_row(application_id="a-2", candidate_id="c-2", benchmark_consent="false"),
            ]
        )

        summary = self.parse_valid(result)
        self.assert_empty_safety_summary(summary)
        self.assertEqual(
            summary["warnings"],
            [
                "multiple candidates present; no aggregate computed without unanimous in-window benchmark consent; rerun once per candidate with --candidate-id"
            ],
        )

    def test_candidate_selection_returns_isolated_summaries_without_aggregate_rates(self) -> None:
        rows = [
            outcome_row(
                application_id="a-1",
                candidate_id="c-1",
                response_date="2026-08-02",
                benchmark_consent="false",
            ),
            outcome_row(
                application_id="a-2",
                candidate_id="c-2",
                interview_date="2026-08-03",
                interview_stage="recruiter_screen",
                benchmark_consent="false",
            ),
        ]

        aggregate = self.parse_valid(run_summary(rows))
        candidate_one = self.parse_valid(
            run_summary(rows, candidate_id="c-1")
        )
        candidate_two = self.parse_valid(
            run_summary(rows, candidate_id="c-2")
        )

        self.assert_empty_safety_summary(aggregate)
        self.assertEqual(candidate_one["applications"], 1)
        self.assertEqual(candidate_one["responses"], 1)
        self.assertEqual(candidate_one["interviews"], 0)
        self.assertEqual(candidate_two["applications"], 1)
        self.assertEqual(candidate_two["responses"], 0)
        self.assertEqual(candidate_two["interviews"], 1)
        self.assertEqual(candidate_two["days_to_first_interview"], 2)

    def test_candidate_selection_scopes_data_quality_and_experiment_warnings(self) -> None:
        rows = [
            outcome_row(application_id="a-1", candidate_id="c-1", currency="USD"),
            outcome_row(
                application_id="a-2",
                candidate_id="c-2",
                application_date="",
                currency="MXN",
                intervention_id="other-candidate-change",
                confounders="other-candidate-confounder",
                simultaneous_interventions="true",
            ),
        ]

        summary = self.parse_valid(run_summary(rows, candidate_id="c-1"))

        self.assertEqual(summary["applications"], 1)
        self.assertNotIn("missing application_date rows ignored: 1", summary["warnings"])
        self.assertNotIn("multiple currencies present; no conversion performed", summary["warnings"])
        self.assertNotIn(
            "interventions observed; summary is descriptive and does not prove causality",
            summary["warnings"],
        )
        self.assertFalse(any("confounder" in warning for warning in summary["warnings"]))

    def test_candidate_selection_ignores_malformed_dates_owned_by_another_candidate(self) -> None:
        private_b_values = (
            "candidate-b-private",
            "application-b-private-malformed",
            "private-bad-date",
        )
        result = run_summary(
            [
                outcome_row(
                    application_id="application-a",
                    candidate_id="candidate-a",
                    response_date="2026-08-02",
                ),
                outcome_row(
                    application_id=private_b_values[1],
                    candidate_id=private_b_values[0],
                    application_date=private_b_values[2],
                ),
            ],
            candidate_id="candidate-a",
        )

        self.assert_private_candidate_a_summary(
            result,
            private_b_values=private_b_values,
        )

    def test_candidate_selection_ignores_future_dates_owned_by_another_candidate(self) -> None:
        private_b_values = (
            "candidate-b-future-private",
            "application-b-future-private",
            "2099-12-31",
        )
        result = run_summary(
            [
                outcome_row(
                    application_id="application-a",
                    candidate_id="candidate-a",
                    response_date="2026-08-02",
                ),
                outcome_row(
                    application_id=private_b_values[1],
                    candidate_id=private_b_values[0],
                    application_date=private_b_values[2],
                ),
            ],
            candidate_id="candidate-a",
        )

        self.assert_private_candidate_a_summary(
            result,
            private_b_values=private_b_values,
        )

    def test_candidate_selection_ignores_duplicate_ids_owned_by_another_candidate(self) -> None:
        private_b_values = (
            "candidate-b-duplicate-private",
            "application-b-duplicate-private",
        )
        result = run_summary(
            [
                outcome_row(
                    application_id="application-a",
                    candidate_id="candidate-a",
                    response_date="2026-08-02",
                ),
                outcome_row(
                    application_id=private_b_values[1],
                    candidate_id=private_b_values[0],
                ),
                outcome_row(
                    application_id=private_b_values[1],
                    candidate_id=private_b_values[0],
                ),
            ],
            candidate_id="candidate-a",
        )

        self.assert_private_candidate_a_summary(
            result,
            private_b_values=private_b_values,
        )

    def test_candidate_selection_ignores_invalid_booleans_owned_by_another_candidate(self) -> None:
        private_b_values = (
            "candidate-b-boolean-private",
            "application-b-boolean-private",
            "private-b-boolean-value",
        )
        result = run_summary(
            [
                outcome_row(
                    application_id="application-a",
                    candidate_id="candidate-a",
                    response_date="2026-08-02",
                ),
                outcome_row(
                    application_id=private_b_values[1],
                    candidate_id=private_b_values[0],
                    benchmark_consent=private_b_values[2],
                ),
            ],
            candidate_id="candidate-a",
        )

        self.assert_private_candidate_a_summary(
            result,
            private_b_values=private_b_values,
        )

    def test_candidate_selection_ignores_other_row_errors_owned_by_another_candidate(self) -> None:
        private_b_values = (
            "candidate-b-outcome-private",
            "application-b-outcome-private",
            "2026-08-03",
        )
        result = run_summary(
            [
                outcome_row(
                    application_id="application-a",
                    candidate_id="candidate-a",
                    response_date="2026-08-02",
                ),
                outcome_row(
                    application_id=private_b_values[1],
                    candidate_id=private_b_values[0],
                    application_date="",
                    response_date=private_b_values[2],
                ),
            ],
            candidate_id="candidate-a",
        )

        self.assert_private_candidate_a_summary(
            result,
            private_b_values=private_b_values,
        )

    def test_unknown_candidate_selection_is_invalid_without_traceback(self) -> None:
        result = run_summary([outcome_row(candidate_id="c-1")], candidate_id="c-missing")

        self.assert_invalid(result, "candidate_id not found")

    def test_unknown_candidate_path_is_not_echoed_in_diagnostics(self) -> None:
        private_identifier = "/private/candidate/profile"
        result = run_summary([outcome_row(candidate_id="c-1")], candidate_id=private_identifier)

        self.assert_invalid(result, "candidate_id not found")
        self.assertNotIn(private_identifier, result.stdout + result.stderr)

    def test_unknown_candidate_does_not_validate_or_reveal_other_candidates(self) -> None:
        private_b_values = (
            "candidate-b-unknown-private",
            "application-b-unknown-private",
            "private-bad-date-for-unknown",
        )
        rows = [
            outcome_row(
                application_id=private_b_values[1],
                candidate_id=private_b_values[0],
                application_date=private_b_values[2],
            )
        ]

        first = run_summary(rows, candidate_id="candidate-missing")
        second = run_summary(rows, candidate_id="candidate-missing")

        for result in (first, second):
            self.assert_invalid(
                result,
                "candidate_id not found",
            )
            combined_output = result.stdout + result.stderr
            for private_value in private_b_values:
                self.assertNotIn(private_value, combined_output)
        self.assertEqual(first.stderr, second.stderr)

    def test_multiple_candidates_aggregate_only_with_unanimous_explicit_consent(self) -> None:
        result = run_summary(
            [
                outcome_row(
                    application_id="a-1",
                    candidate_id="c-1",
                    response_date="2026-08-02",
                    benchmark_consent="true",
                ),
                outcome_row(
                    application_id="a-2",
                    candidate_id="c-2",
                    interview_date="2026-08-03",
                    interview_stage="hiring_manager",
                    benchmark_consent="true",
                ),
            ]
        )

        summary = self.parse_valid(result)
        self.assertEqual(summary["applications"], 2)
        self.assertEqual(summary["responses"], 1)
        self.assertEqual(summary["interviews"], 1)
        self.assertEqual(summary["response_rate"], 0.5)
        self.assertIn(
            "multiple candidates aggregated with explicit benchmark consent; preserve anonymity",
            summary["warnings"],
        )

    def test_boolean_fields_reject_ambiguous_values(self) -> None:
        for field in ("simultaneous_interventions", "benchmark_consent"):
            with self.subTest(field=field):
                result = run_summary([outcome_row(**{field: "maybe"})])
                self.assert_invalid(
                    result,
                    f"row 2: {field} must be true, false, or empty",
                )

    def test_invalid_scalar_diagnostics_never_echo_input_values(self) -> None:
        cases = (
            (run_summary([outcome_row(application_date="/Users/private/profile.json")]), "profile.json"),
            (run_summary([outcome_row(benchmark_consent="token_sk_live_SYNTHETIC")]), "token_sk_live_SYNTHETIC"),
            (
                run_summary(
                    [
                        outcome_row(application_id="/Users/private/app.json"),
                        outcome_row(application_id="/Users/private/app.json"),
                    ]
                ),
                "/Users/private/app.json",
            ),
            (run_summary([], window="/Users/private/window.csv"), "/Users/private/window.csv"),
            (run_summary([], as_of="/Users/private/date.csv"), "/Users/private/date.csv"),
            (
                run_summary(
                    [outcome_row()],
                    fieldnames=CSV_FIELDS + ("/Users/private/header.csv", "/Users/private/header.csv"),
                ),
                "/Users/private/header.csv",
            ),
        )
        for result, sentinel in cases:
            with self.subTest(sentinel=sentinel):
                self.assertNotIn(sentinel, result.stdout)
                self.assertNotIn(sentinel, result.stderr)

    def test_bundled_asset_and_forward_fixtures_use_the_canonical_header(self) -> None:
        paths = [
            REPO_ROOT
            / "plugins"
            / "professional-growth-coach"
            / "skills"
            / "track-career-outcomes"
            / "assets"
            / "outcomes.csv",
            *sorted(
                (REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures").glob(
                    "outcomes-*.csv"
                )
            ),
        ]

        for path in paths:
            with self.subTest(path=path.name), path.open(
                newline="", encoding="utf-8"
            ) as handle:
                self.assertEqual(tuple(next(csv.reader(handle))), CSV_FIELDS)

    def test_forward_fixtures_reproduce_the_recorded_raw_json(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures"
        cases = {
            "outcomes-sparse.csv": {
                "applications": 1,
                "days_to_first_interview": 4,
                "interview_rate": 1.0,
                "interviews": 1,
                "offer_rate": 0.0,
                "offers": 0,
                "response_rate": 1.0,
                "responses": 1,
                "warnings": [
                    "small sample: 1 applications in window; rates are descriptive",
                    "unknown interview_stage on in-window interview rows: 1",
                ],
                "window_days": 30,
            },
            "outcomes-confounded.csv": {
                "applications": 2,
                "days_to_first_interview": 10,
                "interview_rate": 0.5,
                "interviews": 1,
                "offer_rate": 0.5,
                "offers": 1,
                "response_rate": 1.0,
                "responses": 2,
                "warnings": [
                    "small sample: 2 applications in window; rates are descriptive",
                    "interventions observed; summary is descriptive and does not prove causality",
                    "confounders reported on in-window rows: 2; no causal attribution",
                    "simultaneous interventions reported on in-window rows: 2; no causal attribution",
                    "role mix varies across in-window rows: 2 values; possible confounder",
                    "geography varies across in-window rows: 2 values; possible confounder",
                    "application source varies across in-window rows: 2 values; possible confounder",
                    "referral status varies across in-window rows: 2 values; possible confounder",
                    "asset_version varies across in-window rows: 2 values; possible confounder",
                    "referrals present in window; referral effects are a confounder",
                ],
                "window_days": 30,
            },
            "outcomes-currency.csv": {
                "applications": 2,
                "days_to_first_interview": 8,
                "interview_rate": 1.0,
                "interviews": 2,
                "offer_rate": 1.0,
                "offers": 2,
                "response_rate": 1.0,
                "responses": 2,
                "warnings": [
                    "small sample: 2 applications in window; rates are descriptive",
                    "multiple currencies present; no conversion performed",
                ],
                "window_days": 30,
            },
            "outcomes-linkedin-outreach.csv": {
                "applications": 4,
                "days_to_first_interview": None,
                "interview_rate": 0.0,
                "interviews": 0,
                "offer_rate": 0.0,
                "offers": 0,
                "response_rate": 0.25,
                "responses": 1,
                "warnings": [
                    "small sample: 4 applications in window; rates are descriptive",
                    "interventions observed; summary is descriptive and does not prove causality",
                    "LinkedIn outreach measurement events observed; descriptive only, no causal attribution",
                ],
                "window_days": 30,
            },
            "outcomes-two-candidate-consented.csv": {
                "applications": 2,
                "days_to_first_interview": 2,
                "interview_rate": 0.5,
                "interviews": 1,
                "offer_rate": 0.0,
                "offers": 0,
                "response_rate": 0.5,
                "responses": 1,
                "warnings": [
                    "small sample: 2 applications in window; rates are descriptive",
                    "multiple candidates aggregated with explicit benchmark consent; preserve anonymity",
                ],
                "window_days": 30,
            },
            "outcomes-two-candidate-no-consent.csv": {
                "applications": 0,
                "days_to_first_interview": None,
                "interview_rate": 0,
                "interviews": 0,
                "offer_rate": 0,
                "offers": 0,
                "response_rate": 0,
                "responses": 0,
                "warnings": [
                    "multiple candidates present; no aggregate computed without unanimous in-window benchmark consent; rerun once per candidate with --candidate-id"
                ],
                "window_days": 30,
            },
        }

        for filename, expected in cases.items():
            with self.subTest(filename=filename):
                result = run_path(fixture_root / filename)
                self.assertEqual(self.parse_valid(result), expected)
                self.assertEqual(
                    result.stdout,
                    json.dumps(expected, sort_keys=True, separators=(",", ":")) + "\n",
                )

        isolated_cases = {
            "candidate-001": {
                "applications": 1,
                "days_to_first_interview": None,
                "interview_rate": 0.0,
                "interviews": 0,
                "offer_rate": 0.0,
                "offers": 0,
                "response_rate": 1.0,
                "responses": 1,
                "warnings": [
                    "small sample: 1 applications in window; rates are descriptive"
                ],
                "window_days": 30,
            },
            "candidate-002": {
                "applications": 1,
                "days_to_first_interview": 2,
                "interview_rate": 1.0,
                "interviews": 1,
                "offer_rate": 0.0,
                "offers": 0,
                "response_rate": 0.0,
                "responses": 0,
                "warnings": [
                    "small sample: 1 applications in window; rates are descriptive"
                ],
                "window_days": 30,
            },
        }
        no_consent_fixture = fixture_root / "outcomes-two-candidate-no-consent.csv"
        for candidate_id, expected in isolated_cases.items():
            with self.subTest(candidate_id=candidate_id):
                result = run_path(no_consent_fixture, candidate_id=candidate_id)
                self.assertEqual(self.parse_valid(result), expected)
                self.assertEqual(
                    result.stdout,
                    json.dumps(expected, sort_keys=True, separators=(",", ":")) + "\n",
                )


if __name__ == "__main__":
    unittest.main()
