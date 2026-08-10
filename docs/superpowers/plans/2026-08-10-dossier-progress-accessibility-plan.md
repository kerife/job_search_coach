# Dossier scorecard progress accessibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Associate dossier scorecard progress bars with their visible dimension headings for screen-reader users.

**Architecture:** Keep the existing scorecard markup and CSS. Derive one deterministic ID from each validator-closed dimension key, put it on the card heading, and reference it from the native progress element. Renderer tests assert the relationship for both locales.

**Tech Stack:** Python 3.11 standard library, offline HTML renderer, unittest, Superdesign design-system constraints.

## Global Constraints

- Preserve visual order, score text, localization, print, forced-colors, and mobile CSS.
- Do not add JavaScript, network dependencies, persistence, or new user-facing copy.
- IDs must be deterministic and use only validator-closed dimension keys.
- Follow RED → GREEN → focused regression → `git diff --check`.

---

### Task 1: Name scorecard progress bars

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_executive_career_dossier.py:696-716`
- Test: `tests/test_executive_career_dossier.py:1835-1855`

**Interfaces:**
- `_render_dimensions(dossier, locale)` continues returning the same scorecard HTML, with each evaluated progress element adding `aria-labelledby="dimension-title-<dimension>"` and its card `<h3>` receiving that ID.

- [ ] **Step 1: Write the failing test**

  Render the canonical Spanish and English dossiers, collect every progress
  element's `aria-labelledby`, and assert each referenced ID appears on an
  `<h3>` in the same rendered document. Assert the number of named progress
  bars equals the number of evaluated dimensions.

- [ ] **Step 2: Run the renderer tests and verify RED**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_executive_career_dossier.ExecutiveCareerDossierRendererTests.test_scorecard_progress_has_named_dimension_headings -v
  ```

  Expected before implementation: the test fails because progress elements
  have no `aria-labelledby` and dimension headings have no matching IDs.

- [ ] **Step 3: Implement the minimal markup association**

  In `_render_dimensions`, compute `dimension_key` from the already validated
  dimension value, set `heading_id = f"dimension-title-{dimension_key}"`, add
  `id=heading_id` to the `<h3>`, and add
  `aria-labelledby=heading_id` to the evaluated `<progress>` only.

- [ ] **Step 4: Run GREEN and regression checks**

  Run the focused renderer test, the full dossier module, and `git diff --check`.
  Confirm non-evaluated dimensions still render only their existing state chip.

- [ ] **Step 5: Commit implementation**

  ```bash
  git add plugins/job-search-coach/scripts/render_executive_career_dossier.py tests/test_executive_career_dossier.py
  git commit -m "fix: name dossier scorecard progress bars"
  ```
