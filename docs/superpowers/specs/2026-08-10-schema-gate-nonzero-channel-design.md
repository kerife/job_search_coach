# Select the useful channel for nonzero diagnostics

## Goal

Keep nonzero schema-harness diagnostics useful when stderr contains a warning
but stdout contains the actual failure.

## Design

Reuse the shared channel selector in `format_harness_failure`: choose a channel
with a unittest summary or, when no summary exists, the non-empty channel that
contains the substantive diagnostic. Preserve bounded first/last-line output,
harness path, and one-error behavior. No runtime schema changes.

## Verification

Test warning-in-stderr plus failure-in-stdout, both nonzero channels, and empty
output. Existing pass, timeout, invalid-summary, and static behavior remain
green.
