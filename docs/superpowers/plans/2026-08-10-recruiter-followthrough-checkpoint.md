# Recruiter Follow-through Checkpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a closed candidate-supplied checkpoint after a recruiter outcome receipt, mapping bounded action states to safe manual next steps.

**Architecture:** Validate a checkpoint only against a separately supplied valid outcome receipt; enforce exact state/event/action mapping and immutable delivery fields; render fixed localized labels without IDs or free prose; document routing boundaries while leaving receipt v1 and CSV untouched.

**Tech Stack:** JSON Schema Draft 2020-12, Python validator/CLI, offline HTML/CSS, unittest, repository privacy/static/release gates.

## Global Constraints

- Source receipt is required and must validate before checkpoint validation.
- Source receipt fields are closed: schema version, artifact kind, `D-###` ID, source version, and event type must match exactly.
- States are exactly `accepted`, `deferred`, `declined`, `completed`.
- Events are exactly `screen_prepared`, `screen_attended`, `interview_requested`, `stop_decision`, `unknown`; completed `screen_attended` uses the closed `debrief_after_screen` manual action.
- Non-completed states require `next_measurement_event=unknown`; a source stop may only be declined/completed. Dates are real ISO dates, checkpoint date is on/after receipt date, and both are no later than injected `as_of`.
- IDs stay in JSON only; HTML omits all IDs and raw data.
- No auto-start, module packet, send, calendar, score, answer, outcome guarantee, CSV update, or candidate aggregation.

---

### Task 1: Add the checkpoint contract

**Files:**
- Create: `plugins/job-search-coach/schemas/private-recruiter-followthrough-checkpoint-v1.schema.json`
- Create: `plugins/job-search-coach/scripts/validate_private_recruiter_followthrough_checkpoint.py`
- Create: `plugins/job-search-coach/tests/test_private_recruiter_followthrough_checkpoint.py`
- Create: `plugins/job-search-coach/tests/fixtures/private-recruiter-followthrough-checkpoint/*.json`

- [ ] Write RED tests for valid EN/ES checkpoints and the full state/event action matrix, including non-completed unknown-event constraints and source-stop restrictions.
- [ ] Write RED tests for missing/invalid/mismatched receipt fields, chronology/as-of, extra/wrong fields/types, raw/identity/action/outcome/score, receipt symlink/size safety, and immutable delivery.
- [ ] Confirm RED before implementation.
- [ ] Implement closed schema, receipt loading, cross-artifact equality, date checks, and action mapping.
- [ ] Add fixtures and schema JSON validation.
- [ ] Run focused tests and diff check.
- [ ] Commit `feat: add recruiter followthrough checkpoint contract`.

### Task 2: Render the checkpoint

**Files:**
- Create: `plugins/job-search-coach/scripts/render_private_recruiter_followthrough_checkpoint.py`
- Create: `plugins/job-search-coach/assets/private-recruiter-followthrough-checkpoint-v1.css`
- Create: `plugins/job-search-coach/assets/private-recruiter-followthrough-checkpoint-v1.html`
- Create: `plugins/job-search-coach/tests/test_render_private_recruiter_followthrough_checkpoint.py`

- [ ] Add RED tests for all states/locales, ID omission, no interactive output, and 0600 atomic writes.
- [ ] Render fixed enum labels only after receipt/checkpoint validation.
- [ ] Add responsive/print/reduced-motion/forced-color hooks.
- [ ] Run contract+renderer tests and diff check.
- [ ] Commit `feat: render recruiter followthrough checkpoint`.

### Task 3: Preserve routes and measurement

**Files:**
- Modify: `plugins/job-search-coach/skills/track-job-search-outcomes/SKILL.md`
- Modify: `plugins/job-search-coach/skills/prepare-role-interviews/SKILL.md`
- Modify: `plugins/job-search-coach/skills/job-search-coach/references/routing.md`
- Test: `tests/test_skill_contracts.py`, `tests/test_full_plugin.py`

- [ ] Add RED tests for replay idempotence, completed-screen/interview manual prep, decline/stop blocking prep, and unchanged CSV/ordinary routes.
- [ ] Add concise candidate-supplied/no-aggregation/no-auto-start wording.
- [ ] Run focused integration/privacy tests and diff check.
- [ ] Commit `docs: route recruiter followthrough safely`.

### Task 4: Publish and install

**Files:**
- Modify mechanically only: provenance sidecars/indexes/summary and manifest version.

- [ ] Refresh provenance with canonical helpers.
- [ ] Run all pre-release gates and full discovery.
- [ ] Invoke cachebuster exactly once and commit release.
- [ ] Run post-release gates/full discovery, install exact version, compare source/cache identity.
- [ ] Smoke all state/event mappings EN/ES with receipt validation, `--as-of`, mode `0600`, and cache cleanup.
