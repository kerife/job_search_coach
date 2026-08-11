"""Unicode safety checks for private prose."""

from __future__ import annotations

import re
import unicodedata


_SUSPICIOUS_DIAGNOSTIC_FIELD = re.compile(
    r"@|://|~[\\/]|(?:^|[\\/])(?:users|private|tmp|home)[\\/]|"
    r"(?:www\.|linkedin\.com/)|"
    r"(?:token|secret|password|credential|api[_-]?key|access[_-]?key|auth|cookie|private)",
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
    return isinstance(value, str) and not contains_unicode_controls(value)


def safe_diagnostic_field_name(value: str) -> str:
    """Redact contact-, path-, and credential-shaped keys in diagnostics."""
    if _SUSPICIOUS_DIAGNOSTIC_FIELD.search(value):
        return "<redacted-field>"
    return value
