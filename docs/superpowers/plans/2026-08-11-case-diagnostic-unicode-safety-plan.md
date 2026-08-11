# Case Diagnostic Unicode Safety Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make case-validator diagnostics safe for isolated surrogates and Unicode line separators without changing validation semantics.

**Architecture:** Keep the existing `_safe_path_key` boundary and extend its small `_escape_diagnostic_controls` helper. The validator still returns its complete error list to internal callers; only diagnostic path rendering changes before the CLI byte-budget formatter.

**Tech Stack:** Python 3.11+, `unicodedata`, `unittest`, existing offline plugin validators.

## Global Constraints

- Escape only Unicode categories `Cc`, `Cs`, `Zl`, and `Zp` as `\\uXXXX`.
- Preserve ordinary Unicode, accents, combining marks, sensitivity classification, schemas, renderers, and API list output semantics.
- Keep diagnostics bounded by the existing 16,384-byte CLI formatter.
- Do not change the cache or installed plugin until all tests and release gates pass.

---

### Task 1: Add regression coverage

**Files:**
- Modify: `tests/test_validate_case.py`
- Read: `plugins/professional-growth-coach/scripts/validate_case.py`

**Interfaces:**
- Consumes the existing `valid_case()` and `run_validator()` helpers.
- Produces failing CLI tests for `Cs`, `Zl`, and `Zp` diagnostic keys.

- [ ] **Step 1: Write the failing tests**

Add one test that places `\ud800` in an unsupported key and asserts `returncode == 2`, no traceback, and the escaped code unit. Add a table-driven test for `\u2028` and `\u2029` that asserts the escaped output contains no literal separator and `len(result.stderr.splitlines()) == 1`.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_validate_case.ValidateCaseTests.test_cli_escapes_unicode_diagnostic_controls -v
```

Expected: the surrogate case fails with a `UnicodeEncodeError`/nonzero traceback, and the separator cases contain literal separators.

### Task 2: Implement the minimal Unicode escape extension

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_case.py:_escape_diagnostic_controls`
- Test: `tests/test_validate_case.py`

**Interfaces:**
- Consumes a string path segment.
- Produces the same string except characters whose `unicodedata.category` is in `{'Cc', 'Cs', 'Zl', 'Zp'}` become lowercase four-digit `\\uXXXX` escapes.

- [ ] **Step 1: Implement the category set**

Replace the single-category comparison with membership in the four-category set. Keep the original key passed to `_has_sensitive_key_segment()` and `_is_credential_shaped_value()`; only the final diagnostic string uses the escaped value.

- [ ] **Step 2: Run the focused tests and verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_validate_case -q
```

Expected: all case tests pass, including the new surrogate and separator regressions, with no stderr traceback.

- [ ] **Step 3: Run the related plugin/privacy checks**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/professional-growth-coach/tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
git diff --check
```

Expected: 146 plugin tests, privacy exit 0, and a clean diff check.

- [ ] **Step 4: Commit the functional increment**

```bash
git add plugins/professional-growth-coach/scripts/validate_case.py tests/test_validate_case.py
git commit -m "fix: harden case diagnostics for Unicode controls"
```

### Task 3: Release and installed verification

**Files:**
- Modify mechanically: `plugins/professional-growth-coach/.codex-plugin/plugin.json`, provenance sidecars, and `tests/evals/final/installed-smoke-test.md`

**Interfaces:**
- Consumes the functional commit from Task 2.
- Produces one cache-busted canonical plugin release with exact source/cache parity.

- [ ] **Step 1: Run static and official release gates before the cachebuster**
- [ ] **Step 2: Invoke `update_plugin_cachebuster.py` exactly once and commit the manifest with provenance bound to the functional parent**
- [ ] **Step 3: Run `codex plugin add professional-growth-coach@professional-growth-coach-local --json`**
- [ ] **Step 4: Compare source/cache files and normalized hash, then run the five installed smoke fixtures**
- [ ] **Step 5: Refresh the attestation, rebind sidecars to the immediate parent when required, and rerun static/release/status gates**
