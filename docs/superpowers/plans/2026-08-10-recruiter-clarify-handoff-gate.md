# Recruiter clarify handoff gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended; otherwise use superpowers:executing-plans). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic clarify-only explanation of the evidence category blocking private handoff.

**Architecture:** Renderer-only fixed localized mapping from validated state/context/fact enums; no schema, routing, or persistence changes.

**Tech Stack:** Python 3.11, unittest, inline HTML/CSS.

## Global Constraints

- Cue appears only for `clarify_first`; ready/stop remain unchanged.
- Never render `blocked_claims` or arbitrary user prose as the blocker.
- Exactly one question, no controls, links, actions, scores, identity, raw text, contact, calendar, or outcome.

---

### Task 1: Clarify gate cue

**Files:** renderer, triage tests, scoped CSS if needed.

- [ ] Add RED tests for candidate-reported, missing-context, and generic blocker mappings in ES/EN, ordering, omission, and one-question invariant.
- [ ] Run focused tests and confirm RED.
- [ ] Implement deterministic fixed copy and semantic labeling.
- [ ] Run triage/renderer/privacy/diff checks and commit.

### Task 2: Review and publish

- [ ] Run independent value/security/design review and fix findings with RED→GREEN tests.
- [ ] Run full pre-release gates, refresh provenance, invoke cachebuster once, publish, install, and smoke all states.
