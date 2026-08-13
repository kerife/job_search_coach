# Identity-free triage unlabeled-name Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent ordinary unlabeled personal-name prose from entering identity-free triage artifacts while preserving legitimate role-focused prose.

**Architecture:** Extend the triage validator's existing `unlabelled_identity` regex with the bounded verb family already established by the dossier practice identity-free guard. Add API/CLI and renderer regression tests across every prose field; leave rendering and CSS unchanged because validation must fail before persistence.

**Tech Stack:** Python `unittest`, triage validator/renderer, offline HTML output, local Codex plugin release tooling.

## Global Constraints

- Modify only `validate_private_recruiter_reply_triage.py` and its focused tests until release metadata is intentionally updated.
- Preserve the fixed diagnostic category `session contains forbidden unlabelled_identity prose`; never echo the name.
- Preserve existing accepted role-focused prose such as `Platform engineering work includes incident response practice.`
- No HTML/CSS/template/schema/Superdesign changes.

---

### Task 1: Add RED identity-boundary tests

**Files:**
- Modify: `tests/test_private_recruiter_reply_triage.py`
- Modify: `tests/test_render_private_recruiter_reply_triage.py` only if the renderer rejection assertion is not already covered

**Interfaces:**
- Consumes: `validate_triage()` and `render_triage_html()`.
- Produces: failing tests for ordinary English/Spanish full-name sentences in `safe_context.summary`, facts, question, and blocked claims.

- [ ] **Step 1: Write the failing test**

Use the existing fixture helpers and prose-field loops to assert that these
sentences are rejected with the fixed category and that the sentinel names are
absent from CLI/renderer errors:

```python
sentences = (
    "John Smith has a verified technical achievement.",
    "Juan Pérez tiene un logro técnico verificado.",
)
```

Add one renderer assertion using the English sentence in a valid triage payload
and assert `render_triage_html()` raises `TriageValidationError` without the
name in the exception text.

- [ ] **Step 2: Run RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_private_recruiter_reply_triage -k unlabelled_name
```

Expected: FAIL because the current validator returns no `unlabelled_identity`
error and the renderer accepts the payload.

- [ ] **Step 3: Commit RED tests**

```bash
git add tests/test_private_recruiter_reply_triage.py tests/test_render_private_recruiter_reply_triage.py
git commit -m "test: reject unlabeled triage names"
```

### Task 2: Implement the minimal validator guard

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_private_recruiter_reply_triage.py`

**Interfaces:**
- Consumes: RED tests from Task 1.
- Produces: deterministic `unlabelled_identity` errors before renderer output.

- [ ] **Step 1: Extend the existing pattern only**

Add the established verb variants to the existing `unlabelled_identity` regex;
do not introduce a new name detector, alter diagnostics, or broaden the
company/action patterns. Keep the existing regex's capitalization and Latin
script boundaries.

- [ ] **Step 2: Run GREEN and compatibility tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_private_recruiter_reply_triage tests.test_render_private_recruiter_reply_triage -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins.professional-growth-coach.tests.test_private_recruiter_reply_triage -q
git diff --check
```

Expected: all existing identity, role-focused, renderer, and CLI tests pass.

- [ ] **Step 3: Commit GREEN**

```bash
git add plugins/professional-growth-coach/scripts/validate_private_recruiter_reply_triage.py tests/test_private_recruiter_reply_triage.py tests/test_render_private_recruiter_reply_triage.py
git commit -m "fix: close unlabeled triage identity prose"
```

### Task 3: Verify and publish the increment

**Files:**
- Modify: release manifest/version and final provenance files only through the established release workflow.

**Interfaces:**
- Consumes: green validator/tests from Task 2.
- Produces: installed local plugin version, exact source/cache parity, current attestation, and pushed `main`.

- [ ] **Step 1: Run pre-cachebuster gates**

Run triage API/CLI/render suites, full plugin and root suites, static/privacy checks, release validation, and `git diff --check`. Do not bump while any gate is red.

- [ ] **Step 2: Bump/install/attest once**

Run the official cachebuster once, install `professional-growth-coach@professional-growth-coach-local`, compute source/cache counts and normalized hash, and update cycle-1/cycle-2 provenance plus installed-smoke.

- [ ] **Step 3: Re-run and publish**

Run post-cachebuster gates, commit attestation, push `main`, verify local refs and cache parity, and report the persistent dual-plugin identity caveat without modifying Codex configuration.
