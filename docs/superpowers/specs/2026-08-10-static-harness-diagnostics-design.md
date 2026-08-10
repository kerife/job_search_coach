# Bound static schema-harness diagnostics

## Goal

Make failures from the private schema conformance subprocess actionable without
leaking fixture content or changing the static gate's pass behavior.

## Design

When the harness exits non-zero, report the harness path and at most its first
and last non-empty output lines, with a deterministic marker for an omitted
middle. Keep output bounded and source-only; do not include full stdout/stderr.
The existing successful marker and exit code remain unchanged.

## Verification

Add a focused unit test around the summary helper with empty, one-line, and
multi-line output. Assert the static gate retains the current pass output and
that failure summaries contain path/context without raw fixture data.
