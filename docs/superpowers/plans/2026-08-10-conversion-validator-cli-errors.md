# Conversion validator CLI errors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make malformed conversion validator arguments deterministic and consistent with other private CLIs.

**Architecture:** Preserve argparse definitions and validation code; normalize only nonzero parser exits inside `_cli`.

**Tech Stack:** Python 3 standard library, unittest, subprocess.

## Global Constraints

- Missing/unknown/invalid-date input returns 3.
- `--help` returns 0.
- Semantic validation remains 2 and valid output is unchanged.

### Task 1: Normalize conversion validator parsing

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_private_recruiter_conversion_outcome.py`
- Modify: `plugins/job-search-coach/tests/test_private_recruiter_conversion_outcome.py`

- [ ] **Step 1: Add failing CLI tests**

  Invoke the validator with missing `--as-of`/`--output` and an unknown flag; assert code 3, no traceback, and no artifact. Assert `--help` remains 0.

- [ ] **Step 2: Run tests and verify RED**

  Run the conversion validator test module; expect argparse code 2 before the fix.

- [ ] **Step 3: Implement minimal parser catch**

  Catch parser `SystemExit`, return 0 for help and 3 for other parse failures; retain validation/date handling.

- [ ] **Step 4: Verify GREEN**

  Run conversion validator/renderer tests, static checks, privacy checks, and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit validator, tests, spec, and plan as `fix: normalize conversion validator CLI`.
