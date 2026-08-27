#!/usr/bin/env python3
"""Build a private next-stage review from a completed screen debrief."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_next_stage_builder_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("next-stage dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _sibling("validate_private_recruiter_next_stage_review.py")
DEBRIEF = _sibling("validate_private_recruiter_screen_debrief.py")
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


def build_next_stage_review(
    debrief: Mapping[str, object],
    receipt: Mapping[str, object],
    intake: Mapping[str, object],
    checkpoint: Mapping[str, object],
    next_stage: str,
) -> dict[str, object]:
    if next_stage not in VALIDATOR.STAGES:
        raise ValueError("next stage must be explicit and supported")
    if not all(isinstance(value, Mapping) for value in (debrief, receipt, intake, checkpoint)):
        raise ValueError("next-stage inputs are unavailable")
    observed_value = debrief.get("observed_date")
    try:
        observed = dt.date.fromisoformat(str(observed_value))
    except ValueError as error:
        raise ValueError("debrief date is unavailable") from error
    if observed > dt.date.today():
        raise ValueError("review date cannot be in the future")
    coverage = debrief.get("coverage") if isinstance(debrief.get("coverage"), list) else []
    checklist = [
        {"topic": row.get("topic"), "status": "covered" if row.get("status") == "discussed" else "needs_clarification"}
        for row in coverage if isinstance(row, Mapping)
    ]
    complete = debrief.get("decision") == "continue_review" and len(checklist) == 3 and all(row["status"] == "covered" for row in checklist) and not debrief.get("unknown_topics")
    state = "ready" if complete else "blocked"
    decision = debrief.get("decision")
    action = "manual_prepare_next_stage_review" if state == "ready" else ("record_stop_decision" if decision == "stop" else "collect_debrief_context")
    artifact: dict[str, object] = {
        "schema_version": VALIDATOR.SCHEMA_VERSION,
        "artifact_kind": VALIDATOR.ARTIFACT_KIND,
        "locale": debrief.get("locale"),
        "observed_date": str(observed_value),
        "source_debrief": copy.deepcopy(dict(debrief)),
        "source_snapshot": debrief.get("source_snapshot"),
        "source_intake": copy.deepcopy(dict(intake)),
        "review_owner": "candidate_with_coach_review",
        "review_state": state,
        "next_stage": next_stage,
        "checklist": checklist,
        "facts_used": copy.deepcopy(debrief.get("facts_used")),
        "unknown_topics": copy.deepcopy(debrief.get("unknown_topics")),
        "replay_fingerprint": "",
        "handoff": {"next_safe_action": action, "manual_review_required": True, "draft_only": True, "external_actions_authorized": False, "no_message_action": True, "no_calendar_action": True},
        "delivery": {"draft_only": True, "external_actions_authorized": False, "no_message_action": True, "no_calendar_action": True, "raw_transcript_retained": False, "local_save_mode": "disabled"},
    }
    artifact["replay_fingerprint"] = VALIDATOR.replay_fingerprint(artifact)
    if VALIDATOR.validate_next_stage_review(artifact, debrief, receipt, intake, checkpoint, as_of=observed):
        raise ValueError("next-stage review validation failed")
    return artifact


def _atomic_private_write(output: Path, content: bytes) -> None:
    WRITER._atomic_private_write(output, content)


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Build a private next-stage review.")
    parser.add_argument("debrief", type=Path); parser.add_argument("receipt", type=Path); parser.add_argument("intake", type=Path); parser.add_argument("checkpoint", type=Path); parser.add_argument("next_stage", choices=tuple(sorted(VALIDATOR.STAGES))); parser.add_argument("output", type=Path)
    try:
        args = parser.parse_args(argv)
        read = lambda path: json.loads(LOADER.read_bounded_bytes(path, MAX_INPUT_BYTES), object_pairs_hook=_unique)
        artifact = build_next_stage_review(read(args.debrief), read(args.receipt), read(args.intake), read(args.checkpoint), args.next_stage)
        _atomic_private_write(args.output, (json.dumps(artifact, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    print("built private recruiter next-stage review")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
