# Dossier copy-button context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give each rendered dossier copy button a unique localized accessible name without changing visible copy controls.

**Architecture:** Derive the accessible label in the existing `_render_copy_blocks` loop from `COPY[locale]["copy_button"]` and the validated `COPY_LABELS` category. Keep the existing article heading IDs, status descriptions, data attributes, and JavaScript untouched.

**Tech Stack:** Python standard library, HTML string renderer, `unittest`, static/privacy/release gates.

## Global Constraints

- Visible button text remains the existing localized action label.
- Omitted copy blocks render no button and no new accessible label.
- No CSS, schema, clipboard, live-status, print, or external-action changes.
- Use TDD and verify source/cache parity after installation.

### Task 1: RED renderer contract

**Files:** `tests/test_executive_career_dossier.py`

- [ ] Add ES/EN assertions mapping each rendered `data-copy-target` to its localized category label and requiring unique contextual `aria-label` values.
- [ ] Confirm the test fails because current buttons lack contextual labels.

### Task 2: GREEN renderer change

**Files:** `plugins/professional-growth-coach/scripts/render_executive_career_dossier.py`

- [ ] Add the contextual `aria-label` attribute to the existing button string only.
- [ ] Run renderer and accessibility/parity tests until green.

### Task 3: Release verification

**Files:** `.codex-plugin/plugin.json`, `tests/evals/final/*`

- [ ] Bump, install, attest, push, and verify plugin/cache parity, full plugin suite, static/privacy, provenance, and official release validation.
