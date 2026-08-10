# Conversion outcome loader hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden conversion-outcome JSON ingestion against symlink redirection and resource-amplifying nesting.

**Architecture:** Keep the current validator/renderer APIs and error model. Add checks at `load_outcome`, then exercise them through contract and renderer tests; no schema or routing changes.

**Tech Stack:** Python 3 standard library, unittest, JSON loader.

## Global Constraints

- Reject symlink input paths before reading.
- Preserve duplicate-key, size, type, and privacy validation behavior.
- Enforce a fixed maximum JSON nesting depth and fail closed.
- Keep valid EN/ES fixtures and output mode `0600` unchanged.

### Task 1: Harden the loader

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_private_recruiter_conversion_outcome.py`
- Modify: `plugins/job-search-coach/tests/test_private_recruiter_conversion_outcome.py`
- Modify: `plugins/job-search-coach/tests/test_render_private_recruiter_conversion_outcome.py`

- [ ] **Step 1: Add failing symlink/depth tests**

  Create a temporary symlink to a valid fixture and a JSON document nested beyond the chosen limit; assert `load_outcome` raises its existing load error and renderer raises its existing validation/load error.

- [ ] **Step 2: Run focused tests and verify RED**

  Run `python3 -B -m unittest plugins/job-search-coach/tests/test_private_recruiter_conversion_outcome.py plugins/job-search-coach/tests/test_render_private_recruiter_conversion_outcome.py -q`; expect the new cases to fail before implementation.

- [ ] **Step 3: Implement minimal boundary checks**

  Reject `Path.is_symlink()` before `read_text`; parse with the existing duplicate-key hook while tracking container depth and raise the existing loader error when the fixed limit is exceeded.

- [ ] **Step 4: Verify GREEN**

  Re-run the focused tests, `python3 -B plugins/job-search-coach/tests/run_static_checks.py`, and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit the validator, tests, spec, and plan as `fix: harden conversion outcome ingestion`.
