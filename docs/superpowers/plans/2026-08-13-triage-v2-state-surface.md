# Triage v2 Answer-Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a ready-only, localized answer-path scaffold to private recruiter triage and prove it across v2 states/locales.

**Architecture:** Extend the renderer's fixed `COPY` table with three localized labels per answer-path family. Render one semantic card only when `handoff_allowed` is true, keyed by the already validated question kind. Add CSS using existing triage, print, and forced-color conventions; keep the v2 state matrix in renderer tests.

**Tech Stack:** Python 3.11 standard library `unittest`, inline HTML/CSS, existing private asset loader.

## Global Constraints

- No schema, fixture, or external-action changes.
- No raw answers, IDs, snapshots, recruiter identity, URLs, forms, controls, scores, or auto-start language.
- Keep v1 behavior and v2 `ui_locale`/`content_locale` separation intact.
- The card is a draft-only reading aid; it does not persist or submit anything.

### Task 1: Write the failing contract tests

**Files:**
- Modify: `tests/test_render_private_recruiter_reply_triage.py`

- [ ] Add `test_ready_handoff_renders_one_answer_path_and_non_ready_omits_it`.

For each canonical ready fixture, assert one
`triage-handoff-answer-path`, a resolved `aria-labelledby` heading, three list
steps, no form/control/link tags, and the correct kind-specific English/Spanish
copy. For clarify and stop fixtures assert the card is absent.

- [ ] Add `test_v2_state_surface_matrix`.

Deep-copy each fixture into v2 for `(en, es)` and `(es, en)`, remove `locale`,
bind ready snapshots, and assert question cardinality, document language, and
content-language attributes for all three states.

- [ ] Run the two new tests and confirm RED because the card does not yet
  exist.

### Task 2: Implement the fixed localized answer path

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/render_private_recruiter_reply_triage.py`

- [ ] Add fixed `answer_path_title` and three step labels for each locale and
  question-kind family.
- [ ] Add a mapping from validated question kind to a fixed copy-key family;
  unknown kinds must never be interpolated into HTML.
- [ ] Render the card inside the existing ready-only handoff, after the safe
  question preview, as `<section class="triage-handoff-answer-path" ...>` with
  an `<ol>` of exactly three `<li>` items.
- [ ] Run focused tests and confirm GREEN.

### Task 3: Style and verify the card

**Files:**
- Modify: `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.css`
- Modify: `.superdesign/init/theme.md`

- [ ] Add scoped card, list, print `break-inside: avoid`, responsive, and
  forced-colors system-border rules matching existing triage handoff styles.
- [ ] Synchronize the exact CSS dump in `theme.md`.
- [ ] Run renderer, dark/parity/print, `git diff --check`, and plugin tests.

### Task 4: Review and publish

- [ ] Run independent security and UX/value review against the exact diff.
- [ ] Fix only review findings with RED→GREEN tests.
- [ ] Refresh provenance, invoke the official cachebuster exactly once, install
  the resulting version, compare source/cache trees and normalized hash, smoke
  ready/clarify/stop in both locales, and rerun release/static/privacy gates.
- [ ] Commit release metadata, push `main`, and leave the worktree clean.
