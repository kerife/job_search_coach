"""Small dependency-free checker for the closed private artifact schemas.

This intentionally implements only keywords used by the two local schemas; it
is a conformance gate, not a general JSON Schema implementation.
"""
from __future__ import annotations

import datetime as dt
import copy
import importlib.util
import json
import sys
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))
from validate_json_schema_subset import validate_schema_instance


def _load_private_validator(filename: str, module_name: str):
    path = Path(__file__).resolve().parents[1] / "scripts" / filename
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"private validator unavailable: {filename}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def validate_outcome_for_test(value: object, *, as_of: dt.date) -> list[str]:
    validator = _load_private_validator(
        "validate_private_recruiter_conversion_outcome.py",
        "private_conversion_outcome_harness_validator",
    )
    return validator.validate_outcome(value, as_of=as_of)


def validate_checkpoint_for_test(value: object, receipt: object, *, as_of: dt.date) -> list[str]:
    validator = _load_private_validator(
        "validate_private_recruiter_followthrough_checkpoint.py",
        "private_followthrough_checkpoint_harness_validator",
    )
    return validator.validate_checkpoint(value, receipt, as_of=as_of)


def validate_private_fixture_semantics(root: Path, *, as_of: dt.date) -> list[str]:
    """Run custom semantic validators over every private schema fixture."""
    errors: list[str] = []
    outcome_dir = root / "tests/fixtures/private-recruiter-conversion-outcome"
    for path in sorted(outcome_dir.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        for error in validate_outcome_for_test(value, as_of=as_of):
            errors.append(f"{path.name}: {error}")
    checkpoint_dir = root / "tests/fixtures/private-recruiter-followthrough-checkpoint"
    receipts: dict[tuple[object, object, object], dict[str, object]] = {}
    for receipt_path in sorted(outcome_dir.glob("*.json")):
        receipt_value = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipts[(receipt_value.get("source_artifact_id"), receipt_value.get("source_version"), receipt_value.get("event_type"))] = receipt_value
    for path in sorted(checkpoint_dir.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        source = value.get("source_receipt", {})
        receipt = receipts.get((source.get("id"), source.get("source_version"), source.get("event_type")))
        if receipt is None:
            errors.append(f"{path.name}: source receipt fixture is unavailable")
            continue
        receipt = copy.deepcopy(receipt)
        if receipt.get("locale") != value.get("locale"):
            receipt["locale"] = value.get("locale")
        for error in validate_checkpoint_for_test(value, receipt, as_of=as_of):
            errors.append(f"{path.name}: {error}")
    return sorted(set(errors))
