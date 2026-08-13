# LinkedIn diagnostic path redaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent caller-controlled JSON mapping keys from leaking private paths or control characters through LinkedIn validator diagnostics.

**Architecture:** Keep the recursive privacy scanner and its canonical source URL handling unchanged. Sanitize only mapping-key segments through `_safe_diagnostic_field_name()` before composing `child_path`; extend that helper for Unix absolute roots, drive-letter paths, and UNC paths. List indexes and ordinary keys remain structurally readable.

**Tech Stack:** Python 3, `unittest`, standard-library JSON/CLI helpers.

## Global Constraints

- Preserve existing `source_catalog[N].url` canonical-source behavior.
- Preserve ordinary diagnostic paths such as `priorities[0].done_when`.
- Do not echo caller-controlled absolute paths, credentials, or control characters.
- Redact `/opt`, `/Applications`, drive-letter, and UNC path keys while preserving relative backslash keys.
- Keep the validator dependency-free and bounded by existing input limits.

---

### Task 1: Regression contract

**Files:**
- Modify: `tests/test_linkedin_report_fixtures.py`
- Test: `tests/test_linkedin_report_fixtures.py::LinkedInReportFixtureTests.test_privacy_diagnostics_redact_untrusted_mapping_key_paths_api_and_cli`

- [x] **Step 1: Write the failing test**

Use a valid fixture with a top-level key `/Users/PRIVATE_SENTINEL/profile.json`
and value `https://evil.example`; call both `validate_fixture_bundle()` and
`_cli()` and assert the sentinel is absent while `<redacted-field>` remains.

- [x] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_linkedin_report_fixtures.LinkedInReportFixtureTests.test_privacy_diagnostics_redact_untrusted_mapping_key_paths_api_and_cli -q
```

Expected: FAIL because `_scan_privacy()` reports the raw mapping key.

### Task 2: Minimal sanitizer integration

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_linkedin_client_report.py:_scan_privacy`

- [x] **Step 1: Sanitize mapping keys before path composition**

Replace raw `str(key)` path composition with:

```python
safe_key = _safe_diagnostic_field_name(key)
child_path = f"{path}.{safe_key}" if path else safe_key
```

Keep the existing list branch and canonical URL matching unchanged.

- [x] **Step 2: Run focused GREEN tests**

Run the regression test above and then:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_linkedin_report_fixtures tests.test_linkedin_client_report -q
```

Expected: 238 tests pass with no raw sentinel in API or CLI output.

### Task 3: Release verification

**Files:**
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json`
- Modify: `tests/evals/final/cycle-1/*.json`, `cycle-2/*.json`, both index files,
  and `installed-smoke-test.md`

- [ ] **Step 1: Run full plugin/static/privacy gates**
- [ ] **Step 2: Bump the plugin version and install it in Codex**
- [ ] **Step 3: Rebind provenance to the functional parent and cache hash**
- [ ] **Step 4: Verify source/cache parity and installed smoke**
- [ ] **Step 5: Commit and push the release**
