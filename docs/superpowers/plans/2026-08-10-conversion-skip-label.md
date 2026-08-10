# Conversion skip label Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Localize and clarify the conversion receipt skip-link action name.

**Architecture:** Add one renderer copy token and one template substitution; retain the existing focus target and all other markup.

**Tech Stack:** Python 3 standard library, unittest, static HTML template.

## Global Constraints

- EN: `Skip to main content`; ES: `Saltar al contenido principal`.
- Kicker remains a separate visible paragraph.
- No new external links, actions, data, or schema fields.

### Task 1: Clarify skip-link copy

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_private_recruiter_conversion_outcome.py`
- Modify: `plugins/job-search-coach/assets/private-recruiter-conversion-outcome-v1.html`
- Test: `plugins/job-search-coach/tests/test_render_private_recruiter_conversion_outcome.py`

- [ ] **Step 1: Add failing localized assertions**

  Assert both locale outputs contain the localized skip action in the anchor, retain the kicker in the separate paragraph, and do not place the kicker text inside the anchor.

- [ ] **Step 2: Run focused test and verify RED**

  Run `python3 -B -m unittest plugins/job-search-coach/tests/test_render_private_recruiter_conversion_outcome.py -q`; expect the new anchor assertion to fail.

- [ ] **Step 3: Implement minimal token split**

  Add `skip` labels and replace only the anchor token with `{{SKIP}}`; keep `{{KICKER}}` in the paragraph and substitution map.

- [ ] **Step 4: Verify GREEN**

  Run the focused conversion tests, `python3 -B plugins/job-search-coach/tests/run_static_checks.py`, and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit implementation, tests, spec, and plan as `feat: label conversion skip link`.
