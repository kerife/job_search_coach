"""Shared privacy guard for dossier-to-practice projected text."""

from __future__ import annotations

import re


_FORBIDDEN_TEXT = re.compile(
    r"(?<![A-Z0-9+.-])(?:[A-Z][A-Z0-9+.-]*):(?=//|[^\s])|"
    r"\bwww\.|"
    r"(?<![A-Z0-9_])(?:~[/\\]|\.\.?[/\\]|"
    r"/(?:users|home|private|tmp|var|etc|opt|volumes|workspace)[/\\]|"
    r"[A-Z]:[/\\]|\\\\[^\s\\]+\\[^\s\\]+)|"
    r"\b(?:candidate\s+name|nombre\s+del\s+candidat[oa]|name|contact|contacto|"
    r"tel[eé]fono(?:\s+de\s+contacto)?|phone|email|correo|recruiter\s+name|"
    r"nombre\s+del\s+reclutador)\s*[:=]|"
    r"\b(?:candidate|candidat[oa]|recruiter|reclutador[ae]?)\s+"
    r"(?:name\s+|nombre\s+)?[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\s+"
    r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\b|"
    r"\b(?:mr|mrs|ms|dr|sr|sra|srta)\.?\s+"
    r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\s+"
    r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\b|"
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|"
    r"(?<!\d)(?:\+\d{1,3}[\s.-])?(?:\(?\d{2,4}\)?[\s.-])"
    r"\d{3,4}[\s.-]\d{3,4}(?!\d)|"
    r"\b(?:raw\s+(?:profile|vacancy|job\s+description|reply|source|cv|resume)|"
    r"texto\s+crudo\s+del\s+(?:perfil|puesto|mensaje|origen)|"
    r"perfil\s+de\s+linkedin|linkedin\s+profile|curriculum\s+vitae|resume)\b|"
    r"\b(?:browser(?:[_-]session)?|session|sesi[oó]n)[_-]?"
    r"(?:id|identifier|token)\s*[:=]|"
    r"\b(?:browser|session|sesi[oó]n)[_-][A-Z0-9_-]{3,}\b|"
    r"\b(?:sha(?:1|256|512)|md5|hash)\s*[:=]|"
    r"\b[A-F0-9]{32,128}\b",
    re.IGNORECASE,
)


def is_safe_handoff_text(value: object, maximum: int) -> bool:
    """Return whether text is bounded, non-empty, and safe to project."""
    return (
        isinstance(value, str)
        and bool(value.strip())
        and len(value) <= maximum
        and _FORBIDDEN_TEXT.search(value) is None
    )
