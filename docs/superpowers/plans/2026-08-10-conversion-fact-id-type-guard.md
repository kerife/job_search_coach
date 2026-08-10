# Conversion fact ID type guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make malformed conversion outcome fact ID arrays fail closed without exceptions.

**Architecture:** Keep the existing validator rule and renderer gate. Reorder type validation before `set()` uniqueness and add mutation tests for objects/mixed types.

**Tech Stack:** Python 3 standard library, unittest.

## Global Constraints

- `fact_ids` must remain a list of strings with the existing bounded ID grammar.
- Validation must return errors, never leak `TypeError` or traceback.
- Valid output and all privacy/action boundaries remain unchanged.

### Task 1: Guard fact ID types

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_private_recruiter_conversion_outcome.py`
- Modify: `plugins/job-search-coach/tests/test_private_recruiter_conversion_outcome.py`
- Modify: `plugins/job-search-coach/tests/test_render_private_recruiter_conversion_outcome.py`

- [ ] **Step 1: Add failing malformed-type tests**

  Mutate a valid fixture with `fact_ids=[{}]` and `fact_ids=["F-101", 7]`; assert validation returns errors and renderer raises its existing validation error rather than `TypeError`.

- [ ] **Step 2: Run focused tests and verify RED**

  Run the two conversion validator/renderer test modules; expect a `TypeError` before the fix.

- [ ] **Step 3: Implement minimal ordering fix**

  Check list shape and `all(isinstance(value, str) ...)` before `len(set(...))`; only construct the set after type safety is established.

- [ ] **Step 4: Verify GREEN**

  Run focused tests, static checks, privacy checks, and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit validator, tests, spec, and plan as `fix: guard conversion fact id types`.
