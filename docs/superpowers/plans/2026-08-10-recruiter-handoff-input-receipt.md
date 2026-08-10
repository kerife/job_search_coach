# Recruiter handoff input receipt Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the safe inputs and boundaries for manual recruiter-screen preparation re-entry.

**Architecture:** Renderer/CSS-only fixed copy nested in ready step 03; add `aria-describedby` to the existing handoff aside. No schema, routing, or persistence changes.

**Tech Stack:** Python 3.11, unittest, inline HTML/CSS.

## Global Constraints

- Ready state only; clarify/stop omit receipt.
- Allowed: identity-free role/reply summary and one verified fact.
- Forbidden: raw recruiter text/identity and calendar/contact details.
- Practice begins only after manual re-entry; no controls, links, auto-start, scores, or outcomes.

---

### Task 1: Input receipt and accessibility linkage

**Files:** renderer, triage CSS, renderer tests.

- [ ] Add RED tests for both locales, exact two allowed/two forbidden rows, ordering before preview, ready-only omission, and `aria-describedby` linkage.
- [ ] Run focused tests and confirm RED.
- [ ] Render fixed localized receipt and link the handoff description semantically.
- [ ] Add scoped responsive/print styles without changing existing sequence semantics.
- [ ] Run triage/renderer/privacy/diff checks and commit the feature.

### Task 2: Review and publish

- [ ] Run independent value/security/design review and fix findings with RED→GREEN tests.
- [ ] Run full pre-release gates, refresh provenance, invoke cachebuster once, publish, install, and smoke all states.
