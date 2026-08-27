#!/usr/bin/env python3
"""Fail-closed validation for a target-specific recruiter screen intake."""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "recruiter-target-screen-intake-v1"
ARTIFACT_KIND = "private_recruiter_target_screen_intake"
TOP_FIELDS = frozenset({
    "schema_version", "artifact_kind", "locale", "as_of_date", "source_gate_snapshot", "source_gate",
    "target_id", "target_decision", "intake", "checks", "readiness_decision",
    "measurement_event", "handoff", "delivery",
})
INTAKE_FIELDS = frozenset({"stated_stage", "vacancy_requirements", "candidate_fact_ids", "company_evidence_state", "source_date"})
CHECK_FIELDS = frozenset({"check", "status", "evidence_note"})
HANDOFF_FIELDS = frozenset({"next_safe_action", "selected_module", "manual_review_required", "draft_only", "external_actions_authorized", "no_message_action", "no_calendar_action"})
DELIVERY_FIELDS = frozenset({"draft_only", "external_actions_authorized", "local_save_mode", "raw_contact_details_retained"})
CHECKS = frozenset({"target_context", "proof_packet", "low_friction_ask", "screen_readiness"})
STAGES = frozenset({"recruiter_screen", "first_interview", "technical_screen"})
COMPANY_STATES = frozenset({"verified", "candidate_reported", "unknown"})
DECISIONS = frozenset({"advance", "clarify", "pause", "stop"})
READINESS = frozenset({"ready", "clarify_first", "stop"})
MEASUREMENTS = frozenset({"screen_context_submitted", "clarify_context", "stop_decision"})
SAFE_ACTIONS = frozenset({"manual_prepare_role_interviews_review", "collect_screen_intake", "stop_and_record"})
TARGET_ID = re.compile(r"^T-[0-9]{3}$")
FACT_ID = re.compile(r"^F-[0-9]{3}$")
VACANCY_ID = re.compile(r"^V-[0-9]{3}:\s+.+$")
SNAPSHOT = re.compile(r"^snap-shortlist-sha256-[0-9a-f]{64}$")


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise ValueError("invalid arguments")


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_screen_intake_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("screen intake dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PROSE = _sibling("private_prose_safety.py")
LOADER = _sibling("private_input_loader.py")
GATE = _sibling("validate_recruiter_target_decision_gate.py")
SHORTLIST = GATE.SHORTLIST


def _closed(value: object, path: str, fields: frozenset[str], errors: list[str]) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    if set(value) - fields:
        errors.append(f"{path} has unsupported fields")
    if fields - set(value):
        errors.append(f"{path} is missing required fields")
    return value


def _safe_text(value: object, path: str, errors: list[str], maximum: int) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or not PROSE.is_safe_prose_text(value) or SHORTLIST.RESTRICTED.search(value):
        errors.append(f"{path} must be bounded safe text")


def _date(value: object, path: str, errors: list[str], reference: dt.date | None) -> dt.date | None:
    if not isinstance(value, str):
        errors.append(f"{path} must be an ISO date")
        return None
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path} must be an ISO date")
        return None
    if reference is not None and parsed > reference:
        errors.append(f"{path} cannot be in the future")
    return parsed


def validate_screen_intake(value: object, *, source_gate: Mapping[str, object] | None = None, as_of: dt.date | None = None) -> list[str]:
    errors: list[str] = []
    item = _closed(value, "intake", TOP_FIELDS, errors)
    if item is None:
        return sorted(set(errors))
    if item.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version has invalid value")
    if item.get("artifact_kind") != ARTIFACT_KIND:
        errors.append("artifact_kind has invalid value")
    if item.get("locale") not in {"es", "en"}:
        errors.append("locale has invalid value")
    _date(item.get("as_of_date"), "as_of_date", errors, as_of)
    embedded_gate = item.get("source_gate")
    if not isinstance(embedded_gate, Mapping):
        errors.append("source_gate must be an object")
    elif source_gate is None:
        source_gate = embedded_gate
    snapshot = item.get("source_gate_snapshot")
    if not isinstance(snapshot, str) or not SNAPSHOT.fullmatch(snapshot):
        errors.append("source_gate_snapshot has invalid value")
    target_id = item.get("target_id")
    if not isinstance(target_id, str) or not TARGET_ID.fullmatch(target_id):
        errors.append("target_id has invalid value")
    target_decision = item.get("target_decision")
    if target_decision not in DECISIONS:
        errors.append("target_decision has invalid value")

    intake = _closed(item.get("intake"), "intake.context", INTAKE_FIELDS, errors)
    stage: object = None
    company_state: object = None
    facts: list[object] = []
    requirements: list[object] = []
    source_date: dt.date | None = None
    if intake is not None:
        stage = intake.get("stated_stage")
        if stage not in STAGES:
            errors.append("intake.stated_stage has invalid value")
        raw_requirements = intake.get("vacancy_requirements")
        if not isinstance(raw_requirements, list) or not 1 <= len(raw_requirements) <= 5:
            errors.append("intake.vacancy_requirements must contain one to five items")
        else:
            requirements = raw_requirements
            for index, requirement in enumerate(raw_requirements):
                if not isinstance(requirement, str) or not VACANCY_ID.fullmatch(requirement) or len(requirement) > 240 or not PROSE.is_safe_prose_text(requirement) or SHORTLIST.RESTRICTED.search(requirement):
                    errors.append(f"intake.vacancy_requirements[{index}] has invalid value")
        raw_facts = intake.get("candidate_fact_ids")
        if not isinstance(raw_facts, list) or not 1 <= len(raw_facts) <= 8 or len(set(raw_facts)) != len(raw_facts):
            errors.append("intake.candidate_fact_ids must contain one to eight unique IDs")
        else:
            facts = raw_facts
            if any(not isinstance(fact, str) or not FACT_ID.fullmatch(fact) for fact in raw_facts):
                errors.append("intake.candidate_fact_ids has invalid value")
        company_state = intake.get("company_evidence_state")
        if company_state not in COMPANY_STATES:
            errors.append("intake.company_evidence_state has invalid value")
        source_date = _date(intake.get("source_date"), "intake.source_date", errors, as_of)

    checks_value = item.get("checks")
    checks: list[Mapping[str, object]] = []
    if not isinstance(checks_value, list) or len(checks_value) != 4:
        errors.append("checks must contain exactly four items")
    else:
        seen: set[str] = set()
        for index, check_value in enumerate(checks_value):
            check = _closed(check_value, f"checks[{index}]", CHECK_FIELDS, errors)
            if check is None:
                continue
            name = check.get("check")
            if name not in CHECKS or name in seen:
                errors.append(f"checks[{index}].check has invalid or duplicated value")
            else:
                seen.add(name)
            if check.get("status") not in {"pass", "clarify", "stop"}:
                errors.append(f"checks[{index}].status has invalid value")
            _safe_text(check.get("evidence_note"), f"checks[{index}].evidence_note", errors, 240)
            checks.append(check)
        if seen != CHECKS:
            errors.append("checks must cover target_context, proof_packet, low_friction_ask, and screen_readiness")

    readiness = item.get("readiness_decision")
    if readiness not in READINESS:
        errors.append("readiness_decision has invalid value")
    status_by_check = {check.get("check"): check.get("status") for check in checks}
    has_stop = any(status == "stop" for status in status_by_check.values())
    all_pass = len(status_by_check) == 4 and all(status == "pass" for status in status_by_check.values())
    expected_readiness = "stop" if target_decision == "stop" or has_stop else ("ready" if target_decision == "advance" and all_pass and stage in STAGES and requirements and facts and company_state in {"verified", "candidate_reported"} else "clarify_first")
    if readiness != expected_readiness:
        errors.append("readiness_decision does not reconcile with target decision and checks")
    event = item.get("measurement_event")
    expected_event = "stop_decision" if expected_readiness == "stop" else ("screen_context_submitted" if expected_readiness == "ready" else "clarify_context")
    if event not in MEASUREMENTS or event != expected_event:
        errors.append("measurement_event does not match readiness_decision")

    handoff = _closed(item.get("handoff"), "handoff", HANDOFF_FIELDS, errors)
    if handoff is not None:
        expected_action = {"ready": "manual_prepare_role_interviews_review", "clarify_first": "collect_screen_intake", "stop": "stop_and_record"}[expected_readiness]
        if handoff.get("next_safe_action") != expected_action:
            errors.append("handoff.next_safe_action does not match readiness_decision")
        if handoff.get("selected_module") != "prepare-role-interviews":
            errors.append("handoff.selected_module has invalid value")
        for field, expected in (("manual_review_required", True), ("draft_only", True), ("external_actions_authorized", False), ("no_message_action", True), ("no_calendar_action", True)):
            if handoff.get(field) != expected:
                errors.append(f"handoff.{field} has immutable value")
    delivery = _closed(item.get("delivery"), "delivery", DELIVERY_FIELDS, errors)
    if delivery is not None:
        for field, expected in (("draft_only", True), ("external_actions_authorized", False), ("local_save_mode", "disabled"), ("raw_contact_details_retained", False)):
            if delivery.get(field) != expected:
                errors.append(f"delivery.{field} has immutable value")

    if source_gate is not None:
        gate_errors = GATE.validate_decision_gate(source_gate, as_of=as_of)
        if gate_errors:
            errors.append("source gate is invalid")
        elif snapshot != source_gate.get("source_snapshot"):
            errors.append("source_gate_snapshot does not match source gate")
        else:
            source_rows = source_gate.get("decision_rows")
            matching = next((row for row in source_rows if isinstance(row, Mapping) and row.get("target_id") == target_id), None) if isinstance(source_rows, list) else None
            if matching is None:
                errors.append("target_id does not exist in source gate")
            elif target_decision != matching.get("decision"):
                errors.append("target_decision does not match source gate")
    return sorted(set(errors))


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Validate a private recruiter target screen intake.")
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
        value = json.loads(LOADER.read_bounded_bytes(args.input, 128_000), object_pairs_hook=_unique)
        errors = validate_screen_intake(value, as_of=args.as_of)
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    if errors:
        print('{"error":{"code":"invalid_screen_intake"}}', file=sys.stderr)
        return 2
    print("valid recruiter target screen intake")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
