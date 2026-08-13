# Schema `$ref` cycle guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline execution in this session).

**Goal:** Bound recursive `$ref` schema evaluation and convert malformed references into stable validator diagnostics.

**Architecture:** Add an active-reference set to the existing recursive `_validate` helper. Resolve pointers through `_pointer` under a narrow exception boundary, preserving the current evaluation budget and all valid-schema behavior.

**Tech Stack:** Python 3, `unittest`, dependency-free JSON-schema subset validator.

## Global Constraints

- No changes to canonical schema files or valid payload semantics.
- Keep `SCHEMA_EVALUATION_LIMIT_ERROR` as the fixed cycle diagnostic.
- Use a fixed non-echoing message for malformed references.
- Verify RED before production changes and refresh cache/provenance before release.

### Task 1: RED coverage

**Files:**
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

- [x] Add a self-referential `$defs`/`$ref` test asserting the evaluation-limit error.
- [ ] Add a malformed/missing `$ref` test asserting a stable `schema reference is invalid` diagnostic.
- [x] Run the cycle test and observe the current `RecursionError`.

### Task 2: GREEN guard

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_json_schema_subset.py`

- [ ] Pass an active-reference set through recursive `_validate` calls.
- [ ] Detect an active target before recursing and return the fixed limit error.
- [ ] Remove the target in `finally` so sibling reuse remains valid.
- [ ] Catch pointer lookup/type failures and return `schema reference is invalid`.
- [ ] Run schema conformance and handoff tests.

### Task 3: Publish and verify

- [ ] Bump the plugin version and install it from the local marketplace.
- [ ] Rebind final provenance and installed smoke metadata.
- [ ] Run plugin, static, privacy, release, and source/cache parity gates.
- [ ] Push the verified release and confirm remote HEAD.

