#!/usr/bin/env python3
"""Validate bounded dossier provenance for a private practice session."""

from __future__ import annotations

import importlib.util
import re
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path


SCHEMA_VERSION = "dossier-recruiter-practice-handoff-v1"
_SNAPSHOT = re.compile(r"snap-dossier-[0-9]{3}\Z")


@lru_cache(maxsize=None)
def _load_sibling(name: str):
    path = Path(__file__).with_name(f"{name}.py")
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError("source validator is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _closed(
    value: object,
    path: str,
    fields: frozenset[str],
    errors: list[str],
) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    if set(value) - fields:
        errors.append(f"{path} has unsupported fields")
    if fields - set(value):
        errors.append(f"{path} is missing required fields")
    return value


def _identifiers(value: object, prefix: str) -> bool:
    return (
        isinstance(value, list)
        and 1 <= len(value) <= 10
        and all(isinstance(item, str) and re.fullmatch(rf"{prefix}-[0-9]{{3}}", item) for item in value)
        and len(value) == len(set(value))
    )


def _safe_text(value: object, maximum: int) -> bool:
    return _load_sibling("dossier_practice_safe_text").is_safe_handoff_text(
        value, maximum
    )


def _validate_handoff_schema(value: object) -> list[str]:
    """Check the closed v1 sidecar without exposing its private prose."""
    errors: list[str] = []
    handoff = _closed(
        value,
        "handoff",
        frozenset({"schema_version", "source", "source_snapshot", "dossier_projection", "practice_projection", "delivery"}),
        errors,
    )
    if handoff is None:
        return errors
    if handoff.get("schema_version") != SCHEMA_VERSION:
        errors.append("handoff.schema_version has invalid value")
    if handoff.get("source") != "executive_career_dossier":
        errors.append("handoff.source has invalid value")
    if not isinstance(handoff.get("source_snapshot"), str) or not _SNAPSHOT.fullmatch(handoff["source_snapshot"]):
        errors.append("handoff.source_snapshot must use the snap-dossier-000 identifier format")

    dossier = _closed(
        handoff.get("dossier_projection"),
        "handoff.dossier_projection",
        frozenset({"question_rank", "claim_ids", "evidence_ids", "question_evidence_ids", "source_fact_evidence_id", "fact_state", "fact_summary"}),
        errors,
    )
    if dossier is not None:
        if type(dossier.get("question_rank")) is not int or dossier.get("question_rank") != 1:
            errors.append("handoff.dossier_projection.question_rank must be 1")
        for field in ("claim_ids", "evidence_ids", "question_evidence_ids"):
            if not _identifiers(dossier.get(field), "C" if field == "claim_ids" else "E"):
                errors.append(f"handoff.dossier_projection.{field} must contain bounded identifiers")
        if not isinstance(dossier.get("source_fact_evidence_id"), str) or not re.fullmatch(r"E-[0-9]{3}", dossier["source_fact_evidence_id"]):
            errors.append("handoff.dossier_projection.source_fact_evidence_id must use the E-000 identifier format")
        if dossier.get("fact_state") not in {"verified", "candidate_reported"}:
            errors.append("handoff.dossier_projection.fact_state has invalid value")
        if not _safe_text(dossier.get("fact_summary"), 500):
            errors.append("handoff.dossier_projection.fact_summary must be safe text")

    projection = _closed(
        handoff.get("practice_projection"),
        "handoff.practice_projection",
        frozenset({"safe_context", "requirement", "question", "facts", "handoff_context"}),
        errors,
    )
    if projection is not None:
        context = _closed(projection.get("safe_context"), "handoff.practice_projection.safe_context", frozenset({"stage", "vacancy_state", "summary"}), errors)
        if context is not None and (context.get("stage") != "recruiter_screen" or context.get("vacancy_state") != "safe_summary_provided" or not _safe_text(context.get("summary"), 280)):
            errors.append("handoff.practice_projection.safe_context must be a safe recruiter-screen context")
        requirement = _closed(projection.get("requirement"), "handoff.practice_projection.requirement", frozenset({"id", "summary", "fact_ids"}), errors)
        if requirement is not None:
            if requirement.get("id") != "R-001":
                errors.append("handoff.practice_projection.requirement.id must be R-001")
            if not _safe_text(requirement.get("summary"), 280):
                errors.append("handoff.practice_projection.requirement.summary must be safe text")
            if requirement.get("fact_ids") != ["F-001"]:
                errors.append("handoff.practice_projection.requirement.fact_ids must be F-001")
        question = _closed(projection.get("question"), "handoff.practice_projection.question", frozenset({"id", "kind", "text", "requirement_id", "fact_ids"}), errors)
        if question is not None:
            if question.get("id") != "Q-001":
                errors.append("handoff.practice_projection.question.id must be Q-001")
            if question.get("kind") != "screen_opening":
                errors.append("handoff.practice_projection.question.kind must be screen_opening")
            if not _safe_text(question.get("text"), 500):
                errors.append("handoff.practice_projection.question.text must be safe text")
            if question.get("requirement_id") != "R-001" or question.get("fact_ids") != ["F-001"]:
                errors.append("handoff.practice_projection.question must reference R-001 and F-001")
        facts = projection.get("facts")
        if not isinstance(facts, list) or len(facts) != 1:
            errors.append("handoff.practice_projection.facts must contain one fact")
        elif (fact := _closed(facts[0], "handoff.practice_projection.facts[0]", frozenset({"id", "state", "summary"}), errors)) is not None:
            if fact.get("id") != "F-001":
                errors.append("handoff.practice_projection.facts[0].id must be F-001")
            if fact.get("state") not in {"verified", "candidate_reported"}:
                errors.append("handoff.practice_projection.facts[0].state has invalid value")
            if not _safe_text(fact.get("summary"), 500):
                errors.append("handoff.practice_projection.facts[0].summary must be safe text")
        source = _closed(projection.get("handoff_context"), "handoff.practice_projection.handoff_context", frozenset({"source", "source_snapshot", "question_rank", "question_id", "requirement_id", "fact_ids", "claim_ids", "evidence_ids", "draft_only", "external_actions_authorized"}), errors)
        if source is not None:
            if source.get("source") != "executive_career_dossier" or type(source.get("question_rank")) is not int or source.get("question_rank") != 1:
                errors.append("handoff.practice_projection.handoff_context has invalid provenance")
            if source.get("question_id") != "Q-001" or source.get("requirement_id") != "R-001" or source.get("fact_ids") != ["F-001"]:
                errors.append("handoff.practice_projection.handoff_context must reference Q-001, R-001, and F-001")
            if not isinstance(source.get("source_snapshot"), str) or not _SNAPSHOT.fullmatch(source["source_snapshot"]):
                errors.append("handoff.practice_projection.handoff_context.source_snapshot must use the snap-dossier-000 identifier format")
            for field, prefix in (("claim_ids", "C"), ("evidence_ids", "E")):
                if not _identifiers(source.get(field), prefix):
                    errors.append(f"handoff.practice_projection.handoff_context.{field} must contain bounded identifiers")
            if source.get("draft_only") is not True or source.get("external_actions_authorized") is not False:
                errors.append("handoff.practice_projection.handoff_context must remain draft-only without external actions")

    delivery = _closed(handoff.get("delivery"), "handoff.delivery", frozenset({"draft_only", "external_actions_authorized", "manual_reentry_required", "auto_start", "candidate_answer_state", "score_state", "local_save_mode", "raw_answer_retained"}), errors)
    if delivery is not None:
        expected_delivery = {"draft_only": True, "external_actions_authorized": False, "manual_reentry_required": True, "auto_start": False, "candidate_answer_state": "unanswered", "score_state": "unknown", "local_save_mode": "disabled", "raw_answer_retained": False}
        for field, expected in expected_delivery.items():
            if type(delivery.get(field)) is not type(expected) or delivery.get(field) != expected:
                rendered = str(expected).lower() if isinstance(expected, bool) else expected
                errors.append(f"handoff.delivery.{field} must be {rendered}")
    return errors


def _compare_practice(projection: Mapping[str, object], practice: Mapping[str, object], errors: list[str]) -> None:
    for section, field in (("safe_context", "summary"), ("requirement", "id"), ("requirement", "summary"), ("requirement", "fact_ids"), ("question", "id"), ("question", "kind"), ("question", "text"), ("question", "requirement_id"), ("question", "fact_ids"), ("handoff_context", "source"), ("handoff_context", "source_snapshot"), ("handoff_context", "question_rank"), ("handoff_context", "question_id"), ("handoff_context", "requirement_id"), ("handoff_context", "fact_ids"), ("handoff_context", "claim_ids"), ("handoff_context", "evidence_ids"), ("handoff_context", "draft_only"), ("handoff_context", "external_actions_authorized")):
        expected_section = projection.get(section)
        actual_section = practice.get(section)
        if isinstance(expected_section, Mapping) and (not isinstance(actual_section, Mapping) or actual_section.get(field) != expected_section.get(field)):
            if section == "handoff_context" and field == "source_snapshot":
                errors.append("practice_session.handoff_context.source_snapshot must match handoff.source_snapshot")
            else:
                errors.append(f"practice_session.{section}.{field} must match handoff.practice_projection.{section}.{field}")
    expected_facts = projection.get("facts")
    actual_facts = practice.get("facts")
    if isinstance(expected_facts, list) and expected_facts and isinstance(expected_facts[0], Mapping):
        for field in ("id", "state", "summary"):
            if not isinstance(actual_facts, list) or not actual_facts or not isinstance(actual_facts[0], Mapping) or actual_facts[0].get(field) != expected_facts[0].get(field):
                errors.append(f"practice_session.facts[0].{field} must match handoff.practice_projection.facts[0].{field}")


def _projection_value(value: object, path: tuple[str | int, ...]) -> object:
    current = value
    for part in path:
        if isinstance(part, str) and isinstance(current, Mapping):
            current = current.get(part)
        elif isinstance(part, int) and isinstance(current, list) and 0 <= part < len(current):
            current = current[part]
        else:
            return None
    return current


def _compare_expected_projection(
    actual: Mapping[str, object],
    expected: Mapping[str, object],
    errors: list[str],
) -> None:
    paths = (
        ("safe_context", "stage"),
        ("safe_context", "vacancy_state"),
        ("safe_context", "summary"),
        ("requirement", "id"),
        ("requirement", "summary"),
        ("requirement", "fact_ids"),
        ("question", "id"),
        ("question", "kind"),
        ("question", "text"),
        ("question", "requirement_id"),
        ("question", "fact_ids"),
        ("facts", 0, "id"),
        ("facts", 0, "state"),
        ("facts", 0, "summary"),
        ("handoff_context", "source"),
        ("handoff_context", "source_snapshot"),
        ("handoff_context", "question_rank"),
        ("handoff_context", "question_id"),
        ("handoff_context", "requirement_id"),
        ("handoff_context", "fact_ids"),
        ("handoff_context", "claim_ids"),
        ("handoff_context", "evidence_ids"),
        ("handoff_context", "draft_only"),
        ("handoff_context", "external_actions_authorized"),
    )
    for path in paths:
        if _projection_value(actual, path) != _projection_value(expected, path):
            rendered = ".".join(str(part) for part in path).replace(".0.", "[0].")
            errors.append(
                f"handoff.practice_projection.{rendered} must match expected practice projection"
            )


def _validate_bridge_claim_evidence_links(
    dossier: Mapping[str, object],
    handoff: Mapping[str, object],
    errors: list[str],
) -> None:
    bridge = dossier.get("screen_bridge")
    claims = dossier.get("claims")
    questions = dossier.get("questions")
    if (
        not isinstance(bridge, Mapping)
        or not isinstance(claims, list)
        or not isinstance(questions, list)
    ):
        return
    claim_ids = bridge.get("claim_ids")
    evidence_ids = bridge.get("evidence_ids")
    if not isinstance(claim_ids, list) or not isinstance(evidence_ids, list):
        return
    claim_records = {
        claim.get("id"): claim
        for claim in claims
        if isinstance(claim, Mapping) and isinstance(claim.get("id"), str)
    }
    linked_evidence = {
        evidence_id
        for claim_id in claim_ids
        for evidence_id in (
            claim_records.get(claim_id, {}).get("evidence_ids", [])
            if isinstance(claim_records.get(claim_id), Mapping)
            else []
        )
        if isinstance(evidence_id, str)
    }
    if any(evidence_id not in linked_evidence for evidence_id in evidence_ids):
        errors.append("dossier.screen_bridge.evidence_ids must link to dossier.screen_bridge.claim_ids")
    bridge_evidence = {item for item in evidence_ids if isinstance(item, str)}
    if any(
        not bridge_evidence.intersection(
            item
            for item in claim_records.get(claim_id, {}).get("evidence_ids", [])
            if isinstance(item, str)
        )
        for claim_id in claim_ids
        if isinstance(claim_id, str)
    ):
        errors.append(
            "dossier.screen_bridge.claim_ids must each link to dossier.screen_bridge.evidence_ids"
        )

    selected = next(
        (
            row
            for row in questions
            if isinstance(row, Mapping) and row.get("rank") == 1
        ),
        None,
    )
    question_evidence = (
        {
            item
            for item in selected.get("evidence_ids", [])
            if isinstance(item, str)
        }
        if isinstance(selected, Mapping)
        else set()
    )
    if not question_evidence <= bridge_evidence:
        errors.append(
            "dossier.questions.rank_1.evidence_ids must belong to dossier.screen_bridge.evidence_ids"
        )

    projection = handoff.get("dossier_projection")
    if isinstance(projection, Mapping):
        source_fact = projection.get("source_fact_evidence_id")
        if source_fact not in question_evidence or source_fact not in bridge_evidence:
            errors.append(
                "handoff.dossier_projection.source_fact_evidence_id must belong to candidate bridge evidence"
            )


def validate_handoff(
    handoff: Mapping[str, object],
    dossier: Mapping[str, object],
    vacancy: Mapping[str, object],
    practice_session: Mapping[str, object],
) -> list[str]:
    """Return sorted, bounded errors for the two-source handoff contract."""
    errors = _validate_handoff_schema(handoff)
    dossier_validator = _load_sibling("validate_executive_career_dossier")
    practice_validator = _load_sibling("validate_recruiter_practice_session")
    dossier_is_mapping = isinstance(dossier, Mapping)
    practice_is_mapping = isinstance(practice_session, Mapping)
    dossier_errors = dossier_validator.validate_dossier(dossier) if dossier_is_mapping else []
    practice_errors = practice_validator.validate_session(practice_session) if practice_is_mapping else []
    if not dossier_is_mapping:
        errors.append("dossier must be an object")
    elif dossier_errors:
        errors.append("dossier validation failed")
    if not practice_is_mapping:
        errors.append("practice_session must be an object")
    elif practice_errors:
        errors.append("practice_session validation failed")
    if not isinstance(vacancy, Mapping):
        errors.append("vacancy must be an object")
        return sorted(set(errors))
    if not isinstance(handoff, Mapping) or not dossier_is_mapping or not practice_is_mapping:
        return sorted(set(errors))
    source_snapshot = handoff.get("source_snapshot")
    if not isinstance(source_snapshot, str) or not _SNAPSHOT.fullmatch(source_snapshot):
        return sorted(set(errors))
    dossier_locale = dossier.get("locale")
    locale_mismatch = False
    if vacancy.get("locale") != dossier_locale:
        errors.append("vacancy.locale must match dossier.locale")
        locale_mismatch = True
    if practice_session.get("locale") != dossier_locale:
        errors.append("practice_session.locale must match dossier.locale")
        locale_mismatch = True
    if locale_mismatch:
        return sorted(set(errors))
    if dossier_errors:
        return sorted(set(errors))
    _validate_bridge_claim_evidence_links(dossier, handoff, errors)

    builder = _load_sibling("build_dossier_recruiter_practice_handoff")
    try:
        expected = builder.build_handoff(dossier, vacancy, source_snapshot)
    except ValueError:
        errors.append("vacancy source is invalid")
        return sorted(set(errors))

    expected_dossier = expected["dossier_projection"]
    actual_dossier = handoff.get("dossier_projection")
    if isinstance(actual_dossier, Mapping):
        for field in ("question_rank", "claim_ids", "evidence_ids", "question_evidence_ids", "source_fact_evidence_id", "fact_state", "fact_summary"):
            if actual_dossier.get(field) != expected_dossier[field]:
                errors.append(f"handoff.dossier_projection.{field} must match dossier source projection")
    expected_projection = expected["practice_projection"]
    actual_projection = handoff.get("practice_projection")
    if isinstance(actual_projection, Mapping):
        _compare_expected_projection(actual_projection, expected_projection, errors)
        actual_context = actual_projection.get("handoff_context")
        expected_context = expected_projection["handoff_context"]
        if isinstance(actual_context, Mapping):
            if actual_context.get("claim_ids") != expected_context["claim_ids"]:
                errors.append("handoff.practice_projection.handoff_context.claim_ids must match dossier.screen_bridge.claim_ids")
            if actual_context.get("evidence_ids") != expected_context["evidence_ids"]:
                errors.append("handoff.practice_projection.handoff_context.evidence_ids must match dossier.screen_bridge.evidence_ids")
        _compare_practice(actual_projection, practice_session, errors)
    if practice_session.get("observed_answer") is not None:
        errors.append("practice_session.observed_answer must be absent")
    feedback = practice_session.get("feedback")
    if isinstance(feedback, Mapping) and feedback.get("score") != "unknown":
        errors.append("practice_session.feedback.score must be unknown")
    return sorted(set(errors))
