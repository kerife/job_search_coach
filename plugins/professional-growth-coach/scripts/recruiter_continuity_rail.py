"""Render the shared, identity-free recruiter-flow continuity rail."""

from __future__ import annotations

import html


COPY = {
    "es": {
        "label": "Ruta de revisión recruiter · Orientación; no indica avance ni contacto realizado",
        "current": "Superficie actual de revisión",
        "steps": ("Elegir objetivos", "Revisar la decisión", "Preparar la pantalla", "Revisar la pantalla", "Preparar la siguiente etapa"),
    },
    "en": {
        "label": "Recruiter review path · Review orientation; does not track progress or contact",
        "current": "Current review surface",
        "steps": ("Choose targets", "Review decision", "Prepare the screen", "Review the screen", "Prepare the next stage"),
    },
}

STEP_KEYS = ("shortlist", "decision_gate", "screen_intake", "screen_debrief", "next_stage")

TRIAGE_STEP_KEYS = ("classify", "prepare", "reentry")
TRIAGE_COPY = {
    "es": {
        "label": "Ruta de respuesta recruiter · Orientación; no envía ni agenda",
        "steps": ("Clasificar respuesta", "Aclarar o preparar", "Reingreso manual"),
    },
    "en": {
        "label": "Recruiter reply path · Orientation; does not send or schedule",
        "steps": ("Classify reply", "Clarify or prepare", "Manual re-entry"),
    },
}
TRIAGE_CURRENT_STEP = {
    "clarify_first": "prepare",
    "ready_for_private_prep": "reentry",
    "stop": "classify",
}


def render_continuity_rail(locale: str, current_step: str) -> tuple[str, str]:
    """Return the localized label and a five-step rail with one current marker."""

    labels = COPY[locale]
    items = []
    for index, (key, label) in enumerate(zip(STEP_KEYS, labels["steps"], strict=True), start=1):
        current = key == current_step
        current_suffix = f'<span class="continuity-rail__status">{html.escape(labels["current"])}</span>' if current else ""
        current_attrs = ' data-state="current" aria-current="location"' if current else ' data-state="context"'
        items.append(
            f'<li{current_attrs}><span class="continuity-rail__marker" aria-hidden="true">{index}</span>'
            f'<span class="continuity-rail__copy"><strong>{html.escape(label)}</strong>{current_suffix}</span></li>'
        )
    return labels["label"], "".join(items)


def render_triage_continuity_rail(locale: str, state: str) -> tuple[str, str]:
    """Return a localized three-step rail with one state-bound current marker."""
    labels = TRIAGE_COPY[locale]
    current_step = TRIAGE_CURRENT_STEP[state]
    items = []
    for index, (key, label) in enumerate(zip(TRIAGE_STEP_KEYS, labels["steps"], strict=True), start=1):
        current = key == current_step
        attrs = ' data-state="current" aria-current="step"' if current else ' data-state="context"'
        items.append(
            f'<li{attrs}><span class="triage-continuity-marker" aria-hidden="true">{index}</span>'
            f'<span class="triage-continuity-copy"><strong>{html.escape(label)}</strong></span></li>'
        )
    return labels["label"], "".join(items)
