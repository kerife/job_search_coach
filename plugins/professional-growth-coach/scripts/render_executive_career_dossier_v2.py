#!/usr/bin/env python3
"""Render the private LinkedIn coaching dossier v2 by composing v1 surfaces."""

from __future__ import annotations

import argparse
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

ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
TEMPLATE_PATH = ASSET_ROOT / "executive-career-dossier-v1.html"
BASE_CSS_PATH = ASSET_ROOT / "executive-career-dossier-v1.css"
CSS_PATH = ASSET_ROOT / "executive-career-dossier-v2.css"

DossierValidationError = BASE.DossierValidationError
RenderReceipt = BASE.RenderReceipt


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
        "availability": "Disponibilidad", "reason": "Motivo", "request": "Decisión de inspección",
        "priorities": "Prioridades de coaching", "target": "Sección objetivo",
        "observation": "Observación", "why": "Por qué importa", "prompt": "Pregunta de coaching",
        "template": "Plantilla privada", "market_title": "Evidencia de mercado no disponible",
        "market_body": "Este dossier no incluye evidencia de mercado. Continúa con la evidencia del perfil ya revisada.",
    },
    "en": {
        "coverage_title": "Section coverage", "availability": "Availability", "reason": "Reason",
        "request": "Inspection decision", "priorities": "Coaching priorities",
        "target": "Target section", "observation": "Observation", "why": "Why it matters",
        "prompt": "Coaching prompt", "template": "Private template",
        "market_title": "Market evidence unavailable",
        "market_body": "This dossier includes no market evidence. Continue with the profile evidence already reviewed.",
    },
}


def _validate_and_freeze(dossier: Mapping[str, object]) -> Mapping[str, object]:
    errors = VALIDATOR.validate_dossier(dossier)
    if errors:
        raise DossierValidationError(errors)
    return BASE._mapping(BASE._freeze(dossier))


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
    return f'''<section class="section-block section-coverage-ledger" aria-labelledby="section-coverage-ledger-title">
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
    return f'''<section class="section-block coach-priorities" aria-labelledby="coach-priorities-title">
      <h2 id="coach-priorities-title">{labels['priorities']}</h2>
      <div class="dossier-grid priorities-grid">{''.join(cards)}</div>
    </section>'''


def _render_market_evidence_unavailable(locale: str) -> str:
    labels = COPY[locale]
    return f'''<div class="dossier-grid section-block">
      <section class="card market-unavailable-card span-12" aria-labelledby="market-unavailable-title">
        <h2 id="market-unavailable-title">{labels['market_title']}</h2>
        <p>{labels['market_body']}</p>
      </section>
    </div>'''


def _render_main(dossier: Mapping[str, object], locale: str) -> str:
    projected = COMPAT.project_v2_to_v1(BASE._mapping(_plain(dossier)))
    opening = BASE._render_verdict(projected, locale) + BASE._render_recruiter_scan(projected, locale)
    bridge_holds = BASE._render_holds(projected, locale) + BASE._render_screen_bridge(projected, locale)
    market_context = projected.get("market_context")
    market_surface = (
        BASE._render_market_context(BASE._mapping(BASE._freeze(projected)), locale)
        if isinstance(market_context, Mapping)
        and market_context.get("state") == "dated_vacancy_evidence"
        else _render_market_evidence_unavailable(locale)
    )
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


def render_dossier_html(dossier: Mapping[str, object]) -> str:
    frozen = _validate_and_freeze(dossier)
    locale = str(frozen["locale"])
    template = BASE.ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, TEMPLATE_PATH)
    base_css = BASE.ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, BASE_CSS_PATH)
    extension_css = BASE.ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, CSS_PATH)
    static_tokens = BASE.STATIC_TEMPLATE_TOKEN.findall(template)
    if sorted(static_tokens) != sorted(BASE.TEMPLATE_TOKENS):
        raise RuntimeError("dossier template token contract is invalid")
    substitutions = {
        "{{LANG}}": locale,
        "{{TITLE}}": BASE.COPY[locale]["title"],
        "{{INLINE_CSS}}": base_css + extension_css,
        "{{HEADER}}": BASE._render_header(locale),
        "{{MAIN}}": _render_main(frozen, locale),
        "{{INLINE_SCRIPT}}": BASE.INLINE_SCRIPT,
    }
    return BASE.STATIC_TEMPLATE_TOKEN.sub(lambda match: substitutions[match.group(0)], template)


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
    BASE._atomic_private_write(output, rendered.encode("utf-8"), force=force)
    return RenderReceipt(output, "text/html", str(dossier["locale"]), summary)


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a private career dossier v2.")
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        receipt = write_dossier_html(arguments.dossier, arguments.output, force=arguments.force)
    except OSError:
        print("cannot write dossier artifact", file=sys.stderr)
        return 3
    except (VALIDATOR.DossierLoadError, DossierValidationError) as error:
        if isinstance(error, DossierValidationError):
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
