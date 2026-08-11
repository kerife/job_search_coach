# Pressure Scorer Article Count Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent article-only prose from becoming a false market-volume mismatch in dossier pressure scoring.

**Architecture:** Keep the existing market noun backtracking and numeric parser. Add one narrow filtering condition after parsing so valid numeric phrases and malformed numeric-looking phrases retain their existing behavior.

**Tech Stack:** Python 3, `unittest`, dossier pressure scorer in `run_static_checks.py`.

## Global Constraints

- Preserve existing mismatch detection for numeric and malformed numeric phrases.
- Do not change schemas, renderer output, privacy rules, or action gates.
- Use the existing canonical pressure tests as the RED/GREEN evidence.

### Task 1: Reproduce and fix the article-only false positive

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_executive_career_dossier.py` in `extract_market_volume_values`
- Test: `tests/test_plugin_structure.py` existing pressure scorer tests

**Interfaces:**
- Consumes: visible dossier text and the existing `parse_bounded_number` helper.
- Produces: the same tuple of parsed market-volume values, excluding only an isolated article span.

- [x] **Step 1: Observe RED**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_plugin_structure.JobSearchCoachPluginStructureTests.test_pressure_scorer_accepts_all_canonical_dossier_fixtures tests.test_plugin_structure.JobSearchCoachPluginStructureTests.test_pressure_scorer_reconciles_visible_market_word_numbers -q
  ```

  Before the fix, the canonical market fixture fails with one claim violation because `a job` contributes an unparsed count.

- [x] **Step 2: Apply the minimal parser guard**

  Store the backtracked span in `phrase`, parse it, and append when parsing succeeds or when `phrase != "a"`. This keeps invalid numeric spans visible to reconciliation.

- [x] **Step 3: Verify GREEN**

  Re-run the command above; expected result: 2 tests OK. Then run the full plugin suite and root suite before the release bump.
