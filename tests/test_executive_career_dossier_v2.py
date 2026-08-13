"""Behavioral contracts for the status-only executive career dossier v2."""

from __future__ import annotations

import copy
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
VALIDATOR_PATH = SCRIPTS / "validate_executive_career_dossier_v2.py"
RENDERER_PATH = SCRIPTS / "render_executive_career_dossier_v2.py"
FIXTURE_ROOT = REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "executive-career-dossier"
V2_FIXTURE_ROOT = FIXTURE_ROOT.with_name("executive-career-dossier-v2")

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
                    r'<section class="section-block section-coverage-ledger" aria-labelledby="([^"]+)">(.*?)</section>',
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

    def test_market_placeholder_is_one_bounded_non_recommendation_state(self) -> None:
        for name in ("scenario-a-es.json", "scenario-c-en.json"):
            with self.subTest(name=name):
                dossier = json.loads((V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
                rendered = self.renderer.render_dossier_html(dossier)
                regions = re.findall(
                    r'<section class="card market-unavailable-card span-12" aria-labelledby="market-unavailable-title">(.*?)</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(len(regions), 1)
                text_value = visible_text(regions[0]).casefold()
                self.assertNotIn("<progress", regions[0].casefold())
                self.assertNotRegex(text_value, r"\d+(?:\.\d+)?%")
                for forbidden in (
                    "score", "vacancy", "vacante", "employer", "empleador",
                    "course", "curso", "paid", "pago",
                ):
                    self.assertNotIn(forbidden, text_value)

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
