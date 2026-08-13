# Schema pattern error guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline execution in this session).

**Goal:** Convert invalid schema regex syntax into a deterministic validator diagnostic.

**Architecture:** Catch only `re.error` around the existing pattern search and return the fixed `schema pattern is invalid` message.

**Tech Stack:** Python 3, `unittest`, standard-library `re`.

## Global Constraints

- Preserve valid pattern behavior and current mismatch text.
- Do not change schemas, regex flags, or input limits.
- Verify RED→GREEN before release bump/install.

### Task 1: RED

**File:** `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

- [ ] Add invalid patterns `[` , `(?'`, and `\\K` and assert `schema pattern is invalid`.
- [ ] Run the focused test and observe `re.error`.

### Task 2: GREEN

**File:** `plugins/professional-growth-coach/scripts/validate_json_schema_subset.py`

- [ ] Catch `re.error` around `re.search` and append the fixed diagnostic.
- [ ] Run schema and plugin suites plus static/privacy checks.

### Task 3: Release

- [ ] Bump/install, rebind provenance, verify parity, and push.

