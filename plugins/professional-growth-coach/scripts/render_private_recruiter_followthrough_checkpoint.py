#!/usr/bin/env python3
"""Render a validated, candidate-supplied follow-through checkpoint offline."""
from __future__ import annotations

import argparse
import datetime as dt
import html
import importlib.util
import json
import os
import re
import secrets
import stat
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
TEMPLATE_PATH = ASSET_ROOT / "private-recruiter-followthrough-checkpoint-v1.html"
CSS_PATH = ASSET_ROOT / "private-recruiter-followthrough-checkpoint-v1.css"


def _load_asset_loader() -> Any:
    path = Path(__file__).with_name("private_asset_loader.py")
    specification = importlib.util.spec_from_file_location("private_renderer_asset_loader", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("private renderer asset loader is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


ASSET_LOADER = _load_asset_loader()

LABELS = {
    "en": {
        "title": "Private recruiter follow-through checkpoint", "skip": "Skip to checkpoint",
        "kicker": "Private candidate checkpoint", "heading": "Recruiter follow-through checkpoint",
        "state": "Action state", "event": "Next measurement event", "date": "Observed date", "action": "Safe next step",
        "boundary": "Candidate-supplied checkpoint only. No external action was taken.", "employment_boundary": "This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.", "save": "Local saving is disabled.",
        "manual_next_step_heading": "Manual next step", "manual_next_step_body": "Return to the private Codex conversation and re-enter preparation manually to review the reported request. This receipt does not contact, send, or schedule anything.",
        "states": {"accepted": "Accepted", "deferred": "Deferred", "declined": "Declined", "completed": "Completed"},
        "events": {"screen_prepared": "Screen prepared", "screen_attended": "Screen attended", "interview_requested": "Interview request observed", "stop_decision": "Stop decision", "unknown": "Not specified"},
        "actions": {"manual_reenter_private_prep": "Re-enter private preparation manually", "clarify_context_before_reply": "Clarify context before replying", "debrief_after_screen": "Debrief the screen privately", "record_stop_decision": "Record the stop decision", "route_to_prepare-role-interviews": "Route to interview preparation"},
    },
    "es": {
        "title": "Punto de control privado de seguimiento del reclutador", "skip": "Ir al punto de control",
        "kicker": "Punto de control privado reportado por la persona", "heading": "Seguimiento del reclutador",
        "state": "Estado de acción", "event": "Siguiente evento de medición", "date": "Fecha observada", "action": "Siguiente paso seguro",
        "boundary": "Solo punto de control reportado por la persona. No se realizó ninguna acción externa.", "employment_boundary": "Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.", "save": "El guardado local está deshabilitado.",
        "manual_next_step_heading": "Siguiente paso manual", "manual_next_step_body": "Regresa a la conversación privada de Codex y vuelve a entrar manualmente a la preparación para revisar la solicitud reportada. Este recibo no contacta, envía ni agenda nada.",
        "states": {"accepted": "Aceptado", "deferred": "Pospuesto", "declined": "Rechazado", "completed": "Completado"},
        "events": {"screen_prepared": "Filtro preparado", "screen_attended": "Filtro atendido", "interview_requested": "Solicitud de entrevista observada", "stop_decision": "Decisión de detenerse", "unknown": "No especificado"},
        "actions": {"manual_reenter_private_prep": "Reingresa manualmente a la preparación privada", "clarify_context_before_reply": "Aclara el contexto antes de responder", "debrief_after_screen": "Haz un debrief privado del filtro", "record_stop_decision": "Registra la decisión de detenerse", "route_to_prepare-role-interviews": "Dirige a preparación de entrevista"},
    },
}

STOP_COPY = {
    "en": {
        "action": "Record this recruiter-process outcome privately.",
        "boundary": "Scope: this records one recruiter-process outcome only. It is not advice to resign, leave a job, or stop your job search; you decide what comes next.",
    },
    "es": {
        "action": "Registra en privado el resultado de este proceso de reclutamiento.",
        "boundary": "Alcance: esto solo registra un resultado de este proceso de reclutamiento. No es una recomendación de renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
    },
}

ACTION_RAIL_COPY = {
    "en": {
        "manual_reenter_private_prep": {
            "title": "Re-enter private preparation",
            "kicker": "Manual preparation route",
            "steps": (("receipt", "current", "Receipt", "The supplied checkpoint is recorded."), ("safe-step", "current", "Private preparation", "Re-enter private preparation manually."), ("review", "blocked", "Manual review", "Review the private preparation before any next step.")),
        },
        "clarify_context_before_reply": {
            "title": "Clarify context before replying",
            "kicker": "Safe clarification route",
            "steps": (("receipt", "current", "Receipt", "The supplied checkpoint is recorded."), ("safe-step", "current", "Clarify context", "Clarify only the missing context before replying."), ("review", "blocked", "Manual review", "Re-enter the private conversation manually before replying.")),
        },
        "debrief_after_screen": {
            "title": "Debrief the screen privately",
            "kicker": "Manual debrief route",
            "steps": (("receipt", "current", "Receipt", "The supplied checkpoint is recorded."), ("safe-step", "current", "Debrief", "Record what was discussed and what remains unknown, privately."), ("review", "blocked", "Manual review", "Review the debrief before any follow-up.")),
        },
        "route_to_prepare-role-interviews": {
            "title": "Route to private preparation",
            "kicker": "Safe preparation route",
            "steps": (("receipt", "current", "Receipt", "The supplied checkpoint is recorded."), ("safe-step", "current", "Preparation", "Re-enter private preparation manually to review the reported next step."), ("review", "blocked", "Manual review", "Review the preparation privately before any next step.")),
        },
        "record_stop_decision": {
            "title": "Outcome recorded",
            "kicker": "Terminal record",
            "steps": (("record", "recorded", "Outcome recorded", "The recruiter-process outcome is recorded privately."),),
        },
    },
    "es": {
        "manual_reenter_private_prep": {
            "title": "Vuelve a entrar a la preparación privada",
            "kicker": "Ruta manual de preparación",
            "steps": (("receipt", "current", "Recibo", "El punto de control reportado queda registrado."), ("safe-step", "current", "Preparación privada", "Vuelve a entrar manualmente a la preparación privada."), ("review", "blocked", "Revisión manual", "Revisa la preparación privada antes de cualquier siguiente paso.")),
        },
        "clarify_context_before_reply": {
            "title": "Aclara el contexto antes de responder",
            "kicker": "Ruta segura de aclaración",
            "steps": (("receipt", "current", "Recibo", "El punto de control reportado queda registrado."), ("safe-step", "current", "Aclaración", "Aclara solo el contexto faltante antes de responder."), ("review", "blocked", "Revisión manual", "Vuelve a entrar manualmente a la conversación privada antes de responder.")),
        },
        "debrief_after_screen": {
            "title": "Haz un debrief privado del filtro",
            "kicker": "Ruta manual de debrief",
            "steps": (("receipt", "current", "Recibo", "El punto de control reportado queda registrado."), ("safe-step", "current", "Debrief", "Registra en privado lo que se habló y lo que sigue desconocido."), ("review", "blocked", "Revisión manual", "Revisa el debrief antes de cualquier seguimiento.")),
        },
        "route_to_prepare-role-interviews": {
            "title": "Dirige a preparación privada",
            "kicker": "Ruta segura de preparación",
            "steps": (("receipt", "current", "Recibo", "El punto de control reportado queda registrado."), ("safe-step", "current", "Preparación", "Vuelve a entrar manualmente a la preparación para revisar el siguiente paso reportado."), ("review", "blocked", "Revisión manual", "Revisa la preparación en privado antes de cualquier siguiente paso.")),
        },
        "record_stop_decision": {
            "title": "Resultado registrado",
            "kicker": "Registro terminal",
            "steps": (("record", "recorded", "Resultado registrado", "El resultado del proceso de reclutamiento queda registrado en privado."),),
        },
    },
}

RAIL_STATES = {"en": {"current": "Current", "blocked": "Blocked", "recorded": "Recorded"}, "es": {"current": "Actual", "blocked": "Bloqueada", "recorded": "Registrado"}}

class CheckpointRenderValidationError(ValueError):
    def __init__(self, errors: Sequence[str]):
        self.errors = tuple(errors)
        super().__init__("private recruiter checkpoint validation failed")


class _ArgumentError(ValueError):
    pass


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise _ArgumentError

def _load_validator() -> Any:
    path = Path(__file__).with_name("validate_private_recruiter_followthrough_checkpoint.py")
    spec = importlib.util.spec_from_file_location("followthrough_checkpoint_validator", path)
    if spec is None or spec.loader is None: raise RuntimeError("checkpoint validator unavailable")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

VALIDATOR = _load_validator()


def _action_rail(locale: str, action: str, *, terminal: bool = False) -> str:
    labels = ACTION_RAIL_COPY[locale][action]
    steps = "".join(
        f'<li class="continuity-step continuity-step--{state}" data-stage="{stage}" data-state="{state}">'
        f'<span class="continuity-step-state">{RAIL_STATES[locale][state]}</span>'
        f'<strong>{html.escape(title)}</strong><p>{html.escape(description)}</p></li>'
        for stage, state, title, description in labels["steps"]
    )
    terminal_attribute = ' data-terminal="true"' if terminal else ''
    return (
        f'<section class="continuity-rail" aria-labelledby="continuity-rail-title"{terminal_attribute}>'
        f'<p class="continuity-rail-kicker">{html.escape(labels["kicker"])}</p>'
        f'<h2 id="continuity-rail-title">{html.escape(labels["title"])}</h2>'
        f'<ol class="continuity-rail-list">{steps}</ol></section>'
    )


def _terminal_rail(locale: str) -> str:
    return _action_rail(locale, "record_stop_decision", terminal=True)

def _validated(item: Mapping[str, object], receipt: Mapping[str, object], *, as_of: dt.date | None) -> Mapping[str, object]:
    errors = VALIDATOR.validate_checkpoint(item, receipt, as_of=as_of)
    if errors: raise CheckpointRenderValidationError(errors)
    return item

def render_checkpoint_html(item: Mapping[str, object], receipt: Mapping[str, object], *, as_of: dt.date | None = None) -> str:
    value = _validated(item, receipt, as_of=as_of)
    locale = value["locale"]
    labels = LABELS[locale]
    action = value["next_safe_action"]
    is_stop = action == "record_stop_decision"
    stop_copy = STOP_COPY[locale] if is_stop else None
    manual_next_step = _terminal_rail(locale) if is_stop else _action_rail(locale, action)
    if action == "route_to_prepare-role-interviews":
        manual_next_step += (
            '<section class="checkpoint-manual-next-step" '
            'aria-labelledby="checkpoint-manual-next-step-heading">'
            f'<h2 id="checkpoint-manual-next-step-heading">{html.escape(labels["manual_next_step_heading"])}</h2>'
            f'<p>{html.escape(labels["manual_next_step_body"])}</p></section>'
        )
    template = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, TEMPLATE_PATH)
    css = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, CSS_PATH)
    replacements = {
        "{{LANG}}": html.escape(locale), "{{TITLE}}": labels["title"], "{{INLINE_CSS}}": css,
        "{{SKIP}}": labels["skip"], "{{KICKER}}": labels["kicker"], "{{HEADING}}": labels["heading"],
        "{{STATE_LABEL}}": labels["state"], "{{STATE}}": labels["states"][value["action_state"]],
        "{{EVENT_LABEL}}": labels["event"], "{{EVENT}}": labels["events"][value["next_measurement_event"]],
        "{{DATE_LABEL}}": labels["date"], "{{DATE}}": html.escape(value["observed_date"]),
        "{{ACTION_LABEL}}": labels["action"], "{{ACTION}}": stop_copy["action"] if stop_copy else labels["actions"][value["next_safe_action"]],
        "{{BOUNDARY}}": stop_copy["boundary"] if stop_copy else labels["boundary"], "{{MANUAL_NEXT_STEP}}": manual_next_step, "{{EMPLOYMENT_BOUNDARY}}": "" if stop_copy else f'<p class="checkpoint-employment-boundary">{labels["employment_boundary"]}</p>', "{{SAVE}}": labels["save"],
    }
    for token, replacement in replacements.items(): template = template.replace(token, replacement)
    if re.search(r"\{\{[A-Z_]+\}\}", template): raise RuntimeError("checkpoint template token contract is invalid")
    return template

def _open_private_parent(parent: Path) -> int:
    if not parent.is_absolute() or parent.anchor != os.sep: raise OSError("output parent must be absolute")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0); descriptor = os.open(os.sep, flags)
    try:
        for index, component in enumerate(parent.parts[1:]):
            if component in {"", ".", ".."}: raise OSError("output parent is unsafe")
            try: os.mkdir(component, 0o700, dir_fd=descriptor); created = True
            except FileExistsError: created = False
            alias = index == 0 and component in {"tmp", "var"} and os.path.islink(os.path.join(os.sep, component)) and os.path.realpath(os.path.join(os.sep, component)) == os.path.join(os.sep, "private", component)
            next_descriptor = os.open(component, flags | (0 if alias else getattr(os, "O_NOFOLLOW", 0)), dir_fd=descriptor)
            if not stat.S_ISDIR(os.fstat(next_descriptor).st_mode): os.close(next_descriptor); raise OSError("output parent is not a directory")
            if created: os.fchmod(next_descriptor, 0o700)
            os.close(descriptor); descriptor = next_descriptor
        return descriptor
    except BaseException: os.close(descriptor); raise

def _atomic_private_write(output: Path, content: bytes, *, force: bool = False) -> None:
    parent = _open_private_parent(output.parent); temp = None; descriptor = None
    try:
        try: status = os.stat(output.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError: status = None
        if status is not None:
            if stat.S_ISLNK(status.st_mode): raise OSError("output target is a symbolic link")
            if not stat.S_ISREG(status.st_mode): raise OSError("output target is not a regular file")
            if not force: raise FileExistsError("output already exists")
        for _ in range(100):
            candidate = f".{output.name}.tmp-{secrets.token_hex(8)}"
            try: descriptor = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=parent); temp = candidate; break
            except FileExistsError: continue
        if temp is None or descriptor is None: raise OSError("cannot create private temporary artifact")
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None; os.fchmod(stream.fileno(), 0o600); stream.write(content); stream.flush(); os.fsync(stream.fileno())
        if force: os.replace(temp, output.name, src_dir_fd=parent, dst_dir_fd=parent)
        else: os.link(temp, output.name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False); os.unlink(temp, dir_fd=parent)
        temp = None; os.fsync(parent)
    finally:
        if descriptor is not None: os.close(descriptor)
        if temp:
            try: os.unlink(temp, dir_fd=parent)
            except FileNotFoundError: pass
        os.close(parent)

def write_checkpoint_html(item: Mapping[str, object], receipt: Mapping[str, object], output: Path, *, as_of: dt.date | None = None, force: bool = False):
    rendered = render_checkpoint_html(item, receipt, as_of=as_of)
    target = Path(os.path.abspath(os.fspath(output)))
    _atomic_private_write(target, rendered.encode("utf-8"), force=force)
    return type("RenderReceipt", (), {"artifact_path": target, "artifact_type": "text/html", "locale": item["locale"]})()

def _date_arg(value: str) -> dt.date:
    try: return dt.date.fromisoformat(value)
    except ValueError as error: raise argparse.ArgumentTypeError("must use YYYY-MM-DD") from error

def _cli(argv=None) -> int:
    parser = _PrivateArgumentParser(description="Render a private recruiter follow-through checkpoint.")
    parser.add_argument("input", type=Path); parser.add_argument("--receipt", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--force", action="store_true"); parser.add_argument("--include-artifact-path", action="store_true", help="include the local output path in the CLI receipt"); parser.add_argument("--as-of", type=_date_arg, required=True)
    try:
        args = parser.parse_args(argv); item = VALIDATOR.load_checkpoint(args.input); receipt = VALIDATOR.load_receipt(args.receipt); result = write_checkpoint_html(item, receipt, args.output, as_of=args.as_of, force=args.force)
    except _ArgumentError:
        print(json.dumps({"error": {"code": "invalid_arguments"}}, separators=(",", ":")), file=sys.stderr)
        return 3
    except SystemExit as error: return 0 if error.code == 0 else 3
    except (OSError, VALIDATOR.CheckpointLoadError): print("cannot render private recruiter checkpoint", file=sys.stderr); return 3
    except CheckpointRenderValidationError as error: print("\n".join(error.errors), file=sys.stderr); return 2
    payload = {"artifact_type": result.artifact_type, "locale": result.locale}
    if args.include_artifact_path:
        payload["artifact_path"] = str(result.artifact_path)
    print(json.dumps(payload, separators=(",", ":"))); return 0

if __name__ == "__main__": raise SystemExit(_cli())
