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
            "render_recruiter_target_shortlist",
            "recruiter_target_decision_gate",
            "no_message_action=true",
            "no_calendar_action=true",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
