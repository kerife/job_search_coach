"""Contract tests for the private, identity-free recruiter reply triage."""

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
    / "validate_private_recruiter_reply_triage.py"
)
SCHEMA_PATH = (
    REPO_ROOT
    / "plugins"
    / "professional-growth-coach"
    / "schemas"
    / "private-recruiter-reply-triage-v1.schema.json"
)
FIXTURE_DIRECTORY = (
    REPO_ROOT
    / "tests"
    / "evals"
    / "with-skill"
    / "fixtures"
    / "private-recruiter-reply-triage"
)
FIXTURE_NAMES = (
    "clarify-es.json",
    "clarify-en.json",
    "ready-es.json",
    "ready-en.json",
    "stop-es.json",
    "stop-en.json",
)
CLASSIFICATIONS = {
    "screen_invite",
    "request_for_proof",
    "eligibility_question",
    "compensation_question",
    "decline",
    "unknown",
}
QUESTION_KINDS = {
    "screen_opening",
    "proof_example",
    "eligibility_boundary",
    "compensation_boundary",
    "missing_detail",
}
CLASSIFICATION_QUESTION_KINDS = {
    "screen_invite": "screen_opening",
    "request_for_proof": "proof_example",
    "eligibility_question": "eligibility_boundary",
    "compensation_question": "compensation_boundary",
    "unknown": "missing_detail",
}
STATE_NEXT_SAFE_ACTIONS = {
    "clarify_first": "clarify_context_before_private_prep",
    "ready_for_private_prep": "manual_reenter_private_prep",
    "stop": "record_stop_decision",
}
V2_READY_EN_SNAPSHOT = (
    "snap-triage-sha256-"
    "85ad96e9cab8b222315a01a85d4a6f61f0d5a38650a1286773bc8e1664c15ebd"
)


def load_fixture(name: str) -> dict[str, object]:
    value = json.loads((FIXTURE_DIRECTORY / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture must be a JSON object")
    return value


class PrivateRecruiterReplyTriageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = {name: load_fixture(name) for name in FIXTURE_NAMES}

    def run_cli(self, triage: object) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "triage.json"
            path.write_text(json.dumps(triage), encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-B", str(VALIDATOR_PATH), str(path)],
                capture_output=True,
                text=True,
                check=False,
            )

    def assert_accepted(self, triage: object) -> None:
        result = self.run_cli(triage)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "valid private recruiter reply triage")

    def assert_rejected(self, triage: object, message: str) -> None:
        result = self.run_cli(triage)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(message, result.stderr)

    def test_schema_is_closed_and_declares_the_six_classifications(self) -> None:
        self.assertTrue(SCHEMA_PATH.is_file())
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(CLASSIFICATIONS, set(schema["properties"]["classification"]["enum"]))
        self.assertEqual(QUESTION_KINDS, set(schema["$defs"]["question"]["properties"]["kind"]["enum"]))

    def test_cli_accepts_es_and_en_clarify_ready_and_stop_fixtures(self) -> None:
        for name, triage in self.fixtures.items():
            with self.subTest(fixture=name):
                self.assert_accepted(triage)

    def test_v2_requires_separate_ui_and_content_locales_without_changing_v1(self) -> None:
        v2 = copy.deepcopy(self.fixtures["clarify-es.json"])
        v2["schema_version"] = "private-recruiter-reply-triage-v2"
        v2["ui_locale"] = "en"
        v2["content_locale"] = "es"
        del v2["locale"]
        self.assert_accepted(v2)

        missing_content_locale = copy.deepcopy(v2)
        del missing_content_locale["content_locale"]
        self.assert_rejected(missing_content_locale, "missing required field: content_locale")

        v1_with_v2_locales = copy.deepcopy(self.fixtures["clarify-es.json"])
        v1_with_v2_locales.update({"ui_locale": "en", "content_locale": "es"})
        self.assert_rejected(v1_with_v2_locales, "session has unsupported fields: content_locale, ui_locale")

    def test_v2_ready_handoff_accepts_content_bound_snapshot(self) -> None:
        v2 = copy.deepcopy(self.fixtures["ready-en.json"])
        v2["schema_version"] = "private-recruiter-reply-triage-v2"
        v2["ui_locale"] = "en"
        v2["content_locale"] = "en"
        del v2["locale"]
        v2["handoff"]["packet"]["source_snapshot"] = V2_READY_EN_SNAPSHOT
        v2["handoff"]["reentry_packet"]["source_snapshot"] = V2_READY_EN_SNAPSHOT
        self.assert_accepted(v2)

    def test_v2_snapshot_rejects_bound_content_mutation(self) -> None:
        v2 = copy.deepcopy(self.fixtures["ready-en.json"])
        v2["schema_version"] = "private-recruiter-reply-triage-v2"
        v2["ui_locale"] = "en"
        v2["content_locale"] = "en"
        del v2["locale"]
        v2["handoff"]["packet"]["source_snapshot"] = V2_READY_EN_SNAPSHOT
        v2["handoff"]["reentry_packet"]["source_snapshot"] = V2_READY_EN_SNAPSHOT
        changed = "A different safe summary with altered role constraints."
        v2["safe_context"]["summary"] = changed
        v2["handoff"]["packet"]["context_summary"] = changed
        v2["handoff"]["reentry_packet"]["context_summary"] = changed
        self.assert_rejected(v2, "source_snapshot must match triage content")

    def test_schema_declares_closed_next_safe_action_values(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            set(schema["properties"]["next_safe_action"]["enum"]),
            set(STATE_NEXT_SAFE_ACTIONS.values()),
        )

    def test_next_safe_action_is_required_and_bound_to_state(self) -> None:
        for name, fixture in self.fixtures.items():
            with self.subTest(fixture=name):
                self.assertEqual(STATE_NEXT_SAFE_ACTIONS[fixture["state"]], fixture.get("next_safe_action"))
                missing = copy.deepcopy(fixture)
                del missing["next_safe_action"]
                self.assert_rejected(missing, "missing required field: next_safe_action")

        for name, fixture in self.fixtures.items():
            invalid = copy.deepcopy(fixture)
            invalid["next_safe_action"] = "unknown_action"
            self.assert_rejected(invalid, "next_safe_action has invalid value")
            for action in ("record_stop_decision", "manual_reenter_private_prep"):
                if action == STATE_NEXT_SAFE_ACTIONS[fixture["state"]]:
                    continue
                with self.subTest(fixture=name, action=action):
                    mutated = copy.deepcopy(fixture)
                    mutated["next_safe_action"] = action
                    self.assert_rejected(mutated, "next_safe_action must match state")

    def test_ready_handoff_packet_binds_context_fact_question_and_scope(self) -> None:
        fixture = self.fixtures["ready-en.json"]
        packet = fixture["handoff"]["packet"]
        self.assertEqual(packet["context_summary"], fixture["safe_context"]["summary"])
        self.assertEqual(packet["fact_id"], fixture["facts"][0]["id"])
        self.assertEqual(packet["question_id"], fixture["question"]["id"])
        self.assertEqual(packet["prep_scope"], "eligibility_boundary")

        for field in ("context_summary", "fact_id", "question_id", "prep_scope"):
            mutated = copy.deepcopy(fixture)
            del mutated["handoff"]["packet"][field]
            self.assert_rejected(mutated, f"missing required field: handoff.packet.{field}")

        mutated = copy.deepcopy(fixture)
        mutated["handoff"]["packet"]["fact_id"] = "F-999"
        self.assert_rejected(mutated, "handoff.packet.fact_id must match the sole supplied fact")
        mutated = copy.deepcopy(fixture)
        mutated["handoff"]["packet"]["question_id"] = "Q-999"
        self.assert_rejected(mutated, "handoff.packet.question_id must match the sole question")

    def test_handoff_packet_is_ready_only_closed_and_scope_bound_to_question_kind(self) -> None:
        fixture = self.fixtures["ready-en.json"]
        for kind, scope in {
            "screen_opening": "screen_opening",
            "proof_example": "proof_example",
            "eligibility_boundary": "eligibility_boundary",
            "compensation_boundary": "compensation_boundary",
            "missing_detail": "missing_detail",
        }.items():
            with self.subTest(kind=kind):
                mutated = copy.deepcopy(fixture)
                mutated["classification"] = {
                    "screen_opening": "screen_invite",
                    "proof_example": "request_for_proof",
                    "eligibility_boundary": "eligibility_question",
                    "compensation_boundary": "compensation_question",
                    "missing_detail": "unknown",
                }[kind]
                mutated["question"]["kind"] = kind
                mutated["handoff"]["packet"]["prep_scope"] = scope
                mutated["handoff"]["reentry_packet"]["prep_scope"] = scope
                self.assert_accepted(mutated)

        canonical = copy.deepcopy(fixture)
        canonical["classification"] = "screen_invite"
        canonical["question"]["kind"] = "screen_opening"
        canonical["handoff"]["packet"]["prep_scope"] = "screen_opening"
        canonical["handoff"]["reentry_packet"]["prep_scope"] = "screen_opening"
        for field, message in (
            ("packet", "handoff.packet.prep_scope has invalid value"),
            ("reentry_packet", "handoff.reentry_packet.prep_scope has invalid value"),
        ):
            with self.subTest(removed_alias_field=field):
                removed_alias = copy.deepcopy(canonical)
                removed_alias["handoff"][field]["prep_scope"] = "recruiter_screen_opening"
                self.assert_rejected(removed_alias, message)

        invalid = copy.deepcopy(fixture)
        invalid["handoff"]["packet"]["prep_scope"] = "not-a-scope"
        self.assert_rejected(invalid, "handoff.packet.prep_scope has invalid value")
        invalid = copy.deepcopy(fixture)
        invalid["handoff"]["packet"]["prep_scope"] = "proof_example"
        self.assert_rejected(invalid, "handoff.packet.prep_scope must match question.kind")

        for name in ("clarify-en.json", "stop-en.json"):
            invalid = copy.deepcopy(self.fixtures[name])
            invalid["handoff"] = {"packet": {}}
            self.assert_rejected(invalid, "handoff is permitted only for ready_for_private_prep")

        invalid = copy.deepcopy(fixture)
        invalid["handoff"]["packet"]["extra"] = "no"
        self.assert_rejected(invalid, "handoff.packet has unsupported fields: extra")

    def test_reentry_packet_is_closed_ready_only_and_answer_unaware(self) -> None:
        fixture = self.fixtures["ready-es.json"]
        packet = fixture["handoff"]["reentry_packet"]
        self.assertEqual(packet["schema_version"], "private-recruiter-screen-reentry-v1")
        self.assertTrue(packet["manual_reentry_required"])
        self.assertEqual(packet["candidate_answer_state"], "unanswered")
        self.assertEqual(packet["score_state"], "unknown")

        missing = copy.deepcopy(fixture)
        del missing["handoff"]["reentry_packet"]
        self.assert_rejected(missing, "missing required field: handoff.reentry_packet")

        for field, value, message in (
            ("context_summary", "otro contexto", "handoff.reentry_packet.context_summary must match safe_context.summary"),
            ("source_snapshot", "snap-dossier-001", "handoff.reentry_packet.source_snapshot must use the snap-triage-000 identifier format"),
            ("fact_id", "F-999", "handoff.reentry_packet.fact_id must match the sole supplied fact"),
            ("question_id", "Q-999", "handoff.reentry_packet.question_id must match the sole question"),
            ("prep_scope", "proof_example", "handoff.reentry_packet.prep_scope must match question.kind"),
            ("candidate_answer_state", "answered", "handoff.reentry_packet.candidate_answer_state has immutable value"),
            ("score_state", 4, "handoff.reentry_packet.score_state has immutable value"),
        ):
            mutated = copy.deepcopy(fixture)
            mutated["handoff"]["reentry_packet"][field] = value
            self.assert_rejected(mutated, message)

        mutated = copy.deepcopy(fixture)
        mutated["handoff"]["reentry_packet"]["extra"] = "no"
        self.assert_rejected(mutated, "handoff.reentry_packet has unsupported fields: extra")
        mutated = copy.deepcopy(fixture)
        mutated["handoff"]["reentry_packet"]["raw_reply"] = "texto original"
        self.assert_rejected(mutated, "handoff.reentry_packet has unsupported fields: raw_reply")

        for name in ("clarify-en.json", "stop-en.json"):
            mutated = copy.deepcopy(self.fixtures[name])
            mutated["handoff"] = {"reentry_packet": {}}
            self.assert_rejected(mutated, "handoff is permitted only for ready_for_private_prep")

        mutated = copy.deepcopy(fixture)
        mutated["facts"][0]["state"] = "candidate_reported"
        self.assert_rejected(mutated, "ready_for_private_prep requires a verified supplied fact for handoff")

        mutated = copy.deepcopy(fixture)
        mutated["handoff"]["packet"]["prep_scope"] = "proof_example"
        self.assert_rejected(mutated, "handoff.reentry_packet.prep_scope must match handoff.packet.prep_scope")

    def test_cli_accepts_each_closed_classification_value(self) -> None:
        fixture = self.fixtures["ready-en.json"]
        for classification in CLASSIFICATIONS:
            if classification == "decline":
                continue
            with self.subTest(classification=classification):
                triage = copy.deepcopy(fixture)
                triage["classification"] = classification
                triage["question"]["kind"] = CLASSIFICATION_QUESTION_KINDS.get(classification, "missing_detail")
                triage["handoff"]["packet"]["prep_scope"] = {
                    "screen_opening": "screen_opening",
                    "proof_example": "proof_example",
                    "eligibility_boundary": "eligibility_boundary",
                    "compensation_boundary": "compensation_boundary",
                    "missing_detail": "missing_detail",
                }[triage["question"]["kind"]]
                triage["handoff"]["reentry_packet"]["prep_scope"] = triage["handoff"]["packet"]["prep_scope"]
                self.assert_accepted(triage)

    def test_ready_rejects_decline_classification_but_unknown_remains_generic_ready(self) -> None:
        triage = copy.deepcopy(self.fixtures["ready-en.json"])
        triage["classification"] = "decline"
        self.assert_rejected(triage, "ready_for_private_prep cannot use decline classification")

        triage["classification"] = "unknown"
        triage["question"]["kind"] = "missing_detail"
        triage["handoff"]["packet"]["prep_scope"] = "missing_detail"
        triage["handoff"]["reentry_packet"]["prep_scope"] = "missing_detail"
        self.assert_accepted(triage)

    def test_closed_top_level_field_is_rejected(self) -> None:
        triage = copy.deepcopy(self.fixtures["clarify-es.json"])
        triage["raw_reply"] = "texto recibido"
        self.assert_rejected(triage, "session has unsupported fields: raw_reply")

    def test_requires_exactly_one_fact_and_one_safe_question_with_known_references(self) -> None:
        triage = copy.deepcopy(self.fixtures["clarify-en.json"])
        triage["facts"].append(copy.deepcopy(triage["facts"][0]))
        self.assert_rejected(triage, "facts must contain exactly one supplied fact")

        triage = copy.deepcopy(self.fixtures["clarify-en.json"])
        triage["question"]["fact_ids"] = ["F-999"]
        self.assert_rejected(triage, "question.fact_ids references unknown identifier")

    def test_question_text_allows_one_question_but_rejects_multiple_interrogatives(self) -> None:
        for locale, text in (("en", "Which role scope remains unconfirmed?"), ("es", "¿Qué alcance falta confirmar?")):
            triage = copy.deepcopy(self.fixtures[f"clarify-{locale}.json"])
            triage["question"]["text"] = text
            self.assert_accepted(triage)
        for locale, text in (("en", "Which role scope remains unconfirmed? What should I practice?"), ("es", "¿Qué alcance falta confirmar? ¿Qué debo practicar?")):
            triage = copy.deepcopy(self.fixtures[f"clarify-{locale}.json"])
            triage["question"]["text"] = text
            self.assert_rejected(triage, "question.text must contain exactly one question")

    def test_ready_question_kind_is_required_and_matches_classification(self) -> None:
        fixture = self.fixtures["ready-en.json"]
        for classification, question_kind in CLASSIFICATION_QUESTION_KINDS.items():
            with self.subTest(classification=classification):
                triage = copy.deepcopy(fixture)
                triage["classification"] = classification
                triage["question"]["kind"] = question_kind
                triage["handoff"]["packet"]["prep_scope"] = {
                    "screen_opening": "screen_opening",
                    "proof_example": "proof_example",
                    "eligibility_boundary": "eligibility_boundary",
                    "compensation_boundary": "compensation_boundary",
                    "missing_detail": "missing_detail",
                }[question_kind]
                triage["handoff"]["reentry_packet"]["prep_scope"] = triage["handoff"]["packet"]["prep_scope"]
                self.assert_accepted(triage)

        triage = copy.deepcopy(fixture)
        triage["question"].pop("kind")
        self.assert_rejected(triage, "missing required field: question.kind")

        triage = copy.deepcopy(fixture)
        triage["question"]["kind"] = "not-a-question-kind"
        self.assert_rejected(triage, "question.kind has invalid value")

        triage = copy.deepcopy(fixture)
        triage["classification"] = "eligibility_question"
        triage["question"]["kind"] = "proof_example"
        self.assert_rejected(triage, "question.kind must match classification")

    def test_ready_requires_confirmed_context_and_private_handoff(self) -> None:
        triage = copy.deepcopy(self.fixtures["ready-es.json"])
        triage["safe_context"]["role_context"] = "missing"
        self.assert_rejected(triage, "ready_for_private_prep requires confirmed stage, role, and critical constraints")

        triage = copy.deepcopy(self.fixtures["ready-es.json"])
        triage["handoff_allowed"] = False
        self.assert_rejected(triage, "ready_for_private_prep requires handoff_allowed=true")

    def test_ready_handoff_requires_a_verified_supplied_fact_in_es_and_en(self) -> None:
        for name in ("ready-es.json", "ready-en.json"):
            with self.subTest(fixture=name):
                triage = copy.deepcopy(self.fixtures[name])
                triage["facts"][0]["state"] = "candidate_reported"
                self.assert_rejected(
                    triage,
                    "ready_for_private_prep requires a verified supplied fact for handoff",
                )

    def test_handoff_is_rejected_outside_ready_state(self) -> None:
        for name in ("clarify-es.json", "stop-en.json"):
            with self.subTest(fixture=name):
                triage = copy.deepcopy(self.fixtures[name])
                triage["handoff_allowed"] = True
                self.assert_rejected(triage, "handoff_allowed is permitted only for ready_for_private_prep")

    def test_ready_requires_closed_recruiter_screen_handoff(self) -> None:
        triage = copy.deepcopy(self.fixtures["ready-en.json"])
        triage.pop("handoff", None)
        self.assert_rejected(triage, "ready_for_private_prep requires handoff")

        triage = copy.deepcopy(self.fixtures["ready-en.json"])
        triage["handoff"]["module"] = "other-module"
        self.assert_rejected(triage, "handoff.module has invalid value")

        triage = copy.deepcopy(self.fixtures["ready-en.json"])
        triage["handoff"]["auto_start"] = True
        self.assert_rejected(triage, "handoff.auto_start has immutable value")

    def test_handoff_is_closed_and_forbidden_on_non_ready_or_unverified_fact(self) -> None:
        triage = copy.deepcopy(self.fixtures["clarify-en.json"])
        triage["handoff"] = copy.deepcopy(self.fixtures["ready-en.json"]["handoff"])
        self.assert_rejected(triage, "handoff is permitted only for ready_for_private_prep")

        triage = copy.deepcopy(self.fixtures["ready-en.json"])
        triage["facts"][0]["state"] = "candidate_reported"
        self.assert_rejected(triage, "ready_for_private_prep requires a verified supplied fact for handoff")

        triage = copy.deepcopy(self.fixtures["ready-en.json"])
        triage["handoff"]["unexpected"] = True
        self.assert_rejected(triage, "handoff has unsupported fields: unexpected")

    def test_rejects_raw_identity_contact_action_time_guarantee_and_analytics_prose(self) -> None:
        unsafe_phrases = {
            "raw": "Raw recruiter reply: please call tomorrow.",
            "identity": "Recruiter: Jordan Lee.",
            "contact": "Reach me at person@example.com.",
            "action": "Send a message to the recruiter.",
            "time": "The meeting is Tuesday at 14:00.",
            "guarantee": "You will get an interview.",
            "analytics": "Private analytics show profile views.",
        }
        for violation, phrase in unsafe_phrases.items():
            with self.subTest(violation=violation):
                triage = copy.deepcopy(self.fixtures["clarify-es.json"])
                triage["facts"][0]["summary"] = phrase
                self.assert_rejected(triage, f"session contains forbidden {violation} prose")

    def test_rejects_sensitive_mutations_in_every_prose_field(self) -> None:
        mutations = {
            "identity": "The recruiter is Jordan Lee.",
            "company": "The employer is Acme Corporation.",
            "raw": "Quoted inbound content says to call.",
            "action": "Submit the reply externally.",
            "time": "A call at 2 pm is proposed.",
            "guarantee": "This will result in an offer.",
            "analytics": "A private dashboard has engagement metrics.",
        }
        prose_fields = (
            ("safe_context", "summary"),
            ("facts", 0, "summary"),
            ("question", "text"),
            ("blocked_claims", 0),
        )
        for violation, phrase in mutations.items():
            for path in prose_fields:
                with self.subTest(violation=violation, path=path):
                    triage = copy.deepcopy(self.fixtures["clarify-en.json"])
                    target: object = triage
                    for key in path[:-1]:
                        target = target[key]  # type: ignore[index]
                    target[path[-1]] = phrase  # type: ignore[index]
                    self.assert_rejected(
                        triage,
                        f"session contains forbidden {violation} prose",
                    )

    def test_rejects_contextual_unlabelled_person_and_company_prose(self) -> None:
        mutations = {
            "unlabelled_identity": "Jordan Lee described incident response experience.",
            "unlabelled_company": "The candidate works at Acme Corporation.",
        }
        prose_fields = (
            ("safe_context", "summary"),
            ("facts", 0, "summary"),
            ("question", "text"),
            ("blocked_claims", 0),
        )
        for violation, phrase in mutations.items():
            for path in prose_fields:
                with self.subTest(violation=violation, path=path):
                    triage = copy.deepcopy(self.fixtures["clarify-en.json"])
                    target: object = triage
                    for key in path[:-1]:
                        target = target[key]  # type: ignore[index]
                    target[path[-1]] = f"{phrase[:-1]}?" if path[0] == "question" else phrase  # type: ignore[index]
                    result = self.run_cli(triage)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn(f"session contains forbidden {violation} prose", result.stderr)
                    self.assertNotIn("Jordan Lee", result.stderr)
                    self.assertNotIn("Acme Corporation", result.stderr)

    def test_accepts_role_focused_prose_without_identity_context(self) -> None:
        for summary in (
            "Platform engineering work includes incident response practice.",
            "Site Reliability Engineering manages production reliability.",
            "Platform Engineering works at scale across regions.",
            "The company is hiring for a platform role.",
            "The employer is seeking production experience.",
            "١٢٣ candidate experience examples are supplied.",
        ):
            with self.subTest(summary=summary):
                triage = copy.deepcopy(self.fixtures["clarify-en.json"])
                triage["facts"][0]["summary"] = summary
                self.assert_accepted(triage)

    def test_rejects_identity_prose_in_unsupported_scripts(self) -> None:
        mutations = {
            "cyrillic": "Алексей Иванов described incident response experience.",
            "cjk": "王伟 works at 株式会社青空.",
            "ethiopic": "ሚካኤል ገብረ described incident response experience.",
            "cherokee": "ᎠᎾᏘ ᎠᏂᏴ described incident response experience.",
        }
        prose_fields = (
            ("safe_context", "summary"),
            ("facts", 0, "summary"),
            ("question", "text"),
            ("blocked_claims", 0),
        )
        for script, phrase in mutations.items():
            for path in prose_fields:
                with self.subTest(script=script, path=path):
                    triage = copy.deepcopy(self.fixtures["clarify-en.json"])
                    target: object = triage
                    for key in path[:-1]:
                        target = target[key]  # type: ignore[index]
                    target[path[-1]] = f"{phrase[:-1]}?" if path[0] == "question" else phrase  # type: ignore[index]
                    result = self.run_cli(triage)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("session contains forbidden unsupported_script prose", result.stderr)
                    for sentinel in ("Алексей", "王伟", "ሚካኤል", "ᎠᎾᏘ"):
                        self.assertNotIn(sentinel, result.stderr)

    def test_rejects_unicode_controls_in_every_prose_field(self) -> None:
        prose_fields = (
            ("safe_context", "summary"),
            ("facts", 0, "summary"),
            ("question", "text"),
            ("blocked_claims", 0),
        )
        controls = ("\u200b", "\u202e", "\u2066", "\ufeff")
        for control in controls:
            for path in prose_fields:
                with self.subTest(code_point=f"U+{ord(control):04X}", path=path):
                    triage = copy.deepcopy(self.fixtures["clarify-en.json"])
                    target: object = triage
                    for key in path[:-1]:
                        target = target[key]  # type: ignore[index]
                    target[path[-1]] = (
                        f"Visible{control} prose?" if path[0] == "question"
                        else f"Visible{control} prose"
                    )  # type: ignore[index]
                    result = self.run_cli(triage)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    field_path = (
                        f"facts[0].summary" if path[0] == "facts"
                        else f"blocked_claims[0]" if path[0] == "blocked_claims"
                        else ".".join(str(part) for part in path)
                    )
                    maximum = 500 if path[0] in {"facts", "question"} else 280
                    self.assertIn(
                        f"{field_path} must be non-empty prose within {maximum} characters",
                        result.stderr,
                    )
                    self.assertNotIn("Visible", result.stderr)

    def test_rejects_internal_fact_and_question_ids_embedded_in_prose(self) -> None:
        for path in (("facts", 0, "summary"), ("question", "text"), ("blocked_claims", 0)):
            with self.subTest(path=path):
                triage = copy.deepcopy(self.fixtures["clarify-en.json"])
                target: object = triage
                for key in path[:-1]:
                    target = target[key]  # type: ignore[index]
                target[path[-1]] = "Use F-001 and Q-001 as internal references?"  # type: ignore[index]
                self.assert_rejected(triage, "session contains forbidden internal_id prose")

    def test_rejects_direct_en_and_es_job_offer_and_interview_outcomes_in_every_prose_field(self) -> None:
        outcome_claims = {
            "en-job": "This will result in a job.",
            "en-offer": "This will result in an offer.",
            "en-interview": "This will result in an interview.",
            "es-job": "Esto resultará en un empleo.",
            "es-offer": "Esto resultará en una oferta.",
            "es-interview": "Esto resultará en una entrevista.",
        }
        prose_fields = (
            ("safe_context", "summary"),
            ("facts", 0, "summary"),
            ("question", "text"),
            ("blocked_claims", 0),
        )
        for locale, phrase in outcome_claims.items():
            for path in prose_fields:
                with self.subTest(locale=locale, path=path):
                    triage = copy.deepcopy(self.fixtures[f"clarify-{locale[:2]}.json"])
                    target: object = triage
                    for key in path[:-1]:
                        target = target[key]  # type: ignore[index]
                    target[path[-1]] = phrase  # type: ignore[index]
                    self.assert_rejected(triage, "session contains forbidden guarantee prose")

    def test_rejects_direct_es_plural_outcomes_in_every_prose_field(self) -> None:
        outcome_claims = {
            "bare-interviews": "Esto resultará en entrevistas.",
            "bare-offers": "Esto resultará en ofertas.",
            "bare-employments": "Esto resultará en empleos.",
            "bare-jobs": "Esto resultará en trabajos.",
            "article-interviews": "Esto resultará en unas entrevistas.",
            "article-offers": "Esto resultará en unas ofertas.",
            "article-employments": "Esto resultará en unos empleos.",
            "article-jobs": "Esto resultará en unos trabajos.",
        }
        prose_fields = (
            ("safe_context", "summary"),
            ("facts", 0, "summary"),
            ("question", "text"),
            ("blocked_claims", 0),
        )
        for outcome, phrase in outcome_claims.items():
            for path in prose_fields:
                with self.subTest(outcome=outcome, path=path):
                    triage = copy.deepcopy(self.fixtures["clarify-es.json"])
                    target: object = triage
                    for key in path[:-1]:
                        target = target[key]  # type: ignore[index]
                    target[path[-1]] = phrase  # type: ignore[index]
                    self.assert_rejected(triage, "session contains forbidden guarantee prose")

    def test_accepts_non_outcome_boundary_prose_in_en_and_es(self) -> None:
        for locale, phrase in {
            "en": "This will result in a clearer preparation plan.",
            "es": "Esto resultará en un plan de preparación más claro.",
        }.items():
            with self.subTest(locale=locale):
                triage = copy.deepcopy(self.fixtures[f"clarify-{locale}.json"])
                triage["facts"][0]["summary"] = phrase
                self.assert_accepted(triage)

    def test_accepts_identity_free_summaries_in_every_prose_field(self) -> None:
        triage = copy.deepcopy(self.fixtures["clarify-en.json"])
        triage["safe_context"]["summary"] = "A summarized request lacks confirmed role scope."
        triage["facts"][0]["summary"] = "The candidate reports experience with incident response."
        triage["question"]["text"] = "Which role scope remains unconfirmed?"
        triage["blocked_claims"][0] = "Do not claim unverified role scope."
        self.assert_accepted(triage)

    def test_delivery_and_no_action_flags_are_immutable(self) -> None:
        immutable_values = {
            "draft_only": False,
            "external_actions_authorized": True,
            "no_calendar_action": False,
            "raw_reply_retained": True,
            "local_save_mode": "enabled",
        }
        for field, value in immutable_values.items():
            with self.subTest(field=field):
                triage = copy.deepcopy(self.fixtures["ready-en.json"])
                triage["delivery"][field] = value
                self.assert_rejected(triage, f"delivery.{field} has immutable value")

    def test_delivery_rejects_integer_boolean_coercion(self) -> None:
        for field, value in {
            "draft_only": 1,
            "external_actions_authorized": 0,
            "no_calendar_action": 1,
            "raw_reply_retained": 0,
        }.items():
            with self.subTest(field=field):
                triage = copy.deepcopy(self.fixtures["ready-en.json"])
                triage["delivery"][field] = value
                self.assert_rejected(triage, f"delivery.{field} has immutable value")

    def test_handoff_rejects_integer_boolean_coercion(self) -> None:
        for field, value in {
            "auto_start": 0,
            "external_actions": 0,
            "raw_reply_retained": 0,
        }.items():
            with self.subTest(field=field):
                triage = copy.deepcopy(self.fixtures["ready-en.json"])
                triage["handoff"][field] = value
                self.assert_rejected(triage, f"handoff.{field} has immutable value")

    def test_handoff_reentry_rejects_integer_boolean_coercion(self) -> None:
        triage = copy.deepcopy(self.fixtures["ready-en.json"])
        triage["handoff"]["reentry_packet"]["manual_reentry_required"] = 1
        self.assert_rejected(
            triage,
            "handoff.reentry_packet.manual_reentry_required has immutable value",
        )

    def test_malformed_blocked_claim_is_rejected_without_a_validator_crash(self) -> None:
        triage = copy.deepcopy(self.fixtures["clarify-es.json"])
        triage["blocked_claims"] = [{"unexpected": "object"}]
        self.assert_rejected(triage, "blocked_claims must contain one through four unique claims")

    def test_cli_rejects_symlink_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "target.json"
            link = root / "link.json"
            target.write_text(json.dumps(self.fixtures["clarify-en.json"]), encoding="utf-8")
            link.symlink_to(target)
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(link)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 3)
            self.assertIn("symlink", result.stderr)

    def test_locale_enum_rejects_non_string_json_values_without_traceback(self) -> None:
        for fixture_name in FIXTURE_NAMES:
            for value in ({}, []):
                with self.subTest(fixture=fixture_name, value=value):
                    mutated = copy.deepcopy(self.fixtures[fixture_name])
                    mutated["locale"] = value
                    self.assert_rejected(mutated, "locale has invalid value")

    def test_cli_normalizes_parser_failures_and_help(self) -> None:
        fixture = FIXTURE_DIRECTORY / "clarify-en.json"
        invalid = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(fixture), "--unknown"], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 3)
        missing = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH)], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 3)
        help_result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
