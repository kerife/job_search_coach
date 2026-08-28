#!/usr/bin/env python3
"""Build a private decision gate from one validated recruiter shortlist."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import importlib.util
import json
import os
import secrets
import stat
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "recruiter-target-decision-gate-v1"


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise ValueError("invalid arguments")


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_gate_builder_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("decision gate dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SHORTLIST = _sibling("validate_recruiter_target_shortlist.py")
GATE = _sibling("validate_recruiter_target_decision_gate.py")
LOADER = _sibling("private_input_loader.py")
MAX_INPUT_BYTES = 128_000


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result

_STRATEGY = {
    "es": {
        "advance": ("Revisar primero el ángulo de contacto de menor riesgo.", "Contexto y prueba suficientes para revisión manual."),
        "clarify": ("Resolver el contexto del rol antes de pensar en un borrador.", "La conexión puede servir, pero falta una confirmación."),
        "pause": ("Conservar el objetivo en investigación sin preparar contacto.", "La coincidencia temática no basta todavía."),
        "stop": ("Registrar el motivo de detención y no continuar.", "La condición actual no permite un contacto seguro."),
    },
    "en": {
        "advance": ("Review the lowest-risk contact angle first.", "Context and proof are sufficient for manual review."),
        "clarify": ("Resolve role context before considering a draft.", "The path may help, but one confirmation is missing."),
        "pause": ("Keep this target in research without preparing contact.", "Topic overlap is not enough yet."),
        "stop": ("Record the stop reason and do not continue.", "The current condition does not support safe contact."),
    },
}


def _safe_context(value: object, label: str) -> str:
    if not GATE.screen_context_is_safe(value):
        raise ValueError(f"{label} is unavailable")
    lowered = value.casefold()
    if any(marker in lowered for marker in ("://", "www.", "linkedin.com/", "file:", "ssh:", "ftp:", "mailto:", "javascript:", "data:")):
        raise ValueError(f"{label} is unavailable")
    return value


def build_decision_gate(
    shortlist: Mapping[str, object],
    *,
    screen_context: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Return a closed gate whose source snapshot can be replay-verified."""
    if not isinstance(shortlist, Mapping) or SHORTLIST.validate_shortlist(shortlist):
        raise ValueError("source shortlist validation failed")
    locale = shortlist.get("locale")
    if locale not in _STRATEGY:
        raise ValueError("source shortlist locale is invalid")
    as_of_date = shortlist.get("as_of_date")
    if not isinstance(as_of_date, str):
        raise ValueError("source shortlist date is unavailable")
    reference_date = dt.date.fromisoformat(as_of_date)
    if reference_date > dt.date.today():
        raise ValueError("source shortlist date cannot be in the future")
    if screen_context is not None:
        if not isinstance(screen_context, Mapping):
            raise ValueError("screen context is unavailable")
        screen = {
            "vacancy_summary": _safe_context(screen_context.get("vacancy_summary"), "vacancy summary"),
            "confirmed_fact_summary": _safe_context(screen_context.get("confirmed_fact_summary"), "confirmed fact summary"),
        }
    else:
        screen = None
    source = copy.deepcopy(dict(shortlist))
    rows: list[dict[str, object]] = []
    for target in source["targets"]:
        decision = str(target["decision"])
        strategy, readiness = _STRATEGY[locale][decision]
        rows.append({
            "target_id": target["target_id"],
            "decision": decision,
            "decision_reason": target["decision_reason"],
            "contactability_status": target["contactability_status"],
            "missing_context": target["missing_context"],
            "recommended_draft_type": target["recommended_draft_type"],
            "first_contact_strategy": strategy,
            "warm_intro_readiness": readiness,
            "next_safe_action": target["next_safe_action"],
            "draft_only": True,
            "consent": "not_granted",
            "authorization_required": True,
            "no_message_action": True,
            "no_calendar_action": True,
        })
    counts = {decision: sum(1 for row in rows if row["decision"] == decision) for decision in ("advance", "clarify", "pause", "stop")}
    output: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "private_recruiter_target_decision_gate",
        "locale": locale,
        "as_of_date": as_of_date,
        "source_shortlist": source,
        "source_snapshot": GATE.snapshot_for_shortlist(source),
        "decision_counts": counts,
        "decision_rows": rows,
        "screen_context": screen,
        "handoff": {
            "screen_context_state": "provided" if screen is not None else "missing",
            "next_safe_action": "prepare_role_interviews_review" if screen is not None else "collect_screen_context",
            "manual_review_required": True,
            "selected_module": "prepare-role-interviews",
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
    if GATE.validate_decision_gate(output, as_of=reference_date):
        raise ValueError("decision gate validation failed")
    return output


def _open_private_parent(parent: Path) -> int:
    parent = Path(parent)
    if not parent.is_absolute() or parent.anchor != os.sep:
        raise OSError("output parent must be absolute")
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(os.sep, os.O_RDONLY | directory_flag)
    try:
        for index, component in enumerate(parent.parts[1:]):
            if component in {"", ".", ".."}:
                raise OSError("output parent is unsafe")
            created = False
            try:
                os.mkdir(component, 0o700, dir_fd=descriptor)
                created = True
            except FileExistsError:
                pass
            alias = index == 0 and component in {"tmp", "var"} and os.path.islink(os.path.join(os.sep, component)) and os.path.realpath(os.path.join(os.sep, component)) == os.path.join(os.sep, "private", component)
            next_descriptor = os.open(component, os.O_RDONLY | directory_flag | (0 if alias else no_follow), dir_fd=descriptor)
            if not stat.S_ISDIR(os.fstat(next_descriptor).st_mode):
                os.close(next_descriptor)
                raise OSError("output parent is not a directory")
            if created:
                os.fchmod(next_descriptor, 0o700)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _atomic_private_write(output: Path, content: bytes) -> None:
    output = Path(os.path.abspath(os.fspath(output)))
    parent = _open_private_parent(output.parent)
    temporary: str | None = None
    descriptor: int | None = None
    try:
        try:
            existing = os.stat(output.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None:
            raise FileExistsError("output already exists")
        for _ in range(100):
            candidate = f".{output.name}.tmp-{secrets.token_hex(8)}"
            try:
                descriptor = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=parent)
                temporary = candidate
                break
            except FileExistsError:
                continue
        if descriptor is None or temporary is None:
            raise OSError("cannot create private temporary artifact")
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, output.name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
        os.unlink(temporary, dir_fd=parent)
        temporary = None
        os.fsync(parent)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
        os.close(parent)


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Build a private recruiter target decision gate.")
    parser.add_argument("shortlist", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--screen-context", type=Path)
    try:
        args = parser.parse_args(argv)
        shortlist = json.loads(
            LOADER.read_bounded_bytes(args.shortlist, MAX_INPUT_BYTES),
            object_pairs_hook=_unique,
        )
        screen = (
            json.loads(
                LOADER.read_bounded_bytes(args.screen_context, MAX_INPUT_BYTES),
                object_pairs_hook=_unique,
            )
            if args.screen_context
            else None
        )
        gate = build_decision_gate(shortlist, screen_context=screen)
        _atomic_private_write(args.output, (json.dumps(gate, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    print("built recruiter target decision gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
