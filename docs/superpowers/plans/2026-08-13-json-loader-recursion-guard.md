# JSON Loader Recursion Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox syntax.

**Goal:** Convert decoder-level `RecursionError` crashes in five supported JSON loaders into bounded, traceback-free input errors.

**Architecture:** Preserve each loader's existing error type and message while extending only its `json.loads()` exception tuple. Add regression tests at the loader/CLI boundary using a small deeply nested JSON document. No schema, depth-limit, or dependency changes.

**Tech Stack:** Python 3.11 standard library, `unittest`, existing plugin validators and release gates.

## Global Constraints

- Catch `RecursionError` before it escapes any of the five supported JSON loaders.
- Preserve each loader's existing safe invalid-JSON/load message and CLI return code.
- Do not echo input paths, JSON content, or tracebacks.
- Do not increase `_assert_max_depth` limits or change schemas.
- Preserve duplicate-key, malformed-JSON, UTF-8, symlink, and size-limit behavior.

---

### Task 1: Add RED regression coverage for decoder recursion

**Files:**
- Modify: `plugins/professional-growth-coach/tests/test_private_input_boundaries.py` (or the existing loader-boundary test module selected after inspection)

**Interfaces:**
- Consumes: the five loader CLIs and their existing fixture/input boundaries.
- Produces: a deterministic regression matrix that fails on the published release before production changes.

- [ ] **Step 1: Write a bounded nested-JSON fixture helper and one parametrized test per loader boundary.**

Use a string of approximately 1,000 nested arrays around `0`, write it below
each loader's existing byte cap, invoke the supported CLI with required
arguments, and assert the expected nonzero input-error return, no `Traceback`,
and the existing loader-specific safe message.

- [ ] **Step 2: Run the focused tests and verify RED.**

Run the selected boundary test module with `PYTHONDONTWRITEBYTECODE=1` and
`python3 -B`. Expected result: the five new cases fail because the current
release emits `RecursionError` tracebacks/return code 1.

- [ ] **Step 3: Commit only the RED tests.**

```bash
git add plugins/professional-growth-coach/tests/test_private_input_boundaries.py
git commit -m "test: bound JSON loader recursion failures"
```

### Task 2: Add the minimal loader exception guards

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_recruiter_practice_session.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_private_recruiter_reply_triage.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_private_recruiter_conversion_outcome.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_private_recruiter_followthrough_checkpoint.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_executive_career_dossier.py`

**Interfaces:**
- Consumes: each existing `json.loads()` call and loader-specific error class.
- Produces: the same safe invalid-input error for `RecursionError`, without changing decoded-depth policy.

- [ ] **Step 1: Extend each existing decoder exception tuple.**

For each loader, add `RecursionError` to the existing `except` tuple that maps
JSON decoding and duplicate-key failures to its current safe message. Keep the
existing `from error` chaining internally; the CLI already prints only the
safe exception string.

- [ ] **Step 2: Run the new focused tests and verify GREEN.**

Run the same boundary test module. Expected result: all five deep-input cases
return their existing input-error code, contain no traceback, and preserve the
existing message.

- [ ] **Step 3: Run neighboring validator/renderer tests.**

Run the five validator modules' existing tests plus triage/practice/outcome/
checkpoint/dossier renderer suites. Confirm valid fixtures, malformed JSON,
duplicate keys, size limits, and depth-limit diagnostics remain green.

- [ ] **Step 4: Commit the minimal implementation.**

```bash
git add plugins/professional-growth-coach/scripts/validate_recruiter_practice_session.py \
  plugins/professional-growth-coach/scripts/validate_private_recruiter_reply_triage.py \
  plugins/professional-growth-coach/scripts/validate_private_recruiter_conversion_outcome.py \
  plugins/professional-growth-coach/scripts/validate_private_recruiter_followthrough_checkpoint.py \
  plugins/professional-growth-coach/scripts/validate_executive_career_dossier.py
git commit -m "fix: bound JSON loader recursion errors"
```

### Task 3: Independent review and release gates

**Files:** Read-only review of Tasks 1–2; no additional production files.

- [ ] Verify source-to-sink reproduction is closed for all five loaders, the
  safe messages are stable/non-echoing, and no depth/schema policy changed.
- [ ] Run plugin suite, static checks, privacy scanner, official release
  validation, and the full root suite; record known harness diagnostics only
  when the process still exits successfully.

### Task 4: Cachebuster, install, provenance, and publish

**Files:** Generated plugin manifest and existing final-evaluation provenance
  files only.

- [ ] Run the approved cachebuster exactly once and commit the version bump.
- [ ] Install `professional-growth-coach@professional-growth-coach-local` and
  verify source/cache file counts and normalized content parity.
- [ ] Rebind cycle provenance and installed-smoke metadata to the installed
  source commit/tree/version/timestamp/hash, then commit attestation.
- [ ] Rerun all gates and push `main` after verification; confirm local plugin
  remains installed/enabled and report the separate public identity without
  changing configuration.
