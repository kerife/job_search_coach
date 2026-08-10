# Recruiter handoff readiness boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Explain the three validated readiness conditions before the private recruiter handoff preview.

**Architecture:** Renderer-only change derived from the already validated `safe_context` enums. Reorder the existing handoff section after the decision and add a semantic readiness `<dl>`; no schema, routing, or provenance changes.

**Tech Stack:** Python 3.11, unittest, inline HTML/CSS.

## Global Constraints

- Ready state only; clarify/stop omit readiness and handoff.
- Use categorical fixed copy, never score or percentage.
- No identity, recruiter/company, vacancy, raw text, IDs, contacts, links, times, actions, calendar, or outcome language.

---

### Task 1: Implement and verify the readiness boundary

**Files:** renderer script, triage CSS, renderer tests.

- [ ] Add RED tests for all three ready rows, ordering after decision, clarify/stop omission, and tampered context rejection.
- [ ] Run focused renderer tests and confirm RED.
- [ ] Render fixed localized rows from validated enums and move the handoff section after the decision block.
- [ ] Add scoped `<dl>` mobile/print styles and accessible labeling.
- [ ] Run triage/renderer/privacy/diff gates and commit the feature.

### Task 2: Review and publish

- [ ] Run independent value/security/design review and fix any RED finding.
- [ ] Run full pre-release gates, refresh provenance, invoke cachebuster once, publish, install, and smoke all states.
