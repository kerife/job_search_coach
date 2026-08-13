#!/usr/bin/env python3
"""Validate the v2 status-only coverage ledger without retaining authorization."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("required dossier validator is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_v1 = _sibling("validate_executive_career_dossier.py")
_compat = _sibling("executive_career_dossier_v2_compat.py")
_loader = _sibling("private_input_loader.py")
_prose = _sibling("private_prose_safety.py")

CANONICAL_PROFILE_SECTIONS = _compat.CANONICAL_PROFILE_SECTIONS
project_v2_to_v1 = _compat.project_v2_to_v1
DossierLoadError = _v1.DossierLoadError
PrivateInputError = _loader.PrivateInputError
read_bounded_bytes = _loader.read_bounded_bytes
format_bounded_diagnostics = _prose.format_bounded_diagnostics

SCHEMA_VERSION = "executive-career-dossier-v2"
TOP_FIELDS = frozenset(set(_v1.TOP_FIELDS) | {"section_coverage"})
ROW_FIELDS = frozenset({"section", "availability", "evidence_state", "reason", "inspection_request"})
REQUEST_FIELDS = frozenset({"access_type", "decision", "scope", "carry_forward"})
PRIORITY_FIELDS = frozenset({
    "rank", "title", "problem", "why_now", "action", "timebox_minutes", "done_when",
    "evidence_state", "evidence_ids", "dimensions", "target_section", "coach_observation",
    "why_it_matters", "coach_prompt", "client_template", "privacy_boundary",
})
TEMPLATE_IDS = frozenset({"context_action_result_v1", "positioning_evidence_v1", "proof_scope_result_v1"})
TEMPLATE_KEYS = frozenset({"target_role", "specialty", "context", "action", "scope", "result", "metric", "evidence_source"})
MATRIX = {
    "inspected_present": ("verified", "inspected_content_available", None),
    "inspected_absent": ("verified", "inspected_section_absent", None),
    "candidate_supplied": ("candidate_reported", "candidate_material_supplied", None),
    "unavailable": ("unknown", None, "request"),
}
UNAVAILABLE_DECISIONS = {
    "authorization_required": "pending_response",
    "inspection_declined": "declined_for_session",
    "authorized_inspection_failed": "authorized_inspection_failed",
}


def _closed(value: object, path: str, fields: frozenset[str], errors: list[str]) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    if set(value) - fields:
        errors.append(f"{path} has unsupported fields")
    if fields - set(value):
        errors.append(f"{path} is missing required fields")
    return value


def _valid_text(value: object, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value or len(value) > 500:
        errors.append(f"{path} must be bounded text")


def _validate_private_prose(value: object, path: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        return
    if (
        re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", value)
        or re.search(r"(?:https?://|www\.)", value, re.I)
        or re.search(r"(?:^|\s)(?:/[A-Za-z]|[A-Za-z]:[\\/])", value)
        or _prose.contains_unicode_controls(value)
    ):
        errors.append(f"{path} contains forbidden private value")


def _validate_rows(root: Mapping[str, object], errors: list[str]) -> dict[str, Mapping[str, object]]:
    rows = root.get("section_coverage")
    if not isinstance(rows, list):
        errors.append("section_coverage must be an array")
        return {}
    sections = tuple(row.get("section") if isinstance(row, Mapping) else None for row in rows)
    if sections != CANONICAL_PROFILE_SECTIONS:
        errors.append("section_coverage must contain every canonical section exactly once in canonical order")
    evidence_by_section: dict[str, list[Mapping[str, object]]] = {}
    evidence = root.get("evidence")
    if isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, Mapping) and isinstance(item.get("profile_section"), str):
                evidence_by_section.setdefault(item["profile_section"], []).append(item)
    output: dict[str, Mapping[str, object]] = {}
    for index, item in enumerate(rows):
        path = f"section_coverage[{index}]"
        if not isinstance(item, Mapping):
            errors.append(f"{path} must be an object")
            continue
        if set(item) - ROW_FIELDS:
            errors.append(f"{path} has unsupported fields")
        section = item.get("section")
        if not isinstance(section, str) or section not in CANONICAL_PROFILE_SECTIONS:
            errors.append(f"{path}.section has invalid section")
            continue
        output[section] = item
        availability = item.get("availability")
        state = item.get("evidence_state")
        reason = item.get("reason")
        request = item.get("inspection_request")
        if availability not in MATRIX:
            errors.append(f"{path}.availability has invalid availability")
            continue
        expected_state, expected_reason, request_type = MATRIX[availability]
        if state != expected_state:
            errors.append(f"{path} has invalid persisted state")
        if availability == "unavailable":
            if reason not in UNAVAILABLE_DECISIONS:
                errors.append(f"{path}.reason has invalid unavailable reason")
            if not isinstance(request, Mapping):
                errors.append(f"{path} unavailable section requires inspection_request")
                continue
            request_row = _closed(request, f"{path}.inspection_request", REQUEST_FIELDS, errors)
            if request_row is None:
                continue
            if request_row.get("access_type") != "read_only_visible_section_inspection":
                errors.append(f"{path}.inspection_request has invalid access_type")
            if request_row.get("scope") != "current_session_only":
                errors.append(f"{path}.inspection_request has invalid scope")
            if request_row.get("carry_forward") is not False:
                errors.append(f"{path}.inspection_request must not carry forward")
            if reason in UNAVAILABLE_DECISIONS and request_row.get("decision") != UNAVAILABLE_DECISIONS[reason]:
                errors.append(f"{path}.inspection_request decision does not match reason")
        else:
            required = ROW_FIELDS - {"inspection_request"}
            _closed(item, path, required, errors)
            if reason != expected_reason:
                errors.append(f"{path} has invalid persisted state")
            if request is not None:
                errors.append(f"{path} inspected section forbids inspection_request")
            if availability in {"inspected_present", "candidate_supplied"} and not evidence_by_section.get(section):
                errors.append(f"{path} requires evidence for its profile_section")
    scope = root.get("evidence_scope")
    if isinstance(scope, Mapping):
        for field, forbidden in (("inspected_sections", "unavailable"), ("unavailable_sections", "inspected")):
            listed = scope.get(field)
            if isinstance(listed, list):
                for section in listed:
                    row = output.get(section) if isinstance(section, str) else None
                    if row is None:
                        continue
                    availability = row.get("availability")
                    bad = availability == "unavailable" if forbidden == "unavailable" else availability != "unavailable"
                    if bad:
                        index = CANONICAL_PROFILE_SECTIONS.index(section)
                        errors.append(f"section_coverage[{index}] contradicts evidence_scope.{field}")
    return output


def _validate_priorities(root: Mapping[str, object], errors: list[str]) -> None:
    priorities = root.get("priorities")
    evidence = root.get("evidence")
    evidence_sections: dict[str, object] = {}
    if isinstance(evidence, list):
        for evidence_index, record in enumerate(evidence):
            if not isinstance(record, Mapping):
                continue
            profile_section = record.get("profile_section")
            if "profile_section" not in record or (
                profile_section is not None
                and (not isinstance(profile_section, str) or profile_section not in CANONICAL_PROFILE_SECTIONS)
            ):
                errors.append(f"evidence[{evidence_index}].profile_section has invalid profile section")
            identifier = record.get("id")
            if isinstance(identifier, str):
                evidence_sections[identifier] = profile_section
    if not isinstance(priorities, list):
        return
    for index, item in enumerate(priorities):
        path = f"priorities[{index}]"
        row = _closed(item, path, PRIORITY_FIELDS, errors)
        if row is None:
            continue
        target = row.get("target_section")
        if target not in CANONICAL_PROFILE_SECTIONS:
            errors.append(f"{path}.target_section has invalid section")
        for field in ("coach_observation", "why_it_matters", "coach_prompt", "privacy_boundary"):
            _valid_text(row.get(field), f"{path}.{field}", errors)
            if isinstance(row.get(field), str):
                errors.extend(
                    f"{path}.{field} {error}" for error in _v1._privacy_errors(row[field])
                )
            _validate_private_prose(row.get(field), f"{path}.{field}", errors)
        if row.get("privacy_boundary") != "no_raw_profile_text_or_private_values":
            errors.append(f"{path}.privacy_boundary has invalid boundary")
        template = _closed(row.get("client_template"), f"{path}.client_template", frozenset({"template_id", "field_keys"}), errors)
        if template is not None:
            if template.get("template_id") not in TEMPLATE_IDS:
                errors.append(f"{path}.client_template has invalid template_id")
            keys = template.get("field_keys")
            if (
                not isinstance(keys, list)
                or not 1 <= len(keys) <= 5
                or any(not isinstance(key, str) or key not in TEMPLATE_KEYS for key in keys)
                or (isinstance(keys, list) and len(keys) != len(set(keys)))
            ):
                errors.append(f"{path}.client_template.field_keys has invalid keys")
        ids = row.get("evidence_ids")
        if isinstance(ids, list) and isinstance(target, str) and any(
            not isinstance(identifier, str) or evidence_sections.get(identifier) != target
            for identifier in ids
        ):
            errors.append(f"{path}.evidence_ids must bind to the target section")


def validate_dossier(value: object) -> list[str]:
    """Return fixed diagnostics for v2 plus the established v1 semantics."""
    if not isinstance(value, Mapping):
        return ["v2 dossier must be an object"]
    errors: list[str] = []
    if set(value) - TOP_FIELDS:
        errors.append("v2 dossier has unsupported fields")
    if set(value) != TOP_FIELDS:
        errors.append("v2 dossier is missing required fields")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be executive-career-dossier-v2")
    errors.extend(_v1.validate_dossier(project_v2_to_v1(value)))
    _validate_rows(value, errors)
    _validate_priorities(value, errors)
    errors.extend(_v1._scan_privacy(value))
    return sorted(set(errors))


def select_pending_inspection_section(dossier: Mapping[str, object]) -> str | None:
    """Return one read-only pending section, preferring ranked coaching targets."""
    rows = dossier.get("section_coverage")
    pending: set[str] = set()
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, Mapping) and isinstance(row.get("section"), str):
                request = row.get("inspection_request")
                if (
                    row.get("availability") == "unavailable"
                    and isinstance(request, Mapping)
                    and request.get("decision") == "pending_response"
                ):
                    pending.add(row["section"])
    priorities = dossier.get("priorities")
    if isinstance(priorities, list):
        for priority in sorted((item for item in priorities if isinstance(item, Mapping)), key=lambda item: item.get("rank") if isinstance(item.get("rank"), int) else 99):
            target = priority.get("target_section")
            if target in pending:
                return target
    return next((section for section in CANONICAL_PROFILE_SECTIONS if section in pending), None)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, nested in pairs:
        if key in result:
            raise DossierLoadError("duplicate JSON key")
        result[key] = nested
    return result


def _assert_max_depth(value: object, maximum: int, depth: int = 0) -> None:
    if depth > maximum:
        raise DossierLoadError("v2 dossier exceeds maximum nesting depth")
    if isinstance(value, Mapping):
        for nested in value.values():
            _assert_max_depth(nested, maximum, depth + 1)
    elif isinstance(value, list):
        for nested in value:
            _assert_max_depth(nested, maximum, depth + 1)


def load_dossier(path: Path) -> dict[str, object]:
    try:
        raw = read_bounded_bytes(path, 256 * 1024)
    except PrivateInputError as error:
        message = {"symlink": "v2 dossier input must not be a symlink", "too_large": "v2 dossier exceeds 256 KiB"}.get(error.reason, "cannot read v2 dossier")
        raise DossierLoadError(message) from error
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, DossierLoadError) as error:
        if isinstance(error, DossierLoadError):
            raise
        raise DossierLoadError("v2 dossier must be valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise DossierLoadError("v2 dossier must be a JSON object")
    _assert_max_depth(value, 12)
    return value


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an executive career dossier v2.")
    parser.add_argument("dossier", type=Path)
    arguments = parser.parse_args(argv)
    try:
        dossier = load_dossier(arguments.dossier)
    except DossierLoadError as error:
        print(str(error), file=sys.stderr)
        return 2
    errors = validate_dossier(dossier)
    if errors:
        sys.stderr.write(format_bounded_diagnostics(errors))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
