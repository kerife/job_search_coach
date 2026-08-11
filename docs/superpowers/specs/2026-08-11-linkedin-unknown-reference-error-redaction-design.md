# Redact unknown evidence references in LinkedIn validation errors

## Context

The LinkedIn client-report validator rejects references that are not present in
the validated fact/evidence set, but several diagnostics interpolate the
unknown ID. Case, triage, and practice validators now keep these diagnostics
path-specific without echoing untrusted values. The LinkedIn module should use
the same privacy boundary.

## Design

Keep each existing path/row context and fixed reason (`unknown evidence` or
`unknown fact`), but omit the supplied reference from the diagnostic. Apply the
redaction to score rows, priorities, copy blocks, generic reference validation,
and duplicate/reference errors that currently interpolate IDs. Valid references
and all accepted output remain unchanged.

## Non-goals

No acceptance changes, schema/version changes, ID normalization, auto-repair,
renderer changes, or changes to unrelated human-readable labels.

## Acceptance

1. Unknown evidence/fact errors retain useful path/section/rank context.
2. Email, phone-like, URL, and local-path values supplied as unknown evidence
   or fact references never appear in validator errors. Identifier-token
   scanning and duplicate-ID diagnostics remain separate follow-up contracts.
3. Valid references and existing privacy/static/schema/release behavior remain
   unchanged.
