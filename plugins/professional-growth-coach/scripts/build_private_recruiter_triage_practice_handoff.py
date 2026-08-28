#!/usr/bin/env python3
"""Fail-closed composition from verified recruiter triage to private practice."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import secrets
import stat
import sys
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path


SCHEMA_VERSION = "private-recruiter-triage-practice-handoff-v2"
_QUESTION_KINDS = frozenset({
    "screen_opening", "proof_example", "eligibility_boundary",
    "compensation_boundary", "missing_detail",
})
_DELIVERY = {
    "draft_only": True,
    "external_actions_authorized": False,
    "manual_reentry_required": True,
    "auto_start": False,
    "local_save_mode": "disabled",
    "raw_reply_retained": False,
}
_PRACTICE_DELIVERY = {
    "draft_only": True,
    "external_actions_authorized": False,
    "local_save_mode": "disabled",
    "raw_answer_retained": False,
}
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


class CompositionError(ValueError):
    """Raised when triage cannot safely compose into a practice session."""


class TriageInputError(CompositionError):
    """Raised when the supplied private triage file cannot be safely decoded."""


class _ArgumentError(ValueError):
    """Internal parse failure that deliberately carries no supplied argument text."""


class _PrivateArgumentParser(argparse.ArgumentParser):
    """Prevent argparse from reflecting private CLI values in usage diagnostics."""

    def error(self, message: str) -> None:
        del message
        raise _ArgumentError


@lru_cache(maxsize=None)
def _load_sibling(name: str):
    path = Path(__file__).with_name(f"{name}.py")
    specification = importlib.util.spec_from_file_location(
        f"job_search_coach_triage_practice_handoff_{name}", path
    )
    if specification is None or specification.loader is None:
        raise CompositionError("composition dependency is unavailable")
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


def validate_triage(value: object) -> list[str]:
    return _load_sibling("validate_private_recruiter_reply_triage").validate_triage(value)


def snapshot_for_triage(triage: Mapping[str, object]) -> str:
    return _load_sibling("triage_snapshot").snapshot_for_triage(triage)


def validate_session(value: object) -> list[str]:
    return _load_sibling("validate_recruiter_practice_session").validate_session(value)


def validate_handoff(value: object) -> list[str]:
    return _load_sibling("validate_private_recruiter_triage_practice_handoff").validate_handoff(value)


def projection_snapshot_for_session(session: Mapping[str, object]) -> str:
    return _load_sibling("validate_private_recruiter_triage_practice_handoff").projection_snapshot_for_session(session)


def validate_schema_instance(value: object, schema: Mapping[str, object]) -> list[str]:
    return _load_sibling("validate_json_schema_subset").validate_schema_instance(value, schema)


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CompositionError(f"{label} is unavailable")
    return value


def _source_fields(triage: Mapping[str, object]) -> tuple[str, str, str, str, str]:
    handoff = _mapping(triage.get("handoff"), "triage handoff")
    packet = _mapping(handoff.get("packet"), "triage handoff packet")
    reentry = _mapping(handoff.get("reentry_packet"), "triage reentry packet")
    snapshot = snapshot_for_triage(triage)
    values = ("context_summary", "source_snapshot", "fact_id", "question_id", "prep_scope")
    if any(packet.get(field) != reentry.get(field) for field in values):
        raise CompositionError("triage handoff packet and reentry packet differ")
    if packet.get("source_snapshot") != snapshot:
        raise CompositionError("triage handoff snapshot does not match content")
    context = packet.get("context_summary")
    fact_id = packet.get("fact_id")
    question_id = packet.get("question_id")
    scope = packet.get("prep_scope")
    if not all(isinstance(value, str) for value in (context, fact_id, question_id, scope)):
        raise CompositionError("triage handoff references are invalid")
    return snapshot, context, fact_id, question_id, scope


def build_handoff(triage: Mapping[str, object]) -> dict[str, object]:
    """Return a closed, unanswered session only for one verified ready triage."""
    if not isinstance(triage, Mapping) or validate_triage(triage):
        raise CompositionError("triage validation failed")
    if triage.get("schema_version") != "private-recruiter-reply-triage-v2":
        raise CompositionError("triage must use schema version v2")
    if triage.get("state") != "ready_for_private_prep" or triage.get("handoff_allowed") is not True:
        raise CompositionError("triage is not ready for private preparation")

    snapshot, context_summary, source_fact_id, source_question_id, prep_scope = _source_fields(triage)
    if prep_scope not in _QUESTION_KINDS:
        raise CompositionError("triage preparation scope is unsupported")
    safe_context = _mapping(triage.get("safe_context"), "triage safe context")
    facts = triage.get("facts")
    question = _mapping(triage.get("question"), "triage question")
    if not isinstance(facts, list) or len(facts) != 1:
        raise CompositionError("triage must provide one verified fact")
    fact = _mapping(facts[0], "triage fact")
    if fact.get("state") != "verified" or fact.get("id") != source_fact_id:
        raise CompositionError("triage fact reference is not verified")
    if question.get("id") != source_question_id or question.get("kind") != prep_scope:
        raise CompositionError("triage question reference is invalid")
    if safe_context.get("summary") != context_summary:
        raise CompositionError("triage context reference is invalid")
    fact_ids = question.get("fact_ids")
    if fact_ids != [source_fact_id]:
        raise CompositionError("triage question fact reference is invalid")
    locale = triage.get("content_locale")
    ui_locale = triage.get("ui_locale")
    if locale not in _COPY or ui_locale not in {"es", "en"}:
        raise CompositionError("triage locale is invalid")
    requirement_summary, rubric_criterion = _COPY[locale][prep_scope]
    source_question_text = question.get("text")
    source_fact_summary = fact.get("summary")
    if not isinstance(source_question_text, str) or not isinstance(source_fact_summary, str):
        raise CompositionError("triage source prose is invalid")

    projected_fact_ids = ["F-001"]
    practice_session: dict[str, object] = {
        "schema_version": "recruiter-practice-session-v2",
        "session_kind": "private_recruiter_practice",
        "ui_locale": ui_locale,
        "content_locale": locale,
        "state": "ready_to_practice",
        "safe_context": {
            "stage": "recruiter_screen",
            "vacancy_state": "safe_summary_provided",
            "summary": context_summary,
        },
        "requirement": {"id": "R-001", "summary": requirement_summary, "fact_ids": projected_fact_ids},
        "question": {"id": "Q-001", "kind": prep_scope, "text": source_question_text, "requirement_id": "R-001", "fact_ids": projected_fact_ids},
        "facts": [{"id": "F-001", "state": "verified", "summary": source_fact_summary}],
        "observed_answer": None,
        "rubric": {"id": "RB-001", "criterion": rubric_criterion},
        "feedback": {"score": "unknown", "score_state": "unknown", "observations": []},
        "delivery": dict(_PRACTICE_DELIVERY),
        "handoff_context": {
            "source": "private_recruiter_reply_triage",
            "source_snapshot": snapshot,
            "question_rank": 1,
            "question_id": "Q-001",
            "requirement_id": "R-001",
            "fact_ids": projected_fact_ids,
            "draft_only": True,
            "external_actions_authorized": False,
        },
    }
    handoff: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "source_artifact_kind": "private_recruiter_reply_triage",
        "source_snapshot": snapshot,
        "projection_snapshot": projection_snapshot_for_session(practice_session),
        "prep_scope": prep_scope,
        "practice_session": practice_session,
        "delivery": dict(_DELIVERY),
    }
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / f"{SCHEMA_VERSION}.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CompositionError("handoff schema is unavailable") from error
    if validate_schema_instance(handoff, schema):
        raise CompositionError("handoff output failed schema validation")
    if validate_session(practice_session):
        raise CompositionError("practice projection failed validation")
    return handoff


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CompositionError("input JSON contains duplicate keys")
        result[key] = value
    return result


def _assert_max_depth(value: object, maximum: int = 12, depth: int = 0) -> None:
    if depth > maximum:
        raise TriageInputError("triage input is unavailable")
    if isinstance(value, Mapping):
        for child in value.values():
            _assert_max_depth(child, maximum, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _assert_max_depth(child, maximum, depth + 1)


def load_triage(path: Path) -> dict[str, object]:
    """Load exactly one bounded v2 triage object without following symlinks."""
    loader = _load_sibling("private_input_loader")
    try:
        raw_bytes = loader.read_bounded_bytes(path, 64_000)
        decoded = raw_bytes.decode("utf-8")
        value = json.loads(decoded, object_pairs_hook=_unique_object)
    except (UnicodeError, json.JSONDecodeError, RecursionError, CompositionError, ValueError, loader.PrivateInputError) as error:
        raise TriageInputError("triage input is unavailable") from error
    _assert_max_depth(value)
    if not isinstance(value, dict):
        raise TriageInputError("triage input must be an object")
    return value


def _open_private_parent(parent: Path) -> int:
    if not parent.is_absolute() or parent.anchor != os.sep:
        raise OSError("output parent is unsafe")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    if not nofollow or not directory_flag:
        raise OSError("safe output is unsupported")
    descriptor = os.open(os.sep, os.O_RDONLY | directory_flag | getattr(os, "O_CLOEXEC", 0))
    try:
        for index, component in enumerate(parent.parts[1:]):
            if component in {"", ".", ".."}:
                raise OSError("output parent is unsafe")
            try:
                os.mkdir(component, 0o700, dir_fd=descriptor)
            except FileExistsError:
                pass
            absolute = os.path.join(os.sep, component)
            trusted_alias = (
                index == 0
                and component in {"tmp", "var"}
                and os.path.islink(absolute)
                and os.path.realpath(absolute) == os.path.join(os.sep, "private", component)
            )
            child = os.open(
                component,
                os.O_RDONLY | directory_flag | getattr(os, "O_CLOEXEC", 0) | (0 if trusted_alias else nofollow),
                dir_fd=descriptor,
            )
            if not stat.S_ISDIR(os.fstat(child).st_mode):
                os.close(child)
                raise OSError("output parent is unsafe")
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _atomic_private_write(output: Path, content: bytes, *, force: bool) -> None:
    if not output.name or output.name in {".", ".."}:
        raise OSError("output target is unsafe")
    parent = _open_private_parent(output.parent)
    temporary: str | None = None
    descriptor: int | None = None
    try:
        try:
            current = os.stat(output.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            current = None
        if current is not None:
            if stat.S_ISLNK(current.st_mode) or not stat.S_ISREG(current.st_mode):
                raise OSError("output target is unsafe")
            if not force:
                raise FileExistsError("output already exists")
        for _ in range(100):
            candidate = f".{output.name}.tmp-{secrets.token_hex(8)}"
            try:
                descriptor = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=parent)
                temporary = candidate
                break
            except FileExistsError:
                continue
        if temporary is None or descriptor is None:
            raise OSError("cannot create private output")
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            os.fchmod(stream.fileno(), 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if force:
            os.replace(temporary, output.name, src_dir_fd=parent, dst_dir_fd=parent)
        else:
            try:
                os.link(temporary, output.name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
            except FileExistsError as error:
                raise FileExistsError("output already exists") from error
            os.unlink(temporary, dir_fd=parent)
        temporary = None
        os.fsync(parent)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
        os.close(parent)


def write_handoff(triage_path: Path, output_path: Path, *, force: bool = False) -> None:
    """Build, validate, canonically encode, and privately write one handoff."""
    triage = load_triage(triage_path)
    handoff = build_handoff(triage)
    if validate_handoff(handoff):
        raise CompositionError("handoff validation failed")
    output = Path(os.path.abspath(os.fspath(output_path.expanduser())))
    encoded = json.dumps(handoff, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    _atomic_private_write(output, encoded, force=force)


def _error(code: str) -> None:
    print(json.dumps({"error": {"code": code}}, separators=(",", ":")), file=sys.stderr)


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Compose a private triage practice handoff.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    try:
        arguments = parser.parse_args(argv)
    except _ArgumentError:
        _error("invalid_arguments")
        return 3
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    try:
        write_handoff(arguments.input, arguments.output, force=arguments.force)
    except FileExistsError:
        _error("output_exists")
        return 3
    except OSError:
        _error("unsafe_output")
        return 3
    except TriageInputError:
        _error("invalid_input")
        return 3
    except CompositionError:
        _error("validation_failed")
        return 2
    print(json.dumps({"artifact_kind": "private_recruiter_triage_practice_handoff", "schema_version": SCHEMA_VERSION}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
