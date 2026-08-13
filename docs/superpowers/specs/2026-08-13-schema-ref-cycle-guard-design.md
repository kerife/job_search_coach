# Schema `$ref` cycle guard

## Problem

The public `validate_schema_instance` helper already bounds combinator
evaluation, but a JSON-compatible schema whose `$ref` points back to itself
recurses until Python raises `RecursionError`. A missing or non-object `$ref`
target can likewise raise `KeyError` or a type error instead of returning the
validator's normal list of diagnostics.

## Design

Track reference targets active on the current validation path. A target already
active returns the existing fixed evaluation-limit diagnostic; the target is
removed when that recursive branch finishes, so legitimate reuse in sibling
branches remains valid. Resolve each pointer inside a narrow error boundary and
return a fixed `schema reference is invalid` diagnostic for missing, malformed,
or non-object targets. Existing value/schema validation, bounded branch
evaluation, and canonical plugin schemas remain unchanged.

## Success criteria

- Self-referential and mutually recursive JSON schemas return a bounded error,
  never `RecursionError`.
- Missing and non-object `$ref` targets return a deterministic validation list,
  never `KeyError`/`TypeError`.
- Existing schema conformance and handoff tests remain green.
- Source/cache parity and release provenance are refreshed before publishing.

