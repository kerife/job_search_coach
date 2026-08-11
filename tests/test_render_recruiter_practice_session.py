"""Behavioral tests for the offline private recruiter-practice renderer."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_PATH = REPO_ROOT / "plugins" / "professional-growth-coach" / "scripts"
if str(SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_PATH))
RENDERER_PATH = (
    REPO_ROOT
    / "plugins"
    / "professional-growth-coach"
    / "scripts"
    / "render_recruiter_practice_session.py"
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
V2_TRIAGE_PHONE_LIKE_SNAPSHOT = (
    "snap-triage-sha256-"
    "9cfca8aaaeb249e38dbeee70bbbcd3189173398fea1c3f9baee95fa0e56b3af0"
)


def load_fixture() -> dict[str, object]:
    value = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture must be a JSON object")
    return value


def load_renderer() -> object:
    if not RENDERER_PATH.is_file():
        raise AssertionError("recruiter practice renderer is missing")
    specification = importlib.util.spec_from_file_location(
        "render_recruiter_practice_session", RENDERER_PATH
    )
    assert specification is not None and specification.loader is not None
    renderer = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = renderer
    specification.loader.exec_module(renderer)
    return renderer


class RecruiterPracticeSessionRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.renderer = load_renderer()
        self.awaiting_session = load_fixture()

    def feedback_session(self) -> dict[str, object]:
        session = copy.deepcopy(self.awaiting_session)
        session["state"] = "feedback_available"
        session["observed_answer"] = {
            "id": "OBS-001",
            "text": "Organicé el proceso y expliqué el alcance que confirmé.",
            "storage": "ephemeral",
        }
        session["feedback"] = {
            "score": "unknown",
            "score_state": "categorical",
            "observations": [
                {
                    "label": "solid",
                    "statement": "La respuesta describe una acción concreta.",
                    "source_refs": ["OBS-001", "RB-001"],
                }
            ],
        }
        return session

    def _css_block(self, css: str, selector: str) -> str:
        match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]+)\}}", css)
        self.assertIsNotNone(match, selector)
        assert match is not None
        return match.group(1)

    def english_session(self) -> dict[str, object]:
        session = copy.deepcopy(self.awaiting_session)
        session["locale"] = "en"
        session["safe_context"]["summary"] = (
            "Practice a brief explanation for a confirmed technical requirement."
        )
        session["requirement"]["summary"] = (
            "Explain relevant technical experience without extending the confirmed scope."
        )
        session["question"]["text"] = (
            "How would you explain this experience in a first conversation?"
        )
        session["facts"][0]["summary"] = (
            "The person confirmed relevant experience for explaining a technical process."
        )
        session["rubric"]["criterion"] = (
            "Describe a relevant action without asserting unobserved results."
        )
        return session

    def v2_mixed_locale_session(self) -> dict[str, object]:
        session = copy.deepcopy(self.awaiting_session)
        session["schema_version"] = "recruiter-practice-session-v2"
        session["ui_locale"] = "en"
        session["content_locale"] = "es"
        del session["locale"]
        return session

    def test_v2_uses_ui_locale_for_copy_and_content_locale_for_dynamic_prose(self) -> None:
        rendered = self.renderer.render_session_html(self.v2_mixed_locale_session())

        self.assertIn('lang="en"', rendered)
        self.assertIn("Private rehearsal", rendered)
        self.assertIn(
            '<p id="practice-question-text" lang="es">¿Cómo explicarías esta experiencia en una primera conversación?</p>',
            rendered,
        )
        self.assertIn(
            '<span lang="es">La persona confirmó experiencia relevante para explicar un proceso técnico.</span>',
            rendered,
        )

    def test_awaiting_answer_renders_spanish_context_prompt_and_categorical_state(self) -> None:
        rendered = self.renderer.render_session_html(self.awaiting_session)

        self.assertTrue(rendered.casefold().startswith("<!doctype html>"))
        self.assertIn('lang="es"', rendered)
        self.assertEqual(rendered.count("<h1"), 1)
        self.assertIn("Contexto seguro", rendered)
        self.assertIn("Pregunta para practicar", rendered)
        self.assertIn("Lista para responder", rendered)
        self.assertNotIn("Esperando tu respuesta", rendered)
        self.assertIn("La persona confirmó experiencia relevante", rendered)
        self.assertIn("No se realizó ninguna acción externa.", rendered)
        self.assertNotIn("Comentarios sobre la respuesta", rendered)
        self.assertIn('class="practice-handoff practice-handoff--dossier" aria-labelledby="practice-handoff-title" aria-describedby="prompt-title practice-question-text"', rendered)
        self.assertIn('<p id="practice-question-text">¿Cómo explicarías esta experiencia en una primera conversación?</p>', rendered)
        self.assertIn("Origen de práctica", rendered)
        self.assertNotRegex(rendered, r"\b(?:F|R|Q|RB)-\d{3}\b")
        self.assertNotRegex(rendered, r"\b(?:C|E)-\d{3}\b")
        self.assertNotRegex(rendered, r"(?:readiness|preparaci[oó]n)\D{0,20}\d+%")

    def test_ready_and_awaiting_states_have_distinct_next_actions(self) -> None:
        ready = self.renderer.render_session_html(self.awaiting_session | {"state": "ready_to_practice"})
        awaiting = self.renderer.render_session_html(self.awaiting_session)
        self.assertIn(
            "Lee la pregunta y prepara tu respuesta; después regresa a la conversación privada de Codex que originó esta práctica. Esta página no guarda tu respuesta.",
            ready,
        )
        self.assertNotIn("Responde con contexto breve", ready)
        self.assertIn(
            "Regresa a la conversación privada de Codex que originó esta práctica para responder. Esta página no guarda tu respuesta.",
            awaiting,
        )
        self.assertNotIn("Lee la pregunta y prepara tu respuesta", awaiting)
        self.assertIn('practice-next-action--awaiting_answer', awaiting)
        self.assertIn('practice-next-action--ready_to_practice', ready)

        english = self.english_session() | {"state": "ready_to_practice"}
        self.assertIn(
            "Read the question and prepare your answer; then return to the private Codex conversation that originated this practice. This page does not save your answer.",
            self.renderer.render_session_html(english),
        )

    def test_state_chip_is_described_by_practice_region_without_live_announcements(self) -> None:
        for state, label in (("ready_to_practice", "Lista para practicar"), ("awaiting_answer", "Lista para responder")):
            with self.subTest(state=state):
                rendered = self.renderer.render_session_html(dict(self.awaiting_session, state=state))
                self.assertIn(
                    '<section class="practice-session" aria-labelledby="practice-session-title" '
                    'aria-describedby="practice-session-state">', rendered,
                )
                self.assertIn(f'<p id="practice-session-state" class="state-chip state-chip--{state}">{label}</p>', rendered)
                self.assertIn(f".recruiter-practice-document .state-chip--{state} {{", rendered)
                self.assertNotIn("aria-live", rendered)

        feedback = self.renderer.render_session_html(self.feedback_session())
        self.assertIn("Comentarios disponibles", feedback)
        self.assertIn('id="practice-session-state"', feedback)

    def test_sourced_pre_feedback_session_is_decision_led(self) -> None:
        sourced = self.renderer.render_session_html(self.awaiting_session)
        handoff = sourced.index('<aside class="practice-handoff ')
        next_action = sourced.index('<section class="practice-next-action')
        rehearsal = sourced.index('<section class="practice-rehearsal"')
        evidence = sourced.index('<section class="practice-evidence"')
        boundary = sourced.index('<aside class="practice-boundary"')
        self.assertLess(handoff, next_action)
        self.assertLess(next_action, rehearsal)
        self.assertLess(rehearsal, evidence)
        self.assertLess(evidence, boundary)
        self.assertIn("Regresa a la conversación privada de Codex que originó esta práctica", sourced)
        self.assertIn("Esta página no guarda tu respuesta.", sourced)
        next_action_html = sourced.split(
            '<section class="practice-next-action', 1
        )[1].split("</section>", 1)[0]
        self.assertIn(
            'aria-describedby="prompt-title practice-question-text"',
            next_action_html,
        )
        self.assertNotIn("rehearsal-title", next_action_html)

        independent = dict(self.awaiting_session)
        independent.pop("handoff_context")
        independent_html = self.renderer.render_session_html(independent)
        self.assertLess(independent_html.index('<section class="practice-rehearsal"'), independent_html.index('<section class="practice-next-action'))
        self.assertNotIn('<aside class="practice-handoff"', independent_html)
        self.assertNotIn("originó esta práctica", independent_html)
        self.assertNotIn("originated this practice", independent_html)

    def test_next_action_copy_distinguishes_sourced_and_independent_pre_feedback_sessions(self) -> None:
        expected_sourced = {
            ("es", "ready_to_practice"): "Lee la pregunta y prepara tu respuesta; después regresa a la conversación privada de Codex que originó esta práctica. Esta página no guarda tu respuesta.",
            ("es", "awaiting_answer"): "Regresa a la conversación privada de Codex que originó esta práctica para responder. Esta página no guarda tu respuesta.",
            ("en", "ready_to_practice"): "Read the question and prepare your answer; then return to the private Codex conversation that originated this practice. This page does not save your answer.",
            ("en", "awaiting_answer"): "Return to the private Codex conversation that originated this practice to answer. This page does not save your answer.",
        }
        for (locale, state), expected_copy in expected_sourced.items():
            candidate = self.english_session() if locale == "en" else copy.deepcopy(self.awaiting_session)
            candidate["state"] = state
            with self.subTest(locale=locale, state=state):
                self.assertIn(f"<p>{expected_copy}</p>", self.renderer.render_session_html(candidate))

        expected_independent = {
            ("es", "ready_to_practice"): "Lee la pregunta y prepara tu respuesta en tres movimientos. No se guarda tu respuesta.",
            ("es", "awaiting_answer"): "Responde con contexto breve, acción concreta y resultado observado. No se guarda tu respuesta.",
            ("en", "ready_to_practice"): "Read the question and prepare your answer in three moves. Your answer is not saved.",
            ("en", "awaiting_answer"): "Answer with brief context, a concrete action, and an observed result. Your answer is not saved.",
        }
        for (locale, state), expected_copy in expected_independent.items():
            candidate = self.english_session() if locale == "en" else copy.deepcopy(self.awaiting_session)
            candidate["state"] = state
            candidate.pop("handoff_context")
            with self.subTest(locale=locale, state=state, sourced=False):
                self.assertIn(f"<p>{expected_copy}</p>", self.renderer.render_session_html(candidate))

    def test_feedback_available_has_no_next_action_panel(self) -> None:
        feedback = self.renderer.render_session_html(self.feedback_session())
        self.assertNotIn(
            '<section class="practice-next-action practice-next-action--feedback_available"',
            feedback,
        )
        self.assertLess(feedback.index('<section class="practice-rehearsal"'), feedback.index('<section class="practice-feedback"'))
        self.assertLess(feedback.index('<section class="practice-feedback"'), feedback.index('<section class="practice-decision"'))
        self.assertLess(feedback.index('<section class="practice-decision"'), feedback.index('<section class="practice-evidence"'))
        self.assertNotIn('aria-live="polite"', feedback)
        awaiting = self.renderer.render_session_html(self.awaiting_session)
        self.assertNotIn('<section class="practice-feedback"', awaiting)

    def test_feedback_available_renders_one_three_pair_decision_after_feedback(self) -> None:
        session = self.feedback_session()
        session["feedback"]["observations"] = [
            {
                "label": label,
                "statement": "Bounded observation.",
                "source_refs": ["OBS-001", "RB-001"],
            }
            for label in ("solid", "confirm", "do_not_assert")
        ]
        feedback = self.renderer.render_session_html(session)
        markers = (
            '<aside class="practice-handoff ',
            '<section class="practice-rehearsal"',
            '<section class="practice-feedback"',
            '<section class="practice-decision"',
            '<section class="practice-evidence"',
            '<aside class="practice-boundary"',
        )
        indices = [feedback.index(marker) for marker in markers]
        self.assertEqual(indices, sorted(indices))
        self.assertNotIn(
            '<section class="practice-next-action practice-next-action--feedback_available"',
            feedback,
        )
        self.assertEqual(feedback.count('<section class="practice-decision"'), 1)
        decision = feedback.split(
            '<section class="practice-decision"', 1
        )[1].split("</section>", 1)[0]
        self.assertIn('aria-labelledby="decision-title"', decision)
        self.assertNotIn("aria-describedby", decision)
        self.assertEqual(decision.count("<dt>"), 3)
        self.assertEqual(decision.count("<dd>"), 3)
        self.assertLess(
            decision.index("Señal prioritaria"),
            decision.index("Objetivo de esta respuesta"),
        )
        self.assertLess(
            decision.index("Objetivo de esta respuesta"),
            decision.index("Decisión antes de volver a practicar"),
        )
        self.assertIn("No afirmar todavía", decision)

    def test_decision_explanation_is_exact_in_both_locales(self) -> None:
        explanations = {
            "es": "Cuando aparecen varias señales, la que requiere más cautela guía la siguiente versión.",
            "en": "When several signals appear, the one requiring the most caution guides the next version.",
        }
        for locale, explanation in explanations.items():
            session = self.feedback_session()
            session["locale"] = locale
            with self.subTest(locale=locale):
                rendered = self.renderer.render_session_html(session)
                decision = rendered.split('<section class="practice-decision"', 1)[1].split(
                    "</section>", 1
                )[0]
                self.assertIn(
                    f'<p class="practice-decision-explanation">{explanation}</p>',
                    decision,
                )

    def test_decision_field_labels_are_exact_in_both_locales(self) -> None:
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
            session = self.feedback_session()
            session["locale"] = locale
            with self.subTest(locale=locale):
                rendered = self.renderer.render_session_html(session)
                decision = rendered.split(
                    '<section class="practice-decision"', 1
                )[1].split("</section>", 1)[0]
                self.assertEqual(re.findall(r"<dt>([^<]+)</dt>", decision), list(labels))

    def test_pre_feedback_next_actions_preserve_their_aria_references(self) -> None:
        awaiting = self.renderer.render_session_html(self.awaiting_session)
        self.assertIn('aria-describedby="prompt-title practice-question-text"', awaiting)
        independent = copy.deepcopy(self.awaiting_session)
        independent.pop("handoff_context")
        independent_html = self.renderer.render_session_html(independent)
        self.assertIn('aria-describedby="prompt-title rehearsal-title"', independent_html)

    def test_sequence_matrix_preserves_order_and_resolved_aria_references(self) -> None:
        cases = (
            ("sourced-ready", self.awaiting_session | {"state": "ready_to_practice"}, ("handoff", "next", "rehearsal", "evidence", "boundary"), "prompt-title practice-question-text"),
            ("sourced-awaiting", self.awaiting_session, ("handoff", "next", "rehearsal", "evidence", "boundary"), "prompt-title practice-question-text"),
            ("independent-ready", {key: value for key, value in (self.awaiting_session | {"state": "ready_to_practice"}).items() if key != "handoff_context"}, ("rehearsal", "next", "evidence", "boundary"), "prompt-title rehearsal-title"),
            ("independent-awaiting", {key: value for key, value in self.awaiting_session.items() if key != "handoff_context"}, ("rehearsal", "next", "evidence", "boundary"), "prompt-title rehearsal-title"),
            ("sourced-feedback", self.feedback_session(), ("handoff", "rehearsal", "feedback", "decision", "evidence", "boundary"), None),
            ("independent-feedback", {key: value for key, value in self.feedback_session().items() if key != "handoff_context"}, ("rehearsal", "feedback", "decision", "evidence", "boundary"), None),
        )
        markers = {
            "handoff": '<aside class="practice-handoff ',
            "rehearsal": '<section class="practice-rehearsal"',
            "next": '<section class="practice-next-action',
            "feedback": '<section class="practice-feedback"',
            "decision": '<section class="practice-decision"',
            "evidence": '<section class="practice-evidence"',
            "boundary": '<aside class="practice-boundary"',
        }
        for name, session, expected_order, described_by in cases:
            with self.subTest(case=name):
                rendered = self.renderer.render_session_html(session)
                indices = [rendered.index(markers[section]) for section in expected_order]
                self.assertEqual(indices, sorted(indices))
                if described_by is not None:
                    next_action = rendered.split('<section class="practice-next-action', 1)[1].split("</section>", 1)[0]
                    self.assertIn(f'aria-describedby="{described_by}"', next_action)
                ids = re.findall(r'\bid="([^"]+)"', rendered)
                self.assertEqual(len(ids), len(set(ids)))
                for value in re.findall(r'\baria-(?:labelledby|describedby)="([^"]+)"', rendered):
                    for identifier in value.split():
                        self.assertIn(identifier, ids)

    def test_sourced_sessions_keep_the_renderer_private_and_non_interactive(self) -> None:
        sourced = self.renderer.render_session_html(self.awaiting_session)
        for forbidden in ("<form", "<input", "<textarea", "<button"):
            self.assertNotIn(forbidden, sourced.casefold())
        self.assertEqual(sourced.count("href="), 1)
        self.assertNotRegex(sourced, r"\b(?:Q|R|F|C|E|OBS|RB)-\d{3}\b")
        self.assertNotIn("source_snapshot", sourced)
        self.assertNotIn("external_actions_authorized", sourced)

    def test_feedback_labels_have_semantic_classes_in_spanish_and_english(self) -> None:
        for label, css_class in (("solid", "feedback-label--solid"), ("confirm", "feedback-label--confirm"), ("do_not_assert", "feedback-label--do_not_assert")):
            with self.subTest(label=label):
                session = self.feedback_session()
                session["feedback"]["observations"][0]["label"] = label
                rendered = self.renderer.render_session_html(session)
                self.assertIn(f'class="feedback-label {css_class}"', rendered)
                self.assertIn(f'class="feedback-item feedback-item--{label}"', rendered)
                self.assertNotIn("aria-live", rendered)
                session["locale"] = "en"
                english = self.renderer.render_session_html(session)
                self.assertIn(f'class="feedback-label {css_class}"', english)

    def test_rendered_feedback_uses_kind_copy_without_upgrading_candidate_reported_facts(self) -> None:
        for locale in ("es", "en"):
            for kind in self.renderer.QUESTION_KINDS:
                for label in self.renderer.FEEDBACK_LABELS:
                    session = self.feedback_session()
                    session["locale"] = locale
                    session["question"]["kind"] = kind
                    session["feedback"]["observations"] = [{
                        "label": label,
                        "statement": "Bounded observation.",
                        "source_refs": ["OBS-001", "RB-001"],
                    }]
                    session["facts"][0]["state"] = (
                        "verified" if kind == "proof_example" else "candidate_reported"
                    )
                    with self.subTest(locale=locale, kind=kind, label=label):
                        rendered = self.renderer.render_session_html(session)
                        feedback = rendered.split(
                            '<section class="practice-feedback"', 1
                        )[1].split("</section>", 1)[0]
                        rehearsal = rendered.split(
                            '<section class="practice-rehearsal"', 1
                        )[1].split("</section>", 1)[0]
                        decision = rendered.split(
                            '<section class="practice-decision"', 1
                        )[1].split("</section>", 1)[0]
                        self.assertIn(
                            self.renderer._feedback_description(locale, kind, label),
                            feedback,
                        )
                        if kind != "proof_example":
                            self.assertNotRegex(
                                (rehearsal + feedback + decision).casefold(),
                                r"\b(?:confirmad[oa]s?|verified|confirmed)\b",
                            )

    def test_rendered_feedback_preserves_present_canonical_labels_without_private_prose(self) -> None:
        session = self.feedback_session()
        session["observed_answer"]["text"] = "PRIVATE-ANSWER-SENTINEL"
        session["feedback"]["observations"] = [
            {
                "label": label,
                "statement": "PRIVATE-FEEDBACK-SENTINEL",
                "source_refs": ["OBS-001", "RB-001"],
            }
            for label in ("solid", "do_not_assert")
        ]

        rendered = self.renderer.render_session_html(session)
        feedback = rendered.split('<section class="practice-feedback"', 1)[1].split(
            "</section>", 1
        )[0]
        self.assertEqual(feedback.count('<li class="feedback-item '), 2)
        self.assertLess(
            feedback.index('feedback-item--solid'),
            feedback.index('feedback-item--do_not_assert'),
        )
        self.assertIn('<span class="feedback-label feedback-label--solid">Sólido:</span>', feedback)
        self.assertIn(
            '<span class="feedback-label feedback-label--do_not_assert">No afirmar todavía:</span>',
            feedback,
        )
        self.assertNotIn('feedback-label--confirm', feedback)
        self.assertNotIn("PRIVATE-ANSWER-SENTINEL", rendered)
        self.assertNotIn("PRIVATE-FEEDBACK-SENTINEL", rendered)

    def test_feedback_and_decision_helpers_reject_private_values_without_echoing_them(self) -> None:
        for locale, kind, label, message, private_value in (
            ("xx-private", "screen_opening", "solid", "unsupported locale", "xx-private"),
            ("es", "private-kind", "solid", "unsupported question kind", "private-kind"),
            ("es", "screen_opening", "private-label", "unsupported feedback label", "private-label"),
        ):
            with self.subTest(message=message, helper="decision"):
                with self.assertRaises(ValueError) as context:
                    self.renderer._render_decision(
                        locale, kind, label,
                        self.renderer.COPY.get(locale, self.renderer.COPY["es"]),
                    )
                self.assertEqual(str(context.exception), message)
                self.assertNotIn(private_value, str(context.exception))
            with self.subTest(message=message, helper="feedback"):
                with self.assertRaises(ValueError) as context:
                    self.renderer._render_feedback(
                        locale, kind, (label,),
                        self.renderer.COPY.get(locale, self.renderer.COPY["es"]),
                    )
                self.assertEqual(str(context.exception), message)
                self.assertNotIn(private_value, str(context.exception))

    def test_feedback_available_output_keeps_private_surface_and_aria_contracts(self) -> None:
        for sourced in (True, False):
            session = self.feedback_session()
            session["observed_answer"]["text"] = "PRIVATE-ANSWER-SENTINEL"
            session["feedback"]["observations"][0]["statement"] = "PRIVATE-FEEDBACK-SENTINEL"
            if not sourced:
                session.pop("handoff_context")
            with self.subTest(sourced=sourced):
                rendered = self.renderer.render_session_html(session)
                self.assertEqual(rendered.count('href="#main-content"'), 1)
                self.assertEqual(rendered.count('<main id="main-content" class="practice-shell" tabindex="-1">'), 1)
                self.assertEqual(rendered.count("href="), 1)
                for forbidden in (
                    "<form", "<input", "<textarea", "<button", "aria-live", 'role="status"'
                ):
                    self.assertNotIn(forbidden, rendered.casefold())
                self.assertNotRegex(rendered, r"\b(?:Q|R|F|C|E|OBS|RB)-\d{3}\b")
                self.assertNotIn("PRIVATE-ANSWER-SENTINEL", rendered)
                self.assertNotIn("PRIVATE-FEEDBACK-SENTINEL", rendered)
                ids = re.findall(r'\bid="([^"]+)"', rendered)
                self.assertEqual(len(ids), len(set(ids)))
                for value in re.findall(r'\baria-(?:labelledby|describedby)="([^"]+)"', rendered):
                    for identifier in value.split():
                        self.assertIn(identifier, ids)
                feedback = rendered.split('<section class="practice-feedback"', 1)[1].split(
                    "</section>", 1
                )[0]
                decision = rendered.split('<section class="practice-decision"', 1)[1].split(
                    "</section>", 1
                )[0]
                self.assertIn('aria-describedby="feedback-ephemeral-note"', feedback)
                self.assertNotIn("aria-describedby", decision)

    def test_next_action_renderer_rejects_unknown_state(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported recruiter practice state: bogus"):
            self.renderer._render_next_action("bogus", self.renderer.COPY["es"], sourced=False)

    def test_feedback_copy_is_closed_and_kind_aware_in_both_locales(self) -> None:
        expected = {
            "es": {
                "screen_opening": {
                    "solid": "Una versión respaldada mantiene el posicionamiento dentro del alcance de la evidencia suministrada y crea un puente relevante hacia la conversación.",
                    "confirm": "Confirma o acota el enfoque antes de usar esta apertura para representar tu experiencia.",
                    "do_not_assert": "Quita de la apertura cualquier afirmación de ajuste, propiedad, disponibilidad o resultado que no esté respaldada.",
                },
                "proof_example": {
                    "solid": "Una versión respaldada distingue el contexto confirmado, una acción concreta y un impacto observado directamente.",
                    "confirm": "Confirma el alcance o el impacto antes de presentarlo como hecho.",
                    "do_not_assert": "Quita la afirmación sin respaldo; sustitúyela por evidencia confirmada o pausa este ejemplo.",
                },
                "eligibility_boundary": {
                    "solid": "Una versión respaldada separa el dato suministrado, la condición de elegibilidad aún desconocida y una aclaración concreta.",
                    "confirm": "Confirma la condición de elegibilidad pendiente antes de presentarla como hecho.",
                    "do_not_assert": "No afirmes elegibilidad, autorización o disponibilidad que no esté respaldada; formula una pregunta acotada o pausa la respuesta.",
                },
                "compensation_boundary": {
                    "solid": "Una versión respaldada separa la evidencia suministrada, la condición de compensación pendiente y el límite de decisión.",
                    "confirm": "Confirma la condición, el rango o el contexto pendiente antes de depender de ello en el ensayo privado.",
                    "do_not_assert": "No afirmes monto, rango, moneda o aceptación sin evidencia; conviértelo en una aclaración o pausa la respuesta.",
                },
                "missing_detail": {
                    "solid": "Una versión respaldada presenta el mínimo suministrado y nombra un solo detalle que aún necesita aclaración antes del próximo ensayo privado.",
                    "confirm": "Confirma el detalle faltante antes de depender de él en la respuesta.",
                    "do_not_assert": "Quita el detalle sin respaldo; pide una sola aclaración o pausa la respuesta.",
                },
            },
            "en": {
                "screen_opening": {
                    "solid": "A supported version keeps the positioning within the scope of the supplied evidence and creates a relevant bridge into the conversation.",
                    "confirm": "Confirm or qualify the focus before using this opening to represent your experience.",
                    "do_not_assert": "Remove any unsupported fit, ownership, availability, or outcome claim from the opening.",
                },
                "proof_example": {
                    "solid": "A supported version distinguishes confirmed context, a concrete action, and directly observed impact.",
                    "confirm": "Confirm the scope or impact before presenting it as fact.",
                    "do_not_assert": "Remove the unsupported claim; replace it with confirmed evidence or pause this example.",
                },
                "eligibility_boundary": {
                    "solid": "A supported version separates the supplied fact, the still-unknown eligibility condition, and one concrete clarification.",
                    "confirm": "Confirm the pending eligibility condition before presenting it as fact.",
                    "do_not_assert": "Do not assert unsupported eligibility, authorization, or availability; ask one bounded question or pause the answer.",
                },
                "compensation_boundary": {
                    "solid": "A supported version separates the supplied evidence, the pending compensation condition, and the decision boundary.",
                    "confirm": "Confirm the pending condition, range, or context before relying on it in the private rehearsal.",
                    "do_not_assert": "Do not assert an unsupported amount, range, currency, or acceptance; turn it into a clarification or pause the answer.",
                },
                "missing_detail": {
                    "solid": "A supported version presents the supplied minimum and names one detail that still needs clarification before the next private rehearsal.",
                    "confirm": "Confirm the missing detail before relying on it in the answer.",
                    "do_not_assert": "Remove the unsupported detail; ask one clarification or pause the answer.",
                },
            },
        }
        self.assertEqual(set(self.renderer.FEEDBACK_DESCRIPTION_COPY), {"es", "en"})
        for locale, kinds in expected.items():
            self.assertEqual(set(kinds), set(self.renderer.QUESTION_KINDS))
            for kind, label_copy in kinds.items():
                self.assertEqual(set(label_copy), set(self.renderer.FEEDBACK_LABELS))
                for label, sentence in label_copy.items():
                    with self.subTest(locale=locale, kind=kind, label=label):
                        self.assertEqual(
                            self.renderer._feedback_description(locale, kind, label),
                            sentence,
                        )

    def test_decision_copy_is_closed_in_both_locales(self) -> None:
        expected_targets = {
            "es": {
                "screen_opening": "Presentar el posicionamiento respaldado por la evidencia suministrada, un enfoque relevante y un puente seguro hacia la conversación.",
                "proof_example": "Presentar contexto confirmado, una acción concreta y un impacto observado directamente.",
                "eligibility_boundary": "Separar el dato suministrado, la condición de elegibilidad desconocida y una sola pregunta de aclaración.",
                "compensation_boundary": "Separar la evidencia suministrada, la condición de compensación pendiente y el límite de decisión.",
                "missing_detail": "Presentar el mínimo suministrado y el único detalle que todavía necesita aclaración antes del próximo ensayo privado.",
            },
            "en": {
                "screen_opening": "Present positioning supported by the supplied evidence, a relevant focus, and a safe bridge into the conversation.",
                "proof_example": "Present confirmed context, a concrete action, and directly observed impact.",
                "eligibility_boundary": "Separate the supplied fact, the unknown eligibility condition, and one clarification question.",
                "compensation_boundary": "Separate the supplied evidence, the pending compensation condition, and the decision boundary.",
                "missing_detail": "Present the supplied minimum and the one detail that still needs clarification before the next private rehearsal.",
            },
        }
        expected_actions = {
            "es": {
                "solid": "Conserva esta estructura para el próximo ensayo privado y mantén el alcance respaldado por la evidencia suministrada.",
                "confirm": "Confirma o acota el punto incierto antes del próximo ensayo privado.",
                "do_not_assert": "Quita la afirmación sin respaldo; sustitúyela por evidencia respaldada o una aclaración acotada, o pausa la respuesta.",
            },
            "en": {
                "solid": "Keep this structure for the next private rehearsal and stay within the scope supported by the supplied evidence.",
                "confirm": "Confirm or qualify the uncertain point before the next private rehearsal.",
                "do_not_assert": "Remove the unsupported claim; replace it with supported evidence or a bounded clarification, or pause the answer.",
            },
        }
        self.assertEqual(self.renderer.DECISION_TARGET_COPY, expected_targets)
        self.assertEqual(self.renderer.DECISION_ACTION_COPY, expected_actions)
        for locale, targets in expected_targets.items():
            for kind, target in targets.items():
                with self.subTest(locale=locale, kind=kind):
                    self.assertEqual(self.renderer._decision_target(locale, kind), target)
        for locale, actions in expected_actions.items():
            for label, action in actions.items():
                with self.subTest(locale=locale, label=label):
                    self.assertEqual(self.renderer._decision_action(locale, label), action)

    def test_governing_feedback_uses_most_cautious_present_label(self) -> None:
        cases = {
            ("solid",): "solid",
            ("confirm",): "confirm",
            ("do_not_assert",): "do_not_assert",
            ("solid", "confirm"): "confirm",
            ("solid", "do_not_assert"): "do_not_assert",
            ("confirm", "do_not_assert"): "do_not_assert",
            ("solid", "confirm", "do_not_assert"): "do_not_assert",
        }
        for labels, expected in cases.items():
            with self.subTest(labels=labels):
                self.assertEqual(
                    self.renderer._governing_feedback_label(labels), expected
                )

    def test_feedback_decision_helpers_fail_closed_without_echoing_input(self) -> None:
        cases = (
            (lambda: self.renderer._feedback_description("xx-private", "screen_opening", "solid"), "unsupported locale", "xx-private"),
            (lambda: self.renderer._feedback_description("es", "private-kind", "solid"), "unsupported question kind", "private-kind"),
            (lambda: self.renderer._feedback_description("es", "screen_opening", "private-label"), "unsupported feedback label", "private-label"),
            (lambda: self.renderer._decision_target("xx-private", "screen_opening"), "unsupported locale", "xx-private"),
            (lambda: self.renderer._decision_target("es", "private-kind"), "unsupported question kind", "private-kind"),
            (lambda: self.renderer._decision_action("xx-private", "solid"), "unsupported locale", "xx-private"),
            (lambda: self.renderer._decision_action("es", "private-label"), "unsupported feedback label", "private-label"),
            (lambda: self.renderer._governing_feedback_label(()), "feedback labels must not be empty", "private"),
            (lambda: self.renderer._governing_feedback_label(("solid", "solid")), "feedback labels must be unique", "private"),
            (lambda: self.renderer._governing_feedback_label(("confirm", "solid")), "feedback labels must use canonical order", "private"),
            (lambda: self.renderer._governing_feedback_label(("private-label",)), "unsupported feedback label", "private-label"),
        )
        for call, expected, private_value in cases:
            with self.subTest(expected=expected):
                with self.assertRaises(ValueError) as context:
                    call()
                self.assertEqual(str(context.exception), expected)
                self.assertNotIn(private_value, str(context.exception))

    def test_each_question_kind_renders_closed_bilingual_coaching(self) -> None:
        expected = {
            "screen_opening": {
                "es": ("Prepara una apertura breve que conecte la evidencia suministrada con la conversación.", ("Contexto suministrado", "Enfoque relevante", "Puente a la conversación")),
                "en": ("Prepare a brief opening that connects the supplied evidence to the conversation.", ("Supplied context", "Relevant focus", "Conversation bridge")),
            },
            "proof_example": {
                "es": ("Presenta una evidencia confirmada en tres movimientos fáciles de seguir.", ("Contexto de la evidencia", "Acción técnica concreta", "Impacto observado directo")),
                "en": ("Present confirmed evidence in three easy-to-follow moves.", ("Evidence context", "Concrete technical action", "Directly observed impact")),
            },
            "eligibility_boundary": {
                "es": ("Separa el dato suministrado de la pregunta de elegibilidad que aún debe aclararse.", ("Dato suministrado", "Pregunta abierta", "Límite seguro")),
                "en": ("Separate the supplied fact from the eligibility question that still needs clarification.", ("Supplied fact", "Open question", "Safe boundary")),
            },
            "compensation_boundary": {
                "es": ("Separa lo conocido de la condición de compensación que necesitas aclarar.", ("Contexto conocido", "Pregunta de compensación", "Límite de decisión")),
                "en": ("Separate what is known from the compensation condition you need to clarify.", ("Known context", "Compensation question", "Decision boundary")),
            },
            "missing_detail": {
                "es": ("Expón el mínimo suministrado y formula solo el detalle que falta confirmar.", ("Mínimo suministrado", "Detalle faltante", "Próxima confirmación")),
                "en": ("State the supplied minimum and ask only for the detail still needing confirmation.", ("Supplied minimum", "Missing detail", "Next confirmation")),
            },
        }
        self.assertEqual(set(self.renderer.REHEARSAL_COPY), {"es", "en"})
        for locale in ("es", "en"):
            self.assertEqual(set(self.renderer.REHEARSAL_COPY[locale]), set(expected))
        for kind, localized in expected.items():
            for locale, (hint, steps) in localized.items():
                with self.subTest(kind=kind, locale=locale):
                    session = copy.deepcopy(self.awaiting_session)
                    session["question"]["kind"] = kind
                    session["locale"] = locale
                    rendered = self.renderer.render_session_html(session)
                    rehearsal = rendered.split('<section class="practice-rehearsal"', 1)[1].split("</section>", 1)[0]
                    self.assertIn(f'<p class="practice-rehearsal-hint">{hint}</p>', rehearsal)
                    self.assertEqual(re.findall(r"<li>(.*?)</li>", rehearsal), list(steps))

        with self.assertRaisesRegex(ValueError, "unsupported recruiter practice question kind: free_form"):
            self.renderer._render_rehearsal_scaffold("es", "free_form", self.renderer.COPY["es"])

    def test_non_proof_rehearsal_never_upgrades_candidate_reported_facts(self) -> None:
        expected = {
            "es": {
                "screen_opening": ("Prepara una apertura breve que conecte la evidencia suministrada con la conversación.", "Contexto suministrado"),
                "eligibility_boundary": ("Separa el dato suministrado de la pregunta de elegibilidad que aún debe aclararse.", "Dato suministrado"),
                "compensation_boundary": ("Separa lo conocido de la condición de compensación que necesitas aclarar.", "Contexto conocido"),
                "missing_detail": ("Expón el mínimo suministrado y formula solo el detalle que falta confirmar.", "Mínimo suministrado"),
            },
            "en": {
                "screen_opening": ("Prepare a brief opening that connects the supplied evidence to the conversation.", "Supplied context"),
                "eligibility_boundary": ("Separate the supplied fact from the eligibility question that still needs clarification.", "Supplied fact"),
                "compensation_boundary": ("Separate what is known from the compensation condition you need to clarify.", "Known context"),
                "missing_detail": ("State the supplied minimum and ask only for the detail still needing confirmation.", "Supplied minimum"),
            },
        }
        for locale, kinds in expected.items():
            for kind, (hint, first_step) in kinds.items():
                for state in ("ready_to_practice", "awaiting_answer", "feedback_available"):
                    session = self.feedback_session() if state == "feedback_available" else copy.deepcopy(self.awaiting_session)
                    session["locale"] = locale
                    session["state"] = state
                    session["question"]["kind"] = kind
                    session["facts"][0]["state"] = "candidate_reported"
                    if state != "feedback_available":
                        session["observed_answer"] = None
                        session["feedback"] = {
                            "score": "unknown",
                            "score_state": "unknown",
                            "observations": [],
                        }
                    with self.subTest(locale=locale, kind=kind, state=state):
                        rendered = self.renderer.render_session_html(session)
                        rehearsal = rendered.split('<section class="practice-rehearsal"', 1)[1].split("</section>", 1)[0]
                        self.assertIn(f'<p class="practice-rehearsal-hint">{hint}</p>', rehearsal)
                        self.assertIn(f"<li>{first_step}</li>", rehearsal)
                        self.assertNotRegex(
                            rehearsal.casefold(),
                            r"\b(?:confirmad[oa]s?|verified|confirmed)\b",
                        )

    def test_non_proof_rehearsal_evidence_guard_detects_confirmed(self) -> None:
        self.assertRegex(
            "confirmed",
            r"\b(?:confirmad[oa]s?|verified|confirmed)\b",
        )

    def test_chat_summary_and_html_reject_internal_ids_in_question_prose(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["question"]["text"] = "Practica Q-001 en privado."
        with self.assertRaises(self.renderer.SessionValidationError):
            self.renderer.build_chat_summary(invalid)
        with self.assertRaises(self.renderer.SessionValidationError):
            self.renderer.render_session_html(invalid)

    def test_renderer_rejects_unsupported_script_prose_without_echoing_content(self) -> None:
        invalid = copy.deepcopy(self.awaiting_session)
        invalid["facts"][0]["summary"] = "Алексей Иванов описал опыт."
        with self.assertRaises(self.renderer.SessionValidationError) as captured:
            self.renderer.render_session_html(invalid)
        self.assertIn("session contains forbidden unsupported_script prose", captured.exception.errors)
        self.assertNotIn("Алексей Иванов", str(captured.exception.errors))

    def test_awaiting_answer_renders_english_context_and_prompt(self) -> None:
        rendered = self.renderer.render_session_html(self.english_session())

        self.assertIn('lang="en"', rendered)
        self.assertIn("Safe context", rendered)
        self.assertIn("Practice prompt", rendered)
        self.assertIn("Ready to answer", rendered)
        self.assertNotIn("Awaiting your answer", rendered)
        self.assertIn("No external action was taken.", rendered)

    def test_feedback_is_rendered_only_for_an_observed_answer_without_retaining_raw_answer(self) -> None:
        raw_answer = "Organicé el proceso y expliqué el alcance que confirmé."
        rendered = self.renderer.render_session_html(self.feedback_session())

        self.assertIn("Comentarios sobre la respuesta", rendered)
        self.assertIn(
            "Una versión respaldada distingue el contexto confirmado, una acción concreta y un impacto observado directamente.",
            rendered,
        )
        self.assertNotIn(raw_answer, rendered)
        self.assertNotIn("unknown", rendered.casefold())

    def test_handoff_context_question_id_matches_practice_question(self) -> None:
        session = self.feedback_session()
        session["state"] = "awaiting_answer"
        session["observed_answer"] = None
        session["feedback"] = {"score": "unknown", "score_state": "unknown", "observations": []}
        self.assertEqual(self.renderer.VALIDATOR.validate_session(session), [])

        missing = copy.deepcopy(session)
        del missing["handoff_context"]["question_id"]
        self.assertTrue(any("missing required field: handoff_context.question_id" in error for error in self.renderer.VALIDATOR.validate_session(missing)))

        mismatched = copy.deepcopy(session)
        mismatched["handoff_context"]["question_id"] = "Q-002"
        self.assertIn("handoff_context.question_id must match question.id", self.renderer.VALIDATOR.validate_session(mismatched))

        invalid = copy.deepcopy(session)
        invalid["handoff_context"]["question_id"] = "not-a-question"
        self.assertTrue(any("handoff_context.question_id must use the Q-000 identifier format" in error for error in self.renderer.VALIDATOR.validate_session(invalid)))

        fact_mismatch = copy.deepcopy(session)
        fact_mismatch["handoff_context"]["fact_ids"] = ["F-999"]
        self.assertTrue(any("handoff_context.fact_ids references unknown identifier: F-999" in error for error in self.renderer.VALIDATOR.validate_session(fact_mismatch)))

    def test_handoff_context_source_is_closed_and_not_rendered(self) -> None:
        session = self.feedback_session()
        session["state"] = "awaiting_answer"
        session["observed_answer"] = None
        session["feedback"] = {"score": "unknown", "score_state": "unknown", "observations": []}
        session["handoff_context"]["source"] = "private_recruiter_reply_triage"
        session["handoff_context"]["source_snapshot"] = "snap-triage-001"
        errors = self.renderer.VALIDATOR.validate_session(session)
        self.assertEqual(errors, [])
        rendered = self.renderer.render_session_html(session)
        self.assertIn('practice-handoff--reply', rendered)
        self.assertNotIn("private_recruiter_reply_triage", rendered)
        session["handoff_context"]["source"] = "untrusted_source"
        self.assertIn("handoff_context.source has invalid value", self.renderer.VALIDATOR.validate_session(session))

    def test_handoff_context_requirement_id_matches_question_and_requirement(self) -> None:
        session = self.feedback_session()
        session["state"] = "awaiting_answer"
        session["observed_answer"] = None
        session["feedback"] = {"score": "unknown", "score_state": "unknown", "observations": []}
        self.assertEqual(self.renderer.VALIDATOR.validate_session(session), [])
        missing = copy.deepcopy(session)
        del missing["handoff_context"]["requirement_id"]
        self.assertTrue(any("missing required field: handoff_context.requirement_id" in error for error in self.renderer.VALIDATOR.validate_session(missing)))
        invalid = copy.deepcopy(session)
        invalid["handoff_context"]["requirement_id"] = "R-invalid"
        self.assertTrue(any("handoff_context.requirement_id must use the R-000 identifier format" in error for error in self.renderer.VALIDATOR.validate_session(invalid)))
        mismatch = copy.deepcopy(session)
        mismatch["handoff_context"]["requirement_id"] = "R-002"
        errors = self.renderer.VALIDATOR.validate_session(mismatch)
        self.assertIn("handoff_context.requirement_id must match requirement.id", errors)
        self.assertIn("handoff_context.requirement_id must match question.requirement_id", errors)

    def test_handoff_context_source_snapshot_is_bounded_and_hidden(self) -> None:
        session = self.feedback_session()
        session["state"] = "awaiting_answer"
        session["observed_answer"] = None
        session["feedback"] = {"score": "unknown", "score_state": "unknown", "observations": []}
        self.assertEqual(self.renderer.VALIDATOR.validate_session(session), [])
        rendered = self.renderer.render_session_html(session)
        self.assertNotIn("snap-dossier-sha256-873fb8cf4957d72c0aa06a15b253716a3d0397d45997073adb0b8e486decfa25", rendered)
        missing = copy.deepcopy(session)
        del missing["handoff_context"]["source_snapshot"]
        self.assertTrue(any("missing required field: handoff_context.source_snapshot" in error for error in self.renderer.VALIDATOR.validate_session(missing)))
        invalid = copy.deepcopy(session)
        invalid["handoff_context"]["source_snapshot"] = "snapshot-with-sensitive-url"
        self.assertIn("handoff_context.source_snapshot must use the bound dossier or snap-triage-000 identifier format", self.renderer.VALIDATOR.validate_session(invalid))
        wrong_source = copy.deepcopy(session)
        wrong_source["handoff_context"]["source"] = "private_recruiter_reply_triage"
        self.assertIn("handoff_context.source_snapshot must match private_recruiter_reply_triage source", self.renderer.VALIDATOR.validate_session(wrong_source))

    def test_v2_phone_like_snapshot_remains_hidden_in_rendered_practice_card(self) -> None:
        session = copy.deepcopy(self.awaiting_session)
        session["schema_version"] = "recruiter-practice-session-v2"
        session["ui_locale"] = "en"
        session["content_locale"] = "es"
        del session["locale"]
        session["handoff_context"]["source"] = "private_recruiter_reply_triage"
        session["handoff_context"]["source_snapshot"] = V2_TRIAGE_PHONE_LIKE_SNAPSHOT
        session["handoff_context"].pop("claim_ids")
        session["handoff_context"].pop("evidence_ids")
        self.assertEqual(self.renderer.VALIDATOR.validate_session(session), [])
        rendered = self.renderer.render_session_html(session)
        self.assertNotIn("source_snapshot", rendered)
        self.assertNotIn(V2_TRIAGE_PHONE_LIKE_SNAPSHOT, rendered)

    def test_dossier_handoff_requires_claim_and_evidence_provenance(self) -> None:
        session = self.feedback_session()
        session["state"] = "awaiting_answer"
        session["observed_answer"] = None
        session["feedback"] = {"score": "unknown", "score_state": "unknown", "observations": []}
        del session["handoff_context"]["claim_ids"]
        del session["handoff_context"]["evidence_ids"]
        errors = self.renderer.VALIDATOR.validate_session(session)
        self.assertIn("handoff_context.claim_ids must contain C-000 identifiers for dossier source", errors)
        self.assertIn("handoff_context.evidence_ids must contain E-000 identifiers for dossier source", errors)

    def test_handoff_provenance_rejects_duplicate_or_malformed_ids_for_any_source(self) -> None:
        duplicate = copy.deepcopy(self.awaiting_session)
        duplicate["handoff_context"]["claim_ids"] = ["C-001", "C-001"]
        duplicate["handoff_context"]["evidence_ids"] = ["E-001", "E-001"]
        errors = self.renderer.VALIDATOR.validate_session(duplicate)
        self.assertIn("handoff_context.claim_ids must contain unique C-000 identifiers", errors)
        self.assertIn("handoff_context.evidence_ids must contain unique E-000 identifiers", errors)

        malformed = copy.deepcopy(self.awaiting_session)
        malformed["handoff_context"]["source"] = "private_recruiter_reply_triage"
        malformed["handoff_context"]["source_snapshot"] = "snap-triage-001"
        malformed["handoff_context"]["evidence_ids"] = ["not-an-evidence-id"]
        self.assertIn("handoff_context.evidence_ids must contain E-000 identifiers", self.renderer.VALIDATOR.validate_session(malformed))

        for empty in ([], None):
            candidate = copy.deepcopy(malformed)
            candidate["handoff_context"]["evidence_ids"] = empty
            self.assertIn("handoff_context.evidence_ids must be a non-empty list", self.renderer.VALIDATOR.validate_session(candidate))

        oversized = copy.deepcopy(self.awaiting_session)
        oversized["handoff_context"]["claim_ids"] = [f"C-{index:03d}" for index in range(1, 12)]
        self.assertIn("handoff_context.claim_ids must contain at most 10 identifiers", self.renderer.VALIDATOR.validate_session(oversized))

    def test_handoff_copy_matches_reply_triage_source_in_both_locales(self) -> None:
        session = copy.deepcopy(self.awaiting_session)
        session["handoff_context"]["source"] = "private_recruiter_reply_triage"
        session["handoff_context"]["source_snapshot"] = "snap-triage-001"
        rendered = self.renderer.render_session_html(session)
        self.assertIn("triaje privado de respuesta de reclutador", rendered)
        self.assertNotIn("dossier de carrera", rendered)

        session["locale"] = "en"
        rendered = self.renderer.render_session_html(session)
        self.assertIn("private recruiter-reply triage", rendered)
        self.assertNotIn("career dossier", rendered)

    def test_feedback_region_is_a_quiet_named_region_with_ephemeral_answer_note(self) -> None:
        rendered = self.renderer.render_session_html(self.feedback_session())

        self.assertIn(
            '<section class="practice-feedback" role="region" '
            'aria-labelledby="feedback-title" aria-describedby="feedback-ephemeral-note">',
            rendered,
        )
        self.assertNotIn('class="practice-feedback" aria-live=', rendered)
        self.assertIn(
            '<p class="visually-hidden" id="feedback-ephemeral-note">'
            'La respuesta se usó solo para esta práctica y no se conserva.</p>',
            rendered,
        )

    def test_feedback_available_state_chip_has_a_matching_css_selector(self) -> None:
        rendered = self.renderer.render_session_html(self.feedback_session())

        self.assertIn(
            '<p id="practice-session-state" class="state-chip state-chip--feedback_available">',
            rendered,
        )
        self.assertIn(
            ".recruiter-practice-document .state-chip--feedback_available {",
            rendered,
        )

    def test_feedback_decision_css_covers_contrast_mobile_print_and_system_modes(self) -> None:
        rendered = self.renderer.render_session_html(self.feedback_session())
        self.assertIn("--decision-term: #dfbf70;", rendered)
        self.assertIn(
            "color: var(--ink);",
            self._css_block(rendered, ".recruiter-practice-document .feedback-label"),
        )
        for suffix in ("solid", "confirm", "do_not_assert"):
            block = self._css_block(
                rendered,
                f".recruiter-practice-document .feedback-label--{suffix}",
            )
            self.assertIn("color: var(--ink);", block)
        self.assertIn(
            "color: var(--decision-term);",
            self._css_block(
                rendered, ".recruiter-practice-document .practice-decision dt"
            ),
        )
        for selector in (
            ".recruiter-practice-document .practice-decision dl",
            ".recruiter-practice-document .practice-decision dt",
            ".recruiter-practice-document .practice-decision dd",
        ):
            block = self._css_block(rendered, selector)
            self.assertTrue(
                "min-width: 0;" in block or "overflow-wrap:" in block,
                selector,
            )
        self.assertRegex(
            rendered,
            r"(?s)@media \(max-width: 640px\).*?\.practice-shell\s*\{[^}]*width: min\(100% - 1rem, 920px\);",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(forced-colors: active\).*?\.practice-feedback[^}]*background: Canvas;[^}]*color: CanvasText;.*?\.practice-decision[^}]*background: Canvas;[^}]*color: CanvasText;",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(forced-colors: active\).*?\.practice-decision h2,[^{]*\.practice-decision dt,[^{]*\.practice-decision dd\s*\{[^}]*color: CanvasText;",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media \(prefers-contrast: more\).*?\.practice-feedback,[^{]*\.feedback-item,[^{]*\.practice-decision\s*\{[^}]*border-width: 2px;",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media print.*?\.practice-feedback\s*\{[^}]*break-after: avoid-page;[^}]*\}.*?\.practice-decision\s*\{[^}]*break-before: avoid-page;[^}]*\}",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media print.*?\.practice-decision h2,[^{]*\.practice-decision dt,[^{]*\.practice-decision dd\s*\{[^}]*color: var\(--ink\);",
        )

    def test_rendering_never_exposes_contract_identifiers_or_remote_dependencies(self) -> None:
        rendered = self.renderer.render_session_html(self.feedback_session())

        self.assertNotRegex(rendered, r"\b(?:F|R|Q|RB|OBS)-\d{3}\b")
        for token in ("<script", "<link rel=", "@import", "fetch(", "fonts.googleapis.com"):
            with self.subTest(token=token):
                self.assertNotIn(token, rendered)

    def test_renderer_rejects_feedback_that_echoes_raw_answers_or_internal_identifiers(self) -> None:
        cases = (
            (
                "raw_answer",
                "Organicé el proceso y expliqué el alcance que confirmé.",
                "feedback.observations[0].statement must not repeat the observed answer",
            ),
            (
                "observed_answer_id",
                "OBS-001 describe una acción concreta.",
                "feedback.observations[0].statement must not expose internal identifiers",
            ),
            (
                "rubric_id",
                "La respuesta cumple RB-001.",
                "feedback.observations[0].statement must not expose internal identifiers",
            ),
        )
        for name, statement, message in cases:
            with self.subTest(case=name):
                invalid = self.feedback_session()
                invalid["feedback"]["observations"][0]["statement"] = statement

                with self.assertRaises(self.renderer.SessionValidationError) as context:
                    self.renderer.render_session_html(invalid)

                self.assertIn(message, context.exception.errors)

    def test_rendered_document_has_accessible_landmarks_and_responsive_print_motion_rules(self) -> None:
        rendered = self.renderer.render_session_html(self.awaiting_session)

        self.assertIn('<a class="skip-link" href="#main-content">', rendered)
        self.assertIn("<header", rendered)
        self.assertIn('<main id="main-content"', rendered)
        self.assertIn("<footer", rendered)
        self.assertIn('aria-labelledby="practice-session-title"', rendered)
        self.assertIn("@media (max-width: 640px)", rendered)
        self.assertIn("@media print", rendered)
        self.assertIn("@media (prefers-reduced-motion: reduce)", rendered)
        self.assertIn("@media (prefers-contrast: more)", rendered)
        self.assertIn("animation: none !important", rendered)
        self.assertIn("transition: none !important", rendered)

    def test_print_keeps_next_action_ink_safe_and_freezes_entrance_motion(self) -> None:
        rendered = self.renderer.render_session_html(self.awaiting_session)
        self.assertRegex(
            rendered,
            r"(?s)@media print.*?\.practice-next-action\s*\{[^}]*background:\s*transparent;[^}]*color:\s*var\(--ink\);[^}]*border:\s*1px solid var\(--ink\);[^}]*border-left-width:\s*4px;",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media print.*?\.practice-next-action h2\s*\{[^}]*color:\s*var\(--ink\);",
        )
        self.assertRegex(
            rendered,
            r"(?s)@media print.*?\.practice-session\s*\{[^}]*animation:\s*none !important;[^}]*transition:\s*none !important;[^}]*transform:\s*none !important;",
        )

    def test_malformed_reference_types_fail_closed_without_renderer_crash(self) -> None:
        for field in ("requirement", "question"):
            invalid = copy.deepcopy(self.awaiting_session)
            invalid[field]["fact_ids"] = [{}]
            with self.assertRaises(self.renderer.SessionValidationError):
                self.renderer.render_session_html(invalid)

    def test_rendering_is_byte_deterministic(self) -> None:
        first = self.renderer.render_session_html(self.awaiting_session)
        second = self.renderer.render_session_html(copy.deepcopy(self.awaiting_session))

        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))

    def test_private_writer_uses_mode_0600_and_refuses_symlinked_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "private" / "recruiter-practice-session.html"
            receipt = self.renderer.write_session_html(FIXTURE_PATH, output)

            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(output.parent.stat().st_mode), 0o700)
            self.assertEqual(receipt.artifact_path, Path(os.path.abspath(output)))

            victim = root / "victim.html"
            victim.write_text("keep", encoding="utf-8")
            linked_output = root / "linked.html"
            linked_output.symlink_to(victim)
            with self.assertRaises(OSError):
                self.renderer.write_session_html(FIXTURE_PATH, linked_output, force=True)
            self.assertEqual(victim.read_text(encoding="utf-8"), "keep")


class RecruiterPracticeSessionRendererCliTests(unittest.TestCase):
    def test_cli_normalizes_unknown_missing_and_help_args(self) -> None:
        invalid = subprocess.run([sys.executable, "-B", str(RENDERER_PATH), str(FIXTURE_PATH), "--output", "/tmp/practice.html", "--unknown"], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 3)
        missing = subprocess.run([sys.executable, "-B", str(RENDERER_PATH), str(FIXTURE_PATH)], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 3)
        help_result = subprocess.run([sys.executable, "-B", str(RENDERER_PATH), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)

    def test_cli_writes_private_html_and_emits_a_minimal_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "session.html"
            result = subprocess.run(
                [sys.executable, "-B", str(RENDERER_PATH), str(FIXTURE_PATH), "--output", str(output)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertEqual(receipt["artifact_path"], os.path.abspath(output))
            self.assertEqual(receipt["artifact_type"], "text/html")
            self.assertEqual(receipt["locale"], "es")
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertFalse(re.search(r"\b(?:F|R|Q|RB|OBS)-\d{3}\b", output.read_text(encoding="utf-8")))
