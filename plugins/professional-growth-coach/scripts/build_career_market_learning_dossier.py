#!/usr/bin/env python3
"""Build a pure, identity-free vacancy evidence alignment dossier."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import secrets
import stat
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("required market builder dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RESEARCH = _sibling("validate_target_vacancy_research.py")
EXECUTIVE = _sibling("validate_executive_career_dossier_v2.py")
SNAPSHOTS = _sibling("dossier_snapshot.py")
OUTPUT = _sibling("validate_career_market_learning_dossier.py")
_LOADER = _sibling("private_input_loader.py")
MAX_INPUT_BYTES = 256 * 1024
MAX_DEPTH = 12

ALIGNMENT_FIELDS = frozenset({
    "schema_version", "research_snapshot", "executive_dossier_snapshot", "signal_bindings",
    "privacy_boundary",
})
BINDING_FIELDS = frozenset({"signal", "support_state", "evidence_ids"})
SUPPORT_STATES = frozenset(OUTPUT.SUPPORT_NUMERATORS)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _within_depth(value: object, level: int = 0) -> bool:
    if level > MAX_DEPTH:
        return False
    if isinstance(value, Mapping):
        return all(_within_depth(key, level + 1) and _within_depth(item, level + 1) for key, item in value.items())
    if isinstance(value, list):
        return all(_within_depth(item, level + 1) for item in value)
    return True


def _load_alignment(path: Path) -> dict[str, object]:
    raw = _LOADER.read_bounded_bytes(path, MAX_INPUT_BYTES)
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    if not isinstance(value, dict) or not _within_depth(value):
        raise ValueError("alignment input is invalid")
    return value


def _open_private_parent(parent: Path) -> int:
    parent = Path(os.path.abspath(parent))
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    base_flags = os.O_RDONLY | directory_flag
    descriptor = os.open(os.sep, base_flags)
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
            candidate = os.path.join(os.sep, component)
            trusted_system_alias = (
                index == 0
                and component in {"tmp", "var"}
                and os.path.islink(candidate)
                and os.path.realpath(candidate)
                == os.path.join(os.sep, "private", component)
            )
            next_descriptor = os.open(
                component,
                base_flags | (0 if trusted_system_alias else no_follow),
                dir_fd=descriptor,
            )
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


def _write_private_json(path: Path, value: Mapping[str, object]) -> None:
    encoded = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    output = Path(os.path.abspath(path))
    if not output.name or output.name in {".", ".."}:
        raise OSError("output name is unsafe")
    parent_descriptor = _open_private_parent(output.parent)
    temporary_name: str | None = None
    descriptor: int | None = None
    try:
        try:
            target_status = os.stat(
                output.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            target_status = None
        if target_status is not None:
            if stat.S_ISLNK(target_status.st_mode):
                raise OSError("output target is a symbolic link")
            if not stat.S_ISREG(target_status.st_mode):
                raise OSError("output target is not a regular file")
            raise FileExistsError("output already exists")
        for _ in range(100):
            candidate = f".{output.name}.tmp-{secrets.token_hex(8)}"
            try:
                descriptor = os.open(
                    candidate,
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent_descriptor,
                )
                temporary_name = candidate
                break
            except FileExistsError:
                continue
        if temporary_name is None or descriptor is None:
            raise OSError("cannot create private temporary artifact")
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            os.fchmod(stream.fileno(), 0o600)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(
                temporary_name,
                output.name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileExistsError as error:
            raise FileExistsError("output already exists") from error
        os.unlink(temporary_name, dir_fd=parent_descriptor)
        temporary_name = None
        os.fsync(parent_descriptor)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=parent_descriptor)
            except FileNotFoundError:
                pass
        os.close(parent_descriptor)


def _closed(value: object, fields: frozenset[str], errors: list[str], path: str) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    if set(value) - fields:
        errors.append(f"{path} has unsupported fields")
    if fields - set(value):
        errors.append(f"{path} is missing required fields")
    return value


def validate_alignment(
    value: object,
    research: Mapping[str, object],
    executive_dossier: Mapping[str, object],
) -> list[str]:
    """Validate closed bindings against the two validated immutable inputs."""
    errors: list[str] = []
    try:
        if not isinstance(value, Mapping):
            return ["candidate market alignment must be an object"]
        if set(value) - ALIGNMENT_FIELDS:
            errors.append("candidate market alignment has unsupported fields")
        if ALIGNMENT_FIELDS - set(value):
            errors.append("candidate market alignment is missing required fields")
        if value.get("schema_version") != "candidate-market-alignment-v1":
            errors.append("alignment schema_version has invalid value")
        if value.get("privacy_boundary") != "identity_free_evidence_references_only":
            errors.append("alignment privacy_boundary has invalid value")
        if value.get("research_snapshot") != RESEARCH.snapshot_for_market_dossier(research):
            errors.append("alignment research_snapshot does not match research")
        if value.get("executive_dossier_snapshot") != SNAPSHOTS.snapshot_for_dossier(executive_dossier):
            errors.append("alignment executive_dossier_snapshot does not match dossier")
        known_evidence = {
            row.get("id"): row.get("state")
            for row in executive_dossier.get("evidence", [])
            if isinstance(row, Mapping) and isinstance(row.get("id"), str)
        }
        signals = {
            requirement.get("signal")
            for vacancy in research.get("vacancies", [])
            if isinstance(vacancy, Mapping)
            for requirement in vacancy.get("requirements", [])
            if isinstance(requirement, Mapping) and isinstance(requirement.get("signal"), str)
        }
        bindings = value.get("signal_bindings")
        if not isinstance(bindings, list):
            errors.append("alignment signal_bindings must be an array")
            return sorted(set(errors))
        seen: set[str] = set()
        for index, item in enumerate(bindings):
            row = _closed(item, BINDING_FIELDS, errors, f"alignment signal_bindings[{index}]")
            if row is None:
                continue
            signal = row.get("signal")
            if not isinstance(signal, str) or signal not in signals or signal in seen:
                errors.append(f"alignment signal_bindings[{index}].signal is invalid or duplicated")
            else:
                seen.add(signal)
            state = row.get("support_state")
            if state not in SUPPORT_STATES:
                errors.append(f"alignment signal_bindings[{index}].support_state has invalid value")
            evidence_ids = row.get("evidence_ids")
            if not isinstance(evidence_ids, list) or len(evidence_ids) != len(set(evidence_ids)) or any(not isinstance(identifier, str) or identifier not in known_evidence for identifier in evidence_ids):
                errors.append(f"alignment signal_bindings[{index}].evidence_ids has invalid values")
                continue
            if state == "unknown" and evidence_ids:
                errors.append(f"alignment signal_bindings[{index}].unknown must not reference evidence")
            if state != "unknown" and not evidence_ids:
                errors.append(f"alignment signal_bindings[{index}].support state requires evidence")
            permitted = {
                "verified_match": {"verified"},
                "candidate_reported_match": {"candidate_reported"},
                "adjacent_evidence": {"verified", "candidate_reported"},
                "explicit_gap": {"verified", "candidate_reported"},
                "unknown": set(),
            }.get(state, set())
            if state != "unknown" and any(known_evidence.get(identifier) not in permitted for identifier in evidence_ids):
                errors.append(f"alignment signal_bindings[{index}].evidence state is incompatible")
        if seen != signals:
            errors.append("alignment must cover every scoreable signal exactly once")
    except (TypeError, ValueError, KeyError, RecursionError):
        errors.append("candidate market alignment could not be validated")
    return sorted(set(errors))


def _qualitative_band(alignment: int, coverage: int) -> str:
    if coverage < 50:
        return "insufficient_evidence"
    if alignment >= 75:
        return "higher_documented_alignment"
    if alignment >= 50:
        return "moderate_documented_alignment"
    return "lower_documented_alignment"


def build_market_dossier(
    research: Mapping[str, object], executive_dossier: Mapping[str, object], alignment: Mapping[str, object],
) -> dict[str, object]:
    """Build one deterministic scoreable market artifact from validated inputs."""
    research_copy = copy.deepcopy(dict(research))
    dossier_copy = copy.deepcopy(dict(executive_dossier))
    alignment_copy = copy.deepcopy(dict(alignment))
    if RESEARCH.validate_research(research_copy):
        raise ValueError("target vacancy research is invalid")
    if EXECUTIVE.validate_dossier(dossier_copy):
        raise ValueError("executive dossier is invalid")
    if research_copy.get("locale") != dossier_copy.get("locale") or research_copy.get("as_of_date") != dossier_copy.get("evidence_as_of"):
        raise ValueError("research and executive dossier locale/date do not match")
    alignment_errors = validate_alignment(alignment_copy, research_copy, dossier_copy)
    if alignment_errors:
        raise ValueError("candidate market alignment is invalid")
    bindings = {row["signal"]: row for row in alignment_copy["signal_bindings"]}
    employers = {
        row["employer_id"]: row["display_name"]
        for row in research_copy["employers"]
        if isinstance(row, Mapping)
    }
    cards: list[dict[str, object]] = []
    for vacancy in research_copy["vacancies"]:
        requirements = [
            {key: requirement[key] for key in ("requirement_id", "signal", "importance")}
            for requirement in vacancy["requirements"]
        ]
        earned, maximum, known = OUTPUT.alignment_score(requirements, bindings)
        alignment_percent = OUTPUT.rounded_percent(earned, maximum)
        coverage_percent = OUTPUT.rounded_percent(known, maximum)
        cards.append({
            "vacancy_id": vacancy["vacancy_id"],
            "employer_name": employers[vacancy["employer_id"]],
            "title": vacancy["title"],
            "location": vacancy["location"],
            "arrangement": vacancy["arrangement"],
            "source_kind": vacancy["source_kind"],
            "source_url": vacancy["source_url"],
            "requirements": requirements,
            "earned_points": earned,
            "maximum_points": maximum,
            "known_points": known,
            "alignment_percent": alignment_percent,
            "evidence_coverage_percent": coverage_percent,
            "interpretation": "directional_documented_evidence_not_hiring_fit",
            "qualitative_band": _qualitative_band(alignment_percent, coverage_percent),
        })
    cards.sort(key=lambda card: (-int(card["alignment_percent"]), str(card["vacancy_id"])))
    ordered_ids = [card["vacancy_id"] for card in cards]
    all_signals = sorted({requirement["signal"] for card in cards for requirement in card["requirements"]})
    matrix_rows = []
    for signal in all_signals:
        binding = bindings[signal]
        matrix_rows.append({
            "signal": signal,
            "support_state": binding["support_state"],
            "evidence_ids": list(binding["evidence_ids"]),
            "cells": [
                {"vacancy_id": card["vacancy_id"], "required": any(requirement["signal"] == signal for requirement in card["requirements"])}
                for card in cards
            ],
        })
    output = {
        "schema_version": "career-market-learning-dossier-v1",
        "evidence_mode": research_copy["evidence_mode"],
        "locale": research_copy["locale"],
        "as_of_date": research_copy["as_of_date"],
        "state": research_copy["state"],
        "source_research_snapshot": RESEARCH.snapshot_for_market_dossier(research_copy),
        "source_executive_dossier_snapshot": SNAPSHOTS.snapshot_for_dossier(dossier_copy),
        "search_summary": {
            "vacancy_sample_count": len(cards),
            "bounded_queries_run": research_copy["search_limit"]["bounded_queries_run"],
            "limit_reason": research_copy["search_limit"]["limit_reason"],
            "limitation": research_copy["search_limit"]["limitation"],
        },
        "vacancy_cards": cards,
        "matrix_rows": matrix_rows,
        "recurrence_rows": OUTPUT.recurrence_rows(cards, bindings),
        "learning_state": "not_evaluated",
        "learning_decisions": [],
        "methodology_boundary": "sample_based_documented_evidence_only_no_hiring_fit",
        "privacy_boundary": "identity_free_evidence_references_only",
        "no_external_action": True,
    }
    if OUTPUT.validate_market_dossier(output):
        raise ValueError("built market dossier failed validation")
    return output


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("research", type=Path)
    parser.add_argument("dossier", type=Path)
    parser.add_argument("alignment", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        research = RESEARCH.load_research(args.research)
        dossier = EXECUTIVE.load_dossier(args.dossier)
        alignment = _load_alignment(args.alignment)
        output = build_market_dossier(research, dossier, alignment)
        _write_private_json(args.output, output)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        print("market learning dossier could not be built", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
