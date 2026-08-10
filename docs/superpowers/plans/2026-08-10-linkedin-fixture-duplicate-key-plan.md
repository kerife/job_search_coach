# LinkedIn fixture duplicate-key boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject duplicate JSON keys at the LinkedIn fixture loader and CLI boundary before privacy/schema validation can be bypassed.

**Architecture:** Reuse one ordered-pairs hook in `validate_linkedin_client_report.py`. `load_bundle()` raises a bounded `ValueError`; `_cli()` parses with the same hook and converts the failure into its existing generic validation diagnostic. No schema or renderer changes are needed.

**Tech Stack:** Python 3.11 standard library, `json`, `unittest`, existing plugin CLI.

## Global Constraints

- Do not echo fixture values, email-like content, absolute paths, or raw JSON in diagnostics.
- Preserve valid fixture behavior and existing report-pair validation.
- Keep the change limited to the loader/CLI and focused tests.
- Follow RED → GREEN → focused regression → `git diff --check`.

---

### Task 1: Duplicate-key loader and CLI guard

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_linkedin_client_report.py:803-808, 3530-3555`
- Test: `tests/test_linkedin_report_fixtures.py:88-100, 260-330`

**Interfaces:**
- `load_bundle(path: Path) -> dict[str, object]` continues to return a mapping for valid JSON and raises `ValueError("fixture contains duplicate JSON key")` for repeated keys at any object depth.
- `_cli()` continues to return its existing nonzero malformed-input result and emits only the bounded generic validation error.

- [ ] **Step 1: Write the failing tests**

  Add one test that writes a temporary JSON object with duplicate `fixture_id`
  values, where the first value is email-like, and assert `load_bundle()` raises
  `ValueError` without the email in the exception text. Add a nested duplicate
  object test. Add a CLI test that pairs a valid report with the duplicate
  bundle and asserts a nonzero return code, no accepted-bundle output, and no
  duplicated value in stderr.

- [ ] **Step 2: Run the focused tests and verify RED**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_linkedin_report_fixtures -q
  ```

  Expected before implementation: the new loader test receives the last
  duplicate value instead of raising, and the CLI test accepts the bundle.

- [ ] **Step 3: Implement the minimal hook**

  Add:

  ```python
  def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
      result: dict[str, object] = {}
      for key, value in pairs:
          if key in result:
              raise ValueError("fixture contains duplicate JSON key")
          result[key] = value
      return result
  ```

  Pass `object_pairs_hook=_unique_object` to both `json.loads` calls used by
  `load_bundle()` and `_cli()`. Catch the new `ValueError` in `_cli()` through
  its existing malformed-bundle error path without interpolating the message.

- [ ] **Step 4: Run focused GREEN checks**

  Run the same fixture test module and the direct CLI mutation test. Expect all
  tests to pass, including the existing valid fixture and privacy mutations.

- [ ] **Step 5: Run broader regression checks**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_linkedin_report_fixtures tests.test_full_plugin -q
  git diff --check
  ```

- [ ] **Step 6: Commit the implementation**

  ```bash
  git add plugins/job-search-coach/scripts/validate_linkedin_client_report.py tests/test_linkedin_report_fixtures.py
  git commit -m "fix: reject duplicate LinkedIn fixture keys"
  ```
