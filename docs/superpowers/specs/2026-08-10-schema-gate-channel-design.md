# Align schema-gate summary channel handling

## Goal

Keep the full integration assertion aligned with the static gate's accepted
stdout/stderr summary behavior.

## Design

Parse `result.stderr or result.stdout` in the full-gate assertion, matching the
static runner's bounded formatter. Add a focused test using a synthetic stdout
summary and preserve stderr precedence when both are present. No runtime or
release behavior changes.

## Verification

Current and stdout-only unittest summaries pass; malformed summaries remain
rejected by the existing parser tests.
