# Schema combinator branch-shape guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline execution in this session).

**Goal:** Convert malformed non-object schema branches into stable diagnostics instead of uncaught exceptions.

**Architecture:** Guard the existing recursive `_validate` entry point with a Mapping check. Parameterized tests exercise one malformed branch through each supported combinator family.

**Tech Stack:** Python 3 and `unittest`.

## Global Constraints

- Preserve valid JSON-schema subset semantics.
- Use the fixed non-echoing diagnostic `schema branch is invalid`.
- Do not alter canonical schema files or input limits.
- Verify RED→GREEN and refresh cache/provenance before release.

### Task 1: RED

**Files:** `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

- [ ] Add a parameterized test for `oneOf`, `anyOf`, `allOf`, `if`, and `not` with a non-object branch.
- [ ] Assert the call returns `schema branch is invalid` rather than raising.
- [ ] Run the focused test and observe the current exception.

### Task 2: GREEN

**Files:** `plugins/professional-growth-coach/scripts/validate_json_schema_subset.py`

- [ ] Add the Mapping guard at `_validate` entry.
- [ ] Run focused, schema, handoff, and full plugin tests.
- [ ] Run static/privacy/release checks.

### Task 3: Release

- [ ] Bump and install the plugin.
- [ ] Rebind provenance and installed smoke metadata.
- [ ] Verify source/cache parity and push the release.

