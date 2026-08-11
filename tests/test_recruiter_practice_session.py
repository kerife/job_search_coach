"""Contract tests for the private, identity-free recruiter practice session."""

from __future__ import annotations

import copy
import json
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
    / "validate_recruiter_practice_session.py"
)
TRIAGE_VALIDATOR_PATH = (
    REPO_ROOT
    / "plugins"
    / "professional-growth-coach"
    / "scripts"
    / "validate_private_recruiter_reply_triage.py"
)
FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "evals"
    / "with-skill"
    / "fixtures"
    / "recruiter-practice-session"
    / "session-es.json"
)
TRIAGE_FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "evals"
    / "with-skill"
    / "fixtures"
    / "private-recruiter-reply-triage"
    / "ready-en.json"
)
V2_TRIAGE_SNAPSHOT = (
    "snap-triage-sha256-"
    "85ad96e9cab8b222315a01a85d4a6f61f0d5a38650a1286773bc8e1664c15ebd"
)
V2_TRIAGE_PHONE_LIKE_SNAPSHOT = (
    "snap-triage-sha256-"
    "9cfca8aaaeb249e38dbeee70bbbcd3189173398fea1c3f9baee95fa0e56b3af0"
)


def load_fixture() -> dict[str, object]:
    value = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture must be a JSON object")
    return value


def load_triage_fixture() -> dict[str, object]:
    value = json.loads(TRIAGE_FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("triage fixture must be a JSON object")
    return value


class RecruiterPracticeSessionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.awaiting_session = load_fixture()

    def run_cli(self, session: object) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "session.json"
            path.write_text(json.dumps(session), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(VALIDATOR_PATH), str(path)],
                capture_output=True,
                text=True,
                check=False,
            )

    def assert_accepted(self, session: object) -> None:
        result = self.run_cli(session)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "valid recruiter practice session")

    def assert_rejected(self, session: object, message: str) -> None:
        result = self.run_cli(session)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(message, result.stderr)

    def run_triage_cli(self, triage: object) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "triage.json"
            path.write_text(json.dumps(triage), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(TRIAGE_VALIDATOR_PATH), str(path)],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_all_ready_triage_scopes_are_directly_assignable_to_practice_kind(self) -> None:
        cases = {
            "screen_invite": "screen_opening",
            "request_for_proof": "proof_example",
            "eligibility_question": "eligibility_boundary",
            "compensation_question": "compensation_boundary",
            "unknown": "missing_detail",
        }
        for classification, kind in cases.items():
            with self.subTest(classification=classification):
                triage = load_triage_fixture()
                triage["classification"] = classification
                triage["question"]["kind"] = kind
                triage["handoff"]["packet"]["prep_scope"] = kind
                triage["handoff"]["reentry_packet"]["prep_scope"] = kind
                triage_result = self.run_triage_cli(triage)
                self.assertEqual(triage_result.returncode, 0, triage_result.stderr)

                practice = copy.deepcopy(self.awaiting_session)
                practice["safe_context"]["summary"] = triage["safe_context"]["summary"]
                practice["facts"][0] = copy.deepcopy(triage["facts"][0])
                practice["question"]["id"] = triage["question"]["id"]
                practice["question"]["kind"] = triage["handoff"]["reentry_packet"]["prep_scope"]
                practice["question"]["text"] = triage["question"]["text"]
                practice["question"]["fact_ids"] = [triage["facts"][0]["id"]]
                practice["requirement"]["fact_ids"] = [triage["facts"][0]["id"]]
                practice["handoff_context"]["source"] = "private_recruiter_reply_triage"
                practice["handoff_context"]["source_snapshot"] = triage["handoff"]["reentry_packet"]["source_snapshot"]
                practice["handoff_context"]["question_id"] = triage["question"]["id"]
                practice["handoff_context"]["fact_ids"] = [triage["facts"][0]["id"]]
                practice["handoff_context"].pop("claim_ids")
                practice["handoff_context"].pop("evidence_ids")

                self.assertEqual(kind, triage["question"]["kind"])
                self.assertEqual(kind, triage["handoff"]["packet"]["prep_scope"])
                self.assertEqual(kind, triage["handoff"]["reentry_packet"]["prep_scope"])
                self.assertEqual(kind, practice["question"]["kind"])
                self.assertEqual(1, practice["handoff_context"]["question_rank"])
                self.assert_accepted(practice)

    def test_ready_recruiter_handoff_binds_to_answer_unaware_practice(self) -> None:
        triage = load_triage_fixture()
        triage_result = self.run_triage_cli(triage)
        self.assertEqual(triage_result.returncode, 0, triage_result.stderr)

        practice = copy.deepcopy(self.awaiting_session)
        practice["safe_context"]["summary"] = triage["safe_context"]["summary"]
        practice["facts"][0] = copy.deepcopy(triage["facts"][0])
        practice["question"] = {
            **practice["question"],
            "id": triage["question"]["id"],
            "kind": triage["question"]["kind"],
            "text": triage["question"]["text"],
            "fact_ids": [triage["facts"][0]["id"]],
        }
        practice["requirement"]["fact_ids"] = [triage["facts"][0]["id"]]
        practice["handoff_context"]["source"] = "private_recruiter_reply_triage"
        practice["handoff_context"]["source_snapshot"] = "snap-triage-001"
        self.assert_accepted(practice)
        self.assertIsNone(practice["observed_answer"])
        self.assertEqual(practice["feedback"]["score_state"], "unknown")
        triage_without_dossier_provenance = copy.deepcopy(practice)
        triage_without_dossier_provenance["handoff_context"].pop("claim_ids")
        triage_without_dossier_provenance["handoff_context"].pop("evidence_ids")
        self.assert_accepted(triage_without_dossier_provenance)
        def assert_parity(candidate: dict[str, object]) -> None:
            self.assertEqual(triage["handoff"]["reentry_packet"]["question_id"], candidate["question"]["id"])
            self.assertEqual(triage["handoff"]["reentry_packet"]["fact_id"], candidate["facts"][0]["id"])
            self.assertEqual(triage["handoff"]["reentry_packet"]["context_summary"], candidate["safe_context"]["summary"])
            self.assertEqual(triage["handoff"]["packet"]["prep_scope"], candidate["question"]["kind"])
            self.assertEqual(triage["handoff"]["packet"]["source_snapshot"], triage["handoff"]["reentry_packet"]["source_snapshot"])
            self.assertEqual(triage["handoff"]["packet"]["source_snapshot"], candidate["handoff_context"]["source_snapshot"])

        assert_parity(practice)

        invalid_source = copy.deepcopy(practice)
        invalid_source["handoff_context"]["source"] = "executive_dossier_typo"
        self.assert_rejected(invalid_source, "handoff_context.source has invalid value")

        scope_drift = copy.deepcopy(practice)
        scope_drift["question"]["kind"] = "proof_example"
        with self.assertRaises(AssertionError):
            assert_parity(scope_drift)

        snapshot_drift = copy.deepcopy(practice)
        snapshot_drift["handoff_context"]["source_snapshot"] = "snap-triage-002"
        with self.assertRaises(AssertionError):
            assert_parity(snapshot_drift)

        answered = copy.deepcopy(practice)
        answered["observed_answer"] = {"id": "OBS-001", "text": "respuesta privada", "storage": "ephemeral"}
        self.assert_rejected(answered, "pre-answer states cannot include an observed answer")
        scored = copy.deepcopy(practice)
        scored["feedback"]["score"] = "80"
        self.assert_rejected(scored, "feedback.score must be unknown before an observed answer")

        auto_start = copy.deepcopy(triage)
        auto_start["handoff"]["auto_start"] = True
        auto_result = self.run_triage_cli(auto_start)
        self.assertNotEqual(auto_result.returncode, 0)
        self.assertIn("auto_start", auto_result.stderr)

    def test_direct_triage_practice_remains_valid_without_a_dossier_sidecar(self) -> None:
        direct_triage_practice = copy.deepcopy(self.awaiting_session)
        direct_triage_practice["handoff_context"]["source"] = "private_recruiter_reply_triage"
        direct_triage_practice["handoff_context"]["source_snapshot"] = "snap-triage-001"
        direct_triage_practice["handoff_context"].pop("claim_ids")
        direct_triage_practice["handoff_context"].pop("evidence_ids")

        self.assert_accepted(direct_triage_practice)

    def test_handoff_question_rank_rejects_json_booleans_but_accepts_numeric_one(self) -> None:
        for invalid_rank in (True, False):
            with self.subTest(question_rank=repr(invalid_rank)):
                invalid = copy.deepcopy(self.awaiting_session)
                invalid["handoff_context"]["question_rank"] = invalid_rank
                self.assert_rejected(
                    invalid,
                    "handoff_context.question_rank must be 1",
                )

        for numeric_rank in (1, 1.0):
            with self.subTest(question_rank=repr(numeric_rank)):
                canonical = copy.deepcopy(self.awaiting_session)
                canonical["handoff_context"]["question_rank"] = numeric_rank
                self.assert_accepted(canonical)

    def test_cli_accepts_ready_awaiting_and_feedback_states(self) -> None:
        ready = copy.deepcopy(self.awaiting_session)
        ready["state"] = "ready_to_practice"
        awaiting = copy.deepcopy(self.awaiting_session)
        feedback = copy.deepcopy(self.awaiting_session)
        feedback["state"] = "feedback_available"
        feedback["observed_answer"] = {
            "id": "OBS-001",
            "text": "Organicé el proceso y expliqué el alcance que confirmé.",
            "storage": "ephemeral"
        }
        feedback["feedback"] = {
            "score": "unknown",
            "score_state": "categorical",
            "observations": [
                {
                    "label": "solid",
                    "statement": "La respuesta describe una acción concreta.",
                    "source_refs": ["OBS-001", "RB-001"]
                }
            ]
        }
        for state in (ready, awaiting, feedback):
            with self.subTest(state=state["state"]):
                self.assert_accepted(state)

    def test_v2_requires_separate_ui_and_content_locales_without_changing_v1(self) -> None:
        v2 = copy.deepcopy(self.awaiting_session)
        v2["schema_version"] = "recruiter-practice-session-v2"
        v2["ui_locale"] = "en"
        v2["content_locale"] = "es"
        del v2["locale"]
        self.assert_accepted(v2)

        missing_content_locale = copy.deepcopy(v2)
        del missing_content_locale["content_locale"]
        self.assert_rejected(missing_content_locale, "missing required field: content_locale")

        v1_with_v2_locales = copy.deepcopy(self.awaiting_session)
        v1_with_v2_locales.update({"ui_locale": "en", "content_locale": "es"})
        self.assert_rejected(v1_with_v2_locales, "session has unsupported fields: content_locale, ui_locale")

    def test_v2_accepts_content_bound_triage_snapshot(self) -> None:
        v2 = copy.deepcopy(self.awaiting_session)
        v2["schema_version"] = "recruiter-practice-session-v2"
        v2["ui_locale"] = "en"
        v2["content_locale"] = "es"
        del v2["locale"]
        v2["handoff_context"]["source"] = "private_recruiter_reply_triage"
        v2["handoff_context"]["source_snapshot"] = V2_TRIAGE_SNAPSHOT
        v2["handoff_context"].pop("claim_ids")
        v2["handoff_context"].pop("evidence_ids")
        self.assert_accepted(v2)

    def test_v1_rejects_content_bound_triage_snapshot_but_keeps_legacy_id(self) -> None:
        legacy = copy.deepcopy(self.awaiting_session)
        legacy["handoff_context"]["source"] = "private_recruiter_reply_triage"
        legacy["handoff_context"]["source_snapshot"] = V2_TRIAGE_SNAPSHOT
        legacy["handoff_context"].pop("claim_ids")
        legacy["handoff_context"].pop("evidence_ids")
        self.assert_rejected(legacy, "handoff_context.source_snapshot must use the bound dossier or snap-triage-000 identifier format")

        legacy["handoff_context"]["source_snapshot"] = "snap-triage-001"
        self.assert_accepted(legacy)

    def test_v2_rejects_malformed_triage_snapshot_without_echoing_value(self) -> None:
        malformed = copy.deepcopy(self.awaiting_session)
        malformed["schema_version"] = "recruiter-practice-session-v2"
        malformed["ui_locale"] = "en"
        malformed["content_locale"] = "es"
        del malformed["locale"]
        malformed["handoff_context"]["source"] = "private_recruiter_reply_triage"
        malformed["handoff_context"]["source_snapshot"] = "snap-triage-sha256-" + ("g" * 64)
        malformed["handoff_context"].pop("claim_ids")
        malformed["handoff_context"].pop("evidence_ids")
        result = self.run_cli(malformed)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("handoff_context.source_snapshot", result.stderr)
        self.assertNotIn(malformed["handoff_context"]["source_snapshot"], result.stderr)

    def test_v2_accepts_phone_like_hash_without_prose_false_positive(self) -> None:
        v2 = copy.deepcopy(self.awaiting_session)
        v2["schema_version"] = "recruiter-practice-session-v2"
        v2["ui_locale"] = "en"
        v2["content_locale"] = "es"
        del v2["locale"]
        v2["handoff_context"]["source"] = "private_recruiter_reply_triage"
        v2["handoff_context"]["source_snapshot"] = V2_TRIAGE_PHONE_LIKE_SNAPSHOT
        v2["handoff_context"].pop("claim_ids")
        v2["handoff_context"].pop("evidence_ids")
        self.assert_accepted(v2)

    def test_session_without_an_observed_answer_has_exactly_unknown_score(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["feedback"]["score"] = "75"
        self.assert_rejected(
            invalid,
            "feedback.score must be unknown before an observed answer",
        )

    def test_missing_vacancy_or_candidate_facts_fails_closed(self) -> None:
        missing_vacancy = copy.deepcopy(self.awaiting_session)
        del missing_vacancy["safe_context"]
        self.assert_rejected(missing_vacancy, "missing required field: safe_context")

        missing_facts = copy.deepcopy(self.awaiting_session)
        missing_facts["facts"] = []
        self.assert_rejected(missing_facts, "facts must contain exactly one supplied fact")

    def test_malformed_references_fail_closed(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["question"]["fact_ids"] = ["F-999"]
        self.assert_rejected(
            invalid,
            "question.fact_ids references unknown identifier",
        )

    def test_unknown_fact_reference_rejects_without_echoing_private_value(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        sentinel = "person@example.com"
        invalid["question"]["fact_ids"] = [sentinel]

        result = self.run_cli(invalid)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("question.fact_ids references unknown identifier", result.stderr)
        self.assertNotIn(sentinel, result.stderr)

    def test_unsupported_claims_are_not_part_of_the_closed_contract(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["unsupported_claim"] = "Expert in a technology without supplied evidence."
        self.assert_rejected(invalid, "session has unsupported fields: unsupported_claim")

    def test_suspicious_unsupported_field_names_are_not_echoed(self) -> None:
        for sentinel in (
            "person@example.invalid",
            "/Users/synthetic/private-case.json",
            "token_sk_live_SYNTHETIC",
        ):
            with self.subTest(sentinel=sentinel):
                invalid = copy.deepcopy(self.awaiting_session)
                invalid[sentinel] = "synthetic"

                result = self.run_cli(invalid)

                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(
                    "session has unsupported fields: <redacted-field>",
                    result.stderr,
                )
                self.assertNotIn(sentinel, result.stderr)

    def test_raw_identity_and_external_action_prose_are_rejected(self) -> None:
        identity = copy.deepcopy(self.awaiting_session)
        identity["question"]["text"] = "Candidate: Example Person. ¿Cómo responderías?"
        self.assert_rejected(identity, "session contains forbidden identity or raw-content prose")

        action = copy.deepcopy(self.awaiting_session)
        action["question"]["text"] = "Contacta al reclutador después de practicar."
        self.assert_rejected(action, "session contains external-action prose")

    def test_unsupported_script_prose_is_rejected_without_echoing_content(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["facts"][0]["summary"] = "Алексей Иванов описал опыт."
        result = self.run_cli(invalid)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("session contains forbidden unsupported_script prose", result.stderr)
        self.assertNotIn("Алексей Иванов", result.stderr)

    def test_internal_question_requirement_and_fact_ids_are_rejected_in_prose(self) -> None:
        for section, field, prose in (
            ("question", "text", "Practica Q-001 en una respuesta breve."),
            ("requirement", "summary", "R-001 es el requisito de esta práctica."),
            ("facts", "summary", "Usa F-001 como evidencia."),
        ):
            with self.subTest(section=section):
                invalid = copy.deepcopy(self.awaiting_session)
                target = invalid[section][0] if section == "facts" else invalid[section]
                target[field] = prose
                path = "facts[0].summary" if section == "facts" else f"{section}.{field}"
                self.assert_rejected(invalid, f"{path} must not expose internal identifiers")

    def test_rejects_unicode_controls_in_every_prose_field(self) -> None:
        prose_fields = (
            ("safe_context", "summary", 280),
            ("requirement", "summary", 280),
            ("question", "text", 500),
            ("facts", 0, "summary", 500),
            ("rubric", "criterion", 500),
            ("observed_answer", "text", 2000),
        )
        controls = ("\u200b", "\u202e", "\u2066", "\ufeff")
        for control in controls:
            for path in prose_fields:
                with self.subTest(code_point=f"U+{ord(control):04X}", path=path):
                    invalid = copy.deepcopy(self.awaiting_session)
                    if path[0] == "observed_answer":
                        invalid["state"] = "feedback_available"
                        invalid["observed_answer"] = {
                            "id": "OBS-001",
                            "text": f"Visible{control} prose",
                            "storage": "ephemeral",
                        }
                        invalid["feedback"] = {
                            "score": "unknown",
                            "score_state": "categorical",
                            "observations": [{
                                "label": "solid",
                                "statement": "Distinct feedback statement.",
                                "source_refs": ["OBS-001", "RB-001"],
                            }],
                        }
                    else:
                        target: object = invalid
                        for key in path[:-2]:
                            target = target[key]  # type: ignore[index]
                        target[path[-2]] = (
                            f"Visible{control} prose?" if path[0] == "question"
                            else f"Visible{control} prose"
                        )  # type: ignore[index]
                    result = self.run_cli(invalid)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    field_path = "facts[0].summary" if path[0] == "facts" else ".".join(str(part) for part in path[:2])
                    self.assertIn(
                        f"{field_path} must be non-empty prose within {path[-1]} characters",
                        result.stderr,
                    )
                    self.assertNotIn("Visible", result.stderr)

    def test_rejects_unicode_controls_in_feedback_statements(self) -> None:
        for control in ("\u200b", "\u202e", "\u2066", "\ufeff"):
            with self.subTest(code_point=f"U+{ord(control):04X}"):
                invalid = copy.deepcopy(self.awaiting_session)
                invalid["state"] = "feedback_available"
                invalid["observed_answer"] = {
                    "id": "OBS-001",
                    "text": "Expliqué una acción relevante.",
                    "storage": "ephemeral",
                }
                invalid["feedback"] = {
                    "score": "unknown",
                    "score_state": "categorical",
                    "observations": [{
                        "label": "solid",
                        "statement": f"Visible{control} feedback statement.",
                        "source_refs": ["OBS-001", "RB-001"],
                    }],
                }
                result = self.run_cli(invalid)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(
                    "feedback.observations[0].statement must be non-empty prose within 500 characters",
                    result.stderr,
                )
                self.assertNotIn("Visible", result.stderr)

    def test_internal_prose_ids_are_rejected_after_unicode_normalization(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["question"]["text"] = "Practica Ｑ－００１ en privado."
        self.assert_rejected(invalid, "question.text must not expose internal identifiers")

    def test_internal_prose_ids_are_rejected_through_format_controls(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["question"]["text"] = "Practica Q\u200b-\u200b001 en privado."
        self.assert_rejected(invalid, "question.text must not expose internal identifiers")

    def test_internal_prose_ids_are_rejected_when_separated_by_whitespace(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["question"]["text"] = "Practica Q - 001 en privado."
        self.assert_rejected(invalid, "question.text must not expose internal identifiers")

    def test_internal_prose_ids_are_rejected_when_letter_and_number_are_split(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["question"]["text"] = "Practica Q 001 en privado."
        self.assert_rejected(invalid, "question.text must not expose internal identifiers")

    def test_internal_prose_guard_covers_all_candidate_facing_fields(self) -> None:
        cases = (
            ("safe_context", "summary", "Contexto F 001."),
            ("requirement", "summary", "Requisito R 001."),
            ("rubric", "criterion", "Criterio Q 001."),
        )
        for section, field, prose in cases:
            with self.subTest(section=section):
                invalid = copy.deepcopy(self.awaiting_session)
                invalid[section][field] = prose
                self.assert_rejected(invalid, f"{section}.{field} must not expose internal identifiers")

    def test_company_identity_recruiter_action_and_readiness_percentage_are_rejected(self) -> None:
        cases = (
            ("company", "safe_context", "summary", "Empresa: Acme Servicios.", "session contains forbidden identity or raw-content prose"),
            ("recruiter_action", "question", "text", "Escribe al recruiter después de practicar.", "session contains external-action prose"),
            ("readiness", "rubric", "criterion", "Tu preparación para la entrevista es 85%.", "session contains numeric-readiness prose"),
        )
        for name, section, field, prose, message in cases:
            with self.subTest(case=name):
                invalid = copy.deepcopy(self.awaiting_session)
                invalid[section][field] = prose
                self.assert_rejected(invalid, message)

    def test_offer_guarantee_and_private_analytics_are_rejected(self) -> None:
        cases = (
            ("guarantee", "question", "text", "Te garantizo una oferta después de esta práctica.", "session contains outcome-guarantee prose"),
            ("analytics", "safe_context", "summary", "Las visitas privadas al perfil aumentaron.", "session contains private-analytics prose"),
        )
        for name, section, field, prose, message in cases:
            with self.subTest(case=name):
                invalid = copy.deepcopy(self.awaiting_session)
                invalid[section][field] = prose
                self.assert_rejected(invalid, message)

    def test_feedback_can_reference_only_the_observed_answer_and_rubric(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["state"] = "feedback_available"
        invalid["observed_answer"] = {
            "id": "OBS-001",
            "text": "Expliqué una acción relevante.",
            "storage": "ephemeral"
        }
        invalid["feedback"] = {
            "score": "unknown",
            "score_state": "categorical",
            "observations": [
                {
                    "label": "solid",
                    "statement": "La respuesta usa un hecho suministrado.",
                    "source_refs": ["F-001"]
                }
            ]
        }
        self.assert_rejected(
            invalid,
            "feedback.observations[0].source_refs may reference only OBS-001 or RB-001",
        )

    def test_feedback_requires_observed_answer_and_rubric_evidence(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["state"] = "feedback_available"
        invalid["observed_answer"] = {
            "id": "OBS-001",
            "text": "Expliqué una acción relevante.",
            "storage": "ephemeral"
        }
        invalid["feedback"] = {
            "score": "unknown",
            "score_state": "categorical",
            "observations": [
                {
                    "label": "solid",
                    "statement": "La respuesta usa una acción concreta.",
                    "source_refs": ["RB-001"]
                }
            ]
        }
        self.assert_rejected(
            invalid,
            "feedback.observations[0].source_refs must cite OBS-001 and RB-001",
        )

    def test_feedback_statements_cannot_echo_raw_answers_or_internal_identifiers(self) -> None:
        cases = (
            (
                "raw_answer",
                "Expliqué una acción relevante.",
                "feedback.observations[0].statement must not repeat the observed answer",
            ),
            (
                "observed_answer_id",
                "OBS-001 demuestra una acción relevante.",
                "feedback.observations[0].statement must not expose internal identifiers",
            ),
            (
                "rubric_id",
                "La respuesta satisface RB-001.",
                "feedback.observations[0].statement must not expose internal identifiers",
            ),
        )
        for name, statement, message in cases:
            with self.subTest(case=name):
                invalid = copy.deepcopy(self.awaiting_session)
                invalid["state"] = "feedback_available"
                invalid["observed_answer"] = {
                    "id": "OBS-001",
                    "text": "Expliqué una acción relevante.",
                    "storage": "ephemeral",
                }
                invalid["feedback"] = {
                    "score": "unknown",
                    "score_state": "categorical",
                    "observations": [
                        {
                            "label": "solid",
                            "statement": statement,
                            "source_refs": ["OBS-001", "RB-001"],
                        }
                    ],
                }
                self.assert_rejected(invalid, message)

    def test_feedback_statements_cannot_echo_answers_after_normalization(self) -> None:
        cases = (
            ("case", "EXPLIQUÉ UNA ACCIÓN RELEVANTE.", "feedback.observations[0].statement must not repeat the observed answer"),
            ("whitespace", "Expliqué\n  una   acción relevante.", "feedback.observations[0].statement must be non-empty prose within 500 characters"),
            ("unicode", "Explique\u0301 una accio\u0301n relevante.", "feedback.observations[0].statement must not repeat the observed answer"),
            ("zero_width", "Expliqué una acci\u200bón relevante.", "feedback.observations[0].statement must be non-empty prose within 500 characters"),
        )
        for name, statement, message in cases:
            with self.subTest(case=name):
                invalid = copy.deepcopy(self.awaiting_session)
                invalid["state"] = "feedback_available"
                invalid["observed_answer"] = {
                    "id": "OBS-001",
                    "text": "Expliqué una acción relevante.",
                    "storage": "ephemeral",
                }
                invalid["feedback"] = {
                    "score": "unknown",
                    "score_state": "categorical",
                    "observations": [
                        {
                            "label": "solid",
                            "statement": statement,
                            "source_refs": ["OBS-001", "RB-001"],
                        }
                    ],
                }
                self.assert_rejected(
                    invalid,
                    message,
                )

    def test_feedback_statements_cannot_obscure_internal_identifiers(self) -> None:
        cases = (
            ("observed_answer_id", "ＯＢＳ－００１ demuestra una acción relevante."),
            ("rubric_id", "La respuesta satisface ＲＢ－００１."),
        )
        for name, statement in cases:
            with self.subTest(case=name):
                invalid = copy.deepcopy(self.awaiting_session)
                invalid["state"] = "feedback_available"
                invalid["observed_answer"] = {
                    "id": "OBS-001",
                    "text": "Expliqué una acción relevante.",
                    "storage": "ephemeral",
                }
                invalid["feedback"] = {
                    "score": "unknown",
                    "score_state": "categorical",
                    "observations": [
                        {
                            "label": "solid",
                            "statement": statement,
                            "source_refs": ["OBS-001", "RB-001"],
                        }
                    ],
                }

                self.assert_rejected(
                    invalid,
                    "feedback.observations[0].statement must not expose internal identifiers",
                )

    def test_feedback_identifiers_with_spaced_hyphens_are_rejected(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["state"] = "feedback_available"
        invalid["observed_answer"] = {"id": "OBS-001", "text": "Expliqué una acción relevante.", "storage": "ephemeral"}
        invalid["feedback"] = {"score": "unknown", "score_state": "categorical", "observations": [{"label": "solid", "statement": "O B S - 001 demuestra una acción.", "source_refs": ["OBS-001", "RB-001"]}]}
        self.assert_rejected(invalid, "feedback.observations[0].statement must not expose internal identifiers")

    def test_feedback_accepts_distinct_rubric_observation(self) -> None:
        valid = copy.deepcopy(self.awaiting_session)
        valid["state"] = "feedback_available"
        valid["observed_answer"] = {
            "id": "OBS-001",
            "text": "Expliqué una acción relevante.",
            "storage": "ephemeral",
        }
        valid["feedback"] = {
            "score": "unknown",
            "score_state": "categorical",
            "observations": [
                {
                    "label": "solid",
                    "statement": "La respuesta describe una acción concreta según el criterio.",
                    "source_refs": ["OBS-001", "RB-001"],
                }
            ],
        }

        self.assert_accepted(valid)

    def test_feedback_available_requires_categorical_score_state_without_numeric_score(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["state"] = "feedback_available"
        invalid["observed_answer"] = {
            "id": "OBS-001",
            "text": "Expliqué una acción relevante.",
            "storage": "ephemeral",
        }
        invalid["feedback"] = {
            "score": "unknown",
            "score_state": "unknown",
            "observations": [{
                "label": "confirm",
                "statement": "Conviene precisar el alcance de la acción.",
                "source_refs": ["OBS-001", "RB-001"],
            }],
        }
        self.assert_rejected(
            invalid,
            "feedback_available feedback.score_state must be categorical",
        )

        numeric = copy.deepcopy(invalid)
        numeric["feedback"]["score_state"] = "categorical"
        numeric["feedback"]["score"] = 4
        self.assert_rejected(
            numeric,
            "feedback.score must be unknown before an observed answer",
        )

    def test_pre_answer_feedback_cannot_claim_categorical_state(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["feedback"]["score_state"] = "categorical"
        self.assert_rejected(
            invalid,
            "pre-answer feedback.score_state must be unknown",
        )

    def test_feedback_requires_explicit_score_state(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        del invalid["feedback"]["score_state"]
        self.assert_rejected(invalid, "missing required field: feedback.score_state")

    def test_cli_rejects_symlink_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "target.json"
            link = root / "link.json"
            target.write_text(json.dumps(self.awaiting_session), encoding="utf-8")
            link.symlink_to(target)
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(link)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 3)
            self.assertIn("symlink", result.stderr)

    def test_cli_rejects_malformed_reference_types_without_crashing(self) -> None:
        for field in ("requirement", "question"):
            invalid = copy.deepcopy(self.awaiting_session)
            invalid[field]["fact_ids"] = [{}]
            result = self.run_cli(invalid)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("fact_ids", result.stderr)

    def test_locale_enum_rejects_non_string_json_values_without_traceback(self) -> None:
        for value in ({}, []):
            with self.subTest(value=value):
                mutated = copy.deepcopy(self.awaiting_session)
                mutated["locale"] = value
                self.assert_rejected(mutated, "locale has invalid value")

    def test_cli_normalizes_parser_failures_and_help(self) -> None:
        invalid = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(FIXTURE_PATH), "--unknown"], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 3)
        missing = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH)], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 3)
        help_result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
