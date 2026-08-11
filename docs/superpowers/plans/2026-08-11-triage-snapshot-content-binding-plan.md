# Triage Snapshot Content Binding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add content-bound provenance to triage v2 handoffs without changing v1 compatibility.

**Architecture:** A small `triage_snapshot.py` helper canonicalizes a triage mapping after removing only duplicated handoff snapshot fields and returns a versioned SHA-256 identifier. The v2 validator and schema require that identifier; v1 remains on the existing opaque format. Renderers consume validated triage but never render provenance handles.

**Tech Stack:** Python 3.11 standard library (`hashlib`, `json`, `copy`), JSON Schema draft 2020-12, `unittest`.

## Global Constraints

- Preserve v1 `snap-triage-###` fixtures and behavior exactly.
- Hash canonical UTF-8 JSON with sorted keys, compact separators, and `ensure_ascii=False`.
- Remove only `handoff.packet.source_snapshot` and `handoff.reentry_packet.source_snapshot` before hashing.
- Keep errors bounded; never echo raw triage text or digest values.
- Do not publish or modify the installed plugin cache.

### Task 1: Specify the v2 contract and write RED tests

**Files:**
- Create: `docs/superpowers/specs/2026-08-11-triage-snapshot-content-binding-design.md`
- Create: `docs/superpowers/plans/2026-08-11-triage-snapshot-content-binding-plan.md`
- Modify: `tests/test_private_recruiter_reply_triage.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

- [ ] Add tests for a known v2 content-bound snapshot, digest mismatch after summary mutation, schema acceptance, v1 compatibility, and renderer no-echo.
- [ ] Run focused tests and confirm RED failures are caused by the missing v2 hash contract, not test setup.

### Task 2: Implement the canonical helper and v2 validator binding

**Files:**
- Create: `plugins/professional-growth-coach/scripts/triage_snapshot.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_private_recruiter_reply_triage.py`

- [ ] Implement `snapshot_for_triage(triage: Mapping[str, object]) -> str` with the canonicalization rules above.
- [ ] For v2 only, validate both packet snapshots against the helper; keep v1 regex checks unchanged.
- [ ] Run the focused validator tests and confirm GREEN.

### Task 3: Bind the v2 JSON schema and verify renderer/privacy parity

**Files:**
- Modify: `plugins/professional-growth-coach/schemas/private-recruiter-reply-triage-v2.schema.json`
- Modify: `tests/test_private_recruiter_reply_triage.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

- [ ] Change only v2 packet/reentry snapshot patterns to the hash-bound format.
- [ ] Assert v2 schema and Python validator agree on valid and mutated cases.
- [ ] Assert v2 HTML renderer omits the internal snapshot and digest.
- [ ] Run focused tests, plugin private tests, static checks, and the full repository test subset that covers triage.

### Task 4: Commit the bounded increment

**Files:** all files above.

- [ ] Review the diff for v1 compatibility, no-echo, and unrelated changes.
- [ ] Commit with `feat: bind triage v2 snapshots to content`.
- [ ] Do not publish or refresh the installed cache in this cycle.
