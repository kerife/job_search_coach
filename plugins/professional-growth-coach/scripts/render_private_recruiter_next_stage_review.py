#!/usr/bin/env python3
"""Render a private bilingual next-stage review without identifiers or raw notes."""

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
TEMPLATE = ROOT / "assets" / "private-recruiter-next-stage-review-v1.html"
CSS = ROOT / "assets" / "private-recruiter-next-stage-review-v1.css"


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_next_stage_renderer_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("next-stage dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _sibling("validate_private_recruiter_next_stage_review.py")
LOADER = _sibling("private_asset_loader.py")
INPUT_LOADER = _sibling("private_input_loader.py")
WRITER = _sibling("render_private_recruiter_followthrough_checkpoint.py")
CONTINUITY_RAIL = _sibling("recruiter_continuity_rail.py")


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise ValueError("invalid arguments")


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError("duplicate json key")
        output[key] = value
    return output


COPY = {
    "es": {"title": "Revisión de la siguiente etapa", "skip": "Ir a la revisión", "kicker": "Preparación privada posterior al filtro", "heading": "¿Está lista la siguiente conversación?", "current_stage_label": "Etapa actual", "stage_label": "Etapa objetivo", "blocked_guidance": "Aclara estos temas antes de continuar", "date": "Fecha observada", "stage": {"recruiter_screen": "Filtro de reclutamiento", "first_interview": "Primera entrevista", "technical_screen": "Filtro técnico", "hiring_manager": "Entrevista con hiring manager", "technical_deep_dive": "Profundización técnica", "take_home": "Ejercicio para casa", "system_design": "System design", "behavioral_loop": "Ronda conductual", "panel": "Panel", "offer_stage": "Etapa de oferta"}, "topics": {"requirement": "Requisitos", "scope": "Alcance y éxito", "team_context": "Contexto del equipo"}, "state": {"ready": "Lista para revisión manual", "blocked": "Bloqueada hasta aclarar"}, "owner": "Responsable", "owner_value": "Candidato con revisión del coach", "checklist": "Lista de cobertura", "covered": "Cubierto", "needs_clarification": "Requiere aclaración", "next": "Siguiente paso seguro", "action": {"manual_prepare_next_stage_review": "Preparar la siguiente etapa para revisión manual", "collect_debrief_context": "Recopilar contexto del debrief", "record_stop_decision": "Registrar la decisión de detenerse"}, "boundary": "Esta revisión organiza la preparación privada. No conserva respuestas crudas, no contacta, no agenda y no predice resultados.", "footer": "Revisión manual requerida · sin mensajes · sin calendario"},
    "en": {"title": "Next-stage review", "skip": "Skip to review", "kicker": "Private post-screen preparation", "heading": "Is the next conversation ready?", "current_stage_label": "Current stage", "stage_label": "Target stage", "blocked_guidance": "Clarify these topics before continuing", "date": "Observed date", "stage": {"recruiter_screen": "Recruiter screen", "first_interview": "First interview", "technical_screen": "Technical screen", "hiring_manager": "Hiring manager interview", "technical_deep_dive": "Technical deep dive", "take_home": "Take-home exercise", "system_design": "System design", "behavioral_loop": "Behavioral loop", "panel": "Panel", "offer_stage": "Offer stage"}, "topics": {"requirement": "Requirements", "scope": "Scope and success", "team_context": "Team context"}, "state": {"ready": "Ready for manual review", "blocked": "Blocked until clarified"}, "owner": "Owner", "owner_value": "Candidate with coach review", "checklist": "Coverage checklist", "covered": "Covered", "needs_clarification": "Needs clarification", "next": "Safe next step", "action": {"manual_prepare_next_stage_review": "Prepare the next stage for manual review", "collect_debrief_context": "Collect debrief context", "record_stop_decision": "Record the stop decision"}, "boundary": "This review organizes private preparation. It keeps no raw answers, contacts, calendars, or outcome predictions.", "footer": "Manual review required · no messages · no calendar"},
}


def render_next_stage_review_html(value: Mapping[str, object], debrief: Mapping[str, object], receipt: Mapping[str, object], intake: Mapping[str, object], checkpoint: Mapping[str, object]) -> str:
    errors = VALIDATOR.validate_next_stage_review(value, debrief, receipt, intake, checkpoint, as_of=dt.date.today())
    if errors:
        raise ValueError("private next-stage review validation failed")
    labels = COPY[str(value["locale"])]
    source_context = intake.get("intake") if isinstance(intake.get("intake"), Mapping) else {}
    current_stage = str(source_context.get("stated_stage"))
    flow_label, flow_rail = CONTINUITY_RAIL.render_continuity_rail(str(value["locale"]), "next_stage")
    rows = "".join(f'<li class="next-stage-check next-stage-check--{html.escape(str(row["status"]))}"><strong>{html.escape(labels["topics"].get(str(row["topic"]), ""))}</strong><span>{html.escape(labels[str(row["status"])])}</span></li>' for row in value["checklist"])
    unclear = [labels["topics"][str(row["topic"])] for row in value["checklist"] if row["status"] == "needs_clarification"]
    guidance = ""
    if unclear:
        items = "".join(f"<li>{html.escape(topic)}</li>" for topic in unclear)
        guidance = f'<aside class="next-stage-guidance" role="note"><strong>{html.escape(labels["blocked_guidance"])}</strong><ul>{items}</ul></aside>'
    summary_class = "next-stage-summary next-stage-summary--blocked" if value["review_state"] == "blocked" else "next-stage-summary"
    template = LOADER.read_private_asset(ROOT, TEMPLATE)
    css = LOADER.read_private_asset(ROOT, CSS)
    replacements = {"{{LANG}}": html.escape(str(value["locale"])), "{{TITLE}}": html.escape(labels["title"], quote=True), "{{SKIP}}": html.escape(labels["skip"]), "{{KICKER}}": html.escape(labels["kicker"]), "{{HEADING}}": html.escape(labels["heading"]), "{{CURRENT_STAGE_LABEL}}": html.escape(labels["current_stage_label"]), "{{CURRENT_STAGE}}": html.escape(labels["stage"][current_stage]), "{{STAGE_LABEL}}": html.escape(labels["stage_label"]), "{{STAGE}}": html.escape(labels["stage"][str(value["next_stage"])]), "{{DATE_LABEL}}": html.escape(labels["date"]), "{{DATE}}": html.escape(str(value["observed_date"]), quote=True), "{{STATE}}": html.escape(labels["state"][str(value["review_state"])]), "{{SUMMARY_CLASS}}": summary_class, "{{BLOCKED_GUIDANCE}}": guidance, "{{OWNER_LABEL}}": html.escape(labels["owner"]), "{{OWNER}}": html.escape(labels["owner_value"]), "{{CHECKLIST_LABEL}}": html.escape(labels["checklist"]), "{{CHECKLIST}}": rows, "{{NEXT_LABEL}}": html.escape(labels["next"]), "{{ACTION}}": html.escape(labels["action"][str(value["handoff"]["next_safe_action"])]), "{{BOUNDARY}}": html.escape(labels["boundary"]), "{{FOOTER}}": html.escape(labels["footer"]), "{{INLINE_CSS}}": css, "{{FLOW_RAIL_LABEL}}": html.escape(flow_label), "{{FLOW_RAIL}}": flow_rail}
    for key, replacement in replacements.items():
        template = template.replace(key, replacement)
    return template


def write_next_stage_review_html(value: Mapping[str, object], debrief: Mapping[str, object], receipt: Mapping[str, object], intake: Mapping[str, object], checkpoint: Mapping[str, object], output: Path) -> None:
    WRITER._atomic_private_write(output, render_next_stage_review_html(value, debrief, receipt, intake, checkpoint).encode("utf-8"))


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Render a private next-stage review.")
    parser.add_argument("input", type=Path); parser.add_argument("--debrief", type=Path, required=True); parser.add_argument("--receipt", type=Path, required=True); parser.add_argument("--intake", type=Path, required=True); parser.add_argument("--checkpoint", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    try:
        args = parser.parse_args(argv); read = lambda path: json.loads(INPUT_LOADER.read_bounded_bytes(path, 128_000), object_pairs_hook=_unique)
        value = read(args.input)
        write_next_stage_review_html(value, read(args.debrief), read(args.receipt), read(args.intake), read(args.checkpoint), args.output)
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr); return 3
    print(json.dumps({"artifact_kind": value["artifact_kind"], "schema_version": value["schema_version"], "ui_locale": value["locale"]}, separators=(",", ":"))); return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
