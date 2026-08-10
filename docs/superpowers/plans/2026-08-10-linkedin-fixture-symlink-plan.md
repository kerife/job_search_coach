# LinkedIn fixture symlink boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fail closed when LinkedIn fixture loaders or the static inventory encounter symlinked report/bundle files.

**Architecture:** Reuse the loader's existing bounded `ValueError` boundary for bundle inputs. Add a pre-read symlink check in `validate_linkedin_report_fixture_directory()` for every expected report and bundle, leaving regular-file validation and artifact inventory rules unchanged.

**Tech Stack:** Python 3.11 standard library, `pathlib`, offline validator/static checker, `unittest`.

## Global Constraints

- Never resolve or read a symlink target during validation.
- Do not echo target paths, fixture contents, or private values.
- Preserve regular-file behavior, duplicate-key rejection, report-pair checks, and static inventory ordering.
- Follow RED → GREEN → focused regression → `git diff --check`.

---

### Task 1: Reject symlinked LinkedIn fixtures

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_linkedin_client_report.py:803-817,3540-3560`
- Modify: `plugins/job-search-coach/tests/run_static_checks.py:1318-1345`
- Test: `tests/test_linkedin_report_fixtures.py:88-155`
- Test: `tests/test_full_plugin.py:500-550`

**Interfaces:**
- `load_bundle(path: Path) -> dict[str, object]` raises `ValueError("fixture bundle input must not be a symlink")` before reading a symlink.
- `_cli()` rejects symlink report or bundle arguments with a bounded nonzero result and no target echo.
- `validate_linkedin_report_fixture_directory(root: Path)` returns a stable error containing `symlink` for a symlinked expected report or bundle and never loads its target.

- [ ] **Step 1: Write failing tests**

  Create a regular temporary bundle target and a symlink path, then assert
  `load_bundle()` rejects the link while the regular target remains valid. Add
  a CLI mutation using a symlink report/bundle and assert nonzero/no accepted
  output. In the static checker test, copy the normal artifact inventory,
  replace one expected bundle and one expected report with symlinks to regular
  external files, and assert the returned errors mention the symlink path and
  `symlink`.

- [ ] **Step 2: Run RED**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_linkedin_report_fixtures.LinkedInReportFixtureTests.test_load_bundle_rejects_symlink_input tests.test_full_plugin.FullPluginIntegrationTests.test_linkedin_report_fixture_directory_rejects_symlink_artifacts -v
  ```

  Expected before implementation: the loader follows the link and the static
  inventory returns no symlink error.

- [ ] **Step 3: Implement the minimal guards**

  Add `path.is_symlink()` before `read_text`/`json.loads` in `load_bundle`.
  In `_cli`, reject symlink report/bundle arguments before reading them. In the
  static checker, reject a symlink root and check `report_path.is_symlink()` and
  `bundle_path.is_symlink()` before `is_file()`; append bounded diagnostics and
  skip that pair's reads when either is linked.

- [ ] **Step 4: Run GREEN and regressions**

  Run the two focused tests, all LinkedIn fixture tests, the static-checker
  integration tests, and `git diff --check`. Confirm canonical regular fixtures
  still pass.

- [ ] **Step 5: Commit**

  ```bash
  git add plugins/job-search-coach/scripts/validate_linkedin_client_report.py plugins/job-search-coach/tests/run_static_checks.py tests/test_linkedin_report_fixtures.py tests/test_full_plugin.py
  git commit -m "fix: reject LinkedIn fixture symlinks"
  ```
