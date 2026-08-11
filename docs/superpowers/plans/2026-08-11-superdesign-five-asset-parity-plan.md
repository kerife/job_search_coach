# Superdesign Five-Asset Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Superdesign parity test guard every shipped CSS dump.

**Architecture:** Keep `_theme_dump(name)` as the exact byte comparison. Add a
small heading extractor and assert the set of theme CSS paths equals the set of
asset CSS paths before comparing each file. This preserves current behavior and
adds coverage for the two compact receipts.

**Tech Stack:** Python 3.14, `unittest`, regular expressions, Markdown raw CSS
dumps.

## Global Constraints

- No production CSS, renderer, schema, copy, or runtime changes.
- Preserve exact UTF-8 dump equality and existing subtest diagnostics.
- Fail closed on both missing and unexpected theme dump headings.

---

### Task 1: Add the parity regression coverage

**Files:**
- Modify: `tests/test_superdesign_theme_asset_parity.py`
- Reference: `.superdesign/init/theme.md`
- Assets: `plugins/professional-growth-coach/assets/*.css`

**Interfaces:**
- Consumes: Markdown headings matching
  ``### `plugins/professional-growth-coach/assets/<name>.css` ``.
- Produces: exact five-asset parity assertion and byte-for-byte comparisons.

- [ ] **Step 1: Write the failing coverage assertion**

Add the two compact filenames to the expected asset set and add a helper that
extracts all CSS headings from `theme.md`. Assert that the extracted relative
paths equal the shipped CSS path set. In a temporary-copy mutation check,
changing the compact dump must make the corresponding exact comparison fail.

- [ ] **Step 2: Run RED against the old coverage**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_superdesign_theme_asset_parity -v
```

Expected: the new five-asset expectation fails before implementation because
the hard-coded three-name tuple omits the compact assets.

- [ ] **Step 3: Implement the minimal test fix**

Set `ASSET_NAMES` to all five shipped CSS filenames, extract theme headings
with an anchored multiline regex, compare exact path sets, and retain the
existing loop through `_theme_dump(name)` for byte equality.

- [ ] **Step 4: Run GREEN and integration checks**

Run the parity test, all plugin tests, design-token validation, root privacy/
structure tests, static checks, and release validation. No browser claim is
needed because this increment only strengthens source parity.

- [ ] **Step 5: Publish and smoke**

Bump once, install the canonical plugin, verify source/cache parity and hash,
refresh the attestation/provenance, and rerun the existing five renderer
smokes before closing the cycle.
