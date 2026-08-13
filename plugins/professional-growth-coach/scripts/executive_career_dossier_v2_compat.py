"""Lossless-in-spirit v2-to-v1 projection for shared dossier validation."""

from __future__ import annotations

import copy
from collections.abc import Mapping


CANONICAL_PROFILE_SECTIONS: tuple[str, ...] = (
    "photo", "banner", "name", "profile_url", "headline", "location",
    "contact_info", "about", "experience", "skills", "featured",
    "certifications", "education", "recommendations", "activity",
    "analytics", "job_preferences",
)


def project_v2_to_v1(value: Mapping[str, object]) -> dict[str, object]:
    """Return a deep-copied v1 view without v2-only ledger metadata."""
    projected = copy.deepcopy(dict(value))
    projected["schema_version"] = "executive-career-dossier-v1"
    projected.pop("section_coverage", None)
    for evidence in projected.get("evidence", []):
        if isinstance(evidence, dict):
            evidence.pop("profile_section", None)
    for priority in projected.get("priorities", []):
        if isinstance(priority, dict):
            for key in (
                "target_section", "coach_observation", "why_it_matters", "coach_prompt",
                "client_template", "privacy_boundary",
            ):
                priority.pop(key, None)
    return projected
