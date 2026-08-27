"""Fail-closed privacy guard for triage-sourced practice prose."""

from __future__ import annotations

import re

from dossier_practice_safe_text import is_safe_handoff_text


_LINKEDIN_PROFILE = re.compile(
    r"\blinkedin\.com/(?:in|pub)/[^\s/]+", re.IGNORECASE
)
_CREDENTIAL_SHAPED = re.compile(
    r"\b(?:api|access|secret|password|passwd|token|credential|auth)"
    r"(?:[_\-\s]*(?:key|token|secret|value))?\s*[:=]",
    re.IGNORECASE,
)
_BEARER_CREDENTIAL = re.compile(
    r"\b(?:authorization\s*:\s*)?bearer\s+[A-Z0-9._~+/-]{3,}\b",
    re.IGNORECASE,
)


def is_safe_triage_practice_prose(value: object, maximum: int) -> bool:
    """Return whether private triage prose is safe to project or render."""
    return (
        is_safe_handoff_text(value, maximum)
        and isinstance(value, str)
        and _LINKEDIN_PROFILE.search(value) is None
        and _CREDENTIAL_SHAPED.search(value) is None
        and _BEARER_CREDENTIAL.search(value) is None
    )
