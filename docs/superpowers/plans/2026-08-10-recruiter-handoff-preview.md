# Recruiter handoff preparation preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render a ready-only, identity-free preview of the verified recruiter-screen fact and single safe question in the existing private triage handoff.

**Architecture:** Keep the closed triage schema and routing contract unchanged; derive a semantic preview from validated fields in the existing renderer. Add scoped CSS and regression tests for ready-only output, safety, accessibility, print, and deterministic behavior.

**Tech Stack:** Python 3.11 standard library, unittest, inline HTML/CSS, existing privacy/static gates.

## Global Constraints

- Preview appears only for `ready_for_private_prep`.
- It contains exactly one verified fact and one question already accepted by the validator.
- No raw reply, identity, company, contact, URL, time, internal ID, score, action, link, button, auto-start, or outcome promise.
- Clarify/stop and normal dossier routes are unchanged.

---

### Task 1: Renderer preview

**Files:** `plugins/job-search-coach/scripts/render_private_recruiter_reply_triage.py`, `plugins/job-search-coach/assets/private-recruiter-reply-triage-v1.css`, `tests/test_render_private_recruiter_reply_triage.py`

- [ ] Add RED tests for ready ES/EN semantic `dl`, exact fact/question, clarify/stop omission, escaping, and no forbidden output.
- [ ] Run the focused renderer tests and confirm RED.
- [ ] Add the localized preview markup from validated fields only.
- [ ] Add scoped mobile/print/accessibility styles with `break-inside: avoid` and visible labels.
- [ ] Run the focused renderer/privacy tests and commit `feat: show recruiter handoff preview`.

### Task 2: Independent review and release

**Files:** inspect Task 1 diff; release-owned provenance/manifest only during publication.

- [ ] Run independent value, security, and design review; add RED→GREEN fixes for any disclosure or state bypass.
- [ ] Run full schema, focused, full, privacy, static, official, and diff gates.
- [ ] Refresh provenance, invoke cachebuster exactly once, publish, install, and smoke ready/clarify/stop.
