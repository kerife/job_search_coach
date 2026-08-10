# Recruiter next safe action Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended; otherwise use superpowers:executing-plans). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a state-bound, non-executable `next_safe_action` enum to private recruiter triage.

**Architecture:** Extend the closed schema/validator and fixtures with one enum; render fixed localized copy from it. No routing, persistence, or external action changes.

**Tech Stack:** Python 3.11, closed JSON Schema, unittest, inline HTML/CSS.

## Global Constraints

- Exact mapping: clarify→clarify_context_before_private_prep; ready→manual_reenter_private_prep; stop→record_stop_decision.
- Missing, unknown, and mismatched values fail closed.
- Copy remains static and informational; no controls, links, contact, calendar, time, score, guarantee, or outcome.

---

### Task 1: Closed state-bound contract

**Files:** schema, validator, fixtures, contract tests.

- [ ] Add RED tests for missing/unknown/mismatched values and valid mappings.
- [ ] Run focused contract tests and confirm RED.
- [ ] Add enum, state conditionals, fixture fields, and validator mirror.
- [ ] Run contract/schema/privacy/diff checks and commit.

### Task 2: Localized rendering

**Files:** renderer, renderer tests, scoped CSS if needed.

- [ ] Add RED tests for localized state copy and ready/clarify/stop presence/order.
- [ ] Implement fixed labels from validated enum and run focused renderer tests.
- [ ] Commit renderer changes.

### Task 3: Review and publish

- [ ] Run independent value/security/design review and fix findings with RED→GREEN tests.
- [ ] Run full pre-release gates, refresh provenance, invoke cachebuster once, publish, install, and smoke all states.
