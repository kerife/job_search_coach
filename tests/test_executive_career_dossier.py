"""Contract tests for the identity-free executive career dossier runtime."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    REPO_ROOT
    / "plugins"
    / "professional-growth-coach"
    / "scripts"
    / "validate_executive_career_dossier.py"
)
FIXTURE_ROOT = (
    REPO_ROOT
    / "tests"
    / "evals"
    / "with-skill"
    / "fixtures"
    / "executive-career-dossier"
)
MARKDOWN_VALIDATOR_PATH = (
    REPO_ROOT
    / "plugins"
    / "professional-growth-coach"
    / "scripts"
    / "validate_linkedin_client_report.py"
)
PRIVACY_SCANNER_PATH = REPO_ROOT / "scripts" / "check_repository_privacy.py"
RENDERER_PATH = (
    REPO_ROOT
    / "plugins"
    / "professional-growth-coach"
    / "scripts"
    / "render_executive_career_dossier.py"
)


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load_fixture(name: str) -> dict[str, object]:
    value = json.loads(
        (FIXTURE_ROOT / name).read_text(encoding="utf-8"),
        object_pairs_hook=unique_object,
    )
    if not isinstance(value, dict):
        raise ValueError("fixture must be a JSON object")
    return value


def mutate_path(value: object, path: tuple[object, ...], replacement: object) -> object:
    mutated = copy.deepcopy(value)
    target = mutated
    for component in path[:-1]:
        target = target[component]  # type: ignore[index]
    target[path[-1]] = replacement  # type: ignore[index]
    return mutated


def load_validator() -> object:
    specification = importlib.util.spec_from_file_location(
        "validate_executive_career_dossier", VALIDATOR_PATH
    )
    assert specification is not None and specification.loader is not None
    validator = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(validator)
    return validator


def load_markdown_validator() -> object:
    specification = importlib.util.spec_from_file_location(
        "validate_linkedin_client_report", MARKDOWN_VALIDATOR_PATH
    )
    assert specification is not None and specification.loader is not None
    validator = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(validator)
    return validator


def load_renderer() -> object:
    specification = importlib.util.spec_from_file_location(
        "render_executive_career_dossier", RENDERER_PATH
    )
    assert specification is not None and specification.loader is not None
    renderer = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = renderer
    specification.loader.exec_module(renderer)
    return renderer


class ExecutiveCareerDossierSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()
        cls.es_dossier = load_fixture("scenario-a-es.json")
        cls.en_dossier = load_fixture("scenario-c-en.json")

    def validate_dossier(self, value: object) -> list[str]:
        return self.validator.validate_dossier(value)

    def review_contract_dossier(self) -> dict[str, object]:
        dossier = copy.deepcopy(self.es_dossier)
        if isinstance(dossier["focus"], str):
            dossier["focus"] = {
                "statement": "Objetivo bajo revisión: posicionamiento profesional con evidencia disponible.",
                "state": "target_under_review",
                "claim_ids": [],
            }
        scope = dossier["evidence_scope"]
        scope.setdefault("visual_state", "authorized_visual_visible")
        scope.setdefault("visual_capture_ref", "CAP-001")
        for item in dossier["evidence"]:
            item.setdefault(
                "capture_ref",
                "CAP-001" if item["section"] in {"photo", "banner"} else None,
            )
        dossier["verdict"].setdefault("evidence_ids", ["E-001", "E-002"])
        recruiter_references = {
            "understood_signal": ("verified", ["E-001"]),
            "ambiguity": ("candidate_reported", ["E-004"]),
            "positioning_bridge": ("verified", ["E-001", "E-002"]),
        }
        for field, (state, evidence_ids) in recruiter_references.items():
            if isinstance(dossier["recruiter_scan"][field], str):
                dossier["recruiter_scan"][field] = {
                    "statement": dossier["recruiter_scan"][field],
                    "evidence_state": state,
                    "evidence_ids": evidence_ids,
                }
        for dimension in dossier["dimensions"]:
            dimension.setdefault(
                "capture_ref",
                "CAP-001" if dimension["dimension"] == "visual" else None,
            )
        component_scores = {"photo": 76, "banner": 71}
        component_evidence = {"photo": "E-006", "banner": "E-007"}
        for component in ("photo", "banner"):
            item = dossier["visual_review"][component]
            item.setdefault("evidence_state", "verified")
            item.setdefault("capture_ref", "CAP-001")
            item.setdefault("score", component_scores[component])
            item["evidence_ids"] = [component_evidence[component]]
        return dossier

    def test_valid_es_and_en_runtime_dossiers_are_accepted(self) -> None:
        self.assertEqual(self.validate_dossier(self.es_dossier), [])
        self.assertEqual(self.validate_dossier(self.en_dossier), [])

    def test_contract_is_closed_identity_free_and_single_candidate(self) -> None:
        forbidden_mutations = {
            "candidate identity": ("candidate_id", "candidate-synthetic"),
            "name": ("candidate_name", "Example Person"),
            "profile url": ("profile_url", "https://www.linkedin.com/in/example"),
            "raw profile": ("raw_profile_text", "copied profile text"),
            "analytics": ("analytics_value", "private value"),
        }
        for label, (key, value) in forbidden_mutations.items():
            with self.subTest(label=label):
                mutated = copy.deepcopy(self.es_dossier)
                mutated[key] = value
                self.assertTrue(self.validate_dossier(mutated))

    def test_exact_evidence_claim_and_decision_references_are_required(self) -> None:
        mutations = (
            ("dangling evidence", ("priorities", 0, "evidence_ids"), ["E-999"]),
            ("dangling claim", ("copy_blocks", 0, "claim_ids"), ["C-999"]),
            ("duplicate evidence", ("claims", 0, "evidence_ids"), ["E-001", "E-001"]),
        )
        for label, path, value in mutations:
            with self.subTest(label=label):
                mutated = mutate_path(self.es_dossier, path, value)
                self.assertTrue(self.validate_dossier(mutated))

    def test_exactly_three_human_priorities_are_required(self) -> None:
        self.assertEqual([priority["rank"] for priority in self.es_dossier["priorities"]], [1, 2, 3])
        for value in ("GAP-A-PRIMARY", "ACTION-A-HEADLINE", "TIMEBOX-A-1", "DONE-WHEN-A-1"):
            with self.subTest(value=value):
                mutated = copy.deepcopy(self.es_dossier)
                mutated["priorities"][0]["action"] = value
                self.assertIn(
                    "priorities[0].action must be client-facing prose",
                    self.validate_dossier(mutated),
                )

    def test_ready_copy_uses_only_allowed_claims(self) -> None:
        mutated = copy.deepcopy(self.es_dossier)
        mutated["claims"][0]["public_use"] = "confirmation_required"
        self.assertIn(
            "copy_blocks[0] ready copy requires allowed claims",
            self.validate_dossier(mutated),
        )

    def test_requested_technology_ledger_is_bound_and_cannot_self_exempt_ready_copy(self) -> None:
        for technology in ("Terraform", "Jenkins", "Terra\u200bform"):
            with self.subTest(technology=technology):
                mutated = copy.deepcopy(self.es_dossier)
                mutated["unsupported_copy_terms"] = []
                mutated["copy_blocks"][0]["copy"] = (
                    f"Especialista en {technology} para plataformas de alta escala"
                )
                self.assertIn(
                    "copy_blocks[0].copy contains unsupported requested technology",
                    self.validate_dossier(mutated),
                )

        bound = copy.deepcopy(self.es_dossier)
        bound.pop("unsupported_copy_terms", None)
        bound["requested_technology_terms"] = [
            {"term": "Terraform", "claim_ids": ["C-002"]}
        ]
        bound["claims"][1]["paraphrase"] = (
            "Terraform was reported and requires a verifiable example."
        )
        bound["evidence"][3]["paraphrase"] = (
            "Terraform was candidate-reported without a verified example."
        )
        self.assertEqual([], self.validate_dossier(bound))

        dangling = copy.deepcopy(bound)
        dangling["requested_technology_terms"][0]["claim_ids"] = ["C-999"]
        self.assertIn(
            "requested_technology_terms[0].claim_ids references unknown identifier",
            self.validate_dossier(dangling),
        )

        promoted = copy.deepcopy(bound)
        promoted["copy_blocks"][0]["copy"] = "Terraform specialist for platform scale"
        promoted["copy_blocks"][0]["claim_ids"] = ["C-002"]
        promoted["copy_blocks"][0]["evidence_ids"] = ["E-004"]
        self.assertIn(
            "copy_blocks[0].copy contains unsupported requested technology",
            self.validate_dossier(promoted),
        )

        supported = copy.deepcopy(self.es_dossier)
        supported["requested_technology_terms"] = [
            {"term": "Terraform", "claim_ids": ["C-001"]}
        ]
        supported["claims"][0]["paraphrase"] = "Terraform experience is verified."
        supported["evidence"][0]["paraphrase"] = "Terraform experience is verified."
        supported["copy_blocks"][0]["copy"] = "Terraform specialist for platform scale"
        self.assertEqual([], self.validate_dossier(supported))

    def test_arbitrary_expertise_promotion_requires_a_bound_supported_term(self) -> None:
        phrases = (
            "Especialista en Pulumi para plataformas de alta escala",
            "Experto en Argo CD para entrega continua",
            "Expert in Pulumi for platform automation",
            "Specialist with Argo CD for delivery systems",
            "Dominio de Pulumi para automatización de plataformas",
            "Proficient in Pulumi for platform automation",
            "Skilled in Argo CD for delivery systems",
            "Advanced Pulumi practitioner for platform scale",
            "Mastery of Argo CD for delivery systems",
            "Pulumi proficiency for platform automation",
            "Strong Pulumi skills for platform automation",
        )
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                dossier = copy.deepcopy(self.es_dossier)
                dossier["requested_technology_terms"] = []
                dossier["copy_blocks"][0]["copy"] = phrase
                self.assertIn(
                    "copy_blocks[0].copy expertise term requires a bound allowed claim",
                    self.validate_dossier(dossier),
                )

        supported = copy.deepcopy(self.es_dossier)
        supported["requested_technology_terms"] = [
            {"term": "Terraform", "claim_ids": ["C-001"]}
        ]
        supported["claims"][0]["paraphrase"] = "Terraform experience is verified."
        supported["evidence"][0]["paraphrase"] = "Terraform experience is verified."
        supported["copy_blocks"][0]["copy"] = (
            "Proficient in Terraform for platform automation"
        )
        self.assertEqual([], self.validate_dossier(supported))

    def test_every_promoted_expertise_complement_requires_its_own_allowed_binding(self) -> None:
        supported = copy.deepcopy(self.es_dossier)
        supported["requested_technology_terms"] = [
            {"term": "Terraform", "claim_ids": ["C-001"]}
        ]
        supported["claims"][0]["paraphrase"] = "Terraform experience is verified."
        supported["evidence"][0]["paraphrase"] = "Terraform experience is verified."
        mixed_phrases = (
            "Terraform foundation; proficient in Pulumi for platform automation",
            "Terraform experience with mastery of Argo CD for delivery systems",
            "Terraform specialist and skilled in Pulumi for automation",
            "Strong Pulumi skills for platform automation",
        )
        expected_terms = (
            ("pulumi",),
            ("argo cd",),
            ("terraform", "pulumi"),
            ("pulumi",),
        )
        for phrase, complements in zip(mixed_phrases, expected_terms, strict=True):
            with self.subTest(boundary="extractor", phrase=phrase):
                self.assertEqual(
                    complements,
                    self.validator.extract_ready_expertise_terms(phrase),
                )
            with self.subTest(boundary="validator", phrase=phrase):
                dossier = copy.deepcopy(supported)
                dossier["copy_blocks"][0]["copy"] = phrase
                self.assertIn(
                    "copy_blocks[0].copy expertise term requires a bound allowed claim",
                    self.validate_dossier(dossier),
                )

        both_supported = copy.deepcopy(supported)
        both_supported["evidence"].append(
            {
                "id": "E-008",
                "state": "verified",
                "section": "skills",
                "source_kind": "provided_material",
                "paraphrase": "Pulumi experience is verified.",
                "capture_ref": None,
            }
        )
        both_supported["claims"].append(
            {
                "id": "C-003",
                "state": "verified",
                "paraphrase": "Pulumi experience is verified.",
                "evidence_ids": ["E-008"],
                "public_use": "allowed",
            }
        )
        both_supported["requested_technology_terms"].append(
            {"term": "Pulumi", "claim_ids": ["C-003"]}
        )
        both_supported["copy_blocks"][0]["copy"] = (
            "Terraform specialist and skilled in Pulumi for automation"
        )
        both_supported["copy_blocks"][0]["claim_ids"] = ["C-001", "C-003"]
        both_supported["copy_blocks"][0]["evidence_ids"] = [
            "E-001",
            "E-002",
            "E-008",
        ]
        self.assertEqual([], self.validate_dossier(both_supported))

    def test_private_action_fields_reject_external_actions_in_english_and_spanish(self) -> None:
        mutations = (
            (("verdict", "start_here_action"), "Edit your LinkedIn headline now."),
            (("priorities", 0, "action"), "Publica el borrador en LinkedIn ahora."),
            (("visual_review", "photo", "private_action"), "Upload the photo to LinkedIn."),
            (("seven_day_plan", 0, "action"), "Contacta al reclutador."),
            (("seven_day_plan", 0, "action"), "Apply to the role."),
            (("seven_day_plan", 0, "action"), "Message the recruiter."),
            (("seven_day_plan", 0, "action"), "Review the draft, then publish it."),
            (("seven_day_plan", 0, "action"), "Revisa el borrador y luego publícalo."),
            (("seven_day_plan", 0, "action"), "Draft the headline and publish it."),
            (("seven_day_plan", 0, "action"), "Redacta el titular y publícalo."),
            (("seven_day_plan", 0, "action"), "Publicar el borrador en LinkedIn."),
            (("seven_day_plan", 0, "action"), "You must contact the recruiter."),
            (("seven_day_plan", 0, "action"), "Debes enviar el mensaje."),
            (("seven_day_plan", 0, "done_when"), "The post is shared publicly."),
            (("seven_day_plan", 0, "done_when"), "La publicación queda programada."),
        )
        for path, text in mutations:
            with self.subTest(path=path, text=text):
                dossier = mutate_path(self.es_dossier, path, text)
                error_path = ""
                for component in path:
                    error_path += (
                        f"[{component}]"
                        if isinstance(component, int)
                        else ("." if error_path else "") + component
                    )
                self.assertIn(
                    f"{error_path} must remain a private review action",
                    self.validate_dossier(dossier),
                )

    def test_external_actions_are_rejected_in_natural_forms_on_every_surface(self) -> None:
        cases = (
            (("verdict", "start_here_action"), "When ready, publish the headline."),
            (("priorities", 0, "action"), "Use LinkedIn to publish the headline."),
            (("priorities", 0, "done_when"), "LinkedIn shows the updated headline."),
            (("priorities", 0, "done_when"), "LinkedIn muestra el nuevo titular."),
            (("priorities", 0, "action"), "Considera publicar el titular."),
            (("priorities", 0, "action"), "Al terminar la revisión, publica el titular."),
            (("priorities", 0, "action"), "Review the draft before publishing it on LinkedIn."),
            (("priorities", 0, "action"), "Revisa el borrador antes de publicarlo en LinkedIn."),
            (("priorities", 0, "action"), "Draft the message for sending to the recruiter."),
            (("priorities", 0, "done_when"), "The new headline appears on LinkedIn."),
            (("priorities", 0, "done_when"), "The new headline is live on LinkedIn."),
            (("priorities", 0, "done_when"), "The profile is live on LinkedIn."),
            (("priorities", 0, "done_when"), "The headline is now public on LinkedIn."),
            (("priorities", 0, "done_when"), "The profile is now public on LinkedIn."),
            (("priorities", 0, "done_when"), "The headline can now be seen on LinkedIn."),
            (("priorities", 0, "done_when"), "The profile can now be seen on LinkedIn."),
            (("priorities", 0, "done_when"), "The copy can now be seen on LinkedIn."),
            (("priorities", 0, "done_when"), "The message can now be seen on LinkedIn."),
            (("priorities", 0, "done_when"), "The copy is live on LinkedIn."),
            (("priorities", 0, "done_when"), "The message is now public on LinkedIn."),
            (("priorities", 0, "done_when"), "The profile shows on LinkedIn."),
            (("priorities", 0, "done_when"), "El nuevo titular queda visible en LinkedIn."),
            (("priorities", 0, "done_when"), "The recruiter was contacted on LinkedIn."),
            (("priorities", 0, "done_when"), "The message was sent to the recruiter."),
            (("visual_review", "photo", "private_action"), "Now upload the photo."),
            (("seven_day_plan", 0, "action"), "You can upload the photo."),
            (("seven_day_plan", 0, "action"), "Reach out to the recruiter."),
            (("seven_day_plan", 0, "action"), "El siguiente paso es enviar el mensaje."),
            (("seven_day_plan", 0, "action"), "Cuando esté listo, publícalo."),
            (("seven_day_plan", 0, "action"), "Cuando esté listo, publí\u200bcalo."),
            (("seven_day_plan", 0, "done_when"), "Done: published on LinkedIn."),
            (("seven_day_plan", 0, "done_when"), "The post went live."),
            (("seven_day_plan", 0, "done_when"), "The message has gone out."),
            (("seven_day_plan", 0, "done_when"), "Ya quedó publicado."),
        )
        for path, text in cases:
            with self.subTest(path=path, text=text):
                dossier = mutate_path(self.es_dossier, path, text)
                error_path = ""
                for component in path:
                    error_path += (
                        f"[{component}]"
                        if isinstance(component, int)
                        else ("." if error_path else "") + component
                    )
                self.assertIn(
                    f"{error_path} must remain a private review action",
                    self.validate_dossier(dossier),
                )

    def test_private_action_fields_allow_local_drafting_and_technical_review(self) -> None:
        dossier = copy.deepcopy(self.en_dossier)
        dossier["verdict"]["start_here_action"] = (
            "Review a private headline draft before making any profile change."
        )
        dossier["priorities"][0]["action"] = (
            "Draft and review technical proof in a private document."
        )
        dossier["seven_day_plan"][0]["action"] = (
            "Review a private message draft for technical accuracy."
        )
        dossier["seven_day_plan"][0]["done_when"] = (
            "The local draft is ready for another private review."
        )

        self.assertEqual([], self.validate_dossier(dossier))

    def test_private_action_fields_allow_bounded_negated_and_historical_review(self) -> None:
        controls = (
            "Do not publish the draft; keep it private.",
            "Confirm the recruiter was not contacted.",
            "Review the published vacancy in a private note.",
        )
        for text in controls:
            with self.subTest(text=text):
                dossier = mutate_path(
                    self.en_dossier,
                    ("seven_day_plan", 0, "action"),
                    text,
                )
                self.assertEqual([], self.validate_dossier(dossier))

    def test_candidate_analytics_claim_requires_trend_or_quantity_semantics(self) -> None:
        cases = (
            (
                "Este dossier no incluye identidad, contacto, texto crudo del perfil ni analítica privada individual.",
                False,
            ),
            ("Profile traffic doubled this week.", True),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(
                    expected,
                    self.validator.candidate_text_has_analytics_claim(text),
                )

    def test_outcome_guarantees_are_rejected_in_english_and_spanish(self) -> None:
        for text in (
            "Recruiters will call after this change.",
            "An interview is guaranteed after this revision.",
            "You will get hired after this change.",
            "Los reclutadores llamarán después de este cambio.",
            "La entrevista está garantizada después de esta revisión.",
            "Conseguirás una oferta después de este cambio.",
        ):
            with self.subTest(text=text):
                dossier = mutate_path(self.es_dossier, ("verdict", "rationale"), text)
                self.assertIn(
                    "verdict.rationale client report cannot guarantee an employment or platform outcome",
                    self.validate_dossier(dossier),
                )

    def test_employment_continuity_footer_is_not_an_outcome_guarantee(self) -> None:
        for text in (
            "No LinkedIn action was performed. This analysis evaluates professional options and development; "
            "it does not recommend resigning or leaving your job. You decide what comes next.",
            "No se realizó ninguna acción en LinkedIn. Este análisis evalúa opciones y desarrollo profesional; "
            "no recomienda renunciar ni dejar tu empleo. Tú decides qué sigue.",
        ):
            with self.subTest(text=text):
                self.assertFalse(self.validator.candidate_text_has_outcome_guarantee(text))

    def test_legacy_linkedin_profile_urls_are_rejected_from_dossier_prose(self) -> None:
        linkedin_host = "linkedin" + ".com"
        for value in (
            f"https://www.{linkedin_host}/pub/synthetic-sentinel/42/7b/123",
            f"www.{linkedin_host}/pub/synthetic-sentinel/42/7b/123",
            f"{linkedin_host}/pub/synthetic-sentinel/42/7b/123",
        ):
            with self.subTest(value=value):
                dossier = mutate_path(self.es_dossier, ("verdict", "rationale"), value)
                errors = self.validate_dossier(dossier)
                self.assertIn(
                    "verdict.rationale client report contains forbidden LinkedIn profile URL value",
                    errors,
                )
                self.assertNotIn(value, "\n".join(errors))

    def test_natural_outcome_guarantees_are_rejected_dossier_wide(self) -> None:
        for text in (
            "This headline lands interviews.",
            "An interview follows this change.",
            "An interview follows this revision.",
            "This will lead to recruiter messages.",
            "Te van a contratar después de este cambio.",
            "La contratación está asegurada.",
            "Tu contratación está asegurada.",
        ):
            with self.subTest(text=text):
                dossier = mutate_path(self.es_dossier, ("priorities", 0, "why_now"), text)
                self.assertIn(
                    "priorities[0].why_now client report cannot guarantee an employment or platform outcome",
                    self.validate_dossier(dossier),
                )

    def test_duplicate_priorities_questions_and_multi_sentence_verdict_are_rejected(self) -> None:
        duplicated_priorities = copy.deepcopy(self.es_dossier)
        for index in (1, 2):
            rank = duplicated_priorities["priorities"][index]["rank"]
            duplicated_priorities["priorities"][index] = copy.deepcopy(
                duplicated_priorities["priorities"][0]
            )
            duplicated_priorities["priorities"][index]["rank"] = rank
        self.assertIn(
            "priorities must not duplicate normalized coaching decisions",
            self.validate_dossier(duplicated_priorities),
        )

        duplicated_questions = copy.deepcopy(self.es_dossier)
        duplicate = copy.deepcopy(duplicated_questions["questions"][0])
        duplicate["rank"] = 2
        duplicated_questions["questions"].append(duplicate)
        self.assertIn(
            "questions must not duplicate normalized coaching decisions",
            self.validate_dossier(duplicated_questions),
        )

        two_sentence_verdict = mutate_path(
            self.es_dossier,
            ("verdict", "statement"),
            "La propuesta puede ser más concreta. La evidencia marca el siguiente paso.",
        )
        self.assertIn(
            "verdict.statement must contain exactly one sentence",
            self.validate_dossier(two_sentence_verdict),
        )

        unterminated_second_sentence = mutate_path(
            self.es_dossier,
            ("verdict", "statement"),
            "La propuesta puede ser más concreta. La evidencia marca el siguiente paso",
        )
        self.assertIn(
            "verdict.statement must contain exactly one sentence",
            self.validate_dossier(unterminated_second_sentence),
        )

    def test_identity_cues_and_raw_copy_attestations_are_bound_to_prose(self) -> None:
        cases = (
            ("Candidate: Synthetic Given Family.", "forbidden candidate identity cue"),
            ("Candi\u200bdate: Synthetic Given Family.", "forbidden candidate identity cue"),
            ("Candidate name: Synthetic Given Family.", "forbidden candidate identity cue"),
            ("Prepared for: Synthetic Given Family.", "forbidden candidate identity cue"),
            ("Pre\u200bpared for: Synthetic Given Family.", "forbidden candidate identity cue"),
            ("My name is Synthetic Given Family.", "forbidden candidate identity cue"),
            ("Nombre: Persona Sintética.", "forbidden candidate identity cue"),
            ("Nombre del candidato: Persona Sintética.", "forbidden candidate identity cue"),
            ("Me llamo Persona Sintética.", "forbidden candidate identity cue"),
            ("Copied directly from the LinkedIn profile.", "forbidden raw-profile alias"),
            ("Copied directly from the Linked\u200bIn profile.", "forbidden raw-profile alias"),
            ("Exact copied headline text from the profile.", "forbidden raw-profile alias"),
            ("Texto exacto copiado del perfil.", "forbidden raw-profile alias"),
            ("Confidential employer: Synthetic Systems.", "forbidden confidential identity cue"),
            ("Confidential emplo\u200byer: Synthetic Systems.", "forbidden confidential identity cue"),
            ("Empresa confidencial: Sistemas Sintéticos.", "forbidden confidential identity cue"),
        )
        for text, fragment in cases:
            with self.subTest(text=text):
                dossier = mutate_path(self.es_dossier, ("evidence", 0, "paraphrase"), text)
                errors = self.validate_dossier(dossier)
                self.assertTrue(any(fragment in error for error in errors), errors)

    def test_confirmation_copy_requires_one_linked_question(self) -> None:
        mutated = copy.deepcopy(self.es_dossier)
        mutated["questions"] = []
        self.assertIn(
            "confirmation copy requires its decision-changing question",
            self.validate_dossier(mutated),
        )

    def test_confirmation_screen_bridge_requires_one_linked_question(self) -> None:
        mutated = copy.deepcopy(self.es_dossier)
        mutated["screen_bridge"]["state"] = "requires_confirmation"
        mutated["screen_bridge"]["claim_ids"] = ["C-002"]
        mutated["screen_bridge"]["evidence_ids"] = ["E-004"]
        mutated["screen_bridge"]["evidence_state"] = "candidate_reported"
        self.assertIn(
            "screen_bridge confirmation requires its decision-changing question",
            self.validate_dossier(mutated),
        )

    def test_confirmation_screen_bridge_rejects_a_question_for_other_copy(self) -> None:
        mutated = copy.deepcopy(self.es_dossier)
        mutated["screen_bridge"]["state"] = "requires_confirmation"
        mutated["screen_bridge"]["claim_ids"] = ["C-002"]
        mutated["screen_bridge"]["evidence_ids"] = ["E-004"]
        mutated["screen_bridge"]["evidence_state"] = "candidate_reported"
        mutated["screen_bridge"]["question_rank"] = 1
        self.assertIn(
            "screen_bridge confirmation requires its decision-changing question",
            self.validate_dossier(mutated),
        )

    def test_decision_consumers_cannot_promote_referenced_state(self) -> None:
        mutations = (
            ("priority", ("priorities", 0), "E-003", "priorities[0].evidence_state"),
            ("dimension", ("dimensions", 3), "E-003", "dimensions[3].evidence_state"),
            ("visual", ("visual_review", "photo"), "E-003", "visual_review.photo.evidence_state"),
            ("verdict", ("verdict",), "E-003", "verdict.evidence_state"),
            ("recruiter", ("recruiter_scan", "ambiguity"), "E-003", "recruiter_scan.ambiguity.evidence_state"),
            ("copy", ("copy_blocks", 2), "E-003", "copy_blocks[2].evidence_state"),
            ("hold", ("do_not_change", 0), "E-003", "do_not_change[0].evidence_state"),
            ("bridge", ("screen_bridge",), "E-003", "screen_bridge.evidence_state"),
        )
        for label, path, evidence_id, error_path in mutations:
            with self.subTest(label=label):
                dossier = self.review_contract_dossier()
                target = dossier
                for component in path:
                    target = target[component]
                target["evidence_ids"] = [evidence_id]
                target["evidence_state"] = "verified"
                self.assertIn(
                    f"{error_path} exceeds referenced evidence state",
                    self.validate_dossier(dossier),
                )

    def test_decision_guidance_requires_exact_non_dangling_evidence(self) -> None:
        mutations = (
            ("priority", ("priorities", 0, "evidence_ids"), "priorities[0].evidence_ids"),
            ("dimension", ("dimensions", 1, "evidence_ids"), "dimensions[1].evidence_ids"),
            ("visual", ("visual_review", "photo", "evidence_ids"), "visual_review.photo.evidence_ids"),
            ("verdict", ("verdict", "evidence_ids"), "verdict.evidence_ids"),
            ("recruiter", ("recruiter_scan", "understood_signal", "evidence_ids"), "recruiter_scan.understood_signal.evidence_ids"),
        )
        for label, path, error_path in mutations:
            with self.subTest(label=label):
                dossier = mutate_path(self.review_contract_dossier(), path, ["E-999"])
                self.assertIn(
                    f"{error_path} references unknown identifier",
                    self.validate_dossier(dossier),
                )

    def test_focus_is_a_closed_localized_target_under_review(self) -> None:
        mutations = (
            ("flat expertise", "Senior Jenkins expert", "focus must be an object"),
            (
                "unsupported factual expertise",
                {"statement": "Senior Jenkins expert", "state": "target_under_review", "claim_ids": []},
                "focus.statement must use the localized target-under-review prefix",
            ),
            (
                "unsupported focus state",
                {"statement": "Objetivo bajo revisión: roles de entrega.", "state": "established_expertise", "claim_ids": []},
                "focus.state must be target_under_review",
            ),
        )
        for label, focus, expected in mutations:
            with self.subTest(label=label):
                dossier = self.review_contract_dossier()
                dossier["focus"] = focus
                self.assertIn(expected, self.validate_dossier(dossier))

    def test_full_visual_score_requires_one_authorized_capture_and_reconciles(self) -> None:
        mutations = (
            (
                "capture mismatch",
                ("visual_review", "banner", "capture_ref"),
                "CAP-002",
                "visual_review components must share the authorized visual capture",
            ),
            (
                "aggregate mismatch",
                ("dimensions", 0, "score"),
                75,
                "dimensions[0].score does not match visual component scores",
            ),
            (
                "unauthorized source",
                ("evidence", 5, "source_kind"),
                "candidate_statement",
                "visual_review.photo requires verified authorized-visible evidence",
            ),
        )
        for label, path, replacement, expected in mutations:
            with self.subTest(label=label):
                dossier = mutate_path(self.review_contract_dossier(), path, replacement)
                self.assertIn(expected, self.validate_dossier(dossier))

    def test_partial_visual_evidence_remains_unscored(self) -> None:
        dossier = copy.deepcopy(self.en_dossier)
        self.assertEqual(dossier["evidence_scope"].get("visual_state"), "partial_visual")
        visual = next(row for row in dossier["dimensions"] if row["dimension"] == "visual")
        self.assertEqual(visual["state"], "not_evaluated")
        self.assertIsNone(visual["score"])
        self.assertEqual(self.validate_dossier(dossier), [])

    def test_unknown_evaluated_dimension_returns_errors_without_raising(self) -> None:
        dossier = self.review_contract_dossier()
        dossier["dimensions"][0]["dimension"] = "unknown"
        try:
            errors = self.validate_dossier(dossier)
        except Exception as error:  # pragma: no cover - assertion reports the unsafe type
            self.fail(f"validator raised {type(error).__name__}")
        self.assertIn("dimensions[0].dimension has invalid dimension", errors)

    def test_unsupported_field_errors_do_not_echo_supplied_key_text(self) -> None:
        supplied_keys = ("private candidate detail", "secret-looking attacker key")
        for index, supplied_key in enumerate(supplied_keys):
            with self.subTest(location=index):
                dossier = self.review_contract_dossier()
                target = dossier if index == 0 else dossier["evidence"][0]
                target[supplied_key] = "benign"
                errors = self.validate_dossier(dossier)
                self.assertIn(
                    "dossier has unsupported fields" if index == 0 else "evidence[0] has unsupported fields",
                    errors,
                )
                self.assertTrue(all(supplied_key not in error for error in errors))


class ExecutiveCareerDossierEvidenceModuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator()
        self.markdown_validator = load_markdown_validator()
        self.es_dossier = load_fixture("scenario-a-es.json")
        self.analytics_dossier = load_fixture("scenario-analytics-es.json")
        self.market_dossier = load_fixture("scenario-market-en.json")

    def observed_analytics_dossier(self) -> dict[str, object]:
        dossier = copy.deepcopy(self.analytics_dossier)
        dossier["evidence"].append(
            {
                "id": "E-020",
                "state": "verified",
                "section": "analytics",
                "source_kind": "consented_aggregate",
                "paraphrase": "A consented aggregate observation is available for this report.",
                "capture_ref": None,
            }
        )
        dossier["analytics"] = {
            "state": "observed_aggregate",
            "explicit_report_consent": True,
            "observed_as_of": "2026-08-07",
            "window_days": 30,
            "raw_records_retained": False,
            "profile_views": 12,
            "inbound_contacts": 3,
            "qualified_contacts": 1,
            "qualified_contact_rate": 33.33,
            "evidence_ids": ["E-020"],
            "causality_boundary": "observed_not_attributed",
        }
        dossier["privacy"]["aggregate_analytics_included"] = True
        return dossier

    def dated_market_dossier_with_full_scorecard(self) -> dict[str, object]:
        dossier = copy.deepcopy(self.analytics_dossier)
        dossier["evidence"].append(
            {
                "id": "E-020",
                "state": "verified",
                "section": "market",
                "source_kind": "dated_vacancy_research",
                "paraphrase": "A dated vacancy sample supports separate guidance.",
                "capture_ref": None,
            }
        )
        dossier["market_context"] = copy.deepcopy(self.market_dossier["market_context"])
        dossier["market_context"]["evidence_ids"] = ["E-020"]
        dossier["market_context"]["target_roles"][0]["evidence_ids"] = ["E-020"]
        return dossier

    def synchronize_coverage(self, dossier: dict[str, object]) -> None:
        score, scored, not_scored, confidence = self.validator.calculate_dossier_score(
            dossier["dimensions"]
        )
        dossier["coverage"] = {
            "evaluated_count": sum(
                row["state"] == "evaluated" for row in dossier["dimensions"]
            ),
            "scored_weight": scored,
            "not_scored_weight": not_scored,
            "overall_score": score,
            "confidence": confidence,
        }

    def test_evidence_module_fixtures_are_valid_and_tracked_analytics_is_value_free(self) -> None:
        self.assertEqual(self.validator.validate_dossier(self.analytics_dossier), [])
        self.assertEqual(self.validator.validate_dossier(self.market_dossier), [])
        self.assertEqual(
            self.analytics_dossier["analytics"],
            {"state": "not_requested", "reason": "No se solicitó una observación agregada."},
        )
        specification = importlib.util.spec_from_file_location(
            "repository_privacy_for_dossier_test", PRIVACY_SCANNER_PATH
        )
        assert specification is not None and specification.loader is not None
        scanner = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(scanner)
        for fixture_name in ("scenario-analytics-es.json", "scenario-market-en.json"):
            with self.subTest(fixture=fixture_name):
                path = Path(
                    "tests/evals/with-skill/fixtures/executive-career-dossier/"
                    f"{fixture_name}"
                )
                text = (REPO_ROOT / path).read_text(encoding="utf-8")
                self.assertEqual(scanner.scan_text(path, text), {})

    def test_analytics_requires_explicit_consent_date_and_aggregates(self) -> None:
        for field in (
            "explicit_report_consent",
            "observed_as_of",
            "window_days",
            "raw_records_retained",
        ):
            with self.subTest(field=field):
                mutated = self.observed_analytics_dossier()
                del mutated["analytics"][field]
                self.assertIn(
                    f"analytics missing required field: {field}",
                    self.validator.validate_dossier(mutated),
                )

    def test_analytics_rejects_named_raw_and_unreconciled_values(self) -> None:
        forbidden = {
            "company_name": "Example Company",
            "visitor_name": "Example Person",
            "message_text": "private message",
            "company_logo": "logo",
            "profile_url": "https://www.linkedin.com/in/example",
            "city": "small locality",
        }
        for key, value in forbidden.items():
            with self.subTest(key=key):
                mutated = self.observed_analytics_dossier()
                mutated["analytics"][key] = value
                errors = self.validator.validate_dossier(mutated)
                self.assertIn("analytics has unsupported fields", errors)
                self.assertTrue(all(key not in error and value not in error for error in errors))
        mutated = self.observed_analytics_dossier()
        mutated["analytics"]["qualified_contact_rate"] = 99.0
        self.assertIn(
            "analytics.qualified_contact_rate does not reconcile",
            self.validator.validate_dossier(mutated),
        )

    def test_analytics_rejects_invalid_counts_dates_and_references(self) -> None:
        cases = (
            ("negative count", "profile_views", -1, "analytics.profile_views must be a non-negative integer"),
            ("qualified above inbound", "qualified_contacts", 4, "analytics.qualified_contacts cannot exceed inbound_contacts"),
            ("future date", "observed_as_of", "2026-08-08", "analytics.observed_as_of cannot be after evidence_as_of"),
            ("unknown evidence", "evidence_ids", ["E-999"], "analytics.evidence_ids references unknown identifier"),
        )
        for label, field, value, expected in cases:
            with self.subTest(label=label):
                mutated = self.observed_analytics_dossier()
                mutated["analytics"][field] = value
                self.assertIn(expected, self.validator.validate_dossier(mutated))

    def test_profile_score_dimensions_reject_analytics_and_market_evidence(self) -> None:
        sources = (
            ("analytics", self.observed_analytics_dossier()),
            ("market", self.dated_market_dossier_with_full_scorecard()),
        )
        for source, dossier in sources:
            self.assertEqual(self.validator.validate_dossier(dossier), [])
            for index, dimension in enumerate(dossier["dimensions"]):
                with self.subTest(source=source, dimension=dimension["dimension"]):
                    mutated = copy.deepcopy(dossier)
                    row = mutated["dimensions"][index]
                    row.update(
                        {
                            "state": "evaluated",
                            "score": 100,
                            "reason": "This score uses attached profile evidence.",
                            "evidence_state": "verified",
                        }
                    )
                    if row["dimension"] == "visual":
                        mutated["visual_review"]["photo"]["score"] = 100
                        mutated["visual_review"]["banner"]["score"] = 100
                        mutated["visual_review"]["photo"]["evidence_ids"].append("E-020")
                        row["evidence_ids"] = sorted(
                            set(mutated["visual_review"]["photo"]["evidence_ids"])
                            | set(mutated["visual_review"]["banner"]["evidence_ids"])
                        )
                    else:
                        row["evidence_ids"] = ["E-020"]
                    self.synchronize_coverage(mutated)
                    self.assertIn(
                        f"dimensions[{index}].evidence_ids must use profile evidence for the dimension",
                        self.validator.validate_dossier(mutated),
                    )

    def test_candidate_claims_and_copy_reject_analytics_and_market_evidence(self) -> None:
        sources = (
            ("analytics", self.observed_analytics_dossier()),
            ("market", self.dated_market_dossier_with_full_scorecard()),
        )
        consumers = (
            ("claim", ("claims", 0, "evidence_ids"), "claims[0].evidence_ids must use candidate-profile evidence"),
            ("copy block", ("copy_blocks", 0, "evidence_ids"), "copy_blocks[0].evidence_ids must use candidate-profile evidence"),
            ("screen bridge", ("screen_bridge", "evidence_ids"), "screen_bridge.evidence_ids must use candidate-profile evidence"),
        )
        for source, dossier in sources:
            for consumer, path, expected in consumers:
                with self.subTest(source=source, consumer=consumer):
                    mutated = mutate_path(dossier, path, ["E-020"])
                    self.assertIn(expected, self.validator.validate_dossier(mutated))

    def test_not_researched_market_cannot_carry_market_values(self) -> None:
        for key, value in (
            ("target_roles", ["Unresearched Role"]),
            ("salary_range", "PRIVATE-MARKET-VALUE"),
            ("demand_strength", "PRIVATE-DEMAND-VALUE"),
        ):
            with self.subTest(key=key):
                mutated = copy.deepcopy(self.es_dossier)
                mutated["market_context"][key] = value
                errors = self.validator.validate_dossier(mutated)
                self.assertIn("market_context not_researched must contain no market values", errors)
                self.assertTrue(all(key not in error and str(value) not in error for error in errors))

    def test_not_researched_market_reason_rejects_unsupported_prose_without_echo(self) -> None:
        cases = (
            "Salary demand is high in the market. CANARY-EN-701",
            "This profile will rank first. CANARY-EN-702",
            "El salario y la demanda laboral son altos. CANARY-ES-703",
            "Este perfil lidera el ranking del mercado. CANARY-ES-704",
        )
        for text in cases:
            with self.subTest(locale=text[:2]):
                mutated = copy.deepcopy(self.analytics_dossier)
                mutated["market_context"]["reason"] = text
                errors = self.validator.validate_dossier(mutated)
                self.assertIn(
                    "market_context.reason market language requires linked dated market evidence",
                    errors,
                )
                self.assertTrue(all("CANARY-" not in error for error in errors))

    def test_employment_continuity_guard_rejects_separation_imperatives_without_echo(self) -> None:
        cases = (
            (("market_context", "reason"), "Resign now and leave your job."),
            (("priorities", 0, "why_now"), "You should quit your current job."),
            (("priorities", 0, "action"), "Leave your employer today."),
            (("priorities", 0, "title"), "Create a voluntary gap."),
            (("priorities", 0, "problem"), "Reduce your working hours."),
            (("priorities", 0, "done_when"), "Leave your employer today."),
            (("seven_day_plan", 0, "action"), "Renuncia ahora y deja tu empleo."),
            (("seven_day_plan", 0, "done_when"), "Deja tu trabajo y crea una brecha laboral."),
            (("seven_day_plan", 0, "action"), "Reduce tu jornada laboral."),
            (("market_context", "reason"), "No es una recomendación. Renuncia a tu empleo."),
            (("market_context", "reason"), "This is not a recommendation. Resign now."),
            (("market_context", "reason"), "This is not a recommendation; resign now."),
            (("market_context", "reason"), "No es una recomendación, renuncia a tu empleo."),
            (("market_context", "reason"), "We do not advise you; leave your current job."),
            (("market_context", "reason"), "No es una recomendación: renuncia a tu empleo."),
            (("market_context", "reason"), "You should resign from your job."),
            (("market_context", "reason"), "You must quit your current role."),
            (("market_context", "reason"), "Resign from your current job."),
            (("market_context", "reason"), "Leave your role."),
            (("market_context", "reason"), "Leave the company."),
            (("market_context", "reason"), "Quit your employment."),
            (("market_context", "reason"), "Reducir tu jornada laboral."),
            (("market_context", "reason"), "Reducir tu horario."),
            (("market_context", "reason"), "Reduce tu jornada."),
            (("market_context", "reason"), "Reducir tus horas laborales."),
            (("market_context", "reason"), "Crear una brecha voluntaria."),
            (("market_context", "reason"), "Abandonar tu empleo."),
            (("market_context", "reason"), "Abandona tu trabajo."),
        )
        for path, text in cases:
            with self.subTest(path=path):
                errors = self.validator.validate_dossier(mutate_path(self.es_dossier, path, text))
                error_path = ""
                for part in path:
                    error_path += f"[{part}]" if isinstance(part, int) else (f".{part}" if error_path else part)
                self.assertIn(
                    f"{error_path} must preserve current employment by default",
                    errors,
                )
                self.assertTrue(all(text not in error for error in errors))

    def test_employment_continuity_guard_allows_negated_boundary_copy(self) -> None:
        dossier = copy.deepcopy(self.es_dossier)
        dossier["market_context"]["reason"] = (
            "No es una recomendación de renunciar; compara evidencia del mercado "
            "mientras preservas tu empleo actual."
        )
        dossier["seven_day_plan"][0]["action"] = (
            "Investiga opciones externas sin dejar tu empleo actual."
        )
        dossier["priorities"][0]["why_now"] = (
            "We do not advise you to leave your current job; compare market evidence."
        )
        dossier["priorities"][0]["problem"] = "No es un consejo para dejar tu empleo."
        dossier["priorities"][0]["done_when"] = "No se recomienda dejar tu empleo."
        dossier["priorities"][0]["title"] = "No se aconseja dejar tu empleo."
        dossier["priorities"][0]["action"] = "No aconsejamos dejar tu empleo."
        errors = self.validator.validate_dossier(dossier)
        self.assertFalse(
            any("must preserve current employment by default" in error for error in errors)
        )

    def test_unsupported_script_prose_is_rejected_without_echoing_content(self) -> None:
        for path in (("verdict", "rationale"), ("priorities", 0, "why_now")):
            with self.subTest(path=path):
                dossier = mutate_path(
                    self.es_dossier,
                    path,
                    "Алексей Иванов описал опыт.",
                )
                errors = self.validator.validate_dossier(dossier)
                self.assertTrue(
                    any("unsupported_script prose" in error for error in errors),
                    errors,
                )
                self.assertTrue(all("Алексей Иванов" not in error for error in errors))

    def test_dated_market_context_requires_vacancy_provenance(self) -> None:
        cases = (
            ("zero sample", ("market_context", "vacancy_sample_count"), 0, "market_context.vacancy_sample_count must be greater than zero"),
            ("future research", ("market_context", "research_date"), "2026-08-08", "market_context.research_date cannot be after evidence_as_of"),
            ("unknown market evidence", ("market_context", "evidence_ids"), ["E-999"], "market_context.evidence_ids references unknown identifier"),
            ("role evidence", ("market_context", "target_roles", 0, "evidence_ids"), ["E-001"], "market_context.target_roles[0].evidence_ids must use dated market evidence"),
            ("no public sources", ("market_context", "public_sources"), [], "market_context.public_sources has invalid item count"),
        )
        for label, path, value, expected in cases:
            with self.subTest(label=label):
                mutated = mutate_path(self.market_dossier, path, value)
                self.assertIn(expected, self.validator.validate_dossier(mutated))

    def test_market_dates_are_fresh_coherent_and_cover_multiple_sources(self) -> None:
        day_90 = copy.deepcopy(self.market_dossier)
        day_90["market_context"]["research_date"] = "2026-05-09"
        day_90["market_context"]["public_sources"][0]["access_date"] = "2026-05-09"
        self.assertEqual(self.validator.validate_dossier(day_90), [])

        leap_window = copy.deepcopy(day_90)
        leap_window["evidence_as_of"] = "2024-03-01"
        leap_window["evidence_scope"]["captured_as_of"] = "2024-03-01"
        leap_window["market_context"]["research_date"] = "2023-12-02"
        leap_window["market_context"]["public_sources"][0]["access_date"] = "2023-12-02"
        self.assertEqual(self.validator.validate_dossier(leap_window), [])

        cases = (
            (
                "research day 91",
                ("market_context", "research_date"),
                "2026-05-08",
                "market_context.research_date is older than 90 days",
            ),
            (
                "access day 91",
                ("market_context", "public_sources", 0, "access_date"),
                "2026-05-08",
                "market_context.public_sources[0].access_date is older than 90 days",
            ),
            (
                "access after research",
                ("market_context", "public_sources", 0, "access_date"),
                "2026-08-07",
                "market_context.public_sources[0].access_date cannot be after research_date",
            ),
            (
                "invalid leap research date",
                ("market_context", "research_date"),
                "2026-02-29",
                "market_context.research_date must be an ISO date",
            ),
            (
                "invalid leap access date",
                ("market_context", "public_sources", 0, "access_date"),
                "2026-02-29",
                "market_context.public_sources[0].access_date must be an ISO date",
            ),
        )
        for label, path, value, expected in cases:
            with self.subTest(label=label):
                mutated = mutate_path(self.market_dossier, path, value)
                errors = self.validator.validate_dossier(mutated)
                self.assertIn(expected, errors)
                self.assertTrue(all(value not in error for error in errors))

        multiple = copy.deepcopy(self.market_dossier)
        second = copy.deepcopy(multiple["market_context"]["public_sources"][0])
        second["url"] = "https://www.themuse.com/advice/how-to-use-linkedin"
        second["access_date"] = "2026-08-07"
        multiple["market_context"]["public_sources"].append(second)
        self.assertIn(
            "market_context.public_sources[1].access_date cannot be after research_date",
            self.validator.validate_dossier(multiple),
        )

    def test_public_source_wrappers_preserve_registry_and_url_policy(self) -> None:
        sources = self.markdown_validator.resolve_methodology_sources(
            ("skills", "good_profile")
        )
        self.assertEqual(
            [source["source_category"] for source in sources],
            ["skills", "good_profile"],
        )
        self.assertEqual(
            [source["url"] for source in sources],
            [
                "https://www.linkedin.com/help/linkedin/answer/a549047",
                "https://www.linkedin.com/help/linkedin/answer/a554351",
            ],
        )
        with self.assertRaises(TypeError):
            sources[0]["url"] = "https://www.linkedin.com/help/linkedin/answer/a000000"  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "methodology source category is unsupported"):
            self.markdown_validator.resolve_methodology_sources(("private category",))
        for malformed in (None, "skills", ("skills", "skills"), ("skills", [])):
            with self.subTest(malformed_type=type(malformed).__name__):
                with self.assertRaisesRegex(
                    ValueError, "methodology source category is unsupported"
                ):
                    self.markdown_validator.resolve_methodology_sources(malformed)

        cases = (
            ("https://www.themuse.com/advice/linkedin-profile-tips", []),
            ("http://www.themuse.com/advice/linkedin-profile-tips", ["secondary URL must use HTTPS"]),
            ("https://user:pass@career.public-domain.com/article", ["secondary URL cannot include credentials"]),
            ("https://career.public-domain.com:8443/article", ["secondary URL cannot include a port"]),
            ("https://127.1/article", ["secondary URL host must be a public hostname"]),
            ("https://www.linkedin.com/in", ["secondary URL cannot be a LinkedIn profile URL"]),
            ("https://www.themuse.com/advice/linkedin-profile-tips?token=opaque", ["secondary URL cannot include a sensitive query or fragment"]),
        )
        for value, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(
                    self.markdown_validator.validate_secondary_source_url(value),
                    expected,
                )

    def test_market_context_never_changes_linkedin_score(self) -> None:
        expected = self.validator.calculate_dossier_score(self.market_dossier["dimensions"])
        mutated = copy.deepcopy(self.market_dossier)
        mutated["market_context"]["vacancy_sample_count"] = 999
        mutated["market_context"]["target_roles"][0]["required_signals"].append(
            "Additional dated signal"
        )
        self.assertEqual(
            self.validator.calculate_dossier_score(mutated["dimensions"]), expected
        )
        self.assertEqual(
            mutated["coverage"]["overall_score"],
            self.market_dossier["coverage"]["overall_score"],
        )

    def test_market_language_is_gated_across_candidate_facing_dossier_prose(self) -> None:
        mutations = (
            ("focus", ("focus", "statement"), "Target under review: roles with high employer demand."),
            ("verdict", ("verdict", "rationale"), "High employer demand makes this urgent."),
            ("priority", ("priorities", 0, "why_now"), "Salary demand is rising in the market."),
            ("recruiter", ("recruiter_scan", "positioning_bridge", "statement"), "This profile will rank highly in a strong market."),
            ("dimension", ("dimensions", 1, "reason"), "The current market makes this signal important."),
            ("copy", ("copy_blocks", 0, "why_it_works"), "It targets high employer demand."),
            ("plan", ("seven_day_plan", 0, "done_when"), "The salary ranking is documented."),
        )
        for label, path, text in mutations:
            with self.subTest(label=label):
                dossier = mutate_path(self.es_dossier, path, text)
                errors = self.validator.validate_dossier(dossier)
                error_path = ""
                for part in path:
                    if isinstance(part, int):
                        error_path += f"[{part}]"
                    else:
                        error_path += ("." if error_path else "") + part
                self.assertIn(
                    f"{error_path} market language requires linked dated market evidence",
                    errors,
                )
                self.assertTrue(all(text not in error for error in errors))

    def test_absent_analytics_rejects_fabricated_measures_dossier_wide(self) -> None:
        paths = (
            ("verdict", "statement"),
            ("priorities", 0, "problem"),
            ("recruiter_scan", "ambiguity", "statement"),
            ("dimensions", 1, "reason"),
            ("copy_blocks", 0, "why_it_works"),
            ("do_not_change", 0, "reason"),
            ("questions", 0, "changes"),
            ("seven_day_plan", 0, "done_when"),
        )
        for path in paths:
            with self.subTest(path=path):
                dossier = mutate_path(
                    self.es_dossier,
                    path,
                    "El perfil recibió 42 vistas y 7 contactos esta semana.",
                )
                error_path = ""
                for component in path:
                    error_path += (
                        f"[{component}]"
                        if isinstance(component, int)
                        else ("." if error_path else "") + component
                    )
                self.assertIn(
                    f"{error_path} analytics measures require observed aggregate analytics",
                    self.validator.validate_dossier(dossier),
                )

    def test_unresearched_market_rejects_demand_claims_dossier_wide(self) -> None:
        paths = (
            ("verdict", "statement"),
            ("priorities", 0, "problem"),
            ("recruiter_scan", "ambiguity", "statement"),
            ("dimensions", 1, "reason"),
            ("copy_blocks", 0, "why_it_works"),
            ("do_not_change", 0, "reason"),
            ("questions", 0, "changes"),
            ("seven_day_plan", 0, "done_when"),
        )
        statements = (
            "Hay muchas vacantes para este perfil.",
            "Employers actively seek this type of profile.",
        )
        for path, text in zip(paths, statements * 4, strict=True):
            with self.subTest(path=path, text=text):
                dossier = mutate_path(self.es_dossier, path, text)
                error_path = ""
                for component in path:
                    error_path += (
                        f"[{component}]"
                        if isinstance(component, int)
                        else ("." if error_path else "") + component
                    )
                self.assertIn(
                    f"{error_path} demand language requires linked dated market evidence",
                    self.validator.validate_dossier(dossier),
                )

    def test_linked_dated_market_language_is_allowed_without_score_effect(self) -> None:
        dossier = copy.deepcopy(self.market_dossier)
        dossier["priorities"][0]["why_now"] = "Dated vacancy evidence shows employer demand for the required signal."
        dossier["priorities"][0]["evidence_ids"].append("E-008")
        before = dossier["coverage"]["overall_score"]
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        self.assertEqual(dossier["coverage"]["overall_score"], before)

    def test_observed_analytics_does_not_authorize_free_prose_or_unreconciled_numbers(self) -> None:
        cases = (
            "Profile views rose strongly during the observation window.",
            "The profile received 999 views during the observation window.",
            "Las visualizaciones crecieron con fuerza durante el periodo.",
        )
        for text in cases:
            with self.subTest(text=text):
                dossier = mutate_path(
                    self.observed_analytics_dossier(),
                    ("priorities", 0, "why_now"),
                    text,
                )
                self.assertIn(
                    "priorities[0].why_now analytics language must come from structured aggregates",
                    self.validator.validate_dossier(dossier),
                )

    def test_analytics_prose_is_normalized_and_confined_to_structured_values(self) -> None:
        outside_cases = (
            "Profile vi\u200bews doubled this week.",
            "Profile visibility doubled this week.",
            "La visibilidad del perfil se duplicó esta semana.",
            "La tasa de conver\u200bsión mejoró esta semana.",
            "El perfil tuvo 999 vistas esta semana.",
            "El alcance del perfil aumentó esta semana.",
            "Profile engagement increased this week.",
            "Profile traffic doubled this week.",
            "A dozen visits were recorded this week.",
        )
        for text in outside_cases:
            with self.subTest(text=text):
                dossier = mutate_path(self.es_dossier, ("priorities", 0, "why_now"), text)
                self.assertIn(
                    "priorities[0].why_now analytics language must come from structured aggregates",
                    self.validator.validate_dossier(dossier),
                )

        for reason in (
            "The profile received 999 views.",
            "Profile engagement increased this week.",
        ):
            with self.subTest(reason=reason):
                dossier = mutate_path(self.es_dossier, ("analytics", "reason"), reason)
                self.assertIn(
                    "analytics.reason cannot contain analytics measures or trends",
                    self.validator.validate_dossier(dossier),
                )

        for text in (
            "Profile visibility doubled this week.",
            "La visibilidad del perfil se duplicó esta semana.",
        ):
            with self.subTest(observed=text):
                dossier = mutate_path(
                    self.observed_analytics_dossier(),
                    ("priorities", 0, "why_now"),
                    text,
                )
                self.assertIn(
                    "priorities[0].why_now analytics language must come from structured aggregates",
                    self.validator.validate_dossier(dossier),
                )

    def test_dated_market_context_does_not_globally_authorize_demand_or_volume(self) -> None:
        cases = (
            "Employers strongly seek this profile.",
            "There are 999 vacancies for this profile.",
            "Hay abundante demanda para este perfil.",
            "Vacancies are abundant for this profile.",
            "Companies are eager to hire this profile.",
            "Sobran oportunidades laborales para este perfil.",
            "Este perfil es muy solicitado por empresas.",
            "Las empresas compiten por este talento.",
            "Hiring demand is strong for this profile.",
            "This profile is widely sought after by companies.",
        )
        for text in cases:
            with self.subTest(text=text):
                dossier = mutate_path(
                    self.market_dossier,
                    ("priorities", 0, "why_now"),
                    text,
                )
                dossier["priorities"][0]["evidence_ids"].append("E-008")
                self.assertIn(
                    "priorities[0].why_now demand or volume is not reconciled to dated market evidence",
                    self.validator.validate_dossier(dossier),
                )

    def test_market_claims_are_normalized_locally_referenced_and_sample_reconciled(self) -> None:
        cases = (
            "Companies are ea\u200bger to hire this profile.",
            "Vacancies are abun\u200bdant for this profile.",
            "Demand outpaces supply for this profile.",
            "Roles are difficult for employers to fill.",
            "Talent with this profile is scarce.",
            "El talento con este perfil escasea para los empleadores.",
            "Employers struggle to fill roles like this.",
            "Profiles like this are scarce.",
            "There is a candidate shortage for roles like this.",
            "There is a talent shortage for this profile.",
            "Open roles exceed available candidates.",
            "There aren't enough candidates for roles like this.",
            "There are too few candidates for roles like this.",
            "There are 4 vacancies for this profile.",
        )
        for text in cases:
            with self.subTest(text=text):
                dossier = mutate_path(self.market_dossier, ("priorities", 0, "why_now"), text)
                self.assertIn(
                    "priorities[0].why_now market claims require local dated market evidence",
                    self.validator.validate_dossier(dossier),
                )

        for text in (
            "There are 999 vacancies for this profile.",
            "Dated research covers nine vacancies in the sample.",
            "Dated research covers forty vacancies in the sample.",
            "La investigación fechada cubre nueve vacantes en la muestra.",
            "Dated research covers a couple of vacancies in the sample.",
            "La investigación fechada cubre un par de vacantes en la muestra.",
        ):
            with self.subTest(mismatched_volume=text):
                mismatched = mutate_path(
                    self.market_dossier,
                    ("priorities", 0, "why_now"),
                    text,
                )
                mismatched["priorities"][0]["evidence_ids"].append("E-008")
                self.assertIn(
                    "priorities[0].why_now market vacancy volume must equal the dated sample",
                    self.validator.validate_dossier(mismatched),
                )

        for text in (
            "Dated research covers one hundred one vacancies in the sample.",
            "La investigación fechada cubre ciento uno vacantes en la muestra.",
        ):
            with self.subTest(invalid_compound_volume=text):
                invalid = mutate_path(
                    self.market_dossier,
                    ("priorities", 0, "why_now"),
                    text,
                )
                invalid["market_context"]["vacancy_sample_count"] = 1
                invalid["priorities"][0]["evidence_ids"].append("E-008")
                self.assertIn(
                    "priorities[0].why_now market vacancy volume must equal the dated sample",
                    self.validator.validate_dossier(invalid),
                )

        for text in (
            "Dated research covers 4 vacancies in the sample.",
            "Dated research covers four vacancies in the sample.",
            "La investigación fechada cubre cuatro vacantes en la muestra.",
        ):
            with self.subTest(reconciled_volume=text):
                linked = mutate_path(
                    self.market_dossier,
                    ("priorities", 0, "why_now"),
                    text,
                )
                linked["priorities"][0]["evidence_ids"].append("E-008")
                self.assertEqual([], self.validator.validate_dossier(linked))

    def test_bounded_word_number_parser_covers_english_spanish_and_collectives(self) -> None:
        cases = {
            "zero": 0,
            "nineteen": 19,
            "twenty one": 21,
            "forty": 40,
            "ninety-nine": 99,
            "one hundred": 100,
            "cero": 0,
            "diecinueve": 19,
            "veintiuno": 21,
            "cuarenta": 40,
            "noventa y nueve": 99,
            "cien": 100,
            "a dozen": 12,
            "una docena": 12,
            "a couple": 2,
            "un par": 2,
            "a couple of": 2,
            "un par de": 2,
        }
        for phrase, expected in cases.items():
            with self.subTest(phrase=phrase):
                self.assertEqual(expected, self.validator.parse_bounded_number(phrase))
        for phrase in ("one hundred one", "ciento uno", "thousand", "mil"):
            with self.subTest(out_of_bounds=phrase):
                self.assertIsNone(self.validator.parse_bounded_number(phrase))

    def test_verdict_sentence_count_ignores_common_abbreviations(self) -> None:
        dossier = mutate_path(
            self.es_dossier,
            ("verdict", "statement"),
            "La evidencia, p. ej. el titular, permite priorizar claridad.",
        )
        self.assertEqual([], self.validator.validate_dossier(dossier))

    def test_verdict_sentence_count_ignores_decimal_versions(self) -> None:
        dossier = mutate_path(
            self.es_dossier,
            ("verdict", "statement"),
            "La versión 2.0 permite priorizar claridad.",
        )
        self.assertEqual([], self.validator.validate_dossier(dossier))


class ExecutiveCareerDossierRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_score_is_half_up_and_withheld_below_seventy_five_weight(self) -> None:
        domains = [
            {"dimension": "visual", "state": "evaluated", "score": 68},
            {"dimension": "headline", "state": "evaluated", "score": 68},
            {"dimension": "about", "state": "evaluated", "score": 68},
            {"dimension": "experience", "state": "evaluated", "score": 68},
            {"dimension": "skills", "state": "evaluated", "score": 68},
            {"dimension": "proof", "state": "evaluated", "score": 68},
            {"dimension": "completeness", "state": "not_evaluated", "score": None},
        ]
        self.assertEqual(
            self.validator.calculate_dossier_score(domains),
            (68, 90, 10, "high"),
        )
        domains[-2] = {"dimension": "proof", "state": "not_evaluated", "score": None}
        self.assertEqual(
            self.validator.calculate_dossier_score(domains),
            (68, 80, 20, "medium"),
        )
        domains[-3] = {"dimension": "skills", "state": "not_evaluated", "score": None}
        self.assertEqual(
            self.validator.calculate_dossier_score(domains),
            (None, 65, 35, "medium"),
        )

    def test_loader_rejects_duplicate_keys_without_echoing_content(self) -> None:
        path = REPO_ROOT / "tests" / "tmp-executive-dossier-duplicate.json"
        self.addCleanup(path.unlink, missing_ok=True)
        path.write_text('{"locale":"es","locale":"en"}', encoding="utf-8")
        with self.assertRaisesRegex(self.validator.DossierLoadError, "duplicate JSON key"):
            self.validator.load_dossier(path)

    def test_locale_enum_rejects_non_string_json_values_without_crashing(self) -> None:
        dossier = load_fixture("scenario-a-es.json")
        for value in ({}, []):
            with self.subTest(value=value):
                mutated = copy.deepcopy(dossier)
                mutated["locale"] = value
                errors = self.validator.validate_dossier(mutated)
                self.assertTrue(any("locale has invalid value" in error for error in errors), value)

    def test_loader_rejects_symlink_input_but_accepts_regular_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            link = root / "link.json"
            target.write_bytes((FIXTURE_ROOT / "scenario-a-es.json").read_bytes())

            loaded = self.validator.load_dossier(target)
            self.assertEqual(loaded["schema_version"], "executive-career-dossier-v1")

            link.symlink_to(target)
            with self.assertRaisesRegex(self.validator.DossierLoadError, "symlink"):
                self.validator.load_dossier(link)


class ExecutiveCareerDossierRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.renderer = load_renderer()
        cls.fixture_path = FIXTURE_ROOT / "scenario-a-es.json"
        cls.es_dossier = load_fixture("scenario-a-es.json")
        cls.en_dossier = load_fixture("scenario-c-en.json")

    def render(self, dossier: dict[str, object]) -> str:
        return self.renderer.render_dossier_html(dossier)

    def test_screen_preparation_card_uses_bridge_claims_and_rank_one_question(self) -> None:
        html = self.render(self.es_dossier)

        self.assertIn("Preparación para la primera conversación", html)
        self.assertIn("Enfoque profesional claro", html)
        self.assertIn("No afirmar todavía", html)
        self.assertIn("Ensayo", html)
        self.assertEqual(html.count('id="questions-title"'), 1)
        self.assertNotRegex(html, r"\b(?:E|C)-\d{3}\b")

    def test_renderer_rejects_legacy_linkedin_profile_urls_without_echoing_them(self) -> None:
        linkedin_host = "linkedin" + ".com"
        for value in (
            f"www.{linkedin_host}/pub/synthetic-sentinel/42/7b/123",
            f"{linkedin_host}/pub/synthetic-sentinel/42/7b/123",
        ):
            with self.subTest(value=value):
                dossier = copy.deepcopy(self.es_dossier)
                dossier["verdict"]["rationale"] = value
                with self.assertRaises(self.renderer.DossierValidationError) as context:
                    self.render(dossier)
                self.assertNotIn(value, "\n".join(context.exception.errors))

    def test_renderer_rejects_unsupported_script_prose_without_echoing_content(self) -> None:
        for path in (("verdict", "rationale"), ("priorities", 0, "why_now")):
            with self.subTest(path=path):
                dossier = copy.deepcopy(self.es_dossier)
                target = dossier
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = "Алексей Иванов описал опыт."
                with self.assertRaises(self.renderer.DossierValidationError) as context:
                    self.render(dossier)
                self.assertTrue(
                    any("unsupported_script prose" in error for error in context.exception.errors),
                    context.exception.errors,
                )
                self.assertNotIn("Алексей Иванов", str(context.exception.errors))

    def test_screen_preparation_card_localizes_english_labels(self) -> None:
        html = self.render(self.en_dossier)

        self.assertIn("First-conversation preparation", html)
        self.assertIn("Do not claim yet", html)
        self.assertIn("Rehearsal", html)

    def test_screen_preparation_card_has_semantic_state_and_content_structure(self) -> None:
        dossier = copy.deepcopy(self.es_dossier)
        dossier["screen_bridge"]["state"] = "ready"
        dossier["screen_bridge"]["claim_ids"] = ["C-001"]
        dossier["screen_bridge"]["evidence_ids"] = ["E-001", "E-002"]
        dossier["screen_bridge"]["evidence_state"] = "verified"
        dossier["screen_bridge"]["question_rank"] = 1
        dossier["questions"][0]["linked_copy_category"] = "screen_bridge"
        html = self.renderer._render_screen_bridge(dossier, "es")

        self.assertIn(
            '<section class="card screen-preparation-card span-7" '
            'aria-labelledby="screen-preparation-title">',
            html,
        )
        self.assertIn(
            '<p class="readiness-chip screen-preparation-state '
            'screen-preparation-state--ready">Enfoque profesional claro</p>',
            html,
        )
        self.assertIn('id="screen-preparation-title"', html)
        self.assertIn(
            '<section class="screen-preparation-evidence" '
            'aria-labelledby="screen-preparation-evidence-title">', html,
        )
        self.assertIn('<h3 id="screen-preparation-evidence-title">Evidencia para usar</h3>', html)
        self.assertRegex(html, r'class="[^"]*screen-preparation-boundary')
        self.assertIn(
            '<section class="screen-preparation-question" '
            'aria-labelledby="screen-preparation-question-title">',
            html,
        )
        self.assertIn(
            '<h3 id="screen-preparation-question-title">Pregunta para aclarar</h3>',
            html,
        )
        self.assertIn('<p id="screen-preparation-question-text">¿Qué ejemplo confirmado describe mejor el alcance de la habilidad reportada?</p>', html)
        self.assertIn(
            'aria-describedby="screen-preparation-question-title screen-preparation-question-text">', html,
        )
        self.assertLess(html.index("screen-preparation-boundary"), html.index("screen-preparation-question"))
        self.assertLess(html.index("screen-preparation-question"), html.index("screen-preparation-rehearsal"))
        self.assertIn(
            '<aside class="screen-preparation-handoff" '
            'aria-labelledby="screen-preparation-handoff-title" '
            'aria-describedby="screen-preparation-question-title screen-preparation-question-text">',
            html,
        )
        self.assertIn("Ensayo privado siguiente", html)
        self.assertIn("Tu respuesta es efímera y no se guarda", html)
        self.assertLess(html.index("screen-preparation-question"), html.index("screen-preparation-handoff"))
        self.assertLess(html.index("screen-preparation-handoff"), html.index("screen-preparation-rehearsal"))
        self.assertIn('class="screen-preparation-rehearsal"', html)
        self.assertIn("@media (prefers-contrast: more)", self.renderer.CSS_PATH.read_text(encoding="utf-8"))

    def test_screen_preparation_evidence_has_localized_empty_state(self) -> None:
        for source, locale, expected in (
            (self.es_dossier, "es", "No hay evidencia utilizable para esta conversación todavía."),
            (self.en_dossier, "en", "No usable evidence is available for this conversation yet."),
        ):
            dossier = copy.deepcopy(source)
            for row in dossier["claims"] + dossier["evidence"]:
                row["state"] = "unknown"
            html = self.renderer._render_screen_bridge(dossier, locale)
            self.assertIn(f'<p class="screen-preparation-evidence-empty" role="status">{expected}</p>', html)
            self.assertNotIn('<ul class="clean-list"></ul>', html)

    def test_screen_preparation_html_preserves_rank_two_bridge_question(self) -> None:
        dossier = copy.deepcopy(self.es_dossier)
        dossier["screen_bridge"].update({
            "state": "requires_confirmation",
            "question_rank": 2,
            "copy": "El ejemplo permanece pendiente de confirmación.",
        })
        dossier["questions"].append({
            "rank": 2,
            "question": "Pregunta de puente de rango dos.",
            "changes": "Cambiaría la preparación del puente.",
            "linked_copy_category": "screen_bridge",
            "evidence_ids": ["E-004"],
        })
        html = self.renderer._render_screen_bridge(dossier, "es")
        self.assertIn("Pregunta de puente de rango dos.", html)
        self.assertIn('id="screen-preparation-question-text"', html)
        self.assertNotIn("Ensayo privado siguiente", html)
        self.assertIn("Preparación manual", html)
        self.assertIn(
            '<aside class="screen-preparation-manual-note" '
            'aria-labelledby="screen-preparation-manual-title" '
            'aria-describedby="screen-preparation-question-title screen-preparation-question-text">',
            html,
        )
        self.assertIn("Siguiente paso manual", html)
        self.assertNotIn(">Ensayo<", html)
        css = self.renderer.CSS_PATH.read_text(encoding="utf-8")
        self.assertIn(".screen-preparation-manual-note", css)
        self.assertIn("screen-preparation-manual-note { break-inside: avoid", css)

    def test_question_region_and_cards_have_accessible_names(self) -> None:
        html = self.render(self.es_dossier)

        self.assertIn(
            '<section class="section-block" aria-labelledby="questions-title">',
            html,
        )
        self.assertIn(
            '<article class="card question-card span-4" '
            'aria-labelledby="question-title-1">',
            html,
        )
        self.assertIn('<h3 id="question-title-1">', html)

    def test_screen_preparation_confirmation_and_omit_states_are_categorical_not_numeric(self) -> None:
        cases = (
            ("requires_confirmation", "Confirmación pendiente"),
            ("omit", "Omitir por ahora"),
        )
        for state, label in cases:
            with self.subTest(state=state):
                dossier = copy.deepcopy(self.es_dossier)
                dossier["screen_bridge"]["state"] = state
                if state == "omit":
                    dossier["screen_bridge"]["copy"] = None

                html = self.renderer._render_screen_bridge(dossier, "es")

                self.assertIn(
                    f'screen-preparation-state--{state.replace("_", "-")}', html
                )
                self.assertIn(label, html)
                self.assertNotRegex(
                    html,
                    r'(?is)<p class="readiness-chip[^"]*">[^<]*\d',
                )

    def test_screen_preparation_renders_a_rank_two_bridge_question(self) -> None:
        dossier = copy.deepcopy(self.es_dossier)
        bridge = dossier["screen_bridge"]
        bridge.update(
            {
                "state": "requires_confirmation",
                "copy": "El ejemplo permanece pendiente de confirmación.",
                "claim_ids": ["C-002"],
                "evidence_ids": ["E-004"],
                "evidence_state": "candidate_reported",
                "question_rank": 2,
            }
        )
        dossier["questions"].append(
            {
                "rank": 2,
                "question": "Pregunta de puente de rango dos.",
                "changes": "Cambiaría la preparación del puente.",
                "linked_copy_category": "screen_bridge",
                "evidence_ids": ["E-004"],
            }
        )

        view = self.renderer._screen_bridge_view(dossier, "es")

        self.assertEqual(view["question"], "Pregunta de puente de rango dos.")

    def test_screen_preparation_opener_is_labeled_as_a_private_draft(self) -> None:
        for dossier, label in (
            (self.es_dossier, "Borrador privado"),
            (self.en_dossier, "Private draft"),
        ):
            with self.subTest(locale=dossier["locale"]):
                html = self.render(dossier)

                self.assertIn(
                    f'<span class="label">{label}</span><p class="copy-text">', html
                )

    def test_valid_dossier_renders_offline_semantic_html(self) -> None:
        rendered = self.renderer.render_dossier_html(self.es_dossier)

        self.assertTrue(rendered.casefold().startswith("<!doctype html>"))
        self.assertEqual(rendered.count("<h1"), 1)
        self.assertIn('lang="es"', rendered)
        self.assertIn("Veredicto ejecutivo", rendered)
        self.assertIn("Lectura en siete segundos", rendered)
        self.assertIn("Confianza: alta", rendered)
        self.assertNotIn("Confianza: high", rendered)
        self.assertIn('<span class="state-chip">Necesita confirmación</span>', rendered)
        self.assertEqual(rendered.count('data-priority-card="true"'), 3)
        self.assertEqual(rendered.count('data-dimension-card="true"'), 7)

    def test_dossier_footer_preserves_employment_continuity_in_english_and_spanish(self) -> None:
        for dossier, expected, absent in (
            (
                self.es_dossier,
                "Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
                "Este análisis evalúa opciones y desarrollo profesional; no recomienda renunciar ni dejar tu empleo. Tú decides qué sigue.",
            ),
            (
                self.en_dossier,
                "This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.",
                "This analysis evaluates professional options and development; it does not recommend resigning or leaving your job. You decide what comes next.",
            ),
        ):
            with self.subTest(locale=dossier["locale"]):
                rendered = self.renderer.render_dossier_html(dossier)
                self.assertIn(expected, rendered)
                self.assertNotIn(absent, rendered)
                self.assertIn('</strong> <span class="employment-boundary">', rendered)
                self.assertIn("</strong> <span class=\"employment-boundary\">", rendered)

    def test_copy_controls_have_stable_names_and_live_status_targets(self) -> None:
        rendered = self.renderer.render_dossier_html(self.es_dossier)
        buttons = re.findall(
            r'<button[^>]*data-copy-target="([^"]+)"[^>]*aria-describedby="([^"]+)"[^>]*>(.*?)</button>',
            rendered,
        )
        statuses = re.findall(
            r'<(?:span|p)[^>]*id="([^"]+)"[^>]*role="status"[^>]*aria-live="polite"[^>]*aria-atomic="true"',
            rendered,
        )
        self.assertEqual(len(buttons), 3)
        self.assertEqual(len(statuses), 3)
        self.assertTrue(all(f"{source_id}-status" in described for source_id, described, _ in buttons))
        self.assertTrue(all(label == "Copiar borrador" for _, _, label in buttons))
        self.assertIn("Borrador copiado", rendered)
        self.assertIn("No se pudo copiar; selecciona y copia el texto", rendered)
        self.assertIn("Necesita confirmación; conserva este texto como borrador privado.", rendered)

    def test_copy_controls_have_unique_localized_accessible_context(self) -> None:
        for dossier in (self.es_dossier, self.en_dossier):
            rendered = self.renderer.render_dossier_html(dossier)
            buttons = {
                target: (label, visible)
                for target, label, visible in re.findall(
                    r'<button[^>]*data-copy-target="([^"]+)"[^>]*aria-label="([^"]+)"[^>]*>([^<]+)</button>',
                    rendered,
                )
            }
            expected = {
                f"copy-source-{index}": (
                    f"{self.renderer.COPY[dossier['locale']]['copy_button']}: "
                    f"{self.renderer.COPY_LABELS[dossier['locale']][block['category']]}"
                )
                for index, block in enumerate(dossier["copy_blocks"], start=1)
                if block["copy"] is not None
            }
            self.assertEqual(
                {target: (label, self.renderer.COPY[dossier['locale']]['copy_button']) for target, label in expected.items()},
                buttons,
            )
            self.assertEqual(len(buttons), len({label for label, _ in buttons.values()}))
            for label, visible in buttons.values():
                self.assertEqual(self.renderer.COPY[dossier['locale']]['copy_button'], visible)
                self.assertIn("Copy draft" if dossier["locale"] == "en" else "Copiar borrador", label)

    def test_dossier_article_cards_have_named_headings_in_spanish_and_english(self) -> None:
        selectors = (
            'data-priority-card="true"',
            'data-dimension-card="true"',
            'class="card visual-card span-6"',
            'class="card copy-card span-4"',
        )
        for dossier in (self.es_dossier, self.en_dossier):
            rendered = self.renderer.render_dossier_html(dossier)
            for marker in selectors:
                with self.subTest(locale=dossier["locale"], marker=marker):
                    cards = re.findall(
                        rf'<article\b(?=[^>]*{re.escape(marker)})[^>]*aria-labelledby="([^"]+)"[^>]*>(.*?)</article>',
                        rendered,
                        re.DOTALL,
                    )
                    self.assertTrue(cards)
                    for heading_id, body in cards:
                        self.assertEqual(
                            1,
                            len(re.findall(rf'<h3\s+id="{re.escape(heading_id)}">', body)),
                        )
                    self.assertEqual(len(cards), len({heading_id for heading_id, _ in cards}))
    def test_confirmation_boundary_is_localized_and_associated_only_when_needed(self) -> None:
        for dossier, expected, absent in (
            (self.es_dossier, "Necesita confirmación; conserva este texto como borrador privado.", "Needs confirmation; keep this text as a private draft."),
            (self.en_dossier, "Needs confirmation; keep this text as a private draft.", "Necesita confirmación; conserva este texto como borrador privado."),
        ):
            rendered = self.renderer.render_dossier_html(dossier)
            self.assertIn(expected, rendered)
            self.assertNotIn(absent, rendered)
            self.assertIn("aria-describedby=\"copy-source-2-status copy-source-2-confirmation\"", rendered)

    def test_copy_handler_updates_status_without_renaming_button(self) -> None:
        rendered = self.renderer.render_dossier_html(self.en_dossier)
        self.assertIn("status.textContent = copied ? button.dataset.copySuccess : button.dataset.copyFailure", rendered)
        self.assertNotIn("button.textContent = copied", rendered)
        self.assertIn("class=\"copy-status no-print\"", rendered)

    def test_copy_handler_announces_missing_source_as_failure(self) -> None:
        rendered = self.renderer.render_dossier_html(self.en_dossier)
        self.assertIn(
            "if (!source) {\n        const status = document.getElementById(button.dataset.copyStatus);\n        if (status) status.textContent = button.dataset.copyFailure;\n        return;\n      }",
            rendered,
        )

    def test_rendered_dossier_has_private_offline_landmarks_and_skip_navigation(self) -> None:
        rendered = self.renderer.render_dossier_html(self.es_dossier)

        self.assertEqual(rendered.count("<h1"), 1)
        self.assertIn(
            '<a class="skip-link" href="#main-content">Saltar al contenido principal</a>',
            rendered,
        )
        for landmark in ("<header", '<div class="utility-actions no-print" role="group"', '<main id="main-content"', "<aside", "<footer"):
            with self.subTest(landmark=landmark):
                self.assertIn(landmark, rendered)
        self.assertNotIn("<nav", rendered)
        self.assertEqual(rendered.count('<main id="main-content" class="shell" tabindex="-1">'), 1)
        self.assertIn(
            '<meta name="robots" content="noindex,nofollow,noarchive">',
            rendered,
        )
        self.assertIn('<meta name="referrer" content="no-referrer">', rendered)
        csp = re.search(
            r'<meta http-equiv="Content-Security-Policy" content="([^"]+)">',
            rendered,
        )
        self.assertIsNotNone(csp)
        assert csp is not None
        for directive in (
            "default-src 'none'",
            "img-src 'none'",
            "font-src 'none'",
            "connect-src 'none'",
            "media-src 'none'",
            "object-src 'none'",
            "frame-src 'none'",
        ):
            with self.subTest(directive=directive):
                self.assertIn(directive, csp.group(1))
        self.assertNotIn("<script src=", rendered)
        self.assertNotIn("<link rel=", rendered)
        self.assertNotIn("@import", rendered)

    def test_dated_market_table_has_caption_scoped_headers_and_text_equivalent(self) -> None:
        dossier = load_fixture("scenario-market-en.json")
        rendered = self.renderer.render_dossier_html(dossier)

        self.assertIn('<table class="comparison-table">', rendered)
        self.assertIn(
            "<caption>Comparison kept separate from the LinkedIn diagnosis</caption>",
            rendered,
        )
        self.assertEqual(rendered.count('<th scope="col">'), 4)
        self.assertEqual(
            rendered.count('<th scope="row">'),
            len(dossier["market_context"]["target_roles"]),
        )
        self.assertNotIn("<canvas", rendered)
        self.assertNotIn("<svg", rendered)

    def test_controls_focus_and_motion_have_accessible_structural_guards(self) -> None:
        rendered = self.renderer.render_dossier_html(self.es_dossier)

        self.assertRegex(
            rendered,
            r"button\s*\{[^}]*min-width:\s*44px;[^}]*min-height:\s*44px;",
        )
        self.assertRegex(
            rendered,
            r"details summary\s*\{[^}]*min-height:\s*44px;",
        )
        self.assertIn("button:focus-visible", rendered)
        self.assertIn("summary:focus-visible", rendered)
        self.assertIn("main:focus-visible", rendered)
        reduced_motion = re.search(
            r"@media \(prefers-reduced-motion: reduce\)\s*\{(.+?)\n\}",
            rendered,
            re.DOTALL,
        )
        self.assertIsNotNone(reduced_motion)
        assert reduced_motion is not None
        self.assertIn("animation: none !important", reduced_motion.group(1))
        self.assertIn("transition: none !important", reduced_motion.group(1))

    def test_print_button_forced_colors_uses_explicit_system_colors_in_both_locales(self) -> None:
        for dossier, label in (
            (self.es_dossier, "Imprimir / Guardar PDF"),
            (self.en_dossier, "Print / Save PDF"),
        ):
            with self.subTest(locale=dossier["locale"]):
                rendered = self.renderer.render_dossier_html(dossier)
                self.assertIn(label, rendered)
                self.assertRegex(
                    rendered,
                    r"(?s)@media \(forced-colors: active\).*?button\s*\{[^}]*background: ButtonFace;[^}]*color: ButtonText;[^}]*border-color: ButtonText;",
                )

    def test_print_css_delegates_paper_size_without_clipping_or_controls(self) -> None:
        rendered = self.renderer.render_dossier_html(self.es_dossier)
        style = re.search(r"<style>(.+)</style>", rendered, re.DOTALL)
        self.assertIsNotNone(style)
        assert style is not None
        css = style.group(1)

        page_rules = re.findall(r"@page(?:\s+[^\s{]+)?\s*\{([^}]*)\}", css)
        self.assertEqual(page_rules, [" size: auto; margin: 14mm; "])
        self.assertNotRegex(css, r"(?m)^\s*page:\s*")
        print_css = re.search(r"@media print\s*\{(.+)\n\}", css, re.DOTALL)
        self.assertIsNotNone(print_css)
        assert print_css is not None
        self.assertIn(".no-print", print_css.group(1))
        self.assertIn("display: none !important", print_css.group(1))
        self.assertIn("break-inside: avoid", print_css.group(1))
        self.assertIn("page-break-inside: avoid", print_css.group(1))
        self.assertIn("print-color-adjust: exact", print_css.group(1))
        self.assertRegex(
            print_css.group(1),
            r"\.dossier-document\s*\{[^}]*font-size:\s*12pt;",
        )
        self.assertNotRegex(
            print_css.group(1),
            r"\.comparison-table\s*\{[^}]*font-size:",
        )

    def test_small_view_css_wraps_tables_without_horizontal_scroll_primitives(self) -> None:
        rendered = self.renderer.render_dossier_html(self.es_dossier)

        self.assertNotRegex(rendered, r"overflow-x:\s*(?:auto|scroll)")
        self.assertIn("table-layout: fixed", rendered)
        self.assertRegex(
            rendered,
            r"\.comparison-table (?:th|td),\s*\n\.comparison-table (?:th|td)\s*\{[^}]*overflow-wrap:\s*anywhere;",
        )
        table_font_sizes = re.findall(
            r"\.comparison-table\s*\{[^}]*font-size:\s*([0-9.]+)rem;",
            rendered,
            re.DOTALL,
        )
        self.assertGreater(len(table_font_sizes), 0)
        self.assertTrue(all(float(size) >= 1 for size in table_font_sizes))

    def test_numeric_progress_has_visible_text_equivalent(self) -> None:
        rendered = self.renderer.render_dossier_html(self.es_dossier)
        progress_values = re.findall(
            r'<progress value="(\d+)" max="100"[^>]*>(\d+)/100</progress>',
            rendered,
        )

        self.assertGreater(len(progress_values), 0)
        for value, fallback in progress_values:
            with self.subTest(value=value):
                self.assertEqual(value, fallback)
                self.assertIn(f'<span class="score-value">{value}/100</span>', rendered)

    def test_scorecard_progress_has_named_dimension_headings(self) -> None:
        for dossier in (self.es_dossier, self.en_dossier):
            with self.subTest(locale=dossier["locale"]):
                rendered = self.renderer.render_dossier_html(dossier)
                progress_refs = re.findall(
                    r'<progress\b[^>]*aria-labelledby="([^"]+)"[^>]*>',
                    rendered,
                )
                dimension_headings = dict(
                    re.findall(
                        r'<h3 id="(dimension-title-[^"]+)">([^<]+)</h3>',
                        rendered,
                    )
                )
                evaluated_count = sum(
                    row["state"] == "evaluated" for row in dossier["dimensions"]
                )
                self.assertEqual(evaluated_count, len(progress_refs))
                self.assertEqual(len(dimension_headings), len(dossier["dimensions"]))
                self.assertEqual(len(progress_refs), len(set(progress_refs)))
                self.assertTrue(
                    all(reference in dimension_headings for reference in progress_refs)
                )

    def test_renderer_escapes_dynamic_text(self) -> None:
        mutated = copy.deepcopy(self.es_dossier)
        mutated["verdict"]["statement"] = '<img src=x onerror="alert(1)">'

        rendered = self.renderer.render_dossier_html(mutated)

        self.assertNotIn("<img", rendered)
        self.assertIn("&lt;img", rendered)

    def test_renderer_rejects_zero_width_explicit_identity_cues(self) -> None:
        dossier = mutate_path(
            self.es_dossier,
            ("evidence", 0, "paraphrase"),
            "Candi\u200bdate: Synthetic Given Family.",
        )
        with self.assertRaises(self.renderer.DossierValidationError):
            self.renderer.render_dossier_html(dossier)

    def test_artifact_has_no_remote_dependency_or_runtime_ledger(self) -> None:
        rendered = self.renderer.render_dossier_html(self.es_dossier)

        forbidden = (
            "cdn.tailwindcss.com",
            "fonts.googleapis.com",
            "iconify",
            "fetch(",
            "XMLHttpRequest",
            "E-001",
            "C-001",
            "GAP-",
            "ACTION-",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, rendered)

    def test_atomic_private_write_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "private" / "executive-career-dossier.html"
            receipt = self.renderer.write_dossier_html(self.fixture_path, output)
            original = output.read_bytes()

            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(output.parent.stat().st_mode), 0o700)
            with self.assertRaises(FileExistsError):
                self.renderer.write_dossier_html(self.fixture_path, output)
            self.assertEqual(output.read_bytes(), original)
            self.assertEqual(
                receipt.artifact_path,
                Path(os.path.abspath(output)),
            )

    def test_writer_refuses_final_symlinks_without_touching_referent(self) -> None:
        for force in (False, True):
            with self.subTest(force=force), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                victim = root / "victim.txt"
                victim.write_text("keep", encoding="utf-8")
                output = root / "executive-career-dossier.html"
                output.symlink_to(victim)

                with self.assertRaises(OSError):
                    self.renderer.write_dossier_html(
                        self.fixture_path, output, force=force
                    )

                self.assertTrue(output.is_symlink())
                self.assertEqual(victim.read_text(encoding="utf-8"), "keep")

    def test_writer_refuses_broken_final_symlink_without_creating_referent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            victim = root / "missing-victim.html"
            output = root / "executive-career-dossier.html"
            output.symlink_to(victim)

            with self.assertRaises(OSError):
                self.renderer.write_dossier_html(self.fixture_path, output)

            self.assertTrue(output.is_symlink())
            self.assertFalse(victim.exists())

    def test_writer_refuses_symlinked_parent_without_writing_through_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real_parent = root / "real-parent"
            real_parent.mkdir()
            linked_parent = root / "linked-parent"
            linked_parent.symlink_to(real_parent, target_is_directory=True)
            output = linked_parent / "executive-career-dossier.html"

            with self.assertRaises(OSError):
                self.renderer.write_dossier_html(
                    self.fixture_path, output, force=True
                )

            self.assertFalse((real_parent / output.name).exists())

    def test_writer_refuses_symlink_in_intermediate_parent_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real_parent = root / "real-parent"
            nested_parent = real_parent / "nested"
            nested_parent.mkdir(parents=True)
            linked_parent = root / "linked-parent"
            linked_parent.symlink_to(real_parent, target_is_directory=True)
            output = linked_parent / "nested" / "executive-career-dossier.html"

            with self.assertRaises(OSError):
                self.renderer.write_dossier_html(
                    self.fixture_path, output, force=True
                )

            self.assertFalse((nested_parent / output.name).exists())

    def test_invalid_input_leaves_no_target_or_partial_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dossier_path = root / "invalid.json"
            output = root / "private" / "executive-career-dossier.html"
            mutated = copy.deepcopy(self.es_dossier)
            mutated["schema_version"] = "unsupported"
            dossier_path.write_text(json.dumps(mutated), encoding="utf-8")

            with self.assertRaises(self.renderer.DossierValidationError):
                self.renderer.write_dossier_html(dossier_path, output)

            self.assertFalse(output.exists())
            self.assertEqual(list(output.parent.glob(".*.tmp-*")), [])

    def test_force_replaces_existing_artifact_privately(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "executive-career-dossier.html"
            output.write_text("old", encoding="utf-8")
            os.chmod(output, 0o644)

            receipt = self.renderer.write_dossier_html(
                self.fixture_path, output, force=True
            )

            self.assertTrue(output.read_text(encoding="utf-8").startswith("<!doctype html>"))
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertEqual(receipt.artifact_type, "text/html")

    def test_chat_summary_is_short_human_and_metadata_free(self) -> None:
        summary = self.renderer.build_chat_summary(self.es_dossier)

        self.assertLessEqual(len(summary.split()), 180)
        self.assertIn(self.es_dossier["verdict"]["statement"], summary)
        self.assertIn(self.es_dossier["priorities"][0]["action"], summary)
        for token in (
            "schema_version",
            "evidence_id",
            "candidate_id",
            "E-001",
            "C-001",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token, summary)

    def test_chat_summary_keeps_html_shaped_values_inert(self) -> None:
        mutations = (
            ("verdict", "statement"),
            ("priorities", 0, "action"),
            ("questions", 0, "question"),
        )
        attack = '<img src=x onerror="alert(1)">'
        validator = load_validator()
        for path in mutations:
            with self.subTest(path=path):
                dossier = mutate_path(self.es_dossier, path, attack)
                self.assertEqual(validator.validate_dossier(dossier), [])

                summary = self.renderer.build_chat_summary(dossier)

                self.assertNotIn("<img", summary)
                self.assertIn("&lt;img", summary)

    def test_chat_summary_normalizes_markdown_controls_as_plain_text(self) -> None:
        dossier = copy.deepcopy(self.es_dossier)
        dossier["verdict"]["statement"] = "# Encabezado"
        dossier["priorities"][0]["action"] = (
            "[texto](javascript:alert(1)) ![imagen](data:image/svg+xml;base64,AAAA)"
        )
        dossier["questions"][0]["question"] = "```bloque``` > cita - lista"
        self.assertEqual(load_validator().validate_dossier(dossier), [])

        summary = self.renderer.build_chat_summary(dossier)

        self.assertFalse(summary.startswith("# "))
        for active_control in (
            "[texto](",
            "![imagen](",
            "```",
            " > cita",
            " - lista",
        ):
            with self.subTest(active_control=active_control):
                self.assertNotIn(active_control, summary)
        self.assertIn(r"\# Encabezado", summary)
        self.assertIn(r"\[texto\](javascript:alert(1))", summary)
        self.assertIn(r"\!\[imagen\](data:image/svg+xml;base64,AAAA)", summary)
        self.assertIn(r"\`\`\`bloque\`\`\`", summary)

    def test_maximum_valid_summary_input_is_deterministically_bounded(self) -> None:
        dossier = copy.deepcopy(self.es_dossier)
        long_text = " ".join(["proof"] * 75)
        dossier["verdict"]["statement"] = long_text
        dossier["priorities"][0]["action"] = long_text
        dossier["questions"][0]["question"] = long_text
        self.assertEqual(load_validator().validate_dossier(dossier), [])

        first = self.renderer.build_chat_summary(dossier)
        second = self.renderer.build_chat_summary(copy.deepcopy(dossier))

        self.assertLessEqual(len(first.split()), 180)
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("No se realizó ninguna acción en LinkedIn."))

    def test_rendering_is_byte_deterministic(self) -> None:
        first = self.renderer.render_dossier_html(self.en_dossier)
        second = self.renderer.render_dossier_html(copy.deepcopy(self.en_dossier))

        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))

    def test_closed_display_values_are_localized_in_spanish(self) -> None:
        dossier = load_fixture("scenario-market-en.json")
        dossier["locale"] = "es"
        dossier["focus"]["statement"] = (
            "Objetivo bajo revisión: aclarar una propuesta profesional con evidencia disponible."
        )

        rendered = self.renderer.render_dossier_html(dossier)

        self.assertIn("National aggregate · remoto", rendered)
        self.assertNotIn("National aggregate · remote", rendered)

    def test_reserved_template_tokens_remain_literal_candidate_text(self) -> None:
        for token in (
            "{{LANG}}",
            "{{TITLE}}",
            "{{INLINE_CSS}}",
            "{{HEADER}}",
            "{{MAIN}}",
            "{{INLINE_SCRIPT}}",
        ):
            with self.subTest(token=token):
                dossier = copy.deepcopy(self.es_dossier)
                dossier["verdict"]["statement"] = token
                self.assertEqual(load_validator().validate_dossier(dossier), [])

                rendered = self.renderer.render_dossier_html(dossier)

                self.assertIn(f'<p class="verdict-statement">{token}</p>', rendered)

    def test_target_and_evidence_scope_are_visible_without_internal_ids(self) -> None:
        rendered = self.renderer.render_dossier_html(self.en_dossier)

        self.assertIn(self.en_dossier["focus"]["statement"], rendered)
        self.assertIn("Evidence scope", rendered)
        self.assertIn("Mode: Mixed evidence", rendered)
        self.assertIn("Unavailable sections: Banner, Proof, Completeness", rendered)
        self.assertNotIn("CAP-002", rendered)

    def test_evidence_scope_confidence_is_distinct_from_score_coverage_confidence(self) -> None:
        high_scope = copy.deepcopy(self.es_dossier)
        low_scope = copy.deepcopy(self.es_dossier)
        low_scope["evidence_scope"]["confidence"] = "low"
        validator = load_validator()
        self.assertEqual(validator.validate_dossier(high_scope), [])
        self.assertEqual(validator.validate_dossier(low_scope), [])

        high_html = self.renderer.render_dossier_html(high_scope)
        low_html = self.renderer.render_dossier_html(low_scope)

        self.assertIn("Confianza: alta", high_html)
        self.assertIn("Confianza: alta", low_html)
        self.assertIn("Confianza del alcance: alta", high_html)
        self.assertIn("Confianza del alcance: baja", low_html)
        self.assertNotEqual(high_html, low_html)

    def test_analytics_states_and_observation_window_are_explicit(self) -> None:
        not_requested = copy.deepcopy(self.es_dossier)
        unavailable = copy.deepcopy(self.es_dossier)
        unavailable["analytics"] = {
            "state": "unavailable",
            "reason": not_requested["analytics"]["reason"],
        }
        self.assertEqual(load_validator().validate_dossier(unavailable), [])
        observed = self._observed_analytics_dossier()

        not_requested_html = self.renderer.render_dossier_html(not_requested)
        unavailable_html = self.renderer.render_dossier_html(unavailable)
        observed_html = self.renderer.render_dossier_html(observed)

        self.assertIn("No solicitada", not_requested_html)
        self.assertIn("No disponible", unavailable_html)
        self.assertNotEqual(not_requested_html, unavailable_html)
        self.assertIn(
            "No hay una interpretación analítica porque no se solicitó una observación agregada.",
            not_requested_html,
        )
        self.assertIn(
            "No hay una interpretación analítica porque la observación agregada no estuvo disponible.",
            unavailable_html,
        )
        self.assertEqual(not_requested_html.count('<strong class="metric-value">'), 0)
        self.assertEqual(unavailable_html.count('<strong class="metric-value">'), 0)
        self.assertIn("Ventana observada: 30 días", observed_html)
        self.assertEqual(observed_html.count('<strong class="metric-value">'), 4)

    def test_market_sample_and_validated_sources_are_visible(self) -> None:
        dossier = load_fixture("scenario-market-en.json")

        rendered = self.renderer.render_dossier_html(dossier)

        self.assertIn("Dated vacancy evidence", rendered)
        self.assertIn("Dated sample: 4 vacancies", rendered)
        self.assertIn("Public vacancy research methodology", rendered)
        self.assertIn("Career research publisher", rendered)
        self.assertIn(
            'href="https://www.themuse.com/advice/linkedin-profile-tips"',
            rendered,
        )

    def test_two_analytics_cards_precede_full_width_market_section(self) -> None:
        unavailable = self.renderer.render_dossier_html(self.en_dossier)
        observed = self.renderer.render_dossier_html(
            self._observed_analytics_dossier()
        )

        for state, rendered in (("unavailable", unavailable), ("observed", observed)):
            with self.subTest(state=state):
                self.assertEqual(rendered.count('class="card analytics-card'), 2)
                self.assertIn(
                    'class="card analytics-card analytics-status-card span-6"',
                    rendered,
                )
                self.assertIn(
                    'class="card analytics-card analytics-impact-card span-6"',
                    rendered,
                )
                self.assertIn('class="card market-card span-12"', rendered)
                self.assertLess(
                    rendered.index('class="card analytics-card analytics-status-card'),
                    rendered.index('class="card market-card'),
                )
        self.assertIn("No analytics interpretation is available", unavailable)
        self.assertIn("Impacto, calidad y límite", observed)
        self.assertIn("Vistas del perfil", observed)
        self.assertIn("Tasa calificada", observed)
        self.assertIn(".comparison-table {\n  width: 100%;\n  border-collapse: collapse;\n  font-size: 1rem;", rendered)

    def test_focus_statement_does_not_repeat_its_fixed_label(self) -> None:
        rendered = self.renderer.render_dossier_html(self.en_dossier)

        self.assertEqual(rendered.count("Target under review"), 1)

    def _observed_analytics_dossier(self) -> dict[str, object]:
        dossier = copy.deepcopy(self.es_dossier)
        dossier["evidence"].append(
            {
                "id": "E-020",
                "state": "verified",
                "section": "analytics",
                "source_kind": "consented_aggregate",
                "paraphrase": "Hay una observación agregada autorizada para este informe.",
                "capture_ref": None,
            }
        )
        dossier["analytics"] = {
            "state": "observed_aggregate",
            "explicit_report_consent": True,
            "observed_as_of": "2026-08-07",
            "window_days": 30,
            "raw_records_retained": False,
            "profile_views": 12,
            "inbound_contacts": 3,
            "qualified_contacts": 1,
            "qualified_contact_rate": 33.33,
            "evidence_ids": ["E-020"],
            "causality_boundary": "observed_not_attributed",
        }
        dossier["privacy"]["aggregate_analytics_included"] = True
        self.assertEqual(load_validator().validate_dossier(dossier), [])
        return dossier


class ExecutiveCareerDossierCliTests(unittest.TestCase):
    def run_cli(self, *arguments: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(RENDERER_PATH), *(str(item) for item in arguments)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_validator_cli(self, dossier: object) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dossier.json"
            path.write_text(json.dumps(dossier), encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-B", str(VALIDATOR_PATH), str(path)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

    def test_validator_cli_preserves_short_diagnostic_output(self) -> None:
        baseline = load_fixture("scenario-c-en.json")
        short = copy.deepcopy(baseline)
        short["extra"] = True
        short_result = self.run_validator_cli(short)
        self.assertEqual(short_result.returncode, 2)
        self.assertEqual(short_result.stderr, "dossier has unsupported fields\n")

    def test_success_emits_one_json_receipt_and_private_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "executive-career-dossier.html"

            result = self.run_cli(
                FIXTURE_ROOT / "scenario-c-en.json", "--output", output
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            receipt = json.loads(result.stdout)
            self.assertEqual(
                set(receipt),
                {"artifact_path", "artifact_type", "locale", "chat_summary"},
            )
            self.assertEqual(
                receipt["artifact_path"],
                os.path.abspath(output),
            )
            self.assertEqual(receipt["artifact_type"], "text/html")
            self.assertEqual(receipt["locale"], "en")
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)

    def test_validation_failure_exits_two_without_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dossier_path = root / "invalid.json"
            output = root / "executive-career-dossier.html"
            dossier_path.write_text('{"schema_version":"unsupported"}', encoding="utf-8")

            result = self.run_cli(dossier_path, "--output", output)

            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertFalse(output.exists())
            self.assertNotIn("Traceback", result.stderr)

    def test_symlink_input_exits_two_without_rendering_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            link = root / "link.json"
            output = root / "executive-career-dossier.html"
            regular_output = root / "regular-executive-career-dossier.html"
            target.write_bytes((FIXTURE_ROOT / "scenario-a-es.json").read_bytes())

            regular_result = self.run_cli(target, "--output", regular_output)
            self.assertEqual(regular_result.returncode, 0, regular_result.stderr)
            self.assertTrue(regular_output.is_file())

            link.symlink_to(target)

            result = self.run_cli(link, "--output", output)

            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertIn("symlink", result.stderr)
            self.assertFalse(output.exists())

    def test_existing_target_exits_three_without_changing_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "executive-career-dossier.html"
            output.write_text("keep", encoding="utf-8")

            result = self.run_cli(
                FIXTURE_ROOT / "scenario-a-es.json", "--output", output
            )

            self.assertEqual(result.returncode, 3)
            self.assertEqual(result.stdout, "")
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")
            self.assertNotIn("Traceback", result.stderr)

    def test_expected_write_failures_exit_three_without_path_or_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent_file = root / "parent-file"
            parent_file.write_text("keep", encoding="utf-8")
            output = parent_file / "executive-career-dossier.html"

            result = self.run_cli(
                FIXTURE_ROOT / "scenario-a-es.json", "--output", output
            )

            self.assertEqual(result.returncode, 3)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "cannot write dossier artifact\n")
            self.assertNotIn(str(root), result.stderr)
            self.assertEqual(parent_file.read_text(encoding="utf-8"), "keep")

    def test_force_cannot_replace_output_directory_or_leak_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "existing-directory"
            output.mkdir()

            result = self.run_cli(
                FIXTURE_ROOT / "scenario-a-es.json",
                "--output",
                output,
                "--force",
            )

            self.assertEqual(result.returncode, 3)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "cannot write dossier artifact\n")
            self.assertNotIn(str(root), result.stderr)
            self.assertTrue(output.is_dir())

    def test_missing_home_alias_exits_three_without_path_or_traceback(self) -> None:
        output = (
            "~job_search_coach_user_that_does_not_exist_8f311/"
            "executive-career-dossier.html"
        )

        result = self.run_cli(
            FIXTURE_ROOT / "scenario-a-es.json", "--output", output
        )

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "cannot write dossier artifact\n")
        self.assertNotIn("Traceback", result.stderr)
        self.assertNotIn("job_search_coach", result.stderr)


class CandidateFacingTextSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_markdown_validator()

    def test_guard_tokens_reuses_precompiled_controlled_term_patterns(self) -> None:
        original_escape = self.validator.re.escape
        self.validator.re.escape = lambda value: (_ for _ in ()).throw(AssertionError("re.escape called during guard scan"))
        try:
            tokens = self.validator._guard_tokens("No private analytics or recruiter message.")
        finally:
            self.validator.re.escape = original_escape
        self.assertIn("private", tokens)

    def test_public_wrapper_preserves_bundle_independent_safety_checks(self) -> None:
        errors = self.validator.validate_candidate_facing_text(
            "I sent the recruiter a message. I guarantee an interview."
        )
        self.assertEqual(
            errors,
            [
                "client report cannot claim an external action was executed",
                "client report cannot guarantee an employment or platform outcome",
            ],
        )
