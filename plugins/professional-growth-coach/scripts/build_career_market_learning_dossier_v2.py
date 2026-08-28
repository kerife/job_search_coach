"""Build a pure, identity-free recurring-gap learning dossier v2."""

from __future__ import annotations

import copy
import importlib.util
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_build_v2_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("required learning dossier dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V1 = _sibling("validate_career_market_learning_dossier.py")
RESEARCH = _sibling("validate_learning_option_research.py")
V2 = _sibling("validate_career_market_learning_dossier_v2.py")


def required_recurrence(sample_size: int) -> int:
    if type(sample_size) is not int or not 2 <= sample_size <= 5:
        raise ValueError("sample size must be between two and five")
    return max(2, sample_size // 2 + 1)


def _text(value: str) -> str:
    return value


def _is_professional_signal(signal: object) -> bool:
    value = str(signal)
    return value in {"professional_experience", "production_experience", "operational_experience", "leadership_experience"} or "experience" in value or value.startswith(("production_", "operational_", "leadership_"))


def _decision_for(option: Mapping[str, object], recurrence: Mapping[str, object], preferences: Mapping[str, object], as_of_date: str) -> str:
    option_type = option.get("option_type")
    signal = str(option.get("gap_signal"))
    if _is_professional_signal(signal):
        if option_type in {"candidate_owned_project", "lab"}:
            return "project_first"
        if option_type in {"course", "certification"}:
            return "pause"
        return "apply_with_boundary"
    if option_type == "candidate_owned_project" or option_type == "lab":
        return "project_first"
    if option_type in {"course", "certification"}:
        threshold = required_recurrence(int(recurrence["sample_size"]))
        if int(recurrence["occurrences"]) >= threshold and preferences.get("weekly_time_budget") != "unknown" and preferences.get("money_budget") != "unknown" and option.get("source_state") == "active" and RESEARCH.provider_source_is_fresh(option.get("source_date"), as_of_date):
            return "recommended"
        return "consider"
    if option_type == "free_resource":
        return "consider"
    return "not_needed"


def _decision_rank(decision: str) -> int:
    return {"project_first": 0, "recommended": 1, "consider": 2, "apply_with_boundary": 3, "pause": 4, "not_needed": 5}[decision]


def _preferred_option(options: list[Mapping[str, object]]) -> Mapping[str, object]:
    return min(
        options,
        key=lambda option: (
            V2.OPTION_TYPE_PRECEDENCE.get(str(option.get("option_type")), 99),
            str(option.get("option_id")),
        ),
    )


def _decision_row(rank: int, option: Mapping[str, object], recurrence: Mapping[str, object], decision: str, preferences: Mapping[str, object], as_of_date: str) -> dict[str, object]:
    signal = str(option["gap_signal"])
    option_type = str(option["option_type"])
    paid_unknown = option_type in {"course", "certification"} and (preferences.get("weekly_time_budget") == "unknown" or preferences.get("money_budget") == "unknown")
    provider_stale = option_type in {"course", "certification"} and option.get("source_state") == "active" and not RESEARCH.provider_source_is_fresh(option.get("source_date"), as_of_date)
    basis = "candidate-owned evidence has higher signal than a certificate; keep publication review pending" if decision == "project_first" else "official provider source is outside the 90-day freshness window; refresh it before considering enrollment" if provider_stale else "official provider source and exact recurring vacancy evidence; review budget and authorization before enrollment" if option_type in {"course", "certification"} else "recurring vacancy evidence is bounded and the next review gate remains private"
    gate = "no external action; complete ownership, secrets, confidentiality, customer-data, rights-holder, and publication review" if option_type == "candidate_owned_project" else "no external action; refresh provider source and confirm exact enrollment authorization" if provider_stale else "no external action; confirm candidate budget/time preferences and exact enrollment authorization" if paid_unknown else "no external action; confirm the exact candidate action and target before proceeding"
    if paid_unknown and signal not in {"professional_experience", "production_experience", "operational_experience", "leadership_experience"}:
        decision = "consider"
    return {
        "rank": rank,
        "gap_signal": signal,
        "frequency_occurrences": int(recurrence["occurrences"]),
        "frequency_sample_size": int(recurrence["sample_size"]),
        "frequency_display": str(recurrence["display_fraction"]),
        "gap_type": "professional_experience_gap" if _is_professional_signal(signal) else "proof_gap" if option_type in {"candidate_owned_project", "lab"} else "learnable_gap",
        "option_id": str(option["option_id"]),
        "option_type": option_type,
        "decision": decision,
        "proof_needed": _text(str(option["proof_artifact"])),
        "opportunity_cost": "time diverted from applications, interview preparation, and higher-signal candidate-owned proof",
        "decision_basis": basis,
        "next_action_gate": gate,
        "expected_signal": "bounded hypothesis a bounded proof artifact may make the gap easier to discuss without predicting hiring outcomes",
        "confidence": "medium" if int(recurrence["occurrences"]) >= 2 else "low",
        "outcome_boundary": "not_an_interview_offer_salary_or_roi_prediction",
        "draft_only": True,
        "no_external_action": True,
    }


def build_learning_dossier(market: Mapping[str, object], learning_research: Mapping[str, object]) -> dict[str, object]:
    if V1.validate_market_dossier(market):
        raise ValueError("market dossier is invalid")
    if RESEARCH.validate_research(learning_research):
        raise ValueError("learning option research is invalid")
    if learning_research.get("source_market_snapshot") != V1.snapshot_for_market_dossier(market):
        raise ValueError("learning research is bound to a different market dossier")
    output = copy.deepcopy(dict(market))
    output["schema_version"] = "career-market-learning-dossier-v2"
    output["learning_evidence_mode"] = learning_research["evidence_mode"]
    output["source_market_snapshot"] = V1.snapshot_for_market_dossier(market)
    output["source_learning_research_snapshot"] = RESEARCH.snapshot_for_learning_research(learning_research)
    output["candidate_preferences"] = copy.deepcopy(learning_research["candidate_preferences"])
    output["learning_options"] = copy.deepcopy(learning_research["options"])
    output["learning_state"] = "evaluated"
    recurrence = {str(row["signal"]): row for row in market["recurrence_rows"] if isinstance(row, Mapping)}
    options = [
        row for row in learning_research["options"]
        if isinstance(row, Mapping)
        and str(row.get("gap_signal")) in recurrence
        and recurrence[str(row.get("gap_signal"))].get("support_state") == "explicit_gap"
    ]
    if not 3 <= len(options) <= 5:
        raise ValueError("three through five exact recurring learning options are required")
    preferences = learning_research["candidate_preferences"]
    pending: list[tuple[Mapping[str, object], str]] = []
    by_signal: dict[str, list[Mapping[str, object]]] = {}
    for option in options:
        by_signal.setdefault(str(option["gap_signal"]), []).append(option)
    for signal, candidates in by_signal.items():
        option = _preferred_option(candidates)
        pending.append((option, _decision_for(option, recurrence[signal], preferences, str(learning_research["as_of_date"]))))
    if len(pending) < 3:
        raise ValueError("three distinct explicit recurring learning gaps are required")
    pending.sort(key=lambda item: (_decision_rank(item[1]), str(item[0]["option_id"])))
    decisions = [_decision_row(index, option, recurrence[str(option["gap_signal"])], decision, preferences, str(learning_research["as_of_date"])) for index, (option, decision) in enumerate(pending[:5], 1)]
    if len(decisions) < 3:
        raise ValueError("three through five learning decisions are required")
    output["learning_decisions"] = decisions
    project_present = any(row["decision"] == "project_first" for row in decisions)
    output["coach_decision"] = {
        "decision": "project_first" if project_present else "hold_until_preferences_confirmed" if any(row["decision"] == "consider" for row in decisions) else "do_nothing_now",
        "rationale": "Prioritize candidate-owned proof before paid learning while preserving private review gates.",
        "review_gate": "No external action; review the exact option, candidate preferences, and publication boundary before proceeding.",
        "draft_only": True,
        "no_external_action": True,
    }
    output["proof_sprint"] = {"duration_days": 5, "scope": "Private bounded proof sprint for the recurring gap.", "steps": ["Define the gap and acceptance check.", "Build a minimal private artifact.", "Record the reproducible result.", "Review ownership and confidentiality.", "Decide whether any reuse is authorized."], "ownership_review": "required_before_publication", "publication_review": "required_before_publication", "no_external_action": True} if project_present else None
    output["reuse_map"] = [{"destination": destination, "claim_boundary": "Use only the private, evidence-backed artifact claim; do not imply hiring outcomes.", "exact_authorization_required": True, "publication_authorized": False, "no_external_action": True} for destination in ("linkedin", "application_packet", "interview")] if project_present else []
    if V2.validate_learning_dossier(output):
        raise ValueError("built market learning dossier v2 failed validation")
    return output
