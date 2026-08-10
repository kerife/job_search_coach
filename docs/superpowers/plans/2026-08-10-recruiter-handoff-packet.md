# Recruiter handoff packet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended; otherwise use superpowers:executing-plans). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a closed, identity-free ready-only handoff packet linking context, verified fact, safe question, and preparation scope.

**Architecture:** Extend the triage schema/validator with a packet derived from existing validated fields; render a fixed localized scope receipt. No routing execution, persistence, or external actions.

**Tech Stack:** Python 3.11, closed JSON Schema, unittest, inline HTML/CSS.

## Global Constraints

- Ready only; clarify/stop omit packet.
- Packet fields: exact context summary, sole verified fact ID, sole question ID, mapped prep scope.
- No raw/identity/contact/calendar/link/action/score/outcome/auto-start fields.

---

### Task 1: Packet contract

**Files:** schema, validator, fixtures, contract tests.

- [ ] Add RED tests for missing/extra packet, mismatched IDs/kind/scope, candidate-reported fact, and valid mappings.
- [ ] Run focused contract tests and confirm RED.
- [ ] Add closed schema/validator bindings and update ready fixtures.
- [ ] Run contract/schema/privacy/diff checks and commit.

### Task 2: Packet rendering

**Files:** renderer, renderer tests, scoped CSS if needed.

- [ ] Add RED tests for localized preparation scope, ready-only presence, and no unsafe/interactivity output.
- [ ] Render fixed scope labels from validated packet values and run focused tests.
- [ ] Commit renderer changes.

### Task 3: Review and publish

- [ ] Run independent value/security/design review and resolve findings with RED→GREEN tests.
- [ ] Run full pre-release gates, refresh provenance, invoke cachebuster once, publish, install, and smoke all states.
