import importlib.util
import json
import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parent.parent
SCRIPTS = PLUGIN_ROOT / "scripts"
FIXTURES = REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "private-recruiter-reply-triage"
sys.path.insert(0, str(SCRIPTS))


spec = importlib.util.spec_from_file_location(
    "private_recruiter_reply_triage_renderer",
    SCRIPTS / "render_private_recruiter_reply_triage.py",
)
assert spec is not None and spec.loader is not None
renderer = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = renderer
spec.loader.exec_module(renderer)


class PrivateRecruiterReplyTriageRendererTests(unittest.TestCase):
    def test_normal_states_show_employment_continuity_and_stop_keeps_specific_scope(self):
        expected = {
            "en": "This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.",
            "es": "Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
        }
        stop_scope = {
            "en": "Scope: this records one recruiter-process outcome only. It is not advice to resign, leave a job, or stop your job search; you decide what comes next.",
            "es": "Alcance: esto solo registra un resultado de este proceso de reclutamiento. No es una recomendación de renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
        }
        for locale in ("en", "es"):
            for state in ("ready", "clarify", "stop"):
                value = json.loads((FIXTURES / f"{state}-{locale}.json").read_text(encoding="utf-8"))
                with self.subTest(locale=locale, state=state):
                    rendered = renderer.render_triage_html(value)
                    if state == "stop":
                        self.assertEqual(rendered.count(stop_scope[locale]), 1)
                        self.assertNotIn(expected[locale], rendered)
                    else:
                        self.assertEqual(rendered.count(expected[locale]), 1)
                        self.assertIn('class="triage-footer triage-shell"', rendered)
                        self.assertNotIn("no-print", rendered.split("triage-footer", 1)[1])


if __name__ == "__main__":
    unittest.main()
