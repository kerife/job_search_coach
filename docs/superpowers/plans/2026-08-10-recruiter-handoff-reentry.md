# Recruiter Handoff Re-entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a ready-only, identity-free re-entry receipt that safely bridges private recruiter triage to one-question interview preparation without auto-start or external action.

**Architecture:** Extend the existing closed triage schema with a nested `reentry_packet`; validate every field against the already validated triage context, fact, question, and scope; render only fixed localized scope copy while retaining IDs internally. Keep the downstream preparation module manual and answer-unaware until a later explicit candidate input.

**Tech Stack:** JSON Schema Draft 2020-12, Python validator/CLI, offline HTML renderer, unittest, repository privacy/static/release validators.

## Global Constraints

- Ready-only: `reentry_packet` is required for `ready_for_private_prep` and forbidden for `clarify_first` and `stop`.
- Exact one context summary, one verified fact, one question, and one mapped scope; re-entry values must equal both canonical triage fields and the existing `handoff.packet`.
- `manual_reentry_required=true`, `candidate_answer_state=unanswered`, `score_state=unknown`.
- No raw recruiter text, identity/contact, URLs, calendar/time, send/message, outcome/offer/fit claims, or persisted answer text.
- No new external action, auto-start, router rows, module execution packet, or LinkedIn access.
- IDs remain internal to validated JSON and are omitted from HTML.

---

### Task 1: Add the closed re-entry contract

**Files:**
- Modify: `plugins/job-search-coach/schemas/private-recruiter-reply-triage-v1.schema.json`
- Modify: `plugins/job-search-coach/scripts/validate_private_recruiter_reply_triage.py`
- Modify: `plugins/job-search-coach/tests/fixtures/private-recruiter-reply-triage/*.json`
- Test: `plugins/job-search-coach/tests/test_private_recruiter_reply_triage.py`

**Interfaces:**
- Consumes the existing `handoff.packet` fields and ready-state invariants.
- Produces `handoff.reentry_packet` with the exact fields defined in the spec.

- [ ] Write RED tests for valid EN/ES packets and omission in clarify/stop.
- [ ] Write RED mutation tests for missing/extra fields, candidate-reported fact, context/ID/scope mismatch, answer text, score, and forbidden prose.
- [ ] Run `python3 -B -m unittest plugins/job-search-coach/tests/test_private_recruiter_reply_triage.py -q` and confirm the new cases fail before implementation.
- [ ] Add closed JSON Schema definitions and ready-state conditional requirements.
- [ ] Add validator checks that compare packet values to triage values and reject all mutations.
- [ ] Update only the canonical fixtures with deterministic unanswered/unknown values.
- [ ] Re-run the focused contract tests and `python3 -m json.tool` on the schema.
- [ ] Commit `feat: add recruiter screen reentry contract`.

### Task 2: Render the bounded re-entry cue

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_private_recruiter_reply_triage.py`
- Modify: `plugins/job-search-coach/assets/private-recruiter-reply-triage-v1.css`
- Test: `plugins/job-search-coach/tests/test_render_private_recruiter_reply_triage.py`

**Interfaces:**
- Consumes validated `handoff.reentry_packet`.
- Produces ready-only localized scope/manual-reentry copy with no IDs or raw packet interpolation.

- [ ] Add RED tests for ready EN/ES scope cue, clarify/stop omission, and prohibited HTML output.
- [ ] Run the renderer test file and confirm the new assertions fail.
- [ ] Render fixed localized copy from the validated `prep_scope` enum; do not render IDs or packet summaries.
- [ ] Add semantic labels and existing responsive/print/forced-color hooks without controls or links.
- [ ] Run contract + renderer suites and `git diff --check`.
- [ ] Commit `feat: render recruiter screen reentry cue`.

### Task 3: Preserve routing and preparation boundaries

**Files:**
- Modify: `plugins/job-search-coach/skills/prepare-role-interviews/SKILL.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/references/networking-and-content.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/references/client-report.md`
- Test: `tests/test_full_plugin.py`, `tests/test_skill_contracts.py`

**Interfaces:**
- Documents the re-entry receipt as manual input to preparation, never as an execution packet.
- Preserves private triage precedence and all normal recruiter-reply behavior.

- [ ] Add RED integration assertions for manual re-entry, no auto-start, and no router/module packet output.
- [ ] Add concise contract wording and the exact `unanswered`/`unknown` boundary.
- [ ] Run focused integration/privacy tests and confirm normal dossier behavior remains unchanged.
- [ ] Commit `docs: route recruiter screen reentry safely`.

### Task 4: Publish and install the increment

**Files:**
- Modify mechanically only: provenance sidecars/indexes/summary and manifest version.

- [ ] Refresh provenance to the approved functional commit and plugin subtree using canonical helpers.
- [ ] Run schema, focused, privacy, static, official, diff, and full discovery gates to explicit green.
- [ ] Invoke the official cachebuster exactly once and create the release commit.
- [ ] Run post-release gates and full discovery to explicit green.
- [ ] Install the exact version and verify source/cache file identity and aggregate hash.
- [ ] Smoke clarify/ready/stop validator+renderer outputs, verify mode `0600`, remove only generated caches.
- [ ] Record the release SHA/version and keep the worktree clean.
