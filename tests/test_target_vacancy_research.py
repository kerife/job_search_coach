"""Contract tests for the identity-free current vacancy research artifact."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
FIXTURES = ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "target-vacancy-research"
sys.path.insert(0, str(SCRIPTS))

from validate_target_vacancy_research import (  # noqa: E402
    MAX_INPUT_BYTES,
    canonical_research_snapshot,
    load_research,
    source_url_policy_error,
    snapshot_for_market_dossier,
    validate_research,
)


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class TargetVacancyResearchTests(unittest.TestCase):
    def test_synthetic_evidence_mode_keeps_shipped_fixture_contract_valid(self) -> None:
        value = load_fixture("complete-five-es.json")
        value["evidence_mode"] = "synthetic"

        self.assertEqual([], validate_research(value))

    def test_live_evidence_rejects_reserved_domains_without_echoing_them(self) -> None:
        value = load_fixture("complete-five-es.json")
        value["evidence_mode"] = "live"

        errors = validate_research(value)

        self.assertIn("live evidence cannot use a reserved source domain", errors)
        self.assertNotIn("example.com", " ".join(errors))

    def test_live_evidence_rejects_future_dates_without_echoing_them(self) -> None:
        value = load_fixture("complete-five-es.json")
        value["evidence_mode"] = "live"
        future = (date.today() + timedelta(days=1)).isoformat()
        value["as_of_date"] = future

        errors = validate_research(value)

        self.assertIn("as_of_date cannot be in the future for live evidence", errors)
        self.assertNotIn(future, " ".join(errors))

    def test_synthetic_source_urls_reject_public_domains_and_session_path_material(self) -> None:
        source = load_fixture("complete-five-es.json")
        for url in (
            "https://careers.public.example/roles/123",
            "https://example.com/careers/session_id=private-marker",
            "https://example.com/careers/session%25255Fid%253Dprivate-marker",
        ):
            with self.subTest(url=url):
                value = copy.deepcopy(source)
                value["vacancies"][0]["source_url"] = url

                errors = validate_research(value)

                self.assertTrue(errors)
                self.assertNotIn(url, " ".join(errors))

    def test_observation_text_rejects_urls_contacts_and_session_identifiers_without_echo(self) -> None:
        source = load_fixture("complete-five-es.json")
        mutations = (
            ("qualification_observation", "See https://private.invalid/role", "employers[0].qualification_observation"),
            ("observed_condition", "Call +52 55 1234 5678", "vacancies[0].eligibility_gates[0].observed_condition"),
            ("source_paraphrase", "session_id=private-marker", "vacancies[0].requirements[0].source_paraphrase"),
        )
        for field, restricted_text, path in mutations:
            with self.subTest(field=field):
                value = copy.deepcopy(source)
                value["evidence_mode"] = "synthetic"
                if field == "qualification_observation":
                    value["employers"][0][field] = restricted_text
                elif field == "observed_condition":
                    value["vacancies"][0]["eligibility_gates"][0][field] = restricted_text
                else:
                    value["vacancies"][0]["requirements"][0][field] = restricted_text

                errors = validate_research(value)

                self.assertIn(f"{path} contains restricted observation data", errors)
                self.assertNotIn(restricted_text, " ".join(errors))

    def test_supported_states_have_exact_bounded_counts(self) -> None:
        expected = {
            "complete-five-es.json": ("complete", 5),
            "limited-four-en.json": ("limited_market_evidence", 4),
            "unavailable-es.json": ("market_evidence_unavailable", 0),
        }
        for filename, (state, count) in expected.items():
            with self.subTest(filename=filename):
                value = load_fixture(filename)
                self.assertEqual([], validate_research(value))
                self.assertEqual(state, value["state"])
                self.assertEqual(count, len(value["vacancies"]))
                self.assertEqual(count, len({row["vacancy_id"] for row in value["vacancies"]}))
                self.assertEqual(
                    count,
                    len({row["duplicate_fingerprint"] for row in value["vacancies"]}),
                )
                self.assertTrue(
                    all(row["access_date"] == value["as_of_date"] for row in value["vacancies"])
                )

    def test_snapshot_is_typed_and_deterministic(self) -> None:
        value = load_fixture("complete-five-es.json")
        first = canonical_research_snapshot(value)
        second = canonical_research_snapshot(copy.deepcopy(value))
        self.assertRegex(first, r"^[0-9a-f]{64}$")
        self.assertEqual(first, second)
        self.assertEqual(f"snap-market-sha256-{first}", snapshot_for_market_dossier(value))

    def test_limited_state_rejects_five_and_complete_requires_five(self) -> None:
        limited = load_fixture("limited-four-en.json")
        limited["vacancies"].append(copy.deepcopy(limited["vacancies"][-1]))
        limited["vacancies"][-1]["vacancy_id"] = "V-005"
        limited["vacancies"][-1]["duplicate_fingerprint"] = "fp-005"
        limited["vacancies"][-1]["employer_id"] = "EMP-005"
        self.assertIn("state/count coupling is invalid", validate_research(limited))

        complete = load_fixture("complete-five-es.json")
        complete["vacancies"] = complete["vacancies"][:4]
        self.assertIn("state/count coupling is invalid", validate_research(complete))

    def test_duplicate_ids_fingerprints_requirements_and_signals_fail(self) -> None:
        source = load_fixture("complete-five-es.json")
        mutations = []

        duplicate_id = copy.deepcopy(source)
        duplicate_id["vacancies"][1]["vacancy_id"] = duplicate_id["vacancies"][0]["vacancy_id"]
        mutations.append(duplicate_id)

        duplicate_fingerprint = copy.deepcopy(source)
        duplicate_fingerprint["vacancies"][1]["duplicate_fingerprint"] = duplicate_fingerprint["vacancies"][0]["duplicate_fingerprint"]
        mutations.append(duplicate_fingerprint)

        duplicate_requirement_id = copy.deepcopy(source)
        duplicate_requirement_id["vacancies"][0]["requirements"][1]["requirement_id"] = duplicate_requirement_id["vacancies"][0]["requirements"][0]["requirement_id"]
        mutations.append(duplicate_requirement_id)

        duplicate_signal = copy.deepcopy(source)
        duplicate_signal["vacancies"][0]["requirements"][1]["signal"] = duplicate_signal["vacancies"][0]["requirements"][0]["signal"]
        mutations.append(duplicate_signal)

        for value in mutations:
            with self.subTest(value=value):
                self.assertTrue(validate_research(value))

    def test_duplicate_source_urls_fail_even_when_ids_and_fingerprints_differ(self) -> None:
        value = load_fixture("complete-five-es.json")
        value["vacancies"][1]["source_url"] = value["vacancies"][0]["source_url"]

        errors = validate_research(value)

        self.assertIn("duplicate vacancy source URL", " ".join(errors))

    def test_duplicate_employer_source_urls_fail_even_when_ids_differ(self) -> None:
        value = load_fixture("complete-five-es.json")
        value["employers"][1]["official_source_url"] = value["employers"][0]["official_source_url"]

        errors = validate_research(value)

        self.assertIn("duplicate employer source URL", " ".join(errors))

    def test_repeated_employer_requires_exhaustion_and_distinct_postings(self) -> None:
        value = load_fixture("complete-five-es.json")
        value["vacancies"][1]["employer_id"] = value["vacancies"][0]["employer_id"]
        self.assertIn("repeated employer requires exhausted search", validate_research(value))

        value["search_limit"]["distinct_employer_search_exhausted"] = True
        self.assertEqual([], validate_research(value))

        same_posting = copy.deepcopy(value)
        same_posting["vacancies"][1]["duplicate_fingerprint"] = same_posting["vacancies"][0]["duplicate_fingerprint"]
        self.assertIn("duplicate vacancy fingerprint", validate_research(same_posting))

    def test_active_date_and_target_limit_invariants_fail_closed(self) -> None:
        source = load_fixture("complete-five-es.json")
        cases = []

        inactive = copy.deepcopy(source)
        inactive["vacancies"][0]["source_state"] = "expired"
        cases.append(inactive)

        mismatched_access = copy.deepcopy(source)
        mismatched_access["vacancies"][0]["access_date"] = "2026-08-12"
        cases.append(mismatched_access)

        future_publication = copy.deepcopy(source)
        future_publication["vacancies"][0]["publication_date"] = "2026-08-14"
        cases.append(future_publication)

        target_short = copy.deepcopy(source)
        target_short["vacancies"] = target_short["vacancies"][:4]
        target_short["search_limit"]["limitation"] = "none"
        cases.append(target_short)

        for value in cases:
            with self.subTest(value=value):
                self.assertTrue(validate_research(value))

    def test_source_kind_hostname_and_scheme_rules_are_enforced(self) -> None:
        source = load_fixture("complete-five-es.json")
        cases = (
            ("http://example.com/careers/a", "official_employer"),
            ("https://www.linkedin.com/jobs/view/123", "official_employer"),
            ("https://example.com/careers/a", "linkedin_jobs_backup"),
            ("https://www.linkedin.com/not-jobs/123", "linkedin_jobs_backup"),
        )
        for url, kind in cases:
            with self.subTest(url=url, kind=kind):
                value = copy.deepcopy(source)
                value["vacancies"][0]["source_url"] = url
                value["vacancies"][0]["source_kind"] = kind
                self.assertTrue(validate_research(value))

    def test_linkedin_backup_rejects_private_url_metadata_and_nonstandard_port(self) -> None:
        source = load_fixture("complete-five-es.json")
        urls = (
            "https://synthetic-user:private-marker@www.linkedin.com/jobs/view/123",
            "https://www.linkedin.com/jobs/view/123?access_token=private-marker",
            "https://www.linkedin.com/jobs/view/123#private-marker",
            "https://www.linkedin.com:8443/jobs/view/123",
        )
        for url in urls:
            with self.subTest(url=url):
                value = copy.deepcopy(source)
                value["vacancies"][0]["source_url"] = url
                value["vacancies"][0]["source_kind"] = "linkedin_jobs_backup"
                errors = validate_research(value)
                self.assertTrue(errors)
                self.assertNotIn("private-marker", " ".join(errors))

    def test_linkedin_backup_rejects_encoded_path_traversal(self) -> None:
        error = source_url_policy_error(
            "https://www.linkedin.com/jobs/%2e%2e/in/example",
            source_kind="linkedin_jobs_backup",
            evidence_mode="live",
        )

        self.assertEqual("source URL contains path traversal", error)

    def test_unknown_eligibility_cannot_contain_inferred_pass(self) -> None:
        value = load_fixture("complete-five-es.json")
        value["vacancies"][0]["eligibility_gates"][0] = {
            "gate": "work_authorization",
            "state": "unknown",
            "observed_condition": "Candidate is eligible to work in Mexico",
        }
        errors = validate_research(value)
        self.assertIn("unknown eligibility gate contains an inferred conclusion", errors)
        self.assertNotIn("Candidate is eligible", " ".join(errors))

    def test_closed_fields_and_raw_markup_are_rejected_without_echo(self) -> None:
        source = load_fixture("complete-five-es.json")
        extra = copy.deepcopy(source)
        extra["private_candidate_key"] = "DO-NOT-ECHO"
        errors = validate_research(extra)
        self.assertIn("research artifact has unsupported fields", errors)
        self.assertNotIn("DO-NOT-ECHO", " ".join(errors))

        raw_markup = copy.deepcopy(source)
        raw_markup["vacancies"][0]["title"] = "<script>alert(1)</script>"
        self.assertTrue(validate_research(raw_markup))
        self.assertNotIn("<script>", " ".join(validate_research(raw_markup)))

    def test_loader_is_bounded_and_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "research.json"
            path.write_text('{"schema_version":"x","schema_version":"y"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_research(path)

            path.write_bytes(b"{}")
            self.assertEqual({}, load_research(path))

            path.write_bytes(b"{}" + b" " * (MAX_INPUT_BYTES + 1))
            with self.assertRaises(ValueError):
                load_research(path)


if __name__ == "__main__":
    unittest.main()
