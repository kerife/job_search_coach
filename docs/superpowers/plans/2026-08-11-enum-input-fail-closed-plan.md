# Enum Input Fail-Closed Plan

1. Add focused mutations for object/list enum values to the existing validator
   test modules and run them to capture RED failures.
2. Add explicit string-type guards before enum membership checks in the five
   validators, preserving current diagnostics and control flow.
3. Run focused validator/schema/render tests plus `git diff --check` and review
   the diff for scope, privacy, and schema stability.
4. Refresh allowlisted provenance, run all pre-cachebuster gates, consume the
   cachebuster exactly once, rerun gates, publish, install, and verify canonical
   source/cache equivalence.
