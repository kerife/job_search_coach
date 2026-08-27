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
INTENT = re.compile(r"(?:recruiter|recruiting|reclutador|reclutadora|network|red de|first interview|first screen|primer filtro|primera entrevista)", re.I)
INTAKE = {
    "es": "Comparte de tres a seis objetivos manuales con contexto visible o proporcionado por ti y el tema de prueba que quieres revisar primero.",
    "en": "Share three to six manually supplied targets with visible or candidate-provided context and the proof theme you want reviewed first.",
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
    if network_plan is None or targets is None or not 3 <= len(targets) <= 6:
        return {
            "route_kind": "recruiter_target_shortlist",
            "case_state": "needs_intake",
            "selected_module": "optimize-professional-profile",
            "next_action": "ask_one_intake_question",
            "authorization_required": False,
            "evidence_gaps": ["three_to_six_manual_targets_with_context"],
            "intake_question": INTAKE[locale],
            "artifact": None,
        }
    try:
        artifact = BUILDER.build_shortlist(locale, as_of_date, copy.deepcopy(dict(network_plan)), copy.deepcopy(list(targets)))
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
        "next_action": "render_recruiter_target_shortlist",
        "authorization_required": False,
        "evidence_gaps": [],
        "artifact": artifact,
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
        return {
            "route_kind": "recruiter_target_screen_intake",
            "case_state": "needs_intake",
            "selected_module": "prepare-role-interviews",
            "next_action": "collect_screen_intake",
            "authorization_required": False,
            "artifact": None,
        }
    try:
        artifact = GATE_BUILDER.build_decision_gate(shortlist)
    except (TypeError, ValueError):
        return {
            "route_kind": "recruiter_target_decision_gate",
            "case_state": "needs_intake",
            "selected_module": "prepare-role-interviews",
            "next_action": "collect_screen_context",
            "authorization_required": False,
            "artifact": None,
        }
    return {
        "route_kind": "recruiter_target_decision_gate",
        "case_state": "ready",
        "selected_module": "prepare-role-interviews",
        "next_action": artifact["handoff"]["next_safe_action"],
        "authorization_required": False,
        "artifact": artifact,
    }


def route_recruiter_screen_intake(
    gate: Mapping[str, object],
    target_id: str,
    context: Mapping[str, object],
) -> dict[str, object]:
    """Route one target through bounded intake before manual interview review."""
    try:
        artifact = SCREEN_INTAKE_BUILDER.build_screen_intake(gate, target_id, context)
    except (TypeError, ValueError):
        return {
            "route_kind": "recruiter_target_screen_intake",
            "case_state": "needs_intake",
            "selected_module": "prepare-role-interviews",
            "next_action": "collect_screen_intake",
            "authorization_required": False,
            "artifact": None,
        }
    ready = artifact["readiness_decision"] == "ready"
    return {
        "route_kind": "recruiter_target_screen_intake",
        "case_state": "ready" if ready else "needs_intake",
        "selected_module": "prepare-role-interviews",
        "next_action": artifact["handoff"]["next_safe_action"],
        "authorization_required": False,
        "artifact": artifact,
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
    except (TypeError, ValueError):
        return {
            "route_kind": "private_recruiter_screen_debrief",
            "case_state": "needs_intake",
            "selected_module": "track-career-outcomes",
            "next_action": "collect_debrief_context",
            "authorization_required": False,
            "artifact": None,
        }
    ready = artifact["decision"] == "continue_review"
    return {
        "route_kind": "private_recruiter_screen_debrief",
        "case_state": "ready" if ready else "needs_intake",
        "selected_module": "track-career-outcomes",
        "next_action": artifact["handoff"]["next_safe_action"],
        "authorization_required": False,
        "artifact": artifact,
    }
