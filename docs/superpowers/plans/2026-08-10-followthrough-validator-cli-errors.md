# Follow-through validator CLI errors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make malformed follow-through validator arguments deterministic and consistent.

**Architecture:** Keep argparse definitions and validation pipeline; wrap parse/date failures at `_cli` and preserve existing success/semantic error paths.

**Tech Stack:** Python 3 standard library, unittest, subprocess.

## Global Constraints

- Input parse/date errors return 3.
- `--help` returns 0.
- Semantic validation errors remain 2; no traceback/artifact.

### Task 1: Normalize validator parser failures

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_private_recruiter_followthrough_checkpoint.py`
- Modify: `plugins/job-search-coach/tests/test_private_recruiter_followthrough_checkpoint.py`

- [ ] **Step 1: Add failing CLI tests**

  Invoke the validator with invalid `--as-of`, missing `--receipt`, and `--help`; assert expected codes 3, 3, and 0 respectively, with no traceback.

- [ ] **Step 2: Run tests and verify RED**

  Run the focused checkpoint test module; expect invalid/missing argument cases to exit 2 before the fix.

- [ ] **Step 3: Implement minimal parse normalization**

  Catch parser `SystemExit` inside `_cli`, return 3 for nonzero parse failures, and allow the help path to return 0; keep validation exceptions unchanged.

- [ ] **Step 4: Verify GREEN**

  Run checkpoint contract/renderer tests, static checks, privacy checks, and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit validator, tests, spec, and plan as `fix: normalize followthrough validator CLI`.
