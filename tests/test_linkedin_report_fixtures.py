"""Behavioral contract for privacy-safe LinkedIn report fixture bundles."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "plugins" / "job-search-coach" / "scripts" / "validate_linkedin_client_report.py"
SOURCE_REGISTRY_PATH = REPO_ROOT / "plugins" / "job-search-coach" / "scripts" / "linkedin_source_registry.json"
FIXTURE_ROOT = REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "linkedin-report-v2"

specification = importlib.util.spec_from_file_location("validate_linkedin_client_report", VALIDATOR_PATH)
assert specification is not None and specification.loader is not None
validator = importlib.util.module_from_spec(specification)
specification.loader.exec_module(validator)


class LinkedInReportFixtureTests(unittest.TestCase):
    def fixture(self, name: str) -> dict[str, object]:
        return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))

    def errors_after(self, path: tuple[object, ...], key: str, value: object) -> list[str]:
        bundle = self.fixture("scenario-a.json")
        target: object = bundle
        for part in path:
            target = target[part]  # type: ignore[index]
        self.assertIsInstance(target, dict)
        target[key] = value  # type: ignore[index]
        return validator.validate_fixture_bundle(bundle)

    def test_all_four_fixture_bundles_are_valid(self) -> None:
        paths = sorted(FIXTURE_ROOT.glob("scenario-[abcd].json"))
        self.assertEqual(4, len(paths))
        for path in paths:
            with self.subTest(path=path.name):
                self.assertEqual([], validator.validate_fixture_bundle(json.loads(path.read_text())))

    def test_banner_only_variant_is_valid_and_has_its_own_ids(self) -> None:
        primary = [self.fixture(path.name) for path in FIXTURE_ROOT.glob("scenario-[abcd].json")]
        variant = self.fixture("scenario-d-banner-only.json")
        self.assertEqual([], validator.validate_fixture_bundle(variant))
        self.assertNotIn(variant["fixture_id"], {item["fixture_id"] for item in primary})
        self.assertNotIn(variant["internal_candidate_id"], {item["internal_candidate_id"] for item in primary})

    def test_all_five_bundles_have_distinct_fixture_and_candidate_ids(self) -> None:
        bundles = [self.fixture(path.name) for path in FIXTURE_ROOT.glob("scenario-*.json")]
        self.assertEqual(5, len(bundles))
        self.assertEqual(5, len({item["fixture_id"] for item in bundles}))
        self.assertEqual(5, len({item["internal_candidate_id"] for item in bundles}))

    def test_all_fixture_and_report_identifiers_use_the_reserved_discriminator(self) -> None:
        identifier = re.compile(
            r"\b(?:FIXTURE|CANDIDATE|EVID|FACT|SOURCE|PRIORITY|COPY)-"
            r"([A-Z0-9]+)-[A-Z0-9]+(?:-[A-Z0-9]+)*\b",
            re.I,
        )
        paths = sorted(FIXTURE_ROOT.glob("scenario-*.*"))
        occurrences = []
        invalid = []
        for path in paths:
            for match in identifier.finditer(path.read_text(encoding="utf-8")):
                occurrences.append((path.name, match.group(0)))
                if re.fullmatch(r"JSC[0-9]+", match.group(1), re.I) is None:
                    invalid.append((path.name, match.group(0)))

        self.assertTrue(occurrences)
        self.assertEqual([], invalid)

    def test_fixture_authorization_state_is_closed_and_not_executed(self) -> None:
        bundle = self.fixture("scenario-a.json")
        self.assertEqual(
            "not_executed",
            bundle["authorization_state"].get("action_state"),
        )
        bundle["authorization_state"].pop("action_state")
        self.assertIn(
            "authorization_state has missing field: action_state",
            validator.validate_fixture_bundle(bundle),
        )

    def test_load_bundle_reads_a_json_object(self) -> None:
        bundle = validator.load_bundle(FIXTURE_ROOT / "scenario-a.json")
        self.assertEqual("FIXTURE-JSC1-TECHNICAL-SIGNAL-DISPERSED", bundle["fixture_id"])

    def test_official_source_registry_matches_the_eight_reviewed_locators(self) -> None:
        self.assertTrue(SOURCE_REGISTRY_PATH.is_file())
        registry = json.loads(SOURCE_REGISTRY_PATH.read_text(encoding="utf-8"))
        expected = {
            "good_profile": "/help/linkedin/answer/a554351",
            "profile_photo": "/help/linkedin/answer/a541850",
            "cover_image": "/help/linkedin/answer/a1377087",
            "featured_section": "/help/linkedin/answer/a552452",
            "skills": "/help/linkedin/answer/a549047",
            "job_match": "/help/linkedin/answer/a8078207",
            "job_seeker_hirer_connection": "/help/linkedin/answer/a7134286",
            "ai_hiring_agents": "/help/linkedin/answer/a7437598",
        }
        self.assertEqual("linkedin-source-registry-1", registry["registry_version"])
        self.assertEqual(set(validator.SOURCE_CATEGORIES), set(registry["official_categories"]))
        self.assertEqual(set(expected), set(registry["official_categories"]))
        for category, path_prefix in expected.items():
            with self.subTest(category=category):
                self.assertEqual(
                    [{"host": "www.linkedin.com", "path_prefix": path_prefix}],
                    registry["official_categories"][category],
                )

    def test_registry_schema_and_executable_source_categories_stay_in_lockstep(self) -> None:
        self.assertTrue(SOURCE_REGISTRY_PATH.is_file())
        registry = json.loads(SOURCE_REGISTRY_PATH.read_text(encoding="utf-8"))
        schema = self.fixture("schema.json")
        schema_categories = set(
            schema["$defs"]["source"]["properties"]["source_category"]["enum"]
        )
        registered_categories = set(registry["official_categories"])
        self.assertEqual(set(validator.SOURCE_CATEGORIES), schema_categories)
        self.assertEqual(schema_categories, registered_categories)
        self.assertEqual(8, len(registered_categories))
        for category, locators in registry["official_categories"].items():
            with self.subTest(category=category):
                self.assertTrue(locators)
                for locator in locators:
                    self.assertEqual({"host", "path_prefix"}, set(locator))
                    self.assertEqual(locator["host"], locator["host"].lower())
                    self.assertFalse(locator["host"].endswith("."))
                    self.assertTrue(locator["path_prefix"].startswith("/"))

        source_schema = schema["$defs"]["source"]
        self.assertEqual(set(validator.SOURCE_FIELDS), set(source_schema["properties"]))
        self.assertEqual(
            set(validator.SOURCE_REQUIRED_FIELDS),
            set(source_schema["required"]),
        )
        secondary_requirement = source_schema["allOf"][0]
        self.assertEqual(
            {"publisher", "document_title"},
            set(secondary_requirement["then"]["required"]),
        )
        self.assertEqual(120, source_schema["properties"]["publisher"]["maxLength"])
        self.assertEqual(240, source_schema["properties"]["document_title"]["maxLength"])
        provenance_line_pattern = (
            r"^[^\n\r\u000B\u000C\u001C-\u001E\u0085\u2028\u2029]+$"
        )
        for field in ("publisher", "document_title"):
            self.assertEqual(
                provenance_line_pattern,
                source_schema["properties"][field]["pattern"],
            )

        source_catalog_schema = schema["properties"]["source_catalog"]
        self.assertEqual(8, source_catalog_schema.get("minItems"))
        official_requirements = source_catalog_schema.get("allOf", [])
        self.assertEqual(8, len(official_requirements))
        required_categories = set()
        for requirement in official_requirements:
            self.assertEqual(1, requirement.get("minContains"))
            self.assertEqual(1, requirement.get("maxContains"))
            contains = requirement.get("contains", {})
            self.assertEqual(
                {"source_class", "source_category"},
                set(contains.get("required", [])),
            )
            properties = contains.get("properties", {})
            self.assertEqual("official", properties.get("source_class", {}).get("const"))
            required_categories.add(
                properties.get("source_category", {}).get("const")
            )
        self.assertEqual(set(validator.SOURCE_CATEGORIES), required_categories)

    def test_source_registry_loader_fails_closed_for_missing_or_malformed_files(self) -> None:
        self.assertTrue(hasattr(validator, "_load_source_registry"))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missing = root / "missing.json"
            malformed = root / "malformed.json"
            malformed.write_text('{"registry_version":', encoding="utf-8")
            for path in (missing, malformed):
                with self.subTest(path=path.name), self.assertRaisesRegex(
                    ValueError,
                    "LinkedIn source registry is missing or malformed",
                ):
                    validator._load_source_registry(path)

    def test_source_registry_loader_rejects_duplicate_json_keys_and_locators(self) -> None:
        registry_text = SOURCE_REGISTRY_PATH.read_text(encoding="utf-8")
        duplicate_key_text = registry_text.replace(
            '"registry_version": "linkedin-source-registry-1",',
            '"registry_version": "linkedin-source-registry-1",\n'
            '  "registry_version": "linkedin-source-registry-1",',
            1,
        )
        duplicate_locator = json.loads(registry_text)
        duplicate_locator["official_categories"]["good_profile"].append(
            copy.deepcopy(
                duplicate_locator["official_categories"]["good_profile"][0]
            )
        )
        cross_category_duplicate = json.loads(registry_text)
        cross_category_duplicate["official_categories"]["ai_hiring_agents"] = [
            copy.deepcopy(
                cross_category_duplicate["official_categories"]["good_profile"][0]
            )
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cases = {
                "duplicate-key.json": duplicate_key_text,
                "duplicate-locator.json": json.dumps(duplicate_locator),
                "cross-category-duplicate.json": json.dumps(cross_category_duplicate),
            }
            for name, content in cases.items():
                path = root / name
                path.write_text(content, encoding="utf-8")
                with self.subTest(name=name), self.assertRaisesRegex(
                    ValueError,
                    "LinkedIn source registry is missing or malformed",
                ):
                    validator._load_source_registry(path)

    def test_all_five_fixtures_use_registered_category_locators_and_provenance(self) -> None:
        self.assertTrue(hasattr(validator, "_is_registered_official_source"))
        for path in sorted(FIXTURE_ROOT.glob("scenario-*.json")):
            bundle = self.fixture(path.name)
            with self.subTest(path=path.name):
                self.assertEqual(8, len(bundle["source_catalog"]))
                for source in bundle["source_catalog"]:
                    self.assertEqual("official", source["source_class"])
                    self.assertTrue(source["publisher"].strip())
                    self.assertTrue(source["document_title"].strip())
                    self.assertTrue(
                        validator._is_registered_official_source(
                            source["source_category"], source["url"]
                        )
                    )
                ai_source = next(
                    source
                    for source in bundle["source_catalog"]
                    if source["source_category"] == "ai_hiring_agents"
                )
                self.assertEqual(
                    "https://www.linkedin.com/help/linkedin/answer/a7437598",
                    ai_source["url"],
                )
                self.assertEqual(
                    "How LinkedIn uses AI Agents to connect job seekers and hirers",
                    ai_source["document_title"],
                )

    def test_fixture_rejects_non_object_input(self) -> None:
        self.assertEqual(["fixture must be a JSON object"], validator.validate_fixture_bundle(["synthetic-sentinel"]))

    def test_fixture_rejects_unknown_property(self) -> None:
        bundle = self.fixture("scenario-a.json")
        bundle["profile_name"] = "Synthetic Person"
        self.assertIn("fixture has unsupported field: profile_name", validator.validate_fixture_bundle(bundle))

    def test_fixture_rejects_profile_derived_private_field(self) -> None:
        errors = self.errors_after(("structural_state_fixture",), "profile_url", "https://www.linkedin.com/in/synthetic-sentinel/")
        self.assertIn("structural_state_fixture has unsupported field: profile_url", errors)

    def test_fixture_rejects_image_ocr_and_fingerprint_fields(self) -> None:
        for field in ("image", "screenshot", "ocr", "hash", "embedding"):
            with self.subTest(field=field):
                errors = self.errors_after(("structural_state_fixture",), field, "SENTINEL")
                self.assertIn(f"structural_state_fixture has unsupported field: {field}", errors)

    def test_fixture_rejects_raw_analytics_social_and_literal_profile_fields(self) -> None:
        fields = ("raw_text", "analytics_value", "connection_count", "follower_count", "employer", "location", "employment_date")
        for field in fields:
            with self.subTest(field=field):
                errors = self.errors_after(("structural_state_fixture",), field, "SENTINEL")
                self.assertIn(f"structural_state_fixture has unsupported field: {field}", errors)

    def test_privacy_scanner_rejects_email_and_phone_in_allowed_fields(self) -> None:
        cases = (("fixture_id", "person@example.invalid", "email-like"), ("internal_candidate_id", "+1 202 555 0199", "phone-like"))
        for field, value, kind in cases:
            with self.subTest(field=field):
                bundle = self.fixture("scenario-a.json")
                bundle[field] = value
                self.assertIn(f"fixture contains forbidden {kind} value at {field}", validator.validate_fixture_bundle(bundle))

    def test_source_url_cannot_bypass_profile_contact_or_local_path_privacy(self) -> None:
        cases = (
            ("https://www.linkedin.com/in/synthetic-sentinel/", "LinkedIn profile URL"),
            ("mailto:person@example.invalid", "email-like"),
            ("tel:+1 202 555 0199", "phone-like"),
            ("tel:+525512345678", "phone-like"),
            ("tel:+52-55-1234-5678", "phone-like"),
            ("tel:+52.55.1234.5678", "phone-like"),
            ("TEL:+52(55)1234 5678", "phone-like"),
            ("/Users/synthetic-sentinel/source.html", "local-path"),
            ("file:///Users/synthetic-sentinel/source.html", "local-path"),
            ("file:///home/synthetic-sentinel/source.html", "local-path"),
            (r"C:\Users\synthetic-sentinel\source.html", "local-path"),
            ("file:///C:/Users/synthetic-sentinel/source.html", "local-path"),
            ("file:///%55sers/synthetic-sentinel/source.html", "local-path"),
            ("FILE:///%55sers/synthetic-sentinel/source.html", "local-path"),
        )
        for value, kind in cases:
            with self.subTest(kind=kind):
                bundle = self.fixture("scenario-a.json")
                bundle["source_catalog"][0]["url"] = value
                self.assertIn(
                    f"fixture contains forbidden {kind} value at source_catalog[0].url",
                    validator.validate_fixture_bundle(bundle),
                )

    def test_fixture_requires_non_mapping_profile_origin(self) -> None:
        bundle = self.fixture("scenario-a.json")
        bundle["real_profile_mapping"] = "mapping_retained"
        self.assertIn("fixture must use real_profile_mapping=none_created", validator.validate_fixture_bundle(bundle))

    def test_fixture_rejects_unknown_top_level_and_nested_enums(self) -> None:
        mutations = (
            (("locale",), "fr", "fixture has invalid locale"),
            (("evidence_mode",), "visual_guess", "fixture has invalid evidence_mode"),
            (("synthetic_fact_catalog", 0, "capability_family"), "quantum", "synthetic_fact_catalog[0] has invalid capability_family"),
            (("priorities", 0, "action_type"), "improve_profile", "priorities[0] has invalid action_type"),
            (("copy_blocks", 0, "state"), "published", "copy_blocks[0] has invalid state"),
            (("authorization_state", "external_actions"), "implied", "authorization_state has invalid external_actions"),
            (("eval_expectations", "pending_evidence_policy"), "ASK_FOR_EVERYTHING", "eval_expectations has invalid pending_evidence_policy"),
        )
        for path, value, expected in mutations:
            with self.subTest(path=path):
                bundle = self.fixture("scenario-a.json")
                target = bundle
                for part in path[:-1]:
                    target = target[part]  # type: ignore[index]
                target[path[-1]] = value  # type: ignore[index]
                self.assertIn(expected, validator.validate_fixture_bundle(bundle))

    def test_fixture_rejects_unhashable_enum_values_without_crashing(self) -> None:
        for field, value in (("locale", ["es"]), ("evidence_mode", ["structural_only"])):
            with self.subTest(field=field):
                bundle = self.fixture("scenario-a.json")
                bundle[field] = value
                self.assertIn(
                    f"fixture has invalid {field}",
                    validator.validate_fixture_bundle(bundle),
                )

    def test_fixture_rejects_unknown_fields_in_each_nested_object_contract(self) -> None:
        locations = (
            (("structural_state_fixture", "observations", 0), "observation"),
            (("synthetic_fact_catalog", 0), "synthetic_fact_catalog[0]"),
            (("score_ledger",), "score_ledger"), (("score_ledger", "domains", 0), "score_ledger.domains[0]"),
            (("priorities", 0), "priorities[0]"), (("copy_blocks", 0), "copy_blocks[0]"),
            (("source_catalog", 0), "source_catalog[0]"), (("authorization_state",), "authorization_state"),
            (("eval_expectations",), "eval_expectations"),
        )
        for path, label in locations:
            with self.subTest(label=label):
                bundle = self.fixture("scenario-a.json")
                target = bundle
                for part in path:
                    target = target[part]  # type: ignore[index]
                target["unexpected"] = "SENTINEL"  # type: ignore[index]
                self.assertIn(f"{label} has unsupported field: unexpected", validator.validate_fixture_bundle(bundle))

    def test_fixture_rejects_duplicate_fact_ids(self) -> None:
        bundle = self.fixture("scenario-a.json")
        bundle["synthetic_fact_catalog"].append(copy.deepcopy(bundle["synthetic_fact_catalog"][0]))
        self.assertIn("synthetic_fact_catalog has duplicate fact_id: FACT-JSC1-READY", validator.validate_fixture_bundle(bundle))

    def test_fixture_rejects_references_to_nonexistent_facts(self) -> None:
        bundle = self.fixture("scenario-a.json")
        bundle["copy_blocks"][0]["fact_ids"].append("FACT-JSC1-MISSING")
        self.assertIn("copy_blocks[0] references unknown fact_id: FACT-JSC1-MISSING", validator.validate_fixture_bundle(bundle))

    def test_fixture_rejects_references_to_nonexistent_evidence(self) -> None:
        bundle = self.fixture("scenario-a.json")
        bundle["priorities"][0]["evidence_ids"].append("EVID-JSC1-MISSING")
        self.assertIn("priorities[0] references unknown evidence_id: EVID-JSC1-MISSING", validator.validate_fixture_bundle(bundle))

    def test_fact_and_source_ids_cannot_substitute_for_observation_evidence(self) -> None:
        mutations = (
            (("priorities", 0, "evidence_ids"), "FACT-JSC1-READY", "priorities[0]"),
            (("copy_blocks", 0, "evidence_ids"), "SOURCE-JSC1-GOOD", "copy_blocks[0]"),
            (("score_ledger", "domains", 0, "evidence_ids"), "FACT-JSC1-READY", "score_ledger.domains[0]"),
        )
        for path, reference, label in mutations:
            with self.subTest(label=label, reference=reference):
                bundle = self.fixture("scenario-a.json")
                target = bundle
                for part in path[:-1]:
                    target = target[part]  # type: ignore[index]
                target[path[-1]] = [reference]  # type: ignore[index]
                self.assertIn(
                    f"{label} references unknown evidence_id: {reference}",
                    validator.validate_fixture_bundle(bundle),
                )

    def test_decision_and_score_evidence_references_cannot_be_empty(self) -> None:
        mutations = (
            (("priorities", 0, "evidence_ids"), "priorities[0]"),
            (("copy_blocks", 0, "evidence_ids"), "copy_blocks[0]"),
            (("score_ledger", "domains", 0, "evidence_ids"), "score_ledger.domains[0]"),
        )
        for path, label in mutations:
            with self.subTest(label=label):
                bundle = self.fixture("scenario-a.json")
                target = bundle
                for part in path[:-1]:
                    target = target[part]  # type: ignore[index]
                target[path[-1]] = []  # type: ignore[index]
                self.assertIn(
                    f"{label}.evidence_ids must contain at least one reference",
                    validator.validate_fixture_bundle(bundle),
                )

    def test_fixture_rejects_wrong_counts_and_duplicate_ranks(self) -> None:
        bundle = self.fixture("scenario-a.json")
        bundle["priorities"].pop()
        bundle["priorities"][1]["rank"] = 1
        bundle["copy_blocks"].pop()
        errors = validator.validate_fixture_bundle(bundle)
        self.assertIn("fixture requires exactly three priorities", errors)
        self.assertIn("fixture priority ranks must be exactly 1, 2, 3", errors)
        self.assertIn("fixture requires exactly three copy_blocks", errors)

    def test_integer_schema_fields_reject_booleans_and_floats(self) -> None:
        mutations = (
            (("priorities", 0, "rank"), True, "priorities[0] has invalid rank"),
            (("score_ledger", "scored_weight"), 100.0, "score_ledger has invalid scored_weight"),
            (("score_ledger", "not_scored_weight"), False, "score_ledger has invalid not_scored_weight"),
            (("score_ledger", "overall_score"), 58.0, "score_ledger has invalid overall_score"),
            (("score_ledger", "domains", 0, "weight"), True, "score_ledger.domains[0] has invalid weight"),
        )
        for path, value, expected in mutations:
            with self.subTest(path=path):
                bundle = self.fixture("scenario-a.json")
                target = bundle
                for part in path[:-1]:
                    target = target[part]  # type: ignore[index]
                target[path[-1]] = value  # type: ignore[index]
                self.assertIn(expected, validator.validate_fixture_bundle(bundle))

    def test_malformed_ledger_values_return_errors_instead_of_throwing(self) -> None:
        mutations = (
            (("score_ledger", "domains", 0, "weight"), [], "score_ledger.domains[0] has invalid weight"),
            (("score_ledger", "domains", 0, "state"), [], "score_ledger.domains[0] has invalid state"),
            (("score_ledger", "domains", 0, "raw_score"), [], "score_ledger.domains[0] has invalid raw_score"),
            (("score_ledger", "domains", 0, "weighted_points"), [], "score_ledger.domains[0] has invalid weighted_points"),
            (("score_ledger", "numeric_weighted_total"), float("nan"), "score_ledger has invalid numeric_weighted_total"),
            (("score_ledger", "domains", 0, "raw_score"), float("inf"), "score_ledger.domains[0] has invalid raw_score"),
            (("score_ledger", "domains", 0, "weighted_points"), float("-inf"), "score_ledger.domains[0] has invalid weighted_points"),
        )
        for path, value, expected in mutations:
            with self.subTest(path=path, value=value):
                bundle = self.fixture("scenario-a.json")
                target = bundle
                for part in path[:-1]:
                    target = target[part]  # type: ignore[index]
                target[path[-1]] = value  # type: ignore[index]
                self.assertIn(expected, validator.validate_fixture_bundle(bundle))

    def test_huge_json_integers_return_range_errors_without_throwing(self) -> None:
        huge = 10**1000
        mutations = (
            (("score_ledger", "numeric_weighted_total"), "score_ledger has invalid numeric_weighted_total"),
            (("score_ledger", "scored_weight"), "score_ledger has invalid scored_weight"),
            (("score_ledger", "not_scored_weight"), "score_ledger has invalid not_scored_weight"),
            (("score_ledger", "overall_score"), "score_ledger has invalid overall_score"),
            (("score_ledger", "domains", 0, "weight"), "score_ledger.domains[0] has invalid weight"),
            (("score_ledger", "domains", 0, "raw_score"), "score_ledger.domains[0] has invalid raw_score"),
            (("score_ledger", "domains", 0, "weighted_points"), "score_ledger.domains[0] has invalid weighted_points"),
        )
        for path, expected in mutations:
            with self.subTest(path=path):
                bundle = self.fixture("scenario-a.json")
                target = bundle
                for part in path[:-1]:
                    target = target[part]  # type: ignore[index]
                target[path[-1]] = huge  # type: ignore[index]
                self.assertIn(expected, validator.validate_fixture_bundle(bundle))

    def test_score_ledgers_match_hand_checked_case_decisions(self) -> None:
        expected = {
            "scenario-a.json": ("es", 100, 0, 58.0, 58, "CAPABILITY_UNVERIFIED"),
            "scenario-b.json": ("en", 90, 10, 55.0, 61, "LEADERSHIP_SCOPE_UNQUANTIFIED"),
            "scenario-c.json": ("es", 85, 15, 54.45, 64, "VISUAL_NOT_INSPECTED"),
            "scenario-d.json": ("en", 75, 25, 47.25, 63, "VISUAL_PARTIAL_NO_AGGREGATE"),
        }
        for name, values in expected.items():
            with self.subTest(name=name):
                bundle = self.fixture(name)
                ledger = bundle["score_ledger"]
                actual = (bundle["locale"], ledger["scored_weight"], ledger["not_scored_weight"], ledger["numeric_weighted_total"], ledger["overall_score"], bundle["blocked_claims"][0])
                self.assertEqual(values, actual)
                self.assertEqual([15, 15, 15, 20, 15, 10, 10], [row["weight"] for row in ledger["domains"]])

    def test_partial_visual_fixtures_never_store_an_aggregate_visual_score(self) -> None:
        for name, mode in (("scenario-d.json", "partial_visual_photo_only"), ("scenario-d-banner-only.json", "partial_visual_banner_only")):
            with self.subTest(name=name):
                bundle = self.fixture(name)
                visual = bundle["score_ledger"]["domains"][0]
                self.assertEqual(mode, bundle["evidence_mode"])
                self.assertEqual("not_scored", visual["state"])
                self.assertIsNone(visual["raw_score"])
                self.assertEqual(0.0, visual["weighted_points"])

    def test_schema_document_matches_executable_field_and_enum_contract(self) -> None:
        schema = self.fixture("schema.json")
        self.assertEqual(set(validator.REQUIRED_BUNDLE_FIELDS), set(schema["required"]))
        self.assertEqual(set(validator.REQUIRED_BUNDLE_FIELDS), set(schema["properties"]))
        constants = {
            "schema_version": "linkedin-client-report-v2-fixture-2",
            "origin_class": "synthetic_from_authorized_structural_review",
            "derivation": "composite_plus_counterfactual_perturbation",
            "real_profile_mapping": "none_created",
        }
        for field, expected in constants.items():
            with self.subTest(constant=field):
                self.assertEqual(expected, schema["properties"][field]["const"])
        self.assertEqual(
            "https://example.invalid/linkedin-client-report-v2-fixture-2.schema.json",
            schema["$id"],
        )
        discriminator = r"JSC[0-9]+"
        segment = r"[A-Z0-9]+"
        patterns = {
            "fixture_id": rf"^FIXTURE-{discriminator}-{segment}(?:-{segment})*$",
            "internal_candidate_id": rf"^CANDIDATE-{discriminator}-{segment}(?:-{segment})*$",
        }
        for field, expected in patterns.items():
            with self.subTest(pattern=field):
                self.assertEqual(expected, schema["properties"][field]["pattern"])
                self.assertEqual(expected, validator._ID_PATTERNS[field].pattern)
        structural = schema["properties"]["structural_state_fixture"]
        self.assertFalse(structural["additionalProperties"])
        self.assertEqual(set(validator.STRUCTURAL_STATE_FIELDS), set(structural["required"]))
        self.assertEqual(set(validator.STRUCTURAL_STATE_FIELDS), set(structural["properties"]))
        definitions = schema["$defs"]
        contracts = {
            "observation": validator.OBSERVATION_FIELDS, "fact": validator.FACT_FIELDS,
            "score_ledger": validator.SCORE_LEDGER_FIELDS, "domain": validator.DOMAIN_SCORE_FIELDS,
            "priority": validator.PRIORITY_FIELDS, "copy": validator.COPY_FIELDS,
            "authorization": validator.AUTHORIZATION_FIELDS,
            "expectations": validator.EVAL_EXPECTATION_FIELDS,
        }
        for name, fields in contracts.items():
            with self.subTest(contract=name):
                self.assertFalse(definitions[name]["additionalProperties"])
                self.assertEqual(set(fields), set(definitions[name]["required"]))
                self.assertEqual(set(fields), set(definitions[name]["properties"]))
        self.assertFalse(definitions["source"]["additionalProperties"])
        self.assertEqual(set(validator.SOURCE_FIELDS), set(definitions["source"]["properties"]))
        self.assertEqual(
            set(validator.SOURCE_REQUIRED_FIELDS),
            set(definitions["source"]["required"]),
        )
        id_patterns = {
            "observation": ("evidence_id", rf"^EVID-{discriminator}-{segment}(?:-{segment})*$"),
            "fact": ("fact_id", rf"^FACT-{discriminator}-{segment}(?:-{segment})*$"),
            "priority": ("priority_id", rf"^PRIORITY-{discriminator}-{segment}(?:-{segment})*$"),
            "copy": ("copy_id", rf"^COPY-{discriminator}-{segment}(?:-{segment})*$"),
            "source": ("source_id", rf"^SOURCE-{discriminator}-{segment}(?:-{segment})*$"),
        }
        for definition, (field, expected) in id_patterns.items():
            with self.subTest(pattern=definition):
                self.assertEqual(expected, definitions[definition]["properties"][field]["pattern"])
                self.assertEqual(expected, validator._ID_PATTERNS[field].pattern)

        for field in ("priorities", "copy_blocks"):
            with self.subTest(cardinality=field):
                self.assertEqual(3, schema["properties"][field]["minItems"])
                self.assertEqual(3, schema["properties"][field]["maxItems"])
                self.assertEqual(3, len(schema["properties"][field]["allOf"]))
        domains = definitions["score_ledger"]["properties"]["domains"]
        self.assertEqual(7, domains["minItems"])
        self.assertEqual(7, domains["maxItems"])
        self.assertEqual(7, len(domains["allOf"]))
        for definition in ("domain", "priority", "copy"):
            self.assertEqual(
                1,
                definitions[definition]["properties"]["evidence_ids"]["minItems"],
            )
        self.assertEqual(9, len(definitions["domain"]["allOf"]))

        ledger_types = definitions["score_ledger"]["properties"]
        self.assertEqual({"type": "number", "minimum": 0, "maximum": 100}, ledger_types["numeric_weighted_total"])
        for field in ("scored_weight", "not_scored_weight", "overall_score"):
            with self.subTest(integer_field=field):
                self.assertEqual("integer", ledger_types[field]["type"])
                self.assertEqual(0, ledger_types[field]["minimum"])
                self.assertEqual(100, ledger_types[field]["maximum"])
        self.assertEqual("integer", definitions["priority"]["properties"]["rank"]["type"])
        self.assertEqual("integer", definitions["domain"]["properties"]["weight"]["type"])
        actual_enums = {
            "evidence_mode": schema["properties"]["evidence_mode"]["enum"], "locale": schema["properties"]["locale"]["enum"],
            "fact.evidence_state": definitions["fact"]["properties"]["evidence_state"]["enum"],
            "fact.fact_type": definitions["fact"]["properties"]["fact_type"]["enum"],
            "fact.role_family": definitions["fact"]["properties"]["role_family"]["enum"],
            "fact.capability_family": definitions["fact"]["properties"]["capability_family"]["enum"],
            "fact.scope_bucket": definitions["fact"]["properties"]["scope_bucket"]["enum"],
            "fact.claim_tokens": definitions["fact"]["properties"]["claim_tokens"]["items"]["enum"],
            "copy.state": definitions["copy"]["properties"]["state"]["enum"],
            "blocked_claims": schema["properties"]["blocked_claims"]["items"]["enum"],
            "observation.section": definitions["observation"]["properties"]["section"]["enum"],
            "observation.state": definitions["observation"]["properties"]["state"]["enum"],
            "domain.domain": definitions["domain"]["properties"]["domain"]["enum"],
            "domain.state": definitions["domain"]["properties"]["state"]["enum"],
            "domain.reason_code": definitions["domain"]["properties"]["reason_code"]["enum"],
            "score.confidence": definitions["score_ledger"]["properties"]["confidence"]["enum"],
            "priority.section": definitions["priority"]["properties"]["section"]["enum"],
            "priority.diagnosed_gap": definitions["priority"]["properties"]["diagnosed_gap"]["enum"],
            "priority.action_type": definitions["priority"]["properties"]["action_type"]["enum"],
            "priority.timebox": definitions["priority"]["properties"]["timebox"]["enum"],
            "priority.done_when": definitions["priority"]["properties"]["done_when"]["enum"],
            "priority.impact_basis": definitions["priority"]["properties"]["impact_basis"]["enum"],
            "copy.section": definitions["copy"]["properties"]["section"]["enum"],
            "copy.audience": definitions["copy"]["properties"]["audience"]["enum"],
            "copy.problem": definitions["copy"]["properties"]["problem"]["enum"],
            "copy.claim_boundary": definitions["copy"]["properties"]["claim_boundary"]["enum"],
            "source.source_category": definitions["source"]["properties"]["source_category"]["enum"],
            "source.source_class": definitions["source"]["properties"]["source_class"]["enum"],
            "source.reachability": definitions["source"]["properties"]["reachability"]["enum"],
            "source.scope": definitions["source"]["properties"]["scope"]["enum"],
            "source.inference_limit": definitions["source"]["properties"]["inference_limit"]["enum"],
            "source.fallback": definitions["source"]["properties"]["fallback"]["enum"],
            "authorization.inspection": definitions["authorization"]["properties"]["inspection"]["enum"],
            "authorization.external_actions": definitions["authorization"]["properties"]["external_actions"]["enum"],
            "authorization.action_state": definitions["authorization"]["properties"]["action_state"]["enum"],
            "expectations.scenario_class": definitions["expectations"]["properties"]["scenario_class"]["enum"],
            "expectations.primary_gap": definitions["expectations"]["properties"]["primary_gap"]["enum"],
            "expectations.primary_copy_category": definitions["expectations"]["properties"]["primary_copy_category"]["enum"],
            "expectations.pending_evidence_policy": definitions["expectations"]["properties"]["pending_evidence_policy"]["enum"],
        }
        expected_enums = {
            "evidence_mode": validator.EVIDENCE_MODES, "locale": validator.LOCALES,
            "fact.evidence_state": validator.EVIDENCE_STATES, "fact.fact_type": validator.FACT_TYPES,
            "fact.role_family": validator.ROLE_FAMILIES, "fact.capability_family": validator.CAPABILITY_FAMILIES,
            "fact.scope_bucket": validator.SCOPE_BUCKETS, "fact.claim_tokens": validator.CLAIM_TOKENS,
            "copy.state": validator.COPY_STATES, "blocked_claims": validator.BLOCKED_CLAIMS,
            "observation.section": validator.OBSERVATION_SECTIONS, "observation.state": validator.OBSERVATION_STATES,
            "domain.domain": validator.DOMAIN_WEIGHTS, "domain.state": validator.SCORE_STATES,
            "domain.reason_code": validator.REASON_CODES, "score.confidence": validator.CONFIDENCE_STATES,
            "priority.section": validator.PRIORITY_SECTIONS, "priority.diagnosed_gap": validator.DIAGNOSED_GAPS,
            "priority.action_type": validator.ACTION_TYPES, "priority.timebox": validator.TIMEBOXES,
            "priority.done_when": validator.DONE_WHEN_CODES, "priority.impact_basis": validator.IMPACT_BASES,
            "copy.section": validator.COPY_SECTIONS, "copy.audience": validator.AUDIENCES,
            "copy.problem": validator.COPY_PROBLEMS, "copy.claim_boundary": validator.CLAIM_BOUNDARIES,
            "source.source_category": validator.SOURCE_CATEGORIES, "source.source_class": validator.SOURCE_CLASSES,
            "source.reachability": validator.REACHABILITY_STATES, "source.scope": validator.SOURCE_SCOPES,
            "source.inference_limit": validator.INFERENCE_LIMITS, "source.fallback": validator.SOURCE_FALLBACKS,
            "authorization.inspection": validator.INSPECTION_AUTHORIZATIONS,
            "authorization.external_actions": validator.EXTERNAL_ACTION_AUTHORIZATIONS,
            "authorization.action_state": validator.ACTION_STATES,
            "expectations.scenario_class": validator.SCENARIO_CLASSES, "expectations.primary_gap": validator.PRIMARY_GAPS,
            "expectations.primary_copy_category": validator.COPY_SECTIONS,
            "expectations.pending_evidence_policy": validator.PENDING_EVIDENCE_POLICIES,
        }
        for name, expected_values in expected_enums.items():
            with self.subTest(enum=name):
                self.assertEqual(set(expected_values), set(actual_enums[name]))


if __name__ == "__main__":
    unittest.main()
