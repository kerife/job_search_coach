# Schema pattern error guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline execution in this session).

**Goal:** Convert invalid or obviously exponential schema regex forms into deterministic validator diagnostics.

**Architecture:** Preflight regex syntax and reject nested unbounded quantifiers before the existing search; preserve finite quantifiers and normal mismatch behavior.

**Tech Stack:** Python 3, `unittest`, standard-library `re`.

## Global Constraints

- Preserve valid finite-quantifier pattern behavior and current mismatch text.
- Do not change schemas, regex flags, or input limits.
- Verify RED→GREEN before release bump/install.

### Task 1: RED

**File:** `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

- [ ] Add invalid patterns `[` , `(?'`, and `\\K` and assert `schema pattern is invalid`.
- [ ] Add `(a+)+$` with adversarial input and assert `schema pattern exceeds safe complexity limit`.
- [ ] Run the focused tests and observe `re.error`/slow mismatch before production changes.

### Task 2: GREEN

**File:** `plugins/professional-growth-coach/scripts/validate_json_schema_subset.py`

- [ ] Preflight `re.compile`, catch `re.error`, and detect nested unbounded quantifiers.
- [ ] Return the two fixed diagnostics without executing unsafe patterns.
- [ ] Run schema and plugin suites plus static/privacy checks.

### Task 3: Release

- [ ] Bump/install, rebind provenance, verify parity, and push.
