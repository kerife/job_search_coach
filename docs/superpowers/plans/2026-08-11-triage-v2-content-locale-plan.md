# Private Recruiter Reply Triage v2 Content Locale Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add a backward-compatible triage v2 contract that separates UI and dynamic-content language.

**Architecture:** Copy the closed v1 schema into a v2 schema with two locale fields. Dispatch the existing validator by schema version and pass UI/content locale explicitly through the renderer; keep all v1 output and dossier/handoff contracts unchanged.

**Tech Stack:** Python standard library, dependency-free schema checker, static HTML, `unittest`.

## Global Constraints

- V1 remains closed and unchanged.
- V2 accepts only `ui_locale` and `content_locale` values `es|en` and rejects top-level `locale`.
- Fixed copy uses UI locale; dynamic prose is escaped and marked with content locale.
- No automatic language detection, translation, new network behavior, or privacy relaxation.

---

### Task 1: Schema/validator RED and contract GREEN

**Files:**
- Create: `plugins/job-search-coach/schemas/private-recruiter-reply-triage-v2.schema.json`
- Modify: `plugins/job-search-coach/scripts/validate_private_recruiter_reply_triage.py`
- Modify: `plugins/job-search-coach/tests/test_private_schema_conformance.py`
- Modify: `tests/test_private_recruiter_reply_triage.py`

- [ ] **Step 1: Add RED cases**

  Copy a valid `ready-es.json`, replace `schema_version` with v2, remove `locale`, add `ui_locale="en"` and `content_locale="es"`; assert custom/schema validation succeeds. Assert missing/invalid content locale fails and v1 with v2 fields fails.

- [ ] **Step 2: Run RED**

  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/job-search-coach/scripts python3 -B -m unittest plugins/job-search-coach/tests/test_private_schema_conformance.py tests.test_private_recruiter_reply_triage -q`

  Expected: v2 cases fail because only v1 is accepted.

- [ ] **Step 3: Add v2 schema**

  Copy v1 and change only `$id`, title, version const, root required `locale` to `ui_locale`/`content_locale`, and root locale property to those enums. Preserve all nested definitions and `additionalProperties: false`.

- [ ] **Step 4: Dispatch validator**

  Add v2 top-level field sets and branch locale checks by schema version; reuse the existing body validation and error privacy. Do not alter v1 paths.

- [ ] **Step 5: Run GREEN**

  Run the focused command again plus `python3 -m json.tool` on the new schema. Expected: v1/v2 valid cases pass and malformed cases fail.

- [ ] **Step 6: Commit**

  `git add plugins/job-search-coach/schemas/private-recruiter-reply-triage-v2.schema.json plugins/job-search-coach/scripts/validate_private_recruiter_reply_triage.py plugins/job-search-coach/tests/test_private_schema_conformance.py tests/test_private_recruiter_reply_triage.py && git commit -m "feat: add triage v2 content locale contract"`

### Task 2: Renderer language markup

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_private_recruiter_reply_triage.py`
- Modify: `tests/test_render_private_recruiter_reply_triage.py`

- [ ] **Step 1: Add failing mixed-locale renderer test**

  Render a v2 copy with English UI and Spanish prose. Assert HTML `lang="en"`, English fixed heading, and Spanish `lang` attributes on context, fact, question, blocked claim, and handoff preview prose.

- [ ] **Step 2: Run RED**

  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/job-search-coach/scripts python3 -B -m unittest tests.test_render_private_recruiter_reply_triage -q`

- [ ] **Step 3: Implement minimal locale helpers**

  Derive UI/content locale by version; keep v1 content attributes empty. Add escaped `lang` only to dynamic text nodes, splitting fixed labels from dynamic values where they share a paragraph. Keep receipt locale equal to UI locale and preserve ARIA/HTML escaping.

- [ ] **Step 4: Run GREEN and commit**

  Run v1/v2 renderer, schema, triage contract, privacy, and `git diff --check` tests; commit `feat: render triage v2 content locale`.

### Task 3: Release

**Files:**
- Modify only at release: plugin manifest and 12 allowlisted final fixture provenance fields.

- [ ] **Step 1:** Run static, plugin/root discovery, triage/schema/render, privacy, release, and diff gates.
- [ ] **Step 2:** Update only `source_commit`/`source_tree` to functional HEAD/tree.
- [ ] **Step 3:** Consume the official cachebuster exactly once.
- [ ] **Step 4:** Repeat gates, stage exactly manifest + provenance, commit `chore: publish triage v2 content locale`.
- [ ] **Step 5:** Install exact version, compare source/cache, run installed validator and v2 smoke, verify enabled identity and clean worktree.
