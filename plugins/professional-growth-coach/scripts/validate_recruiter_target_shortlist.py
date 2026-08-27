#!/usr/bin/env python3
"""Fail-closed validation for a private recruiter target shortlist."""

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


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_shortlist_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("shortlist dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PROSE = _sibling("private_prose_safety.py")
LOADER = _sibling("private_input_loader.py")

SCHEMA_VERSION = "recruiter-target-shortlist-v1"
ARTIFACT_KIND = "private_recruiter_target_shortlist"
TOP_FIELDS = frozenset({
    "schema_version", "artifact_kind", "locale", "as_of_date", "network_plan",
    "targets", "batch_decision", "top_priority_target_id", "delivery",
})
PLAN_FIELDS = frozenset({
    "network_goal", "target_segments", "source_queries", "warm_path_first",
    "context_quality_gate", "outreach_batch_limit", "candidate_time_budget",
    "stop_condition",
})
TARGET_FIELDS = frozenset({
    "target_id", "target_label", "contact_category", "company_or_specialty",
    "context_source", "context_state", "relationship_warmth", "target_theme",
    "supported_fact_ids", "missing_context", "priority_score", "decision",
    "decision_reason", "personalization_trigger", "recommended_draft_type",
    "contactability_status", "do_not_contact_reason", "next_safe_action",
    "draft_only", "consent", "authorization_required", "no_message_action", "no_calendar_action",
})
DELIVERY = {
    "draft_only": True,
    "consent": "not_granted",
    "authorization_required": True,
    "no_message_action": True,
    "no_calendar_action": True,
    "raw_contact_details_retained": False,
    "local_save_mode": "disabled",
}
CONTACT_CATEGORIES = frozenset({"warm_referral", "named_recruiter", "alumni", "community_contact", "technical_peer"})
CONTEXT_STATES = frozenset({"named_context", "context_needed", "do_not_contact"})
WARMTH = frozenset({"warm", "cold_contextual", "unknown"})
DECISIONS = frozenset({"advance", "clarify", "pause", "stop"})
CONTACTABILITY = frozenset({"contactable", "context_needed", "do_not_contact"})
NEXT_ACTIONS = frozenset({"collect_recipient_context", "draft_only_review", "record_observation_only"})
DRAFT_TYPES = frozenset({"connection_note", "recruiter_interest", "referral_request", "none"})
DO_NOT_CONTACT = frozenset({"none", "no_context", "missing_context", "no_consent", "confidentiality_risk", "unsupported_claim", "closed_role", "missing_authorization"})
RESTRICTED = re.compile(r"(?:[a-z][a-z0-9+.-]{1,31}://|(?:file|ssh|ftp|mailto|javascript|data):|www\.|linkedin\.com/|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:^|\s)(?:/Users/|/private/|[A-Za-z]:[\\/]))", re.I)
TARGET_ID = re.compile(r"^T-[0-9]{3}$")
FACT_ID = re.compile(r"^F-[0-9]{3}$")


class _ArgumentError(ValueError):
    pass


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise _ArgumentError


def _closed(value: object, path: str, fields: frozenset[str], errors: list[str]) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    if set(value) - fields:
        errors.append(f"{path} has unsupported fields")
    if fields - set(value):
        errors.append(f"{path} is missing required fields")
    return value


def _text(value: object, path: str, errors: list[str], maximum: int = 500) -> bool:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        errors.append(f"{path} must be bounded text")
        return False
    if PROSE.contains_unicode_controls(value) or RESTRICTED.search(value):
        errors.append(f"{path} contains restricted material")
        return False
    return True


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


def validate_shortlist(value: object, *, as_of: dt.date | None = None) -> list[str]:
    errors: list[str] = []
    item = _closed(value, "shortlist", TOP_FIELDS, errors)
    if item is None:
        return sorted(set(errors))
    if item.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version has invalid value")
    if item.get("artifact_kind") != ARTIFACT_KIND:
        errors.append("artifact_kind has invalid value")
    if item.get("locale") not in {"es", "en"}:
        errors.append("locale has invalid value")
    parsed_as_of = _date(item.get("as_of_date"), "as_of_date", errors, as_of)

    plan = _closed(item.get("network_plan"), "network_plan", PLAN_FIELDS, errors)
    if plan is not None:
        for field in ("network_goal", "context_quality_gate", "candidate_time_budget", "stop_condition"):
            _text(plan.get(field), f"network_plan.{field}", errors)
        segments = plan.get("target_segments")
        if not isinstance(segments, list) or not 1 <= len(segments) <= 5 or not all(isinstance(v, str) for v in segments):
            errors.append("network_plan.target_segments has invalid value")
        elif any(not _text(segment, f"network_plan.target_segments[{index}]", errors, 80) for index, segment in enumerate(segments)):
            pass
        queries = plan.get("source_queries")
        if not isinstance(queries, list) or not 3 <= len(queries) <= 5:
            errors.append("network_plan.source_queries must contain three to five queries")
        elif any(not _text(query, f"network_plan.source_queries[{index}]", errors, 180) for index, query in enumerate(queries)):
            pass
        if plan.get("warm_path_first") is not True:
            errors.append("network_plan.warm_path_first must be true")
        if type(plan.get("outreach_batch_limit")) is not int or not 1 <= plan["outreach_batch_limit"] <= 6:
            errors.append("network_plan.outreach_batch_limit has invalid value")

    targets_value = item.get("targets")
    targets: list[Mapping[str, object]] = []
    if not isinstance(targets_value, list) or not 3 <= len(targets_value) <= 6:
        errors.append("targets must contain three to six rows")
    else:
        seen_ids: set[str] = set()
        for index, target_value in enumerate(targets_value):
            path = f"targets[{index}]"
            target = _closed(target_value, path, TARGET_FIELDS, errors)
            if target is None:
                continue
            target_id = target.get("target_id")
            if not isinstance(target_id, str) or not TARGET_ID.fullmatch(target_id) or target_id in seen_ids:
                errors.append(f"{path}.target_id is invalid or duplicated")
            else:
                seen_ids.add(target_id)
            for field, maximum in (("target_label", 160), ("company_or_specialty", 160), ("context_source", 300), ("target_theme", 240), ("missing_context", 300), ("decision_reason", 300), ("personalization_trigger", 240)):
                _text(target.get(field), f"{path}.{field}", errors, maximum)
            if target.get("contact_category") not in CONTACT_CATEGORIES:
                errors.append(f"{path}.contact_category has invalid value")
            if target.get("context_state") not in CONTEXT_STATES:
                errors.append(f"{path}.context_state has invalid value")
            if target.get("relationship_warmth") not in WARMTH:
                errors.append(f"{path}.relationship_warmth has invalid value")
            fact_ids = target.get("supported_fact_ids")
            if not isinstance(fact_ids, list) or len(fact_ids) > 3 or len(set(fact_ids)) != len(fact_ids) or not all(isinstance(fact, str) and FACT_ID.fullmatch(fact) for fact in fact_ids):
                errors.append(f"{path}.supported_fact_ids has invalid value")
            score = target.get("priority_score")
            if type(score) is not int or not 0 <= score <= 100:
                errors.append(f"{path}.priority_score has invalid value")
            decision = target.get("decision")
            if decision not in DECISIONS:
                errors.append(f"{path}.decision has invalid value")
            if target.get("personalization_trigger") == "generic":
                errors.append(f"{path}.personalization_trigger cannot be generic")
            if target.get("recommended_draft_type") not in DRAFT_TYPES:
                errors.append(f"{path}.recommended_draft_type has invalid value")
            if target.get("contactability_status") not in CONTACTABILITY:
                errors.append(f"{path}.contactability_status has invalid value")
            if target.get("do_not_contact_reason") not in DO_NOT_CONTACT:
                errors.append(f"{path}.do_not_contact_reason has invalid value")
            if target.get("next_safe_action") not in NEXT_ACTIONS:
                errors.append(f"{path}.next_safe_action has invalid value")
            for field, expected in (("draft_only", True), ("consent", "not_granted"), ("authorization_required", True), ("no_message_action", True), ("no_calendar_action", True)):
                if target.get(field) != expected:
                    errors.append(f"{path}.{field} has immutable value")
            if decision == "advance" and (
                target.get("context_state") != "named_context"
                or not fact_ids
                or target.get("missing_context") != "none"
                or target.get("do_not_contact_reason") != "none"
                or target.get("contactability_status") != "contactable"
                or target.get("next_safe_action") != "draft_only_review"
            ):
                errors.append(f"{path}.advance requires named context, supported facts, and no missing context")
            if decision != "advance" and target.get("next_safe_action") == "draft_only_review":
                errors.append(f"{path}.non-advance target cannot enter draft review")
            if target.get("do_not_contact_reason") == "none" and decision != "advance":
                errors.append(f"{path}.non-advance target must name a do-not-contact reason")
            targets.append(target)
        expected_order = sorted(targets, key=lambda target: (-int(target.get("priority_score", -1)), str(target.get("target_id", ""))))
        if [target.get("target_id") for target in targets] != [target.get("target_id") for target in expected_order]:
            errors.append("targets must be sorted by priority score then target id")
        if targets and item.get("top_priority_target_id") != targets[0].get("target_id"):
            errors.append("top_priority_target_id must match the first target")

    decisions = [target.get("decision") for target in targets]
    expected_batch = "advance" if "advance" in decisions else "clarify" if "clarify" in decisions else "pause" if "pause" in decisions else "stop"
    if item.get("batch_decision") != expected_batch:
        errors.append("batch_decision does not reconcile with target decisions")

    delivery = _closed(item.get("delivery"), "delivery", frozenset(DELIVERY), errors)
    if delivery is not None:
        for field, expected in DELIVERY.items():
            if delivery.get(field) != expected:
                errors.append(f"delivery.{field} has immutable value")
    del parsed_as_of
    return sorted(set(errors))


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Validate a private recruiter target shortlist.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--as-of", required=True, type=dt.date.fromisoformat)
    try:
        args = parser.parse_args(argv)
    except (_ArgumentError, ValueError):
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    try:
        raw = LOADER.read_bounded_bytes(args.input, 64_000)
        value = json.loads(raw, object_pairs_hook=lambda pairs: _unique_json_pairs(pairs))
    except Exception:
        print("shortlist input is unavailable", file=sys.stderr)
        return 3
    errors = validate_shortlist(value, as_of=args.as_of)
    if errors:
        print(json.dumps({"error": {"code": "invalid_shortlist"}}, separators=(",", ":")), file=sys.stderr)
        return 2
    print("valid recruiter target shortlist")
    return 0


def _unique_json_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


if __name__ == "__main__":
    raise SystemExit(_cli())
