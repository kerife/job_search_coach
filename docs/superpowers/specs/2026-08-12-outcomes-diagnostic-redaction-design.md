# Outcome summary diagnostic redaction

## Context

The outcome-summary CLI correctly isolates candidates, but its unknown-candidate
error currently interpolates the requested identifier. A caller-supplied path
or private identifier can therefore be copied into stderr and automation logs,
contrary to the career-outcomes contract that diagnostics must not echo
candidate identifiers or input paths.

## Decision

Replace the unknown-candidate error with the fixed message
`candidate_id not found`. Keep exit code `2`, empty stdout, JSON error output,
candidate filtering, and all valid summary behavior unchanged.

This is a one-sink diagnostic-only fix. Date/boolean and other malformed-row
diagnostics remain separate follow-up work so this cycle does not alter their
existing error grammar.

## Verification

Tests will assert ordinary missing-candidate behavior and a path-shaped
candidate identifier. The latter must be absent from both stdout and stderr,
while stderr remains valid deterministic JSON and stdout remains empty.

No schema, CSV shape, renderer, persistence, or external action changes are in
scope.
