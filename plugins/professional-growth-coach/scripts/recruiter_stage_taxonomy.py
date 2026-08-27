"""Closed recruiter-stage vocabulary and safe forward transitions."""

from __future__ import annotations

STAGES: tuple[str, ...] = (
    "recruiter_screen",
    "first_interview",
    "technical_screen",
    "hiring_manager",
    "technical_deep_dive",
    "take_home",
    "system_design",
    "behavioral_loop",
    "panel",
    "offer_stage",
)

_TRANSITIONS: dict[str, frozenset[str]] = {
    "recruiter_screen": frozenset({"first_interview", "technical_screen"}),
    "first_interview": frozenset({"technical_screen", "hiring_manager", "technical_deep_dive", "take_home", "system_design", "behavioral_loop", "panel"}),
    "technical_screen": frozenset({"hiring_manager", "technical_deep_dive", "take_home", "system_design", "behavioral_loop", "panel"}),
    "hiring_manager": frozenset({"technical_deep_dive", "panel", "offer_stage"}),
    "technical_deep_dive": frozenset({"hiring_manager", "system_design", "behavioral_loop", "panel", "offer_stage"}),
    "take_home": frozenset({"technical_deep_dive", "system_design", "panel", "offer_stage"}),
    "system_design": frozenset({"panel", "offer_stage"}),
    "behavioral_loop": frozenset({"panel", "offer_stage"}),
    "panel": frozenset({"offer_stage"}),
    "offer_stage": frozenset(),
}


def allowed_next_stages(current_stage: object) -> frozenset[str]:
    """Return the closed set of explicit forward handoffs for a stage."""

    if not isinstance(current_stage, str):
        return frozenset()
    return _TRANSITIONS.get(current_stage, frozenset())


def is_supported_transition(current_stage: object, next_stage: object) -> bool:
    return isinstance(next_stage, str) and next_stage in allowed_next_stages(current_stage)
