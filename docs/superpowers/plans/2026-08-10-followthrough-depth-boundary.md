# Follow-through depth boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject excessively nested follow-through checkpoint and receipt JSON at the loader boundary.

**Architecture:** Reuse the current `_load_json` path, duplicate-key hook, byte bound, symlink guard, and `CheckpointLoadError`; add one recursive depth check and focused mutations.

**Tech Stack:** Python 3 standard library, unittest, JSON loader.

## Global Constraints

- Maximum depth is 12 with root depth 0.
- Checkpoint and receipt inputs share the same loader and error boundary.
- Valid output, privacy, routing, and renderer behavior remain unchanged.

### Task 1: Enforce follow-through depth

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_private_recruiter_followthrough_checkpoint.py`
- Modify: `plugins/job-search-coach/tests/test_private_recruiter_followthrough_checkpoint.py`

- [ ] **Step 1: Add failing deep-input tests**

  Build nested object JSON beyond depth 12 for the checkpoint and receipt temporary inputs; assert `load_checkpoint` and `load_receipt` raise `CheckpointLoadError`, while the existing fixtures remain valid.

- [ ] **Step 2: Run focused tests and verify RED**

  Run `python3 -B -m unittest plugins/job-search-coach/tests/test_private_recruiter_followthrough_checkpoint.py -q`; expect the new deep-input cases to fail before implementation.

- [ ] **Step 3: Implement the recursive guard**

  Add `_assert_max_depth(value, maximum=12, depth=0)` and call it after JSON parsing in `_load_json`; retain duplicate-key and symlink behavior.

- [ ] **Step 4: Verify GREEN**

  Run the follow-through contract/renderer tests, `python3 -B plugins/job-search-coach/tests/run_static_checks.py`, and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit validator, tests, spec, and plan as `fix: bound followthrough JSON depth`.
