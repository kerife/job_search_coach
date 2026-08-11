# Dossier Employment Boundary Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the executive dossier employment-continuity footer with the canonical office-safe boundary used by the other Professional Growth Coach surfaces.

**Architecture:** Preserve the existing renderer footer and change only its localized copy. Add renderer regressions for canonical wording, legacy-copy absence, deterministic output, and preserved no-action text; then publish the unchanged data contract as a new plugin version.

**Tech Stack:** Python 3, `unittest`, static/schema validators, offline HTML renderer, Codex local marketplace/cache.

## Global Constraints

- No schema, validator, route, action, or data-model changes.
- The canonical EN sentence is `This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.`
- The canonical ES sentence is `Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.`
- The boundary remains visible in print and contains no external controls, links, IDs, raw profile data, or action authorization.
- Run RED before changing renderer code and run the complete plugin/root gates before release.

### Task 1: Add dossier copy regression

**Files:**
- Modify: `tests/test_executive_career_dossier.py` near the existing employment-boundary renderer tests
- Read: `tests/evals/with-skill/fixtures/executive-career-dossier/scenario-a-es.json`, `scenario-c-en.json`, and one partial dossier fixture

**Interfaces:**
- Consumes: existing `render_dossier_html` test helper and fixture loader.
- Produces: a test proving canonical EN/ES copy, legacy-copy absence, deterministic rendering, and preserved no-action text.

- [ ] **Step 1: Write the failing test**

  Render `scenario-a-es`, `scenario-c-en`, and the existing partial fixture. Assert the canonical localized sentence occurs once, assert the old shorter sentence occurs zero times, and assert the localized no-LinkedIn-action text remains present.

- [ ] **Step 2: Run the test to verify RED**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_executive_career_dossier -q
  ```

  Expected: the new canonical-copy assertions fail because the renderer still uses the shorter dossier strings.

### Task 2: Update the renderer minimally

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/render_executive_career_dossier.py` localized `employment_boundary` values only

**Interfaces:**
- Consumes: the failing renderer test from Task 1.
- Produces: the same `render_dossier_html` API and footer markup with canonical EN/ES text.

- [ ] **Step 1: Replace only the two localized strings**

  Set the EN and ES values to the exact canonical sentences in the spec. Do not alter the footer template, CSS class, action boundary, or renderer control flow.

- [ ] **Step 2: Run the focused GREEN test**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_executive_career_dossier -q
  ```

  Expected: all dossier tests pass, including the new canonical-copy regression.

### Task 3: Verify the release and install it

**Files:**
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json` via the approved cachebuster once
- Modify: `tests/evals/final/cycle-1/*`, `tests/evals/final/cycle-2/*`, and `tests/evals/final/installed-smoke-test.md` with current release provenance and normalized source/cache hash

**Interfaces:**
- Consumes: the green renderer and plugin/root test suites.
- Produces: one installed canonical plugin version and an `installed_green` attestation.

- [ ] **Step 1: Run pre-release gates**

  Run plugin tests, root tests, `run_static_checks.py`, repository privacy, `scripts/run_release_validation.sh`, and the locked official plugin validator. All must pass before the cachebuster.

- [ ] **Step 2: Bump once and commit the release**

  Run the cachebuster exactly once, bind cycle sidecars to the functional parent/tree, and commit the manifest plus provenance metadata together.

- [ ] **Step 3: Install and smoke-test**

  Run:

  ```bash
  codex plugin add professional-growth-coach@professional-growth-coach-local --json
  ```

  Verify the installed version, source/cache `diff -qr`, normalized aggregate hash, canonical-only plugin list, dossier EN/ES smoke renders, and `installed_green` attestation.

- [ ] **Step 4: Close provenance and final gates**

  Bind final cycle sidecars to the immediate parent of the attestation commit, run static/provenance/plugin/root checks again, run `git diff --check`, and require a clean worktree.
