"""Contract tests for the private triage-to-practice composition boundary."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from collections.abc import Mapping
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIRECTORY = (
    ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage"
)
sys.path.insert(0, str(ROOT / "scripts"))

from build_private_recruiter_triage_practice_handoff import (  # noqa: E402
    CompositionError,
    build_handoff,
)
from triage_snapshot import snapshot_for_triage  # noqa: E402
from validate_recruiter_practice_session import validate_session  # noqa: E402
from validate_private_recruiter_reply_triage import validate_triage  # noqa: E402


def _strings(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        return tuple(text for child in value.values() for text in _strings(child))
    if isinstance(value, list):
        return tuple(text for child in value for text in _strings(child))
    return ()


class PrivateRecruiterTriagePracticeHandoffTests(unittest.TestCase):
    def _ready_triage(self, locale: str) -> dict[str, object]:
        path = FIXTURE_DIRECTORY / f"ready-{locale}.json"
        triage = json.loads(path.read_text(encoding="utf-8"))
        triage["schema_version"] = "private-recruiter-reply-triage-v2"
        triage["ui_locale"] = locale
        triage["content_locale"] = locale
        del triage["locale"]
        snapshot = snapshot_for_triage(triage)
        triage["handoff"]["packet"]["source_snapshot"] = snapshot
        triage["handoff"]["reentry_packet"]["source_snapshot"] = snapshot
        self.assertEqual([], validate_triage(triage))
        return triage

    def test_builds_valid_es_and_en_practice_sessions_from_ready_triage(self) -> None:
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                triage = self._ready_triage(locale)

                result = build_handoff(triage)

                self.assertEqual(
                    "private-recruiter-triage-practice-handoff-v1",
                    result["schema_version"],
                )
                session = result["practice_session"]
                self.assertEqual("recruiter-practice-session-v2", session["schema_version"])
                self.assertEqual("ready_to_practice", session["state"])
                self.assertEqual(
                    snapshot_for_triage(triage),
                    result["handoff_context"]["source_snapshot"],
                )
                self.assertEqual(
                    snapshot_for_triage(triage),
                    session["handoff_context"]["source_snapshot"],
                )
                self.assertEqual([], validate_session(session))

    def test_rejects_non_ready_triage_and_unverified_source_evidence(self) -> None:
        clarify = json.loads((FIXTURE_DIRECTORY / "clarify-es.json").read_text(encoding="utf-8"))
        stop = json.loads((FIXTURE_DIRECTORY / "stop-en.json").read_text(encoding="utf-8"))
        candidate_reported = self._ready_triage("en")
        candidate_reported["facts"][0]["state"] = "candidate_reported"
        candidate_reported["handoff_allowed"] = False
        candidate_reported["state"] = "clarify_first"
        candidate_reported["next_safe_action"] = "clarify_context_before_private_prep"
        candidate_reported.pop("handoff")

        for label, triage in (
            ("clarify_first", clarify),
            ("stop", stop),
            ("candidate_reported", candidate_reported),
        ):
            with self.subTest(label=label):
                with self.assertRaises(CompositionError):
                    build_handoff(triage)

    def test_rejects_changed_handoff_packet_snapshot_fact_or_question_identifier(self) -> None:
        mutations = (
            ("packet snapshot", lambda value: value["handoff"]["packet"].update({"source_snapshot": "snap-triage-sha256-" + "0" * 64})),
            ("fact ID", lambda value: value["handoff"]["packet"].update({"fact_id": "F-999"})),
            ("question ID", lambda value: value["handoff"]["packet"].update({"question_id": "Q-999"})),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                triage = self._ready_triage("en")
                mutate(triage)
                with self.assertRaises(CompositionError):
                    build_handoff(triage)

    def test_practice_session_redacts_source_ids_and_raw_reply_sentinel(self) -> None:
        triage = self._ready_triage("es")
        source_fact_id = "F-777"
        source_question_id = "Q-777"
        raw_reply_sentinel = "RAW_REPLY_SENTINEL"
        triage["facts"][0]["id"] = source_fact_id
        triage["question"]["id"] = source_question_id
        triage["question"]["fact_ids"] = [source_fact_id]
        triage["handoff"]["packet"].update(
            {"fact_id": source_fact_id, "question_id": source_question_id}
        )
        triage["handoff"]["reentry_packet"].update(
            {"fact_id": source_fact_id, "question_id": source_question_id}
        )
        triage["blocked_claims"].append(raw_reply_sentinel)
        snapshot = snapshot_for_triage(triage)
        triage["handoff"]["packet"]["source_snapshot"] = snapshot
        triage["handoff"]["reentry_packet"]["source_snapshot"] = snapshot
        self.assertEqual([], validate_triage(triage))

        result = build_handoff(triage)

        session_strings = _strings(result["practice_session"])
        for value in (source_fact_id, source_question_id, raw_reply_sentinel):
            with self.subTest(redacted=value):
                self.assertNotIn(value, session_strings)


if __name__ == "__main__":
    unittest.main()
