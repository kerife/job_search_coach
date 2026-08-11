#!/usr/bin/env python3
"""Fail-closed validation for one private recruiter practice session."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from private_prose_safety import is_safe_prose_text


SCHEMA_VERSION = "recruiter-practice-session-v1"
V2_SCHEMA_VERSION = "recruiter-practice-session-v2"
TOP_LEVEL_FIELDS = frozenset({
    "schema_version", "session_kind", "locale", "state", "safe_context",
    "requirement", "question", "facts", "observed_answer", "rubric",
    "feedback", "delivery", "handoff_context",
})
REQUIRED_TOP_LEVEL_FIELDS = TOP_LEVEL_FIELDS - {"handoff_context"}
V2_TOP_LEVEL_FIELDS = frozenset({
    "schema_version", "session_kind", "ui_locale", "content_locale", "state",
    "safe_context", "requirement", "question", "facts", "observed_answer",
    "rubric", "feedback", "delivery", "handoff_context",
})
V2_REQUIRED_TOP_LEVEL_FIELDS = V2_TOP_LEVEL_FIELDS - {"handoff_context"}


def _enum(value: object, allowed: set[str] | frozenset[str]) -> bool:
    return isinstance(value, str) and value in allowed
IDENTITY_OR_RAW_CONTENT = re.compile(
    r"\b(?:candidate(?:\s+name)?|prepared\s+for|nombre(?:\s+del\s+candidat[oa])?|"
    r"my\s+name\s+is|me\s+llamo|company|empresa|compañ[ií]a|employer|empleador)\s*:|"
    r"\b(?:linkedin|curriculum\s+vitae|resume|"
    r"raw\s+(?:vacancy|profile)|job\s+description)\b|"
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|\+?\d[\d .()-]{7,}\d",
    re.IGNORECASE,
)
EXTERNAL_ACTION = re.compile(
    r"\b(?:contact(?:a|e|ar)?|mensajea|env[ií]a|escribe|comparte|llama|aplica|postula|publica|"
    r"sube|agenda|programa)\b[^.!?\n]{0,72}\b(?:reclutador|recruiter|empresa|compañ[ií]a|"
    r"hiring\s+manager|empleador|employer|"
    r"mensaje|message|solicitud|application|perfil|profile|entrevista|interview)\b|"
    r"\b(?:reach\s+out|send\s+(?:a\s+)?message|apply\s+for|publish\s+(?:the\s+)?profile|"
    r"schedule\s+(?:an\s+)?interview)\b",
    re.IGNORECASE,
)
OUTCOME_GUARANTEE = re.compile(
    r"\b(?:guarantee[sd]?|assured|promise[sd]?|will\s+(?:get|receive|land)\s+(?:an\s+)?"
    r"(?:interview|offer|job)|entrevista|oferta|empleo)\b[^.!?\n]{0,32}\b"
    r"(?:garantizad[oa]|asegurad[oa])\b|"
    r"\b(?:te\s+)?(?:garantizo|garantizamos|garantizad[oa]|aseguro|aseguramos|asegurad[oa])\b"
    r"[^.!?\n]{0,64}\b(?:entrevista|oferta|empleo|interview|offer|job)\b",
    re.IGNORECASE,
)
NUMERIC_READINESS = re.compile(
    r"\b(?:readiness|preparedness|preparaci[oó]n|list[oa]\s+para\s+(?:la\s+)?entrevista|"
    r"interview[-\s]?ready)\b[^.!?\n]{0,32}\b(?:100|[1-9]?\d)\s*%|"
    r"\b(?:100|[1-9]?\d)\s*%\s*(?:readiness|preparedness|preparaci[oó]n|list[oa])\b",
    re.IGNORECASE,
)
PRIVATE_ANALYTICS = re.compile(
    r"\b(?:private\s+analytics|anal[ií]ticas?\s+privadas?|profile\s+(?:views|traffic)|"
    r"visitas?\s+(?:privadas?\s+)?al\s+perfil|inbound\s+contacts?|contactos?\s+entrantes?)\b",
    re.IGNORECASE,
)
INTERNAL_FEEDBACK_IDENTIFIER = re.compile(
    r"(?<![A-Z0-9])(?:OBS|RB)\s*-\s*\d{3}(?!\d)", re.IGNORECASE
)
OBFUSCATED_FEEDBACK_IDENTIFIER = re.compile(
    r"(?<![A-Z0-9])(?:O\s*B\s*S|R\s*B)\s*-\s*\d{3}(?!\d)", re.IGNORECASE
)
INTERNAL_PROSE_IDENTIFIER = re.compile(
    r"(?<![A-Z0-9])(?:Q|R|F)\s*-\s*\d{3}(?!\d)", re.IGNORECASE
)
OBFUSCATED_PROSE_IDENTIFIER = re.compile(
    r"(?<![A-Z0-9])(?:Q|R|F)\s*-\s*\d{3}(?!\d)|(?<![A-Z0-9])(?:Q|\s*R|\s*F)\s*\d{3}(?!\d)", re.IGNORECASE
)


class SessionLoadError(ValueError):
    """Raised for deterministic, privacy-safe JSON input failures."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SessionLoadError("duplicate JSON key")
        result[key] = value
    return result


def _assert_max_depth(value: object, maximum: int = 12, depth: int = 0) -> None:
    if depth > maximum:
        raise SessionLoadError("JSON nesting exceeds safe limit")
    if isinstance(value, Mapping):
        for child in value.values():
            _assert_max_depth(child, maximum, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _assert_max_depth(child, maximum, depth + 1)


def load_session(path: Path) -> dict[str, object]:
    if path.is_symlink():
        raise SessionLoadError("session input must not be a symlink")
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise SessionLoadError("session input is unavailable") from error
    if len(raw.encode("utf-8")) > 64_000:
        raise SessionLoadError("session input exceeds safe size limit")
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, SessionLoadError) as error:
        raise SessionLoadError("session input is not valid JSON") from error
    _assert_max_depth(value)
    if not isinstance(value, dict):
        raise SessionLoadError("session input must be a JSON object")
    return value


def _closed(
    value: object,
    path: str,
    fields: frozenset[str],
    errors: list[str],
    *,
    required: frozenset[str] | None = None,
) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    missing = sorted((fields if required is None else required) - set(value))
    unsupported = sorted(set(value) - fields)
    for field in missing:
        errors.append(f"missing required field: {path}.{field}" if path else f"missing required field: {field}")
    if unsupported:
        prefix = "session" if not path else path
        errors.append(f"{prefix} has unsupported fields: {', '.join(unsupported)}")
    return value


def _text(value: object, path: str, errors: list[str], *, maximum: int) -> str | None:
    if not is_safe_prose_text(value) or not value.strip() or len(value) > maximum:
        errors.append(f"{path} must be non-empty prose within {maximum} characters")
        return None
    return value


def _id(value: object, path: str, prefix: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not re.fullmatch(rf"{re.escape(prefix)}-[0-9]{{3}}", value):
        errors.append(f"{path} must use the {prefix}-000 identifier format")
        return None
    return value


def _references(
    value: object,
    known: set[str],
    path: str,
    errors: list[str],
    *,
    allowed: set[str] | None = None,
    maximum: int = 1,
) -> list[str]:
    valid_shape = isinstance(value, list) and 1 <= len(value) <= maximum
    valid_types = valid_shape and all(isinstance(item, str) for item in value)
    valid_unique = valid_types and len(value) == len(set(value))
    if not (valid_shape and valid_types and valid_unique):
        errors.append(
            f"{path} must contain exactly one reference"
            if maximum == 1
            else f"{path} must contain one through {maximum} unique references"
        )
        return []
    references = list(value)
    for reference in references:
        if allowed is not None and reference not in allowed:
            errors.append(f"{path} may reference only OBS-001 or RB-001")
        elif reference not in known:
            errors.append(f"{path} references unknown identifier: {reference}")
    return references


def _walk_strings(value: object, *, path: tuple[str, ...] = ()) -> Sequence[str]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        return tuple(
            text
            for key, child in value.items()
            if not (path == ("handoff_context",) and key == "source_snapshot")
            for text in _walk_strings(child, path=path + (key,))
        )
    if isinstance(value, list):
        return tuple(text for child in value for text in _walk_strings(child, path=path))
    return ()


def _validate_prose_safety(value: Mapping[str, object], errors: list[str]) -> None:
    text = "\n".join(_walk_strings(value))
    if IDENTITY_OR_RAW_CONTENT.search(text):
        errors.append("session contains forbidden identity or raw-content prose")
    if EXTERNAL_ACTION.search(text):
        errors.append("session contains external-action prose")
    if OUTCOME_GUARANTEE.search(text):
        errors.append("session contains outcome-guarantee prose")
    if NUMERIC_READINESS.search(text):
        errors.append("session contains numeric-readiness prose")
    if PRIVATE_ANALYTICS.search(text):
        errors.append("session contains private-analytics prose")


def _normalize_feedback_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    without_format_controls = "".join(
        " " if character.isspace()
        else "" if unicodedata.category(character) in {"Cc", "Cf"}
        else character
        for character in normalized
    )
    return re.sub(r"\s+", " ", without_format_controls).strip()


def _validate_feedback_statement(
    statement: str | None,
    observed_answer_text: str | None,
    path: str,
    errors: list[str],
) -> None:
    if statement is None:
        return
    normalized_statement = _normalize_feedback_text(statement)
    identifier_scan = re.sub(r"(?<=\w)\s*-\s*(?=\d)", "-", normalized_statement)
    if (
        observed_answer_text is not None
        and _normalize_feedback_text(observed_answer_text) in normalized_statement
    ):
        errors.append(f"{path} must not repeat the observed answer")
    if INTERNAL_FEEDBACK_IDENTIFIER.search(identifier_scan) or OBFUSCATED_FEEDBACK_IDENTIFIER.search(normalized_statement):
        errors.append(f"{path} must not expose internal identifiers")


def _validate_prose_identifier(value: object, path: str, errors: list[str]) -> None:
    normalized = unicodedata.normalize("NFKC", value) if isinstance(value, str) else ""
    normalized = "".join(character for character in normalized if unicodedata.category(character) not in {"Cc", "Cf"})
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if INTERNAL_PROSE_IDENTIFIER.search(normalized) or OBFUSCATED_PROSE_IDENTIFIER.search(normalized):
        errors.append(f"{path} must not expose internal identifiers")


def validate_session(value: object) -> list[str]:
    """Return deterministic errors; an empty list means the session is safe."""

    errors: list[str] = []
    if not isinstance(value, Mapping):
        errors.append("session must be an object")
        return sorted(set(errors))
    session = value
    schema_version = session.get("schema_version")
    fields = V2_TOP_LEVEL_FIELDS if schema_version == V2_SCHEMA_VERSION else TOP_LEVEL_FIELDS
    required_fields = (
        V2_REQUIRED_TOP_LEVEL_FIELDS
        if schema_version == V2_SCHEMA_VERSION
        else REQUIRED_TOP_LEVEL_FIELDS
    )
    for field in sorted(required_fields - set(session)):
        errors.append(f"missing required field: {field}")
    unsupported = sorted(set(session) - fields)
    if unsupported:
        errors.append(f"session has unsupported fields: {', '.join(unsupported)}")
    if not _enum(schema_version, {SCHEMA_VERSION, V2_SCHEMA_VERSION}):
        errors.append("schema_version has invalid value")
    if session.get("session_kind") != "private_recruiter_practice":
        errors.append("session_kind has invalid value")
    if schema_version == V2_SCHEMA_VERSION:
        if not _enum(session.get("ui_locale"), {"es", "en"}):
            errors.append("ui_locale has invalid value")
        if not _enum(session.get("content_locale"), {"es", "en"}):
            errors.append("content_locale has invalid value")
    elif not _enum(session.get("locale"), {"es", "en"}):
        errors.append("locale has invalid value")
    state = session.get("state")
    if not _enum(state, {"ready_to_practice", "awaiting_answer", "feedback_available"}):
        errors.append("state has invalid value")

    context = _closed(session.get("safe_context"), "safe_context", frozenset({"stage", "vacancy_state", "summary"}), errors)
    if context is not None:
        if context.get("stage") != "recruiter_screen":
            errors.append("safe_context.stage must be recruiter_screen")
        if context.get("vacancy_state") != "safe_summary_provided":
            errors.append("safe_context.vacancy_state must be safe_summary_provided")
        _text(context.get("summary"), "safe_context.summary", errors, maximum=280)
        _validate_prose_identifier(context.get("summary"), "safe_context.summary", errors)

    facts_value = session.get("facts")
    fact_ids: set[str] = set()
    fact_states: dict[str, str] = {}
    if not isinstance(facts_value, list) or len(facts_value) != 1:
        errors.append("facts must contain exactly one supplied fact")
    else:
        fact = _closed(facts_value[0], "facts[0]", frozenset({"id", "state", "summary"}), errors)
        if fact is not None:
            fact_id = _id(fact.get("id"), "facts[0].id", "F", errors)
            if fact_id is not None:
                fact_ids.add(fact_id)
                if _enum(fact.get("state"), {"verified", "candidate_reported"}):
                    fact_states[fact_id] = str(fact.get("state"))
            if not _enum(fact.get("state"), {"verified", "candidate_reported"}):
                errors.append("facts[0].state must be verified or candidate_reported")
        _text(fact.get("summary"), "facts[0].summary", errors, maximum=500)
        _validate_prose_identifier(fact.get("summary"), "facts[0].summary", errors)

    requirement = _closed(session.get("requirement"), "requirement", frozenset({"id", "summary", "fact_ids"}), errors)
    requirement_id: str | None = None
    if requirement is not None:
        requirement_id = _id(requirement.get("id"), "requirement.id", "R", errors)
        _text(requirement.get("summary"), "requirement.summary", errors, maximum=280)
        _validate_prose_identifier(requirement.get("summary"), "requirement.summary", errors)
        _references(requirement.get("fact_ids"), fact_ids, "requirement.fact_ids", errors)

    question = _closed(session.get("question"), "question", frozenset({"id", "kind", "text", "requirement_id", "fact_ids"}), errors)
    if question is not None:
        _id(question.get("id"), "question.id", "Q", errors)
        if not _enum(question.get("kind"), {"screen_opening", "proof_example", "eligibility_boundary", "compensation_boundary", "missing_detail"}):
            errors.append("question.kind has invalid value")
        _text(question.get("text"), "question.text", errors, maximum=500)
        _validate_prose_identifier(question.get("text"), "question.text", errors)
        if question.get("requirement_id") != requirement_id:
            errors.append("question.requirement_id must reference the supplied requirement")
        _references(question.get("fact_ids"), fact_ids, "question.fact_ids", errors)
        question_kind = question.get("kind")
        referenced_fact_ids = question.get("fact_ids")
        if isinstance(referenced_fact_ids, list) and referenced_fact_ids:
            referenced_states = {
                fact_states[reference]
                for reference in referenced_fact_ids
                if isinstance(reference, str) and reference in fact_states
            }
            required_state = "verified" if question_kind == "proof_example" else None
            if required_state is not None and referenced_states and referenced_states != {required_state}:
                errors.append(
                    f"question.kind {question_kind} requires {required_state} fact state"
                )

    handoff = session.get("handoff_context")
    if handoff is not None:
        handoff_fields = frozenset({"source", "source_snapshot", "question_rank", "question_id", "requirement_id", "fact_ids", "claim_ids", "evidence_ids", "draft_only", "external_actions_authorized"})
        handoff_required = handoff_fields - {"claim_ids", "evidence_ids"}
        if isinstance(handoff, Mapping) and handoff.get("source") == "executive_career_dossier":
            handoff_required = handoff_fields
        handoff = _closed(handoff, "handoff_context", handoff_fields, errors, required=handoff_required)
        if handoff is not None:
            if not _enum(handoff.get("source"), {"executive_career_dossier", "private_recruiter_reply_triage"}): errors.append("handoff_context.source has invalid value")
            source_snapshot = handoff.get("source_snapshot")
            snapshot_pattern = (
                r"snap-(?:dossier-sha256-[0-9a-f]{64}|triage-(?:[0-9]{3}|sha256-[0-9a-f]{64}))"
                if schema_version == V2_SCHEMA_VERSION
                else r"snap-(?:dossier-sha256-[0-9a-f]{64}|triage-[0-9]{3})"
            )
            if not isinstance(source_snapshot, str) or not re.fullmatch(snapshot_pattern, source_snapshot):
                if schema_version == V2_SCHEMA_VERSION:
                    errors.append("handoff_context.source_snapshot must use the bound dossier or triage v2 identifier format")
                else:
                    errors.append("handoff_context.source_snapshot must use the bound dossier or snap-triage-000 identifier format")
            elif handoff.get("source") == "executive_career_dossier" and not source_snapshot.startswith("snap-dossier-sha256-"):
                errors.append("handoff_context.source_snapshot must match executive_career_dossier source")
            elif handoff.get("source") == "private_recruiter_reply_triage" and not source_snapshot.startswith("snap-triage-"):
                errors.append("handoff_context.source_snapshot must match private_recruiter_reply_triage source")
            if isinstance(handoff.get("question_rank"), bool) or handoff.get("question_rank") != 1: errors.append("handoff_context.question_rank must be 1")
            if handoff.get("draft_only") is not True: errors.append("handoff_context.draft_only must be true")
            if handoff.get("external_actions_authorized") is not False: errors.append("handoff_context.external_actions_authorized must be false")
            handoff_question_id = _id(handoff.get("question_id"), "handoff_context.question_id", "Q", errors)
            if handoff_question_id is not None and question is not None and handoff_question_id != question.get("id"):
                errors.append("handoff_context.question_id must match question.id")
            handoff_requirement_id = _id(handoff.get("requirement_id"), "handoff_context.requirement_id", "R", errors)
            if handoff_requirement_id is not None and requirement_id is not None and handoff_requirement_id != requirement_id:
                errors.append("handoff_context.requirement_id must match requirement.id")
            if handoff_requirement_id is not None and question is not None and handoff_requirement_id != question.get("requirement_id"):
                errors.append("handoff_context.requirement_id must match question.requirement_id")
            _references(handoff.get("fact_ids"), fact_ids, "handoff_context.fact_ids", errors)
            claim_ids = handoff.get("claim_ids")
            evidence_ids = handoff.get("evidence_ids")
            dossier_source = handoff.get("source") == "executive_career_dossier"
            for field, value, prefix in (("claim_ids", claim_ids, "C"), ("evidence_ids", evidence_ids, "E")):
                if field not in handoff and not dossier_source:
                    continue
                if not isinstance(value, list) or not value:
                    if dossier_source:
                        errors.append(f"handoff_context.{field} must contain {prefix}-000 identifiers for dossier source")
                    else:
                        errors.append(f"handoff_context.{field} must be a non-empty list")
                elif len(value) > 10:
                    errors.append(f"handoff_context.{field} must contain at most 10 identifiers")
                elif not all(isinstance(item, str) and re.fullmatch(rf"{prefix}-[0-9]{{3}}", item) for item in value):
                    errors.append(f"handoff_context.{field} must contain {prefix}-000 identifiers" + (" for dossier source" if dossier_source else ""))
                elif len(set(value)) != len(value):
                    errors.append(f"handoff_context.{field} must contain unique {prefix}-000 identifiers")

    rubric = _closed(session.get("rubric"), "rubric", frozenset({"id", "criterion"}), errors)
    rubric_id: str | None = None
    if rubric is not None:
        rubric_id = _id(rubric.get("id"), "rubric.id", "RB", errors)
        _text(rubric.get("criterion"), "rubric.criterion", errors, maximum=500)
        _validate_prose_identifier(rubric.get("criterion"), "rubric.criterion", errors)

    answer = session.get("observed_answer")
    answer_id: str | None = None
    answer_text: str | None = None
    if answer is not None:
        observed = _closed(answer, "observed_answer", frozenset({"id", "text", "storage"}), errors)
        if observed is not None:
            answer_id = _id(observed.get("id"), "observed_answer.id", "OBS", errors)
            answer_text = _text(observed.get("text"), "observed_answer.text", errors, maximum=2000)
            if observed.get("storage") != "ephemeral":
                errors.append("observed_answer.storage must be ephemeral")

    feedback = _closed(session.get("feedback"), "feedback", frozenset({"score", "score_state", "observations"}), errors)
    if _enum(state, {"ready_to_practice", "awaiting_answer"}) and answer is not None:
        errors.append("pre-answer states cannot include an observed answer")
    if feedback is not None:
        if feedback.get("score") != "unknown":
            errors.append("feedback.score must be unknown before an observed answer")
        score_state = feedback.get("score_state")
        if not _enum(score_state, {"unknown", "categorical"}):
            errors.append("feedback.score_state must be unknown or categorical")
        if _enum(state, {"ready_to_practice", "awaiting_answer"}) and score_state != "unknown":
            errors.append("pre-answer feedback.score_state must be unknown")
        observations = feedback.get("observations")
        if not isinstance(observations, list) or len(observations) > 3:
            errors.append("feedback.observations must contain at most three observations")
            observations = []
        if answer is None and observations:
            errors.append("feedback.observations require an observed answer")
        if state == "feedback_available" and (answer is None or not observations):
            errors.append("feedback_available requires an observed answer and feedback")
        if state == "feedback_available" and score_state != "categorical":
            errors.append("feedback_available feedback.score_state must be categorical")
        allowed_feedback_refs = {item for item in (answer_id, rubric_id) if item is not None}
        feedback_label_order = {"solid": 0, "confirm": 1, "do_not_assert": 2}
        seen_feedback_labels: set[str] = set()
        previous_feedback_rank = -1
        for index, item in enumerate(observations):
            observation = _closed(item, f"feedback.observations[{index}]", frozenset({"label", "statement", "source_refs"}), errors)
            if observation is None:
                continue
            label = observation.get("label")
            if label not in feedback_label_order:
                errors.append(f"feedback.observations[{index}].label has invalid value")
            elif label in seen_feedback_labels:
                errors.append(f"feedback.observations[{index}].label must be unique")
            else:
                rank = feedback_label_order[label]
                if rank < previous_feedback_rank:
                    errors.append(
                        "feedback.observations labels must use canonical order: "
                        "solid, confirm, do_not_assert"
                    )
                seen_feedback_labels.add(label)
                previous_feedback_rank = rank
            statement_path = f"feedback.observations[{index}].statement"
            statement = _text(observation.get("statement"), statement_path, errors, maximum=500)
            _validate_feedback_statement(statement, answer_text, statement_path, errors)
            references = _references(
                observation.get("source_refs"), allowed_feedback_refs,
                f"feedback.observations[{index}].source_refs", errors,
                allowed=allowed_feedback_refs, maximum=2,
            )
            if answer_id is not None and rubric_id is not None and set(references) != allowed_feedback_refs:
                errors.append(
                    f"feedback.observations[{index}].source_refs must cite OBS-001 and RB-001"
                )

    delivery = _closed(session.get("delivery"), "delivery", frozenset({"draft_only", "external_actions_authorized", "local_save_mode", "raw_answer_retained"}), errors)
    if delivery is not None:
        if delivery.get("draft_only") is not True:
            errors.append("delivery.draft_only must be true")
        if delivery.get("external_actions_authorized") is not False:
            errors.append("delivery.external_actions_authorized must be false")
        if delivery.get("local_save_mode") != "disabled":
            errors.append("delivery.local_save_mode must be disabled")
        if delivery.get("raw_answer_retained") is not False:
            errors.append("delivery.raw_answer_retained must be false")

    _validate_prose_safety(session, errors)
    return sorted(set(errors))


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a private recruiter practice session.")
    parser.add_argument("input", type=Path, help="Path to one session JSON file.")
    try:
        arguments = parser.parse_args(argv)
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    try:
        session = load_session(arguments.input)
    except SessionLoadError as error:
        print(str(error), file=sys.stderr)
        return 3
    errors = validate_session(session)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2
    print("valid recruiter practice session")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
