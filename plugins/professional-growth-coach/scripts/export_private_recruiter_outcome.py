#!/usr/bin/env python3
"""Export one semantically safe recruiter receipt into the canonical outcomes CSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import secrets
import stat
import sys
import tempfile
from collections.abc import Mapping
from datetime import date
from pathlib import Path

try:
    from canonical_date import date_arg, parse_canonical_date
    from validate_private_recruiter_conversion_outcome import load_outcome, validate_outcome
    from summarize_outcomes import CSV_FIELDS
except ModuleNotFoundError:
    raise RuntimeError("private recruiter export dependencies are unavailable")


class ExportError(ValueError):
    """Raised for deterministic, user-correctable export failures."""


_EXPORTABLE_EVENT = "reply_received"
_INTERVENTION_PREFIX = "recruiter-receipt-sha256-"
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_SAFE_VERSION = re.compile(r"^[a-z0-9][a-z0-9.-]{0,31}$")
_SAFE_CURRENCY = re.compile(r"^[A-Z]{3}$")
_FORMULA_PREFIX = re.compile(r"^\s*[=+\-@]")


def _safe_absolute(path: Path) -> Path:
    absolute = os.path.abspath(os.fspath(path))
    parts = Path(absolute).parts
    if len(parts) > 1 and parts[1] in {"tmp", "var"}:
        component = parts[1]
        alias = os.path.join(os.sep, component)
        if os.path.islink(alias) and os.path.realpath(alias) == os.path.join(os.sep, "private", component):
            suffix = os.path.join(*parts[2:]) if len(parts) > 2 else ""
            absolute = os.path.join(os.sep, "private", component, suffix)
    return Path(absolute)


def _required_id(value: str, label: str) -> str:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise ExportError(f"{label} is required")
    return value


def _date(value: str, label: str) -> date:
    if not isinstance(value, str):
        raise ExportError(f"{label} must use YYYY-MM-DD")
    try:
        parsed = parse_canonical_date(value, field=label)
    except ValueError as error:
        raise ExportError(f"{label} must use YYYY-MM-DD") from error
    return parsed


def _fingerprint(receipt: Mapping[str, object], application_id: str) -> str:
    payload = {
        "receipt": {
            key: receipt.get(key)
            for key in (
                "schema_version", "artifact_kind", "locale", "event_date",
                "event_type", "source_version", "fact_ids",
                "observation_state", "next_safe_action", "source_artifact_id",
            )
        },
        "application_id": application_id,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _INTERVENTION_PREFIX + hashlib.sha256(encoded).hexdigest()


def export_row(
    receipt: Mapping[str, object],
    *,
    candidate_id: str,
    application_id: str,
    application_date: str,
    as_of: str,
    role: str = "",
    geography: str = "",
    currency: str = "",
    asset_version: str = "",
    referral: bool = False,
    confounders: str = "",
    simultaneous_interventions: bool = False,
    benchmark_consent: bool = False,
) -> dict[str, str]:
    if not isinstance(receipt, Mapping):
        raise ExportError("receipt is required")
    reference = _date(as_of, "as_of")
    application = _date(application_date, "application_date")
    _required_id(candidate_id, "candidate_id")
    _required_id(application_id, "application_id")
    receipt_errors = validate_outcome(receipt, as_of=reference)
    if receipt_errors:
        raise ExportError("receipt validation failed")
    if receipt.get("event_type") != _EXPORTABLE_EVENT:
        raise ExportError("event_type is not exportable")
    event_date = _date(str(receipt.get("event_date", "")), "event_date")
    if application > event_date:
        raise ExportError("application_date cannot follow response_date")
    if role or geography or confounders:
        for label, value in (("role", role), ("geography", geography), ("confounders", confounders)):
            if "\n" in value or "\r" in value or len(value) > 180 or _FORMULA_PREFIX.match(value):
                raise ExportError(f"{label} is invalid")
    if currency and not _SAFE_CURRENCY.fullmatch(currency):
        raise ExportError("currency is invalid")
    if asset_version and not _SAFE_VERSION.fullmatch(asset_version):
        raise ExportError("asset_version is invalid")
    fingerprint = _fingerprint(receipt, application_id)
    row = {field: "" for field in CSV_FIELDS}
    row.update(
        {
            "application_id": application_id,
            "candidate_id": candidate_id,
            "application_date": application.isoformat(),
            "response_date": event_date.isoformat(),
            "source": "recruiter_private_receipt",
            "referral": "true" if referral else "false",
            "asset_version": asset_version,
            "intervention_id": fingerprint,
            "role": role,
            "geography": geography,
            "currency": currency,
            "confounders": confounders,
            "simultaneous_interventions": "true" if simultaneous_interventions else "false",
            "benchmark_consent": "true" if benchmark_consent else "false",
        }
    )
    return row


def _csv_bytes(rows: list[Mapping[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _existing_rows(output: Path) -> list[dict[str, str]]:
    try:
        with output.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != list(CSV_FIELDS):
                raise ExportError("existing CSV output is unavailable")
            rows = list(reader)
            if any(set(row) != set(CSV_FIELDS) for row in rows):
                raise ExportError("existing CSV output is unavailable")
            if any(_FORMULA_PREFIX.match(value) for row in rows for value in row.values() if isinstance(value, str)):
                raise ExportError("existing CSV output is unavailable")
            return rows
    except (OSError, UnicodeError, csv.Error) as error:
        raise ExportError("existing CSV output is unavailable") from error


def _parent_is_safe(parent: Path) -> None:
    current = Path(parent.anchor)
    for component in parent.parts[1:]:
        candidate = current / component
        try:
            status = os.lstat(candidate)
        except FileNotFoundError as error:
            raise ExportError("output parent is unavailable") from error
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            raise ExportError("output parent is unavailable")
        current = candidate


def _atomic_write(output: Path, content: bytes, *, force: bool) -> None:
    target = _safe_absolute(output)
    parent = target.parent
    if not parent.is_absolute():
        raise ExportError("output parent is unavailable")
    _parent_is_safe(parent)
    try:
        status = os.lstat(target)
    except FileNotFoundError:
        status = None
    if status is not None:
        if os.path.islink(target) or not os.path.isfile(target):
            raise ExportError("output target is not a regular file")
        if not force:
            raise FileExistsError("output already exists")
    temporary = None
    descriptor = None
    try:
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.tmp-{secrets.token_hex(8)}-", dir=parent)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
        os.chmod(target, 0o600)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def write_export(
    receipt: Mapping[str, object],
    *,
    candidate_id: str,
    application_id: str,
    application_date: str,
    as_of: str,
    output: Path,
    force: bool = False,
    **kwargs: object,
) -> dict[str, str]:
    row = export_row(
        receipt,
        candidate_id=candidate_id,
        application_id=application_id,
        application_date=application_date,
        as_of=as_of,
        **kwargs,
    )
    target = _safe_absolute(output)
    fingerprint = row["intervention_id"]
    try:
        status = os.lstat(target)
    except FileNotFoundError:
        status = None
    if status is not None and (stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode)):
        raise ExportError("output target is not a regular file")
    rows = _existing_rows(target) if status is not None else []
    if any(existing.get("intervention_id") == fingerprint for existing in rows):
        return {"status": "already_present", "intervention_id": fingerprint}
    if status is not None and force:
        rows = [existing for existing in rows if existing.get("application_id") != application_id]
    _atomic_write(target, _csv_bytes([*rows, row]), force=force)
    return {"status": "written", "intervention_id": fingerprint}


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise ExportError("invalid arguments")


def _cli(argv: list[str] | None = None) -> int:
    parser = _ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--application-id", required=True)
    parser.add_argument("--application-date", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--role", default="")
    parser.add_argument("--geography", default="")
    parser.add_argument("--currency", default="")
    parser.add_argument("--asset-version", default="")
    parser.add_argument("--referral", action="store_true")
    parser.add_argument("--confounders", default="")
    parser.add_argument("--simultaneous-interventions", action="store_true")
    parser.add_argument("--benchmark-consent", action="store_true")
    parser.add_argument("--force", action="store_true")
    try:
        args = parser.parse_args(argv)
        receipt = load_outcome(args.receipt)
        result = write_export(
            receipt,
            candidate_id=args.candidate_id,
            application_id=args.application_id,
            application_date=args.application_date,
            as_of=args.as_of,
            output=args.output,
            force=args.force,
            role=args.role,
            geography=args.geography,
            currency=args.currency,
            asset_version=args.asset_version,
            referral=args.referral,
            confounders=args.confounders,
            simultaneous_interventions=args.simultaneous_interventions,
            benchmark_consent=args.benchmark_consent,
        )
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    except (ExportError, OSError, ValueError):
        print(json.dumps({"error": {"code": "export_failed"}}, separators=(",", ":")), file=sys.stderr)
        return 2
    print(json.dumps({"artifact_kind": "private_recruiter_outcome_csv", "status": result["status"]}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
