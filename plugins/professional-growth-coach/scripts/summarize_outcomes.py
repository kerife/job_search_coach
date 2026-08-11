#!/usr/bin/env python3
"""Summarize validated job-search outcomes without causal claims."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path


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
DATE_FIELDS = ("application_date", "response_date", "interview_date", "offer_date")
BOOLEAN_FIELDS = ("simultaneous_interventions", "benchmark_consent")
SUMMARY_FIELDS = (
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
)


class InputError(ValueError):
    """A deterministic, user-correctable CLI input error."""


class JsonArgumentParser(argparse.ArgumentParser):
    """Turn argparse failures into the CLI's JSON error contract."""

    def error(self, message: str) -> None:
        raise InputError(message)


def parse_iso_date(value: str, *, label: str) -> date | None:
    cleaned = (value or "").strip()
    if not cleaned:
        return None
    try:
        parsed = date.fromisoformat(cleaned)
    except ValueError as error:
        raise InputError(
            f"{label} must be empty or YYYY-MM-DD; got {cleaned!r}"
        ) from error
    if parsed.isoformat() != cleaned:
        raise InputError(f"{label} must be empty or YYYY-MM-DD; got {cleaned!r}")
    return parsed


def parse_boolean(value: str, *, row_number: int, field: str) -> bool:
    cleaned = (value or "").strip().lower()
    if cleaned in ("", "false"):
        return False
    if cleaned == "true":
        return True
    raise InputError(
        f"row {row_number}: {field} must be true, false, or empty; got {value.strip()!r}"
    )


def rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0
    return float(Decimal(numerator) / Decimal(denominator))


def summary(
    *,
    window: int,
    applications: int,
    responses: int,
    interviews: int,
    offers: int,
    days_to_first_interview: int | None,
    warnings: list[str],
) -> dict[str, object]:
    result: dict[str, object] = {
        "window_days": window,
        "applications": applications,
        "responses": responses,
        "interviews": interviews,
        "offers": offers,
        "response_rate": rate(responses, applications),
        "interview_rate": rate(interviews, applications),
        "offer_rate": rate(offers, applications),
        "days_to_first_interview": days_to_first_interview,
        "warnings": warnings,
    }
    assert tuple(result) == SUMMARY_FIELDS
    return result


def empty_summary(window: int, warnings: list[str]) -> dict[str, object]:
    return summary(
        window=window,
        applications=0,
        responses=0,
        interviews=0,
        offers=0,
        days_to_first_interview=None,
        warnings=warnings,
    )


def read_rows(
    path: Path,
    as_of: date,
    candidate_id: str | None = None,
) -> list[dict[str, object]]:
    try:
        handle = path.open(newline="", encoding="utf-8-sig")
    except FileNotFoundError as error:
        raise InputError(f"CSV file not found: {path}") from error
    except OSError as error:
        raise InputError(f"cannot read CSV file {path}: {error.strerror or error}") from error

    try:
        with handle:
            reader = csv.DictReader(handle, strict=True)
            headers = reader.fieldnames or []
            duplicate_headers = sorted(
                header for header, count in Counter(headers).items() if count > 1
            )
            if duplicate_headers:
                raise InputError(
                    "duplicate CSV headers: " + ", ".join(duplicate_headers)
                )
            missing_headers = [field for field in CSV_FIELDS if field not in headers]
            if missing_headers:
                raise InputError(
                    "missing required CSV headers: " + ", ".join(missing_headers)
                )

            rows: list[dict[str, object]] = []
            seen_application_ids: dict[str, int] = {}
            for row_number, raw_row in enumerate(reader, start=2):
                raw_candidate_id = (raw_row.get("candidate_id") or "").strip()
                if candidate_id is not None and raw_candidate_id != candidate_id:
                    continue
                if None in raw_row:
                    raise InputError(f"row {row_number}: more values than CSV headers")
                if not any((value or "").strip() for value in raw_row.values()):
                    continue

                row = {field: (raw_row.get(field) or "").strip() for field in CSV_FIELDS}
                for field in ("application_id", "candidate_id"):
                    if not row[field]:
                        raise InputError(f"row {row_number}: {field} is required")

                application_id = row["application_id"]
                first_row = seen_application_ids.get(application_id)
                if first_row is not None:
                    raise InputError(
                        f"row {row_number}: duplicate application_id {application_id!r} "
                        f"first seen on row {first_row}"
                    )
                seen_application_ids[application_id] = row_number

                parsed_dates: dict[str, date | None] = {}
                for field in DATE_FIELDS:
                    parsed_dates[field] = parse_iso_date(
                        row[field], label=f"row {row_number}: {field}"
                    )
                    if parsed_dates[field] is not None and parsed_dates[field] > as_of:
                        raise InputError(
                            f"row {row_number}: {field} cannot be after --as-of {as_of.isoformat()}"
                        )

                application_date = parsed_dates["application_date"]
                if application_date is None:
                    if any(parsed_dates[field] is not None for field in DATE_FIELDS[1:]):
                        raise InputError(
                            f"row {row_number}: outcome dates require application_date"
                        )
                else:
                    previous_field = "application_date"
                    previous_date = application_date
                    for field in DATE_FIELDS[1:]:
                        current_date = parsed_dates[field]
                        if current_date is None:
                            continue
                        if current_date < previous_date:
                            raise InputError(
                                f"row {row_number}: {field} cannot precede {previous_field}"
                            )
                        previous_field = field
                        previous_date = current_date

                parsed_booleans = {
                    field: parse_boolean(
                        row[field], row_number=row_number, field=field
                    )
                    for field in BOOLEAN_FIELDS
                }
                row.update(parsed_dates)
                row.update(parsed_booleans)
                rows.append(row)
    except UnicodeError as error:
        raise InputError(f"CSV file must be UTF-8: {path}") from error
    except csv.Error as error:
        raise InputError(f"malformed CSV: {error}") from error

    return rows


def distinct(rows: list[dict[str, object]], field: str) -> set[str]:
    return {str(row[field]) for row in rows if row[field]}


def summarize(
    path: Path,
    window: int,
    as_of: date,
    candidate_id: str | None = None,
) -> dict[str, object]:
    rows = read_rows(path, as_of, candidate_id=candidate_id)
    if candidate_id is not None:
        candidate_ids = distinct(rows, "candidate_id")
        if candidate_id not in candidate_ids:
            raise InputError(f"candidate_id not found: {candidate_id!r}")
        rows = [row for row in rows if row["candidate_id"] == candidate_id]

    missing_application_dates = sum(
        row["application_date"] is None for row in rows
    )
    start = as_of - timedelta(days=window - 1)
    in_window = [
        row
        for row in rows
        if isinstance(row["application_date"], date)
        and start <= row["application_date"] <= as_of
    ]

    candidate_ids = distinct(in_window, "candidate_id")
    if len(candidate_ids) > 1 and not all(
        bool(row["benchmark_consent"]) for row in in_window
    ):
        return empty_summary(
            window,
            [
                "multiple candidates present; no aggregate computed without unanimous in-window benchmark consent; rerun once per candidate with --candidate-id"
            ],
        )

    applications = len(in_window)
    responses = sum(row["response_date"] is not None for row in in_window)
    interviews = sum(row["interview_date"] is not None for row in in_window)
    offers = sum(row["offer_date"] is not None for row in in_window)
    interview_lags = [
        (row["interview_date"] - row["application_date"]).days
        for row in in_window
        if isinstance(row["interview_date"], date)
        and isinstance(row["application_date"], date)
    ]

    warnings: list[str] = []
    if missing_application_dates:
        warnings.append(
            f"missing application_date rows ignored: {missing_application_dates}"
        )
    if applications < 10:
        warnings.append(
            f"small sample: {applications} applications in window; rates are descriptive"
        )

    unknown_stages = sum(
        1
        for row in in_window
        if row["interview_date"] is not None
        and str(row["interview_stage"]).strip().lower() in ("", "unknown")
    )
    if unknown_stages:
        warnings.append(
            f"unknown interview_stage on in-window interview rows: {unknown_stages}"
        )

    if len(distinct(in_window, "currency")) > 1:
        warnings.append("multiple currencies present; no conversion performed")
    if distinct(in_window, "intervention_id"):
        warnings.append(
            "interventions observed; summary is descriptive and does not prove causality"
        )
    linkedin_measurement_events = sorted({
        str(row["intervention_id"])
        for row in in_window
        if str(row["source"]).strip().lower() == "linkedin_outreach"
        and str(row["intervention_id"]).startswith("LI-")
    })
    if linkedin_measurement_events:
        warnings.append(
            "LinkedIn outreach measurement events observed: "
            + ", ".join(linkedin_measurement_events)
            + "; descriptive only, no causal attribution"
        )

    confounded_rows = sum(bool(row["confounders"]) for row in in_window)
    if confounded_rows:
        warnings.append(
            f"confounders reported on in-window rows: {confounded_rows}; no causal attribution"
        )
    simultaneous_rows = sum(
        bool(row["simultaneous_interventions"]) for row in in_window
    )
    if simultaneous_rows:
        warnings.append(
            f"simultaneous interventions reported on in-window rows: {simultaneous_rows}; no causal attribution"
        )

    varying_fields = (
        ("role", "role mix"),
        ("geography", "geography"),
        ("source", "application source"),
        ("referral", "referral status"),
        ("asset_version", "asset_version"),
    )
    for field, label in varying_fields:
        values = distinct(in_window, field)
        if len(values) > 1:
            warnings.append(
                f"{label} varies across in-window rows: {len(values)} values; possible confounder"
            )

    referral_values = {value.lower() for value in distinct(in_window, "referral")}
    if referral_values.intersection({"true", "yes", "1"}):
        warnings.append("referrals present in window; referral effects are a confounder")

    if len(candidate_ids) > 1:
        warnings.append(
            "multiple candidates aggregated with explicit benchmark consent; preserve anonymity"
        )

    return summary(
        window=window,
        applications=applications,
        responses=responses,
        interviews=interviews,
        offers=offers,
        days_to_first_interview=min(interview_lags) if interview_lags else None,
        warnings=warnings,
    )


def emit_json(payload: dict[str, object], *, stream: object) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")), file=stream)


def parse_window(raw_window: str, as_of: date) -> int:
    cleaned = raw_window.strip()
    if not cleaned or not cleaned.isascii() or not cleaned.isdecimal():
        raise InputError(f"--window must be a positive integer; got {raw_window!r}")
    normalized = cleaned.lstrip("0")
    if not normalized:
        raise InputError(f"--window must be a positive integer; got {raw_window!r}")

    maximum = as_of.toordinal()
    maximum_text = str(maximum)
    if len(normalized) > len(maximum_text) or (
        len(normalized) == len(maximum_text) and normalized > maximum_text
    ):
        raise InputError(
            f"--window exceeds valid range for --as-of {as_of.isoformat()}; "
            f"maximum is {maximum}"
        )
    return int(normalized)


def main(argv: list[str] | None = None) -> int:
    parser = JsonArgumentParser(add_help=True)
    parser.add_argument("csv_path")
    parser.add_argument("--window", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--candidate-id")
    try:
        arguments = parser.parse_args(argv)
        try:
            as_of = parse_iso_date(arguments.as_of, label="--as-of")
        except InputError as error:
            raise InputError(
                f"--as-of must be YYYY-MM-DD; got {arguments.as_of!r}"
            ) from error
        if as_of is None:
            raise InputError(f"--as-of must be YYYY-MM-DD; got {arguments.as_of!r}")
        window = parse_window(arguments.window, as_of)
        candidate_id = arguments.candidate_id
        if candidate_id is not None:
            candidate_id = candidate_id.strip()
            if not candidate_id:
                raise InputError("--candidate-id must be non-empty")
        result = summarize(
            Path(arguments.csv_path),
            window,
            as_of,
            candidate_id=candidate_id,
        )
    except InputError as error:
        emit_json({"error": str(error)}, stream=sys.stderr)
        return 2

    emit_json(result, stream=sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
