# Make schema-gate test discovery extensible

## Goal

Prevent the full integration gate from becoming brittle when the private schema
harness gains legitimate tests.

## Design

Replace the exact `Ran 3 tests` assertion with a small parser that accepts the
standard unittest summary `Ran N test(s)` only when `N` is a positive integer.
The subprocess must still exit zero and malformed or missing summaries fail the
gate. No harness, runtime, or static-gate behavior changes.

## Verification

Test the current summary, a larger count, and malformed/zero-count summaries;
the full gate remains green while future harness tests require no integration
test edit.
