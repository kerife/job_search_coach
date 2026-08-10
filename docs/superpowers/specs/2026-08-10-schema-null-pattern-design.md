# Schema subset nullable-pattern design

## Goal

Make the dependency-free JSON Schema subset checker conform to JSON Schema's
conditional `pattern` behavior for nullable fields.

## Problem

The checker currently reports a type mismatch whenever a schema contains a
`pattern` and the instance is not a string. That is incorrect when the schema
already accepts a non-string branch, such as `type: ["string", "null"]`.
The executive dossier schema uses this shape for nullable capture references,
so valid dossiers fail the repository schema gate.

## Design

Keep type validation authoritative. After `_type_ok` accepts the instance,
apply `pattern` only when the instance is a string. A non-string value accepted
by a union (including `null`) skips the string-only pattern constraint. A
non-string value still fails the existing type check when the schema does not
accept its type. No schema changes, renderer changes, or coercion are needed.

## Acceptance

- `null` passes `{type: ["string", "null"], pattern: "^CAP-[0-9]{3}$"}`.
- A matching string passes and a non-matching string fails.
- A non-string value still fails a string-only schema with `pattern`.
- The canonical executive dossier fixture passes the subset checker.
- Existing plugin, root privacy, static, release, and installed-cache gates
  remain green.

## Safety

The checker does not normalize, coerce, or expose input values. The change is
limited to the conditional application of a string constraint after type
validation.
