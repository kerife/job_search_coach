# Recruiter Practice Session Implementation Plan

> Execute with TDD and independent review after each task.

**Goal:** Build a separate validated private practice-session artifact for one vacancy-backed recruiter-screen question, with observed-answer-only feedback.

## Constraints

- Do not change executive dossier schema v1 or public LinkedIn behavior.
- No recruiter identity/contact, raw source text, outcome promise, numeric readiness, or external action.
- Reuse existing interview rubric semantics; keep session inputs identity-free and local.

## Task 1 — Define closed session contract and fixtures

Files: `plugins/job-search-coach/schemas/`, `plugins/job-search-coach/scripts/`, `tests/`, a new fixture under `tests/evals/with-skill/fixtures/`.

1. Add RED tests for valid ready/awaiting/feedback states, missing vacancy/facts, malformed references, unsupported claims, raw identity, and external-action prose.
2. Define a closed JSON schema for one session: safe context, one requirement, one question, supplied facts, optional observed answer, rubric criterion, feedback, and draft-only/privacy flags.
3. Implement fail-closed validator and CLI. Before an answer, score is exactly `unknown`; after a supplied answer, feedback references only observed answer and rubric.
4. Run focused schema/validator tests and commit `feat: add private recruiter practice contract`.

## Task 2 — Render the session artifact

Files: `render_recruiter_practice_session.py`, scoped CSS/template assets, renderer tests.

1. Add RED tests for ES/EN context, prompt, awaiting-answer state, feedback state, no IDs/raw text, no-action footer, mode 0600, and deterministic bytes.
2. Implement an offline self-contained HTML renderer with one full-width session section, explicit state chip, labelled prompt, evidence points, safe boundary, and feedback only when an observed answer exists.
3. Add responsive, reduced-motion, and print rules; reject symlink/unsafe outputs using the existing atomic-output pattern.
4. Run focused renderer/accessibility/privacy tests and commit `feat: render private recruiter practice sessions`.

## Task 3 — Integrate skill routing without disturbing dossier v1

Files: `skills/prepare-role-interviews/SKILL.md` and references, root routing/client-report contracts, integration tests.

1. Add RED routing assertions: explicit practice request plus vacancy/facts selects the private session; missing inputs asks one concise question; normal LinkedIn dossier remains unchanged.
2. Document one-question/one-answer sequencing, no-score-before-answer, no-save-by-default, and no-action boundaries.
3. Run skill/full-plugin/privacy/static tests and an independent value/security review. Fix findings with RED regressions.
4. Commit `feat: route private recruiter practice sessions`.

## Task 4 — Publish and load

1. Refresh deterministic provenance to the final functional parent only.
2. Run schema/privacy/static/full/official gates.
3. Run the official cachebuster exactly once preserving base `0.2.0`.
4. Commit manifest/provenance release changes, rerun post-commit gates, install with `codex plugin add job-search-coach@job-search-coach-local`, verify source/cache identity, and run installed smoke for ready/awaiting/feedback states.
