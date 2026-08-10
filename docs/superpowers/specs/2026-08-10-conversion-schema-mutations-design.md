# Cover conversion schema mutations

## Goal

Ensure the dependency-free private schema harness detects regressions in the
conversion outcome schema, not only follow-through.

## Design

Extend the existing schema-conformance test with conversion mutations derived
from a valid fixture: mismatched event/action, impossible ISO date, and an
unsupported top-level field. Keep the harness and runtime validators unchanged;
the test should assert each mutation produces at least one schema error.

## Verification

Both private artifact fixture suites remain valid, all follow-through mutations
remain rejected, and the static gate still runs the same two harness tests with
its timeout and diagnostics unchanged.
