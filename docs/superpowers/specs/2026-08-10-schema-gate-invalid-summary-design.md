# Reject invalid schema-harness summaries end-to-end

## Goal

Prove the static gate rejects a successful subprocess whose unittest summary is
missing or has zero tests, rather than testing only the parser helper.

## Design

Add a focused integration test that patches the existing harness runner with a
simulated code-0 result and malformed/zero summary, invokes the gate's bounded
summary branch, and asserts exit/error behavior. No extra subprocess is spawned;
normal pass and timeout paths remain unchanged.

## Verification

The test covers invalid summary rejection and the existing parser, static gate,
harness, and full gate remain green.
