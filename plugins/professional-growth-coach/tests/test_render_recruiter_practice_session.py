import copy
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_recruiter_practice_session.py"
FIXTURE_DIRECTORY = (
    ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage"
)
sys.path.insert(0, str(ROOT / "scripts"))
from build_private_recruiter_triage_practice_handoff import build_handoff
from triage_snapshot import snapshot_for_triage

spec = importlib.util.spec_from_file_location("practice_renderer", SCRIPT)
renderer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = renderer
spec.loader.exec_module(renderer)

VALIDATOR_SCRIPT = ROOT / "scripts" / "validate_recruiter_practice_session.py"
validator_spec = importlib.util.spec_from_file_location("practice_validator", VALIDATOR_SCRIPT)
validator = importlib.util.module_from_spec(validator_spec)
assert validator_spec.loader is not None
sys.modules[validator_spec.name] = validator
validator_spec.loader.exec_module(validator)


class RecruiterPracticeRendererTests(unittest.TestCase):
    def _triage_practice_session(self, locale: str) -> dict[str, object]:
        triage = json.loads((FIXTURE_DIRECTORY / f"ready-{locale}.json").read_text())
        triage["schema_version"] = "private-recruiter-reply-triage-v2"
        triage["ui_locale"] = locale
        triage["content_locale"] = locale
        del triage["locale"]
        snapshot = snapshot_for_triage(triage)
        triage["handoff"]["packet"]["source_snapshot"] = snapshot
        triage["handoff"]["reentry_packet"]["source_snapshot"] = snapshot
        return build_handoff(triage)["practice_session"]

    def test_triage_practice_route_is_localized_static_and_safe(self):
        expected_stages = {
            "es": ("Triaje validado", "Ensayo privado", "Revisión privada"),
            "en": ("Validated triage", "Private rehearsal", "Private review"),
        }
        for locale, stages in expected_stages.items():
            with self.subTest(locale=locale):
                rendered = renderer.render_session_html(
                    self._triage_practice_session(locale)
                )
                self.assertEqual(rendered.count('class="triage-practice-route"'), 1)
                route = rendered.split('<section class="triage-practice-route"', 1)[1].split(
                    "</section>", 1
                )[0]
                for stage in stages:
                    self.assertIn(stage, route)
                self.assertNotRegex(route, r"\b(?:Q|R|F|C|E|OBS|RB)-\d{3}\b")
                self.assertEqual(rendered.count("href="), 1)
                self.assertNotRegex(rendered, r"<(?:form|button|script)\b")
                self.assertRegex(
                    rendered,
                    r"(?s)@media \(max-width: 640px\).*?\.triage-practice-route-list \{[^}]*grid-template-columns: 1fr;",
                )
                self.assertRegex(
                    rendered,
                    r"(?s)@media \(forced-colors: active\).*?\.triage-practice-route \{[^}]*background: Canvas;[^}]*color: CanvasText;",
                )
                self.assertRegex(
                    rendered,
                    r"(?s)@media print.*?\.triage-practice-route[^}]*\{[^}]*break-inside: avoid;",
                )

    def test_triage_practice_shows_localized_answer_boundary_after_question(self):
        expected = {
            "es": {
                "title": "Límite de tu respuesta",
                "label": "Usa solo evidencia confirmada",
                "instruction": "No agregues resultados, alcance ni disponibilidad que no estén confirmados.",
            },
            "en": {
                "title": "Your answer boundary",
                "label": "Use only confirmed evidence",
                "instruction": "Do not add outcomes, scope, or availability that are not confirmed.",
            },
        }
        for locale, copy in expected.items():
            with self.subTest(locale=locale):
                session = self._triage_practice_session(locale)
                session["facts"][0]["summary"] = 'Verified <evidence> & "scope"'
                rendered = renderer.render_session_html(session)
                guardrail = rendered.split(
                    '<section class="practice-claim-guardrail"', 1
                )[1].split("</section>", 1)[0]
                self.assertEqual(rendered.count('class="practice-claim-guardrail"'), 1)
                self.assertLess(
                    rendered.index('id="practice-question-text"'),
                    rendered.index('<section class="practice-claim-guardrail"'),
                )
                self.assertLess(
                    rendered.index('<section class="practice-claim-guardrail"'),
                    rendered.index('<section class="triage-practice-route"'),
                )
                self.assertIn(copy["title"], guardrail)
                self.assertIn(copy["label"], guardrail)
                self.assertIn(copy["instruction"], guardrail)
                self.assertIn('Verified &lt;evidence&gt; &amp; &quot;scope&quot;', guardrail)
                self.assertNotIn('Verified <evidence>', guardrail)
                self.assertNotRegex(guardrail, r"\b(?:Q|R|F|C|E|OBS|RB)-\d{3}\b")
                self.assertNotIn("snap-triage-sha256-", guardrail)
                self.assertNotIn("https://", guardrail)
                self.assertNotRegex(guardrail, r"<(?:form|button|script)\b")

    def test_triage_answer_boundary_has_accessible_visual_contract(self):
        css = renderer.CSS_PATH.read_text(encoding="utf-8")
        selector = r"\.recruiter-practice-document \.practice-claim-guardrail"
        self.assertRegex(
            css,
            selector + r"\s*\{[^}]*border: 1px solid var\(--coral\);[^}]*border-left: 4px solid var\(--coral\);[^}]*background: var\(--coral-soft\);",
        )
        self.assertRegex(
            css,
            selector + r"\s*\{[^}]*max-width: var\(--measure\);",
        )
        self.assertRegex(
            css,
            r"(?s)@media screen and \(prefers-color-scheme: dark\).*?"
            + selector
            + r"\s*\{[^}]*background: var\(--coral-soft\);[^}]*color: var\(--ink\);",
        )
        self.assertRegex(
            css,
            r"(?s)@media \(max-width: 640px\).*?"
            + selector
            + r"\s*\{[^}]*padding: .875rem;",
        )
        self.assertRegex(
            css,
            r"(?s)@media \(forced-colors: active\).*?"
            + selector
            + r"\s*\{[^}]*border-color: CanvasText;[^}]*background: Canvas;[^}]*color: CanvasText;",
        )
        self.assertRegex(
            css,
            r"(?s)@media \(prefers-contrast: more\).*?"
            + selector
            + r"\s*\{[^}]*border-width: 2px;[^}]*border-left-width: .5rem;",
        )
        self.assertRegex(
            css,
            r"(?s)@media print.*?"
            + selector
            + r"\s*\{[^}]*break-inside: avoid;[^}]*page-break-inside: avoid;",
        )
        self.assertRegex(
            css,
            r"(?s)@media \(prefers-reduced-motion: reduce\).*?"
            + selector
            + r"\s*\{[^}]*transition: none !important;",
        )

    def test_answer_boundary_is_absent_for_dossier_and_unsourced_practice(self):
        session = self._feedback_session([self._observation("solid")])
        unsourced_html = renderer.render_session_html(session)
        self.assertNotIn('class="practice-claim-guardrail"', unsourced_html)

        sourced = copy.deepcopy(session)
        sourced["handoff_context"] = {
            "source": "executive_career_dossier",
            "source_snapshot": "snap-dossier-sha256-873fb8cf4957d72c0aa06a15b253716a3d0397d45997073adb0b8e486decfa25",
            "question_rank": 1,
            "question_id": "Q-001",
            "requirement_id": "R-001",
            "fact_ids": ["F-001"],
            "claim_ids": ["C-001"],
            "evidence_ids": ["E-001"],
            "draft_only": True,
            "external_actions_authorized": False,
        }
        dossier_html = renderer.render_session_html(sourced)
        self.assertNotIn('class="practice-claim-guardrail"', dossier_html)

    def test_triage_answer_boundary_rejects_url_in_dynamic_fact_summary(self):
        session = self._triage_practice_session("en")
        session["facts"][0]["summary"] = "Verified result https://example.invalid"

        with self.assertRaisesRegex(ValueError, "URL"):
            renderer.render_session_html(session)

    def test_triage_answer_boundary_rejects_www_url_without_echoing_it(self):
        session = self._triage_practice_session("en")
        unsafe_summary = "Verified result www.example.invalid/path"
        session["facts"][0]["summary"] = unsafe_summary

        with self.assertRaisesRegex(ValueError, "URL") as error:
            renderer.render_session_html(session)
        self.assertNotIn(unsafe_summary, str(error.exception))

    def test_triage_sourced_prose_rejects_url_contact_and_path_in_every_dynamic_field(self):
        targets = {
            "safe_context.summary": ("safe_context", "summary"),
            "question.text": ("question", "text"),
            "facts[0].summary": ("facts", 0, "summary"),
        }
        sentinels = (
            "Read https://example.invalid/private before practice.",
            "Reply to person@example.invalid before practice.",
            "Read /private/tmp/private-note before practice.",
            "Use Bearer abc123 before practice.",
            "Authorization: Bearer abc123 before practice.",
        )
        for target_name, target_path in targets.items():
            for sentinel in sentinels:
                with self.subTest(target=target_name, sentinel_kind=sentinel.split()[1]):
                    session = self._triage_practice_session("en")
                    target = session
                    for segment in target_path[:-1]:
                        target = target[segment]
                    target[target_path[-1]] = sentinel
                    with self.assertRaises(ValueError) as error:
                        renderer.render_session_html(session)
                    self.assertNotIn(sentinel, str(error.exception))

    def test_handoff_prose_guard_does_not_apply_to_dossier_source(self):
        session = self._feedback_session([self._observation("solid")])
        session["handoff_context"] = {
            "source": "executive_career_dossier",
            "source_snapshot": "snap-dossier-sha256-873fb8cf4957d72c0aa06a15b253716a3d0397d45997073adb0b8e486decfa25",
            "question_rank": 1,
            "question_id": "Q-001",
            "requirement_id": "R-001",
            "fact_ids": ["F-001"],
            "claim_ids": ["C-001"],
            "evidence_ids": ["E-001"],
            "draft_only": True,
            "external_actions_authorized": False,
        }
        session["safe_context"]["summary"] = "Read www.example.invalid privately."
        self.assertIn("www.example.invalid", renderer.render_session_html(session))

    def test_invalid_utf8_input_is_reported_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_bytes(b"\xff")

            result = subprocess.run(
                [sys.executable, "-B", str(VALIDATOR_SCRIPT), str(path)],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stderr, "session input is not valid JSON\n")
        self.assertNotIn("Traceback", result.stderr)

    def _feedback_session(self, observations):
        return {
            "schema_version": "recruiter-practice-session-v1",
            "session_kind": "private_recruiter_practice",
            "locale": "es",
            "state": "feedback_available",
            "safe_context": {"stage": "recruiter_screen", "vacancy_state": "safe_summary_provided", "summary": "Contexto"},
            "requirement": {"id": "R-001", "summary": "Liderazgo", "fact_ids": ["F-001"]},
            "question": {"id": "Q-001", "kind": "proof_example", "text": "¿Cómo lo hiciste?", "requirement_id": "R-001", "fact_ids": ["F-001"]},
            "facts": [{"id": "F-001", "state": "verified", "summary": "Resultado confirmado"}],
            "observed_answer": {"id": "OBS-001", "text": "Hice la acción y observé el resultado.", "storage": "ephemeral"},
            "rubric": {"id": "RB-001", "criterion": "Conecta acción y resultado observado."},
            "feedback": {"score": "unknown", "score_state": "categorical", "observations": observations},
            "delivery": {"draft_only": True, "external_actions_authorized": False, "local_save_mode": "disabled", "raw_answer_retained": False},
        }

    def _observation(self, label):
        return {"label": label, "statement": "Observación acotada.", "source_refs": ["OBS-001", "RB-001"]}

    def test_feedback_taxonomy_accepts_canonical_order(self):
        session = self._feedback_session([self._observation(label) for label in ("solid", "confirm", "do_not_assert")])
        self.assertEqual(validator.validate_session(session), [])

    def test_feedback_taxonomy_rejects_duplicate_or_reversed_labels(self):
        duplicate = self._feedback_session([self._observation(label) for label in ("solid", "solid")])
        reversed_order = self._feedback_session([self._observation(label) for label in ("confirm", "solid")])
        self.assertTrue(any("must be unique" in error for error in validator.validate_session(duplicate)))
        self.assertTrue(any("canonical order" in error for error in validator.validate_session(reversed_order)))

    def test_feedback_renderer_uses_closed_kind_aware_copy_without_private_prose(self):
        for locale in ("es", "en"):
            for kind in renderer.QUESTION_KINDS:
                for label in renderer.FEEDBACK_LABELS:
                    session = self._feedback_session([
                        {**self._observation(label), "statement": "PRIVATE-FEEDBACK-SENTINEL"},
                    ])
                    session["locale"] = locale
                    session["question"]["kind"] = kind
                    session["facts"][0]["state"] = (
                        "verified" if kind == "proof_example" else "candidate_reported"
                    )
                    with self.subTest(locale=locale, kind=kind, label=label):
                        rendered = renderer.render_session_html(session)
                        feedback = rendered.split(
                            '<section class="practice-feedback"', 1
                        )[1].split("</section>", 1)[0]
                        self.assertIn(
                            renderer._feedback_description(locale, kind, label), feedback
                        )
                        self.assertNotIn("PRIVATE-FEEDBACK-SENTINEL", rendered)

    def test_mixed_feedback_labels_render_decision_after_feedback_without_private_ids(self):
        session = self._feedback_session([
            self._observation(label)
            for label in ("solid", "confirm", "do_not_assert")
        ])
        rendered = renderer.render_session_html(session)
        self.assertLess(
            rendered.index('<section class="practice-feedback"'),
            rendered.index('<section class="practice-decision"'),
        )
        self.assertLess(
            rendered.index('<section class="practice-decision"'),
            rendered.index('<section class="practice-evidence"'),
        )
        self.assertEqual(rendered.count("<dt>"), 3)
        self.assertEqual(rendered.count("<dd>"), 3)
        decision = rendered.split('<section class="practice-decision"', 1)[1].split(
            "</section>", 1
        )[0]
        self.assertIn("No afirmar todavía", decision)
        self.assertIn(renderer._decision_action("es", "do_not_assert"), decision)
        self.assertNotIn(renderer._decision_action("es", "solid"), decision)
        self.assertNotIn(renderer._decision_action("es", "confirm"), decision)
        self.assertNotIn("practice-next-action--feedback_available", rendered)
        self.assertEqual(rendered.count("href="), 1)
        self.assertNotRegex(rendered, r"\b(?:Q|R|F|C|E|OBS|RB)-\d{3}\b")

    def test_continuity_rail_shows_practice_route_and_keeps_next_step_manual(self):
        rendered = renderer.render_session_html(
            self._feedback_session([self._observation("solid")])
        )
        self.assertEqual(rendered.count('class="continuity-rail"'), 1)
        self.assertEqual(rendered.count('class="continuity-step continuity-step--'), 3)
        self.assertIn('data-stage="evidence" data-state="current"', rendered)
        self.assertIn('data-stage="rehearsal" data-state="current"', rendered)
        self.assertIn('data-stage="next-version" data-state="pending"', rendered)
        self.assertNotIn("D-104", rendered)
        self.assertNotIn("F-105", rendered)

    def test_first_screen_readiness_card_exposes_manual_conditions_in_both_locales(self):
        for locale in ("es", "en"):
            for fact_state in ("verified", "candidate_reported"):
                session = self._feedback_session([self._observation("solid")])
                session["locale"] = locale
                session["question"]["kind"] = "screen_opening"
                session["facts"][0]["state"] = fact_state
                with self.subTest(locale=locale, fact_state=fact_state):
                    rendered = renderer.render_session_html(session)
                    self.assertEqual(rendered.count('class="screen-readiness"'), 1)
                    readiness = rendered.split(
                        '<section class="screen-readiness"', 1
                    )[1].split("</section>", 1)[0]
                    expected = {
                        "es": {
                            "title": "Preparación de primera conversación",
                            "stage": "Filtro inicial",
                            "evidence": "Confirmada" if fact_state == "verified" else "Por confirmar",
                            "boundary": "Solo preparación privada",
                            "next": "Revisión privada antes de cualquier acción externa",
                        },
                        "en": {
                            "title": "First-conversation readiness",
                            "stage": "Recruiter screen",
                            "evidence": "Confirmed" if fact_state == "verified" else "Needs confirmation",
                            "boundary": "Private preparation only",
                            "next": "Private review before any external action",
                        },
                    }[locale]
                    for value in expected.values():
                        self.assertIn(value, readiness)
                    self.assertIn('data-state="current"', readiness)
                    self.assertIn('data-state="pending"', readiness)
                    self.assertNotRegex(readiness, r"\b(?:Q|R|F|C|E|OBS|RB)-\d{3}\b")

    def test_decision_field_labels_are_exact_in_both_locales(self):
        expected_labels = {
            "es": (
                "Señal prioritaria",
                "Objetivo de esta respuesta",
                "Decisión antes de volver a practicar",
            ),
            "en": (
                "Governing feedback",
                "Target for this answer",
                "Decision before rehearsing again",
            ),
        }
        for locale, labels in expected_labels.items():
            session = self._feedback_session([self._observation("solid")])
            session["locale"] = locale
            with self.subTest(locale=locale):
                rendered = renderer.render_session_html(session)
                decision = rendered.split(
                    '<section class="practice-decision"', 1
                )[1].split("</section>", 1)[0]
                self.assertEqual(re.findall(r"<dt>([^<]+)</dt>", decision), list(labels))

    def test_question_kind_is_closed_and_required(self):
        session = self._feedback_session([])
        session["state"] = "awaiting_answer"
        session["observed_answer"] = None
        session["feedback"] = {"score": "unknown", "score_state": "unknown", "observations": []}
        session["question"]["kind"] = "free_form"
        errors = validator.validate_session(session)
        self.assertTrue(any("question.kind" in error for error in errors))

    def test_question_kind_requires_semantically_matching_fact_state(self):
        session = self._feedback_session([])
        session["state"] = "awaiting_answer"
        session["observed_answer"] = None
        session["feedback"] = {"score": "unknown", "score_state": "unknown", "observations": []}
        session["question"]["kind"] = "proof_example"
        session["facts"][0]["state"] = "candidate_reported"
        errors = validator.validate_session(session)
        self.assertTrue(any("proof_example requires verified fact" in error for error in errors))

        session["question"]["kind"] = "eligibility_boundary"
        session["facts"][0]["state"] = "verified"
        errors = validator.validate_session(session)
        self.assertFalse(any("eligibility_boundary requires" in error for error in errors))

    def test_prompt_includes_rehearsal_scaffold_for_first_screen_answer(self):
        session = {
            "schema_version": "recruiter-practice-session-v1",
            "session_kind": "private_recruiter_practice",
            "locale": "es",
            "state": "awaiting_answer",
            "safe_context": {"stage": "recruiter_screen", "vacancy_state": "safe_summary_provided", "summary": "Contexto"},
            "requirement": {"id": "R-001", "summary": "Liderazgo", "fact_ids": ["F-001"]},
            "question": {"id": "Q-001", "kind": "proof_example", "text": "¿Cómo lo hiciste?", "requirement_id": "R-001", "fact_ids": ["F-001"]},
            "facts": [{"id": "F-001", "state": "verified", "summary": "Resultado confirmado"}],
            "observed_answer": None,
            "rubric": {"id": "RB-001", "criterion": "Conecta acción y resultado observado."},
            "feedback": {"score": "unknown", "score_state": "unknown", "observations": []},
            "delivery": {"draft_only": True, "external_actions_authorized": False, "local_save_mode": "disabled", "raw_answer_retained": False},
        }
        rendered = renderer.render_session_html(session)
        self.assertIn("Propósito de la pregunta", rendered)
        self.assertIn("Presenta una evidencia confirmada", rendered)
        self.assertIn("Estructura de respuesta", rendered)
        self.assertIn("Contexto de la evidencia", rendered)
        self.assertIn("Acción técnica concreta", rendered)
        self.assertIn("Impacto observado directo", rendered)
        self.assertNotIn("Contexto breve", rendered)
        self.assertIn('class="practice-rehearsal-hint"', rendered)
        self.assertIn('aria-labelledby="rehearsal-title"', rendered)
        self.assertIn("Siguiente paso", rendered)
        self.assertIn("Responde con contexto breve, acción concreta y resultado observado", rendered)
        self.assertIn("No se guarda tu respuesta", rendered)

        expected_steps = {
            "screen_opening": "Puente a la conversación",
            "proof_example": "Impacto observado directo",
            "eligibility_boundary": "Pregunta abierta",
            "compensation_boundary": "Pregunta de compensación",
            "missing_detail": "Detalle faltante",
        }
        for kind, expected_step in expected_steps.items():
            candidate = copy.deepcopy(session)
            candidate["question"]["kind"] = kind
            with self.subTest(kind=kind):
                self.assertIn(expected_step, renderer.render_session_html(candidate))

        sourced = copy.deepcopy(session)
        sourced["handoff_context"] = {
            "source": "executive_career_dossier",
            "source_snapshot": "snap-dossier-sha256-873fb8cf4957d72c0aa06a15b253716a3d0397d45997073adb0b8e486decfa25",
            "question_rank": 1,
            "question_id": "Q-001",
            "requirement_id": "R-001",
            "fact_ids": ["F-001"],
            "claim_ids": ["C-001"],
            "evidence_ids": ["E-001"],
            "draft_only": True,
            "external_actions_authorized": False,
        }
        sourced_html = renderer.render_session_html(sourced)
        self.assertLess(
            sourced_html.index('<section class="practice-next-action'),
            sourced_html.index('<section class="practice-rehearsal"'),
        )
        self.assertIn("Lista para responder", sourced_html)
        self.assertIn(
            "Regresa a la conversación privada de Codex que originó esta práctica",
            sourced_html,
        )
        self.assertNotIn('class="triage-practice-route"', sourced_html)

    def test_next_action_forced_colors_uses_explicit_system_color_surface_in_both_locales(self):
        session = {
            "schema_version": "recruiter-practice-session-v1",
            "session_kind": "private_recruiter_practice",
            "locale": "es",
            "state": "awaiting_answer",
            "safe_context": {"stage": "recruiter_screen", "vacancy_state": "safe_summary_provided", "summary": "Contexto"},
            "requirement": {"id": "R-001", "summary": "Liderazgo", "fact_ids": ["F-001"]},
            "question": {"id": "Q-001", "kind": "proof_example", "text": "¿Cómo lo hiciste?", "requirement_id": "R-001", "fact_ids": ["F-001"]},
            "facts": [{"id": "F-001", "state": "verified", "summary": "Resultado confirmado"}],
            "observed_answer": None,
            "rubric": {"id": "RB-001", "criterion": "Conecta acción y resultado observado."},
            "feedback": {"score": "unknown", "score_state": "unknown", "observations": []},
            "delivery": {"draft_only": True, "external_actions_authorized": False, "local_save_mode": "disabled", "raw_answer_retained": False},
        }
        expected_heading = {"es": "Siguiente paso", "en": "Next step"}
        for locale, heading in expected_heading.items():
            localized = copy.deepcopy(session)
            localized["locale"] = locale
            with self.subTest(locale=locale):
                rendered = renderer.render_session_html(localized)
                self.assertIn(heading, rendered)
                self.assertRegex(
                    rendered,
                    r"(?s)@media \(forced-colors: active\).*?\.recruiter-practice-document \.practice-next-action \{[^}]*background: Canvas;[^}]*color: CanvasText;[^}]*border-color: CanvasText;",
                )
                self.assertRegex(
                    rendered,
                    r"(?s)@media \(forced-colors: active\).*?\.recruiter-practice-document \.practice-next-action h2 \{[^}]*color: CanvasText;",
                )
                self.assertRegex(
                    rendered,
                    r"(?s)@media \(forced-colors: active\).*?\.recruiter-practice-document \.practice-next-action--ready_to_practice,\s+\.recruiter-practice-document \.practice-next-action--awaiting_answer \{[^}]*border-left-color: CanvasText;",
                )

    def test_sourced_session_hides_provenance_and_raw_answer_material(self):
        sourced = self._feedback_session([self._observation("confirm")])
        sourced["observed_answer"]["text"] = "SOURCE-RAW-ANSWER-SENTINEL"
        sourced["feedback"]["observations"][0]["statement"] = "SOURCE-RAW-FEEDBACK-SENTINEL"
        sourced["handoff_context"] = {
            "source": "executive_career_dossier",
            "source_snapshot": "snap-dossier-sha256-873fb8cf4957d72c0aa06a15b253716a3d0397d45997073adb0b8e486decfa25",
            "question_rank": 1,
            "question_id": "Q-001",
            "requirement_id": "R-001",
            "fact_ids": ["F-001"],
            "claim_ids": ["C-001"],
            "evidence_ids": ["E-001"],
            "draft_only": True,
            "external_actions_authorized": False,
        }

        rendered = renderer.render_session_html(sourced)

        for omitted in (
            "snap-dossier-sha256-873fb8cf4957d72c0aa06a15b253716a3d0397d45997073adb0b8e486decfa25",
            "Q-001",
            "R-001",
            "F-001",
            "C-001",
            "E-001",
            "OBS-001",
            "RB-001",
            "SOURCE-RAW-ANSWER-SENTINEL",
            "SOURCE-RAW-FEEDBACK-SENTINEL",
        ):
            with self.subTest(omitted=omitted):
                self.assertNotIn(omitted, rendered)

    def test_employment_continuity_boundary_is_visible_for_every_practice_state(self):
        expected = {
            "en": "This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.",
            "es": "Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
        }
        for locale in ("en", "es"):
            for state in ("ready_to_practice", "awaiting_answer", "feedback_available"):
                session = self._feedback_session(
                    [self._observation("solid"), self._observation("confirm"), self._observation("do_not_assert")]
                )
                session["locale"] = locale
                session["state"] = state
                if state != "feedback_available":
                    session["observed_answer"] = None
                    session["feedback"] = {
                        "score": "unknown",
                        "score_state": "unknown",
                        "observations": [],
                    }
                with self.subTest(locale=locale, state=state):
                    rendered = renderer.render_session_html(session)
                    self.assertEqual(rendered.count(expected[locale]), 1)
                    self.assertIn('class="practice-footer practice-shell"', rendered)
                    self.assertNotIn("no-print", rendered.split("practice-footer", 1)[1])


if __name__ == "__main__":
    unittest.main()
