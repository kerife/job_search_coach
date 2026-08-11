# Stop Receipt Continuity Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make isolated stop-decision receipts explicitly recruiter-process-scoped and employment-continuity-safe in English and Spanish.

**Architecture:** Keep the existing validated event/action flow and template slots. Each renderer will select a stop-specific localized action and boundary string when the validated event is `stop_decision`; every other event keeps its current copy. No schema or CSS changes.

**Tech Stack:** Python 3, `unittest`, static offline HTML renderers, existing localized dictionaries and templates.

## Global Constraints

- Preserve `stop_decision` as the only trigger; do not alter schemas or fixture data.
- Preserve non-stop copy byte-for-byte.
- Keep HTML escaping, no external actions, no forms, no links, and existing private write behavior.
- Use exact EN/ES strings from `docs/superpowers/specs/2026-08-11-stop-receipt-continuity-copy-design.md`.
- Run plugin static/privacy/release gates before consuming the one cachebuster.

---

### Task 1: Add RED renderer assertions

**Files:**
- Modify: `plugins/professional-growth-coach/tests/test_render_private_recruiter_followthrough_checkpoint.py`
- Modify: `plugins/professional-growth-coach/tests/test_render_private_recruiter_conversion_outcome.py`

**Interfaces:**
- Consumes: existing `render_checkpoint_html`, `render_outcome_html`, and official stop/non-stop fixtures.
- Produces: regression tests that fail against the current generic stop copy and preserve non-stop behavior.

- [ ] **Step 1: Write the failing checkpoint test**

Add `test_stop_decision_copy_preserves_employment_continuity_in_english_and_spanish` that renders `declined`/`stop_decision` checkpoint items in both locales and asserts the exact action and boundary strings from the spec.

- [ ] **Step 2: Write the failing conversion test**

Add `test_stop_decision_copy_preserves_employment_continuity_in_english_and_spanish` that loads `stop-decision-en.json`, renders it as English and Spanish, and asserts the exact action and boundary strings from the spec.

- [ ] **Step 3: Run RED tests**

Run:

```bash
PYTHONPATH=plugins/professional-growth-coach/scripts PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins.professional-growth-coach.tests.test_render_private_recruiter_followthrough_checkpoint plugins.professional-growth-coach.tests.test_render_private_recruiter_conversion_outcome -q
```

Expected: the new assertions fail because the current output contains generic `Record the stop decision` / `Registra la decisión de detenerse` and the generic candidate-supplied boundary.

- [ ] **Step 4: Commit the RED tests**

```bash
git add plugins/professional-growth-coach/tests/test_render_private_recruiter_followthrough_checkpoint.py plugins/professional-growth-coach/tests/test_render_private_recruiter_conversion_outcome.py
git commit -m "test: require continuity-safe stop receipt copy"
```

### Task 2: Implement localized stop copy

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/render_private_recruiter_followthrough_checkpoint.py`
- Modify: `plugins/professional-growth-coach/scripts/render_private_recruiter_conversion_outcome.py`

**Interfaces:**
- Consumes: validated `next_measurement_event`, `event_type`, and locale values.
- Produces: escaped stop-specific action and boundary strings in existing template slots.

- [ ] **Step 1: Add checkpoint stop-specific labels**

Add `stop_action` and `stop_boundary` entries under each locale in `LABELS`, then select them only when `value["next_measurement_event"] == "stop_decision"`; keep the existing `actions[...]` and `boundary` values for all other events.

- [ ] **Step 2: Add conversion stop-specific labels**

Add `stop_action` and `stop_boundary` entries under each locale in `COPY`, then select them only when `value["event_type"] == "stop_decision"`; keep existing `ACTION_LABELS` and generic boundary copy for all other events.

- [ ] **Step 3: Run GREEN focused tests**

```bash
PYTHONPATH=plugins/professional-growth-coach/scripts PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins.professional-growth-coach.tests.test_render_private_recruiter_followthrough_checkpoint plugins.professional-growth-coach.tests.test_render_private_recruiter_conversion_outcome -q
```

Expected: all focused checkpoint/outcome renderer tests pass, including the new EN/ES stop assertions.

- [ ] **Step 4: Commit the implementation**

```bash
git add plugins/professional-growth-coach/scripts/render_private_recruiter_followthrough_checkpoint.py plugins/professional-growth-coach/scripts/render_private_recruiter_conversion_outcome.py
git commit -m "fix: scope stop receipts to recruiter processes"
```

### Task 3: Run complete verification and publish

**Files:**
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json` via the cachebuster tool.
- Modify: the allowlisted final-evaluation provenance sidecars after the functional commit.

**Interfaces:**
- Consumes: the committed implementation and existing marketplace entry `professional-growth-coach-local`.
- Produces: one versioned, installed, byte-identical plugin release.

- [ ] **Step 1: Run pre-cachebuster gates**

Run static checks, repository privacy, release validation, plugin-local discovery, focused renderer/contract tests, and `git diff --check`. Do not consume the cachebuster until every gate exits zero.

- [ ] **Step 2: Consume the cachebuster exactly once**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B /Users/kevinriosferrer/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py plugins/professional-growth-coach
```

- [ ] **Step 3: Bind final-evaluation provenance**

Set all allowlisted `source_commit` and `source_tree` fields to the immediate functional parent and its `plugins/professional-growth-coach` tree hash, then run static/provenance checks again.

- [ ] **Step 4: Run post-cachebuster gates and commit release metadata**

Run the complete root suite, plugin suite, privacy, static, release, and diff checks. Commit manifest and provenance metadata together with a release message.

- [ ] **Step 5: Install and verify**

```bash
codex plugin add professional-growth-coach@professional-growth-coach-local --json
```

Verify the installed version is enabled, the cache matches the source with `diff -qr`, the installed release validator passes, and the final worktree is clean.
