#!/usr/bin/env python3
"""Validate a derived, identity-free recurring-gap learning dossier v2."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any


class _ArgumentError(ValueError):
    pass


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise _ArgumentError


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_v2_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("required learning dossier dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V1 = _sibling("validate_career_market_learning_dossier.py")
RESEARCH = _sibling("validate_learning_option_research.py")
_LOADER = _sibling("private_input_loader.py")
_PROSE = _sibling("private_prose_safety.py")

SCHEMA_VERSION = "career-market-learning-dossier-v2"
MAX_INPUT_BYTES = 256 * 1024
MAX_DEPTH = 12
MARKET_SNAPSHOT = re.compile(r"^snap-market-sha256-[0-9a-f]{64}$")
LEARNING_SNAPSHOT = re.compile(r"^snap-learning-sha256-[0-9a-f]{64}$")
SIGNAL = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
DECISIONS = frozenset({"recommended", "consider", "pause", "project_first", "apply_with_boundary", "not_needed"})
EVIDENCE_MODES = frozenset({"synthetic", "live"})
OPTION_TYPE_PRECEDENCE = {
    "candidate_owned_project": 0,
    "lab": 1,
    "free_resource": 2,
    "course": 3,
    "certification": 4,
    "do_nothing_now": 5,
}
PAID_OPTIONS = frozenset({"course", "certification"})
PROFESSIONAL_EXPERIENCE_SIGNALS = frozenset({
    "professional_experience", "production_experience", "operational_experience", "leadership_experience",
})


def _is_professional_signal(signal: object) -> bool:
    value = str(signal)
    return value in PROFESSIONAL_EXPERIENCE_SIGNALS or "experience" in value or value.startswith(("production_", "operational_", "leadership_"))
TOP_FIELDS = frozenset({
    "schema_version", "evidence_mode", "learning_evidence_mode", "locale", "as_of_date", "state", "source_research_snapshot",
    "source_executive_dossier_snapshot", "source_market_snapshot", "source_learning_research_snapshot",
    "candidate_preferences", "search_summary", "vacancy_cards", "matrix_rows", "recurrence_rows",
    "learning_state", "learning_decisions", "learning_options", "coach_decision", "proof_sprint", "reuse_map",
    "methodology_boundary", "privacy_boundary", "no_external_action",
})
DECISION_FIELDS = frozenset({
    "rank", "gap_signal", "frequency_occurrences", "frequency_sample_size", "frequency_display", "gap_type",
    "option_id", "option_type", "decision", "proof_needed", "opportunity_cost", "decision_basis",
    "next_action_gate", "expected_signal", "confidence", "outcome_boundary", "draft_only", "no_external_action",
})
COACH_FIELDS = frozenset({"decision", "rationale", "review_gate", "draft_only", "no_external_action"})
SPRINT_FIELDS = frozenset({"duration_days", "scope", "steps", "ownership_review", "publication_review", "no_external_action"})
REUSE_FIELDS = frozenset({"destination", "claim_boundary", "exact_authorization_required", "publication_authorized", "no_external_action"})


def _closed(value: object, fields: frozenset[str], path: str, errors: list[str]) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    if set(value) - fields:
        errors.append(f"{path} has unsupported fields")
    if fields - set(value):
        errors.append(f"{path} is missing required fields")
    return value


def _depth(value: object, level: int = 0) -> bool:
    if level > MAX_DEPTH:
        return False
    if isinstance(value, Mapping):
        return all(_depth(key, level + 1) and _depth(item, level + 1) for key, item in value.items())
    if isinstance(value, list):
        return all(_depth(item, level + 1) for item in value)
    return True


def _text(value: object, path: str, errors: list[str], maximum: int = 500) -> None:
    if not isinstance(value, str) or not value or len(value) > maximum:
        errors.append(f"{path} must be bounded text")
        return
    if _PROSE.contains_unicode_controls(value):
        errors.append(f"{path} contains forbidden control characters")
    if re.search(r"<\/?(?:script|iframe|object|style)\b", value, re.I):
        errors.append(f"{path} contains forbidden markup")
    if re.search(r"(?:[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:^|\s)(?:/[A-Za-z]|[A-Za-z]:[\\/]))", value):
        errors.append(f"{path} contains private value")


def _base_market(value: Mapping[str, object]) -> dict[str, object]:
    base = copy.deepcopy(dict(value))
    base["schema_version"] = "career-market-learning-dossier-v1"
    base["learning_state"] = "not_evaluated"
    base["learning_decisions"] = []
    for key in ("source_market_snapshot", "source_learning_research_snapshot", "candidate_preferences", "learning_evidence_mode", "learning_options", "coach_decision", "proof_sprint", "reuse_map"):
        base.pop(key, None)
    return base


def _validate_decision(value: object, index: int, recurrence: Mapping[str, Mapping[str, object]], options: Mapping[str, Mapping[str, object]], preferences: Mapping[str, object], as_of_date: object, errors: list[str]) -> None:
    path = f"learning_decisions[{index}]"
    row = _closed(value, DECISION_FIELDS, path, errors)
    if row is None:
        return
    rank = row.get("rank")
    if type(rank) is not int or rank != index + 1:
        errors.append(f"{path}.rank does not reconcile")
    signal = row.get("gap_signal")
    if not isinstance(signal, str) or not SIGNAL.fullmatch(signal) or signal not in recurrence:
        errors.append(f"{path}.gap_signal is invalid or not recurrent")
        return
    rec = recurrence[signal]
    if rec.get("support_state") != "explicit_gap":
        errors.append(f"{path} requires an explicit gap recurrence")
    if row.get("frequency_occurrences") != rec.get("occurrences") or row.get("frequency_sample_size") != rec.get("sample_size") or row.get("frequency_display") != rec.get("display_fraction"):
        errors.append(f"{path}.frequency does not reconcile")
    option_id = row.get("option_id")
    option = options.get(option_id) if isinstance(option_id, str) else None
    if option is None or option.get("gap_signal") != signal:
        errors.append(f"{path}.option_id is not bound to gap signal")
        return
    if row.get("option_type") != option.get("option_type"):
        errors.append(f"{path}.option_type does not reconcile")
    option_type = option.get("option_type")
    decision = row.get("decision")
    if decision not in DECISIONS:
        errors.append(f"{path}.decision has invalid value")
    if decision == "project_first" and option_type not in {"candidate_owned_project", "lab"}:
        errors.append(f"{path}.project_first requires a project or lab option")
    if decision == "recommended" and option_type not in PAID_OPTIONS:
        errors.append(f"{path}.recommended requires a paid learning option")
    if _is_professional_signal(signal) and option_type in {"course", "certification"} and decision != "pause":
        errors.append(f"{path} professional experience cannot be replaced by a course or certification")
    threshold = max(2, int(rec.get("sample_size", 0)) // 2 + 1)
    occurrences = int(rec.get("occurrences", 0))
    if decision == "project_first" and (rec.get("sample_size", 0) < 2 or occurrences < threshold):
        errors.append(f"{path} project_first requires recurring majority evidence")
    if option_type in PAID_OPTIONS and decision == "recommended":
        if rec.get("sample_size", 0) < 2 or occurrences < threshold:
            errors.append(f"{path} paid recommendation requires recurring majority evidence")
        if preferences.get("weekly_time_budget") == "unknown" or preferences.get("money_budget") == "unknown":
            errors.append(f"{path} paid recommendation requires known candidate budgets")
        if option.get("source_state") != "active":
            errors.append(f"{path} paid recommendation requires an active provider source")
        if not RESEARCH.provider_source_is_fresh(option.get("source_date"), as_of_date):
            errors.append(f"{path} recommended requires a fresh provider source")
    if option_type in PAID_OPTIONS and decision == "consider" and (preferences.get("weekly_time_budget") == "unknown" or preferences.get("money_budget") == "unknown"):
        if "budget" not in str(row.get("next_action_gate", "")).casefold() and "preference" not in str(row.get("next_action_gate", "")).casefold():
            errors.append(f"{path}.next_action_gate must name budget or preference review")
    if not isinstance(row.get("gap_type"), str) or row.get("gap_type") not in {"learnable_gap", "professional_experience_gap", "proof_gap"}:
        errors.append(f"{path}.gap_type has invalid value")
    expected_gap_type = (
        "professional_experience_gap" if _is_professional_signal(signal)
        else "proof_gap" if option_type in {"candidate_owned_project", "lab"}
        else "learnable_gap"
    )
    if row.get("gap_type") != expected_gap_type:
        errors.append(f"{path}.gap_type does not reconcile with option")
    if _is_professional_signal(signal):
        expected_decision = "project_first" if option_type in {"candidate_owned_project", "lab"} else "pause" if option_type in PAID_OPTIONS else "apply_with_boundary"
    elif option_type in {"candidate_owned_project", "lab"}:
        expected_decision = "project_first"
    elif option_type in PAID_OPTIONS:
        expected_decision = "recommended" if rec.get("sample_size", 0) >= 2 and occurrences >= threshold and preferences.get("weekly_time_budget") != "unknown" and preferences.get("money_budget") != "unknown" and option.get("source_state") == "active" and RESEARCH.provider_source_is_fresh(option.get("source_date"), as_of_date) else "consider"
    elif option_type == "free_resource":
        expected_decision = "consider"
    else:
        expected_decision = "not_needed"
    if decision != expected_decision:
        errors.append(f"{path}.decision does not reconcile with option, recurrence, and preferences")
    candidates = [candidate for candidate in options.values() if candidate.get("gap_signal") == signal]
    if candidates:
        preferred = min(candidates, key=lambda candidate: (OPTION_TYPE_PRECEDENCE.get(str(candidate.get("option_type")), 99), str(candidate.get("option_id"))))
        if option_id != preferred.get("option_id"):
            errors.append(f"{path}.option_id does not use deterministic option precedence")
    for field in ("proof_needed", "opportunity_cost", "decision_basis", "next_action_gate", "expected_signal"):
        _text(row.get(field), f"{path}.{field}", errors)
    if not str(row.get("expected_signal", "")).startswith("bounded hypothesis "):
        errors.append(f"{path}.expected_signal must begin with bounded hypothesis")
    if row.get("outcome_boundary") != "not_an_interview_offer_salary_or_roi_prediction":
        errors.append(f"{path}.outcome_boundary has invalid value")
    if row.get("draft_only") is not True or row.get("no_external_action") is not True:
        errors.append(f"{path} must remain draft-only and no-external-action")


def validate_learning_dossier(value: object) -> list[str]:
    """Return sorted, bounded diagnostics for a v2 dossier."""
    errors: list[str] = []
    try:
        if not isinstance(value, Mapping):
            return ["market learning dossier v2 must be an object"]
        if not _depth(value):
            errors.append("market learning dossier v2 exceeds maximum nesting depth")
        if set(value) - TOP_FIELDS:
            errors.append("market learning dossier v2 has unsupported fields")
        if TOP_FIELDS - set(value):
            errors.append("market learning dossier v2 is missing required fields")
        if value.get("schema_version") != SCHEMA_VERSION:
            errors.append("schema_version has invalid value")
        learning_evidence_mode = value.get("learning_evidence_mode")
        if learning_evidence_mode not in EVIDENCE_MODES:
            errors.append("learning_evidence_mode has invalid value")
        base = _base_market(value)
        errors.extend(V1.validate_market_dossier(base))
        if value.get("source_market_snapshot") != V1.snapshot_for_market_dossier(base):
            errors.append("source_market_snapshot does not bind to market dossier")
        if not isinstance(value.get("source_learning_research_snapshot"), str) or not LEARNING_SNAPSHOT.fullmatch(value["source_learning_research_snapshot"]):
            errors.append("source_learning_research_snapshot has invalid value")
        if value.get("learning_state") != "evaluated":
            errors.append("learning_state must be evaluated")
        preferences = _closed(value.get("candidate_preferences"), frozenset({"weekly_time_budget", "money_budget", "currency", "purchase_authorized"}), "candidate_preferences", errors)
        if preferences is None:
            preferences = {}
        elif preferences.get("purchase_authorized") is not False:
            errors.append("candidate_preferences.purchase_authorized must be false")
        as_of_date = value.get("as_of_date")
        options_value = value.get("learning_options")
        options: dict[str, Mapping[str, object]] = {}
        if not isinstance(options_value, list) or not 1 <= len(options_value) <= 5:
            errors.append("learning_options has invalid item count")
        else:
            research_wrapper = {
                "schema_version": "learning-option-research-v1", "evidence_mode": learning_evidence_mode, "locale": value.get("locale"), "as_of_date": value.get("as_of_date"),
                "source_market_snapshot": value.get("source_market_snapshot"), "candidate_preferences": preferences,
                "options": options_value, "privacy_boundary": "identity_free_market_and_provider_evidence_only", "no_external_action": True,
            }
            errors.extend(RESEARCH.validate_research(research_wrapper))
            expected_learning_snapshot = RESEARCH.snapshot_for_learning_research(research_wrapper)
            if value.get("source_learning_research_snapshot") != expected_learning_snapshot:
                errors.append("source_learning_research_snapshot does not bind to learning options")
            for option in options_value:
                if isinstance(option, Mapping) and isinstance(option.get("option_id"), str):
                    options[option["option_id"]] = option
            if learning_evidence_mode in EVIDENCE_MODES:
                expected_state = "synthetic" if learning_evidence_mode == "synthetic" else "active"
                if any(isinstance(option, Mapping) and option.get("source_state") != expected_state for option in options_value):
                    errors.append(f"{learning_evidence_mode} learning evidence requires {expected_state} provider sources")
        recurrence_value = value.get("recurrence_rows")
        recurrence: dict[str, Mapping[str, object]] = {}
        if isinstance(recurrence_value, list):
            for row in recurrence_value:
                if isinstance(row, Mapping) and isinstance(row.get("signal"), str):
                    recurrence[row["signal"]] = row
        decisions = value.get("learning_decisions")
        if not isinstance(decisions, list) or not 3 <= len(decisions) <= 5:
            errors.append("learning_decisions must contain three through five decisions")
        else:
            seen_signals: set[str] = set()
            for index, decision in enumerate(decisions):
                _validate_decision(decision, index, recurrence, options, preferences, as_of_date, errors)
                if isinstance(decision, Mapping) and isinstance(decision.get("gap_signal"), str):
                    if decision["gap_signal"] in seen_signals:
                        errors.append("learning_decisions must contain one decision per recurring signal")
                    seen_signals.add(decision["gap_signal"])
            if len(seen_signals) != len(decisions):
                errors.append("learning_decisions must contain unique recurring signals")
        coach = _closed(value.get("coach_decision"), COACH_FIELDS, "coach_decision", errors)
        project_present = isinstance(decisions, list) and any(isinstance(row, Mapping) and row.get("decision") == "project_first" for row in decisions)
        if coach is not None:
            if coach.get("decision") not in {"project_first", "review_learning_options", "hold_until_preferences_confirmed", "do_nothing_now"}:
                errors.append("coach_decision.decision has invalid value")
            for field in ("rationale", "review_gate"):
                _text(coach.get(field), f"coach_decision.{field}", errors)
            if coach.get("decision") == "project_first" and not project_present:
                errors.append("coach_decision does not reconcile with decisions")
            if project_present and coach.get("decision") != "project_first":
                errors.append("coach_decision must prioritize project_first when present")
            if not project_present and any(isinstance(row, Mapping) and row.get("decision") == "consider" for row in decisions if isinstance(decisions, list)) and coach.get("decision") not in {"hold_until_preferences_confirmed", "review_learning_options"}:
                errors.append("coach_decision must preserve a review gate for consider decisions")
            if not project_present and any(isinstance(row, Mapping) and row.get("decision") in {"apply_with_boundary", "pause"} for row in decisions if isinstance(decisions, list)) and not any(isinstance(row, Mapping) and row.get("decision") == "consider" for row in decisions if isinstance(decisions, list)) and coach.get("decision") != "review_learning_options":
                errors.append("coach_decision must preserve a review gate for apply_with_boundary or pause decisions")
            if coach.get("draft_only") is not True or coach.get("no_external_action") is not True:
                errors.append("coach_decision must remain draft-only and no-external-action")
        sprint = value.get("proof_sprint")
        reuse = value.get("reuse_map")
        if project_present:
            sprint_row = _closed(sprint, SPRINT_FIELDS, "proof_sprint", errors)
            if sprint_row is not None:
                if sprint_row.get("duration_days") != 5 or sprint_row.get("ownership_review") != "required_before_publication" or sprint_row.get("publication_review") != "required_before_publication" or sprint_row.get("no_external_action") is not True:
                    errors.append("proof_sprint has invalid fixed gates")
                _text(sprint_row.get("scope"), "proof_sprint.scope", errors)
                steps = sprint_row.get("steps")
                if not isinstance(steps, list) or len(steps) != 5:
                    errors.append("proof_sprint.steps must contain five bounded steps")
                else:
                    for index, step in enumerate(steps):
                        _text(step, f"proof_sprint.steps[{index}]", errors)
            if not isinstance(reuse, list) or len(reuse) != 3:
                errors.append("project_first requires exactly three reuse-map rows")
            else:
                destinations: set[str] = set()
                for index, item in enumerate(reuse):
                    row = _closed(item, REUSE_FIELDS, f"reuse_map[{index}]", errors)
                    if row is None:
                        continue
                    destinations.add(str(row.get("destination")))
                    if row.get("destination") not in {"linkedin", "application_packet", "interview"}:
                        errors.append(f"reuse_map[{index}].destination has invalid value")
                    _text(row.get("claim_boundary"), f"reuse_map[{index}].claim_boundary", errors)
                    if row.get("exact_authorization_required") is not True or row.get("publication_authorized") is not False or row.get("no_external_action") is not True:
                        errors.append(f"reuse_map[{index}] has invalid action gates")
                if destinations != {"linkedin", "application_packet", "interview"}:
                    errors.append("reuse_map must cover LinkedIn, application packet, and interview")
        elif sprint is not None or reuse != []:
            errors.append("proof_sprint and reuse_map must be empty without project_first")
        if value.get("methodology_boundary") != "sample_based_documented_evidence_only_no_hiring_fit":
            errors.append("methodology_boundary has invalid value")
        if value.get("privacy_boundary") != "identity_free_evidence_references_only":
            errors.append("privacy_boundary has invalid value")
        if value.get("no_external_action") is not True:
            errors.append("no_external_action must be true")
    except (RecursionError, TypeError, ValueError, KeyError):
        errors.append("market learning dossier v2 could not be validated")
    return sorted(set(errors))


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def load_learning_dossier(path: Path) -> dict[str, object]:
    try:
        raw = _LOADER.read_bounded_bytes(path, MAX_INPUT_BYTES)
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        if not isinstance(value, dict) or not _depth(value):
            raise ValueError("market learning dossier v2 exceeds maximum nesting depth")
    except (_LOADER.PrivateInputError, UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ValueError("market learning dossier v2 could not be loaded") from exc
    if not isinstance(value, dict):
        raise ValueError("market learning dossier v2 must be an object")
    return value


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    try:
        args = parser.parse_args(argv)
    except _ArgumentError:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    try:
        value = load_learning_dossier(args.path)
    except (OSError, ValueError):
        print("market learning dossier v2 could not be loaded", file=sys.stderr)
        return 2
    errors = validate_learning_dossier(value)
    if errors:
        sys.stderr.write(_PROSE.format_bounded_diagnostics(errors))
        return 1
    print("valid market learning dossier v2")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
