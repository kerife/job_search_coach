"""Print keeps the employment-continuity footer attached to each artifact."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "plugins" / "professional-growth-coach" / "assets"
FOOTERS = {
    "executive-career-dossier-v1.css": ".footer",
    "recruiter-practice-session-v1.css": ".practice-footer",
    "private-recruiter-reply-triage-v1.css": ".triage-footer",
    "private-recruiter-conversion-outcome-v1.css": ".outcome-footer",
    "private-recruiter-followthrough-checkpoint-v1.css": ".checkpoint-footer",
}


class PrintContinuityFooterIntegrityTests(unittest.TestCase):
    def test_print_keeps_each_continuity_footer_atomic(self) -> None:
        for name, selector in FOOTERS.items():
            with self.subTest(name=name):
                css = (ASSETS / name).read_text(encoding="utf-8")
                start = css.index("@media print")
                print_css = css[start:]
                next_media = re.search(r"\n@media ", print_css[len("@media print") :])
                if next_media:
                    print_css = print_css[: len("@media print") + next_media.start()]
                footer_rule = re.search(
                    rf"{re.escape(selector)}\s*\{{(?P<rule>[^}}]*)\}}",
                    print_css,
                )
                self.assertIsNotNone(footer_rule, f"missing print footer rule: {name}")
                rule = footer_rule.group("rule")
                self.assertIn("break-inside: avoid", rule)
                self.assertIn("page-break-inside: avoid", rule)


if __name__ == "__main__":
    unittest.main()
