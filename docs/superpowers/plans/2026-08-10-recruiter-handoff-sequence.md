# Recruiter handoff sequence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Structure the ready recruiter handoff as a three-step semantic decision sequence.

**Architecture:** Renderer/CSS-only wrapper around existing validated sections; no schema, routing, or provenance changes.

**Tech Stack:** Python 3.11, unittest, inline HTML/CSS.

## Global Constraints

- Steps appear only in ready state and preserve existing localized content.
- Fixed labels: `01 Conditions`, `02 Focus`, `03 Manual re-entry`.
- Preview remains an inset; no controls, links, actions, scores, identity, raw text, or new fields.

---

### Task 1: Semantic sequence

**Files:** renderer, triage CSS, renderer tests.

- [ ] Add RED tests for ordered-list structure, labels/order, preview nesting, ready-only omission, and forced-colors hook.
- [ ] Run focused tests and confirm RED.
- [ ] Wrap existing sections in semantic `<ol>/<li>` with fixed localized labels and preserve existing IDs/ARIA labels.
- [ ] Add scoped responsive/print/forced-colors styles.
- [ ] Run triage/renderer/privacy/diff checks and commit the feature.

### Task 2: Review and publish

- [ ] Run independent value/security/design review and fix any findings with RED→GREEN tests.
- [ ] Run full pre-release gates, refresh provenance, invoke cachebuster once, publish, install, and smoke all states.
