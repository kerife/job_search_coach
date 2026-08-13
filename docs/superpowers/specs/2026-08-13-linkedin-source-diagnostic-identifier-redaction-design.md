# LinkedIn source diagnostic identifier redaction

## Problem

Source-catalog, parser, and report validation errors interpolate untrusted values directly:
the stale/unreachable fallback message prints `source_id`, and the official
URL registration message prints `source_category`. A malformed local fixture
can therefore leak a path, credential-shaped text, or control characters into
API errors and CLI stderr. Unknown score dimensions, unexpected copy headings,
generic priority codes, and duplicate evidence/fact/claim diagnostics have the
same exposure pattern.

## Design

Use the existing `_safe_diagnostic_identifier()` helper at all affected
interpolation sites. Canonical synthetic source IDs and enum categories remain readable;
path-like or sensitive values become `<redacted-value>`. No source resolution,
enum validation, or URL registry behavior changes.

## Success criteria

- API and CLI diagnostics never contain path-like `source_id` or
  `source_category` sentinels.
- The stale fallback and unregistered-category messages remain present with a
  redacted marker.
- Parser and duplicate-reference diagnostics retain their message shape with
  redacted untrusted values.
- Valid source fixtures and all LinkedIn/plugin/release gates remain green.
