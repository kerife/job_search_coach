#!/usr/bin/env python3
"""Build a deterministic, private recruiter target shortlist."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import stat
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_shortlist_builder_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("shortlist dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _sibling("validate_recruiter_target_shortlist.py")
LOADER = _sibling("private_input_loader.py")


def build_shortlist(
    locale: str,
    as_of_date: str,
    network_plan: Mapping[str, object],
    targets: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Return a closed shortlist; target order is score-descending and deterministic."""
    ordered = sorted(
        (copy.deepcopy(dict(target)) for target in targets),
        key=lambda target: (-int(target.get("priority_score", -1)), str(target.get("target_label", ""))),
    )
    rows: list[dict[str, object]] = []
    for index, target in enumerate(ordered, start=1):
        target["target_id"] = f"T-{index:03d}"
        target.update({
            "draft_only": True,
            "consent": "not_granted",
            "authorization_required": True,
            "no_message_action": True,
            "no_calendar_action": True,
        })
        rows.append(target)
    decisions = [str(target.get("decision")) for target in rows]
    batch_decision = "advance" if "advance" in decisions else "clarify" if "clarify" in decisions else "pause" if "pause" in decisions else "stop"
    output: dict[str, object] = {
        "schema_version": VALIDATOR.SCHEMA_VERSION,
        "artifact_kind": VALIDATOR.ARTIFACT_KIND,
        "locale": locale,
        "as_of_date": as_of_date,
        "network_plan": copy.deepcopy(dict(network_plan)),
        "targets": rows,
        "batch_decision": batch_decision,
        "top_priority_target_id": rows[0]["target_id"] if rows else None,
        "delivery": copy.deepcopy(VALIDATOR.DELIVERY),
    }
    errors = VALIDATOR.validate_shortlist(output)
    if errors:
        raise ValueError("recruiter target shortlist is invalid")
    return output


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _write_private_json(path: Path, value: Mapping[str, object]) -> None:
    path = path.resolve()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    finally:
        if descriptor != -1:
            os.close(descriptor)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a private recruiter target shortlist.")
    parser.add_argument("plan", type=Path)
    parser.add_argument("targets", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--locale", choices=("es", "en"), required=True)
    parser.add_argument("--as-of", required=True)
    try:
        args = parser.parse_args(argv)
        plan = json.loads(LOADER.read_bounded_bytes(args.plan, 64_000), object_pairs_hook=_unique)
        targets = json.loads(LOADER.read_bounded_bytes(args.targets, 128_000), object_pairs_hook=_unique)
        if not isinstance(plan, Mapping) or not isinstance(targets, list) or not all(isinstance(target, Mapping) for target in targets):
            raise ValueError("invalid plan or targets")
        value = build_shortlist(args.locale, args.as_of, plan, targets)
        _write_private_json(args.output, value)
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    print("built recruiter target shortlist")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
