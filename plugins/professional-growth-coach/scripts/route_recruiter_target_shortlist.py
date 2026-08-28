#!/usr/bin/env python3
"""Route explicit recruiter-network requests to a private shortlist flow."""

from __future__ import annotations

import copy
import datetime as dt
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
STAGE_TAXONOMY = _sibling("recruiter_stage_taxonomy.py")
INTENT = re.compile(
    r"(?:\b(?:expand(?:ir|iendo)?|ampliar|crecer)\s+(?:mi\s+)?(?:red|network)\s+(?:de\s+)?(?:recruiters?|reclutadores?)\b|"
    r"\b(?:find|buscar|encontrar|identificar)\s+(?:a\s+)?(?:recruiters?|reclutadores?)\b|"
    r"\b(?:recruiter|recruiting|reclutador(?:a|es)?)\s+(?:screen|filtro|entrevista)\b|"
    r"\b(?:first\s+(?:recruiter\s+)?screen|primer\s+filtro(?:\s+con\s+(?:un\s+)?reclutador)?|"
    r"first\s+interview\s+with\s+(?:a\s+)?recruiters?|"
    r"primera\s+entrevista\s+con\s+(?:un\s+)?reclutador(?:a|es)?)\b|"
    r"\b(?:contact|reach(?:\s+out\s+to)?|connect\s+with|talk\s+to|speak\s+with)\s+(?:(?:an?|the)\s+)?(?:(?:senior|technical|lead|principal|internal|executive|hiring|talent|agency|corporate|junior|experienced)\s+)?(?:recruiters?|reclutador(?:a|es)?)\b|"
    r"\b(?:contactar\s+(?:a\s+)?|conectar(?:me)?\s+con\s+|hablar\s+con\s+)(?:(?:un(?:a)?|el|la)\s+)?(?:recruiters?|reclutador(?:a|es)?)\b|"
    r"\b(?:interview|entrevista)\s+(?:[a-záéíóúñ-]+\s+){0,3}(?:with|con)\s+(?:(?:an?|un(?:a)?)\s+)?(?:recruiters?|reclutador(?:a|es)?)\b|"
    r"\b(?:recruiters?|reclutador(?:a|es)?)\s+(?:[a-záéíóúñ-]+\s+){0,3}(?:interview|entrevista)\b|"
    r"\b(?:network|networking)\s+(?:with|con)\s+recruiters?\b|"
    r"\bred\s+profesional\s+con\s+reclutadores?\b|"
    r"\b(?:red|network)\s+de\s+(?:recruiters?|reclutadores?)\b)",
    re.I,
)
DEBRIEF_INTENT = re.compile(
    r"\b(?:debrief|debriefing|post[- ]?(?:screen|interview)|review|revisit|reflect|"
    r"revisar|revisi[oó]n|analizar|reflexionar)\b",
    re.I,
)
SCREEN_COMPLETION = re.compile(
    r"\b(?:had(?!\s+no\s+(?:trouble|questions)\b)|completed|attended|finished|went\s+through|spoke\s+with|talked\s+to|"
    r"termin[eé]|tuve|asist[ií]|atend[ií]|pas[eé]|habl[eé]\s+con|convers[eé]\s+con)\b",
    re.I,
)
SCREEN_NOT_COMPLETED = re.compile(
    r"\b(?:didn['’]?t\s+(?:attend|have|complete|finish)|did\s+not\s+(?:attend|have|complete|finish)|"
    r"(?:had|have)\s+no\s+(?:(?:a|an|the)\s+)?(?:recruiter\s+)?(?:screen|interview|call|conversation)\b|"
    r"not\s+(?:yet\s+)?(?:had|attended|completed|finished)|haven['’]?t\s+"
    r"(?:had|attended|completed|finished)|have\s+not\s+(?:had|attended|completed|finished)|"
    r"scheduled\s+for|upcoming|tomorrow|next\s+week|before\s+(?:the|my)|not\s+yet|"
    r"no\s+he\s+tenido|(?:todav[ií]a\s+)?no\s+(?:he\s+)?(?:tenido|asist[ií]|tuv[eé]|complet[eé]|termin[eé]|atend[ií])|"
    r"programad[oa]\s+para|ma[ñn]ana|pr[oó]xima?\s+semana)\b",
    re.I,
)
SCREEN_CONTEXT = re.compile(
    r"\b(?:screen|interview|entrevista|filtro|call|conversation|llamada|conversaci[oó]n|"
    r"spoke\s+with|talked\s+to|habl[eé]\s+con|convers[eé]\s+con)\b",
    re.I,
)
NEXT_STAGE_INTENT = re.compile(
    r"\b(?:next\s+stage|what(?:'s|\s+is)\s+next|what\s+comes\s+next|what\s+(?:do|should)\s+i\s+do\s+next|"
    r"next\s+step|move\s+on\s+to|advance\s+to|"
    r"hiring\s+manager\s+stage|prepare\s+for\s+(?:the\s+)?(?:next|hiring\s+manager)|"
    r"siguiente\s+etapa|siguiente\s+paso|que\s+sigue|qué\s+sigue|que\s+hago\s+despu[eé]s|"
    r"qué\s+hago\s+despu[eé]s|pasar\s+a\s+la\s+siguiente\s+etapa|"
    r"preparar(?:me)?\s+para\s+(?:la\s+)?siguiente\s+etapa)\b",
    re.I,
)
TECHNICAL_INTENT = re.compile(r"\b(?:technical|t[eé]cnica|t[eé]cnico)\b", re.I)
EXPLICIT_RECRUITER_INTENT = re.compile(r"\b(?:recruiter|recruiting|reclutador(?:a|es)?)\b", re.I)
EXTERNAL_ACTION_INTENT = re.compile(
    r"\b(?:send|message|messages|reply|repl(?:y|ies)|connect|contact|reach|talk|speak|apply|publish|schedule|scheduled|book|calendar|"
    r"confirm|accept|enviar|mensaje|mensajes|responder|respuesta|conectar|contactar|hablar|aplicar|publicar|agendar|"
    r"reservar|calendario|confirmar|aceptar|programar)\b",
    re.I,
)
INTAKE = {
    "es": "Comparte: 3–6 objetivos manuales con contexto visible o proporcionado por ti; la meta de red y sus segmentos; 3–5 consultas manuales; tu tiempo semanal; una condición de pausa o detención; y el tema de prueba que quieres revisar primero.",
    "en": "Share: 3–6 manually supplied targets with visible or candidate-provided context; the networking goal and segments; 3–5 manual queries; your weekly time budget; a pause or stop condition; and the proof theme you want reviewed first.",
}
HANDOFF_QUESTIONS = {
    "es": {
        "recruiter_target_decision_gate": "Comparte la shortlist validada de 3–6 objetivos y su contexto visible o proporcionado por ti para revisar la siguiente decisión manual.",
        "recruiter_target_screen_intake": "Comparte el contexto específico del objetivo: etapa, requisitos V-###, hechos F-###, estado de evidencia de empresa y los cuatro checks de preparación.",
        "private_recruiter_screen_debrief": "Comparte el checkpoint de pantalla atendida, su receipt, el intake del objetivo y un debrief estructurado de cobertura, temas desconocidos y decisión.",
        "private_recruiter_screen_debrief_intake": "Filtro atendido. Registra ahora cobertura de requisito, alcance y contexto del equipo.",
        "private_recruiter_interview_debrief_intake": "Entrevista registrada. Confirma la etapa y registra cobertura de requisito, alcance y contexto del equipo.",
        "private_recruiter_next_stage_review": "Comparte un debrief válido con su checkpoint y elige una etapa posterior permitida para la revisión manual.",
        "forward_stage_transition": "El debrief es válido; elige una etapa posterior permitida para continuar la revisión manual. No se envían mensajes ni se agendan eventos.",
        "terminal_stage": "La etapa de oferta es terminal en este flujo; no hay una etapa posterior permitida. Registra el cierre o inicia un caso nuevo si necesitas preparar otro proceso.",
    },
    "en": {
        "recruiter_target_decision_gate": "Share the validated 3–6 target shortlist and its visible or candidate-provided context for the next manual decision review.",
        "recruiter_target_screen_intake": "Share target-specific context: stage, V-### requirements, F-### facts, company-evidence state, and the four readiness checks.",
        "private_recruiter_screen_debrief": "Share the attended-screen checkpoint, its receipt, the target intake, and a structured debrief covering topics, unknowns, and decision.",
        "private_recruiter_screen_debrief_intake": "Screen attended. Capture requirement coverage, scope, and team context.",
        "private_recruiter_interview_debrief_intake": "Interview request recorded. Confirm the stage and capture requirement coverage, scope, and team context.",
        "private_recruiter_next_stage_review": "Share a valid debrief with its checkpoint and choose an allowed forward stage for manual review.",
        "forward_stage_transition": "The debrief is valid; choose an allowed forward stage to continue manual review. No messages are sent and no events are scheduled.",
        "terminal_stage": "Offer stage is terminal in this flow; no later stage is allowed. Record the close or start a new case if you need to prepare another process.",
    },
}
HANDOFF_GAPS = {
    "recruiter_target_decision_gate": ["validated_shortlist_artifact"],
    "recruiter_target_screen_intake": ["target_specific_screen_context"],
    "private_recruiter_screen_debrief": ["valid_screen_checkpoint_receipt_intake_and_debrief"],
    "private_recruiter_next_stage_review": ["valid_debrief_checkpoint_and_forward_stage"],
}


def _safe_locale(value: object) -> str:
    locale = value.get("locale") if isinstance(value, Mapping) else None
    if isinstance(locale, str) and locale in INTAKE:
        return locale
    return "es"


def _has_recruiter_screen_context(request: str) -> bool:
    return bool(EXPLICIT_RECRUITER_INTENT.search(request) and SCREEN_CONTEXT.search(request))


def _natural_recruiter_route(request: str) -> str | None:
    """Classify natural recruiter follow-up language before shortlist routing."""
    has_screen_context = _has_recruiter_screen_context(request)
    if has_screen_context and SCREEN_NOT_COMPLETED.search(request):
        return "pre_screen"
    if has_screen_context and DEBRIEF_INTENT.search(request):
        return "debrief"
    if has_screen_context and SCREEN_COMPLETION.search(request):
        return "debrief"
    if has_screen_context and NEXT_STAGE_INTENT.search(request):
        return "next_stage"
    if INTENT.search(request):
        return "shortlist"
    return None


def _artifact_free_intake(
    route_kind: str,
    *,
    selected_module: str,
    next_action: str,
    locale: str,
    question_key: str | None = None,
    evidence_gaps: Sequence[str] | None = None,
    allowed_next_stages: Sequence[str] | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "route_kind": route_kind,
        "case_state": "needs_intake",
        "selected_module": selected_module,
        "next_action": next_action,
        "authorization_required": False,
        "evidence_gaps": list(evidence_gaps if evidence_gaps is not None else HANDOFF_GAPS[route_kind]),
        "intake_question": HANDOFF_QUESTIONS[locale].get(question_key or route_kind, INTAKE[locale]),
        "artifact": None,
    }
    if allowed_next_stages is not None:
        result["allowed_next_stages"] = list(allowed_next_stages)
    return result


def _current_stage(intake: Mapping[str, object]) -> object:
    nested = intake.get("intake")
    return nested.get("stated_stage") if isinstance(nested, Mapping) else None


def _debrief_is_complete(debrief: Mapping[str, object]) -> bool:
    if not isinstance(debrief, Mapping):
        return False
    coverage = debrief.get("coverage")
    unknown_topics = debrief.get("unknown_topics")
    return (
        debrief.get("decision") == "continue_review"
        and isinstance(coverage, list)
        and len(coverage) == 3
        and all(isinstance(row, Mapping) and row.get("status") == "discussed" for row in coverage)
        and isinstance(unknown_topics, list)
        and not unknown_topics
    )


def _transition_recovery(
    debrief: Mapping[str, object], intake: Mapping[str, object], next_stage: object
) -> dict[str, object] | None:
    if not isinstance(debrief, Mapping) or not isinstance(intake, Mapping):
        return None
    current_stage = _current_stage(intake)
    if not _debrief_is_complete(debrief) or current_stage not in STAGE_TAXONOMY.STAGES:
        return None
    allowed = [stage for stage in STAGE_TAXONOMY.STAGES if stage in STAGE_TAXONOMY.allowed_next_stages(current_stage)]
    if next_stage in allowed:
        return None
    locale = _safe_locale(debrief)
    if not allowed:
        result = _artifact_free_intake(
            "private_recruiter_next_stage_review",
            selected_module="prepare-role-interviews",
            next_action="record_terminal_stage",
            locale=locale,
            question_key="terminal_stage",
            evidence_gaps=["terminal_stage"],
            allowed_next_stages=[],
        )
        result["case_state"] = "terminal"
        result["terminal_reason"] = "offer_stage_has_no_forward_transition"
        return result
    return _artifact_free_intake(
        "private_recruiter_next_stage_review",
        selected_module="prepare-role-interviews",
        next_action="select_forward_stage",
        locale=locale,
        question_key="forward_stage_transition",
        evidence_gaps=["forward_stage_transition"],
        allowed_next_stages=allowed,
    )


def route_recruiter_request(
    request: str,
    *,
    locale: str,
    as_of_date: str,
    network_plan: Mapping[str, object] | None = None,
    targets: Sequence[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Return an internal route receipt without echoing the request or executing actions."""
    request_authorization_required = bool(
        isinstance(request, str) and EXTERNAL_ACTION_INTENT.search(request)
    )
    if not isinstance(locale, str) or locale not in INTAKE:
        return {
            "route_kind": "recruiter_target_shortlist",
            "case_state": "needs_intake",
            "selected_module": "optimize-professional-profile",
            "next_action": "ask_one_intake_question",
            "authorization_required": request_authorization_required,
            "evidence_gaps": ["valid_locale"],
            "intake_question": INTAKE["es"],
            "artifact": None,
        }
    if not isinstance(request, str) or not request.strip():
        return {
            "route_kind": "ordinary_professional_growth",
            "case_state": "not_applicable",
            "selected_module": None,
            "next_action": "continue_normal_routing",
            "authorization_required": False,
            "evidence_gaps": [],
            "artifact": None,
        }
    natural_route = _natural_recruiter_route(request)
    if natural_route == "debrief":
        return _artifact_free_intake(
            "private_recruiter_screen_debrief",
            selected_module="track-career-outcomes",
            next_action="collect_debrief_context",
            locale=locale,
            question_key="private_recruiter_screen_debrief",
            evidence_gaps=["structured_debrief_context"],
        ) | {"authorization_required": request_authorization_required}
    if natural_route == "next_stage":
        return _artifact_free_intake(
            "private_recruiter_next_stage_review",
            selected_module="prepare-role-interviews",
            next_action="collect_debrief_context",
            locale=locale,
            question_key="private_recruiter_next_stage_review",
            evidence_gaps=["valid_debrief_checkpoint_and_forward_stage"],
        ) | {"authorization_required": request_authorization_required}
    if natural_route == "pre_screen":
        return _artifact_free_intake(
            "recruiter_target_screen_intake",
            selected_module="prepare-role-interviews",
            next_action="collect_screen_intake",
            locale=locale,
            question_key="recruiter_target_screen_intake",
            evidence_gaps=["target_specific_screen_context"],
        ) | {"authorization_required": request_authorization_required}
    if natural_route != "shortlist":
        return {
            "route_kind": "ordinary_professional_growth",
            "case_state": "not_applicable",
            "selected_module": None,
            "next_action": "continue_normal_routing",
            "authorization_required": request_authorization_required,
            "evidence_gaps": [],
            "artifact": None,
        }
    recruiter_intent = True
    if recruiter_intent and TECHNICAL_INTENT.search(request) and not EXPLICIT_RECRUITER_INTENT.search(request):
        recruiter_intent = False
    authorization_required = request_authorization_required
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
            "authorization_required": authorization_required,
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
    except (RecursionError, TypeError, ValueError):
        return {
            "route_kind": "recruiter_target_shortlist",
            "case_state": "needs_intake",
            "selected_module": "optimize-professional-profile",
            "next_action": "ask_one_intake_question",
            "authorization_required": authorization_required,
            "evidence_gaps": ["validated_target_context"],
            "intake_question": INTAKE[locale],
            "artifact": None,
        }
    return {
        "route_kind": "recruiter_target_shortlist",
        "case_state": "ready",
        "selected_module": "optimize-professional-profile",
        "next_action": "review_recruiter_target_shortlist",
        "authorization_required": authorization_required,
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
            question_key="recruiter_target_screen_intake",
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
            question_key="recruiter_target_decision_gate",
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
            question_key="recruiter_target_screen_intake",
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


def route_recruiter_screen_debrief_intake(
    checkpoint: Mapping[str, object],
    receipt: Mapping[str, object],
    intake: Mapping[str, object],
) -> dict[str, object]:
    """Start a bounded, artifact-free debrief after a validated attended screen."""
    locale = _safe_locale(intake)
    question_key = (
        "private_recruiter_interview_debrief_intake"
        if isinstance(receipt, Mapping) and receipt.get("event_type") == "interview_requested"
        else "private_recruiter_screen_debrief_intake"
    )
    try:
        if not all(isinstance(value, Mapping) for value in (checkpoint, receipt, intake)):
            raise ValueError("debrief intake inputs are unavailable")
        as_of = dt.date.today()
        checkpoint_errors = SCREEN_DEBRIEF_BUILDER.VALIDATOR.CHECKPOINT.validate_checkpoint(
            checkpoint, receipt, as_of=as_of
        )
        intake_errors = SCREEN_DEBRIEF_BUILDER.VALIDATOR.INTAKE.validate_screen_intake(
            intake, as_of=as_of
        )
        if checkpoint_errors or intake_errors:
            raise ValueError("debrief intake inputs are invalid")
        if checkpoint.get("action_state") != "completed":
            raise ValueError("screen has not been completed")
        if checkpoint.get("next_measurement_event") != "screen_attended":
            raise ValueError("screen attendance is not observed")
        if checkpoint.get("next_safe_action") != "debrief_after_screen":
            raise ValueError("checkpoint is not ready for debrief")
        if receipt.get("event_type") not in {"screen_requested", "interview_requested"}:
            raise ValueError("receipt is not an interview request")
        if intake.get("readiness_decision") != "ready":
            raise ValueError("screen intake is not ready")
        if not (checkpoint.get("locale") == receipt.get("locale") == intake.get("locale")):
            raise ValueError("debrief locale is not reconciled")
        binding = checkpoint.get("target_binding")
        if not isinstance(binding, Mapping):
            raise ValueError("debrief target binding is unavailable")
        if binding.get("target_id") != intake.get("target_id") or binding.get("source_gate_snapshot") != intake.get("source_gate_snapshot"):
            raise ValueError("debrief target binding is not reconciled")
    except (TypeError, ValueError):
        return _artifact_free_intake(
            "private_recruiter_screen_debrief",
            selected_module="track-career-outcomes",
            next_action="collect_debrief_context",
            locale=locale,
            question_key=question_key,
            evidence_gaps=["validated_screen_checkpoint_receipt_intake"],
        )
    return _artifact_free_intake(
        "private_recruiter_screen_debrief",
        selected_module="track-career-outcomes",
        next_action="collect_debrief_context",
        locale=locale,
        question_key=question_key,
        evidence_gaps=["structured_debrief_context"],
    )


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
            question_key="private_recruiter_screen_debrief",
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
    transition_recovery = _transition_recovery(debrief, intake, next_stage)
    if transition_recovery is not None:
        return transition_recovery
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
            question_key="private_recruiter_next_stage_review",
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
