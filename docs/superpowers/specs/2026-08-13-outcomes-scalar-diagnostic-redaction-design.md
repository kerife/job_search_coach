# Outcomes scalar diagnostic redaction

## Context

The outcomes CLI accepts caller-controlled CSV and command-line values. Several
invalid-input branches still interpolate those values into JSON diagnostics:
date fields, boolean fields, duplicate application IDs, duplicate headers, and
window/as-of arguments. This conflicts with the career-outcomes contract that
diagnostics do not echo input paths or identifiers.

## Decision

Use stable messages without raw values while preserving field names, row
numbers, first-seen row context, validation order, exit codes, JSON shape, and
valid summaries. The increment covers the shared scalar diagnostic family only;
no schema, renderer, CSS, or external action behavior changes.

## Verification

Tests exercise Unix path, credential-like, and duplicate-header sentinels via
the CLI and assert they are absent from both output streams. Existing ordinary
malformed-input tests are updated to the stable messages. The outcomes suite,
full plugin suite, static/privacy/provenance gates, source-cache parity, and
official release validator must all pass after the cachebuster install.
