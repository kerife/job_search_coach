# Triage and Practice Diagnostic Key Redaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent private triage/practice validators from echoing sensitive-looking unknown field names in diagnostics.

**Architecture:** Add one pure sanitizer in `private_prose_safety.py`; both validators call it at their existing closed-mapping diagnostic boundary. Ordinary short field names remain unchanged, while suspicious names become `<redacted-field>`.

**Tech Stack:** Python 3.11+, `re`, `unittest`, existing offline validators/renderers.

## Global Constraints

- Keep schema validation, renderer output, handoff contracts, and external-action gates unchanged.
- Never interpolate the caller-supplied suspicious key into an error string.
- Preserve existing diagnostics for ordinary unsupported field names.
- Do not bump, install, or edit the cache until all focused and release gates pass.

---

### Task 1: Add RED coverage for the shared sanitizer and validators

**Files:**
- Modify: `plugins/professional-growth-coach/tests/test_private_prose_safety.py`
- Modify: `tests/test_private_recruiter_reply_triage.py`
- Modify: `tests/test_recruiter_practice_session.py`

- [ ] **Step 1: Write tests for suspicious field names**

Cover `person@example.invalid`, `/Users/synthetic/private-case.json`, and
`token_sk_live_SYNTHETIC` in the closed top-level mapping of each validator.
Assert rejection, the `<redacted-field>` marker, and absence of the supplied
sentinel. Add a control assertion that `unsupported_claim` remains literal in
the practice diagnostic. Add direct helper cases for ordinary `extra` and one
each of email/path/token-shaped names.

- [ ] **Step 2: Run the focused tests and verify RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_private_recruiter_reply_triage \
  tests.test_recruiter_practice_session \
  plugins.professional-growth-coach.tests.test_private_prose_safety -q
```

Expected: new suspicious-key assertions fail because current stderr contains
the supplied values; ordinary existing assertions remain green.

### Task 2: Implement and verify the sanitizer

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/private_prose_safety.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_private_recruiter_reply_triage.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_recruiter_practice_session.py`

- [ ] **Step 1: Implement `safe_diagnostic_field_name`**

Use a compiled case-insensitive signal pattern for email/phone punctuation,
URLs/local paths, and sensitive terms. Return `<redacted-field>` on a match;
otherwise return the original short string.

- [ ] **Step 2: Route only unsupported-field messages through the helper**

Wrap each `', '.join(unsupported)` expression with the helper per field. Do
not change missing-field, unknown-reference, prose, schema, or renderer paths.

- [ ] **Step 3: Run focused GREEN checks**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_private_recruiter_reply_triage \
  tests.test_recruiter_practice_session \
  plugins.professional-growth-coach.tests.test_private_prose_safety -q
```

Expected: all tests pass and no sentinel appears in rejected diagnostics.

- [ ] **Step 4: Run plugin/privacy checks and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/professional-growth-coach/tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
git diff --check
git add plugins/professional-growth-coach/scripts/private_prose_safety.py plugins/professional-growth-coach/scripts/validate_private_recruiter_reply_triage.py plugins/professional-growth-coach/scripts/validate_recruiter_practice_session.py plugins/professional-growth-coach/tests/test_private_prose_safety.py tests/test_private_recruiter_reply_triage.py tests/test_recruiter_practice_session.py
git commit -m "fix: redact sensitive triage diagnostics"
```

### Task 3: Publish and smoke the exact installed release

- [ ] Run static and official release validation before the cachebuster.
- [ ] Invoke `update_plugin_cachebuster.py` exactly once, commit manifest and provenance, then run `codex plugin add professional-growth-coach@professional-growth-coach-local --json`.
- [ ] Compare source/cache trees and normalized hash; run the five installed render smokes plus one triage/practice suspicious-key no-echo smoke.
- [ ] Refresh installed attestation, rebind provenance to the immediate parent when required, and rerun static, release, privacy, status, and diff gates.
