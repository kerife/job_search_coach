# Cover nonzero schema-harness diagnostics

## Goal

Lock down the static gate's diagnostics when the schema harness genuinely exits
non-zero, including multiline and empty output.

## Design

Add helper-level tests for a nonzero result with multiline stderr (only first
and last lines retained) and empty stdout/stderr (harness path retained). Assert
one deterministic error per result and no raw middle log content. Runtime code
and successful/timeout behavior remain unchanged.

## Verification

Focused full-plugin tests, static checks, schema harness, and diff checks stay
green; mutation of the diagnostic helper would fail the new assertions.
