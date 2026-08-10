# Private renderer CLI errors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make malformed CLI arguments deterministic across private conversion and follow-through renderers.

**Architecture:** Keep argparse configuration and valid code paths, but wrap parse and date conversion at each `_cli`, returning the existing input-error code 3 with concise stderr.

**Tech Stack:** Python 3 standard library, unittest, subprocess.

## Global Constraints

- Invalid dates and missing required flags return 3.
- No traceback, artifact, or change to valid output.
- Validator failures remain distinct and return 2.

### Task 1: Normalize renderer CLI parsing

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_private_recruiter_conversion_outcome.py`
- Modify: `plugins/job-search-coach/scripts/render_private_recruiter_followthrough_checkpoint.py`
- Modify: focused renderer CLI tests for both artifacts

- [ ] **Step 1: Add failing subprocess/CLI tests**

  Invoke both CLIs with `--as-of bad` and with required flags omitted; assert the current expected contract code 3, concise error, no traceback, and no output file.

- [ ] **Step 2: Run tests and verify RED**

  Run the focused renderer test modules; expect exit 2/usage before the fix.

- [ ] **Step 3: Implement minimal normalization**

  Catch parser `SystemExit` and date conversion errors inside `_cli`, print one fixed input-error line, and return 3. Keep validation exceptions and successful JSON receipts unchanged.

- [ ] **Step 4: Verify GREEN**

  Run both focused validator/renderer suites, static checks, privacy checks, and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit implementation, tests, spec, and plan as `fix: normalize private renderer CLI errors`.
