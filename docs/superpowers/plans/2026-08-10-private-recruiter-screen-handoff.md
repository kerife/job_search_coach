# Private recruiter-screen handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Carry a verified, identity-free recruiter-reply triage result back into recruiter-screen preparation without auto-starting work or exposing private content.

**Architecture:** Extend the existing closed triage JSON with a required-in-ready, absent-in-other-states `handoff` object. Reuse the validator's existing safety/prose gate and render a localized, actionless re-entry cue. Update routing/reference contracts and tests without changing the normal LinkedIn dossier path.

**Tech Stack:** Python 3.11 standard library, closed JSON Schema, unittest, static/privacy validators, inline HTML/CSS.

## Global Constraints

- Handoff is valid only for `ready_for_private_prep` with confirmed stage, role context, critical constraints, and one `verified` fact.
- `auto_start`, external actions, raw reply retention, and local saving remain disabled/false.
- No recruiter/company identity, contact details, URLs, times, internal IDs, raw text, analytics, calendar, send, or outcome language.
- Clarify/stop artifacts omit the handoff object; normal LinkedIn dossier and ordinary recruiter-reply routes remain unchanged.

---

### Task 1: Closed handoff contract

**Files:**
- Modify: `plugins/job-search-coach/schemas/private-recruiter-reply-triage-v1.schema.json`
- Modify: `plugins/job-search-coach/scripts/validate_private_recruiter_reply_triage.py`
- Test: `tests/test_private_recruiter_reply_triage.py`

**Interfaces:**
- Consumes the existing triage object and `validate_triage(value) -> list[str]`.
- Produces a closed `handoff` object with fields `module`, `scope`, `input_mode`, `auto_start`, `external_actions`, `raw_reply_retained`, and `local_save_mode`.

- [ ] **Step 1: Write RED mutations** for missing/extra handoff fields, handoff on clarify/stop, candidate-reported fact, wrong module/scope, auto-start/action/raw-save values, and a valid ready control.
- [ ] **Step 2: Run the focused tests** and verify the mutations fail before implementation.
- [ ] **Step 3: Add schema conditionals** requiring the exact handoff values only in ready state and forbidding the field in clarify/stop.
- [ ] **Step 4: Extend `validate_triage`** with closed-field and state/fact binding checks; keep the existing prose scanner unchanged.
- [ ] **Step 5: Run `python3 -B -m unittest tests.test_private_recruiter_reply_triage -v`** and confirm all controls pass.
- [ ] **Step 6: Commit** with `feat: add recruiter screen handoff contract`.

### Task 2: Private handoff rendering

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_private_recruiter_reply_triage.py`
- Modify: `plugins/job-search-coach/assets/private-recruiter-reply-triage-v1.html`
- Modify: `plugins/job-search-coach/assets/private-recruiter-reply-triage-v1.css`
- Test: `tests/test_render_private_recruiter_reply_triage.py`

**Interfaces:**
- Consumes validated triage JSON from Task 1.
- Produces deterministic localized HTML with a ready-only handoff cue and existing 0600 atomic output.

- [ ] **Step 1: Add RED assertions** for localized ready handoff scope/re-entry text, absence in clarify/stop, no auto-start/action/calendar terms, and unchanged no-save disclosure.
- [ ] **Step 2: Run the renderer tests** and verify the new assertions fail.
- [ ] **Step 3: Render the handoff cue** from fixed enum values only; never interpolate raw reply text or identifiers.
- [ ] **Step 4: Add scoped responsive/print styles** without changing the existing card hierarchy or remote dependencies.
- [ ] **Step 5: Run renderer, accessibility, print, privacy, and deterministic-byte tests**; remove generated caches.
- [ ] **Step 6: Commit** with `feat: render private recruiter screen handoff`.

### Task 3: Routing and contract references

**Files:**
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/SKILL.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/references/networking-and-content.md`
- Modify: `plugins/job-search-coach/skills/prepare-role-interviews/SKILL.md`
- Modify: `plugins/job-search-coach/skills/job-search-coach/SKILL.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/references/client-report.md`
- Test: `tests/test_full_plugin.py`, `tests/test_skill_contracts.py`

**Interfaces:**
- Consumes the Task 1 handoff contract and Task 2 renderer behavior.
- Produces explicit precedence/reference wording: re-entry cue only, no automatic module packet or router output.

- [ ] **Step 1: Add RED routing assertions** for ready handoff scope, clarify/stop omission, private precedence over debug/raw/internal prompts, and legacy normal behavior.
- [ ] **Step 2: Run the focused integration tests** and verify they fail on missing wording.
- [ ] **Step 3: Add concise contract text** in each existing reference without duplicating broad non-private rules.
- [ ] **Step 4: Run skill/full-plugin/privacy/diff checks** and confirm root skill focused-loading size remains below its limit.
- [ ] **Step 5: Commit** with `feat: route recruiter screen handoff safely`.

### Task 4: Independent review and publication

**Files:**
- Inspect only the Task 1–3 diff and ignored reports.
- Modify only release-owned provenance/manifest files during publication.

- [ ] **Step 1: Run independent value, security, and design reviews** against exact HEAD; reject raw/identity/action/auto-start bypasses.
- [ ] **Step 2: Fix review findings with RED→GREEN tests** before release refresh.
- [ ] **Step 3: Refresh only the approved provenance bindings** to the functional parent/tree.
- [ ] **Step 4: Run schema, focused, full, privacy, static, official, and diff gates.
- [ ] **Step 5: Invoke the official cachebuster exactly once; audit manifest-only version delta.
- [ ] **Step 6: Commit the publication, rerun post-commit gates, install exact version, and smoke ready/clarify/stop states.
