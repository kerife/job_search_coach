# Practice Snapshot Prose-Scan Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop privacy prose scanning from misclassifying valid triage v2 snapshot hashes while preserving structural validation.

**Architecture:** Keep the existing handoff validator and schema unchanged. Make the recursive prose collector field-aware and omit only `handoff_context.source_snapshot`; add a deterministic regression fixture with a real triage v2 hash containing a decimal run, plus v1, malformed, ordinary-prose, and renderer no-echo coverage.

**Tech Stack:** Python 3.11 standard library and `unittest`.

## Global Constraints

- Exclude only `handoff_context.source_snapshot` from `_validate_prose_safety`.
- Preserve v1/v2 structural regexes, source checks, and no-echo behavior.
- Do not recompute or validate the digest in practice-session code.
- Do not bump version, publish, install, or modify cache.

### Task 1: Write RED regression tests

**Files:**
- Create: `docs/superpowers/specs/2026-08-11-practice-snapshot-prose-scan-boundary-design.md`
- Create: `docs/superpowers/plans/2026-08-11-practice-snapshot-prose-scan-boundary-plan.md`
- Modify: `tests/test_recruiter_practice_session.py`
- Modify: `tests/test_render_recruiter_practice_session.py`

- [ ] Add a v2 session using hash `snap-triage-sha256-9cfca8aaaeb249e38dbeee70bbbcd3189173398fea1c3f9baee95fa0e56b3af0` and assert acceptance.
- [ ] Assert an ordinary question containing forbidden identity prose still fails and the digest is not echoed.
- [ ] Assert the rendered v2 practice card omits the hash.
- [ ] Run the focused tests and confirm RED is the current false-positive prose error.

### Task 2: Implement the field-aware prose boundary

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_recruiter_practice_session.py`

- [ ] Change `_walk_strings` to carry the current field name and skip only `source_snapshot` under `handoff_context`.
- [ ] Keep all other fields recursively scanned and leave structural validation untouched.
- [ ] Run focused tests and verify GREEN.

### Task 3: Verify and commit

- [ ] Run practice, renderer, plugin, and static checks.
- [ ] Run `git diff --check` and verify only the planned files changed.
- [ ] Commit `fix: exclude provenance handle from practice prose scan`.
