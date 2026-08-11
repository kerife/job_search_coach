# Print-safe practice and triage surfaces Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure printed practice and triage artifacts are legible and do not capture an entrance animation frame.

**Architecture:** Add print-only declarations to the two existing CSS assets and keep renderer output unchanged. Add focused root renderer assertions and synchronize the corresponding Superdesign raw dumps; no schema, data, or action changes.

**Tech Stack:** CSS, Python `unittest`, existing offline renderers and static gates.

## Global Constraints

- Preserve all EN/ES copy and employment-continuity boundaries.
- Keep `@media (prefers-reduced-motion: reduce)` and forced-colors rules intact.
- Do not add controls, links, scripts, remote resources, or external actions.

---

### Task 1: Add RED print-contract tests

**Files:**
- Modify: `tests/test_render_recruiter_practice_session.py`
- Modify: `tests/test_render_private_recruiter_reply_triage.py`

- [ ] Add assertions for practice next-action ink/border and print animation reset.
- [ ] Add assertions for triage-card print animation/transform/transition reset.
- [ ] Run the focused tests and confirm they fail before CSS changes.

### Task 2: Implement the CSS-only GREEN fix

**Files:**
- Modify: `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css`
- Modify: `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.css`
- Modify: `.superdesign/init/theme.md`

- [ ] Add the print declarations from the design spec, preserving state marker width.
- [ ] Copy the exact resulting CSS into the two theme dumps.
- [ ] Run focused tests, plugin tests, and theme/source parity.

### Task 3: Verify and publish

- [ ] Run privacy, static, release, plugin, and root suites.
- [ ] Bump cache once, install the exact canonical version, compare source/cache,
  run five installed smokes, update attestation, and bind final eval provenance.
- [ ] Re-run final gates and record the next bounded opportunity.
