# Recruiter Practice v2 Content Locale Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add a backward-compatible `recruiter-practice-session-v2` contract that separates fixed UI language from dynamic content language.

**Architecture:** Keep v1 schema, validator behavior, fixtures, and markup unchanged. Add a closed v2 schema and make the existing validator dispatch common structural validation by version; the existing renderer derives UI/content locales from the validated version and annotates only dynamic prose nodes with `lang`.

**Tech Stack:** Python 3 standard library, dependency-free JSON Schema subset checker, static HTML templates, `unittest`.

## Global Constraints

- V1 remains accepted exactly as before and rejects v2-only fields.
- V2 accepts only `ui_locale` and `content_locale` values `en` or `es`; it does not accept top-level `locale`.
- Fixed labels use `ui_locale`; dynamic prose uses `content_locale`; no automatic language detection or translation.
- Preserve privacy guards, HTML escaping, offline/CSP behavior, ARIA IDs, and delivery invariants.

---

### Task 1: V2 contract and validator RED

**Files:**
- Create: `plugins/job-search-coach/schemas/recruiter-practice-session-v2.schema.json`
- Modify: `plugins/job-search-coach/tests/test_private_schema_conformance.py`
- Modify: `tests/test_recruiter_practice_session.py`

**Interfaces:**
- V2 instance fields: `schema_version`, `session_kind`, `ui_locale`, `content_locale`, and the same closed body as v1.
- Existing `validate_session(value)` remains the public validator entry point.

- [ ] **Step 1: Write failing tests**

  Build a copy of `tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json`, replace `schema_version` with `recruiter-practice-session-v2`, remove `locale`, and add `ui_locale="en"`, `content_locale="es"`. Assert schema and custom validation succeed; assert v1 with `content_locale` or v2 missing either locale fails.

- [ ] **Step 2: Run the tests and verify RED**

  Run:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/job-search-coach/scripts python3 -B -m unittest plugins/job-search-coach/tests/test_private_schema_conformance.py tests.test_recruiter_practice_session -q`

  Expected: the new v2 cases fail because the v1 schema/validator rejects the version and locale fields.

- [ ] **Step 3: Add the closed v2 schema**

  Copy the v1 schema and change only `$id`, `title`, the root `schema_version` const, root required `locale` to required `ui_locale` and `content_locale`, and the root locale property to those two enum properties. Keep `additionalProperties: false` and all body/privacy/delivery definitions identical.

- [ ] **Step 4: Run schema-only checks**

  Run:
  `python3 -m json.tool plugins/job-search-coach/schemas/recruiter-practice-session-v2.schema.json`

  Expected: exit 0; v1 tests still pass while v2 custom tests remain RED until validator dispatch is implemented.

- [ ] **Step 5: Commit**

  `git add plugins/job-search-coach/schemas/recruiter-practice-session-v2.schema.json plugins/job-search-coach/tests/test_private_schema_conformance.py tests/test_recruiter_practice_session.py && git commit -m "test: define recruiter practice v2 locale contract"`

### Task 2: Version dispatch and renderer language RED/GREEN

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_recruiter_practice_session.py`
- Modify: `plugins/job-search-coach/scripts/render_recruiter_practice_session.py`
- Modify: `plugins/job-search-coach/tests/test_render_recruiter_practice_session.py`

**Interfaces:**
- Validator accepts `recruiter-practice-session-v1` and `recruiter-practice-session-v2`; invalid versions remain rejected.
- Renderer helper `_ui_locale(session)` returns v1 `locale` or v2 `ui_locale`; `_content_locale(session)` returns v1 locale or v2 content locale.

- [ ] **Step 1: Write the failing renderer test**

  Add a v2 copy of the Spanish fixture with `ui_locale="en"` and `content_locale="es"`; assert rendered HTML has `<html lang="en">`, English fixed heading/copy, and `lang="es"` on the context, requirement, question, fact, rubric, and feedback prose nodes.

- [ ] **Step 2: Run the focused test and verify RED**

  Run:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/job-search-coach/scripts python3 -B -m unittest plugins/job-search-coach/tests/test_render_recruiter_practice_session.py -q`

  Expected: the v2 instance is rejected or lacks the required language attributes.

- [ ] **Step 3: Implement minimal version dispatch**

  Select the version before closed-field validation. For v1, retain the current top-level field set and locale checks. For v2, require `ui_locale` and `content_locale`, reject `locale`, and reuse all current body validation. Keep all existing error messages bounded and avoid echoing prose.

- [ ] **Step 4: Implement localized dynamic markup**

  Derive UI/content locale once after validation. Use UI locale for labels and template `{{LANG}}`. Add escaped `lang="content_locale"` to dynamic prose elements only; split mixed evidence/boundary nodes into fixed label plus dynamic span. Preserve v1 output by emitting no new `lang` attributes for v1.

- [ ] **Step 5: Run focused GREEN checks**

  Run the renderer test, schema conformance, and root practice contract tests. Expected: v1 and v2 cases pass, malformed locale/version cases fail closed, and no raw identifiers appear.

- [ ] **Step 6: Commit**

  `git add plugins/job-search-coach/scripts/validate_recruiter_practice_session.py plugins/job-search-coach/scripts/render_recruiter_practice_session.py plugins/job-search-coach/tests/test_render_recruiter_practice_session.py && git commit -m "feat: support practice v2 content locale"`

### Task 3: Full verification and release

**Files:**
- Modify only at release: `plugins/job-search-coach/.codex-plugin/plugin.json`
- Modify only at release: the 12 allowlisted `tests/evals/final/cycle-{1,2}/*.json` provenance fields.

- [ ] **Step 1: Run all pre-cachebuster gates**

  Run static checks, plugin discovery, root discovery, privacy tests/CLI, schema and renderer suites, release validation, and `git diff --check` with `PYTHONPATH=plugins/job-search-coach/scripts`.

- [ ] **Step 2: Refresh provenance**

  Update only `source_commit` and `source_tree` in the 12 deterministic final fixtures to the functional HEAD and `HEAD:plugins/job-search-coach` tree.

- [ ] **Step 3: Consume the official cachebuster once**

  `python3 -B /Users/kevinriosferrer/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py plugins/job-search-coach`

- [ ] **Step 4: Run post-cachebuster gates and publish**

  Repeat all gates, stage exactly the manifest plus 12 provenance files, and commit `chore: publish recruiter practice v2 content locale`.

- [ ] **Step 5: Install and verify**

  Run `codex plugin add job-search-coach@job-search-coach-local --json`, compare the exact cache with `diff -qr`, run the installed release validator, verify installed/enabled/source identity, and confirm a clean worktree.
