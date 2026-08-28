#!/usr/bin/env python3
"""Validate reproducible, identity-free market learning dossiers."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from collections.abc import Mapping, Sequence
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
        raise RuntimeError("required market dossier dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_loader = _sibling("private_input_loader.py")
_prose = _sibling("private_prose_safety.py")
RESEARCH = _sibling("validate_target_vacancy_research.py")

SCHEMA_VERSION = "career-market-learning-dossier-v1"
MAX_INPUT_BYTES = 256 * 1024
MAX_DEPTH = 12
MARKET_SNAPSHOT = re.compile(r"^snap-market-sha256-[0-9a-f]{64}$")
DOSSIER_SNAPSHOT = re.compile(r"^snap-dossier-sha256-[0-9a-f]{64}$")
VACANCY_ID = re.compile(r"^V-[0-9]{3}$")
REQUIREMENT_ID = re.compile(r"^V-[0-9]{3}-R-[0-9]{2}$")
SIGNAL = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
SUPPORT_NUMERATORS = {
    "verified_match": 2,
    "candidate_reported_match": 2,
    "adjacent_evidence": 1,
    "explicit_gap": 0,
    "unknown": 0,
}
IMPORTANCE_WEIGHTS = {"must_have": 2, "preferred": 1, "responsibility_only": 0}
EVIDENCE_MODES = frozenset({"synthetic", "live"})
TOP_FIELDS = frozenset({
    "schema_version", "evidence_mode", "locale", "as_of_date", "state", "source_research_snapshot",
    "source_executive_dossier_snapshot", "search_summary", "vacancy_cards", "matrix_rows",
    "recurrence_rows", "learning_state", "learning_decisions", "methodology_boundary",
    "privacy_boundary", "no_external_action",
})
BASE_CARD_FIELDS = frozenset({
    "vacancy_id", "employer_name", "title", "location", "arrangement", "source_kind", "source_url",
    "requirements", "earned_points", "maximum_points", "known_points", "alignment_percent",
    "evidence_coverage_percent", "interpretation", "qualitative_band",
})
FRESHNESS_FIELDS = frozenset({
    "access_date", "publication_date", "freshness_status", "freshness_basis",
    "freshness_window_days", "freshness_reason",
})
FRESHNESS_STATUSES = frozenset({"current", "unknown"})
FRESHNESS_BASES = frozenset({"publication_date", "access_date", "unknown"})
FRESHNESS_REASONS = frozenset({
    "publication_date_within_window",
    "publication_date_unknown_verified_open_on_access_date",
    "outside_window",
    "source_status_unknown",
})


def rounded_percent(numerator: int, denominator: int) -> int:
    return 0 if denominator == 0 else (100 * numerator + denominator // 2) // denominator


def snapshot_for_market_dossier(value: Mapping[str, object]) -> str:
    """Return the canonical content-bound identifier for a validated market dossier."""
    if not isinstance(value, Mapping):
        raise ValueError("market learning dossier must be an object")
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"snap-market-sha256-{hashlib.sha256(canonical).hexdigest()}"


def alignment_score(
    requirements: Sequence[object], bindings: Mapping[str, object],
) -> tuple[int, int, int]:
    """Return earned, possible and evidence-known integer points."""
    earned = possible = known = 0
    for requirement in requirements:
        if not isinstance(requirement, Mapping):
            continue
        weight = IMPORTANCE_WEIGHTS.get(requirement.get("importance"), 0)
        possible += 2 * weight
        binding = bindings.get(requirement.get("signal"))
        state = binding.get("support_state") if isinstance(binding, Mapping) else "unknown"
        numerator = SUPPORT_NUMERATORS.get(state, 0)
        earned += numerator * weight
        if state != "unknown":
            known += 2 * weight
    return earned, possible, known


def recurrence_rows(vacancies: Sequence[object], bindings: Mapping[str, object]) -> list[dict[str, object]]:
    """Return deterministic signal recurrence over the supplied actual sample."""
    if not vacancies:
        return []
    occurrences: dict[str, int] = {}
    for vacancy in vacancies:
        if not isinstance(vacancy, Mapping) or not isinstance(vacancy.get("requirements"), list):
            continue
        seen: set[str] = set()
        for requirement in vacancy["requirements"]:
            if isinstance(requirement, Mapping) and isinstance(requirement.get("signal"), str):
                seen.add(requirement["signal"])
        for signal in seen:
            occurrences[signal] = occurrences.get(signal, 0) + 1
    count = len(vacancies)
    rows: list[dict[str, object]] = []
    for signal, total in occurrences.items():
        binding = bindings.get(signal)
        if not isinstance(binding, Mapping):
            continue
        rows.append({
            "signal": signal,
            "occurrences": total,
            "sample_size": count,
            "display_fraction": f"{total}/{count}",
            "support_state": binding.get("support_state"),
            "evidence_ids": list(binding.get("evidence_ids", [])),
        })
    return sorted(rows, key=lambda row: (-int(row["occurrences"]), str(row["signal"])))


def _closed(
    value: object,
    path: str,
    fields: frozenset[str],
    errors: list[str],
    *,
    required_fields: frozenset[str] | None = None,
) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    if set(value) - fields:
        errors.append(f"{path} has unsupported fields")
    if (required_fields if required_fields is not None else fields) - set(value):
        errors.append(f"{path} is missing required fields")
    return value


def _private_text(value: object, path: str, errors: list[str], maximum: int = 500) -> None:
    if not isinstance(value, str) or not value or len(value) > maximum:
        errors.append(f"{path} must be bounded text")
        return
    if _prose.contains_unicode_controls(value):
        errors.append(f"{path} contains forbidden control characters")
    if re.search(r"<\/?(?:script|iframe|object|style)\b", value, re.I):
        errors.append(f"{path} contains forbidden markup")
    if re.search(r"(?:[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:^|\s)(?:/[A-Za-z]|[A-Za-z]:[\\/]))", value):
        errors.append(f"{path} contains private value")


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


def _source_url_error(value: object, source_kind: object, evidence_mode: object) -> str | None:
    error = RESEARCH.source_url_policy_error(
        value,
        source_kind=source_kind if isinstance(source_kind, str) else None,
        evidence_mode=evidence_mode if isinstance(evidence_mode, str) else "",
    )
    if error == "live evidence cannot use a reserved source domain":
        return "live source URL cannot use a reserved domain"
    return error


def _depth(value: object, level: int = 0) -> bool:
    if level > MAX_DEPTH:
        return False
    if isinstance(value, Mapping):
        return all(_depth(key, level + 1) and _depth(item, level + 1) for key, item in value.items())
    if isinstance(value, list):
        return all(_depth(item, level + 1) for item in value)
    return True


def _card_requirements(value: object, path: str, errors: list[str]) -> list[Mapping[str, object]]:
    if not isinstance(value, list) or not 1 <= len(value) <= 30:
        errors.append(f"{path} has invalid item count")
        return []
    rows: list[Mapping[str, object]] = []
    ids: set[str] = set()
    signals: set[str] = set()
    for index, item in enumerate(value):
        row = _closed(item, f"{path}[{index}]", frozenset({"requirement_id", "signal", "importance"}), errors)
        if row is None:
            continue
        requirement_id = row.get("requirement_id")
        signal = row.get("signal")
        if not isinstance(requirement_id, str) or not REQUIREMENT_ID.fullmatch(requirement_id) or requirement_id in ids:
            errors.append(f"{path}[{index}].requirement_id is invalid or duplicated")
        else:
            ids.add(requirement_id)
        if not isinstance(signal, str) or not SIGNAL.fullmatch(signal) or signal in signals:
            errors.append(f"{path}[{index}].signal is invalid or duplicated")
        else:
            signals.add(signal)
        if row.get("importance") not in IMPORTANCE_WEIGHTS:
            errors.append(f"{path}[{index}].importance has invalid value")
        rows.append(row)
    return rows


def _bindings_from_matrix(value: object, cards: Sequence[Mapping[str, object]], errors: list[str]) -> dict[str, dict[str, object]]:
    if not isinstance(value, list):
        errors.append("matrix_rows must be an array")
        return {}
    expected_signals = {req["signal"] for card in cards for req in card["requirements"] if isinstance(req.get("signal"), str)}
    card_ids = [str(card.get("vacancy_id")) for card in cards]
    bindings: dict[str, dict[str, object]] = {}
    for index, item in enumerate(value):
        row = _closed(item, f"matrix_rows[{index}]", frozenset({"signal", "support_state", "evidence_ids", "cells"}), errors)
        if row is None:
            continue
        signal = row.get("signal")
        if not isinstance(signal, str) or not SIGNAL.fullmatch(signal) or signal in bindings:
            errors.append(f"matrix_rows[{index}].signal is invalid or duplicated")
            continue
        state = row.get("support_state")
        if state not in SUPPORT_NUMERATORS:
            errors.append(f"matrix_rows[{index}].support_state has invalid value")
        evidence_ids = row.get("evidence_ids")
        if not isinstance(evidence_ids, list) or len(evidence_ids) != len(set(evidence_ids)) or any(not isinstance(item, str) or not re.fullmatch(r"E-[0-9]{3}", item) for item in evidence_ids):
            errors.append(f"matrix_rows[{index}].evidence_ids has invalid values")
        if state == "unknown" and evidence_ids != []:
            errors.append(f"matrix_rows[{index}].unknown must not reference evidence")
        if state != "unknown" and not evidence_ids:
            errors.append(f"matrix_rows[{index}].support state requires evidence")
        cells = row.get("cells")
        if not isinstance(cells, list) or len(cells) != len(card_ids):
            errors.append(f"matrix_rows[{index}].cells has invalid item count")
        else:
            observed_ids: list[str] = []
            for cell_index, cell in enumerate(cells):
                cell_row = _closed(cell, f"matrix_rows[{index}].cells[{cell_index}]", frozenset({"vacancy_id", "required"}), errors)
                if cell_row is None:
                    continue
                vacancy_id = cell_row.get("vacancy_id")
                if not isinstance(vacancy_id, str):
                    errors.append(f"matrix_rows[{index}].cells[{cell_index}].vacancy_id is invalid")
                else:
                    observed_ids.append(vacancy_id)
                if type(cell_row.get("required")) is not bool:
                    errors.append(f"matrix_rows[{index}].cells[{cell_index}].required must be boolean")
            if observed_ids != card_ids:
                errors.append(f"matrix_rows[{index}].cells must follow vacancy card order")
            for card, cell in zip(cards, cells):
                required = any(req.get("signal") == signal for req in card["requirements"])
                if isinstance(cell, Mapping) and cell.get("required") is not required:
                    errors.append(f"matrix_rows[{index}].cells do not match requirements")
        bindings[signal] = {"support_state": state, "evidence_ids": evidence_ids}
    if set(bindings) != expected_signals:
        errors.append("matrix_rows must cover every scoreable signal exactly once")
    return bindings


def _qualitative_band(alignment: int, coverage: int) -> str:
    if coverage < 50:
        return "insufficient_evidence"
    if alignment >= 75:
        return "higher_documented_alignment"
    if alignment >= 50:
        return "moderate_documented_alignment"
    return "lower_documented_alignment"


def _validate_freshness(row: Mapping[str, object], path: str, as_of_date: date | None, errors: list[str]) -> None:
    """Require freshness metadata to describe one coherent source state."""
    access_date = _date(row.get("access_date"), f"{path}.access_date", errors)
    if access_date and as_of_date and access_date != as_of_date:
        errors.append(f"{path}.access_date must equal as_of_date")
    publication = row.get("publication_date")
    publication_date = None if publication is None else _date(publication, f"{path}.publication_date", errors)
    if publication_date and as_of_date and publication_date > as_of_date:
        errors.append(f"{path}.publication_date cannot be after as_of_date")
    status = row.get("freshness_status")
    if status not in FRESHNESS_STATUSES:
        errors.append(f"{path}.freshness_status has invalid value")
    basis = row.get("freshness_basis")
    if basis not in FRESHNESS_BASES:
        errors.append(f"{path}.freshness_basis has invalid value")
    window = row.get("freshness_window_days")
    if type(window) is not int or not 1 <= window <= 365:
        errors.append(f"{path}.freshness_window_days has invalid value")
    reason = row.get("freshness_reason")
    if reason not in FRESHNESS_REASONS:
        errors.append(f"{path}.freshness_reason has invalid value")

    if publication_date is None:
        if status == "current":
            errors.append(f"{path}.freshness_status cannot be current without publication_date")
        expected = {
            "freshness_status": "unknown",
            "freshness_basis": "unknown",
            "freshness_reason": "publication_date_unknown_verified_open_on_access_date",
        }
    else:
        expected = {"freshness_basis": "publication_date"}
        age_days = (as_of_date - publication_date).days if as_of_date else None
        if type(window) is int and age_days is not None and age_days >= 0:
            if age_days > window:
                expected.update(freshness_status="unknown", freshness_reason="outside_window")
            elif status == "current":
                expected["freshness_reason"] = "publication_date_within_window"
            else:
                expected.update(freshness_status="unknown", freshness_reason="source_status_unknown")
    for field, expected_value in expected.items():
        if row.get(field) != expected_value:
            errors.append(f"{path}.{field} does not reconcile with freshness metadata")


def validate_market_dossier(value: object) -> list[str]:
    """Validate output shape and recompute every deterministic calculation."""
    errors: list[str] = []
    try:
        if not isinstance(value, Mapping):
            return ["market learning dossier must be an object"]
        if not _depth(value):
            errors.append("market learning dossier exceeds maximum nesting depth")
        if set(value) - TOP_FIELDS:
            errors.append("market learning dossier has unsupported fields")
        if TOP_FIELDS - set(value):
            errors.append("market learning dossier is missing required fields")
        if value.get("schema_version") != SCHEMA_VERSION:
            errors.append("schema_version has invalid value")
        evidence_mode = value.get("evidence_mode")
        if evidence_mode not in EVIDENCE_MODES:
            errors.append("evidence_mode has invalid value")
        if value.get("locale") not in {"es", "en"}:
            errors.append("locale has invalid value")
        as_of_date = _date(value.get("as_of_date"), "as_of_date", errors, live=evidence_mode == "live")
        if not isinstance(value.get("source_research_snapshot"), str) or not MARKET_SNAPSHOT.fullmatch(value["source_research_snapshot"]):
            errors.append("source_research_snapshot has invalid value")
        if not isinstance(value.get("source_executive_dossier_snapshot"), str) or not DOSSIER_SNAPSHOT.fullmatch(value["source_executive_dossier_snapshot"]):
            errors.append("source_executive_dossier_snapshot has invalid value")
        if value.get("state") not in {"complete", "limited_market_evidence", "market_evidence_unavailable"}:
            errors.append("state has invalid value")
        summary = _closed(value.get("search_summary"), "search_summary", frozenset({"vacancy_sample_count", "bounded_queries_run", "limit_reason", "limitation"}), errors)
        if summary is not None:
            if type(summary.get("vacancy_sample_count")) is not int or not 0 <= summary["vacancy_sample_count"] <= 5:
                errors.append("search_summary.vacancy_sample_count has invalid value")
            if type(summary.get("bounded_queries_run")) is not int or not 0 <= summary["bounded_queries_run"] <= 100:
                errors.append("search_summary.bounded_queries_run has invalid value")
            if summary.get("limit_reason") not in {"target_reached", "search_limit_reached", "source_limit", "none"}:
                errors.append("search_summary.limit_reason has invalid value")
            _private_text(summary.get("limitation"), "search_summary.limitation", errors)
        cards_value = value.get("vacancy_cards")
        cards: list[Mapping[str, object]] = []
        if not isinstance(cards_value, list) or len(cards_value) > 5:
            errors.append("vacancy_cards has invalid item count")
        else:
            seen_cards: set[str] = set()
            for index, item in enumerate(cards_value):
                row = _closed(
                    item,
                    f"vacancy_cards[{index}]",
                    BASE_CARD_FIELDS | FRESHNESS_FIELDS,
                    errors,
                    required_fields=BASE_CARD_FIELDS | FRESHNESS_FIELDS,
                )
                if row is None:
                    continue
                vacancy_id = row.get("vacancy_id")
                if not isinstance(vacancy_id, str) or not VACANCY_ID.fullmatch(vacancy_id) or vacancy_id in seen_cards:
                    errors.append(f"vacancy_cards[{index}].vacancy_id is invalid or duplicated")
                else:
                    seen_cards.add(vacancy_id)
                for field, maximum in (("employer_name", 160), ("title", 240), ("location", 160)):
                    _private_text(row.get(field), f"vacancy_cards[{index}].{field}", errors, maximum)
                if row.get("arrangement") not in {"onsite", "hybrid", "remote", "flexible"}:
                    errors.append(f"vacancy_cards[{index}].arrangement has invalid value")
                source_kind = row.get("source_kind")
                if source_kind not in {"official_employer", "employer_operated_ats", "linkedin_jobs_backup"}:
                    errors.append(f"vacancy_cards[{index}].source_kind has invalid value")
                source_error = _source_url_error(row.get("source_url"), source_kind, evidence_mode)
                if source_error:
                    errors.append(source_error if "reserved domain" in source_error else f"vacancy_cards[{index}].source_url is invalid")
                requirements = _card_requirements(row.get("requirements"), f"vacancy_cards[{index}].requirements", errors)
                _validate_freshness(row, f"vacancy_cards[{index}]", as_of_date, errors)
                row = dict(row)
                row["requirements"] = requirements
                cards.append(row)
        count = len(cards)
        expected_count = value.get("state") == "complete" and count == 5 or value.get("state") == "limited_market_evidence" and 1 <= count <= 4 or value.get("state") == "market_evidence_unavailable" and count == 0
        if not expected_count:
            errors.append("state/count coupling is invalid")
        if summary is not None and summary.get("vacancy_sample_count") != count:
            errors.append("search_summary.vacancy_sample_count must equal vacancy card count")
        bindings = _bindings_from_matrix(value.get("matrix_rows"), cards, errors)
        expected_card_order = sorted(cards, key=lambda card: (-rounded_percent(*alignment_score(card["requirements"], bindings)[:2]), str(card.get("vacancy_id"))))
        if [card.get("vacancy_id") for card in cards] != [card.get("vacancy_id") for card in expected_card_order]:
            errors.append("vacancy_cards must be sorted by alignment then vacancy id")
        for index, card in enumerate(cards):
            earned, maximum, known = alignment_score(card["requirements"], bindings)
            expected = {
                "earned_points": earned,
                "maximum_points": maximum,
                "known_points": known,
                "alignment_percent": rounded_percent(earned, maximum),
                "evidence_coverage_percent": rounded_percent(known, maximum),
            }
            for field, computed in expected.items():
                if card.get(field) != computed:
                    errors.append(f"vacancy_cards[{index}].{field} does not reconcile")
            if card.get("interpretation") != "directional_documented_evidence_not_hiring_fit":
                errors.append(f"vacancy_cards[{index}].interpretation has invalid value")
            if card.get("qualitative_band") != _qualitative_band(expected["alignment_percent"], expected["evidence_coverage_percent"]):
                errors.append(f"vacancy_cards[{index}].qualitative_band does not reconcile")
        expected_recurrence = recurrence_rows(cards, bindings)
        if value.get("recurrence_rows") != expected_recurrence:
            errors.append("recurrence_rows do not reconcile")
        if value.get("learning_state") != "not_evaluated" or value.get("learning_decisions") != []:
            errors.append("learning placeholder has invalid value")
        if value.get("methodology_boundary") != "sample_based_documented_evidence_only_no_hiring_fit":
            errors.append("methodology_boundary has invalid value")
        if value.get("privacy_boundary") != "identity_free_evidence_references_only":
            errors.append("privacy_boundary has invalid value")
        if value.get("no_external_action") is not True:
            errors.append("no_external_action must be true")
    except (RecursionError, TypeError, ValueError, KeyError):
        errors.append("market learning dossier could not be validated")
    return sorted(set(errors))


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, item in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = item
    return result


def load_market_dossier(path: Path) -> dict[str, object]:
    try:
        raw = _loader.read_bounded_bytes(path, MAX_INPUT_BYTES)
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        if not isinstance(value, dict) or not _depth(value):
            raise ValueError("market learning dossier exceeds maximum nesting depth")
    except (_loader.PrivateInputError, UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ValueError("market learning dossier could not be loaded") from exc
    if not isinstance(value, dict):
        raise ValueError("market learning dossier must be an object")
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
        value = load_market_dossier(args.path)
    except ValueError:
        print("market learning dossier could not be loaded", file=sys.stderr)
        return 2
    errors = validate_market_dossier(value)
    if errors:
        sys.stderr.write(_prose.format_bounded_diagnostics(errors))
        return 1
    print("valid market learning dossier")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
