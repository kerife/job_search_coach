# Recruiter question purpose Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended; otherwise use superpowers:executing-plans). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Explain the decision purpose of the one safe recruiter-screen question.

**Architecture:** Renderer-only fixed localized mapping from validated classification; no schema/routing/persistence changes.

**Tech Stack:** Python 3.11, unittest, inline HTML/CSS.

## Global Constraints

- Ready state only; clarify/stop omit purpose.
- Exactly one question remains; purpose text contains no question mark.
- No raw/identity/contact/calendar/action/outcome/link/score text.

---

### Task 1: Purpose cue

**Files:** renderer, triage tests, scoped CSS if needed.

- [ ] Add RED tests for all ready classifications ES/EN, purpose ordering, no extra question marks, and ready-only omission.
- [ ] Run focused tests and confirm RED.
- [ ] Implement fixed localized purpose mapping and semantic labeling.
- [ ] Run triage/renderer/privacy/diff checks and commit the feature.

### Task 2: Review and publish

- [ ] Run independent value/security/design review and fix findings with RED→GREEN tests.
- [ ] Run full pre-release gates, refresh provenance, invoke cachebuster once, publish, install, and smoke all states.
