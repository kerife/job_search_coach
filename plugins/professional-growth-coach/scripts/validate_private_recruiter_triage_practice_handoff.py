#!/usr/bin/env python3
"""Fail-closed validation for one private triage-to-practice handoff."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path


SCHEMA_VERSION = "private-recruiter-triage-practice-handoff-v2"
LEGACY_SCHEMA_VERSION = "private-recruiter-triage-practice-handoff-v1"
_SNAPSHOT_PREFIX = "snap-triage-sha256-"
_PROJECTION_SNAPSHOT_PREFIX = "snap-practice-sha256-"
_QUESTION_KINDS = frozenset({
    "screen_opening", "proof_example", "eligibility_boundary",
    "compensation_boundary", "missing_detail",
})
_COPY = {
    "es": {
        "screen_opening": ("Practica una apertura breve y verificable para una conversación inicial.", "Evalúa claridad, brevedad y apego al contexto validado."),
        "proof_example": ("Practica un ejemplo verificable conectado con el hecho confirmado.", "Evalúa un ejemplo concreto, verificable y sin afirmaciones adicionales."),
        "eligibility_boundary": ("Practica una respuesta que mantenga los límites de elegibilidad confirmados.", "Evalúa claridad sobre los límites confirmados sin suponer condiciones."),
        "compensation_boundary": ("Practica una respuesta que mantenga los límites de compensación confirmados.", "Evalúa claridad sobre los límites confirmados sin añadir cifras o promesas."),
        "missing_detail": ("Practica una pregunta breve para aclarar el detalle faltante.", "Evalúa una petición concreta de aclaración sin suposiciones."),
    },
    "en": {
        "screen_opening": ("Practice a brief, verifiable opening for an initial conversation.", "Assess clarity, brevity, and adherence to the validated context."),
        "proof_example": ("Practice a verifiable example connected to the confirmed fact.", "Assess a concrete, verifiable example without added claims."),
        "eligibility_boundary": ("Practice an answer that keeps the confirmed eligibility boundaries.", "Assess clarity about confirmed boundaries without assumed conditions."),
        "compensation_boundary": ("Practice an answer that keeps the confirmed compensation boundaries.", "Assess clarity about confirmed boundaries without figures or promises."),
        "missing_detail": ("Practice a brief question to clarify the missing detail.", "Assess a concrete clarification request without assumptions."),
    },
}


class HandoffLoadError(ValueError):
    """Raised for concise, privacy-safe input failures."""


class _ArgumentError(ValueError):
    """Internal parse failure that deliberately carries no argument text."""


class _PrivateArgumentParser(argparse.ArgumentParser):
    """Prevent argparse from reflecting private values in diagnostics."""

    def error(self, message: str) -> None:
        del message
        raise _ArgumentError


@lru_cache(maxsize=None)
def _load_sibling(name: str):
    path = Path(__file__).with_name(f"{name}.py")
    specification = importlib.util.spec_from_file_location(
        f"private_recruiter_triage_practice_handoff_{name}", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("validation dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    scripts_dir = str(path.parent)
    added_path = scripts_dir not in sys.path
    if added_path:
        sys.path.insert(0, scripts_dir)
    try:
        specification.loader.exec_module(module)
    finally:
        if added_path:
            sys.path.remove(scripts_dir)
    return module


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise HandoffLoadError("duplicate JSON key")
        result[key] = value
    return result


def _assert_max_depth(value: object, maximum: int = 12, depth: int = 0) -> None:
    if depth > maximum:
        raise HandoffLoadError("JSON nesting exceeds safe limit")
    if isinstance(value, Mapping):
        for child in value.values():
            _assert_max_depth(child, maximum, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _assert_max_depth(child, maximum, depth + 1)


def load_handoff(path: Path) -> dict[str, object]:
    """Load one bounded private handoff JSON object without following symlinks."""
    loader = _load_sibling("private_input_loader")
    try:
        raw_bytes = loader.read_bounded_bytes(path, 64_000)
    except loader.PrivateInputError as error:
        message = {
            "symlink": "handoff input must not be a symlink",
            "too_large": "handoff input exceeds safe size limit",
        }.get(error.reason, "handoff input is unavailable")
        raise HandoffLoadError(message) from error
    try:
        raw = raw_bytes.decode("utf-8")
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeError, json.JSONDecodeError, RecursionError, HandoffLoadError, ValueError) as error:
        raise HandoffLoadError("handoff input is not valid JSON") from error
    _assert_max_depth(value)
    if not isinstance(value, dict):
        raise HandoffLoadError("handoff input must be a JSON object")
    return value


def _mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _schema_errors(value: object) -> list[str]:
    schema_version = value.get("schema_version") if isinstance(value, Mapping) else None
    selected_version = schema_version if schema_version in {SCHEMA_VERSION, LEGACY_SCHEMA_VERSION} else SCHEMA_VERSION
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / f"{selected_version}.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["handoff schema is unavailable"]
    return _load_sibling("validate_json_schema_subset").validate_schema_instance(value, schema)


def projection_snapshot_for_session(session: Mapping[str, object]) -> str:
    """Return a deterministic integrity digest for the projected practice session."""
    encoded = json.dumps(session, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _PROJECTION_SNAPSHOT_PREFIX + hashlib.sha256(encoded).hexdigest()


def _projected_reference_errors(handoff: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    session = _mapping(handoff.get("practice_session"))
    if session is None:
        return errors
    context = _mapping(session.get("handoff_context"))
    question = _mapping(session.get("question"))
    requirement = _mapping(session.get("requirement"))
    rubric = _mapping(session.get("rubric"))
    facts = session.get("facts")
    if context is None or question is None or requirement is None or rubric is None:
        return errors
    if context.get("source_snapshot") != handoff.get("source_snapshot"):
        errors.append("practice_session.handoff_context.source_snapshot must match handoff.source_snapshot")
    if context.get("source") != "private_recruiter_reply_triage":
        errors.append("practice_session.handoff_context.source must be private_recruiter_reply_triage")
    if context.get("question_rank") != 1 or context.get("question_id") != "Q-001" or context.get("requirement_id") != "R-001" or context.get("fact_ids") != ["F-001"]:
        errors.append("practice_session.handoff_context must reference Q-001, R-001, and F-001 at rank 1")
    if question.get("kind") != handoff.get("prep_scope"):
        errors.append("practice_session.question.kind must match handoff.prep_scope")
    if question.get("id") != "Q-001" or question.get("requirement_id") != "R-001" or question.get("fact_ids") != ["F-001"]:
        errors.append("practice_session.question must reference Q-001, R-001, and F-001")
    if requirement.get("id") != "R-001" or requirement.get("fact_ids") != ["F-001"]:
        errors.append("practice_session.requirement must reference R-001 and F-001")
    if not isinstance(facts, list) or len(facts) != 1 or not isinstance(facts[0], Mapping) or facts[0].get("id") != "F-001" or facts[0].get("state") != "verified":
        errors.append("practice_session.facts must contain verified F-001")
    locale = session.get("content_locale")
    scope = handoff.get("prep_scope")
    if locale not in _COPY or scope not in _QUESTION_KINDS:
        return errors
    expected_requirement, expected_rubric = _COPY[locale][scope]
    if requirement.get("summary") != expected_requirement:
        errors.append("practice_session.requirement.summary must match the fixed scope copy")
    if rubric.get("criterion") != expected_rubric:
        errors.append("practice_session.rubric.criterion must match the fixed scope copy")
    if session.get("ui_locale") != locale:
        errors.append("practice_session.ui_locale must match practice_session.content_locale")
    return errors


def _triage_prose_errors(handoff: Mapping[str, object]) -> list[str]:
    """Reject source-derived prose that cannot safely enter a private handoff."""
    session = _mapping(handoff.get("practice_session"))
    if session is None:
        return []
    context = _mapping(session.get("safe_context"))
    question = _mapping(session.get("question"))
    facts = session.get("facts")
    if context is None or question is None or not isinstance(facts, list) or len(facts) != 1:
        return []
    fact = _mapping(facts[0])
    if fact is None:
        return []
    guard = _load_sibling("triage_practice_prose_safety").is_safe_triage_practice_prose
    fields = (
        ("practice_session.safe_context.summary", context.get("summary"), 280),
        ("practice_session.question.text", question.get("text"), 500),
        ("practice_session.facts[0].summary", fact.get("summary"), 500),
    )
    return [f"{path} must be safe triage-sourced prose" for path, value, maximum in fields if not guard(value, maximum)]


def validate_handoff(value: object) -> list[str]:
    """Return sorted errors; an empty list means a safe closed handoff."""
    errors = _schema_errors(value)
    handoff = _mapping(value)
    if handoff is None:
        return sorted(set(errors))
    schema_version = handoff.get("schema_version")
    if schema_version not in {SCHEMA_VERSION, LEGACY_SCHEMA_VERSION}:
        errors.append("handoff.schema_version has invalid value")
    snapshot = handoff.get("source_snapshot")
    if not isinstance(snapshot, str) or not snapshot.startswith(_SNAPSHOT_PREFIX) or len(snapshot) != len(_SNAPSHOT_PREFIX) + 64:
        errors.append("handoff.source_snapshot must use the triage snapshot format")
    projection_snapshot = handoff.get("projection_snapshot")
    if schema_version == SCHEMA_VERSION or projection_snapshot is not None:
        if not isinstance(projection_snapshot, str) or not projection_snapshot.startswith(_PROJECTION_SNAPSHOT_PREFIX) or len(projection_snapshot) != len(_PROJECTION_SNAPSHOT_PREFIX) + 64:
            errors.append("handoff.projection_snapshot must use the practice projection format")
    session = _mapping(handoff.get("practice_session"))
    if session is None:
        errors.append("practice_session must be an object")
        return sorted(set(errors))
    if (
        isinstance(projection_snapshot, str)
        and projection_snapshot.startswith(_PROJECTION_SNAPSHOT_PREFIX)
        and (schema_version == SCHEMA_VERSION or projection_snapshot is not None)
        and projection_snapshot != projection_snapshot_for_session(session)
    ):
        errors.append("handoff.projection_snapshot must match practice_session content")
    errors.extend(_load_sibling("validate_recruiter_practice_session").validate_session(session))
    errors.extend(_projected_reference_errors(handoff))
    errors.extend(_triage_prose_errors(handoff))
    return sorted(set(errors))


def _error(code: str) -> None:
    print(json.dumps({"error": {"code": code}}, separators=(",", ":")), file=sys.stderr)


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Validate a private triage practice handoff.")
    parser.add_argument("input", type=Path, help="Path to one handoff JSON file.")
    try:
        arguments = parser.parse_args(argv)
    except _ArgumentError:
        _error("invalid_arguments")
        return 3
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    try:
        handoff = load_handoff(arguments.input)
    except HandoffLoadError as error:
        print(str(error), file=sys.stderr)
        return 3
    errors = validate_handoff(handoff)
    if errors:
        sys.stderr.write(_load_sibling("private_prose_safety").format_bounded_diagnostics(errors))
        return 2
    print("valid private recruiter triage practice handoff")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
