#!/usr/bin/env python3
"""Render a validated private recruiter reply triage as offline HTML."""

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
TEMPLATE_PATH = ASSET_ROOT / "private-recruiter-reply-triage-v1.html"
CSS_PATH = ASSET_ROOT / "private-recruiter-reply-triage-v1.css"
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
    path = Path(__file__).with_name("validate_private_recruiter_reply_triage.py")
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_private_recruiter_triage_validator", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("private recruiter triage validator is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


class TriageValidationError(ValueError):
    """Raised when renderer input does not satisfy the closed triage contract."""

    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("private recruiter triage validation failed")


@dataclass(frozen=True, slots=True)
class RenderReceipt:
    artifact_path: Path
    artifact_type: str
    locale: str
    chat_summary: str


COPY = {
    "es": {
        "title": "Decisión privada de respuesta de reclutador",
        "skip": "Saltar al contenido principal",
        "kicker": "Triage privado",
        "heading": "Decisión ante una respuesta resumida",
        "classification": "Clasificación",
        "decision": "Decisión",
        "next_safe_action": "Siguiente paso seguro",
        "next_safe_action_clarify_context_before_private_prep": "Aclara el contexto del filtro inicial antes de la preparación privada.",
        "next_safe_action_manual_reenter_private_prep": "Vuelve a entrar manualmente a la preparación privada.",
        "next_safe_action_record_stop_decision": "Registra en privado el resultado de este proceso; no continúes por esta vía de preparación.",
        "stop_scope": "Alcance: esto solo registra un resultado de este proceso de reclutamiento. No es una recomendación de renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
        "clarify_gate": "Puerta de traspaso",
        "clarify_gate_candidate_reported": "Falta un hecho confirmado antes de la preparación privada.",
        "clarify_gate_missing_context": "Falta confirmar el contexto mínimo del filtro inicial.",
        "clarify_gate_generic": "Falta una aclaración mínima antes de la preparación privada.",
        "known": "Qué sabemos",
        "missing": "Falta confirmar",
        "blocked": "No afirmar",
        "handoff": "Traspaso local",
        "handoff_preview": "Vista previa para preparación",
        "answer_path_title": "Ruta para construir tu respuesta",
        "answer_path_screen_opening_1": "Contexto: nombra el alcance que sí está confirmado.",
        "answer_path_screen_opening_2": "Acción: describe lo que hiciste, sin ampliar el alcance.",
        "answer_path_screen_opening_3": "Resultado observado: separa el efecto comprobado de lo que aún falta confirmar.",
        "answer_path_proof_example_1": "Contexto: ubica el ejemplo en el trabajo o problema confirmado.",
        "answer_path_proof_example_2": "Acción: explica tu contribución específica.",
        "answer_path_proof_example_3": "Resultado observado: menciona la señal comprobable y su límite.",
        "answer_path_eligibility_boundary_1": "Límite conocido: indica sólo la condición confirmada.",
        "answer_path_eligibility_boundary_2": "Confirmación faltante: señala qué parte sigue abierta.",
        "answer_path_eligibility_boundary_3": "Pregunta: formula una aclaración concreta antes de afirmar elegibilidad.",
        "answer_path_compensation_boundary_1": "Límite conocido: indica sólo el proceso o rango confirmado.",
        "answer_path_compensation_boundary_2": "Confirmación faltante: separa la cifra o condición que no conoces.",
        "answer_path_compensation_boundary_3": "Pregunta: pide el contexto mínimo sin inventar una expectativa.",
        "answer_path_missing_detail_1": "Hecho conocido: empieza con la evidencia suministrada.",
        "answer_path_missing_detail_2": "Brecha exacta: nombra el detalle que impide avanzar.",
        "answer_path_missing_detail_3": "Aclaración: formula una sola pregunta para completar esa brecha.",
        "receipt": "Recibo de entradas",
        "receipt_bring": "Traer",
        "receipt_role_summary": "Resumen del rol/respuesta sin identidad",
        "receipt_verified_fact": "Un hecho confirmado",
        "receipt_do_not_bring": "No traer",
        "receipt_raw_reply": "Texto o identidad sin resumir del reclutador",
        "receipt_contact_calendar": "Detalles de calendario o contacto",
        "receipt_manual_boundary": "La práctica comienza solo después del reingreso manual.",
        "verified_fact": "Hecho confirmado",
        "identity_free_context": "Contexto sin identidad",
        "question_type": "Tipo de pregunta",
        "question_type_screen_opening": "Apertura de filtro",
        "question_type_proof_example": "Ejemplo de evidencia",
        "question_type_eligibility_boundary": "Límite de elegibilidad",
        "question_type_compensation_boundary": "Límite de compensación",
        "question_type_missing_detail": "Detalle faltante",
        "safe_question": "Pregunta segura",
        "packet_prep_scope": "Alcance de preparación",
        "question_purpose": "Propósito de la pregunta",
        "purpose_screen_invite": "Abre la preparación",
        "purpose_request_for_proof": "Selecciona un ejemplo confirmado",
        "purpose_eligibility_question": "Aclara el límite de elegibilidad",
        "purpose_compensation_question": "Aclara el límite de compensación",
        "purpose_unknown": "Encuentra el detalle mínimo que falta",
        "clarify_first": "Aclarar primero",
        "ready_for_private_prep": "Lista para preparación privada",
        "stop": "Detener este proceso de reclutamiento",
        "screen_invite": "Invitación a filtro inicial",
        "request_for_proof": "Solicitud de evidencia",
        "eligibility_question": "Pregunta de elegibilidad",
        "compensation_question": "Pregunta de compensación",
        "decline": "Declinación",
        "unknown": "Sin clasificar",
        "verified": "Confirmado",
        "candidate_reported": "Reportado por la persona",
        "handoff_text": "Disponible solo para preparación privada local; no realiza contacto, envío ni agenda.",
        "handoff_scope": "Alcance: una pregunta de filtro inicial.",
        "handoff_reentry": "Vuelve a entrar manualmente a preparación; no se inicia automáticamente.",
        "readiness": "Condiciones de preparación",
        "readiness_stage": "Etapa",
        "readiness_stage_value": "Filtro inicial",
        "readiness_role": "Contexto del rol",
        "readiness_role_value": "Confirmado",
        "readiness_constraints": "Restricciones críticas",
        "readiness_constraints_value": "Confirmadas",
        "focus": "Enfoque de preparación",
        "focus_screen_invite": "Practica una apertura concisa",
        "focus_request_for_proof": "Elige un ejemplo confirmado",
        "focus_eligibility_question": "Prepara la pregunta límite de elegibilidad",
        "focus_compensation_question": "Prepara la pregunta límite de compensación",
        "focus_decline": "Detener este proceso de reclutamiento: no hay traspaso a preparación privada",
        "focus_unknown": "Aclara el detalle mínimo que falta",
        "next_step": "Siguiente paso manual",
        "next_step_text": "Vuelve a entrar manualmente a preparación privada y responde la única pregunta segura.",
        "reentry_scope": "Alcance de reingreso",
        "reentry_manual": "Reingreso manual requerido; la preparación permanece sin respuesta.",
        "footer": "No se realizó ninguna acción externa.",
        "employment_boundary": "Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
        "save_disabled": (
            "Este flujo no conserva la respuesta de origen. "
            "Este artefacto HTML privado solo se guarda en la ruta que solicitaste."
        ),
        "sequence_conditions": "01 Condiciones",
        "sequence_focus": "02 Enfoque",
        "sequence_reentry": "03 Reingreso manual",
        "summary": "Triage privado: ",
    },
    "en": {
        "title": "Private recruiter reply decision",
        "skip": "Skip to main content",
        "kicker": "Private triage",
        "heading": "Decision for a summarized reply",
        "classification": "Classification",
        "decision": "Decision",
        "next_safe_action": "Next safe step",
        "next_safe_action_clarify_context_before_private_prep": "Clarify recruiter-screen context before private preparation.",
        "next_safe_action_manual_reenter_private_prep": "Re-enter private preparation manually.",
        "next_safe_action_record_stop_decision": "Record this recruiter-process outcome privately; do not continue this preparation path.",
        "stop_scope": "Scope: this records one recruiter-process outcome only. It is not advice to resign, leave a job, or stop your job search; you decide what comes next.",
        "clarify_gate": "Handoff gate",
        "clarify_gate_candidate_reported": "One verified fact is still needed before private preparation.",
        "clarify_gate_missing_context": "The minimum recruiter-screen context is still unconfirmed.",
        "clarify_gate_generic": "One small clarification is still needed before private preparation.",
        "known": "What we know",
        "missing": "Confirm next",
        "blocked": "Do not assert",
        "handoff": "Local handoff",
        "handoff_preview": "Preparation preview",
        "answer_path_title": "Answer path",
        "answer_path_screen_opening_1": "Context: name the scope that is confirmed.",
        "answer_path_screen_opening_2": "Action: describe what you did without widening the scope.",
        "answer_path_screen_opening_3": "Observed result: separate the checked effect from what remains unconfirmed.",
        "answer_path_proof_example_1": "Context: place the example in the confirmed work or problem.",
        "answer_path_proof_example_2": "Action: explain your specific contribution.",
        "answer_path_proof_example_3": "Observed result: name the observable signal and its boundary.",
        "answer_path_eligibility_boundary_1": "Known boundary: state only the condition that is confirmed.",
        "answer_path_eligibility_boundary_2": "Missing confirmation: separate what is still open.",
        "answer_path_eligibility_boundary_3": "Question: ask one concrete clarification before asserting eligibility.",
        "answer_path_compensation_boundary_1": "Known boundary: state only the confirmed process or range.",
        "answer_path_compensation_boundary_2": "Missing confirmation: separate the figure or condition you do not know.",
        "answer_path_compensation_boundary_3": "Question: ask for the minimum context without inventing an expectation.",
        "answer_path_missing_detail_1": "Known fact: start with the supplied evidence.",
        "answer_path_missing_detail_2": "Exact gap: name the detail that blocks progress.",
        "answer_path_missing_detail_3": "Clarification: ask one question to close that gap.",
        "receipt": "Input receipt",
        "receipt_bring": "Bring",
        "receipt_role_summary": "Identity-free role/reply summary",
        "receipt_verified_fact": "One verified fact",
        "receipt_do_not_bring": "Do not bring",
        "receipt_raw_reply": "Raw recruiter text or identity",
        "receipt_contact_calendar": "Calendar or contact details",
        "receipt_manual_boundary": "Practice starts only after manual re-entry.",
        "verified_fact": "Verified fact",
        "identity_free_context": "Identity-free context",
        "question_type": "Question type",
        "question_type_screen_opening": "Screen opening",
        "question_type_proof_example": "Proof example",
        "question_type_eligibility_boundary": "Eligibility boundary",
        "question_type_compensation_boundary": "Compensation boundary",
        "question_type_missing_detail": "Missing detail",
        "safe_question": "Safe question",
        "packet_prep_scope": "Preparation scope",
        "question_purpose": "Question purpose",
        "purpose_screen_invite": "Opens readiness",
        "purpose_request_for_proof": "Selects one verified example",
        "purpose_eligibility_question": "Clarifies the eligibility boundary",
        "purpose_compensation_question": "Clarifies the compensation boundary",
        "purpose_unknown": "Finds the smallest missing detail",
        "clarify_first": "Clarify first",
        "ready_for_private_prep": "Ready for private preparation",
        "stop": "Stop this recruiter process",
        "screen_invite": "Initial screen invitation",
        "request_for_proof": "Proof request",
        "eligibility_question": "Eligibility question",
        "compensation_question": "Compensation question",
        "decline": "Decline",
        "unknown": "Unclassified",
        "verified": "Verified",
        "candidate_reported": "Candidate-reported",
        "handoff_text": "Available only for local private preparation; it does not contact, send, or schedule.",
        "handoff_scope": "One recruiter-screen question.",
        "handoff_reentry": "Re-enter preparation manually; preparation does not begin automatically.",
        "readiness": "Preparation conditions",
        "readiness_stage": "Stage",
        "readiness_stage_value": "Recruiter screen",
        "readiness_role": "Role context",
        "readiness_role_value": "Confirmed",
        "readiness_constraints": "Critical constraints",
        "readiness_constraints_value": "Confirmed",
        "focus": "Preparation focus",
        "focus_screen_invite": "Practice a concise opening",
        "focus_request_for_proof": "Choose one verified example",
        "focus_eligibility_question": "Prepare the eligibility boundary question",
        "focus_compensation_question": "Prepare the compensation boundary question",
        "focus_decline": "Stop this recruiter process: no private preparation handoff",
        "focus_unknown": "Clarify the smallest missing detail",
        "next_step": "Manual next step",
        "next_step_text": "Re-enter private preparation manually and answer the one safe question.",
        "reentry_scope": "Re-entry scope",
        "reentry_manual": "Manual re-entry is required; preparation remains unanswered.",
        "footer": "No external action was taken.",
        "employment_boundary": "This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.",
        "save_disabled": (
            "Source reply is not retained by this flow. "
            "This private HTML artifact is saved only at the path you requested."
        ),
        "sequence_conditions": "01 Conditions",
        "sequence_focus": "02 Focus",
        "sequence_reentry": "03 Manual re-entry",
        "summary": "Private triage: ",
    },
}


CLASSIFICATION_FOCUS_KEYS = {
    "screen_invite": "focus_screen_invite",
    "request_for_proof": "focus_request_for_proof",
    "eligibility_question": "focus_eligibility_question",
    "compensation_question": "focus_compensation_question",
    "decline": "focus_decline",
    "unknown": "focus_unknown",
}

CLASSIFICATION_PURPOSE_KEYS = {
    "screen_invite": "purpose_screen_invite",
    "request_for_proof": "purpose_request_for_proof",
    "eligibility_question": "purpose_eligibility_question",
    "compensation_question": "purpose_compensation_question",
    "unknown": "purpose_unknown",
}

QUESTION_TYPE_LABEL_KEYS = {
    "screen_opening": "question_type_screen_opening",
    "proof_example": "question_type_proof_example",
    "eligibility_boundary": "question_type_eligibility_boundary",
    "compensation_boundary": "question_type_compensation_boundary",
    "missing_detail": "question_type_missing_detail",
}

PREP_SCOPE_LABEL_KEYS = {
    "screen_opening": "question_type_screen_opening",
    "proof_example": "question_type_proof_example",
    "eligibility_boundary": "question_type_eligibility_boundary",
    "compensation_boundary": "question_type_compensation_boundary",
    "missing_detail": "question_type_missing_detail",
}

ANSWER_PATH_FAMILY_KEYS = {
    "screen_opening": "screen_opening",
    "proof_example": "proof_example",
    "eligibility_boundary": "eligibility_boundary",
    "compensation_boundary": "compensation_boundary",
    "missing_detail": "missing_detail",
}

NEXT_SAFE_ACTION_LABEL_KEYS = {
    "clarify_context_before_private_prep": "next_safe_action_clarify_context_before_private_prep",
    "manual_reenter_private_prep": "next_safe_action_manual_reenter_private_prep",
    "record_stop_decision": "next_safe_action_record_stop_decision",
}


def _clarify_gate_copy_key(triage: Mapping[str, object]) -> str:
    """Return a fixed gate reason without rendering user-supplied blocker prose."""
    fact = _rows(triage["facts"])[0]
    if _text(fact["state"]) == "candidate_reported":
        return "clarify_gate_candidate_reported"
    context = _mapping(triage["safe_context"])
    if any(context[field] == "missing" for field in ("stage", "role_context", "critical_constraints")):
        return "clarify_gate_missing_context"
    return "clarify_gate_generic"


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeError("validated triage has invalid mapping")
    return value


def _rows(value: object) -> Sequence[Mapping[str, object]]:
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        raise RuntimeError("validated triage has invalid rows")
    return value


def _texts(value: object) -> Sequence[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RuntimeError("validated triage has invalid text rows")
    return value


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise RuntimeError("validated triage has invalid text")
    return value


def _validate(triage: Mapping[str, object]) -> Mapping[str, object]:
    errors = VALIDATOR.validate_triage(triage)
    if errors:
        raise TriageValidationError(errors)
    return triage


def _render_header(locale: str) -> str:
    labels = COPY[locale]
    return f'''<a class="skip-link" href="#main-content">{labels["skip"]}</a>
  <header class="triage-header triage-shell">
    <p class="triage-kicker">{labels["kicker"]}</p>
    <h1 id="triage-title">{labels["heading"]}</h1>
  </header>'''


def _render_main(
    triage: Mapping[str, object], locale: str, content_locale: str | None = None
) -> str:
    labels = COPY[locale]
    dynamic_lang = "" if content_locale is None else f' lang="{content_locale}"'
    context = _mapping(triage["safe_context"])
    fact = _rows(triage["facts"])[0]
    state = _text(triage["state"])
    classification = _text(triage["classification"])
    next_safe_action = _text(triage["next_safe_action"])
    question = _mapping(triage["question"])
    handoff_data = _mapping(triage.get("handoff", {}))
    reentry_packet: Mapping[str, object] = {}
    blocked = _texts(triage["blocked_claims"])
    blocked_items = "".join(f"<li{dynamic_lang}>{html.escape(_text(item))}</li>" for item in blocked)
    handoff = ""
    if triage["handoff_allowed"]:
        # The validator has already bound this closed packet to the canonical
        # context, fact, question, and scope.  Render only its enum scope;
        # identifiers and packet prose remain internal.
        reentry_packet = _mapping(handoff_data["reentry_packet"])
        answer_path_family = ANSWER_PATH_FAMILY_KEYS[_text(question["kind"])]
        answer_path = f'''<section class="triage-handoff-answer-path" aria-labelledby="handoff-answer-path-title">
              <h3 id="handoff-answer-path-title">{labels["answer_path_title"]}</h3>
              <ol>
                <li>{labels[f"answer_path_{answer_path_family}_1"]}</li>
                <li>{labels[f"answer_path_{answer_path_family}_2"]}</li>
                <li>{labels[f"answer_path_{answer_path_family}_3"]}</li>
              </ol>
            </section>'''
        handoff = f'''<aside class="triage-section triage-handoff" aria-labelledby="handoff-title" aria-describedby="handoff-description">
        <h2 id="handoff-title">{labels["handoff"]}</h2>
        <p>{labels["handoff_text"]}</p>
        <p id="handoff-description">{labels["handoff_scope"]} {labels["handoff_reentry"]}</p>
        <ol class="triage-handoff-sequence" aria-label="{labels["handoff"]}">
          <li><span class="triage-handoff-step-label">{labels["sequence_conditions"]}</span>
            <section class="triage-handoff-readiness" aria-labelledby="handoff-readiness-title">
              <h3 id="handoff-readiness-title">{labels["readiness"]}</h3>
              <dl>
                <div class="triage-handoff-readiness-row"><dt>{labels["readiness_stage"]}</dt><dd>{labels["readiness_stage_value"]}</dd></div>
                <div class="triage-handoff-readiness-row"><dt>{labels["readiness_role"]}</dt><dd>{labels["readiness_role_value"]}</dd></div>
                <div class="triage-handoff-readiness-row"><dt>{labels["readiness_constraints"]}</dt><dd>{labels["readiness_constraints_value"]}</dd></div>
              </dl>
            </section>
          </li>
          <li><span class="triage-handoff-step-label">{labels["sequence_focus"]}</span>
            <section class="triage-handoff-focus" aria-labelledby="handoff-focus-title">
              <h3 id="handoff-focus-title">{labels["focus"]}</h3>
              <p>{labels[CLASSIFICATION_FOCUS_KEYS[classification]]}</p>
            </section>
          </li>
          <li><span class="triage-handoff-step-label">{labels["sequence_reentry"]}</span>
            <section class="triage-handoff-next-step" aria-labelledby="handoff-next-step-title">
              <h3 id="handoff-next-step-title">{labels["next_step"]}</h3>
              <p>{labels["next_step_text"]}</p>
              <p class="triage-handoff-reentry-cue"><strong>{labels["reentry_scope"]}:</strong> {labels[PREP_SCOPE_LABEL_KEYS[_text(reentry_packet["prep_scope"])] ]} {labels["reentry_manual"]}</p>
            </section>
            <section class="triage-handoff-preview" aria-labelledby="handoff-preview-title">
              <h3 id="handoff-preview-title">{labels["handoff_preview"]}</h3>
              <dl>
                <dt>{labels["identity_free_context"]}</dt>
                <dd{dynamic_lang}>{html.escape(_text(context["summary"]))}</dd>
                <dt>{labels["verified_fact"]}</dt>
                <dd{dynamic_lang}>{html.escape(_text(fact["summary"]))}</dd>
                <dt>{labels["question_type"]}</dt>
                <dd>{labels[QUESTION_TYPE_LABEL_KEYS[_text(question["kind"])]]}</dd>
                <dt>{labels["question_purpose"]}</dt>
                <dd>{labels[CLASSIFICATION_PURPOSE_KEYS[classification]]}</dd>
                <dt>{labels["safe_question"]}</dt>
                <dd{dynamic_lang}>{html.escape(_text(question["text"]))}</dd>
                <dt>{labels["packet_prep_scope"]}</dt>
                <dd>{labels[PREP_SCOPE_LABEL_KEYS[_text(reentry_packet["prep_scope"])] ]}</dd>
              </dl>
            </section>
            {answer_path}
            <section class="triage-handoff-receipt" aria-labelledby="handoff-receipt-title">
              <h3 id="handoff-receipt-title">{labels["receipt"]}</h3>
              <div class="triage-handoff-receipt-group" aria-labelledby="receipt-bring-title">
                <h4 id="receipt-bring-title">{labels["receipt_bring"]}</h4>
                <ul class="triage-handoff-receipt-list" aria-labelledby="receipt-bring-title">
                  <li>{labels["receipt_role_summary"]}</li>
                  <li>{labels["receipt_verified_fact"]}</li>
                </ul>
              </div>
              <div class="triage-handoff-receipt-group" aria-labelledby="receipt-do-not-bring-title">
                <h4 id="receipt-do-not-bring-title">{labels["receipt_do_not_bring"]}</h4>
                <ul class="triage-handoff-receipt-list" aria-labelledby="receipt-do-not-bring-title">
                  <li>{labels["receipt_raw_reply"]}</li>
                  <li>{labels["receipt_contact_calendar"]}</li>
                </ul>
              </div>
              <p>{labels["receipt_manual_boundary"]}</p>
            </section>
          </li>
        </ol>
      </aside>'''
    clarify_gate = ""
    if state == "clarify_first":
        clarify_gate = f'''<section class="triage-section triage-clarify-gate" aria-labelledby="clarify-gate-title">
        <h2 id="clarify-gate-title">{labels["clarify_gate"]}</h2>
        <p>{labels[_clarify_gate_copy_key(triage)]}</p>
      </section>'''
    blocked_section = f'''<section class="triage-section triage-blocked" aria-labelledby="blocked-title">
        <h2 id="blocked-title">{labels["blocked"]}</h2>
        <ul>{blocked_items}</ul>
      </section>'''
    question_section = ""
    if state == "clarify_first":
        question_section = f'''<section class="triage-section triage-missing" aria-labelledby="missing-title">
        <h2 id="missing-title">{labels["missing"]}</h2>
        <p{dynamic_lang}>{html.escape(_text(question["text"]))}</p>
      </section>'''
    employment_boundary = "" if state == "stop" else f'<p class="triage-employment-boundary">{labels["employment_boundary"]}</p>'
    return f'''<main id="main-content" class="triage-shell" tabindex="-1">
    <section class="triage-card" aria-labelledby="triage-title">
      <p class="triage-state triage-state--{html.escape(state)}">{labels[state]}</p>
      <section class="triage-section" aria-labelledby="classification-title">
        <h2 id="classification-title">{labels["classification"]}</h2>
        <p>{html.escape(labels[classification])}</p>
      </section>
      <section class="triage-section triage-decision" aria-labelledby="decision-title">
        <h2 id="decision-title">{labels["decision"]}</h2>
        <p>{html.escape(labels[state])}</p>
      </section>
      <section class="triage-section triage-next-safe-action" aria-labelledby="next-safe-action-title">
        <h2 id="next-safe-action-title">{labels["next_safe_action"]}</h2>
        <p>{labels[NEXT_SAFE_ACTION_LABEL_KEYS[next_safe_action]]}</p>
        {f'<p class="triage-stop-scope">{labels["stop_scope"]}</p>' if state == "stop" else ""}
      </section>
      {blocked_section}
      {clarify_gate}
      {handoff}
      <section class="triage-section" aria-labelledby="known-title">
        <h2 id="known-title">{labels["known"]}</h2>
        <p{dynamic_lang}>{html.escape(_text(context["summary"]))}</p>
        <p><strong>{labels[_text(fact["state"])]}:</strong> <span{dynamic_lang}>{html.escape(_text(fact["summary"]))}</span></p>
      </section>
      {question_section}
    </section>
  </main>
  <footer class="triage-footer triage-shell"><strong>{labels["footer"]}</strong>{employment_boundary}<p>{labels["save_disabled"]}</p></footer>'''


def render_triage_html(triage: Mapping[str, object]) -> str:
    """Return a deterministic, standalone decision card from validated triage."""

    validated = _validate(triage)
    is_v2 = _text(validated["schema_version"]) == VALIDATOR.V2_SCHEMA_VERSION
    locale = _text(validated["ui_locale"] if is_v2 else validated["locale"])
    content_locale = _text(validated["content_locale"]) if is_v2 else None
    template = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, TEMPLATE_PATH)
    static_tokens = STATIC_TEMPLATE_TOKEN.findall(template)
    if sorted(static_tokens) != sorted(TEMPLATE_TOKENS):
        raise RuntimeError("private recruiter triage template token contract is invalid")
    substitutions = {
        "{{LANG}}": locale,
        "{{TITLE}}": COPY[locale]["title"],
        "{{INLINE_CSS}}": ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, CSS_PATH),
        "{{HEADER}}": _render_header(locale),
        "{{MAIN}}": _render_main(validated, locale, content_locale),
    }
    return STATIC_TEMPLATE_TOKEN.sub(lambda match: substitutions[match.group(0)], template)


def build_chat_summary(triage: Mapping[str, object]) -> str:
    validated = _validate(triage)
    locale = _text(
        validated["ui_locale"]
        if _text(validated["schema_version"]) == VALIDATOR.V2_SCHEMA_VERSION
        else validated["locale"]
    )
    labels = COPY[locale]
    return f'{labels["summary"]}{labels[_text(validated["state"])]}. {labels["footer"]}'


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


def write_triage_html(triage_path: Path, output_path: Path, *, force: bool = False) -> RenderReceipt:
    triage = VALIDATOR.load_triage(Path(triage_path))
    validated = _validate(triage)
    try:
        expanded_output = Path(output_path).expanduser()
    except RuntimeError as error:
        raise OSError("output path is unavailable") from error
    output = Path(os.path.abspath(os.fspath(expanded_output)))
    rendered = render_triage_html(validated)
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
    parser = argparse.ArgumentParser(description="Render a private recruiter reply triage decision card.")
    parser.add_argument("triage", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--include-artifact-path", action="store_true", help="include the local output path in the CLI receipt")
    try:
        arguments = parser.parse_args(argv)
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    try:
        receipt = write_triage_html(arguments.triage, arguments.output, force=arguments.force)
    except OSError:
        print("cannot write private recruiter triage artifact", file=sys.stderr)
        return 3
    except VALIDATOR.TriageLoadError:
        print("cannot load private recruiter triage input", file=sys.stderr)
        return 3
    except TriageValidationError as error:
        print("\n".join(error.errors), file=sys.stderr)
        return 2
    payload = {
        "artifact_type": receipt.artifact_type,
        "locale": receipt.locale,
        "chat_summary": receipt.chat_summary,
    }
    if arguments.include_artifact_path:
        payload["artifact_path"] = str(receipt.artifact_path)
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
