# Outcome warning redaction for LinkedIn intervention identifiers

## Context

The outcomes summary accepts CSV data supplied by the caller. When an in-window
row is marked `source=linkedin_outreach` and its intervention identifier starts
with `LI-`, the summary currently copies that identifier into a successful JSON
warning. A path-like or private identifier can therefore escape through normal
stdout even though the summary is otherwise descriptive-only.

## Decision

Keep the LinkedIn measurement warning and its count-independent semantics, but
make its text fixed: `LinkedIn outreach measurement events observed; descriptive
only, no causal attribution`. Do not expose identifiers, add a new schema, or
change rates, filtering, exit codes, or ordinary intervention warnings.

## Verification

Add API/CLI-facing behavior tests using Unix, drive-letter, and UNC-shaped
identifiers. Each must remain a valid summary, omit the sentinel from stdout and
stderr, and retain the fixed warning. Update deterministic fixture expectations
and run the full outcomes suite, plugin suite, static/privacy checks, cache
parity, and release validation after the version bump.

No browser capture or external LinkedIn access is required: this increment is a
diagnostic-output boundary, not a UI or network behavior change.
