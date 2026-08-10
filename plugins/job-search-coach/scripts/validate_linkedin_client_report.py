#!/usr/bin/env python3
"""Validate privacy-safe synthetic inputs for LinkedIn client reports."""

from __future__ import annotations

import argparse
import ipaddress
import json
import math
import re
import sys
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Any, NamedTuple
from urllib.parse import unquote, urlsplit


REQUIRED_BUNDLE_FIELDS = frozenset({
    "schema_version", "fixture_id", "origin_class", "derivation",
    "internal_candidate_id", "real_profile_mapping", "locale", "evaluation_date",
    "evidence_mode", "structural_state_fixture", "synthetic_fact_catalog",
    "score_ledger", "priorities", "copy_blocks", "blocked_claims",
    "source_catalog", "authorization_state", "eval_expectations",
})
STRUCTURAL_STATE_FIELDS = frozenset({"observations"})
OBSERVATION_FIELDS = frozenset({"evidence_id", "section", "state"})
FACT_FIELDS = frozenset({"fact_id", "evidence_state", "fact_type", "role_family", "capability_family", "scope_bucket", "claim_tokens"})
PRIORITY_FIELDS = frozenset({"priority_id", "rank", "section", "diagnosed_gap", "action_type", "evidence_ids", "timebox", "done_when", "impact_basis"})
COPY_FIELDS = frozenset({"copy_id", "section", "state", "audience", "problem", "fact_ids", "evidence_ids", "claim_boundary"})
SOURCE_FIELDS = frozenset({"source_id", "source_category", "source_class", "url", "publisher", "document_title", "access_date", "reachability", "scope", "inference_limit", "fallback"})
SOURCE_REQUIRED_FIELDS = SOURCE_FIELDS - {"publisher", "document_title"}
SCORE_LEDGER_FIELDS = frozenset({"numeric_weighted_total", "scored_weight", "not_scored_weight", "overall_score", "confidence", "domains"})
DOMAIN_SCORE_FIELDS = frozenset({"domain", "weight", "state", "raw_score", "weighted_points", "evidence_ids", "reason_code"})
AUTHORIZATION_FIELDS = frozenset({"inspection", "external_actions", "action_state"})
EVAL_EXPECTATION_FIELDS = frozenset({"scenario_class", "primary_gap", "primary_copy_category", "pending_evidence_policy"})

LOCALES = frozenset({"en", "es"})
EVIDENCE_MODES = frozenset({"authorized_visual_visible", "structural_only", "partial_visual_photo_only", "partial_visual_banner_only"})
OBSERVATION_SECTIONS = frozenset({"about", "banner", "completeness", "experience", "headline", "photo", "proof", "skills", "visual"})
OBSERVATION_STATES = frozenset({"absent", "not_applicable", "not_inspected", "partially_visible", "present", "visible"})
EVIDENCE_STATES = frozenset({"candidate_reported", "inferred", "unknown", "verified"})
FACT_TYPES = frozenset({"capability_signal", "proof_signal", "role_signal", "scope_signal"})
ROLE_FAMILIES = frozenset({"engineering_leadership", "platform_reliability", "technical_operations"})
CAPABILITY_FAMILIES = frozenset({"automation", "delivery", "leadership", "none", "observability", "reliability"})
SCOPE_BUCKETS = frozenset({"cross_functional", "individual", "team", "unknown"})
CLAIM_TOKENS = frozenset({"AUTOMATION", "DELIVERY", "LEADERSHIP", "OBSERVABILITY", "OUTCOME_SCOPE", "RELIABILITY", "TECHNICAL_SCOPE"})
DOMAIN_WEIGHTS = {"visual": 15, "headline": 15, "about": 15, "experience": 20, "skills": 15, "proof": 10, "completeness": 10}
SCORE_STATES = frozenset({"not_scored", "scored"})
CONFIDENCE_STATES = frozenset({"high", "medium"})
REASON_CODES = frozenset({"CONTENT_GENERAL", "CONTENT_SPECIFIC", "PARTIAL_VISUAL_NO_AGGREGATE", "PROOF_AVAILABLE", "PROOF_NOT_SCORED", "SIGNAL_DISPERSED", "STRUCTURAL_COMPLETE", "STRUCTURAL_GAP", "VISUAL_NOT_INSPECTED", "VISUAL_VISIBLE"})
PRIORITY_SECTIONS = frozenset({"about", "experience", "headline", "proof", "skills", "visual"})
DIAGNOSED_GAPS = frozenset(f"GAP-{case}-{kind}" for case in "ABCD" for kind in ("PRIMARY", "SECONDARY", "PROOF"))
ACTION_TYPES = frozenset({
    "ACTION-A-ABOUT", "ACTION-A-EXPERIENCE", "ACTION-A-HEADLINE",
    "ACTION-B-ABOUT", "ACTION-B-EXPERIENCE", "ACTION-B-HEADLINE",
    "ACTION-C-ABOUT", "ACTION-C-EVIDENCE", "ACTION-C-HEADLINE",
    "ACTION-D-ABOUT", "ACTION-D-EVIDENCE", "ACTION-D-EXPERIENCE",
})
TIMEBOXES = frozenset(f"TIMEBOX-{case}-{rank}" for case in "ABCD" for rank in range(1, 4))
DONE_WHEN_CODES = frozenset(f"DONE-WHEN-{case}-{rank}" for case in "ABCD" for rank in range(1, 4))
IMPACT_BASES = frozenset({"COACH_HEURISTIC", "CURRENT_OFFICIAL_SOURCE"})
COPY_SECTIONS = frozenset({"about_opening", "experience_bullet", "headline"})
COPY_STATES = frozenset({"omit", "ready", "requires_confirmation"})
AUDIENCES = frozenset({"HIRING_MANAGER", "RECRUITER", "TECHNICAL_PEER"})
COPY_PROBLEMS = frozenset({"GENERAL_LEADERSHIP_STORY", "MISSING_PROOF_BOUNDARY", "PARTIAL_VISUAL_CONTEXT", "STRUCTURAL_SIGNAL_GAP", "TECHNICAL_SIGNAL_DISPERSED"})
CLAIM_BOUNDARIES = frozenset({"CONFIRM_CAPABILITY_BEFORE_USE", "CONFIRM_SCOPE_BEFORE_USE", "OMIT_UNSUPPORTED_OUTCOME", "USE_ONLY_SUPPORTED_FACTS"})
BLOCKED_CLAIMS = frozenset({"CAPABILITY_UNVERIFIED", "LEADERSHIP_SCOPE_UNQUANTIFIED", "VISUAL_NOT_INSPECTED", "VISUAL_PARTIAL_NO_AGGREGATE"})
SOURCE_CATEGORIES = frozenset({"ai_hiring_agents", "cover_image", "featured_section", "good_profile", "job_match", "job_seeker_hirer_connection", "profile_photo", "skills"})
SOURCE_CLASSES = frozenset({"official", "secondary"})
REACHABILITY_STATES = frozenset({"reachable", "unreachable"})
SOURCE_SCOPES = frozenset({"PROFILE_GUIDANCE"})
INFERENCE_LIMITS = frozenset({"NO_INDIVIDUAL_OUTCOME_INFERENCE"})
SOURCE_FALLBACKS = frozenset({"BLOCK_CLAIM", "COACH_HEURISTIC"})
INSPECTION_AUTHORIZATIONS = frozenset({"authorized"})
EXTERNAL_ACTION_AUTHORIZATIONS = frozenset({"not_authorized"})
ACTION_STATES = frozenset({"not_executed"})
SCENARIO_CLASSES = frozenset({"leadership_story_general", "partial_visual_no_aggregate", "structural_no_visual", "technical_signal_dispersed"})
PRIMARY_GAPS = frozenset({"GAP-A-PRIMARY", "GAP-B-PRIMARY", "GAP-C-PRIMARY", "GAP-D-PRIMARY"})
PENDING_EVIDENCE_POLICIES = frozenset({"ASK_ONLY_IF_DECISION_CHANGES", "NO_EXTRA_VISUAL_REQUEST"})

_ID_DISCRIMINATOR = r"JSC[0-9]+"
_ID_SEGMENT = r"[A-Z0-9]+"
_ID_GRAMMARS = MappingProxyType({
    "fixture_id": rf"FIXTURE-{_ID_DISCRIMINATOR}-{_ID_SEGMENT}(?:-{_ID_SEGMENT})*",
    "internal_candidate_id": rf"CANDIDATE-{_ID_DISCRIMINATOR}-{_ID_SEGMENT}(?:-{_ID_SEGMENT})*",
    "evidence_id": rf"EVID-{_ID_DISCRIMINATOR}-{_ID_SEGMENT}(?:-{_ID_SEGMENT})*",
    "fact_id": rf"FACT-{_ID_DISCRIMINATOR}-{_ID_SEGMENT}(?:-{_ID_SEGMENT})*",
    "priority_id": rf"PRIORITY-{_ID_DISCRIMINATOR}-{_ID_SEGMENT}(?:-{_ID_SEGMENT})*",
    "copy_id": rf"COPY-{_ID_DISCRIMINATOR}-{_ID_SEGMENT}(?:-{_ID_SEGMENT})*",
    "source_id": rf"SOURCE-{_ID_DISCRIMINATOR}-{_ID_SEGMENT}(?:-{_ID_SEGMENT})*",
})
_ID_PATTERNS = {
    field: re.compile(rf"^{grammar}$")
    for field, grammar in _ID_GRAMMARS.items()
}
REPORT_IDENTIFIER = re.compile(
    rf"(?<![A-Z0-9-])(?:{'|'.join(_ID_GRAMMARS.values())})"
    r"(?![A-Z0-9-])"
)
IDENTIFIER_SEPARATOR_LIKE = frozenset("_\u00ad‐‑‒–—―−⁃")
PRIORITY_CODE_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9]*(?:[-_][A-Z0-9]+)+$"
)
PRIORITY_TIMEBOX_PATTERN = re.compile(
    r"^(?:[1-9]\d{0,2}m|TIMEBOX-[A-Z0-9]+(?:-[A-Z0-9]+)+)$"
)
_EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
_PHONE = re.compile(
    r"(?:\+\d{7,15}\b|\+\d{1,3}(?:[ .()-]*\d){7,14}\b|"
    r"(?:\+\d{1,3}[ .-]?)?(?:\(?\d{3}\)?[ .-])\d{3}[ .-]\d{4})"
)
_PROFILE_URL = re.compile(r"https?://(?:[a-z0-9-]+\.)?linkedin\.com/in/", re.I)
_LOCAL_PATH = re.compile(r"(?:^|\s)(?:/Users/|/home/|[A-Z]:[/\\])", re.I)
_ANY_URL = re.compile(r"(?:https?|file)://", re.I)
_FORBIDDEN_URI_PREFIXES = (("tel:", "phone-like"), ("file:", "local-path"))
SOURCE_REGISTRY_PATH = Path(__file__).with_name("linkedin_source_registry.json")
PROVENANCE_LIMITS = MappingProxyType({"publisher": 120, "document_title": 240})
_PROVENANCE_LINE_BREAK = re.compile(r"[\n\r\v\f\x1c-\x1e\u0085\u2028\u2029]")
_SECONDARY_PRIVATE_HOST_SUFFIXES = (
    ".home",
    ".internal",
    ".lan",
    ".local",
    ".localdomain",
)
_SECONDARY_SPECIAL_USE_HOST_SUFFIXES = (
    ".alt",
    ".arpa",
    ".example",
    ".invalid",
    ".localhost",
    ".onion",
    ".test",
)
_SECONDARY_RESERVED_EXAMPLE_HOSTS = frozenset({"example.com", "example.net", "example.org"})
_SENSITIVE_KEY_COMPONENTS = frozenset({
    "auth", "authorization", "bearer", "contact", "cookie", "credential", "email", "key",
    "pass", "passwd", "password", "phone", "secret", "session", "token",
})
_SENSITIVE_COMPACT_KEY_PARTS = (
    "accesstoken", "apikey", "authorization", "bearer", "clientsecret", "cookie",
    "credential", "password", "passwd", "privatekey", "secret", "session", "token",
)
FORBIDDEN_PLACEHOLDERS = frozenset({"x", "criteria", "generic", "tbd"})
SAFETY_TOKEN_CLASSES = {
    "visual": frozenset({"banner", "foto", "imagen", "image", "photo", "visual"}),
    "protected": frozenset({
        "age", "disability", "discapacidad", "edad", "embarazada", "embarazo",
        "ethnicity", "etnia", "gender", "genero", "health", "hombre", "joven",
        "man", "mayor", "mujer", "nacionalidad", "nationality", "old", "orientacion",
        "pregnancy", "pregnant", "race", "raza", "religion", "salud", "sexual",
        "woman", "young",
    }),
    "completed_action": frozenset({
        "aplicado", "aplicada", "aplicados", "aplicadas", "applied", "compartido",
        "compartida", "compartidos", "compartidas", "comparti", "conectado",
        "conectada", "conectados", "conectadas", "conecte", "connected", "changed",
        "cambie", "edited", "edite", "enviado", "enviada", "enviados", "enviadas",
        "envie", "messaged",
        "mensajeado", "mensajeada", "posted", "posteado", "posteada", "postulado",
        "postulada", "postule", "presentado", "presentada", "presentados", "presentadas",
        "presentar", "presente", "presento", "programado", "programada", "programe",
        "published", "publicado", "publicada", "publique", "scheduled", "sent", "shared",
        "subido", "subida", "subi", "submit", "submits", "submitted", "submitting",
        "updated", "actualizado", "actualizada", "actualice", "uploaded",
    }),
    "guarantee": frozenset({
        "asegura", "aseguran", "ensure", "ensures", "garantiza", "garantizan",
        "guarantee", "guarantees",
    }),
    "certainty": frozenset({
        "certain", "certainly", "cierta", "ciertas", "cierto", "ciertos",
        "definite", "definitely", "definitiva", "definitivamente", "definitivo",
        "inevitable", "inevitables", "inevitably", "segura", "seguramente", "seguro",
    }),
    "causation": frozenset({
        "aumenta", "aumentan", "aumentar", "aumentara", "boost", "boosts", "cause",
        "causa", "causan", "causar", "causara", "causes", "conduce", "conducen",
        "conducir", "conducira", "conduciran", "consigue", "consiguen", "conseguir",
        "conseguira", "deliver", "delivers", "drive", "drives", "entrega", "entregan",
        "entregar", "genera", "generan", "generar", "generara", "get", "gets",
        "increase", "increases", "incrementa", "incrementan", "incrementar", "impulsa",
        "impulsan", "impulsar", "lead", "leads", "lleva", "llevan", "llevar",
        "llevara", "llevaran", "obtiene", "obtienen", "obtener", "obtendra", "produce",
        "producen", "producir", "producira", "produces", "result", "resulta",
        "resultan", "resultar", "resultara", "resultaran", "results",
    }),
    "outcome": frozenset({
        "contratacion", "empleo", "hiring", "interview", "interviews", "entrevista",
        "entrevistas", "job", "ranking", "response", "responses", "respuesta", "respuestas",
    }),
    "probability": frozenset({
        "chance", "chances", "odds", "percent", "percentage", "porcentaje",
        "posibilidad", "posibilidades", "probabilidad", "probability",
    }),
    "individual": frozenset({
        "candidate", "candidata", "candidato", "individual", "persona", "personal",
        "ti", "tu", "tus", "usted", "you", "your", "yours",
    }),
    "external_surface": frozenset({
        "application", "applications", "headline", "linkedin", "message", "messages",
        "mensaje", "mensajes", "perfil", "post", "profile", "recruiter", "recruiters",
        "reclutador", "reclutadores", "reclutamiento", "screen", "solicitud",
        "solicitudes", "titular", "vacancy", "vacante", "interview", "entrevista",
    }),
    "score": frozenset({"puntaje", "score"}),
    "math": frozenset({"calculo", "math", "multiplicador", "multiplier"}),
    "request_verb": frozenset({
        "adjunta", "comparte", "envia", "manda", "need", "needed", "needs", "necesita",
        "necesitamos", "necesito", "provide", "require", "required", "requires", "send",
        "share", "solicita", "solicito", "sube", "upload",
    }),
    "evidence_object": frozenset({
        "actividad", "activity", "banner", "captura", "evidence", "evidencia", "foto",
        "image", "imagen", "photo", "profile", "screenshot", "text", "texto",
    }),
    "visual_evidence_object": frozenset({
        "actividad", "activity", "banner", "captura", "foto", "image", "imagen", "photo",
        "screenshot",
    }),
}
SAFETY_CONTROLLED_TERMS = frozenset().union(*SAFETY_TOKEN_CLASSES.values())
_CONTROLLED_TERM_PATTERNS = tuple(
    (
        term,
        re.compile(
            rf"(?<![a-z0-9]){r'[\W_]*'.join(re.escape(character) for character in term)}(?![a-z0-9])"
        ),
    )
    for term in SAFETY_CONTROLLED_TERMS
)
RAW_PROFILE_ALIAS = re.compile(
    r"\b(?:raw[_ -]?profile[_ -]?(?:text|data|export)|profile[_ -]?(?:ocr|raw[_ -]?text))\b",
    re.I,
)
PRIVATE_ANALYTICS_ALIAS = re.compile(
    r"\b(?:analytics[_ -]?value|search[_ -]?appearances[_ -]?count|profile[_ -]?views[_ -]?count)\b",
    re.I,
)
CONFIRMATION_MARKER = re.compile(r"\[\s*confirmar\s+despu[eé]s\s*\]", re.I)
INFERENCE_PREDICATE = re.compile(
    r"\b(?:aparenta|aparento|appeared|appears?|indica|indicated|indicates?|indico|infiere|infiero|"
    r"infer(?:red|ir|s?)?|infieras?|looked|looks?|parece|revela|revel(?:o|ó)|revealed|"
    r"parecia|reveals?|showed|shows?|sugiere|sugiri(?:o|ó)|suggested|suggests?)\b",
    re.I,
)
SAFETY_CLAUSE_BOUNDARY = re.compile(
    r"(?:;|,\s*(?:but|however|pero)\b|\b(?:but|however|pero|sin\s+embargo)\b)",
    re.I,
)
INFERENCE_COORDINATOR = re.compile(r"\b(?:and|e|y)\b", re.I)
INFERENCE_NEGATION = re.compile(
    r"(?:\b(?:do|does|did|must|should|could|will|would)\s+not|"
    r"\b(?:ca|could|do|does|did|must|should|will|would)n['’]?t|\bcannot|"
    r"\b(?:is|are|was|were)\s+not(?:\s+(?:accurately|clearly|reliably))*\s+able\s+to|"
    r"\b(?:never|not|nunca|jamas|sin)|"
    r"\bno(?:\s+(?:se|nos))?(?:\s+(?:debe|debemos|puede|podemos|permite|permiten))?)"
    r"(?:\s+(?:accurately|claramente|clearly|fiablemente|reliably|reasonably|safely|validly))*"
    r"(?:\s+(?:(?:be\s+)?used\s+to|usar\s+para|(?:appear|seem)s?\s+to|parece))?"
    r"(?:\s+(?:accurately|claramente|clearly|fiablemente|reliably|reasonably|safely|validly))*"
    r"\s*$",
    re.I,
)
EXECUTED_EXTERNAL_ACTION = re.compile(
    r"\b(?:"
    r"(?:i|we)(?:\s+(?:have|had)|['’](?:d|ve))?\s+"
    r"(?:(?:already|just|now|previously|recently|successfully)\s+){0,2}"
    r"(?:edited|updated|changed|sent|uploaded|applied|registered|scheduled|published|posted|shared|"
    r"connected|messaged|presented|submitted)|"
    r"(?:was|were|has|have|had)\s+"
    r"(?:(?:already|just|now|previously|recently|successfully)\s+){0,2}"
    r"(?:been\s+)?(?:(?:already|just|now|recently|successfully)\s+){0,2}"
    r"(?:edited|updated|changed|sent|uploaded|applied|registered|scheduled|published|posted|shared|"
    r"connected|messaged|presented|submitted)|"
    r"(?:yo\s+)?(?:(?:ya|finalmente|recientemente)\s+){0,2}"
    r"(?:edité|actualicé|cambié|envié|subí|apliqué|programé|publiqué|"
    r"compartí|presenté)|"
    r"me\s+(?:(?:ya|finalmente|recientemente)\s+){0,2}(?:postulé|conecté|"
    r"registré|inscribí)|"
    r"nos\s+(?:(?:ya|finalmente|recientemente)\s+){0,2}(?:postulamos|inscribimos)|"
    r"(?:(?:nosotros|nosotras)\s+)?(?:(?:ya|finalmente|recientemente)\s+){0,2}"
    r"(?:editamos|actualizamos|cambiamos|enviamos|subimos|aplicamos|programamos|"
    r"publicamos|compartimos|conectamos|postulamos|inscribimos|presentamos|registramos)|"
    r"(?:he|hemos)\s+(?:(?:ya|finalmente|recientemente)\s+){0,2}"
    r"(?:editad[oa]s?|actualizad[oa]s?|cambiad[oa]s?|enviad[oa]s?|subid[oa]s?|"
    r"aplicad[oa]s?|postulad[oa]s?|programad[oa]s?|publicad[oa]s?|compartid[oa]s?|"
    r"conectad[oa]s?|presentad[oa]s?|registrad[oa]s?)|"
    r"(?:fue|fueron|ha\s+sido|han\s+sido)\s+"
    r"(?:(?:ya|finalmente|recientemente|exitosamente)\s+){0,2}"
    r"(?:editad[oa]s?|actualizad[oa]s?|cambiad[oa]s?|enviad[oa]s?|subid[oa]s?|"
    r"aplicad[oa]s?|postulad[oa]s?|programad[oa]s?|publicad[oa]s?|compartid[oa]s?|"
    r"conectad[oa]s?|presentad[oa]s?|registrad[oa]s?)|"
    r"se\s+(?:(?:ya|finalmente|recientemente)\s+){0,2}"
    r"(?:editó|actualizó|cambió|envió|subió|aplicó|programó|publicó|"
    r"compartió|conectó|inscribió|postuló|presentó|registró)"
    r")\b",
    re.I,
)
APPLICATION_DESTINATION_TAIL = (
    r"(?:[ \t]+(?:on|through|to|via)[ \t]+"
    r"(?=[^.!?¡¿;\n]{1,64}[ \t]*$)"
    r"[a-z0-9](?:[a-z0-9&(),' \t-]{0,62}[a-z0-9)])?)?"
)
EXTERNAL_ACTION_TARGETS = (
    (
        re.compile(
            r"\b(?:changed|cambi(?:amos|é|ó|ad[oa]s?)|edited|edit(?:amos|é|ó|ad[oa]s?)|"
            r"updated|actualicé|actualiz(?:amos|ó|ad[oa]s?))\b",
            re.I,
        ),
        re.compile(
            r"\b(?:linkedin[^.!?¡¿;\n]{0,32}(?:profile|headline|perfil|titular)|"
            r"(?:profile|headline|perfil|titular)[^.!?¡¿;\n]{0,32}linkedin|"
            r"your\s+(?:profile|headline)|tu\s+(?:perfil|titular))\b",
            re.I,
        ),
    ),
    (
        re.compile(r"\b(?:sent|messaged|envi(?:amos|é|ó|ad[oa]s?))\b", re.I),
        re.compile(
            r"\b(?:sent[ \t]+(?:the[ \t]+recruiter[ \t]+(?:a[ \t]+)?message|"
            r"(?:a|the)[ \t]+recruiter[ \t]+message|"
            r"(?:a|the)[ \t]+message[ \t]+to[ \t]+(?:a|the)[ \t]+recruiter)"
            r"(?:[ \t]+(?:on|through|via)[ \t]+linkedin)?[ \t]*$|"
            r"messaged[ \t]+(?:(?:a|the)[ \t]+)?recruiter"
            r"(?:[ \t]+on[ \t]+linkedin)?[ \t]*$|"
            r"recruiter[ \t]+messages?[ \t]+(?:was|were)[ \t]+"
            r"(?:successfully[ \t]+)?sent(?:[ \t]+on[ \t]+linkedin)?[ \t]*$|"
            r"messages?[ \t]+to[ \t]+(?:the[ \t]+)?recruiter[ \t]+"
            r"(?:was|were)[ \t]+sent[ \t]*$|"
            r"envi(?:amos|é|ó|ad[oa]s?)[ \t]+(?:un|el|los)?[ \t]*mensajes?"
            r"[ \t]+(?:al|a[ \t]+los?)[ \t]+reclutador(?:es)?(?:[ \t]+en[ \t]+linkedin)?[ \t]*$|"
            r"mensajes?[ \t]+(?:al|a[ \t]+los?)[ \t]+reclutador(?:es)?"
            r"[ \t]+(?:fue|fueron)[ \t]+enviad[oa]s?"
            r"(?:[ \t]+en[ \t]+linkedin)?[ \t]*$)",
            re.I,
        ),
    ),
    (
        re.compile(r"\b(?:uploaded|sub(?:í|ió|imos|id[oa]s?))\b", re.I),
        re.compile(
            r"\b(?:uploaded[ \t]+(?:(?:a|an|my|our|the|your)[ \t]+)?"
            r"(?:asset|banner|cv|file|image|photo|resume)[ \t]+"
            r"(?:on|onto|to)[ \t]+linkedin[ \t]*$|"
            r"sub(?:í|ió|imos|id[oa]s?)[ \t]+(?:(?:el|la|los|un|una)[ \t]+)?"
            r"(?:archivo|banner|cv|foto|imagen|recurso)[ \t]+(?:a|en)[ \t]+linkedin[ \t]*$)",
            re.I,
        ),
    ),
    (
        re.compile(
            r"\b(?:applied|presented|registered|submitted|apliqué|aplic(?:amos|ó|ad[oa]s?)|"
            r"inscrib(?:í|ió|imos)|postul(?:é|ó|amos|ad[oa]s?)|"
            r"present(?:é|ó|amos|ad[oa]s?)|registr(?:é|ó|amos|ad[oa]s?))\b",
            re.I,
        ),
        re.compile(
            r"\b(?:applied[ \t]+(?:to|for)[ \t]+(?:(?:a|an|the|this|that)[ \t]+)?(?:job|vacancy)|"
            r"registered[ \t]+(?:to|for)[ \t]+(?:(?:a|an|the|this|that)[ \t]+)?(?:job|vacancy)|"
            r"presented[ \t]+(?:(?:a|an|my|our|the|your)[ \t]+)?application"
            rf"{APPLICATION_DESTINATION_TAIL}"
            r"(?:[ \t]+(?:today|yesterday))?[ \t]*$|"
            r"submitted[ \t]+(?:(?:a|an|my|the|your)[ \t]+)?(?:job[ \t]+)?"
            r"application(?:[ \t]+(?:already|today|yesterday))?"
            rf"{APPLICATION_DESTINATION_TAIL}"
            r"(?:[ \t]+(?:already|today|yesterday))?[ \t]*$|"
            r"applications?[^.!?¡¿;\n]{0,32}\b(?:was|were|has[ \t]+been|have[ \t]+been)\b"
            r"[^.!?¡¿;\n]{0,16}\b(?:presented|registered|submitted)\b|"
            r"(?:(?:me|nos|se)[ \t]+)?(?:apliqué|aplicamos|aplicó|inscribí|inscribió|"
            r"inscribimos|postulé|postulamos|postuló|presenté|presentamos|presentó|"
            r"registré|registramos|registró)"
            r"[^.!?¡¿;\n]{0,32}\b(?:solicitud(?:es)?|vacante)\b|"
            r"solicitud(?:es)?[^.!?¡¿;\n]{0,32}\b(?:fue|fueron|ha[ \t]+sido|han[ \t]+sido)\b"
            r"[^.!?¡¿;\n]{0,16}\b(?:presentad|registrad)[oa]s?\b)",
            re.I,
        ),
    ),
    (
        re.compile(r"\b(?:scheduled|program(?:é|amos|ó|ad[oa]s?))\b", re.I),
        re.compile(
            r"\b(?:scheduled[ \t]+(?:(?:a|an|the)[ \t]+)?"
            r"(?:interview(?:[ \t]+with[ \t]+(?:the[ \t]+)?recruiter)?|"
            r"recruiter[ \t]+screen)(?:[ \t]+(?:today|yesterday))?[ \t]*$|"
            r"(?:interview|recruiter[ \t]+screen)[ \t]+(?:was|were)[ \t]+scheduled\b|"
            r"program(?:é|amos|ó|ad[oa]s?)[ \t]+(?:la[ \t]+)?entrevista"
            r"(?:[ \t]+con[ \t]+(?:el[ \t]+)?reclutamiento)?[ \t]*$)",
            re.I,
        ),
    ),
    (
        re.compile(
            r"\b(?:published|posted|shared|publiqué|public(?:amos|ó|ad[oa]s?)|"
            r"compart(?:imos|í|ió|id[oa]s?))\b",
            re.I,
        ),
        re.compile(
            r"\b(?:(?:published|posted|shared)[ \t]+"
            r"(?:(?:a|my|our|the|your)[ \t]+)?post"
            r"(?:[ \t]+(?:on|through|to)[ \t]+linkedin)?[ \t]*$|"
            r"post[ \t]+(?:was|were)[ \t]+(?:published|posted|shared)[ \t]*$|"
            r"(?:publiqué|public(?:amos|ó|ad[oa]s?)|compart(?:imos|í|ió|id[oa]s?))"
            r"[ \t]+(?:(?:el|un)[ \t]+)?post(?:[ \t]+en[ \t]+linkedin)?[ \t]*$|"
            r"(?:publiqué|public(?:amos|ó|ad[oa]s?))[ \t]+(?:el[ \t]+)?"
            r"(?:perfil|titular)(?:[ \t]+[a-záéíóúñ]+){0,3}"
            r"[ \t]+en[ \t]+linkedin[ \t]*$)",
            re.I,
        ),
    ),
    (
        re.compile(r"\b(?:connected|conect(?:amos|é|ó|ad[oa]s?))\b", re.I),
        re.compile(
            r"\b(?:connected[ \t]+with[ \t]+(?:(?:a|the)[ \t]+)?recruiter"
            r"(?:[ \t]+on[ \t]+linkedin)?[ \t]*$|"
            r"(?:(?:me|nos|se)[ \t]+)?conect(?:amos|é|ó|ad[oa]s?)"
            r"[ \t]+con[ \t]+(?:el[ \t]+)?reclutador(?:es)?"
            r"(?:[ \t]+en[ \t]+linkedin)?[ \t]*$)",
            re.I,
        ),
    ),
)
EXTERNAL_ACTION_NEGATION = re.compile(
    r"\b(?:no|nunca|jamás)(?:\s+(?:la|las|le|les|lo|los|me|nos|se|te)){0,2}\s*$",
    re.I,
)
CREDENTIAL_ASSIGNMENT = re.compile(
    r"\b(?:access[ _-]{0,3}token|refresh[ _-]{0,3}token|api[ _-]{0,3}key|password|"
    r"passwd|private[ _-]{0,3}key|client[ _-]{0,3}secret|"
    r"credential[ _-]{0,3}(?:key|token|value)|secret[ _-]{0,3}(?:key|token|value))"
    r"\b\s*[:=]\s*"
    r"[\"']?[A-Za-z0-9][A-Za-z0-9_./+=:-]{7,}",
    re.I,
)
GENERIC_CREDENTIAL_LABEL = re.compile(
    r"\b(credential|secret)\b[ \t]*([:=])[ \t]*([^\r\n.!?;]{1,120})",
    re.I,
)
OPAQUE_CREDENTIAL_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./+=:-]{15,}")
CAREER_CREDENTIAL_TERMS = frozenset({
    "administrator", "architect", "associate", "certification", "certified",
    "engineer", "professional",
})
CAREER_CREDENTIAL_SUFFIXES = frozenset({"based", "v", "version"})
FORBIDDEN_CAREER_CREDENTIAL_COMPONENTS = frozenset({
    "key", "password", "private", "secret", "token", "value",
})
CREDENTIAL_COMPONENT = re.compile(
    r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|[A-Z]+|\d+"
)
AUTHORIZATION_HEADER = re.compile(
    r"\bauthorization\s*:\s*(?:bearer|basic)\s+"
    r"[A-Za-z0-9][A-Za-z0-9_./+=:-]{7,}",
    re.I,
)
OUTCOME_GUARANTEE = re.compile(
    r"\b(?:garantiza|garantizar[aá]|asegura|guarantees?|will\s+(?:guarantee|get))\b"
    r"[^.\n]{0,100}\b(?:ranking|respuesta|reclutador(?:es)?|entrevista(?:s)?|contrataci[oó]n|"
    r"recruiter\s+responses?|interviews?|hiring|job|employment)\b",
    re.I,
)
INSPECTION_AUTHORIZATION_INFERENCE = re.compile(
    r"(?:(?:inspecci[oó]n|inspection)[^.\n]{0,100}(?:autoriza|authori[sz]es?|permits?)|"
    r"(?:authorized|autorizada)\s+(?:profile\s+)?(?:inspection|inspecci[oó]n)"
    r"[^.\n]{0,100}(?:permits?|autoriza))"
    r"[^.\n]{0,80}(?:publicar|editar|conectar|mensaj|aplicar|cargar|compartir|"
    r"publish|edit|connect|message|apply|upload|share)",
    re.I,
)

SECTION_KEYS = (
    "verdict",
    "score",
    "priorities",
    "copy",
    "do_not_change",
    "plan",
    "evidence_needed",
    "boundaries",
)
HEADING_MAP = {
    "es": {
        "title": "Diagnóstico ejecutivo de LinkedIn",
        "verdict": "Veredicto",
        "score": "Calificación",
        "priorities": "Las tres decisiones prioritarias",
        "copy": "Copy listo para revisar",
        "do_not_change": "No cambies todavía",
        "plan": "Plan privado de siete días",
        "evidence_needed": "Evidencia pendiente",
        "boundaries": "Límites del diagnóstico",
        "appendix": "Apéndice de evidencia",
    },
    "en": {
        "title": "LinkedIn Executive Diagnostic",
        "verdict": "Verdict",
        "score": "Score",
        "priorities": "Three priority decisions",
        "copy": "Copy ready for review",
        "do_not_change": "Do not change yet",
        "plan": "Private seven-day plan",
        "evidence_needed": "Evidence needed",
        "boundaries": "Diagnostic boundaries",
        "appendix": "Evidence appendix",
    },
}
SCORE_TABLE_HEADERS = {
    "es": ("Dimensión", "Estado", "Puntaje", "Evidencia", "Razón"),
    "en": ("Dimension", "Status", "Score", "Evidence", "Reason"),
}
SCORE_DOMAIN_LABELS = {
    "es": {
        "Identidad visual": "visual",
        "Titular": "headline",
        "Acerca de": "about",
        "Experiencia": "experience",
        "Aptitudes": "skills",
        "Prueba": "proof",
        "Completitud": "completeness",
    },
    "en": {
        "Visual identity": "visual",
        "Headline": "headline",
        "About": "about",
        "Experience": "experience",
        "Skills": "skills",
        "Proof": "proof",
        "Completeness": "completeness",
    },
}
SCORE_STATE_LABELS = {
    "es": {"Evaluada": "scored", "No evaluado": "not_scored"},
    "en": {"Scored": "scored", "Not scored": "not_scored"},
}
SCORE_METADATA = {
    "es": {
        "overall": re.compile(r"^\*\*Calificación global:\*\*\s*(\d{1,3})/100$"),
        "coverage": re.compile(r"^\*\*Cobertura:\*\*\s*(\d{1,3}) evaluado; (\d{1,3}) no evaluado$"),
        "confidence": re.compile(r"^\*\*Confianza:\*\*\s*(alta|media)$"),
        "confidence_values": {"alta": "high", "media": "medium"},
    },
    "en": {
        "overall": re.compile(r"^\*\*Overall score:\*\*\s*(\d{1,3})/100$"),
        "coverage": re.compile(r"^\*\*Coverage:\*\*\s*(\d{1,3}) scored; (\d{1,3}) not scored$"),
        "confidence": re.compile(r"^\*\*Confidence:\*\*\s*(high|medium)$"),
        "confidence_values": {"high": "high", "medium": "medium"},
    },
}
PRIORITY_SECTION_LABELS = {
    "es": {
        "Titular": "headline",
        "Acerca de": "about",
        "Experiencia": "experience",
        "Prueba": "proof",
        "Aptitudes": "skills",
        "Identidad visual": "visual",
    },
    "en": {
        "Headline": "headline",
        "About": "about",
        "Experience": "experience",
        "Proof": "proof",
        "Skills": "skills",
        "Visual identity": "visual",
    },
}
COPY_SECTION_LABELS = {
    "es": {
        "Titular": "headline",
        "Apertura de About": "about_opening",
        "Bullet de experiencia": "experience_bullet",
    },
    "en": {
        "Headline": "headline",
        "About opening": "about_opening",
        "Experience bullet": "experience_bullet",
    },
}
PRIORITY_FIELD_LABELS = {
    "es": {
        "Brecha": "diagnosed_gap",
        "Acción": "action_type",
        "Evidencia": "evidence_ids",
        "Tiempo": "timebox",
        "Terminado cuando": "done_when",
        "Base de impacto": "impact_basis",
    },
    "en": {
        "Gap": "diagnosed_gap",
        "Action": "action_type",
        "Evidence": "evidence_ids",
        "Timebox": "timebox",
        "Done when": "done_when",
        "Impact basis": "impact_basis",
    },
}
COPY_FIELD_LABELS = {
    "es": {
        "ID": "copy_id",
        "Estado": "state",
        "Audiencia": "audience",
        "Problema": "problem",
        "Hechos": "fact_ids",
        "Evidencia": "evidence_ids",
        "Frontera del claim": "claim_boundary",
        "Claims": "claims",
        "Copy": "actual_copy",
    },
    "en": {
        "ID": "copy_id",
        "State": "state",
        "Audience": "audience",
        "Problem": "problem",
        "Facts": "fact_ids",
        "Evidence": "evidence_ids",
        "Claim boundary": "claim_boundary",
        "Claims": "claims",
        "Copy": "actual_copy",
    },
}
COPY_STATE_LABELS = {
    "es": {
        "listo": "ready",
        "requiere confirmación": "requires_confirmation",
        "omitir": "omit",
    },
    "en": {
        "ready": "ready",
        "requires confirmation": "requires_confirmation",
        "omit": "omit",
    },
}
PRIMARY_COPY_CATEGORY_LABEL = {
    "es": "Categoría de copy principal",
    "en": "Primary copy category",
}
BLOCKED_CLAIM_LABELS = {"es": "Claim bloqueado", "en": "Blocked claim"}
PRIVATE_PLAN_LABEL_ACTIONS = {
    "es": {
        "Perfil": "PROFILE_REVIEW",
        "Copy": "COPY_VALIDATE",
        "Evidencia": "EVIDENCE_REQUEST",
        "Prueba": "PROOF_PREPARE",
    },
    "en": {
        "Profile": "PROFILE_REVIEW",
        "Copy": "COPY_VALIDATE",
        "Evidence": "EVIDENCE_REQUEST",
        "Proof": "PROOF_PREPARE",
    },
}
PRIVATE_PLAN_ACTION_TARGETS = {
    "PROFILE_REVIEW": frozenset({"headline", "about_opening", "experience_example"}),
    "COPY_VALIDATE": frozenset({"headline", "about_opening", "experience_example"}),
    "EVIDENCE_REQUEST": frozenset({"pending_fact", "visual_boundary"}),
    "PROOF_PREPARE": frozenset({"experience_example", "pending_fact"}),
}
QUESTION_HEADING = {"es": "Pregunta", "en": "Question"}
QUESTION_FIELD_LABELS = {
    "es": {"Pregunta": "question", "Hecho": "fact_id", "Puede cambiar": "decision"},
    "en": {"Question": "question", "Fact": "fact_id", "Can change": "decision"},
}
GENERIC_PRIORITY_CODES = frozenset({
    "improve_profile", "improve_your_profile", "optimize_profile", "enhance_profile",
    "add_keywords", "add_more_keywords", "create_content", "post_content",
    "create_posts", "be_more_attractive", "mejorar_perfil", "agregar_keywords",
    "crear_contenido", "ser_mas_atractivo",
})
PRIVATE_PLAN_FORBIDDEN_STEMS = frozenset({
    "agend", "aplic", "appl", "aval", "call", "carg", "coment", "comment",
    "compan", "compart", "conect", "connect", "conex", "contact", "correo", "curs",
    "cookie", "course", "credential", "email", "empres", "endors", "entrevist", "extern", "follow",
    "gust", "invit", "like", "llam", "mail", "mensaj", "messag", "network",
    "outreach", "passwd", "password", "post", "postul", "program", "public", "publish", "reach",
    "recomend", "reclut", "recruit", "respald", "schedul", "segu", "shar",
    "secret", "send", "session", "solicitud", "token", "upload",
})
PRIVATE_PLAN_FORBIDDEN_TOKENS = frozenset({"red"})
PRIVATE_PLAN_NO_EXTERNAL_ACTION = {
    "es": frozenset({
        "No se ejecuta ninguna acción externa.",
        "No hay acción externa.",
    }),
    "en": frozenset({"No external action is performed."}),
}
QUESTION_PLACEHOLDER_PREFIXES = frozenset({
    "n/a", "n a", "na", "pending", "placeholder", "question", "tbd", "todo",
    "to be determined", "unknown", "desconocido", "desconocida", "pendiente",
    "pregunta", "por definir", "sin definir",
})
APPENDIX_MODES = frozenset({"normal", "debug", "eval", "detail_requested"})
CONTRACT_TOKEN = re.compile(
    r"(?<![A-Za-z0-9_])(?:candidate_id|linkedin_[a-z0-9_]+)\s*=",
    re.I,
)
CANONICAL_CONTRACT_ROW = re.compile(
    r"(?m)^ {0,3}-[ \t]*(?:verified|candidate-reported|inferred|unknown):"
    r"[^\n]*\b[a-z][a-z0-9_]*=[^;\n]+;[ \t]*[^\n]*\b[a-z][a-z0-9_]*=[^\n]*$",
    re.I,
)
CANDIDATE_ID_KEY = re.compile(r"(?<![A-Za-z0-9_])candidate_id\s*=", re.I)
CANDIDATE_ID_VALUE = re.compile(
    r"(?<![A-Za-z0-9_])candidate_id\s*=\s*([^;\s]+)",
    re.I,
)
_WORD = re.compile(r"\b[^\W_]+(?:[’'-][^\W_]+)*\b", re.UNICODE)


class ParsedClientReport(NamedTuple):
    """Immutable structural split of the visible report and its appendix."""

    locale: str
    client_report: str
    evidence_appendix: str
    section_bodies: Mapping[str, str]


class ReportDomainScore(NamedTuple):
    """One normalized, client-visible score-table row."""

    domain: str
    state: str
    score: int | None
    evidence_ids: tuple[str, ...]
    reason: str


class ReportPriority(NamedTuple):
    """One normalized client-visible priority block."""

    rank: int
    section: str
    diagnosed_gap: str
    action_type: str
    evidence_ids: tuple[str, ...]
    timebox: str
    done_when: str
    impact_basis: str
    present_fields: frozenset[str]


class ReportCopyBlock(NamedTuple):
    """One normalized client-visible copy decision."""

    copy_id: str
    section: str
    state: str
    audience: str
    problem: str
    fact_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    claim_boundary: str
    claims: tuple[str, ...]
    actual_copy: str
    present_fields: frozenset[str]


class EvidenceQuestion(NamedTuple):
    """One pending-evidence question linked to a decision."""

    rank: int
    question: str
    fact_id: str
    decision: str
    present_fields: frozenset[str]


class _InvalidScoreBundle(ValueError):
    """Internal marker for malformed score-ledger inputs."""


class _InvalidDecisionBundle(ValueError):
    """Internal marker for malformed decision-ledger inputs."""


LEGACY_APPENDIX_SECTION_KEYS = (
    "coach_brief",
    "executive_diagnosis",
    "visibility_gaps",
    "positioning",
    "rewrites",
    "networking_drafts",
    "content_plan",
    "experiment_plan",
    "approval_gates",
    "audit_priority_matrix",
    "keyword_evidence_matrix",
    "outreach_funnel",
    "proof_asset_matrix",
    "linkedin_funnel_events",
)


class LegacyAppendixSection(NamedTuple):
    """One ordered legacy appendix section and its canonical rows."""

    key: str
    body: str
    rows: tuple[str, ...]


def load_bundle(path: Path) -> dict[str, object]:
    """Load a fixture bundle and require a JSON object at the file boundary."""
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_json_object,
    )
    if not isinstance(value, dict):
        raise ValueError("fixture must be a JSON object")
    return value


def _split_markdown_lines(
    markdown: str,
    *,
    keepends: bool = False,
) -> tuple[str, ...]:
    """Split only on the CRLF, LF, and CR line endings Markdown recognizes."""
    lines = tuple(
        match.group(0)
        for match in re.finditer(r"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+", markdown)
    )
    if keepends:
        return lines
    return tuple(
        line[:-2]
        if line.endswith("\r\n")
        else line[:-1]
        if line.endswith(("\r", "\n"))
        else line
        for line in lines
    )


def _trim_markdown_whitespace(text: str) -> str:
    """Trim only Markdown spaces, tabs, and recognized line endings."""
    return text.strip(" \t\r\n")


def _markdown_indent(line: str) -> tuple[int, int]:
    """Return leading-character count and visual columns using four-column tabs."""
    characters = 0
    columns = 0
    for character in line:
        if character == " ":
            columns += 1
        elif character == "\t":
            columns += 4 - (columns % 4)
        else:
            break
        characters += 1
    return characters, columns


def _classify_markdown_lines(markdown: str) -> tuple[tuple[str, bool], ...]:
    """Return each Markdown line with whether CommonMark treats it as code."""
    classified: list[tuple[str, bool]] = []
    fence_marker = ""
    fence_length = 0
    for line in _split_markdown_lines(markdown):
        if fence_marker:
            classified.append((line, True))
            closing = re.fullmatch(
                rf" {{0,3}}{re.escape(fence_marker)}{{{fence_length},}}[ \t]*",
                line,
            )
            if closing is not None:
                fence_marker = ""
                fence_length = 0
            continue

        indent_characters, indent_columns = _markdown_indent(line)
        if indent_columns >= 4:
            classified.append((line, True))
            continue

        opening = re.match(r"^(`{3,}|~{3,})(.*)$", line[indent_characters:])
        if opening is not None and not (
            opening.group(1).startswith("`") and "`" in opening.group(2)
        ):
            fence_marker = opening.group(1)[0]
            fence_length = len(opening.group(1))
            classified.append((line, True))
            continue

        classified.append((line, False))

    if fence_marker:
        raise ValueError("unclosed Markdown fence")
    return tuple(classified)


def _live_markdown(classified: tuple[tuple[str, bool], ...]) -> str:
    """Preserve line positions while blanking fenced and indented code."""
    return "\n".join("" if is_code else line for line, is_code in classified)


def parse_client_report(markdown: str) -> ParsedClientReport:
    """Parse only the localized report layers and ordered H2 structure."""
    lines = _split_markdown_lines(markdown)
    first_line = lines[0] if lines else ""
    if first_line == "# Diagnóstico ejecutivo de LinkedIn":
        locale = "es"
    elif first_line == "# LinkedIn Executive Diagnostic":
        locale = "en"
    else:
        raise ValueError("client report must start at byte 0 with a localized H1")

    classified = _classify_markdown_lines(markdown)
    headings = HEADING_MAP[locale]
    appendix_heading = f"## {headings['appendix']}"
    appendix_indexes = tuple(
        index
        for index, (line, is_code) in enumerate(classified)
        if not is_code and line == appendix_heading
    )
    if len(appendix_indexes) != 1:
        raise ValueError("report requires exactly one localized appendix boundary")
    appendix_index = appendix_indexes[0]
    source_lines = _split_markdown_lines(markdown, keepends=True)
    client_report = "".join(source_lines[:appendix_index]).rstrip("\r\n")
    evidence_appendix = "".join(source_lines[appendix_index + 1:]).lstrip("\r\n")
    live_client_report = _live_markdown(classified[:appendix_index])
    matches = list(re.finditer(r"(?m)^## ([^\n]+)$", live_client_report))
    expected = tuple(headings[key] for key in SECTION_KEYS)
    if tuple(match.group(1) for match in matches) != expected:
        raise ValueError("client report sections are missing, duplicated, or out of order")
    section_bodies = MappingProxyType(_slice_h2_bodies(live_client_report, matches))
    return ParsedClientReport(locale, client_report, evidence_appendix, section_bodies)


def parse_full_debug_appendix(
    parsed: ParsedClientReport,
) -> tuple[LegacyAppendixSection, ...]:
    """Parse the complete ordered 14-section legacy appendix."""
    live_appendix = _live_markdown(_classify_markdown_lines(parsed.evidence_appendix))
    matches = list(re.finditer(r"(?m)^### ([^\n]+)$", live_appendix))
    if tuple(match.group(1) for match in matches) != LEGACY_APPENDIX_SECTION_KEYS:
        raise ValueError("debug appendix sections are missing, duplicated, or out of order")

    sections: list[LegacyAppendixSection] = []
    for index, key in enumerate(LEGACY_APPENDIX_SECTION_KEYS):
        body_start = matches[index].end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(live_appendix)
        body = _trim_markdown_whitespace(live_appendix[body_start:body_end])
        rows = tuple(match.group(0) for match in CANONICAL_CONTRACT_ROW.finditer(body))
        if not rows:
            raise ValueError(f"legacy appendix section {key} requires at least one canonical row")
        sections.append(LegacyAppendixSection(key, body, rows))
    return tuple(sections)


def parse_score_table(parsed: ParsedClientReport) -> tuple[ReportDomainScore, ...]:
    """Parse the localized five-column score table into canonical typed rows."""
    table_lines = [
        trimmed
        for line in _split_markdown_lines(parsed.section_bodies["score"])
        if (trimmed := _trim_markdown_whitespace(line)).startswith("|")
    ]
    if len(table_lines) < 2:
        raise ValueError("score table requires the localized five-column header")
    if _parse_table_cells(table_lines[0]) != SCORE_TABLE_HEADERS[parsed.locale]:
        raise ValueError("score table requires the localized five-column header")
    separator = _parse_table_cells(table_lines[1])
    if len(separator) != 5 or any(re.fullmatch(r":?-{3,}:?", cell) is None for cell in separator):
        raise ValueError("score table requires a five-column separator")

    domains = SCORE_DOMAIN_LABELS[parsed.locale]
    states = SCORE_STATE_LABELS[parsed.locale]
    rows: list[ReportDomainScore] = []
    for line in table_lines[2:]:
        cells = _parse_table_cells(line)
        if len(cells) != 5:
            raise ValueError("score table rows must contain exactly five columns")
        domain_label, state_label, score_text, evidence_text, reason = cells
        if domain_label not in domains:
            raise ValueError(f"score table has unknown dimension: {domain_label}")
        if state_label not in states:
            raise ValueError(f"score table has invalid state for {domains[domain_label]}")
        if score_text == "—":
            score = None
        elif re.fullmatch(r"\d{1,3}", score_text) is not None and int(score_text) <= 100:
            score = int(score_text)
        else:
            raise ValueError(f"score table has invalid score for {domains[domain_label]}")
        evidence_ids = tuple(
            _trim_markdown_whitespace(evidence_id)
            for evidence_id in evidence_text.split(",")
            if _trim_markdown_whitespace(evidence_id)
        )
        rows.append(
            ReportDomainScore(
                domains[domain_label],
                states[state_label],
                score,
                evidence_ids,
                reason,
            )
        )
    return tuple(rows)


def parse_priority_blocks(parsed: ParsedClientReport) -> tuple[ReportPriority, ...]:
    """Parse numbered localized priority H3 blocks and their fixed fields."""
    blocks = _h3_blocks(parsed.section_bodies["priorities"])
    priorities: list[ReportPriority] = []
    for heading, body in blocks:
        match = re.fullmatch(r"([1-9]\d*)\.[ \t]+(.+)", heading)
        if match is None:
            continue
        rank = int(match.group(1))
        section = PRIORITY_SECTION_LABELS[parsed.locale].get(match.group(2), "")
        fields = _localized_fields(
            body,
            PRIORITY_FIELD_LABELS[parsed.locale],
            f"priority {rank}",
        )
        priorities.append(
            ReportPriority(
                rank,
                section,
                _single_code(fields.get("diagnosed_gap", "")),
                _single_code(fields.get("action_type", "")),
                _code_list(fields.get("evidence_ids", "")),
                _single_code(fields.get("timebox", "")),
                _single_code(fields.get("done_when", "")),
                _single_code(fields.get("impact_basis", "")),
                frozenset(fields),
            )
        )
    return tuple(priorities)


def parse_copy_blocks(parsed: ParsedClientReport) -> tuple[ReportCopyBlock, ...]:
    """Parse the three fixed localized copy-category H3 blocks."""
    blocks = _h3_blocks(parsed.section_bodies["copy"])
    allowed_headings = COPY_SECTION_LABELS[parsed.locale]
    for heading, _body in blocks:
        if heading not in allowed_headings:
            raise ValueError(f"copy section has unexpected H3: {heading}")
    copies: list[ReportCopyBlock] = []
    for heading, body in blocks:
        section = allowed_headings[heading]
        fields = _localized_fields(
            body,
            COPY_FIELD_LABELS[parsed.locale],
            f"copy {section}",
        )
        raw_state = _trim_markdown_whitespace(fields.get("state", "")).casefold()
        copies.append(
            ReportCopyBlock(
                _single_code(fields.get("copy_id", "")),
                section,
                COPY_STATE_LABELS[parsed.locale].get(raw_state, ""),
                _single_code(fields.get("audience", "")),
                _single_code(fields.get("problem", "")),
                _code_list(fields.get("fact_ids", ""), empty_words={"none", "ninguno"}),
                _code_list(fields.get("evidence_ids", "")),
                _single_code(fields.get("claim_boundary", "")),
                _code_list(fields.get("claims", ""), empty_words={"none", "ninguno"}),
                _trim_markdown_whitespace(fields.get("actual_copy", "")),
                frozenset(fields),
            )
        )
    return tuple(copies)


def parse_visible_primary_copy_category(parsed: ParsedClientReport) -> str:
    """Parse the single localized client-visible primary copy category."""
    fields = _localized_fields(
        parsed.section_bodies["copy"],
        {PRIMARY_COPY_CATEGORY_LABEL[parsed.locale]: "primary_copy_category"},
        "copy section",
    )
    return _single_code(fields.get("primary_copy_category", ""))


def priority_fingerprint(
    priority: Mapping[str, object],
) -> tuple[str, str, str, tuple[str, ...], str]:
    """Return the candidate-specific semantic fingerprint for one priority."""
    evidence_ids = priority.get("evidence_ids")
    if (
        not isinstance(priority.get("section"), str)
        or not isinstance(priority.get("diagnosed_gap"), str)
        or not isinstance(priority.get("action_type"), str)
        or not isinstance(evidence_ids, (list, tuple))
        or any(not isinstance(item, str) for item in evidence_ids)
        or not isinstance(priority.get("done_when"), str)
    ):
        raise ValueError("priority fingerprint requires complete string fields")
    return (
        priority["section"],
        priority["diagnosed_gap"],
        priority["action_type"],
        tuple(evidence_ids),
        priority["done_when"],
    )


def _report_priority_fingerprint(
    priority: ReportPriority,
) -> tuple[str, str, str, tuple[str, ...], str]:
    return (
        priority.section,
        priority.diagnosed_gap,
        priority.action_type,
        priority.evidence_ids,
        priority.done_when,
    )


def _h3_blocks(body: str) -> tuple[tuple[str, str], ...]:
    headings = list(re.finditer(r"(?m)^(#{3,6}) ([^\n]+)$", body))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(headings):
        if match.group(1) != "###":
            continue
        block_end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        blocks.append(
            (
                _trim_markdown_whitespace(match.group(2)),
                _trim_markdown_whitespace(body[match.end():block_end]),
            )
        )
    return tuple(blocks)


def _localized_fields(
    body: str,
    labels: Mapping[str, str],
    block_label: str,
) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in _split_markdown_lines(body):
        match = re.fullmatch(r"[ \t]*[-*][ \t]+([^:]+):[ \t]*(.*)", line)
        if match is None or _trim_markdown_whitespace(match.group(1)) not in labels:
            continue
        field = labels[_trim_markdown_whitespace(match.group(1))]
        if field in fields:
            raise ValueError(f"{block_label} has duplicate field: {field}")
        fields[field] = _trim_markdown_whitespace(match.group(2))
    return fields


def _single_code(value: str) -> str:
    value = _trim_markdown_whitespace(value)
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        return _trim_markdown_whitespace(value[1:-1])
    return value


def _code_list(value: str, *, empty_words: set[str] | None = None) -> tuple[str, ...]:
    if empty_words is not None and _trim_markdown_whitespace(value).casefold() in empty_words:
        return ()
    return tuple(
        _single_code(item)
        for item in value.split(",")
        if _single_code(item)
    )


def calculate_half_up_score(numeric_weighted_total: float, scored_weight: int) -> int | None:
    """Normalize weighted points to a half-up integer score."""
    if scored_weight <= 0:
        return None
    return int((numeric_weighted_total / scored_weight) * 100 + 0.5)


def parse_visible_overall_score(parsed: ParsedClientReport) -> int:
    """Parse the single localized visible overall score."""
    match = _single_score_metadata_match(parsed, "overall", "visible overall score")
    score = int(match.group(1))
    if score > 100:
        raise ValueError("visible overall score must be between 0 and 100")
    return score


def parse_visible_coverage(parsed: ParsedClientReport) -> tuple[int, int]:
    """Parse visible scored and excluded weights."""
    match = _single_score_metadata_match(parsed, "coverage", "visible coverage")
    scored_weight, not_scored_weight = (int(match.group(1)), int(match.group(2)))
    if scored_weight > 100 or not_scored_weight > 100:
        raise ValueError("visible coverage weights must be between 0 and 100")
    return scored_weight, not_scored_weight


def parse_visible_confidence(parsed: ParsedClientReport) -> str:
    """Parse and normalize the localized visible confidence state."""
    match = _single_score_metadata_match(parsed, "confidence", "visible confidence")
    values = SCORE_METADATA[parsed.locale]["confidence_values"]
    assert isinstance(values, Mapping)
    return values[match.group(1)]


def validate_client_report(
    markdown: str,
    bundle: Mapping[str, object],
    *,
    appendix_mode: str = "normal",
) -> list[str]:
    """Return deterministic structural and layer-limit errors for a report."""
    if not isinstance(markdown, str):
        return ["client report must be Markdown text"]
    try:
        fixture_errors = validate_fixture_bundle(bundle)
    except Exception:
        return ["fixture validation failed for malformed input"]
    if fixture_errors:
        return sorted(set(fixture_errors))
    assert isinstance(bundle, Mapping)
    try:
        parsed = parse_client_report(markdown)
    except ValueError as error:
        return [str(error)]

    errors: list[str] = []
    if bundle.get("locale") != parsed.locale:
        errors.append("client report locale must match fixture locale")
        errors.append("report evidence does not belong to fixture")
    if _client_report_word_count(parsed) > 800:
        errors.append("client report exceeds 800 words excluding the score table")
    if _has_contract_marker(parsed.client_report):
        errors.append("client report cannot contain legacy contract markers")

    if appendix_mode not in APPENDIX_MODES:
        errors.append(f"unsupported appendix mode: {appendix_mode}")
    elif appendix_mode == "normal":
        if _word_count(parsed.evidence_appendix) > 250:
            errors.append("normal evidence appendix exceeds 250 words")
        if _word_count(markdown) > 1100:
            errors.append("normal report payload exceeds 1100 words")
        if _has_contract_marker(parsed.evidence_appendix):
            errors.append("normal evidence appendix cannot contain canonical contract rows")
    else:
        sections: tuple[LegacyAppendixSection, ...] = ()
        try:
            sections = parse_full_debug_appendix(parsed)
        except ValueError as error:
            errors.append(str(error))
        rows = tuple(row for section in sections for row in section.rows)
        expected_candidate_id = bundle.get("internal_candidate_id")
        rows_have_valid_identity = all(
            len(CANDIDATE_ID_KEY.findall(row)) == 1
            and CANDIDATE_ID_VALUE.findall(row) == [expected_candidate_id]
            for row in rows
        )
        identity_is_row_bound = (
            bool(rows)
            and rows_have_valid_identity
            and len(CANDIDATE_ID_KEY.findall(parsed.evidence_appendix)) == len(rows)
        )
        if sections and not identity_is_row_bound:
            errors.append("debug appendix candidate_id must match fixture internal_candidate_id")
    try:
        errors.extend(_validate_decisions(parsed, bundle))
    except _InvalidDecisionBundle:
        errors.append("report decision validation requires a valid fixture decision ledger")
    except (TypeError, ValueError) as error:
        errors.append(str(error))
    try:
        errors.extend(_validate_scores(parsed, bundle))
    except _InvalidScoreBundle:
        errors.append("report score validation requires a valid fixture score ledger")
    except ValueError as error:
        errors.append(str(error))
    errors.extend(_scan_privacy(bundle))
    errors.extend(_validate_report_identifiers(parsed, bundle, appendix_mode))
    errors.extend(_validate_privacy_and_safety(parsed, bundle))
    source_errors: list[str] = []
    _validate_sources(
        bundle.get("source_catalog"),
        source_errors,
        evaluation_date=bundle.get("evaluation_date"),
    )
    errors.extend(source_errors)
    return sorted(set(errors))


def _parse_table_cells(line: str) -> tuple[str, ...]:
    if not line.startswith("|") or not line.endswith("|"):
        return ()
    return tuple(_trim_markdown_whitespace(cell) for cell in line[1:-1].split("|"))


def _single_score_metadata_match(
    parsed: ParsedClientReport,
    field: str,
    label: str,
) -> re.Match[str]:
    pattern = SCORE_METADATA[parsed.locale][field]
    assert isinstance(pattern, re.Pattern)
    matches = [
        pattern.fullmatch(_trim_markdown_whitespace(line))
        for line in _split_markdown_lines(parsed.section_bodies["score"])
    ]
    matches = [match for match in matches if match is not None]
    if len(matches) != 1:
        raise ValueError(f"score section requires exactly one {label}")
    return matches[0]


def _bundle_evidence_ids(bundle: Mapping[str, object]) -> frozenset[str]:
    state = bundle.get("structural_state_fixture")
    if not isinstance(state, Mapping):
        raise _InvalidScoreBundle
    observations = state.get("observations")
    if not isinstance(observations, list):
        raise _InvalidScoreBundle
    evidence_ids: set[str] = set()
    for observation in observations:
        if not isinstance(observation, Mapping) or not isinstance(observation.get("evidence_id"), str):
            raise _InvalidScoreBundle
        evidence_ids.add(observation["evidence_id"])
    return frozenset(evidence_ids)


def _score_ledger(bundle: Mapping[str, object]) -> tuple[Mapping[str, object], tuple[Mapping[str, object], ...]]:
    evidence_mode = bundle.get("evidence_mode")
    if not isinstance(evidence_mode, str) or evidence_mode not in EVIDENCE_MODES:
        raise _InvalidScoreBundle
    ledger = bundle.get("score_ledger")
    if not isinstance(ledger, Mapping):
        raise _InvalidScoreBundle
    domains = ledger.get("domains")
    if not isinstance(domains, list) or any(not isinstance(row, Mapping) for row in domains):
        raise _InvalidScoreBundle
    required_ledger = {
        "numeric_weighted_total", "scored_weight", "not_scored_weight",
        "overall_score", "confidence",
    }
    required_domain = {
        "domain", "weight", "state", "raw_score", "weighted_points", "evidence_ids",
    }
    if not required_ledger.issubset(ledger):
        raise _InvalidScoreBundle
    typed_domains = tuple(domains)
    if any(not required_domain.issubset(row) for row in typed_domains):
        raise _InvalidScoreBundle
    if (
        not _is_finite_number(ledger["numeric_weighted_total"])
        or not 0 <= ledger["numeric_weighted_total"] <= 100
        or not _is_json_integer(ledger["scored_weight"])
        or not 0 <= ledger["scored_weight"] <= 100
        or not _is_json_integer(ledger["not_scored_weight"])
        or not 0 <= ledger["not_scored_weight"] <= 100
        or not _is_json_integer(ledger["overall_score"])
        or not 0 <= ledger["overall_score"] <= 100
        or not isinstance(ledger["confidence"], str)
        or ledger["confidence"] not in CONFIDENCE_STATES
    ):
        raise _InvalidScoreBundle
    for row in typed_domains:
        if (
            not isinstance(row["domain"], str)
            or row["domain"] not in DOMAIN_WEIGHTS
            or not _is_json_integer(row["weight"])
            or row["weight"] != DOMAIN_WEIGHTS[row["domain"]]
            or not isinstance(row["state"], str)
            or row["state"] not in SCORE_STATES
            or not isinstance(row["evidence_ids"], list)
            or not row["evidence_ids"]
            or any(
                not isinstance(evidence_id, str) or not evidence_id
                for evidence_id in row["evidence_ids"]
            )
            or len(row["evidence_ids"]) != len(set(row["evidence_ids"]))
            or not _is_finite_number(row["weighted_points"])
            or not 0 <= row["weighted_points"] <= 20
            or (
                row["state"] == "scored"
                and (
                    not _is_finite_number(row["raw_score"])
                    or not 0 <= row["raw_score"] <= 100
                )
            )
            or (
                row["state"] == "not_scored"
                and (row["raw_score"] is not None or row["weighted_points"] != 0)
            )
        ):
            raise _InvalidScoreBundle
    ledger_domain_names = tuple(row["domain"] for row in typed_domains)
    if (
        len(typed_domains) != len(DOMAIN_WEIGHTS)
        or len(set(ledger_domain_names)) != len(typed_domains)
        or set(ledger_domain_names) != set(DOMAIN_WEIGHTS)
    ):
        raise _InvalidScoreBundle
    return ledger, typed_domains


def _validate_scores(parsed: ParsedClientReport, bundle: Mapping[str, object]) -> list[str]:
    rows = parse_score_table(parsed)
    ledger, ledger_domains = _score_ledger(bundle)
    expected = {row["domain"]: row for row in ledger_domains}
    errors: list[str] = []
    visible_domains = tuple(row.domain for row in rows)
    if (
        len(rows) != len(DOMAIN_WEIGHTS)
        or len(set(visible_domains)) != len(rows)
        or set(visible_domains) != set(DOMAIN_WEIGHTS)
    ):
        errors.append("score table must contain exactly the seven canonical dimensions")

    known_evidence = _bundle_evidence_ids(bundle)
    for row in rows:
        ledger_row = expected.get(row.domain)
        if ledger_row is None:
            continue
        if row.state != ledger_row["state"]:
            errors.append(f"visible state for {row.domain} does not match ledger")
        if not _trim_markdown_whitespace(row.reason):
            errors.append(f"score row {row.domain} requires a reason")
        if not row.evidence_ids:
            errors.append(f"score row {row.domain} requires evidence")
        if (
            len(row.evidence_ids) != len(set(row.evidence_ids))
            or set(row.evidence_ids) != set(ledger_row["evidence_ids"])
        ):
            errors.append(f"visible evidence for {row.domain} does not match ledger")
        if ledger_row["state"] == "not_scored":
            if row.score is not None:
                errors.append(f"unavailable dimension {row.domain} must be not scored, not zero")
        elif row.score != ledger_row["raw_score"]:
            errors.append(f"visible domain score for {row.domain} does not match ledger")
        for evidence_id in row.evidence_ids:
            if evidence_id not in known_evidence:
                errors.append(f"score row references unknown evidence {evidence_id}")

    visual = next((row for row in rows if row.domain == "visual"), None)
    if (
        bundle.get("evidence_mode")
        in {"structural_only", "partial_visual_photo_only", "partial_visual_banner_only"}
        and visual is not None
        and (visual.state != "not_scored" or visual.score is not None)
    ):
        errors.append("partial or structural visual evidence cannot have an aggregate visual score")

    visible_scored_weight, visible_not_scored_weight = parse_visible_coverage(parsed)
    if (
        visible_scored_weight != ledger["scored_weight"]
        or visible_not_scored_weight != ledger["not_scored_weight"]
    ):
        errors.append("visible coverage denominator/exclusions do not match ledger")
    ledger_scored_weight = sum(
        row["weight"] for row in ledger_domains if row["state"] == "scored"
    )
    ledger_not_scored_weight = sum(
        row["weight"] for row in ledger_domains if row["state"] == "not_scored"
    )
    if (
        ledger_scored_weight != ledger["scored_weight"]
        or ledger_not_scored_weight != ledger["not_scored_weight"]
    ):
        errors.append("ledger coverage weights do not reconcile")

    scored_domains = tuple(row for row in ledger_domains if row["state"] == "scored")
    for row in scored_domains:
        expected_points = row["raw_score"] * row["weight"] / 100
        if abs(expected_points - row["weighted_points"]) > 1e-9:
            errors.append(
                f"score_ledger domain {row['domain']} weighted_points do not reconcile"
            )
    recomputed_points = math.fsum(row["weighted_points"] for row in scored_domains)
    if abs(recomputed_points - ledger["numeric_weighted_total"]) > 1e-9:
        errors.append("ledger weighted points do not reconcile")
    recomputed = calculate_half_up_score(
        ledger["numeric_weighted_total"],
        ledger["scored_weight"],
    )
    visible_overall_score = parse_visible_overall_score(parsed)
    if recomputed != ledger["overall_score"]:
        errors.append("ledger overall score does not reconcile")
    if visible_overall_score != ledger["overall_score"]:
        errors.append(
            f"visible overall score {visible_overall_score} does not match ledger score {ledger['overall_score']}"
        )

    expected_confidence = "high" if ledger["scored_weight"] >= 90 else "medium"
    if ledger["confidence"] != expected_confidence:
        errors.append("ledger confidence does not match scored coverage")
    if parse_visible_confidence(parsed) != ledger["confidence"]:
        errors.append("visible confidence does not match scored coverage")
    return errors


def _slice_h2_bodies(markdown: str, matches: list[re.Match[str]]) -> dict[str, str]:
    bodies: dict[str, str] = {}
    for index, key in enumerate(SECTION_KEYS):
        body_start = matches[index].end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        bodies[key] = _trim_markdown_whitespace(markdown[body_start:body_end])
    return bodies


def _word_count(text: str) -> int:
    return len(_WORD.findall(text))


def _nfkc_without_format_characters(text: str) -> str:
    """Apply compatibility normalization and remove invisible format controls."""
    compatibility = unicodedata.normalize("NFKC", text)
    return "".join(
        character
        for character in compatibility
        if unicodedata.category(character) != "Cf"
    )


def _normalized_guard_text(text: str) -> str:
    decomposed = unicodedata.normalize(
        "NFKD", _nfkc_without_format_characters(text).casefold()
    )
    return "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )


def _normalized_controlled_text(text: str) -> str:
    """Normalize controlled terms, including punctuation-split spellings."""
    normalized = _normalized_guard_text(text)
    for term, pattern in _CONTROLLED_TERM_PATTERNS:
        normalized = pattern.sub(term, normalized)
    return normalized


def _normalized_syntax_text(text: str) -> str:
    """Normalize syntax without erasing Spanish tense-bearing diacritics."""
    return _nfkc_without_format_characters(text).casefold()


def _guard_tokens(text: str) -> frozenset[str]:
    normalized = _normalized_guard_text(text)
    tokens = set(re.findall(r"[a-z0-9]+", normalized))
    for term, pattern in _CONTROLLED_TERM_PATTERNS:
        if pattern.search(normalized):
            tokens.add(term)
    return frozenset(tokens)


def _has_token_classes(tokens: frozenset[str], *classes: str) -> bool:
    return all(tokens & SAFETY_TOKEN_CLASSES[name] for name in classes)


def _has_token_classes_in_normalized_sentence(text: str, *classes: str) -> bool:
    normalized = _normalized_guard_text(text)
    return any(
        _has_token_classes(_guard_tokens(sentence), *classes)
        for sentence in re.split(r"[.!?¡¿\n]+", normalized)
        if _trim_markdown_whitespace(sentence)
    )


def _bounded_safety_clause(
    text: str,
    start: int,
    end: int,
) -> tuple[str, int, int]:
    """Return the bounded clause containing one safety predicate and its offsets."""
    left_boundary = 0
    for boundary in SAFETY_CLAUSE_BOUNDARY.finditer(text, 0, start):
        left_boundary = boundary.end()
    right_boundary = SAFETY_CLAUSE_BOUNDARY.search(text, end)
    clause_end = right_boundary.start() if right_boundary is not None else len(text)
    return text[left_boundary:clause_end], start - left_boundary, end - left_boundary


def _has_protected_trait_inference(text: str) -> bool:
    normalized = _normalized_controlled_text(text)
    for sentence in re.split(r"[.!?¡¿\n]+", normalized):
        for predicate in INFERENCE_PREDICATE.finditer(sentence):
            clause, predicate_start, predicate_end = _bounded_safety_clause(
                sentence,
                predicate.start(),
                predicate.end(),
            )
            predicates = tuple(INFERENCE_PREDICATE.finditer(clause))
            predicate_index = next(
                index
                for index, candidate in enumerate(predicates)
                if candidate.start() == predicate_start and candidate.end() == predicate_end
            )
            complement_start = 0
            if predicate_index:
                coordinators = tuple(
                    INFERENCE_COORDINATOR.finditer(
                        clause,
                        predicates[predicate_index - 1].end(),
                        predicate_start,
                    )
                )
                if coordinators:
                    complement_start = coordinators[-1].end()
            complement_end = len(clause)
            if predicate_index + 1 < len(predicates):
                coordinator = INFERENCE_COORDINATOR.search(
                    clause,
                    predicate_end,
                    predicates[predicate_index + 1].start(),
                )
                if coordinator is not None:
                    complement_end = coordinator.start()
            complement = clause[complement_start:complement_end]
            if not _has_token_classes(_guard_tokens(clause), "visual"):
                continue
            if not _has_token_classes(_guard_tokens(complement), "protected"):
                continue
            predicate_prefix = clause[complement_start:predicate_start]
            if INFERENCE_NEGATION.search(predicate_prefix) is None:
                return True
    return False


def _has_completed_external_action(text: str) -> bool:
    normalized = _normalized_syntax_text(text)
    for sentence in re.split(r"[.!?¡¿\n]+", normalized):
        if not _trim_markdown_whitespace(sentence):
            continue
        for action in EXECUTED_EXTERNAL_ACTION.finditer(sentence):
            clause, action_start, action_end = _bounded_safety_clause(
                sentence,
                action.start(),
                action.end(),
            )
            if EXTERNAL_ACTION_NEGATION.search(clause[:action_start]) is not None:
                continue
            context = clause[
                max(0, action_start - 80):min(len(clause), action_end + 100)
            ]
            if any(
                action_verbs.search(action.group(0)) is not None
                and target.search(context) is not None
                for action_verbs, target in EXTERNAL_ACTION_TARGETS
            ):
                return True
    return False


def _has_generic_credential_shape(text: str) -> bool:
    def credential_components(value: str) -> tuple[str, ...]:
        return tuple(
            component.casefold()
            for token in re.findall(r"[A-Za-z0-9]+", value)
            for component in CREDENTIAL_COMPONENT.findall(token)
        )

    def has_bounded_career_title(value: str) -> bool:
        components = credential_components(value)
        if set(components) & FORBIDDEN_CAREER_CREDENTIAL_COMPONENTS:
            return False
        words = tuple(component for component in components if not component.isdigit())
        if not set(words) & CAREER_CREDENTIAL_TERMS:
            return False
        return bool(words) and (
            words[-1] in CAREER_CREDENTIAL_TERMS
            or words[-1] in CAREER_CREDENTIAL_SUFFIXES
        )

    for assignment in GENERIC_CREDENTIAL_LABEL.finditer(text):
        value = _trim_markdown_whitespace(assignment.group(3)).lstrip("\"'")
        forbidden_components = set(
            re.findall(r"[a-z0-9]+", value.casefold())
        ) & FORBIDDEN_CAREER_CREDENTIAL_COMPONENTS
        if forbidden_components:
            return True
        leading = re.match(r"[A-Za-z0-9][A-Za-z0-9_./+=:-]*", value)
        if leading is None:
            continue
        token = leading.group(0)
        if OPAQUE_CREDENTIAL_TOKEN.fullmatch(token) is None:
            continue
        is_explicit_career_credential = (
            assignment.group(1).casefold() == "credential"
            and assignment.group(2) == ":"
            and (
                has_bounded_career_title(token)
                or has_bounded_career_title(value)
            )
        )
        if not is_explicit_career_credential:
            return True
    return False


def _without_canonical_question_fields(parsed: ParsedClientReport) -> str:
    evidence_lines: list[str] = []
    parsed_questions = {
        question.rank: question
        for question in _parse_evidence_questions(parsed)
    }
    canonical_question: EvidenceQuestion | None = None
    question_heading = re.compile(
        rf"^### {re.escape(QUESTION_HEADING[parsed.locale])}[ \t]+([1-9]\d*)$"
    )
    field_labels = QUESTION_FIELD_LABELS[parsed.locale]
    for line in _split_markdown_lines(parsed.section_bodies["evidence_needed"]):
        heading = re.fullmatch(r"#{3,6} [^\r\n]+", line)
        if heading is not None:
            question_match = question_heading.fullmatch(line)
            canonical_question = (
                parsed_questions.get(int(question_match.group(1)))
                if question_match is not None
                else None
            )
            evidence_lines.append(line)
            continue
        field = re.fullmatch(r"[ \t]*[-*][ \t]+([^:]+):[ \t]*(.*)", line)
        field_name = (
            field_labels.get(_trim_markdown_whitespace(field.group(1)))
            if field is not None
            else None
        )
        if (
            canonical_question is not None
            and field_name in canonical_question.present_fields
        ):
            continue
        evidence_lines.append(line)

    outside = [
        body
        for key, body in parsed.section_bodies.items()
        if key != "evidence_needed"
    ]
    outside.append("\n".join(evidence_lines))
    return "\n".join(outside)


def _validated_synthetic_identifiers(bundle: Mapping[str, object]) -> set[str]:
    identifiers: set[str] = set()
    plural_fields = {"evidence_ids": "evidence_id", "fact_ids": "fact_id"}

    def collect(value: object) -> None:
        if isinstance(value, Mapping):
            for field, nested in value.items():
                pattern_field = plural_fields.get(field, field)
                pattern = _ID_PATTERNS.get(pattern_field)
                candidates = nested if isinstance(nested, list) else [nested]
                if pattern is not None:
                    identifiers.update(
                        candidate
                        for candidate in candidates
                        if isinstance(candidate, str) and pattern.fullmatch(candidate)
                    )
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    collect(bundle)
    return identifiers


def _extract_identifier_tokens(text: str) -> tuple[str, ...]:
    """Extract normalized synthetic identifier-shaped tokens from report prose."""
    compatibility = unicodedata.normalize("NFKC", text)
    normalized = "".join(
        "-"
        if character in IDENTIFIER_SEPARATOR_LIKE
        or unicodedata.category(character) == "Pd"
        else character
        for character in compatibility
        if character == "\u00ad" or unicodedata.category(character) != "Cf"
    ).upper()
    return tuple(match.group(0) for match in REPORT_IDENTIFIER.finditer(normalized))


def _validate_report_identifiers(
    parsed: ParsedClientReport,
    bundle: Mapping[str, object],
    appendix_mode: str,
) -> list[str]:
    """Reject cross-fixture IDs while preserving expanded canonical identities."""
    allowed = {
        identifier.upper() for identifier in _validated_synthetic_identifiers(bundle)
    }
    expected_candidate = bundle.get("internal_candidate_id")
    normalized_candidate = (
        expected_candidate.upper() if isinstance(expected_candidate, str) else None
    )
    errors: list[str] = []

    def validate_text(text: str) -> None:
        for identifier in _extract_identifier_tokens(text):
            if identifier.startswith("FIXTURE-"):
                errors.append(
                    f"client report contains forbidden fixture identifier: {identifier}"
                )
            elif identifier.startswith("CANDIDATE-"):
                errors.append(
                    "client report contains forbidden internal candidate "
                    f"identifier: {identifier}"
                )
            elif identifier not in allowed:
                errors.append(
                    f"client report references identifier outside fixture: {identifier}"
                )

    validate_text(parsed.client_report)
    if appendix_mode in APPENDIX_MODES - {"normal"}:
        for line in _split_markdown_lines(parsed.evidence_appendix):
            masked = line
            if CANONICAL_CONTRACT_ROW.fullmatch(line):
                matches = CANDIDATE_ID_VALUE.finditer(line)
                spans = [
                    match.span(1)
                    for match in matches
                    if match.group(1) == normalized_candidate
                ]
                for start, end in reversed(spans):
                    masked = f"{masked[:start]}allowed-current{masked[end:]}"
            validate_text(masked)
    else:
        validate_text(parsed.evidence_appendix)
    return errors


def validate_candidate_facing_text(text: str) -> list[str]:
    """Return privacy/action/outcome errors without fixture-specific policy."""
    normalized_text = _normalized_guard_text(text)
    tokens = _guard_tokens(text)
    errors: list[str] = []
    checks = (
        ("client report contains forbidden email-like value", _EMAIL),
        ("client report contains forbidden phone-like value", _PHONE),
        ("client report contains forbidden LinkedIn profile URL value", _PROFILE_URL),
        ("client report contains forbidden local-path value", _LOCAL_PATH),
    )
    for message, pattern in checks:
        if pattern.search(normalized_text):
            errors.append(message)
    if _ANY_URL.search(normalized_text) and not _PROFILE_URL.search(normalized_text):
        errors.append("client report contains forbidden URL value")
    if RAW_PROFILE_ALIAS.search(normalized_text):
        errors.append("client report contains forbidden raw-profile alias")
    if PRIVATE_ANALYTICS_ALIAS.search(normalized_text):
        errors.append("client report contains forbidden private analytics value")
    if _has_protected_trait_inference(text):
        errors.append("client report cannot infer a protected trait from visual evidence")
    if (
        CREDENTIAL_ASSIGNMENT.search(normalized_text)
        or _has_generic_credential_shape(text)
        or AUTHORIZATION_HEADER.search(normalized_text)
    ):
        errors.append("client report contains credential-shaped content")
    if _has_completed_external_action(text):
        errors.append("client report cannot claim an external action was executed")
    has_outcome_guarantee = (
        _has_token_classes(tokens, "guarantee", "outcome")
        or _has_token_classes(tokens, "certainty", "outcome")
        or _has_token_classes_in_normalized_sentence(text, "causation", "outcome")
        or OUTCOME_GUARANTEE.search(normalized_text)
    )
    if has_outcome_guarantee:
        errors.append("client report cannot guarantee an employment or platform outcome")
    if INSPECTION_AUTHORIZATION_INFERENCE.search(normalized_text):
        errors.append("profile inspection authorization cannot authorize an external action")
    if "lift" in normalized_text and re.search(
        r"\b(?:source|fuente|linkedin|official|oficial)\b", normalized_text, re.I
    ):
        errors.append("source-derived lift cannot be used in the client report")
    has_numeric_probability = (
        re.search(r"\b\d+(?:[.,]\d+)?\s*%?", normalized_text) is not None
    )
    if (
        has_numeric_probability
        and _has_token_classes(tokens, "probability", "individual", "outcome")
    ):
        errors.append("individual outcome probability is not allowed")
    has_two_x = re.search(r"(?<!\w)2\s*(?:x|×)(?!\w)", normalized_text) is not None
    if has_two_x and _has_token_classes(tokens, "score", "math"):
        errors.append("aggregate 2x claims cannot affect score math")
    if re.search(
        r"COACH_HEURISTIC[^.\n]{0,140}(?:LinkedIn\s+(?:measurement|metric|medici[oó]n|m[eé]trica)|"
        r"guarantees?|garantiza|causes?|causa|will\s+increase|aumentar[aá])",
        normalized_text,
        re.I,
    ):
        errors.append(
            "COACH_HEURISTIC cannot be presented as a LinkedIn measurement or causal guarantee"
        )
    return errors


def _validate_privacy_and_safety(
    parsed: ParsedClientReport,
    bundle: Mapping[str, object],
) -> list[str]:
    """Reject deterministic privacy, authorization, and claim-safety breaks."""
    text = f"{parsed.client_report}\n{parsed.evidence_appendix}"
    normalized_text = _normalized_guard_text(text)
    candidate_facing_errors = validate_candidate_facing_text(text)
    errors = candidate_facing_errors[:7]
    placeholder_text = normalized_text
    for identifier in sorted(
        _validated_synthetic_identifiers(bundle), key=len, reverse=True
    ):
        placeholder_text = re.sub(
            re.escape(_normalized_guard_text(identifier)),
            "synthetic-id",
            placeholder_text,
            flags=re.I,
        )
    for placeholder in sorted(FORBIDDEN_PLACEHOLDERS):
        separated = r"[\W_]*".join(re.escape(character) for character in placeholder)
        if re.search(rf"(?<![\w]){separated}(?![\w])", placeholder_text):
            errors.append(f"client report contains forbidden placeholder: {placeholder}")

    questions: tuple[EvidenceQuestion, ...] = ()
    try:
        questions = _parse_evidence_questions(parsed)
    except (TypeError, ValueError):
        pass
    if CONFIRMATION_MARKER.search(normalized_text):
        marker_is_bound = any(
            CONFIRMATION_MARKER.search(_normalized_guard_text(question.question))
            and _is_meaningful_question(
                CONFIRMATION_MARKER.sub(
                    "", _normalized_guard_text(question.question)
                )
            )
            and bool(question.fact_id)
            and bool(question.decision)
            for question in questions
        )
        if not marker_is_bound:
            errors.append(
                "confirmation marker requires a concrete decision-changing question"
            )
    errors.extend(candidate_facing_errors[7:])

    expectations = bundle.get("eval_expectations")
    if (
        isinstance(expectations, Mapping)
        and expectations.get("scenario_class") == "structural_no_visual"
    ):
        try:
            _, fixture_copies, _, _, _, _ = _decision_ledger(bundle)
            required = {
                (fact_id, f"copy:{copy_block['section']}")
                for copy_block in fixture_copies
                if copy_block["state"] == "requires_confirmation"
                for fact_id in copy_block["fact_ids"]
            }
            actual = {(question.fact_id, question.decision) for question in questions}
            if actual - required:
                errors.append(
                    "scenario C cannot request evidence that changes no current decision"
                )
            if expectations.get("pending_evidence_policy") == "NO_EXTRA_VISUAL_REQUEST":
                pending_section_tokens = _guard_tokens(
                    parsed.section_bodies["evidence_needed"]
                )
                if (
                    pending_section_tokens
                    & SAFETY_TOKEN_CLASSES["visual_evidence_object"]
                ):
                    errors.append("scenario C cannot request extra visual evidence")
            outside_question_tokens = _guard_tokens(
                _without_canonical_question_fields(parsed)
            )
            if _has_token_classes(
                outside_question_tokens, "request_verb", "evidence_object"
            ):
                errors.append(
                    "scenario C evidence requests must appear only in canonical "
                    "decision-changing questions"
                )
        except (_InvalidDecisionBundle, TypeError, ValueError):
            pass
    return errors


def _normalized_safety_tokens(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9]+", _normalized_guard_text(text)))


def _normalized_code_is_exposed(text: str, code: str) -> bool:
    text_tokens = _normalized_safety_tokens(text)
    code_tokens = _normalized_safety_tokens(code)
    normalized_text = " ".join(text_tokens)
    normalized_code = " ".join(code_tokens)
    compact_text = "".join(text_tokens)
    compact_code = "".join(code_tokens)
    return bool(compact_code) and (
        f" {normalized_code} " in f" {normalized_text} "
        or compact_code in compact_text
    )


def _private_plan_has_forbidden_action(text: str) -> bool:
    return any(
        token in PRIVATE_PLAN_FORBIDDEN_TOKENS
        or any(token.startswith(stem) for stem in PRIVATE_PLAN_FORBIDDEN_STEMS)
        for token in _normalized_safety_tokens(text)
    )


def _client_report_word_count(parsed: ParsedClientReport) -> int:
    score_table_words = sum(
        _word_count(line)
        for line in _split_markdown_lines(parsed.section_bodies["score"])
        if line.startswith("|") and line.endswith("|")
    )
    return _word_count(parsed.client_report) - score_table_words


def _has_contract_marker(text: str) -> bool:
    normalized = _normalized_guard_text(text)
    return (
        CONTRACT_TOKEN.search(normalized) is not None
        or CANONICAL_CONTRACT_ROW.search(normalized) is not None
    )


def _decision_ledger(
    bundle: Mapping[str, object],
) -> tuple[
    tuple[Mapping[str, object], ...],
    tuple[Mapping[str, object], ...],
    Mapping[str, Mapping[str, object]],
    frozenset[str],
    tuple[str, ...],
    Mapping[str, object],
]:
    raw_priorities = bundle.get("priorities")
    raw_copies = bundle.get("copy_blocks")
    raw_facts = bundle.get("synthetic_fact_catalog")
    raw_blocked = bundle.get("blocked_claims")
    expectations = bundle.get("eval_expectations")
    if (
        not isinstance(raw_priorities, list)
        or len(raw_priorities) != 3
        or any(not isinstance(item, Mapping) for item in raw_priorities)
        or not isinstance(raw_copies, list)
        or len(raw_copies) != 3
        or any(not isinstance(item, Mapping) for item in raw_copies)
        or not isinstance(raw_facts, list)
        or any(not isinstance(item, Mapping) for item in raw_facts)
        or not isinstance(raw_blocked, list)
        or any(not isinstance(item, str) for item in raw_blocked)
        or not isinstance(expectations, Mapping)
    ):
        raise _InvalidDecisionBundle

    priorities = tuple(raw_priorities)
    copies = tuple(raw_copies)
    required_priority = {
        "rank", "section", "diagnosed_gap", "action_type", "evidence_ids",
        "timebox", "done_when", "impact_basis",
    }
    required_copy = {
        "copy_id", "section", "state", "audience", "problem", "fact_ids",
        "evidence_ids", "claim_boundary",
    }
    if any(
        not required_priority.issubset(item)
        or not _is_json_integer(item["rank"])
        or not all(
            isinstance(item[field], str)
            for field in (
                "section", "diagnosed_gap", "action_type", "timebox",
                "done_when", "impact_basis",
            )
        )
        or not _string_sequence(item["evidence_ids"], require_nonempty=True)
        for item in priorities
    ):
        raise _InvalidDecisionBundle
    if {item["rank"] for item in priorities} != {1, 2, 3}:
        raise _InvalidDecisionBundle
    if any(
        not required_copy.issubset(item)
        or not all(
            isinstance(item[field], str)
            for field in (
                "copy_id", "section", "state", "audience", "problem",
                "claim_boundary",
            )
        )
        or not _string_sequence(item["fact_ids"])
        or not _string_sequence(item["evidence_ids"], require_nonempty=True)
        for item in copies
    ):
        raise _InvalidDecisionBundle
    if {item["section"] for item in copies} != set(COPY_SECTIONS):
        raise _InvalidDecisionBundle

    facts: dict[str, Mapping[str, object]] = {}
    for fact in raw_facts:
        fact_id = fact.get("fact_id")
        state = fact.get("evidence_state")
        claim_tokens = fact.get("claim_tokens")
        if (
            not isinstance(fact_id, str)
            or not isinstance(state, str)
            or fact_id in facts
            or not _string_sequence(claim_tokens)
            or any(token not in CLAIM_TOKENS for token in claim_tokens)
            or len(claim_tokens) != len(set(claim_tokens))
        ):
            raise _InvalidDecisionBundle
        facts[fact_id] = fact
    try:
        evidence_ids = _bundle_evidence_ids(bundle)
    except _InvalidScoreBundle as error:
        raise _InvalidDecisionBundle from error
    return priorities, copies, MappingProxyType(facts), evidence_ids, tuple(raw_blocked), expectations


def _string_sequence(value: object, *, require_nonempty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (bool(value) or not require_nonempty)
        and all(isinstance(item, str) and bool(item) for item in value)
    )


def _duplicates(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return tuple(duplicates)


def _validate_decisions(parsed: ParsedClientReport, bundle: Mapping[str, object]) -> list[str]:
    priorities = parse_priority_blocks(parsed)
    copies = parse_copy_blocks(parsed)
    (
        fixture_priorities,
        fixture_copies,
        facts,
        known_evidence,
        blocked_claims,
        expectations,
    ) = _decision_ledger(bundle)
    errors: list[str] = []
    primary_copy_category = parse_visible_primary_copy_category(parsed)
    if not primary_copy_category:
        errors.append("copy section requires visible primary copy category")
    elif primary_copy_category not in COPY_SECTIONS:
        errors.append("copy section has invalid visible primary copy category")
    elif primary_copy_category != expectations.get("primary_copy_category"):
        errors.append("visible primary copy category does not match fixture")
    for priority in fixture_priorities:
        for evidence_id in _duplicates(priority["evidence_ids"]):
            errors.append(
                f"fixture priority {priority['rank']} has duplicate evidence {evidence_id}"
            )
    for copy_block in fixture_copies:
        for fact_id in _duplicates(copy_block["fact_ids"]):
            errors.append(
                f"fixture copy {copy_block['section']} has duplicate fact {fact_id}"
            )
        for evidence_id in _duplicates(copy_block["evidence_ids"]):
            errors.append(
                f"fixture copy {copy_block['section']} has duplicate evidence {evidence_id}"
            )
    errors.extend(_validate_report_priorities(priorities, fixture_priorities, known_evidence))
    errors.extend(_validate_report_copies(copies, fixture_copies, facts, known_evidence, blocked_claims))
    errors.extend(_validate_blocked_claims(parsed, blocked_claims, copies))
    errors.extend(_validate_private_plan_scope(parsed))
    errors.extend(_validate_pending_evidence(parsed, fixture_copies, facts))
    return errors


def _validate_report_priorities(
    priorities: tuple[ReportPriority, ...],
    fixture_priorities: tuple[Mapping[str, object], ...],
    known_evidence: frozenset[str],
) -> list[str]:
    errors: list[str] = []
    if len(priorities) != 3 or tuple(priority.rank for priority in priorities) != (1, 2, 3):
        errors.append("report requires exactly three complete priorities")
    required = (
        "diagnosed_gap", "action_type", "evidence_ids", "timebox", "done_when",
        "impact_basis",
    )
    fixture_by_rank = {item["rank"]: item for item in fixture_priorities}
    fingerprints: list[tuple[str, str, str, tuple[str, ...], str]] = []
    for priority in priorities:
        for field in required:
            if field not in priority.present_fields:
                errors.append(f"priority {priority.rank} missing required field: {field}")
        if not priority.section:
            errors.append(f"priority {priority.rank} has invalid localized section")
        for code in (priority.diagnosed_gap, priority.action_type):
            if _is_generic_priority_code(code):
                errors.append(f"generic priority code is not allowed: {code}")
        for evidence_id in _duplicates(priority.evidence_ids):
            errors.append(f"priority {priority.rank} has duplicate evidence {evidence_id}")
        for evidence_id in priority.evidence_ids:
            if evidence_id not in known_evidence:
                errors.append(
                    f"priority {priority.rank} references unknown evidence {evidence_id}"
                )
        if priority.impact_basis and priority.impact_basis != "COACH_HEURISTIC":
            errors.append(
                f"priority {priority.rank} impact basis must be COACH_HEURISTIC "
                "without direct official support"
            )
        expected = fixture_by_rank.get(priority.rank)
        if expected is not None:
            report_values = {
                "section": priority.section,
                "diagnosed_gap": priority.diagnosed_gap,
                "action_type": priority.action_type,
                "evidence_ids": list(priority.evidence_ids),
                "timebox": priority.timebox,
                "done_when": priority.done_when,
                "impact_basis": priority.impact_basis,
            }
            for field, value in report_values.items():
                if value != expected[field]:
                    errors.append(f"priority {priority.rank} does not match fixture {field}")
        if all(field in priority.present_fields for field in required) and priority.section:
            fingerprints.append(_report_priority_fingerprint(priority))
    if len(fingerprints) == 3 and len(set(fingerprints)) != 3:
        errors.append("report priorities must have three distinct fingerprints")
    return errors


def _is_generic_priority_code(value: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    if normalized in GENERIC_PRIORITY_CODES:
        return True
    tokens = set(normalized.split("_"))
    return bool(
        ({"profile", "perfil"} & tokens and {"improve", "optimize", "enhance", "mejorar"} & tokens)
        or ({"keyword", "keywords"} & tokens and {"add", "agregar", "añadir"} & tokens)
        or ({"content", "contenido", "posts"} & tokens and {"create", "post", "crear"} & tokens)
    )


def _validate_report_copies(
    copies: tuple[ReportCopyBlock, ...],
    fixture_copies: tuple[Mapping[str, object], ...],
    facts: Mapping[str, Mapping[str, object]],
    known_evidence: frozenset[str],
    blocked_claims: tuple[str, ...],
) -> list[str]:
    errors: list[str] = []
    if len(copies) != 3 or {item.section for item in copies} != set(COPY_SECTIONS):
        errors.append(
            "report copy must cover exactly headline, about_opening, and experience_bullet"
        )
    required = (
        "copy_id", "state", "audience", "problem", "fact_ids", "evidence_ids",
        "claim_boundary", "claims",
    )
    fixture_by_section = {item["section"]: item for item in fixture_copies}
    all_fact_claim_tokens = {
        claim
        for fact in facts.values()
        for claim in fact["claim_tokens"]
    }
    for copy_block in copies:
        for field in required:
            if field not in copy_block.present_fields:
                errors.append(f"copy {copy_block.section} missing required field: {field}")
        if "actual_copy" not in copy_block.present_fields or not copy_block.actual_copy:
            errors.append(f"copy {copy_block.section} requires nonempty actual copy")
        for fact_id in _duplicates(copy_block.fact_ids):
            errors.append(f"copy {copy_block.section} has duplicate fact {fact_id}")
        for evidence_id in _duplicates(copy_block.evidence_ids):
            errors.append(f"copy {copy_block.section} has duplicate evidence {evidence_id}")
        for claim in _duplicates(copy_block.claims):
            errors.append(f"copy {copy_block.section} has duplicate claim {claim}")
        expected = fixture_by_section.get(copy_block.section)
        report_values = {
            "copy_id": copy_block.copy_id,
            "state": copy_block.state,
            "audience": copy_block.audience,
            "problem": copy_block.problem,
            "fact_ids": list(copy_block.fact_ids),
            "evidence_ids": list(copy_block.evidence_ids),
            "claim_boundary": copy_block.claim_boundary,
        }
        if expected is not None:
            for field, value in report_values.items():
                if value != expected[field]:
                    errors.append(f"copy {copy_block.section} does not match fixture {field}")
        for fact_id in copy_block.fact_ids:
            fact = facts.get(fact_id)
            if fact is None:
                errors.append(f"copy {copy_block.section} references unknown fact {fact_id}")
            elif copy_block.state == "ready" and fact["evidence_state"] not in {
                "verified", "candidate_reported",
            }:
                errors.append(f"ready copy references unsupported fact {fact_id}")
            if copy_block.state == "ready" and fact_id in blocked_claims:
                errors.append(f"ready copy duplicates blocked claim {fact_id}")
        expected_claims: list[str] = []
        claim_states = {
            "ready": {"verified", "candidate_reported"},
            "requires_confirmation": {"unknown", "inferred"},
        }.get(copy_block.state, set())
        for fact_id in copy_block.fact_ids:
            fact = facts.get(fact_id)
            if fact is None or fact.get("evidence_state") not in claim_states:
                continue
            for claim in fact["claim_tokens"]:
                if claim not in expected_claims:
                    expected_claims.append(claim)
        if copy_block.state == "omit":
            if copy_block.claims:
                errors.append(
                    f"copy {copy_block.section} omit state requires empty claims"
                )
        elif (
            len(copy_block.claims) != len(set(copy_block.claims))
            or set(copy_block.claims) != set(expected_claims)
        ):
            errors.append(
                f"copy {copy_block.section} claims do not match referenced fact tokens"
            )
        for claim in copy_block.claims:
            if claim not in CLAIM_TOKENS:
                errors.append(f"copy {copy_block.section} has uncontrolled claim {claim}")
        for claim in sorted(all_fact_claim_tokens):
            if (
                _normalized_code_is_exposed(copy_block.actual_copy, claim)
                and (claim not in copy_block.claims or claim not in expected_claims)
            ):
                errors.append(
                    f"copy {copy_block.section} actual copy exposes undeclared or "
                    f"unsupported claim {claim}"
                )
        for blocked_claim in blocked_claims:
            if (
                blocked_claim in copy_block.claims
                or _normalized_code_is_exposed(copy_block.actual_copy, blocked_claim)
            ):
                errors.append(
                    f"copy {copy_block.section} exposes blocked claim {blocked_claim}"
                )
        for evidence_id in copy_block.evidence_ids:
            if evidence_id not in known_evidence:
                errors.append(
                    f"copy {copy_block.section} references unknown evidence {evidence_id}"
                )
        if copy_block.state == "requires_confirmation" and not any(
            facts.get(fact_id, {}).get("evidence_state") in {"unknown", "inferred"}
            for fact_id in copy_block.fact_ids
        ):
            errors.append(
                f"copy {copy_block.section} requires confirmation but has no unconfirmed fact"
            )
        expected_boundary = {
            "ready": "USE_ONLY_SUPPORTED_FACTS",
            "omit": "OMIT_UNSUPPORTED_OUTCOME",
        }.get(copy_block.state)
        if copy_block.state == "requires_confirmation":
            boundary_valid = copy_block.claim_boundary.startswith("CONFIRM_")
        else:
            boundary_valid = expected_boundary is not None and copy_block.claim_boundary == expected_boundary
        if copy_block.state and not boundary_valid:
            errors.append(f"copy {copy_block.section} has a contradictory claim boundary")
    return errors


def _validate_blocked_claims(
    parsed: ParsedClientReport,
    blocked_claims: tuple[str, ...],
    copies: tuple[ReportCopyBlock, ...],
) -> list[str]:
    body = parsed.section_bodies["do_not_change"]
    explicit_items = [
        line
        for line in _split_markdown_lines(body)
        if re.match(r"[ \t]*(?:[-*+]|\d+[.)])[ \t]+", line)
    ]
    errors: list[str] = []
    if len(explicit_items) > 3:
        errors.append("do not change section must contain at most three explicit items")
    label = re.escape(BLOCKED_CLAIM_LABELS[parsed.locale])
    pattern = re.compile(rf"^[ \t]*[-*+][ \t]+{label}:[ \t]*`([^`]+)`")
    visible_claims = tuple(
        match.group(1)
        for line in explicit_items
        if (match := pattern.match(line)) is not None
    )
    if visible_claims != blocked_claims:
        errors.append("visible blocked claims do not match fixture blocked_claims")
    ready_facts = {
        fact_id
        for copy_block in copies
        if copy_block.state == "ready"
        for fact_id in copy_block.fact_ids
    }
    for claim in visible_claims:
        if claim in ready_facts:
            errors.append(f"ready copy duplicates blocked claim {claim}")
    return errors


def _validate_private_plan_scope(parsed: ParsedClientReport) -> list[str]:
    label_actions = PRIVATE_PLAN_LABEL_ACTIONS[parsed.locale]
    boundary_lines = PRIVATE_PLAN_NO_EXTERNAL_ACTION[parsed.locale]
    plan_lines = _split_markdown_lines(parsed.section_bodies["plan"])
    for line in plan_lines:
        stripped = _trim_markdown_whitespace(line)
        if not stripped or stripped in boundary_lines:
            continue
        match = re.fullmatch(
            r"[ \t]*(?:[-*+]|\d+[.)])[ \t]+([^:]+):[ \t]*"
            r"([A-Z]+(?:_[A-Z]+)*)\|([a-z]+(?:_[a-z]+)*)",
            line,
        )
        if match is None:
            return ["private seven-day plan requires closed action and target codes"]
        label, action, target = (
            _trim_markdown_whitespace(match.group(1)),
            match.group(2),
            match.group(3),
        )
        if (
            label_actions.get(label) != action
            or target not in PRIVATE_PLAN_ACTION_TARGETS.get(action, frozenset())
        ):
            return ["private seven-day plan requires closed action and target codes"]
        if _private_plan_has_forbidden_action(f"{action}|{target}"):
            return [
                "private seven-day plan may contain only profile, copy, evidence, or proof work"
            ]
    return []


def _parse_evidence_questions(parsed: ParsedClientReport) -> tuple[EvidenceQuestion, ...]:
    questions: list[EvidenceQuestion] = []
    prefix = re.escape(QUESTION_HEADING[parsed.locale])
    for heading, body in _h3_blocks(parsed.section_bodies["evidence_needed"]):
        match = re.fullmatch(rf"{prefix}[ \t]+([1-9]\d*)", heading)
        if match is None:
            continue
        rank = int(match.group(1))
        fields = _localized_fields(
            body,
            QUESTION_FIELD_LABELS[parsed.locale],
            f"evidence question {rank}",
        )
        questions.append(
            EvidenceQuestion(
                rank,
                fields.get("question", ""),
                _single_code(fields.get("fact_id", "")),
                _single_code(fields.get("decision", "")),
                frozenset(fields),
            )
        )
    return tuple(questions)


def _is_meaningful_question(text: str) -> bool:
    words = [word.casefold() for word in _WORD.findall(text)]
    if len(words) < 3:
        return False
    normalized = " ".join(words)
    return not any(
        normalized == placeholder or normalized.startswith(f"{placeholder} ")
        for placeholder in QUESTION_PLACEHOLDER_PREFIXES
    )


def _validate_pending_evidence(
    parsed: ParsedClientReport,
    fixture_copies: tuple[Mapping[str, object], ...],
    facts: Mapping[str, Mapping[str, object]],
) -> list[str]:
    questions = _parse_evidence_questions(parsed)
    errors: list[str] = []
    signatures: list[tuple[str, str]] = []
    required_signatures = {
        (fact_id, f"copy:{copy_block['section']}")
        for copy_block in fixture_copies
        if copy_block["state"] == "requires_confirmation"
        for fact_id in copy_block["fact_ids"]
        if facts.get(fact_id, {}).get("evidence_state") in {"unknown", "inferred"}
    }
    for question in questions:
        for field in ("question", "fact_id", "decision"):
            if field not in question.present_fields:
                errors.append(f"evidence question {question.rank} missing required field: {field}")
        question_is_meaningful = _is_meaningful_question(question.question)
        if not question_is_meaningful:
            errors.append(
                f"evidence question {question.rank} requires meaningful question text"
            )
        signature = (question.fact_id, question.decision)
        if signature not in required_signatures:
            errors.append(
                f"evidence question {question.rank} does not change its declared decision"
            )
        if question_is_meaningful:
            signatures.append(signature)
    if (
        len(signatures) != len(set(signatures))
        or set(signatures) != required_signatures
        or len(signatures) != len(required_signatures)
    ):
        errors.append(
            "pending evidence questions must exactly match confirmation copy decisions"
        )
    return errors


def validate_report_pair_differentiation(
    report_a: object,
    bundle_a: object,
    report_b: object,
    bundle_b: object,
) -> list[str]:
    """Validate that two reports make materially different structured decisions."""
    if not isinstance(report_a, str) or not isinstance(report_b, str):
        return ["report pair must contain Markdown text"]
    if not isinstance(bundle_a, Mapping) or not isinstance(bundle_b, Mapping):
        return ["report pair requires two fixture objects"]
    errors = [
        *(f"report A: {error}" for error in validate_client_report(report_a, bundle_a)),
        *(f"report B: {error}" for error in validate_client_report(report_b, bundle_b)),
    ]
    try:
        _decision_ledger(bundle_a)
        _decision_ledger(bundle_b)
        parsed_a = parse_client_report(report_a)
        parsed_b = parse_client_report(report_b)
        priorities_a = parse_priority_blocks(parsed_a)
        priorities_b = parse_priority_blocks(parsed_b)
        copies_a = parse_copy_blocks(parsed_a)
        copies_b = parse_copy_blocks(parsed_b)
        primary_copy_category_a = parse_visible_primary_copy_category(parsed_a)
        primary_copy_category_b = parse_visible_primary_copy_category(parsed_b)
    except (_InvalidDecisionBundle, TypeError, ValueError) as error:
        message = str(error) or "report pair requires valid decision ledgers"
        return _deduplicate([*errors, message])

    if len(priorities_a) != 3 or len(priorities_b) != 3:
        return _deduplicate([
            *errors,
            "report pair requires exactly three priorities per report",
        ])
    required_priority_fields = frozenset({
        "diagnosed_gap", "action_type", "evidence_ids", "timebox", "done_when",
        "impact_basis",
    })
    required_copy_fields = frozenset({
        "copy_id", "state", "audience", "problem", "fact_ids", "evidence_ids",
        "claim_boundary", "claims", "actual_copy",
    })
    if (
        any(
            not priority.section
            or not required_priority_fields.issubset(priority.present_fields)
            for priority in priorities_a + priorities_b
        )
        or len(copies_a) != 3
        or len(copies_b) != 3
        or primary_copy_category_a not in COPY_SECTIONS
        or primary_copy_category_b not in COPY_SECTIONS
        or any(
            not required_copy_fields.issubset(copy_block.present_fields)
            for copy_block in copies_a + copies_b
        )
    ):
        return _deduplicate([*errors, "report pair requires complete structured decisions"])
    differing = sum(
        _report_priority_fingerprint(left) != _report_priority_fingerprint(right)
        for left, right in zip(priorities_a, priorities_b)
    )
    if differing < 2:
        errors.append("report pair must differ in at least two priority fingerprints")
    if priorities_a[0].diagnosed_gap == priorities_b[0].diagnosed_gap:
        errors.append("report pair must not reuse the same primary diagnosed gap")

    if primary_copy_category_a == primary_copy_category_b:
        errors.append("report pair must recommend a different primary copy category")
    return _deduplicate(errors)


def validate_fixture_bundle(bundle: object) -> list[str]:
    """Return deterministic errors for a closed synthetic fixture bundle."""
    if not isinstance(bundle, Mapping):
        return ["fixture must be a JSON object"]

    errors: list[str] = []
    _validate_fields(bundle, "fixture", REQUIRED_BUNDLE_FIELDS, errors)
    errors.extend(_scan_privacy(bundle))
    if set(bundle) != REQUIRED_BUNDLE_FIELDS:
        return _deduplicate(errors)

    expected = {
        "schema_version": "linkedin-client-report-v2-fixture-2",
        "origin_class": "synthetic_from_authorized_structural_review",
        "derivation": "composite_plus_counterfactual_perturbation",
        "real_profile_mapping": "none_created",
    }
    for field, value in expected.items():
        if bundle[field] != value:
            errors.append(f"fixture must use {field}={value}")
    _validate_pattern(bundle["fixture_id"], "fixture_id", "fixture", errors)
    _validate_pattern(bundle["internal_candidate_id"], "internal_candidate_id", "fixture", errors)
    _validate_enum(bundle["locale"], LOCALES, "fixture", "locale", errors)
    _validate_date(bundle["evaluation_date"], "fixture", "evaluation_date", errors)
    _validate_enum(bundle["evidence_mode"], EVIDENCE_MODES, "fixture", "evidence_mode", errors)

    observation_ids = _validate_structural_state(bundle["structural_state_fixture"], errors)
    fact_ids = _validate_facts(bundle["synthetic_fact_catalog"], errors)
    _validate_sources(
        bundle["source_catalog"],
        errors,
        evaluation_date=bundle["evaluation_date"],
    )
    _validate_score_ledger(bundle["score_ledger"], bundle["evidence_mode"], observation_ids, errors)
    fixture_id = bundle["fixture_id"]
    candidate_id = bundle["internal_candidate_id"]
    fixture_discriminator = _identifier_discriminator(fixture_id, "fixture_id")
    candidate_discriminator = _identifier_discriminator(
        candidate_id,
        "internal_candidate_id",
    )
    if (
        fixture_discriminator is not None
        and candidate_discriminator is not None
        and fixture_discriminator != candidate_discriminator
    ):
        errors.append(
            "fixture and internal_candidate_id discriminators must match"
        )
    expectations = bundle["eval_expectations"]
    closed_priority_enums = bool(
        isinstance(expectations, Mapping)
        and expectations.get("primary_gap") in PRIMARY_GAPS
    )
    _validate_priorities(
        bundle["priorities"], observation_ids, errors, closed_priority_enums
    )
    _validate_copies(bundle["copy_blocks"], fact_ids, observation_ids, errors)
    _validate_enum_list(bundle["blocked_claims"], BLOCKED_CLAIMS, "blocked_claims", errors)
    _validate_authorization(bundle["authorization_state"], errors)
    _validate_expectations(
        bundle["eval_expectations"],
        bundle["priorities"],
        errors,
        closed_priority_enums,
    )
    return _deduplicate(errors)


def _validate_fields(
    value: Mapping[str, Any],
    label: str,
    fields: frozenset[str],
    errors: list[str],
    missing_phrase: str = "missing required field",
) -> None:
    for field in sorted(set(value) - fields):
        errors.append(f"{label} has unsupported field: {field}")
    for field in sorted(fields - set(value)):
        errors.append(f"{label} {missing_phrase}: {field}")


def _closed_object(
    value: object,
    label: str,
    fields: frozenset[str],
    errors: list[str],
    missing_phrase: str = "missing required field",
) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{label} must be a JSON object")
        return None
    _validate_fields(value, label, fields, errors, missing_phrase)
    return value if set(value) == fields else None


def _object_list(value: object, label: str, errors: list[str]) -> list[object]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    return value


def _validate_enum(value: object, allowed: frozenset[object], label: str, field: str, errors: list[str]) -> None:
    try:
        is_valid = value in allowed
    except TypeError:
        is_valid = False
    if not is_valid:
        errors.append(f"{label} has invalid {field}")


def _is_finite_number(value: object) -> bool:
    if type(value) is int:
        return True
    return type(value) is float and math.isfinite(value)


def _is_json_integer(value: object) -> bool:
    return type(value) is int


def _validate_pattern(value: object, field: str, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or _ID_PATTERNS[field].fullmatch(value) is None:
        errors.append(f"{label} has invalid {field}")


def _identifier_discriminator(value: object, field: str) -> str | None:
    if not isinstance(value, str) or _ID_PATTERNS[field].fullmatch(value) is None:
        return None
    return value.split("-", 2)[1]


def _validate_priority_value(
    value: object,
    label: str,
    field: str,
    errors: list[str],
) -> None:
    pattern = PRIORITY_TIMEBOX_PATTERN if field == "timebox" else PRIORITY_CODE_PATTERN
    if (
        not isinstance(value, str)
        or pattern.fullmatch(value) is None
        or (field in {"diagnosed_gap", "action_type"} and _is_generic_priority_code(value))
        or (field != "timebox" and _private_plan_has_forbidden_action(value))
    ):
        errors.append(f"{label} has invalid {field}")


def _validate_date(value: object, label: str, field: str, errors: list[str]) -> None:
    try:
        if not isinstance(value, str):
            raise ValueError
        date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} has invalid {field}")


def _validate_string_list(value: object, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{label} must be a list of strings")
        return []
    return value


def _validate_enum_list(value: object, allowed: frozenset[str], label: str, errors: list[str]) -> list[str]:
    items = _validate_string_list(value, label, errors)
    for item in items:
        if item not in allowed:
            errors.append(f"{label} has invalid value: {item}")
    return items


def _validate_structural_state(value: object, errors: list[str]) -> set[str]:
    state = _closed_object(value, "structural_state_fixture", STRUCTURAL_STATE_FIELDS, errors)
    if state is None:
        return set()
    evidence_ids: set[str] = set()
    for raw in _object_list(state["observations"], "structural_state_fixture.observations", errors):
        label = "observation"
        observation = _closed_object(raw, label, OBSERVATION_FIELDS, errors)
        if observation is None:
            continue
        _validate_pattern(observation["evidence_id"], "evidence_id", label, errors)
        _validate_enum(observation["section"], OBSERVATION_SECTIONS, label, "section", errors)
        _validate_enum(observation["state"], OBSERVATION_STATES, label, "state", errors)
        evidence_id = observation["evidence_id"]
        if isinstance(evidence_id, str):
            if evidence_id in evidence_ids:
                errors.append(f"structural_state_fixture has duplicate evidence_id: {evidence_id}")
            evidence_ids.add(evidence_id)
    return evidence_ids


def _validate_facts(value: object, errors: list[str]) -> set[str]:
    fact_ids: set[str] = set()
    for index, raw in enumerate(_object_list(value, "synthetic_fact_catalog", errors)):
        label = f"synthetic_fact_catalog[{index}]"
        fact = _closed_object(raw, label, FACT_FIELDS, errors)
        if fact is None:
            continue
        _validate_pattern(fact["fact_id"], "fact_id", label, errors)
        _validate_enum(fact["evidence_state"], EVIDENCE_STATES, label, "evidence_state", errors)
        _validate_enum(fact["fact_type"], FACT_TYPES, label, "fact_type", errors)
        _validate_enum(fact["role_family"], ROLE_FAMILIES, label, "role_family", errors)
        _validate_enum(fact["capability_family"], CAPABILITY_FAMILIES, label, "capability_family", errors)
        _validate_enum(fact["scope_bucket"], SCOPE_BUCKETS, label, "scope_bucket", errors)
        _validate_enum_list(fact["claim_tokens"], CLAIM_TOKENS, f"{label}.claim_tokens", errors)
        fact_id = fact["fact_id"]
        if isinstance(fact_id, str):
            if fact_id in fact_ids:
                errors.append(f"synthetic_fact_catalog has duplicate fact_id: {fact_id}")
            fact_ids.add(fact_id)
    return fact_ids


def _validate_score_ledger(value: object, evidence_mode: object, observation_ids: set[str], errors: list[str]) -> None:
    ledger = _closed_object(value, "score_ledger", SCORE_LEDGER_FIELDS, errors)
    if ledger is None:
        return
    _validate_enum(ledger["confidence"], CONFIDENCE_STATES, "score_ledger", "confidence", errors)
    numeric_total_is_valid = (
        _is_finite_number(ledger["numeric_weighted_total"])
        and 0 <= ledger["numeric_weighted_total"] <= 100
    )
    if not numeric_total_is_valid:
        errors.append("score_ledger has invalid numeric_weighted_total")
    integer_fields_are_valid: dict[str, bool] = {}
    for field in ("scored_weight", "not_scored_weight", "overall_score"):
        integer_fields_are_valid[field] = (
            _is_json_integer(ledger[field]) and 0 <= ledger[field] <= 100
        )
        if not integer_fields_are_valid[field]:
            errors.append(f"score_ledger has invalid {field}")

    domains: list[Mapping[str, Any]] = []
    arithmetic_domains: list[Mapping[str, Any]] = []
    seen_domains: set[str] = set()
    for index, raw in enumerate(_object_list(ledger["domains"], "score_ledger.domains", errors)):
        label = f"score_ledger.domains[{index}]"
        row = _closed_object(raw, label, DOMAIN_SCORE_FIELDS, errors)
        if row is None:
            continue
        _validate_enum(row["domain"], frozenset(DOMAIN_WEIGHTS), label, "domain", errors)
        _validate_enum(row["state"], SCORE_STATES, label, "state", errors)
        _validate_enum(row["reason_code"], REASON_CODES, label, "reason_code", errors)
        domain = row["domain"]
        domain_is_valid = isinstance(domain, str) and domain in DOMAIN_WEIGHTS
        if domain_is_valid:
            if domain in seen_domains:
                errors.append(f"score_ledger has duplicate domain: {domain}")
            seen_domains.add(domain)
        weight_is_valid = (
            domain_is_valid
            and _is_json_integer(row["weight"])
            and row["weight"] == DOMAIN_WEIGHTS[domain]
        )
        if not weight_is_valid:
            errors.append(f"{label} has invalid weight")
        state_is_valid = isinstance(row["state"], str) and row["state"] in SCORE_STATES
        weighted_points_are_valid = (
            _is_finite_number(row["weighted_points"])
            and 0 <= row["weighted_points"] <= 20
        )
        if not weighted_points_are_valid:
            errors.append(f"{label} has invalid weighted_points")

        raw_score_is_valid = False
        if state_is_valid and row["state"] == "not_scored":
            raw_score_is_valid = row["raw_score"] is None
            if not raw_score_is_valid or not weighted_points_are_valid or row["weighted_points"] != 0:
                errors.append(f"{label} not_scored values must be null and zero")
        elif state_is_valid and row["state"] == "scored":
            raw_score_is_valid = (
                _is_finite_number(row["raw_score"])
                and 0 <= row["raw_score"] <= 100
            )
            if not raw_score_is_valid:
                errors.append(f"{label} has invalid raw_score")
            elif weight_is_valid and weighted_points_are_valid:
                expected_points = row["raw_score"] * row["weight"] / 100
                if abs(expected_points - row["weighted_points"]) > 1e-9:
                    errors.append(f"{label} weighted_points do not reconcile")
        _validate_references(
            row["evidence_ids"], observation_ids, label, "evidence_id", errors,
            require_nonempty=True,
        )
        domains.append(row)
        if (
            domain_is_valid
            and state_is_valid
            and weight_is_valid
            and weighted_points_are_valid
            and raw_score_is_valid
        ):
            arithmetic_domains.append(row)
    if seen_domains != set(DOMAIN_WEIGHTS):
        errors.append("score_ledger must contain exactly the seven canonical domains")
    can_reconcile = (
        numeric_total_is_valid
        and all(integer_fields_are_valid.values())
        and len(arithmetic_domains) == 7
        and seen_domains == set(DOMAIN_WEIGHTS)
    )
    if can_reconcile:
        scored_weight = sum(row["weight"] for row in arithmetic_domains if row["state"] == "scored")
        not_scored_weight = sum(row["weight"] for row in arithmetic_domains if row["state"] == "not_scored")
        points = sum(row["weighted_points"] for row in arithmetic_domains if row["state"] == "scored")
        if ledger["scored_weight"] != scored_weight or ledger["not_scored_weight"] != not_scored_weight:
            errors.append("score_ledger coverage weights do not reconcile")
        if abs(ledger["numeric_weighted_total"] - points) > 1e-9:
            errors.append("score_ledger numeric_weighted_total does not reconcile")
        expected_score = int(points / scored_weight * 100 + 0.5) if scored_weight else None
        if ledger["overall_score"] != expected_score:
            errors.append("score_ledger overall_score does not reconcile")
    visual = next((row for row in domains if row["domain"] == "visual"), None)
    if (
        isinstance(evidence_mode, str)
        and evidence_mode in {"structural_only", "partial_visual_photo_only", "partial_visual_banner_only"}
        and visual is not None
        and visual["state"] != "not_scored"
    ):
        errors.append("fixture evidence_mode requires visual to be not_scored")


def _validate_priorities(
    value: object,
    known_evidence: set[str],
    errors: list[str],
    closed_priority_enums: bool,
) -> None:
    items = _object_list(value, "priorities", errors)
    if len(items) != 3:
        errors.append("fixture requires exactly three priorities")
    ranks: list[object] = []
    for index, raw in enumerate(items):
        label = f"priorities[{index}]"
        item = _closed_object(raw, label, PRIORITY_FIELDS, errors)
        if item is None:
            continue
        _validate_pattern(item["priority_id"], "priority_id", label, errors)
        if not _is_json_integer(item["rank"]) or item["rank"] not in {1, 2, 3}:
            errors.append(f"{label} has invalid rank")
        _validate_enum(item["section"], PRIORITY_SECTIONS, label, "section", errors)
        if closed_priority_enums:
            _validate_enum(item["diagnosed_gap"], DIAGNOSED_GAPS, label, "diagnosed_gap", errors)
            _validate_enum(item["action_type"], ACTION_TYPES, label, "action_type", errors)
            _validate_enum(item["timebox"], TIMEBOXES, label, "timebox", errors)
            _validate_enum(item["done_when"], DONE_WHEN_CODES, label, "done_when", errors)
        else:
            _validate_priority_value(item["diagnosed_gap"], label, "diagnosed_gap", errors)
            _validate_priority_value(item["action_type"], label, "action_type", errors)
            _validate_priority_value(item["timebox"], label, "timebox", errors)
            _validate_priority_value(item["done_when"], label, "done_when", errors)
        _validate_enum(item["impact_basis"], IMPACT_BASES, label, "impact_basis", errors)
        _validate_references(
            item["evidence_ids"], known_evidence, label, "evidence_id", errors,
            require_nonempty=True,
        )
        ranks.append(item["rank"])
    if sorted(rank for rank in ranks if _is_json_integer(rank)) != [1, 2, 3]:
        errors.append("fixture priority ranks must be exactly 1, 2, 3")


def _validate_copies(value: object, fact_ids: set[str], known_evidence: set[str], errors: list[str]) -> None:
    items = _object_list(value, "copy_blocks", errors)
    if len(items) != 3:
        errors.append("fixture requires exactly three copy_blocks")
    sections: list[object] = []
    for index, raw in enumerate(items):
        label = f"copy_blocks[{index}]"
        item = _closed_object(raw, label, COPY_FIELDS, errors)
        if item is None:
            continue
        _validate_pattern(item["copy_id"], "copy_id", label, errors)
        _validate_enum(item["section"], COPY_SECTIONS, label, "section", errors)
        _validate_enum(item["state"], COPY_STATES, label, "state", errors)
        _validate_enum(item["audience"], AUDIENCES, label, "audience", errors)
        _validate_enum(item["problem"], COPY_PROBLEMS, label, "problem", errors)
        _validate_enum(item["claim_boundary"], CLAIM_BOUNDARIES, label, "claim_boundary", errors)
        _validate_references(item["fact_ids"], fact_ids, label, "fact_id", errors)
        _validate_references(
            item["evidence_ids"], known_evidence, label, "evidence_id", errors,
            require_nonempty=True,
        )
        if isinstance(item["section"], str) and item["section"] in COPY_SECTIONS:
            sections.append(item["section"])
    if set(sections) != set(COPY_SECTIONS):
        errors.append("fixture copy_blocks must cover headline, about_opening, and experience_bullet")


def resolve_source_state(source: Mapping[str, object], evaluation_date: date) -> str:
    """Resolve freshness from the fixture evaluation date, never the system clock."""
    if source.get("reachability") == "unreachable":
        return "unreachable"
    try:
        access_date = date.fromisoformat(source["access_date"])
    except (KeyError, TypeError, ValueError):
        return "stale"
    age = (evaluation_date - access_date).days
    return "current" if 0 <= age <= 90 else "stale"


def _decoded_url_component(value: str, *, reject_traversal: bool = False) -> str | None:
    """Bounded fixed-point percent decoding with ambiguity/traversal rejection."""
    current = _nfkc_without_format_characters(value)
    for _ in range(5):
        if "\ufffd" in current or re.search(r"%(?![0-9A-Fa-f]{2})", current):
            return None
        normalized_path = current.replace("\\", "/")
        if reject_traversal and any(
            segment in {".", ".."} for segment in normalized_path.split("/")
        ):
            return None
        decoded = unquote(current)
        if decoded == current:
            return current
        current = _nfkc_without_format_characters(decoded)
    if re.search(r"%[0-9A-Fa-f]{2}", current):
        return None
    normalized_path = current.replace("\\", "/")
    if reject_traversal and any(
        segment in {".", ".."} for segment in normalized_path.split("/")
    ):
        return None
    return current


def _canonical_source_url_parts(
    value: object,
) -> tuple[object, str, str, str] | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
    ):
        return None
    path = _decoded_url_component(parsed.path, reject_traversal=True)
    query = _decoded_url_component(parsed.query)
    fragment = _decoded_url_component(parsed.fragment)
    if path is None or "\\" in path or query is None or fragment is None:
        return None
    return parsed, path, query, fragment


def _contains_sensitive_marker(value: str) -> bool:
    normalized = _normalized_guard_text(value).casefold()
    components = tuple(re.findall(r"[a-z0-9]+", normalized))
    compact = "".join(components)
    return bool(
        set(components) & _SENSITIVE_KEY_COMPONENTS
        or any(part in compact for part in _SENSITIVE_COMPACT_KEY_PARTS)
    )


def _source_metadata_is_sensitive(query: str, fragment: str) -> bool:
    metadata = _normalized_guard_text(f"{query}#{fragment}")
    for item in re.split(r"[&;#]", metadata):
        key_and_value = re.split(r"[:=]", item, maxsplit=1)
        if any(_contains_sensitive_marker(part) for part in key_and_value):
            return True
    return bool(
        _EMAIL.search(metadata)
        or _PHONE.search(metadata)
        or _PROFILE_URL.search(metadata)
        or _LOCAL_PATH.search(metadata)
        or _ANY_URL.search(metadata)
    )


def _provenance_contains_sensitive_or_private_content(value: str) -> bool:
    normalized = _normalized_guard_text(value)
    return bool(
        _contains_sensitive_marker(normalized)
        or _EMAIL.search(normalized)
        or _PHONE.search(normalized)
        or _PROFILE_URL.search(normalized)
        or _LOCAL_PATH.search(normalized)
        or _ANY_URL.search(normalized)
        or RAW_PROFILE_ALIAS.search(normalized)
        or PRIVATE_ANALYTICS_ALIAS.search(normalized)
    )


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _load_source_registry(path: Path) -> Mapping[str, tuple[Mapping[str, str], ...]]:
    try:
        raw = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("LinkedIn source registry is missing or malformed") from error
    if not isinstance(raw, Mapping) or set(raw) != {
        "registry_version", "official_categories",
    }:
        raise ValueError("LinkedIn source registry is missing or malformed")
    if raw["registry_version"] != "linkedin-source-registry-1":
        raise ValueError("LinkedIn source registry is missing or malformed")
    categories = raw["official_categories"]
    if not isinstance(categories, Mapping) or set(categories) != set(SOURCE_CATEGORIES):
        raise ValueError("LinkedIn source registry is missing or malformed")

    normalized: dict[str, tuple[Mapping[str, str], ...]] = {}
    locator_keys: set[tuple[str, str]] = set()
    for category in sorted(SOURCE_CATEGORIES):
        raw_locators = categories[category]
        if not isinstance(raw_locators, list) or not raw_locators:
            raise ValueError("LinkedIn source registry is missing or malformed")
        locators: list[Mapping[str, str]] = []
        for locator in raw_locators:
            if not isinstance(locator, Mapping) or set(locator) != {
                "host", "path_prefix",
            }:
                raise ValueError("LinkedIn source registry is missing or malformed")
            host = locator["host"]
            path_prefix = locator["path_prefix"]
            if (
                not isinstance(host, str)
                or host != host.casefold()
                or host.endswith(".")
                or not isinstance(path_prefix, str)
                or not path_prefix.startswith("/")
                or path_prefix.endswith("/")
                or "\\" in path_prefix
                or "?" in path_prefix
                or "#" in path_prefix
                or _decoded_url_component(path_prefix, reject_traversal=True)
                != path_prefix
            ):
                raise ValueError("LinkedIn source registry is missing or malformed")
            locator_key = (host, path_prefix)
            if locator_key in locator_keys:
                raise ValueError("LinkedIn source registry is missing or malformed")
            locator_keys.add(locator_key)
            locators.append(MappingProxyType({
                "host": host,
                "path_prefix": path_prefix,
            }))
        normalized[category] = tuple(locators)
    return MappingProxyType(normalized)


try:
    OFFICIAL_SOURCE_REGISTRY = _load_source_registry(SOURCE_REGISTRY_PATH)
    SOURCE_REGISTRY_ERROR: str | None = None
except ValueError as error:
    OFFICIAL_SOURCE_REGISTRY = MappingProxyType({})
    SOURCE_REGISTRY_ERROR = str(error)


def _is_registered_official_source(source_category: object, value: object) -> bool:
    if SOURCE_REGISTRY_ERROR is not None or not isinstance(source_category, str):
        return False
    canonical = _canonical_source_url_parts(value)
    if canonical is None:
        return False
    parsed, decoded_path, _, _ = canonical
    host = (parsed.hostname or "").casefold().rstrip(".")
    return any(
        host == locator["host"]
        and (
            decoded_path == locator["path_prefix"]
            or decoded_path.startswith(f"{locator['path_prefix']}/")
        )
        for locator in OFFICIAL_SOURCE_REGISTRY.get(source_category, ())
    )


def _is_any_registered_official_source(value: object) -> bool:
    return any(
        _is_registered_official_source(category, value)
        for category in SOURCE_CATEGORIES
    )


def resolve_methodology_sources(
    categories: Sequence[str],
) -> tuple[Mapping[str, str], ...]:
    """Return immutable canonical source locators for requested categories."""
    if (
        SOURCE_REGISTRY_ERROR is not None
        or not isinstance(categories, Sequence)
        or isinstance(categories, (str, bytes))
        or any(not isinstance(category, str) for category in categories)
        or any(category not in SOURCE_CATEGORIES for category in categories)
        or len(categories) != len(set(categories))
    ):
        raise ValueError("methodology source category is unsupported")
    return tuple(
        MappingProxyType({
            "source_category": category,
            "url": f"https://{locator['host']}{locator['path_prefix']}",
        })
        for category in categories
        for locator in OFFICIAL_SOURCE_REGISTRY[category]
    )


def _host_is_numeric_ip_form(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass
    numeric_label = re.compile(r"(?:0[xX][0-9A-Fa-f]+|0[0-7]*|[0-9]+)")
    return bool(host and all(numeric_label.fullmatch(label) for label in host.split(".")))


def _host_is_reserved_or_special_use(host: str) -> bool:
    return bool(
        host in _SECONDARY_RESERVED_EXAMPLE_HOSTS
        or any(host.endswith(f".{reserved}") for reserved in _SECONDARY_RESERVED_EXAMPLE_HOSTS)
        or host in {suffix[1:] for suffix in _SECONDARY_SPECIAL_USE_HOST_SUFFIXES}
        or host.endswith(_SECONDARY_SPECIAL_USE_HOST_SUFFIXES)
    )


def _secondary_source_url_error(value: object) -> str | None:
    if not isinstance(value, str):
        return "secondary URL must use HTTPS"
    try:
        parsed = urlsplit(value)
    except ValueError:
        return "secondary URL must use HTTPS"
    if parsed.scheme.casefold() != "https":
        return "secondary URL must use HTTPS"
    if parsed.username is not None or parsed.password is not None:
        return "secondary URL cannot include credentials"
    try:
        if parsed.port is not None:
            return "secondary URL cannot include a port"
    except ValueError:
        return "secondary URL cannot include a port"

    host = (parsed.hostname or "").casefold().rstrip(".")
    labels = host.split(".")
    host_is_valid = bool(
        host
        and "." in host
        and not _host_is_numeric_ip_form(host)
        and not _host_is_reserved_or_special_use(host)
        and not host.endswith(_SECONDARY_PRIVATE_HOST_SUFFIXES)
        and all(not label.startswith("xn--") for label in labels)
        and all(
            re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
            for label in labels
        )
    )
    if not host_is_valid:
        return "secondary URL host must be a public hostname"

    path = _decoded_url_component(parsed.path, reject_traversal=True)
    query = _decoded_url_component(parsed.query)
    fragment = _decoded_url_component(parsed.fragment)
    if path is None:
        return "secondary URL must use HTTPS"
    if "\\" in path:
        return "secondary URL cannot include a backslash path"
    if host == "linkedin.com" or host.endswith(".linkedin.com"):
        folded_path = path.casefold()
        if folded_path in {"/in", "/pub"} or folded_path.startswith(("/in/", "/pub/")):
            return "secondary URL cannot be a LinkedIn profile URL"
    if query is None or fragment is None:
        return "secondary URL cannot include a sensitive query or fragment"
    if _source_metadata_is_sensitive(query, fragment):
        return "secondary URL cannot include a sensitive query or fragment"
    return None


def validate_secondary_source_url(value: object) -> list[str]:
    """Return the existing secondary-source URL policy result without input echo."""
    error = _secondary_source_url_error(value)
    return [] if error is None else [error]


def _validate_sources(
    value: object,
    errors: list[str],
    *,
    evaluation_date: object = None,
) -> set[str]:
    source_ids: set[str] = set()
    official_categories: set[str] = set()
    official_category_counts = {category: 0 for category in SOURCE_CATEGORIES}
    if SOURCE_REGISTRY_ERROR is not None:
        errors.append(SOURCE_REGISTRY_ERROR)
    try:
        fixture_date = date.fromisoformat(evaluation_date) if isinstance(evaluation_date, str) else None
    except ValueError:
        fixture_date = None
    for index, raw in enumerate(_object_list(value, "source_catalog", errors)):
        label = f"source_catalog[{index}]"
        if not isinstance(raw, Mapping):
            errors.append(f"{label} must be a JSON object")
            continue
        unsupported_fields = set(raw) - SOURCE_FIELDS
        missing_fields = SOURCE_REQUIRED_FIELDS - set(raw)
        for field in sorted(unsupported_fields):
            errors.append(f"{label} has unsupported field: {field}")
        for field in sorted(missing_fields):
            errors.append(f"{label} missing required field: {field}")
        if unsupported_fields or missing_fields:
            continue
        source = raw
        _validate_pattern(source["source_id"], "source_id", label, errors)
        _validate_enum(source["source_category"], SOURCE_CATEGORIES, label, "source_category", errors)
        _validate_enum(source["source_class"], SOURCE_CLASSES, label, "source_class", errors)
        source_class = source["source_class"]
        source_category = source["source_category"]
        url_is_allowed = False
        if source_class == "official":
            if isinstance(source_category, str) and source_category in SOURCE_CATEGORIES:
                official_category_counts[source_category] += 1
            canonical = _canonical_source_url_parts(source["url"])
            sensitive_metadata = bool(
                canonical is not None
                and _source_metadata_is_sensitive(canonical[2], canonical[3])
            )
            registered_official_url = _is_registered_official_source(
                source_category, source["url"]
            )
            url_is_allowed = registered_official_url and not sensitive_metadata
            if sensitive_metadata:
                errors.append(
                    f"{label} official URL cannot include a sensitive query or fragment"
                )
            if not registered_official_url and isinstance(source_category, str):
                errors.append(
                    f"{label} official URL is not registered for source_category "
                    f"{source_category}"
                )
        elif source_class == "secondary":
            secondary_url_error = _secondary_source_url_error(source["url"])
            url_is_allowed = secondary_url_error is None
            if secondary_url_error is not None:
                errors.append(f"{label} {secondary_url_error}")
        for provenance_field in ("publisher", "document_title"):
            provenance_value = source.get(provenance_field)
            if provenance_field not in source:
                if source_class == "secondary":
                    errors.append(
                        f"{label} secondary source requires non-empty "
                        f"{provenance_field}"
                    )
            elif not isinstance(provenance_value, str) or not provenance_value.strip():
                prefix = "secondary source " if source_class == "secondary" else ""
                errors.append(
                    f"{label} {prefix}requires non-empty {provenance_field}"
                )
            else:
                limit = PROVENANCE_LIMITS[provenance_field]
                if _PROVENANCE_LINE_BREAK.search(provenance_value) or len(provenance_value) > limit:
                    errors.append(
                        f"{label} {provenance_field} must be a single line of at most "
                        f"{limit} characters"
                    )
                if _provenance_contains_sensitive_or_private_content(provenance_value):
                    errors.append(
                        f"{label} {provenance_field} contains sensitive or private content"
                    )
        _validate_date(source["access_date"], label, "access_date", errors)
        _validate_enum(source["reachability"], REACHABILITY_STATES, label, "reachability", errors)
        _validate_enum(source["scope"], SOURCE_SCOPES, label, "scope", errors)
        _validate_enum(source["inference_limit"], INFERENCE_LIMITS, label, "inference_limit", errors)
        _validate_enum(source["fallback"], SOURCE_FALLBACKS, label, "fallback", errors)
        if (
            source_class == "official"
            and isinstance(source["source_category"], str)
            and source["source_category"] in SOURCE_CATEGORIES
            and url_is_allowed
        ):
            official_categories.add(source["source_category"])
        if fixture_date is not None:
            state = resolve_source_state(source, fixture_date)
            fallback = source["fallback"]
            fallback_is_safe = isinstance(fallback, str) and fallback in {
                "COACH_HEURISTIC", "BLOCK_CLAIM",
            }
            if state in {"stale", "unreachable"} and not fallback_is_safe:
                errors.append(
                    f"source {source['source_id']} resolved {state} and must degrade to "
                    "COACH_HEURISTIC or BLOCK_CLAIM"
                )
        source_id = source["source_id"]
        if isinstance(source_id, str):
            if source_id in source_ids:
                errors.append(f"source_catalog has duplicate source_id: {source_id}")
            source_ids.add(source_id)
    for category in sorted(SOURCE_CATEGORIES - official_categories):
        errors.append(f"source_catalog missing required official source category: {category}")
    for category, count in sorted(official_category_counts.items()):
        if count > 1:
            errors.append(
                f"source_catalog requires exactly one official source for category: {category}"
            )
    return source_ids


def _validate_authorization(value: object, errors: list[str]) -> None:
    item = _closed_object(
        value,
        "authorization_state",
        AUTHORIZATION_FIELDS,
        errors,
        missing_phrase="has missing field",
    )
    if item is None:
        return
    _validate_enum(item["inspection"], INSPECTION_AUTHORIZATIONS, "authorization_state", "inspection", errors)
    _validate_enum(item["external_actions"], EXTERNAL_ACTION_AUTHORIZATIONS, "authorization_state", "external_actions", errors)
    _validate_enum(item["action_state"], ACTION_STATES, "authorization_state", "action_state", errors)


def _validate_expectations(
    value: object,
    priorities: object,
    errors: list[str],
    closed_priority_enums: bool,
) -> None:
    item = _closed_object(value, "eval_expectations", EVAL_EXPECTATION_FIELDS, errors)
    if item is None:
        return
    _validate_enum(item["scenario_class"], SCENARIO_CLASSES, "eval_expectations", "scenario_class", errors)
    if closed_priority_enums:
        _validate_enum(
            item["primary_gap"],
            PRIMARY_GAPS,
            "eval_expectations",
            "primary_gap",
            errors,
        )
    else:
        _validate_priority_value(
            item["primary_gap"],
            "eval_expectations",
            "primary_gap",
            errors,
        )
    _validate_enum(item["primary_copy_category"], COPY_SECTIONS, "eval_expectations", "primary_copy_category", errors)
    _validate_enum(item["pending_evidence_policy"], PENDING_EVIDENCE_POLICIES, "eval_expectations", "pending_evidence_policy", errors)
    if isinstance(priorities, list):
        primary = next(
            (
                priority
                for priority in priorities
                if isinstance(priority, Mapping) and priority.get("rank") == 1
            ),
            None,
        )
        if (
            primary is not None
            and isinstance(primary.get("diagnosed_gap"), str)
            and item["primary_gap"] != primary["diagnosed_gap"]
        ):
            errors.append("eval_expectations primary_gap must match priority rank 1")


def _validate_references(
    value: object,
    known: set[str],
    label: str,
    kind: str,
    errors: list[str],
    *,
    require_nonempty: bool = False,
) -> None:
    references = _validate_string_list(value, f"{label}.{kind}s", errors)
    if require_nonempty and not references:
        errors.append(f"{label}.{kind}s must contain at least one reference")
    for reference in _duplicates(references):
        errors.append(f"{label}.{kind}s has duplicate {kind}: {reference}")
    for reference in references:
        if reference not in known:
            errors.append(f"{label} references unknown {kind}: {reference}")


def _scan_privacy(value: object, path: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            errors.extend(_scan_privacy(nested, child_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            errors.extend(_scan_privacy(nested, f"{path}[{index}]"))
    elif isinstance(value, str):
        canonical_source = (
            _canonical_source_url_parts(value)
            if re.fullmatch(r"source_catalog\[\d+\]\.url", path) is not None
            else None
        )
        is_proven_source_url = (
            canonical_source is not None
            and (
                _is_any_registered_official_source(value)
                or _secondary_source_url_error(value) is None
            )
        )
        scan_value = value
        if canonical_source is not None:
            parsed_url, decoded_path, decoded_query, decoded_fragment = canonical_source
            scan_value = (
                f"https://{parsed_url.hostname or ''}{decoded_path}"
                f"?{decoded_query}#{decoded_fragment}"
            )
        scan_value = _normalized_guard_text(scan_value)
        casefolded_value = scan_value.casefold()
        for prefix, label in _FORBIDDEN_URI_PREFIXES:
            if casefolded_value.startswith(prefix):
                errors.append(f"fixture contains forbidden {label} value at {path}")
                return errors
        checks = (("email-like", _EMAIL), ("phone-like", _PHONE), ("LinkedIn profile URL", _PROFILE_URL), ("local-path", _LOCAL_PATH))
        for label, pattern in checks:
            if pattern.search(scan_value):
                errors.append(f"fixture contains forbidden {label} value at {path}")
        if (
            _ANY_URL.search(scan_value)
            and not is_proven_source_url
            and not any(pattern.search(scan_value) for _, pattern in checks)
        ):
            errors.append(
                f"fixture contains forbidden URL value outside source_catalog[].url at {path}"
            )
    return errors


def _deduplicate(errors: list[str]) -> list[str]:
    return list(dict.fromkeys(errors))


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a LinkedIn client report fixture pair.")
    parser.add_argument("report", type=Path)
    parser.add_argument("bundle", type=Path)
    parser.add_argument(
        "--appendix-mode",
        choices=sorted(APPENDIX_MODES),
        default="normal",
    )
    arguments = parser.parse_args(argv)

    errors: list[str] = []
    try:
        markdown = arguments.report.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        errors.append("cannot read report file as UTF-8")
        markdown = ""
    try:
        raw_bundle = arguments.bundle.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        errors.append("cannot read bundle file as UTF-8")
        raw_bundle = ""
    bundle: object = None
    if raw_bundle:
        try:
            bundle = json.loads(raw_bundle, object_pairs_hook=_unique_json_object)
        except (json.JSONDecodeError, RecursionError, ValueError):
            errors.append("bundle file must contain valid JSON")

    if not errors:
        try:
            fixture_errors = validate_fixture_bundle(bundle)
            if fixture_errors:
                errors.extend(fixture_errors)
            else:
                assert isinstance(bundle, Mapping)
                errors.extend(
                    validate_client_report(
                        markdown,
                        bundle,
                        appendix_mode=arguments.appendix_mode,
                    )
                )
        except Exception:
            errors.append("validation failed for malformed input")
    if errors:
        for error in sorted(set(errors)):
            print(error, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
