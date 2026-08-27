#!/usr/bin/env python3
"""Fail-closed validation for the private recruiter target decision gate."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "recruiter-target-decision-gate-v1"
ARTIFACT_KIND = "private_recruiter_target_decision_gate"
SNAPSHOT_PREFIX = "snap-shortlist-sha256-"


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise ValueError("invalid arguments")
TOP_FIELDS = frozenset({
    "schema_version", "artifact_kind", "locale", "as_of_date", "source_shortlist",
    "source_snapshot", "decision_counts", "decision_rows", "screen_context", "handoff", "delivery",
})
ROW_FIELDS = frozenset({
    "target_id", "decision", "decision_reason", "contactability_status", "missing_context",
    "recommended_draft_type", "first_contact_strategy", "warm_intro_readiness", "next_safe_action",
    "draft_only", "consent", "authorization_required", "no_message_action", "no_calendar_action",
})
COUNT_FIELDS = frozenset({"advance", "clarify", "pause", "stop"})
SCREEN_FIELDS = frozenset({"vacancy_summary", "confirmed_fact_summary"})
HANDOFF_FIELDS = frozenset({
    "screen_context_state", "next_safe_action", "manual_review_required", "selected_module",
    "draft_only", "external_actions_authorized", "no_message_action", "no_calendar_action",
})
DELIVERY_FIELDS = frozenset({"draft_only", "external_actions_authorized", "local_save_mode", "raw_contact_details_retained"})
SAFE_ACTIONS = frozenset({"collect_screen_context", "prepare_role_interviews_review"})
DECISIONS = frozenset({"advance", "clarify", "pause", "stop"})


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_gate_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("decision gate dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SHORTLIST = _sibling("validate_recruiter_target_shortlist.py")
PROSE = _sibling("private_prose_safety.py")
LOADER = _sibling("private_input_loader.py")


def snapshot_for_shortlist(shortlist: Mapping[str, object]) -> str:
    canonical = json.dumps(shortlist, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return SNAPSHOT_PREFIX + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _closed(value: object, path: str, fields: frozenset[str], errors: list[str]) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    if set(value) - fields:
        errors.append(f"{path} has unsupported fields")
    if fields - set(value):
        errors.append(f"{path} is missing required fields")
    return value


def _text(value: object, path: str, errors: list[str], maximum: int) -> bool:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or not PROSE.is_safe_prose_text(value):
        errors.append(f"{path} must be bounded safe text")
        return False
    return True


def _date(value: object, path: str, errors: list[str], reference: dt.date | None) -> None:
    if not isinstance(value, str):
        errors.append(f"{path} must be an ISO date")
        return
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path} must be an ISO date")
        return
    if reference is not None and parsed > reference:
        errors.append(f"{path} cannot be in the future")


def validate_decision_gate(value: object, *, as_of: dt.date | None = None) -> list[str]:
    errors: list[str] = []
    item = _closed(value, "gate", TOP_FIELDS, errors)
    if item is None:
        return sorted(set(errors))
    if item.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version has invalid value")
    if item.get("artifact_kind") != ARTIFACT_KIND:
        errors.append("artifact_kind has invalid value")
    locale = item.get("locale")
    if locale not in {"es", "en"}:
        errors.append("locale has invalid value")
    _date(item.get("as_of_date"), "as_of_date", errors, as_of)

    source = item.get("source_shortlist")
    if not isinstance(source, Mapping):
        errors.append("source_shortlist must be an object")
        source = None
    else:
        errors.extend(SHORTLIST.validate_shortlist(source, as_of=as_of))
    snapshot = item.get("source_snapshot")
    if not isinstance(snapshot, str) or not snapshot.startswith(SNAPSHOT_PREFIX) or len(snapshot) != len(SNAPSHOT_PREFIX) + 64:
        errors.append("source_snapshot has invalid value")
    elif source is not None and snapshot_for_shortlist(source) != snapshot:
        errors.append("source_shortlist snapshot does not match source_snapshot")

    counts = _closed(item.get("decision_counts"), "decision_counts", COUNT_FIELDS, errors)
    rows_value = item.get("decision_rows")
    rows: list[Mapping[str, object]] = []
    if not isinstance(rows_value, list) or not 3 <= len(rows_value) <= 6:
        errors.append("decision_rows must contain three to six rows")
    else:
        seen: set[str] = set()
        for index, row_value in enumerate(rows_value):
            row = _closed(row_value, f"decision_rows[{index}]", ROW_FIELDS, errors)
            if row is None:
                continue
            target_id = row.get("target_id")
            if not isinstance(target_id, str) or target_id in seen:
                errors.append(f"decision_rows[{index}].target_id is invalid or duplicated")
            else:
                seen.add(target_id)
            if row.get("decision") not in DECISIONS:
                errors.append(f"decision_rows[{index}].decision has invalid value")
            if row.get("contactability_status") not in {"contactable", "context_needed", "do_not_contact"}:
                errors.append(f"decision_rows[{index}].contactability_status has invalid value")
            if row.get("recommended_draft_type") not in {"connection_note", "recruiter_interest", "referral_request", "none"}:
                errors.append(f"decision_rows[{index}].recommended_draft_type has invalid value")
            for field, maximum in (("decision_reason", 300), ("missing_context", 300), ("first_contact_strategy", 300), ("warm_intro_readiness", 240)):
                _text(row.get(field), f"decision_rows[{index}].{field}", errors, maximum)
            action = row.get("next_safe_action")
            if action not in {"draft_only_review", "collect_recipient_context", "record_observation_only"}:
                errors.append(f"decision_rows[{index}].next_safe_action has invalid value")
            for field, expected in (("draft_only", True), ("consent", "not_granted"), ("authorization_required", True), ("no_message_action", True), ("no_calendar_action", True)):
                if row.get(field) != expected:
                    errors.append(f"decision_rows[{index}].{field} has immutable value")
            rows.append(row)

    if source is not None:
        source_rows = source.get("targets")
        if isinstance(source_rows, list) and len(rows) == len(source_rows):
            source_ids = [row.get("target_id") for row in source_rows if isinstance(row, Mapping)]
            row_ids = [row.get("target_id") for row in rows]
            if row_ids != source_ids:
                errors.append("decision_rows must preserve source target order")
            for index, row in enumerate(rows):
                source_row = source_rows[index]
                if isinstance(source_row, Mapping) and row.get("decision") != source_row.get("decision"):
                    errors.append(f"decision_rows[{index}].decision must match source shortlist")

    if counts is not None:
        expected = {decision: sum(1 for row in rows if row.get("decision") == decision) for decision in COUNT_FIELDS}
        if any(type(counts.get(key)) is not int for key in COUNT_FIELDS):
            errors.append("decision_counts must contain integer values")
        elif {key: counts.get(key) for key in COUNT_FIELDS} != expected:
            errors.append("decision_counts do not reconcile with decision rows")

    screen = item.get("screen_context")
    if screen is not None:
        screen = _closed(screen, "screen_context", SCREEN_FIELDS, errors)
        if screen is not None:
            _text(screen.get("vacancy_summary"), "screen_context.vacancy_summary", errors, 280)
            _text(screen.get("confirmed_fact_summary"), "screen_context.confirmed_fact_summary", errors, 280)

    handoff = _closed(item.get("handoff"), "handoff", HANDOFF_FIELDS, errors)
    if handoff is not None:
        state = handoff.get("screen_context_state")
        if state not in {"missing", "provided"}:
            errors.append("handoff.screen_context_state has invalid value")
        action = handoff.get("next_safe_action")
        if action not in SAFE_ACTIONS:
            errors.append("handoff.next_safe_action has invalid value")
        expected_state = "provided" if screen is not None else "missing"
        expected_action = "prepare_role_interviews_review" if screen is not None else "collect_screen_context"
        if state != expected_state or action != expected_action:
            errors.append("handoff state does not match screen_context")
        if handoff.get("manual_review_required") is not True:
            errors.append("handoff.manual_review_required must be true")
        if handoff.get("selected_module") != "prepare-role-interviews":
            errors.append("handoff.selected_module has invalid value")
        for field, expected in (("draft_only", True), ("external_actions_authorized", False), ("no_message_action", True), ("no_calendar_action", True)):
            if handoff.get(field) != expected:
                errors.append(f"handoff.{field} has immutable value")

    delivery = _closed(item.get("delivery"), "delivery", DELIVERY_FIELDS, errors)
    if delivery is not None:
        expected_delivery = {"draft_only": True, "external_actions_authorized": False, "local_save_mode": "disabled", "raw_contact_details_retained": False}
        for field, expected in expected_delivery.items():
            if delivery.get(field) != expected:
                errors.append(f"delivery.{field} has immutable value")
    return sorted(set(errors))


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Validate a private recruiter target decision gate.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--as-of", required=True, type=dt.date.fromisoformat)
    try:
        args = parser.parse_args(argv)
        def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
            result: dict[str, object] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate JSON key")
                result[key] = value
            return result
        value = json.loads(
            LOADER.read_bounded_bytes(args.input, 128_000),
            object_pairs_hook=_unique,
        )
        errors = validate_decision_gate(value, as_of=args.as_of)
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    if errors:
        print('{"error":{"code":"invalid_decision_gate"}}', file=sys.stderr)
        return 2
    print("valid recruiter target decision gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
