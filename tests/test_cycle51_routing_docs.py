"""Contract checks for the recruiter shortlist first-class route."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/professional-growth-coach/skills/professional-growth-coach/SKILL.md"
ROUTING = ROOT / "plugins/professional-growth-coach/skills/professional-growth-coach/references/routing.md"


class RecruiterShortlistRoutingDocsTests(unittest.TestCase):
    def test_explicit_network_request_routes_to_private_shortlist(self) -> None:
        text = "\n".join((SKILL.read_text(encoding="utf-8"), ROUTING.read_text(encoding="utf-8")))
        for token in (
            "recruiter-target-shortlist-v1",
            "ask_one_intake_question",
            "review_recruiter_target_shortlist",
            "recruiter_target_decision_gate",
            "recruiter-target-screen-intake-v1",
            "route_recruiter_screen_intake",
            "manual_prepare_role_interviews_review",
            "screen_readiness",
            "private-recruiter-screen-debrief-v1",
            "private-recruiter-next-stage-review-v1",
            "route_recruiter_screen_debrief",
            "manual_prepare_next_stage_review",
            "collect_debrief_context",
            "evidence_gaps",
            "intake_question",
            "network with recruiters",
            "primera entrevista con un reclutador",
            "3–5 manual queries",
            "rendered_html",
            "no_message_action=true",
            "no_calendar_action=true",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
