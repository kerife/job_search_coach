# Private loader symlink consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject symlink input paths consistently across private practice-session and recruiter-reply triage loaders.

**Architecture:** Reuse each loader's current error type and parsing pipeline. Insert a path guard before reading and cover it with focused tests; leave renderers and contracts unchanged.

**Tech Stack:** Python 3 standard library, unittest, JSON loaders.

## Global Constraints

- Reject symlink input paths before `read_text`.
- Preserve regular-file validation, duplicate-key checks, 64KB limits, and max-depth behavior.
- Preserve existing CLI failure codes and privacy boundaries.

### Task 1: Add symlink guards

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_recruiter_practice_session.py`
- Modify: `plugins/job-search-coach/scripts/validate_private_recruiter_reply_triage.py`
- Modify: focused loader test files for both validators

- [ ] **Step 1: Write failing symlink tests**

  Create temporary regular JSON targets and symlinks; assert each loader raises its existing load/validation error for the symlink while the regular target remains valid.

- [ ] **Step 2: Run focused tests and verify RED**

  Run the two loader test modules; expect the new symlink assertions to fail before the guard.

- [ ] **Step 3: Implement the minimal guard**

  At the start of each loader, call `path.is_symlink()` and raise its existing input error before reading. Do not change parsing or error text beyond the established boundary.

- [ ] **Step 4: Verify GREEN**

  Run the focused loader/renderer suites, `python3 -B plugins/job-search-coach/tests/run_static_checks.py`, and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit implementation, tests, spec, and plan as `fix: reject symlinked private inputs`.
