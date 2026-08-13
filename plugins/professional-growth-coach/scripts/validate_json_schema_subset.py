"""Dependency-free validator for the JSON Schema subset used by this plugin."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Mapping

from private_prose_safety import safe_diagnostic_field_name


MAX_SCHEMA_EVALUATIONS = 4_096
SCHEMA_EVALUATION_LIMIT_ERROR = "schema validation exceeds safe evaluation limit"
SCHEMA_KEYWORD_INVALID_ERROR = "schema keyword is invalid"
SCHEMA_PATTERN_INVALID_ERROR = "schema pattern is invalid"
SCHEMA_PATTERN_COMPLEXITY_ERROR = "schema pattern exceeds safe complexity limit"
_NESTED_UNBOUNDED_QUANTIFIER = re.compile(
    r"\((?:[^()\\]|\\.)*(?<!\\[A-Za-z])[+*]\s*\)[+*?]"
)


def _keyword_shapes_valid(schema: Mapping[str, object]) -> bool:
    if "properties" in schema and not isinstance(schema["properties"], Mapping):
        return False
    for keyword in ("required", "enum"):
        if keyword in schema and not isinstance(schema[keyword], list):
            return False
    for keyword in ("minimum", "maximum"):
        value = schema.get(keyword)
        if value is not None and (
            not isinstance(value, (int, float)) or isinstance(value, bool)
        ):
            return False
    for keyword in ("minLength", "maxLength", "minItems", "maxItems"):
        value = schema.get(keyword)
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value < 0
        ):
            return False
    if "pattern" in schema and not isinstance(schema["pattern"], str):
        return False
    return True


def _pattern_error(pattern: str) -> str | None:
    if _NESTED_UNBOUNDED_QUANTIFIER.search(pattern):
        return SCHEMA_PATTERN_COMPLEXITY_ERROR
    try:
        re.compile(pattern)
    except re.error:
        return SCHEMA_PATTERN_INVALID_ERROR
    return None


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


def _json_equal(
    left: object, right: object, seen: set[tuple[int, int]] | None = None
) -> bool:
    """Compare JSON values without Python's bool/int equality quirk."""
    if seen is None:
        seen = set()
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list) and isinstance(right, list):
        pair = (id(left), id(right))
        if pair in seen:
            return True
        seen.add(pair)
        return len(left) == len(right) and all(
            _json_equal(item, other, seen) for item, other in zip(left, right)
        )
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        pair = (id(left), id(right))
        if pair in seen:
            return True
        seen.add(pair)
        return set(left) == set(right) and all(
            _json_equal(left[key], right[key], seen) for key in left
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
    active_ref_targets: set[int] | None = None,
) -> list[str]:
    if budget is None:
        budget = [MAX_SCHEMA_EVALUATIONS]
    if active_ref_targets is None:
        active_ref_targets = set()
    if not isinstance(schema, Mapping):
        return ["schema branch is invalid"]
    if not _keyword_shapes_valid(schema):
        return [SCHEMA_KEYWORD_INVALID_ERROR]
    if "pattern" in schema:
        pattern_error = _pattern_error(schema["pattern"])
        if pattern_error is not None:
            return [pattern_error]
    for combinator in ("oneOf", "anyOf", "allOf"):
        branches = schema.get(combinator)
        if branches is not None and (
            not isinstance(branches, list)
            or any(not isinstance(branch, Mapping) for branch in branches)
        ):
            return ["schema branch is invalid"]
    for branch_name in ("if", "then", "else", "not"):
        if branch_name in schema and not isinstance(schema[branch_name], Mapping):
            return ["schema branch is invalid"]
    if budget[0] <= 0:
        return [SCHEMA_EVALUATION_LIMIT_ERROR]
    budget[0] -= 1
    errors: list[str] = []
    if "$ref" in schema:
        reference = schema["$ref"]
        if not isinstance(reference, str):
            return ["schema reference is invalid"]
        try:
            target = _pointer(root, reference)
        except (KeyError, TypeError, AttributeError, IndexError):
            return ["schema reference is invalid"]
        if not isinstance(target, Mapping):
            return ["schema reference is invalid"]
        target_identity = id(target)
        if target_identity in active_ref_targets:
            return [SCHEMA_EVALUATION_LIMIT_ERROR]
        active_ref_targets.add(target_identity)
        try:
            return _validate(
                value, target, root, path, collect=collect, budget=budget,
                active_ref_targets=active_ref_targets,
            )
        finally:
            active_ref_targets.remove(target_identity)
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
                f"{path}: unsupported field {safe_diagnostic_field_name(str(key))}"
                for key in value
                if key not in properties
            )
        for key in schema.get("required", []):
            if key not in value:
                errors.append(
                    f"{path}: missing required field {safe_diagnostic_field_name(str(key))}"
                )
        for key, child_schema in properties.items():
            if key in value:
                safe_key = safe_diagnostic_field_name(str(key))
                errors.extend(
                    _validate(
                        value[key], child_schema, root, f"{path}.{safe_key}",
                        budget=budget, active_ref_targets=active_ref_targets,
                    )
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
                    _validate(
                        child, schema["items"], root, f"{path}[{index}]",
                        budget=budget, active_ref_targets=active_ref_targets,
                    )
                )
        if "contains" in schema and not any(
            not _validate(
                child, schema["contains"], root, f"{path}[{index}]",
                budget=budget, active_ref_targets=active_ref_targets,
            )
            for index, child in enumerate(value)
        ):
            errors.append(f"{path}: contains mismatch")
    for branch in schema.get("allOf", []):
        errors.extend(
            _validate(value, branch, root, path, budget=budget,
                      active_ref_targets=active_ref_targets)
        )
    if "oneOf" in schema:
        matches = sum(
            not _validate(
                value, branch, root, path, budget=budget,
                active_ref_targets=active_ref_targets,
            )
            for branch in schema["oneOf"]
        )
        if matches != 1:
            errors.append(f"{path}: oneOf mismatch")
    if "anyOf" in schema:
        if not any(
            not _validate(
                value, branch, root, path, budget=budget,
                active_ref_targets=active_ref_targets,
            )
            for branch in schema["anyOf"]
        ):
            errors.append(f"{path}: anyOf mismatch")
    if "not" in schema and not _validate(
        value, schema["not"], root, path, budget=budget,
        active_ref_targets=active_ref_targets,
    ):
        errors.append(f"{path}: not mismatch")
    if "if" in schema:
        condition_matches = (
            _validate(
                value, schema["if"], root, path, collect=False,
                budget=budget, active_ref_targets=active_ref_targets,
            ) == []
        )
        branch = schema.get("then", {}) if condition_matches else schema.get("else", {})
        if branch:
            errors.extend(
                _validate(value, branch, root, path, budget=budget,
                          active_ref_targets=active_ref_targets)
            )
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
