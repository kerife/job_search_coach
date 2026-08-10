# Recruiter handoff context preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended; otherwise use superpowers:executing-plans). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the validated identity-free context as the first row of the ready handoff preview.

**Architecture:** Renderer-only addition using `safe_context.summary` already validated by the closed triage contract; no schema, routing, or persistence changes.

**Tech Stack:** Python 3.11, unittest, inline HTML/CSS.

## Global Constraints

- Ready state only; clarify/stop omit the preview.
- Three rows exactly: identity-free context, verified fact, safe question.
- Escape the context; preserve all existing raw/identity/contact/calendar/action/outcome/ID protections.

---

### Task 1: Context preview row

**Files:** renderer, triage tests.

- [ ] Add RED tests for localized context row, exact ordering/count, escaping, and ready-only omission.
- [ ] Run focused tests and confirm RED.
- [ ] Render the escaped validated summary as the first preview row.
- [ ] Run triage/renderer/privacy/diff checks and commit the feature.

### Task 2: Review and publish

- [ ] Run independent value/security/design review and fix findings with RED→GREEN tests.
- [ ] Run full pre-release gates, refresh provenance, invoke cachebuster once, publish, install, and smoke all states.
