#!/usr/bin/env python3
"""Render a validated recruiter-practice session as private, offline HTML."""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import os
import re
import secrets
import stat
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
TEMPLATE_PATH = ASSET_ROOT / "recruiter-practice-session-v1.html"
CSS_PATH = ASSET_ROOT / "recruiter-practice-session-v1.css"
TEMPLATE_TOKENS = ("{{LANG}}", "{{TITLE}}", "{{INLINE_CSS}}", "{{HEADER}}", "{{MAIN}}")
STATIC_TEMPLATE_TOKEN = re.compile(r"\{\{[A-Z_]+\}\}")


def _load_asset_loader() -> Any:
    path = Path(__file__).with_name("private_asset_loader.py")
    specification = importlib.util.spec_from_file_location("private_renderer_asset_loader", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("private renderer asset loader is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


ASSET_LOADER = _load_asset_loader()


def _load_validator() -> Any:
    path = Path(__file__).with_name("validate_recruiter_practice_session.py")
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_recruiter_practice_validator", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("recruiter practice validator is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


def _load_triage_practice_prose_guard() -> Any:
    path = Path(__file__).with_name("triage_practice_prose_safety.py")
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_triage_practice_prose_safety", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("triage practice prose guard is unavailable")
    module = importlib.util.module_from_spec(specification)
    scripts_dir = str(path.parent)
    added_path = scripts_dir not in sys.path
    if added_path:
        sys.path.insert(0, scripts_dir)
    try:
        specification.loader.exec_module(module)
    finally:
        if added_path:
            sys.path.remove(scripts_dir)
    return module


TRIAGE_PROSE_GUARD = _load_triage_practice_prose_guard()


class SessionValidationError(ValueError):
    """Raised when renderer input does not satisfy the closed session contract."""

    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("recruiter practice session validation failed")


@dataclass(frozen=True, slots=True)
class RenderReceipt:
    artifact_path: Path
    artifact_type: str
    locale: str
    chat_summary: str


COPY = {
    "es": {
        "title": "Práctica privada con reclutador",
        "skip": "Saltar al contenido principal",
        "kicker": "Ensayo privado",
        "heading": "Práctica para primera conversación",
        "ready_to_practice": "Lista para practicar",
        "awaiting_answer": "Lista para responder",
        "feedback_available": "Comentarios disponibles",
        "context": "Contexto seguro",
        "focus": "Enfoque de la práctica",
        "prompt": "Pregunta para practicar",
        "question_purpose": "Propósito de la pregunta",
        "purpose_screen_opening": "Abre la preparación para la conversación inicial.",
        "purpose_proof_example": "Selecciona un ejemplo de evidencia confirmada.",
        "purpose_eligibility_boundary": "Aclara el límite de elegibilidad relevante.",
        "purpose_compensation_boundary": "Aclara el límite de compensación relevante.",
        "purpose_missing_detail": "Encuentra el detalle mínimo que falta.",
        "rehearsal": "Estructura de respuesta",
        "next_action": "Siguiente paso",
        "next_action_ready": "Lee la pregunta y prepara tu respuesta en tres movimientos. No se guarda tu respuesta.",
        "next_action_answer": "Responde con contexto breve, acción concreta y resultado observado. No se guarda tu respuesta.",
        "next_action_sourced_ready": "Lee la pregunta y prepara tu respuesta; después regresa a la conversación privada de Codex que originó esta práctica. Esta página no guarda tu respuesta.",
        "next_action_sourced_answer": "Regresa a la conversación privada de Codex que originó esta práctica para responder. Esta página no guarda tu respuesta.",
        "evidence": "Puntos de evidencia",
        "verified": "Confirmado",
        "candidate_reported": "Reportado por la persona",
        "boundary": "Límite seguro",
        "boundary_text": "Practica solo con el alcance confirmado; no afirmes resultados no observados.",
        "feedback": "Comentarios sobre la respuesta",
        "ephemeral_note": "La respuesta se usó solo para esta práctica y no se conserva.",
        "decision_heading": "Decide tu siguiente versión",
        "decision_governing": "Señal prioritaria",
        "decision_target": "Objetivo de esta respuesta",
        "decision_action": "Decisión antes de volver a practicar",
        "decision_explanation": "Cuando aparecen varias señales, la que requiere más cautela guía la siguiente versión.",
        "handoff_title": "Origen de práctica",
        "handoff_text_dossier": "Esta pregunta proviene de un dossier de carrera y se practica en privado; no se realizó ninguna acción externa.",
        "handoff_text_reply": "Esta pregunta proviene de un triaje privado de respuesta de reclutador y se practica en privado; no se realizó ninguna acción externa.",
        "solid": "Sólido",
        "confirm": "Por confirmar",
        "do_not_assert": "No afirmar todavía",
        "footer": "No se realizó ninguna acción externa.",
        "employment_boundary": "Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
        "summary": "Práctica privada: ",
    },
    "en": {
        "title": "Private recruiter practice",
        "skip": "Skip to main content",
        "kicker": "Private rehearsal",
        "heading": "First-conversation practice",
        "ready_to_practice": "Ready to practice",
        "awaiting_answer": "Ready to answer",
        "feedback_available": "Feedback available",
        "context": "Safe context",
        "focus": "Practice focus",
        "prompt": "Practice prompt",
        "question_purpose": "Question purpose",
        "purpose_screen_opening": "Opens preparation for the first conversation.",
        "purpose_proof_example": "Selects one confirmed evidence example.",
        "purpose_eligibility_boundary": "Clarifies the relevant eligibility boundary.",
        "purpose_compensation_boundary": "Clarifies the relevant compensation boundary.",
        "purpose_missing_detail": "Finds the smallest missing detail.",
        "rehearsal": "Answer structure",
        "next_action": "Next step",
        "next_action_ready": "Read the question and prepare your answer in three moves. Your answer is not saved.",
        "next_action_answer": "Answer with brief context, a concrete action, and an observed result. Your answer is not saved.",
        "next_action_sourced_ready": "Read the question and prepare your answer; then return to the private Codex conversation that originated this practice. This page does not save your answer.",
        "next_action_sourced_answer": "Return to the private Codex conversation that originated this practice to answer. This page does not save your answer.",
        "evidence": "Evidence points",
        "verified": "Verified",
        "candidate_reported": "Candidate-reported",
        "boundary": "Safe boundary",
        "boundary_text": "Practice only within the confirmed scope; do not assert unobserved results.",
        "feedback": "Feedback on the answer",
        "ephemeral_note": "The answer was used only for this practice and is not retained.",
        "decision_heading": "Decide your next version",
        "decision_governing": "Governing feedback",
        "decision_target": "Target for this answer",
        "decision_action": "Decision before rehearsing again",
        "decision_explanation": "When several signals appear, the one requiring the most caution guides the next version.",
        "handoff_title": "Practice source",
        "handoff_text_dossier": "This question came from a career dossier and is practiced privately; no external action was taken.",
        "handoff_text_reply": "This question came from a private recruiter-reply triage and is practiced privately; no external action was taken.",
        "solid": "Solid",
        "confirm": "Confirm",
        "do_not_assert": "Do not assert yet",
        "footer": "No external action was taken.",
        "employment_boundary": "This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.",
        "summary": "Private practice: ",
    },
}


QUESTION_KINDS = (
    "screen_opening",
    "proof_example",
    "eligibility_boundary",
    "compensation_boundary",
    "missing_detail",
)
FEEDBACK_LABELS = ("solid", "confirm", "do_not_assert")
FEEDBACK_PRECEDENCE = {
    label: index for index, label in enumerate(FEEDBACK_LABELS)
}

FEEDBACK_DESCRIPTION_COPY = {
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

DECISION_TARGET_COPY = {
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

DECISION_ACTION_COPY = {
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

CONTINUITY_COPY = {
    "en": {
        "title": "Manual continuity route",
        "kicker": "Route at a glance",
        "states": {"current": "Current", "pending": "Pending", "blocked": "Blocked"},
        "steps": (
            ("evidence", "current", "Supplied evidence", "Use only the evidence already in the private session."),
            ("rehearsal", "current", "Rehearsal", "Practice the bounded answer structure without saving it."),
            ("next-version", "pending", "Next version", "Review the next answer privately before any external action."),
        ),
    },
    "es": {
        "title": "Ruta de continuidad manual",
        "kicker": "Ruta de un vistazo",
        "states": {"current": "Actual", "pending": "Pendiente", "blocked": "Bloqueada"},
        "steps": (
            ("evidence", "current", "Evidencia suministrada", "Usa solo la evidencia ya presente en la sesión privada."),
            ("rehearsal", "current", "Ensayo", "Practica la estructura acotada sin guardarla."),
            ("next-version", "pending", "Siguiente versión", "Revisa en privado la próxima respuesta antes de cualquier acción externa."),
        ),
    },
}


READINESS_COPY = {
    "en": {
        "title": "First-conversation readiness",
        "kicker": "Before rehearsal",
        "intro": "Check the minimum conditions for a private recruiter-screen practice.",
        "stage_label": "Stage",
        "stage_value": "Recruiter screen",
        "evidence_label": "Evidence",
        "evidence_verified": "Confirmed",
        "evidence_candidate_reported": "Needs confirmation",
        "boundary_label": "Boundary",
        "boundary_value": "Private preparation only",
        "next_label": "Next",
        "next_value": "Private review before any external action",
        "current": "Current",
        "pending": "Pending",
    },
    "es": {
        "title": "Preparación de primera conversación",
        "kicker": "Antes de ensayar",
        "intro": "Comprueba las condiciones mínimas para una práctica privada de filtro inicial.",
        "stage_label": "Etapa",
        "stage_value": "Filtro inicial",
        "evidence_label": "Evidencia",
        "evidence_verified": "Confirmada",
        "evidence_candidate_reported": "Por confirmar",
        "boundary_label": "Límite",
        "boundary_value": "Solo preparación privada",
        "next_label": "Siguiente",
        "next_value": "Revisión privada antes de cualquier acción externa",
        "current": "Actual",
        "pending": "Pendiente",
    },
}


TRIAGE_ROUTE_COPY = {
    "en": {
        "title": "Private practice route",
        "kicker": "Validated private handoff",
        "steps": ("Validated triage", "Private rehearsal", "Private review"),
    },
    "es": {
        "title": "Ruta de práctica privada",
        "kicker": "Traspaso privado validado",
        "steps": ("Triaje validado", "Ensayo privado", "Revisión privada"),
    },
}


CLAIM_GUARDRAIL_COPY = {
    "en": {
        "title": "Your answer boundary",
        "label": "Use only confirmed evidence",
        "instruction": "Do not add outcomes, scope, or availability that are not confirmed.",
    },
    "es": {
        "title": "Límite de tu respuesta",
        "label": "Usa solo evidencia confirmada",
        "instruction": "No agregues resultados, alcance ni disponibilidad que no estén confirmados.",
    },
}


def _render_claim_guardrail(locale: str, fact: Mapping[str, object]) -> str:
    labels = CLAIM_GUARDRAIL_COPY[locale]
    fact_summary = _text(fact["summary"])
    if re.search(r"(?:https?://|www\.)", fact_summary, flags=re.IGNORECASE):
        raise ValueError("practice answer boundary fact summary must not contain a URL")
    summary = html.escape(fact_summary)
    return f'''<section class="practice-claim-guardrail" aria-labelledby="practice-claim-guardrail-title">
      <h2 id="practice-claim-guardrail-title">{labels["title"]}</h2>
      <p><strong>{labels["label"]}:</strong> <span>{summary}</span></p>
      <p>{labels["instruction"]}</p>
    </section>'''


def _require_safe_triage_prose(
    context: Mapping[str, object], question: Mapping[str, object], fact: Mapping[str, object]
) -> None:
    """Keep triage-derived dynamic text out of HTML unless it is safe to project."""
    fields = (
        (context.get("summary"), 280),
        (question.get("text"), 500),
        (fact.get("summary"), 500),
    )
    if not all(TRIAGE_PROSE_GUARD.is_safe_triage_practice_prose(value, maximum) for value, maximum in fields):
        raise ValueError("triage-sourced practice prose contains a URL, contact, path, or credential-shaped value")


def _render_triage_practice_route(locale: str) -> str:
    labels = TRIAGE_ROUTE_COPY[locale]
    steps = "".join(
        f'<li class="triage-practice-route-step"><strong>{html.escape(step)}</strong></li>'
        for step in labels["steps"]
    )
    return f'''<section class="triage-practice-route" aria-label="{labels["title"]}">
      <p class="triage-practice-route-kicker">{labels["kicker"]}</p>
      <h2>{labels["title"]}</h2>
      <ol class="triage-practice-route-list">{steps}</ol>
    </section>'''


def _continuity_rail(locale: str) -> str:
    labels = CONTINUITY_COPY[locale]
    steps = "".join(
        f'<li class="continuity-step continuity-step--{state}" data-stage="{stage}" data-state="{state}">'
        f'<span class="continuity-step-state">{labels["states"][state]}</span>'
        f'<strong>{title}</strong><p>{description}</p></li>'
        for stage, state, title, description in labels["steps"]
    )
    return (
        '<section class="continuity-rail" aria-labelledby="continuity-rail-title">'
        f'<p class="continuity-rail-kicker">{labels["kicker"]}</p>'
        f'<h2 id="continuity-rail-title">{labels["title"]}</h2>'
        f'<ol class="continuity-rail-list">{steps}</ol></section>'
    )


def _render_screen_readiness(
    locale: str, state: str, fact_state: str
) -> str:
    labels = READINESS_COPY[locale]
    evidence_state = "current" if fact_state == "verified" else "pending"
    next_state = "pending" if state == "feedback_available" else "current"
    evidence_value = labels[f"evidence_{fact_state}"]
    return f'''<section class="screen-readiness" aria-labelledby="screen-readiness-title">
      <p class="screen-readiness-kicker">{labels["kicker"]}</p>
      <h2 id="screen-readiness-title">{labels["title"]}</h2>
      <p class="screen-readiness-intro">{labels["intro"]}</p>
      <div class="screen-readiness-grid">
        <div class="screen-readiness-item screen-readiness-item--current" data-state="current">
          <span class="screen-readiness-label">{labels["stage_label"]}</span><strong>{labels["stage_value"]}</strong><span class="screen-readiness-state">{labels["current"]}</span>
        </div>
        <div class="screen-readiness-item screen-readiness-item--{evidence_state}" data-state="{evidence_state}">
          <span class="screen-readiness-label">{labels["evidence_label"]}</span><strong>{evidence_value}</strong><span class="screen-readiness-state">{labels[evidence_state]}</span>
        </div>
        <div class="screen-readiness-item screen-readiness-item--current" data-state="current">
          <span class="screen-readiness-label">{labels["boundary_label"]}</span><strong>{labels["boundary_value"]}</strong><span class="screen-readiness-state">{labels["current"]}</span>
        </div>
        <div class="screen-readiness-item screen-readiness-item--{next_state}" data-state="{next_state}">
          <span class="screen-readiness-label">{labels["next_label"]}</span><strong>{labels["next_value"]}</strong><span class="screen-readiness-state">{labels[next_state]}</span>
        </div>
      </div>
    </section>'''


REHEARSAL_COPY = {
    "es": {
        "screen_opening": {
            "hint": "Prepara una apertura breve que conecte la evidencia suministrada con la conversación.",
            "steps": ("Contexto suministrado", "Enfoque relevante", "Puente a la conversación"),
        },
        "proof_example": {
            "hint": "Presenta una evidencia confirmada en tres movimientos fáciles de seguir.",
            "steps": ("Contexto de la evidencia", "Acción técnica concreta", "Impacto observado directo"),
        },
        "eligibility_boundary": {
            "hint": "Separa el dato suministrado de la pregunta de elegibilidad que aún debe aclararse.",
            "steps": ("Dato suministrado", "Pregunta abierta", "Límite seguro"),
        },
        "compensation_boundary": {
            "hint": "Separa lo conocido de la condición de compensación que necesitas aclarar.",
            "steps": ("Contexto conocido", "Pregunta de compensación", "Límite de decisión"),
        },
        "missing_detail": {
            "hint": "Expón el mínimo suministrado y formula solo el detalle que falta confirmar.",
            "steps": ("Mínimo suministrado", "Detalle faltante", "Próxima confirmación"),
        },
    },
    "en": {
        "screen_opening": {
            "hint": "Prepare a brief opening that connects the supplied evidence to the conversation.",
            "steps": ("Supplied context", "Relevant focus", "Conversation bridge"),
        },
        "proof_example": {
            "hint": "Present confirmed evidence in three easy-to-follow moves.",
            "steps": ("Evidence context", "Concrete technical action", "Directly observed impact"),
        },
        "eligibility_boundary": {
            "hint": "Separate the supplied fact from the eligibility question that still needs clarification.",
            "steps": ("Supplied fact", "Open question", "Safe boundary"),
        },
        "compensation_boundary": {
            "hint": "Separate what is known from the compensation condition you need to clarify.",
            "steps": ("Known context", "Compensation question", "Decision boundary"),
        },
        "missing_detail": {
            "hint": "State the supplied minimum and ask only for the detail still needing confirmation.",
            "steps": ("Supplied minimum", "Missing detail", "Next confirmation"),
        },
    },
}


def _require_locale(locale: str) -> None:
    if locale not in ("es", "en"):
        raise ValueError("unsupported locale")


def _require_question_kind(question_kind: str) -> None:
    if question_kind not in QUESTION_KINDS:
        raise ValueError("unsupported question kind")


def _require_feedback_label(label: str) -> None:
    if label not in FEEDBACK_LABELS:
        raise ValueError("unsupported feedback label")


def _feedback_description(locale: str, question_kind: str, label: str) -> str:
    _require_locale(locale)
    _require_question_kind(question_kind)
    _require_feedback_label(label)
    return FEEDBACK_DESCRIPTION_COPY[locale][question_kind][label]


def _decision_target(locale: str, question_kind: str) -> str:
    _require_locale(locale)
    _require_question_kind(question_kind)
    return DECISION_TARGET_COPY[locale][question_kind]


def _decision_action(locale: str, label: str) -> str:
    _require_locale(locale)
    _require_feedback_label(label)
    return DECISION_ACTION_COPY[locale][label]


def _governing_feedback_label(labels: Sequence[str]) -> str:
    if not labels:
        raise ValueError("feedback labels must not be empty")
    if not all(
        isinstance(label, str) and label in FEEDBACK_LABELS for label in labels
    ):
        raise ValueError("unsupported feedback label")
    if len(labels) != len(set(labels)):
        raise ValueError("feedback labels must be unique")
    canonical = tuple(label for label in FEEDBACK_LABELS if label in labels)
    if tuple(labels) != canonical:
        raise ValueError("feedback labels must use canonical order")
    return max(labels, key=FEEDBACK_PRECEDENCE.__getitem__)


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeError("validated session has invalid mapping")
    return value


def _rows(value: object) -> Sequence[Mapping[str, object]]:
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        raise RuntimeError("validated session has invalid rows")
    return value


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise RuntimeError("validated session has invalid text")
    return value


def _validate(session: Mapping[str, object]) -> Mapping[str, object]:
    errors = VALIDATOR.validate_session(session)
    if errors:
        raise SessionValidationError(errors)
    return session


def _render_header(locale: str) -> str:
    labels = COPY[locale]
    return f'''<a class="skip-link" href="#main-content">{labels["skip"]}</a>
  <header class="practice-header practice-shell">
    <div>
      <p class="practice-kicker">{labels["kicker"]}</p>
      <h1 id="practice-session-title">{labels["heading"]}</h1>
    </div>
  </header>'''


def _render_feedback(
    locale: str,
    question_kind: str,
    feedback_labels: Sequence[str],
    labels: Mapping[str, str],
) -> str:
    _require_locale(locale)
    _require_question_kind(question_kind)
    _governing_feedback_label(feedback_labels)
    items = "".join(
        f'<li class="feedback-item feedback-item--{label}"><span class="feedback-label feedback-label--{label}">{labels[label]}:</span> '
        f'{html.escape(_feedback_description(locale, question_kind, label))}</li>'
        for label in feedback_labels
    )
    return f'''<section class="practice-feedback" role="region" aria-labelledby="feedback-title" aria-describedby="feedback-ephemeral-note">
      <h2 id="feedback-title">{labels["feedback"]}</h2>
      <p class="visually-hidden" id="feedback-ephemeral-note">{labels["ephemeral_note"]}</p>
      <ul>{items}</ul>
    </section>'''


def _render_decision(
    locale: str,
    question_kind: str,
    governing_label: str,
    labels: Mapping[str, str],
) -> str:
    _require_locale(locale)
    _require_question_kind(question_kind)
    _require_feedback_label(governing_label)
    return f'''<section class="practice-decision" aria-labelledby="decision-title">
      <h2 id="decision-title">{labels["decision_heading"]}</h2>
      <p class="practice-decision-explanation">{labels["decision_explanation"]}</p>
      <dl>
        <dt>{labels["decision_governing"]}</dt><dd>{labels[governing_label]}</dd>
        <dt>{labels["decision_target"]}</dt><dd>{html.escape(_decision_target(locale, question_kind))}</dd>
        <dt>{labels["decision_action"]}</dt><dd>{html.escape(_decision_action(locale, governing_label))}</dd>
      </dl>
    </section>'''


def _render_rehearsal_scaffold(
    locale: str, question_kind: str, labels: Mapping[str, str]
) -> str:
    try:
        coaching = REHEARSAL_COPY[locale][question_kind]
    except KeyError as error:
        raise ValueError(
            f"unsupported recruiter practice question kind: {question_kind}"
        ) from error
    steps = coaching["steps"]
    return f'''<section class="practice-rehearsal" aria-labelledby="rehearsal-title">
      <h2 id="rehearsal-title">{labels["rehearsal"]}</h2>
      <p class="practice-rehearsal-hint">{coaching["hint"]}</p>
      <ol>{"".join(f"<li>{step}</li>" for step in steps)}</ol>
    </section>'''


def _render_next_action(
    state: str, labels: Mapping[str, str], *, sourced: bool
) -> str:
    copy_keys = {
        "ready_to_practice": "next_action_sourced_ready" if sourced else "next_action_ready",
        "awaiting_answer": "next_action_sourced_answer" if sourced else "next_action_answer",
    }
    try:
        copy_key = copy_keys[state]
    except KeyError as error:
        raise ValueError(f"unsupported recruiter practice state: {state}") from error
    if sourced:
        described_by = "prompt-title practice-question-text"
    else:
        described_by = "prompt-title rehearsal-title"
    return f'''<section class="practice-next-action practice-next-action--{html.escape(state)}" aria-labelledby="next-action-title" aria-describedby="{described_by}">
      <h2 id="next-action-title">{labels["next_action"]}</h2>
      <p>{labels[copy_key]}</p>
    </section>'''


def _render_main(
    session: Mapping[str, object], ui_locale: str, content_locale: str | None = None,
) -> str:
    locale = ui_locale
    dynamic_lang = "" if content_locale is None else f' lang="{content_locale}"'
    labels = COPY[locale]
    context = _mapping(session["safe_context"])
    requirement = _mapping(session["requirement"])
    question = _mapping(session["question"])
    question_kind = _text(question["kind"])
    fact = _rows(session["facts"])[0]
    rubric = _mapping(session["rubric"])
    state = _text(session["state"])
    readiness = _render_screen_readiness(locale, state, _text(fact["state"]))
    rehearsal = _render_rehearsal_scaffold(locale, question_kind, labels)
    sourced = session.get("handoff_context") is not None
    handoff = ""
    claim_guardrail = ""
    triage_route = ""
    if sourced:
        source = _text(_mapping(session["handoff_context"])["source"])
        text_key = "handoff_text_reply" if source == "private_recruiter_reply_triage" else "handoff_text_dossier"
        source_class = "reply" if source == "private_recruiter_reply_triage" else "dossier"
        handoff = f'''<aside class="practice-handoff practice-handoff--{source_class}" aria-labelledby="practice-handoff-title" aria-describedby="prompt-title practice-question-text"><h2 id="practice-handoff-title">{labels["handoff_title"]}</h2><p>{labels[text_key]}</p></aside>'''
        if source == "private_recruiter_reply_triage":
            _require_safe_triage_prose(context, question, fact)
            claim_guardrail = _render_claim_guardrail(locale, fact)
            triage_route = _render_triage_practice_route(locale)
    if state == "feedback_available":
        feedback_data = _mapping(session["feedback"])
        observations = _rows(feedback_data["observations"])
        feedback_labels = tuple(_text(observation["label"]) for observation in observations)
        governing_label = _governing_feedback_label(feedback_labels)
        feedback = _render_feedback(locale, question_kind, feedback_labels, labels)
        decision = _render_decision(locale, question_kind, governing_label, labels)
        practice_sequence = f"{claim_guardrail}{triage_route}{handoff}{rehearsal}{feedback}{decision}"
    elif sourced:
        next_action = _render_next_action(state, labels, sourced=sourced)
        practice_sequence = f"{claim_guardrail}{triage_route}{handoff}{next_action}{rehearsal}"
    else:
        next_action = _render_next_action(state, labels, sourced=sourced)
        practice_sequence = f"{rehearsal}{next_action}"
    continuity = _continuity_rail(locale)
    return f'''<main id="main-content" class="practice-shell" tabindex="-1">
    <section class="practice-session" aria-labelledby="practice-session-title" aria-describedby="practice-session-state">
      <p id="practice-session-state" class="state-chip state-chip--{html.escape(state)}">{labels[state]}</p>
      <section class="practice-context" aria-labelledby="context-title">
        <h2 id="context-title">{labels["context"]}</h2>
        <p class="practice-summary"{dynamic_lang}>{html.escape(_text(context["summary"]))}</p>
        <p class="practice-label">{labels["focus"]}</p>
        <p class="practice-summary"{dynamic_lang}>{html.escape(_text(requirement["summary"]))}</p>
      </section>
      {readiness}
      <section class="practice-prompt" aria-labelledby="prompt-title">
        <h2 id="prompt-title">{labels["prompt"]}</h2>
        <p class="practice-label">{labels["question_purpose"]}</p>
        <p class="practice-purpose">{labels["purpose_" + _text(question["kind"])]}</p>
        <p id="practice-question-text"{dynamic_lang}>{html.escape(_text(question["text"]))}</p>
      </section>
      {practice_sequence}
      {continuity}
      <section class="practice-evidence" aria-labelledby="evidence-title">
        <h2 id="evidence-title">{labels["evidence"]}</h2>
        <ul><li><strong>{labels[_text(fact["state"])]}:</strong> <span{dynamic_lang}>{html.escape(_text(fact["summary"]))}</span></li></ul>
      </section>
      <aside class="practice-boundary" aria-labelledby="boundary-title">
        <h2 id="boundary-title">{labels["boundary"]}</h2>
        <p>{labels["boundary_text"]} <span{dynamic_lang}>{html.escape(_text(rubric["criterion"]))}</span></p>
      </aside>
    </section>
  </main>
  <footer class="practice-footer practice-shell"><strong>{labels["footer"]}</strong><p class="practice-employment-boundary">{labels["employment_boundary"]}</p></footer>'''


def render_session_html(session: Mapping[str, object]) -> str:
    validated = _validate(session)
    is_v2 = _text(validated["schema_version"]) == VALIDATOR.V2_SCHEMA_VERSION
    locale = _text(validated["ui_locale"] if is_v2 else validated["locale"])
    content_locale = _text(validated["content_locale"]) if is_v2 else None
    template = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, TEMPLATE_PATH)
    static_tokens = STATIC_TEMPLATE_TOKEN.findall(template)
    if sorted(static_tokens) != sorted(TEMPLATE_TOKENS):
        raise RuntimeError("recruiter practice template token contract is invalid")
    substitutions = {
        "{{LANG}}": locale,
        "{{TITLE}}": COPY[locale]["title"],
        "{{INLINE_CSS}}": ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, CSS_PATH),
        "{{HEADER}}": _render_header(locale),
        "{{MAIN}}": _render_main(validated, locale, content_locale),
    }
    return STATIC_TEMPLATE_TOKEN.sub(lambda match: substitutions[match.group(0)], template)


def build_chat_summary(session: Mapping[str, object]) -> str:
    validated = _validate(session)
    locale = _text(
        validated["ui_locale"]
        if _text(validated["schema_version"]) == VALIDATOR.V2_SCHEMA_VERSION
        else validated["locale"]
    )
    labels = COPY[locale]
    question = _mapping(validated["question"])
    return f'{labels["summary"]}{_text(question["text"])} {labels["footer"]}'


def _open_private_parent(parent: Path) -> int:
    if not parent.is_absolute() or parent.anchor != os.sep:
        raise OSError("output parent must be absolute")
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    base_flags = os.O_RDONLY | directory_flag
    descriptor = os.open(os.sep, base_flags)
    try:
        for index, component in enumerate(parent.parts[1:]):
            if component in {"", ".", ".."}:
                raise OSError("output parent is unsafe")
            created = False
            try:
                os.mkdir(component, 0o700, dir_fd=descriptor)
                created = True
            except FileExistsError:
                pass
            candidate = os.path.join(os.sep, component)
            trusted_system_alias = (
                index == 0
                and component in {"tmp", "var"}
                and os.path.islink(candidate)
                and os.path.realpath(candidate) == os.path.join(os.sep, "private", component)
            )
            next_descriptor = os.open(
                component, base_flags | (0 if trusted_system_alias else no_follow), dir_fd=descriptor
            )
            if not stat.S_ISDIR(os.fstat(next_descriptor).st_mode):
                os.close(next_descriptor)
                raise OSError("output parent is not a directory")
            if created:
                os.fchmod(next_descriptor, 0o700)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _atomic_private_write(output: Path, content: bytes, *, force: bool) -> None:
    if not output.name or output.name in {".", ".."}:
        raise OSError("output name is unsafe")
    parent_descriptor = _open_private_parent(output.parent)
    temporary_name: str | None = None
    descriptor: int | None = None
    try:
        try:
            target_status = os.stat(output.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            target_status = None
        if target_status is not None:
            if stat.S_ISLNK(target_status.st_mode):
                raise OSError("output target is a symbolic link")
            if not stat.S_ISREG(target_status.st_mode):
                raise OSError("output target is not a regular file")
            if not force:
                raise FileExistsError("output already exists")
        for _ in range(100):
            candidate = f".{output.name}.tmp-{secrets.token_hex(8)}"
            try:
                descriptor = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent_descriptor,
                )
                temporary_name = candidate
                break
            except FileExistsError:
                continue
        if temporary_name is None or descriptor is None:
            raise OSError("cannot create private temporary artifact")
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            os.fchmod(stream.fileno(), 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if force:
            os.replace(temporary_name, output.name, src_dir_fd=parent_descriptor, dst_dir_fd=parent_descriptor)
            temporary_name = None
        else:
            try:
                os.link(temporary_name, output.name, src_dir_fd=parent_descriptor, dst_dir_fd=parent_descriptor, follow_symlinks=False)
            except FileExistsError as error:
                raise FileExistsError("output already exists") from error
            os.unlink(temporary_name, dir_fd=parent_descriptor)
            temporary_name = None
        os.fsync(parent_descriptor)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=parent_descriptor)
            except FileNotFoundError:
                pass
        os.close(parent_descriptor)


def write_session_html(session_path: Path, output_path: Path, *, force: bool = False) -> RenderReceipt:
    session = VALIDATOR.load_session(Path(session_path))
    validated = _validate(session)
    try:
        expanded_output = Path(output_path).expanduser()
    except RuntimeError as error:
        raise OSError("output path is unavailable") from error
    output = Path(os.path.abspath(os.fspath(expanded_output)))
    rendered = render_session_html(validated)
    _atomic_private_write(output, rendered.encode("utf-8"), force=force)
    return RenderReceipt(
        artifact_path=output,
        artifact_type="text/html",
        locale=_text(
            validated["ui_locale"]
            if _text(validated["schema_version"]) == VALIDATOR.V2_SCHEMA_VERSION
            else validated["locale"]
        ),
        chat_summary=build_chat_summary(validated),
    )


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a private recruiter practice session.")
    parser.add_argument("session", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    try:
        arguments = parser.parse_args(argv)
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    try:
        receipt = write_session_html(arguments.session, arguments.output, force=arguments.force)
    except OSError:
        print("cannot write recruiter practice artifact", file=sys.stderr)
        return 3
    except (VALIDATOR.SessionLoadError, SessionValidationError) as error:
        if isinstance(error, SessionValidationError):
            print("\n".join(error.errors), file=sys.stderr)
        else:
            print(str(error), file=sys.stderr)
        return 2
    print(json.dumps({
        "artifact_path": str(receipt.artifact_path),
        "artifact_type": receipt.artifact_type,
        "locale": receipt.locale,
        "chat_summary": receipt.chat_summary,
    }, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
