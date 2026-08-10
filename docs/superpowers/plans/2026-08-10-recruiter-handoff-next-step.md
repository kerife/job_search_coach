# Recruiter handoff next step Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one clear, static manual next-step cue to the ready recruiter handoff.

**Architecture:** Renderer-only fixed localized copy inside the existing handoff rail. No schema, routing, action, or persistence changes.

**Tech Stack:** Python 3.11, unittest, inline HTML/CSS.

## Global Constraints

- Ready state only; clarify/stop omit the cue.
- No button, link, form, auto-start, send, calendar, time, score, outcome, identity, raw text, or internal ID.
- Copy says only to re-enter private preparation manually and answer the one safe question.

---

### Task 1: Static next-step cue

**Files:** renderer, triage CSS, renderer tests.

- [ ] Add RED tests for localized ready copy/order, omission outside ready, and no interactive/actionable markup.
- [ ] Run focused tests and confirm RED.
- [ ] Add fixed localized section after focus and before preview; escape no interpolated values.
- [ ] Add scoped mobile/print styles and semantic label.
- [ ] Run triage/renderer/privacy/diff checks and commit the feature.

### Task 2: Review and publish

- [ ] Run independent value/security/design review and resolve findings with RED→GREEN tests.
- [ ] Run full pre-release gates, refresh provenance, invoke cachebuster once, publish, install, and smoke all states.
