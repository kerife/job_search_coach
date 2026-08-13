# Schema keyword shape guard

## Problem

`validate_schema_instance` safely handles malformed combinator branches and
`$ref` cycles, but it still assumes that several ordinary schema keywords have
the expected JSON types. Caller-controlled schemas with `properties: null`,
`required: null`, `enum: null`, or non-numeric bounds raise Python exceptions
instead of returning validator diagnostics.

## Design

Add a narrow keyword-shape preflight at the recursive `_validate` boundary. It
checks only the types required by operations in this subset: mappings for
`properties`, arrays for `required`/`enum`, numeric values for numeric bounds,
and non-negative integers for item/length bounds. Invalid shapes return the
fixed, non-echoing `schema keyword is invalid`; valid schemas retain existing
validation behavior and evaluation budgets.

## Success criteria

- Malformed keyword shapes return a list containing `schema keyword is invalid`.
- No `TypeError`/`AttributeError` escapes for the covered JSON inputs.
- Canonical schema conformance, handoff, plugin, static, privacy, release, and
  source/cache parity gates remain green before publishing.

