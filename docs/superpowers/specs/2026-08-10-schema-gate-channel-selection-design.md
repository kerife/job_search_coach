# Select the channel containing the unittest summary

## Goal

Avoid rejecting a valid schema harness when stderr contains a warning but stdout
contains the unittest summary.

## Design

Update the shared summary helper to prefer stderr only when it contains a valid
`Ran N test(s)` summary; otherwise select stdout when it contains one. If both
contain valid summaries, retain stderr precedence; if neither does, retain the
existing non-empty fallback for diagnostics. No runtime schema or harness
changes.

## Verification

Test warning+stdout-valid, both-valid, stderr-only, stdout-only, and malformed
channels. Static/full gates and timeout/error behavior remain green.
