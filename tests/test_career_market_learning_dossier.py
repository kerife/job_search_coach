"""Contracts for the reproducible identity-free market learning dossier."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
RESEARCH_FIXTURES = ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "target-vacancy-research"
V2_FIXTURES = ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "executive-career-dossier-v2"
MARKET_FIXTURES = ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "career-market-learning-dossier"
sys.path.insert(0, str(SCRIPTS))

from build_career_market_learning_dossier import (  # noqa: E402
    _cli,
    _load_alignment,
    _write_private_json,
    build_market_dossier,
)
from validate_career_market_learning_dossier import (  # noqa: E402
    alignment_score,
    recurrence_rows,
    validate_market_dossier,
)
from validate_target_vacancy_research import snapshot_for_market_dossier  # noqa: E402
from dossier_snapshot import snapshot_for_dossier  # noqa: E402


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def valid_research(name: str = "complete-five-es.json") -> dict[str, object]:
    return load_json(RESEARCH_FIXTURES / name)


def valid_dossier(locale: str = "es") -> dict[str, object]:
    dossier = load_json(V2_FIXTURES / ("scenario-a-es.json" if locale == "es" else "scenario-c-en.json"))
    research = valid_research("complete-five-es.json" if locale == "es" else "limited-four-en.json")
    dossier["evidence_as_of"] = research["as_of_date"]
    dossier["evidence_scope"]["captured_as_of"] = research["as_of_date"]
    return dossier


def bindings_for(research: dict[str, object], dossier: dict[str, object]) -> dict[str, object]:
    signals = sorted({
        requirement["signal"]
        for vacancy in research["vacancies"]
        for requirement in vacancy["requirements"]
    })
    evidence_by_state: dict[str, list[str]] = {}
    for row in dossier["evidence"]:
        evidence_by_state.setdefault(row["state"], []).append(row["id"])
    states = ["verified_match", "candidate_reported_match", "adjacent_evidence", "explicit_gap", "unknown"]
    bindings = []
    for index, signal in enumerate(signals):
        state = states[index % len(states)]
        compatible = {
            "verified_match": evidence_by_state["verified"],
            "candidate_reported_match": evidence_by_state["candidate_reported"],
            "adjacent_evidence": evidence_by_state["verified"],
            "explicit_gap": evidence_by_state["candidate_reported"],
            "unknown": [],
        }[state]
        bindings.append({
            "signal": signal,
            "support_state": state,
            "evidence_ids": [] if state == "unknown" else [compatible[index % len(compatible)]],
        })
    return {
        "schema_version": "candidate-market-alignment-v1",
        "research_snapshot": snapshot_for_market_dossier(research),
        "executive_dossier_snapshot": snapshot_for_dossier(dossier),
        "signal_bindings": bindings,
        "privacy_boundary": "identity_free_evidence_references_only",
    }


class CareerMarketLearningDossierTests(unittest.TestCase):
    def test_builder_propagates_evidence_mode_and_enforces_mode_specific_source_domains(self) -> None:
        research = valid_research()
        dossier = valid_dossier()
        built = build_market_dossier(research, dossier, bindings_for(research, dossier))

        self.assertEqual("synthetic", built.get("evidence_mode"))

        synthetic_nonreserved = copy.deepcopy(built)
        synthetic_nonreserved["evidence_mode"] = "synthetic"
        synthetic_nonreserved["vacancy_cards"][0]["source_url"] = "https://careers.invalid.example/role"
        errors = validate_market_dossier(synthetic_nonreserved)
        self.assertIn("synthetic source URL must use a reserved domain", errors)
        self.assertNotIn("careers.invalid.example", " ".join(errors))

        live_reserved = copy.deepcopy(built)
        live_reserved["evidence_mode"] = "live"
        errors = validate_market_dossier(live_reserved)
        self.assertIn("live source URL cannot use a reserved domain", errors)
        self.assertNotIn("example.com", " ".join(errors))

    def test_market_validator_rejects_synthetic_url_policy_bypasses_and_live_future_dates(self) -> None:
        research = valid_research()
        dossier = valid_dossier()
        built = build_market_dossier(research, dossier, bindings_for(research, dossier))
        for url in (
            "https://careers.public.example/roles/123",
            "https://example.com/careers/session_id=private-marker",
            "https://example.com/careers/session%25255Fid%253Dprivate-marker",
        ):
            with self.subTest(url=url):
                value = copy.deepcopy(built)
                value["vacancy_cards"][0]["source_url"] = url
                errors = validate_market_dossier(value)
                self.assertTrue(errors)
                self.assertNotIn(url, " ".join(errors))

        live = copy.deepcopy(built)
        live["evidence_mode"] = "live"
        future = (date.today() + timedelta(days=1)).isoformat()
        live["as_of_date"] = future
        for card in live["vacancy_cards"]:
            card["source_url"] = "https://careers.public.example/roles/123"
        errors = validate_market_dossier(live)
        self.assertIn("as_of_date cannot be in the future for live evidence", errors)
        self.assertNotIn(future, " ".join(errors))

    def test_exact_integer_score_and_evidence_coverage(self) -> None:
        requirements = [
            {"signal": "a", "importance": "must_have"},
            {"signal": "b", "importance": "must_have"},
            {"signal": "c", "importance": "preferred"},
            {"signal": "d", "importance": "responsibility_only"},
        ]
        bindings = {
            "a": {"support_state": "verified_match"},
            "b": {"support_state": "adjacent_evidence"},
            "c": {"support_state": "unknown"},
            "d": {"support_state": "explicit_gap"},
        }
        self.assertEqual((6, 10, 8), alignment_score(requirements, bindings))

        bindings["c"] = {"support_state": "explicit_gap"}
        self.assertEqual((6, 10, 10), alignment_score(requirements, bindings))

    def test_recurrence_uses_actual_sample_size_and_has_no_zero_sample_rows(self) -> None:
        vacancies = [
            {"vacancy_id": f"V-00{index}", "requirements": [{"signal": "kubernetes", "importance": "must_have"}]}
            for index in range(1, 6)
        ]
        vacancies[3]["requirements"] = [{"signal": "terraform", "importance": "preferred"}]
        vacancies[4]["requirements"] = [{"signal": "terraform", "importance": "preferred"}]
        bindings = {"kubernetes": {"support_state": "verified_match", "evidence_ids": ["E-001"]}, "terraform": {"support_state": "unknown", "evidence_ids": []}}
        rows = recurrence_rows(vacancies, bindings)
        self.assertEqual("3/5", rows[0]["display_fraction"])
        self.assertEqual(5, rows[0]["sample_size"])
        self.assertEqual("3/4", recurrence_rows(vacancies[:4], bindings)[0]["display_fraction"])
        self.assertEqual([], recurrence_rows([], bindings))

    def test_builder_produces_closed_complete_limited_and_unavailable_artifacts(self) -> None:
        for research_name, expected_state, expected_count in (
            ("complete-five-es.json", "complete", 5),
            ("limited-four-en.json", "limited_market_evidence", 4),
            ("unavailable-es.json", "market_evidence_unavailable", 0),
        ):
            with self.subTest(research_name=research_name):
                research = valid_research(research_name)
                dossier = valid_dossier("en" if research["locale"] == "en" else "es")
                alignment = bindings_for(research, dossier)
                built = build_market_dossier(research, dossier, alignment)
                self.assertEqual([], validate_market_dossier(built))
                self.assertEqual(expected_state, built["state"])
                self.assertEqual(expected_count, len(built["vacancy_cards"]))
                self.assertEqual(expected_count, len({row["vacancy_id"] for row in built["vacancy_cards"]}))
                self.assertEqual([], built["recurrence_rows"] if expected_count == 0 else []) if expected_count == 0 else self.assertTrue(built["recurrence_rows"])

    def test_builder_propagates_per_vacancy_freshness_and_never_marks_unknown_publication_current(self) -> None:
        research = valid_research()
        dossier = valid_dossier()
        built = build_market_dossier(research, dossier, bindings_for(research, dossier))

        first = built["vacancy_cards"][0]
        self.assertEqual("2026-08-13", first["access_date"])
        self.assertEqual("2026-08-10", first["publication_date"])
        self.assertEqual("current", first["freshness_status"])
        self.assertEqual("publication_date", first["freshness_basis"])
        self.assertEqual(90, first["freshness_window_days"])
        self.assertEqual("publication_date_within_window", first["freshness_reason"])

        unknown_publication = copy.deepcopy(built)
        unknown_publication["vacancy_cards"][0]["publication_date"] = None
        unknown_publication["vacancy_cards"][0]["freshness_status"] = "current"
        errors = validate_market_dossier(unknown_publication)
        self.assertIn("vacancy_cards[0].freshness_status cannot be current without publication_date", errors)

    def test_builder_marks_publication_outside_window_unconfirmed(self) -> None:
        research = valid_research()
        research["vacancies"][0]["publication_date"] = "2026-04-15"
        dossier = valid_dossier()
        built = build_market_dossier(research, dossier, bindings_for(research, dossier))
        first = next(card for card in built["vacancy_cards"] if card["vacancy_id"] == "V-001")
        self.assertEqual("unknown", first["freshness_status"])
        self.assertEqual("outside_window", first["freshness_reason"])

    def test_validator_reconciles_freshness_status_basis_and_reason(self) -> None:
        research = valid_research()
        dossier = valid_dossier()
        built = build_market_dossier(research, dossier, bindings_for(research, dossier))
        mutations = (
            ("freshness_status", "unknown", "freshness_reason", "publication_date_within_window"),
            ("freshness_status", "current", "freshness_reason", "outside_window"),
            ("freshness_basis", "unknown", "freshness_reason", "publication_date_within_window"),
        )
        for field, value, companion, companion_value in mutations:
            with self.subTest(field=field):
                mutated = copy.deepcopy(built)
                mutated["vacancy_cards"][0][field] = value
                mutated["vacancy_cards"][0][companion] = companion_value
                errors = validate_market_dossier(mutated)
                self.assertTrue(any("freshness" in error for error in errors), errors)

        missing = copy.deepcopy(built)
        for card in missing["vacancy_cards"]:
            for field in ("access_date", "publication_date", "freshness_status", "freshness_basis", "freshness_window_days", "freshness_reason"):
                del card[field]
        self.assertTrue(validate_market_dossier(missing))

    def test_builder_rejects_stale_snapshot_unknown_evidence_and_state_mismatch(self) -> None:
        research = valid_research()
        dossier = valid_dossier()
        alignment = bindings_for(research, dossier)
        stale = copy.deepcopy(alignment)
        stale["research_snapshot"] = "snap-market-sha256-" + "0" * 64
        with self.assertRaises(ValueError):
            build_market_dossier(research, dossier, stale)

        unknown_evidence = copy.deepcopy(alignment)
        unknown_evidence["signal_bindings"][0]["evidence_ids"] = ["E-999"]
        with self.assertRaises(ValueError):
            build_market_dossier(research, dossier, unknown_evidence)

        mismatched = copy.deepcopy(dossier)
        mismatched["locale"] = "en"
        with self.assertRaises(ValueError):
            build_market_dossier(research, mismatched, alignment)

    def test_builder_alignment_loader_rejects_duplicate_keys_and_writer_is_private(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            duplicate = root / "duplicate.json"
            duplicate.write_text('{"signal_bindings": [], "signal_bindings": []}', encoding="utf-8")
            with self.assertRaises(ValueError):
                _load_alignment(duplicate)

            output = root / "nested" / "market.json"
            _write_private_json(output, {"schema_version": "test"})
            original = output.read_bytes()
            self.assertEqual(0o600, os.stat(output).st_mode & 0o777)
            with self.assertRaises(FileExistsError):
                _write_private_json(output, {"schema_version": "replacement"})
            self.assertEqual(original, output.read_bytes())

    def test_private_json_writer_refuses_symlinked_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            real_parent = root / "real-parent"
            real_parent.mkdir()
            linked_parent = root / "linked-parent"
            linked_parent.symlink_to(real_parent, target_is_directory=True)
            output = linked_parent / "market.json"

            with self.assertRaises(OSError):
                _write_private_json(output, {"schema_version": "test"})

            self.assertFalse((real_parent / output.name).exists())

    def test_private_json_writer_refuses_leaf_symlink_and_hardlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            for link_kind in ("symlink", "hardlink"):
                with self.subTest(link_kind=link_kind):
                    victim = root / f"{link_kind}-victim.json"
                    victim.write_text("keep\n", encoding="utf-8")
                    output = root / f"{link_kind}-output.json"
                    if link_kind == "symlink":
                        output.symlink_to(victim)
                    else:
                        os.link(victim, output)

                    with self.assertRaises(OSError):
                        _write_private_json(output, {"schema_version": "test"})

                    self.assertEqual("keep\n", victim.read_text(encoding="utf-8"))

    def test_private_json_writer_cleans_temporary_file_when_fsync_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            output = root / "private" / "market.json"

            with mock.patch(
                "build_career_market_learning_dossier.os.fsync",
                side_effect=OSError("simulated durability failure"),
            ):
                with self.assertRaises(OSError):
                    _write_private_json(output, {"schema_version": "test"})

            self.assertFalse(output.exists())
            self.assertEqual([], list(output.parent.glob(".market.json.tmp-*")))

    def test_private_json_writer_preserves_racing_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            output = root / "market.json"

            def create_competing_target(*_args: object, **_kwargs: object) -> None:
                output.write_text("prior\n", encoding="utf-8")
                raise FileExistsError("simulated competing writer")

            with mock.patch(
                "build_career_market_learning_dossier.os.link",
                side_effect=create_competing_target,
            ):
                with self.assertRaises(FileExistsError):
                    _write_private_json(output, {"schema_version": "test"})

            self.assertEqual("prior\n", output.read_text(encoding="utf-8"))
            self.assertEqual([], list(root.glob(".market.json.tmp-*")))

    def test_builder_cli_uses_private_json_writer_for_valid_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            research = valid_research()
            dossier = valid_dossier()
            alignment = bindings_for(research, dossier)
            research_path = root / "research.json"
            dossier_path = root / "dossier.json"
            alignment_path = root / "alignment.json"
            output = root / "private" / "market.json"
            for path, value in (
                (research_path, research),
                (dossier_path, dossier),
                (alignment_path, alignment),
            ):
                path.write_text(json.dumps(value), encoding="utf-8")

            exit_code = _cli([
                str(research_path),
                str(dossier_path),
                str(alignment_path),
                "--output",
                str(output),
            ])

            self.assertEqual(0, exit_code)
            self.assertEqual([], validate_market_dossier(load_json(output)))
            self.assertEqual(0o600, os.stat(output).st_mode & 0o777)

    def test_builder_cli_does_not_write_output_rejected_by_final_validator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            research = valid_research()
            dossier = valid_dossier()
            alignment = bindings_for(research, dossier)
            research_path = root / "research.json"
            dossier_path = root / "dossier.json"
            alignment_path = root / "alignment.json"
            output = root / "private" / "market.json"
            for path, value in (
                (research_path, research),
                (dossier_path, dossier),
                (alignment_path, alignment),
            ):
                path.write_text(json.dumps(value), encoding="utf-8")

            with mock.patch(
                "build_career_market_learning_dossier.OUTPUT.validate_market_dossier",
                return_value=["derived output is invalid"],
            ):
                exit_code = _cli([
                    str(research_path), str(dossier_path), str(alignment_path),
                    "--output", str(output),
                ])

            self.assertEqual(2, exit_code)
            self.assertFalse(output.exists())

    def test_builder_rejects_inferred_or_unknown_evidence_for_explicit_gap(self) -> None:
        research = valid_research()
        dossier = valid_dossier()
        alignment = bindings_for(research, dossier)
        gap = next(row for row in alignment["signal_bindings"] if row["support_state"] == "explicit_gap")
        gap["evidence_ids"] = ["E-003"]
        dossier["evidence"] = [row for row in dossier["evidence"] if row["id"] != "E-003"]
        with self.assertRaises(ValueError):
            build_market_dossier(research, dossier, alignment)

    def test_validator_rejects_calculation_order_and_private_mutations_without_echo(self) -> None:
        research = valid_research()
        dossier = valid_dossier()
        built = build_market_dossier(research, dossier, bindings_for(research, dossier))
        mutations = []
        score = copy.deepcopy(built)
        score["vacancy_cards"][0]["earned_points"] += 1
        mutations.append(score)
        order = copy.deepcopy(built)
        order["vacancy_cards"].reverse()
        mutations.append(order)
        private = copy.deepcopy(built)
        private["vacancy_cards"][0]["title"] = "<script>DO-NOT-ECHO</script>"
        mutations.append(private)
        for value in mutations:
            errors = validate_market_dossier(value)
            self.assertTrue(errors)
            self.assertNotIn("DO-NOT-ECHO", " ".join(errors))

    def test_validator_rejects_private_or_misclassified_source_urls(self) -> None:
        research = valid_research()
        dossier = valid_dossier()
        built = build_market_dossier(research, dossier, bindings_for(research, dossier))
        for url, kind in (
            ("http://example.com/careers/a", "official_employer"),
            ("https://127.0.0.1/careers/a", "official_employer"),
            ("https://user:pass@example.com/careers/a", "official_employer"),
            ("https://www.linkedin.com/not-jobs/123", "linkedin_jobs_backup"),
            ("https://example.com/careers/a", "linkedin_jobs_backup"),
        ):
            mutated = copy.deepcopy(built)
            mutated["vacancy_cards"][0]["source_url"] = url
            mutated["vacancy_cards"][0]["source_kind"] = kind
            with self.subTest(url=url, kind=kind):
                self.assertTrue(validate_market_dossier(mutated))

    def test_validator_rejects_non_iso_evidence_date(self) -> None:
        value = load_json(MARKET_FIXTURES / "complete-five-es.json")
        value["as_of_date"] = "not-a-date"

        self.assertIn("as_of_date must be an ISO date", validate_market_dossier(value))

    def test_fixture_outputs_are_reproducible_and_closed(self) -> None:
        fixtures = sorted(MARKET_FIXTURES.glob("*.json"))
        self.assertEqual(
            ["complete-five-es.json", "limited-four-en.json", "unavailable-es.json"],
            [path.name for path in fixtures],
        )
        for path in fixtures:
            value = load_json(path)
            self.assertEqual([], validate_market_dossier(value), path.name)
            self.assertNotIn("source_paraphrase", json.dumps(value, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
