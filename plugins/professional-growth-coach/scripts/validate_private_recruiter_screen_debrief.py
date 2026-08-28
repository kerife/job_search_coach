#!/usr/bin/env python3
"""Fail-closed validation for a private post-screen debrief."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "private-recruiter-screen-debrief-v1"
ARTIFACT_KIND = "private_recruiter_screen_debrief"
TOP_FIELDS = frozenset({
    "schema_version", "artifact_kind", "locale", "observed_date", "source_receipt",
    "source_checkpoint", "source_intake", "source_snapshot", "coverage", "unknown_topics",
    "facts_used", "decision", "measurement_event", "replay_fingerprint", "handoff", "delivery",
})
COVERAGE_FIELDS = frozenset({"topic", "status", "note"})
HANDOFF_FIELDS = frozenset({
    "next_safe_action", "manual_review_required", "draft_only", "external_actions_authorized",
    "no_message_action", "no_calendar_action",
})
DELIVERY_FIELDS = frozenset({
    "draft_only", "external_actions_authorized", "no_message_action", "no_calendar_action",
    "raw_transcript_retained", "local_save_mode",
})
TOPICS = frozenset({"requirement", "scope", "team_context"})
STATUSES = frozenset({"discussed", "not_discussed", "unclear"})
DECISIONS = frozenset({"continue_review", "pause", "stop"})
MEASUREMENTS = frozenset({"next_stage_review", "debrief_context", "stop_decision"})
ACTIONS = frozenset({"manual_prepare_next_stage_review", "collect_debrief_context", "record_stop_decision"})
FACT_ID = re.compile(r"^F-[0-9]{3}$")
SNAPSHOT = re.compile(r"^snap-shortlist-sha256-[0-9a-f]{64}$")
REPLAY = re.compile(r"^replay-debrief-sha256-[0-9a-f]{64}$")
RESTRICTED = re.compile(
    r"(?:https?://|www\.|linkedin\.com/|mailto:|file:|ssh:|ftp:|javascript:|data:|"
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|\+?\d[\d .()\-]{7,}\d|"
    r"\b(?:send|message|contact|reach out|schedule|book|call|email|enviar|escribir|contactar|"
    r"agendar|programar|reservar|llamar|mensaje|contacto)\b|"
    r"\b(?:raw|verbatim|quoted|original|texto crudo|respuesta|answer|score|puntaje|"
    r"probability|probabilidad|guarantee|garantiz)\b)",
    re.I,
)


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_debrief_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("screen debrief dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CHECKPOINT = _sibling("validate_private_recruiter_followthrough_checkpoint.py")
INTAKE = _sibling("validate_recruiter_target_screen_intake.py")
PROSE = _sibling("private_prose_safety.py")
LOADER = _sibling("private_input_loader.py")


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise ValueError("invalid arguments")


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


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
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or not PROSE.is_safe_prose_text(value) or RESTRICTED.search(value):
        errors.append(f"{path} must be bounded safe text")


def _date(value: object, path: str, errors: list[str], as_of: dt.date | None) -> dt.date | None:
    if not isinstance(value, str):
        errors.append(f"{path} must be an ISO date")
        return None
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path} must be an ISO date")
        return None
    if as_of is not None and parsed > as_of:
        errors.append(f"{path} cannot be in the future")
    return parsed


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def replay_fingerprint(value: Mapping[str, object]) -> str:
    payload = {
        "source_receipt": value.get("source_receipt"),
        "source_snapshot": value.get("source_snapshot"),
        "target_binding": value.get("source_checkpoint", {}).get("target_binding") if isinstance(value.get("source_checkpoint"), Mapping) else None,
        "observed_date": value.get("observed_date"),
        "coverage": value.get("coverage"),
        "unknown_topics": value.get("unknown_topics"),
        "facts_used": value.get("facts_used"),
        "decision": value.get("decision"),
        "measurement_event": value.get("measurement_event"),
    }
    return "replay-debrief-sha256-" + hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def validate_screen_debrief(
    value: object,
    receipt: Mapping[str, object] | None,
    intake: Mapping[str, object] | None,
    *,
    checkpoint: Mapping[str, object] | None = None,
    as_of: dt.date | None = None,
) -> list[str]:
    errors: list[str] = []
    if as_of is not None and as_of > dt.date.today():
        errors.append("as_of cannot be in the future")
    item = _closed(value, "debrief", TOP_FIELDS, errors)
    if item is None:
        return sorted(set(errors))
    if item.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version has invalid value")
    if item.get("artifact_kind") != ARTIFACT_KIND:
        errors.append("artifact_kind has invalid value")
    if not isinstance(item.get("locale"), str) or item.get("locale") not in {"en", "es"}:
        errors.append("locale has invalid value")
    observed = _date(item.get("observed_date"), "observed_date", errors, as_of)

    embedded_receipt = item.get("source_receipt")
    embedded_checkpoint = item.get("source_checkpoint")
    embedded_intake = item.get("source_intake")
    if not isinstance(embedded_receipt, Mapping):
        errors.append("source_receipt must be an object")
    if not isinstance(embedded_checkpoint, Mapping):
        errors.append("source_checkpoint must be an object")
    if not isinstance(embedded_intake, Mapping):
        errors.append("source_intake must be an object")

    if receipt is None or not isinstance(receipt, Mapping):
        errors.append("receipt is required")
    else:
        receipt_errors = CHECKPOINT._outcome_validator().validate_outcome(receipt, as_of=as_of)
        if receipt_errors:
            errors.append("source receipt is invalid")
        elif receipt.get("event_type") not in {"screen_requested", "interview_requested"}:
            errors.append("source receipt is not a requested screen")
        if isinstance(embedded_receipt, Mapping) and _canonical(embedded_receipt) != _canonical(receipt):
            errors.append("source_receipt does not match receipt")
    if checkpoint is None and isinstance(embedded_checkpoint, Mapping):
        checkpoint = embedded_checkpoint
    if checkpoint is None or not isinstance(checkpoint, Mapping):
        errors.append("checkpoint is required")
    else:
        checkpoint_errors = CHECKPOINT.validate_checkpoint(checkpoint, receipt, as_of=as_of)
        if checkpoint_errors:
            errors.append("source checkpoint is invalid")
        if isinstance(embedded_checkpoint, Mapping) and _canonical(embedded_checkpoint) != _canonical(checkpoint):
            errors.append("source_checkpoint does not match checkpoint")
        if checkpoint.get("action_state") != "completed" or checkpoint.get("next_measurement_event") != "screen_attended" or checkpoint.get("next_safe_action") != "debrief_after_screen":
            errors.append("source checkpoint is not a completed screen_attended checkpoint")
        binding = checkpoint.get("target_binding")
        if not isinstance(binding, Mapping):
            errors.append("source checkpoint target_binding is required")
        elif isinstance(intake, Mapping) and (
            binding.get("target_id") != intake.get("target_id")
            or binding.get("source_gate_snapshot") != intake.get("source_gate_snapshot")
        ):
            errors.append("source checkpoint target_binding does not match source intake")
    if intake is None and isinstance(embedded_intake, Mapping):
        intake = embedded_intake
    if intake is None or not isinstance(intake, Mapping):
        errors.append("intake is required")
    else:
        intake_errors = INTAKE.validate_screen_intake(intake, as_of=as_of)
        if intake_errors:
            errors.append("source intake is invalid")
        if isinstance(embedded_intake, Mapping) and _canonical(embedded_intake) != _canonical(intake):
            errors.append("source_intake does not match intake")
        if intake.get("readiness_decision") != "ready" or intake.get("target_decision") != "advance":
            errors.append("source intake must be ready for an advance target")
        if item.get("locale") != intake.get("locale"):
            errors.append("locale does not match source intake")

    snapshot = item.get("source_snapshot")
    if not isinstance(snapshot, str) or not SNAPSHOT.fullmatch(snapshot):
        errors.append("source_snapshot has invalid value")
    elif isinstance(intake, Mapping) and snapshot != intake.get("source_gate_snapshot"):
        errors.append("source_snapshot does not match source intake")
    if observed is not None and isinstance(checkpoint, Mapping):
        try:
            checkpoint_date = dt.date.fromisoformat(str(checkpoint.get("observed_date")))
            if observed < checkpoint_date:
                errors.append("observed_date cannot precede checkpoint date")
        except ValueError:
            pass

    coverage_value = item.get("coverage")
    coverage: list[Mapping[str, object]] = []
    if not isinstance(coverage_value, list) or len(coverage_value) != 3:
        errors.append("coverage must contain exactly three items")
    else:
        seen: set[str] = set()
        for index, raw in enumerate(coverage_value):
            row = _closed(raw, f"coverage[{index}]", COVERAGE_FIELDS, errors)
            if row is None:
                continue
            topic = row.get("topic")
            if not isinstance(topic, str) or topic not in TOPICS or topic in seen:
                errors.append(f"coverage[{index}].topic has invalid or duplicated value")
            else:
                seen.add(topic)
            status = row.get("status")
            if not isinstance(status, str) or status not in STATUSES:
                errors.append(f"coverage[{index}].status has invalid value")
            _safe_text(row.get("note"), f"coverage[{index}].note", errors, 240)
            coverage.append(row)
        if seen != TOPICS:
            errors.append("coverage must cover requirement, scope, and team_context")

    unknown_value = item.get("unknown_topics")
    unknown_topics: list[object] = []
    if not isinstance(unknown_value, list) or len(unknown_value) > 5:
        errors.append("unknown_topics must contain zero to five items")
    else:
        unknown_topics = unknown_value
        for index, topic in enumerate(unknown_value):
            _safe_text(topic, f"unknown_topics[{index}]", errors, 180)

    facts_value = item.get("facts_used")
    facts: list[object] = []
    if not isinstance(facts_value, list) or not 1 <= len(facts_value) <= 8 or any(not isinstance(fact, str) for fact in facts_value) or len(set(facts_value)) != len(facts_value):
        errors.append("facts_used must contain one to eight unique fact IDs")
    else:
        facts = facts_value
        if any(not FACT_ID.fullmatch(fact) for fact in facts_value):
            errors.append("facts_used has invalid value")
        if isinstance(intake, Mapping):
            intake_facts = intake.get("intake", {}).get("candidate_fact_ids", []) if isinstance(intake.get("intake"), Mapping) else []
            if any(fact not in intake_facts for fact in facts_value):
                errors.append("facts_used must be drawn from source intake")

    decision = item.get("decision")
    if not isinstance(decision, str) or decision not in DECISIONS:
        errors.append("decision has invalid value")
    statuses = [row.get("status") for row in coverage if isinstance(row.get("status"), str)]
    complete = len(statuses) == 3 and all(status == "discussed" for status in statuses) and not unknown_topics
    expected_decision = "stop" if decision == "stop" else ("continue_review" if complete else "pause")
    if decision != expected_decision:
        errors.append("decision does not reconcile with coverage and unknown_topics")
    expected_action = {"continue_review": "manual_prepare_next_stage_review", "pause": "collect_debrief_context", "stop": "record_stop_decision"}.get(expected_decision)
    expected_event = {"continue_review": "next_stage_review", "pause": "debrief_context", "stop": "stop_decision"}.get(expected_decision)
    if item.get("measurement_event") != expected_event:
        errors.append("measurement_event does not match decision")
    handoff = _closed(item.get("handoff"), "handoff", HANDOFF_FIELDS, errors)
    if handoff is not None:
        if handoff.get("next_safe_action") != expected_action:
            errors.append("handoff.next_safe_action does not match decision")
        for key, expected in (("manual_review_required", True), ("draft_only", True), ("external_actions_authorized", False), ("no_message_action", True), ("no_calendar_action", True)):
            if handoff.get(key) != expected:
                errors.append(f"handoff.{key} has immutable value")
    delivery = _closed(item.get("delivery"), "delivery", DELIVERY_FIELDS, errors)
    if delivery is not None:
        for key, expected in (("draft_only", True), ("external_actions_authorized", False), ("no_message_action", True), ("no_calendar_action", True), ("raw_transcript_retained", False), ("local_save_mode", "disabled")):
            if type(delivery.get(key)) is not type(expected) or delivery.get(key) != expected:
                errors.append(f"delivery.{key} has immutable value")
    fingerprint = item.get("replay_fingerprint")
    if not isinstance(fingerprint, str) or not REPLAY.fullmatch(fingerprint):
        errors.append("replay_fingerprint has invalid value")
    elif fingerprint != replay_fingerprint(item):
        errors.append("replay_fingerprint does not match debrief")
    return sorted(set(errors))


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Validate a private recruiter screen debrief.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--intake", type=Path, required=True)
    parser.add_argument("--as-of", required=True, type=dt.date.fromisoformat)
    try:
        args = parser.parse_args(argv)
        value = json.loads(LOADER.read_bounded_bytes(args.input, 128_000), object_pairs_hook=_unique)
        checkpoint = json.loads(LOADER.read_bounded_bytes(args.checkpoint, 128_000), object_pairs_hook=_unique)
        receipt = json.loads(LOADER.read_bounded_bytes(args.receipt, 128_000), object_pairs_hook=_unique)
        intake = json.loads(LOADER.read_bounded_bytes(args.intake, 128_000), object_pairs_hook=_unique)
        errors = validate_screen_debrief(value, receipt, intake, checkpoint=checkpoint, as_of=args.as_of)
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    if errors:
        print('{"error":{"code":"invalid_screen_debrief"}}', file=sys.stderr)
        return 2
    print("valid private recruiter screen debrief")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
