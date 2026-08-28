#!/usr/bin/env python3
"""Render a private bilingual recruiter screen intake brief."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets"
TEMPLATE_PATH = ASSET_ROOT / "recruiter-target-screen-intake-v1.html"
CSS_PATH = ASSET_ROOT / "recruiter-target-screen-intake-v1.css"


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_screen_renderer_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("screen intake dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _sibling("validate_recruiter_target_screen_intake.py")
ASSET_LOADER = _sibling("private_asset_loader.py")
WRITER = _sibling("render_recruiter_target_shortlist.py")
INPUT_LOADER = _sibling("private_input_loader.py")
CONTINUITY_RAIL = _sibling("recruiter_continuity_rail.py")


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise ValueError("invalid arguments")


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _display_requirement(value: object) -> str:
    """Render requirement prose without exposing the internal V-### key."""
    return re.sub(r"^V-\d{3}:\s*", "", str(value))


COPY = {
    "es": {
        "skip": "Saltar al brief de preparación",
        "title": "Intake de preparación para entrevista",
        "kicker": "Puente privado por objetivo",
        "heading": "¿Está listo este objetivo para preparar la entrevista?",
        "date": "Fecha de referencia",
        "ready": "Listo para revisión manual",
        "clarify_first": "Aclarar contexto antes de preparar",
        "stop": "Detener y registrar",
        "requirements": "Requisitos de la vacante",
        "context": "Contexto confirmado",
        "facts": "Hechos del candidato",
        "company": "Evidencia de compañía",
        "stage": "Etapa declarada",
        "checks": "Cuatro checks de preparación",
        "pass": "Pasa",
        "clarify": "Aclarar",
        "stop_check": "Detener",
        "next": "Siguiente paso seguro",
        "ready_heading": "Preparar entrevista para revisión",
        "clarify_heading": "Recopilar contexto antes de preparar",
        "stop_heading": "No contactar; registrar decisión",
        "ready_next": "Revisar manualmente la preparación de entrevista; no se envía ni agenda nada.",
        "clarify_next": "Completar el contexto faltante y volver a revisar antes de preparar.",
        "stop_next": "Registrar la decisión y no contactar mientras esta condición siga vigente.",
        "boundary": "Este brief sólo organiza evidencia por objetivo. No autoriza contacto, no prepara automáticamente y no predice una entrevista.",
        "footer": "Sin mensajes, conexiones, calendario ni respuestas guardadas.",
        "check_names": {"target_context": "Contexto del objetivo", "proof_packet": "Paquete de pruebas", "low_friction_ask": "Pregunta de baja fricción", "screen_readiness": "Preparación para el filtro"},
        "company_states": {"verified": "Verificada", "candidate_reported": "Reportada por el candidato", "unknown": "Aún desconocida"},
        "stages": {
            "recruiter_screen": "Filtro con reclutador", "first_interview": "Primera entrevista", "technical_screen": "Filtro técnico",
            "hiring_manager": "Entrevista con hiring manager", "technical_deep_dive": "Profundización técnica", "take_home": "Ejercicio para casa",
            "system_design": "Diseño de sistemas", "behavioral_loop": "Ronda conductual", "panel": "Panel de entrevistas", "offer_stage": "Etapa de oferta",
        },
    },
    "en": {
        "skip": "Skip to preparation brief",
        "title": "Interview preparation intake",
        "kicker": "Private target-specific bridge",
        "heading": "Is this target ready for interview preparation?",
        "date": "Reference date",
        "ready": "Ready for manual review",
        "clarify_first": "Clarify context before preparing",
        "stop": "Stop and record",
        "requirements": "Vacancy requirements",
        "context": "Confirmed context",
        "facts": "Candidate facts",
        "company": "Company evidence",
        "stage": "Stated stage",
        "checks": "Four preparation checks",
        "pass": "Pass",
        "clarify": "Clarify",
        "stop_check": "Stop",
        "next": "Safe next step",
        "ready_heading": "Prepare interview for review",
        "clarify_heading": "Collect context before preparing",
        "stop_heading": "Do not contact; record decision",
        "ready_next": "Review interview preparation manually; nothing is sent or scheduled.",
        "clarify_next": "Complete the missing context and review again before preparing.",
        "stop_next": "Record the decision and do not contact while this condition remains.",
        "boundary": "This brief organizes evidence by target only. It does not authorize contact, prepare automatically, or predict an interview.",
        "footer": "No messages, connections, calendar actions, or saved answers.",
        "check_names": {"target_context": "Target context", "proof_packet": "Proof packet", "low_friction_ask": "Low-friction ask", "screen_readiness": "Screen readiness"},
        "company_states": {"verified": "Verified", "candidate_reported": "Candidate-reported", "unknown": "Still unknown"},
        "stages": {
            "recruiter_screen": "Recruiter screen", "first_interview": "First interview", "technical_screen": "Technical screen",
            "hiring_manager": "Hiring manager interview", "technical_deep_dive": "Technical deep dive", "take_home": "Take-home exercise",
            "system_design": "System design", "behavioral_loop": "Behavioral loop", "panel": "Interview panel", "offer_stage": "Offer stage",
        },
    },
}


def render_screen_intake_html(value: Mapping[str, object]) -> str:
    errors = VALIDATOR.validate_screen_intake(value, as_of=dt.date.today())
    if errors:
        raise ValueError("recruiter target screen intake validation failed")
    locale = str(value["locale"])
    labels = COPY[locale]
    readiness = str(value["readiness_decision"])
    status_label = labels[readiness]
    next_copy = labels[f"{readiness}_next"]
    flow_label, flow_rail = CONTINUITY_RAIL.render_continuity_rail(locale, "screen_intake")
    intake = value["intake"]
    check_items = []
    for check in value["checks"]:
        label = labels[str(check["status"])] if check["status"] != "stop" else labels["stop_check"]
        check_items.append(
            f'<li class="screen-check screen-check--{html.escape(str(check["status"]))}"><strong>{html.escape(labels["check_names"][str(check["check"])])}</strong><span>{html.escape(label)}</span><p>{html.escape(str(check["evidence_note"]), quote=True)}</p></li>'
        )
    requirement_items = "".join(
        f"<li>{html.escape(_display_requirement(item), quote=True)}</li>"
        for item in intake["vacancy_requirements"]
    )
    fact_count = str(len(intake["candidate_fact_ids"]))
    template = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, TEMPLATE_PATH)
    css = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, CSS_PATH)
    replacements = {
        "{{LANG}}": locale,
        "{{SKIP_LINK}}": html.escape(labels["skip"]),
        "{{TITLE}}": html.escape(labels["title"], quote=True),
        "{{KICKER}}": html.escape(labels["kicker"]),
        "{{HEADING}}": html.escape(labels["heading"]),
        "{{DATE_LABEL}}": html.escape(labels["date"]),
        "{{AS_OF_DATE}}": html.escape(str(value["as_of_date"]), quote=True),
        "{{STATUS}}": html.escape(status_label),
        "{{NEXT_HEADING}}": html.escape(labels[f"{readiness}_heading"]),
        "{{NEXT_COPY}}": html.escape(next_copy),
        "{{REQUIREMENTS_LABEL}}": html.escape(labels["requirements"]),
        "{{CONTEXT_LABEL}}": html.escape(labels["context"]),
        "{{REQUIREMENTS}}": requirement_items,
        "{{FACTS_LABEL}}": html.escape(labels["facts"]),
        "{{FACT_COUNT}}": html.escape(fact_count),
        "{{COMPANY_LABEL}}": html.escape(labels["company"]),
        "{{COMPANY_STATE}}": html.escape(labels["company_states"][str(intake["company_evidence_state"])]),
        "{{STAGE_LABEL}}": html.escape(labels["stage"]),
        "{{STAGE}}": html.escape(labels["stages"][str(intake["stated_stage"])]),
        "{{CHECKS_LABEL}}": html.escape(labels["checks"]),
        "{{CHECKS}}": "".join(check_items),
        "{{NEXT_LABEL}}": html.escape(labels["next"]),
        "{{BOUNDARY}}": html.escape(labels["boundary"]),
        "{{FOOTER}}": html.escape(labels["footer"]),
        "{{INLINE_CSS}}": css,
        "{{FLOW_RAIL_LABEL}}": html.escape(flow_label),
        "{{FLOW_RAIL}}": flow_rail,
    }
    for key, replacement in replacements.items():
        template = template.replace(key, replacement)
    return template


def write_screen_intake_html(value: Mapping[str, object], output: Path) -> None:
    WRITER._atomic_private_write(output, render_screen_intake_html(value).encode("utf-8"))


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Render a private recruiter target screen intake.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    try:
        args = parser.parse_args(argv)
        value = json.loads(INPUT_LOADER.read_bounded_bytes(args.input, 128_000), object_pairs_hook=_unique)
        write_screen_intake_html(value, args.output)
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    print(json.dumps({"artifact_kind": value["artifact_kind"], "schema_version": value["schema_version"], "ui_locale": value["locale"]}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
