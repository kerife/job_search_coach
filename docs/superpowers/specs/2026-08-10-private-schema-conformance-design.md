# Private schema conformance harness

## Goal

Exercise the closed Draft 2020-12 subset used by the private conversion and
follow-through schemas without adding a runtime dependency.

## Design

Add a test-only, small stdlib harness that resolves local `$ref` definitions and
checks the schema keywords used by these artifacts: object closure, required and
properties, const/enum, string pattern/format date, and the existing `if`/`then`
and `allOf` conditionals. It returns deterministic error lists rather than
changing production validators.

Use it against every valid EN/ES fixture plus mutations for impossible dates and
wrong action/event mappings. Keep the harness scoped to tests and document that
it is not a general JSON Schema implementation; the Python validators remain
authoritative for cross-file and chronology checks.

## Verification

All valid fixtures pass the harness; each targeted mutation fails; existing
runtime, renderer, static, and privacy suites remain unchanged and green.
