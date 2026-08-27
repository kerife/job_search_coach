#!/usr/bin/env python3
"""Render a private, bilingual recruiter target decision brief."""

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
ASSET_ROOT = ROOT / "assets"
TEMPLATE_PATH = ASSET_ROOT / "recruiter-target-decision-gate-v1.html"
CSS_PATH = ASSET_ROOT / "recruiter-target-decision-gate-v1.css"


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_gate_renderer_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("decision gate dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _sibling("validate_recruiter_target_decision_gate.py")
ASSET_LOADER = _sibling("private_asset_loader.py")
WRITER = _sibling("render_recruiter_target_shortlist.py")
INPUT_LOADER = _sibling("private_input_loader.py")


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result

COPY = {
    "es": {
        "title": "Gate de decisión de reclutamiento",
        "skip": "Saltar al brief de decisión",
        "kicker": "Brief privado de revisión manual",
        "heading": "Siguiente decisión",
        "date": "Fecha de referencia",
        "manual_pending": "Revisión manual pendiente",
        "collect": "Recopilar contexto de pantalla",
        "prepare": "Preparar entrevista para revisión",
        "next": "Siguiente paso seguro",
        "overview": "Resumen del lote",
        "target_count": "Objetivos",
        "counts": "Conteo por decisión",
        "priority": "Objetivo prioritario",
        "why": "Por qué ahora",
        "missing": "Qué falta para avanzar",
        "screen_missing": "Comparte un resumen de vacante y un hecho verificable antes de preparar la entrevista.",
        "screen_ready": "El contexto está recibido; la preparación de entrevista requiere revisión manual.",
        "rows": "Decisiones por objetivo",
        "reason": "Razón",
        "context": "Contexto faltante",
        "strategy": "Estrategia de primer contacto",
        "warmth": "Preparación de puente",
        "boundary": "Este gate decide qué merece revisión manual. No autoriza contacto, no transfiere contexto automáticamente y no predice una entrevista.",
        "footer": "Sin mensajes, conexiones, agenda ni respuestas guardadas.",
        "advance": "Avanzar",
        "clarify": "Aclarar",
        "pause": "Pausar",
        "stop": "Detener",
    },
    "en": {
        "title": "Recruiter target decision gate",
        "skip": "Skip to decision brief",
        "kicker": "Private manual-review brief",
        "heading": "Next decision",
        "date": "Reference date",
        "manual_pending": "Manual review pending",
        "collect": "Collect screen context",
        "prepare": "Prepare interview for review",
        "next": "Safe next step",
        "overview": "Batch summary",
        "target_count": "Targets",
        "counts": "Decision counts",
        "priority": "Priority target",
        "why": "Why now",
        "missing": "What is needed to advance",
        "screen_missing": "Provide a vacancy summary and one verifiable fact before preparing the interview.",
        "screen_ready": "Context is provided; interview preparation still requires manual review.",
        "rows": "Decisions by target",
        "reason": "Reason",
        "context": "Missing context",
        "strategy": "First-contact strategy",
        "warmth": "Bridge readiness",
        "boundary": "This gate decides what deserves manual review. It does not authorize contact, transfer context automatically, or predict an interview.",
        "footer": "No messages, connections, calendar actions, or saved answers.",
        "advance": "Advance",
        "clarify": "Clarify",
        "pause": "Pause",
        "stop": "Stop",
    },
}


def _row(row: Mapping[str, object], locale: str, index: int) -> str:
    labels = COPY[locale]
    decision = str(row["decision"])
    return f'''<li class="gate-row gate-row--{html.escape(decision)}">
      <div class="gate-row-heading"><span class="gate-row-index">{index}</span><h3>{html.escape(labels[decision])}</h3></div>
      <p class="gate-row-reason">{html.escape(str(row["decision_reason"]), quote=True)}</p>
      <dl class="gate-row-facts">
        <div><dt>{html.escape(labels["context"])}</dt><dd>{html.escape(str(row["missing_context"]), quote=True)}</dd></div>
        <div><dt>{html.escape(labels["strategy"])}</dt><dd>{html.escape(str(row["first_contact_strategy"]), quote=True)}</dd></div>
        <div><dt>{html.escape(labels["warmth"])}</dt><dd>{html.escape(str(row["warm_intro_readiness"]), quote=True)}</dd></div>
      </dl>
    </li>'''


def render_decision_gate_html(value: Mapping[str, object]) -> str:
    errors = VALIDATOR.validate_decision_gate(value, as_of=dt.date.today())
    if errors:
        raise ValueError("recruiter target decision gate validation failed")
    locale = str(value["locale"])
    labels = COPY[locale]
    source = value["source_shortlist"]
    source_targets = source["targets"]
    top = source_targets[0]
    handoff = value["handoff"]
    screen_present = value["screen_context"] is not None
    counts = value["decision_counts"]
    count_items = "".join(
        f'<li class="gate-count gate-count--{decision}"><strong>{html.escape(labels[decision])}</strong><span>{int(counts[decision])}</span></li>'
        for decision in ("advance", "clarify", "pause", "stop")
    )
    template = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, TEMPLATE_PATH)
    css = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, CSS_PATH)
    replacements = {
        "{{LANG}}": locale,
        "{{SKIP_LINK}}": html.escape(labels["skip"]),
        "{{TITLE}}": html.escape(labels["title"], quote=True),
        "{{KICKER}}": html.escape(labels["kicker"]),
        "{{HEADING}}": html.escape(labels["heading"]),
        "{{AS_OF_DATE}}": html.escape(str(value["as_of_date"]), quote=True),
        "{{DATE_LABEL}}": html.escape(labels["date"]),
        "{{NEXT_ACTION}}": html.escape(labels["prepare"] if screen_present else labels["collect"]),
        "{{NEXT_STATE}}": html.escape(labels["manual_pending"]),
        "{{OVERVIEW_LABEL}}": html.escape(labels["overview"]),
        "{{TARGET_COUNT_LABEL}}": html.escape(labels["target_count"]),
        "{{TARGET_COUNT}}": str(len(source_targets)),
        "{{COUNTS_LABEL}}": html.escape(labels["counts"]),
        "{{COUNTS}}": count_items,
        "{{PRIORITY_LABEL}}": html.escape(labels["priority"]),
        "{{PRIORITY}}": html.escape(str(top["target_label"]), quote=True),
        "{{WHY_LABEL}}": html.escape(labels["why"]),
        "{{WHY}}": html.escape(str(top["decision_reason"]), quote=True),
        "{{MISSING_LABEL}}": html.escape(labels["missing"]),
        "{{MISSING}}": html.escape(labels["screen_ready"] if screen_present else labels["screen_missing"]),
        "{{ROWS_LABEL}}": html.escape(labels["rows"]),
        "{{ROWS}}": "".join(_row(row, locale, index) for index, row in enumerate(value["decision_rows"], start=1)),
        "{{BOUNDARY}}": html.escape(labels["boundary"]),
        "{{FOOTER}}": html.escape(labels["footer"]),
        "{{INLINE_CSS}}": css,
    }
    for key, replacement in replacements.items():
        template = template.replace(key, replacement)
    return template


def write_decision_gate_html(value: Mapping[str, object], output: Path) -> None:
    WRITER._atomic_private_write(output, render_decision_gate_html(value).encode("utf-8"))


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a private recruiter target decision gate.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    try:
        args = parser.parse_args(argv)
        value = json.loads(
            INPUT_LOADER.read_bounded_bytes(args.input, 128_000),
            object_pairs_hook=lambda pairs: _unique(pairs),
        )
        write_decision_gate_html(value, args.output)
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    print("rendered recruiter target decision gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
