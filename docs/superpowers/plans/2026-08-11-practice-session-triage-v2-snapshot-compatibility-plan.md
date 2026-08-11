# Practice Session v2 Triage Snapshot Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permit the new triage v2 content-bound snapshot in practice-session v2 while preserving practice-session v1 behavior.

**Architecture:** Extend the practice validator's v2-only source pattern and mirror that allowance in practice-session v2 JSON Schema. Do not compute or expose the digest; triage remains the provenance authority. Add focused parity tests for v1 rejection, v2 acceptance, malformed rejection, and renderer no-echo.

**Tech Stack:** Python 3.11 standard library, JSON Schema draft 2020-12, `unittest`.

## Global Constraints

- v1 practice-session pattern remains exactly `snap-triage-###`.
- v2 practice-session triage source accepts `snap-triage-###` or `snap-triage-sha256-[0-9a-f]{64}`.
- Dossier source accepts only the existing bound dossier format.
- Do not recompute, render, log, or echo the digest.
- Do not bump version, publish, install, or modify cache.

### Task 1: Write RED parity and schema tests

**Files:**
- Create: `docs/superpowers/specs/2026-08-11-practice-session-triage-v2-snapshot-compatibility-design.md`
- Create: `docs/superpowers/plans/2026-08-11-practice-session-triage-v2-snapshot-compatibility-plan.md`
- Modify: `tests/test_recruiter_practice_session.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

- [ ] Convert the existing session fixture to v2 and assert the triage SHA-256 handle is accepted by both validator and v2 schema.
- [ ] Assert v1 rejects the same SHA-256 handle while legacy `snap-triage-001` remains accepted.
- [ ] Assert malformed v2 handles fail closed and no snapshot value is echoed.
- [ ] Run the focused tests and record the expected RED failure from the legacy v2 pattern.

### Task 2: Implement the v2-only compatibility allowance

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_recruiter_practice_session.py`
- Modify: `plugins/professional-growth-coach/schemas/recruiter-practice-session-v2.schema.json`

- [ ] Use a v2-only regex branch for triage source snapshots.
- [ ] Keep the v1 validator/schema patterns unchanged.
- [ ] Do not import the triage snapshot helper or recompute a digest.
- [ ] Run the focused tests and verify GREEN.

### Task 3: Verify the bounded increment

**Files:** no additional files.

- [ ] Run focused practice-session and schema tests, then plugin tests and static checks.
- [ ] Run `git diff --check` and inspect that no renderer/source/cache files changed.
- [ ] Commit with `fix: accept triage v2 snapshots in practice sessions`.
