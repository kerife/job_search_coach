# Recruiter readiness focus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve ready-handoff scan semantics and provide one safe classification-driven preparation focus.

**Architecture:** Renderer-only fixed-copy mapping from validated classification; split readiness definition-list labels from values. No schema, routing, or provenance changes.

**Tech Stack:** Python 3.11, unittest, inline HTML/CSS.

## Global Constraints

- Ready state only; clarify/stop omit focus and handoff.
- Fixed localized copy only; no raw reply, IDs, contacts, links, times, actions, scores, or outcome language.
- `unknown` and `decline` use safe generic/stop copy; normal dossier behavior is unchanged.

---

### Task 1: Renderer semantics and focus

**Files:** renderer script, triage CSS, renderer tests.

- [ ] Add RED tests for category/value `<dt>/<dd>` semantics and all six classification focus mappings in ES/EN.
- [ ] Run focused tests and confirm RED.
- [ ] Implement fixed localized focus mapping and split readiness rows without interpolating unsafe prose.
- [ ] Add scoped CSS only if needed for readable focus text and mobile/print behavior.
- [ ] Run triage/renderer/privacy/diff gates and commit the feature.

### Task 2: Review and publish

- [ ] Run independent value/security/design review and resolve any findings with RED→GREEN tests.
- [ ] Run full pre-release gates, refresh provenance, invoke cachebuster once, publish, install, and smoke all states.
