# Conversion evidence plural Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve localized evidence-count copy in the private conversion receipt.

**Architecture:** Add a closed locale/cardinality helper in the renderer; continue deriving the count only from validated `fact_ids`.

**Tech Stack:** Python 3 standard library, unittest, static HTML.

## Global Constraints

- EN singular/plural and ES singular/plural copy are fixed constants.
- Count comes only from validated `fact_ids` length.
- No raw IDs, external actions, links, or schema changes.

### Task 1: Pluralize evidence copy

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_private_recruiter_conversion_outcome.py`
- Test: `plugins/job-search-coach/tests/test_render_private_recruiter_conversion_outcome.py`

- [ ] **Step 1: Add failing copy assertions**

  Render one-fact EN and two-fact ES fixtures; assert natural singular/plural strings and reject `fact(s)`/`hecho(s)`.

- [ ] **Step 2: Run focused tests and verify RED**

  Run the conversion renderer/contract tests; expect the new copy assertions to fail.

- [ ] **Step 3: Implement fixed locale/cardinality mapping**

  Add a helper that selects singular only when count equals one, otherwise plural; substitute it in the existing evidence row.

- [ ] **Step 4: Verify GREEN**

  Run focused tests, static checks, and `git diff --check`.

- [ ] **Step 5: Commit**

  Commit renderer, test, spec, and plan as `feat: pluralize conversion evidence copy`.
