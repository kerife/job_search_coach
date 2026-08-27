# Triage handoff CLI and independent validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose a safe CLI and independent validator for the verified triage-to-practice handoff.

**Architecture:** Reuse `private_input_loader.py` and existing atomic private-output patterns. Keep composition in the current builder, place wrapper invariants in a dedicated validator, and make the builder CLI call both validators before writing canonical JSON.

**Tech Stack:** Python 3.11+, `argparse`, existing JSON-subset validator, private input loader, unittest.

**Spec:** `docs/superpowers/specs/2026-08-26-triage-handoff-cli-validator-design.md`

## Global Constraints

- Fail closed on every schema, provenance, privacy, and filesystem mismatch.
- Do not echo raw recruiter replies, candidate prose, IDs, URLs, paths, or secrets in CLI errors.
- Preserve existing v1 routes and fixtures; only v2 may enter this handoff.
- No network, forms, uploads, scheduling, auto-start, raw-answer persistence, or external actions.
- Commit and review every task before publishing its increment.

---

### Task 1: Independent wrapper validator

**Files:**
- Create: `plugins/professional-growth-coach/scripts/validate_private_recruiter_triage_practice_handoff.py`
- Test: `plugins/professional-growth-coach/tests/test_private_recruiter_triage_practice_handoff_validator.py`

**Interfaces:**
- Consumes: a mapping produced by `build_private_recruiter_triage_practice_handoff.build_handoff`.
- Produces: `validate_handoff(value: object) -> list[str]` and a CLI taking one input path.

- [ ] Write failing tests for a valid ES/EN wrapper, each mutated wrapper invariant, unsafe prose, and nested practice drift.
- [ ] Run the focused test and confirm import failure because the validator is absent.
- [ ] Implement schema loading, closed wrapper checks, projected-reference checks, source/scope/delivery checks, and nested `validate_session` delegation without importing the builder (avoid circular dependency).
- [ ] Add bounded private-input CLI parsing with concise JSON errors and exit status 0/1.
- [ ] Run focused tests and confirm all pass; run `py_compile` and `git diff --check`.
- [ ] Commit as `feat: add independent triage practice handoff validator`.

### Task 2: Safe builder CLI and routing contract

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/build_private_recruiter_triage_practice_handoff.py`
- Modify: `plugins/professional-growth-coach/skills/professional-growth-coach/references/routing.md`
- Modify: `plugins/professional-growth-coach/README.md`
- Test: `plugins/professional-growth-coach/tests/test_private_recruiter_triage_practice_handoff_cli.py`

**Interfaces:**
- Consumes: `validate_handoff` from Task 1 and `private_input_loader.read_bounded_bytes`.
- Produces: CLI `--input PATH --output PATH [--force]`, canonical JSON output, and stable non-sensitive errors.

- [ ] Write failing subprocess tests for ES/EN success, malformed/duplicate JSON, symlink, oversized input, v1 rejection, unsafe output, and no overwrite without `--force`.
- [ ] Run the focused tests and confirm the CLI contract is absent or fails.
- [ ] Implement unique-key decoding, bounded loader use, canonical serialization, atomic private output, validator-before-write, and JSON error envelope.
- [ ] Update routing/README to state v2-only handoff CLI/re-entry and preserve v1 legacy behavior.
- [ ] Run focused tests, full plugin suite, privacy/static/release checks, and `git diff --check`.
- [ ] Commit as `feat: expose triage practice handoff cli`.

### Task 3: Release installation and attestation

**Files:**
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json`
- Modify: `tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json`
- Modify: `tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-en.json`
- Modify: release attestation fixture(s) identified by static checks.

**Interfaces:**
- Consumes: Tasks 1–2 CLI/validator and docs.
- Produces: installed plugin version, source/cache parity record, and published `main`.

- [ ] Bump cachebuster/version, install with `codex plugin add professional-growth-coach@professional-growth-coach-local --json`, and run direct installed ES/EN builder/validator/renderer smoke.
- [ ] Bind fixture provenance to the immediate parent of the attestation commit and record `fresh_agent_smoke=not_run` unless actually evidenced.
- [ ] Run plugin suite, static, privacy, release, and root suite; re-run all post-attestation gates.
- [ ] Commit attestation, obtain independent release review, then push `git push origin HEAD:main` and verify local/remote hashes.
