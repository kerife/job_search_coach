"""Contracts for the private recruiter target shortlist artifact."""

from __future__ import annotations

import copy
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_recruiter_target_shortlist import build_shortlist  # noqa: E402
from render_recruiter_target_shortlist import render_shortlist_html  # noqa: E402
from validate_recruiter_target_shortlist import validate_shortlist  # noqa: E402


def valid_plan() -> dict[str, object]:
    return {
        "network_goal": "Review context-qualified recruiter paths for platform roles.",
        "target_segments": ["named_recruiter", "warm_referral", "technical_peer"],
        "source_queries": ["platform recruiter visible specialty", "alumni platform engineering", "site reliability peer"],
        "warm_path_first": True,
        "context_quality_gate": "named target plus visible specialty, shared context, supported proof, and no contact risk",
        "outreach_batch_limit": 3,
        "candidate_time_budget": "45 minutes weekly",
        "stop_condition": "Stop when context is missing, declined, closed, unsafe, or authorization is absent.",
    }


def valid_targets() -> list[dict[str, object]]:
    return [
        {
            "target_label": "Named platform recruiter",
            "contact_category": "named_recruiter",
            "company_or_specialty": "Platform engineering",
            "context_source": "Visible platform specialty and role context",
            "context_state": "named_context",
            "relationship_warmth": "cold_contextual",
            "target_theme": "Reliability and delivery systems",
            "supported_fact_ids": ["F-001"],
            "missing_context": "none",
            "priority_score": 92,
            "decision": "advance",
            "decision_reason": "Named specialty and supported proof fit the target theme.",
            "personalization_trigger": "Visible platform specialty",
            "recommended_draft_type": "recruiter_interest",
            "contactability_status": "contactable",
            "do_not_contact_reason": "none",
            "next_safe_action": "draft_only_review",
        },
        {
            "target_label": "Alumni referral path",
            "contact_category": "warm_referral",
            "company_or_specialty": "Reliability community",
            "context_source": "Candidate-provided alumni bridge",
            "context_state": "named_context",
            "relationship_warmth": "warm",
            "target_theme": "Operational resilience",
            "supported_fact_ids": ["F-002"],
            "missing_context": "Confirm current role scope before drafting.",
            "priority_score": 81,
            "decision": "clarify",
            "decision_reason": "The bridge is useful but current scope needs confirmation.",
            "personalization_trigger": "Alumni connection",
            "recommended_draft_type": "referral_request",
            "contactability_status": "context_needed",
            "do_not_contact_reason": "missing_context",
            "next_safe_action": "collect_recipient_context",
        },
        {
            "target_label": "Community technical peer",
            "contact_category": "technical_peer",
            "company_or_specialty": "Cloud operations",
            "context_source": "Community topic only",
            "context_state": "context_needed",
            "relationship_warmth": "unknown",
            "target_theme": "Cloud operations",
            "supported_fact_ids": [],
            "missing_context": "Need a named shared context and supported proof.",
            "priority_score": 45,
            "decision": "pause",
            "decision_reason": "Topic overlap alone is insufficient for a useful draft.",
            "personalization_trigger": "none",
            "recommended_draft_type": "connection_note",
            "contactability_status": "context_needed",
            "do_not_contact_reason": "no_context",
            "next_safe_action": "record_observation_only",
        },
    ]


class RecruiterTargetShortlistTests(unittest.TestCase):
    def test_builder_returns_deterministic_closed_private_artifact(self) -> None:
        built = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
        self.assertEqual([], validate_shortlist(built, as_of=date(2026, 8, 27)))
        self.assertEqual("recruiter-target-shortlist-v1", built["schema_version"])
        self.assertEqual("T-001", built["targets"][0]["target_id"])
        self.assertEqual("advance", built["batch_decision"])
        self.assertEqual("T-001", built["top_priority_target_id"])
        self.assertFalse(built["delivery"]["no_message_action"] is False)

    def test_validator_blocks_advance_without_context_or_supported_proof(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        value["targets"][0]["context_state"] = "context_needed"
        value["targets"][0]["supported_fact_ids"] = []
        errors = validate_shortlist(value, as_of=date(2026, 8, 27))
        self.assertIn("targets[0].advance requires named context, supported facts, and no missing context", errors)

    def test_validator_rejects_target_identity_material_and_unapproved_action(self) -> None:
        value = build_shortlist("en", "2026-08-27", valid_plan(), valid_targets())
        value["targets"][0]["context_source"] = "https://private.example/profile"
        value["targets"][0]["next_safe_action"] = "send_message"
        errors = validate_shortlist(value, as_of=date(2026, 8, 27))
        self.assertTrue(any("restricted material" in error for error in errors))
        self.assertIn("targets[0].next_safe_action has invalid value", errors)

    def test_renderer_is_bilingual_compact_and_never_exposes_target_ids(self) -> None:
        value = build_shortlist("es", "2026-08-27", valid_plan(), valid_targets())
        rendered = render_shortlist_html(value)
        self.assertIn("Objetivos de reclutamiento", rendered)
        self.assertIn("No contactar todavía", rendered)
        self.assertIn("Named platform recruiter", rendered)
        self.assertNotIn("T-001", rendered)
        self.assertNotIn("F-001", rendered)
        self.assertIn("class=\"target-shortlist-card target-shortlist-card--advance\"", rendered)
        english = copy.deepcopy(value)
        english["locale"] = "en"
        english_rendered = render_shortlist_html(english)
        self.assertIn("Recruiter target shortlist", english_rendered)
        self.assertIn("Do not contact yet", english_rendered)

