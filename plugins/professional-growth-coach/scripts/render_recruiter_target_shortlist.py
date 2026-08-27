#!/usr/bin/env python3
"""Render a validated recruiter target shortlist as private offline HTML."""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import os
import secrets
import stat
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets"
TEMPLATE_PATH = ASSET_ROOT / "recruiter-target-shortlist-v1.html"
CSS_PATH = ASSET_ROOT / "recruiter-target-shortlist-v1.css"


def _load_loader() -> Any:
    path = Path(__file__).with_name("private_input_loader.py")
    spec = importlib.util.spec_from_file_location("recruiter_target_shortlist_loader", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("shortlist input loader is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LOADER = _load_loader()


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
        "count": "Conteo por decisión",
        "priority": "Primera prioridad",
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
        "count": "Decision counts",
        "priority": "Top priority",
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
    action_labels = {"es": {"draft_only_review": "Revisar borrador", "collect_recipient_context": "Recopilar contexto", "record_observation_only": "Registrar observación"}, "en": {"draft_only_review": "Review draft", "collect_recipient_context": "Collect context", "record_observation_only": "Record observation"}}
    return f'''<article class="target-shortlist-card target-shortlist-card--{html.escape(decision)}" aria-labelledby="target-title-{index}">
      <p class="target-shortlist-index">{index}</p>
      <h2 id="target-title-{index}">{html.escape(str(target["target_label"]), quote=True)}</h2>
      <p class="target-shortlist-status"><strong>{html.escape(status)}</strong> · {labels["score"]}: {int(target["priority_score"])} / 100</p>
      <dl class="target-shortlist-facts">
        <div><dt>{html.escape(labels["context"])}</dt><dd>{html.escape(str(target["context_source"]), quote=True)}</dd></div>
        <div><dt>{html.escape(labels["theme"])}</dt><dd>{html.escape(str(target["target_theme"]), quote=True)}</dd></div>
        <div><dt>{html.escape(labels["reason"])}</dt><dd>{html.escape(str(target["decision_reason"]), quote=True)}</dd></div>
        <div><dt>{html.escape(labels["missing"])}</dt><dd>{html.escape(missing, quote=True)}</dd></div>
        <div><dt>{html.escape(labels["next"])}</dt><dd>{html.escape(action_labels[locale][str(target["next_safe_action"])] , quote=True)}</dd></div>
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
    counts = {decision: sum(1 for target in targets if target["decision"] == decision) for decision in ("advance", "clarify", "pause", "stop")}
    count_labels = {"es": {"advance": "Avanzar", "clarify": "Aclarar", "pause": "Pausar", "stop": "Detener"}, "en": {"advance": "Advance", "clarify": "Clarify", "pause": "Pause", "stop": "Stop"}}[locale]
    decision_counts = "".join(f'<li class="shortlist-decision-count shortlist-decision-count--{decision}"><strong>{html.escape(count_labels[decision])}</strong><span>{counts[decision]}</span></li>' for decision in counts)
    top_target = targets[0]
    priority = f'<p class="shortlist-priority-label">{html.escape(labels["priority"])}</p><p class="shortlist-priority-value">{html.escape(str(top_target["target_label"]), quote=True)}</p>'
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
        "{{COUNT_LABEL}}": html.escape(labels["count"]),
        "{{DECISION_COUNTS}}": decision_counts,
        "{{PRIORITY}}": priority,
        "{{TARGETS}}": target_cards,
        "{{BOUNDARY}}": html.escape(labels["boundary"]),
        "{{NO_SAVE}}": html.escape(labels["no_save"]),
    }
    for key, replacement in replacements.items():
        template = template.replace(key, replacement)
    template = template.replace("{{INLINE_CSS}}", css)
    return template


def _open_private_parent(parent: Path) -> int:
    if not parent.is_absolute() or parent.anchor != os.sep:
        raise OSError("output parent must be absolute")
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(os.sep, os.O_RDONLY | directory_flag)
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
            alias = index == 0 and component in {"tmp", "var"} and os.path.islink(os.path.join(os.sep, component)) and os.path.realpath(os.path.join(os.sep, component)) == os.path.join(os.sep, "private", component)
            next_descriptor = os.open(component, os.O_RDONLY | directory_flag | (0 if alias else no_follow), dir_fd=descriptor)
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


def _atomic_private_write(output: Path, content: bytes) -> None:
    output = Path(os.path.abspath(os.fspath(output)))
    parent = _open_private_parent(output.parent)
    temp_name: str | None = None
    descriptor: int | None = None
    try:
        try:
            existing = os.stat(output.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None:
            if stat.S_ISLNK(existing.st_mode):
                raise OSError("output target is a symbolic link")
            if not stat.S_ISREG(existing.st_mode):
                raise OSError("output target is not a regular file")
            raise FileExistsError("output already exists")
        for _ in range(100):
            candidate = f".{output.name}.tmp-{secrets.token_hex(8)}"
            try:
                descriptor = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=parent)
                temp_name = candidate
                break
            except FileExistsError:
                continue
        if descriptor is None or temp_name is None:
            raise OSError("cannot create private temporary artifact")
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            os.fchmod(stream.fileno(), 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp_name, output.name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
        os.unlink(temp_name, dir_fd=parent)
        temp_name = None
        os.fsync(parent)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temp_name:
            try:
                os.unlink(temp_name, dir_fd=parent)
            except FileNotFoundError:
                pass
        os.close(parent)


def write_shortlist_html(value: Mapping[str, object], output: Path) -> None:
    _atomic_private_write(output, render_shortlist_html(value).encode("utf-8"))


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a private recruiter target shortlist.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    try:
        def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
            result: dict[str, object] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate JSON key")
                result[key] = value
            return result
        raw = json.loads(LOADER.read_bounded_bytes(args.input, 64_000), object_pairs_hook=_unique)
        write_shortlist_html(raw, args.output)
    except Exception:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    print("rendered recruiter target shortlist")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
