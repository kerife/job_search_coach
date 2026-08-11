# Professional Growth Coach Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the complete Codex plugin identity and active skill surface to Professional Growth Coach while preserving data contracts and making employment continuity explicit.

**Architecture:** Perform a filesystem-level Git rename for the plugin and
selected skill directories, then update the marketplace, manifests, imports,
tests, references, and static inventories as one coherent breaking migration.
Keep renderers/schemas behaviorally unchanged except for neutral stop copy and
the required Python 3.11 syntax repair. Publish as a new marketplace package
after all gates and a single cachebuster invocation.

**Tech Stack:** Python 3.11.15 locked release environment, Python standard
library/unittest, Markdown skills, JSON schemas, static HTML/CSS, Codex local
marketplace, authenticated Superdesign CLI.

## Global Constraints

- Canonical plugin ID: `professional-growth-coach`.
- Canonical marketplace ID: `professional-growth-coach-local`.
- Display name: `Professional Growth Coach`.
- Preserve schema versions and validated data shapes unless a focused test proves otherwise.
- Preserve offline CSP, privacy, no-external-action, print, responsive, forced-colors, reduced-motion, and ARIA contracts.
- Preserve current-employment continuity by default; never turn a path decision into a separation instruction.
- No symlinks, duplicate package copies, remote assets, telemetry, employer monitoring, or HR export.
- Consume the official cachebuster exactly once, only after all pre-cachebuster gates pass.

---

### Task 1: Freeze the migration inventory and write RED contract tests

**Files:**
- Modify: `tests/test_plugin_structure.py`
- Modify: `tests/test_full_plugin.py`
- Modify: `tests/test_skill_contracts.py`
- Modify: `tests/test_validate_case.py` only if the Python 3.11 compatibility regression needs a focused test.
- Create: `tests/test_professional_growth_contract.py`

**Interfaces:**
- Consumes: current manifest, marketplace JSON, `EXPECTED_SKILLS`, active skill paths, and current release validator.
- Produces: failing tests that define the new IDs, no-stale-reference allowlist, workplace-neutral copy, and Python 3.11 importability.

- [ ] **Step 1: Add manifest and marketplace RED assertions**

Assert the manifest name/display name, marketplace name, plugin source path,
and new canonical skill inventory. Assert that old IDs do not appear in active
source paths or marketplace metadata.

- [ ] **Step 2: Add continuity-boundary RED assertions**

Read the active root skill, career-options skill, path-scoring reference,
routing reference, README, and triage stop copy. Assert exact stable markers:

```text
preserve_current_employment_by_default
no_resignation_recommendation=true
staying_and_growing_is_valid
```

Assert both English and Spanish stop messages name the recruiter process and
return candidate agency.

- [ ] **Step 3: Add Python 3.11 RED import regression**

Run the locked interpreter against the LinkedIn validator import path and
assert it does not raise `SyntaxError`.

- [ ] **Step 4: Run RED tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_professional_growth_contract -q
```

Expected: failures identify the old identity, missing continuity markers, and
the uncorrected Python 3.11 syntax.

### Task 2: Rename the plugin package, marketplace, and skill surface

**Files:**
- Rename: `plugins/job-search-coach/` → `plugins/professional-growth-coach/`
- Modify: `.agents/plugins/marketplace.json`
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json`
- Rename skill directories according to the mapping in the spec.
- Modify: all active tests and scripts that resolve the old package/skill paths.

**Interfaces:**
- Consumes: Task 1 RED inventory.
- Produces: one coherent package tree with no broken relative links/imports.

- [ ] **Step 1: Use `git mv` for the package and five skill directories**

Do not copy the tree and do not create symlink aliases. Keep the two unchanged
capability skill directories in the renamed package.

- [ ] **Step 2: Update manifest and marketplace IDs**

Set `name`, display metadata, skills path, marketplace name, plugin name, and
source path to the canonical Professional Growth Coach values. Keep
capabilities `Interactive`, `Read`, and `Write` unchanged.

- [ ] **Step 3: Update active references and test fixtures**

Replace old paths/IDs in active Python tests, static checks, eval indexes,
skill cross-links, README, and agent metadata. Keep historical SDD documents
unchanged or mark them as historical in the allowlist rather than performing a
blind repository-wide replacement.

- [ ] **Step 4: Run structural RED/GREEN tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_plugin_structure tests.test_full_plugin \
  tests.test_professional_growth_contract -q
```

Expected: all path, inventory, link, and manifest checks pass with the new IDs.

### Task 3: Apply workplace-neutral product framing

**Files:**
- Modify: `plugins/professional-growth-coach/README.md`
- Modify: `plugins/professional-growth-coach/skills/professional-growth-coach/SKILL.md`
- Modify: `plugins/professional-growth-coach/skills/explore-career-options/SKILL.md`
- Modify: `plugins/professional-growth-coach/skills/explore-career-options/references/path-scoring.md`
- Modify: `plugins/professional-growth-coach/skills/professional-growth-coach/references/routing.md`
- Modify: `plugins/professional-growth-coach/scripts/render_private_recruiter_reply_triage.py`
- Modify: `tests/test_render_private_recruiter_reply_triage.py`
- Modify: `.superdesign/init/theme.md`, `.superdesign/design-system.md` product-context lines only.

**Interfaces:**
- Consumes: Task 1 continuity tests and existing evidence/action-boundary contracts.
- Produces: bilingual/neutral product language with unchanged schemas and
  output shapes.

- [ ] **Step 1: Add the employment-continuity boundary**

State that the current job is preserved by default, route external market
research as an optional evidence exercise, and make `stay_and_improve_current_role`
and `do_nothing_now` valid outcomes.

- [ ] **Step 2: Add the explicit separation-analysis boundary**

If a user explicitly asks whether to leave, require a neutral matrix covering
runway, benefits, notice, eligibility, safety, and HR/legal questions. Never
produce an unqualified “leave” recommendation.

- [ ] **Step 3: Localize stop-state scope and agency**

Change only the stop triage copy to refer to the recruiter process, not the
person's employment or entire job search; add the no-resignation disclaimer in
English and Spanish.

- [ ] **Step 4: Update starter prompts and visible descriptions**

Use “professional growth”, “market literacy”, “role options”, and “development
plan”. Remove default prompts that imply searching for a new job is the goal;
keep external job-search actions explicitly draft-only and authorized.

- [ ] **Step 5: Run copy/renderer tests**

```bash
PYTHONPATH=plugins/professional-growth-coach/scripts \
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_professional_growth_contract \
  tests.test_render_private_recruiter_reply_triage \
  tests.test_skill_contracts -q
```

### Task 4: Repair Python 3.11 compatibility before release

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_linkedin_client_report.py`
- Modify: focused validator tests if needed.

**Interfaces:**
- Consumes: current nested f-string at the LinkedIn report validator's term
  pattern construction.
- Produces: identical runtime regex semantics without a backslash expression
  inside an f-string.

- [ ] **Step 1: Add/confirm a locked-interpreter import regression**
- [ ] **Step 2: Calculate `term_pattern` before the f-string**
- [ ] **Step 3: Run the locked validator and focused report suite**

```bash
PYTHON=/Users/kevinriosferrer/projects/job_search_coach/.release-validation-venv/bin/python
$PYTHON -B -m unittest tests.test_linkedin_report_fixtures tests.test_linkedin_client_report -q
```

Expected: no SyntaxError, deterministic privacy diagnostics, and no output
content changes beyond the intended compatibility repair.

### Task 5: Full verification, Superdesign review, and release

**Files:**
- Modify mechanically only: new manifest version and allowlisted provenance
  sidecars for the renamed package.
- Do not modify `.superdesign` assets beyond the approved context copy.

- [ ] **Step 1: Run all pre-cachebuster gates**

Run static/schema/handoff checks, plugin discovery, root discovery under locked
Python, structure/privacy, repository privacy, official release validation, and
`git diff --check`.

- [ ] **Step 2: Run Superdesign preflight and review the existing canvas**

Use `npx --yes @superdesign/cli@latest`, read all init/design-system files,
confirm no visual regression, and record the canvas/draft review. Do not create
new UI assets unless a concrete visual defect is found.

- [ ] **Step 3: Refresh provenance and consume the cachebuster exactly once**

Bind all deterministic fixtures to the functional HEAD/tree, invoke the official
cachebuster once for the new package identity, then rerun every gate.

- [ ] **Step 4: Commit the migration as a release**

Stage only renamed active files, tests, docs/spec/plan, manifest, marketplace,
and allowlisted provenance. Create one migration commit and record its SHA.

- [ ] **Step 5: Install and verify the new marketplace package**

```bash
codex plugin add professional-growth-coach@professional-growth-coach-local --json
```

Verify installed/enabled state, exact source/cache identity with `diff -qr`,
installed skill validation, fresh-chat discoverability, and a clean worktree.

- [ ] **Step 6: Publish the migration note**

Document that `job-search-coach` is the previous package identity and
`professional-growth-coach` is the new canonical package; do not silently
rewrite an existing user's loaded plugin.

## Rollback

If any rename or release gate fails, stop before cachebuster/installation. The
previous `job-search-coach` release remains intact in Git and its installed
cache is not deleted. Revert only the uncommitted migration tree; never mutate
the old cache manually.
