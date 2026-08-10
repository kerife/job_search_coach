# Recruiter question order Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorder the ready private recruiter triage renderer so the actionable safe-question preview follows the manual re-entry cue and precedes the receipt.

**Architecture:** Keep the existing validated renderer data and HTML blocks. Change only template assembly order and focused order assertions; no schema or routing surface changes.

**Tech Stack:** Python 3 standard library, unittest, static HTML/CSS templates.

## Global Constraints

- Preserve closed validation and identity-free output.
- Preserve exactly one safe question and existing EN/ES localization.
- Preserve no links, buttons, forms, calendar, send, raw reply, or internal IDs in HTML.
- Preserve deterministic rendering and existing responsive/print/forced-colors hooks.

### Task 1: Reorder ready preview

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_private_recruiter_reply_triage.py`
- Test: `tests/test_render_private_recruiter_reply_triage.py`

**Interfaces:**
- Consumes the existing validated triage mapping and rendered `next_step`, `preview`, and `receipt` blocks.
- Produces the same HTML blocks in order: next step, preview, receipt.

- [ ] **Step 1: Write the failing order assertion**

  Update the ready-fixture order assertion to require the `triage-handoff-next-step` marker before `triage-handoff-preview`, and the preview before `triage-handoff-receipt`.

- [ ] **Step 2: Run the focused test and verify the pre-change failure**

  Run `python3 -B -m unittest tests.test_render_private_recruiter_reply_triage -q`.
  Expected: the order assertion fails because the existing receipt precedes the preview.

- [ ] **Step 3: Make the minimal assembly change**

  In the ready-only handoff rendering branch, move the existing preview block above the receipt block without changing either block's content or validation.

- [ ] **Step 4: Run focused verification**

  Run `python3 -B -m unittest tests.test_render_private_recruiter_reply_triage tests.test_private_recruiter_reply_triage -q` and `git diff --check`.
  Expected: all focused tests pass and the diff is clean.

- [ ] **Step 5: Commit**

  Run `git add plugins/job-search-coach/scripts/render_private_recruiter_reply_triage.py tests/test_render_private_recruiter_reply_triage.py docs/superpowers/specs/2026-08-10-recruiter-question-order-design.md docs/superpowers/plans/2026-08-10-recruiter-question-order.md && git commit -m "feat: prioritize recruiter safe question"`.
