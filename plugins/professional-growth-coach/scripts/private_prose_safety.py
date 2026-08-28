"""Unicode safety checks for private prose."""

from __future__ import annotations

import html
import re
import unicodedata
from collections.abc import Sequence
from urllib.parse import unquote


MAX_DIAGNOSTIC_BYTES = 16_384
DIAGNOSTIC_TRUNCATION_MARKER = "validation diagnostics truncated; additional errors omitted\n"


_SUSPICIOUS_DIAGNOSTIC_FIELD = re.compile(
    r"@|://|~[\\/]|[.]{1,2}[\\/]|"
    r"(?:^[A-Za-z]:[\\/]|^\\\\|^//)|"
    r"(?:^|[\\/])(?:users|private|tmp|home|var|opt|applications|volumes|root|srv|usr)[\\/]|"
    r"(?:www\.|linkedin\.com/)|"
    r"(?<![A-Za-z])\+?\d[\d .()_-]{6,}\d|"
    r"(?:token|secret|password|credential|api[_-]?key|access[_-]?key|auth|cookie|private)",
    re.IGNORECASE,
)

_RESTRICTED_PRIVATE_MATERIAL = re.compile(
    r"(?:^|\s)/(?:Users|private|tmp|home|var|opt|Applications|Volumes|root|srv|usr)/|"
    r"(?<!\w)\+?\d[\d .()_-]{6,}\d|"
    r"\b(?:bearer|token|secret|password|passwd|credential|api[_-]?key|access[_-]?key|auth|cookie)\b"
    r"(?:\s*[:=]\s*|\s+[A-Za-z0-9._-]{12,})",
    re.IGNORECASE,
)


def contains_unicode_controls(value: object) -> bool:
    """Return whether string text contains a Unicode control or format character."""
    if not isinstance(value, str):
        return False
    normalized = unicodedata.normalize("NFKC", value)
    return any(unicodedata.category(character) in {"Cc", "Cf"} for character in normalized)


def is_safe_prose_text(value: object) -> bool:
    """Return whether text is a string without Unicode controls or format characters."""
    return isinstance(value, str) and not contains_unicode_controls(
        normalize_prose_for_validation(value)
    )


def normalize_prose_for_validation(value: str) -> str:
    """Decode bounded nested markup and percent escapes before safety checks."""
    normalized = unicodedata.normalize("NFKC", value)
    for _ in range(5):
        decoded = html.unescape(unquote(normalized))
        if decoded == normalized:
            break
        normalized = decoded
    return normalized


def contains_restricted_private_material(value: object) -> bool:
    """Return whether bounded prose contains a local path, phone, or credential marker."""
    return isinstance(value, str) and _RESTRICTED_PRIVATE_MATERIAL.search(
        normalize_prose_for_validation(value)
    ) is not None


def safe_diagnostic_field_name(value: str) -> str:
    """Redact contact-, path-, and credential-shaped keys in diagnostics."""
    normalized = normalize_prose_for_validation(value)
    if contains_unicode_controls(normalized) or _SUSPICIOUS_DIAGNOSTIC_FIELD.search(normalized):
        return "<redacted-field>"
    return value


def format_bounded_diagnostics(
    errors: Sequence[str], *, max_bytes: int = MAX_DIAGNOSTIC_BYTES
) -> str:
    """Render diagnostics without exceeding a UTF-8 byte budget.

    Complete diagnostic lines are retained when they fit; otherwise a stable
    marker is emitted so callers can distinguish truncation from a clean result.
    The helper never slices an encoded line, preserving UTF-8 boundaries.
    """
    marker_bytes = len(DIAGNOSTIC_TRUNCATION_MARKER.encode("utf-8"))
    if max_bytes < marker_bytes:
        raise ValueError("diagnostic byte budget is smaller than truncation marker")
    lines: list[str] = []
    used_bytes = 0
    for error in errors:
        line = f"{error}\n"
        line_bytes = len(line.encode("utf-8"))
        if used_bytes + line_bytes <= max_bytes:
            lines.append(line)
            used_bytes += line_bytes
            continue
        while lines and used_bytes + marker_bytes > max_bytes:
            used_bytes -= len(lines.pop().encode("utf-8"))
        return "".join(lines) + DIAGNOSTIC_TRUNCATION_MARKER
    return "".join(lines)
