# Case Provenance ID Type Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject non-string optional record provenance IDs before downstream case processing.

**Architecture:** Extend the existing `_validate_records` field loop in `validate_case.py` with a closed, record-specific ID type check. Add focused CLI mutations in `tests/test_validate_case.py`; keep schemas and fixture shape unchanged.

**Tech Stack:** Python 3 standard library, `unittest`, existing privacy/static/release gates.

## Global Constraints

- IDs remain optional; only supplied values are checked.
- Valid IDs are non-empty strings; no format coercion or uniqueness rule is added.
- Error messages are deterministic, path-specific, and do not echo input values.
- Consume the plugin cachebuster exactly once after pre-cachebuster gates pass.

---

### Task 1: Add provenance ID type regressions

**Files:**
- Modify: `tests/test_validate_case.py`
- Test: `plugins/job-search-coach/scripts/validate_case.py`

- [ ] **Step 1: Write failing tests** for each record ID field using `{}`, `[]`, `7`, and `true`; assert `rc=2`, the path-specific message, and no value echo.
- [ ] **Step 2: Run `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_validate_case -q` and confirm RED because the CLI currently accepts the values.
- [ ] **Step 3: Implement a minimal `_validate_records` check:**

```python
for id_field in record_fields & {"source_id", "claim_id", "intervention_id", "outcome_id"}:
    if id_field in record and (
        not isinstance(record[id_field], str) or not record[id_field].strip()
    ):
        errors.append(f"{field}[{index}].{id_field} must be a non-empty string")
```

- [ ] **Step 4: Run focused case/privacy tests GREEN and inspect diagnostics for no input echo.**
- [ ] **Step 5: Run `git diff --check`, review scope, and commit `fix: validate case provenance id types`.**

### Task 2: Publish and install

- [ ] Bind the 14 allowlisted provenance sidecars to the functional commit/tree.
- [ ] Run all pre-cachebuster gates.
- [ ] Consume the cachebuster exactly once, repeat all gates, and commit manifest + provenance.
- [ ] Install via the local marketplace and verify installed/enabled state, exact source/cache diff, release validation, and clean worktree.
