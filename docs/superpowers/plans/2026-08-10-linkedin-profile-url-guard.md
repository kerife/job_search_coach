# LinkedIn Profile URL Privacy Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject LinkedIn `/in/` and legacy `/pub/` profile URLs in case ingestion without changing the public validator interface or diagnostic.

**Architecture:** Extend the existing `_LINKEDIN_PROFILE_VALUE` regex in
`validate_case.py`; keep recursive privacy scanning and error construction
unchanged. Add focused table-driven tests against the real CLI helper, then
run the full plugin and release gates before publication.

**Tech Stack:** Python 3 standard library, `unittest`, JSON fixtures, Codex
plugin manifest/marketplace.

## Global Constraints

- Preserve the existing error text and do not echo sensitive values.
- Reject LinkedIn `/in/` and legacy `/pub/` profile URLs while preserving host boundaries.
- Do not add dependencies, network calls, schemas, renderers, or UI changes.
- Use TDD: observe RED before production code, then GREEN and full gates.

---

### Task 1: Add the failing privacy regressions

**Files:**
- Modify: `tests/test_validate_case.py` near the existing LinkedIn profile URL test.

**Interfaces:**
- Consumes: the existing `valid_case()` fixture and `run_validator_contents()` helper.
- Produces: one table-driven regression covering scheme, `www`, and bare `/in/` forms.

- [ ] **Step 1: Write the failing test**

Add a test that mutates `claims[0].text` for each of these values:

```python
(
    "https://www.linkedin.com/in/synthetic-sentinel/",
    "www.linkedin.com/in/synthetic-sentinel/",
    "linkedin.com/in/synthetic-sentinel/",
    "https://www.linkedin.com/pub/synthetic-sentinel/42/7b/123",
    "www.linkedin.com/pub/synthetic-sentinel/42/7b/123",
    "linkedin.com/pub/synthetic-sentinel/42/7b/123",
)
```

For every mutation assert return code `2`, the existing path-specific
diagnostic, and that the URL is absent from stderr.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_validate_case.ValidateCaseTests.test_rejects_linkedin_profile_url_without_scheme -q
```

Expected: the new `/pub/` cases fail with return code `0` before the production
regex changes; the existing `/in/` cases remain green.

### Task 2: Implement the bounded regex change

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_case.py:99-101`.

**Interfaces:**
- Consumes: the existing recursive `_scan_value` privacy rule list.
- Produces: the same compiled `_LINKEDIN_PROFILE_VALUE` matcher and unchanged
  error path/wording.

- [ ] **Step 1: Write the minimal implementation**

Use a case-insensitive pattern equivalent to:

```python
r"(?<![a-z0-9.-])(?:https?://)?(?:[a-z0-9-]+\.)*linkedin\.com/(?:in|pub)/"
```

Keep the matcher scoped to the host and profile paths; do not broaden it to
arbitrary LinkedIn URLs.

- [ ] **Step 2: Run the focused test and verify GREEN**

Run the Task 1 command again. Expected: all three variants pass and the URL
does not appear in diagnostics.

- [ ] **Step 3: Run the complete case-validator suite**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_validate_case -q
```

Expected: zero failures and no unrelated changed files.

### Task 3: Review, publish, and load

**Files:**
- Modify: `plugins/job-search-coach/.codex-plugin/plugin.json` (release version only).
- Modify: the allowlisted final-eval provenance sidecars (source commit/tree only).

- [ ] **Step 1: Run static, plugin, root, privacy, release, and diff gates.**
- [ ] **Step 2: Consume the cachebuster exactly once after all pre-gates pass.**
- [ ] **Step 3: Stage only the manifest and allowlisted provenance files; commit the publication.**
- [ ] **Step 4: Install with `codex plugin add job-search-coach@job-search-coach-local --json`.**
- [ ] **Step 5: Verify `diff -qr` source/cache, installed release validation, plugin list, and clean Git status.**

Expected: canonical source and installed cache are identical, the plugin is
installed/enabled at the new version, and no unallowlisted tracked file is
modified.
