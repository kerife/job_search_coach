#!/usr/bin/env python3
"""Fail-closed validation for a candidate-supplied recruiter follow-through checkpoint."""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path

from private_prose_safety import safe_diagnostic_field_name
from private_input_loader import PrivateInputError, read_bounded_bytes

SCHEMA_VERSION = "private-recruiter-followthrough-checkpoint-v1"
TOP_LEVEL_FIELDS = frozenset({
    "schema_version", "artifact_kind", "locale", "source_receipt", "action_state",
    "observed_date", "next_measurement_event", "next_safe_action", "delivery",
})
SOURCE_FIELDS = frozenset({"id", "source_version", "event_type"})
STATES = frozenset({"accepted", "deferred", "declined", "completed"})
EVENTS = frozenset({"screen_prepared", "screen_attended", "interview_requested", "stop_decision", "unknown"})
DELIVERY = {
    "draft_only": True,
    "external_actions_authorized": False,
    "no_message_action": True,
    "no_calendar_action": True,
    "raw_event_retained": False,
    "local_save_mode": "disabled",
}
def _enum(value: object, allowed: set[str] | frozenset[str]) -> bool:
    return isinstance(value, str) and value in allowed
FORBIDDEN = re.compile(
    r"(?:raw|verbatim|quoted|original|inbound|texto\s+(?:crudo|original)|"
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|https?://|www\.|linkedin\.com/|"
    r"\+?\d[\d .()\-]{7,}\d|(?:candidate|candidato|recruiter|reclutador|"
    r"company|empresa|employer|empleador|contact|contacto)\s*(?::|is|es|named|llamad[oa])|"
    r"\b(?:send|message|contact|reach out|apply|submit|schedule|book|confirm|accept|call|email|"
    r"enviar|escribir|contactar|agendar|programar|reservar|confirmar|aceptar|llamar)\b|"
    r"\b(?:interview|entrevista|offer|oferta|fit|encaje|guarantee|garantiz|score|puntaje|"
    r"probability|probabilidad|answer|respuesta|action|accion)\b)", re.I)


class CheckpointLoadError(ValueError):
    pass


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CheckpointLoadError("duplicate JSON key")
        result[key] = value
    return result


def _assert_max_depth(value: object, maximum: int = 12, depth: int = 0) -> None:
    if depth > maximum:
        raise CheckpointLoadError("checkpoint input nesting exceeds safe limit")
    if isinstance(value, Mapping):
        for child in value.values():
            _assert_max_depth(child, maximum, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _assert_max_depth(child, maximum, depth + 1)


def _load_json(path: Path, label: str) -> dict[str, object]:
    try:
        raw_bytes = read_bounded_bytes(path, 64_000)
    except PrivateInputError as error:
        message = {
            "symlink": f"{label} input must not be a symlink",
            "too_large": f"{label} input exceeds safe size limit",
        }.get(error.reason, f"{label} input is unavailable")
        raise CheckpointLoadError(message) from error
    try:
        raw = raw_bytes.decode("utf-8")
    except UnicodeError as error:
        raise CheckpointLoadError(f"{label} input is not valid JSON") from error
    try:
        value = json.loads(raw, object_pairs_hook=_unique)
    except (json.JSONDecodeError, CheckpointLoadError) as error:
        raise CheckpointLoadError(f"{label} input is not valid JSON") from error
    _assert_max_depth(value)
    if not isinstance(value, dict):
        raise CheckpointLoadError(f"{label} input must be a JSON object")
    return value


def load_checkpoint(path: Path) -> dict[str, object]:
    return _load_json(path, "checkpoint")


def load_receipt(path: Path) -> dict[str, object]:
    return _load_json(path, "receipt")


def _outcome_validator():
    path = Path(__file__).with_name("validate_private_recruiter_conversion_outcome.py")
    spec = importlib.util.spec_from_file_location("conversion_outcome_validator", path)
    if spec is None or spec.loader is None:
        raise CheckpointLoadError("receipt validator is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _closed(value: object, path: str, fields: frozenset[str], errors: list[str]) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    for key in sorted(fields - set(value)):
        errors.append(f"missing required field: {path}.{key}")
    for key in sorted(set(value) - fields):
        errors.append(f"{path} has unsupported fields: {safe_diagnostic_field_name(key)}")
    return value


def _date(value: object, path: str, as_of: dt.date, errors: list[str]) -> dt.date | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        errors.append(f"{path} must use YYYY-MM-DD")
        return None
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path} is not a real calendar date")
        return None
    if parsed > as_of:
        errors.append(f"{path} cannot be after as_of")
    return parsed


def _walk_strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for child in value.values():
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)


def _expected_action(state: object, event: object) -> str | None:
    if state == "accepted":
        return "manual_reenter_private_prep"
    if state == "deferred":
        return "clarify_context_before_reply"
    if state == "declined":
        return "record_stop_decision"
    if state == "completed":
        if event in {"screen_prepared", "interview_requested"}:
            return "route_to_prepare-role-interviews"
        if event == "stop_decision":
            return "record_stop_decision"
        return "clarify_context_before_reply"
    return None


def validate_checkpoint(value: object, receipt: object, *, as_of: dt.date | None = None) -> list[str]:
    """Return sorted deterministic errors; empty means the checkpoint is valid."""
    errors: list[str] = []
    if receipt is None or not isinstance(receipt, Mapping):
        errors.append("receipt is required and must be a valid outcome")
        return errors
    try:
        validator = _outcome_validator()
        receipt_errors = validator.validate_outcome(receipt, as_of=as_of)
    except Exception:
        receipt_errors = ["receipt validator is unavailable"]
    if receipt_errors:
        errors.extend(f"receipt: {error}" for error in receipt_errors)
        return sorted(set(errors))
    item = _closed(value, "checkpoint", TOP_LEVEL_FIELDS, errors)
    if item is None:
        return sorted(set(errors))
    if item.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version has invalid value")
    if item.get("artifact_kind") != "private_recruiter_followthrough_checkpoint":
        errors.append("artifact_kind has invalid value")
    if not _enum(item.get("locale"), {"en", "es"}):
        errors.append("locale has invalid value")
    source = _closed(item.get("source_receipt"), "source_receipt", SOURCE_FIELDS, errors)
    if source is not None:
        if not isinstance(source.get("id"), str) or not re.fullmatch(r"D-\d{3}", source.get("id", "")):
            errors.append("source_receipt.id must use the D-000 identifier format")
        if not isinstance(source.get("source_version"), str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,31}", source.get("source_version", "")):
            errors.append("source_receipt.source_version has invalid value")
        if not _enum(source.get("event_type"), validator.EVENTS):
            errors.append("source_receipt.event_type has invalid value")
        for key in SOURCE_FIELDS:
            if source.get(key) != receipt.get({"id": "source_artifact_id", "source_version": "source_version", "event_type": "event_type"}[key]):
                errors.append(f"source_receipt.{key} does not match receipt")
    state = item.get("action_state")
    event = item.get("next_measurement_event")
    if not _enum(state, STATES):
        errors.append("action_state has invalid value")
    if not _enum(event, EVENTS):
        errors.append("next_measurement_event has invalid value")
    if _enum(state, {"accepted", "deferred", "declined"}) and event != "unknown":
        errors.append("non-completed action_state requires next_measurement_event=unknown")
    receipt_date = None
    try:
        receipt_date = dt.date.fromisoformat(str(receipt.get("event_date", "")))
    except ValueError:
        pass
    observed = _date(item.get("observed_date"), "observed_date", as_of or dt.date.today(), errors)
    if observed is not None and receipt_date is not None and observed < receipt_date:
        errors.append("observed_date cannot precede receipt date")
    if receipt.get("event_type") == "stop_decision" and not _enum(state, {"declined", "completed"}):
        errors.append("stop receipt requires declined or completed action_state")
    if _expected_action(state, event) != item.get("next_safe_action"):
        errors.append("next_safe_action does not match action_state and next_measurement_event")
    delivery = _closed(item.get("delivery"), "delivery", frozenset(DELIVERY), errors)
    if delivery is not None:
        for key, expected in DELIVERY.items():
            if type(delivery.get(key)) is not type(expected) or delivery.get(key) != expected:
                errors.append(f"delivery.{key} has immutable value")
    structural = {SCHEMA_VERSION, "private_recruiter_followthrough_checkpoint", "en", "es", *STATES, *EVENTS, *DELIVERY.values(), *validator.EVENTS, *validator.ACTION_BY_EVENT.values(), "observed_candidate_reported", "draft-v1"}
    prose = "\n".join(text for text in _walk_strings(item) if text not in structural and not re.fullmatch(r"(?:D|F)-\d{3}|\d{4}-\d{2}-\d{2}", text))
    if FORBIDDEN.search(prose):
        errors.append("checkpoint contains forbidden raw, identity, action, outcome, answer, or score prose")
    return sorted(set(errors))


def _date_arg(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must use YYYY-MM-DD") from error


def _cli(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate a private recruiter follow-through checkpoint.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--as-of", type=_date_arg, required=True)
    try:
        args = parser.parse_args(argv)
        item = load_checkpoint(args.input)
        receipt = load_receipt(args.receipt)
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    except CheckpointLoadError as error:
        print(str(error), file=sys.stderr)
        return 3
    errors = validate_checkpoint(item, receipt, as_of=args.as_of)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2
    print("valid private recruiter followthrough checkpoint")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
