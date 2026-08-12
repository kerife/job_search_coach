#!/usr/bin/env python3
"""Fail-closed validation for a candidate-supplied recruiter event."""
from __future__ import annotations
import argparse, datetime as dt, importlib.util, json, re, sys
from collections.abc import Mapping
from pathlib import Path

from private_prose_safety import safe_diagnostic_field_name
try:
    from private_input_loader import PrivateInputError, read_bounded_bytes
except ModuleNotFoundError:
    _loader_spec = importlib.util.spec_from_file_location("_pgc_private_input_loader", Path(__file__).with_name("private_input_loader.py"))
    if _loader_spec is None or _loader_spec.loader is None:
        raise
    _loader_module = importlib.util.module_from_spec(_loader_spec)
    _loader_spec.loader.exec_module(_loader_module)
    PrivateInputError = _loader_module.PrivateInputError
    read_bounded_bytes = _loader_module.read_bounded_bytes

SCHEMA_VERSION = "private-recruiter-conversion-outcome-v1"
TOP_LEVEL_FIELDS = frozenset({"schema_version", "artifact_kind", "locale", "event_date", "event_type", "source_artifact_id", "source_version", "fact_ids", "observation_state", "next_safe_action", "delivery"})
EVENTS = frozenset({"contact_received", "reply_received", "referral_received", "screen_requested", "interview_requested", "stop_decision"})
ACTION_BY_EVENT = {"contact_received": "clarify_context_before_reply", "reply_received": "clarify_context_before_reply", "referral_received": "prepare_fact_checked_summary", "screen_requested": "route_to_prepare-role-interviews", "interview_requested": "route_to_prepare-role-interviews", "stop_decision": "record_stop_decision"}
DELIVERY = {"draft_only": True, "external_actions_authorized": False, "no_message_action": True, "no_calendar_action": True, "raw_event_retained": False, "local_save_mode": "disabled"}
def _enum(value: object, allowed: set[str] | frozenset[str]) -> bool:
    return isinstance(value, str) and value in allowed
FORBIDDEN = re.compile(r"(?:raw|verbatim|quoted|original|inbound|texto\s+(?:crudo|original)|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|https?://|www\.|linkedin\.com/|\+?\d[\d .()\-]{7,}\d|(?:company|empresa|employer|recruiter|reclutador|contact|contacto)\s*(?::|is|es|named|llamad[oa])|\b(?:send|message|contact|reach out|apply|submit|schedule|book|confirm|accept|call|email|enviar|escribir|contactar|agendar|programar|reservar|confirmar|aceptar|llamar)\b|\b(?:interview|entrevista|offer|oferta|fit|encaje|guarantee|garantiz|score|puntaje|probability|probabilidad)\b)", re.I)

class OutcomeLoadError(ValueError): pass
def _unique(pairs):
    out = {}
    for k, v in pairs:
        if k in out: raise OutcomeLoadError("duplicate JSON key")
        out[k] = v
    return out
def _assert_max_depth(value, maximum=12, depth=0):
    if depth > maximum: raise OutcomeLoadError("outcome input nesting exceeds safe limit")
    if isinstance(value, Mapping):
        for child in value.values(): _assert_max_depth(child, maximum, depth + 1)
    elif isinstance(value, list):
        for child in value: _assert_max_depth(child, maximum, depth + 1)
def load_outcome(path: Path) -> dict:
    try:
        raw_bytes = read_bounded_bytes(path, 32_000)
    except PrivateInputError as error:
        message = {"symlink": "outcome input must not be a symlink", "too_large": "outcome input exceeds safe size limit"}.get(error.reason, "outcome input is unavailable")
        raise OutcomeLoadError(message) from error
    try:
        raw = raw_bytes.decode("utf-8")
    except UnicodeError as error:
        raise OutcomeLoadError("outcome input is not valid JSON") from error
    try: value = json.loads(raw, object_pairs_hook=_unique)
    except (json.JSONDecodeError, OutcomeLoadError) as e: raise OutcomeLoadError("outcome input is not valid JSON") from e
    _assert_max_depth(value)
    if not isinstance(value, dict): raise OutcomeLoadError("outcome input must be a JSON object")
    return value
def _closed(value, path, fields, errors):
    if not isinstance(value, Mapping): errors.append(f"{path} must be an object"); return None
    for key in sorted(set(value) - fields): errors.append(f"{path} has unsupported fields: {safe_diagnostic_field_name(key)}")
    for key in sorted(fields - set(value)): errors.append(f"missing required field: {path}.{key}")
    return value
def _strings(value):
    if isinstance(value, str): yield value
    elif isinstance(value, Mapping):
        for child in value.values(): yield from _strings(child)
    elif isinstance(value, list):
        for child in value: yield from _strings(child)
def validate_outcome(value: object, *, today: dt.date | None = None, as_of: dt.date | None = None) -> list[str]:
    errors=[]; item=_closed(value, "outcome", TOP_LEVEL_FIELDS, errors)
    if item is None: return sorted(set(errors))
    if item.get("schema_version") != SCHEMA_VERSION: errors.append("schema_version has invalid value")
    if item.get("artifact_kind") != "private_recruiter_conversion_outcome": errors.append("artifact_kind has invalid value")
    if not _enum(item.get("locale"), {"en", "es"}): errors.append("locale has invalid value")
    date=item.get("event_date")
    parsed=None
    if not isinstance(date,str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date): errors.append("event_date must use YYYY-MM-DD")
    else:
        try: parsed=dt.date.fromisoformat(date)
        except ValueError: errors.append("event_date is not a real calendar date")
        reference_date = as_of or today or dt.date.today()
        if parsed and parsed > reference_date: errors.append("event_date cannot be in the future")
    event=item.get("event_type")
    if not _enum(event, EVENTS): errors.append("event_type has invalid value")
    elif item.get("next_safe_action") != ACTION_BY_EVENT[event]: errors.append("next_safe_action must match event_type")
    if not isinstance(item.get("source_artifact_id"),str) or not re.fullmatch(r"D-\d{3}", item.get("source_artifact_id","")): errors.append("source_artifact_id must use the D-000 identifier format")
    if not isinstance(item.get("source_version"),str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,31}", item.get("source_version","")): errors.append("source_version must be a bounded version label")
    facts=item.get("fact_ids")
    if not isinstance(facts,list) or not 1 <= len(facts) <= 3:
        errors.append("fact_ids must contain one through three unique F-000 identifiers")
    elif not all(isinstance(f, str) and re.fullmatch(r"F-\d{3}", f) for f in facts):
        errors.append("fact_ids must contain one through three unique F-000 identifiers")
    elif len(set(facts)) != len(facts):
        errors.append("fact_ids must contain one through three unique F-000 identifiers")
    if item.get("observation_state") != "observed_candidate_reported": errors.append("observation_state has immutable value")
    if not _enum(item.get("next_safe_action"), set(ACTION_BY_EVENT.values())): errors.append("next_safe_action has invalid value")
    delivery=_closed(item.get("delivery"), "delivery", frozenset(DELIVERY), errors)
    if delivery is not None:
        for key, expected in DELIVERY.items():
            if type(delivery.get(key)) is not type(expected) or delivery.get(key) != expected: errors.append(f"delivery.{key} has immutable value")
    structural = {SCHEMA_VERSION, "private_recruiter_conversion_outcome", "en", "es", *EVENTS, *ACTION_BY_EVENT.values(), "observed_candidate_reported", "draft-v1", *DELIVERY.values()}
    prose="\n".join(text for text in _strings(item) if text not in structural and not re.fullmatch(r"(?:D|F)-\d{3}|\d{4}-\d{2}-\d{2}", text))
    if FORBIDDEN.search(prose): errors.append("outcome contains forbidden raw, identity, action, outcome, score, or contact prose")
    return sorted(set(errors))
def _cli(argv=None):
    parser=argparse.ArgumentParser(description="Validate a private recruiter conversion outcome."); parser.add_argument("input",type=Path); parser.add_argument("--as-of",dest="as_of",type=lambda value: dt.date.fromisoformat(value), required=True, help="Reference date for deterministic future-date validation (YYYY-MM-DD).")
    try:
        args=parser.parse_args(argv)
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    try: item=load_outcome(args.input)
    except OutcomeLoadError as e: print(str(e),file=sys.stderr); return 3
    except (ValueError, argparse.ArgumentTypeError): print("--as-of must use YYYY-MM-DD",file=sys.stderr); return 3
    errors=validate_outcome(item, as_of=args.as_of)
    if errors:
        print("\n".join(errors),file=sys.stderr); return 2
    print("valid private recruiter conversion outcome"); return 0
if __name__ == "__main__": raise SystemExit(_cli())
