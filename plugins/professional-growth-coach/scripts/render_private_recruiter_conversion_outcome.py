#!/usr/bin/env python3
"""Render a validator-approved recruiter conversion outcome as offline HTML."""
from __future__ import annotations

import argparse, datetime as dt, html, importlib.util, json, os, re, secrets, stat, sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
TEMPLATE_PATH = ASSET_ROOT / "private-recruiter-conversion-outcome-v1.html"
CSS_PATH = ASSET_ROOT / "private-recruiter-conversion-outcome-v1.css"


def _load_asset_loader() -> Any:
    path = Path(__file__).with_name("private_asset_loader.py")
    specification = importlib.util.spec_from_file_location("private_renderer_asset_loader", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("private renderer asset loader is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


ASSET_LOADER = _load_asset_loader()

EVENT_LABELS = {
    "en": {"contact_received": "Contact received", "reply_received": "Reply received", "referral_received": "Referral received", "screen_requested": "Screen requested", "interview_requested": "Interview request observed", "stop_decision": "Stop decision"},
    "es": {"contact_received": "Recibimos un contacto", "reply_received": "Recibimos una respuesta", "referral_received": "Recibimos una referencia", "screen_requested": "Solicitaron un filtro", "interview_requested": "Solicitud de entrevista observada", "stop_decision": "Decisión de detenerse"},
}
ACTION_LABELS = {
    "en": {"clarify_context_before_reply": "Clarify context before replying", "prepare_fact_checked_summary": "Prepare a fact-checked summary", "route_to_prepare-role-interviews": "Route to interview preparation", "record_stop_decision": "Record the stop decision"},
    "es": {"clarify_context_before_reply": "Aclara el contexto antes de responder", "prepare_fact_checked_summary": "Prepara un resumen verificado", "route_to_prepare-role-interviews": "Dirige a preparación de entrevista", "record_stop_decision": "Registra la decisión de detenerse"},
}
COPY = {
    "en": {
        "title": "Private recruiter outcome receipt", "skip": "Skip to main content",
        "kicker": "Private observation receipt", "heading": "Recruiter conversion outcome",
        "event": "Observed event", "date": "Event date", "action": "Safe next step",
        "evidence": "Evidence count", "boundary": "Candidate-supplied observation only. No external action was taken.",
        "manual_next_step_heading": "Manual next step",
        "manual_next_step_body": "Return to the private Codex conversation and re-enter preparation manually to review the reported request. This receipt does not contact, send, or schedule anything.",
        "employment_boundary": "This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.",
        "save": "Local saving is disabled.",
    },
    "es": {
        "title": "Recibo privado de resultado del reclutador", "skip": "Saltar al contenido principal",
        "kicker": "Recibo privado de observación", "heading": "Resultado de conversión del reclutador",
        "event": "Evento observado", "date": "Fecha del evento", "action": "Siguiente paso seguro",
        "evidence": "Evidencia", "boundary": "Solo observación reportada por la persona. No se realizó ninguna acción externa.",
        "manual_next_step_heading": "Siguiente paso manual",
        "manual_next_step_body": "Regresa a la conversación privada de Codex y vuelve a entrar manualmente a la preparación para revisar la solicitud reportada. Este recibo no contacta, envía ni agenda nada.",
        "employment_boundary": "Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
        "save": "El guardado local está deshabilitado.",
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
        "clarify_context_before_reply": {
            "title": "Clarify context before replying",
            "kicker": "Safe clarification route",
            "steps": (
                ("observation", "recorded", "Observation", "The supplied observation is recorded."),
                ("safe-step", "pending", "Clarify context", "Clarify only the missing context before replying."),
                ("review", "blocked", "Manual review", "Re-enter the private conversation manually before replying."),
            ),
        },
        "prepare_fact_checked_summary": {
            "title": "Prepare a fact-checked summary",
            "kicker": "Safe preparation route",
            "steps": (
                ("observation", "recorded", "Observation", "The supplied observation is recorded."),
                ("safe-step", "pending", "Fact check", "Prepare a fact-checked summary from supplied facts only."),
                ("review", "blocked", "Manual review", "Review the summary privately before any next step."),
            ),
        },
        "route_to_prepare-role-interviews": {
            "title": "Route to private preparation",
            "kicker": "Safe preparation route",
            "steps": (
                ("observation", "recorded", "Observation", "The supplied observation is recorded."),
                ("safe-step", "pending", "Preparation", "Re-enter private preparation manually to review the reported next step."),
                ("review", "blocked", "Manual review", "Review the preparation privately before any next step."),
            ),
        },
        "record_stop_decision": {
            "title": "Outcome recorded",
            "kicker": "Terminal record",
            "steps": (("record", "recorded", "Outcome recorded", "The recruiter-process outcome is recorded privately."),),
        },
    },
    "es": {
        "clarify_context_before_reply": {
            "title": "Aclara el contexto antes de responder",
            "kicker": "Ruta segura de aclaración",
            "steps": (
                ("observation", "recorded", "Observación", "La observación reportada queda registrada."),
                ("safe-step", "pending", "Aclaración", "Aclara solo el contexto faltante antes de responder."),
                ("review", "blocked", "Revisión manual", "Vuelve a entrar manualmente a la conversación privada antes de responder."),
            ),
        },
        "prepare_fact_checked_summary": {
            "title": "Prepara un resumen verificado",
            "kicker": "Ruta segura de preparación",
            "steps": (
                ("observation", "recorded", "Observación", "La observación reportada queda registrada."),
                ("safe-step", "pending", "Verificación", "Prepara un resumen verificado solo con hechos reportados."),
                ("review", "blocked", "Revisión manual", "Revisa el resumen en privado antes de cualquier siguiente paso."),
            ),
        },
        "route_to_prepare-role-interviews": {
            "title": "Dirige a preparación privada",
            "kicker": "Ruta segura de preparación",
            "steps": (
                ("observation", "recorded", "Observación", "La observación reportada queda registrada."),
                ("safe-step", "pending", "Preparación", "Vuelve a entrar manualmente a la preparación para revisar el siguiente paso reportado."),
                ("review", "blocked", "Revisión manual", "Revisa la preparación en privado antes de cualquier siguiente paso."),
            ),
        },
        "record_stop_decision": {
            "title": "Resultado registrado",
            "kicker": "Registro terminal",
            "steps": (("record", "recorded", "Resultado registrado", "El resultado del proceso de reclutamiento queda registrado en privado."),),
        },
    },
}

RAIL_STATES = {
    "en": {"current": "Current", "pending": "Pending", "blocked": "Blocked", "recorded": "Recorded"},
    "es": {"current": "Actual", "pending": "Pendiente", "blocked": "Bloqueada", "recorded": "Registrado"},
}

EVIDENCE_COUNT_COPY = {
    "en": ("{count} candidate-supplied fact", "{count} candidate-supplied facts"),
    "es": ("{count} hecho reportado por la persona", "{count} hechos reportados por la persona"),
}

def _evidence_count_copy(locale: str, count: int) -> str:
    singular, plural = EVIDENCE_COUNT_COPY[locale]
    return (singular if count == 1 else plural).format(count=count)


def _action_rail(locale: str, action: str, *, terminal: bool = False) -> str:
    labels = ACTION_RAIL_COPY[locale][action]
    steps = "".join(
        f'<li class="continuity-step continuity-step--{state}" data-stage="{stage}" data-state="{state}"{(" aria-current=\"step\"" if state == "pending" else "")}>'
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


def _load_validator() -> Any:
    path = Path(__file__).with_name("validate_private_recruiter_conversion_outcome.py")
    spec = importlib.util.spec_from_file_location("conversion_outcome_validator", path)
    if spec is None or spec.loader is None: raise RuntimeError("outcome validator unavailable")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


VALIDATOR = _load_validator()


class OutcomeRenderValidationError(ValueError):
    def __init__(self, errors: Sequence[str]):
        self.errors = tuple(errors); super().__init__("private recruiter outcome validation failed")


class _ArgumentError(ValueError):
    pass


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise _ArgumentError


def _validated(item: Mapping[str, object], *, today: dt.date | None) -> Mapping[str, object]:
    errors = VALIDATOR.validate_outcome(item, today=today)
    if errors: raise OutcomeRenderValidationError(errors)
    return item


def render_outcome_html(item: Mapping[str, object], *, today: dt.date | None = None) -> str:
    value = _validated(item, today=today)
    locale = value["locale"]
    labels, event, action = COPY[locale], value["event_type"], value["next_safe_action"]
    stop_copy = STOP_COPY[locale] if action == "record_stop_decision" else None
    manual_next_step = _terminal_rail(locale) if action == "record_stop_decision" else _action_rail(locale, action)
    if action == "route_to_prepare-role-interviews":
        manual_next_step += (
            '<section class="outcome-manual-next-step" '
            'aria-labelledby="outcome-manual-next-step-heading">'
            f'<h2 id="outcome-manual-next-step-heading">{html.escape(labels["manual_next_step_heading"])}</h2>'
            f'<p>{html.escape(labels["manual_next_step_body"])}</p></section>'
        )
    template = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, TEMPLATE_PATH)
    css = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, CSS_PATH)
    replacements = {
        "{{LANG}}": html.escape(locale), "{{TITLE}}": labels["title"], "{{SKIP}}": labels["skip"], "{{INLINE_CSS}}": css,
        "{{KICKER}}": labels["kicker"], "{{HEADING}}": labels["heading"], "{{EVENT_LABEL}}": labels["event"],
        "{{EVENT}}": EVENT_LABELS[locale][event], "{{DATE_LABEL}}": labels["date"], "{{DATE}}": html.escape(value["event_date"]),
        "{{ACTION_LABEL}}": labels["action"], "{{ACTION}}": stop_copy["action"] if stop_copy else ACTION_LABELS[locale][action], "{{EVIDENCE_LABEL}}": labels["evidence"],
        "{{EVIDENCE}}": _evidence_count_copy(locale, len(value["fact_ids"])), "{{BOUNDARY}}": stop_copy["boundary"] if stop_copy else labels["boundary"], "{{MANUAL_NEXT_STEP}}": manual_next_step, "{{EMPLOYMENT_BOUNDARY}}": "" if stop_copy else f'<p class="outcome-employment-boundary">{labels["employment_boundary"]}</p>', "{{SAVE}}": labels["save"],
    }
    for token, replacement in replacements.items(): template = template.replace(token, replacement)
    if re.search(r"\{\{[A-Z_]+\}\}", template): raise RuntimeError("outcome template token contract is invalid")
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


def _atomic_private_write(output: Path, content: bytes, *, force: bool) -> None:
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
        else:
            os.link(temp, output.name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False); os.unlink(temp, dir_fd=parent)
        temp = None; os.fsync(parent)
    finally:
        if descriptor is not None: os.close(descriptor)
        if temp:
            try: os.unlink(temp, dir_fd=parent)
            except FileNotFoundError: pass
        os.close(parent)


def write_outcome_html(item: Mapping[str, object], output: Path, *, today: dt.date | None = None, force: bool = False):
    rendered = render_outcome_html(item, today=today)
    target = Path(os.path.abspath(os.fspath(output)))
    _atomic_private_write(target, rendered.encode("utf-8"), force=force)
    return type("RenderReceipt", (), {"artifact_path": target, "artifact_type": "text/html", "locale": item["locale"]})()


def _cli(argv=None) -> int:
    parser = _PrivateArgumentParser(); parser.add_argument("input", type=Path); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--force", action="store_true"); parser.add_argument("--include-artifact-path", action="store_true", help="include the local output path in the CLI receipt"); parser.add_argument("--as-of", dest="as_of", type=lambda value: dt.date.fromisoformat(value), required=True, help="Reference date for deterministic validation (YYYY-MM-DD).")
    try:
        args = parser.parse_args(argv)
    except _ArgumentError:
        print(json.dumps({"error": {"code": "invalid_arguments"}}, separators=(",", ":")), file=sys.stderr)
        return 3
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    try: item = VALIDATOR.load_outcome(args.input); receipt = write_outcome_html(item, args.output, today=args.as_of, force=args.force)
    except (OSError, VALIDATOR.OutcomeLoadError): print("cannot render private recruiter outcome", file=sys.stderr); return 3
    except OutcomeRenderValidationError as error: print("\n".join(error.errors), file=sys.stderr); return 2
    except ValueError:
        print("--as-of must use YYYY-MM-DD", file=sys.stderr); return 3
    payload = {"artifact_type": receipt.artifact_type, "locale": receipt.locale}
    if args.include_artifact_path:
        payload["artifact_path"] = str(receipt.artifact_path)
    print(json.dumps(payload, separators=(",", ":"))); return 0


if __name__ == "__main__": raise SystemExit(_cli())
