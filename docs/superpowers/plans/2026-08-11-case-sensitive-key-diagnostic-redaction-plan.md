# Case Sensitive-Key Diagnostic Redaction Implementation Plan

> **For agentic workers:** Use the test-driven-development skill. Do not bump,
> install, or publish until a later release cycle explicitly authorizes it.

**Goal:** Reject sensitive or credential-shaped unsupported keys without
echoing their caller-supplied material in case-validator diagnostics.

**Architecture:** Add one local safe-path-key helper. Preserve canonical
sensitive names and ordinary unsupported-field names; redact only dynamic
segments recognized by the existing classifiers. Use the helper consistently
where recursive validator paths are constructed.

## Task 1: Add the failing regression matrix

- [x] Add a table-driven test covering top-level, target, and record scopes
  with email-, contact-, and token-shaped key sentinels.
- [x] Run the focused test and observe the expected failure because current
  errors contain each sentinel.

## Task 2: Implement the minimal safe-path behavior

- [x] Add `_safe_path_key` to preserve canonical and ordinary names while
  mapping sensitive dynamic names to `<redacted-key>`.
- [x] Use it in closed-mapping diagnostics and all recursive path builders.
- [x] Keep candidate binding, schema validation, consent behavior, and error
  ordering unchanged.

## Task 3: Verify and document

- [x] Run the focused regression test.
- [x] Run the complete `tests.test_validate_case` suite.
- [ ] Run broader repository/static/privacy gates in the parent release cycle.
- [ ] Commit this bounded functional increment; do not bump/install here.
