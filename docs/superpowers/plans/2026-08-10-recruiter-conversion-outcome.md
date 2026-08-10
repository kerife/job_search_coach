# Recruiter Conversion Outcome Receipt Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a closed, dated, candidate-supplied recruiter outcome receipt that maps observations to safe next steps without external action or causality claims.

**Architecture:** Implement a dedicated JSON schema and Python validator/CLI, then an offline localized renderer that consumes only validated enum data. Add routing/skill contract wording and tests while preserving existing triage, dossier, CSV, and normal recruiter-reply paths.

**Tech Stack:** JSON Schema Draft 2020-12, Python validator/CLI, offline HTML/CSS, unittest, repository privacy/static/release gates.

## Global Constraints

- Event types are exactly `contact_received`, `reply_received`, `referral_received`, `screen_requested`, `interview_requested`, and `stop_decision`.
- Next-safe-action mapping is exact: contact/reply → `clarify_context_before_reply`; referral → `prepare_fact_checked_summary`; screen/interview → `route_to_prepare-role-interviews`; stop → `record_stop_decision`.
- Date is ISO `YYYY-MM-DD`, a real non-future date, checked against an injected `as_of` date (default today).
- IDs are internal JSON only: source `D-###`, facts `F-###`; HTML never renders them.
- No cross-artifact candidate identity claim; only one artifact's declared ID namespace and references are validated.
- Delivery is draft-only, no message/calendar action, no raw event retention, and local save disabled.
- No auto-start, module execution packet, send, schedule, score, fit, offer, or causal claim.

---

### Task 1: Add the closed outcome contract

**Files:**
- Create: `plugins/job-search-coach/schemas/private-recruiter-conversion-outcome-v1.schema.json`
- Create: `plugins/job-search-coach/scripts/validate_private_recruiter_conversion_outcome.py`
- Create: `plugins/job-search-coach/tests/test_private_recruiter_conversion_outcome.py`
- Create: `plugins/job-search-coach/tests/fixtures/private-recruiter-conversion-outcome/*.json`

**Interfaces:**
- Consumes only closed candidate-supplied event JSON.
- Produces validation errors or a validated event mapping with immutable delivery fields.

- [ ] Write RED tests for one valid fixture per event type and EN/ES metadata.
- [ ] Write RED tests for all six exact event/action mappings, invalid/noncanonical/future dates with injected `as_of`, unknown/extra fields and wrong types, missing source/version/facts, malformed IDs/version, mixed IDs, raw/identity/action/outcome/score injection, and delivery gates.
- [ ] Run the focused test file and confirm the new assertions fail before implementation.
- [ ] Implement closed JSON Schema with exact enums, patterns, constants, and delivery gates.
- [ ] Implement validator/CLI with injected `as_of`, real-date/no-future-date checks, strict ID/version bounds, and event/action mapping.
- [ ] Add fixtures and JSON syntax validation.
- [ ] Run focused tests and `git diff --check`.
- [ ] Commit `feat: add recruiter conversion outcome contract`.

### Task 2: Render the private outcome receipt

**Files:**
- Create: `plugins/job-search-coach/scripts/render_private_recruiter_conversion_outcome.py`
- Create: `plugins/job-search-coach/assets/private-recruiter-conversion-outcome-v1.css`
- Create: `plugins/job-search-coach/assets/private-recruiter-conversion-outcome-v1.html`
- Create: `plugins/job-search-coach/tests/test_render_private_recruiter_conversion_outcome.py`

**Interfaces:**
- Consumes only validator-approved event objects.
- Produces deterministic localized HTML with fixed event/action labels and no IDs/raw prose.

- [ ] Write RED tests for six event mappings, EN/ES copy, ID omission, no interactive output, and 0600 atomic/symlink-safe writes.
- [ ] Implement fixed enum-to-label mappings, escaped template data, and validation gate.
- [ ] Add responsive, print, reduced-motion, and forced-color CSS hooks.
- [ ] Run contract + renderer suites and `git diff --check`.
- [ ] Commit `feat: render recruiter conversion outcome receipt`.

### Task 3: Preserve routing and measurement boundaries

**Files:**
- Modify: `plugins/job-search-coach/skills/track-job-search-outcomes/SKILL.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/SKILL.md`
- Modify: `plugins/job-search-coach/skills/job-search-coach/references/routing.md`
- Test: `tests/test_full_plugin.py`, `tests/test_skill_contracts.py`

**Interfaces:**
- Documents the artifact as candidate-supplied observation only.
- Keeps normal CSV/outcome and LinkedIn behavior unchanged.

- [ ] Add RED tests for event-to-action mapping, no auto-start/module packet, and ordinary-route preservation.
- [ ] Add concise contract wording for candidate isolation, no causality, and manual next step.
- [ ] Run focused integration/privacy tests and `git diff --check`.
- [ ] Commit `docs: route recruiter conversion outcome safely`.

### Task 4: Publish and install

**Files:**
- Modify mechanically only: provenance sidecars/indexes/summary and manifest version.

- [ ] Refresh provenance with canonical helpers for the approved functional tree.
- [ ] Run schema, focused, privacy, static, official, diff, and full discovery gates.
- [ ] Invoke cachebuster exactly once and create the release commit.
- [ ] Run post-release gates/full discovery explicitly to green.
- [ ] Install exact current version; verify source/cache identity and aggregate hash.
- [ ] Smoke all six event mappings in EN/ES, ensure outputs are `0600`, clean only generated caches, and leave worktree clean.
