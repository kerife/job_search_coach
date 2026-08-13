# Schema keyword shape guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline execution in this session).

**Goal:** Return stable diagnostics for malformed ordinary schema keyword types instead of uncaught exceptions.

**Architecture:** Extend the existing `_validate` preflight beside the `$ref` and combinator guards. Keep all canonical schema semantics and evaluation limits unchanged.

**Tech Stack:** Python 3, `unittest`, dependency-free schema validator.

## Global Constraints

- Fixed diagnostic: `schema keyword is invalid`.
- Preserve valid keyword semantics and existing error text.
- Do not change schema files or plugin input formats.
- Verify RED→GREEN before version bump and installation.

### Task 1: RED

**File:** `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

- [ ] Add parameterized cases for `properties`, `required`, `enum`, `minimum`, and `minItems` malformed shapes.
- [ ] Assert each returns `schema keyword is invalid`.
- [ ] Run the focused test and observe the current exception.

### Task 2: GREEN

**File:** `plugins/professional-growth-coach/scripts/validate_json_schema_subset.py`

- [ ] Add the minimal type checks at `_validate` entry.
- [ ] Run schema, handoff, and full plugin suites.
- [ ] Run static/privacy/release checks.

### Task 3: Release

- [ ] Bump and install the plugin.
- [ ] Rebind provenance/installed smoke metadata.
- [ ] Verify parity and push the release.

