#!/usr/bin/env python3
"""Validate closed, identity-free LinkedIn executive career dossiers."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from private_input_loader import PrivateInputError, read_bounded_bytes
from typing import Any


SCHEMA_VERSION = "executive-career-dossier-v1"
DOSSIER_KIND = "linkedin_profile_diagnostic"


def _enum(value: object, allowed: set[str] | frozenset[str]) -> bool:
    return isinstance(value, str) and value in allowed
DOMAIN_WEIGHTS = {
    "visual": 15,
    "headline": 15,
    "about": 15,
    "experience": 20,
    "skills": 15,
    "proof": 10,
    "completeness": 10,
}

TOP_FIELDS = frozenset({
    "schema_version", "dossier_kind", "locale", "evidence_as_of", "case_scope",
    "benchmarking", "requested_technology_terms", "focus", "evidence_scope", "evidence", "claims", "verdict",
    "coverage", "priorities", "recruiter_scan", "dimensions", "visual_review",
    "copy_blocks", "do_not_change", "screen_bridge", "questions", "seven_day_plan",
    "analytics", "market_context", "methodology_source_categories", "privacy", "authorization",
})
SECTIONS = frozenset({"headline", "about", "experience", "skills", "proof", "completeness", "photo", "banner", "visual"})
EVIDENCE_SECTIONS = SECTIONS | {"analytics", "market"}
EVIDENCE_SOURCE_KINDS = frozenset({
    "provided_material", "candidate_statement", "authorized_visible",
    "consented_aggregate", "dated_vacancy_research",
})
PROFILE_EVIDENCE_SOURCE_KINDS = frozenset({
    "provided_material", "candidate_statement", "authorized_visible",
})
EVIDENCE_STATES = frozenset({"verified", "candidate_reported", "inferred", "unknown"})
EVIDENCE_STATE_STRENGTH = {
    "unknown": 0,
    "inferred": 1,
    "candidate_reported": 2,
    "verified": 3,
}
VISUAL_STATES = frozenset({"unavailable", "structural_only", "partial_visual", "authorized_visual_visible"})
METHOD_CATEGORIES = frozenset({"ai_hiring_agents", "cover_image", "featured_section", "good_profile", "job_match", "job_seeker_hirer_connection", "profile_photo", "skills"})
COPY_CATEGORIES = ("headline", "about_opening", "experience_bullet")
PRIVATE_PLAN_CATEGORIES = frozenset({"confirm_target", "validate_fact", "review_copy", "prepare_proof"})
ID_PATTERN = re.compile(r"[EC]-\d{3}\Z")
CAPTURE_REF_PATTERN = re.compile(r"CAP-\d{3}\Z")
PLACEHOLDER = re.compile(r"^(?:GAP|ACTION|TIMEBOX|DONE-WHEN)-|^(?:TBD|TODO|PENDIENTE)\Z", re.I)
MARKET_LANGUAGE = re.compile(
    r"\b(?:salary|salaries|compensation|pay\s+range|employer\s+demand|"
    r"market|market\s+demand|high\s+demand|in[- ]demand|rank(?:ing|ed|s)?|"
    r"salarios?|sueldos?|remuneraci[oó]n|compensaci[oó]n|alta\s+demanda|"
    r"mercado|demanda\s+(?:laboral|del\s+mercado|de\s+empleadores)|r[aá]nking)\b",
    re.I,
)
MARKET_CLAIM_LANGUAGE = re.compile(
    r"\b(?:vacancies|openings|jobs|vacantes|empleos|employer\s+demand|hiring\s+demand|"
    r"demanda|oportunidades\s+laborales|sought|solicitad[oa]s?|scarce|escas[oa]s?|"
    r"outpaces?\s+supply|supera\s+la\s+oferta|difficult\s+for\s+employers?\s+to\s+fill|"
    r"dificil(?:es)?\s+de\s+cubrir|eager\s+to\s+hire|compete\s+for\s+(?:this\s+)?talent|"
    r"scarcity|escasez|escasea|(?:candidate|talent)\s+shortage|"
    r"open\s+roles?\s+exceed\s+available\s+candidates?|"
    r"(?:are|aren\s+t|are\s+not)\s+enough\s+(?:candidates?|talent)|"
    r"too\s+few\s+(?:candidates?|people|roles?)|"
    r"employers?\s+struggle\s+to\s+fill|"
    r"compiten\s+por\s+(?:este\s+)?talento)\b",
    re.I,
)
EMPLOYMENT_CONTINUITY_NEGATED = re.compile(
    r"\b(?:not\s+(?:advice|a\s+recommendation)\b[^.!?,;:]{0,64}\b(?:resign|quit|leave)\b|"
    r"do\s+not\s+advise\b[^.!?,;:]{0,64}\b(?:resign|quit|leave)\b|"
    r"no\s+(?:es\s+un[ao]?\s+)?(?:recomendaci[oó]n|consejo)\b[^.!?,;:]{0,64}\b(?:renunci(?:ar|a)|dejar|deja)\b|"
    r"no\s+se\s+recomienda\b[^.!?,;:]{0,64}\b(?:dejar|renunciar)\b|"
    r"no\s+(?:se\s+)?aconseja(?:mos)?\b[^.!?,;:]{0,64}\b(?:dejar|renunciar)\b|"
    r"sin\s+(?:recomendar|aconsejar)\b[^.!?,;:]{0,64}\b(?:dejar|renunciar)\b|"
    r"sin\s+(?:dejar|renunciar)\b)",
    re.I,
)
EMPLOYMENT_SEPARATION_IMPERATIVE = re.compile(
    r"\b(?:you\s+(?:should|must|need\s+to|have\s+to)\s+)?(?:resign|quit)\s+"
    r"(?:now|today|your\s+(?:current\s+)?(?:job|role|employment|company|employer)|the\s+(?:job|role|company)|"
    r"from\s+(?:your\s+)?(?:current\s+)?(?:job|role|employment|company|employer))\b|"
    r"\b(?:you\s+(?:should|must|need\s+to|have\s+to)\s+)?leave\s+"
    r"(?:your\s+|the\s+)?(?:current\s+)?(?:job|role|employer|employment|company)\b|"
    r"\b(?:renuncia|renunciar)\s+(?:ahora|hoy|a\s+tu\s+(?:empleo|trabajo))\b|"
    r"\b(?:deja|dejar)\s+(?:tu\s+)?(?:empleo|trabajo|empresa)\b|"
    r"\b(?:reduce|reducir)\s+(?:your\s+|tus\s+)?(?:working\s+)?hours\b|"
    r"\b(?:reduce|reducir)\s+tu\s+jornada(?:\s+laboral)?\b|"
    r"\b(?:reduce|reducir)\s+(?:tu|tus)\s+(?:horario|horas\s+laborales)\b|"
    r"\b(?:crea|crear)\s+(?:una\s+)?brecha\s+(?:voluntaria|laboral|de\s+empleo)\b|"
    r"\b(?:create|crear)\s+(?:a\s+)?(?:voluntary\s+)?(?:employment\s+)?gap\b|"
    r"\b(?:abandona|abandonar)\s+(?:tu\s+)?(?:empleo|trabajo|empresa)\b|"
    r"\b(?:recommend(?:s|ed)?|recomiendo|recomienda)\s+(?:that\s+you\s+)?(?:resign|quit|renunciar)\b",
    re.I,
)
UNRECONCILED_MARKET_STRENGTH = re.compile(
    r"\b(?:strong|high|active|abundant|plentiful|numerous|eager|widely\s+sought|"
    r"outpaces?\s+supply|difficult\s+for\s+employers?\s+to\s+fill|scarce|"
    r"alta|fuerte|activa|abundante|muy\s+solicitad[oa]s?|sobran|"
    r"compiten\s+por|escas[oa]s?|escasea|scarcity|escasez|"
    r"(?:candidate|talent)\s+shortage|open\s+roles?\s+exceed\s+available\s+candidates?|"
    r"(?:are|aren\s+t|are\s+not)\s+enough\s+(?:candidates?|talent)|"
    r"too\s+few\s+(?:candidates?|people|roles?)|"
    r"employers?\s+struggle\s+to\s+fill|dificil(?:es)?\s+de\s+cubrir)\b",
    re.I,
)
ANALYTICS_MEASURE_LANGUAGE = re.compile(
    r"(?:\b\d[\d,.%]*\b[^.!?\n]{0,80}\b(?:profile\s+views?|views?|"
    r"inbound\s+contacts?|qualified\s+contacts?|conversion\s+rate|"
    r"search\s+appearances?|visitas?|visualizaciones?|contactos?|"
    r"tasa\s+de\s+conversi[oó]n|apariciones?\s+en\s+b[uú]squedas?)\b|"
    r"\b(?:profile\s+views?|views?|inbound\s+contacts?|qualified\s+contacts?|"
    r"conversion\s+rate|search\s+appearances?|visitas?|visualizaciones?|"
    r"contactos?|tasa\s+de\s+conversi[oó]n|apariciones?\s+en\s+b[uú]squedas?)"
    r"\b[^.!?\n]{0,80}\b\d[\d,.%]*\b)",
    re.I,
)
ANALYTICS_LANGUAGE = re.compile(
    r"\b(?:profile\s+(?:views?|reach|engagement|visibility|traffic)|views?|inbound\s+contacts?|"
    r"qualified\s+contacts?|conversion\s+rate|search\s+appearances?|reach|"
    r"engagement|visits?|visitas?|vistas?|visualizaciones?|contactos?|tasa\s+de\s+conversion|"
    r"apariciones?\s+en\s+busquedas?|alcance\s+del\s+perfil|visibilidad\s+del\s+perfil|"
    r"trafico\s+del\s+perfil|"
    r"interaccion(?:es)?\s+del\s+perfil)\b",
    re.I,
)
ANALYTICS_TREND_LANGUAGE = re.compile(
    r"\b(?:rose|rising|increased?|improved?|grew|grown|growth|doubled?|tripled?|"
    r"fell|fallen|declined?|decreased?|changed?|higher|lower|up|down|"
    r"aumento|aumentaron|subio|subieron|mejoro|mejoraron|crecio|crecieron|"
    r"duplico|duplicaron|triplico|triplicaron|cayo|cayeron|disminuyo|"
    r"disminuyeron|bajo|bajaron|tendencia)\b",
    re.I,
)
ANALYTICS_QUANTITY_LANGUAGE = re.compile(
    r"\b(?:\d[\d,.%]*|zero|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)"
    r"(?:[ -](?:one|two|three|four|five|six|seven|eight|nine))?|hundred|thousand|"
    r"cero|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|"
    r"trece|catorce|quince|dieci(?:seis|siete|ocho|nueve)|veinte|"
    r"veinti(?:uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve)|"
    r"(?:treinta|cuarenta|cincuenta|sesenta|setenta|ochenta|noventa)"
    r"(?:\s+y\s+(?:uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve))?|"
    r"cien|ciento|mil)\b",
    re.I,
)
UNSUPPORTED_DEMAND_LANGUAGE = re.compile(
    r"\b(?:many|numerous|plenty\s+of|lots\s+of)\s+(?:vacancies|openings|jobs)\b|"
    r"\b(?:muchas?|numerosas?)\s+vacantes\b|"
    r"\bemployers?\b[^.!?\n]{0,48}\b(?:actively\s+)?(?:seek|search\s+for|"
    r"look\s+for|want|hire|demand)\b|"
    r"\b(?:empleadores?|reclutadores?)\b[^.!?\n]{0,48}\b(?:buscan|"
    r"contratan|demandan|necesitan)\b",
    re.I,
)
PRIVATE_EXTERNAL_ACTION = re.compile(
    r"(?:^|[.!?]\s+)(?:please\s+)?(?:edit|update|publish|post|contact|apply|"
    r"message|upload|share|schedule|send|email|connect)\b|"
    r"(?:^|[.!?]\s+)(?:por\s+favor\s+)?(?:edita|actualiza|publica|postea|"
    r"contacta|aplica|postula|mensajea|env[ií]a|manda|sube|carga|comparte|"
    r"programa|agenda|conecta)\b|"
    r"(?:^|[.!?]\s+)(?:editar|actualizar|publicar|postear|contactar|aplicar|"
    r"postular|mensajear|enviar|mandar|subir|cargar|compartir|programar|"
    r"agendar|conectar)\b|"
    r"(?:,\s*then\s+|\b(?:and(?:\s+then)?|then)\s+)(?:edit|update|publish|post|"
    r"contact|apply|message|upload|share|schedule|send|email|connect)\b|"
    r"\b(?:y(?:\s+luego)?|luego)\s+(?:edita|actualiza|publ[ií]ca(?:lo|la|los|las)?|"
    r"postea|contacta|aplica|postula|mensajea|env[ií]a|manda|sube|carga|"
    r"comparte|programa|agenda|conecta)\b|"
    r"\byou\s+(?:must|should)\s+(?:edit|update|publish|post|contact|apply|"
    r"message|upload|share|schedule|send|email|connect)\b|"
    r"\bdebes?\s+(?:editar|actualizar|publicar|postear|contactar|aplicar|"
    r"postular|mensajear|enviar|mandar|subir|cargar|compartir|programar|"
    r"agendar|conectar)\b|"
    r"\b(?:is|are|queda|quedan|est[aá]|est[aá]n)\s+(?:published|posted|"
    r"contacted|applied|messaged|uploaded|shared|scheduled|sent|emailed|"
    r"connected|publicad[oa]s?|contactad[oa]s?|aplicad[oa]s?|postulad[oa]s?|"
    r"enviad[oa]s?|subid[oa]s?|cargad[oa]s?|compartid[oa]s?|programad[oa]s?|"
    r"agendad[oa]s?|conectad[oa]s?)\b",
    re.I,
)
NORMALIZED_PRIVATE_EXTERNAL_ACTION = re.compile(
    r"(?:^|\b(?:now|please|then|when ready|you can|you should|you must|"
    r"use linkedin to|the next step is)\s+)(?:edit|update|publish|post|contact|"
    r"apply|message|upload|share|schedule|send|email|connect)\b|"
    r"\breach out\b|"
    r"(?:^|\b(?:ahora|por favor|luego|cuando este listo|puedes|debes|"
    r"el siguiente paso es)\s+)(?:edita|actualiza|publica(?:lo|la|los|las)?|"
    r"postea|contacta|aplica|postula|mensajea|envia|manda|sube|carga|"
    r"comparte|programa|agenda|conecta|editar|actualizar|publicar|postear|"
    r"contactar|aplicar|postular|mensajear|enviar|mandar|subir|cargar|"
    r"compartir|programar|agendar|conectar)\b|"
    r"\blinkedin (?:shows|muestra)\b[^.!?]*(?:updated|published|posted|sent|shared|nuevo|actualizado|publicado|enviado)|"
    r"\bdone\s+(?:published|posted|sent|shared|uploaded)|"
    r"\b(?:went live|has gone out|have gone out)\b|"
    r"\bya quedo\s+(?:publicado|publicada|enviado|enviada|compartido|compartida)\b",
    re.I,
)
NORMALIZED_EXTERNAL_ACTION_ANYWHERE = re.compile(
    r"\b(?:edit|update|publish|post|contact|apply|upload|share|schedule|send|email|connect|"
    r"editing|updating|publishing|posting|contacting|applying|messaging|"
    r"uploading|sharing|scheduling|sending|emailing|connecting|edited|updated|"
    r"published|posted|contacted|applied|messaged|uploaded|shared|scheduled|sent|"
    r"emailed|connected)\b|"
    r"\b(?:edita|actualiza|publica(?:lo|la|los|las)?|postea|contacta|aplica|postula|"
    r"envia|manda|sube|carga|comparte|programa|agenda|conecta|"
    r"edite|actualice|publique|postee|contacte|aplique|postule|envie|mande|subi|"
    r"cargue|comparti|programe|agende|conecte|"
    r"editar|actualizar|publicar(?:lo|la|los|las)?|postear|contactar|aplicar|"
    r"postular|mensajear|enviar|mandar|subir|cargar|compartir|programar|agendar|"
    r"conectar|editando|actualizando|publicando|posteando|contactando|aplicando|"
    r"postulando|mensajeando|enviando|mandando|subiendo|cargando|compartiendo|"
    r"programando|agendando|conectando|editad[oa]s?|actualizad[oa]s?|publicad[oa]s?|"
    r"postead[oa]s?|contactad[oa]s?|aplicad[oa]s?|postulad[oa]s?|mensajead[oa]s?|"
    r"enviad[oa]s?|mandad[oa]s?|subid[oa]s?|cargad[oa]s?|compartid[oa]s?|"
    r"programad[oa]s?|agendad[oa]s?|conectad[oa]s?)\b|"
    r"\b(?:consider|considera)\s+(?:publishing|posting|sending|publicar|postear|enviar)\b|"
    r"\b(?:linkedin|recruiter|reclutador)\b[^.!?]{0,48}\b(?:appears?|visible|"
    r"contacted|sent|published|posted|aparece|visible|contactado|enviado|publicado)\b|"
    r"\b(?:appears?|visible|queda\s+visible)\b[^.!?]{0,32}\blinkedin\b",
    re.I,
)
NORMALIZED_LIVE_EXTERNAL_STATE = re.compile(
    r"\b(?:headline|profile|copy|message|titular|perfil|copia|mensaje)\b[^.!?]{0,24}\b"
    r"(?:is|esta|queda)\s+(?:now\s+|ahora\s+)?(?:live|visible|public|publicad[oa])\b"
    r"(?:[^.!?]{0,24}\blinkedin\b)?|"
    r"\b(?:headline|profile|copy|message|titular|perfil|copia|mensaje)\b"
    r"[^.!?]{0,32}\b(?:can\s+now\s+be\s+seen|(?:now\s+)?(?:appears?|shows?))\b"
    r"[^.!?]{0,32}\blinkedin\b|"
    r"\blinkedin\b[^.!?]{0,32}\b(?:shows?|displays?|muestra)\b"
    r"[^.!?]{0,32}\b(?:headline|profile|copy|message|titular|perfil|copia|mensaje)\b",
    re.I,
)
NORMALIZED_SAFE_ACTION_CONTEXT = re.compile(
    r"\bdo not publish the draft keep it private\b|"
    r"\bconfirm the recruiter was not contacted\b|"
    r"\breview the published vacancy in a private note\b",
    re.I,
)
NORMALIZED_OUTCOME_GUARANTEE = re.compile(
    r"\b(?:an?\s+)?(?:interview|offer|job)\s+follows?\s+(?:this|the)\s+(?:change|revision)\b|"
    r"\b(?:this|the)\s+(?:change|revision|profile|headline)\b[^.!?]{0,32}\b"
    r"(?:guarantees?|lands?|leads?\s+to)\s+(?:interviews?|offers?|jobs?|recruiter\s+messages?)\b|"
    r"\b(?:entrevista|oferta|empleo|trabajo)\b[^.!?,;:]{0,24}\b(?:sigue|seguira)\b",
    re.I,
)
DOSSIER_OUTCOME_GUARANTEE = re.compile(
    r"\b(?:recruiters?|employers?)\s+will\s+(?:call|contact|message|interview|hire)\b|"
    r"\b(?:an?\s+)?(?:interview|offer|job)\s+is\s+(?:assured|guaranteed)\b|"
    r"\byou\s+will\s+(?:(?:get|be)\s+)?(?:hired|interviewed|contacted|messaged)\b|"
    r"\byou\s+will\s+(?:get|receive|land)\s+(?:an?\s+)?(?:interview|offer|job)\b|"
    r"\b(?:reclutadores?|empleadores?)\s+(?:llamar[aá]n|contactar[aá]n|"
    r"escribir[aá]n|entrevistar[aá]n|contratar[aá]n)\b|"
    r"\b(?:la\s+)?(?:entrevista|oferta|vacante)\s+est[aá]\s+garantizada\b|"
    r"\b(?:conseguir[aá]s|obtendr[aá]s|recibir[aá]s)\s+(?:una?\s+)?"
    r"(?:entrevista|oferta|vacante|empleo|trabajo)\b|"
    r"\b(?:this\s+\w+|this|the\s+change)\s+lands?\s+(?:interviews?|offers?|jobs?)\b|"
    r"\b(?:an?\s+)?(?:interview|offer|job)\s+follows?\s+(?:this|the)\s+change\b|"
    r"\bwill\s+lead\s+to\s+(?:recruiter\s+)?(?:messages?|interviews?|offers?)\b|"
    r"\bte\s+van\s+a\s+contratar\b|"
    r"\b(?:la\s+)?contrataci[oó]n\s+est[aá]\s+asegurada\b",
    re.I,
)
IDENTITY_CUE = re.compile(
    r"\b(?:candidate(?:\s+name)?|prepared\s+for|nombre(?:\s+del\s+candidat[oa])?)\s*:|"
    r"\b(?:my\s+name\s+is|me\s+llamo)\b",
    re.I,
)
RAW_COPY_CUE = re.compile(
    r"\bcopied\s+directly\s+from\s+the\s+linkedin\s+profile\b|"
    r"\bexact\s+copied\s+headline\s+text\s+from\s+the\s+profile\b|"
    r"\b(?:exact|verbatim)\s+(?:copied\s+)?(?:headline|about|experience|profile)\s+text\b|"
    r"\btexto\s+(?:exacto\s+copiado|copiado\s+literalmente)\s+del\s+perfil\b",
    re.I,
)
CONFIDENTIAL_IDENTITY_CUE = re.compile(
    r"\b(?:confidential\s+(?:employer|company)|(?:empleador|empresa)\s+confidencial)\s*:",
    re.I,
)
EXPERTISE_PROMOTION_LANGUAGE = re.compile(
    r"\b(?:expert|specialist)(?:\s+(?:in|with))?\b|"
    r"\b(?:proficient|skilled)\s+(?:in|with)\b|"
    r"\b(?:expertise|proficiency|mastery)\s+(?:in|of|with|for)\b|"
    r"\b(?:advanced|senior)\b[^.!?]{0,64}\bpractitioner\b|"
    r"\b(?:strong|advanced|deep|extensive|proven)\b[^.!?]{0,64}\b"
    r"(?:skills?|experience|mastery)\b|"
    r"\b(?:especialista|experto|experta)\s+en\b|"
    r"\bdominio\s+de\b|"
    r"\b(?:domina|dominando)\b|"
    r"\b(?:habilidad|competencia)\s+(?:avanzada\s+)?en\b",
    re.I,
)
MARKET_FRESHNESS_DAYS = 90
KNOWN_DOSSIER_FIELDS = TOP_FIELDS | frozenset({
    "inspection_mode", "captured_as_of", "inspected_sections", "unavailable_sections",
    "confidence", "visual_state", "visual_capture_ref", "id", "state", "section",
    "source_kind", "paraphrase", "capture_ref", "evidence_ids", "public_use",
    "statement", "claim_ids", "rationale", "start_here_action", "evidence_state",
    "evaluated_count", "scored_weight", "not_scored_weight", "overall_score",
    "rank", "title", "problem", "why_now", "action", "timebox_minutes",
    "done_when", "dimensions", "understood_signal", "ambiguity", "positioning_bridge",
    "dimension", "score", "reason", "photo", "banner", "finding", "private_action",
    "category", "copy", "why_it_works", "claim_boundary", "question_rank", "question",
    "changes", "linked_copy_category", "day", "private_report",
    "candidate_identity_included", "contact_data_included", "raw_profile_retained",
    "raw_private_analytics_included", "aggregate_analytics_included",
    "external_actions_authorized", "action_state", "explicit_report_consent",
    "observed_as_of", "window_days", "raw_records_retained", "profile_views",
    "inbound_contacts", "qualified_contacts", "qualified_contact_rate",
    "causality_boundary", "geography", "arrangement", "research_date",
    "vacancy_sample_count", "target_roles", "required_signals", "supported_signals",
    "gaps", "public_sources", "url", "publisher", "document_title", "access_date",
    "requested_technology_terms", "term",
})


class DossierLoadError(ValueError):
    """Raised for safe, deterministic dossier input failures."""


def _load_linkedin_safety_module() -> Any:
    path = Path(__file__).with_name("validate_linkedin_client_report.py")
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_linkedin_safety", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("LinkedIn safety validator is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    for name in (
        "resolve_methodology_sources",
        "validate_candidate_facing_text",
        "validate_secondary_source_url",
    ):
        if not callable(getattr(module, name, None)):
            raise RuntimeError("LinkedIn safety validator is unavailable")
    return module


LINKEDIN_SAFETY = _load_linkedin_safety_module()


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DossierLoadError("duplicate JSON key")
        result[key] = value
    return result


def _assert_max_depth(value: object, maximum: int, depth: int = 0) -> None:
    if depth > maximum:
        raise DossierLoadError("dossier exceeds maximum nesting depth")
    if isinstance(value, Mapping):
        for nested in value.values():
            _assert_max_depth(nested, maximum, depth + 1)
    elif isinstance(value, list):
        for nested in value:
            _assert_max_depth(nested, maximum, depth + 1)


def load_dossier(path: Path) -> dict[str, object]:
    try:
        raw = read_bounded_bytes(path, 256 * 1024)
    except PrivateInputError as error:
        message = {
            "symlink": "dossier input must not be a symlink",
            "too_large": "dossier exceeds 256 KiB",
        }.get(error.reason, "cannot read dossier")
        raise DossierLoadError(message) from error
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, DossierLoadError) as error:
        if isinstance(error, DossierLoadError):
            raise
        raise DossierLoadError("dossier must be valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise DossierLoadError("dossier must be a JSON object")
    _assert_max_depth(value, 12)
    return value


def calculate_dossier_score(
    domains: Sequence[Mapping[str, object]],
) -> tuple[int | None, int, int, str]:
    scored = [
        row
        for row in domains
        if row.get("state") == "evaluated"
        and isinstance(row.get("dimension"), str)
        and row["dimension"] in DOMAIN_WEIGHTS
        and type(row.get("score")) is int
    ]
    scored_weight = sum(DOMAIN_WEIGHTS[row["dimension"]] for row in scored)
    not_scored_weight = 100 - scored_weight
    weighted = sum(
        row["score"] * DOMAIN_WEIGHTS[row["dimension"]]
        for row in scored
        if isinstance(row.get("dimension"), str)
    )
    normalized = Decimal(weighted) / Decimal(scored_weight) if scored_weight else None
    score = None if scored_weight < 75 else int(normalized.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    confidence = "high" if scored_weight >= 90 else "medium" if scored_weight >= 50 else "low"
    return score, scored_weight, not_scored_weight, confidence


def _closed(value: object, path: str, fields: frozenset[str], errors: list[str]) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    if set(value) - fields:
        errors.append(f"{path} has unsupported fields")
    for key in sorted(fields - set(value)):
        errors.append(f"{path} missing required field: {key}")
    return value


def _text(value: object, path: str, errors: list[str], *, nullable: bool = False, limit: int = 500) -> bool:
    if nullable and value is None:
        return True
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        errors.append(f"{path} must be bounded client-facing prose")
        return False
    if PLACEHOLDER.search(value.strip()):
        errors.append(f"{path} must be client-facing prose")
        return False
    return True


def _validate_employment_continuity(value: object, path: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        return
    normalized = unicodedata.normalize("NFKD", value).casefold()
    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) not in {"Cf", "Mn"}
    )
    normalized = " ".join(normalized.split())
    if EMPLOYMENT_CONTINUITY_NEGATED.search(normalized):
        return
    if EMPLOYMENT_SEPARATION_IMPERATIVE.search(normalized):
        errors.append(f"{path} must preserve current employment by default")


def _date(value: object, path: str, errors: list[str]) -> date | None:
    if not isinstance(value, str):
        errors.append(f"{path} must be an ISO date")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path} must be an ISO date")
        return None


def _string_list(value: object, path: str, errors: list[str], *, minimum: int = 0, maximum: int | None = None) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{path} must be a list of strings")
        return []
    if len(value) < minimum or (maximum is not None and len(value) > maximum):
        errors.append(f"{path} has invalid item count")
    if len(value) != len(set(value)):
        errors.append(f"{path} must not contain duplicates")
    return value


def _references(value: object, known: set[str], path: str, prefix: str, errors: list[str], *, minimum: int = 0) -> list[str]:
    items = _string_list(value, path, errors, minimum=minimum)
    for item in items:
        if ID_PATTERN.fullmatch(item) is None or not item.startswith(prefix):
            errors.append(f"{path} has invalid reference format")
        elif item not in known:
            errors.append(f"{path} references unknown identifier")
    return items


def validate_analytics(value: object, known_evidence: set[str]) -> list[str]:
    """Validate consented aggregate analytics without accepting raw records."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return ["analytics must be an object"]
    state = value.get("state")
    if _enum(state, {"not_requested", "unavailable"}):
        row = _closed(value, "analytics", frozenset({"state", "reason"}), errors)
        if row is not None:
            _text(row.get("reason"), "analytics.reason", errors)
        return sorted(set(errors))
    fields = frozenset({
        "state", "explicit_report_consent", "observed_as_of", "window_days",
        "raw_records_retained", "profile_views", "inbound_contacts",
        "qualified_contacts", "qualified_contact_rate", "evidence_ids",
        "causality_boundary",
    })
    row = _closed(value, "analytics", fields, errors)
    if row is None:
        return sorted(set(errors))
    if state != "observed_aggregate":
        errors.append("analytics.state has invalid state")
    if row.get("explicit_report_consent") is not True:
        errors.append("analytics.explicit_report_consent must be true")
    _date(row.get("observed_as_of"), "analytics.observed_as_of", errors)
    window = row.get("window_days")
    if type(window) is not int or window < 1:
        errors.append("analytics.window_days must be a positive integer")
    if row.get("raw_records_retained") is not False:
        errors.append("analytics.raw_records_retained must be false")
    counts: dict[str, int] = {}
    for field in ("profile_views", "inbound_contacts", "qualified_contacts"):
        count = row.get(field)
        if type(count) is not int or count < 0:
            errors.append(f"analytics.{field} must be a non-negative integer")
        else:
            counts[field] = count
    if (
        "qualified_contacts" in counts
        and "inbound_contacts" in counts
        and counts["qualified_contacts"] > counts["inbound_contacts"]
    ):
        errors.append("analytics.qualified_contacts cannot exceed inbound_contacts")
    rate = row.get("qualified_contact_rate")
    if type(rate) not in {int, float} or not 0 <= rate <= 100:
        errors.append("analytics.qualified_contact_rate must be from 0 through 100")
    elif "qualified_contacts" in counts and "inbound_contacts" in counts:
        denominator = counts["inbound_contacts"]
        expected = Decimal("0.00") if denominator == 0 else (
            Decimal(counts["qualified_contacts"]) / Decimal(denominator) * Decimal(100)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if Decimal(str(rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) != expected:
            errors.append("analytics.qualified_contact_rate does not reconcile")
    _references(
        row.get("evidence_ids"), known_evidence, "analytics.evidence_ids", "E-",
        errors, minimum=1,
    )
    if row.get("causality_boundary") != "observed_not_attributed":
        errors.append("analytics.causality_boundary must be observed_not_attributed")
    return sorted(set(errors))


def validate_market_context(
    value: object,
    evidence_as_of: date,
    known_evidence: set[str],
) -> list[str]:
    """Validate dated vacancy evidence independently from profile scoring."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return ["market_context must be an object"]
    state = value.get("state")
    if state == "not_researched":
        if set(value) != {"state", "reason"}:
            errors.append("market_context not_researched must contain no market values")
        row = _closed(value, "market_context", frozenset({"state", "reason"}), errors)
        if row is not None:
            _text(row.get("reason"), "market_context.reason", errors)
            _validate_employment_continuity(row.get("reason"), "market_context.reason", errors)
        return sorted(set(errors))
    fields = frozenset({
        "state", "geography", "arrangement", "research_date",
        "vacancy_sample_count", "target_roles", "evidence_ids", "public_sources",
    })
    row = _closed(value, "market_context", fields, errors)
    if row is None:
        return sorted(set(errors))
    if state != "dated_vacancy_evidence":
        errors.append("market_context.state has invalid state")
    _text(row.get("geography"), "market_context.geography", errors, limit=120)
    if not _enum(row.get("arrangement"), {"onsite", "hybrid", "remote", "flexible"}):
        errors.append("market_context.arrangement has invalid arrangement")
    research_date = _date(row.get("research_date"), "market_context.research_date", errors)
    if research_date is not None and research_date > evidence_as_of:
        errors.append("market_context.research_date cannot be after evidence_as_of")
    elif research_date is not None and (evidence_as_of - research_date).days > MARKET_FRESHNESS_DAYS:
        errors.append("market_context.research_date is older than 90 days")
    sample_count = row.get("vacancy_sample_count")
    if type(sample_count) is not int or sample_count <= 0:
        errors.append("market_context.vacancy_sample_count must be greater than zero")
    _references(
        row.get("evidence_ids"), known_evidence, "market_context.evidence_ids", "E-",
        errors, minimum=1,
    )
    roles = row.get("target_roles")
    if not isinstance(roles, list) or not 1 <= len(roles) <= 3:
        errors.append("market_context.target_roles has invalid item count")
    else:
        role_fields = frozenset({
            "title", "required_signals", "supported_signals", "gaps", "evidence_ids",
        })
        for index, item in enumerate(roles):
            path = f"market_context.target_roles[{index}]"
            role = _closed(item, path, role_fields, errors)
            if role is None:
                continue
            _text(role.get("title"), f"{path}.title", errors, limit=160)
            _string_list(
                role.get("required_signals"), f"{path}.required_signals", errors,
                minimum=1, maximum=8,
            )
            _string_list(
                role.get("supported_signals"), f"{path}.supported_signals", errors,
                maximum=8,
            )
            _string_list(role.get("gaps"), f"{path}.gaps", errors, maximum=8)
            _references(
                role.get("evidence_ids"), known_evidence, f"{path}.evidence_ids",
                "E-", errors, minimum=1,
            )
    sources = row.get("public_sources")
    if not isinstance(sources, list) or not 1 <= len(sources) <= 4:
        errors.append("market_context.public_sources has invalid item count")
    else:
        source_fields = frozenset({"url", "publisher", "document_title", "access_date"})
        for index, item in enumerate(sources):
            path = f"market_context.public_sources[{index}]"
            source = _closed(item, path, source_fields, errors)
            if source is None:
                continue
            for source_error in LINKEDIN_SAFETY.validate_secondary_source_url(source.get("url")):
                errors.append(f"{path}.url {source_error}")
            for field, limit in (("publisher", 120), ("document_title", 240)):
                candidate = source.get(field)
                if _text(candidate, f"{path}.{field}", errors, limit=limit):
                    for source_error in LINKEDIN_SAFETY.validate_candidate_facing_text(candidate):
                        errors.append(f"{path}.{field} {source_error}")
            access_date = _date(source.get("access_date"), f"{path}.access_date", errors)
            if access_date is not None and access_date > evidence_as_of:
                errors.append(f"{path}.access_date cannot be after evidence_as_of")
            elif access_date is not None and (
                evidence_as_of - access_date
            ).days > MARKET_FRESHNESS_DAYS:
                errors.append(f"{path}.access_date is older than 90 days")
            if (
                access_date is not None
                and research_date is not None
                and access_date > research_date
            ):
                errors.append(f"{path}.access_date cannot be after research_date")
    return sorted(set(errors))


def _state_exceeds_references(
    state: object,
    references: Sequence[str],
    states: Mapping[str, str],
) -> bool:
    if not _enum(state, EVIDENCE_STATE_STRENGTH):
        return False
    referenced_strengths = [
        EVIDENCE_STATE_STRENGTH[states[reference]]
        for reference in references
        if reference in states and states[reference] in EVIDENCE_STATE_STRENGTH
    ]
    return bool(referenced_strengths) and EVIDENCE_STATE_STRENGTH[state] > min(referenced_strengths)


def _validate_consumer_state(
    state: object,
    references: Sequence[str],
    states: Mapping[str, str],
    path: str,
    errors: list[str],
) -> None:
    if not _enum(state, EVIDENCE_STATES):
        errors.append(f"{path} has invalid evidence state")
    elif _state_exceeds_references(state, references, states):
        errors.append(f"{path} exceeds referenced evidence state")


def _privacy_errors(text: str) -> list[str]:
    errors = list(candidate_text_privacy_errors(text))
    errors.extend(LINKEDIN_SAFETY.validate_candidate_facing_text(text))
    if candidate_text_has_outcome_guarantee(text):
        errors.append("client report cannot guarantee an employment or platform outcome")
    return sorted(set(errors))


def _normalize_decision_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKD", value).casefold()
    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) not in {"Cf", "Mn"}
    )
    normalized = re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def normalize_candidate_text(value: object) -> str:
    """Normalize candidate-facing text for every lexical safety boundary."""

    return _normalize_decision_text(value)


def _normalize_outcome_text(value: object) -> str:
    """Normalize outcome prose without joining separate sentences or clauses."""

    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKD", value).casefold()
    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) not in {"Cf", "Mn"}
    )
    normalized = re.sub(r"[^\w.!?,;:]+", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def normalize_candidate_label_text(value: object) -> str:
    """Normalize obfuscation while preserving label punctuation for privacy cues."""

    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKD", value).casefold()
    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) not in {"Cf", "Mn"}
    )
    return " ".join(normalized.split())


_ENGLISH_SMALL_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
}
_ENGLISH_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
_SPANISH_SMALL_NUMBERS = {
    "cero": 0, "uno": 1, "una": 1, "un": 1, "dos": 2, "tres": 3,
    "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8,
    "nueve": 9, "diez": 10, "once": 11, "doce": 12, "trece": 13,
    "catorce": 14, "quince": 15, "dieciseis": 16, "diecisiete": 17,
    "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiuno": 21,
    "veintiuna": 21, "veintiun": 21, "veintidos": 22, "veintitres": 23,
    "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26,
    "veintisiete": 27, "veintiocho": 28, "veintinueve": 29,
}
_SPANISH_TENS = {
    "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
    "setenta": 70, "ochenta": 80, "noventa": 90,
}


def parse_bounded_number(value: object) -> int | None:
    """Parse an exact English or Spanish cardinal from zero through one hundred."""

    normalized = normalize_candidate_text(value)
    if not normalized:
        return None
    if re.fullmatch(r"\d{1,3}", normalized):
        parsed = int(normalized)
        return parsed if 0 <= parsed <= 100 else None
    collectives = {
        "dozen": 12, "a dozen": 12, "one dozen": 12,
        "docena": 12, "una docena": 12, "couple": 2, "a couple": 2,
        "one couple": 2, "a couple of": 2, "one couple of": 2,
        "par": 2, "un par": 2, "un par de": 2,
    }
    if normalized in collectives:
        return collectives[normalized]
    if normalized in {"hundred", "one hundred", "cien", "ciento"}:
        return 100
    if normalized in _ENGLISH_SMALL_NUMBERS:
        return _ENGLISH_SMALL_NUMBERS[normalized]
    english_parts = normalized.split()
    if len(english_parts) in {2, 3} and english_parts[0] in _ENGLISH_TENS:
        unit_index = 2 if len(english_parts) == 3 and english_parts[1] == "and" else 1
        if unit_index < len(english_parts):
            unit = _ENGLISH_SMALL_NUMBERS.get(english_parts[unit_index])
            if unit is not None and 1 <= unit <= 9 and unit_index == len(english_parts) - 1:
                return _ENGLISH_TENS[english_parts[0]] + unit
    if normalized in _ENGLISH_TENS:
        return _ENGLISH_TENS[normalized]
    if normalized in _SPANISH_SMALL_NUMBERS:
        return _SPANISH_SMALL_NUMBERS[normalized]
    spanish_parts = normalized.split()
    if (
        len(spanish_parts) == 3
        and spanish_parts[0] in _SPANISH_TENS
        and spanish_parts[1] == "y"
    ):
        unit = _SPANISH_SMALL_NUMBERS.get(spanish_parts[2])
        if unit is not None and 1 <= unit <= 9:
            return _SPANISH_TENS[spanish_parts[0]] + unit
    if normalized in _SPANISH_TENS:
        return _SPANISH_TENS[normalized]
    return None


def extract_bounded_numbers(value: object) -> tuple[int, ...]:
    """Extract bounded cardinals greedily so compound words are counted once."""

    tokens = normalize_candidate_text(value).split()
    numbers: list[int] = []
    index = 0
    while index < len(tokens):
        matched: tuple[int, int] | None = None
        for width in range(min(4, len(tokens) - index), 0, -1):
            parsed = parse_bounded_number(" ".join(tokens[index : index + width]))
            if parsed is not None:
                matched = parsed, width
                break
        if matched is None:
            index += 1
            continue
        parsed, width = matched
        numbers.append(parsed)
        index += width
    return tuple(numbers)


def extract_market_volume_values(value: object) -> tuple[int | None, ...]:
    """Extract bounded counts immediately attached to market-volume nouns."""

    tokens = normalize_candidate_text(value).split()
    nouns = {"vacancy", "vacancies", "opening", "openings", "job", "jobs", "vacante", "vacantes", "empleo", "empleos"}
    number_tokens = (
        set(_ENGLISH_SMALL_NUMBERS)
        | set(_ENGLISH_TENS)
        | set(_SPANISH_SMALL_NUMBERS)
        | set(_SPANISH_TENS)
        | {
            "a", "and", "of", "hundred", "dozen", "couple",
            "y", "de", "cien", "ciento", "docena", "par",
        }
    )
    values: list[int | None] = []
    for index, token in enumerate(tokens):
        if token not in nouns:
            continue
        start = index
        while start and (
            tokens[start - 1] in number_tokens
            or re.fullmatch(r"\d+", tokens[start - 1])
        ):
            start -= 1
        if start < index:
            phrase = " ".join(tokens[start:index])
            parsed = parse_bounded_number(phrase)
            # The article in ordinary prose ("a job") is not a count. Keep
            # unparseable numeric-looking phrases (for example, >100) so
            # those still fail reconciliation, but ignore article-only spans.
            if parsed is not None or phrase != "a":
                values.append(parsed)
    return tuple(values)


def extract_dated_market_sample(value: object) -> int | None:
    """Read the renderer's labeled market sample from visible candidate text."""

    normalized = normalize_candidate_text(value)
    for match in re.finditer(
        r"\b(?:dated sample|muestra fechada)\s+(.{1,48}?)\s+(?:vacancies|vacantes)\b",
        normalized,
    ):
        return parse_bounded_number(match.group(1))
    return None


def candidate_text_has_market_volume_mismatch(value: object, expected_sample: object) -> bool:
    """Return whether any visible market count differs from its labeled sample."""

    if type(expected_sample) is not int:
        return False
    return any(
        observed is None or observed != expected_sample
        for observed in extract_market_volume_values(value)
    )


_VISIBLE_NEGATED_PRIVACY_NOTICE = re.compile(
    r"\b(?:this dossier (?:does not include|includes no)|este dossier no incluye)\s+"
    r"(?:candidate )?identity\s*,?\s*contact data\s*,?\s*raw profile text\s*,?\s*"
    r"(?:or\s+)?(?:individual\s+)?private analytics\b",
    re.I,
)
_VISIBLE_SHARE_CONTACT = re.compile(
    r"\b(?:share|shares|sharing|shared|contact|contacts|contacting|contacted)\b",
    re.I,
)
_VISIBLE_DIRECT_SHARE_CONTACT_ACTION = re.compile(
    r"^(?:(?:please|now)\s+)?(?:share|contact)\b|"
    r"\b(?:when ready|then|please|now|you can|you should|you must)\s+"
    r"(?:share|contact)\b",
    re.I,
)
_VISIBLE_EXTERNAL_TARGET = re.compile(
    r"\b(?:linkedin|recruiters?|hiring managers?|employers?|companies?|candidate|"
    r"public|publicly|external|externally|network|audience|them|him|her|me|"
    r"sent|posted|published)\b",
    re.I,
)


def candidate_visible_text_privacy_errors(value: object) -> tuple[str, ...]:
    """Apply privacy checks to public text while allowing the fixed negated notice."""

    if not isinstance(value, str):
        return ()
    normalized = normalize_candidate_label_text(value)
    return candidate_text_privacy_errors(
        _VISIBLE_NEGATED_PRIVACY_NOTICE.sub(" ", normalized)
    )


def candidate_visible_text_has_external_action(value: object) -> bool:
    """Require local external context for share/contact nouns in visible text."""

    if not isinstance(value, str):
        return False
    for segment in re.split(r"[.!?\n]+", value):
        normalized = normalize_candidate_text(segment)
        if not normalized or not candidate_text_has_external_action(normalized):
            continue
        if _VISIBLE_DIRECT_SHARE_CONTACT_ACTION.search(normalized):
            return True
        without_share_contact = _VISIBLE_SHARE_CONTACT.sub(" ", normalized)
        if candidate_text_has_external_action(without_share_contact):
            return True
        if (
            _VISIBLE_SHARE_CONTACT.search(normalized)
            and _VISIBLE_EXTERNAL_TARGET.search(normalized)
        ):
            return True
    return False


def candidate_text_has_external_action(value: object) -> bool:
    normalized = normalize_candidate_text(value)
    action_text = NORMALIZED_SAFE_ACTION_CONTEXT.sub(" ", normalized)
    return bool(
        action_text
        and (
            NORMALIZED_PRIVATE_EXTERNAL_ACTION.search(action_text)
            or NORMALIZED_EXTERNAL_ACTION_ANYWHERE.search(action_text)
            or NORMALIZED_LIVE_EXTERNAL_STATE.search(action_text)
        )
    )


def candidate_text_has_outcome_guarantee(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = _normalize_outcome_text(value)
    return bool(
        DOSSIER_OUTCOME_GUARANTEE.search(value)
        or NORMALIZED_OUTCOME_GUARANTEE.search(normalized)
    )


def candidate_text_has_analytics_claim(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return any(
        ANALYTICS_LANGUAGE.search(normalized)
        and (
            ANALYTICS_TREND_LANGUAGE.search(normalized)
            or bool(extract_bounded_numbers(normalized))
            or re.search(r"\b\d+\b", normalized)
        )
        for segment in re.split(r"[.!?\n]+", normalize_candidate_label_text(value))
        if (normalized := normalize_candidate_text(segment))
    )


def candidate_text_privacy_errors(value: object) -> tuple[str, ...]:
    """Return shared candidate-facing privacy failures after obfuscation normalization."""

    if not isinstance(value, str):
        return ()
    errors = [
        error
        for error in LINKEDIN_SAFETY.validate_candidate_facing_text(value)
        if error.startswith("client report contains forbidden")
        or error == "client report contains credential-shaped content"
        or error == "client report cannot infer a protected trait from visual evidence"
    ]
    normalized = normalize_candidate_label_text(value)
    if IDENTITY_CUE.search(normalized):
        errors.append("client report contains forbidden candidate identity cue")
    if RAW_COPY_CUE.search(normalized):
        errors.append("client report contains forbidden raw-profile alias")
    if CONFIDENTIAL_IDENTITY_CUE.search(normalized):
        errors.append("client report contains forbidden confidential identity cue")
    return tuple(sorted(set(errors)))


def candidate_text_has_expertise_promotion(value: object) -> bool:
    """Return whether ready copy uses an explicit expertise or mastery marker."""

    return bool(EXPERTISE_PROMOTION_LANGUAGE.search(normalize_candidate_text(value)))


def extract_ready_expertise_terms(value: object) -> tuple[str, ...]:
    """Extract explicitly promoted expertise terms without a finite brand list."""

    searchable = normalize_candidate_label_text(value)
    if not searchable:
        return ()
    prefix_patterns = (
        r"\b(?:especialista|experto|experta)\s+en\s+(.+?)(?=\s+(?:para|orientad[oa]|enfocad[oa]|con\s+impacto)\b|[;,.]|$)",
        r"\b(?:expert|specialist)\s+(?:in|with)\s+(.+?)(?=\s+(?:for|focused|across|to\s+support)\b|[;,.]|$)",
        r"\b(?:proficient|skilled)\s+(?:in|with)\s+(.+?)(?=\s+(?:for|focused|across|to\s+support)\b|[;,.]|$)",
        r"\b(?:expertise|proficiency|mastery)\s+(?:in|of|with)\s+(.+?)(?=\s+(?:for|focused|across|to\s+support)\b|[;,.]|$)",
        r"\bdominio\s+de\s+(.+?)(?=\s+(?:para|orientad[oa]|enfocad[oa]|con\s+impacto)\b|[;,.]|$)",
        r"\badvanced\s+(.+?)\s+practitioner\b",
        r"\b(?:strong|advanced|deep|extensive|proven)\s+(.+?)\s+"
        r"(?:skills?|experience|mastery)\b",
    )
    suffix_patterns = (
        r"(?:^|[;,.]|\band\b|\by\b)\s*([^;,.]{1,64}?)\s+(?:expert|specialist|proficiency)\b",
    )
    matches: list[tuple[int, str]] = []
    for pattern in prefix_patterns + suffix_patterns:
        for match in re.finditer(pattern, searchable, flags=re.I):
            term = normalize_candidate_text(match.group(1))
            if term:
                matches.append((match.start(1), term))
    terms: list[str] = []
    for _, term in sorted(matches):
        if term not in terms:
            terms.append(term)
    return tuple(terms)


def _validate_private_action(value: object, path: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        return
    if (
        PRIVATE_EXTERNAL_ACTION.search(value.strip())
        or candidate_text_has_external_action(value)
    ):
        errors.append(f"{path} must remain a private review action")


def _walk_strings(value: object, path: str = "") -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            safe_key = key if key in KNOWN_DOSSIER_FIELDS else "unsupported"
            child = f"{path}.{safe_key}" if path else str(safe_key)
            rows.extend(_walk_strings(nested, child))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk_strings(nested, f"{path}[{index}]"))
    elif isinstance(value, str):
        rows.append((path, value))
    return rows


def _contains_unsupported_script(value: str) -> bool:
    normalized = unicodedata.normalize("NFKC", value)
    return any(
        character.isalpha() and "LATIN" not in unicodedata.name(character, "")
        for character in normalized
    )


def _validate_supported_script_prose(value: Mapping[str, object]) -> list[str]:
    return sorted(
        {
            f"{path} contains unsupported_script prose"
            for path, text in _walk_strings(value)
            if _contains_unsupported_script(text)
        }
    )


def _scan_privacy(value: object, path: str = "") -> list[str]:
    if isinstance(value, Mapping):
        errors: list[str] = []
        for key, nested in value.items():
            safe_key = key if key in KNOWN_DOSSIER_FIELDS else "unsupported"
            child = f"{path}.{safe_key}" if path else str(safe_key)
            errors.extend(_scan_privacy(nested, child))
        return errors
    if isinstance(value, list):
        return [error for index, nested in enumerate(value) for error in _scan_privacy(nested, f"{path}[{index}]")]
    if isinstance(value, str):
        if (
            re.fullmatch(r"market_context\.public_sources\[\d+\]\.url", path)
            and not LINKEDIN_SAFETY.validate_secondary_source_url(value)
        ):
            return []
        return [f"{path} {error}" for error in _privacy_errors(value)]
    return []


def _validate_evidence(
    value: object,
    errors: list[str],
) -> tuple[set[str], dict[str, str], dict[str, Mapping[str, object]]]:
    known: set[str] = set()
    states: dict[str, str] = {}
    records: dict[str, Mapping[str, object]] = {}
    if not isinstance(value, list) or not value:
        errors.append("evidence must contain at least one item")
        return known, states, records
    fields = frozenset({"id", "state", "section", "source_kind", "paraphrase", "capture_ref"})
    for index, item in enumerate(value):
        path = f"evidence[{index}]"
        row = _closed(item, path, fields, errors)
        if row is None:
            continue
        identifier = row.get("id")
        if not isinstance(identifier, str) or not identifier.startswith("E-") or ID_PATTERN.fullmatch(identifier) is None:
            errors.append(f"{path}.id has invalid evidence identifier")
        elif identifier in known:
            errors.append("evidence contains duplicate identifier")
        else:
            known.add(identifier)
            records[identifier] = row
        state = row.get("state")
        if not _enum(state, EVIDENCE_STATES):
            errors.append(f"{path}.state has invalid evidence state")
        elif isinstance(identifier, str):
            states[identifier] = state
        if not _enum(row.get("section"), EVIDENCE_SECTIONS):
            errors.append(f"{path}.section has invalid section")
        if not _enum(row.get("source_kind"), EVIDENCE_SOURCE_KINDS):
            errors.append(f"{path}.source_kind has invalid source kind")
        capture_ref = row.get("capture_ref")
        if capture_ref is not None and (
            not isinstance(capture_ref, str)
            or CAPTURE_REF_PATTERN.fullmatch(capture_ref) is None
        ):
            errors.append(f"{path}.capture_ref has invalid capture reference")
        if row.get("source_kind") == "authorized_visible" and capture_ref is None:
            errors.append(f"{path}.capture_ref is required for authorized visible evidence")
        if row.get("source_kind") != "authorized_visible" and capture_ref is not None:
            errors.append(f"{path}.capture_ref is reserved for authorized visible evidence")
        if row.get("source_kind") == "consented_aggregate" and (
            row.get("section") != "analytics" or row.get("state") != "verified"
        ):
            errors.append(f"{path} consented aggregate evidence must be verified analytics")
        if row.get("source_kind") == "dated_vacancy_research" and (
            row.get("section") != "market" or row.get("state") != "verified"
        ):
            errors.append(f"{path} dated vacancy evidence must be verified market research")
        if row.get("section") == "analytics" and row.get("source_kind") != "consented_aggregate":
            errors.append(f"{path} analytics evidence requires consented aggregate provenance")
        if row.get("section") == "market" and row.get("source_kind") != "dated_vacancy_research":
            errors.append(f"{path} market evidence requires dated vacancy provenance")
        _text(row.get("paraphrase"), f"{path}.paraphrase", errors)
    return known, states, records


def _validate_claims(value: object, evidence_ids: set[str], evidence_states: Mapping[str, str], errors: list[str]) -> tuple[set[str], dict[str, str], dict[str, str]]:
    known: set[str] = set()
    public_use: dict[str, str] = {}
    claim_states: dict[str, str] = {}
    if not isinstance(value, list) or not value:
        errors.append("claims must contain at least one item")
        return known, public_use, claim_states
    fields = frozenset({"id", "state", "paraphrase", "evidence_ids", "public_use"})
    for index, item in enumerate(value):
        path = f"claims[{index}]"
        row = _closed(item, path, fields, errors)
        if row is None:
            continue
        identifier = row.get("id")
        if not isinstance(identifier, str) or not identifier.startswith("C-") or ID_PATTERN.fullmatch(identifier) is None:
            errors.append(f"{path}.id has invalid claim identifier")
        elif identifier in known:
            errors.append("claims contains duplicate identifier")
        else:
            known.add(identifier)
        state = row.get("state")
        if not _enum(state, EVIDENCE_STATES):
            errors.append(f"{path}.state has invalid claim state")
        _text(row.get("paraphrase"), f"{path}.paraphrase", errors)
        references = _references(row.get("evidence_ids"), evidence_ids, f"{path}.evidence_ids", "E-", errors, minimum=1)
        use = row.get("public_use")
        if not _enum(use, {"allowed", "confirmation_required", "blocked"}):
            errors.append(f"{path}.public_use has invalid public-use state")
        elif isinstance(identifier, str):
            public_use[identifier] = use
        if isinstance(identifier, str) and isinstance(state, str) and state in EVIDENCE_STATES:
            claim_states[identifier] = state
        if _state_exceeds_references(state, references, evidence_states):
            errors.append(f"{path}.state exceeds referenced evidence state")
        if _enum(state, {"unknown", "inferred"}) and use == "allowed":
            errors.append(f"{path} inferred or unknown claim cannot be allowed")
    return known, public_use, claim_states


def _validate_focus(
    value: object,
    locale: object,
    claim_ids: set[str],
    errors: list[str],
) -> None:
    row = _closed(
        value,
        "focus",
        frozenset({"statement", "state", "claim_ids"}),
        errors,
    )
    if row is None:
        return
    statement = row.get("statement")
    _text(statement, "focus.statement", errors)
    if row.get("state") != "target_under_review":
        errors.append("focus.state must be target_under_review")
    prefixes = {
        "es": "Objetivo bajo revisión:",
        "en": "Target under review:",
    }
    prefix = prefixes.get(locale) if isinstance(locale, str) else None
    if not isinstance(statement, str) or prefix is None or not statement.startswith(prefix):
        errors.append("focus.statement must use the localized target-under-review prefix")
    _references(row.get("claim_ids"), claim_ids, "focus.claim_ids", "C-", errors)


def _validate_dimensions(
    value: object,
    visual: Mapping[str, object] | None,
    scope: Mapping[str, object] | None,
    evidence_ids: set[str],
    evidence_states: Mapping[str, str],
    errors: list[str],
) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        errors.append("dimensions must be a list")
        return []
    fields = frozenset({"dimension", "state", "score", "reason", "evidence_state", "evidence_ids", "capture_ref"})
    rows: list[Mapping[str, object]] = []
    seen: list[str] = []
    for index, item in enumerate(value):
        path = f"dimensions[{index}]"
        row = _closed(item, path, fields, errors)
        if row is None:
            continue
        dimension = row.get("dimension")
        if not _enum(dimension, set(DOMAIN_WEIGHTS)):
            errors.append(f"{path}.dimension has invalid dimension")
        elif isinstance(dimension, str):
            seen.append(dimension)
        state = row.get("state")
        if not _enum(state, {"evaluated", "not_evaluated"}):
            errors.append(f"{path}.state has invalid state")
        score = row.get("score")
        if state == "evaluated" and (type(score) is not int or not 0 <= score <= 100):
            errors.append(f"{path}.score must be an integer from 0 through 100")
        if state == "not_evaluated" and score is not None:
            errors.append(f"{path}.score must be null when not evaluated")
        references = _references(
            row.get("evidence_ids"),
            evidence_ids,
            f"{path}.evidence_ids",
            "E-",
            errors,
            minimum=1 if state == "evaluated" else 0,
        )
        _validate_consumer_state(
            row.get("evidence_state"),
            references,
            evidence_states,
            f"{path}.evidence_state",
            errors,
        )
        capture_ref = row.get("capture_ref")
        if capture_ref is not None and (
            not isinstance(capture_ref, str)
            or CAPTURE_REF_PATTERN.fullmatch(capture_ref) is None
        ):
            errors.append(f"{path}.capture_ref has invalid capture reference")
        if dimension != "visual" and capture_ref is not None:
            errors.append(f"{path}.capture_ref is reserved for the visual dimension")
        _text(row.get("reason"), f"{path}.reason", errors)
        rows.append(row)
    if [row.get("dimension") for row in rows] != list(DOMAIN_WEIGHTS):
        errors.append("dimensions must contain the seven canonical dimensions in order")
    if visual is not None and scope is not None:
        visual_row = next((row for row in rows if row.get("dimension") == "visual"), None)
        visual_state = scope.get("visual_state")
        photo = visual.get("photo")
        banner = visual.get("banner")
        if visual_row is not None and visual_state == "authorized_visual_visible":
            if not (
                visual_row.get("state") == "evaluated"
                and isinstance(photo, Mapping)
                and photo.get("state") == "evaluated"
                and isinstance(banner, Mapping)
                and banner.get("state") == "evaluated"
            ):
                errors.append("dimensions.visual requires evaluated photo and banner evidence")
            capture_refs = {
                reference
                for reference in (
                    scope.get("visual_capture_ref"),
                    visual_row.get("capture_ref"),
                    photo.get("capture_ref") if isinstance(photo, Mapping) else None,
                    banner.get("capture_ref") if isinstance(banner, Mapping) else None,
                )
                if isinstance(reference, str)
            }
            if len(capture_refs) != 1 or None in capture_refs:
                errors.append("visual_review components must share the authorized visual capture")
            if isinstance(photo, Mapping) and isinstance(banner, Mapping):
                photo_score = photo.get("score")
                banner_score = banner.get("score")
                if type(photo_score) is int and type(banner_score) is int:
                    aggregate = int(
                        (
                            Decimal(photo_score) * Decimal("0.6")
                            + Decimal(banner_score) * Decimal("0.4")
                        ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                    )
                    if visual_row.get("score") != aggregate:
                        errors.append("dimensions[0].score does not match visual component scores")
                component_references = {
                    reference
                    for component in (photo, banner)
                    for reference in component.get("evidence_ids", [])
                    if isinstance(reference, str)
                }
                visual_references = {
                    reference
                    for reference in visual_row.get("evidence_ids", [])
                    if isinstance(reference, str)
                }
                if visual_references != component_references:
                    errors.append("dimensions[0].evidence_ids must match visual component evidence")
        elif visual_row is not None and _enum(visual_state, {"unavailable", "structural_only", "partial_visual"}):
            if visual_row.get("state") != "not_evaluated" or visual_row.get("score") is not None:
                errors.append("dimensions[0] partial or unavailable visual evidence must not be scored")
    return rows


def _validate_visual(
    value: object,
    scope: Mapping[str, object] | None,
    evidence_ids: set[str],
    evidence_states: Mapping[str, str],
    evidence_records: Mapping[str, Mapping[str, object]],
    errors: list[str],
) -> Mapping[str, object] | None:
    row = _closed(value, "visual_review", frozenset({"photo", "banner"}), errors)
    if row is None:
        return None
    fields = frozenset({"state", "finding", "private_action", "evidence_state", "evidence_ids", "capture_ref", "score"})
    visual_state = scope.get("visual_state") if scope is not None else None
    for name in ("photo", "banner"):
        item = _closed(row.get(name), f"visual_review.{name}", fields, errors)
        if item is None:
            continue
        state = item.get("state")
        if not _enum(state, {"evaluated", "not_evaluated"}):
            errors.append(f"visual_review.{name}.state has invalid state")
        _text(item.get("finding"), f"visual_review.{name}.finding", errors)
        _text(item.get("private_action"), f"visual_review.{name}.private_action", errors, nullable=True)
        _validate_private_action(
            item.get("private_action"), f"visual_review.{name}.private_action", errors
        )
        references = _references(item.get("evidence_ids"), evidence_ids, f"visual_review.{name}.evidence_ids", "E-", errors)
        _validate_consumer_state(
            item.get("evidence_state"),
            references,
            evidence_states,
            f"visual_review.{name}.evidence_state",
            errors,
        )
        capture_ref = item.get("capture_ref")
        if capture_ref is not None and (
            not isinstance(capture_ref, str)
            or CAPTURE_REF_PATTERN.fullmatch(capture_ref) is None
        ):
            errors.append(f"visual_review.{name}.capture_ref has invalid capture reference")
        if state == "evaluated" and not references:
            errors.append(f"visual_review.{name} evaluated state requires evidence")
        if state == "not_evaluated" and references:
            errors.append(f"visual_review.{name} not_evaluated state requires no evidence")
        score = item.get("score")
        if visual_state == "authorized_visual_visible":
            if type(score) is not int or not 0 <= score <= 100:
                errors.append(f"visual_review.{name}.score must be an integer from 0 through 100")
            if any(
                evidence_records.get(reference, {}).get("state") != "verified"
                or evidence_records.get(reference, {}).get("source_kind") != "authorized_visible"
                or evidence_records.get(reference, {}).get("section") != name
                or evidence_records.get(reference, {}).get("capture_ref") != capture_ref
                for reference in references
            ):
                errors.append(f"visual_review.{name} requires verified authorized-visible evidence")
        elif score is not None:
            errors.append(f"visual_review.{name}.score must be null without full authorized visual evidence")
    return row


def _validate_coverage(value: object, dimensions: Sequence[Mapping[str, object]], errors: list[str]) -> None:
    row = _closed(value, "coverage", frozenset({"evaluated_count", "scored_weight", "not_scored_weight", "overall_score", "confidence"}), errors)
    if row is None:
        return
    expected_score, expected_weight, expected_not_weight, expected_confidence = calculate_dossier_score(dimensions)
    for field, expected in (("evaluated_count", sum(item.get("state") == "evaluated" for item in dimensions)), ("scored_weight", expected_weight), ("not_scored_weight", expected_not_weight), ("overall_score", expected_score), ("confidence", expected_confidence)):
        if row.get(field) != expected:
            errors.append(f"coverage.{field} does not match evaluated dimensions")


def _validate_priorities(
    value: object,
    evidence_ids: set[str],
    evidence_states: Mapping[str, str],
    errors: list[str],
) -> None:
    if not isinstance(value, list) or len(value) != 3:
        errors.append("priorities must contain exactly three items")
        return
    fields = frozenset({"rank", "title", "problem", "why_now", "action", "timebox_minutes", "done_when", "evidence_state", "evidence_ids", "dimensions"})
    ranks: list[object] = []
    normalized_fields: dict[str, list[str]] = {
        field: [] for field in ("title", "action", "done_when")
    }
    for index, item in enumerate(value):
        path = f"priorities[{index}]"
        row = _closed(item, path, fields, errors)
        if row is None:
            continue
        ranks.append(row.get("rank"))
        for field in ("title", "problem", "why_now", "action", "done_when"):
            _text(row.get(field), f"{path}.{field}", errors)
        for field in ("title", "problem", "why_now", "action", "done_when"):
            _validate_employment_continuity(row.get(field), f"{path}.{field}", errors)
        _validate_private_action(row.get("action"), f"{path}.action", errors)
        _validate_private_action(row.get("done_when"), f"{path}.done_when", errors)
        for field in normalized_fields:
            normalized_fields[field].append(_normalize_decision_text(row.get(field)))
        timebox = row.get("timebox_minutes")
        if type(timebox) is not int or not 5 <= timebox <= 120:
            errors.append(f"{path}.timebox_minutes must be an integer from 5 through 120")
        references = _references(row.get("evidence_ids"), evidence_ids, f"{path}.evidence_ids", "E-", errors, minimum=1)
        _validate_consumer_state(
            row.get("evidence_state"),
            references,
            evidence_states,
            f"{path}.evidence_state",
            errors,
        )
        dimensions = _string_list(row.get("dimensions"), f"{path}.dimensions", errors, minimum=1)
        if any(not _enum(dimension, set(DOMAIN_WEIGHTS)) for dimension in dimensions):
            errors.append(f"{path}.dimensions has invalid dimension")
    if ranks != [1, 2, 3]:
        errors.append("priorities must use ordered ranks 1, 2, 3")
    if any(
        len(values) != len(set(values))
        for values in normalized_fields.values()
        if all(values)
    ):
        errors.append("priorities must not duplicate normalized coaching decisions")


def _validate_copies(
    value: object,
    claim_ids: set[str],
    public_use: Mapping[str, str],
    evidence_ids: set[str],
    evidence_states: Mapping[str, str],
    question_links: Mapping[int, str],
    errors: list[str],
) -> None:
    if not isinstance(value, list) or len(value) != 3:
        errors.append("copy_blocks must contain exactly three items")
        return
    fields = frozenset({"category", "state", "copy", "why_it_works", "claim_ids", "evidence_ids", "claim_boundary", "evidence_state", "question_rank"})
    categories: list[object] = []
    requires_question = False
    for index, item in enumerate(value):
        path = f"copy_blocks[{index}]"
        row = _closed(item, path, fields, errors)
        if row is None:
            continue
        categories.append(row.get("category"))
        state = row.get("state")
        if not _enum(state, {"ready", "requires_confirmation", "omit"}):
            errors.append(f"{path}.state has invalid state")
        copy = row.get("copy")
        if state == "omit":
            if copy is not None:
                errors.append(f"{path} omitted copy must be null")
        else:
            _text(copy, f"{path}.copy", errors, limit=300)
        _text(row.get("why_it_works"), f"{path}.why_it_works", errors)
        claims = _references(row.get("claim_ids"), claim_ids, f"{path}.claim_ids", "C-", errors, minimum=1)
        evidence_references = _references(row.get("evidence_ids"), evidence_ids, f"{path}.evidence_ids", "E-", errors, minimum=1)
        _text(row.get("claim_boundary"), f"{path}.claim_boundary", errors)
        _validate_consumer_state(
            row.get("evidence_state"),
            evidence_references,
            evidence_states,
            f"{path}.evidence_state",
            errors,
        )
        rank = row.get("question_rank")
        if state == "ready":
            if any(public_use.get(claim) != "allowed" for claim in claims):
                errors.append(f"{path} ready copy requires allowed claims")
            if rank is not None:
                errors.append(f"{path} ready copy cannot require a question")
        elif state == "requires_confirmation":
            requires_question = True
            if not any(public_use.get(claim) == "confirmation_required" for claim in claims):
                errors.append(f"{path} confirmation copy requires a confirmation claim")
            if type(rank) is not int or question_links.get(rank) != row.get("category"):
                errors.append("confirmation copy requires its decision-changing question")
        elif state == "omit" and rank is not None:
            errors.append(f"{path} omitted copy cannot require a question")
    if categories != list(COPY_CATEGORIES):
        errors.append("copy_blocks must contain headline, about_opening, experience_bullet in order")
    if requires_question and not question_links:
        errors.append("confirmation copy requires its decision-changing question")


def _validate_requested_technology_terms(
    value: Mapping[str, object],
    claim_ids: set[str],
    public_use: Mapping[str, str],
    errors: list[str],
) -> None:
    raw_terms = value.get("requested_technology_terms")
    if not isinstance(raw_terms, list) or len(raw_terms) > 20:
        errors.append("requested_technology_terms must contain zero through twenty items")
        raw_terms = []

    claims_by_id = {
        row.get("id"): row
        for row in value.get("claims", [])
        if isinstance(row, Mapping) and isinstance(row.get("id"), str)
    } if isinstance(value.get("claims"), list) else {}
    evidence_by_id = {
        row.get("id"): row
        for row in value.get("evidence", [])
        if isinstance(row, Mapping) and isinstance(row.get("id"), str)
    } if isinstance(value.get("evidence"), list) else {}
    term_claims: dict[str, set[str]] = {}
    normalized_terms: list[str] = []
    fields = frozenset({"term", "claim_ids"})
    for index, item in enumerate(raw_terms):
        path = f"requested_technology_terms[{index}]"
        row = _closed(item, path, fields, errors)
        if row is None:
            continue
        term = row.get("term")
        normalized = _normalize_decision_text(term)
        if not isinstance(term, str) or not normalized or len(term) > 80 or len(normalized.split()) > 6:
            errors.append("requested_technology_terms must contain bounded requested terms")
            continue
        references = _references(
            row.get("claim_ids"), claim_ids, f"{path}.claim_ids", "C-", errors, minimum=1
        )
        if not references:
            errors.append(f"{path}.claim_ids must not be empty")
        if any(reference not in claim_ids for reference in references):
            errors.append(f"{path}.claim_ids references unknown identifier")
        normalized_terms.append(normalized)
        term_claims[normalized] = set(references)
        linked_claims = [claims_by_id.get(reference) for reference in references]
        if not any(
            isinstance(claim, Mapping)
            and normalized in _normalize_decision_text(claim.get("paraphrase"))
            for claim in linked_claims
        ):
            errors.append(f"{path}.term must appear in a linked claim paraphrase")
        linked_evidence = {
            evidence_id
            for claim in linked_claims
            if isinstance(claim, Mapping) and isinstance(claim.get("evidence_ids"), list)
            for evidence_id in claim["evidence_ids"]
            if isinstance(evidence_id, str)
        }
        if not any(
            normalized in _normalize_decision_text(evidence_by_id[evidence_id].get("paraphrase"))
            for evidence_id in linked_evidence
            if evidence_id in evidence_by_id
        ):
            errors.append(f"{path}.term must appear in linked evidence paraphrase")
    if len(set(normalized_terms)) != len(normalized_terms):
        errors.append("requested_technology_terms must not contain normalized duplicates")

    ready_rows: list[tuple[str, Mapping[str, object]]] = []
    copies = value.get("copy_blocks")
    if isinstance(copies, list):
        ready_rows.extend(
            (f"copy_blocks[{index}].copy", row)
            for index, row in enumerate(copies)
            if isinstance(row, Mapping) and row.get("state") == "ready"
        )
    bridge = value.get("screen_bridge")
    if isinstance(bridge, Mapping) and bridge.get("state") == "ready":
        ready_rows.append(("screen_bridge.copy", bridge))
    for path, row in ready_rows:
        copy_text = _normalize_decision_text(row.get("copy"))
        row_claims = {
            claim for claim in row.get("claim_ids", []) if isinstance(claim, str)
        } if isinstance(row.get("claim_ids"), list) else set()
        for normalized in set(normalized_terms):
            if not re.search(rf"(?<!\w){re.escape(normalized)}(?!\w)", copy_text):
                continue
            declared_claims = term_claims.get(normalized, set())
            supported = bool(declared_claims & row_claims) and all(
                public_use.get(claim) == "allowed" for claim in declared_claims
            )
            if not supported:
                errors.append(f"{path} contains unsupported requested technology")
        expertise_terms = extract_ready_expertise_terms(row.get("copy"))
        for expertise_term in expertise_terms:
            declared_claims = term_claims.get(expertise_term, set())
            supported = bool(declared_claims & row_claims) and all(
                public_use.get(claim) == "allowed" for claim in declared_claims
            )
            if not supported:
                errors.append(
                    f"{path} expertise term requires a bound allowed claim"
                )
                errors.append(f"{path} contains unsupported requested technology")
        if candidate_text_has_expertise_promotion(row.get("copy")) and not expertise_terms:
            errors.append(f"{path} expertise term requires a bound allowed claim")
            errors.append(f"{path} contains unsupported requested technology")


def _validate_questions(value: object, evidence_ids: set[str], errors: list[str]) -> dict[int, str]:
    if not isinstance(value, list) or len(value) > 3:
        errors.append("questions must contain zero through three items")
        return {}
    fields = frozenset({"rank", "question", "changes", "linked_copy_category", "evidence_ids"})
    ranks: list[int] = []
    links: dict[int, str] = {}
    normalized_fields: dict[str, list[str]] = {"question": [], "changes": []}
    for index, item in enumerate(value):
        path = f"questions[{index}]"
        row = _closed(item, path, fields, errors)
        if row is None:
            continue
        rank = row.get("rank")
        if type(rank) is not int or rank < 1 or rank > 3:
            errors.append(f"{path}.rank has invalid rank")
        else:
            ranks.append(rank)
        _text(row.get("question"), f"{path}.question", errors)
        _text(row.get("changes"), f"{path}.changes", errors)
        for field in normalized_fields:
            normalized_fields[field].append(_normalize_decision_text(row.get(field)))
        linked = row.get("linked_copy_category")
        if not _enum(linked, set(COPY_CATEGORIES + ("screen_bridge",))):
            errors.append(f"{path}.linked_copy_category has invalid decision")
        elif type(rank) is int:
            links[rank] = linked
        _references(row.get("evidence_ids"), evidence_ids, f"{path}.evidence_ids", "E-", errors, minimum=1)
    if ranks != list(range(1, len(ranks) + 1)):
        errors.append("questions must use ordered unique ranks")
    if any(
        len(values) != len(set(values))
        for values in normalized_fields.values()
        if all(values)
    ):
        errors.append("questions must not duplicate normalized coaching decisions")
    return links


def _validate_simple_sections(
    value: Mapping[str, object],
    evidence_ids: set[str],
    evidence_states: Mapping[str, str],
    claim_ids: set[str],
    claim_states: Mapping[str, str],
    public_use: Mapping[str, str],
    question_links: Mapping[int, str],
    errors: list[str],
) -> None:
    verdict = _closed(value.get("verdict"), "verdict", frozenset({"statement", "rationale", "start_here_action", "evidence_state", "evidence_ids"}), errors)
    if verdict is not None:
        for field in ("statement", "rationale", "start_here_action"):
            _text(verdict.get(field), f"verdict.{field}", errors)
        statement = verdict.get("statement")
        if isinstance(statement, str):
            stripped_statement = statement.strip()
            sentence_scan = re.sub(
                r"\b(?:p\.\s*ej\.|e\.\s*g\.|i\.\s*e\.)",
                lambda match: " " * len(match.group(0)),
                stripped_statement,
                flags=re.I,
            )
            sentence_scan = re.sub(
                r"(?<=\d)\.(?=\d)", " ", sentence_scan
            )
            sentence_boundaries = list(re.finditer(r"[.!?]+", sentence_scan))
            if len(sentence_boundaries) > 1 or (
                sentence_boundaries
                and sentence_boundaries[0].end() != len(stripped_statement)
            ):
                errors.append("verdict.statement must contain exactly one sentence")
        _validate_private_action(
            verdict.get("start_here_action"), "verdict.start_here_action", errors
        )
        references = _references(
            verdict.get("evidence_ids"),
            evidence_ids,
            "verdict.evidence_ids",
            "E-",
            errors,
            minimum=1,
        )
        _validate_consumer_state(
            verdict.get("evidence_state"),
            references,
            evidence_states,
            "verdict.evidence_state",
            errors,
        )
    scan = _closed(value.get("recruiter_scan"), "recruiter_scan", frozenset({"understood_signal", "ambiguity", "positioning_bridge"}), errors)
    if scan is not None:
        guidance_fields = frozenset({"statement", "evidence_state", "evidence_ids"})
        for field in ("understood_signal", "ambiguity", "positioning_bridge"):
            path = f"recruiter_scan.{field}"
            guidance = _closed(scan.get(field), path, guidance_fields, errors)
            if guidance is None:
                continue
            _text(guidance.get("statement"), f"{path}.statement", errors)
            references = _references(
                guidance.get("evidence_ids"),
                evidence_ids,
                f"{path}.evidence_ids",
                "E-",
                errors,
                minimum=1,
            )
            _validate_consumer_state(
                guidance.get("evidence_state"),
                references,
                evidence_states,
                f"{path}.evidence_state",
                errors,
            )
    holds = value.get("do_not_change")
    if not isinstance(holds, list) or len(holds) > 3:
        errors.append("do_not_change must contain zero through three items")
    elif isinstance(holds, list):
        fields = frozenset({"claim_ids", "evidence_ids", "reason", "evidence_state"})
        for index, item in enumerate(holds):
            row = _closed(item, f"do_not_change[{index}]", fields, errors)
            if row is not None:
                claim_references = _references(row.get("claim_ids"), claim_ids, f"do_not_change[{index}].claim_ids", "C-", errors, minimum=1)
                evidence_references = _references(row.get("evidence_ids"), evidence_ids, f"do_not_change[{index}].evidence_ids", "E-", errors, minimum=1)
                _text(row.get("reason"), f"do_not_change[{index}].reason", errors)
                combined_states = dict(evidence_states)
                combined_states.update(claim_states)
                _validate_consumer_state(
                    row.get("evidence_state"),
                    evidence_references + claim_references,
                    combined_states,
                    f"do_not_change[{index}].evidence_state",
                    errors,
                )
    bridge = _closed(value.get("screen_bridge"), "screen_bridge", frozenset({"state", "copy", "why_it_works", "claim_ids", "evidence_ids", "claim_boundary", "evidence_state", "question_rank"}), errors)
    if bridge is not None:
        state = bridge.get("state")
        if not _enum(state, {"ready", "requires_confirmation", "omit"}):
            errors.append("screen_bridge.state has invalid state")
        _text(bridge.get("copy"), "screen_bridge.copy", errors, nullable=state == "omit")
        _text(bridge.get("why_it_works"), "screen_bridge.why_it_works", errors)
        references = _references(bridge.get("claim_ids"), claim_ids, "screen_bridge.claim_ids", "C-", errors, minimum=1)
        evidence_references = _references(bridge.get("evidence_ids"), evidence_ids, "screen_bridge.evidence_ids", "E-", errors, minimum=1)
        _text(bridge.get("claim_boundary"), "screen_bridge.claim_boundary", errors)
        _validate_consumer_state(
            bridge.get("evidence_state"),
            evidence_references,
            evidence_states,
            "screen_bridge.evidence_state",
            errors,
        )
        rank = bridge.get("question_rank")
        if state == "ready":
            if any(public_use.get(reference) != "allowed" for reference in references):
                errors.append("screen_bridge ready copy requires allowed claims")
            if rank is not None:
                errors.append("screen_bridge ready copy cannot require a question")
        elif state == "requires_confirmation":
            if not any(public_use.get(reference) == "confirmation_required" for reference in references):
                errors.append("screen_bridge confirmation requires a confirmation claim")
            if type(rank) is not int or question_links.get(rank) != "screen_bridge":
                errors.append("screen_bridge confirmation requires its decision-changing question")
        elif state == "omit":
            if bridge.get("copy") is not None:
                errors.append("screen_bridge omitted copy must be null")
            if rank is not None:
                errors.append("screen_bridge omitted copy cannot require a question")


def _validate_plan(value: object, evidence_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, list) or not 1 <= len(value) <= 7:
        errors.append("seven_day_plan must contain one through seven items")
        return
    fields = frozenset({"day", "category", "action", "done_when", "evidence_ids"})
    days: list[int] = []
    for index, item in enumerate(value):
        path = f"seven_day_plan[{index}]"
        row = _closed(item, path, fields, errors)
        if row is None:
            continue
        day = row.get("day")
        if type(day) is not int or not 1 <= day <= 7:
            errors.append(f"{path}.day has invalid day")
        else:
            days.append(day)
        if not _enum(row.get("category"), PRIVATE_PLAN_CATEGORIES):
            errors.append(f"{path}.category has invalid private category")
        _text(row.get("action"), f"{path}.action", errors)
        _text(row.get("done_when"), f"{path}.done_when", errors)
        _validate_employment_continuity(row.get("action"), f"{path}.action", errors)
        _validate_employment_continuity(row.get("done_when"), f"{path}.done_when", errors)
        _validate_private_action(row.get("action"), f"{path}.action", errors)
        _validate_private_action(row.get("done_when"), f"{path}.done_when", errors)
        _references(row.get("evidence_ids"), evidence_ids, f"{path}.evidence_ids", "E-", errors, minimum=1)
    if days != list(range(1, len(days) + 1)):
        errors.append("seven_day_plan must use ordered unique days")


def _validate_fixed(value: Mapping[str, object], errors: list[str]) -> Mapping[str, object] | None:
    scope = _closed(value.get("evidence_scope"), "evidence_scope", frozenset({"inspection_mode", "captured_as_of", "inspected_sections", "unavailable_sections", "confidence", "visual_state", "visual_capture_ref"}), errors)
    if scope is not None:
        if not _enum(scope.get("inspection_mode"), {"live_read_only", "provided_material", "mixed"}):
            errors.append("evidence_scope.inspection_mode has invalid mode")
        _date(scope.get("captured_as_of"), "evidence_scope.captured_as_of", errors)
        inspected = _string_list(scope.get("inspected_sections"), "evidence_scope.inspected_sections", errors, minimum=1)
        unavailable = _string_list(scope.get("unavailable_sections"), "evidence_scope.unavailable_sections", errors)
        if any(not _enum(item, SECTIONS) for item in inspected + unavailable):
            errors.append("evidence_scope contains invalid section")
        if set(inspected) & set(unavailable):
            errors.append("evidence_scope inspected and unavailable sections must be disjoint")
        if not _enum(scope.get("confidence"), {"low", "medium", "high"}):
            errors.append("evidence_scope.confidence has invalid confidence")
        visual_state = scope.get("visual_state")
        capture_ref = scope.get("visual_capture_ref")
        if not _enum(visual_state, VISUAL_STATES):
            errors.append("evidence_scope.visual_state has invalid state")
        if _enum(visual_state, {"partial_visual", "authorized_visual_visible"}):
            if not isinstance(capture_ref, str) or CAPTURE_REF_PATTERN.fullmatch(capture_ref) is None:
                errors.append("evidence_scope.visual_capture_ref requires a local capture reference")
        elif capture_ref is not None:
            errors.append("evidence_scope.visual_capture_ref must be null without visible evidence")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version has invalid value")
    if value.get("dossier_kind") != DOSSIER_KIND:
        errors.append("dossier_kind has invalid value")
    if not _enum(value.get("locale"), {"es", "en"}):
        errors.append("locale has invalid value")
    _date(value.get("evidence_as_of"), "evidence_as_of", errors)
    if value.get("case_scope") != "single_candidate":
        errors.append("case_scope must be single_candidate")
    if value.get("benchmarking") != "disabled":
        errors.append("benchmarking must be disabled")
    if not isinstance(value.get("requested_technology_terms"), list):
        errors.append("requested_technology_terms must be a list")
    categories = _string_list(value.get("methodology_source_categories"), "methodology_source_categories", errors)
    if any(not _enum(category, METHOD_CATEGORIES) for category in categories):
        errors.append("methodology_source_categories has invalid category")
    try:
        LINKEDIN_SAFETY.resolve_methodology_sources(categories)
    except ValueError:
        errors.append("methodology_source_categories cannot be resolved")
    privacy = _closed(value.get("privacy"), "privacy", frozenset({"private_report", "candidate_identity_included", "contact_data_included", "raw_profile_retained", "raw_private_analytics_included", "aggregate_analytics_included"}), errors)
    if privacy is not None:
        expected = {"private_report": True, "candidate_identity_included": False, "contact_data_included": False, "raw_profile_retained": False, "raw_private_analytics_included": False}
        for field, expected_value in expected.items():
            if privacy.get(field) is not expected_value:
                errors.append(f"privacy.{field} has invalid fixed value")
        if type(privacy.get("aggregate_analytics_included")) is not bool:
            errors.append("privacy.aggregate_analytics_included must be boolean")
    authorization = _closed(value.get("authorization"), "authorization", frozenset({"external_actions_authorized", "action_state"}), errors)
    if authorization is not None:
        if authorization.get("external_actions_authorized") is not False:
            errors.append("authorization.external_actions_authorized must be false")
        if authorization.get("action_state") != "not_executed":
            errors.append("authorization.action_state must be not_executed")
    return scope


def _validate_evidence_isolation(
    value: Mapping[str, object],
    evidence_records: Mapping[str, Mapping[str, object]],
) -> list[str]:
    """Keep analytics and market evidence out of profile facts, copy, and score."""
    errors: list[str] = []

    def references(row: Mapping[str, object]) -> list[str]:
        raw = row.get("evidence_ids")
        return [item for item in raw if isinstance(item, str)] if isinstance(raw, list) else []

    def uses_only_profile_evidence(
        row: Mapping[str, object], allowed_sections: set[str] | frozenset[str]
    ) -> bool:
        return all(
            reference not in evidence_records
            or (
                _enum(evidence_records[reference].get("section"), allowed_sections)
                and _enum(evidence_records[reference].get("source_kind"), PROFILE_EVIDENCE_SOURCE_KINDS)
            )
            for reference in references(row)
        )

    claims = value.get("claims")
    if isinstance(claims, list):
        for index, row in enumerate(claims):
            if isinstance(row, Mapping) and not uses_only_profile_evidence(row, SECTIONS):
                errors.append(
                    f"claims[{index}].evidence_ids must use candidate-profile evidence"
                )

    dimensions = value.get("dimensions")
    if isinstance(dimensions, list):
        for index, row in enumerate(dimensions):
            if not isinstance(row, Mapping):
                continue
            dimension = row.get("dimension")
            allowed_sections = (
                {"visual", "photo", "banner"}
                if dimension == "visual"
                else {dimension} if isinstance(dimension, str) else set()
            )
            if not uses_only_profile_evidence(row, allowed_sections):
                errors.append(
                    f"dimensions[{index}].evidence_ids must use profile evidence for the dimension"
                )

    visual = value.get("visual_review")
    if isinstance(visual, Mapping):
        for name in ("photo", "banner"):
            row = visual.get(name)
            if isinstance(row, Mapping) and not uses_only_profile_evidence(row, {name}):
                errors.append(
                    f"visual_review.{name}.evidence_ids must use visual profile evidence"
                )

    copies = value.get("copy_blocks")
    if isinstance(copies, list):
        for index, row in enumerate(copies):
            if isinstance(row, Mapping) and not uses_only_profile_evidence(row, SECTIONS):
                errors.append(
                    f"copy_blocks[{index}].evidence_ids must use candidate-profile evidence"
                )
    bridge = value.get("screen_bridge")
    if isinstance(bridge, Mapping) and not uses_only_profile_evidence(bridge, SECTIONS):
        errors.append("screen_bridge.evidence_ids must use candidate-profile evidence")

    def contains_market_language(item: object) -> bool:
        if isinstance(item, Mapping):
            return any(contains_market_language(nested) for nested in item.values())
        if isinstance(item, list):
            return any(contains_market_language(nested) for nested in item)
        normalized = normalize_candidate_text(item)
        return bool(
            normalized
            and (
                MARKET_LANGUAGE.search(normalized)
                or MARKET_CLAIM_LANGUAGE.search(normalized)
            )
        )

    guidance: list[tuple[str, Mapping[str, object]]] = []
    verdict = value.get("verdict")
    if isinstance(verdict, Mapping):
        guidance.append(("verdict.evidence_ids", verdict))
    for field in ("priorities", "do_not_change", "questions", "seven_day_plan"):
        rows = value.get(field)
        if isinstance(rows, list):
            guidance.extend(
                (f"{field}[{index}].evidence_ids", row)
                for index, row in enumerate(rows)
                if isinstance(row, Mapping)
            )
    recruiter_scan = value.get("recruiter_scan")
    if isinstance(recruiter_scan, Mapping):
        guidance.extend(
            (f"recruiter_scan.{name}.evidence_ids", row)
            for name, row in recruiter_scan.items()
            if isinstance(row, Mapping)
        )

    for path, row in guidance:
        records = [
            evidence_records[reference]
            for reference in references(row)
            if reference in evidence_records
        ]
        if any(
            record.get("section") == "analytics"
            or record.get("source_kind") == "consented_aggregate"
            for record in records
        ):
            errors.append(f"{path} cannot use aggregate analytics evidence")
        if any(
            record.get("section") == "market"
            or record.get("source_kind") == "dated_vacancy_research"
            for record in records
        ) and not contains_market_language(row):
            errors.append(f"{path} dated market evidence requires explicit market guidance")
    return errors


def _validate_market_language(
    value: Mapping[str, object],
    market_evidence: set[str],
) -> list[str]:
    claim_evidence: dict[str, set[str]] = {}
    claims = value.get("claims")
    if isinstance(claims, list):
        for claim in claims:
            if not isinstance(claim, Mapping) or not isinstance(claim.get("id"), str):
                continue
            references = claim.get("evidence_ids")
            if isinstance(references, list):
                claim_evidence[claim["id"]] = {
                    reference for reference in references if isinstance(reference, str)
                }

    errors: list[str] = []
    market = value.get("market_context")
    market_sample = (
        market.get("vacancy_sample_count")
        if isinstance(market, Mapping)
        and type(market.get("vacancy_sample_count")) is int
        else None
    )
    def walk(item: object, path: str, inherited: set[str]) -> None:
        if isinstance(item, Mapping):
            references = set(inherited)
            evidence_references = item.get("evidence_ids")
            if isinstance(evidence_references, list):
                references.update(
                    reference
                    for reference in evidence_references
                    if isinstance(reference, str)
                )
            claim_references = item.get("claim_ids")
            if isinstance(claim_references, list):
                for claim_id in claim_references:
                    if isinstance(claim_id, str):
                        references.update(claim_evidence.get(claim_id, set()))
            identifier = item.get("id")
            if isinstance(identifier, str) and identifier in market_evidence:
                references.add(identifier)
            for key, nested in item.items():
                if path == "" and key == "methodology_source_categories":
                    continue
                safe_key = key if key in KNOWN_DOSSIER_FIELDS else "unsupported"
                child = f"{path}.{safe_key}" if path else str(safe_key)
                walk(nested, child, references)
        elif isinstance(item, list):
            for index, nested in enumerate(item):
                walk(nested, f"{path}[{index}]", inherited)
        elif isinstance(item, str):
            normalized = normalize_candidate_text(item)
            if (
                path == "market_context.reason"
                and isinstance(market, Mapping)
                and market.get("state") == "not_researched"
                and normalized
                in {
                    "no hay investigacion de vacantes fechada",
                    "no dated vacancy research is available",
                }
            ):
                return
            is_legacy_market = MARKET_LANGUAGE.search(normalized) is not None
            is_market_claim = (
                is_legacy_market
                or MARKET_CLAIM_LANGUAGE.search(normalized) is not None
            )
            if not is_market_claim:
                return
            locally_linked = bool(inherited & market_evidence)
            if not locally_linked:
                errors.append(
                    f"{path} market claims require local dated market evidence"
                )
            if is_legacy_market and not locally_linked:
                errors.append(
                    f"{path} market language requires linked dated market evidence"
                )
            volumes = extract_market_volume_values(normalized)
            if locally_linked and any(
                observed_volume != market_sample for observed_volume in volumes
            ):
                errors.append(
                    f"{path} market vacancy volume must equal the dated sample"
                )
            if (
                not path.startswith("market_context")
                and UNRECONCILED_MARKET_STRENGTH.search(normalized)
            ):
                errors.append(
                    f"{path} demand or volume is not reconciled to dated market evidence"
                )

    walk(value, "", set())
    return sorted(set(errors))


def _validate_absent_module_claims(value: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    analytics = value.get("analytics")
    analytics_observed = (
        isinstance(analytics, Mapping)
        and analytics.get("state") == "observed_aggregate"
    )
    market = value.get("market_context")
    market_researched = (
        isinstance(market, Mapping)
        and market.get("state") == "dated_vacancy_evidence"
    )
    for path, text in _walk_strings(value):
        normalized = normalize_candidate_text(text)
        if not analytics_observed and ANALYTICS_MEASURE_LANGUAGE.search(normalized):
            errors.append(
                f"{path} analytics measures require observed aggregate analytics"
            )
        if not market_researched and UNSUPPORTED_DEMAND_LANGUAGE.search(normalized):
            errors.append(
                f"{path} demand language requires linked dated market evidence"
            )
    return sorted(set(errors))


def _validate_structured_module_prose(value: Mapping[str, object]) -> list[str]:
    """Keep quantitative analytics and market strength/volume in their structures."""

    errors: list[str] = []
    market = value.get("market_context")
    market_sample = (
        market.get("vacancy_sample_count")
        if isinstance(market, Mapping) and type(market.get("vacancy_sample_count")) is int
        else None
    )
    strong_demand = re.compile(
        r"\b(?:strong(?:ly)?|high|active(?:ly)?|eager(?:ly)?|widely|abundant|plentiful)\b"
        r"[^.!?\n]{0,48}\b(?:demand|seek|seeking|sought|vacanc(?:y|ies)|openings?|jobs?)\b|"
        r"\b(?:abundante|alta|fuerte|activa)\b[^.!?\n]{0,48}\b(?:demanda|vacantes?|empleos?)\b|"
        r"\b(?:vacancies|openings|jobs)\b[^.!?\n]{0,48}\b(?:abundant|plentiful|numerous)\b|"
        r"\bcompan(?:y|ies)\b[^.!?\n]{0,48}\b(?:eager|compete|competing)\b|"
        r"\bhiring\s+demand\b[^.!?\n]{0,32}\b(?:strong|high|active)\b|"
        r"\bsobran\s+oportunidades\s+laborales\b|"
        r"\bmuy\s+solicitad[oa]s?\b[^.!?\n]{0,32}\b(?:empresas?|empleadores?)\b|"
        r"\bempresas?\s+compiten\s+por\b",
        re.I,
    )
    for path, text in _walk_strings(value):
        normalized = normalize_candidate_text(text)
        if path.startswith("analytics") and ANALYTICS_LANGUAGE.search(normalized):
            errors.append(
                f"{path} cannot contain analytics measures or trends"
            )
        elif ANALYTICS_LANGUAGE.search(normalized):
            errors.append(
                f"{path} analytics language must come from structured aggregates"
            )
        if path.startswith("market_context"):
            continue
        volumes = extract_market_volume_values(normalized)
        volume_mismatch = any(volume != market_sample for volume in volumes)
        if strong_demand.search(normalized) or volume_mismatch:
            errors.append(
                f"{path} demand or volume is not reconciled to dated market evidence"
            )
    return sorted(set(errors))


def validate_dossier(value: object) -> list[str]:
    """Return sorted, path-based errors for a runtime dossier without raw values."""
    errors: list[str] = []
    root = _closed(value, "dossier", TOP_FIELDS, errors)
    if root is None:
        return sorted(set(errors))
    errors.extend(_validate_supported_script_prose(root))
    scope = _validate_fixed(root, errors)
    evidence_ids, evidence_states, evidence_records = _validate_evidence(root.get("evidence"), errors)
    errors.extend(_validate_evidence_isolation(root, evidence_records))
    claim_ids, public_use, claim_states = _validate_claims(root.get("claims"), evidence_ids, evidence_states, errors)
    _validate_focus(root.get("focus"), root.get("locale"), claim_ids, errors)
    visual = _validate_visual(
        root.get("visual_review"),
        scope,
        evidence_ids,
        evidence_states,
        evidence_records,
        errors,
    )
    dimensions = _validate_dimensions(
        root.get("dimensions"),
        visual,
        scope,
        evidence_ids,
        evidence_states,
        errors,
    )
    _validate_coverage(root.get("coverage"), dimensions, errors)
    _validate_priorities(root.get("priorities"), evidence_ids, evidence_states, errors)
    question_links = _validate_questions(root.get("questions"), evidence_ids, errors)
    _validate_copies(
        root.get("copy_blocks"),
        claim_ids,
        public_use,
        evidence_ids,
        evidence_states,
        question_links,
        errors,
    )
    _validate_requested_technology_terms(root, claim_ids, public_use, errors)
    _validate_simple_sections(
        root,
        evidence_ids,
        evidence_states,
        claim_ids,
        claim_states,
        public_use,
        question_links,
        errors,
    )
    _validate_plan(root.get("seven_day_plan"), evidence_ids, errors)
    evidence_as_of = date.max
    if isinstance(root.get("evidence_as_of"), str):
        try:
            evidence_as_of = date.fromisoformat(root["evidence_as_of"])
        except ValueError:
            pass
    errors.extend(validate_analytics(root.get("analytics"), evidence_ids))
    errors.extend(
        validate_market_context(
            root.get("market_context"), evidence_as_of, evidence_ids
        )
    )
    analytics_evidence = {
        identifier
        for identifier, record in evidence_records.items()
        if record.get("section") == "analytics"
        and record.get("source_kind") == "consented_aggregate"
        and record.get("state") == "verified"
    }
    market_evidence = {
        identifier
        for identifier, record in evidence_records.items()
        if record.get("section") == "market"
        and record.get("source_kind") == "dated_vacancy_research"
        and record.get("state") == "verified"
    }
    analytics = root.get("analytics")
    if isinstance(analytics, Mapping) and analytics.get("state") == "observed_aggregate":
        references = analytics.get("evidence_ids")
        if isinstance(references, list) and any(
            reference not in analytics_evidence for reference in references
        ):
            errors.append("analytics.evidence_ids must use consented aggregate evidence")
        observed_as_of = analytics.get("observed_as_of")
        if isinstance(observed_as_of, str):
            try:
                if date.fromisoformat(observed_as_of) > evidence_as_of:
                    errors.append("analytics.observed_as_of cannot be after evidence_as_of")
            except ValueError:
                pass
    market = root.get("market_context")
    if isinstance(market, Mapping) and market.get("state") == "dated_vacancy_evidence":
        references = market.get("evidence_ids")
        if isinstance(references, list) and any(
            reference not in market_evidence for reference in references
        ):
            errors.append("market_context.evidence_ids must use dated market evidence")
        roles = market.get("target_roles")
        if isinstance(roles, list):
            for index, role in enumerate(roles):
                role_references = role.get("evidence_ids") if isinstance(role, Mapping) else None
                if isinstance(role_references, list) and any(
                    reference not in market_evidence for reference in role_references
                ):
                    errors.append(
                        f"market_context.target_roles[{index}].evidence_ids must use dated market evidence"
                    )
    errors.extend(_validate_market_language(root, market_evidence))
    errors.extend(_validate_absent_module_claims(root))
    errors.extend(_validate_structured_module_prose(root))
    if isinstance(root.get("privacy"), Mapping) and isinstance(root.get("analytics"), Mapping):
        expected_aggregate = root["analytics"].get("state") == "observed_aggregate"
        if root["privacy"].get("aggregate_analytics_included") is not expected_aggregate:
            errors.append("privacy.aggregate_analytics_included must match observed aggregate analytics")
    errors.extend(_scan_privacy(value))
    return sorted(set(errors))


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an executive career dossier.")
    parser.add_argument("dossier", type=Path)
    arguments = parser.parse_args(argv)
    try:
        dossier = load_dossier(arguments.dossier)
    except DossierLoadError as error:
        print(str(error), file=sys.stderr)
        return 2
    errors = validate_dossier(dossier)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
