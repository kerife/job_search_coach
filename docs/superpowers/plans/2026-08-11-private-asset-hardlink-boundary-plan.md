# Private renderer asset hardlink boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every canonical private renderer asset fail closed when its inode has more than one hardlink.

**Architecture:** Keep the existing `private_asset_loader` as the single runtime and static boundary. Add a focused loader test for normal files and external hardlinks, then enforce `stat.S_ISREG` and `st_nlink == 1` immediately before reading; no renderer or schema changes are needed.

**Tech Stack:** Python 3, `pathlib`, `stat`, `unittest`, existing static/release harnesses.

## Global Constraints

- Preserve the generic bounded error: `renderer asset input must be a regular file`.
- Do not echo external paths or file contents.
- Preserve symlink/traversal and no-external-action behavior.
- Run the cachebuster exactly once after all code changes and verify source/cache equivalence before loading the release.

---

### Task 1: Add the hardlink regression test

**Files:**
- Create: `plugins/professional-growth-coach/tests/test_private_asset_loader.py`

**Interfaces:**
- Consumes: `private_asset_loader.read_private_asset`.
- Produces: focused tests proving regular-file acceptance and hardlink rejection.

- [ ] **Step 1: Write the failing test**

Create a temporary package root, write `outside.txt` with a sentinel, create
`assets/asset.css` with `os.link(outside, asset)`, and assert
`read_private_asset(root, asset)` raises `PrivateAssetError` without including
the sentinel in the exception text. Also write a copied regular file and assert
its content is returned.

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins.professional-growth-coach.tests.test_private_asset_loader -v
```

Expected: the hardlink case fails because the current loader reads the linked
inode.

### Task 2: Enforce the inode boundary

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/private_asset_loader.py`

**Interfaces:**
- Consumes: the existing absolute/path-component checks.
- Produces: `_regular_package_path(plugin_root, asset_path) -> Path` that rejects
  non-regular or multiply-linked inodes with the existing `PrivateAssetError`.

- [ ] **Step 1: Add the minimal check**

Import `stat`, call `current.stat(follow_symlinks=False)` after the existing
symlink and `is_file()` checks, and reject unless
`stat.S_ISREG(status.st_mode)` and `status.st_nlink == 1`.

- [ ] **Step 2: Run the focused test to verify it passes**

Run the Task 1 command; expected result is all focused tests green, with the
external sentinel never present in an error.

### Task 3: Run package gates

**Files:**
- Modify: none beyond Tasks 1–2.

- [ ] **Step 1: Run loader, renderer, privacy, and static tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/professional-growth-coach/tests -p 'test_*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py --repo-root .
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
```

- [ ] **Step 2: Run the root suite**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_*.py' -q
```

Expected: no hardlink regressions, no stale provenance, and all tests green.

### Task 4: Publish and load the increment

- [ ] **Step 1: Commit code and tests, then run the cachebuster once**

```bash
git add plugins/professional-growth-coach/scripts/private_asset_loader.py plugins/professional-growth-coach/tests/test_private_asset_loader.py docs/superpowers/specs/2026-08-11-private-asset-hardlink-boundary-design.md docs/superpowers/plans/2026-08-11-private-asset-hardlink-boundary-plan.md
git commit -m "fix: reject hardlinked private renderer assets"
PYTHONDONTWRITEBYTECODE=1 python3 -B $HOME/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py plugins/professional-growth-coach
```

- [ ] **Step 2: Rebind final-cycle provenance to the current commit**

Set each `source_commit` in `tests/evals/final/cycle-1` and `cycle-2` to the
commit immediately before the provenance-only commit, preserve the current
`source_tree`, run `run_static_checks.py`, then commit only those 14 sidecars.

- [ ] **Step 3: Install the exact canonical version locally**

```bash
codex plugin add professional-growth-coach@professional-growth-coach-local --json
```

- [ ] **Step 4: Compare source/cache trees and run the five-artifact installed smoke**

Use `diff -qr --exclude='__pycache__'` against the installed version and run
the installed validators/renderers on dossier ES/EN, triage ES/EN, and practice
ES, asserting five non-empty HTML outputs, CSP `default-src 'none'`, and no
`javascript:` URLs.

- [ ] **Step 5: Update the installed attestation and run final gates**

Record the new version, source commit/tree, file counts, normalized aggregate
hash, and `installed_green` in `tests/evals/final/installed-smoke-test.md`,
then run the privacy gate, static checks, release validation, root unittest
suite, `git diff --check`, and `git status --short --branch`.
