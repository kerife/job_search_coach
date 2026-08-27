#!/usr/bin/env python3
"""Validate the identity-free current-vacancy research contract."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any


class _ArgumentError(ValueError):
    pass


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise _ArgumentError


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("required research validator dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_report = _sibling("validate_linkedin_client_report.py")
_loader = _sibling("private_input_loader.py")
_prose = _sibling("private_prose_safety.py")

SCHEMA_VERSION = "target-vacancy-research-v1"
RESEARCH_KIND = "sre_platform_devops_current_vacancies"
MAX_INPUT_BYTES = 256 * 1024
MAX_DEPTH = 12
VACANCY_ID = re.compile(r"^V-[0-9]{3}$")
EMPLOYER_ID = re.compile(r"^EMP-[0-9]{3}$")
REQUIREMENT_ID = re.compile(r"^V-[0-9]{3}-R-[0-9]{2}$")
SIGNAL = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
ALLOWED_STATES = frozenset({"complete", "limited_market_evidence", "market_evidence_unavailable"})
ROLE_FAMILIES = frozenset({"site_reliability_engineering", "platform_engineering", "devops_engineering"})
ARRANGEMENTS = frozenset({"onsite", "hybrid", "remote", "flexible"})
GEOGRAPHIC_COMPATIBILITY = frozenset({"explicit_mexico", "stated_remote_unknown_eligibility"})
SOURCE_KINDS = frozenset({"official_employer", "employer_operated_ats", "linkedin_jobs_backup"})
GATE_NAMES = frozenset({
    "work_authorization", "country_geography", "work_arrangement", "language",
    "seniority", "experience_floor", "employment_arrangement",
})
IMPORTANCES = frozenset({"must_have", "preferred", "responsibility_only"})
GATE_STATES = frozenset({"pass", "blocked", "unknown"})
FRESHNESS = frozenset({"current", "unknown"})
EVIDENCE_MODES = frozenset({"synthetic", "live"})
TOP_FIELDS = frozenset({
    "schema_version", "research_kind", "evidence_mode", "locale", "as_of_date", "search_scope", "state",
    "search_limit", "employers", "vacancies", "privacy_boundary", "no_external_action",
})
RESTRICTED_OBSERVATION = re.compile(
    r"(?:https?://|www\.[a-z0-9.-]+\.[a-z]{2,}|[\w.+-]+@[\w.-]+\.[a-z]{2,}|"
    r"\+?\d[\d\s().-]{7,}\d|\b(?:session(?:[_-]?(?:id|token|key))?|sid|jsessionid|phpsessid|cookie)\s*[=:])",
    re.I,
)


def _closed(value: object, path: str, fields: frozenset[str], errors: list[str]) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    if set(value) - fields:
        errors.append(f"{path} has unsupported fields")
    if fields - set(value):
        errors.append(f"{path} is missing required fields")
    return value


def _text(value: object, path: str, errors: list[str], *, maximum: int) -> bool:
    if not isinstance(value, str) or not value or len(value) > maximum:
        errors.append(f"{path} must be bounded text")
        return False
    if _prose.contains_unicode_controls(value):
        errors.append(f"{path} contains forbidden control characters")
        return False
    if re.search(r"<\/?(?:script|iframe|object|style)\b", value, re.I):
        errors.append(f"{path} contains forbidden markup")
        return False
    if re.search(r"(?:[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:^|\s)(?:/[A-Za-z]|[A-Za-z]:[\\/]))", value):
        errors.append(f"{path} contains private value")
        return False
    return True


def _observation_text(value: object, path: str, errors: list[str], *, maximum: int) -> None:
    _text(value, path, errors, maximum=maximum)
    if isinstance(value, str) and RESTRICTED_OBSERVATION.search(value):
        errors.append(f"{path} contains restricted observation data")


def _date(value: object, path: str, errors: list[str], *, live: bool = False) -> date | None:
    if not isinstance(value, str):
        errors.append(f"{path} must be an ISO date")
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path} must be an ISO date")
        return None
    if live and parsed > date.today():
        errors.append(f"{path} cannot be in the future for live evidence")
    return parsed


def _reserved_domain(host: str) -> bool:
    return host in {"example.com", "example.net", "example.org", "localhost"} or host.endswith(
        (".example.com", ".example.net", ".example.org", ".test", ".invalid", ".localhost"),
    )


def _canonical_url_path(path: str) -> str | None:
    from urllib.parse import unquote

    decoded = path
    for _ in range(4):
        next_path = unquote(decoded)
        if next_path == decoded:
            return decoded
        decoded = next_path
    return None


def _normalized_source_url(value: object) -> str | None:
    """Return a stable identity for an already policy-validated source URL."""
    if not isinstance(value, str):
        return None
    from urllib.parse import urlsplit

    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").casefold().rstrip(".")
        path = _canonical_url_path(parsed.path)
    except ValueError:
        return None
    if not host or path is None:
        return None
    if len(path) > 1:
        path = path.rstrip("/") or "/"
    return f"https://{host}{path}"


def _path_has_traversal(path: str) -> bool:
    """Reject dot segments after URL decoding, including encoded traversal."""
    return any(segment in {".", ".."} for segment in path.split("/"))


def source_url_policy_error(
    value: object, *, source_kind: str | None = None, evidence_mode: str,
) -> str | None:
    if not isinstance(value, str):
        return "source URL must use HTTPS"
    try:
        from urllib.parse import urlsplit

        parsed = urlsplit(value)
    except ValueError:
        return "source URL must use HTTPS"
    host = (parsed.hostname or "").casefold().rstrip(".")
    try:
        port = parsed.port
    except ValueError:
        return "source URL must use HTTPS"
    if parsed.scheme.casefold() != "https" or parsed.username or parsed.password or port not in {None, 443}:
        return "source URL must use HTTPS"
    canonical_path = _canonical_url_path(parsed.path)
    if (
        parsed.query
        or parsed.fragment
        or canonical_path is None
        or _path_has_traversal(canonical_path)
        or RESTRICTED_OBSERVATION.search(canonical_path)
    ):
        if canonical_path is not None and _path_has_traversal(canonical_path):
            return "source URL contains path traversal"
        return "source URL contains restricted metadata"
    if evidence_mode == "synthetic" and not _reserved_domain(host):
        return "synthetic source URL must use a reserved domain"
    if evidence_mode == "live" and _reserved_domain(host):
        return "live evidence cannot use a reserved source domain"
    if source_kind == "linkedin_jobs_backup":
        if host not in {"linkedin.com", "www.linkedin.com"} or not parsed.path.startswith("/jobs/"):
            return "LinkedIn backup URL must use the linkedin.com/jobs path"
        return None
    if evidence_mode == "synthetic":
        return None
    errors = _report.validate_secondary_source_url(value)
    if errors:
        return "source URL violates public HTTPS policy"
    if host == "linkedin.com" or host.endswith(".linkedin.com"):
        return "official source URL cannot point to LinkedIn"
    return None


def _url_error(
    value: object, *, source_kind: str | None = None, evidence_mode: str,
) -> str | None:
    return source_url_policy_error(
        value, source_kind=source_kind, evidence_mode=evidence_mode,
    )


def _depth(value: object, level: int = 0) -> bool:
    if level > MAX_DEPTH:
        return False
    if isinstance(value, Mapping):
        return all(_depth(key, level + 1) and _depth(item, level + 1) for key, item in value.items())
    if isinstance(value, list):
        return all(_depth(item, level + 1) for item in value)
    return True


def _validate_search_scope(value: object, errors: list[str]) -> None:
    fields = frozenset({
        "geography_scope", "target_role_families", "maximum_vacancies", "distinct_employers_preferred",
        "official_sources_first", "linkedin_jobs_backup_allowed", "no_eligibility_inference",
    })
    row = _closed(value, "search_scope", fields, errors)
    if row is None:
        return
    if row.get("geography_scope") != "mexico_or_stated_remote":
        errors.append("search_scope.geography_scope has invalid value")
    families = row.get("target_role_families")
    if not isinstance(families, list) or not families or any(item not in ROLE_FAMILIES for item in families):
        errors.append("search_scope.target_role_families has invalid values")
    if row.get("maximum_vacancies") != 5:
        errors.append("search_scope.maximum_vacancies must be five")
    for field in ("distinct_employers_preferred", "official_sources_first", "linkedin_jobs_backup_allowed", "no_eligibility_inference"):
        if row.get(field) is not True:
            errors.append(f"search_scope.{field} must be true")


def _validate_employers(value: object, evidence_mode: str, errors: list[str]) -> set[str]:
    if not isinstance(value, list):
        errors.append("employers must be an array")
        return set()
    ids: set[str] = set()
    fields = frozenset({"employer_id", "display_name", "qualification_type", "qualification_observation", "official_source_title", "official_source_url", "source_date", "access_date"})
    for index, item in enumerate(value):
        path = f"employers[{index}]"
        row = _closed(item, path, fields, errors)
        if row is None:
            continue
        employer_id = row.get("employer_id")
        if not isinstance(employer_id, str) or not EMPLOYER_ID.fullmatch(employer_id) or employer_id in ids:
            errors.append(f"{path}.employer_id is invalid or duplicated")
        else:
            ids.add(employer_id)
        _text(row.get("display_name"), f"{path}.display_name", errors, maximum=160)
        if row.get("qualification_type") not in {"official_headcount", "official_index_membership"}:
            errors.append(f"{path}.qualification_type has invalid value")
        _observation_text(row.get("qualification_observation"), f"{path}.qualification_observation", errors, maximum=500)
        _text(row.get("official_source_title"), f"{path}.official_source_title", errors, maximum=240)
        url_error = _url_error(row.get("official_source_url"), evidence_mode=evidence_mode)
        if url_error:
            errors.append(url_error if url_error == "live evidence cannot use a reserved source domain" else f"{path}.official_source_url is invalid")
        source_date = _date(row.get("source_date"), f"{path}.source_date", errors, live=evidence_mode == "live")
        access_date = _date(row.get("access_date"), f"{path}.access_date", errors, live=evidence_mode == "live")
        if source_date and access_date and source_date > access_date:
            errors.append(f"{path}.source_date cannot be after access_date")
    return ids


def _validate_vacancies(
    value: object, employers: set[str], as_of: date | None, evidence_mode: str, errors: list[str],
) -> None:
    if not isinstance(value, list):
        errors.append("vacancies must be an array")
        return
    vacancy_ids: set[str] = set()
    fingerprints: set[str] = set()
    source_urls: set[str] = set()
    requirement_ids: set[str] = set()
    repeated_employer = False
    seen_employers: set[str] = set()
    for index, item in enumerate(value):
        path = f"vacancies[{index}]"
        fields = frozenset({"vacancy_id", "duplicate_fingerprint", "employer_id", "title", "role_family", "location", "arrangement", "geographic_compatibility", "source_kind", "source_url", "official_referrer_url", "source_state", "access_date", "publication_date", "freshness_status", "eligibility_gates", "requirements"})
        row = _closed(item, path, fields, errors)
        if row is None:
            continue
        vacancy_id = row.get("vacancy_id")
        if not isinstance(vacancy_id, str) or not VACANCY_ID.fullmatch(vacancy_id) or vacancy_id in vacancy_ids:
            errors.append(f"{path}.vacancy_id is invalid or duplicated")
        else:
            vacancy_ids.add(vacancy_id)
        fingerprint = row.get("duplicate_fingerprint")
        if not isinstance(fingerprint, str) or not re.fullmatch(r"[a-z0-9-]{3,120}", fingerprint):
            errors.append(f"{path}.duplicate_fingerprint is invalid")
        elif fingerprint in fingerprints:
            errors.append("duplicate vacancy fingerprint")
        else:
            fingerprints.add(fingerprint)
        employer_id = row.get("employer_id")
        if employer_id not in employers:
            errors.append(f"{path}.employer_id does not resolve")
        elif employer_id in seen_employers:
            repeated_employer = True
        seen_employers.add(employer_id)
        _text(row.get("title"), f"{path}.title", errors, maximum=240)
        if row.get("role_family") not in ROLE_FAMILIES:
            errors.append(f"{path}.role_family has invalid value")
        _text(row.get("location"), f"{path}.location", errors, maximum=160)
        if row.get("arrangement") not in ARRANGEMENTS or row.get("geographic_compatibility") not in GEOGRAPHIC_COMPATIBILITY:
            errors.append(f"{path} has invalid location or arrangement value")
        source_kind = row.get("source_kind")
        if source_kind not in SOURCE_KINDS:
            errors.append(f"{path}.source_kind has invalid value")
        url_error = _url_error(
            row.get("source_url"), source_kind=source_kind if isinstance(source_kind, str) else None,
            evidence_mode=evidence_mode,
        )
        if url_error:
            errors.append(url_error if url_error == "live evidence cannot use a reserved source domain" else f"{path}.source_url is invalid")
        else:
            normalized_url = _normalized_source_url(row.get("source_url"))
            if normalized_url is not None:
                if normalized_url in source_urls:
                    errors.append("duplicate vacancy source URL")
                else:
                    source_urls.add(normalized_url)
        referrer = row.get("official_referrer_url")
        if referrer is not None:
            referrer_error = _url_error(referrer, evidence_mode=evidence_mode)
            if referrer_error:
                errors.append(referrer_error if referrer_error == "live evidence cannot use a reserved source domain" else f"{path}.official_referrer_url is invalid")
        if row.get("source_state") != "active":
            errors.append(f"{path}.source_state must be active")
        access_date = _date(row.get("access_date"), f"{path}.access_date", errors, live=evidence_mode == "live")
        if as_of and access_date and access_date != as_of:
            errors.append(f"{path}.access_date must equal as_of_date")
        publication = row.get("publication_date")
        publication_date = _date(publication, f"{path}.publication_date", errors, live=evidence_mode == "live") if publication is not None else None
        if as_of and publication_date and publication_date > as_of:
            errors.append(f"{path}.publication_date cannot be after as_of_date")
        if row.get("freshness_status") not in FRESHNESS:
            errors.append(f"{path}.freshness_status has invalid value")
        gates = row.get("eligibility_gates")
        if not isinstance(gates, list) or not 1 <= len(gates) <= len(GATE_NAMES):
            errors.append(f"{path}.eligibility_gates has invalid item count")
        else:
            gate_names: set[str] = set()
            for gate_index, gate in enumerate(gates):
                gate_path = f"{path}.eligibility_gates[{gate_index}]"
                gate_row = _closed(gate, gate_path, frozenset({"gate", "state", "observed_condition"}), errors)
                if gate_row is None:
                    continue
                name = gate_row.get("gate")
                if name not in GATE_NAMES or name in gate_names:
                    errors.append(f"{gate_path}.gate is invalid or duplicated")
                gate_names.add(name)
                state = gate_row.get("state")
                if state not in GATE_STATES:
                    errors.append(f"{gate_path}.state has invalid value")
                _observation_text(gate_row.get("observed_condition"), f"{gate_path}.observed_condition", errors, maximum=500)
                if state == "unknown" and re.search(r"\b(?:eligible|authorized|pass|cumple|aprobado)\b", str(gate_row.get("observed_condition", "")), re.I):
                    errors.append("unknown eligibility gate contains an inferred conclusion")
        requirements = row.get("requirements")
        if not isinstance(requirements, list) or not 1 <= len(requirements) <= 30:
            errors.append(f"{path}.requirements has invalid item count")
        else:
            signals: set[str] = set()
            for req_index, requirement in enumerate(requirements):
                req_path = f"{path}.requirements[{req_index}]"
                req_row = _closed(requirement, req_path, frozenset({"requirement_id", "signal", "importance", "source_paraphrase"}), errors)
                if req_row is None:
                    continue
                req_id = req_row.get("requirement_id")
                if not isinstance(req_id, str) or not REQUIREMENT_ID.fullmatch(req_id) or req_id in requirement_ids or not vacancy_id or not req_id.startswith(f"{vacancy_id}-"):
                    errors.append(f"{req_path}.requirement_id is invalid or duplicated")
                else:
                    requirement_ids.add(req_id)
                signal = req_row.get("signal")
                if not isinstance(signal, str) or not SIGNAL.fullmatch(signal) or signal in signals:
                    errors.append(f"{req_path}.signal is invalid or duplicated")
                else:
                    signals.add(signal)
                if req_row.get("importance") not in IMPORTANCES:
                    errors.append(f"{req_path}.importance has invalid value")
                _observation_text(req_row.get("source_paraphrase"), f"{req_path}.source_paraphrase", errors, maximum=500)
    if repeated_employer:
        # The caller checks the search-limit flag after all rows are known.
        errors.append("__repeated_employer__")


def validate_research(value: object) -> list[str]:
    """Return bounded, non-echoing diagnostics without mutating *value*."""
    errors: list[str] = []
    try:
        if not isinstance(value, Mapping):
            return ["research artifact must be an object"]
        if not _depth(value):
            errors.append("research artifact exceeds maximum nesting depth")
        if set(value) - TOP_FIELDS:
            errors.append("research artifact has unsupported fields")
        if TOP_FIELDS - set(value):
            errors.append("research artifact is missing required fields")
        if value.get("schema_version") != SCHEMA_VERSION:
            errors.append("schema_version has invalid value")
        if value.get("research_kind") != RESEARCH_KIND:
            errors.append("research_kind has invalid value")
        if value.get("locale") not in {"es", "en"}:
            errors.append("locale has invalid value")
        evidence_mode = value.get("evidence_mode")
        if evidence_mode not in EVIDENCE_MODES:
            errors.append("evidence_mode has invalid value")
        mode = str(evidence_mode)
        as_of = _date(value.get("as_of_date"), "as_of_date", errors, live=mode == "live")
        _validate_search_scope(value.get("search_scope"), errors)
        state = value.get("state")
        if state not in ALLOWED_STATES:
            errors.append("state has invalid value")
        search_limit = _closed(value.get("search_limit"), "search_limit", frozenset({"bounded_queries_run", "limit_reason", "distinct_employer_search_exhausted", "limitation"}), errors)
        if search_limit is not None:
            if type(search_limit.get("bounded_queries_run")) is not int or not 0 <= search_limit["bounded_queries_run"] <= 100:
                errors.append("search_limit.bounded_queries_run has invalid value")
            if search_limit.get("limit_reason") not in {"target_reached", "search_limit_reached", "source_limit", "none"}:
                errors.append("search_limit.limit_reason has invalid value")
            if type(search_limit.get("distinct_employer_search_exhausted")) is not bool:
                errors.append("search_limit.distinct_employer_search_exhausted must be boolean")
            _observation_text(search_limit.get("limitation"), "search_limit.limitation", errors, maximum=500)
        employers = _validate_employers(value.get("employers"), mode, errors)
        vacancies = value.get("vacancies")
        _validate_vacancies(vacancies, employers, as_of, mode, errors)
        count = len(vacancies) if isinstance(vacancies, list) else -1
        expected = state == "complete" and count == 5 or state == "limited_market_evidence" and 1 <= count <= 4 or state == "market_evidence_unavailable" and count == 0
        if not expected:
            errors.append("state/count coupling is invalid")
        if search_limit is not None and "__repeated_employer__" in errors:
            errors.remove("__repeated_employer__")
            if search_limit.get("distinct_employer_search_exhausted") is not True:
                errors.append("repeated employer requires exhausted search")
        if state == "complete" and search_limit is not None and search_limit.get("limit_reason") != "target_reached":
            errors.append("complete research must use target_reached limit reason")
        if state == "limited_market_evidence" and count < 5 and search_limit is not None and search_limit.get("limitation") == "none":
            errors.append("limited research requires a limitation")
        if state == "market_evidence_unavailable" and count != 0:
            errors.append("unavailable research must contain no vacancies")
        if value.get("privacy_boundary") != "public_vacancy_sources_and_identity_free_candidate_evidence_only":
            errors.append("privacy_boundary has invalid value")
        if value.get("no_external_action") is not True:
            errors.append("no_external_action must be true")
    except (RecursionError, TypeError, ValueError):
        errors.append("research artifact could not be validated")
    return sorted(set(error for error in errors if not error.startswith("__")))


def canonical_research_snapshot(value: Mapping[str, object]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def snapshot_for_market_dossier(value: Mapping[str, object]) -> str:
    return f"snap-market-sha256-{canonical_research_snapshot(value)}"


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, item in pairs:
        if key in output:
            raise ValueError("duplicate JSON key")
        output[key] = item
    return output


def load_research(path: Path) -> dict[str, object]:
    try:
        raw = _loader.read_bounded_bytes(path, MAX_INPUT_BYTES)
    except _loader.PrivateInputError as exc:
        raise ValueError("research artifact exceeds input bound") from exc
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        if not isinstance(value, dict) or not _depth(value):
            raise ValueError("research artifact exceeds maximum nesting depth")
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ValueError("research artifact could not be loaded") from exc
    if not isinstance(value, dict):
        raise ValueError("research artifact must be an object")
    return value


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    try:
        args = parser.parse_args(argv)
    except _ArgumentError:
        print('{"error":{"code":"invalid_arguments"}}', file=sys.stderr)
        return 3
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    try:
        value = load_research(args.path)
    except (OSError, UnicodeError, ValueError):
        print("research artifact could not be loaded", file=sys.stderr)
        return 2
    errors = validate_research(value)
    if errors:
        sys.stderr.write(_prose.format_bounded_diagnostics(errors))
        return 1
    print("valid target vacancy research")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
