"""Dependency-free validator for the JSON Schema subset used by this plugin."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Mapping


MAX_SCHEMA_EVALUATIONS = 4_096
SCHEMA_EVALUATION_LIMIT_ERROR = "schema validation exceeds safe evaluation limit"


def _pointer(root: Mapping[str, object], reference: str) -> Mapping[str, object]:
    value: object = root
    for part in reference.removeprefix("#/").split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]  # type: ignore[index]
    return value  # type: ignore[return-value]


def _type_ok(value: object, expected: object) -> bool:
    if isinstance(expected, list):
        return any(_type_ok(value, option) for option in expected)
    if not isinstance(expected, str):
        return True
    return {
        "object": isinstance(value, Mapping),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "null": value is None,
    }.get(expected, True)


def _json_equal(left: object, right: object) -> bool:
    """Compare JSON values without Python's bool/int equality quirk."""
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _json_equal(item, other) for item, other in zip(left, right)
        )
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return set(left) == set(right) and all(
            _json_equal(left[key], right[key]) for key in left
        )
    return left == right


def _validate(
    value: object,
    schema: Mapping[str, object],
    root: Mapping[str, object],
    path: str,
    *,
    collect: bool = True,
    budget: list[int] | None = None,
) -> list[str]:
    if budget is None:
        budget = [MAX_SCHEMA_EVALUATIONS]
    if budget[0] <= 0:
        return [SCHEMA_EVALUATION_LIMIT_ERROR]
    budget[0] -= 1
    errors: list[str] = []
    if "$ref" in schema:
        return _validate(
            value,
            _pointer(root, str(schema["$ref"])),
            root,
            path,
            collect=collect,
            budget=budget,
        )
    if "type" in schema and not _type_ok(value, schema["type"]):
        return [f"{path}: type mismatch"]
    if "const" in schema and not _json_equal(value, schema["const"]):
        errors.append(f"{path}: const mismatch")
    if "enum" in schema and not any(
        _json_equal(value, option) for option in schema["enum"]
    ):
        errors.append(f"{path}: enum mismatch")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: number below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: number above maximum")
    if "pattern" in schema and isinstance(value, str):
        if re.search(str(schema["pattern"]), value) is None:
            errors.append(f"{path}: pattern mismatch")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: string too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: string too long")
        if schema.get("format") == "date":
            try:
                dt.date.fromisoformat(value)
            except ValueError:
                errors.append(f"{path}: invalid date format")
    if isinstance(value, Mapping):
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            errors.extend(
                f"{path}: unsupported field {key}" for key in value if key not in properties
            )
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required field {key}")
        for key, child_schema in properties.items():
            if key in value:
                errors.extend(
                    _validate(value[key], child_schema, root, f"{path}.{key}", budget=budget)
                )
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: too many items")
        if schema.get("uniqueItems") and len({repr(item) for item in value}) != len(value):
            errors.append(f"{path}: duplicate items")
        if "items" in schema:
            for index, child in enumerate(value):
                errors.extend(
                    _validate(child, schema["items"], root, f"{path}[{index}]", budget=budget)
                )
        if "contains" in schema and not any(
            not _validate(
                child, schema["contains"], root, f"{path}[{index}]", budget=budget
            )
            for index, child in enumerate(value)
        ):
            errors.append(f"{path}: contains mismatch")
    for branch in schema.get("allOf", []):
        errors.extend(_validate(value, branch, root, path, budget=budget))
    if "oneOf" in schema:
        matches = sum(
            not _validate(value, branch, root, path, budget=budget)
            for branch in schema["oneOf"]
        )
        if matches != 1:
            errors.append(f"{path}: oneOf mismatch")
    if "anyOf" in schema:
        if not any(
            not _validate(value, branch, root, path, budget=budget)
            for branch in schema["anyOf"]
        ):
            errors.append(f"{path}: anyOf mismatch")
    if "not" in schema and not _validate(value, schema["not"], root, path, budget=budget):
        errors.append(f"{path}: not mismatch")
    if "if" in schema:
        condition_matches = (
            _validate(value, schema["if"], root, path, collect=False, budget=budget) == []
        )
        branch = schema.get("then", {}) if condition_matches else schema.get("else", {})
        if branch:
            errors.extend(_validate(value, branch, root, path, budget=budget))
    return errors


def validate_schema_instance(
    value: object, schema: Mapping[str, object]
) -> list[str]:
    """Return bounded schema errors for the supported keyword subset."""
    budget = [MAX_SCHEMA_EVALUATIONS]
    errors = _validate(value, schema, schema, "$", budget=budget)
    if budget[0] <= 0:
        errors.append(SCHEMA_EVALUATION_LIMIT_ERROR)
    return sorted(set(errors))
