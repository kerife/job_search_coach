#!/usr/bin/env python3
"""Render a validated LinkedIn career dossier as private, offline HTML."""

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
from types import MappingProxyType
from typing import Any


ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
TEMPLATE_PATH = ASSET_ROOT / "executive-career-dossier-v1.html"
CSS_PATH = ASSET_ROOT / "executive-career-dossier-v1.css"
TEMPLATE_TOKENS = (
    "{{LANG}}",
    "{{TITLE}}",
    "{{INLINE_CSS}}",
    "{{HEADER}}",
    "{{MAIN}}",
    "{{INLINE_SCRIPT}}",
)
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
SUMMARY_MARKDOWN_ESCAPE = re.compile(r"[\\`*_{}\[\]#!|~]")
SUMMARY_MARKDOWN_PREFIX = re.compile(r"(^|\s)([>+\-])(?=\s)")
SUMMARY_ORDERED_PREFIX = re.compile(r"(^|\s)(\d+)([.)])(?=\s)")


def _load_validator() -> Any:
    path = Path(__file__).with_name("validate_executive_career_dossier.py")
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_executive_dossier_validator", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("dossier validator is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


class DossierValidationError(ValueError):
    """Raised when renderer input does not satisfy the closed dossier contract."""

    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("dossier validation failed")


@dataclass(frozen=True, slots=True)
class RenderReceipt:
    artifact_path: Path
    artifact_type: str
    locale: str
    chat_summary: str


COPY = {
    "es": {
        "title": "Dossier privado de carrera",
        "skip": "Saltar al contenido principal",
        "eyebrow": "Dossier de carrera profesional",
        "report_title": "Análisis estratégico de LinkedIn",
        "private": "Privado · solo lectura",
        "print": "Imprimir / Guardar PDF",
        "verdict": "Veredicto ejecutivo",
        "target": "Objetivo bajo revisión",
        "start": "Empieza aquí",
        "confidence": "Confianza",
        "coverage": "Cobertura evaluada",
        "score": "Calificación global",
        "unscored": "No evaluado",
        "scan": "Lectura en siete segundos",
        "understood": "Se entiende",
        "ambiguity": "Permanece ambiguo",
        "bridge": "Puente de posicionamiento",
        "priorities": "Tres prioridades",
        "problem": "Problema",
        "why": "Por qué importa ahora",
        "action": "Acción privada",
        "done": "Terminado cuando",
        "minutes": "minutos",
        "analytics": "Analítica privada",
        "analytics_impact": "Impacto, calidad y límite",
        "analytics_interpretation": "Límite de interpretación",
        "analytics_window": "Ventana observada",
        "days": "días",
        "observed": "Observación agregada autorizada",
        "profile_views": "Vistas del perfil",
        "inbound": "Contactos entrantes",
        "qualified": "Contactos calificados",
        "qualified_rate": "Tasa calificada",
        "analytics_boundary": "Observación fechada; no atribuye causalidad a cambios del perfil.",
        "analytics_not_requested_interpretation": "No hay una interpretación analítica porque no se solicitó una observación agregada.",
        "analytics_unavailable_interpretation": "No hay una interpretación analítica porque la observación agregada no estuvo disponible.",
        "scorecard": "Diagnóstico por dimensión",
        "visual_review": "Revisión visual",
        "photo": "Foto",
        "banner": "Banner",
        "private_review": "Revisión privada sugerida",
        "market": "Contexto de vacantes y brechas",
        "market_sample": "Muestra fechada",
        "vacancies": "vacantes",
        "market_sources": "Fuentes de la investigación de vacantes",
        "market_caption": "Comparación separada del diagnóstico de LinkedIn",
        "role": "Rol objetivo",
        "required": "Señales requeridas",
        "supported": "Señales sustentadas",
        "gaps": "Por confirmar",
        "market_boundary": "La evidencia de vacantes no modifica la calificación del perfil.",
        "copy_studio": "Estudio de copy",
        "copy": "Borrador privado",
        "why_works": "Por qué funciona",
        "boundary": "Límite del claim",
        "copy_button": "Copiar borrador",
        "copied": "Borrador copiado",
        "copy_failed": "No se pudo copiar; selecciona y copia el texto",
        "copy_confirmation_boundary": "Necesita confirmación; conserva este texto como borrador privado.",
        "hold": "No cambies todavía",
        "screen_bridge": "Puente para una primera conversación",
        "questions": "Preguntas que cambian la recomendación",
        "changes": "Qué cambia con la respuesta",
        "plan": "Plan privado de siete días",
        "day": "Día",
        "details": "Evidencia, metodología y límites",
        "evidence_scope": "Alcance de evidencia",
        "evidence_confidence": "Confianza del alcance",
        "mode": "Modo",
        "captured": "Capturado",
        "inspected": "Secciones revisadas",
        "unavailable_sections": "Secciones no disponibles",
        "visual_evidence": "Evidencia visual",
        "none": "Ninguna",
        "evidence": "Evidencia disponible",
        "methodology": "Fuentes metodológicas oficiales",
        "privacy": "Privacidad y límites",
        "privacy_text": "Este dossier no incluye identidad, contacto, texto crudo del perfil ni analítica privada individual.",
        "action_boundary": "No se realizó ninguna acción en LinkedIn.",
        "employment_boundary": "Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
        "first_action": "Primera acción privada",
        "first_question": "Pregunta clave",
        "not_evaluated": "No evaluado",
        "no_copy": "No se propone copy hasta contar con la confirmación necesaria.",
        "method_label": "Guía oficial de LinkedIn",
    },
    "en": {
        "title": "Private career dossier",
        "skip": "Skip to main content",
        "eyebrow": "Professional career dossier",
        "report_title": "Strategic LinkedIn analysis",
        "private": "Private · read only",
        "print": "Print / Save PDF",
        "verdict": "Executive verdict",
        "target": "Target under review",
        "start": "Start here",
        "confidence": "Confidence",
        "coverage": "Evaluated coverage",
        "score": "Overall score",
        "unscored": "Not evaluated",
        "scan": "Seven-second reading",
        "understood": "Understood",
        "ambiguity": "Still ambiguous",
        "bridge": "Positioning bridge",
        "priorities": "Three priorities",
        "problem": "Problem",
        "why": "Why it matters now",
        "action": "Private action",
        "done": "Done when",
        "minutes": "minutes",
        "analytics": "Private analytics",
        "analytics_impact": "Impact, quality, and boundary",
        "analytics_interpretation": "Interpretation boundary",
        "analytics_window": "Observed window",
        "days": "days",
        "observed": "Authorized aggregate observation",
        "profile_views": "Profile views",
        "inbound": "Inbound contacts",
        "qualified": "Qualified contacts",
        "qualified_rate": "Qualified rate",
        "analytics_boundary": "Dated observation; it does not attribute causality to profile changes.",
        "analytics_not_requested_interpretation": "No analytics interpretation is available because an aggregate observation was not requested.",
        "analytics_unavailable_interpretation": "No analytics interpretation is available because the aggregate observation was unavailable.",
        "scorecard": "Dimension diagnosis",
        "visual_review": "Visual review",
        "photo": "Photo",
        "banner": "Banner",
        "private_review": "Suggested private review",
        "market": "Vacancy context and gaps",
        "market_sample": "Dated sample",
        "vacancies": "vacancies",
        "market_sources": "Vacancy research sources",
        "market_caption": "Comparison kept separate from the LinkedIn diagnosis",
        "role": "Target role",
        "required": "Required signals",
        "supported": "Supported signals",
        "gaps": "Needs confirmation",
        "market_boundary": "Vacancy evidence does not change the profile score.",
        "copy_studio": "Copy studio",
        "copy": "Private draft",
        "why_works": "Why it works",
        "boundary": "Claim boundary",
        "copy_button": "Copy draft",
        "copied": "Draft copied",
        "copy_failed": "Could not copy; select and copy the text",
        "copy_confirmation_boundary": "Needs confirmation; keep this text as a private draft.",
        "hold": "Do not change yet",
        "screen_bridge": "First-conversation bridge",
        "questions": "Questions that change the recommendation",
        "changes": "What the answer changes",
        "plan": "Private seven-day plan",
        "day": "Day",
        "details": "Evidence, methodology, and limits",
        "evidence_scope": "Evidence scope",
        "evidence_confidence": "Evidence-scope confidence",
        "mode": "Mode",
        "captured": "Captured",
        "inspected": "Inspected sections",
        "unavailable_sections": "Unavailable sections",
        "visual_evidence": "Visual evidence",
        "none": "None",
        "evidence": "Available evidence",
        "methodology": "Official methodology sources",
        "privacy": "Privacy and limits",
        "privacy_text": "This dossier includes no identity, contact data, raw profile text, or individual private analytics.",
        "action_boundary": "No LinkedIn action was performed.",
        "employment_boundary": "This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.",
        "first_action": "First private action",
        "first_question": "Key question",
        "not_evaluated": "Not evaluated",
        "no_copy": "No copy is proposed until the required fact is confirmed.",
        "method_label": "Official LinkedIn guidance",
    },
}

DIMENSION_LABELS = {
    "es": {
        "visual": "Identidad visual",
        "headline": "Titular",
        "about": "Acerca de",
        "experience": "Experiencia",
        "skills": "Aptitudes",
        "proof": "Prueba",
        "completeness": "Completitud",
    },
    "en": {
        "visual": "Visual identity",
        "headline": "Headline",
        "about": "About",
        "experience": "Experience",
        "skills": "Skills",
        "proof": "Proof",
        "completeness": "Completeness",
    },
}

COPY_LABELS = {
    "es": {
        "headline": "Titular",
        "about_opening": "Apertura de Acerca de",
        "experience_bullet": "Bullet de experiencia",
    },
    "en": {
        "headline": "Headline",
        "about_opening": "About opening",
        "experience_bullet": "Experience bullet",
    },
}

EVIDENCE_LABELS = {
    "es": {
        "verified": "Observado",
        "candidate_reported": "Reportado por ti",
        "inferred": "Juicio de coaching",
        "unknown": "No disponible",
    },
    "en": {
        "verified": "Observed",
        "candidate_reported": "Reported by you",
        "inferred": "Coaching judgment",
        "unknown": "Unavailable",
    },
}

CONFIDENCE_LABELS = {
    "es": {"low": "baja", "medium": "media", "high": "alta"},
    "en": {"low": "low", "medium": "medium", "high": "high"},
}

ARRANGEMENT_LABELS = {
    "es": {
        "onsite": "presencial",
        "hybrid": "híbrido",
        "remote": "remoto",
        "flexible": "flexible",
    },
    "en": {
        "onsite": "onsite",
        "hybrid": "hybrid",
        "remote": "remote",
        "flexible": "flexible",
    },
}

DECISION_STATE_LABELS = {
    "es": {
        "ready": "Listo para revisión",
        "requires_confirmation": "Necesita confirmación",
        "omit": "No disponible",
    },
    "en": {
        "ready": "Ready for review",
        "requires_confirmation": "Needs confirmation",
        "omit": "Unavailable",
    },
}

SCREEN_PREPARATION_LABELS = {
    "es": {
        "title": "Preparación para la primera conversación",
        "state": {
            "ready": "Enfoque profesional claro",
            "requires_confirmation": "Confirmación pendiente",
            "omit": "Omitir por ahora",
        },
        "paused": "Pausado",
        "evidence": "Evidencia para usar",
        "empty_evidence": "No hay evidencia utilizable para esta conversación todavía.",
        "boundary": "No afirmar todavía",
        "question": "Pregunta para aclarar",
        "handoff_title": "Ensayo privado siguiente",
        "handoff_text": "Practica esta pregunta en privado. Tu respuesta es efímera y no se guarda; no se realizó ninguna acción externa.",
        "manual_title": "Preparación manual",
        "manual_text": "Revisa esta pregunta en el dossier; no se transfiere automáticamente a la práctica privada.",
        "rehearsal": "Ensayo",
        "manual_step": "Siguiente paso manual",
    },
    "en": {
        "title": "First-conversation preparation",
        "state": {
            "ready": "Clear professional focus",
            "requires_confirmation": "Confirmation pending",
            "omit": "Omit for now",
        },
        "paused": "Paused",
        "evidence": "Evidence to use",
        "empty_evidence": "No usable evidence is available for this conversation yet.",
        "boundary": "Do not claim yet",
        "question": "Question to clarify",
        "handoff_title": "Next private rehearsal",
        "handoff_text": "Practice this question privately. Your answer is ephemeral and not saved; no external action was taken.",
        "manual_title": "Manual preparation",
        "manual_text": "Review this question in the dossier; it is not transferred automatically to private practice.",
        "rehearsal": "Rehearsal",
        "manual_step": "Manual next step",
    },
}

ANALYTICS_STATE_LABELS = {
    "es": {
        "not_requested": "No solicitada",
        "unavailable": "No disponible",
        "observed_aggregate": "Observación agregada autorizada",
    },
    "en": {
        "not_requested": "Not requested",
        "unavailable": "Unavailable",
        "observed_aggregate": "Authorized aggregate observation",
    },
}

MARKET_STATE_LABELS = {
    "es": {
        "not_researched": "No investigado",
        "dated_vacancy_evidence": "Evidencia fechada de vacantes",
    },
    "en": {
        "not_researched": "Not researched",
        "dated_vacancy_evidence": "Dated vacancy evidence",
    },
}

INSPECTION_MODE_LABELS = {
    "es": {
        "live_read_only": "Inspección visible de solo lectura",
        "provided_material": "Material proporcionado",
        "mixed": "Evidencia mixta",
    },
    "en": {
        "live_read_only": "Visible read-only inspection",
        "provided_material": "Provided material",
        "mixed": "Mixed evidence",
    },
}

VISUAL_SCOPE_LABELS = {
    "es": {
        "unavailable": "No disponible",
        "structural_only": "Solo estructura",
        "partial_visual": "Evidencia visual parcial",
        "authorized_visual_visible": "Evidencia visual autorizada",
    },
    "en": {
        "unavailable": "Unavailable",
        "structural_only": "Structure only",
        "partial_visual": "Partial visual evidence",
        "authorized_visual_visible": "Authorized visual evidence",
    },
}

SECTION_LABELS = {
    "es": {
        "visual": "Visual",
        "headline": "Titular",
        "about": "Acerca de",
        "experience": "Experiencia",
        "skills": "Aptitudes",
        "proof": "Prueba",
        "completeness": "Completitud",
        "photo": "Foto",
        "banner": "Banner",
    },
    "en": {
        "visual": "Visual",
        "headline": "Headline",
        "about": "About",
        "experience": "Experience",
        "skills": "Skills",
        "proof": "Proof",
        "completeness": "Completeness",
        "photo": "Photo",
        "banner": "Banner",
    },
}

METHOD_LABELS = {
    "es": {
        "ai_hiring_agents": "Agentes de IA en contratación",
        "cover_image": "Imagen de portada",
        "featured_section": "Sección Destacado",
        "good_profile": "Buenas prácticas del perfil",
        "job_match": "Coincidencia con empleos",
        "job_seeker_hirer_connection": "Conexión entre talento y contratación",
        "profile_photo": "Foto de perfil",
        "skills": "Aptitudes",
    },
    "en": {
        "ai_hiring_agents": "AI hiring agents",
        "cover_image": "Cover image",
        "featured_section": "Featured section",
        "good_profile": "Profile best practices",
        "job_match": "Job match",
        "job_seeker_hirer_connection": "Job seeker and hirer connection",
        "profile_photo": "Profile photo",
        "skills": "Skills",
    },
}

INLINE_SCRIPT = """
(() => {
  const printButton = document.querySelector('[data-print]');
  if (printButton) printButton.addEventListener('click', () => window.print());

  const copyFallback = (value) => {
    const area = document.createElement('textarea');
    area.value = value;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    const copied = document.execCommand('copy');
    area.remove();
    return copied;
  };

  document.querySelectorAll('[data-copy-target]').forEach((button) => {
    button.addEventListener('click', async () => {
      const source = document.getElementById(button.dataset.copyTarget);
      if (!source) {
        const status = document.getElementById(button.dataset.copyStatus);
        if (status) status.textContent = button.dataset.copyFailure;
        return;
      }
      const value = source.textContent || '';
      let copied = false;
      try {
        if (navigator.clipboard) {
          await navigator.clipboard.writeText(value);
          copied = true;
        } else {
          copied = copyFallback(value);
        }
      } catch (_) {
        copied = copyFallback(value);
      }
      const status = document.getElementById(button.dataset.copyStatus);
      if (status) status.textContent = copied ? button.dataset.copySuccess : button.dataset.copyFailure;
    });
  });
})();
""".strip()


def text(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("render text requires a validated string")
    return html.escape(value, quote=True)


def _summary_text(value: object, maximum_words: int) -> str:
    if not isinstance(value, str):
        raise TypeError("summary text requires a validated string")
    escaped = html.escape(value, quote=False)
    escaped = SUMMARY_MARKDOWN_ESCAPE.sub(lambda match: "\\" + match.group(0), escaped)
    escaped = SUMMARY_MARKDOWN_PREFIX.sub(
        lambda match: match.group(1) + "\\" + match.group(2), escaped
    )
    escaped = SUMMARY_ORDERED_PREFIX.sub(
        lambda match: match.group(1) + match.group(2) + "\\" + match.group(3),
        escaped,
    )
    words = escaped.split()
    if len(words) <= maximum_words:
        return " ".join(words)
    return " ".join(words[:maximum_words]) + "…"


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError("render value requires a validated object")
    return value


def _rows(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, (list, tuple)):
        raise TypeError("render value requires a validated list")
    return tuple(_mapping(item) for item in value)


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(nested) for key, nested in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(nested) for nested in value)
    return value


def _validate_and_freeze(dossier: Mapping[str, object]) -> Mapping[str, object]:
    errors = VALIDATOR.validate_dossier(dossier)
    if errors:
        raise DossierValidationError(errors)
    frozen = _freeze(dossier)
    return _mapping(frozen)


def _natural_state(locale: str, value: object) -> str:
    return EVIDENCE_LABELS[locale][text(value)]


def _render_header(locale: str) -> str:
    labels = COPY[locale]
    return f"""
  <a class="skip-link" href="#main-content">{labels['skip']}</a>
  <header class="shell utility-header">
    <div>
      <p class="eyebrow">{labels['eyebrow']}</p>
      <h1 class="report-title">{labels['report_title']}</h1>
    </div>
    <div class="utility-actions no-print" role="group" aria-label="{labels['private']}">
      <span class="privacy-chip">{labels['private']}</span>
      <button type="button" data-print>{labels['print']}</button>
    </div>
  </header>"""


def _render_verdict(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    verdict = _mapping(dossier["verdict"])
    focus = _mapping(dossier["focus"])
    coverage = _mapping(dossier["coverage"])
    score = coverage["overall_score"]
    score_markup = (
        f'<span class="score-value">{score}/100</span>'
        if type(score) is int
        else f'<span class="score-note">{labels["not_evaluated"]}</span>'
    )
    return f"""
    <section class="card verdict-card span-8" aria-labelledby="verdict-title">
      <div>
        <p class="section-kicker">{_natural_state(locale, verdict['evidence_state'])}</p>
        <h2 id="verdict-title">{labels['verdict']}</h2>
        <p class="focus-statement">{text(focus['statement'])}</p>
        <p class="verdict-statement">{text(verdict['statement'])}</p>
        <p>{text(verdict['rationale'])}</p>
      </div>
      <div>
        <div class="start-here"><strong>{labels['start']}</strong>{text(verdict['start_here_action'])}</div>
        <div class="coverage-row">
          <span class="confidence-chip">{labels['confidence']}: {CONFIDENCE_LABELS[locale][text(coverage['confidence'])]}</span>
          <span>{labels['coverage']}: <strong>{coverage['scored_weight']}%</strong></span>
          <span>{labels['score']}: {score_markup}</span>
        </div>
      </div>
    </section>"""


def _render_recruiter_scan(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    scan = _mapping(dossier["recruiter_scan"])
    fields = (
        ("understood_signal", labels["understood"]),
        ("ambiguity", labels["ambiguity"]),
        ("positioning_bridge", labels["bridge"]),
    )
    items = []
    for field, label in fields:
        row = _mapping(scan[field])
        items.append(
            f'<li><span class="label">{label} · {_natural_state(locale, row["evidence_state"])}</span>'
            f'{text(row["statement"])}</li>'
        )
    return f"""
    <aside class="card span-4" aria-labelledby="scan-title">
      <h2 id="scan-title">{labels['scan']}</h2>
      <ul class="scan-list">{''.join(items)}</ul>
    </aside>"""


def _render_priorities(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    cards = []
    for priority in _rows(dossier["priorities"]):
        heading_id = f"priority-title-{priority['rank']}"
        cards.append(f"""
      <article class="card span-4" data-priority-card="true" aria-labelledby="{heading_id}">
        <div class="priority-header"><h3 id="{heading_id}">{text(priority['title'])}</h3><span class="priority-rank">{priority['rank']}</span></div>
        <p class="status-label">{_natural_state(locale, priority['evidence_state'])}</p>
        <dl class="priority-body">
          <dt>{labels['problem']}</dt><dd>{text(priority['problem'])}</dd>
          <dt>{labels['why']}</dt><dd>{text(priority['why_now'])}</dd>
          <dt>{labels['action']}</dt><dd>{text(priority['action'])}</dd>
          <dt>{labels['done']}</dt><dd>{text(priority['done_when'])}</dd>
        </dl>
        <span class="timebox">{priority['timebox_minutes']} {labels['minutes']}</span>
      </article>""")
    return f"""
    <section class="section-block" aria-labelledby="priorities-title">
      <h2 id="priorities-title">{labels['priorities']}</h2>
      <div class="dossier-grid priorities-grid">{''.join(cards)}</div>
    </section>"""


def _render_analytics(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    analytics = _mapping(dossier["analytics"])
    state_label = ANALYTICS_STATE_LABELS[locale][text(analytics["state"])]
    if analytics["state"] != "observed_aggregate":
        status_body = f'<p class="status-label">{state_label}</p><p>{text(analytics["reason"])}</p>'
        interpretation_key = (
            "analytics_not_requested_interpretation"
            if analytics["state"] == "not_requested"
            else "analytics_unavailable_interpretation"
        )
        impact_body = (
            f'<p class="status-label">{labels["analytics_interpretation"]}</p>'
            f'<p class="boundary">{labels[interpretation_key]}</p>'
        )
    else:
        status_body = f"""
        <p class="status-label">{state_label} · {text(analytics['observed_as_of'])}</p>
        <p>{labels['analytics_window']}: {analytics['window_days']} {labels['days']}</p>
        <div class="metric-row"><span>{labels['profile_views']}</span><strong class="metric-value">{analytics['profile_views']}</strong></div>"""
        impact_body = f"""
        <div class="metric-row"><span>{labels['inbound']}</span><strong class="metric-value">{analytics['inbound_contacts']}</strong></div>
        <div class="metric-row"><span>{labels['qualified']}</span><strong class="metric-value">{analytics['qualified_contacts']}</strong></div>
        <div class="metric-row"><span>{labels['qualified_rate']}</span><strong class="metric-value">{analytics['qualified_contact_rate']}%</strong></div>
        <p class="boundary">{labels['analytics_boundary']}</p>"""
    return f"""
    <section class="card analytics-card analytics-status-card span-6" aria-labelledby="analytics-status-title">
      <h2 id="analytics-status-title">{labels['analytics']}</h2>{status_body}
    </section>
    <section class="card analytics-card analytics-impact-card span-6" aria-labelledby="analytics-impact-title">
      <h2 id="analytics-impact-title">{labels['analytics_impact']}</h2>{impact_body}
    </section>"""


def _render_dimensions(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    cards = []
    for dimension in _rows(dossier["dimensions"]):
        evaluated = dimension["state"] == "evaluated"
        score = dimension["score"]
        dimension_key = text(dimension["dimension"])
        heading_id = f"dimension-title-{dimension_key}"
        score_markup = (
            f'<div class="score-line"><span class="score-value">{score}/100</span>'
            f'<span class="state-chip">{_natural_state(locale, dimension["evidence_state"])}</span></div>'
            f'<progress value="{score}" max="100" aria-labelledby="{heading_id}">{score}/100</progress>'
            if evaluated
            else f'<span class="state-chip">{labels["not_evaluated"]}</span>'
        )
        extra_class = "" if evaluated else " not-evaluated"
        cards.append(f"""
      <article class="card dimension-card{extra_class}" data-dimension-card="true" aria-labelledby="{heading_id}">
        <h3 id="{heading_id}">{DIMENSION_LABELS[locale][dimension_key]}</h3>
        {score_markup}
        <p>{text(dimension['reason'])}</p>
      </article>""")
    return f"""
    <section class="section-block" aria-labelledby="scorecard-title">
      <h2 id="scorecard-title">{labels['scorecard']}</h2>
      <div class="dossier-grid dimension-grid">{''.join(cards)}</div>
    </section>"""


def _render_visual_review(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    review = _mapping(dossier["visual_review"])
    cards = []
    for key in ("photo", "banner"):
        item = _mapping(review[key])
        heading_id = f"visual-title-{key}"
        private_action = (
            f'<p><span class="label">{labels["private_review"]}</span>{text(item["private_action"])}</p>'
            if item["private_action"] is not None
            else ""
        )
        cards.append(f"""
      <article class="card visual-card span-6" aria-labelledby="{heading_id}">
        <p class="status-label">{_natural_state(locale, item['evidence_state'])}</p>
        <h3 id="{heading_id}">{labels[key]}</h3>
        <p>{text(item['finding'])}</p>{private_action}
      </article>""")
    return f"""
    <section class="section-block" aria-labelledby="visual-title">
      <h2 id="visual-title">{labels['visual_review']}</h2>
      <div class="dossier-grid">{''.join(cards)}</div>
    </section>"""


def _join_values(values: object) -> str:
    if not isinstance(values, tuple):
        raise TypeError("render value requires a validated list")
    return ", ".join(text(value) for value in values)


def _render_market_context(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    market = _mapping(dossier["market_context"])
    state_label = MARKET_STATE_LABELS[locale][text(market["state"])]
    if market["state"] != "dated_vacancy_evidence":
        body = f'<p class="status-label">{state_label}</p><p>{text(market["reason"])}</p>'
    else:
        rows = []
        for role in _rows(market["target_roles"]):
            rows.append(f"""
          <tr>
            <th scope="row">{text(role['title'])}</th>
            <td>{_join_values(role['required_signals'])}</td>
            <td>{_join_values(role['supported_signals'])}</td>
            <td>{_join_values(role['gaps'])}</td>
          </tr>""")
        source_items = "".join(
            f'<li><a href="{text(source["url"])}" rel="noreferrer">{text(source["document_title"])}</a> — {text(source["publisher"])}</li>'
            for source in _rows(market["public_sources"])
        )
        body = f"""
        <p class="status-label">{state_label}</p>
        <p>{text(market['geography'])} · {ARRANGEMENT_LABELS[locale][text(market['arrangement'])]} · {text(market['research_date'])}</p>
        <p>{labels['market_sample']}: {market['vacancy_sample_count']} {labels['vacancies']}</p>
        <table class="comparison-table">
          <caption>{labels['market_caption']}</caption>
          <thead><tr><th scope="col">{labels['role']}</th><th scope="col">{labels['required']}</th><th scope="col">{labels['supported']}</th><th scope="col">{labels['gaps']}</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
        <h3>{labels['market_sources']}</h3><ul class="method-list">{source_items}</ul>
        <p class="boundary">{labels['market_boundary']}</p>"""
    return f"""
    <section class="card market-card span-12" aria-labelledby="market-title">
      <h2 id="market-title">{labels['market']}</h2>{body}
    </section>"""


def _render_copy_blocks(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    cards = []
    for index, block in enumerate(_rows(dossier["copy_blocks"]), start=1):
        source_id = f"copy-source-{index}"
        status_id = f"{source_id}-status"
        confirmation_id = f"{source_id}-confirmation"
        confirmation = (
            f'<span class="copy-boundary no-print" id="{confirmation_id}">{labels["copy_confirmation_boundary"]}</span>'
            if block["state"] == "requires_confirmation"
            else ""
        )
        described_by = f"{status_id} {confirmation_id}" if confirmation else status_id
        heading_id = f"copy-title-{index}"
        accessible_copy_label = (
            f"{labels['copy_button']}: "
            f"{COPY_LABELS[locale][text(block['category'])]}"
        )
        draft = (
            f'<p class="copy-text" id="{source_id}" data-copy-source>{text(block["copy"])}</p>'
            f'<button class="no-print" type="button" data-copy-target="{source_id}" '
            f'data-copy-status="{status_id}" aria-label="{accessible_copy_label}" '
            f'aria-describedby="{described_by}" '
            f'data-copy-success="{labels["copied"]}" data-copy-failure="{labels["copy_failed"]}">{labels["copy_button"]}</button>'
            f'<span class="copy-status no-print" id="{status_id}" role="status" aria-live="polite" aria-atomic="true"></span>{confirmation}'
            if block["copy"] is not None
            else f'<p class="copy-text">{labels["no_copy"]}</p>'
        )
        cards.append(f"""
      <article class="card copy-card span-4" aria-labelledby="{heading_id}">
        <div class="copy-heading"><h3 id="{heading_id}">{COPY_LABELS[locale][text(block['category'])]}</h3><span class="state-chip">{DECISION_STATE_LABELS[locale][text(block['state'])]}</span></div>
        {draft}
        <p><span class="label">{labels['why_works']}</span>{text(block['why_it_works'])}</p>
        <p class="boundary"><span class="label">{labels['boundary']}</span>{text(block['claim_boundary'])}</p>
      </article>""")
    return f"""
    <section class="section-block" aria-labelledby="copy-title">
      <h2 id="copy-title">{labels['copy_studio']}</h2>
      <div class="dossier-grid">{''.join(cards)}</div>
    </section>"""


def _render_holds(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    holds = _rows(dossier["do_not_change"])
    if not holds:
        return ""
    items = "".join(
        f'<li><span class="label">{_natural_state(locale, hold["evidence_state"])}</span>{text(hold["reason"])}</li>'
        for hold in holds
    )
    return f"""
    <section class="card hold-card span-5" aria-labelledby="hold-title">
      <h2 id="hold-title">{labels['hold']}</h2><ul class="clean-list">{items}</ul>
    </section>"""


def _linked_evidence_points(
    dossier: Mapping[str, object], bridge: Mapping[str, object], locale: str, limit: int
) -> tuple[str, ...]:
    claim_by_id = {row["id"]: row for row in _rows(dossier["claims"])}
    evidence_by_id = {row["id"]: row for row in _rows(dossier["evidence"])}
    points: list[str] = []
    for identifier in tuple(bridge["claim_ids"]) + tuple(bridge["evidence_ids"]):
        row = claim_by_id.get(identifier) or evidence_by_id.get(identifier)
        if row is None or row["state"] == "unknown":
            continue
        points.append(f"{_natural_state(locale, row['state'])}: {text(row['paraphrase'])}")
        if len(points) == limit:
            break
    return tuple(points)


def _ranked_bridge_question(dossier: Mapping[str, object], rank: object) -> str | None:
    for question in _rows(dossier["questions"]):
        if question["rank"] == rank and question["linked_copy_category"] == "screen_bridge":
            return text(question["question"])
    return None


def _rehearsal_step(dossier: Mapping[str, object], locale: str) -> str:
    first_step = _rows(dossier["seven_day_plan"])[0]
    return f"{text(SCREEN_PREPARATION_LABELS[locale]['rehearsal'])}: {text(first_step['action'])}"


def _screen_bridge_view(dossier: Mapping[str, object], locale: str) -> Mapping[str, object]:
    bridge = _mapping(dossier["screen_bridge"])
    state = bridge["state"]
    labels = SCREEN_PREPARATION_LABELS[locale]
    safe_state = state if state in {"ready", "requires_confirmation", "omit"} else "paused"
    return {
        "state_label": text(labels["state"].get(safe_state, labels["paused"])),
        "state_tone": safe_state,
        "opener": text(bridge["copy"]) if state != "omit" else None,
        "evidence_points": _linked_evidence_points(dossier, bridge, locale, limit=3),
        "boundary": text(bridge["claim_boundary"]),
        "question": _ranked_bridge_question(dossier, bridge["question_rank"]),
        "question_rank": bridge["question_rank"],
        "rehearsal_label": _rehearsal_step(dossier, locale),
        "manual_step_label": f"{text(labels['manual_step'])}: {text(_rows(dossier['seven_day_plan'])[0]['action'])}",
    }


def _render_screen_bridge(dossier: Mapping[str, object], locale: str) -> str:
    labels = SCREEN_PREPARATION_LABELS[locale]
    view = _screen_bridge_view(dossier, locale)
    opener = (
        f'<span class="label">{COPY[locale]["copy"]}</span><p class="copy-text">{view["opener"]}</p>'
        if view["opener"]
        else ""
    )
    evidence = "".join(f"<li>{point}</li>" for point in view["evidence_points"])
    evidence_content = (
        f'<ul class="clean-list">{evidence}</ul>'
        if evidence
        else f'<p class="screen-preparation-evidence-empty" role="status">{text(labels["empty_evidence"])}</p>'
    )
    question = (
        f'<section class="screen-preparation-question" aria-labelledby="screen-preparation-question-title">'
        f'<h3 id="screen-preparation-question-title">{text(labels["question"])}</h3>'
        f'<p id="screen-preparation-question-text">{view["question"]}</p></section>'
        if view["question"]
        else ""
    )
    handoff = (
        f'<aside class="screen-preparation-handoff" aria-labelledby="screen-preparation-handoff-title" aria-describedby="screen-preparation-question-title screen-preparation-question-text">'
        f'<h3 id="screen-preparation-handoff-title">{text(labels["handoff_title"])}</h3>'
        f'<p>{text(labels["handoff_text"])}</p></aside>'
        if view["question"] and view["question_rank"] == 1
        else ""
    )
    manual_note = (
        f'<aside class="screen-preparation-manual-note" aria-labelledby="screen-preparation-manual-title" aria-describedby="screen-preparation-question-title screen-preparation-question-text">'
        f'<h3 id="screen-preparation-manual-title">{text(labels["manual_title"])}</h3>'
        f'<p>{text(labels["manual_text"])}</p></aside>'
        if view["question"] and view["question_rank"] != 1
        else ""
    )
    return f"""
    <section class="card screen-preparation-card span-7" aria-labelledby="screen-preparation-title">
      <p class="readiness-chip screen-preparation-state screen-preparation-state--{view['state_tone'].replace('_', '-')}">{view['state_label']}</p>
      <h2 id="screen-preparation-title">{text(labels['title'])}</h2>
      {opener}
      <section class="screen-preparation-evidence" aria-labelledby="screen-preparation-evidence-title"><h3 id="screen-preparation-evidence-title">{text(labels['evidence'])}</h3>{evidence_content}</section>
      <p class="boundary screen-preparation-boundary"><span class="label">{text(labels['boundary'])}</span>{view['boundary']}</p>
      {question}
      {handoff}
      {manual_note}
      <p class="screen-preparation-rehearsal"><span class="label">{(view['manual_step_label'] if view['question_rank'] in (2, 3) else view['rehearsal_label']).split(':', 1)[0]}</span>{(view['manual_step_label'] if view['question_rank'] in (2, 3) else view['rehearsal_label']).split(':', 1)[1].lstrip()}</p>
    </section>"""


def _render_questions(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    questions = _rows(dossier["questions"])
    if not questions:
        return ""
    cards = []
    for question in questions:
        question_title_id = f"question-title-{question['rank']}"
        cards.append(f"""
      <article class="card question-card span-4" aria-labelledby="{question_title_id}">
        <span class="priority-rank">{question['rank']}</span>
        <h3 id="{question_title_id}">{text(question['question'])}</h3>
        <p><span class="label">{labels['changes']}</span>{text(question['changes'])}</p>
      </article>""")
    return f"""
    <section class="section-block" aria-labelledby="questions-title">
      <h2 id="questions-title">{labels['questions']}</h2>
      <div class="dossier-grid">{''.join(cards)}</div>
    </section>"""


def _render_plan(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    items = []
    for item in _rows(dossier["seven_day_plan"]):
        items.append(f"""
      <li class="plan-day">
        <span class="day-badge">{labels['day']} {item['day']}</span>
        <div><strong>{text(item['action'])}</strong><br><span class="boundary">{labels['done']}: {text(item['done_when'])}</span></div>
      </li>""")
    return f"""
    <section class="card span-12" aria-labelledby="plan-title">
      <h2 id="plan-title">{labels['plan']}</h2><ol class="plan-list">{''.join(items)}</ol>
    </section>"""


def _render_details(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    scope = _mapping(dossier["evidence_scope"])
    inspected = ", ".join(
        SECTION_LABELS[locale][text(section)] for section in scope["inspected_sections"]
    )
    unavailable = ", ".join(
        SECTION_LABELS[locale][text(section)] for section in scope["unavailable_sections"]
    ) or labels["none"]
    evidence_items = "".join(
        f'<li><span class="label">{_natural_state(locale, row["state"])}</span>{text(row["paraphrase"])}</li>'
        for row in _rows(dossier["evidence"])
    )
    sources = VALIDATOR.LINKEDIN_SAFETY.resolve_methodology_sources(
        dossier["methodology_source_categories"]
    )
    source_items = "".join(
        f'<li><a href="{text(source["url"])}" rel="noreferrer">{METHOD_LABELS[locale][text(source["source_category"])]} — {labels["method_label"]}</a></li>'
        for source in sources
    )
    return f"""
    <section class="card span-12" aria-labelledby="details-title">
      <h2 id="details-title">{labels['details']}</h2>
      <details>
        <summary>{labels['evidence_scope']}</summary>
        <p>{labels['mode']}: {INSPECTION_MODE_LABELS[locale][text(scope['inspection_mode'])]}</p>
        <p>{labels['captured']}: {text(scope['captured_as_of'])}</p>
        <p>{labels['evidence_confidence']}: {CONFIDENCE_LABELS[locale][text(scope['confidence'])]}</p>
        <p>{labels['inspected']}: {inspected}</p>
        <p>{labels['unavailable_sections']}: {unavailable}</p>
        <p>{labels['visual_evidence']}: {VISUAL_SCOPE_LABELS[locale][text(scope['visual_state'])]}</p>
      </details>
      <details>
        <summary>{labels['evidence']}</summary><ul class="clean-list">{evidence_items}</ul>
      </details>
      <details>
        <summary>{labels['methodology']}</summary><ul class="method-list">{source_items}</ul>
      </details>
      <details>
        <summary>{labels['privacy']}</summary><p>{labels['privacy_text']}</p><p><strong>{labels['action_boundary']}</strong></p>
      </details>
    </section>"""


def _render_main(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    opening = _render_verdict(dossier, locale) + _render_recruiter_scan(dossier, locale)
    bridge_holds = _render_holds(dossier, locale) + _render_screen_bridge(dossier, locale)
    return f"""
  <main id="main-content" class="shell" tabindex="-1">
    <div class="dossier-grid">{opening}</div>
    {_render_priorities(dossier, locale)}
    <div class="dossier-grid section-block">{_render_analytics(dossier, locale)}</div>
    {_render_dimensions(dossier, locale)}
    {_render_visual_review(dossier, locale)}
    <div class="dossier-grid section-block">{_render_market_context(dossier, locale)}</div>
    {_render_copy_blocks(dossier, locale)}
    <div class="dossier-grid section-block">{bridge_holds}</div>
    {_render_questions(dossier, locale)}
    <div class="dossier-grid section-block">{_render_plan(dossier, locale)}{_render_details(dossier, locale)}</div>
  </main>
  <footer class="shell footer"><strong>{labels['action_boundary']}</strong> <span class="employment-boundary">{labels['employment_boundary']}</span></footer>"""


def build_chat_summary(dossier: Mapping[str, object]) -> str:
    frozen = _validate_and_freeze(dossier)
    locale = text(frozen["locale"])
    labels = COPY[locale]
    verdict = _mapping(frozen["verdict"])
    first_priority = _rows(frozen["priorities"])[0]
    parts = [
        _summary_text(verdict["statement"], 60),
        f"{labels['first_action']}: {_summary_text(first_priority['action'], 55)}",
    ]
    questions = _rows(frozen["questions"])
    if questions:
        parts.append(
            f"{labels['first_question']}: "
            f"{_summary_text(questions[0]['question'], 45)}"
        )
    parts.append(labels["action_boundary"])
    summary = "\n\n".join(parts)
    if len(summary.split()) > 180:
        raise RuntimeError("chat summary budget is invalid")
    return summary


def render_dossier_html(dossier: Mapping[str, object]) -> str:
    frozen = _validate_and_freeze(dossier)
    locale = text(frozen["locale"])
    template = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, TEMPLATE_PATH)
    css = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, CSS_PATH)
    static_tokens = STATIC_TEMPLATE_TOKEN.findall(template)
    if sorted(static_tokens) != sorted(TEMPLATE_TOKENS):
        raise RuntimeError("dossier template token contract is invalid")
    substitutions = {
        "{{LANG}}": locale,
        "{{TITLE}}": COPY[locale]["title"],
        "{{INLINE_CSS}}": css,
        "{{HEADER}}": _render_header(locale),
        "{{MAIN}}": _render_main(frozen, locale),
        "{{INLINE_SCRIPT}}": INLINE_SCRIPT,
    }
    return STATIC_TEMPLATE_TOKEN.sub(
        lambda match: substitutions[match.group(0)],
        template,
    )


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
                and os.path.realpath(candidate)
                == os.path.join(os.sep, "private", component)
            )
            flags = base_flags | (0 if trusted_system_alias else no_follow)
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
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
            target_status = os.stat(
                output.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
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
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_NOFOLLOW", 0),
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
            os.replace(
                temporary_name,
                output.name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
            )
            temporary_name = None
        else:
            try:
                os.link(
                    temporary_name,
                    output.name,
                    src_dir_fd=parent_descriptor,
                    dst_dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
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


def write_dossier_html(
    dossier_path: Path,
    output_path: Path,
    *,
    force: bool = False,
) -> RenderReceipt:
    dossier = VALIDATOR.load_dossier(Path(dossier_path))
    errors = VALIDATOR.validate_dossier(dossier)
    if errors:
        raise DossierValidationError(errors)
    try:
        expanded_output = Path(output_path).expanduser()
    except RuntimeError as error:
        raise OSError("output path is unavailable") from error
    output = Path(os.path.abspath(os.fspath(expanded_output)))
    rendered = render_dossier_html(dossier)
    summary = build_chat_summary(dossier)
    _atomic_private_write(output, rendered.encode("utf-8"), force=force)
    return RenderReceipt(
        artifact_path=output,
        artifact_type="text/html",
        locale=text(dossier["locale"]),
        chat_summary=summary,
    )


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a private career dossier.")
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        receipt = write_dossier_html(
            arguments.dossier,
            arguments.output,
            force=arguments.force,
        )
    except OSError:
        print("cannot write dossier artifact", file=sys.stderr)
        return 3
    except (VALIDATOR.DossierLoadError, DossierValidationError) as error:
        if isinstance(error, DossierValidationError):
            print("\n".join(error.errors), file=sys.stderr)
        else:
            print(str(error), file=sys.stderr)
        return 2
    payload = {
        "artifact_path": str(receipt.artifact_path),
        "artifact_type": receipt.artifact_type,
        "locale": receipt.locale,
        "chat_summary": receipt.chat_summary,
    }
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
