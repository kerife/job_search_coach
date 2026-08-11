#!/usr/bin/env python3
"""Build a closed, identity-free dossier-to-practice source projection."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path


SCHEMA_VERSION = "dossier-recruiter-practice-handoff-v1"
_VACANCY_FIELDS = frozenset({"locale", "safe_context", "requirement"})
_SAFE_CONTEXT_FIELDS = frozenset({"stage", "vacancy_state", "summary"})
_REQUIREMENT_FIELDS = frozenset({"summary"})


@lru_cache(maxsize=None)
def _load_sibling(name: str):
    path = Path(__file__).with_name(f"{name}.py")
    specification = importlib.util.spec_from_file_location(
        f"job_search_coach_dossier_handoff_{name}", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("handoff dependency is unavailable")
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


def _load_dossier_validator():
    return _load_sibling("validate_executive_career_dossier")


def snapshot_for_dossier(dossier: Mapping[str, object]) -> str:
    return _load_sibling("dossier_snapshot").snapshot_for_dossier(dossier)


def is_safe_handoff_text(value: object, maximum: int) -> bool:
    return _load_sibling("dossier_practice_safe_text").is_safe_handoff_text(
        value, maximum
    )


def validate_schema_instance(value: object, schema: Mapping[str, object]) -> list[str]:
    return _load_sibling("validate_json_schema_subset").validate_schema_instance(
        value, schema
    )


def _closed_mapping(value: object, fields: frozenset[str], label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    unsupported = sorted(set(value) - fields)
    missing = sorted(fields - set(value))
    if unsupported:
        raise ValueError(f"{label} has unsupported fields")
    if missing:
        raise ValueError(f"{label} is missing required fields")
    return value


def _safe_text(value: object, label: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{label} must be non-empty text within {maximum} characters")
    if not is_safe_handoff_text(value, maximum):
        raise ValueError(f"{label} contains forbidden safe text")
    return value


def _validate_vacancy(
    vacancy: Mapping[str, object],
) -> tuple[dict[str, object], str, str]:
    value = _closed_mapping(vacancy, _VACANCY_FIELDS, "vacancy")
    locale = value.get("locale")
    if locale not in {"es", "en"}:
        raise ValueError("vacancy.locale must be es or en")
    context = _closed_mapping(value.get("safe_context"), _SAFE_CONTEXT_FIELDS, "vacancy.safe_context")
    if context.get("stage") != "recruiter_screen":
        raise ValueError("vacancy.safe_context.stage must be recruiter_screen")
    if context.get("vacancy_state") != "safe_summary_provided":
        raise ValueError("vacancy.safe_context.vacancy_state must be safe_summary_provided")
    summary = _safe_text(context.get("summary"), "vacancy.safe_context.summary", 280)
    requirement = _closed_mapping(value.get("requirement"), _REQUIREMENT_FIELDS, "vacancy.requirement")
    requirement_summary = _safe_text(requirement.get("summary"), "vacancy.requirement.summary", 280)
    return {
        "stage": "recruiter_screen",
        "vacancy_state": "safe_summary_provided",
        "summary": summary,
    }, requirement_summary, locale


def _records(value: object, prefix: str, label: str) -> dict[str, Mapping[str, object]]:
    if not isinstance(value, list):
        raise ValueError(f"dossier {label} must be a list")
    result: dict[str, Mapping[str, object]] = {}
    for row in value:
        if not isinstance(row, Mapping) or not isinstance(row.get("id"), str):
            raise ValueError(f"dossier {label} has invalid record")
        identifier = row["id"]
        if not re.fullmatch(rf"{prefix}-[0-9]{{3}}", identifier) or identifier in result:
            raise ValueError(f"dossier {label} has invalid identifiers")
        result[identifier] = row
    return result


def _references(value: object, records: Mapping[str, object], label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not 1 <= len(value) <= 10
        or not all(isinstance(identifier, str) for identifier in value)
    ):
        raise ValueError(f"{label} must contain 1 through 10 unique references")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} must contain 1 through 10 unique references")
    if not all(isinstance(identifier, str) and identifier in records for identifier in value):
        raise ValueError(f"{label} references unknown source record")
    return list(value)


def build_handoff(
    dossier: Mapping[str, object], vacancy: Mapping[str, object], source_snapshot: str
) -> dict[str, object]:
    """Return a deterministic, closed projection for one rank-1 bridge."""
    if not isinstance(dossier, Mapping):
        raise ValueError("dossier must be an object")
    if not _load_sibling("dossier_snapshot").is_snapshot(source_snapshot):
        raise ValueError("source_snapshot must use snap-dossier-sha256 format")
    validator = _load_dossier_validator()
    if validator.validate_dossier(dossier):
        raise ValueError("dossier validation failed")
    safe_context, requirement_summary, vacancy_locale = _validate_vacancy(vacancy)
    if dossier.get("locale") != vacancy_locale:
        raise ValueError("dossier.locale must match vacancy.locale")

    bridge = dossier.get("screen_bridge")
    if not isinstance(bridge, Mapping) or bridge.get("state") != "requires_confirmation":
        raise ValueError("dossier screen_bridge must require confirmation")
    if bridge.get("question_rank") != 1:
        raise ValueError("dossier screen_bridge must select rank 1")

    questions = dossier.get("questions")
    if not isinstance(questions, list):
        raise ValueError("dossier questions must be a list")
    selected = next((row for row in questions if isinstance(row, Mapping) and row.get("rank") == 1), None)
    if not isinstance(selected, Mapping) or selected.get("linked_copy_category") != "screen_bridge":
        raise ValueError("dossier rank 1 question must link screen_bridge")
    question_text = selected.get("question")
    if not isinstance(question_text, str) or not question_text.strip() or len(question_text) > 500:
        raise ValueError("dossier rank 1 question must contain safe text")
    if not is_safe_handoff_text(question_text, 500):
        raise ValueError("dossier rank 1 question contains forbidden safe text")

    claims = _records(dossier.get("claims"), "C", "claims")
    evidence = _records(dossier.get("evidence"), "E", "evidence")
    claim_ids = _references(bridge.get("claim_ids"), claims, "screen_bridge.claim_ids")
    evidence_ids = _references(bridge.get("evidence_ids"), evidence, "screen_bridge.evidence_ids")
    bridge_evidence = set(evidence_ids)
    linked_evidence = {
        identifier
        for claim_id in claim_ids
        for identifier in claims[claim_id].get("evidence_ids", [])
        if isinstance(identifier, str)
    }
    if not bridge_evidence <= linked_evidence:
        raise ValueError("dossier screen_bridge evidence must link to selected claims")
    if any(
        not bridge_evidence.intersection(
            identifier
            for identifier in claims[claim_id].get("evidence_ids", [])
            if isinstance(identifier, str)
        )
        for claim_id in claim_ids
    ):
        raise ValueError("dossier screen_bridge must back every selected claim with bridge evidence")
    question_evidence_ids = _references(selected.get("evidence_ids"), evidence, "questions.rank_1.evidence_ids")
    if not set(question_evidence_ids) <= bridge_evidence:
        raise ValueError("dossier rank 1 question evidence must come from screen_bridge evidence")
    if any(evidence[identifier].get("state") not in {"verified", "candidate_reported"} for identifier in question_evidence_ids):
        raise ValueError("source question evidence must be verified or candidate_reported")
    source_fact_evidence_id = question_evidence_ids[0]
    source_fact = evidence[source_fact_evidence_id]
    fact_state = source_fact.get("state")
    if fact_state not in {"verified", "candidate_reported"}:
        raise ValueError("source fact evidence must be verified or candidate_reported")
    fact_summary = source_fact.get("paraphrase")
    if not isinstance(fact_summary, str) or not fact_summary.strip() or len(fact_summary) > 500:
        raise ValueError("source fact evidence must contain safe summary")
    if not is_safe_handoff_text(fact_summary, 500):
        raise ValueError("source fact evidence contains forbidden safe text")
    if source_snapshot != snapshot_for_dossier(dossier):
        raise ValueError("source_snapshot must match dossier content")

    fact_ids = ["F-001"]
    practice_projection = {
        "safe_context": safe_context,
        "requirement": {"id": "R-001", "summary": requirement_summary, "fact_ids": fact_ids},
        "question": {
            "id": "Q-001", "kind": "screen_opening", "text": question_text,
            "requirement_id": "R-001", "fact_ids": fact_ids,
        },
        "facts": [{"id": "F-001", "state": fact_state, "summary": fact_summary}],
        "handoff_context": {
            "source": "executive_career_dossier", "source_snapshot": source_snapshot,
            "question_rank": 1, "question_id": "Q-001", "requirement_id": "R-001",
            "fact_ids": fact_ids, "claim_ids": claim_ids, "evidence_ids": evidence_ids,
            "draft_only": True, "external_actions_authorized": False,
        },
    }
    handoff = {
        "schema_version": SCHEMA_VERSION,
        "source": "executive_career_dossier",
        "source_snapshot": source_snapshot,
        "dossier_projection": {
            "question_rank": 1, "claim_ids": claim_ids, "evidence_ids": evidence_ids,
            "question_evidence_ids": question_evidence_ids,
            "source_fact_evidence_id": source_fact_evidence_id,
            "fact_state": fact_state, "fact_summary": fact_summary,
        },
        "practice_projection": practice_projection,
        "delivery": {
            "draft_only": True, "external_actions_authorized": False,
            "manual_reentry_required": True, "auto_start": False,
            "candidate_answer_state": "unanswered", "score_state": "unknown",
            "local_save_mode": "disabled", "raw_answer_retained": False,
        },
    }
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / f"{SCHEMA_VERSION}.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("builder output schema is unavailable") from exc
    if validate_schema_instance(handoff, schema):
        raise ValueError("builder output failed handoff schema validation")
    return handoff
