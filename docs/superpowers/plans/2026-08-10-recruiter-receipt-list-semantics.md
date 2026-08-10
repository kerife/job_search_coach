# Recruiter receipt list semantics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace repeated receipt definition-list labels with two accessible fixed-content lists.

**Architecture:** Renderer-only HTML structure and scoped CSS changes. Validation, routing, data contracts, and privacy boundaries stay unchanged.

**Tech Stack:** Python 3 standard library, unittest, inline HTML/CSS templates.

## Global Constraints

- Ready-only receipt; clarify and stop omit it.
- Exactly two labeled groups and exactly two list items per group.
- No raw reply, identity, contact, calendar, IDs, links, buttons, forms, or actions.
- Preserve EN/ES localization, mobile, print, forced-colors, and deterministic output.

### Task 1: Convert receipt groups to lists

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_private_recruiter_reply_triage.py`
- Modify: `plugins/job-search-coach/assets/private-recruiter-reply-triage-v1.css`
- Test: `tests/test_render_private_recruiter_reply_triage.py`

- [ ] **Step 1: Add failing semantic assertions**

  Assert both ready fixtures contain two receipt groups, each with a labeled `<ul>` and two `<li>` elements, and the receipt substring contains no `<dt>` or `<dd>`.

- [ ] **Step 2: Run the focused renderer test and verify failure**

  Run `python3 -B -m unittest tests.test_render_private_recruiter_reply_triage -q`; expect failure against the current `<dl>` groups.

- [ ] **Step 3: Implement minimal HTML/CSS change**

  Replace each receipt-group `<dl>` with `<ul class="triage-handoff-receipt-list" aria-labelledby="...">` and two `<li>` fixed labels. Add only scoped list reset/spacing rules, retaining print/mobile/forced-color behavior.

- [ ] **Step 4: Verify**

  Run `python3 -B -m unittest tests.test_render_private_recruiter_reply_triage tests.test_private_recruiter_reply_triage -q` and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit the renderer, CSS, test, spec, and plan as `feat: clarify recruiter receipt list semantics`.
