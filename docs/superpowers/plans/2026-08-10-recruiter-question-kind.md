# Recruiter question kind Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended; otherwise use superpowers:executing-plans). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce and display a classification-bound question kind for private recruiter triage.

**Architecture:** Extend the closed triage schema/validator with one enum and invariant; render fixed localized labels from that enum. No routing, persistence, or external actions.

**Tech Stack:** Python 3.11, closed JSON Schema, unittest, inline HTML/CSS.

## Global Constraints

- Exact mapping: screen invite→screen_opening; proof→proof_example; eligibility→eligibility_boundary; compensation→compensation_boundary; unknown→missing_detail.
- Decline cannot be ready; clarify/stop preserve current state rules.
- No raw/identity/contact/calendar/action/score/outcome/link prose.

---

### Task 1: Closed question-kind contract

**Files:** schema, validator, ready fixtures, contract tests.

- [ ] Add RED tests for missing/unknown/mismatched kinds and valid mappings.
- [ ] Run focused contract tests and confirm RED.
- [ ] Add the enum and classification invariant to schema and validator; update ready fixtures.
- [ ] Run contract/schema/privacy/diff checks and commit.

### Task 2: Localized rendering

**Files:** renderer, renderer tests, scoped CSS if needed.

- [ ] Add RED tests for localized `Question type`, order, ready-only behavior, and unsafe-output absence.
- [ ] Implement fixed labels from validated enum and run focused renderer tests.
- [ ] Commit renderer changes.

### Task 3: Review and publish

- [ ] Run independent value/security/design review and resolve findings with RED→GREEN tests.
- [ ] Run full pre-release gates, refresh provenance, invoke cachebuster once, publish, install, and smoke all states.
