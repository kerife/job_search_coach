#!/usr/bin/env python3
"""Scan tracked evaluation evidence without emitting matched private values."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterator, NamedTuple
from urllib.parse import unquote


TEXT_SUFFIXES = frozenset(
    {".csv", ".html", ".json", ".md", ".tsv", ".txt", ".yaml", ".yml"}
)
STAGED_RELEASE_ARTIFACT_ROOTS = frozenset(
    {Path(".professional-growth-coach-artifacts"), Path(".superpowers")}
)
MAX_STAGED_ARTIFACT_BYTES = 1024 * 1024
DOSSIER_SOURCE_INVENTORY_PATHS = (
    Path("plugins/professional-growth-coach/schemas/executive-career-dossier-v1.schema.json"),
    Path("plugins/professional-growth-coach/scripts/validate_executive_career_dossier.py"),
    Path("plugins/professional-growth-coach/scripts/render_executive_career_dossier.py"),
    Path("plugins/professional-growth-coach/assets/executive-career-dossier-v1.html"),
    Path("plugins/professional-growth-coach/assets/executive-career-dossier-v1.css"),
    Path("tests/test_executive_career_dossier.py"),
    Path("plugins/professional-growth-coach/schemas/target-vacancy-research-v1.schema.json"),
    Path("plugins/professional-growth-coach/schemas/candidate-market-alignment-v1.schema.json"),
    Path("plugins/professional-growth-coach/schemas/career-market-learning-dossier-v1.schema.json"),
    Path("plugins/professional-growth-coach/schemas/career-market-learning-dossier-v2.schema.json"),
    Path("plugins/professional-growth-coach/schemas/learning-option-research-v1.schema.json"),
    Path("plugins/professional-growth-coach/scripts/validate_target_vacancy_research.py"),
    Path("plugins/professional-growth-coach/scripts/build_career_market_learning_dossier.py"),
    Path("plugins/professional-growth-coach/scripts/validate_career_market_learning_dossier.py"),
    Path("plugins/professional-growth-coach/scripts/build_career_market_learning_dossier_v2.py"),
    Path("plugins/professional-growth-coach/scripts/validate_career_market_learning_dossier_v2.py"),
    Path("plugins/professional-growth-coach/scripts/validate_learning_option_research.py"),
    Path("plugins/professional-growth-coach/assets/career-market-learning-dossier-v1.css"),
)
INVENTORY_PATHS = (
    Path("docs/superpowers/plans/2026-08-05-job-search-coach-plugin.md"),
    Path("docs/superpowers/plans/2026-08-07-linkedin-client-report-v2.md"),
    Path("tests/evals/final/installed-smoke-test.md"),
    Path("tests/evals/baseline/linkedin.md"),
    Path("tests/evals/with-skill/linkedin.md"),
)
MARKER_PATHS = (
    Path("tests/evals/baseline/linkedin.md"),
    Path("tests/evals/with-skill/linkedin.md"),
    Path("tests/evals/final/installed-smoke-test.md"),
    Path("tests/evals/final/cycle-1.md"),
    Path("tests/evals/final/cycle-2.md"),
)
MARKER_DIRECTORIES = (
    Path("tests/evals/final/cycle-1"),
    Path("tests/evals/final/cycle-2"),
)

RULES = {
    "EMAIL_ADDRESS": re.compile(
        r"(?i)(?<![a-z0-9._%+-])[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}(?![a-z0-9.-])"
    ),
    "PHONE_NUMBER": re.compile(
        r"(?<![a-z0-9])(?:\+?\d[\s().-]*)?(?:\d[\s().-]*){9,}\d(?![a-z0-9])",
        re.I,
    ),
    "LINKEDIN_PROFILE_URL": re.compile(
        r"(?i)(?<![a-z0-9.-])(?:https?://)?(?:[a-z]{2,3}\.)?"
        r"linkedin\.com/(?:in|pub)/[^\s\]\[<>()]+"
    ),
    "LOCAL_USER_PATH": re.compile(
        r"(?i)(?:/Users/[^/\s]+/|/home/[^/\s]+/|[A-Z]:\\Users\\[^\\\s]+\\)"
    ),
    "RAW_PROFILE_MATERIAL": re.compile(
        r"(?i)\b(?:raw[_ -]?profile|profile[_ -]?(?:dump|export|payload|transcript|text)|"
        r"about_text|experience_text|headline_text)\b\s*[:=]"
    ),
    "SECRET_ASSIGNMENT": re.compile(
        r"(?i)(?:\bauthorization\b[\"']?\s*:\s*[\"']?"
        r"(?:Bearer|Basic)\s+[^\s;,\"']{8,}|"
        r"[?&#](?:access[_-]?token|refresh[_-]?token|api[_-]?key|auth[_-]?token)="
        r"[^\s&#,\"']{8,})"
    ),
}
HANDLE_PATTERN = re.compile(r"(?i)(?<![a-z0-9._%+-])@[a-z][a-z0-9._-]{2,}(?![a-z0-9._-])")
ANALYTICS_LABEL = (
    r"(?:profile[ _-]?views?|profile[ _-]?view[ _-]?count|search[ _-]?appearances?|"
    r"post[ _-]?impressions?|social[ _-]?selling[ _-]?index|follower[ _-]?count|"
    r"private[ _-]?analytics?|visitas?\s+al\s+perfil|apariciones?\s+en\s+b[uú]squedas?)"
)
ANALYTICS_VALUE_PATTERNS = (
    re.compile(rf"(?is)\b{ANALYTICS_LABEL}\b.{{0,160}}?\b\d[\d,.%]*\b"),
    re.compile(rf"(?is)\b\d[\d,.%]*\b.{{0,160}}?\b{ANALYTICS_LABEL}\b"),
    re.compile(
        rf"(?is)[\"']?\b{ANALYTICS_LABEL}\b[\"']?\s*[:=]\s*[\"']?"
        r"(?!unknown\b|not[_ -]?observed\b|none\b)[^\s;,]{2,}"
    ),
)
MARKDOWN_TRUE_MARKER = re.compile(r"(?m)^no_real_profile_mapping: true$")
ASSIGNMENT_PATTERN = re.compile(
    r"(?im)[\"']?([a-z][a-z0-9 _-]{1,79})[\"']?\s*[:=]\s*"
    r"[\"']?([^\n;,\"'}]{1,160})"
)
SAFE_PLACEHOLDER_VALUES = frozenset({"none", "unknown", "not_observed", "not observed"})
NON_RECORD_SCHEMA_PATH = Path(
    "tests/evals/with-skill/fixtures/linkedin-report-v2/schema.json"
)
DOSSIER_SCHEMA_VERSION = "executive-career-dossier-v1"
DOSSIER_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins/professional-growth-coach/scripts/validate_executive_career_dossier.py"
)
DOSSIER_V2_SCHEMA_VERSION = "executive-career-dossier-v2"
DOSSIER_V2_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins/professional-growth-coach/scripts/validate_executive_career_dossier_v2.py"
)
RECRUITER_PRACTICE_SCHEMA_VERSION = "recruiter-practice-session-v1"
RECRUITER_PRACTICE_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins/professional-growth-coach/scripts/validate_recruiter_practice_session.py"
)
MARKET_RESEARCH_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins/professional-growth-coach/scripts/validate_target_vacancy_research.py"
)
MARKET_DOSSIER_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins/professional-growth-coach/scripts/validate_career_market_learning_dossier.py"
)
MARKET_DOSSIER_V2_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins/professional-growth-coach/scripts/validate_career_market_learning_dossier_v2.py"
)
PUBLIC_MARKET_ROW_SCHEMAS = frozenset(
    {
        frozenset(
            {
                "market_public_source_row",
                "source_id",
                "source_url",
                "role_family",
                "geography_bucket",
                "observation_date",
                "compensation_bucket",
                "no_real_profile_mapping",
            }
        ),
        frozenset(
            {
                "geography",
                "currency",
                "seniority",
                "source_date",
                "sample_context",
                "range",
                "demand_signals",
                "recurring_requirements",
                "confidence",
                "warning",
            }
        ),
        frozenset(
            {
                "geography",
                "currency",
                "seniority",
                "source_date",
                "source_state",
                "compensation_observation",
                "sample_context",
                "range",
                "demand_signals",
                "recurring_requirements",
                "confidence",
                "warning",
            }
        ),
        frozenset(
            {
                "geography",
                "currency",
                "seniority",
                "as_of_date",
                "source_date",
                "source_age_days",
                "freshness_window_days",
                "freshness_status",
                "source_state",
                "compensation_observation",
                "compensation_components",
                "component_gaps",
                "employer_or_publisher",
                "source_id",
                "independent_observation_id",
                "comparable_group_id",
                "comparability_status",
                "comparability_check",
                "range_method",
                "conversion_basis",
                "sample_context",
                "range",
                "demand_signals",
                "recurring_requirements",
                "confidence",
                "warning",
            }
        ),
    }
)


def _decode_json_escape_sequences(value: str) -> str:
    def replace_unicode(match: re.Match[str]) -> str:
        return chr(int(match.group(1), 16))

    value = re.sub(r"\\u([0-9a-fA-F]{4})", replace_unicode, value)
    return value.replace(r"\/", "/").replace(r"\\", "\\")


def normalize_and_decode(value: str) -> str:
    current = value
    for _ in range(3):
        normalized = unicodedata.normalize("NFKC", current)
        normalized = "".join(
            character
            for character in normalized
            if unicodedata.category(character) != "Cf"
        )
        decoded = _decode_json_escape_sequences(unquote(normalized))
        if decoded == current:
            return decoded
        current = decoded
    return current


def _json_scalars(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _json_scalars(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _json_scalars(nested)
    elif isinstance(value, (str, int, float, bool)) or value is None:
        yield str(value)


def _json_leaf_assignments(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(nested, (dict, list)):
                yield from _json_leaf_assignments(nested)
            else:
                yield json.dumps(str(key), ensure_ascii=False) + ": " + json.dumps(
                    nested,
                    ensure_ascii=False,
                )
    elif isinstance(value, list):
        for nested in value:
            if isinstance(nested, (dict, list)):
                yield from _json_leaf_assignments(nested)
            else:
                yield json.dumps(nested, ensure_ascii=False)


class _DuplicateJsonKeyError(ValueError):
    pass


class StagedArtifactReadError(ValueError):
    pass


class StagedArtifact(NamedTuple):
    path: Path
    mode: str
    stage: int
    object_id: str


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError("duplicate JSON key")
        result[key] = value
    return result


def _json_depth_is_bounded(value: object, maximum: int, depth: int = 0) -> bool:
    if depth > maximum:
        return False
    if isinstance(value, dict):
        return all(
            _json_depth_is_bounded(nested, maximum, depth + 1)
            for nested in value.values()
        )
    if isinstance(value, list):
        return all(
            _json_depth_is_bounded(nested, maximum, depth + 1)
            for nested in value
        )
    return True


@lru_cache(maxsize=1)
def _load_dossier_validator() -> Callable[[object], list[str]] | None:
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_executive_career_dossier_privacy",
        DOSSIER_VALIDATOR_PATH,
    )
    if specification is None or specification.loader is None:
        return None
    module = importlib.util.module_from_spec(specification)
    try:
        specification.loader.exec_module(module)
    except Exception:
        return None
    validate = getattr(module, "validate_dossier", None)
    return validate if callable(validate) else None


def _safe_dossier_scan_value(text: str, value: object) -> dict[str, object] | None:
    if not isinstance(value, dict) or value.get("schema_version") != DOSSIER_SCHEMA_VERSION:
        return None
    analytics = value.get("analytics")
    privacy = value.get("privacy")
    if (
        not isinstance(analytics, dict)
        or analytics.get("state") != "not_requested"
        or not isinstance(privacy, dict)
        or privacy.get("raw_private_analytics_included") is not False
        or privacy.get("aggregate_analytics_included") is not False
        or len(text.encode("utf-8")) > 256 * 1024
        or not _json_depth_is_bounded(value, 12)
    ):
        return None
    try:
        validate = _load_dossier_validator()
        if validate is None:
            return None
        errors = validate(value)
    except Exception:
        return None
    if type(errors) is not list or any(type(error) is not str for error in errors) or errors:
        return None
    scan_value = copy.deepcopy(value)
    del scan_value["analytics"]["state"]
    del scan_value["privacy"]["raw_private_analytics_included"]
    del scan_value["privacy"]["aggregate_analytics_included"]
    return scan_value


@lru_cache(maxsize=1)
def _load_dossier_v2_contract() -> (
    tuple[Callable[[object], list[str]], Callable[[dict[str, object]], dict[str, object]]]
    | None
):
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_executive_career_dossier_v2_privacy",
        DOSSIER_V2_VALIDATOR_PATH,
    )
    if specification is None or specification.loader is None:
        return None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    try:
        specification.loader.exec_module(module)
    except Exception:
        return None
    validate = getattr(module, "validate_dossier", None)
    project = getattr(module, "project_v2_to_v1", None)
    if not callable(validate) or not callable(project):
        return None
    return validate, project


def _safe_dossier_v2_scan_value(
    text: str, value: object
) -> dict[str, object] | None:
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != DOSSIER_V2_SCHEMA_VERSION
        or len(text.encode("utf-8")) > 256 * 1024
        or not _json_depth_is_bounded(value, 12)
    ):
        return None
    before = copy.deepcopy(value)
    try:
        contract = _load_dossier_v2_contract()
        if contract is None:
            return None
        validate, project = contract
        errors = validate(value)
        if (
            type(errors) is not list
            or any(type(error) is not str for error in errors)
            or errors
        ):
            return None
        projected = project(value)
    except Exception:
        return None
    if value != before or not isinstance(projected, dict):
        return None
    return _safe_dossier_scan_value(text, projected)


@lru_cache(maxsize=1)
def _load_recruiter_practice_validator() -> Callable[[object], list[str]] | None:
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_recruiter_practice_privacy",
        RECRUITER_PRACTICE_VALIDATOR_PATH,
    )
    if specification is None or specification.loader is None:
        return None
    module = importlib.util.module_from_spec(specification)
    previous_path = list(sys.path)
    sys.path.insert(0, str(RECRUITER_PRACTICE_VALIDATOR_PATH.parent))
    try:
        specification.loader.exec_module(module)
    except Exception:
        return None
    finally:
        sys.path[:] = previous_path
    validate = getattr(module, "validate_session", None)
    return validate if callable(validate) else None


def _safe_recruiter_practice_scan_value(
    text: str, value: object
) -> dict[str, object] | None:
    """Elide two validated schema markers, never session prose or other fields.

    The closed schema requires a false no-action guard and a fixed session-kind
    marker. They are classification metadata, not secrets. Any invalid session,
    changed marker, additional field, or prose continues through normal scans.
    """

    if (
        not isinstance(value, dict)
        or value.get("schema_version") != RECRUITER_PRACTICE_SCHEMA_VERSION
        or len(text.encode("utf-8")) > 64_000
        or not _json_depth_is_bounded(value, 12)
    ):
        return None
    delivery = value.get("delivery")
    if (
        not isinstance(delivery, dict)
        or delivery.get("external_actions_authorized") is not False
    ):
        return None
    try:
        validate = _load_recruiter_practice_validator()
        if validate is None:
            return None
        errors = validate(value)
    except Exception:
        return None
    if type(errors) is not list or any(type(error) is not str for error in errors) or errors:
        return None
    scan_value = copy.deepcopy(value)
    del scan_value["delivery"]["external_actions_authorized"]
    del scan_value["session_kind"]
    return scan_value


def _safe_market_artifact_scan_value(text: str, value: object) -> dict[str, object] | None:
    """Elide validated identity-free market artifacts from privacy heuristics."""
    if not isinstance(value, dict):
        return None
    version = value.get("schema_version")
    if version == "target-vacancy-research-v1":
        validator_path = MARKET_RESEARCH_VALIDATOR_PATH
        validator_name = "validate_research"
    elif version == "career-market-learning-dossier-v1":
        validator_path = MARKET_DOSSIER_VALIDATOR_PATH
        validator_name = "validate_market_dossier"
    elif version == "career-market-learning-dossier-v2":
        validator_path = MARKET_DOSSIER_V2_VALIDATOR_PATH
        validator_name = "validate_learning_dossier"
    else:
        return None
    if len(text.encode("utf-8")) > 256 * 1024 or not _json_depth_is_bounded(value, 12):
        return None
    specification = importlib.util.spec_from_file_location(
        f"job_search_coach_{version.replace('-', '_')}_privacy", validator_path
    )
    if specification is None or specification.loader is None:
        return None
    module = importlib.util.module_from_spec(specification)
    try:
        specification.loader.exec_module(module)
        validate = getattr(module, validator_name, None)
        errors = validate(value) if callable(validate) else ["validator unavailable"]
    except Exception:
        return None
    if type(errors) is not list or errors:
        return None
    return {"schema_version": version, "privacy_boundary": value.get("privacy_boundary"), "no_external_action": value.get("no_external_action")}


def _normalize_key(key: object) -> tuple[str, ...]:
    text = normalize_and_decode(str(key))
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)
    return tuple(token for token in re.split(r"[^a-z0-9]+", text.casefold()) if token)


def _key_is_secret(tokens: tuple[str, ...]) -> bool:
    token_set = set(tokens)
    return bool(
        token_set & {"secret", "password", "passwd", "session", "cookie"}
        or ("token" in token_set and token_set & {"access", "refresh", "auth", "api", "bearer", "client"})
        or ("credential" in token_set and token_set & {"access", "auth", "api", "client", "login"})
        or ("key" in token_set and token_set & {"api", "private", "client", "access"})
    )


def _key_is_free_name(tokens: tuple[str, ...]) -> bool:
    token_set = set(tokens)
    return (
        "name" in token_set
        and bool(
            token_set
            & {
                "full", "display", "person", "candidate", "profile", "recruiter", "contact",
                "given", "family", "first", "last", "legal", "preferred", "middle",
            }
        )
    ) or bool(token_set & {"surname", "forename"}) or {"recruiter", "target"} <= token_set


def _key_is_private_analytics(tokens: tuple[str, ...]) -> bool:
    token_set = set(tokens)
    return bool(
        "analytics" in token_set
        or ({"profile"} <= token_set and bool(token_set & {"view", "views", "visit", "visits"}))
        or ({"search"} <= token_set and bool(token_set & {"appearance", "appearances", "result", "results"}))
        or ({"post", "impression"} <= token_set)
        or ({"post", "impressions"} <= token_set)
        or ({"follower"} <= token_set and bool(token_set & {"count", "total"}))
    )


def _key_dimension_families(key: object) -> set[str]:
    tokens = _normalize_key(key)
    token_set = set(tokens)
    families: set[str] = set()
    if (
        _key_is_free_name(tokens)
        or "handle" in token_set
        or bool(token_set & {"candidate", "subject", "person", "profile"} and token_set & {"id", "identifier", "reference", "ref"})
    ):
        families.add("identity")
    if token_set & {"employer", "employing", "company", "organization", "organisation", "org"}:
        families.add("employer")
    if token_set & {"title", "role", "position", "seniority"}:
        families.add("title")
    if token_set & {"location", "geography", "geographic", "region"}:
        families.add("location")
    if token_set & {"date", "time", "timestamp"} or tokens[-1:] == ("at",):
        families.add("date")
    if token_set & {"metric", "count", "scale", "scope", "range", "compensation"}:
        families.add("metric")
    return families


def _mapping_dimension_families(mapping: dict[str, object]) -> set[str]:
    families: set[str] = set()
    for key, nested in mapping.items():
        families.update(_key_dimension_families(key))
        if isinstance(nested, dict):
            families.update(_mapping_dimension_families(nested))
    return families


def _mapping_is_singling_out(mapping: dict[str, object]) -> bool:
    families = _mapping_dimension_families(mapping)
    non_identity_count = len(families - {"identity"})
    return non_identity_count >= 4 or ("identity" in families and non_identity_count >= 3)


def _walk_mappings(value: object) -> Iterator[dict[str, object]]:
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk_mappings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_mappings(nested)


def _parse_semicolon_row(line: str) -> dict[str, str] | None:
    mapping: dict[str, str] = {}
    for part in line.strip().lstrip("- ").split("; "):
        if "=" not in part:
            return None
        key, value = part.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", key):
            return None
        if key in mapping:
            return None
        mapping[key] = value.strip().rstrip(".")
    return mapping or None


def _structured_text_singling_out(path: Path, text: str) -> int:
    count = 0
    for line in text.splitlines():
        mapping = _parse_semicolon_row(line)
        if mapping is None:
            continue
        keys = frozenset(mapping)
        if path == Path("tests/evals/with-skill/market.md") and keys in PUBLIC_MARKET_ROW_SCHEMAS:
            continue
        if _mapping_is_singling_out(mapping):
            count += 1
    return count


def has_true_non_mapping_marker(path: Path, text: str) -> bool:
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return False
        return isinstance(payload, dict) and payload.get("no_real_profile_mapping") is True
    marker_lines = [
        line
        for line in text.splitlines()
        if line.startswith("no_real_profile_mapping:")
    ]
    return marker_lines == ["no_real_profile_mapping: true"]


def validate_closed_vocabulary_artifact(
    path: Path,
    text: str,
    schema: dict[str, object],
) -> list[str]:
    """Validate the replacement LinkedIn artifact with an exact allowlist."""
    errors: list[str] = []
    if path.as_posix() != schema.get("artifact_path"):
        errors.append("CLOSED_VOCABULARY_PATH")
        return errors

    allowed_headings = tuple(schema.get("allowed_headings", ()))
    required_metadata = schema.get("required_metadata", {})
    required_contract_keys = tuple(schema.get("required_contract_keys", ()))
    if not isinstance(required_metadata, dict):
        return ["CLOSED_VOCABULARY_SCHEMA"]

    headings: list[str] = []
    metadata: dict[str, str] = {}
    contract_keys: list[str] = []
    row_pattern = re.compile(r"^- unknown: (.+)\.$")
    for line in text.splitlines():
        if not line:
            continue
        if line.startswith("#"):
            if line not in allowed_headings:
                errors.append("CLOSED_VOCABULARY_TOKEN")
            headings.append(line)
            continue
        if ": " in line and not line.startswith("- "):
            key, value = line.split(": ", 1)
            if required_metadata.get(key) != value or key in metadata:
                errors.append("CLOSED_VOCABULARY_TOKEN")
            metadata[key] = value
            continue
        row_match = row_pattern.fullmatch(line)
        if row_match is None:
            errors.append("CLOSED_VOCABULARY_TOKEN")
            continue
        mapping = _parse_semicolon_row(row_match.group(1))
        if mapping is None:
            errors.append("CLOSED_VOCABULARY_ROW")
            continue
        dynamic_keys = set(mapping) - {
            "candidate_id",
            "evidence_state",
            "scope_bucket",
            "target_id",
            "no_external_action",
            "draft_only",
        }
        if len(dynamic_keys) != 1:
            errors.append("CLOSED_VOCABULARY_ROW")
            continue
        contract_key = dynamic_keys.pop()
        expected_mapping = {
            "candidate_id": "JSC-CASE-ALPHA",
            contract_key: "unknown",
            "evidence_state": "unknown",
            "scope_bucket": "scope_bucket_unknown",
            "target_id": "JSC-TARGET-ALPHA",
            "no_external_action": "true",
            "draft_only": "true",
        }
        if mapping != expected_mapping or contract_key not in required_contract_keys:
            errors.append(f"{contract_key}: CLOSED_VOCABULARY_TOKEN")
        contract_keys.append(contract_key)

    if tuple(headings) != allowed_headings:
        errors.append("CLOSED_VOCABULARY_HEADINGS")
    if metadata != required_metadata:
        errors.append("CLOSED_VOCABULARY_METADATA")
    if tuple(contract_keys) != required_contract_keys:
        errors.append("CLOSED_VOCABULARY_CONTRACT_KEYS")
        for contract_key in required_contract_keys:
            if contract_keys.count(contract_key) != 1:
                errors.append(f"{contract_key}: CLOSED_VOCABULARY_CONTRACT_KEY")
    return sorted(set(errors))


def scan_text(path: Path, text: str) -> Counter[str]:
    corpus_parts = [normalize_and_decode(text)]
    parsed_json: object | None = None
    dossier_candidate: object | None = None
    has_duplicate_json_key = False
    market_artifact_safe = False
    if path.suffix.lower() == ".json":
        try:
            parsed_json = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            parsed_json = None
        try:
            dossier_candidate = json.loads(text, object_pairs_hook=_unique_json_object)
        except _DuplicateJsonKeyError:
            has_duplicate_json_key = True
            dossier_candidate = None
        except (json.JSONDecodeError, ValueError):
            dossier_candidate = None
        if parsed_json is not None:
            safe_scan_value = _safe_dossier_scan_value(text, dossier_candidate)
            if safe_scan_value is None:
                safe_scan_value = _safe_dossier_v2_scan_value(
                    text, dossier_candidate
                )
            if safe_scan_value is None:
                safe_scan_value = _safe_recruiter_practice_scan_value(
                    text, dossier_candidate
                )
            if safe_scan_value is None:
                market_safe_value = _safe_market_artifact_scan_value(
                    text, dossier_candidate
                )
                if market_safe_value is not None:
                    safe_scan_value = market_safe_value
                    market_artifact_safe = True
            if safe_scan_value is not None:
                corpus_parts = [
                    normalize_and_decode(fragment)
                    for fragment in _json_leaf_assignments(safe_scan_value)
                ]
                corpus_parts.extend(
                    normalize_and_decode(scalar)
                    for scalar in _json_scalars(safe_scan_value)
                )
            else:
                corpus_parts.append(
                    normalize_and_decode(
                        json.dumps(parsed_json, sort_keys=True, ensure_ascii=False)
                    )
                )
                corpus_parts.extend(
                    normalize_and_decode(scalar) for scalar in _json_scalars(parsed_json)
                )
    corpus = "\n".join(corpus_parts)
    violations: Counter[str] = Counter()
    if has_duplicate_json_key:
        violations["DUPLICATE_JSON_KEY"] = 1
    for rule_id, pattern in RULES.items():
        matches = list(pattern.finditer(corpus))
        if rule_id == "PHONE_NUMBER":
            matches = [
                match
                for match in matches
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", match.group())
                and not re.search(r"sha256-$", corpus[max(0, match.start() - 7):match.start()])
                and not re.search(r"(?i)codex\.\d+$", corpus[max(0, match.start() - 6):match.end()])
            ]
        count = len(matches)
        if count:
            violations[rule_id] = count
    for key, raw_value in ASSIGNMENT_PATTERN.findall(corpus):
        value = raw_value.strip().casefold().replace("-", "_")
        if value in SAFE_PLACEHOLDER_VALUES:
            continue
        tokens = _normalize_key(key)
        if _key_is_secret(tokens):
            violations["SECRET_ASSIGNMENT"] += 1
        if _key_is_free_name(tokens):
            violations["NAME_FIELD"] += 1
        if _key_is_private_analytics(tokens):
            violations["PRIVATE_ANALYTICS_VALUE"] += 1
    handles = [
        match
        for match in HANDLE_PATTERN.findall(corpus)
        if not re.search(re.escape(match) + r"[a-z0-9.-]+\.[a-z]{2,}", corpus, re.I)
    ]
    if handles:
        violations["SOCIAL_HANDLE"] = len(handles)
    analytics_count = sum(len(pattern.findall(corpus)) for pattern in ANALYTICS_VALUE_PATTERNS)
    if analytics_count:
        violations["PRIVATE_ANALYTICS_VALUE"] = analytics_count
    structured_count = 0 if market_artifact_safe else _structured_text_singling_out(path, normalize_and_decode(text))
    is_exact_non_record_schema = (
        path == NON_RECORD_SCHEMA_PATH
        and isinstance(parsed_json, dict)
        and isinstance(parsed_json.get("$schema"), str)
    )
    if parsed_json is not None and not is_exact_non_record_schema and not market_artifact_safe:
        json_structured_count = sum(
            _mapping_is_singling_out(mapping) for mapping in _walk_mappings(parsed_json)
        )
        structured_count += json_structured_count
    if structured_count:
        violations["SINGLING_OUT_STRUCTURED_COMBINATION"] = structured_count
    return violations


def scan_repository_source_text(path: Path, text: str) -> Counter[str]:
    """Scan code/schema/assets with high-confidence rules that avoid test syntax."""

    corpus = normalize_and_decode(text)
    violations: Counter[str] = Counter()
    email_matches = list(RULES["EMAIL_ADDRESS"].finditer(corpus))
    non_placeholder_emails = [
        match.group(0)
        for match in email_matches
        if not match.group(0).casefold().endswith(".invalid")
        and not re.search(
            r"https?://[^\s/@:]+:$",
            corpus[max(0, match.start() - 80) : match.start()],
            re.I,
        )
    ]
    if non_placeholder_emails:
        violations["EMAIL_ADDRESS"] = len(non_placeholder_emails)

    profile_urls = RULES["LINKEDIN_PROFILE_URL"].findall(corpus)
    non_placeholder_urls = [
        url
        for url in profile_urls
        if not re.search(r"/in/(?:example|synthetic[-a-z0-9]*)\b", url, re.I)
    ]
    if non_placeholder_urls:
        violations["LINKEDIN_PROFILE_URL"] = len(non_placeholder_urls)

    local_paths = RULES["LOCAL_USER_PATH"].findall(corpus)
    if local_paths:
        violations["LOCAL_USER_PATH"] = len(local_paths)

    name_assignment = re.compile(
        r"(?im)\b(?:candidate[_ -]?name|display[_ -]?name|given[_ -]?name|"
        r"family[_ -]?name|legal[_ -]?name|nombre[_ -]?del[_ -]?candidato)\b"
        r"\s*[:=]\s*['\"]([^'\"\n]{2,160})['\"]"
    )
    names = [
        value
        for value in name_assignment.findall(corpus)
        if not re.search(r"\b(?:synthetic|example|placeholder|sentinel|sint[eé]tic[oa])\b", value, re.I)
    ]
    if names:
        violations["NAME_FIELD"] = len(names)

    raw_assignment = re.compile(
        r"(?im)\b(?:raw[_ -]?profile(?:[_ -]?(?:text|data|export))?|"
        r"headline[_ -]?text|about[_ -]?text|experience[_ -]?text)\b"
        r"\s*[:=]\s*['\"]([^'\"\n]{8,500})['\"]"
    )
    raw_values = [
        value
        for value in raw_assignment.findall(corpus)
        if not re.search(r"\b(?:synthetic|example|placeholder|copied profile text)\b", value, re.I)
    ]
    if raw_values:
        violations["RAW_PROFILE_MATERIAL"] = len(raw_values)
    return violations


def tracked_eval_paths(repo_root: Path) -> tuple[Path, ...]:
    result = subprocess.run(
        ["git", "ls-files", "tests/evals"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return tuple(
        Path(line)
        for line in result.stdout.splitlines()
        if Path(line).suffix.lower() in TEXT_SUFFIXES
    )


def staged_release_artifact_snapshot(repo_root: Path) -> tuple[StagedArtifact, ...]:
    """Capture eligible staged paths and their exact blob OIDs in one Git snapshot."""

    result = subprocess.run(
        [
            "git", "diff", "--cached", "--raw", "-z", "--no-renames",
            "--diff-filter=ACMR", "--", *(root.as_posix() for root in STAGED_RELEASE_ARTIFACT_ROOTS),
        ],
        cwd=repo_root,
        capture_output=True,
        check=True,
    )
    parts = result.stdout.split(b"\0")
    records: list[StagedArtifact] = []
    index = 0
    while index + 1 < len(parts):
        metadata = parts[index]
        raw_path = parts[index + 1]
        index += 2
        if not metadata or not raw_path or not metadata.startswith(b":"):
            continue
        fields = metadata[1:].split()
        if len(fields) != 5:
            continue
        new_mode, object_id, status = fields[1], fields[3], fields[4]
        path = Path(raw_path.decode("utf-8", errors="surrogateescape"))
        if (
            status not in {b"A", b"C", b"M", b"R"}
            or new_mode not in {b"100644", b"100755"}
            or path.is_absolute()
            or ".." in path.parts
            or path.suffix.lower() not in TEXT_SUFFIXES
            or not any(path.is_relative_to(root) for root in STAGED_RELEASE_ARTIFACT_ROOTS)
        ):
            continue
        records.append(
            StagedArtifact(
                path=path,
                mode=new_mode.decode("ascii"),
                stage=0,
                object_id=object_id.decode("ascii", errors="strict"),
            )
        )
    return tuple(sorted(set(records)))


def staged_release_artifact_paths(repo_root: Path) -> tuple[Path, ...]:
    return tuple(record.path for record in staged_release_artifact_snapshot(repo_root))


def read_staged_release_artifact_text(
    repo_root: Path, artifact: StagedArtifact | Path
) -> str:
    """Read the immutable blob captured in the supplied staged snapshot record."""

    if isinstance(artifact, Path):
        matches = [
            record
            for record in staged_release_artifact_snapshot(repo_root)
            if record.path == artifact
        ]
        if len(matches) != 1:
            raise StagedArtifactReadError("staged artifact has no unique snapshot entry")
        artifact = matches[0]
    if artifact.mode not in {"100644", "100755"} or artifact.stage != 0:
        raise StagedArtifactReadError("staged artifact is not a regular stage-zero blob")
    object_id = artifact.object_id
    size_result = subprocess.run(
        ["git", "cat-file", "-s", object_id],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    try:
        size = int(size_result.stdout.strip())
    except ValueError as error:
        raise StagedArtifactReadError("staged artifact has invalid blob size") from error
    if size > MAX_STAGED_ARTIFACT_BYTES:
        raise StagedArtifactReadError("staged artifact exceeds scan size limit")
    blob_result = subprocess.run(
        ["git", "cat-file", "blob", object_id],
        cwd=repo_root,
        capture_output=True,
        check=True,
    )
    if len(blob_result.stdout) != size:
        raise StagedArtifactReadError("staged artifact blob size changed")
    try:
        return blob_result.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise StagedArtifactReadError("staged artifact is not UTF-8") from error


def scan_paths(
    repo_root: Path,
    staged_paths: tuple[Path, ...] | set[Path] | None = None,
) -> tuple[Path, ...]:
    staged_snapshot = (
        set(staged_release_artifact_paths(repo_root))
        if staged_paths is None
        else set(staged_paths)
    )
    return tuple(
        sorted(
            set(tracked_eval_paths(repo_root))
            | set(INVENTORY_PATHS)
            | set(DOSSIER_SOURCE_INVENTORY_PATHS)
            | staged_snapshot
        )
    )


def required_marker_paths(repo_root: Path) -> tuple[Path, ...]:
    paths = list(MARKER_PATHS)
    for directory in MARKER_DIRECTORIES:
        paths.extend(
            path.relative_to(repo_root)
            for path in sorted((repo_root / directory).iterdir())
            if path.is_file() and path.suffix.lower() in {".json", ".md"}
        )
    return tuple(paths)


def format_finding(path: Path, rule_id: str, count: int) -> str:
    return f"{path}: {rule_id}: count={count}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    repo_root = arguments.repo_root.resolve()
    failures: Counter[tuple[Path, str]] = Counter()
    staged_snapshot = staged_release_artifact_snapshot(repo_root)
    staged_records = {record.path: record for record in staged_snapshot}
    staged_paths = set(staged_records)
    for path in scan_paths(repo_root, staged_paths):
        try:
            text = (
                read_staged_release_artifact_text(repo_root, staged_records[path])
                if path in staged_paths
                else (repo_root / path).read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError, subprocess.CalledProcessError, StagedArtifactReadError):
            failures[(path, "SCAN_INPUT_UNREADABLE")] += 1
            continue
        violations = (
            scan_repository_source_text(path, text)
            if path in DOSSIER_SOURCE_INVENTORY_PATHS
            else scan_text(path, text)
        )
        for rule_id, count in violations.items():
            failures[(path, rule_id)] += count
        if path == Path("tests/evals/with-skill/linkedin.md"):
            schema_path = repo_root / "tests/fixtures/linkedin-closed-vocabulary.schema.json"
            try:
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                failures[(path, "CLOSED_VOCABULARY_SCHEMA")] += 1
            else:
                for rule_id in validate_closed_vocabulary_artifact(path, text, schema):
                    failures[(path, rule_id)] += 1
    current_snapshot = staged_release_artifact_snapshot(repo_root)
    if current_snapshot != staged_snapshot:
        failures[(Path(".git/index"), "STAGED_INDEX_CHANGED")] += 1
    for path in required_marker_paths(repo_root):
        text = (repo_root / path).read_text(encoding="utf-8")
        if not has_true_non_mapping_marker(path, text):
            failures[(path, "NON_MAPPING_MARKER")] += 1
    for (path, rule_id), count in sorted(failures.items()):
        print(format_finding(path, rule_id, count))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
