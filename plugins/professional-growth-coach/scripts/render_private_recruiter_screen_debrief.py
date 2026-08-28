#!/usr/bin/env python3
"""Render a private bilingual screen debrief without raw notes or IDs."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
TEMPLATE = ASSETS / "private-recruiter-screen-debrief-v1.html"
CSS = ASSETS / "private-recruiter-screen-debrief-v1.css"


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_debrief_renderer_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("screen debrief dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _sibling("validate_private_recruiter_screen_debrief.py")
LOADER = _sibling("private_asset_loader.py")
INPUT_LOADER = _sibling("private_input_loader.py")
WRITER = _sibling("render_private_recruiter_followthrough_checkpoint.py")
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


COPY = {
    "es": {
        "title": "Debrief privado del filtro", "skip": "Ir al debrief", "kicker": "Registro estructurado posterior al filtro",
        "heading": "¿Qué quedó claro después del filtro?", "date": "Fecha observada", "stage": "Etapa", "facts": "Hechos usados",
        "unknown": "Temas aún desconocidos", "coverage": "Cobertura de la conversación", "discussed": "Discutido", "not_discussed": "No discutido", "unclear": "Ambiguo",
        "decision": {"continue_review": "Continuar a revisión", "pause": "Pausar y aclarar", "stop": "Detener y registrar"},
        "next": "Siguiente paso seguro", "next_action": {"manual_prepare_next_stage_review": "Preparar la siguiente etapa para revisión manual", "collect_debrief_context": "Recopilar contexto del debrief", "record_stop_decision": "Registrar la decisión de detenerse"},
        "boundary": "Este debrief registra sólo cobertura estructurada. No conserva texto crudo, no contacta, no agenda y no prepara automáticamente.",
        "footer": "Revisión manual requerida · sin mensajes · sin calendario · sin predicciones",
        "stages": {
            "recruiter_screen": "Filtro con reclutador", "first_interview": "Primera entrevista", "technical_screen": "Filtro técnico",
            "hiring_manager": "Entrevista con hiring manager", "technical_deep_dive": "Profundización técnica", "take_home": "Ejercicio para casa",
            "system_design": "Diseño de sistemas", "behavioral_loop": "Ronda conductual", "panel": "Panel de entrevistas", "offer_stage": "Etapa de oferta",
        },
        "topics": {"requirement": "Requisitos", "scope": "Alcance y éxito", "team_context": "Contexto del equipo"},
    },
    "en": {
        "title": "Private screen debrief", "skip": "Skip to debrief", "kicker": "Structured post-screen record",
        "heading": "What became clear after the screen?", "date": "Observed date", "stage": "Stage", "facts": "Facts used",
        "unknown": "Topics still unknown", "coverage": "Conversation coverage", "discussed": "Discussed", "not_discussed": "Not discussed", "unclear": "Unclear",
        "decision": {"continue_review": "Continue to review", "pause": "Pause and clarify", "stop": "Stop and record"},
        "next": "Safe next step", "next_action": {"manual_prepare_next_stage_review": "Prepare the next stage for manual review", "collect_debrief_context": "Collect debrief context", "record_stop_decision": "Record the stop decision"},
        "boundary": "This debrief records structured coverage only. It keeps no raw text, contacts, calendars, or automatic preparation.",
        "footer": "Manual review required · no messages · no calendar · no predictions",
        "stages": {
            "recruiter_screen": "Recruiter screen", "first_interview": "First interview", "technical_screen": "Technical screen",
            "hiring_manager": "Hiring manager interview", "technical_deep_dive": "Technical deep dive", "take_home": "Take-home exercise",
            "system_design": "System design", "behavioral_loop": "Behavioral loop", "panel": "Interview panel", "offer_stage": "Offer stage",
        },
        "topics": {"requirement": "Requirements", "scope": "Scope and success", "team_context": "Team context"},
    },
}


def render_screen_debrief_html(
    value: Mapping[str, object],
    receipt: Mapping[str, object],
    intake: Mapping[str, object],
    *,
    checkpoint: Mapping[str, object] | None = None,
) -> str:
    selected_checkpoint = checkpoint if checkpoint is not None else value.get("source_checkpoint")
    errors = VALIDATOR.validate_screen_debrief(value, receipt, intake, checkpoint=selected_checkpoint, as_of=dt.date.today())
    if errors:
        raise ValueError("private recruiter screen debrief validation failed")
    labels = COPY[str(value["locale"])]
    source_context = intake["intake"]
    stage = labels["stages"][str(source_context["stated_stage"])]
    decision = str(value["decision"])
    action = str(value["handoff"]["next_safe_action"])
    flow_label, flow_rail = CONTINUITY_RAIL.render_continuity_rail(str(value["locale"]), "screen_debrief")
    counts = {status: sum(1 for row in value["coverage"] if row["status"] == status) for status in ("discussed", "not_discussed", "unclear")}
    coverage_rows = "".join(
        f'<li class="debrief-coverage debrief-coverage--{html.escape(str(row["status"]))}"><strong>{html.escape(labels["topics"][str(row["topic"])])}</strong><span>{html.escape(labels[str(row["status"])])}</span></li>'
        for row in value["coverage"]
    )
    template = LOADER.read_private_asset(ROOT, TEMPLATE)
    css = LOADER.read_private_asset(ROOT, CSS)
    replacements = {
        "{{LANG}}": html.escape(str(value["locale"])), "{{TITLE}}": html.escape(labels["title"], quote=True), "{{SKIP}}": html.escape(labels["skip"]),
        "{{KICKER}}": html.escape(labels["kicker"]), "{{HEADING}}": html.escape(labels["heading"]), "{{DATE_LABEL}}": html.escape(labels["date"]),
        "{{DATE}}": html.escape(str(value["observed_date"]), quote=True), "{{STAGE_LABEL}}": html.escape(labels["stage"]), "{{STAGE}}": html.escape(stage),
        "{{FACTS_LABEL}}": html.escape(labels["facts"]), "{{FACT_COUNT}}": str(len(value["facts_used"])), "{{UNKNOWN_LABEL}}": html.escape(labels["unknown"]),
        "{{UNKNOWN_COUNT}}": str(len(value["unknown_topics"])), "{{COVERAGE_LABEL}}": html.escape(labels["coverage"]), "{{COVERAGE}}": coverage_rows,
        "{{DISCUSSED_COUNT}}": str(counts["discussed"]), "{{UNCLEAR_COUNT}}": str(counts["unclear"]), "{{DECISION}}": html.escape(labels["decision"][decision]),
        "{{NEXT_LABEL}}": html.escape(labels["next"]), "{{NEXT_ACTION}}": html.escape(labels["next_action"][action]), "{{BOUNDARY}}": html.escape(labels["boundary"]),
        "{{FOOTER}}": html.escape(labels["footer"]), "{{INLINE_CSS}}": css,
        "{{FLOW_RAIL_LABEL}}": html.escape(flow_label), "{{FLOW_RAIL}}": flow_rail,
    }
    for key, replacement in replacements.items():
        template = template.replace(key, replacement)
    return template


def write_screen_debrief_html(value: Mapping[str, object], receipt: Mapping[str, object], intake: Mapping[str, object], output: Path, *, checkpoint: Mapping[str, object] | None = None) -> None:
    WRITER._atomic_private_write(output, render_screen_debrief_html(value, receipt, intake, checkpoint=checkpoint).encode("utf-8"))


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Render a private recruiter screen debrief.")
    parser.add_argument("input", type=Path); parser.add_argument("--checkpoint", type=Path, required=True); parser.add_argument("--receipt", type=Path, required=True); parser.add_argument("--intake", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    try:
        args = parser.parse_args(argv)
        value = json.loads(INPUT_LOADER.read_bounded_bytes(args.input, 128_000), object_pairs_hook=_unique)
        checkpoint = json.loads(INPUT_LOADER.read_bounded_bytes(args.checkpoint, 128_000), object_pairs_hook=_unique)
        receipt = json.loads(INPUT_LOADER.read_bounded_bytes(args.receipt, 128_000), object_pairs_hook=_unique)
        intake = json.loads(INPUT_LOADER.read_bounded_bytes(args.intake, 128_000), object_pairs_hook=_unique)
        write_screen_debrief_html(value, receipt, intake, args.output, checkpoint=checkpoint)
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    print(json.dumps({"artifact_kind": value["artifact_kind"], "schema_version": value["schema_version"], "ui_locale": value["locale"]}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
