#!/usr/bin/env python3
"""Fail-closed validation for an identity-free private reply triage."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from private_prose_safety import is_safe_prose_text


SCHEMA_VERSION = "private-recruiter-reply-triage-v1"
V2_SCHEMA_VERSION = "private-recruiter-reply-triage-v2"
TOP_LEVEL_FIELDS = frozenset({
    "schema_version", "artifact_kind", "locale", "state", "classification",
    "safe_context", "facts", "question", "blocked_claims", "handoff_allowed",
    "delivery", "handoff", "next_safe_action",
})
V2_TOP_LEVEL_FIELDS = frozenset({
    "schema_version", "artifact_kind", "ui_locale", "content_locale", "state", "classification",
    "safe_context", "facts", "question", "blocked_claims", "handoff_allowed",
    "delivery", "handoff", "next_safe_action",
})
CLASSIFICATIONS = frozenset({
    "screen_invite", "request_for_proof", "eligibility_question",
    "compensation_question", "decline", "unknown",
})
QUESTION_KINDS = frozenset({
    "screen_opening", "proof_example", "eligibility_boundary",
    "compensation_boundary", "missing_detail",
})
CLASSIFICATION_QUESTION_KINDS = {
    "screen_invite": "screen_opening",
    "request_for_proof": "proof_example",
    "eligibility_question": "eligibility_boundary",
    "compensation_question": "compensation_boundary",
    "unknown": "missing_detail",
}
STATE_NEXT_SAFE_ACTIONS = {
    "clarify_first": "clarify_context_before_private_prep",
    "ready_for_private_prep": "manual_reenter_private_prep",
    "stop": "record_stop_decision",
}
def _enum(value: object, allowed: set[str] | frozenset[str]) -> bool:
    return isinstance(value, str) and value in allowed
FORBIDDEN_PROSE = {
    "raw": re.compile(r"\b(?:raw|verbatim|quoted|original|inbound)\s+(?:(?:recruiter\s+)?(?:reply|message|text)|content)\b|\b(?:texto|contenido|respuesta)\s+(?:crudo|original|citado)\b", re.IGNORECASE),
    "identity": re.compile(r"\b(?:recruiter|reclutador(?:a)?|contact|contacto)\s*(?::\s*|(?:is|es|named|llamad[oa])\s+)\S+|\b(?:my\s+name\s+is|me\s+llamo|nombre\s+(?:del\s+)?(?:reclutador|contacto))\b", re.IGNORECASE),
    "company": re.compile(r"\b(?:company|empresa|employer|empleador|organization|organizaci[oó]n)\s*(?::\s*|(?:is|es|named|llamad[oa])\s+)\S+", re.IGNORECASE),
    "unlabelled_identity": re.compile(
        r"\b[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñü'’-]{1,40}\s+"
        r"[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñü'’-]{1,40}\s+"
        r"(?:described|contacted|joined|emailed|describió|contactó|"
        r"se\s+uni[oó]|escribió)\b"
    ),
    "unlabelled_company": re.compile(
        r"\b(?:works?|worked|from|at|with|en|para)\s+"
        r"(?:[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñü'’-]{1,40}\s+){1,3}"
        r"[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñü'’-]{1,40}\b"
    ),
    "contact": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|\+?\d[\d .()-]{7,}\d|\b(?:https?://|www\.|linkedin\.com/)\S*", re.IGNORECASE),
    "action": re.compile(r"\b(?:send|message|contact|reach\s+out|apply|submit|schedule|book|confirm|accept|call|email|enviar|escribir|contactar|agendar|programar|reservar|confirmar|aceptar|llamar)\b[^.!?\n]{0,80}\b(?:extern(?:al|ally)|recruiter|reclutador(?:a)?|message|mensaje|reply|response|respuesta|interview|entrevista|calendar|calendario|meeting|reuni[oó]n)\b", re.IGNORECASE),
    "time": re.compile(r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\b|\b\d{1,2}:\d{2}\b|\b\d{1,2}\s*(?:a\.?m\.?|p\.?m\.?)\b|\b(?:calendar|calendario|meeting\s+time|hora\s+de\s+(?:la\s+)?reuni[oó]n)\b", re.IGNORECASE),
    "guarantee": re.compile(r"\b(?:guarantee[sd]?|assured|promise[sd]?|will\s+(?:(?:get|receive|land)\s+(?:an?\s+)?|result\s+in\s+(?:an?\s+)?)?(?:interviews?|offers?|jobs?)|(?:esto\s+)?resultar[aá]\s+en\s+(?:un(?:a|as|os)?\s+)?(?:entrevistas?|ofertas?|empleos?|trabajos?)|(?:te\s+)?(?:garantizo|garantizamos|aseguro|aseguramos))\b", re.IGNORECASE),
    "analytics": re.compile(r"\b(?:private\s+(?:analytics|dashboard|metrics|data|engagement|views?)|analytics\s+show|profile\s+(?:views|traffic)|anal[ií]ticas?\s+privadas?|visitas?\s+(?:al\s+)?perfil)\b", re.IGNORECASE),
    "internal_id": re.compile(r"\b(?:F|Q)-\d{3}\b", re.IGNORECASE),
}


class TriageLoadError(ValueError):
    """Raised for deterministic, privacy-safe JSON input failures."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise TriageLoadError("duplicate JSON key")
        result[key] = value
    return result


def _assert_max_depth(value: object, maximum: int = 12, depth: int = 0) -> None:
    if depth > maximum:
        raise TriageLoadError("JSON nesting exceeds safe limit")
    if isinstance(value, Mapping):
        for child in value.values():
            _assert_max_depth(child, maximum, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _assert_max_depth(child, maximum, depth + 1)


def load_triage(path: Path) -> dict[str, object]:
    if path.is_symlink():
        raise TriageLoadError("triage input must not be a symlink")
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise TriageLoadError("triage input is unavailable") from error
    if len(raw.encode("utf-8")) > 64_000:
        raise TriageLoadError("triage input exceeds safe size limit")
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, TriageLoadError) as error:
        raise TriageLoadError("triage input is not valid JSON") from error
    _assert_max_depth(value)
    if not isinstance(value, dict):
        raise TriageLoadError("triage input must be a JSON object")
    return value


def _closed(value: object, path: str, fields: frozenset[str], errors: list[str]) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path or 'session'} must be an object")
        return None
    missing = sorted(fields - set(value))
    unsupported = sorted(set(value) - fields)
    for field in missing:
        errors.append(f"missing required field: {path}.{field}" if path else f"missing required field: {field}")
    if unsupported:
        errors.append(f"{path or 'session'} has unsupported fields: {', '.join(unsupported)}")
    return value


def _text(value: object, path: str, errors: list[str], *, maximum: int) -> str | None:
    if not is_safe_prose_text(value) or not value.strip() or len(value) > maximum:
        errors.append(f"{path} must be non-empty prose within {maximum} characters")
        return None
    return value


def _identifier(value: object, path: str, prefix: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not re.fullmatch(rf"{re.escape(prefix)}-[0-9]{{3}}", value):
        errors.append(f"{path} must use the {prefix}-000 identifier format")
        return None
    return value


def _references(value: object, known: set[str], path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or len(value) != 1 or not all(isinstance(item, str) for item in value):
        errors.append(f"{path} must contain exactly one reference")
        return
    reference = value[0]
    if reference not in known:
        errors.append(f"{path} references unknown identifier: {reference}")


def _walk_strings(value: object, *, field: str | None = None) -> Sequence[str]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        return tuple(
            text
            for key, child in value.items()
            if key not in {"id", "fact_ids", "fact_id", "question_id"}
            for text in _walk_strings(child, field=key)
        )
    if isinstance(value, list):
        return tuple(text for child in value for text in _walk_strings(child, field=field))
    return ()


def _validate_prose_safety(value: Mapping[str, object], errors: list[str]) -> None:
    text = "\n".join(_walk_strings(value))
    for category, pattern in FORBIDDEN_PROSE.items():
        if pattern.search(text):
            errors.append(f"session contains forbidden {category} prose")


def validate_triage(value: object) -> list[str]:
    """Return deterministic errors; an empty list means the triage is safe."""

    errors: list[str] = []
    schema_version = value.get("schema_version") if isinstance(value, Mapping) else None
    fields = V2_TOP_LEVEL_FIELDS if schema_version == V2_SCHEMA_VERSION else TOP_LEVEL_FIELDS
    triage = _closed(value, "", fields, errors)
    if "missing required field: handoff" in errors:
        errors.remove("missing required field: handoff")
    if triage is None:
        return sorted(set(errors))
    if not _enum(triage.get("schema_version"), {SCHEMA_VERSION, V2_SCHEMA_VERSION}):
        errors.append("schema_version has invalid value")
    if triage.get("artifact_kind") != "private_recruiter_reply_triage":
        errors.append("artifact_kind has invalid value")
    if schema_version == V2_SCHEMA_VERSION:
        if not _enum(triage.get("ui_locale"), {"es", "en"}):
            errors.append("ui_locale has invalid value")
        if not _enum(triage.get("content_locale"), {"es", "en"}):
            errors.append("content_locale has invalid value")
    elif not _enum(triage.get("locale"), {"es", "en"}):
        errors.append("locale has invalid value")
    state = triage.get("state")
    if not _enum(state, {"clarify_first", "ready_for_private_prep", "stop"}):
        errors.append("state has invalid value")
    if not _enum(triage.get("classification"), CLASSIFICATIONS):
        errors.append("classification has invalid value")
    if state == "ready_for_private_prep" and triage.get("classification") == "decline":
        errors.append("ready_for_private_prep cannot use decline classification")

    context = _closed(triage.get("safe_context"), "safe_context", frozenset({"stage", "role_context", "critical_constraints", "summary"}), errors)
    context_is_ready = False
    if context is not None:
        if not _enum(context.get("stage"), {"recruiter_screen", "unknown", "not_applicable"}):
            errors.append("safe_context.stage has invalid value")
        if not _enum(context.get("role_context"), {"confirmed", "missing", "not_applicable"}):
            errors.append("safe_context.role_context has invalid value")
        if not _enum(context.get("critical_constraints"), {"confirmed", "missing", "not_applicable"}):
            errors.append("safe_context.critical_constraints has invalid value")
        _text(context.get("summary"), "safe_context.summary", errors, maximum=280)
        context_is_ready = (
            context.get("stage") == "recruiter_screen"
            and context.get("role_context") == "confirmed"
            and context.get("critical_constraints") == "confirmed"
        )

    known_fact_ids: set[str] = set()
    supplied_fact_state: str | None = None
    facts = triage.get("facts")
    if not isinstance(facts, list) or len(facts) != 1:
        errors.append("facts must contain exactly one supplied fact")
    else:
        fact = _closed(facts[0], "facts[0]", frozenset({"id", "state", "summary"}), errors)
        if fact is not None:
            fact_id = _identifier(fact.get("id"), "facts[0].id", "F", errors)
            if fact_id is not None:
                known_fact_ids.add(fact_id)
            if not _enum(fact.get("state"), {"verified", "candidate_reported"}):
                errors.append("facts[0].state has invalid value")
            else:
                supplied_fact_state = fact["state"]
            _text(fact.get("summary"), "facts[0].summary", errors, maximum=500)

    question_fields = {"id", "text", "fact_ids"}
    if state == "ready_for_private_prep":
        question_fields.add("kind")
    question = _closed(triage.get("question"), "question", frozenset(question_fields), errors)
    question_id: str | None = None
    question_kind: str | None = None
    if question is not None:
        question_id = _identifier(question.get("id"), "question.id", "Q", errors)
        question_text = _text(question.get("text"), "question.text", errors, maximum=500)
        if question_text is not None and question_text.count("?") != 1:
            errors.append("question.text must contain exactly one question")
        _references(question.get("fact_ids"), known_fact_ids, "question.fact_ids", errors)
        if state == "ready_for_private_prep":
            kind = question.get("kind")
            question_kind = kind if isinstance(kind, str) else None
            if not _enum(kind, QUESTION_KINDS):
                errors.append("question.kind has invalid value")
            elif isinstance(triage.get("classification"), str) and CLASSIFICATION_QUESTION_KINDS.get(triage.get("classification")) != kind:
                errors.append("question.kind must match classification")

    blocked_claims = triage.get("blocked_claims")
    if (
        not isinstance(blocked_claims, list)
        or not 1 <= len(blocked_claims) <= 4
        or not all(isinstance(item, str) for item in blocked_claims)
        or len(blocked_claims) != len(set(blocked_claims))
    ):
        errors.append("blocked_claims must contain one through four unique claims")
    else:
        for index, item in enumerate(blocked_claims):
            _text(item, f"blocked_claims[{index}]", errors, maximum=280)

    handoff_allowed = triage.get("handoff_allowed")
    if not isinstance(handoff_allowed, bool):
        errors.append("handoff_allowed must be boolean")
    elif state == "ready_for_private_prep":
        if not context_is_ready:
            errors.append("ready_for_private_prep requires confirmed stage, role, and critical constraints")
        if supplied_fact_state != "verified":
            errors.append("ready_for_private_prep requires a verified supplied fact for handoff")
        if handoff_allowed is not True:
            errors.append("ready_for_private_prep requires handoff_allowed=true")
    elif handoff_allowed is not False:
        errors.append("handoff_allowed is permitted only for ready_for_private_prep")

    next_safe_action = triage.get("next_safe_action")
    if not _enum(next_safe_action, set(STATE_NEXT_SAFE_ACTIONS.values())):
        errors.append("next_safe_action has invalid value")
    elif _enum(state, set(STATE_NEXT_SAFE_ACTIONS)) and next_safe_action != STATE_NEXT_SAFE_ACTIONS[state]:
        errors.append("next_safe_action must match state")

    handoff = triage.get("handoff")
    if state == "ready_for_private_prep":
        if handoff is None:
            errors.append("ready_for_private_prep requires handoff")
        else:
            handoff_map = _closed(handoff, "handoff", frozenset({"module", "scope", "input_mode", "auto_start", "external_actions", "raw_reply_retained", "local_save_mode", "packet", "reentry_packet"}), errors)
            if handoff_map is not None:
                expected = {
                    "module": "prepare-role-interviews",
                    "scope": "one recruiter-screen question",
                    "input_mode": "identity_free_summary_plus_verified_fact",
                    "auto_start": False,
                    "external_actions": False,
                    "raw_reply_retained": False,
                    "local_save_mode": "disabled",
                }
                for field, value in expected.items():
                    if type(handoff_map.get(field)) is not type(value) or handoff_map.get(field) != value:
                        errors.append(f"handoff.{field} has invalid value" if field in {"module", "scope", "input_mode"} else f"handoff.{field} has immutable value")
                packet = _closed(handoff_map.get("packet"), "handoff.packet", frozenset({"context_summary", "source_snapshot", "fact_id", "question_id", "prep_scope"}), errors)
                reentry = _closed(
                    handoff_map.get("reentry_packet"),
                    "handoff.reentry_packet",
                    frozenset({"schema_version", "source_artifact_kind", "context_summary", "source_snapshot", "fact_id", "question_id", "prep_scope", "manual_reentry_required", "candidate_answer_state", "score_state"}),
                    errors,
                )
                if packet is not None:
                    packet_context = _text(packet.get("context_summary"), "handoff.packet.context_summary", errors, maximum=280)
                    if not isinstance(packet.get("source_snapshot"), str) or not re.fullmatch(r"snap-triage-[0-9]{3}", packet.get("source_snapshot", "")):
                        errors.append("handoff.packet.source_snapshot must use the snap-triage-000 identifier format")
                    if context is not None and packet_context is not None and packet_context != context.get("summary"):
                        errors.append("handoff.packet.context_summary must match safe_context.summary")
                    packet_fact = _identifier(packet.get("fact_id"), "handoff.packet.fact_id", "F", errors)
                    packet_question = _identifier(packet.get("question_id"), "handoff.packet.question_id", "Q", errors)
                    if packet_fact is not None and packet_fact not in known_fact_ids:
                        errors.append("handoff.packet.fact_id must match the sole supplied fact")
                    if packet_question is not None and packet_question != question_id:
                        errors.append("handoff.packet.question_id must match the sole question")
                    scope = packet.get("prep_scope")
                    if not _enum(scope, QUESTION_KINDS):
                        errors.append("handoff.packet.prep_scope has invalid value")
                    elif question_kind != scope:
                        errors.append("handoff.packet.prep_scope must match question.kind")
                if reentry is not None:
                    immutable_reentry = {
                        "schema_version": "private-recruiter-screen-reentry-v1",
                        "source_artifact_kind": "private_recruiter_reply_triage",
                        "manual_reentry_required": True,
                        "candidate_answer_state": "unanswered",
                        "score_state": "unknown",
                    }
                    for field, expected in immutable_reentry.items():
                        if type(reentry.get(field)) is not type(expected) or reentry.get(field) != expected:
                            errors.append(f"handoff.reentry_packet.{field} has immutable value")
                    reentry_context = _text(reentry.get("context_summary"), "handoff.reentry_packet.context_summary", errors, maximum=280)
                    if not isinstance(reentry.get("source_snapshot"), str) or not re.fullmatch(r"snap-triage-[0-9]{3}", reentry.get("source_snapshot", "")):
                        errors.append("handoff.reentry_packet.source_snapshot must use the snap-triage-000 identifier format")
                    if context is not None and reentry_context is not None and reentry_context != context.get("summary"):
                        errors.append("handoff.reentry_packet.context_summary must match safe_context.summary")
                    reentry_fact = _identifier(reentry.get("fact_id"), "handoff.reentry_packet.fact_id", "F", errors)
                    reentry_question = _identifier(reentry.get("question_id"), "handoff.reentry_packet.question_id", "Q", errors)
                    if reentry_fact is not None and reentry_fact not in known_fact_ids:
                        errors.append("handoff.reentry_packet.fact_id must match the sole supplied fact")
                    if reentry_question is not None and reentry_question != question_id:
                        errors.append("handoff.reentry_packet.question_id must match the sole question")
                    reentry_scope = reentry.get("prep_scope")
                    if not _enum(reentry_scope, QUESTION_KINDS):
                        errors.append("handoff.reentry_packet.prep_scope has invalid value")
                    elif question_kind != reentry_scope:
                        errors.append("handoff.reentry_packet.prep_scope must match question.kind")
                    if packet is not None:
                        for field in ("context_summary", "source_snapshot", "fact_id", "question_id", "prep_scope"):
                            if reentry.get(field) != packet.get(field):
                                errors.append(f"handoff.reentry_packet.{field} must match handoff.packet.{field}")
    elif handoff is not None:
        errors.append("handoff is permitted only for ready_for_private_prep")

    if (
        supplied_fact_state == "candidate_reported"
        and state != "clarify_first"
        and handoff_allowed is not False
    ):
        errors.append("candidate_reported supplied fact requires clarify_first or handoff_allowed=false")

    delivery = _closed(triage.get("delivery"), "delivery", frozenset({"draft_only", "external_actions_authorized", "no_calendar_action", "raw_reply_retained", "local_save_mode"}), errors)
    if delivery is not None:
        immutable_values = {
            "draft_only": True,
            "external_actions_authorized": False,
            "no_calendar_action": True,
            "raw_reply_retained": False,
            "local_save_mode": "disabled",
        }
        for field, expected in immutable_values.items():
            if type(delivery.get(field)) is not type(expected) or delivery.get(field) != expected:
                errors.append(f"delivery.{field} has immutable value")

    _validate_prose_safety(triage, errors)
    return sorted(set(errors))


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a private recruiter reply triage.")
    parser.add_argument("input", type=Path, help="Path to one triage JSON file.")
    try:
        arguments = parser.parse_args(argv)
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    try:
        triage = load_triage(arguments.input)
    except TriageLoadError as error:
        print(str(error), file=sys.stderr)
        return 3
    errors = validate_triage(triage)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2
    print("valid private recruiter reply triage")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
