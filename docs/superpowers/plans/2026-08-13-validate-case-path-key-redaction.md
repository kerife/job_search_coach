# Validate-case path-key redaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline execution in this session).

**Goal:** Prevent unsupported absolute/UNC case keys from leaking into API and CLI diagnostics while preserving useful relative-key errors.

**Architecture:** Reuse `_safe_path_key` and its existing `_LOCAL_PATH_VALUE` classifier. Add one parameterized regression covering direct validation and the CLI, then extend only the classifier; no schema or case-model changes.

**Tech Stack:** Python 3, `unittest`, existing case validator and release scripts.

## Global Constraints

- Preserve ordinary relative keys and existing diagnostic control escaping.
- Keep the existing `<redacted-key>` diagnostic marker.
- Do not change valid-case output or input limits.
- Observe RED→GREEN before committing production code.

### Task 1: Add the failing privacy-boundary regression

**Files:**
- Modify: `tests/test_validate_case.py` near existing unsupported-field privacy tests
- Read: `plugins/professional-growth-coach/scripts/validate_case.py`

**Interfaces:**
- Consumes: `run_validator`, `load_validator_module`, and `valid_case` helpers already present in the test module.
- Produces: a test proving both direct diagnostics and CLI stderr redact absolute/UNC path keys while preserving ordinary keys.

- [ ] **Step 1: Write the failing test**

Add one test that iterates these keys: `/opt/private/profile.json`, `/Applications/private.app`, `\\\\server\\share\\profile.json`, and `relative\\profile.json`. For each key, assert direct validation contains `<redacted-key>` for the first three and the literal relative key for the last; run the CLI and assert the same sentinel does not occur in stderr for the first three.

- [ ] **Step 2: Run the focused test to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_validate_case.ValidateCaseTests.test_redacts_absolute_and_unc_path_keys -q
```

Expected: FAIL because the three absolute/UNC keys are currently echoed.

### Task 2: Implement the minimum classifier extension

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_case.py:_LOCAL_PATH_VALUE`

**Interfaces:**
- Consumes: the existing `_safe_path_key` call sites.
- Produces: the same `<redacted-key>` marker for additional absolute roots and UNC paths.

- [ ] **Step 1: Extend the classifier**

Add `/opt/`, `/Applications/`, `/var/`, `/Volumes/`, `/root/`, `/srv/`, `/usr/`, and UNC `\\\\`/`//` prefixes to `_LOCAL_PATH_VALUE`; keep drive, `/Users`, `/home`, `/private`, `/tmp`, and relative-path behavior unchanged.

- [ ] **Step 2: Run the focused test to verify GREEN**

Run the RED command again and expect PASS.

- [ ] **Step 3: Run regression suites**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_validate_case -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/professional-growth-coach/tests -p 'test*.py' -q
```

Expected: all tests pass with no traceback.

### Task 3: Publish and verify the increment

**Files:**
- Modify: plugin manifest/version and release provenance artifacts through the repository's existing release workflow.

- [ ] **Step 1: Run static, privacy, and release validation**
- [ ] **Step 2: Bump the plugin version and install it from the local marketplace**
- [ ] **Step 3: Rebind provenance and installed smoke metadata to the release parent/tree**
- [ ] **Step 4: Re-run source/cache parity, plugin suite, focused tests, and `git status`**
- [ ] **Step 5: Commit and push the verified release**

