#!/usr/bin/env python3
"""Build a private, target-specific bridge from the recruiter decision gate."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path

from canonical_date import parse_canonical_date
from typing import Any


SCHEMA_VERSION = "recruiter-target-screen-intake-v1"


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_screen_builder_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("screen intake dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _sibling("validate_recruiter_target_screen_intake.py")
LOADER = _sibling("private_input_loader.py")
WRITER = _sibling("render_recruiter_target_shortlist.py")
MAX_INPUT_BYTES = 128_000


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


def build_screen_intake(gate: Mapping[str, object], target_id: str, context: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(gate, Mapping) or not isinstance(context, Mapping):
        raise ValueError("screen intake inputs are unavailable")
    gate_errors = VALIDATOR.GATE.validate_decision_gate(gate, as_of=dt.date.today())
    if gate_errors:
        raise ValueError("source decision gate validation failed")
    target = next((row for row in gate["decision_rows"] if isinstance(row, Mapping) and row.get("target_id") == target_id), None)
    if target is None:
        raise ValueError("target is not in source decision gate")
    intake_context = copy.deepcopy(dict(context))
    source_date = intake_context.get("source_date")
    try:
        reference_date = parse_canonical_date(gate["as_of_date"], field="as_of_date")
        parsed_source_date = parse_canonical_date(source_date, field="source_date")
        if parsed_source_date > reference_date:
            raise ValueError("screen intake date is in the future")
    except ValueError as error:
        raise ValueError("screen intake date is unavailable") from error
    output: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "private_recruiter_target_screen_intake",
        "locale": gate["locale"],
        "as_of_date": gate["as_of_date"],
        "source_gate_snapshot": gate["source_snapshot"],
        "source_gate": copy.deepcopy(dict(gate)),
        "target_id": target_id,
        "target_decision": target["decision"],
        "intake": intake_context,
        "checks": intake_context.pop("checks", None),
        "readiness_decision": "clarify_first",
        "measurement_event": "clarify_context",
        "handoff": {
            "next_safe_action": "collect_screen_intake",
            "selected_module": "prepare-role-interviews",
            "manual_review_required": True,
            "draft_only": True,
            "external_actions_authorized": False,
            "no_message_action": True,
            "no_calendar_action": True,
        },
        "delivery": {
            "draft_only": True,
            "external_actions_authorized": False,
            "local_save_mode": "disabled",
            "raw_contact_details_retained": False,
        },
    }
    # `checks` is deliberately a sibling of `intake` so each decision can be audited independently.
    output["intake"] = intake_context
    output["checks"] = copy.deepcopy(context.get("checks"))
    statuses = [check.get("status") for check in output["checks"] if isinstance(check, Mapping)] if isinstance(output["checks"], list) else []
    if target["decision"] == "stop" or "stop" in statuses:
        readiness = "stop"
        event = "stop_decision"
        action = "stop_and_record"
    elif target["decision"] == "advance" and len(statuses) == 4 and all(status == "pass" for status in statuses) and 0 <= (reference_date - parsed_source_date).days <= VALIDATOR.SOURCE_FRESHNESS_DAYS and 0 <= (dt.date.today() - reference_date).days <= VALIDATOR.SOURCE_FRESHNESS_DAYS:
        readiness = "ready"
        event = "screen_context_submitted"
        action = "manual_prepare_role_interviews_review"
    else:
        readiness = "clarify_first"
        event = "clarify_context"
        action = "collect_screen_intake"
    output["readiness_decision"] = readiness
    output["measurement_event"] = event
    output["handoff"]["next_safe_action"] = action
    if VALIDATOR.validate_screen_intake(output, source_gate=gate, as_of=dt.date.today()):
        raise ValueError("screen intake validation failed")
    return output


def _atomic_private_write(output: Path, content: bytes) -> None:
    WRITER._atomic_private_write(output, content)


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Build a private recruiter target screen intake.")
    parser.add_argument("gate", type=Path)
    parser.add_argument("target_id")
    parser.add_argument("context", type=Path)
    parser.add_argument("output", type=Path)
    try:
        args = parser.parse_args(argv)
        gate = json.loads(LOADER.read_bounded_bytes(args.gate, MAX_INPUT_BYTES), object_pairs_hook=_unique)
        context = json.loads(LOADER.read_bounded_bytes(args.context, MAX_INPUT_BYTES), object_pairs_hook=_unique)
        artifact = build_screen_intake(gate, args.target_id, context)
        _atomic_private_write(args.output, (json.dumps(artifact, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    print("built recruiter target screen intake")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
