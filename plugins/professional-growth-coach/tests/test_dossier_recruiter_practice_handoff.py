import copy
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_private_schema_conformance import validate_schema_instance

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_dossier_recruiter_practice_handoff as handoff_builder
from build_dossier_recruiter_practice_handoff import build_handoff
from validate_dossier_recruiter_practice_handoff import validate_handoff
from dossier_practice_safe_text import is_identity_free_handoff_text, is_safe_handoff_text


class DossierRecruiterPracticeHandoffTests(unittest.TestCase):
    def setUp(self):
        fixture_path = ROOT / "tests/fixtures/dossier-recruiter-practice-handoff/valid-es.json"
        self.fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.dossier = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/executive-career-dossier"
                / self.fixture["base_dossier_fixture"]
            ).read_text(encoding="utf-8")
        )
        overrides = self.fixture["dossier_overrides"]
        self.dossier["screen_bridge"] = overrides["screen_bridge"]
        self.dossier["questions"][0]["linked_copy_category"] = overrides["question_linked_copy_category"]
        self.dossier["copy_blocks"][1].update(overrides["about_opening"])

    def _v2_dossier(self):
        dossier = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/executive-career-dossier-v2/scenario-a-es.json"
            ).read_text(encoding="utf-8")
        )
        overrides = self.fixture["dossier_overrides"]
        dossier["screen_bridge"] = copy.deepcopy(overrides["screen_bridge"])
        dossier["questions"][0]["linked_copy_category"] = overrides[
            "question_linked_copy_category"
        ]
        dossier["copy_blocks"][1].update(copy.deepcopy(overrides["about_opening"]))
        return dossier

    def test_builds_closed_source_projection(self):
        handoff = build_handoff(
            self.dossier,
            self.fixture["vacancy"],
            self.fixture["source_snapshot"],
        )
        self.assertEqual(self.fixture["expected"], handoff)
        schema = json.loads(
            (ROOT / "schemas/dossier-recruiter-practice-handoff-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual([], validate_schema_instance(handoff, schema))

    def test_builder_rejects_a_fabricated_but_well_formed_snapshot(self):
        fabricated = self.fixture["source_snapshot"][:-1] + ("0" if self.fixture["source_snapshot"][-1] != "0" else "1")
        with self.assertRaisesRegex(ValueError, "source_snapshot must match dossier"):
            build_handoff(self.dossier, self.fixture["vacancy"], fabricated)

    def test_snapshot_changes_with_dossier_content(self):
        self.assertEqual(
            self.fixture["source_snapshot"],
            handoff_builder.snapshot_for_dossier(self.dossier),
        )
        changed = copy.deepcopy(self.dossier)
        changed["questions"][0]["question"] = "Pregunta segura distinta."
        self.assertNotEqual(
            self.fixture["source_snapshot"],
            handoff_builder.snapshot_for_dossier(changed),
        )
        with self.assertRaisesRegex(ValueError, "source_snapshot must match dossier"):
            build_handoff(changed, self.fixture["vacancy"], self.fixture["source_snapshot"])

    def test_builder_accepts_v2_through_a_pure_v1_projection_and_binds_the_original_snapshot(self):
        dossier = self._v2_dossier()
        source_snapshot = handoff_builder.snapshot_for_dossier(dossier)

        handoff = build_handoff(dossier, self.fixture["vacancy"], source_snapshot)

        self.assertEqual(self.fixture["expected"]["dossier_projection"], handoff["dossier_projection"])
        self.assertEqual(source_snapshot, handoff["source_snapshot"])
        self.assertNotEqual(source_snapshot, handoff_builder.snapshot_for_dossier(
            handoff_builder._load_sibling("executive_career_dossier_v2_compat").project_v2_to_v1(dossier)
        ))

    def test_validator_accepts_v2_source_with_the_original_snapshot_and_v1_practice_projection(self):
        dossier = self._v2_dossier()
        source_snapshot = handoff_builder.snapshot_for_dossier(dossier)
        handoff = build_handoff(dossier, self.fixture["vacancy"], source_snapshot)
        practice_path = (
            ROOT.parent.parent
            / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json"
        )
        practice = json.loads(practice_path.read_text(encoding="utf-8"))
        practice.update(copy.deepcopy(handoff["practice_projection"]))

        self.assertEqual(
            [],
            validate_handoff(handoff, dossier, self.fixture["vacancy"], practice),
        )

    def test_v2_source_snapshot_fails_closed_after_ledger_priority_or_profile_section_mutation(self):
        dossier = self._v2_dossier()
        source_snapshot = handoff_builder.snapshot_for_dossier(dossier)
        mutations = (
            ("ledger", lambda value: value["section_coverage"][2].update({
                "reason": "inspection_declined",
                "inspection_request": {
                    "access_type": "read_only_visible_section_inspection",
                    "decision": "declined_for_session",
                    "scope": "current_session_only",
                    "carry_forward": False,
                },
            })),
            ("priority", lambda value: value["priorities"][0].update({
                "action": "Revisar el enfoque con una plantilla privada distinta.",
            })),
            ("profile section", lambda value: value["evidence"][0].update({
                "profile_section": "about",
            })),
        )

        for label, mutate in mutations:
            with self.subTest(label=label):
                changed = copy.deepcopy(dossier)
                mutate(changed)
                with self.assertRaises(ValueError):
                    build_handoff(changed, self.fixture["vacancy"], source_snapshot)

    def test_parity_rejects_a_fabricated_snapshot(self):
        handoff, practice = self._valid_handoff_and_practice()
        fabricated = handoff["source_snapshot"][:-1] + ("0" if handoff["source_snapshot"][-1] != "0" else "1")
        handoff["source_snapshot"] = fabricated
        handoff["practice_projection"]["handoff_context"]["source_snapshot"] = fabricated
        practice["handoff_context"]["source_snapshot"] = fabricated
        errors = validate_handoff(handoff, self.dossier, self.fixture["vacancy"], practice)
        self.assertIn("handoff.source_snapshot must match dossier content", errors)

    def _valid_handoff_and_practice(self):
        handoff = build_handoff(
            self.dossier,
            self.fixture["vacancy"],
            self.fixture["source_snapshot"],
        )
        practice_path = (
            ROOT.parent.parent
            / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json"
        )
        practice = json.loads(practice_path.read_text(encoding="utf-8"))
        practice.update(copy.deepcopy(handoff["practice_projection"]))
        return handoff, practice

    def test_parity_binds_the_sidecar_to_its_dossier_vacancy_and_practice_session(self):
        handoff, practice = self._valid_handoff_and_practice()

        self.assertEqual(
            [],
            validate_handoff(handoff, self.dossier, self.fixture["vacancy"], practice),
        )

    def test_parity_rejects_field_scoped_projection_drift_without_raw_values(self):
        handoff, practice = self._valid_handoff_and_practice()
        cases = []

        changed = copy.deepcopy(practice)
        changed["handoff_context"]["source_snapshot"] = "snap-dossier-sha256-0000000000000000000000000000000000000000000000000000000000000000"
        cases.append(("source snapshot", handoff, self.dossier, self.fixture["vacancy"], changed,
                      "practice_session.handoff_context.source_snapshot must match handoff.source_snapshot"))

        changed = copy.deepcopy(handoff)
        changed["dossier_projection"]["question_rank"] = 2
        cases.append(("rank", changed, self.dossier, self.fixture["vacancy"], practice,
                      "handoff.dossier_projection.question_rank must be 1"))

        changed = copy.deepcopy(practice)
        changed["question"]["kind"] = "proof_example"
        cases.append(("question kind", handoff, self.dossier, self.fixture["vacancy"], changed,
                      "practice_session.question.kind must match handoff.practice_projection.question.kind"))

        changed = copy.deepcopy(practice)
        changed["question"]["text"] = "Texto privado mutado"
        cases.append(("question text", handoff, self.dossier, self.fixture["vacancy"], changed,
                      "practice_session.question.text must match handoff.practice_projection.question.text"))

        changed = copy.deepcopy(practice)
        changed["requirement"]["summary"] = "Requisito privado mutado"
        cases.append(("requirement", handoff, self.dossier, self.fixture["vacancy"], changed,
                      "practice_session.requirement.summary must match handoff.practice_projection.requirement.summary"))

        changed = copy.deepcopy(practice)
        changed["question"]["id"] = "Q-002"
        changed["handoff_context"]["question_id"] = "Q-002"
        cases.append(("question ID", handoff, self.dossier, self.fixture["vacancy"], changed,
                      "practice_session.question.id must match handoff.practice_projection.question.id"))

        changed = copy.deepcopy(practice)
        changed["requirement"]["id"] = "R-002"
        changed["question"]["requirement_id"] = "R-002"
        changed["handoff_context"]["requirement_id"] = "R-002"
        cases.append(("requirement ID", handoff, self.dossier, self.fixture["vacancy"], changed,
                      "practice_session.requirement.id must match handoff.practice_projection.requirement.id"))

        changed = copy.deepcopy(practice)
        changed["facts"][0]["id"] = "F-002"
        changed["requirement"]["fact_ids"] = ["F-002"]
        changed["question"]["fact_ids"] = ["F-002"]
        changed["handoff_context"]["fact_ids"] = ["F-002"]
        cases.append(("fact ID", handoff, self.dossier, self.fixture["vacancy"], changed,
                      "practice_session.facts[0].id must match handoff.practice_projection.facts[0].id"))

        changed = copy.deepcopy(handoff)
        changed["practice_projection"]["handoff_context"]["claim_ids"] = ["C-001"]
        cases.append(("bridge claim", changed, self.dossier, self.fixture["vacancy"], practice,
                      "handoff.practice_projection.handoff_context.claim_ids must match dossier.screen_bridge.claim_ids"))

        changed = copy.deepcopy(handoff)
        changed["practice_projection"]["handoff_context"]["evidence_ids"] = ["E-001"]
        cases.append(("bridge evidence", changed, self.dossier, self.fixture["vacancy"], practice,
                      "handoff.practice_projection.handoff_context.evidence_ids must match dossier.screen_bridge.evidence_ids"))

        changed = copy.deepcopy(practice)
        changed["facts"][0]["state"] = "verified"
        cases.append(("source fact state", handoff, self.dossier, self.fixture["vacancy"], changed,
                      "practice_session.facts[0].state must match handoff.practice_projection.facts[0].state"))

        changed = copy.deepcopy(practice)
        changed["facts"][0]["summary"] = "Resumen privado mutado"
        cases.append(("source fact summary", handoff, self.dossier, self.fixture["vacancy"], changed,
                      "practice_session.facts[0].summary must match handoff.practice_projection.facts[0].summary"))

        changed = copy.deepcopy(practice)
        changed["observed_answer"] = {"id": "OBS-001", "text": "respuesta privada", "storage": "ephemeral"}
        cases.append(("prefilled answer", handoff, self.dossier, self.fixture["vacancy"], changed,
                      "practice_session.observed_answer must be absent"))

        changed = copy.deepcopy(practice)
        changed["feedback"]["score"] = "60"
        cases.append(("score", handoff, self.dossier, self.fixture["vacancy"], changed,
                      "practice_session.feedback.score must be unknown"))

        changed = copy.deepcopy(handoff)
        changed["delivery"]["auto_start"] = True
        cases.append(("auto start", changed, self.dossier, self.fixture["vacancy"], practice,
                      "handoff.delivery.auto_start must be false"))

        changed = copy.deepcopy(handoff)
        changed["dossier_projection"]["question_rank"] = True
        cases.append(("boolean rank", changed, self.dossier, self.fixture["vacancy"], practice,
                      "handoff.dossier_projection.question_rank must be 1"))

        for field, expected in (("draft_only", True), ("external_actions_authorized", False),
                                ("manual_reentry_required", True), ("auto_start", False),
                                ("raw_answer_retained", False)):
            changed = copy.deepcopy(handoff)
            changed["delivery"][field] = 1 if expected is True else 0
            cases.append((f"integer delivery {field}", changed, self.dossier, self.fixture["vacancy"], practice,
                          f"handoff.delivery.{field} must be {str(expected).lower()}"))

        changed = copy.deepcopy(handoff)
        changed["practice_projection"]["requirement"]["summary"] = "https://example.invalid/private"
        cases.append(("URL", changed, self.dossier, self.fixture["vacancy"], practice,
                      "handoff.practice_projection.requirement.summary must be safe text"))

        for label, candidate_handoff, dossier, vacancy, candidate_practice, expected in cases:
            with self.subTest(label=label):
                errors = validate_handoff(candidate_handoff, dossier, vacancy, candidate_practice)
                self.assertIn(expected, errors)
                self.assertEqual(errors, sorted(set(errors)))
                self.assertNotIn("Texto privado mutado", "\n".join(errors))
                self.assertNotIn("https://example.invalid/private", "\n".join(errors))

    def test_parity_rejects_a_missing_source_side(self):
        handoff, practice = self._valid_handoff_and_practice()

        self.assertEqual(
            ["vacancy must be an object"],
            validate_handoff(handoff, self.dossier, None, practice),
        )

    def test_parity_rejects_bridge_evidence_not_linked_by_its_claim(self):
        handoff, practice = self._valid_handoff_and_practice()
        dossier = copy.deepcopy(self.dossier)
        dossier["screen_bridge"]["evidence_ids"] = ["E-001"]

        self.assertIn(
            "dossier.screen_bridge.evidence_ids must link to dossier.screen_bridge.claim_ids",
            validate_handoff(handoff, dossier, self.fixture["vacancy"], practice),
        )

    def test_builder_rejects_a_bridge_claim_without_its_own_evidence(self):
        dossier = copy.deepcopy(self.dossier)
        dossier["screen_bridge"]["claim_ids"] = ["C-001", "C-002"]

        with self.assertRaisesRegex(
            ValueError,
            "dossier screen_bridge must back every selected claim with bridge evidence",
        ):
            build_handoff(dossier, self.fixture["vacancy"], self.fixture["source_snapshot"])

    def test_parity_rejects_a_coordinated_unbacked_bridge_claim(self):
        handoff, practice = self._valid_handoff_and_practice()
        dossier = copy.deepcopy(self.dossier)
        dossier["screen_bridge"]["claim_ids"] = ["C-001", "C-002"]
        handoff["dossier_projection"]["claim_ids"] = ["C-001", "C-002"]
        handoff["practice_projection"]["handoff_context"]["claim_ids"] = [
            "C-001",
            "C-002",
        ]
        practice["handoff_context"]["claim_ids"] = ["C-001", "C-002"]

        self.assertIn(
            "dossier.screen_bridge.claim_ids must each link to dossier.screen_bridge.evidence_ids",
            validate_handoff(handoff, dossier, self.fixture["vacancy"], practice),
        )

    def test_builder_rejects_question_evidence_outside_bridge_candidates(self):
        dossier = copy.deepcopy(self.dossier)
        dossier["questions"][0]["evidence_ids"] = ["E-001"]

        with self.assertRaisesRegex(
            ValueError,
            "dossier rank 1 question evidence must come from screen_bridge evidence",
        ):
            build_handoff(dossier, self.fixture["vacancy"], self.fixture["source_snapshot"])

    def test_parity_rejects_coordinated_source_fact_outside_bridge_candidates(self):
        handoff, practice = self._valid_handoff_and_practice()
        dossier = copy.deepcopy(self.dossier)
        dossier["questions"][0]["evidence_ids"] = ["E-001"]
        source = dossier["evidence"][0]
        handoff["dossier_projection"].update(
            {
                "question_evidence_ids": ["E-001"],
                "source_fact_evidence_id": "E-001",
                "fact_state": source["state"],
                "fact_summary": source["paraphrase"],
            }
        )
        handoff["practice_projection"]["facts"][0].update(
            {"state": source["state"], "summary": source["paraphrase"]}
        )
        practice.update(copy.deepcopy(handoff["practice_projection"]))

        errors = validate_handoff(
            handoff,
            dossier,
            self.fixture["vacancy"],
            practice,
        )
        self.assertIn(
            "dossier.questions.rank_1.evidence_ids must belong to dossier.screen_bridge.evidence_ids",
            errors,
        )
        self.assertIn(
            "handoff.dossier_projection.source_fact_evidence_id must belong to candidate bridge evidence",
            errors,
        )

    def test_builder_rejects_market_evidence_as_the_candidate_source_fact(self):
        dossier = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/executive-career-dossier/scenario-market-en.json"
            ).read_text(encoding="utf-8")
        )
        dossier["screen_bridge"] = {
            "state": "requires_confirmation",
            "copy": "I can expand on one example after confirming its scope.",
            "why_it_works": "It keeps the answer within reported evidence.",
            "claim_ids": ["C-002"],
            "evidence_ids": ["E-003"],
            "claim_boundary": "Do not expand the reported scope.",
            "evidence_state": "candidate_reported",
            "question_rank": 1,
        }
        dossier["questions"][0].update(
            {
                "question": "What does the dated vacancy sample change about the answer?",
                "changes": "It separates market context from candidate evidence.",
                "linked_copy_category": "screen_bridge",
                "evidence_ids": ["E-008"],
            }
        )
        dossier["copy_blocks"][1].update(
            {
                "state": "ready",
                "claim_ids": ["C-001"],
                "evidence_ids": ["E-001"],
                "evidence_state": "verified",
                "question_rank": None,
            }
        )
        vacancy = copy.deepcopy(self.fixture["vacancy"])
        vacancy["locale"] = "en"

        with self.assertRaisesRegex(
            ValueError,
            "dossier rank 1 question evidence must come from screen_bridge evidence",
        ):
            build_handoff(dossier, vacancy, self.fixture["source_snapshot"])

    def test_parity_rejects_coordinated_sidecar_and_session_projection_drift(self):
        handoff, practice = self._valid_handoff_and_practice()
        cases = (
            (
                "safe context",
                ("safe_context", "summary"),
                "Contexto seguro pero distinto.",
            ),
            (
                "requirement",
                ("requirement", "summary"),
                "Requisito seguro pero distinto.",
            ),
            (
                "question text",
                ("question", "text"),
                "¿Qué ejemplo seguro describe el alcance?",
            ),
            (
                "fact state",
                ("facts", 0, "state"),
                "verified",
            ),
            (
                "fact summary",
                ("facts", 0, "summary"),
                "Resumen seguro pero distinto.",
            ),
            (
                "nested snapshot",
                ("handoff_context", "source_snapshot"),
                "snap-dossier-999",
            ),
        )
        for label, path, value in cases:
            with self.subTest(label=label):
                changed_handoff = copy.deepcopy(handoff)
                changed_practice = copy.deepcopy(practice)
                sidecar_target = changed_handoff["practice_projection"]
                session_target = changed_practice
                for part in path[:-1]:
                    sidecar_target = sidecar_target[part]
                    session_target = session_target[part]
                sidecar_target[path[-1]] = value
                session_target[path[-1]] = value

                errors = validate_handoff(
                    changed_handoff,
                    self.dossier,
                    self.fixture["vacancy"],
                    changed_practice,
                )
                rendered_path = ".".join(str(part) for part in path).replace(".0.", "[0].")
                self.assertIn(
                    f"handoff.practice_projection.{rendered_path} must match expected practice projection",
                    errors,
                )
                self.assertNotIn(str(value), "\n".join(errors))

    def test_rejects_invalid_dossier_rank_and_references(self):
        mutations = []
        bad = copy.deepcopy(self.dossier); bad["screen_bridge"]["question_rank"] = None; mutations.append(bad)
        bad = copy.deepcopy(self.dossier); bad["screen_bridge"]["claim_ids"] = ["C-999"]; mutations.append(bad)
        bad = copy.deepcopy(self.dossier); bad["screen_bridge"]["evidence_ids"] = ["E-999"]; mutations.append(bad)
        bad = copy.deepcopy(self.dossier); bad["questions"][0]["evidence_ids"] = ["E-999"]; mutations.append(bad)
        for dossier in mutations:
            with self.subTest(dossier=dossier):
                with self.assertRaisesRegex(ValueError, "dossier validation failed"):
                    build_handoff(dossier, self.fixture["vacancy"], self.fixture["source_snapshot"])

    def test_rejects_malformed_snapshot_url_and_external_action_flag(self):
        with self.assertRaisesRegex(ValueError, "source_snapshot must use"):
            build_handoff(self.dossier, self.fixture["vacancy"], "dossier-001")

        url_vacancy = copy.deepcopy(self.fixture["vacancy"])
        url_vacancy["safe_context"]["summary"] = "Ver detalles en https://example.invalid/vacante"
        with self.assertRaisesRegex(ValueError, "contains forbidden safe text"):
            build_handoff(self.dossier, url_vacancy, self.fixture["source_snapshot"])

        external_vacancy = copy.deepcopy(self.fixture["vacancy"])
        external_vacancy["external_actions_authorized"] = True
        with self.assertRaisesRegex(ValueError, "vacancy has unsupported fields"):
            build_handoff(self.dossier, external_vacancy, self.fixture["source_snapshot"])

    def test_rejects_private_or_raw_vacancy_text_in_each_projected_field(self):
        private_values = {
            "url": "Consulta https://example.invalid/detalle",
            "name": "Nombre del candidato: Ana López",
            "unlabelled_candidate_name": "Candidate Ana López",
            "contact": "Teléfono de contacto: +52 55 1234 5678",
            "unlabelled_phone": "Disponible en +52 55 1234 5678",
            "raw_source": "Texto crudo del perfil de LinkedIn.",
            "session": "browser_session_id=browser-123",
            "hash": "sha256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        }
        for field in ("safe_context", "requirement"):
            for kind, value in private_values.items():
                with self.subTest(field=field, kind=kind):
                    vacancy = copy.deepcopy(self.fixture["vacancy"])
                    vacancy[field]["summary"] = value
                    with self.assertRaisesRegex(ValueError, "contains forbidden safe text"):
                        build_handoff(self.dossier, vacancy, self.fixture["source_snapshot"])

    def test_builder_rejects_unlabelled_person_name_in_source_fact_projection(self):
        dossier = copy.deepcopy(self.dossier)
        dossier["evidence"][3]["paraphrase"] = "Ana López reports Terraform experience."
        source_snapshot = handoff_builder.snapshot_for_dossier(dossier)
        with self.assertRaisesRegex(ValueError, "dossier validation failed"):
            build_handoff(dossier, self.fixture["vacancy"], source_snapshot)

    def test_identity_free_guard_rejects_person_intros_but_preserves_role_prose(self):
        for value in (
            "Ana López reports Terraform experience.",
            "Jordan Lee works at Acme Corporation.",
            "Ana López reporta experiencia con Terraform.",
            "Ana María López delivered reliability automation.",
            "Ana de la Cruz delivered reliability automation.",
            "José Luis García delivered reliability automation.",
            "Contexto seguro. Ana María López delivered reliability automation.",
        ):
            with self.subTest(rejected=value):
                self.assertFalse(is_identity_free_handoff_text(value, 500))
        for value in (
            "Senior Engineer leads incident response.",
            "Platform Engineering covers incident response scope.",
            "Oracle Cloud delivers reliability automation.",
        ):
            with self.subTest(accepted=value):
                self.assertTrue(is_identity_free_handoff_text(value, 500))

    def test_rejects_every_uri_scheme_and_local_path_in_each_vacancy_field(self):
        private_values = {
            "file_uri": "Detalles en file:///Users/Ana/private-cv.pdf",
            "ftp_uri": "Detalles en ftp://example.invalid/private-cv.pdf",
            "data_uri": "Detalles en data:text/plain,private",
            "mailto_uri": "Escribir a mailto:ana@example.org",
            "arbitrary_scheme": "Detalles en custom+private://source/value",
            "www": "Detalles en www.example.invalid/private",
            "posix_path": "Detalles en /Users/Ana/private-cv.pdf",
            "windows_path": "Details in C:\\Users\\Ana\\private-cv.pdf",
            "home_path": "Detalles en ~/private-cv.pdf",
            "relative_path": "Detalles en ../private-cv.pdf",
        }
        for field in ("safe_context", "requirement"):
            for kind, value in private_values.items():
                with self.subTest(field=field, kind=kind):
                    vacancy = copy.deepcopy(self.fixture["vacancy"])
                    vacancy[field]["summary"] = value
                    with self.assertRaisesRegex(ValueError, "contains forbidden safe text"):
                        build_handoff(
                            self.dossier,
                            vacancy,
                            self.fixture["source_snapshot"],
                        )

    def test_safe_text_preserves_natural_role_prose_and_rejects_private_roots(self):
        for value in (
            "The candidate should explain relevant scope.",
            "Recruiter screen focuses on scope.",
            "The candidate reports experience with SQL.",
        ):
            with self.subTest(value=value):
                self.assertTrue(is_safe_handoff_text(value, 500))

        for value in (
            "/root/.ssh/config",
            "/usr/local/private.txt",
            "/Library/Application Support/private.txt",
            "/Applications/private.app",
            "/mnt/private.txt",
            "/srv/private.txt",
            "//internal.example/private",
            "Candidate\u200b: Ana López",
            "www\u200b.example.invalid/private",
        ):
            with self.subTest(value=value):
                self.assertFalse(is_safe_handoff_text(value, 500))

        for character in ("\u200b", "\u202e", "\u2066", "\ufeff"):
            with self.subTest(code_point=f"U+{ord(character):04X}"):
                self.assertFalse(is_safe_handoff_text(f"Visible{character} prose", 500))

    def test_builder_guards_dossier_text_before_copying_it_to_the_sidecar(self):
        cases = (
            ("question", "questions", "question"),
            ("fact", "evidence", "paraphrase"),
        )
        for label, section, field in cases:
            with self.subTest(label=label):
                dossier = copy.deepcopy(self.dossier)
                row = dossier[section][0] if section == "questions" else dossier[section][3]
                original = row[field]
                row[field] = f"{original} file:///Users/Ana/private-cv.pdf"
                source_validator = mock.Mock()
                source_validator.validate_dossier.return_value = []
                with mock.patch.object(
                    handoff_builder,
                    "_load_dossier_validator",
                    return_value=source_validator,
                ):
                    with self.assertRaisesRegex(ValueError, "contains forbidden safe text"):
                        build_handoff(
                            dossier,
                            self.fixture["vacancy"],
                            self.fixture["source_snapshot"],
                        )

    def test_schema_rejects_private_or_raw_projected_text(self):
        schema = json.loads(
            (ROOT / "schemas/dossier-recruiter-practice-handoff-v1.schema.json").read_text(encoding="utf-8")
        )
        private_values = (
            "https://example.invalid/detalle",
            "custom+private://source/value",
            "data:text/plain,private",
            "/Users/Ana/private-cv.pdf",
            "/root/.ssh/config",
            "/usr/local/private.txt",
            "/Library/Application Support/private.txt",
            "/Applications/private.app",
            "/mnt/private.txt",
            "/srv/private.txt",
            "//internal.example/private",
            "Candidate name: Ana López",
            "Candidate Ana López",
            "Contact: ana@example.org",
            "Disponible en +52 55 1234 5678",
            "Raw job description copied here.",
            "session_id=browser-123",
            "sha256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        )
        for field in ("safe_context", "requirement"):
            for value in private_values:
                with self.subTest(field=field, value=value):
                    handoff = copy.deepcopy(self.fixture["expected"])
                    handoff["practice_projection"][field]["summary"] = value
                    self.assertTrue(validate_schema_instance(handoff, schema))

    def test_schema_preserves_natural_role_prose(self):
        schema = json.loads(
            (ROOT / "schemas/dossier-recruiter-practice-handoff-v1.schema.json").read_text(encoding="utf-8")
        )
        for value in (
            "The candidate should explain relevant scope.",
            "Recruiter screen focuses on scope.",
            "The candidate reports experience with SQL.",
        ):
            handoff = copy.deepcopy(self.fixture["expected"])
            handoff["practice_projection"]["requirement"]["summary"] = value
            self.assertEqual([], validate_schema_instance(handoff, schema), value)

    def test_schema_rejects_forbidden_text_in_every_sidecar_text_projection(self):
        schema = json.loads(
            (ROOT / "schemas/dossier-recruiter-practice-handoff-v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        paths = (
            ("dossier_projection", "fact_summary"),
            ("practice_projection", "safe_context", "summary"),
            ("practice_projection", "requirement", "summary"),
            ("practice_projection", "question", "text"),
            ("practice_projection", "facts", 0, "summary"),
        )
        for path in paths:
            with self.subTest(path=path):
                handoff = copy.deepcopy(self.fixture["expected"])
                target = handoff
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = "file:///Users/Ana/private-cv.pdf"
                self.assertTrue(validate_schema_instance(handoff, schema))

    def test_validator_rejects_forbidden_text_without_echoing_private_values(self):
        handoff, practice = self._valid_handoff_and_practice()
        cases = (
            (
                ("dossier_projection", "fact_summary"),
                "handoff.dossier_projection.fact_summary must be safe text",
            ),
            (
                ("practice_projection", "safe_context", "summary"),
                "handoff.practice_projection.safe_context must be a safe recruiter-screen context",
            ),
            (
                ("practice_projection", "requirement", "summary"),
                "handoff.practice_projection.requirement.summary must be safe text",
            ),
            (
                ("practice_projection", "question", "text"),
                "handoff.practice_projection.question.text must be safe text",
            ),
            (
                ("practice_projection", "facts", 0, "summary"),
                "handoff.practice_projection.facts[0].summary must be safe text",
            ),
        )
        private_value = "file:///Users/Ana/private-cv.pdf"
        for path, expected in cases:
            with self.subTest(path=path):
                changed = copy.deepcopy(handoff)
                target = changed
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = private_value
                errors = validate_handoff(
                    changed,
                    self.dossier,
                    self.fixture["vacancy"],
                    practice,
                )
                self.assertIn(expected, errors)
                self.assertNotIn(private_value, "\n".join(errors))

    def test_builder_caps_each_source_reference_list_at_ten(self):
        source_validator = mock.Mock()
        source_validator.validate_dossier.return_value = []

        claim_heavy = copy.deepcopy(self.dossier)
        extra_claim_ids = []
        for number in range(3, 13):
            identifier = f"C-{number:03d}"
            extra_claim_ids.append(identifier)
            claim_heavy["claims"].append(
                {
                    "id": identifier,
                    "state": "candidate_reported",
                    "paraphrase": f"Reported scope {number} requires confirmation.",
                    "evidence_ids": ["E-004"],
                    "public_use": "confirmation_required",
                }
            )
        claim_heavy["screen_bridge"]["claim_ids"] = ["C-002", *extra_claim_ids]

        evidence_heavy = copy.deepcopy(self.dossier)
        extra_evidence_ids = []
        for number in range(8, 18):
            identifier = f"E-{number:03d}"
            extra_evidence_ids.append(identifier)
            row = copy.deepcopy(evidence_heavy["evidence"][3])
            row["id"] = identifier
            evidence_heavy["evidence"].append(row)
        all_evidence_ids = ["E-004", *extra_evidence_ids]
        evidence_heavy["claims"][1]["evidence_ids"] = all_evidence_ids
        evidence_heavy["screen_bridge"]["evidence_ids"] = all_evidence_ids

        question_heavy = copy.deepcopy(evidence_heavy)
        question_heavy["screen_bridge"]["evidence_ids"] = all_evidence_ids[:10]
        question_heavy["questions"][0]["evidence_ids"] = all_evidence_ids

        cases = (
            (
                "claim_ids",
                claim_heavy,
                "screen_bridge.claim_ids must contain 1 through 10 unique references",
            ),
            (
                "evidence_ids",
                evidence_heavy,
                "screen_bridge.evidence_ids must contain 1 through 10 unique references",
            ),
            (
                "question_evidence_ids",
                question_heavy,
                "questions.rank_1.evidence_ids must contain 1 through 10 unique references",
            ),
        )
        with mock.patch.object(
            handoff_builder,
            "_load_dossier_validator",
            return_value=source_validator,
        ):
            for label, dossier, expected in cases:
                with self.subTest(label=label):
                    with self.assertRaisesRegex(ValueError, expected):
                        build_handoff(
                            dossier,
                            self.fixture["vacancy"],
                            self.fixture["source_snapshot"],
                        )

    def test_builder_normalizes_malformed_snapshot_types_to_bounded_errors(self):
        for value in (None, {}, []):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaisesRegex(ValueError, "source_snapshot must use"):
                    build_handoff(self.dossier, self.fixture["vacancy"], value)

    def test_validator_normalizes_unhashable_reference_ids_to_bounded_errors(self):
        handoff, practice = self._valid_handoff_and_practice()
        cases = (
            (
                ("dossier_projection", "claim_ids"),
                "handoff.dossier_projection.claim_ids must contain bounded identifiers",
            ),
            (
                ("dossier_projection", "evidence_ids"),
                "handoff.dossier_projection.evidence_ids must contain bounded identifiers",
            ),
            (
                ("dossier_projection", "question_evidence_ids"),
                "handoff.dossier_projection.question_evidence_ids must contain bounded identifiers",
            ),
            (
                ("practice_projection", "handoff_context", "claim_ids"),
                "handoff.practice_projection.handoff_context.claim_ids must contain bounded identifiers",
            ),
            (
                ("practice_projection", "handoff_context", "evidence_ids"),
                "handoff.practice_projection.handoff_context.evidence_ids must contain bounded identifiers",
            ),
        )
        for path, expected in cases:
            with self.subTest(path=path):
                changed = copy.deepcopy(handoff)
                target = changed
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = [{}]
                errors = validate_handoff(
                    changed,
                    self.dossier,
                    self.fixture["vacancy"],
                    practice,
                )
                self.assertIn(expected, errors)
                self.assertEqual(errors, sorted(set(errors)))

    def test_validator_normalizes_malformed_top_level_types_to_bounded_errors(self):
        handoff, practice = self._valid_handoff_and_practice()
        cases = (
            (None, self.dossier, self.fixture["vacancy"], practice, "handoff must be an object"),
            (handoff, None, self.fixture["vacancy"], practice, "dossier must be an object"),
            (handoff, self.dossier, None, practice, "vacancy must be an object"),
            (
                handoff,
                self.dossier,
                self.fixture["vacancy"],
                None,
                "practice_session must be an object",
            ),
        )
        for candidate_handoff, dossier, vacancy, session, expected in cases:
            with self.subTest(expected=expected):
                errors = validate_handoff(candidate_handoff, dossier, vacancy, session)
                self.assertIn(expected, errors)
                self.assertEqual(errors, sorted(set(errors)))

    def test_validator_enforces_ten_item_reference_ceiling(self):
        handoff, practice = self._valid_handoff_and_practice()
        cases = (
            (
                ("dossier_projection", "claim_ids"),
                [f"C-{number:03d}" for number in range(1, 12)],
                "handoff.dossier_projection.claim_ids must contain bounded identifiers",
            ),
            (
                ("dossier_projection", "evidence_ids"),
                [f"E-{number:03d}" for number in range(1, 12)],
                "handoff.dossier_projection.evidence_ids must contain bounded identifiers",
            ),
            (
                ("dossier_projection", "question_evidence_ids"),
                [f"E-{number:03d}" for number in range(1, 12)],
                "handoff.dossier_projection.question_evidence_ids must contain bounded identifiers",
            ),
        )
        for path, identifiers, expected in cases:
            with self.subTest(path=path):
                changed = copy.deepcopy(handoff)
                target = changed
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = identifiers
                self.assertIn(
                    expected,
                    validate_handoff(
                        changed,
                        self.dossier,
                        self.fixture["vacancy"],
                        practice,
                    ),
                )

    def test_builder_fails_closed_when_its_output_misses_the_sidecar_schema(self):
        private_diagnostic = "file:///Users/Ana/private-schema-diagnostic"
        with mock.patch.object(
            handoff_builder,
            "validate_schema_instance",
            return_value=[private_diagnostic],
            create=True,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "builder output failed handoff schema validation",
            ) as raised:
                build_handoff(
                    self.dossier,
                    self.fixture["vacancy"],
                    self.fixture["source_snapshot"],
                )
        self.assertNotIn(private_diagnostic, str(raised.exception))

    def test_sidecar_schema_enforces_one_to_ten_source_references(self):
        schema = json.loads(
            (ROOT / "schemas/dossier-recruiter-practice-handoff-v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        paths = (
            ("dossier_projection", "claim_ids", "C"),
            ("dossier_projection", "evidence_ids", "E"),
            ("dossier_projection", "question_evidence_ids", "E"),
            ("practice_projection", "handoff_context", "claim_ids", "C"),
            ("practice_projection", "handoff_context", "evidence_ids", "E"),
        )
        for *path, prefix in paths:
            for identifiers in ([], [f"{prefix}-{number:03d}" for number in range(1, 12)]):
                with self.subTest(path=path, count=len(identifiers)):
                    handoff = copy.deepcopy(self.fixture["expected"])
                    target = handoff
                    for part in path[:-1]:
                        target = target[part]
                    target[path[-1]] = identifiers
                    self.assertTrue(validate_schema_instance(handoff, schema))

    def test_builder_requires_the_vacancy_to_use_the_dossier_locale(self):
        vacancy = copy.deepcopy(self.fixture["vacancy"])
        vacancy["locale"] = "en"

        with self.assertRaisesRegex(
            ValueError,
            "dossier.locale must match vacancy.locale",
        ):
            build_handoff(self.dossier, vacancy, self.fixture["source_snapshot"])

    def test_parity_requires_dossier_vacancy_and_practice_locales_to_match(self):
        handoff, practice = self._valid_handoff_and_practice()
        cases = []

        vacancy = copy.deepcopy(self.fixture["vacancy"])
        vacancy["locale"] = "en"
        cases.append(
            (
                "vacancy",
                self.dossier,
                vacancy,
                practice,
                "vacancy.locale must match dossier.locale",
            )
        )

        session = copy.deepcopy(practice)
        session["locale"] = "en"
        cases.append(
            (
                "practice",
                self.dossier,
                self.fixture["vacancy"],
                session,
                "practice_session.locale must match dossier.locale",
            )
        )

        dossier = copy.deepcopy(self.dossier)
        dossier["locale"] = "en"
        cases.append(
            (
                "dossier",
                dossier,
                self.fixture["vacancy"],
                practice,
                "vacancy.locale must match dossier.locale",
            )
        )

        for label, dossier, vacancy, session, expected in cases:
            with self.subTest(label=label):
                errors = validate_handoff(handoff, dossier, vacancy, session)
                self.assertIn(expected, errors)
                self.assertEqual(errors, sorted(set(errors)))


if __name__ == "__main__":
    unittest.main()
