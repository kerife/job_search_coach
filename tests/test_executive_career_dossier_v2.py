"""Behavioral contracts for the status-only executive career dossier v2."""

from __future__ import annotations

import copy
import hashlib
import html
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins" / "professional-growth-coach" / "scripts"
ASSETS_ROOT = REPO_ROOT / "plugins" / "professional-growth-coach" / "assets"
VALIDATOR_PATH = SCRIPTS / "validate_executive_career_dossier_v2.py"
RENDERER_PATH = SCRIPTS / "render_executive_career_dossier_v2.py"
FIXTURE_ROOT = REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "executive-career-dossier"
V2_FIXTURE_ROOT = FIXTURE_ROOT.with_name("executive-career-dossier-v2")
MARKET_FIXTURE_ROOT = FIXTURE_ROOT.with_name("career-market-learning-dossier")
MARKET_V2_FIXTURE_ROOT = FIXTURE_ROOT.with_name("career-market-learning-dossier-v2")
OVERSIZED_INTEGER_FIXTURE = (
    REPO_ROOT
    / "plugins"
    / "professional-growth-coach"
    / "tests"
    / "fixtures"
    / "private-json"
    / "oversized-integer.json"
)

UNSAFE_COACHING_PROSE = (
    (
        "coach_observation",
        "Publish this on LinkedIn now.",
        "must remain a private review action",
    ),
    (
        "why_it_matters",
        "Publish this on LinkedIn now.",
        "must remain a private review action",
    ),
    (
        "coach_prompt",
        "Publish this on LinkedIn now.",
        "must remain a private review action",
    ),
    (
        "coach_observation",
        "The profile is now live on LinkedIn.",
        "must remain a private review action",
    ),
    (
        "why_it_matters",
        "The profile is now live on LinkedIn.",
        "must remain a private review action",
    ),
    (
        "coach_prompt",
        "The profile is now live on LinkedIn.",
        "must remain a private review action",
    ),
    (
        "coach_prompt",
        "Quit your job now.",
        "must preserve current employment by default",
    ),
    (
        "coach_observation",
        "There were 314 private profile views.",
        "analytics measures require observed aggregate analytics",
    ),
    (
        "why_it_matters",
        "Employers are actively hiring 1000 SREs.",
        "demand language requires linked dated market evidence",
    ),
)

SAFE_COACHING_PROSE = (
    ("coach_observation", "The incident response scope is ready for private review."),
    ("why_it_matters", "Technical scope supports a focused private coaching review."),
    ("coach_prompt", "Review the private incident response scope for technical clarity."),
)

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
    profile_sections = (
        {"E-001": "headline", "E-002": "about", "E-003": "experience", "E-004": "skills", "E-006": "photo", "E-007": "banner"}
        if locale == "es"
        else {"E-001": "headline", "E-002": "skills", "E-003": "about", "E-004": "experience", "E-005": "photo"}
    )
    for evidence in dossier["evidence"]:
        evidence["profile_section"] = profile_sections.get(evidence["id"])
    priority_sections = ("headline", "about", "experience")
    for priority, section in zip(dossier["priorities"], priority_sections, strict=True):
        priority["evidence_ids"] = (
            {"headline": ["E-001"], "about": ["E-002"], "experience": ["E-003"]}
            if locale == "es"
            else {"headline": ["E-001"], "about": ["E-003"], "experience": ["E-004"]}
        )[section]
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


def make_market_v2_dossier(locale: str = "en") -> dict[str, object]:
    source = load_v1_fixture("scenario-market-en.json")
    dossier = make_v2_dossier(locale)
    market_evidence = copy.deepcopy(source["evidence"][-1])
    market_evidence["profile_section"] = None
    dossier["evidence"].append(market_evidence)
    dossier["market_context"] = copy.deepcopy(source["market_context"])
    return dossier


def make_composable_market_dossier(name: str, dossier: dict[str, object]) -> dict[str, object]:
    """Bind a synthetic market fixture to this exact, validated v2 dossier."""
    market = json.loads((MARKET_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
    market["locale"] = dossier["locale"]
    market["as_of_date"] = dossier["evidence_as_of"]
    canonical = json.dumps(dossier, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    market["source_executive_dossier_snapshot"] = "snap-dossier-sha256-" + hashlib.sha256(canonical).hexdigest()
    return market


def make_composable_learning_market_dossier(
    name: str, dossier: dict[str, object], renderer: object,
) -> dict[str, object]:
    """Bind a fixture v2 to the supplied dossier without exposing snapshots."""
    market = json.loads((MARKET_V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
    market["learning_evidence_mode"] = "synthetic"
    market["locale"] = dossier["locale"]
    market["as_of_date"] = dossier["evidence_as_of"]
    for option in market["learning_options"]:
        option["source_date"] = dossier["evidence_as_of"]
    canonical = json.dumps(dossier, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    market["source_executive_dossier_snapshot"] = "snap-dossier-sha256-" + hashlib.sha256(canonical).hexdigest()
    base = copy.deepcopy(market)
    base["schema_version"] = "career-market-learning-dossier-v1"
    base["learning_state"] = "not_evaluated"
    base["learning_decisions"] = []
    for key in ("source_market_snapshot", "source_learning_research_snapshot", "candidate_preferences", "learning_evidence_mode", "learning_options", "coach_decision", "proof_sprint", "reuse_map"):
        base.pop(key, None)
    market["source_market_snapshot"] = renderer.MARKET.snapshot_for_market_dossier(base)
    research = {
        "schema_version": "learning-option-research-v1",
        "evidence_mode": "synthetic",
        "locale": market["locale"],
        "as_of_date": market["as_of_date"],
        "source_market_snapshot": market["source_market_snapshot"],
        "candidate_preferences": market["candidate_preferences"],
        "options": market["learning_options"],
        "privacy_boundary": "identity_free_market_and_provider_evidence_only",
        "no_external_action": True,
    }
    market["source_learning_research_snapshot"] = renderer.MARKET_V2.RESEARCH.snapshot_for_learning_research(research)
    return market


def load_validator() -> object:
    specification = importlib.util.spec_from_file_location(
        "validate_executive_career_dossier_v2", VALIDATOR_PATH
    )
    assert specification is not None and specification.loader is not None
    validator = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = validator
    specification.loader.exec_module(validator)
    return validator


def load_renderer() -> object:
    specification = importlib.util.spec_from_file_location(
        "render_executive_career_dossier_v2", RENDERER_PATH
    )
    assert specification is not None and specification.loader is not None
    renderer = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = renderer
    specification.loader.exec_module(renderer)
    return renderer


def visible_text(rendered: str) -> str:
    without_code = re.sub(r"(?is)<(?:style|script)\b.*?</(?:style|script)>", " ", rendered)
    return " ".join(html.unescape(re.sub(r"(?s)<[^>]+>", " ", without_code)).split())


class DossierDOMAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.references: list[str] = []
        self.classes: list[str] = []
        self.tag_counts: dict[str, int] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
        values = dict(attrs)
        identifier = values.get("id")
        if identifier:
            self.ids.append(identifier)
        for field in ("aria-labelledby", "aria-describedby"):
            references = values.get(field)
            if references:
                self.references.extend(references.split())
        classes = values.get("class")
        if classes:
            self.classes.extend(classes.split())


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

    def test_v2_validator_rejects_unicode_control_prose(self) -> None:
        for character in ("\u202e", "\u200b", "\u0000"):
            with self.subTest(code_point=f"U+{ord(character):04X}"):
                dossier = make_v2_dossier("en")
                dossier["focus"]["statement"] = (
                    f"Target under review: roles with evidence{character} available."
                )
                errors = self.validator.validate_dossier(dossier)
                self.assertTrue(errors)
                self.assertTrue(all(character not in error for error in errors))

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

    def test_new_coaching_prose_reuses_v1_action_employment_analytics_and_market_guards(self) -> None:
        for field, value, diagnostic in UNSAFE_COACHING_PROSE:
            with self.subTest(field=field, diagnostic=diagnostic):
                dossier = make_v2_dossier()
                dossier["priorities"][0][field] = value
                errors = self.validator.validate_dossier(dossier)
                self.assertIn(f"priorities[0].{field} {diagnostic}", errors)
                self.assertNotIn(value, "\n".join(errors))

        for field, value in SAFE_COACHING_PROSE:
            with self.subTest(field=field):
                dossier = make_v2_dossier()
                dossier["priorities"][0][field] = value
                self.assertEqual(self.validator.validate_dossier(dossier), [])

    def test_v2_dated_market_coaching_prose_and_projection_use_v1_hire_and_hiring_semantics(self) -> None:
        source = load_v1_fixture("scenario-market-en.json")
        dossier = make_v2_dossier("en")
        market_evidence = copy.deepcopy(source["evidence"][-1])
        market_evidence["profile_section"] = None
        dossier["evidence"].append(market_evidence)
        dossier["market_context"] = copy.deepcopy(source["market_context"])
        self.assertEqual(self.validator.project_v2_to_v1(dossier), source)

        for text in (
            "Employers actively hire SREs.",
            "Employers are actively hiring SREs.",
        ):
            with self.subTest(text=text, surface="v2 coaching prose"):
                unlinked = copy.deepcopy(dossier)
                unlinked["priorities"][0]["why_it_matters"] = text
                self.assertIn(
                    "priorities[0].why_it_matters market claims require local dated market evidence",
                    self.validator.validate_dossier(unlinked),
                )

            with self.subTest(text=text, surface="v1 projection", evidence="unlinked"):
                projected = self.validator.project_v2_to_v1(dossier)
                projected["priorities"][0]["why_now"] = text
                self.assertIn(
                    "priorities[0].why_now market claims require local dated market evidence",
                    self.validator._v1.validate_dossier(projected),
                )

            with self.subTest(text=text, surface="v1 projection", evidence="linked"):
                projected = self.validator.project_v2_to_v1(dossier)
                projected["priorities"][0]["why_now"] = text
                projected["priorities"][0]["evidence_ids"].append("E-008")
                self.assertEqual(
                    self.validator._v1.validate_dossier(projected),
                    [],
                )

        safe = copy.deepcopy(dossier)
        safe["priorities"][0]["why_it_matters"] = (
            "Technical controls remain available for private review."
        )
        self.assertEqual(self.validator.validate_dossier(safe), [])

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


class ExecutiveCareerDossierV2RendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.renderer = load_renderer()
        cls.validator = load_validator()

    def test_localized_ledger_has_one_named_region_and_exact_semantic_rows(self) -> None:
        expected_labels = {
            "es": (
                "Foto", "Banner", "Nombre", "URL del perfil", "Titular", "Ubicación",
                "Información de contacto", "Acerca de", "Experiencia", "Aptitudes",
                "Destacado", "Certificaciones", "Educación", "Recomendaciones",
                "Actividad", "Analítica", "Preferencias de empleo",
            ),
            "en": (
                "Photo", "Banner", "Name", "Profile URL", "Headline", "Location",
                "Contact information", "About", "Experience", "Skills", "Featured",
                "Certifications", "Education", "Recommendations", "Activity",
                "Analytics", "Job preferences",
            ),
        }
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                rendered = self.renderer.render_dossier_html(make_v2_dossier(locale))
                regions = re.findall(
                    r'<section class="section-block section-coverage-ledger" aria-labelledby="([^"]+)"(?: id="[^"]+")?>(.*?)</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(len(regions), 1)
                region_label, body = regions[0]
                self.assertEqual(len(re.findall(rf'<h2 id="{re.escape(region_label)}">', body)), 1)
                rows = re.findall(
                    r'<li class="section-coverage-row"><article aria-labelledby="([^"]+)">\s*'
                    r'<h3 id="\1">([^<]+)</h3>\s*<dl class="section-coverage-facts">(.*?)</dl>\s*'
                    r'</article></li>',
                    body,
                    re.DOTALL,
                )
                self.assertEqual(len(rows), 17)
                self.assertEqual(tuple(label for _, label, _ in rows), expected_labels[locale])
                self.assertEqual(len({heading_id for heading_id, _, _ in rows}), 17)
                for _, _, facts in rows:
                    self.assertIn("<dt>", facts)
                    self.assertIn("<dd>", facts)
                    self.assertGreaterEqual(facts.count("<dt>"), 2)
                    self.assertEqual(facts.count("<dt>"), len(re.findall(r"<dd(?:\s|>)", facts)))

    def test_reading_path_is_localized_and_targets_four_unique_decision_regions(self) -> None:
        expected = {
            "es": ("Ruta de lectura", "Cobertura", "Prioridades", "Mercado", "Preparar conversación"),
            "en": ("Reading path", "Coverage", "Priorities", "Market", "Prepare conversation"),
        }
        for locale, labels in expected.items():
            with self.subTest(locale=locale):
                rendered = self.renderer.render_dossier_html(make_v2_dossier(locale))
                nav = re.search(
                    r'<nav class="reading-path(?: span-12)?" aria-label="[^"]+">(.*?)</nav>',
                    rendered,
                    re.DOTALL,
                )
                self.assertIsNotNone(nav)
                assert nav is not None
                self.assertIn(f'<span class="reading-path-title">{labels[0]}</span>', nav.group(1))
                for label, target in zip(labels[1:], ("section-coverage", "coach-priorities", "market-evidence", "screen-preparation"), strict=True):
                    self.assertIn(f'href="#{target}"', nav.group(1))
                    self.assertIn(label, nav.group(1))
                    self.assertEqual(1, rendered.count(f'id="{target}"'))
                css = (ASSETS_ROOT / "executive-career-dossier-v2.css").read_text(encoding="utf-8")
                self.assertIn(".reading-path a", css)
                self.assertIn("min-height: 44px", css)
                self.assertIn("@media screen and (max-width: 640px)", css)

    def test_reading_path_has_progressive_active_state_and_scroll_safe_targets(self) -> None:
        rendered = self.renderer.render_dossier_html(make_v2_dossier("en"))
        self.assertEqual(1, len(re.findall(r'<a[^>]+aria-current="location"', rendered)))
        self.assertIn('href="#section-coverage" aria-current="location"', rendered)
        self.assertIn("IntersectionObserver", rendered)
        self.assertIn("reading-path-active", rendered)

    def test_reading_path_scope_spans_the_decision_regions_and_scrollspy_uses_nearest_target(self) -> None:
        rendered = self.renderer.render_dossier_html(make_v2_dossier("en"))
        scope = re.search(r'<div class="reading-path-scope">(.*?)</div>\s*</main>', rendered, re.DOTALL)
        self.assertIsNotNone(scope)
        assert scope is not None
        body = scope.group(1)
        for target in ("section-coverage", "coach-priorities", "market-evidence", "screen-preparation"):
            self.assertIn(f'id="{target}"', body)
        self.assertIn("getBoundingClientRect", rendered)
        self.assertIn("addEventListener('scroll'", rendered)
        self.assertIn("initialHash", rendered)
        self.assertNotIn("targets[0].id);\n  }, { rootMargin", rendered)
        css = (ASSETS_ROOT / "executive-career-dossier-v2.css").read_text(encoding="utf-8")
        self.assertIn(".reading-path-scope", css)
        mobile = css[css.index("@media screen and (max-width: 640px)"):css.index("@media (prefers-reduced-motion: reduce)")]
        self.assertIn("scroll-margin-top: 18rem", mobile)
        css = (ASSETS_ROOT / "executive-career-dossier-v2.css").read_text(encoding="utf-8")
        self.assertIn("position: sticky", css)
        self.assertIn("scroll-margin-top", css)
        self.assertIn("position: static", css[css.index("@media print"):])
        self.assertIn(".reading-path a[aria-current=\"location\"]", css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)

    def test_mobile_reading_path_scroll_margin_clears_sticky_rail(self) -> None:
        css = (ASSETS_ROOT / "executive-career-dossier-v2.css").read_text(encoding="utf-8")
        mobile = css[css.index("@media screen and (max-width: 640px)"):css.index("@media (prefers-reduced-motion: reduce)")]
        self.assertIn("scroll-margin-top: 18rem", mobile)

    def test_tablet_reading_path_scroll_margin_clears_sticky_rail(self) -> None:
        css = (ASSETS_ROOT / "executive-career-dossier-v2.css").read_text(encoding="utf-8")
        tablet = css[css.index("@media screen and (max-width: 900px)"):css.index("@media screen and (max-width: 640px)")]
        self.assertIn("scroll-margin-top: 11rem", tablet)

    def test_reading_path_follows_verdict_and_recruiter_scan(self) -> None:
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                rendered = self.renderer.render_dossier_html(make_v2_dossier(locale))
                self.assertLess(rendered.index('id="verdict-title"'), rendered.index('id="scan-title"'))
                self.assertLess(rendered.index('id="scan-title"'), rendered.index('<nav class="reading-path'))

    def test_unavailable_rows_show_localized_reason_and_request_decision(self) -> None:
        for locale, labels in (
            ("es", ("No disponible", "Autorización requerida", "Respuesta pendiente")),
            ("en", ("Unavailable", "Authorization required", "Response pending")),
        ):
            with self.subTest(locale=locale):
                rendered = self.renderer.render_dossier_html(make_v2_dossier(locale))
                for label in labels:
                    self.assertIn(label, rendered)
                self.assertIn('class="section-coverage-request"', rendered)

    def test_three_named_coach_cards_render_closed_blank_templates_without_legacy_priority_copy(self) -> None:
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                dossier = make_v2_dossier(locale)
                rendered = self.renderer.render_dossier_html(dossier)
                cards = re.findall(
                    r'<article class="card span-4 coach-priority-card" aria-labelledby="([^"]+)">(.*?)</article>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(len(cards), 3)
                self.assertNotIn('class="timebox"', rendered)
                for (heading_id, card), priority in zip(cards, dossier["priorities"], strict=True):
                    self.assertEqual(len(re.findall(rf'<h3 id="{re.escape(heading_id)}">', card)), 1)
                    self.assertIn('class="coach-observation"', card)
                    self.assertIn('class="coach-prompt"', card)
                    self.assertIn('class="coach-template"', card)
                    blanks = re.findall(r'<li><span class="coach-template-field">[^<]+</span><span class="coach-template-blank" aria-hidden="true"></span></li>', card)
                    self.assertGreaterEqual(len(blanks), 1)
                    self.assertLessEqual(len(blanks), 5)
                    for old_value in ("problem", "action"):
                        self.assertNotIn(str(priority[old_value]), card)

    def test_visible_product_surface_excludes_internal_and_private_values(self) -> None:
        dossier = make_v2_dossier("es")
        rendered_text = visible_text(self.renderer.render_dossier_html(dossier))
        forbidden = {
            "read_only_visible_section_inspection", "pending_response",
            "declined_for_session", "authorization_required",
            "context_action_result_v1", "profile_url", "contact_info",
            "/private/path/profile.json", "https://www.linkedin.com/in/example",
            "person@example.test",
        }
        forbidden.update(record["id"] for record in dossier["evidence"])
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, rendered_text)

    def test_writer_rejects_unsafe_new_coaching_prose_before_creating_visible_output(self) -> None:
        for field, value, diagnostic in UNSAFE_COACHING_PROSE:
            with self.subTest(field=field, diagnostic=diagnostic):
                dossier = make_v2_dossier()
                dossier["priorities"][0][field] = value
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    source = root / "unsafe.json"
                    output = root / "unsafe.html"
                    source.write_text(json.dumps(dossier), encoding="utf-8")
                    with self.assertRaises(self.renderer.DossierValidationError) as context:
                        self.renderer.write_dossier_html(source, output)
                    self.assertFalse(output.exists())
                errors = "\n".join(context.exception.errors)
                self.assertIn(f"priorities[0].{field} {diagnostic}", errors)
                self.assertNotIn(value, errors)

    def test_renderer_cli_oversized_integer_exits_three_without_echo_or_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dossier_path = root / "oversized-integer.json"
            output = root / "executive-career-dossier-v2.html"
            dossier_path.write_bytes(OVERSIZED_INTEGER_FIXTURE.read_bytes())

            result = subprocess.run(
                [sys.executable, "-B", str(RENDERER_PATH), str(dossier_path), "--output", str(output)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 3)
            self.assertEqual(result.stdout, "")
            self.assertNotIn("Traceback", result.stderr)
            self.assertNotIn("opaque-private-input", result.stderr)
            self.assertNotIn(str(dossier_path), result.stderr)
            self.assertFalse(output.exists())

    def test_market_placeholder_is_one_bounded_non_recommendation_state(self) -> None:
        for name in ("scenario-a-es.json", "scenario-c-en.json"):
            with self.subTest(name=name):
                dossier = json.loads((V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
                rendered = self.renderer.render_dossier_html(dossier)
                regions = re.findall(
                    r'<section class="card market-unavailable-card span-12" aria-labelledby="market-unavailable-title"(?: id="[^"]+")?>(.*?)</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(len(regions), 1)
                text_value = visible_text(regions[0]).casefold()
                self.assertNotIn("<progress", regions[0].casefold())
                self.assertNotRegex(text_value, r"\d+(?:\.\d+)?%")
                self.assertTrue(
                    "siguiente investigación" in text_value or "next research" in text_value
                )
                for forbidden in (
                    "score", "course", "curso", "paid", "pago",
                ):
                    self.assertNotIn(forbidden, text_value)

    def test_dated_market_context_renders_validated_matrix_and_public_source(self) -> None:
        for locale, heading, caption in (
            ("en", "Vacancy context and gaps", "Comparison kept separate from the LinkedIn diagnosis"),
            ("es", "Contexto de vacantes y brechas", "Comparación separada del diagnóstico de LinkedIn"),
        ):
            with self.subTest(locale=locale):
                dossier = make_market_v2_dossier(locale)
                self.assertEqual(self.validator.validate_dossier(dossier), [])
                rendered = self.renderer.render_dossier_html(dossier)
                self.assertEqual(rendered.count('class="card market-card span-12"'), 1)
                self.assertNotIn('class="card market-unavailable-card span-12"', rendered)
                self.assertIn(heading, rendered)
                self.assertIn("Platform reliability roles", rendered)
                self.assertIn("Public vacancy research methodology", rendered)
                self.assertIn('href="https://www.themuse.com/advice/linkedin-profile-tips"', rendered)
                self.assertIn(caption, rendered)
                self.assertNotIn("source_digest", visible_text(rendered))
                self.assertNotIn("E-008", visible_text(rendered))

    def test_dated_market_table_exposes_localized_mobile_labels_without_changing_semantics(self) -> None:
        expected = {
            "en": ("Required signals", "Supported signals", "Needs confirmation"),
            "es": ("Señales requeridas", "Señales sustentadas", "Por confirmar"),
        }
        css = (ASSETS_ROOT / "executive-career-dossier-v1.css").read_text(encoding="utf-8")
        self.assertIn("@media screen and (max-width: 680px)", css)
        self.assertIn(".comparison-table td::before", css)
        self.assertIn("content: attr(data-label)", css)
        self.assertNotIn("overflow-x: auto", css)
        for locale, labels in expected.items():
            with self.subTest(locale=locale):
                rendered = self.renderer.render_dossier_html(make_market_v2_dossier(locale))
                self.assertIn("<thead>", rendered)
                self.assertEqual(rendered.count("data-label="), 3)
                for label in labels:
                    self.assertIn(f'<td data-label="{label}">', rendered)

    def test_market_matrix_print_layout_stacks_rows_for_readability(self) -> None:
        css = (ASSETS_ROOT / "career-market-learning-dossier-v1.css").read_text(encoding="utf-8")
        print_css = css[css.index("@media print"):]
        self.assertIn(".market-matrix tbody, .market-matrix tr, .market-matrix th, .market-matrix td { display: block;", print_css)
        self.assertIn(".market-matrix td::before { content: attr(data-label);", print_css)
        self.assertNotIn(".market-matrix thead { display: table-header-group; }", print_css)

    def test_optional_market_dossier_renders_complete_cards_matrix_and_recurrence(self) -> None:
        dossier = make_v2_dossier("es")
        market = make_composable_market_dossier("complete-five-es.json", dossier)
        rendered = self.renderer.render_dossier_html(dossier, market)

        self.assertEqual(rendered.count('class="vacancy-alignment-card"'), 5)
        self.assertEqual(rendered.count('<progress max="100"'), 5)
        self.assertEqual(rendered.count('class="market-alignment-score"'), 5)
        self.assertEqual(rendered.count('class="market-recurrence-count"'), len(market["recurrence_rows"]))
        self.assertIn('class="market-matrix"', rendered)
        self.assertIn('class="recurrence-row"', rendered)
        self.assertIn('class="gap-closure-route"', rendered)
        self.assertEqual(rendered.count('class="market-alignment-facts"'), 5)
        self.assertEqual(rendered.count("Cobertura de evidencia"), 5)
        self.assertEqual(rendered.count("Banda cualitativa"), 5)
        self.assertIn("La evidencia es direccional y no representa ajuste de contratación.", visible_text(rendered))
        self.assertEqual(rendered.count('class="market-vacancy-context"'), 5)
        self.assertIn("Ubicación", visible_text(rendered))
        self.assertIn("Arreglo", visible_text(rendered))
        self.assertIn("Tipo de fuente", visible_text(rendered))
        self.assertIn("La elegibilidad y la autorización laboral no se infieren.", visible_text(rendered))
        self.assertEqual(rendered.count('class="market-source-link"'), 5)
        self.assertEqual(rendered.count("Fecha de investigación"), 5)
        self.assertIn('href="https://example.com/careers/v-001"', rendered)
        self.assertIn('rel="noreferrer"', rendered)
        for short_key in ("V1", "V2", "V3", "V4", "V5"):
            self.assertIn(f">{short_key}<", rendered)
        self.assertIn("Evidencia directa", rendered)
        self.assertIn("1/5", rendered)
        self.assertNotIn("snap-market-sha256", rendered)
        self.assertNotIn("E-001", visible_text(rendered))

    def test_market_cards_render_per_vacancy_freshness_and_contextual_source_names(self) -> None:
        dossier = make_v2_dossier("es")
        market = make_composable_market_dossier("complete-five-es.json", dossier)
        for card in market["vacancy_cards"]:
            card.update({
                "access_date": market["as_of_date"],
                "publication_date": "2026-08-05",
                "freshness_status": "current",
                "freshness_basis": "publication_date",
                "freshness_window_days": 90,
                "freshness_reason": "publication_date_within_window",
            })
        rendered = self.renderer.render_dossier_html(dossier, market)
        visible = visible_text(rendered)
        self.assertEqual(5, visible.count("Verificada abierta al"))
        self.assertEqual(5, visible.count("Publicada"))
        self.assertEqual(5, visible.count("Vigencia"))
        self.assertIn('aria-label="Ver fuente pública: Reliability Engineer"', rendered)

        english = make_v2_dossier("en")
        english_market = make_composable_market_dossier("limited-four-en.json", english)
        english_market["vacancy_cards"][0].update({
            "access_date": english_market["as_of_date"],
            "publication_date": None,
            "freshness_status": "unknown",
            "freshness_basis": "unknown",
            "freshness_window_days": 90,
            "freshness_reason": "publication_date_unknown_verified_open_on_access_date",
        })
        english_rendered = self.renderer.render_dossier_html(english, english_market)
        english_visible = visible_text(english_rendered)
        self.assertIn("Publication date: unknown", english_visible)
        self.assertIn("Freshness: unconfirmed", english_visible)
        self.assertIn('aria-label="View public source: Reliability Engineer"', english_rendered)

    def test_market_source_kind_enums_are_localized_and_not_exposed_raw(self) -> None:
        dossier = make_v2_dossier("en")
        market = make_composable_market_dossier("complete-five-es.json", dossier)
        market["vacancy_cards"][1]["source_kind"] = "employer_operated_ats"

        rendered = self.renderer.render_dossier_html(dossier, market)
        visible = visible_text(rendered)

        self.assertIn("Employer-operated ATS", visible)
        self.assertNotIn("employer_operated_ats", visible)
        self.assertEqual(("LinkedIn Jobs (respaldo)", "LinkedIn Jobs backup"), self.renderer.SOURCE_KIND_COPY["linkedin_jobs_backup"])

    def test_evaluated_learning_market_renders_one_private_static_decision_region(self) -> None:
        dossier = make_v2_dossier("es")
        market = make_composable_learning_market_dossier(
            "project-first-five-es.json", dossier, self.renderer,
        )
        rendered = self.renderer.render_dossier_html(dossier, market)
        visible = visible_text(rendered)

        self.assertEqual(rendered.count('class="market-learning-roi"'), 1)
        self.assertEqual(len(re.findall(r'class="learning-decision-row(?: learning-decision-row--[a-z-]+)?"', rendered)), 3)
        self.assertIn('class="learning-coach-decision"', rendered)
        self.assertIn('class="learning-proof-sprint"', rendered)
        self.assertEqual(rendered.count('class="learning-reuse-row"'), 3)
        self.assertLess(rendered.index('id="market-recurrence-title"'), rendered.index('class="market-learning-roi"'))
        self.assertLess(rendered.index('class="market-learning-roi"'), rendered.index('class="gap-closure-route"'))
        self.assertIn("Ruta de aprendizaje", visible)
        self.assertIn("Decisión de coaching", visible)
        region_start = rendered.index('<section class="market-learning-roi"')
        region_end = rendered.index('<section class="gap-closure-route"', region_start)
        region = rendered[region_start:region_end]
        self.assertNotRegex(region, r"<(?:a|button|form|input|select|textarea)\b")
        self.assertNotRegex(region, r"\son[a-z]+=", re.I)
        for private_token in ("snap-market", "snap-learning", "LO-001", "E-001", "https://example.com"):
            self.assertNotIn(private_token, region)

    def test_learning_decision_cards_expose_semantic_state_treatment(self) -> None:
        dossier = make_v2_dossier("es")
        market = make_composable_learning_market_dossier(
            "project-first-five-es.json", dossier, self.renderer,
        )
        rendered = self.renderer.render_dossier_html(dossier, market)

        self.assertIn('class="learning-decision-row learning-decision-row--project-first"', rendered)
        self.assertIn('class="learning-decision-row learning-decision-row--consider"', rendered)
        self.assertIn('class="learning-decision-row learning-decision-row--not-needed"', rendered)
        css = (ASSETS_ROOT / "career-market-learning-dossier-v1.css").read_text(encoding="utf-8")
        self.assertIn(".learning-decision-row--project-first", css)
        self.assertIn(".learning-decision-row--consider", css)
        self.assertIn(".learning-decision-row--not-needed", css)
        self.assertIn(".learning-decision-row--consider .learning-option-type", css)
        self.assertIn("color: var(--gold);", css)
        self.assertIn(".learning-decision-row .learning-option-type { color: CanvasText; border-color: CanvasText; }", css)

    def test_learning_decision_cards_expose_decision_type_and_basis(self) -> None:
        dossier = make_v2_dossier("es")
        market = make_composable_learning_market_dossier("project-first-five-es.json", dossier, self.renderer)
        rendered = self.renderer.render_dossier_html(dossier, market)
        self.assertIn("data-decision=\"project_first\"", rendered)
        self.assertIn("data-option-type=\"candidate_owned_project\"", rendered)
        self.assertIn("decision-basis", rendered)
        self.assertIn("opportunity-cost", rendered)
        self.assertIn("market-provider-evidence-boundary", rendered)

    def test_learning_cards_expose_provenance_context_and_omit_empty_unknowns(self) -> None:
        dossier = make_v2_dossier("es")
        market = make_composable_learning_market_dossier("project-first-five-es.json", dossier, self.renderer)
        rendered = self.renderer.render_dossier_html(dossier, market)
        self.assertEqual(rendered.count('class="learning-provenance"'), len(market["learning_decisions"]))
        rendered_option_ids = {row["option_id"] for row in market["learning_decisions"]}
        for option in market["learning_options"]:
            if option["option_id"] not in rendered_option_ids:
                continue
            for value in (option["provider"], option["option"], option["source_title"], option["source_date"], option["geography"]):
                self.assertIn(str(value), rendered)
        self.assertIn("Contexto de procedencia", visible_text(rendered))
        self.assertIn("Desconocidos", visible_text(rendered))
        self.assertNotIn("<dd></dd>", rendered)
        self.assertNotIn("Desconocidos</dt><dd></dd>", rendered)

    def test_market_v1_keeps_its_existing_gap_route_without_learning_decisions(self) -> None:
        dossier = make_v2_dossier("en")
        market = make_composable_market_dossier("complete-five-es.json", dossier)
        rendered = self.renderer.render_dossier_html(dossier, market)
        self.assertIn('class="gap-closure-route"', rendered)
        self.assertNotIn('class="market-learning-roi"', rendered)

    def test_synthetic_market_is_visibly_not_current_market_evidence(self) -> None:
        dossier = make_v2_dossier("en")
        market = make_composable_market_dossier("complete-five-es.json", dossier)
        market["evidence_mode"] = "synthetic"

        rendered = self.renderer.render_dossier_html(dossier, market)

        self.assertIn('class="market-synthetic-boundary market-boundary"', rendered)
        self.assertIn("Synthetic fixture: not current-market evidence.", visible_text(rendered))

    def test_evaluated_learning_market_rejects_stale_research_snapshot(self) -> None:
        dossier = make_v2_dossier("es")
        market = make_composable_learning_market_dossier(
            "project-first-five-es.json", dossier, self.renderer,
        )
        market["source_learning_research_snapshot"] = "snap-learning-sha256-" + ("0" * 64)

        with self.assertRaises(self.renderer.DossierValidationError):
            self.renderer.render_dossier_html(dossier, market)

    def test_market_progress_indicators_have_composite_text_labels(self) -> None:
        dossier = make_v2_dossier("en")
        market = make_composable_market_dossier("complete-five-es.json", dossier)
        rendered = self.renderer.render_dossier_html(dossier, market)
        audit = DossierDOMAudit()
        audit.feed(rendered)

        self.assertTrue(
            all(reference in audit.ids for reference in audit.references),
            "every market progress label reference resolves to visible text",
        )
        self.assertRegex(
            rendered,
            r'<progress[^>]+aria-labelledby="market-vacancy-title-1 market-alignment-score-1"',
        )
        self.assertRegex(
            rendered,
            r'<progress[^>]+aria-labelledby="market-recurrence-signal-1 market-recurrence-count-1"',
        )

    def test_optional_market_dossier_limited_and_unavailable_states_do_not_pad_or_score(self) -> None:
        english = make_v2_dossier("en")
        limited = make_composable_market_dossier("limited-four-en.json", english)
        limited_html = self.renderer.render_dossier_html(english, limited)
        self.assertEqual(limited_html.count('class="vacancy-alignment-card"'), 4)
        self.assertEqual(limited_html.count('<progress max="100"'), 4)
        self.assertNotIn(">V5<", limited_html)
        self.assertIn('class="market-limitation"', limited_html)

        spanish = make_v2_dossier("es")
        unavailable = make_composable_market_dossier("unavailable-es.json", spanish)
        unavailable_html = self.renderer.render_dossier_html(spanish, unavailable)
        self.assertIn('class="card market-unavailable-card span-12"', unavailable_html)
        self.assertNotIn('class="vacancy-alignment-card"', unavailable_html)
        self.assertNotIn('class="market-matrix"', unavailable_html)
        self.assertNotIn('<progress max="100"', unavailable_html)
        self.assertNotIn('class="gap-closure-route"', unavailable_html)

    def test_unavailable_market_state_exposes_a_localized_read_only_research_next_step(self) -> None:
        expected = {
            "es": (
                "Siguiente investigación",
                "SRE, Platform Engineering y DevOps en México o remoto declarado",
                "Cinco vacantes de empleadores distintos",
                "Sitio oficial del empleador y ATS operado por el empleador",
                "Registrar la fecha de acceso de cada publicación",
                "Solo lectura: no aplicar, contactar, seguir, publicar ni inferir elegibilidad.",
            ),
            "en": (
                "Next research",
                "SRE, Platform Engineering, and DevOps in Mexico or declared remote scope",
                "Five vacancies from distinct employers",
                "Employer official site and employer-operated ATS",
                "Record the access date for each posting",
                "Read-only: do not apply, contact, follow, publish, or infer eligibility.",
            ),
        }
        for locale, labels in expected.items():
            with self.subTest(locale=locale):
                rendered = self.renderer.render_dossier_html(make_v2_dossier(locale))
                self.assertEqual(1, rendered.count('class="market-next-investigation"'))
                for label in labels:
                    self.assertIn(label, rendered)
                self.assertNotIn('class="gap-closure-route"', rendered)

    def test_optional_market_dossier_rejects_mismatched_boundaries_without_echoing_values(self) -> None:
        dossier = make_v2_dossier("es")
        market = make_composable_market_dossier("complete-five-es.json", dossier)
        market["locale"] = "en"
        with self.assertRaises(self.renderer.DossierValidationError) as context:
            self.renderer.render_dossier_html(dossier, market)
        self.assertIn("market dossier locale does not match dossier", context.exception.errors)
        self.assertNotIn("complete-five", "\n".join(context.exception.errors))

    def test_no_market_argument_keeps_existing_render_bytes(self) -> None:
        dossier = make_v2_dossier("es")
        self.assertEqual(
            self.renderer.render_dossier_html(dossier),
            self.renderer.render_dossier_html(dossier, None),
        )

    def test_shipped_fixtures_have_complete_resolved_noninteractive_dom(self) -> None:
        for name in ("scenario-a-es.json", "scenario-c-en.json"):
            with self.subTest(name=name):
                dossier = json.loads((V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
                rendered = self.renderer.render_dossier_html(dossier)
                audit = DossierDOMAudit()
                audit.feed(rendered)

                self.assertEqual(audit.tag_counts.get("h1"), 1)
                self.assertEqual(audit.tag_counts.get("main"), 1)
                self.assertEqual(audit.tag_counts.get("footer"), 1)
                self.assertEqual(len(audit.ids), len(set(audit.ids)))
                self.assertEqual(set(audit.references) - set(audit.ids), set())
                self.assertEqual(audit.classes.count("section-coverage-row"), 17)
                self.assertEqual(audit.classes.count("coach-priority-card"), 3)
                self.assertEqual(audit.classes.count("market-unavailable-card"), 1)
                self.assertNotIn('data-priority-card="true"', rendered)
                self.assertNotIn('class="timebox"', rendered)
                templates = re.findall(
                    r'<section class="coach-template"[^>]*>(.*?)</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(len(templates), 3)
                for template in templates:
                    self.assertNotRegex(
                        template,
                        r"<(?:a|button|input|select|textarea)\b",
                    )

    def test_chat_summary_asks_exactly_one_first_pending_authorization_question(self) -> None:
        summary = self.renderer.build_chat_summary(make_v2_dossier("es"))
        self.assertIn(
            "¿Autorizas inspeccionar en modo solo lectura la sección Nombre durante esta sesión?",
            summary,
        )
        self.assertNotIn("Certificaciones", summary)
        self.assertEqual(summary.count("¿Autorizas inspeccionar"), 1)
        self.assertNotIn(make_v2_dossier("es")["questions"][0]["question"], summary)
        self.assertLessEqual(len(summary.split()), 180)

        english = json.loads(
            (V2_FIXTURE_ROOT / "scenario-c-en.json").read_text(encoding="utf-8")
        )
        summary = self.renderer.build_chat_summary(english)
        self.assertIn(
            "Do you authorize read-only inspection of the Banner section during this session?",
            summary,
        )
        self.assertEqual(summary.count("Do you authorize read-only inspection"), 1)
        self.assertNotIn(
            "Do you authorize read-only inspection of the Name section during this session?",
            summary,
        )
        self.assertNotIn("Certifications", summary)
        self.assertLessEqual(len(summary.split()), 180)

    def test_chat_summary_retains_v1_behavior_when_no_inspection_request_is_pending(self) -> None:
        dossier = make_v2_dossier("en")
        for row in dossier["section_coverage"]:
            request = row.get("inspection_request")
            if isinstance(request, dict) and request["decision"] == "pending_response":
                row["reason"] = "inspection_declined"
                request["decision"] = "declined_for_session"
        summary = self.renderer.build_chat_summary(dossier)
        self.assertNotIn("Do you authorize read-only inspection", summary)
        self.assertIn(dossier["questions"][0]["question"], summary)

    def test_shipped_fixtures_are_valid_and_project_deep_equal_to_v1_sources(self) -> None:
        for name in ("scenario-a-es.json", "scenario-c-en.json"):
            with self.subTest(name=name):
                source = load_v1_fixture(name)
                dossier = json.loads((V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
                self.assertEqual(self.validator.validate_dossier(dossier), [])
                self.assertEqual(self.validator.project_v2_to_v1(dossier), source)

    def test_shipped_fixture_ledger_uses_the_required_pending_and_declined_matrix(self) -> None:
        for name in ("scenario-a-es.json", "scenario-c-en.json"):
            with self.subTest(name=name):
                dossier = json.loads((V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
                evidence_sections = {
                    record["profile_section"]
                    for record in dossier["evidence"]
                    if record["profile_section"] is not None
                }
                rows = {row["section"]: row for row in dossier["section_coverage"]}
                self.assertEqual(rows["featured"]["reason"], "authorization_required")
                self.assertEqual(rows["featured"]["inspection_request"]["decision"], "pending_response")
                self.assertEqual(rows["certifications"]["reason"], "inspection_declined")
                self.assertEqual(rows["certifications"]["inspection_request"]["decision"], "declined_for_session")
                self.assertEqual(dossier["analytics"]["state"], "not_requested")
                for section in CANONICAL_PROFILE_SECTIONS:
                    if section in evidence_sections or section == "certifications":
                        continue
                    self.assertEqual(rows[section]["availability"], "unavailable")
                    self.assertEqual(rows[section]["reason"], "authorization_required")
                    self.assertEqual(rows[section]["inspection_request"]["decision"], "pending_response")

    def test_writer_keeps_the_v2_artifact_private(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "dossier-v2.html"
            receipt = self.renderer.write_dossier_html(
                V2_FIXTURE_ROOT / "scenario-a-es.json", output
            )
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertEqual(receipt.artifact_type, "text/html")

    def test_writer_accepts_a_bound_market_path_and_rejects_a_stale_one_before_writing(self) -> None:
        dossier = make_v2_dossier("es")
        market = make_composable_market_dossier("complete-five-es.json", dossier)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dossier_path = root / "dossier.json"
            market_path = root / "market.json"
            output = root / "market.html"
            dossier_path.write_text(json.dumps(dossier), encoding="utf-8")
            market_path.write_text(json.dumps(market), encoding="utf-8")
            receipt = self.renderer.write_dossier_html(
                dossier_path, output, market_dossier_path=market_path,
            )
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertEqual(receipt.artifact_type, "text/html")
            self.assertIn('class="vacancy-alignment-card"', output.read_text(encoding="utf-8"))

            market["source_executive_dossier_snapshot"] = "snap-dossier-sha256-" + "0" * 64
            market_path.write_text(json.dumps(market), encoding="utf-8")
            stale_output = root / "stale.html"
            with self.assertRaises(self.renderer.DossierValidationError):
                self.renderer.write_dossier_html(
                    dossier_path, stale_output, market_dossier_path=market_path,
                )
            self.assertFalse(stale_output.exists())


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

    def test_cli_rejects_unsafe_new_coaching_prose_with_fixed_non_echoing_diagnostics(self) -> None:
        for field, value, diagnostic in UNSAFE_COACHING_PROSE:
            with self.subTest(field=field, diagnostic=diagnostic):
                dossier = make_v2_dossier()
                dossier["priorities"][0][field] = value
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "unsafe.json"
                    path.write_text(json.dumps(dossier), encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-B", str(VALIDATOR_PATH), str(path)],
                        cwd=REPO_ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                self.assertEqual(result.returncode, 2)
                self.assertIn(f"priorities[0].{field} {diagnostic}", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertNotIn(value, result.stderr)
                self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)

    def test_cli_decoder_recursion_and_truncation_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recursive = root / "recursive.json"
            recursive.write_text("[" * 1200 + "0" + "]" * 1200, encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(recursive)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 3)
            self.assertNotIn("Traceback", result.stderr)
            invalid = make_v2_dossier()
            invalid["section_coverage"] = [None] * 700
            path = root / "many-errors.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)
            self.assertIn("validation diagnostics truncated; additional errors omitted", result.stderr)

    def test_renderer_cli_bounds_validation_diagnostics(self) -> None:
        dossier = make_v2_dossier()
        dossier["section_coverage"] = [None] * 700
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dossier_path = root / "many-errors.json"
            output = root / "executive-career-dossier-v2.html"
            dossier_path.write_text(json.dumps(dossier), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(RENDERER_PATH), str(dossier_path), "--output", str(output)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)
        self.assertIn("validation diagnostics truncated; additional errors omitted", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(output.exists())

    def test_cli_accepts_a_valid_v2_dossier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "valid.json"
            path.write_text(json.dumps(make_v2_dossier()), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
