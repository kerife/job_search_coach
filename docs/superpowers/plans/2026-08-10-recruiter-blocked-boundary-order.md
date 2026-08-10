# Recruiter blocked boundary order Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface the fixed blocked-claims boundary before private recruiter handoff content.

**Architecture:** Reuse the existing rendered blocked section and move its assembly before the existing handoff placeholder. No contract or CSS changes are required.

**Tech Stack:** Python 3 standard library, unittest, static HTML.

## Global Constraints

- Preserve exact blocked item text and escaping.
- Preserve ready-only handoff and clarify/stop omission.
- Preserve semantic IDs, lists, no actions, and deterministic output.

### Task 1: Reorder blocked section

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_private_recruiter_reply_triage.py`
- Test: `tests/test_render_private_recruiter_reply_triage.py`

- [ ] **Step 1: Add the failing order assertion**

  For ready EN/ES assert the next-safe-action marker precedes `triage-blocked`, which precedes `triage-handoff`; preserve clarify/stop omission checks.

- [ ] **Step 2: Run the focused test and verify RED**

  Run `python3 -B -m unittest tests.test_render_private_recruiter_reply_triage -q`; expect the new order assertion to fail.

- [ ] **Step 3: Move the existing blocked block**

  Construct the same blocked HTML once and place it directly after the next-safe-action section, removing the later duplicate position. Do not alter its contents.

- [ ] **Step 4: Verify GREEN**

  Run `python3 -B -m unittest tests.test_render_private_recruiter_reply_triage tests.test_private_recruiter_reply_triage -q` and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit the renderer, test, spec, and plan as `feat: surface recruiter claim boundaries`.
