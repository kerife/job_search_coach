#!/usr/bin/env python3
"""Build a deterministic, private recruiter target shortlist."""

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
from collections.abc import Mapping, Sequence
from pathlib import Path

from canonical_date import parse_canonical_date
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


class _ArgumentError(ValueError):
    """Raised without reflecting private command-line values."""


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise _ArgumentError


def build_shortlist(
    locale: str,
    as_of_date: str,
    network_plan: Mapping[str, object],
    targets: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Return a closed shortlist; target order is score-descending and deterministic."""
    try:
        reference_date = parse_canonical_date(as_of_date, field="as_of_date")
    except ValueError as error:
        raise ValueError("as_of_date must be an ISO date") from error
    if reference_date > dt.date.today():
        raise ValueError("as_of_date cannot be in the future")
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
    errors = VALIDATOR.validate_shortlist(output, as_of=reference_date)
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
            if stat.S_ISLNK(existing.st_mode):
                raise OSError("output target is a symbolic link")
            if not stat.S_ISREG(existing.st_mode):
                raise OSError("output target is not a regular file")
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
            os.fchmod(stream.fileno(), 0o600)
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


def _write_private_json(path: Path, value: Mapping[str, object]) -> None:
    content = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    _atomic_private_write(path, content)


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Build a private recruiter target shortlist.")
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
    print(json.dumps({"artifact_kind": value["artifact_kind"], "schema_version": value["schema_version"], "ui_locale": value["locale"]}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
