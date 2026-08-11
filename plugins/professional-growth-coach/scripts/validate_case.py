#!/usr/bin/env python3
"""Validate a single, isolated Professional Growth Coach case record."""

from __future__ import annotations

import base64
import binascii
import json
import math
import os
import re
import stat
import sys
import unicodedata
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any


REQUIRED_CASE_KEYS = (
    "schema_version",
    "candidate_id",
    "mode",
    "consent",
    "target",
    "sources",
    "claims",
    "interventions",
    "outcomes",
)
EVIDENCE_LABELS = ("verified", "candidate-reported", "inferred", "unknown")
CASE_RECORDS = ("sources", "claims", "interventions", "outcomes")
BENCHMARK_CANDIDATE_ID_FIELDS = ("benchmark_candidate_ids",)
MAX_CASE_NESTING_DEPTH = 100
MAX_CASE_BYTES = 64_000
MAX_DIAGNOSTIC_BYTES = 16_384
CASE_FIELDS = frozenset(REQUIRED_CASE_KEYS)
CONSENT_FIELDS = frozenset({"benchmark"})
TARGET_FIELDS = frozenset({"roles", "geography", "compensation", "constraints"})
RECORD_FIELDS = {
    "sources": frozenset({"candidate_id", "source_id", "kind", "evidence_label"}),
    "claims": frozenset({"candidate_id", "claim_id", "text", "evidence_label"}),
    "interventions": frozenset(
        {"candidate_id", "intervention_id", "kind", "description", "occurred_at"}
    ),
    "outcomes": frozenset(
        {
            "candidate_id",
            "outcome_id",
            "kind",
            "value",
            "observed_at",
            "benchmark_candidate_ids",
        }
    ),
}
SENSITIVE_KEY_SEGMENTS = frozenset(
    {
        "password",
        "passwd",
        "token",
        "credential",
        "api_key",
        "access_key",
        "access_token",
        "auth",
        "client_secret",
        "session",
        "cookie",
        "private_key",
        "secret_key",
        "contact",
        "email",
        "phone",
        "raw_profile",
    }
)
_AUTHORIZATION_HEADER_VALUE = re.compile(
    r"\bauthorization\s*[:∶]\s*\S+",
    re.I,
)
_BARE_BASIC_VALUE = re.compile(
    r"\bbasic\s+([a-z0-9+/]+={0,2})(?![a-z0-9+/=])",
    re.I,
)
_BARE_BEARER_VALUE = re.compile(
    r"\bbearer\s+([a-z0-9._~+/=-]+)",
    re.I,
)
_MIN_BEARER_TOKEN_LENGTH = 24
_SECRET_ASSIGNMENT = re.compile(
    r"\b(?:password|passwd|token|credential|api[_. /-]?key|access[_. /-]?"
    r"(?:key(?:[_. /-]?id)?|token)|client[_. /-]?secret|"
    r"secret[_. /-]?key|auth|session|cookie|private[_. /-]?key)\s*[:=]\s*\S+",
    re.I,
)
_EMAIL_VALUE = re.compile(
    r"[A-Z0-9._%+-]{1,254}@[A-Z0-9.-]{1,253}\.[A-Z]{2,63}", re.I
)
_PHONE_VALUE = re.compile(
    r"(?:\+\d{7,15}\b|\+\d{1,3}(?:[ .()-]*\d){7,14}\b|"
    r"(?:\+\d{1,3}[ .-]?)?(?:\(?\d{3}\)?[ .-])\d{3}[ .-]\d{4})"
)
_LINKEDIN_PROFILE_VALUE = re.compile(
    r"(?<![a-z0-9.-])(?:https?://)?(?:[a-z0-9-]+\.)*linkedin\.com/(?:in|pub)/", re.I
)
_LOCAL_PATH_VALUE = re.compile(
    r"(?<![A-Za-z0-9.])(?:/Users/|/home/|/private/|/var/tmp/|/tmp/|"
    r"~/|\.\.?/|[A-Z]:[/\\])",
    re.I,
)
_HYPHEN_LIKE = frozenset("‐‑‒–—―−⁃")
_SENSITIVE_KEY_ALIASES = frozenset(
    SENSITIVE_KEY_SEGMENTS
    | {segment.replace("_", "") for segment in SENSITIVE_KEY_SEGMENTS}
)
_IDENTITY_KEY_ALIASES = frozenset(
    f"{entity}{identifier}"
    for entity in ("candidate", "person", "subject")
    for identifier in ("id", "ids", "identifier", "identifiers")
)


class _DuplicateJsonKeyError(ValueError):
    """Raised when a JSON object repeats a key before validation."""


class _CaseInputTooLarge(ValueError):
    """Raised before parsing when the bounded case input is too large."""


def _read_case_input(path: str) -> str:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if not nofollow or not directory_flag:
        raise OSError("no-follow input opening is unavailable")

    parent_descriptor, filename = _open_case_parent(path, nofollow, directory_flag)
    try:
        flags = os.O_RDONLY | nofollow
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(filename, flags, dir_fd=parent_descriptor)
    finally:
        os.close(parent_descriptor)

    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError("case input is not a regular file")
        if metadata.st_size > MAX_CASE_BYTES:
            raise _CaseInputTooLarge

        contents = bytearray()
        while True:
            chunk = os.read(descriptor, min(8192, MAX_CASE_BYTES + 1 - len(contents)))
            if not chunk:
                break
            contents.extend(chunk)
            if len(contents) > MAX_CASE_BYTES:
                raise _CaseInputTooLarge
        return bytes(contents).decode("utf-8")
    finally:
        os.close(descriptor)


def _open_case_parent(path: str, nofollow: int, directory_flag: int) -> tuple[int, str]:
    absolute = os.path.abspath(path)
    parent = Path(absolute).parent
    base_flags = os.O_RDONLY | directory_flag | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(os.sep, base_flags)
    try:
        for index, component in enumerate(parent.parts[1:]):
            if component in {"", ".", ".."}:
                raise OSError("case input parent is unsafe")
            candidate = os.path.join(os.sep, component)
            trusted_system_alias = (
                index == 0
                and component in {"tmp", "var"}
                and os.path.islink(candidate)
                and os.path.realpath(candidate) == os.path.join(os.sep, "private", component)
            )
            next_descriptor = os.open(
                component,
                base_flags | (0 if trusted_system_alias else nofollow),
                dir_fd=descriptor,
            )
            if not stat.S_ISDIR(os.fstat(next_descriptor).st_mode):
                os.close(next_descriptor)
                raise OSError("case input parent is not a directory")
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor, Path(absolute).name
    except BaseException:
        os.close(descriptor)
        raise


def _format_diagnostics(errors: list[str]) -> str:
    marker = "validation diagnostics truncated; additional errors omitted\n"
    marker_bytes = len(marker.encode("utf-8"))
    lines: list[str] = []
    used_bytes = 0
    for error in errors:
        line = f"{error}\n"
        line_bytes = len(line.encode("utf-8"))
        if used_bytes + line_bytes + marker_bytes > MAX_DIAGNOSTIC_BYTES:
            return "".join(lines) + marker
        lines.append(line)
        used_bytes += line_bytes
    return "".join(lines)


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError("duplicate JSON key")
        result[key] = value
    return result


def normalize_case(case: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy whose omitted benchmark consent is explicitly false."""
    normalized = deepcopy(dict(case))
    consent = normalized.get("consent")
    if isinstance(consent, Mapping):
        normalized["consent"] = dict(consent)
        normalized["consent"].setdefault("benchmark", False)
    return normalized


def validate_case(case: object) -> list[str]:
    """Return newline-ready validation errors for one candidate's case."""
    if not isinstance(case, Mapping):
        return ["case must be a JSON object"]

    json_errors = _walk_json_domain(case, "")
    if json_errors:
        return list(dict.fromkeys(json_errors))
    case = normalize_case(case)
    errors: list[str] = []
    errors.extend(_closed_mapping(case, CASE_FIELDS, "case"))
    for key in REQUIRED_CASE_KEYS:
        if key not in case:
            errors.append(f"{key} is required")

    candidate_id = case.get("candidate_id")
    has_valid_candidate_id = isinstance(candidate_id, str) and bool(candidate_id.strip())
    if "candidate_id" in case and not has_valid_candidate_id:
        errors.append("candidate_id must be a non-empty string")

    if "schema_version" in case and case.get("schema_version") != "1.0":
        errors.append("schema_version must equal 1.0")

    mode = case.get("mode")
    if "mode" in case and mode not in {"self-service", "coach"}:
        errors.append("mode must be self-service or coach")

    consent = case.get("consent")
    if "consent" in case and not isinstance(consent, Mapping):
        errors.append("consent must be an object")
    elif isinstance(consent, Mapping):
        errors.extend(_closed_mapping(consent, CONSENT_FIELDS, "consent"))
        if not isinstance(consent.get("benchmark"), bool):
            errors.append("consent.benchmark must be true or false")

    target = case.get("target")
    if "target" in case and not isinstance(target, Mapping):
        errors.append("target must be an object")
    elif isinstance(target, Mapping):
        errors.extend(_closed_mapping(target, TARGET_FIELDS, "target"))

    for field in CASE_RECORDS:
        records = case.get(field)
        if field not in case:
            continue
        if not isinstance(records, list):
            errors.append(f"{field} must be a list")
            continue
        errors.extend(
            _validate_records(
                field,
                records,
                candidate_id if has_valid_candidate_id else None,
                bool(consent.get("benchmark")) if isinstance(consent, Mapping) else False,
            )
        )

    errors.extend(_walk_sensitive_data(case))
    errors.extend(
        _walk_identity_fields(
            case,
            candidate_id if has_valid_candidate_id else None,
            bool(consent.get("benchmark")) if isinstance(consent, Mapping) else False,
        )
    )
    return list(dict.fromkeys(errors))


def _closed_mapping(
    value: Mapping[str, Any], allowed_fields: frozenset[str], location: str
) -> list[str]:
    """Return path-specific errors for unsupported fields without changing input."""
    return [
        f"{location} has unsupported field: {_safe_path_key(field)}"
        for field in sorted(set(value) - allowed_fields)
    ]


def _safe_path_key(key: object) -> str:
    """Keep diagnostics path-specific without echoing sensitive key material."""
    if not isinstance(key, str):
        return _escape_diagnostic_controls(str(key))
    safe_key = _escape_diagnostic_controls(key)
    if _normalized_key(key) in _SENSITIVE_KEY_ALIASES:
        return safe_key
    if _has_sensitive_key_segment(key) or _is_credential_shaped_value(key):
        return "<redacted-key>"
    return safe_key


def _escape_diagnostic_controls(value: str) -> str:
    """Render C0/DEL controls literally so diagnostics cannot inject records."""
    return "".join(
        f"\\u{ord(character):04x}"
        if unicodedata.category(character) == "Cc"
        else character
        for character in value
    )


def _walk_json_domain(
    value: object,
    path: str,
    active_containers: set[int] | None = None,
    depth: int = 0,
) -> list[str]:
    """Return deterministic path errors for values outside the JSON data model."""
    if depth > MAX_CASE_NESTING_DEPTH:
        return [f"case exceeds maximum nesting depth at {path or 'case'}"]
    errors: list[str] = []
    active = active_containers if active_containers is not None else set()
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in active:
            return [f"case contains cyclic container at {path or 'case'}"]
        active.add(identity)
        container_path = path or "case"
        string_items: list[tuple[str, object]] = []
        non_string_key_types: list[str] = []
        try:
            for key, nested in value.items():
                if not isinstance(key, str):
                    non_string_key_types.append(type(key).__name__)
                else:
                    string_items.append((key, nested))
            errors.extend(
                f"case contains non-string key of type {key_type} at {container_path}"
                for key_type in sorted(non_string_key_types)
            )
            for key, nested in sorted(string_items, key=lambda item: item[0]):
                safe_key = _safe_path_key(key)
                child_path = f"{path}.{safe_key}" if path else safe_key
                errors.extend(
                    _walk_json_domain(nested, child_path, active, depth + 1)
                )
        finally:
            active.remove(identity)
    elif isinstance(value, list):
        identity = id(value)
        if identity in active:
            return [f"case contains cyclic container at {path or 'case'}"]
        active.add(identity)
        try:
            for index, nested in enumerate(value):
                errors.extend(
                    _walk_json_domain(
                        nested,
                        f"{path}[{index}]",
                        active,
                        depth + 1,
                    )
                )
        finally:
            active.remove(identity)
    elif value is None or type(value) in {str, bool, int}:
        pass
    elif type(value) is float:
        if not math.isfinite(value):
            errors.append(f"case contains non-JSON numeric value at {path}")
    else:
        errors.append(
            f"case contains non-JSON value type {type(value).__name__} at {path}"
        )
    return errors


def _validate_records(
    field: str,
    records: list[object],
    candidate_id: object,
    benchmark_consent: bool,
) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, record in enumerate(records):
        location = f"{field}[{index}]"
        if not isinstance(record, Mapping):
            errors.append(f"{location} must be an object")
            continue
        errors.extend(_closed_mapping(record, RECORD_FIELDS[field], location))
        provenance_field = {
            "sources": "source_id",
            "claims": "claim_id",
            "interventions": "intervention_id",
            "outcomes": "outcome_id",
        }[field]
        if provenance_field not in record:
            errors.append(f"{location}.{provenance_field} is required")
        elif (
            not isinstance(record[provenance_field], str)
            or not record[provenance_field].strip()
        ):
            errors.append(
                f"{location}.{provenance_field} must be a non-empty string"
            )
        else:
            record_id = record[provenance_field]
            if record_id in seen_ids:
                errors.append(f"{location}.{provenance_field} must be unique")
            else:
                seen_ids.add(record_id)
        if "candidate_id" not in record:
            errors.append(f"{location}.candidate_id is required")
        elif candidate_id is not None and record["candidate_id"] != candidate_id:
            errors.append(f"{location}.candidate_id must match case candidate_id")
        for benchmark_field in BENCHMARK_CANDIDATE_ID_FIELDS:
            if benchmark_field in record:
                benchmark_ids = record[benchmark_field]
                if not _is_nonempty_string_list(benchmark_ids):
                    errors.append(
                        f"{location}.{benchmark_field} must be a list of non-empty strings"
                    )
                elif not benchmark_consent:
                    errors.append(
                        f"{location}.{benchmark_field} requires consent.benchmark=true"
                    )
        if field in {"sources", "claims"}:
            _validate_evidence_label(location, record, errors)
    return errors


def _normalized_classifier_text(text: str) -> str:
    compatibility = unicodedata.normalize("NFKC", text)
    decomposed = unicodedata.normalize("NFKD", compatibility)
    return "".join(
        "-"
        if character in _HYPHEN_LIKE or unicodedata.category(character) == "Pd"
        else " "
        if unicodedata.category(character) == "Zs"
        else character
        for character in decomposed
        if unicodedata.category(character) != "Cf"
        and not unicodedata.category(character).startswith("M")
    )


def _normalized_key(key: str) -> str:
    normalized = _normalized_classifier_text(key)
    camel_split = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)
    return re.sub(r"[^a-z0-9]+", "_", camel_split.casefold()).strip("_")


def _has_sensitive_key_segment(key: object) -> bool:
    if not isinstance(key, str):
        return False
    normalized = _normalized_key(key)
    return any(
        normalized == segment
        or normalized.startswith(f"{segment}_")
        or normalized.endswith(f"_{segment}")
        or f"_{segment}_" in normalized
        for segment in _SENSITIVE_KEY_ALIASES
    )


def _is_credential_shaped_value(value: str) -> bool:
    normalized = _normalized_classifier_text(value)
    value_patterns = [_SECRET_ASSIGNMENT]
    if "@" in normalized:
        value_patterns.append(_EMAIL_VALUE)
    value_patterns.extend((_PHONE_VALUE, _LINKEDIN_PROFILE_VALUE, _LOCAL_PATH_VALUE))
    return bool(
        _AUTHORIZATION_HEADER_VALUE.search(normalized)
        or _contains_basic_credential(normalized)
        or _contains_opaque_bearer(normalized)
        or any(pattern.search(normalized) for pattern in value_patterns)
    )


def _contains_basic_credential(value: str) -> bool:
    for match in _BARE_BASIC_VALUE.finditer(value):
        token = match.group(1)
        padded = token + "=" * (-len(token) % 4)
        try:
            decoded = base64.b64decode(padded, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeError, ValueError):
            continue
        username, separator, password = decoded.partition(":")
        if separator and username and password and all(
            character.isprintable() for character in decoded
        ):
            return True
    return False


def _contains_opaque_bearer(value: str) -> bool:
    for match in _BARE_BEARER_VALUE.finditer(value):
        token = match.group(1)
        if len(token) < _MIN_BEARER_TOKEN_LENGTH:
            continue
        character_classes = (
            any(character.isalpha() for character in token),
            any(character.isdigit() for character in token),
            any(not character.isalnum() for character in token),
        )
        if sum(character_classes) >= 2:
            return True
    return False


def _is_nonempty_string_list(value: object) -> bool:
    return bool(
        isinstance(value, list)
        and value
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
    )


def _walk_sensitive_data(
    value: object,
    path: str = "",
    active_containers: set[int] | None = None,
    depth: int = 0,
) -> list[str]:
    """Recursively reject sensitive keys and credential-shaped string values."""
    if depth > MAX_CASE_NESTING_DEPTH:
        return [f"case exceeds maximum nesting depth at {path or 'case'}"]
    errors: list[str] = []
    active = active_containers if active_containers is not None else set()
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in active:
            return [f"case contains cyclic container at {path or 'case'}"]
        active.add(identity)
        try:
            for key, nested in value.items():
                safe_key = _safe_path_key(key)
                child_path = f"{path}.{safe_key}" if path else safe_key
                if _has_sensitive_key_segment(key):
                    errors.append(f"case contains sensitive key segment at {child_path}")
                errors.extend(
                    _walk_sensitive_data(nested, child_path, active, depth + 1)
                )
        finally:
            active.remove(identity)
    elif isinstance(value, list):
        identity = id(value)
        if identity in active:
            return [f"case contains cyclic container at {path or 'case'}"]
        active.add(identity)
        try:
            for index, nested in enumerate(value):
                errors.extend(
                    _walk_sensitive_data(
                        nested,
                        f"{path}[{index}]",
                        active,
                        depth + 1,
                    )
                )
        finally:
            active.remove(identity)
    elif isinstance(value, str) and _is_credential_shaped_value(value):
        errors.append(f"case contains credential-shaped value at {path}")
    return errors


def _has_identity_semantics(key: object) -> bool:
    if not isinstance(key, str):
        return False
    segments = _normalized_key(key).split("_")
    return bool(
        _IDENTITY_KEY_ALIASES.intersection(segments)
        or (
            {"candidate", "person", "subject"}.intersection(segments)
            and {"id", "ids", "identifier", "identifiers"}.intersection(segments)
        )
    )


def _identity_matches_candidate(value: object, candidate_id: str) -> bool:
    if isinstance(value, str):
        return value == candidate_id
    if isinstance(value, list):
        return bool(value) and all(item == candidate_id for item in value)
    return False


def _walk_identity_fields(
    value: object,
    candidate_id: str | None,
    benchmark_consent: bool,
    path: str = "",
    active_containers: set[int] | None = None,
    depth: int = 0,
) -> list[str]:
    """Recursively bind identity-bearing fields to the current candidate."""
    if depth > MAX_CASE_NESTING_DEPTH:
        return [f"case exceeds maximum nesting depth at {path or 'case'}"]
    errors: list[str] = []
    active = active_containers if active_containers is not None else set()
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in active:
            return [f"case contains cyclic container at {path or 'case'}"]
        active.add(identity)
        try:
            for key, nested in value.items():
                safe_key = _safe_path_key(key)
                child_path = f"{path}.{safe_key}" if path else safe_key
                if _has_identity_semantics(key):
                    if key == "benchmark_candidate_ids":
                        if _is_nonempty_string_list(nested) and not benchmark_consent:
                            errors.append(
                                f"{child_path} requires consent.benchmark=true"
                            )
                    elif candidate_id is not None and not _identity_matches_candidate(
                        nested, candidate_id
                    ):
                        errors.append(f"{child_path} must match case candidate_id")
                errors.extend(
                    _walk_identity_fields(
                        nested,
                        candidate_id,
                        benchmark_consent,
                        child_path,
                        active,
                        depth + 1,
                    )
                )
        finally:
            active.remove(identity)
    elif isinstance(value, list):
        identity = id(value)
        if identity in active:
            return [f"case contains cyclic container at {path or 'case'}"]
        active.add(identity)
        try:
            for index, nested in enumerate(value):
                errors.extend(
                    _walk_identity_fields(
                        nested,
                        candidate_id,
                        benchmark_consent,
                        f"{path}[{index}]",
                        active,
                        depth + 1,
                    )
                )
        finally:
            active.remove(identity)
    return errors


def _validate_evidence_label(
    location: str, record: Mapping[str, Any], errors: list[str]
) -> None:
    label = record.get("evidence_label")
    if label not in EVIDENCE_LABELS:
        allowed = ", ".join(EVIDENCE_LABELS)
        errors.append(f"{location}.evidence_label must be one of: {allowed}")


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        print("usage: validate_case.py CASE.json", file=sys.stderr)
        return 2
    try:
        case = json.loads(
            _read_case_input(arguments[0]),
            object_pairs_hook=_unique_json_object,
        )
    except _DuplicateJsonKeyError:
        print("invalid case file: duplicate JSON key", file=sys.stderr)
        return 2
    except _CaseInputTooLarge:
        print("invalid case file: input exceeds safe size limit", file=sys.stderr)
        return 2
    except OSError:
        print("invalid case file: unable to read input", file=sys.stderr)
        return 2
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        print(f"invalid case file: {error}", file=sys.stderr)
        return 2

    errors = validate_case(case)
    if errors:
        sys.stderr.write(_format_diagnostics(errors))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
