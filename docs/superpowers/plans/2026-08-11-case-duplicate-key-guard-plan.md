# Case Duplicate-Key Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject duplicate JSON object keys in the isolated case validator before validation or privacy content can be overwritten.

**Architecture:** Keep parsing inside `validate_case.py`, add a recursive `object_pairs_hook` that raises a private bounded error, and map that error to the existing CLI `rc=2` parse-failure boundary. Add only focused CLI regressions in `tests/test_validate_case.py`.

**Tech Stack:** Python 3 standard library `json`, `unittest`, existing shell/static/release gates.

## Global Constraints

- Do not echo duplicate keys, URLs, credentials, or candidate content in diagnostics.
- Preserve valid unique-key behavior and existing error messages.
- Do not change schemas, renderers, marketplace metadata, or unrelated loaders.
- Consume the plugin cachebuster exactly once after all pre-cachebuster gates pass.

---

### Task 1: Duplicate-key parser regression

**Files:**
- Modify: `tests/test_validate_case.py`
- Test: `plugins/job-search-coach/scripts/validate_case.py`

**Interfaces:**
- Consumes: `run_validator_contents()` and `valid_case()` from the existing test module.
- Produces: two failing CLI tests covering top-level and nested duplicate keys.

- [ ] **Step 1: Write the failing tests**

Add tests that build raw JSON with duplicate `claims` and nested `candidate_id`
keys, then assert `returncode == 2`, the generic duplicate-key diagnostic, and
absence of the sensitive URL/key text from stderr.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_validate_case -q
```

Expected: the new cases fail because last-write-wins parsing currently accepts
the duplicate document.

- [ ] **Step 3: Implement the minimal parser guard**

Add a private exception and hook:

```python
class _DuplicateJsonKeyError(ValueError):
    pass

def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError("duplicate JSON key")
        result[key] = value
    return result
```

Pass `object_pairs_hook=_unique_json_object` to the existing `json.loads` call
and catch `_DuplicateJsonKeyError` before the generic parse errors, emitting
`invalid case file: duplicate JSON key` and returning `2`.

- [ ] **Step 4: Run focused and adjacent tests GREEN**

Run the focused case suite, plugin-local discovery, and root case/privacy tests;
all must pass with no traceback or sensitive-input echo.

- [ ] **Step 5: Review and commit the functional change**

Run `git diff --check`, inspect the diff for scope, then commit:

```bash
git add plugins/job-search-coach/scripts/validate_case.py tests/test_validate_case.py
git commit -m "fix: reject duplicate case JSON keys"
```

### Task 2: Publish and install

**Files:**
- Modify: `plugins/job-search-coach/.codex-plugin/plugin.json`
- Modify: the 14 allowlisted final-eval provenance sidecars only

- [ ] **Step 1:** Bind provenance to the functional commit and plugin tree.
- [ ] **Step 2:** Run static, plugin, root, structure/privacy, privacy CLI,
  release, and diff gates before cache invalidation.
- [ ] **Step 3:** Consume the cachebuster exactly once and repeat every gate.
- [ ] **Step 4:** Commit manifest + provenance as the publication commit.
- [ ] **Step 5:** Install with `codex plugin add job-search-coach@job-search-coach-local --json`.
- [ ] **Step 6:** Verify installed/enabled state, exact source/cache `diff -qr`,
  installed release validation, and clean worktree.
