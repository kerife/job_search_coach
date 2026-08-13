# Recruiter Receipt Manual Next Step Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox syntax.

**Goal:** Give route-valued conversion and follow-through receipts a clear, static manual continuation without adding external actions.

**Architecture:** Add one renderer token and one conditional template section per receipt. Reuse existing receipt CSS hooks and Superdesign parity dumps. Validator schemas and next-safe-action semantics remain unchanged.

**Tech Stack:** Python 3, existing HTML/CSS templates, `unittest`, Superdesign parity tests.

## Global Constraints

- Render only for `next_safe_action == "route_to_prepare-role-interviews"`.
- EN copy: `Return to the private Codex conversation, re-enter interview preparation manually, and answer the one safe recruiter-screen question. This receipt does not contact, send, or schedule anything.`
- ES copy: `Regresa a la conversación privada de Codex, vuelve a entrar manualmente a la preparación de entrevista y responde la única pregunta segura de filtro inicial. Este recibo no contacta, envía ni agenda nada.`
- Use a semantic named region; no buttons, forms, external links, icons, scores, raw IDs, route enum, or path interpolation.
- Preserve clarify/stop/manual omission, validator behavior, privacy, print, forced-colors, 320px reflow, and atomic writes.
- Keep `.superdesign/init/theme.md` CSS dumps exactly synchronized with both receipt CSS assets.

---

### Task 1: Add RED tests for the manual continuation contract

**Files:**
- Modify: `plugins/professional-growth-coach/tests/test_render_private_recruiter_conversion_outcome.py`
- Modify: `plugins/professional-growth-coach/tests/test_render_private_recruiter_followthrough_checkpoint.py`

**Interfaces:**
- Consumes: `render_outcome_html()` and `render_checkpoint_html()`.
- Produces: route-only EN/ES copy, omission, accessibility, and no-interaction assertions.

- [ ] Add tests first for route-valued outcome/checkpoint fixtures in both locales. Assert a named `section` appears once with the localized heading and exact copy; assert the route enum, source IDs, buttons, forms, external links, and path-like text are absent.
- [ ] Add omission tests for clarify/stop/manual actions, including the v2 UI/content-locale matrix where existing tests support it.
- [ ] Add CSS/template contract assertions for the new class in print, preferred-contrast, and forced-colors blocks, plus deterministic render and 320px no-overflow checks using existing helpers.
- [ ] Run the focused outcome/checkpoint suites and verify RED because the region is absent.
- [ ] Commit tests only as `test: define manual recruiter receipt continuation` and write a task report.

### Task 2: Implement the minimal localized render/CSS change

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/render_private_recruiter_conversion_outcome.py`
- Modify: `plugins/professional-growth-coach/scripts/render_private_recruiter_followthrough_checkpoint.py`
- Modify: `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html`
- Modify: `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html`
- Modify: `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.css`
- Modify: `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.css`
- Modify: `.superdesign/init/theme.md`

**Interfaces:**
- Consumes: existing validated `next_safe_action` and fixed locale labels.
- Produces: one conditional `receipt-manual-next-step` section per route-valued receipt.

- [ ] Add fixed EN/ES heading/body labels and replace a conditional template token with the escaped fixed section; do not interpolate input values.
- [ ] Add matching CSS in both assets using existing variables and the same print/contrast/forced-color conventions; update the raw Superdesign dump exactly.
- [ ] Run focused tests and renderer suites until GREEN, then commit as `feat: add manual recruiter receipt continuation`.

### Task 3: Independent review and full gates

- [ ] Review both implementations for route-only gating, exact localization, no interaction, no raw data, and asset/theme parity.
- [ ] Run plugin suite, static checks, privacy scanner, release validator, root suite, and focused mobile/print/forced-color contracts.

### Task 4: Cachebuster, install, provenance, and publish

- [ ] Consume the cachebuster exactly once, install local plugin, verify 109/109 source/cache parity, refresh provenance/smoke metadata, commit attestation, rerun all gates, and push `main`.
- [ ] Confirm local plugin enabled at the materialized version and leave the separate public plugin identity/configuration unchanged.
