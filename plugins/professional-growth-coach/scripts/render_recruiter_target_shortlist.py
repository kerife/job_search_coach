#!/usr/bin/env python3
"""Render a validated recruiter target shortlist as private offline HTML."""

from __future__ import annotations

import argparse
import html
import importlib.util
import os
import stat
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets"
TEMPLATE_PATH = ASSET_ROOT / "recruiter-target-shortlist-v1.html"
CSS_PATH = ASSET_ROOT / "recruiter-target-shortlist-v1.css"


def _load_validator() -> Any:
    path = Path(__file__).with_name("validate_recruiter_target_shortlist.py")
    spec = importlib.util.spec_from_file_location("recruiter_target_shortlist_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("shortlist validator is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()

COPY = {
    "es": {
        "title": "Objetivos de reclutamiento",
        "kicker": "Revisión privada de networking",
        "heading": "Shortlist de objetivos",
        "goal": "Objetivo de red",
        "segments": "Segmentos prioritarios",
        "queries": "Hipótesis de búsqueda manual",
        "batch": "Decisión del lote",
        "advance": "Avanzar a revisión de borrador",
        "clarify": "Aclarar contexto",
        "pause": "Pausar",
        "stop": "Detener",
        "score": "Prioridad contextual",
        "context": "Contexto disponible",
        "theme": "Tema objetivo",
        "reason": "Razón de decisión",
        "missing": "Falta resolver",
        "next": "Siguiente paso seguro",
        "do_not_contact": "No contactar todavía",
        "boundary": "No contactar todavía: este artefacto organiza investigación manual. No contiene contactos ni URLs, no envía mensajes, no conecta, no agenda y no promete una entrevista.",
        "no_save": "Guardado local deshabilitado.",
    },
    "en": {
        "title": "Recruiter target shortlist",
        "kicker": "Private networking review",
        "heading": "Target shortlist",
        "goal": "Network goal",
        "segments": "Priority segments",
        "queries": "Manual search hypotheses",
        "batch": "Batch decision",
        "advance": "Advance to draft review",
        "clarify": "Clarify context",
        "pause": "Pause",
        "stop": "Stop",
        "score": "Context priority",
        "context": "Available context",
        "theme": "Target theme",
        "reason": "Decision reason",
        "missing": "Resolve first",
        "next": "Safe next step",
        "do_not_contact": "Do not contact yet",
        "boundary": "Do not contact yet: this artifact organizes manual research. It contains no contact details or URLs, sends no messages, creates no connection, schedules nothing, and promises no interview.",
        "no_save": "Local saving is disabled.",
    },
}

DECISION_LABELS = {
    "es": {"advance": "Avanzar", "clarify": "Aclarar", "pause": "Pausar", "stop": "Detener"},
    "en": {"advance": "Advance", "clarify": "Clarify", "pause": "Pause", "stop": "Stop"},
}


def _target_card(target: Mapping[str, object], locale: str, index: int) -> str:
    labels = COPY[locale]
    decision = str(target["decision"])
    status = DECISION_LABELS[locale][decision]
    missing = str(target["missing_context"])
    if missing == "none":
        missing = labels["do_not_contact"] if decision != "advance" else "none"
    return f'''<article class="target-shortlist-card target-shortlist-card--{html.escape(decision)}" aria-labelledby="target-title-{index}">
      <p class="target-shortlist-index">{index}</p>
      <h2 id="target-title-{index}">{html.escape(str(target["target_label"]), quote=True)}</h2>
      <p class="target-shortlist-status"><strong>{html.escape(status)}</strong> · {labels["score"]}: {int(target["priority_score"])} / 100</p>
      <dl class="target-shortlist-facts">
        <div><dt>{html.escape(labels["context"])}</dt><dd>{html.escape(str(target["context_source"]), quote=True)}</dd></div>
        <div><dt>{html.escape(labels["theme"])}</dt><dd>{html.escape(str(target["target_theme"]), quote=True)}</dd></div>
        <div><dt>{html.escape(labels["reason"])}</dt><dd>{html.escape(str(target["decision_reason"]), quote=True)}</dd></div>
        <div><dt>{html.escape(labels["missing"])}</dt><dd>{html.escape(missing, quote=True)}</dd></div>
        <div><dt>{html.escape(labels["next"])}</dt><dd>{html.escape(str(target["next_safe_action"]), quote=True)}</dd></div>
      </dl>
    </article>'''


def render_shortlist_html(value: Mapping[str, object]) -> str:
    errors = VALIDATOR.validate_shortlist(value)
    if errors:
        raise ValueError("recruiter target shortlist validation failed")
    locale = str(value["locale"])
    labels = COPY[locale]
    plan = value["network_plan"]
    targets = value["targets"]
    target_cards = "".join(_target_card(target, locale, index) for index, target in enumerate(targets, start=1))
    queries = "".join(f"<li>{html.escape(str(query), quote=True)}</li>" for query in plan["source_queries"])
    segments = ", ".join(html.escape(str(segment), quote=True) for segment in plan["target_segments"])
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")
    replacements = {
        "{{LANG}}": locale,
        "{{TITLE}}": html.escape(labels["title"], quote=True),
        "{{KICKER}}": html.escape(labels["kicker"]),
        "{{HEADING}}": html.escape(labels["heading"]),
        "{{AS_OF_DATE}}": html.escape(str(value["as_of_date"]), quote=True),
        "{{GOAL_LABEL}}": html.escape(labels["goal"]),
        "{{GOAL}}": html.escape(str(plan["network_goal"]), quote=True),
        "{{SEGMENTS_LABEL}}": html.escape(labels["segments"]),
        "{{SEGMENTS}}": segments,
        "{{QUERIES_LABEL}}": html.escape(labels["queries"]),
        "{{QUERIES}}": queries,
        "{{BATCH_LABEL}}": html.escape(labels["batch"]),
        "{{BATCH}}": html.escape(DECISION_LABELS[locale][str(value["batch_decision"])]),
        "{{TARGETS}}": target_cards,
        "{{BOUNDARY}}": html.escape(labels["boundary"]),
        "{{NO_SAVE}}": html.escape(labels["no_save"]),
    }
    for key, replacement in replacements.items():
        template = template.replace(key, replacement)
    template = template.replace("{{INLINE_CSS}}", css)
    return template


def write_shortlist_html(value: Mapping[str, object], output: Path) -> None:
    output = output.resolve()
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(output, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            stream.write(render_shortlist_html(value))
    finally:
        if descriptor != -1:
            os.close(descriptor)
    os.chmod(output, stat.S_IRUSR | stat.S_IWUSR)


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a private recruiter target shortlist.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    try:
        import json
        raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
        write_shortlist_html(raw, args.output)
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    print("rendered recruiter target shortlist")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
