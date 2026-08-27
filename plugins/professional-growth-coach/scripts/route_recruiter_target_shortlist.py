#!/usr/bin/env python3
"""Route explicit recruiter-network requests to a private shortlist flow."""

from __future__ import annotations

import copy
import importlib.util
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_route_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("recruiter shortlist route is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = _sibling("build_recruiter_target_shortlist.py")
GATE_BUILDER = _sibling("build_recruiter_target_decision_gate.py")
SCREEN_INTAKE_BUILDER = _sibling("build_recruiter_target_screen_intake.py")
SCREEN_DEBRIEF_BUILDER = _sibling("build_private_recruiter_screen_debrief.py")
NEXT_STAGE_REVIEW_BUILDER = _sibling("build_private_recruiter_next_stage_review.py")
RENDERER = _sibling("render_recruiter_target_shortlist.py")
GATE_RENDERER = _sibling("render_recruiter_target_decision_gate.py")
SCREEN_INTAKE_RENDERER = _sibling("render_recruiter_target_screen_intake.py")
SCREEN_DEBRIEF_RENDERER = _sibling("render_private_recruiter_screen_debrief.py")
NEXT_STAGE_REVIEW_RENDERER = _sibling("render_private_recruiter_next_stage_review.py")
INTENT = re.compile(
    r"(?:\b(?:expand(?:ir|iendo)?|ampliar|crecer)\s+(?:mi\s+)?(?:red|network)\s+(?:de\s+)?(?:recruiters?|reclutadores?)\b|"
    r"\b(?:find|buscar|encontrar|identificar)\s+(?:a\s+)?(?:recruiters?|reclutadores?)\b|"
    r"\b(?:recruiter|recruiting|reclutador(?:a|es)?)\s+(?:screen|filtro|entrevista)\b|"
    r"\b(?:first\s+(?:recruiter\s+)?screen|primer\s+filtro(?:\s+con\s+(?:un\s+)?reclutador)?|"
    r"first\s+interview\s+with\s+(?:a\s+)?recruiters?|"
    r"primera\s+entrevista\s+con\s+(?:un\s+)?reclutadores?)\b|"
    r"\b(?:network|networking)\s+(?:with|con)\s+recruiters?\b|"
    r"\bred\s+profesional\s+con\s+reclutadores?\b|"
    r"\b(?:red|network)\s+de\s+(?:recruiters?|reclutadores?)\b)",
    re.I,
)
TECHNICAL_INTENT = re.compile(r"\b(?:technical|t[eé]cnica|t[eé]cnico)\b", re.I)
EXPLICIT_RECRUITER_INTENT = re.compile(r"\b(?:recruiter|recruiting|reclutador(?:a|es)?)\b", re.I)
INTAKE = {
    "es": "Comparte: 3–6 objetivos manuales con contexto visible o proporcionado por ti; la meta de red y sus segmentos; 3–5 consultas manuales; tu tiempo semanal; una condición de pausa o detención; y el tema de prueba que quieres revisar primero.",
    "en": "Share: 3–6 manually supplied targets with visible or candidate-provided context; the networking goal and segments; 3–5 manual queries; your weekly time budget; a pause or stop condition; and the proof theme you want reviewed first.",
}
HANDOFF_GAPS = {
    "recruiter_target_decision_gate": ["validated_shortlist_artifact"],
    "recruiter_target_screen_intake": ["target_specific_screen_context"],
    "private_recruiter_screen_debrief": ["valid_screen_checkpoint_receipt_intake_and_debrief"],
    "private_recruiter_next_stage_review": ["valid_debrief_checkpoint_and_forward_stage"],
}


def _safe_locale(value: object) -> str:
    if isinstance(value, Mapping) and value.get("locale") in INTAKE:
        return str(value["locale"])
    return "es"


def _artifact_free_intake(
    route_kind: str,
    *,
    selected_module: str,
    next_action: str,
    locale: str,
) -> dict[str, object]:
    return {
        "route_kind": route_kind,
        "case_state": "needs_intake",
        "selected_module": selected_module,
        "next_action": next_action,
        "authorization_required": False,
        "evidence_gaps": list(HANDOFF_GAPS[route_kind]),
        "intake_question": INTAKE[locale],
        "artifact": None,
    }


def route_recruiter_request(
    request: str,
    *,
    locale: str,
    as_of_date: str,
    network_plan: Mapping[str, object] | None = None,
    targets: Sequence[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Return an internal route receipt without echoing the request or executing actions."""
    if locale not in INTAKE:
        raise ValueError("locale must be es or en")
    if not isinstance(request, str) or not request.strip() or not INTENT.search(request):
        return {
            "route_kind": "ordinary_professional_growth",
            "case_state": "not_applicable",
            "selected_module": None,
            "next_action": "continue_normal_routing",
            "authorization_required": False,
            "evidence_gaps": [],
            "artifact": None,
        }
    recruiter_intent = INTENT.search(request) is not None
    if recruiter_intent and TECHNICAL_INTENT.search(request) and not EXPLICIT_RECRUITER_INTENT.search(request):
        recruiter_intent = False
    if not recruiter_intent:
        return {
            "route_kind": "ordinary_professional_growth",
            "case_state": "not_applicable",
            "selected_module": None,
            "next_action": "continue_normal_routing",
            "authorization_required": False,
            "evidence_gaps": [],
            "artifact": None,
        }
    if (
        not isinstance(network_plan, Mapping)
        or not isinstance(targets, Sequence)
        or isinstance(targets, (str, bytes, bytearray))
        or not 3 <= len(targets) <= 6
    ):
        return {
            "route_kind": "recruiter_target_shortlist",
            "case_state": "needs_intake",
            "selected_module": "optimize-professional-profile",
            "next_action": "ask_one_intake_question",
            "authorization_required": False,
            "evidence_gaps": [
                "three_to_six_manual_targets_with_context",
                "network_goal_and_target_segments",
                "three_to_five_manual_queries",
                "weekly_time_budget_and_stop_condition",
                "proof_theme",
            ],
            "intake_question": INTAKE[locale],
            "artifact": None,
        }
    try:
        artifact = BUILDER.build_shortlist(locale, as_of_date, copy.deepcopy(dict(network_plan)), copy.deepcopy(list(targets)))
        rendered_html = RENDERER.render_shortlist_html(artifact)
    except (TypeError, ValueError):
        return {
            "route_kind": "recruiter_target_shortlist",
            "case_state": "needs_intake",
            "selected_module": "optimize-professional-profile",
            "next_action": "ask_one_intake_question",
            "authorization_required": False,
            "evidence_gaps": ["validated_target_context"],
            "intake_question": INTAKE[locale],
            "artifact": None,
        }
    return {
        "route_kind": "recruiter_target_shortlist",
        "case_state": "ready",
        "selected_module": "optimize-professional-profile",
        "next_action": "review_recruiter_target_shortlist",
        "authorization_required": False,
        "evidence_gaps": [],
        "artifact": artifact,
        "rendered_html": rendered_html,
    }


def route_recruiter_decision_gate(
    shortlist: Mapping[str, object],
    *,
    screen_context: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Route one validated shortlist to a manual-only decision gate."""
    if screen_context is not None:
        # Generic screen context is intentionally no longer a handoff signal.
        # The target-specific bridge must bind one target, its snapshot, and
        # four explicit readiness checks before interview preparation review.
        return _artifact_free_intake(
            "recruiter_target_screen_intake",
            selected_module="prepare-role-interviews",
            next_action="collect_screen_intake",
            locale=_safe_locale(shortlist),
        )
    try:
        artifact = GATE_BUILDER.build_decision_gate(shortlist)
        rendered_html = GATE_RENDERER.render_decision_gate_html(artifact)
    except (TypeError, ValueError):
        return _artifact_free_intake(
            "recruiter_target_decision_gate",
            selected_module="prepare-role-interviews",
            next_action="collect_screen_context",
            locale=_safe_locale(shortlist),
        )
    return {
        "route_kind": "recruiter_target_decision_gate",
        "case_state": "ready",
        "selected_module": "prepare-role-interviews",
        "next_action": artifact["handoff"]["next_safe_action"],
        "authorization_required": False,
        "artifact": artifact,
        "rendered_html": rendered_html,
    }


def route_recruiter_screen_intake(
    gate: Mapping[str, object],
    target_id: str,
    context: Mapping[str, object],
) -> dict[str, object]:
    """Route one target through bounded intake before manual interview review."""
    try:
        artifact = SCREEN_INTAKE_BUILDER.build_screen_intake(gate, target_id, context)
        rendered_html = SCREEN_INTAKE_RENDERER.render_screen_intake_html(artifact)
    except (TypeError, ValueError):
        return _artifact_free_intake(
            "recruiter_target_screen_intake",
            selected_module="prepare-role-interviews",
            next_action="collect_screen_intake",
            locale=_safe_locale(gate),
        )
    ready = artifact["readiness_decision"] == "ready"
    return {
        "route_kind": "recruiter_target_screen_intake",
        "case_state": "ready" if ready else "needs_intake",
        "selected_module": "prepare-role-interviews",
        "next_action": artifact["handoff"]["next_safe_action"],
        "authorization_required": False,
        "artifact": artifact,
        "rendered_html": rendered_html,
    }


def route_recruiter_screen_debrief(
    checkpoint: Mapping[str, object],
    receipt: Mapping[str, object],
    intake: Mapping[str, object],
    debrief: Mapping[str, object],
) -> dict[str, object]:
    """Route one attended screen through a private structured debrief."""
    try:
        artifact = SCREEN_DEBRIEF_BUILDER.build_screen_debrief(checkpoint, receipt, intake, debrief)
        rendered_html = SCREEN_DEBRIEF_RENDERER.render_screen_debrief_html(
            artifact, receipt, intake, checkpoint=checkpoint
        )
    except (TypeError, ValueError):
        return _artifact_free_intake(
            "private_recruiter_screen_debrief",
            selected_module="track-career-outcomes",
            next_action="collect_debrief_context",
            locale=_safe_locale(intake),
        )
    ready = artifact["decision"] == "continue_review"
    stopped = artifact["decision"] == "stop"
    return {
        "route_kind": "private_recruiter_screen_debrief",
        "case_state": "stopped" if stopped else ("ready" if ready else "needs_intake"),
        "selected_module": "track-career-outcomes",
        "next_action": artifact["handoff"]["next_safe_action"],
        "authorization_required": False,
        "artifact": artifact,
        "rendered_html": rendered_html,
    }


def route_recruiter_next_stage_review(
    debrief: Mapping[str, object],
    receipt: Mapping[str, object],
    intake: Mapping[str, object],
    checkpoint: Mapping[str, object],
    next_stage: str,
) -> dict[str, object]:
    """Route a completed screen debrief to an explicit, manual next-stage review."""
    try:
        artifact = NEXT_STAGE_REVIEW_BUILDER.build_next_stage_review(debrief, receipt, intake, checkpoint, next_stage)
        rendered_html = NEXT_STAGE_REVIEW_RENDERER.render_next_stage_review_html(
            artifact, debrief, receipt, intake, checkpoint
        )
    except (TypeError, ValueError):
        return _artifact_free_intake(
            "private_recruiter_next_stage_review",
            selected_module="prepare-role-interviews",
            next_action="collect_debrief_context",
            locale=_safe_locale(debrief),
        )
    ready = artifact["review_state"] == "ready"
    stopped = artifact["handoff"]["next_safe_action"] == "record_stop_decision"
    return {
        "route_kind": "private_recruiter_next_stage_review",
        "case_state": "stopped" if stopped else ("ready" if ready else "needs_intake"),
        "selected_module": "prepare-role-interviews",
        "next_action": artifact["handoff"]["next_safe_action"],
        "authorization_required": False,
        "artifact": artifact,
        "rendered_html": rendered_html,
    }
