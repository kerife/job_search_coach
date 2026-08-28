#!/usr/bin/env python3
"""Build a private, structured debrief after an attended recruiter screen."""

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


SCHEMA_VERSION = "private-recruiter-screen-debrief-v1"


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_debrief_builder_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("screen debrief dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _sibling("validate_private_recruiter_screen_debrief.py")
LOADER = _sibling("private_input_loader.py")
WRITER = _sibling("render_private_recruiter_followthrough_checkpoint.py")
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


def build_screen_debrief(
    checkpoint: Mapping[str, object],
    receipt: Mapping[str, object],
    intake: Mapping[str, object],
    debrief: Mapping[str, object],
) -> dict[str, object]:
    if not all(isinstance(value, Mapping) for value in (checkpoint, receipt, intake, debrief)):
        raise ValueError("screen debrief inputs are unavailable")
    observed_value = debrief.get("observed_date")
    try:
        observed_date = parse_canonical_date(observed_value, field="observed_date")
    except ValueError as error:
        raise ValueError("debrief date is unavailable") from error
    if observed_date > dt.date.today():
        raise ValueError("debrief date cannot be in the future")
    output: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "private_recruiter_screen_debrief",
        "locale": intake.get("locale"),
        "observed_date": str(observed_value),
        "source_receipt": copy.deepcopy(dict(receipt)),
        "source_checkpoint": copy.deepcopy(dict(checkpoint)),
        "source_intake": copy.deepcopy(dict(intake)),
        "source_snapshot": intake.get("source_gate_snapshot"),
        "coverage": copy.deepcopy(debrief.get("coverage")),
        "unknown_topics": copy.deepcopy(debrief.get("unknown_topics")),
        "facts_used": copy.deepcopy(debrief.get("facts_used")),
        "decision": debrief.get("decision"),
        "measurement_event": "debrief_context",
        "replay_fingerprint": "",
        "handoff": {
            "next_safe_action": "collect_debrief_context",
            "manual_review_required": True,
            "draft_only": True,
            "external_actions_authorized": False,
            "no_message_action": True,
            "no_calendar_action": True,
        },
        "delivery": {
            "draft_only": True,
            "external_actions_authorized": False,
            "no_message_action": True,
            "no_calendar_action": True,
            "raw_transcript_retained": False,
            "local_save_mode": "disabled",
        },
    }
    decision = output["decision"]
    coverage = output["coverage"] if isinstance(output["coverage"], list) else []
    unknown_topics = output["unknown_topics"] if isinstance(output["unknown_topics"], list) else []
    statuses = [row.get("status") for row in coverage if isinstance(row, Mapping)]
    complete = len(statuses) == 3 and all(status == "discussed" for status in statuses) and not unknown_topics
    if decision == "stop":
        output["measurement_event"] = "stop_decision"
        output["handoff"]["next_safe_action"] = "record_stop_decision"
    elif decision == "continue_review" and complete:
        output["measurement_event"] = "next_stage_review"
        output["handoff"]["next_safe_action"] = "manual_prepare_next_stage_review"
    elif decision == "pause":
        output["decision"] = "pause"
        output["measurement_event"] = "debrief_context"
        output["handoff"]["next_safe_action"] = "collect_debrief_context"
    output["replay_fingerprint"] = VALIDATOR.replay_fingerprint(output)
    errors = VALIDATOR.validate_screen_debrief(output, receipt, intake, checkpoint=checkpoint, as_of=observed_date)
    if errors:
        raise ValueError("screen debrief validation failed")
    return output


def _atomic_private_write(output: Path, content: bytes) -> None:
    WRITER._atomic_private_write(output, content)


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Build a private recruiter screen debrief.")
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("intake", type=Path)
    parser.add_argument("debrief", type=Path)
    parser.add_argument("output", type=Path)
    try:
        args = parser.parse_args(argv)
        checkpoint = json.loads(LOADER.read_bounded_bytes(args.checkpoint, MAX_INPUT_BYTES), object_pairs_hook=_unique)
        receipt = json.loads(LOADER.read_bounded_bytes(args.receipt, MAX_INPUT_BYTES), object_pairs_hook=_unique)
        intake = json.loads(LOADER.read_bounded_bytes(args.intake, MAX_INPUT_BYTES), object_pairs_hook=_unique)
        debrief = json.loads(LOADER.read_bounded_bytes(args.debrief, MAX_INPUT_BYTES), object_pairs_hook=_unique)
        artifact = build_screen_debrief(checkpoint, receipt, intake, debrief)
        _atomic_private_write(args.output, (json.dumps(artifact, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    print("built private recruiter screen debrief")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
