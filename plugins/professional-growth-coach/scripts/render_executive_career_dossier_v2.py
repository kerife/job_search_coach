#!/usr/bin/env python3
"""Render the private LinkedIn coaching dossier v2 by composing v1 surfaces."""

from __future__ import annotations

import argparse
import copy
import html
import importlib.util
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_v2_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("required dossier module is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


VALIDATOR = _sibling("validate_executive_career_dossier_v2.py")
COMPAT = _sibling("executive_career_dossier_v2_compat.py")
BASE = _sibling("render_executive_career_dossier.py")
MARKET = _sibling("validate_career_market_learning_dossier.py")
MARKET_V2 = _sibling("validate_career_market_learning_dossier_v2.py")
SNAPSHOTS = _sibling("dossier_snapshot.py")

ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
TEMPLATE_PATH = ASSET_ROOT / "executive-career-dossier-v1.html"
BASE_CSS_PATH = ASSET_ROOT / "executive-career-dossier-v1.css"
CSS_PATH = ASSET_ROOT / "executive-career-dossier-v2.css"
MARKET_CSS_PATH = ASSET_ROOT / "career-market-learning-dossier-v1.css"

DossierValidationError = BASE.DossierValidationError
RenderReceipt = BASE.RenderReceipt


READING_PATH_SCRIPT = """
(() => {
  const navigation = document.querySelector('.reading-path');
  if (!navigation) return;
  const links = [...navigation.querySelectorAll('a[href^="#"]')];
  const targets = links.map((link) => document.getElementById(link.hash.slice(1))).filter(Boolean);
  if (!links.length || !targets.length) return;
  const setActive = (id) => links.forEach((link) => {
    const active = link.hash.slice(1) === id;
    if (active) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
    link.classList.toggle('reading-path-active', active);
  });
  setActive(targets[0].id);
  if (!('IntersectionObserver' in window)) return;
  const visible = new Set();
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) visible.add(entry.target.id);
      else visible.delete(entry.target.id);
    });
    const active = targets.find((target) => visible.has(target.id)) || targets[0];
    setActive(active.id);
  }, { rootMargin: '-20% 0px -65% 0px', threshold: [0, 1] });
  targets.forEach((target) => observer.observe(target));
})();
""".strip()


class _ArgumentError(ValueError):
    pass


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise _ArgumentError


SECTION_LABELS = {
    "es": {
        "photo": "Foto", "banner": "Banner", "name": "Nombre",
        "profile_url": "URL del perfil", "headline": "Titular", "location": "Ubicación",
        "contact_info": "Información de contacto", "about": "Acerca de",
        "experience": "Experiencia", "skills": "Aptitudes", "featured": "Destacado",
        "certifications": "Certificaciones", "education": "Educación",
        "recommendations": "Recomendaciones", "activity": "Actividad",
        "analytics": "Analítica", "job_preferences": "Preferencias de empleo",
    },
    "en": {
        "photo": "Photo", "banner": "Banner", "name": "Name",
        "profile_url": "Profile URL", "headline": "Headline", "location": "Location",
        "contact_info": "Contact information", "about": "About", "experience": "Experience",
        "skills": "Skills", "featured": "Featured", "certifications": "Certifications",
        "education": "Education", "recommendations": "Recommendations", "activity": "Activity",
        "analytics": "Analytics", "job_preferences": "Job preferences",
    },
}

AVAILABILITY_LABELS = {
    "es": {
        "inspected_present": "Revisada y presente", "inspected_absent": "Revisada y ausente",
        "candidate_supplied": "Material proporcionado", "unavailable": "No disponible",
    },
    "en": {
        "inspected_present": "Inspected and present", "inspected_absent": "Inspected and absent",
        "candidate_supplied": "Candidate-supplied material", "unavailable": "Unavailable",
    },
}

REASON_LABELS = {
    "es": {
        "inspected_content_available": "Contenido revisado disponible",
        "inspected_section_absent": "La sección revisada está ausente",
        "candidate_material_supplied": "Material proporcionado para revisión",
        "authorization_required": "Autorización requerida",
        "inspection_declined": "Inspección declinada para esta sesión",
        "authorized_inspection_failed": "No se pudo completar la inspección autorizada",
    },
    "en": {
        "inspected_content_available": "Inspected content available",
        "inspected_section_absent": "Inspected section is absent",
        "candidate_material_supplied": "Material supplied for review",
        "authorization_required": "Authorization required",
        "inspection_declined": "Inspection declined for this session",
        "authorized_inspection_failed": "Authorized inspection could not be completed",
    },
}

REQUEST_DECISION_LABELS = {
    "es": {
        "pending_response": "Respuesta pendiente", "declined_for_session": "Declinada para esta sesión",
        "authorized_inspection_failed": "Inspección no completada",
    },
    "en": {
        "pending_response": "Response pending", "declined_for_session": "Declined for this session",
        "authorized_inspection_failed": "Inspection not completed",
    },
}

TEMPLATE_LABELS = {
    "es": {
        "context_action_result_v1": "Contexto, acción y resultado",
        "positioning_evidence_v1": "Posicionamiento y evidencia",
        "proof_scope_result_v1": "Prueba, alcance y resultado",
    },
    "en": {
        "context_action_result_v1": "Context, action, and result",
        "positioning_evidence_v1": "Positioning and evidence",
        "proof_scope_result_v1": "Proof, scope, and result",
    },
}

TEMPLATE_FIELD_LABELS = {
    "es": {
        "target_role": "Rol objetivo", "specialty": "Especialidad", "context": "Contexto",
        "action": "Acción", "scope": "Alcance", "result": "Resultado", "metric": "Métrica",
        "evidence_source": "Fuente de evidencia",
    },
    "en": {
        "target_role": "Target role", "specialty": "Specialty", "context": "Context",
        "action": "Action", "scope": "Scope", "result": "Result", "metric": "Metric",
        "evidence_source": "Evidence source",
    },
}

AUTHORIZATION_QUESTIONS = {
    locale: {
        section: (
            f"¿Autorizas inspeccionar en modo solo lectura la sección {label} durante esta sesión?"
            if locale == "es"
            else f"Do you authorize read-only inspection of the {label} section during this session?"
        )
        for section, label in labels.items()
    }
    for locale, labels in SECTION_LABELS.items()
}

COPY = {
    "es": {
        "coverage_title": "Cobertura de secciones",
        "reading_path_aria": "Ruta de lectura",
        "reading_path_title": "Ruta de lectura",
        "reading_path_items": (("section-coverage", "Cobertura"), ("coach-priorities", "Prioridades"), ("market-evidence", "Mercado"), ("screen-preparation", "Preparar conversación")),
        "availability": "Disponibilidad", "reason": "Motivo", "request": "Decisión de inspección",
        "priorities": "Prioridades de coaching", "target": "Sección objetivo",
        "observation": "Observación", "why": "Por qué importa", "prompt": "Pregunta de coaching",
        "template": "Plantilla privada", "market_title": "Evidencia de mercado no disponible",
        "market_body": "Este dossier no incluye evidencia de mercado. Continúa con la evidencia del perfil ya revisada.",
        "market_next_title": "Siguiente investigación",
        "market_next_scope": "Alcance",
        "market_next_scope_value": "SRE, Platform Engineering y DevOps en México o remoto declarado",
        "market_next_sample": "Muestra objetivo",
        "market_next_sample_value": "Cinco vacantes de empleadores distintos",
        "market_next_sources": "Fuentes prioritarias",
        "market_next_sources_value": "Sitio oficial del empleador y ATS operado por el empleador",
        "market_next_date": "Fecha",
        "market_next_date_value": "Registrar la fecha de acceso de cada publicación",
        "market_next_boundary": "Solo lectura: no aplicar, contactar, seguir, publicar ni inferir elegibilidad.",
        "market_summary": "Muestra de vacantes revisada",
        "market_alignment": "Alineación documentada",
        "market_location": "Ubicación",
        "market_arrangement": "Arreglo",
        "market_source_kind": "Tipo de fuente",
        "market_source": "Ver fuente pública",
        "market_researched": "Fecha de investigación",
        "market_eligibility_boundary": "La elegibilidad y la autorización laboral no se infieren.",
        "market_evidence_coverage": "Cobertura de evidencia",
        "market_qualitative_band": "Banda cualitativa",
        "market_directional_legend": "La evidencia es direccional y no representa ajuste de contratación.",
        "market_evidence": "Evidencia del perfil",
        "market_recurrence": "Recurrencia en esta muestra",
        "market_matrix": "Matriz de requisitos y evidencia",
        "market_key": "Clave de vacantes",
        "market_boundary": "La recurrencia describe únicamente esta muestra; no predice contratación ni demanda amplia.",
        "market_route": "Ruta para cerrar brechas",
        "market_route_steps": ("Confirmar la brecha", "Elegir una prueba", "Practicar el ejemplo", "Revisar la evidencia"),
        "market_limited": "Limitación de la muestra",
        "market_synthetic": "Fixture sintético: no es evidencia del mercado actual.",
        "learning_title": "Ruta de aprendizaje",
        "learning_coach": "Decisión de coaching",
        "learning_decisions": "Decisiones priorizadas",
        "learning_decision_label": "Decisión",
        "learning_frequency": "Frecuencia de la muestra",
        "learning_option_type": "Tipo de opción",
        "learning_provenance": "Contexto de procedencia",
        "learning_provider": "Proveedor",
        "learning_option": "Opción",
        "learning_source_title": "Título de la fuente",
        "learning_source_date": "Fecha de la fuente",
        "learning_geography": "Geografía",
        "learning_role": "Rol",
        "learning_seniority": "Senioridad",
        "learning_unknowns": "Desconocidos",
        "learning_decision_basis": "Base de decisión",
        "learning_opportunity_cost": "Costo de oportunidad",
        "learning_provider_synthetic": "Proveedor sintético: no es evidencia actual de disponibilidad, precio ni certificación.",
        "learning_proof": "Prueba necesaria",
        "learning_cost": "Costo actual",
        "learning_currency": "Moneda",
        "learning_tax": "Impuestos",
        "learning_duration": "Duración",
        "learning_availability": "Disponibilidad",
        "learning_sprint": "Sprint privado de prueba",
        "learning_reuse": "Posibles reutilizaciones",
        "learning_boundary": "Estas decisiones son una hipótesis acotada; no autorizan compras, inscripción, publicación ni acciones externas.",
    },
    "en": {
        "coverage_title": "Section coverage", "availability": "Availability", "reason": "Reason",
        "reading_path_aria": "Reading path",
        "reading_path_title": "Reading path",
        "reading_path_items": (("section-coverage", "Coverage"), ("coach-priorities", "Priorities"), ("market-evidence", "Market"), ("screen-preparation", "Prepare conversation")),
        "request": "Inspection decision", "priorities": "Coaching priorities",
        "target": "Target section", "observation": "Observation", "why": "Why it matters",
        "prompt": "Coaching prompt", "template": "Private template",
        "market_title": "Market evidence unavailable",
        "market_body": "This dossier includes no market evidence. Continue with the profile evidence already reviewed.",
        "market_next_title": "Next research",
        "market_next_scope": "Scope",
        "market_next_scope_value": "SRE, Platform Engineering, and DevOps in Mexico or declared remote scope",
        "market_next_sample": "Target sample",
        "market_next_sample_value": "Five vacancies from distinct employers",
        "market_next_sources": "Priority sources",
        "market_next_sources_value": "Employer official site and employer-operated ATS",
        "market_next_date": "Date",
        "market_next_date_value": "Record the access date for each posting",
        "market_next_boundary": "Read-only: do not apply, contact, follow, publish, or infer eligibility.",
        "market_summary": "Reviewed vacancy sample",
        "market_alignment": "Documented alignment",
        "market_location": "Location",
        "market_arrangement": "Arrangement",
        "market_source_kind": "Source type",
        "market_source": "View public source",
        "market_researched": "Research date",
        "market_eligibility_boundary": "Eligibility and work authorization are not inferred.",
        "market_evidence_coverage": "Evidence coverage",
        "market_qualitative_band": "Qualitative band",
        "market_directional_legend": "Evidence is directional and does not represent hiring fit.",
        "market_evidence": "Profile evidence",
        "market_recurrence": "Recurrence in this sample",
        "market_matrix": "Requirements and evidence matrix",
        "market_key": "Vacancy key",
        "market_boundary": "Recurrence describes this sample only; it does not predict hiring or broad market demand.",
        "market_route": "Gap-closure route",
        "market_route_steps": ("Confirm the gap", "Choose evidence", "Practice the example", "Review the evidence"),
        "market_limited": "Sample limitation",
        "market_synthetic": "Synthetic fixture: not current-market evidence.",
        "learning_title": "Learning route",
        "learning_coach": "Coaching decision",
        "learning_decisions": "Ranked decisions",
        "learning_decision_label": "Decision",
        "learning_frequency": "Sample frequency",
        "learning_option_type": "Option type",
        "learning_provenance": "Provenance context",
        "learning_provider": "Provider",
        "learning_option": "Option",
        "learning_source_title": "Source title",
        "learning_source_date": "Source date",
        "learning_geography": "Geography",
        "learning_role": "Role",
        "learning_seniority": "Seniority",
        "learning_unknowns": "Unknowns",
        "learning_decision_basis": "Decision basis",
        "learning_opportunity_cost": "Opportunity cost",
        "learning_provider_synthetic": "Synthetic provider: not current evidence of availability, price, or certification.",
        "learning_proof": "Proof needed",
        "learning_cost": "Current cost",
        "learning_currency": "Currency",
        "learning_tax": "Tax",
        "learning_duration": "Duration",
        "learning_availability": "Availability",
        "learning_sprint": "Private proof sprint",
        "learning_reuse": "Possible reuses",
        "learning_boundary": "These decisions are a bounded hypothesis; they do not authorize purchase, enrollment, publication, or external action.",
    },
}

MATRIX_STATE_COPY = {
    "verified_match": ("✓", "Evidencia directa", "Direct evidence"),
    "candidate_reported_match": ("●", "Reportado por cliente", "Candidate reported"),
    "adjacent_evidence": ("≈", "Evidencia adyacente", "Adjacent evidence"),
    "explicit_gap": ("!", "Brecha confirmada", "Confirmed gap"),
    "unknown": ("?", "No verificado", "Not verified"),
    "not_required": ("—", "No solicitado", "Not requested"),
}

QUALITATIVE_BAND_COPY = {
    "higher_documented_alignment": ("Mayor alineación documentada", "Higher documented alignment"),
    "moderate_documented_alignment": ("Alineación documentada moderada", "Moderate documented alignment"),
    "lower_documented_alignment": ("Menor alineación documentada", "Lower documented alignment"),
    "insufficient_evidence": ("Evidencia insuficiente", "Insufficient evidence"),
}

ARRANGEMENT_COPY = {
    "remote": ("remoto", "remote"),
    "hybrid": ("híbrido", "hybrid"),
    "onsite": ("presencial", "on-site"),
    "unknown": ("No verificado", "Not verified"),
    "not_applicable": ("No aplica", "Not applicable"),
}

SOURCE_KIND_COPY = {
    "official_employer": ("Empleador oficial", "Official employer"),
    "employer_operated_ats": ("ATS operado por empleador", "Employer-operated ATS"),
    "linkedin_jobs_backup": ("LinkedIn Jobs (respaldo)", "LinkedIn Jobs backup"),
}


def _validate_and_freeze(dossier: Mapping[str, object]) -> Mapping[str, object]:
    errors = VALIDATOR.validate_dossier(dossier)
    if errors:
        raise DossierValidationError(errors)
    return BASE._mapping(BASE._freeze(dossier))


def _validate_and_freeze_market(
    dossier: Mapping[str, object], market_dossier: Mapping[str, object],
) -> Mapping[str, object]:
    """Accept only a market artifact bound to this exact executive dossier."""
    version = market_dossier.get("schema_version")
    validator = MARKET_V2.validate_learning_dossier if version == MARKET_V2.SCHEMA_VERSION else MARKET.validate_market_dossier
    errors = validator(market_dossier)
    if errors:
        raise DossierValidationError(errors)
    if market_dossier.get("locale") != dossier.get("locale"):
        raise DossierValidationError(["market dossier locale does not match dossier"])
    if market_dossier.get("as_of_date") != dossier.get("evidence_as_of"):
        raise DossierValidationError(["market dossier date does not match dossier"])
    snapshot = SNAPSHOTS.snapshot_for_dossier(_plain(dossier))
    if market_dossier.get("source_executive_dossier_snapshot") != snapshot:
        raise DossierValidationError(["market dossier snapshot does not match dossier"])
    return BASE._mapping(BASE._freeze(copy.deepcopy(dict(market_dossier))))


def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain(nested) for key, nested in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(nested) for nested in value]
    return value


def _render_section_coverage(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    rows: list[str] = []
    for index, row in enumerate(BASE._rows(dossier["section_coverage"]), start=1):
        section = str(row["section"])
        heading_id = f"section-coverage-title-{index}"
        request = row.get("inspection_request")
        request_fact = ""
        if isinstance(request, Mapping):
            request_fact = (
                f'<dt>{labels["request"]}</dt><dd class="section-coverage-request">'
                f'{REQUEST_DECISION_LABELS[locale][str(request["decision"])]}</dd>'
            )
        rows.append(
            f'<li class="section-coverage-row"><article aria-labelledby="{heading_id}">\n'
            f'  <h3 id="{heading_id}">{SECTION_LABELS[locale][section]}</h3>\n'
            f'  <dl class="section-coverage-facts">'
            f'<dt>{labels["availability"]}</dt><dd>{AVAILABILITY_LABELS[locale][str(row["availability"])]}</dd>'
            f'<dt>{labels["reason"]}</dt><dd>{REASON_LABELS[locale][str(row["reason"])]}</dd>'
            f'{request_fact}</dl>\n'
            f'</article></li>'
        )
    return f'''<section class="section-block section-coverage-ledger" aria-labelledby="section-coverage-ledger-title" id="section-coverage">
      <h2 id="section-coverage-ledger-title">{labels['coverage_title']}</h2>
      <ol class="section-coverage-list">{''.join(rows)}</ol>
    </section>'''


def _render_coach_priorities(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    cards: list[str] = []
    for priority in BASE._rows(dossier["priorities"]):
        rank = priority["rank"]
        heading_id = f"coach-priority-title-{rank}"
        template_heading_id = f"coach-template-title-{rank}"
        template = BASE._mapping(priority["client_template"])
        fields = "".join(
            f'<li><span class="coach-template-field">{TEMPLATE_FIELD_LABELS[locale][str(key)]}</span>'
            f'<span class="coach-template-blank" aria-hidden="true"></span></li>'
            for key in template["field_keys"]
        )
        cards.append(f'''<article class="card span-4 coach-priority-card" aria-labelledby="{heading_id}">
          <div class="priority-header"><h3 id="{heading_id}">{html.escape(str(priority['title']), quote=True)}</h3><span class="priority-rank">{rank}</span></div>
          <p><span class="label">{labels['target']}</span>{SECTION_LABELS[locale][str(priority['target_section'])]}</p>
          <p class="coach-observation"><span class="label">{labels['observation']}</span>{html.escape(str(priority['coach_observation']), quote=True)}</p>
          <p><span class="label">{labels['why']}</span>{html.escape(str(priority['why_it_matters']), quote=True)}</p>
          <p class="coach-prompt"><span class="label">{labels['prompt']}</span>{html.escape(str(priority['coach_prompt']), quote=True)}</p>
          <section class="coach-template" aria-labelledby="{template_heading_id}">
            <h4 id="{template_heading_id}">{labels['template']}: {TEMPLATE_LABELS[locale][str(template['template_id'])]}</h4>
            <ul class="coach-template-list">{fields}</ul>
          </section>
        </article>''')
    return f'''<section class="section-block coach-priorities" aria-labelledby="coach-priorities-title" id="coach-priorities">
      <h2 id="coach-priorities-title">{labels['priorities']}</h2>
      <div class="dossier-grid priorities-grid">{''.join(cards)}</div>
    </section>'''


def _render_market_evidence_unavailable(locale: str) -> str:
    labels = COPY[locale]
    return f'''<div class="dossier-grid section-block">
      <section class="card market-unavailable-card span-12" aria-labelledby="market-unavailable-title" id="market-evidence">
        <h2 id="market-unavailable-title">{labels['market_title']}</h2>
        <p>{labels['market_body']}</p>
        <section class="market-next-investigation" aria-labelledby="market-next-investigation-title">
          <h3 id="market-next-investigation-title">{labels['market_next_title']}</h3>
          <dl class="market-next-investigation-facts">
            <dt>{labels['market_next_scope']}</dt><dd>{labels['market_next_scope_value']}</dd>
            <dt>{labels['market_next_sample']}</dt><dd>{labels['market_next_sample_value']}</dd>
            <dt>{labels['market_next_sources']}</dt><dd>{labels['market_next_sources_value']}</dd>
            <dt>{labels['market_next_date']}</dt><dd>{labels['market_next_date_value']}</dd>
          </dl>
          <p class="market-next-investigation-boundary market-boundary">{labels['market_next_boundary']}</p>
        </section>
      </section>
    </div>'''


def _market_state_copy(state: object, locale: str) -> tuple[str, str]:
    symbol, spanish, english = MATRIX_STATE_COPY.get(str(state), MATRIX_STATE_COPY["unknown"])
    return symbol, spanish if locale == "es" else english


LEARNING_DECISION_COPY = {
    "es": {
        "project_first": "Primero, prueba privada",
        "recommended": "Considerar tras revisión",
        "consider": "Considerar con revisión",
        "pause": "Pausar por ahora",
        "apply_with_boundary": "Aplicar con límite explícito",
        "not_needed": "No es necesario por ahora",
        "candidate_owned_project": "Proyecto propio",
        "lab": "Laboratorio",
        "course": "Curso",
        "certification": "Certificación",
        "free_resource": "Recurso gratuito",
        "do_nothing_now": "Sin aprendizaje por ahora",
        "linkedin": "Perfil",
        "application_packet": "Paquete de candidatura",
        "interview": "Práctica de entrevista",
    },
    "en": {
        "project_first": "Private proof first",
        "recommended": "Consider after review",
        "consider": "Consider with review",
        "pause": "Pause for now",
        "apply_with_boundary": "Apply with an explicit boundary",
        "not_needed": "Not needed now",
        "candidate_owned_project": "Candidate-owned project",
        "lab": "Lab",
        "course": "Course",
        "certification": "Certification",
        "free_resource": "Free resource",
        "do_nothing_now": "No learning now",
        "linkedin": "Profile",
        "application_packet": "Application packet",
        "interview": "Interview practice",
    },
}


def _learning_text(value: object) -> str:
    return html.escape(str(value), quote=True)


def _render_learning_roi(market_dossier: Mapping[str, object], locale: str) -> str:
    """Render only validated v2 learning decisions; v1 keeps its prior bytes."""
    if market_dossier.get("schema_version") != MARKET_V2.SCHEMA_VERSION:
        return ""
    labels = COPY[locale]
    copy_labels = LEARNING_DECISION_COPY[locale]
    options = {
        str(row["option_id"]): BASE._mapping(row)
        for row in BASE._rows(market_dossier["learning_options"])
    }
    decision_rows: list[str] = []
    for index, row_value in enumerate(BASE._rows(market_dossier["learning_decisions"]), start=1):
        row = BASE._mapping(row_value)
        option = options[str(row["option_id"])]
        decision_class = {
            "project_first": "project-first",
            "consider": "consider",
            "not_needed": "not-needed",
            "recommended": "recommended",
            "pause": "pause",
            "apply_with_boundary": "apply-with-boundary",
        }[str(row["decision"])]
        provenance_values = (
            ("learning_provider", option.get("provider")),
            ("learning_option", option.get("option")),
            ("learning_source_title", option.get("source_title")),
            ("learning_source_date", option.get("source_date")),
            ("learning_geography", option.get("geography")),
            ("learning_role", option.get("role")),
            ("learning_seniority", option.get("seniority")),
        )
        provenance_rows = "".join(
            f"<dt>{labels[label]}</dt><dd>{_learning_text(value)}</dd>"
            for label, value in provenance_values
            if value is not None and str(value).strip()
        )
        unknowns = option.get("unknowns")
        if isinstance(unknowns, (list, tuple)) and unknowns:
            provenance_rows += f"<dt>{labels['learning_unknowns']}</dt><dd>{_learning_text('; '.join(str(value) for value in unknowns))}</dd>"
        provenance = f'''<section class="learning-provenance" aria-labelledby="learning-provenance-title-{index}">
            <h5 id="learning-provenance-title-{index}">{labels['learning_provenance']}</h5>
            <dl class="learning-provenance-facts">{provenance_rows}</dl>
          </section>'''
        decision_rows.append(f'''<article class="learning-decision-row learning-decision-row--{decision_class}" data-decision="{_learning_text(row['decision'])}" data-option-type="{_learning_text(row['option_type'])}">
          <header class="learning-decision-heading"><div><span class="learning-decision-kicker">{labels['learning_decision_label']}</span><h4>{copy_labels[str(row['decision'])]}</h4></div><span class="learning-option-type">{copy_labels[str(row['option_type'])]}</span></header>
          {provenance}
          <dl class="learning-decision-facts">
            <dt>{labels['learning_frequency']}</dt><dd>{_learning_text(row['frequency_display'])}</dd>
            <dt>{labels['learning_option_type']}</dt><dd>{copy_labels[str(row['option_type'])]}</dd>
            <dt>{labels['learning_decision_basis']}</dt><dd class="decision-basis">{_learning_text(row['decision_basis'])}</dd>
            <dt>{labels['learning_opportunity_cost']}</dt><dd class="opportunity-cost">{_learning_text(row['opportunity_cost'])}</dd>
            <dt>{labels['learning_proof']}</dt><dd>{_learning_text(row['proof_needed'])}</dd>
            <dt>{labels['learning_cost']}</dt><dd>{_learning_text(option['current_cost'])}</dd>
            <dt>{labels['learning_currency']}</dt><dd>{_learning_text(option['currency'])}</dd>
            <dt>{labels['learning_tax']}</dt><dd>{_learning_text(option['tax'])}</dd>
            <dt>{labels['learning_duration']}</dt><dd>{_learning_text(option['duration'])}</dd>
            <dt>{labels['learning_availability']}</dt><dd>{_learning_text(option['availability'])}</dd>
          </dl>
          <p>{_learning_text(row['expected_signal'])}</p>
          <p class="market-boundary">{_learning_text(row['next_action_gate'])}</p>
        </article>''')
    coach = BASE._mapping(market_dossier["coach_decision"])
    coach_surface = f'''<section class="learning-coach-decision" aria-labelledby="learning-coach-title">
      <h3 id="learning-coach-title">{labels['learning_coach']}</h3>
      <p><strong>{copy_labels[str(coach['decision'])]}</strong></p>
      <p>{_learning_text(coach['rationale'])}</p><p class="market-boundary">{_learning_text(coach['review_gate'])}</p>
    </section>'''
    sprint_surface = ""
    sprint_value = market_dossier.get("proof_sprint")
    if isinstance(sprint_value, Mapping):
        sprint = BASE._mapping(sprint_value)
        steps = "".join(f"<li>{_learning_text(step)}</li>" for step in sprint["steps"])
        sprint_surface = f'''<section class="learning-proof-sprint" aria-labelledby="learning-sprint-title">
          <h3 id="learning-sprint-title">{labels['learning_sprint']}</h3><p>{_learning_text(sprint['scope'])}</p><ol>{steps}</ol>
        </section>'''
    reuse_rows = "".join(
        f'<li class="learning-reuse-row">{copy_labels[str(BASE._mapping(row)["destination"])]}</li>'
        for row in BASE._rows(market_dossier["reuse_map"])
    )
    reuse_surface = f'<section class="learning-reuse" aria-labelledby="learning-reuse-title"><h3 id="learning-reuse-title">{labels["learning_reuse"]}</h3><ul>{reuse_rows}</ul></section>' if reuse_rows else ""
    provider_boundary = f'<p class="market-provider-evidence-boundary market-boundary">{labels["learning_provider_synthetic"]}</p>' if market_dossier.get("learning_evidence_mode") == "synthetic" else ""
    return f'''<section class="market-learning-roi" aria-labelledby="market-learning-title">
      <h3 id="market-learning-title">{labels['learning_title']}</h3>{provider_boundary}{coach_surface}
      <section aria-labelledby="learning-decisions-title"><h4 id="learning-decisions-title">{labels['learning_decisions']}</h4><div class="learning-decision-list">{''.join(decision_rows)}</div></section>
      {sprint_surface}{reuse_surface}<p class="market-boundary">{labels['learning_boundary']}</p>
    </section>'''


def _render_market_context(market_dossier: Mapping[str, object], locale: str) -> str:
    """Render the already-validated market artifact without recomputing it."""
    if market_dossier.get("state") == "market_evidence_unavailable":
        return _render_market_evidence_unavailable(locale)
    labels = COPY[locale]
    cards = BASE._rows(market_dossier["vacancy_cards"])
    summary = BASE._mapping(market_dossier["search_summary"])
    card_html: list[str] = []
    key_rows: list[str] = []
    for index, card_value in enumerate(cards, start=1):
        card = BASE._mapping(card_value)
        heading_id = f"market-vacancy-title-{index}"
        short_key = f"V{index}"
        employer = html.escape(str(card["employer_name"]), quote=True)
        title = html.escape(str(card["title"]), quote=True)
        score = int(card["alignment_percent"])
        coverage = card.get("evidence_coverage_percent")
        band = card.get("qualitative_band")
        score_id = f"market-alignment-score-{index}"
        alignment_facts = [
            f'<dt>{labels["market_alignment"]}</dt><dd>{score} {"de" if locale == "es" else "out of"} 100</dd>',
        ]
        if coverage is not None:
            alignment_facts.append(f'<dt>{labels["market_evidence_coverage"]}</dt><dd>{int(coverage)}%</dd>')
        if band is not None:
            spanish_band, english_band = QUALITATIVE_BAND_COPY.get(str(band), QUALITATIVE_BAND_COPY["insufficient_evidence"])
            alignment_facts.append(f'<dt>{labels["market_qualitative_band"]}</dt><dd>{spanish_band if locale == "es" else english_band}</dd>')
        location = card.get("location")
        arrangement = card.get("arrangement")
        source_kind = card.get("source_kind")
        context_rows: list[str] = []
        if location is not None and str(location).strip():
            context_rows.append(f'<dt>{labels["market_location"]}</dt><dd>{html.escape(str(location), quote=True)}</dd>')
        if arrangement is not None and str(arrangement).strip():
            arrangement_es, arrangement_en = ARRANGEMENT_COPY.get(str(arrangement), (str(arrangement), str(arrangement)))
            context_rows.append(f'<dt>{labels["market_arrangement"]}</dt><dd>{html.escape(arrangement_es if locale == "es" else arrangement_en, quote=True)}</dd>')
        if source_kind is not None and str(source_kind).strip():
            source_es, source_en = SOURCE_KIND_COPY.get(str(source_kind), (str(source_kind), str(source_kind)))
            context_rows.append(f'<dt>{labels["market_source_kind"]}</dt><dd>{html.escape(source_es if locale == "es" else source_en, quote=True)}</dd>')
        vacancy_context = f'<dl class="market-vacancy-context">{"".join(context_rows)}</dl>' if context_rows else ""
        source_url = html.escape(str(card["source_url"]), quote=True)
        researched_date = html.escape(str(market_dossier["as_of_date"]), quote=True)
        source_meta = (
            f'<p class="market-source-meta"><a class="market-source-link" href="{source_url}" rel="noreferrer">'
            f'{labels["market_source"]}</a><span>{labels["market_researched"]}: '
            f'<time datetime="{researched_date}">{researched_date}</time></span></p>'
        )
        card_html.append(f'''<article class="vacancy-alignment-card" aria-labelledby="{heading_id}">
          <p class="market-vacancy-key">{short_key}</p><h3 id="{heading_id}">{employer} — {title}</h3>
          <p class="market-alignment-line"><span>{labels['market_alignment']}</span><strong class="market-alignment-score" id="{score_id}">{score} {'de' if locale == 'es' else 'out of'} 100</strong></p>
          <progress max="100" value="{score}" aria-labelledby="{heading_id} {score_id}">{score}</progress>
          <dl class="market-alignment-facts">{''.join(alignment_facts)}</dl>
          {vacancy_context}
          {source_meta}
        </article>''')
        key_rows.append(f"<li><strong>{short_key}</strong> — {employer} — {title}</li>")

    column_keys = [f"V{index}" for index in range(1, len(cards) + 1)]
    column_labels = {
        f"V{index}": f"V{index}: {card['employer_name']} — {card['title']}"
        for index, card in enumerate(cards, start=1)
    }
    header_cells = "".join(f"<th scope=\"col\">{key}</th>" for key in column_keys)
    matrix_rows: list[str] = []
    for row_value in BASE._rows(market_dossier["matrix_rows"]):
        row = BASE._mapping(row_value)
        symbol, state_label = _market_state_copy(row["support_state"], locale)
        profile_cell = f'<td data-label="{html.escape(labels["market_evidence"], quote=True)}"><span aria-hidden="true">{symbol}</span> {state_label}</td>'
        cells: list[str] = [profile_cell]
        for index, cell_value in enumerate(BASE._rows(row["cells"]), start=1):
            required = BASE._mapping(cell_value)["required"]
            required_symbol, required_label = _market_state_copy("verified_match" if required else "not_required", locale)
            data_label = f"{column_labels[f'V{index}']}: {required_label}"
            cells.append(f'<td data-label="{html.escape(data_label, quote=True)}"><span aria-hidden="true">{required_symbol}</span> {required_label}</td>')
        matrix_rows.append(f'''<tr><th scope="row">{html.escape(str(row['signal']), quote=True)}<span class="market-state"> {symbol} {state_label}</span></th>{''.join(cells)}</tr>''')

    recurrence: list[str] = []
    for index, row_value in enumerate(BASE._rows(market_dossier["recurrence_rows"]), start=1):
        row = BASE._mapping(row_value)
        occurrences, sample_size = int(row["occurrences"]), int(row["sample_size"])
        signal_id = f"market-recurrence-signal-{index}"
        count_id = f"market-recurrence-count-{index}"
        recurrence.append(f'''<li class="recurrence-row"><span id="{signal_id}">{html.escape(str(row['signal']), quote=True)}</span>
          <progress value="{occurrences}" max="{sample_size}" aria-labelledby="{signal_id} {count_id}">{occurrences}/{sample_size}</progress><strong class="market-recurrence-count" id="{count_id}">{occurrences}/{sample_size}</strong></li>''')
    limitation = ""
    if market_dossier.get("state") == "limited_market_evidence":
        limitation = f'<p class="market-limitation"><strong>{labels["market_limited"]}:</strong> {html.escape(str(summary["limitation"]), quote=True)}</p>'
    synthetic_boundary = (
        f'<p class="market-synthetic-boundary market-boundary">{labels["market_synthetic"]}</p>'
        if market_dossier.get("evidence_mode") == "synthetic"
        else ""
    )
    route = "".join(f"<li>{html.escape(step, quote=True)}</li>" for step in labels["market_route_steps"])
    learning_surface = _render_learning_roi(market_dossier, locale)
    return f'''<section class="market-summary section-block" aria-labelledby="market-summary-title" id="market-evidence">
      <h2 id="market-summary-title">{labels['market_summary']}</h2>
      <p>{len(cards)} {'vacantes' if locale == 'es' else 'vacancies'}</p><p class="market-directional-legend market-boundary">{labels['market_directional_legend']}</p><p class="market-eligibility-boundary market-boundary">{labels['market_eligibility_boundary']}</p>{synthetic_boundary}{limitation}
      <div class="vacancy-alignment-list">{''.join(card_html)}</div>
      <section class="market-key" aria-labelledby="market-key-title"><h3 id="market-key-title">{labels['market_key']}</h3><ol>{''.join(key_rows)}</ol></section>
      <section class="market-matrix-wrap" aria-labelledby="market-matrix-title"><h3 id="market-matrix-title">{labels['market_matrix']}</h3>
        <table class="market-matrix"><thead><tr><th scope="col">{'Señal' if locale == 'es' else 'Signal'}</th><th scope="col">{labels['market_evidence']}</th>{header_cells}</tr></thead>
        <tbody>{''.join(matrix_rows)}</tbody></table></section>
      <section aria-labelledby="market-recurrence-title"><h3 id="market-recurrence-title">{labels['market_recurrence']}</h3><ul class="recurrence-list">{''.join(recurrence)}</ul><p class="market-boundary">{labels['market_boundary']}</p></section>
      {learning_surface}
      <section class="gap-closure-route" aria-labelledby="gap-closure-route-title"><h3 id="gap-closure-route-title">{labels['market_route']}</h3><ol>{route}</ol></section>
    </section>'''


def _render_main(dossier: Mapping[str, object], locale: str, market_dossier: Mapping[str, object] | None = None) -> str:
    projected = COMPAT.project_v2_to_v1(BASE._mapping(_plain(dossier)))
    labels = COPY[locale]
    reading_links = "".join(
        f'<li><a href="#{html.escape(target, quote=True)}"{(" aria-current=\"location\"" if index == 0 else "")}>{html.escape(label, quote=True)}</a></li>'
        for index, (target, label) in enumerate(labels["reading_path_items"])
    )
    reading_path = (
        f'<nav class="reading-path span-12" aria-label="{html.escape(labels["reading_path_aria"], quote=True)}">'
        f'<span class="reading-path-title">{html.escape(labels["reading_path_title"], quote=True)}</span>'
        f'<ol>{reading_links}</ol></nav>'
    )
    opening = BASE._render_verdict(projected, locale) + BASE._render_recruiter_scan(projected, locale) + reading_path
    bridge_holds = BASE._render_holds(projected, locale) + BASE._render_screen_bridge(projected, locale)
    market_context = projected.get("market_context")
    legacy_market_surface = (
        BASE._render_market_context(BASE._mapping(BASE._freeze(projected)), locale)
        if isinstance(market_context, Mapping)
        and market_context.get("state") == "dated_vacancy_evidence"
        else _render_market_evidence_unavailable(locale)
    )
    market_surface = _render_market_context(market_dossier, locale) if market_dossier is not None else legacy_market_surface
    return f'''<main id="main-content" class="shell" tabindex="-1">
      <div class="dossier-grid">{opening}</div>
      {_render_section_coverage(dossier, locale)}
      {_render_coach_priorities(dossier, locale)}
      <div class="dossier-grid section-block">{BASE._render_analytics(projected, locale)}</div>
      {BASE._render_dimensions(projected, locale)}
      {BASE._render_visual_review(projected, locale)}
      {market_surface}
      {BASE._render_copy_blocks(projected, locale)}
      <div class="dossier-grid section-block">{bridge_holds}</div>
      {BASE._render_questions(projected, locale)}
      <div class="dossier-grid section-block">{BASE._render_plan(projected, locale)}{BASE._render_details(projected, locale)}</div>
    </main>
    <footer class="shell footer"><strong>{BASE.COPY[locale]['action_boundary']}</strong> <span class="employment-boundary">{BASE.COPY[locale]['employment_boundary']}</span></footer>'''


def build_chat_summary(dossier: Mapping[str, object]) -> str:
    frozen = _validate_and_freeze(dossier)
    locale = str(frozen["locale"])
    projected = COMPAT.project_v2_to_v1(BASE._mapping(_plain(frozen)))
    verdict = BASE._mapping(projected["verdict"])
    first_priority = BASE._rows(projected["priorities"])[0]
    parts = [
        BASE._summary_text(verdict["statement"], 60),
        f"{BASE.COPY[locale]['first_action']}: {BASE._summary_text(first_priority['action'], 55)}",
    ]
    pending = VALIDATOR.select_pending_inspection_section(BASE._mapping(_plain(frozen)))
    if pending is not None:
        parts.append(AUTHORIZATION_QUESTIONS[locale][pending])
    else:
        questions = BASE._rows(projected["questions"])
        if questions:
            parts.append(
                f"{BASE.COPY[locale]['first_question']}: "
                f"{BASE._summary_text(questions[0]['question'], 45)}"
            )
    parts.append(BASE.COPY[locale]["action_boundary"])
    summary = "\n\n".join(parts)
    if len(summary.split()) > 180:
        raise RuntimeError("chat summary budget is invalid")
    return summary


def render_dossier_html(dossier: Mapping[str, object], market_dossier: Mapping[str, object] | None = None) -> str:
    frozen = _validate_and_freeze(dossier)
    frozen_market = _validate_and_freeze_market(frozen, market_dossier) if market_dossier is not None else None
    locale = str(frozen["locale"])
    template = BASE.ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, TEMPLATE_PATH)
    base_css = BASE.ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, BASE_CSS_PATH)
    extension_css = BASE.ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, CSS_PATH)
    market_css = BASE.ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, MARKET_CSS_PATH) if frozen_market is not None else ""
    static_tokens = BASE.STATIC_TEMPLATE_TOKEN.findall(template)
    if sorted(static_tokens) != sorted(BASE.TEMPLATE_TOKENS):
        raise RuntimeError("dossier template token contract is invalid")
    substitutions = {
        "{{LANG}}": locale,
        "{{TITLE}}": BASE.COPY[locale]["title"],
        "{{INLINE_CSS}}": base_css + extension_css + market_css,
        "{{HEADER}}": BASE._render_header(locale),
        "{{MAIN}}": _render_main(frozen, locale, frozen_market),
        "{{INLINE_SCRIPT}}": BASE.INLINE_SCRIPT + "\n\n" + READING_PATH_SCRIPT,
    }
    return BASE.STATIC_TEMPLATE_TOKEN.sub(lambda match: substitutions[match.group(0)], template)


def write_dossier_html(
    dossier_path: Path,
    output_path: Path,
    *,
    market_dossier_path: Path | None = None,
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
    market_dossier = None
    if market_dossier_path is not None:
        try:
            market_dossier = MARKET.load_market_dossier(Path(market_dossier_path))
        except ValueError as error:
            raise DossierValidationError(["market learning dossier could not be loaded"]) from error
    rendered = render_dossier_html(dossier, market_dossier)
    summary = build_chat_summary(dossier)
    BASE._atomic_private_write(output, rendered.encode("utf-8"), force=force)
    return RenderReceipt(output, "text/html", str(dossier["locale"]), summary)


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Render a private career dossier v2.")
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--market-dossier", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--include-artifact-path", action="store_true", help="include the local output path in the CLI receipt")
    try:
        arguments = parser.parse_args(argv)
    except _ArgumentError:
        print(json.dumps({"error": {"code": "invalid_arguments"}}, separators=(",", ":")), file=sys.stderr)
        return 3
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    try:
        receipt = write_dossier_html(arguments.dossier, arguments.output, market_dossier_path=arguments.market_dossier, force=arguments.force)
    except OSError:
        print("cannot write dossier artifact", file=sys.stderr)
        return 3
    except (VALIDATOR.DossierLoadError, DossierValidationError) as error:
        if isinstance(error, DossierValidationError):
            print("\n".join(error.errors), file=sys.stderr)
            return 2
        else:
            print(str(error), file=sys.stderr)
            return 3
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
