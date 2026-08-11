import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURE = (
    ROOT.parent.parent
    / "tests"
    / "evals"
    / "with-skill"
    / "fixtures"
    / "private-recruiter-reply-triage"
    / "clarify-en.json"
)
sys.path.insert(0, str(SCRIPTS))


def _load_script(name: str):
    path = SCRIPTS / f"{name}.py"
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


validator = _load_script("validate_private_recruiter_reply_triage")
renderer = _load_script("render_private_recruiter_reply_triage")


class PrivateRecruiterReplyTriageIdentityTests(unittest.TestCase):
    def test_unknown_fact_reference_rejects_without_echoing_private_value(self):
        triage = json.loads(FIXTURE.read_text(encoding="utf-8"))
        sentinel = "person@example.com"
        triage["question"]["fact_ids"] = [sentinel]

        errors = validator.validate_triage(triage)

        self.assertIn(
            "question.fact_ids references unknown identifier",
            errors,
        )
        self.assertNotIn(sentinel, "\n".join(errors))
        with self.assertRaises(renderer.TriageValidationError) as raised:
            renderer.render_triage_html(triage)
        self.assertNotIn(sentinel, str(raised.exception))

    def test_candidate_identity_markers_are_rejected_before_render(self):
        baseline = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mutations = {
            "safe_context.summary": (("safe_context", "summary"), "Candidate name: John Smith"),
            "facts[0].summary": (("facts", 0, "summary"), "Candidate name: John Smith"),
            "question.text": (
                ("question", "text"),
                "Which question should Candidate name: John Smith answer?",
            ),
            "blocked_claims[0]": (("blocked_claims", 0), "Candidate name: John Smith"),
        }
        sentinel = "Candidate name: John Smith"
        for path, (location, replacement) in mutations.items():
            triage = copy.deepcopy(baseline)
            target = triage
            for component in location[:-1]:
                target = target[component]
            target[location[-1]] = replacement
            with self.subTest(path=path):
                errors = validator.validate_triage(triage)
                self.assertTrue(
                    any("forbidden identity prose" in error for error in errors),
                    errors,
                )
                with self.assertRaises(renderer.TriageValidationError) as raised:
                    renderer.render_triage_html(triage)
                self.assertNotIn(sentinel, str(raised.exception))

    def test_spanish_candidate_identity_marker_is_rejected(self):
        triage = json.loads(
            (
                FIXTURE.parent / "clarify-es.json"
            ).read_text(encoding="utf-8")
        )
        triage["safe_context"]["summary"] = "Nombre del candidato: Juan Pérez"
        errors = validator.validate_triage(triage)
        self.assertTrue(any("forbidden identity prose" in error for error in errors), errors)
        with self.assertRaises(renderer.TriageValidationError):
            renderer.render_triage_html(triage)


if __name__ == "__main__":
    unittest.main()
