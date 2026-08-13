# Outcomes scalar diagnostic redaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent caller-controlled CSV scalar values and invalid CLI arguments from appearing in outcomes diagnostics.

**Architecture:** Keep `summarize_outcomes.py` validation and JSON contracts unchanged except for removing raw value interpolation from scalar error messages. Shared parser helpers emit stable field/row messages; tests exercise both direct CLI behavior and existing deterministic fixture expectations.

**Tech Stack:** Python standard library, `unittest`, JSON CLI, repository static/privacy/release validators.

## Global Constraints

- Preserve exit codes, JSON shape, validation order, row numbers, field names, and valid summaries.
- Do not expose CSV values, candidate identifiers, paths, credentials, or raw CLI arguments in diagnostics.
- Keep the change local to outcomes parsing and its tests/docs; no schema, renderer, CSS, or external LinkedIn action changes.
- Use TDD: failing regression tests before production edits, then focused and full plugin verification.

### Task 1: Add scalar diagnostic RED coverage

**Files:**
- Modify: `tests/test_summarize_outcomes.py`

- [ ] Add path/credential-shaped invalid date, boolean, duplicate-ID, window, and as-of cases asserting the sentinel is absent from both streams while the stable error remains.
- [ ] Update ordinary malformed-input expectations to the fixed messages.
- [ ] Run the focused outcomes suite and confirm the new assertions fail against the current interpolating implementation.

### Task 2: Remove raw scalar interpolation

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/summarize_outcomes.py`

- [ ] Replace raw value interpolation in `parse_iso_date`, `parse_boolean`, duplicate application IDs, `parse_window`, and `--as-of` validation with stable messages.
- [ ] Preserve field names, row numbers, valid-range context, and all successful summary behavior.
- [ ] Run the RED tests and full outcomes suite until green.

### Task 3: Verify and publish

**Files:**
- Modify: `.codex-plugin/plugin.json`
- Modify: `tests/evals/final/*` attestation records

- [ ] Run outcomes, plugin, static, privacy, provenance, parity/hash, and official release validation gates.
- [ ] Bump the cachebuster, install the local plugin, update attestation to the functional parent/tree/hash, and verify the active Codex plugin.
- [ ] Push the final commits and confirm clean worktree and remote parity.
