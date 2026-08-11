# Triage Plain Save Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove schema vocabulary from the triage footer while preserving the internal local-save contract and all safety behavior.

**Architecture:** Change the two localized `save_disabled` strings in the triage renderer only. Extend renderer tests across ready, clarify, and stop fixtures in English and Spanish to assert plain copy, absence of enum/old strings, and unchanged internal validation. No schema, CSS, state, or action changes.

**Tech Stack:** Python 3, `unittest`, deterministic offline HTML renderer, existing plugin release workflow.

## Global Constraints

- Internal `delivery.local_save_mode` remains `disabled` and schema validation remains unchanged.
- Visible copy is exactly `Nothing is saved on this device.` or `No se guarda nada en este dispositivo.`.
- The footer remains printable and outside any `no-print` element.
- Stop continuity/no-resignation copy and external-action boundaries remain unchanged.
- Consume one cachebuster only after all pre-release gates pass.

---

### Task 1: Add RED renderer assertions

**Files:**
- Modify: `tests/test_render_private_recruiter_reply_triage.py` near the existing localized footer tests.

- [ ] **Step 1: Write the failing test**

For ready, clarify, and stop fixtures in both locales, render the HTML and assert:

```python
plain = "Nothing is saved on this device." if locale == "en" else "No se guarda nada en este dispositivo."
old = "Local saving is disabled (local_save_mode=disabled)." if locale == "en" else "El guardado local está deshabilitado (local_save_mode=disabled)."
self.assertEqual(html.count(plain), 1)
self.assertNotIn("local_save_mode=", html)
self.assertNotIn(old, html)
self.assertNotIn("no-print", html[html.index(plain) - 300:html.index(plain) + 300])
```

Also validate the source fixture's `delivery.local_save_mode` remains
`disabled` before rendering.

- [ ] **Step 2: Run the focused test and verify RED**

```bash
PYTHONPATH=plugins/professional-growth-coach/scripts python3 -B -m unittest tests.test_render_private_recruiter_reply_triage -v
```

Expected: the new plain-copy assertions fail because current HTML contains the enum-labelled strings.

### Task 2: Implement the minimal copy change

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/render_private_recruiter_reply_triage.py` localized label maps only.

- [ ] **Step 1: Replace visible labels**

Change only:

```python
"save_disabled": "No se guarda nada en este dispositivo.",
"save_disabled": "Nothing is saved on this device.",
```

Do not alter the fixture enum, validator, HTML class, state branch, or footer structure.

- [ ] **Step 2: Run focused GREEN tests**

```bash
PYTHONPATH=plugins/professional-growth-coach/scripts python3 -B -m unittest tests.test_render_private_recruiter_reply_triage -q
```

Expected: all triage renderer tests pass and no old enum vocabulary remains in rendered output.

### Task 3: Run regression gates

- [ ] **Step 1: Run plugin and root suites**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/professional-growth-coach/tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test*.py' -q
```

- [ ] **Step 2: Run static, privacy, release, and diff checks**

```bash
python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
python3 -B scripts/check_repository_privacy.py
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_release_validation.sh
git diff --check
```

### Task 4: Publish and smoke the increment

- [ ] **Step 1: Commit the functional change and refresh pre-release provenance.**
- [ ] **Step 2: Consume the official cachebuster exactly once, commit manifest and sidecars, and install the canonical marketplace plugin.**
- [ ] **Step 3: Compare source/cache inventory and hash; render installed ready/clarify/stop EN/ES fixtures and assert plain copy plus internal enum validation.**
- [ ] **Step 4: Update installed attestation, bind sidecars to the release parent, rerun all gates, and require a clean worktree.**
