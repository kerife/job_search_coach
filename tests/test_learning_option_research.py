"""Contract tests for identity-free learning-option research."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
FIXTURES = ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "learning-option-research"
sys.path.insert(0, str(SCRIPTS))

from validate_learning_option_research import (  # noqa: E402
    MAX_INPUT_BYTES,
    load_research,
    snapshot_for_learning_research,
    validate_research,
)


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class LearningOptionResearchTests(unittest.TestCase):
    def test_synthetic_fixtures_are_closed_and_identity_free(self) -> None:
        for filename, expected_count in (
            ("complete-five-es.json", 5),
            ("limited-four-en.json", 4),
        ):
            with self.subTest(filename=filename):
                value = load_fixture(filename)
                self.assertEqual([], validate_research(value))
                self.assertEqual(expected_count, len(value["options"]))
                self.assertEqual("synthetic", {row["source_state"] for row in value["options"]}.pop())
                self.assertTrue(all(str(row["url"] or "").startswith("https://example.com/") or row["url"] is None for row in value["options"]))
                self.assertFalse(value["candidate_preferences"]["purchase_authorized"])

    def test_snapshot_is_typed_and_deterministic(self) -> None:
        value = load_fixture("complete-five-es.json")
        snapshot = snapshot_for_learning_research(value)
        self.assertRegex(snapshot, r"^snap-learning-sha256-[0-9a-f]{64}$")
        self.assertEqual(snapshot, snapshot_for_learning_research(copy.deepcopy(value)))

    def test_option_urls_and_purchase_authorization_fail_closed(self) -> None:
        source = load_fixture("complete-five-es.json")
        unsafe = copy.deepcopy(source)
        unsafe["options"][0]["url"] = "http://127.0.0.1/private"
        self.assertTrue(validate_research(unsafe))

        purchased = copy.deepcopy(source)
        purchased["candidate_preferences"]["purchase_authorized"] = True
        self.assertIn("candidate_preferences.purchase_authorized must be false", validate_research(purchased))

    def test_candidate_project_requires_private_publication_gates(self) -> None:
        source = load_fixture("complete-five-es.json")
        project = next(row for row in source["options"] if row["option_type"] == "candidate_owned_project")
        project["action_gate"]["confidentiality_review"] = "not_required"
        self.assertIn("candidate project requires confidentiality review", validate_research(source))

    def test_do_nothing_rows_cannot_claim_provider_commercial_details(self) -> None:
        source = load_fixture("complete-five-es.json")
        do_nothing = next(row for row in source["options"] if row["option_type"] == "do_nothing_now")
        do_nothing["provider"] = "Fixture Vendor"
        self.assertIn("do_nothing_now option has invalid provider fields", validate_research(source))

    def test_loader_rejects_duplicate_keys_and_oversize_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "research.json"
            path.write_text('{"schema_version":"x","schema_version":"y"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_research(path)
            path.write_bytes(b"{}" + b" " * (MAX_INPUT_BYTES + 1))
            with self.assertRaises(ValueError):
                load_research(path)

    def test_research_rejects_duplicate_urls_and_non_current_sources(self) -> None:
        source = load_fixture("complete-five-es.json")
        duplicate = copy.deepcopy(source)
        duplicate["options"][1]["url"] = duplicate["options"][0]["url"]
        self.assertIn("duplicate source URLs", " ".join(validate_research(duplicate)))
        stale = copy.deepcopy(source)
        stale["options"][0]["source_state"] = "stale"
        self.assertTrue(validate_research(stale))

    def test_research_rejects_unsafe_commercial_and_geography_claims(self) -> None:
        source = load_fixture("complete-five-es.json")
        project = copy.deepcopy(source)
        project["options"][0]["current_cost"] = "100"
        self.assertTrue(validate_research(project))
        course = copy.deepcopy(source)
        course["options"][2]["current_cost"] = "100"
        self.assertIn("paid cost requires currency and tax", " ".join(validate_research(course)))
        online = copy.deepcopy(source)
        online["options"][2]["availability"] = "online"
        online["options"][2]["geography"] = "Mexico"
        self.assertIn("Mexico eligibility", " ".join(validate_research(online)))

    def test_research_rejects_credential_and_numeric_ip_urls(self) -> None:
        source = load_fixture("complete-five-es.json")
        for url in ("https://@example.org/x", "https://2130706433/x", "https://0177.0.0.1/x", "https://0x7f.0.0.1/x", "https://127.1/x"):
            unsafe = copy.deepcopy(source)
            unsafe["options"][0]["url"] = url
            self.assertTrue(validate_research(unsafe), url)

    def test_duration_basis_is_closed(self) -> None:
        source = load_fixture("complete-five-es.json")
        source["options"][2]["duration_basis"] = "garbage"
        self.assertIn("duration_basis", " ".join(validate_research(source)))

    def test_synthetic_sources_and_dates_cannot_impersonate_live_evidence(self) -> None:
        source = load_fixture("complete-five-es.json")
        source["options"][0]["url"] = "https://provider.example.org/course"
        self.assertTrue(validate_research(source))
        future = load_fixture("complete-five-es.json")
        future["as_of_date"] = "2099-01-01"
        self.assertIn("future", " ".join(validate_research(future)))
        active_fixture = load_fixture("complete-five-es.json")
        active_fixture["options"][0]["source_state"] = "active"
        self.assertTrue(validate_research(active_fixture))


if __name__ == "__main__":
    unittest.main()
