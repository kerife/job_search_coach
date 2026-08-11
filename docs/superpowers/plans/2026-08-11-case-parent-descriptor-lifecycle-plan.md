# Case Parent Descriptor Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close every provisional parent directory descriptor when case-input traversal fails.

**Architecture:** Keep `_open_case_parent` as the path-walking boundary. A descriptor returned by `os.open` remains provisional until `os.fstat` confirms a directory; only then does it replace the previously adopted descriptor. The public validator API and fixed CLI diagnostics remain unchanged.

**Tech Stack:** Python 3.14, `os.open`/`os.fstat`/`os.close`, `unittest`, existing plugin static and release scripts.

## Global Constraints

- Preserve `O_NOFOLLOW`, `O_DIRECTORY`, `/tmp` and `/var` trusted-alias compatibility.
- Preserve lexical `abspath` normalization and existing regular-file/size behavior.
- Do not echo paths, errno values, payloads, or external targets.

---

### Task 1: Prove provisional descriptor ownership with a failing test

**Files:**
- Modify: `tests/test_validate_case.py`
- Reference: `plugins/professional-growth-coach/scripts/validate_case.py:_open_case_parent`

**Interfaces:**
- Consumes: `_open_case_parent(path, nofollow, directory_flag)`.
- Produces: a deterministic regression test that records descriptors opened and closed when `os.fstat` fails.

- [ ] **Step 1: Write the failing test**

Create a temporary parent directory and case path. Wrap the module's `os.open`
and `os.close` to record returned/closed descriptors, and wrap `os.fstat` to
raise `OSError("synthetic fstat failure")` for the first parent validation.
Call `_open_case_parent` with the platform flags and assert the error plus
`set(opened) == set(closed)` after restoring wrappers.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_validate_case.ValidateCaseTests.test_open_case_parent_closes_provisional_descriptor -v
```

Expected: FAIL because the child descriptor opened for the parent is absent
from the recorded close set.

### Task 2: Close provisional descriptors minimally

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_case.py:_open_case_parent`
- Test: `tests/test_validate_case.py`

**Interfaces:**
- Consumes: the failing ownership test from Task 1.
- Produces: unchanged `_open_case_parent` behavior with deterministic cleanup.

- [ ] **Step 1: Implement the smallest cleanup change**

After `next_descriptor = os.open(...)`, validate it in a `try` block. On any
`fstat` or directory-type failure, close `next_descriptor` before re-raising.
Only after validation succeeds should the function close the previously adopted
`descriptor` and assign `descriptor = next_descriptor`.

- [ ] **Step 2: Run focused GREEN tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_validate_case.ValidateCaseTests.test_open_case_parent_closes_provisional_descriptor tests.test_validate_case -q
```

Expected: the new test and the complete case-validator class pass.

- [ ] **Step 3: Run integration gates**

Run the plugin suite, root privacy/structure/asset-boundary tests, static
checks, and `scripts/run_release_validation.sh`; all must exit zero before a
release bump.

- [ ] **Step 4: Publish and verify**

Run the cachebuster exactly once, install the canonical plugin, compare the
107-file source/cache inventory and normalized hash, refresh the synthetic
attestation/provenance, and run the five installed renderer/validator smokes.

- [ ] **Step 5: Commit each tested boundary**

Use focused commits for the RED/GREEN implementation and release metadata;
finish with a clean `git status`, `git diff --check`, and provenance/static
verification.
