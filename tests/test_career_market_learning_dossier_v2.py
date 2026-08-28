"""Contract tests for the pure recurring-gap learning ROI dossier v2."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
MARKET_FIXTURES = ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "career-market-learning-dossier"
RESEARCH_FIXTURES = ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "learning-option-research"
sys.path.insert(0, str(SCRIPTS))

from build_career_market_learning_dossier_v2 import (  # noqa: E402
    build_learning_dossier,
    required_recurrence,
)
from validate_career_market_learning_dossier_v2 import validate_learning_dossier  # noqa: E402
from validate_career_market_learning_dossier import validate_market_dossier  # noqa: E402
from validate_career_market_learning_dossier import snapshot_for_market_dossier  # noqa: E402
from validate_learning_option_research import (  # noqa: E402
    snapshot_for_learning_research,
)


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _recurring_market(sample_size: int = 5) -> dict[str, object]:
    market = _load(MARKET_FIXTURES / "complete-five-es.json")
    cards = market["vacancy_cards"][:sample_size]
    market["state"] = "complete" if sample_size == 5 else "limited_market_evidence"
    market["search_summary"]["vacancy_sample_count"] = sample_size
    market["vacancy_cards"] = cards
    signals = ("terraform_iac", "kubernetes", "observability")
    for card in cards:
        card["requirements"] = [
            {"requirement_id": f"{card['vacancy_id']}-R-{index:02d}", "signal": signal, "importance": "must_have"}
            for index, signal in enumerate(signals, 1)
        ]
        card["maximum_points"] = 12
        card["known_points"] = 12
        card["evidence_coverage_percent"] = 100
        card["qualitative_band"] = "lower_documented_alignment"
    market["matrix_rows"] = [{
        "signal": signal,
        "support_state": "explicit_gap",
        "evidence_ids": [f"E-{index:03d}"],
        "cells": [
            {"vacancy_id": card["vacancy_id"], "required": True}
            for card in cards
        ],
    } for index, signal in enumerate(signals, 1)]
    market["recurrence_rows"] = sorted([{
        "signal": signal,
        "occurrences": sample_size,
        "sample_size": sample_size,
        "display_fraction": f"{sample_size}/{sample_size}",
        "support_state": "explicit_gap",
        "evidence_ids": [f"E-{index:03d}"],
    } for index, signal in enumerate(signals, 1)], key=lambda row: (-row["occurrences"], row["signal"]))
    # The v1 fixture's card arithmetic remains valid: a gap earns no points.
    return market


def _research(market: dict[str, object], *, project: bool = True, course: bool = True) -> dict[str, object]:
    research = _load(RESEARCH_FIXTURES / "complete-five-es.json")
    research["source_market_snapshot"] = snapshot_for_market_dossier(market)
    options = []
    for option in research["options"]:
        if option["option_type"] == "candidate_owned_project" and not project:
            continue
        if option["option_type"] in {"course", "certification"} and not course:
            continue
        options.append(copy.deepcopy(option))
    if not options:
        raise AssertionError("test research must contain at least one exact option")
    research["options"] = options
    return research


def _bind(research: dict[str, object], market: dict[str, object]) -> dict[str, object]:
    research["source_market_snapshot"] = snapshot_for_market_dossier(market)
    return research


class CareerMarketLearningDossierV2Tests(unittest.TestCase):
    def test_required_recurrence_uses_majority_threshold(self) -> None:
        self.assertEqual(2, required_recurrence(2))
        self.assertEqual(2, required_recurrence(3))
        self.assertEqual(3, required_recurrence(4))
        self.assertEqual(3, required_recurrence(5))

    def test_builder_emits_project_first_for_exact_recurring_gap(self) -> None:
        market = _recurring_market(5)
        market["evidence_mode"] = "synthetic"
        research = _research(market, project=True, course=True)
        dossier = build_learning_dossier(market, research)
        self.assertEqual("career-market-learning-dossier-v2", dossier["schema_version"])
        self.assertEqual("synthetic", dossier["evidence_mode"])
        self.assertEqual("evaluated", dossier["learning_state"])
        self.assertEqual(3, len(dossier["learning_decisions"]))
        first = dossier["learning_decisions"][0]
        self.assertEqual("terraform_iac", first["gap_signal"])
        self.assertEqual("project_first", first["decision"])
        self.assertEqual("5/5", first["frequency_display"])
        self.assertEqual(1, first["rank"])
        self.assertTrue(first["draft_only"])
        self.assertTrue(first["no_external_action"])
        self.assertEqual("project_first", dossier["coach_decision"]["decision"])
        sprint = dossier["proof_sprint"]
        self.assertEqual(5, sprint["duration_days"])
        self.assertEqual(3, len(dossier["reuse_map"]))
        self.assertEqual([], validate_learning_dossier(dossier))

    def test_professional_apply_or_pause_decisions_require_review_coach_decision(self) -> None:
        market = _recurring_market(5)
        market["evidence_mode"] = "synthetic"
        market["recurrence_rows"][0]["signal"] = "production_experience"
        market["recurrence_rows"][1]["signal"] = "leadership_experience"
        market["recurrence_rows"][2]["signal"] = "operational_experience"
        for row, signal in zip(market["matrix_rows"], ("production_experience", "leadership_experience", "operational_experience")):
            row["signal"] = signal
        for card in market["vacancy_cards"]:
            for requirement, signal in zip(card["requirements"], ("production_experience", "leadership_experience", "operational_experience")):
                requirement["signal"] = signal
        evidence_by_signal = {"production_experience": "E-001", "leadership_experience": "E-002", "operational_experience": "E-003"}
        market["recurrence_rows"] = [
            {**row, "evidence_ids": [evidence_by_signal[row["signal"]]]}
            for row in sorted(market["recurrence_rows"], key=lambda item: item["signal"])
        ]
        research = _research(market, project=True, course=True)
        remapped = ["production_experience", "leadership_experience", "operational_experience"]
        option_types = ["free_resource", "course", "free_resource"]
        for option, signal, option_type in zip(research["options"], remapped, option_types):
            option["gap_signal"] = signal
            option["option_type"] = option_type
            if option_type == "free_resource":
                option["current_cost"] = option["currency"] = option["tax"] = "not_applicable"
                option["duration"] = "1 private hour"
                option["duration_basis"] = "candidate_estimated"
        dossier = build_learning_dossier(market, research)
        self.assertEqual({"apply_with_boundary", "pause"}, {row["decision"] for row in dossier["learning_decisions"]})
        self.assertEqual("review_learning_options", dossier["coach_decision"]["decision"])
        self.assertEqual([], validate_learning_dossier(dossier))

    def test_builder_chooses_project_before_lab_when_research_order_changes(self) -> None:
        market = _recurring_market(5)
        market["evidence_mode"] = "synthetic"
        research = _research(market, project=True, course=True)
        project = next(option for option in research["options"] if option["option_type"] == "candidate_owned_project")
        lab = next(option for option in research["options"] if option["option_type"] == "lab")
        research["options"] = [lab, project] + [option for option in research["options"] if option["option_id"] not in {project["option_id"], lab["option_id"]}]
        dossier = build_learning_dossier(market, research)
        first = next(row for row in dossier["learning_decisions"] if row["gap_signal"] == "terraform_iac")
        self.assertEqual("LO-001", first["option_id"])

    def test_market_and_provider_evidence_modes_are_separate_and_propagated(self) -> None:
        market = _recurring_market(5)
        market["evidence_mode"] = "live"
        for card in market["vacancy_cards"]:
            card["source_url"] = f"https://www.python.org/dev/jobs/{card['vacancy_id']}"
        research = _research(market, project=True, course=True)
        research["evidence_mode"] = "synthetic"
        dossier = build_learning_dossier(market, research)
        self.assertEqual("live", dossier["evidence_mode"])
        self.assertEqual("synthetic", dossier["learning_evidence_mode"])
        self.assertTrue(all(row["decision"] != "recommended" for row in dossier["learning_decisions"]))
        self.assertEqual([], validate_learning_dossier(dossier))

    def test_v2_inherits_live_future_date_rejection_from_market_contract(self) -> None:
        fixture = _load(
            ROOT / "tests" / "evals" / "with-skill" / "fixtures"
            / "career-market-learning-dossier-v2" / "project-first-five-es.json",
        )
        future = (date.today() + timedelta(days=1)).isoformat()
        fixture["evidence_mode"] = "live"
        fixture["as_of_date"] = future
        for card in fixture["vacancy_cards"]:
            card["source_url"] = "https://careers.public.example/roles/123"

        errors = validate_learning_dossier(fixture)

        self.assertIn("as_of_date cannot be in the future for live evidence", errors)
        self.assertNotIn(future, " ".join(errors))

    def test_v2_inherits_synthetic_source_url_policy_from_market_contract(self) -> None:
        fixture = _load(
            ROOT / "tests" / "evals" / "with-skill" / "fixtures"
            / "career-market-learning-dossier-v2" / "project-first-five-es.json",
        )
        source_url = "https://example.com/careers/session%25255Fid%253Dprivate-marker"
        fixture["vacancy_cards"][0]["source_url"] = source_url

        errors = validate_learning_dossier(fixture)

        self.assertIn("vacancy_cards[0].source_url is invalid", errors)
        self.assertNotIn(source_url, " ".join(errors))

    def test_unknown_budgets_block_paid_recommended_but_permit_consider(self) -> None:
        market = _recurring_market(4)
        research = _research(market, project=False, course=True)
        for option in research["options"]:
            if option["option_type"] == "candidate_owned_project":
                option["option_type"] = "course"
                option["current_cost"] = "unknown"
                option["currency"] = "unknown"
                option["tax"] = "unknown"
                option["option_id"] = "LO-006"
        _bind(research, market)
        dossier = build_learning_dossier(market, research)
        decisions = dossier["learning_decisions"]
        self.assertTrue(decisions)
        paid = [row for row in decisions if row["option_type"] in {"course", "certification"}]
        self.assertTrue(paid)
        self.assertTrue(all(row["decision"] == "consider" for row in paid))
        self.assertIn("budget", paid[0]["next_action_gate"].casefold())
        self.assertEqual([], validate_learning_dossier(dossier))

    def test_paid_learning_requires_a_fresh_provider_source(self) -> None:
        market = _recurring_market(5)
        research = _research(market, project=True, course=True)
        research["evidence_mode"] = "live"
        research["candidate_preferences"].update({"weekly_time_budget": "5 hours/week", "money_budget": "1000", "currency": "MXN"})
        as_of = date.fromisoformat(research["as_of_date"])
        for option in research["options"]:
            option["source_state"] = "active"
            if option["option_type"] != "do_nothing_now":
                option["url"] = f"https://www.python.org/dev/jobs/{option['option_id']}"
        course = next(option for option in research["options"] if option["option_type"] == "course")
        course["source_date"] = (as_of - timedelta(days=91)).isoformat()
        dossier = build_learning_dossier(market, research)
        kubernetes = next(row for row in dossier["learning_decisions"] if row["gap_signal"] == "kubernetes")
        self.assertEqual("consider", kubernetes["decision"])
        self.assertIn("refresh", kubernetes["next_action_gate"].casefold())
        self.assertEqual([], validate_learning_dossier(dossier))

    def test_ninety_day_provider_source_remains_eligible(self) -> None:
        market = _recurring_market(5)
        research = _research(market, project=True, course=True)
        research["evidence_mode"] = "live"
        research["candidate_preferences"].update({"weekly_time_budget": "5 hours/week", "money_budget": "1000", "currency": "MXN"})
        as_of = date.fromisoformat(research["as_of_date"])
        for option in research["options"]:
            option["source_state"] = "active"
            if option["option_type"] != "do_nothing_now":
                option["url"] = f"https://www.python.org/dev/jobs/{option['option_id']}"
        course = next(option for option in research["options"] if option["option_type"] == "course")
        course["source_date"] = (as_of - timedelta(days=90)).isoformat()
        dossier = build_learning_dossier(market, research)
        kubernetes = next(row for row in dossier["learning_decisions"] if row["gap_signal"] == "kubernetes")
        self.assertEqual("recommended", kubernetes["decision"])

    def test_validator_rejects_recommended_paid_learning_with_stale_source(self) -> None:
        market = _recurring_market(5)
        research = _research(market, project=True, course=True)
        research["evidence_mode"] = "live"
        research["candidate_preferences"].update({"weekly_time_budget": "5 hours/week", "money_budget": "1000", "currency": "MXN"})
        as_of = date.fromisoformat(research["as_of_date"])
        for option in research["options"]:
            option["source_state"] = "active"
            if option["option_type"] != "do_nothing_now":
                option["url"] = f"https://www.python.org/dev/jobs/{option['option_id']}"
        course = next(option for option in research["options"] if option["option_type"] == "course")
        course["source_date"] = (as_of - timedelta(days=91)).isoformat()
        dossier = build_learning_dossier(market, research)
        row = next(row for row in dossier["learning_decisions"] if row["gap_signal"] == "kubernetes")
        row["decision"] = "recommended"
        self.assertIn("fresh provider source", " ".join(validate_learning_dossier(dossier)))

    def test_non_recurring_sample_cannot_produce_paid_recommendation(self) -> None:
        market_one = _recurring_market(1)
        with self.assertRaises(ValueError):
            build_learning_dossier(market_one, _research(market_one, project=False, course=True))
        for sample_size in (2, 3, 4, 5):
            with self.subTest(sample_size=sample_size):
                market = _recurring_market(sample_size)
                dossier = build_learning_dossier(market, _research(market, project=False, course=True))
                self.assertTrue(all(row["decision"] != "recommended" for row in dossier["learning_decisions"]))

    def test_builder_does_not_replace_professional_experience_with_certificate(self) -> None:
        market = _recurring_market(5)
        for card in market["vacancy_cards"]:
            card["requirements"][0]["signal"] = "production_experience"
        next(row for row in market["matrix_rows"] if row["signal"] == "terraform_iac")["signal"] = "production_experience"
        next(row for row in market["recurrence_rows"] if row["signal"] == "terraform_iac")["signal"] = "production_experience"
        market["recurrence_rows"] = sorted(market["recurrence_rows"], key=lambda row: (-row["occurrences"], row["signal"]))
        research = _research(market, project=False, course=True)
        for option in research["options"]:
            if option["gap_signal"] == "terraform_iac":
                option["gap_signal"] = "production_experience"
                option["option_type"] = "certification"
                option["option_id"] = "LO-006"
        _bind(research, market)
        dossier = build_learning_dossier(market, research)
        self.assertTrue(all(
            row["decision"] in {"project_first", "apply_with_boundary", "pause"}
            for row in dossier["learning_decisions"]
            if row["gap_signal"] == "production_experience"
        ))

    def test_builder_deep_copies_market_and_rejects_tampered_derived_values(self) -> None:
        market = _recurring_market(5)
        research = _research(market)
        original = copy.deepcopy(market)
        dossier = build_learning_dossier(market, research)
        self.assertEqual(original, market)
        self.assertEqual([], validate_market_dossier(market))
        mutated = copy.deepcopy(dossier)
        mutated["vacancy_cards"][0]["title"] = "tampered"
        self.assertTrue(validate_learning_dossier(mutated))
        mutated = copy.deepcopy(dossier)
        mutated["learning_decisions"][0]["rank"] = 99
        self.assertTrue(validate_learning_dossier(mutated))
        mutated = copy.deepcopy(dossier)
        mutated["learning_decisions"][0]["frequency_display"] = "1/1"
        self.assertTrue(validate_learning_dossier(mutated))
        mutated = copy.deepcopy(dossier)
        mutated["source_learning_research_snapshot"] = "snap-learning-sha256-" + "f" * 64
        self.assertTrue(validate_learning_dossier(mutated))

    def test_research_snapshot_must_bind_to_exact_market_snapshot(self) -> None:
        market = _recurring_market(5)
        research = _research(market)
        research["source_market_snapshot"] = "snap-market-sha256-" + "0" * 64
        with self.assertRaises(ValueError):
            build_learning_dossier(market, research)


if __name__ == "__main__":
    unittest.main()
