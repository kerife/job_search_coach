"""Shared privacy guard for dossier-to-practice projected text."""

from __future__ import annotations

import re
import unicodedata

from private_prose_safety import is_safe_prose_text


_FORBIDDEN_TEXT = re.compile(
    r"(?<![A-Z0-9+.-])(?:[A-Z][A-Z0-9+.-]*):(?=//|[^\s])|"
    r"\bwww\.|"
    r"(?<![A-Z0-9_])(?:~[/\\]|\.\.?[/\\]|"
    r"/(?:users|home|private|tmp|var|etc|opt|volumes|workspace|root|usr|bin|sbin|lib|lib64|system|library|applications|mnt|srv)(?:[/\\]|$)|"
    r"//[^\s/]+(?:[/\\]|$)|"
    r"[A-Z]:[/\\]|\\\\[^\s\\]+\\[^\s\\]+)|"
    r"\b(?:candidate\s+name|nombre\s+del\s+candidat[oa]|name|contact|contacto|"
    r"tel[eé]fono(?:\s+de\s+contacto)?|phone|email|correo|recruiter\s+name|"
    r"nombre\s+del\s+reclutador)\s*[:=]|"
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

_FORBIDDEN_NAME = re.compile(
    r"\b(?i:(?:candidate|candidat[oa]|recruiter|reclutador[ae]?)\s+"
    r"(?:name\s+|nombre\s+)?)"
    r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\s+"
    r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\b|"
    r"\b(?i:(?:mr|mrs|ms|dr|sr|sra|srta)\.?)\s+"
    r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\s+"
    r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\b"
)

_FORBIDDEN_CONTROL = re.compile(r"[\u0000-\u001f\u007f-\u009f\u200b-\u200d\u2060\ufeff]")

_UNLABELLED_PERSON_INTRO = re.compile(
    r"(?:^|[:.!?]\s+)"
    r"(?!(?i:senior|principal|lead|staff|software|platform|data|product|engineering|"
    r"cloud|security|technical|solutions|project|program|people|talent|customer|"
    r"account|enterprise|sales|marketing|finance|operations|strategy|user|ux|ui)\s+)"
    r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\s+"
    r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\s+"
    r"(?i:reports?|describes?|works?|has|joined|deliver(?:s|ed)?|explains?|reported|"
    r"reporta|describe|trabaja|tiene|entreg[aoó]|explica|menciona|coment[aoó]?)\b"
)


def is_safe_handoff_text(value: object, maximum: int) -> bool:
    """Return whether text is bounded, non-empty, and safe to project."""
    if not is_safe_prose_text(value) or _FORBIDDEN_CONTROL.search(value):
        return False
    normalized = unicodedata.normalize("NFKC", value)
    return (
        bool(normalized.strip())
        and len(normalized) <= maximum
        and _FORBIDDEN_TEXT.search(normalized) is None
        and _FORBIDDEN_NAME.search(normalized) is None
    )


def has_unlabelled_person_intro(value: object) -> bool:
    """Return whether prose begins a sentence with an ordinary person name."""
    return isinstance(value, str) and _UNLABELLED_PERSON_INTRO.search(
        unicodedata.normalize("NFKC", value)
    ) is not None


def is_identity_free_handoff_text(value: object, maximum: int) -> bool:
    """Return whether projected source-fact prose contains no bare person intro."""
    return is_safe_handoff_text(value, maximum) and not has_unlabelled_person_intro(value)
