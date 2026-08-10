# Practice reference type guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make malformed practice-session reference arrays fail closed without exceptions.

**Architecture:** Reorder the existing `_references` checks so `set()` is reached only for strings; add focused validator and renderer mutation tests.

**Tech Stack:** Python 3 standard library, unittest.

## Global Constraints

- Reference IDs retain the existing closed grammar and uniqueness rule.
- Invalid types return ordinary validation errors; no traceback/TypeError.
- Valid rendering, privacy, and action boundaries remain unchanged.

### Task 1: Guard practice references

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_recruiter_practice_session.py`
- Modify: focused practice validator/renderer tests

- [ ] **Step 1: Add failing malformed-reference tests**

  Mutate a valid session requirement and question with `fact_ids=[{}]` and mixed values; assert validation errors and renderer rejection without `TypeError`.

- [ ] **Step 2: Run focused tests and verify RED**

  Run the practice validator and renderer test modules; expect the malformed cases to crash before the fix.

- [ ] **Step 3: Implement minimal ordering change**

  Check list shape and all-string types before uniqueness construction in `_references`.

- [ ] **Step 4: Verify GREEN**

  Run focused tests, static checks, privacy checks, and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit implementation, tests, spec, and plan as `fix: guard practice reference types`.
