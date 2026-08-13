"""Behavioral contracts for the status-only executive career dossier v2."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins" / "professional-growth-coach" / "scripts"
VALIDATOR_PATH = SCRIPTS / "validate_executive_career_dossier_v2.py"
FIXTURE_ROOT = REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "executive-career-dossier"

CANONICAL_PROFILE_SECTIONS = (
    "photo", "banner", "name", "profile_url", "headline", "location",
    "contact_info", "about", "experience", "skills", "featured",
    "certifications", "education", "recommendations", "activity",
    "analytics", "job_preferences",
)


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, nested in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = nested
    return value


def load_v1_fixture(name: str) -> dict[str, object]:
    value = json.loads(
        (FIXTURE_ROOT / name).read_text(encoding="utf-8"), object_pairs_hook=unique_object
    )
    if not isinstance(value, dict):
        raise ValueError("fixture must be an object")
    return value


def make_v2_dossier(locale: str = "es") -> dict[str, object]:
    dossier = copy.deepcopy(load_v1_fixture(
        "scenario-a-es.json" if locale == "es" else "scenario-c-en.json"
    ))
    dossier["schema_version"] = "executive-career-dossier-v2"
    inspected = set(dossier["evidence_scope"]["inspected_sections"])
    dossier["section_coverage"] = []
    for section in CANONICAL_PROFILE_SECTIONS:
        if section in inspected:
            dossier["section_coverage"].append({
                "section": section,
                "availability": "inspected_present",
                "evidence_state": "verified",
                "reason": "inspected_content_available",
            })
            continue
        decision = "declined_for_session" if section == "certifications" else "pending_response"
        dossier["section_coverage"].append({
            "section": section,
            "availability": "unavailable",
            "evidence_state": "unknown",
            "reason": "inspection_declined" if decision == "declined_for_session" else "authorization_required",
            "inspection_request": {
                "access_type": "read_only_visible_section_inspection",
                "decision": decision,
                "scope": "current_session_only",
                "carry_forward": False,
            },
        })
    for evidence in dossier["evidence"]:
        evidence["profile_section"] = (
            evidence["section"] if evidence["section"] in CANONICAL_PROFILE_SECTIONS else None
        )
    priority_sections = ("headline", "about", "experience")
    for priority, section in zip(dossier["priorities"], priority_sections, strict=True):
        priority["evidence_ids"] = {
            "headline": ["E-001"], "about": ["E-002"], "experience": ["E-003"],
        }[section]
        priority.update({
            "target_section": section,
            "coach_observation": f"Coach observation for {section}.",
            "why_it_matters": f"Evidence from {section} changes the review.",
            "coach_prompt": f"Complete the private template for {section}.",
            "client_template": {
                "template_id": "context_action_result_v1",
                "field_keys": ["context", "action", "result"],
            },
            "privacy_boundary": "no_raw_profile_text_or_private_values",
        })
    return dossier


def load_validator() -> object:
    specification = importlib.util.spec_from_file_location(
        "validate_executive_career_dossier_v2", VALIDATOR_PATH
    )
    assert specification is not None and specification.loader is not None
    validator = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = validator
    specification.loader.exec_module(validator)
    return validator


class ExecutiveCareerDossierV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_v2_requires_the_exact_canonical_section_ledger(self) -> None:
        dossier = make_v2_dossier()
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        self.assertEqual(tuple(row["section"] for row in dossier["section_coverage"]), CANONICAL_PROFILE_SECTIONS)
        for mutation in (
            dossier["section_coverage"][:-1],
            list(reversed(dossier["section_coverage"])),
            dossier["section_coverage"] + [copy.deepcopy(dossier["section_coverage"][0])],
        ):
            invalid = copy.deepcopy(dossier)
            invalid["section_coverage"] = mutation
            self.assertIn(
                "section_coverage must contain every canonical section exactly once in canonical order",
                self.validator.validate_dossier(invalid),
            )

    def test_unavailable_sections_require_current_session_read_only_decisions(self) -> None:
        dossier = make_v2_dossier()
        dossier["section_coverage"][10] = {
            "section": "featured", "availability": "unavailable", "evidence_state": "unknown",
            "reason": "authorization_required", "inspection_request": {
                "access_type": "read_only_visible_section_inspection", "decision": "pending_response",
                "scope": "current_session_only", "carry_forward": False,
            },
        }
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        missing = copy.deepcopy(dossier)
        del missing["section_coverage"][10]["inspection_request"]
        self.assertIn("section_coverage[10] unavailable section requires inspection_request", self.validator.validate_dossier(missing))
        forbidden = make_v2_dossier()
        forbidden["section_coverage"][0]["inspection_request"] = copy.deepcopy(dossier["section_coverage"][10]["inspection_request"])
        self.assertIn("section_coverage[0] inspected section forbids inspection_request", self.validator.validate_dossier(forbidden))

    def test_ledger_state_matrix_is_closed_and_status_only(self) -> None:
        dossier = make_v2_dossier()
        cases = (
            ("inspected_present", "verified", "inspected_content_available", None),
            ("inspected_absent", "verified", "inspected_section_absent", None),
            ("candidate_supplied", "candidate_reported", "candidate_material_supplied", None),
            ("unavailable", "unknown", "authorization_required", "pending_response"),
            ("unavailable", "unknown", "inspection_declined", "declined_for_session"),
            ("unavailable", "unknown", "authorized_inspection_failed", "authorized_inspection_failed"),
        )
        for availability, state, reason, decision in cases:
            with self.subTest(availability=availability, decision=decision):
                invalid = copy.deepcopy(dossier)
                row = invalid["section_coverage"][10]
                row.update({"availability": availability, "evidence_state": state, "reason": reason})
                if decision is None:
                    row.pop("inspection_request", None)
                else:
                    row["inspection_request"]["decision"] = decision
                if availability == "candidate_supplied":
                    invalid["evidence"].append({
                        "id": "E-999", "state": "candidate_reported", "section": "proof",
                        "source_kind": "candidate_statement", "paraphrase": "Candidate material was supplied.",
                        "capture_ref": None, "profile_section": "featured",
                    })
                if availability == "inspected_present":
                    invalid["evidence"].append({
                        "id": "E-998", "state": "verified", "section": "proof",
                        "source_kind": "authorized_visible", "paraphrase": "Visible section was inspected.",
                        "capture_ref": "CAP-001", "profile_section": "featured",
                    })
                self.assertEqual(self.validator.validate_dossier(invalid), [])
        for mutation in (
            {"decision": "authorized_for_session"},
            {"carry_forward": True},
            {"access_type": "write_visible_section_inspection"},
            {"scope": "future_sessions"},
        ):
            invalid = make_v2_dossier()
            invalid["section_coverage"][10]["inspection_request"].update(mutation)
            self.assertTrue(self.validator.validate_dossier(invalid))

    def test_legacy_scope_is_a_constraint_not_the_complete_ledger(self) -> None:
        dossier = make_v2_dossier()
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        contradictory = copy.deepcopy(dossier)
        contradictory["section_coverage"][4].update({
            "availability": "unavailable", "evidence_state": "unknown", "reason": "authorization_required",
            "inspection_request": {"access_type": "read_only_visible_section_inspection", "decision": "pending_response", "scope": "current_session_only", "carry_forward": False},
        })
        self.assertIn("section_coverage[4] contradicts evidence_scope.inspected_sections", self.validator.validate_dossier(contradictory))
        unavailable = copy.deepcopy(dossier)
        unavailable["evidence_scope"]["unavailable_sections"] = ["featured"]
        unavailable["section_coverage"][10] = {"section": "featured", "availability": "inspected_absent", "evidence_state": "verified", "reason": "inspected_section_absent"}
        self.assertIn("section_coverage[10] contradicts evidence_scope.unavailable_sections", self.validator.validate_dossier(unavailable))

    def test_present_or_candidate_rows_require_section_evidence_without_score_mutation(self) -> None:
        dossier = make_v2_dossier()
        before = copy.deepcopy(dossier)
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        self.assertEqual(dossier, before)
        missing = copy.deepcopy(dossier)
        missing["evidence"][0]["profile_section"] = None
        self.assertIn("section_coverage[4] requires evidence for its profile_section", self.validator.validate_dossier(missing))
        pending = copy.deepcopy(dossier)
        pending["section_coverage"][10]["inspection_request"]["decision"] = "pending_response"
        declined = copy.deepcopy(pending)
        declined["section_coverage"][10].update({"reason": "inspection_declined"})
        declined["section_coverage"][10]["inspection_request"]["decision"] = "declined_for_session"
        self.assertEqual(pending["coverage"], declined["coverage"])
        self.assertEqual(self.validator.validate_dossier(pending), [])
        self.assertEqual(self.validator.validate_dossier(declined), [])

    def test_contextual_priorities_bind_same_section_evidence(self) -> None:
        dossier = make_v2_dossier()
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        dossier["priorities"][0]["evidence_ids"] = ["E-002"]
        self.assertIn("priorities[0].evidence_ids must bind to the target section", self.validator.validate_dossier(dossier))

    def test_priority_contract_is_closed_and_safe(self) -> None:
        for field in ("target_section", "coach_observation", "why_it_matters", "coach_prompt", "client_template", "privacy_boundary"):
            invalid = make_v2_dossier()
            del invalid["priorities"][0][field]
            self.assertTrue(self.validator.validate_dossier(invalid), field)
        for field_keys in ([], ["context", "action", "result", "scope", "metric", "target_role"], ["context", "context"]):
            invalid = make_v2_dossier()
            invalid["priorities"][0]["client_template"]["field_keys"] = field_keys
            self.assertTrue(self.validator.validate_dossier(invalid), field_keys)
        invalid = make_v2_dossier()
        invalid["priorities"][0]["client_template"]["template_id"] = "unknown_template"
        self.assertTrue(self.validator.validate_dossier(invalid))

    def test_every_ledger_and_request_boundary_rejects_session_or_positive_authorization_fields(self) -> None:
        mutations = (
            ("section_coverage", 10, "session_id"),
            ("section_coverage", 10, "authorized_for_session"),
            ("inspection_request", 10, "session_id"),
            ("inspection_request", 10, "authorization_granted"),
        )
        for boundary, index, key in mutations:
            with self.subTest(boundary=boundary, key=key):
                dossier = make_v2_dossier()
                target = dossier["section_coverage"][index]
                if boundary == "inspection_request":
                    target = target["inspection_request"]
                target[key] = True
                errors = self.validator.validate_dossier(dossier)
                self.assertTrue(errors)
                self.assertNotIn(key, "\n".join(errors))

    def test_every_evidence_record_requires_a_canonical_or_null_profile_section(self) -> None:
        for label, replacement in (("missing", None), ("unknown", "unknown_section"), ("number", 3), ("array", [])):
            with self.subTest(replacement=label):
                dossier = make_v2_dossier()
                if label == "missing":
                    del dossier["evidence"][4]["profile_section"]
                else:
                    dossier["evidence"][4]["profile_section"] = replacement
                self.assertTrue(self.validator.validate_dossier(dossier))

    def test_selector_falls_back_to_canonical_pending_section_not_targeted_by_a_priority(self) -> None:
        dossier = make_v2_dossier()
        for row in dossier["section_coverage"]:
            if isinstance(row.get("inspection_request"), dict):
                row["inspection_request"]["decision"] = "declined_for_session"
                row["reason"] = "inspection_declined"
        dossier["section_coverage"][10]["inspection_request"]["decision"] = "pending_response"
        dossier["section_coverage"][10]["reason"] = "authorization_required"
        self.assertEqual(self.validator.select_pending_inspection_section(dossier), "featured")

    def test_v2_diagnostics_do_not_echo_new_prose_values(self) -> None:
        sentinels = (
            "/private/path/profile.json", "https://www.linkedin.com/in/example",
            "person@example.test", "unsafe\x1b[31m", "unsafe\u202evalue",
        )
        for field in ("coach_observation", "why_it_matters", "coach_prompt", "privacy_boundary"):
            for sentinel in sentinels:
                with self.subTest(field=field, sentinel=repr(sentinel)):
                    dossier = make_v2_dossier()
                    dossier["priorities"][0][field] = sentinel
                    errors = self.validator.validate_dossier(dossier)
                    self.assertTrue(errors)
                    self.assertNotIn(sentinel, "\n".join(errors))

    def test_selector_returns_one_pending_priority_then_ledger_section(self) -> None:
        dossier = make_v2_dossier()
        dossier["section_coverage"][4].update({
            "availability": "unavailable", "evidence_state": "unknown", "reason": "authorization_required",
            "inspection_request": {"access_type": "read_only_visible_section_inspection", "decision": "pending_response", "scope": "current_session_only", "carry_forward": False},
        })
        self.assertEqual(self.validator.select_pending_inspection_section(dossier), "headline")
        dossier["section_coverage"][4].update({"availability": "inspected_present", "evidence_state": "verified", "reason": "inspected_content_available"})
        dossier["section_coverage"][7].update({
            "availability": "unavailable", "evidence_state": "unknown", "reason": "authorization_required",
            "inspection_request": {"access_type": "read_only_visible_section_inspection", "decision": "pending_response", "scope": "current_session_only", "carry_forward": False},
        })
        self.assertEqual(self.validator.select_pending_inspection_section(dossier), "about")
        for row in dossier["section_coverage"]:
            request = row.get("inspection_request")
            if isinstance(request, dict):
                request["decision"] = "declined_for_session"
                row["reason"] = "inspection_declined"
        self.assertIsNone(self.validator.select_pending_inspection_section(dossier))


class ExecutiveCareerDossierV2LoadAndCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_loader_uses_fixed_errors_for_malformed_private_inputs(self) -> None:
        cases = ((b'{"locale":"es","locale":"en"}', "duplicate JSON key"), (b'\xff', "v2 dossier must be valid UTF-8 JSON"), (b'[]', "v2 dossier must be a JSON object"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, (raw, message) in enumerate(cases):
                with self.subTest(message=message):
                    path = root / f"case-{index}.json"
                    path.write_bytes(raw)
                    with self.assertRaisesRegex(self.validator.DossierLoadError, message):
                        self.validator.load_dossier(path)

    def test_loader_rejects_depth_size_fifo_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            deep = root / "deep.json"; deep.write_text('{"a":' + "[" * 14 + "0" + "]" * 14 + "}", encoding="utf-8")
            with self.assertRaisesRegex(self.validator.DossierLoadError, "maximum nesting depth"):
                self.validator.load_dossier(deep)
            oversized = root / "large.json"; oversized.write_bytes(b" " * (256 * 1024 + 1))
            with self.assertRaisesRegex(self.validator.DossierLoadError, "256 KiB"):
                self.validator.load_dossier(oversized)
            target = root / "target.json"; target.write_text("{}", encoding="utf-8")
            link = root / "link.json"; link.symlink_to(target)
            with self.assertRaisesRegex(self.validator.DossierLoadError, "symlink"):
                self.validator.load_dossier(link)
            linked_parent = root / "linked-parent"; linked_parent.symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(self.validator.DossierLoadError, "cannot read v2 dossier"):
                self.validator.load_dossier(linked_parent / "target.json")
            fifo = root / "input.fifo"; os.mkfifo(fifo)
            with self.assertRaisesRegex(self.validator.DossierLoadError, "cannot read v2 dossier"):
                self.validator.load_dossier(fifo)

    def test_cli_returns_bounded_non_echoing_diagnostics(self) -> None:
        for sentinel in ("person@example.test", "https://example.test/private", "/private/path.json", "line\nbreak", "ansi\x1b[31m", "bidi\u202evalue"):
            with self.subTest(sentinel=repr(sentinel)):
                dossier = make_v2_dossier()
                dossier[sentinel] = "bad"
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "invalid.json"
                    path.write_text(json.dumps(dossier), encoding="utf-8")
                    result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertTrue(result.stderr)
                self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)
                self.assertNotIn("Traceback", result.stderr)
                self.assertNotIn(sentinel, result.stderr)

    def test_cli_rejects_row_request_and_template_attacks_without_traceback(self) -> None:
        mutations = (
            ("row", "session_id", "opaque-session-value"),
            ("request", "authorization_granted", True),
            ("template", "field_keys", [{"x": "y"}]),
            ("template", "field_keys", [["context"]]),
        )
        for boundary, key, value in mutations:
            with self.subTest(boundary=boundary, key=key):
                dossier = make_v2_dossier()
                if boundary == "row":
                    dossier["section_coverage"][10][key] = value
                elif boundary == "request":
                    dossier["section_coverage"][10]["inspection_request"][key] = value
                else:
                    dossier["priorities"][0]["client_template"][key] = value
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "invalid.json"
                    path.write_text(json.dumps(dossier), encoding="utf-8")
                    result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
                self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)

    def test_cli_decoder_recursion_and_truncation_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recursive = root / "recursive.json"
            recursive.write_text("[" * 1200 + "0" + "]" * 1200, encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(recursive)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)
            invalid = make_v2_dossier()
            invalid["section_coverage"] = [None] * 700
            path = root / "many-errors.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)
            self.assertIn("validation diagnostics truncated; additional errors omitted", result.stderr)

    def test_cli_accepts_a_valid_v2_dossier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "valid.json"
            path.write_text(json.dumps(make_v2_dossier()), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
