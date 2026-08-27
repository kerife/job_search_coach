# Triage handoff wrapper renderer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render a validated triage-practice handoff wrapper directly to a private HTML artifact.

**Architecture:** Add a wrapper-specific CLI that loads and validates the closed wrapper, extracts its nested session in memory, and calls the existing renderer through an optional delivery-context parameter. The optional context adds one static localized status block; direct session rendering remains unchanged.

**Tech Stack:** Python 3.11+, existing private loader/atomic writer, JSON-subset validator, HTML escaping, unittest.

**Spec:** `docs/superpowers/specs/2026-08-26-triage-handoff-wrapper-renderer-design.md`

## Global Constraints

- Validate wrapper before rendering; never accept a bare session as wrapper proof.
- Fail closed on provenance, delivery, prose, input, output, and permission mismatches.
- Errors and success receipts never echo paths, arguments, IDs, URLs, raw replies, questions, or diagnostics.
- No network, forms, scripts, uploads, scheduling, auto-start, raw-answer persistence, or external actions.
- Preserve direct `render_recruiter_practice_session.py` behavior and historical markup.

---

### Task 1: Wrapper renderer CLI and delivery context

**Files:**
- Create: `plugins/professional-growth-coach/scripts/render_private_recruiter_triage_practice_handoff.py`
- Modify: `plugins/professional-growth-coach/scripts/render_recruiter_practice_session.py`
- Test: `plugins/professional-growth-coach/tests/test_render_private_recruiter_triage_practice_handoff.py`

**Interfaces:**
- Consumes: `validate_handoff`, `private_input_loader`, `render_session_html(session, handoff_delivery=None)`.
- Produces: explicit CLI `HANDOFF.json --output OUT.html [--force]`, minimal JSON receipt, and wrapper-only status block.

- [ ] Add RED subprocess/API tests for ES/EN valid wrapper, session/render parity, delivery/provenance drift, unsafe prose, duplicate/deep/oversized/symlink inputs, overwrite/force, permissions, and error redaction.
- [ ] Run focused tests and confirm the new entrypoint is absent.
- [ ] Implement bounded unique-key load, private parser, validator-before-render, in-memory projection, optional renderer delivery context, static localized status, and atomic output.
- [ ] Run focused suite, plugin suite, privacy/release checks, `py_compile`, and `git diff --check`; update report and commit `feat: render triage handoff wrapper`.

### Task 2: Documentation and release installation

**Files:**
- Modify: `plugins/professional-growth-coach/README.md`
- Modify: `plugins/professional-growth-coach/skills/professional-growth-coach/references/routing.md`
- Modify: `plugins/professional-growth-coach/skills/prepare-role-interviews/references/interview-map.md`
- Modify: release fixture(s) identified by static checks.

**Interfaces:**
- Consumes: Task 1 CLI and delivery status.
- Produces: documented manual invocation and release-ready provenance.

- [ ] Document wrapper→HTML as an explicit manual re-entry step, preserving v1 legacy route and no-action boundary.
- [ ] Run documentation/static/privacy/release checks and commit `docs: document triage wrapper renderer`.

### Task 3: Install, attest, and publish

**Files:**
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json`
- Modify: final evaluation/installed-smoke attestation fixtures.

**Interfaces:**
- Consumes: Tasks 1–2.
- Produces: installed plugin, source/cache parity, attested release, and published `main`.

- [ ] Bump cachebuster, install local plugin, run installed ES/EN wrapper→HTML smoke and verify 0600 output/parity.
- [ ] Bind provenance to the immediate parent of attestation; preserve `fresh_agent_smoke=not_run` absent real evidence.
- [ ] Run plugin/static/privacy/release/root and post-attestation gates.
- [ ] Obtain independent review, push `git push origin HEAD:main`, and verify local/remote hashes.
