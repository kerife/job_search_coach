#!/usr/bin/env python3
"""Validate bounded, identity-free learning-option research artifacts."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
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
        raise RuntimeError("required learning research dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_loader = _sibling("private_input_loader.py")
_prose = _sibling("private_prose_safety.py")

SCHEMA_VERSION = "learning-option-research-v1"
EVIDENCE_MODES = frozenset({"synthetic", "live"})
MAX_INPUT_BYTES = 256 * 1024
MAX_DEPTH = 12
# Research cites the complete canonical market snapshot identifier; it is never
# shown to a client or dereferenced by this validator.
MARKET_SNAPSHOT = re.compile(r"^snap-market-sha256-[0-9a-f]{64}$")
OPTION_ID = re.compile(r"^LO-[0-9]{3}$")
SIGNAL = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
OPTION_TYPES = frozenset({
    "candidate_owned_project", "lab", "course", "certification", "free_resource",
    "do_nothing_now",
})
SOURCE_STATES = frozenset({"active", "stale", "unavailable", "synthetic"})
DURATION_BASES = frozenset({"provider_verified", "provider_duration_unknown", "candidate_estimated"})
REVIEW_STATES = frozenset({"required", "not_applicable"})
TOP_FIELDS = frozenset({
    "schema_version", "evidence_mode", "locale", "as_of_date", "source_market_snapshot",
    "candidate_preferences", "options", "privacy_boundary", "no_external_action",
})
OPTION_FIELDS = frozenset({
    "option_id", "gap_signal", "option_type", "provider", "option", "source_title",
    "source_date", "source_state", "url", "geography", "availability", "role",
    "seniority", "current_cost", "currency", "tax", "duration", "duration_basis",
    "prerequisite", "renewal", "maintenance", "unknowns", "proof_artifact", "action_gate",
})
PREFERENCE_FIELDS = frozenset({"weekly_time_budget", "money_budget", "currency", "purchase_authorized"})
ACTION_GATE_FIELDS = frozenset({
    "external_action_authorized", "exact_authorization_required", "ownership_review",
    "secrets_review", "confidentiality_review", "customer_data_review", "rights_holder_review",
    "publication_authorized",
})


def _closed(value: object, path: str, fields: frozenset[str], errors: list[str]) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    if set(value) - fields:
        errors.append(f"{path} has unsupported fields")
    if fields - set(value):
        errors.append(f"{path} is missing required fields")
    return value


def _depth(value: object, level: int = 0) -> bool:
    if level > MAX_DEPTH:
        return False
    if isinstance(value, Mapping):
        return all(_depth(key, level + 1) and _depth(item, level + 1) for key, item in value.items())
    if isinstance(value, list):
        return all(_depth(item, level + 1) for item in value)
    return True


def _text(value: object, path: str, errors: list[str], *, maximum: int = 500) -> bool:
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
    if re.search(r"(?i)(?:https?://|www\.|linkedin\.com/|\b(?:session|cookie|bearer|api[_ -]?key|access[_ -]?token)\b|\b[a-f0-9]{32,}\b)", value):
        errors.append(f"{path} contains restricted material")
        return False
    return True


def _date(value: object, path: str, errors: list[str]) -> date | None:
    if not isinstance(value, str):
        errors.append(f"{path} must be an ISO date")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path} must be an ISO date")
        return None


def _url_error(value: object, source_state: object, evidence_mode: object) -> str | None:
    if not isinstance(value, str):
        return "learning source URL is invalid"
    # Reserved test URLs are allowed only for explicitly synthetic fixtures.
    if evidence_mode == "synthetic":
        if not value.startswith("https://example.com/") or any(marker in value for marker in ("@", "?", "#")):
            return "learning source URL is invalid"
        return None
    try:
        from urllib.parse import urlsplit
        parsed = urlsplit(value)
    except ValueError:
        return "learning source URL is invalid"
    # `urlsplit` represents an empty userinfo component as an empty string;
    # reject the @ delimiter itself as well as populated credentials.
    if parsed.scheme.casefold() != "https" or "@" in parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        return "learning source URL is invalid"
    host = (parsed.hostname or "").casefold().rstrip(".")
    # Decimal IPv4 forms (for example 2130706433) are not accepted as public
    # hostnames even when the standard library does not parse them as IPs.
    if not host or host.isdigit() or host == "localhost" or host.endswith(".localhost"):
        return "learning source URL is invalid"
    if host == "example.com" or host.endswith(".example.com") or host == "example.org" or host.endswith(".example.org") or host == "example.net" or host.endswith(".example.net"):
        return "learning source URL is invalid"
    if re.fullmatch(r"(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+)){0,3}", host, re.I):
        return "learning source URL is invalid"
    if "." not in host or host.endswith((".internal", ".local", ".home", ".lan")):
        return "learning source URL is invalid"
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
        return "learning source URL is invalid"
    return None


def _source_url_identity(value: str) -> str:
    """Canonicalize policy-approved HTTPS URLs for duplicate detection only."""
    from urllib.parse import unquote, urlsplit

    parsed = urlsplit(value)
    host = (parsed.hostname or "").casefold().rstrip(".")
    path = unquote(parsed.path) or "/"
    if len(path) > 1:
        path = path.rstrip("/") or "/"
    port = parsed.port
    authority = host
    if ":" in host and not host.startswith("["):
        authority = f"[{host}]"
    if port not in {None, 443}:
        authority = f"{authority}:{port}"
    return f"https://{authority}{path}"


def _validate_preferences(value: object, errors: list[str]) -> None:
    row = _closed(value, "candidate_preferences", PREFERENCE_FIELDS, errors)
    if row is None:
        return
    for field in ("weekly_time_budget", "money_budget", "currency"):
        _text(row.get(field), f"candidate_preferences.{field}", errors, maximum=100)
    if row.get("purchase_authorized") is not False:
        errors.append("candidate_preferences.purchase_authorized must be false")


def _validate_action_gate(value: object, path: str, option_type: object, errors: list[str]) -> None:
    row = _closed(value, f"{path}.action_gate", ACTION_GATE_FIELDS, errors)
    if row is None:
        return
    if row.get("external_action_authorized") is not False:
        errors.append(f"{path}.action_gate.external_action_authorized must be false")
    if row.get("exact_authorization_required") is not True:
        errors.append(f"{path}.action_gate.exact_authorization_required must be true")
    if row.get("publication_authorized") is not False:
        errors.append(f"{path}.action_gate.publication_authorized must be false")
    for field in (
        "ownership_review", "secrets_review", "confidentiality_review",
        "customer_data_review", "rights_holder_review",
    ):
        if row.get(field) not in REVIEW_STATES:
            errors.append(f"{path}.action_gate.{field} has invalid value")
    if option_type == "candidate_owned_project":
        for field, message in (
            ("ownership_review", "candidate project requires ownership review"),
            ("secrets_review", "candidate project requires secrets review"),
            ("confidentiality_review", "candidate project requires confidentiality review"),
            ("customer_data_review", "candidate project requires customer data review"),
            ("rights_holder_review", "candidate project requires rights holder review"),
        ):
            if row.get(field) != "required":
                errors.append(message)


def _validate_option(value: object, index: int, as_of: date | None, evidence_mode: object, seen_ids: set[str], seen_urls: set[str], errors: list[str]) -> None:
    path = f"options[{index}]"
    row = _closed(value, path, OPTION_FIELDS, errors)
    if row is None:
        return
    option_id = row.get("option_id")
    if not isinstance(option_id, str) or not OPTION_ID.fullmatch(option_id) or option_id in seen_ids:
        errors.append(f"{path}.option_id is invalid or duplicated")
    else:
        seen_ids.add(option_id)
    if not isinstance(row.get("gap_signal"), str) or not SIGNAL.fullmatch(row["gap_signal"]):
        errors.append(f"{path}.gap_signal is invalid")
    option_type = row.get("option_type")
    if option_type not in OPTION_TYPES:
        errors.append(f"{path}.option_type has invalid value")
    for field, maximum in (
        ("provider", 160), ("option", 240), ("source_title", 240), ("geography", 160),
        ("availability", 160), ("role", 160), ("seniority", 160), ("current_cost", 100),
        ("currency", 100), ("tax", 100), ("duration", 160), ("duration_basis", 100),
        ("prerequisite", 300), ("renewal", 160), ("maintenance", 160), ("proof_artifact", 500),
    ):
        _text(row.get(field), f"{path}.{field}", errors, maximum=maximum)
    source_date = _date(row.get("source_date"), f"{path}.source_date", errors)
    if as_of and source_date and source_date > as_of:
        errors.append(f"{path}.source_date cannot be after as_of_date")
    if source_date and source_date > date.today():
        errors.append(f"{path}.source_date cannot be in the future")
    source_state = row.get("source_state")
    if source_state not in SOURCE_STATES:
        errors.append(f"{path}.source_state has invalid value")
    elif source_state in {"stale", "unavailable"}:
        errors.append(f"{path}.source_state must be active or synthetic")
    if evidence_mode == "synthetic" and source_state != "synthetic":
        errors.append("synthetic evidence requires synthetic provider sources")
    if evidence_mode == "live" and source_state != "active":
        errors.append("live evidence requires active provider sources")
    url = row.get("url")
    if row.get("duration_basis") not in DURATION_BASES:
        errors.append(f"{path}.duration_basis has invalid value")
    if option_type == "do_nothing_now":
        if url is not None:
            errors.append("do_nothing_now option must not have a URL")
        if row.get("provider") != "none" or any(row.get(field) != "not_applicable" for field in ("current_cost", "currency", "tax", "renewal", "maintenance")):
            errors.append("do_nothing_now option has invalid provider fields")
    elif _url_error(url, source_state, evidence_mode):
        errors.append(f"{path}.url is invalid")
    elif isinstance(url, str):
        identity = _source_url_identity(url)
        if identity in seen_urls:
            errors.append("learning options must not duplicate source URLs")
        seen_urls.add(identity)
    if option_type in {"candidate_owned_project", "lab", "free_resource"}:
        if any(row.get(field) != "not_applicable" for field in ("current_cost", "currency", "tax")):
            errors.append(f"{option_type} option must not claim a price")
        if row.get("duration_basis") != "candidate_estimated":
            if option_type in {"candidate_owned_project", "lab"}:
                errors.append(f"{option_type} option requires candidate_estimated duration basis")
    current_cost = str(row.get("current_cost", "")).casefold()
    if current_cost not in {"unknown", "not_applicable", "free", "0", "0.0"} and any(
        row.get(field) in {"unknown", "not_applicable"} for field in ("currency", "tax")
    ):
        errors.append(f"{path} paid cost requires currency and tax")
    if re.search(r"\bm[eé]xico\b", str(row.get("geography", "")), re.I):
        errors.append(f"{path} Mexico eligibility must be explicitly verified")
    merged_terms = f"{row.get('renewal', '')} {row.get('maintenance', '')}".casefold()
    if "renewal" in merged_terms and "maintenance" in merged_terms:
        errors.append(f"{path}.renewal and maintenance must remain separate")
    unknowns = row.get("unknowns")
    if not isinstance(unknowns, list) or len(unknowns) > 20 or any(not _text(item, f"{path}.unknowns", errors, maximum=300) for item in unknowns):
        errors.append(f"{path}.unknowns has invalid values")
    _validate_action_gate(row.get("action_gate"), path, option_type, errors)


def validate_research(value: object) -> list[str]:
    """Return bounded, non-echoing diagnostics for a closed research artifact."""
    errors: list[str] = []
    try:
        if not isinstance(value, Mapping):
            return ["learning option research must be an object"]
        if not _depth(value):
            errors.append("learning option research exceeds maximum nesting depth")
        if set(value) - TOP_FIELDS:
            errors.append("learning option research has unsupported fields")
        if TOP_FIELDS - set(value):
            errors.append("learning option research is missing required fields")
        if value.get("schema_version") != SCHEMA_VERSION:
            errors.append("schema_version has invalid value")
        evidence_mode = value.get("evidence_mode")
        if evidence_mode not in EVIDENCE_MODES:
            errors.append("evidence_mode has invalid value")
        if value.get("locale") not in {"es", "en"}:
            errors.append("locale has invalid value")
        as_of = _date(value.get("as_of_date"), "as_of_date", errors)
        if as_of and as_of > date.today():
            errors.append("as_of_date cannot be in the future")
        if not isinstance(value.get("source_market_snapshot"), str) or not MARKET_SNAPSHOT.fullmatch(value["source_market_snapshot"]):
            errors.append("source_market_snapshot has invalid value")
        _validate_preferences(value.get("candidate_preferences"), errors)
        options = value.get("options")
        if not isinstance(options, list) or not 1 <= len(options) <= 5:
            errors.append("options has invalid item count")
        else:
            seen_ids: set[str] = set()
            seen_urls: set[str] = set()
            for index, option in enumerate(options):
                _validate_option(option, index, as_of, evidence_mode, seen_ids, seen_urls, errors)
        if value.get("privacy_boundary") != "identity_free_market_and_provider_evidence_only":
            errors.append("privacy_boundary has invalid value")
        if value.get("no_external_action") is not True:
            errors.append("no_external_action must be true")
    except (RecursionError, TypeError, ValueError):
        errors.append("learning option research could not be validated")
    return sorted(set(errors))


def snapshot_for_learning_research(value: Mapping[str, object]) -> str:
    """Return a canonical content-bound snapshot identifier for valid-shaped research."""
    if not isinstance(value, Mapping):
        raise ValueError("learning option research must be an object")
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"snap-learning-sha256-{hashlib.sha256(encoded).hexdigest()}"


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, item in pairs:
        if key in output:
            raise ValueError("duplicate JSON key")
        output[key] = item
    return output


def load_research(path: Path) -> dict[str, object]:
    """Load a bounded JSON object without following caller-controlled links."""
    try:
        raw = _loader.read_bounded_bytes(path, MAX_INPUT_BYTES)
    except _loader.PrivateInputError as exc:
        raise ValueError("learning option research exceeds input bound") from exc
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        if not isinstance(value, dict) or not _depth(value):
            raise ValueError("learning option research exceeds maximum nesting depth")
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ValueError("learning option research could not be loaded") from exc
    if not isinstance(value, dict):
        raise ValueError("learning option research must be an object")
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
    except (OSError, ValueError):
        print("learning option research could not be loaded", file=sys.stderr)
        return 2
    errors = validate_research(value)
    if errors:
        sys.stderr.write(_prose.format_bounded_diagnostics(errors))
        return 1
    print("valid learning option research")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
