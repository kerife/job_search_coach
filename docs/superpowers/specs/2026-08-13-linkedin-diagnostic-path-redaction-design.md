# LinkedIn diagnostic path redaction

## Problem

`validate_fixture_bundle()` recursively scans caller-controlled JSON values. Its
privacy diagnostics currently build mapping paths from raw keys, so a key such
as `/Users/PRIVATE_SENTINEL/profile.json` can be echoed in API errors and CLI
stderr even when the value is correctly rejected as a forbidden URL or local
path.

## Design

Reuse `_safe_diagnostic_field_name()` for every mapping-key segment while
`_scan_privacy()` constructs a diagnostic path. The helper recognizes Unix
absolute roots, drive-letter paths, and UNC paths in addition to existing
credential-like aliases. List indexes and ordinary synthetic field names remain
readable; path-like, credential-like, and control characters are redacted or
escaped by the helper. Canonical
`source_catalog[N].url` paths retain their existing source-URL exception.

## Success criteria

- API diagnostics never contain a caller-supplied absolute-path sentinel from a
  mapping key.
- CLI stderr never contains that sentinel and remains one diagnostic per line.
- Ordinary nested keys preserve useful path context.
- LinkedIn fixture tests, plugin tests, static/privacy checks, source-cache
  parity, installed smoke, and provenance all pass before publication.
