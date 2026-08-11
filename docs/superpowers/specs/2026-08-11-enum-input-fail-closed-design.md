# Enum Input Fail-Closed Design

## Goal

Make every private-artifact validator reject malformed JSON enum inputs
deterministically instead of raising `TypeError` when an object or array is
provided where a string enum is required.

## Scope

Update only the five Python validators for conversion outcomes, follow-through
checkpoints, triage, recruiter practice, and executive dossiers. Add focused
regressions for object/list values on the locale (and locale-family) enum
fields. Preserve existing error text, schemas, renderers, and valid fixtures.

## Contract

An enum field is valid only when its value is a string in the existing allowed
set. Missing/non-string/unknown values produce the existing `... has invalid
value` diagnostic and validation continues without an exception or input echo.

## Non-goals

No schema redesign, new enum values, shared abstraction, CLI format change, or
normalization of unrelated fields.

## Acceptance

- RED tests reproduce the current `TypeError` for `{}` and `[]`.
- GREEN tests show all five validators return bounded errors for those values.
- Canonical valid fixtures remain valid and existing error messages remain
  stable.
- Static, focused, full, privacy, release, and marketplace install gates pass.
