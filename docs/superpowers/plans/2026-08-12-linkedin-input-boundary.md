# LinkedIn Input Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make LinkedIn report and bundle ingestion reject symlink traversal and oversized or undecodable files without exposing local paths or payloads.

**Architecture:** Reuse the existing descriptor-anchored private input loader rather than maintaining a second pathname-based reader. The LinkedIn validator translates loader failures into its existing bounded CLI diagnostics, while valid regular files retain the current validation behavior.

**Tech Stack:** Python 3, `os.open`/descriptor-boundary loader, unittest, existing plugin release validator and installed smoke checks.

## Global Constraints

- Reject direct and intermediate symlinks and non-regular input files.
- Bound report and bundle reads at 256 KiB before decoding or parsing.
- Never interpolate input paths, errno text, or input payloads into failure diagnostics.
- Preserve valid regular-file behavior and existing duplicate/JSON validation semantics.
- Keep source and installed cache byte-equivalent after the release refresh.

---

### Task 1: Add failing boundary tests

**Files:**
- Modify: `tests/test_linkedin_client_report.py`
- Modify: `tests/test_linkedin_report_fixtures.py`

- [ ] **Step 1: Write failing tests** for `load_bundle` and CLI validation using a valid fixture behind an intermediate directory symlink, a regular fixture, a 256 KiB-plus fixture, and invalid UTF-8 bytes. Assert fixed nonzero diagnostics, no external marker/path, and unchanged success for regular files.
- [ ] **Step 2: Run the focused tests** and confirm they fail because the current loader follows the parent symlink or reads the full file before validation.

### Task 2: Wire the shared bounded descriptor loader

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_linkedin_client_report.py`
- Reuse: `plugins/professional-growth-coach/scripts/private_input_loader.py`

- [ ] **Step 1: Import the shared loader through the validator's existing dynamic-import-safe pattern.**
- [ ] **Step 2: Replace report and bundle pathname reads with bounded descriptor reads using a 256 KiB limit.**
- [ ] **Step 3: Translate loader errors into the current generic unavailable/invalid-input diagnostics without paths or payloads.**
- [ ] **Step 4: Run the focused tests and confirm GREEN.**

### Task 3: Regression and release checks

**Files:**
- Modify: `tests/evals/final/installed-smoke-test.md` only after the release refresh.
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json` for the cache-buster version.

- [ ] **Step 1: Run LinkedIn fixture/client suites and the complete plugin suite.**
- [ ] **Step 2: Run privacy, static/schema/handoff, and official release validators.**
- [ ] **Step 3: Bump the patch cache-buster, install the canonical local plugin, and compare source/cache manifests and normalized hashes.**
- [ ] **Step 4: Run installed smoke tests and update attestation with the final source commit/tree.**
- [ ] **Step 5: Attempt the configured GitHub push only after the final verification; report network or credential blockers without claiming publication.**
