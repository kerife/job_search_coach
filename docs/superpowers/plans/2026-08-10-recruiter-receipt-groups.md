# Recruiter receipt groups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the ready handoff input receipt into explicit allowed and forbidden groups.

**Architecture:** Renderer/CSS-only markup restructuring; no schema, routing, provenance, or persistence changes.

**Tech Stack:** Python 3.11, unittest, inline HTML/CSS.

## Global Constraints

- Ready state only; clarify/stop omit receipt.
- Fixed identity-free copy only; no controls, links, actions, scores, raw text, identity, contact, calendar, or outcomes.
- Preserve existing manual re-entry, sequence, and preview behavior.

---

### Task 1: Grouped receipt

**Files:** renderer, triage CSS, renderer tests.

- [ ] Add RED tests for two labelled groups, localized headings/order, four rows, omission outside ready, and accessibility linkage.
- [ ] Run focused tests and confirm RED.
- [ ] Implement two semantic labelled lists with fixed copy and scoped styles.
- [ ] Run triage/renderer/privacy/diff checks and commit the feature.

### Task 2: Review and publish

- [ ] Run independent value/security/design review and fix findings with RED→GREEN tests.
- [ ] Run full pre-release gates, refresh provenance, invoke cachebuster once, publish, install, and smoke all states.
