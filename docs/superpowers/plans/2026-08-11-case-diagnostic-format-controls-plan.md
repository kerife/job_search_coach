# Case Diagnostic Format-Control Escaping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent Unicode format characters from spoofing `validate_case` diagnostics.

**Architecture:** Reuse `_escape_diagnostic_controls` in `validate_case.py`.
Only its Unicode-category allowlist changes; all callers, diagnostic caps, and
validation behavior remain unchanged.

**Tech Stack:** Python 3.14, `unicodedata`, `unittest`, existing release gates.

## Global Constraints

- Escape `Cc`, `Cs`, `Cf`, `Zl`, and `Zp` as lowercase `\\uXXXX` sequences.
- Preserve ordinary ASCII and existing short diagnostics.
- Do not echo supplied paths, payloads, or raw control/format characters.

---

### Task 1: Add RED coverage for format controls

**Files:**
- Modify: `tests/test_validate_case.py`
- Reference: `plugins/professional-growth-coach/scripts/validate_case.py:_escape_diagnostic_controls`

- [ ] **Step 1: Add bidi, isolate, and zero-width cases**

Extend the existing CLI diagnostic test with representative `Cf` characters
and assert the escaped form plus absence of the raw character.

- [ ] **Step 2: Run RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_validate_case.ValidateCaseTests.test_cli_escapes_unicode_format_controls_in_unknown_field_diagnostics -v
```

Expected: FAIL because the current category set omits `Cf`.

### Task 2: Implement and verify GREEN

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_case.py:_escape_diagnostic_controls`
- Test: `tests/test_validate_case.py`

- [ ] **Step 1: Add `Cf` to the category set**

Change the existing category membership to `{"Cc", "Cs", "Cf", "Zl", "Zp"}`
without changing formatting or validation flow.

- [ ] **Step 2: Run focused and full case tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_validate_case -q
```

Expected: all case tests pass, including existing C0, surrogate, and line
separator regressions.

- [ ] **Step 3: Run integration gates**

Run the plugin suite, root privacy/structure tests, static checks, and official
release validation. All must pass before the release bump.

- [ ] **Step 4: Publish and smoke**

Bump once, install the canonical plugin, verify source/cache inventory and
hash, update attestation/provenance, and rerun installed validator/renderer
smokes.
