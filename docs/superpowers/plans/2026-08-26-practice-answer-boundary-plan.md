# Practice answer boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one localized, static answer-boundary card before triage practice rehearsal.

**Architecture:** Extend the existing recruiter-practice renderer with a source-gated helper and fixed copy. Add co-located CSS rules and mirror them byte-for-byte in `.superdesign/init/theme.md`; no schema or delivery changes.

**Tech Stack:** Python 3.11+, HTML escaping, existing CSS tokens, unittest.

**Spec:** `docs/superpowers/specs/2026-08-26-practice-answer-boundary-design.md`

## Global Constraints

- Render only for `private_recruiter_reply_triage` handoffs.
- Dynamic fact text must pass existing escaping; no raw reply, IDs, URLs, buttons, forms, scripts, or external actions.
- Keep dossier/unsourced markup and historical selector groups unchanged.
- Keep CSS parity with `.superdesign/init/theme.md` and accessibility/print behavior explicit.
- Commit, independently review, install, and push each completed increment.

---

### Task 1: Guardrail renderer contract

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/render_recruiter_practice_session.py`
- Test: `plugins/professional-growth-coach/tests/test_render_recruiter_practice_session.py`

**Interfaces:**
- Consumes: validated v2 practice session and existing `COPY`/fact mapping.
- Produces: `_render_claim_guardrail(locale, fact)` static section and triage-only placement.

- [ ] Add RED tests for ES/EN triage sessions, order after `practice-question-text`, one section, escaped fact prose, no unsafe/source identifiers, and unchanged dossier/unsourced output.
- [ ] Run focused tests and confirm the guardrail is absent.
- [ ] Implement fixed localized copy and source-gated HTML using existing escaping/helpers; avoid new definition-list rows.
- [ ] Run focused renderer suite and diff-check; update report and commit `feat: show practice answer boundary`.

### Task 2: Accessible visual contract

**Files:**
- Modify: `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css`
- Modify: `.superdesign/init/theme.md`
- Test: `plugins/professional-growth-coach/tests/test_render_recruiter_practice_session.py`

**Interfaces:**
- Consumes: `.practice-claim-guardrail` markup from Task 1.
- Produces: responsive, print-safe, dark/forced-colors/high-contrast CSS with exact raw-theme parity.

- [ ] Add RED assertions for guardrail CSS selectors and media blocks.
- [ ] Implement minimal token-based rules, including max-width/mobile, dark, forced-colors, `prefers-contrast: more`, print, and reduced-motion behavior.
- [ ] Run renderer/CSS/static/privacy/release checks and exact theme parity; update report and commit `feat: style practice answer boundary`.

### Task 3: Release installation and attestation

**Files:**
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json`
- Modify: release fixture(s) identified by static checks.

**Interfaces:**
- Consumes: Tasks 1–2 renderer/CSS.
- Produces: installed plugin and published `main` with current source/cache attestation.

- [ ] Bump cachebuster, install local plugin, run installed ES/EN triage renderer smoke, and verify source/cache parity.
- [ ] Bind provenance to the immediate parent of attestation; keep `fresh_agent_smoke=not_run` unless evidenced.
- [ ] Run plugin/static/privacy/release/root suites and post-attestation gates.
- [ ] Obtain independent review, push `git push origin HEAD:main`, and verify local/remote hashes.
