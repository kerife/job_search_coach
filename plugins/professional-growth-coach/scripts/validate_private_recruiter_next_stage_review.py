#!/usr/bin/env python3
"""Fail-closed validation for the private next-stage review handoff."""

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

SCHEMA_VERSION = "private-recruiter-next-stage-review-v1"
ARTIFACT_KIND = "private_recruiter_next_stage_review"
TOP_FIELDS = frozenset({"schema_version", "artifact_kind", "locale", "observed_date", "source_debrief", "source_snapshot", "source_intake", "review_owner", "review_state", "next_stage", "checklist", "facts_used", "unknown_topics", "replay_fingerprint", "handoff", "delivery"})
CHECKLIST_FIELDS = frozenset({"topic", "status"})
HANDOFF_FIELDS = frozenset({"next_safe_action", "manual_review_required", "draft_only", "external_actions_authorized", "no_message_action", "no_calendar_action"})
DELIVERY_FIELDS = frozenset({"draft_only", "external_actions_authorized", "no_message_action", "no_calendar_action", "raw_transcript_retained", "local_save_mode"})
TOPICS = frozenset({"requirement", "scope", "team_context"})
STAGES = frozenset({
    "recruiter_screen", "first_interview", "technical_screen", "hiring_manager",
    "technical_deep_dive", "take_home", "system_design", "behavioral_loop", "panel", "offer_stage",
})
STATES = frozenset({"ready", "blocked"})
CHECK_STATUSES = frozenset({"covered", "needs_clarification"})
FACT_ID = re.compile(r"^F-[0-9]{3}$")
SNAPSHOT = re.compile(r"^snap-shortlist-sha256-[0-9a-f]{64}$")
REPLAY = re.compile(r"^replay-next-stage-sha256-[0-9a-f]{64}$")


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_next_stage_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("next-stage dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


DEBRIEF = _sibling("validate_private_recruiter_screen_debrief.py")
LOADER = _sibling("private_input_loader.py")
TAXONOMY = _sibling("recruiter_stage_taxonomy.py")
STAGES = frozenset(TAXONOMY.STAGES)


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
    source_debrief = value.get("source_debrief")
    source_debrief_fingerprint = source_debrief.get("replay_fingerprint") if isinstance(source_debrief, Mapping) else None
    payload = {key: value.get(key) for key in ("source_snapshot", "observed_date", "review_state", "next_stage", "checklist", "facts_used", "unknown_topics")}
    payload["source_debrief_fingerprint"] = source_debrief_fingerprint
    payload["source_debrief_hash"] = hashlib.sha256(_canonical(source_debrief).encode("utf-8")).hexdigest()
    return "replay-next-stage-sha256-" + hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def validate_next_stage_review(value: object, debrief: Mapping[str, object] | None, receipt: Mapping[str, object] | None, intake: Mapping[str, object] | None, checkpoint: Mapping[str, object] | None = None, *, as_of: dt.date | None = None) -> list[str]:
    errors: list[str] = []
    if as_of is not None and as_of > dt.date.today():
        errors.append("as_of cannot be in the future")
    item = _closed(value, "review", TOP_FIELDS, errors)
    if item is None:
        return sorted(set(errors))
    if item.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version has invalid value")
    if item.get("artifact_kind") != ARTIFACT_KIND:
        errors.append("artifact_kind has invalid value")
    locale = item.get("locale")
    if locale not in {"en", "es"}:
        errors.append("locale has invalid value")
    _date(item.get("observed_date"), "observed_date", errors, as_of)
    embedded_debrief = item.get("source_debrief")
    embedded_intake = item.get("source_intake")
    if not isinstance(embedded_debrief, Mapping):
        errors.append("source_debrief must be an object")
    if not isinstance(embedded_intake, Mapping):
        errors.append("source_intake must be an object")
    if debrief is None or not isinstance(debrief, Mapping):
        errors.append("debrief is required")
    else:
        debrief_errors = DEBRIEF.validate_screen_debrief(debrief, receipt, intake, checkpoint=checkpoint, as_of=as_of)
        if debrief_errors:
            errors.append("source debrief is invalid")
        if isinstance(embedded_debrief, Mapping) and _canonical(embedded_debrief) != _canonical(debrief):
            errors.append("source_debrief does not match debrief")
    if intake is None or not isinstance(intake, Mapping):
        errors.append("intake is required")
    elif isinstance(embedded_intake, Mapping) and _canonical(embedded_intake) != _canonical(intake):
        errors.append("source_intake does not match intake")
    if isinstance(debrief, Mapping):
        if item.get("locale") != debrief.get("locale"):
            errors.append("locale does not match source debrief")
        if item.get("source_snapshot") != debrief.get("source_snapshot"):
            errors.append("source_snapshot does not match source debrief")
        if item.get("facts_used") != debrief.get("facts_used"):
            errors.append("facts_used does not match source debrief")
        if item.get("unknown_topics") != debrief.get("unknown_topics"):
            errors.append("unknown_topics does not match source debrief")
        try:
            if dt.date.fromisoformat(str(item.get("observed_date"))) < dt.date.fromisoformat(str(debrief.get("observed_date"))):
                errors.append("observed_date cannot precede source debrief")
        except ValueError:
            pass
    snapshot = item.get("source_snapshot")
    if not isinstance(snapshot, str) or not SNAPSHOT.fullmatch(snapshot):
        errors.append("source_snapshot has invalid value")
    owner = item.get("review_owner")
    if owner != "candidate_with_coach_review":
        errors.append("review_owner has invalid value")
    stage = item.get("next_stage")
    if stage not in STAGES:
        errors.append("next_stage must be explicit and supported")
    if isinstance(intake, Mapping):
        source_stage = intake.get("intake", {}).get("stated_stage") if isinstance(intake.get("intake"), Mapping) else None
        if stage == source_stage:
            errors.append("next_stage must differ from current stage")
        elif stage in STAGES and not TAXONOMY.is_supported_transition(source_stage, stage):
            errors.append("next_stage transition is unsupported")
    facts = item.get("facts_used")
    if not isinstance(facts, list) or not 1 <= len(facts) <= 8 or any(not isinstance(fact, str) or not FACT_ID.fullmatch(fact) for fact in facts) or len({fact for fact in facts if isinstance(fact, str)}) != len(facts):
        errors.append("facts_used must contain one to eight unique fact IDs")
    unknowns = item.get("unknown_topics")
    if not isinstance(unknowns, list) or len(unknowns) > 5 or any(not isinstance(topic, str) or not topic.strip() or len(topic) > 180 for topic in unknowns):
        errors.append("unknown_topics must contain zero to five bounded items")
    checklist_value = item.get("checklist")
    checklist: list[Mapping[str, object]] = []
    if not isinstance(checklist_value, list) or len(checklist_value) != 3:
        errors.append("checklist must contain exactly three items")
    else:
        seen: set[str] = set()
        for index, raw in enumerate(checklist_value):
            row = _closed(raw, f"checklist[{index}]", CHECKLIST_FIELDS, errors)
            if row is None:
                continue
            topic = row.get("topic")
            if topic not in TOPICS or topic in seen:
                errors.append(f"checklist[{index}].topic has invalid or duplicated value")
            else:
                seen.add(topic)
            if row.get("status") not in CHECK_STATUSES:
                errors.append(f"checklist[{index}].status has invalid value")
            checklist.append(row)
        if seen != TOPICS:
            errors.append("checklist must cover requirement, scope, and team_context")
        if isinstance(debrief, Mapping):
            expected_status = {row.get("topic"): ("covered" if row.get("status") == "discussed" else "needs_clarification") for row in debrief.get("coverage", []) if isinstance(row, Mapping)}
            if any(row.get("status") != expected_status.get(row.get("topic")) for row in checklist):
                errors.append("checklist does not reconcile with source debrief")
    debrief_complete = isinstance(debrief, Mapping) and debrief.get("decision") == "continue_review" and not debrief.get("unknown_topics") and all(isinstance(row, Mapping) and row.get("status") == "discussed" for row in debrief.get("coverage", []))
    expected_state = "ready" if debrief_complete else "blocked"
    if item.get("review_state") != expected_state:
        errors.append("review_state does not reconcile with source debrief")
    expected_action = "manual_prepare_next_stage_review" if expected_state == "ready" else ("record_stop_decision" if isinstance(debrief, Mapping) and debrief.get("decision") == "stop" else "collect_debrief_context")
    handoff = _closed(item.get("handoff"), "handoff", HANDOFF_FIELDS, errors)
    if handoff is not None:
        if handoff.get("next_safe_action") != expected_action:
            errors.append("handoff.next_safe_action does not match review_state")
        for field, expected in (("manual_review_required", True), ("draft_only", True), ("external_actions_authorized", False), ("no_message_action", True), ("no_calendar_action", True)):
            if handoff.get(field) != expected:
                errors.append(f"handoff.{field} has immutable value")
    delivery = _closed(item.get("delivery"), "delivery", DELIVERY_FIELDS, errors)
    if delivery is not None:
        for field, expected in (("draft_only", True), ("external_actions_authorized", False), ("no_message_action", True), ("no_calendar_action", True), ("raw_transcript_retained", False), ("local_save_mode", "disabled")):
            if delivery.get(field) != expected:
                errors.append(f"delivery.{field} has immutable value")
    fingerprint = item.get("replay_fingerprint")
    if not isinstance(fingerprint, str) or not REPLAY.fullmatch(fingerprint):
        errors.append("replay_fingerprint has invalid value")
    elif fingerprint != replay_fingerprint(item):
        errors.append("replay_fingerprint does not match review")
    return sorted(set(errors))


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Validate a private next-stage review.")
    parser.add_argument("input", type=Path); parser.add_argument("--debrief", type=Path, required=True); parser.add_argument("--receipt", type=Path, required=True); parser.add_argument("--intake", type=Path, required=True); parser.add_argument("--checkpoint", type=Path, required=True); parser.add_argument("--as-of", required=True, type=dt.date.fromisoformat)
    try:
        args = parser.parse_args(argv)
        read = lambda path: json.loads(LOADER.read_bounded_bytes(path, 128_000), object_pairs_hook=_unique)
        errors = validate_next_stage_review(read(args.input), read(args.debrief), read(args.receipt), read(args.intake), read(args.checkpoint), as_of=args.as_of)
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    if errors:
        print('{"error":{"code":"invalid_next_stage_review"}}', file=sys.stderr)
        return 2
    print("valid private recruiter next-stage review")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
