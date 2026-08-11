# Print Continuity Footer Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the employment-continuity boundary footer intact when any generated artifact is printed or saved as PDF.

**Architecture:** Add `break-inside: avoid` and `page-break-inside: avoid` to the existing print footer selector in the dossier, practice, triage, conversion-outcome, and followthrough-checkpoint CSS assets. Add focused static/render assertions; do not alter renderer markup or copy.

**Tech Stack:** Offline HTML/CSS assets, Python `unittest`, existing design-token/theme parity checks.

## Global Constraints

- Preserve EN/ES continuity and stop copy exactly once.
- Keep footers visible in print; do not add `no-print`, links, buttons, or actions.
- Preserve mobile, dark, prefers-contrast, forced-colors, reduced-motion, and existing card fragmentation rules.
- Synchronize `.superdesign/init/theme.md` raw CSS dumps with the two changed asset families.
- Consume one cachebuster only after all pre-release gates pass.

---

### Task 1: Add RED print-footer assertions

**Files:**
- Modify: focused renderer/static tests for dossier, practice, triage, conversion outcome, and followthrough checkpoint.

- [ ] **Step 1: Write the failing assertions**

For each CSS asset, extract its `@media print` block and assert the footer
selector contains both declarations:

```python
self.assertRegex(print_block, r"footer[^}]*break-inside:\s*avoid")
self.assertRegex(print_block, r"footer[^}]*page-break-inside:\s*avoid")
```

For one EN and one ES representative per surface, assert the canonical
employment boundary occurs once in rendered HTML and `no-print` is absent from
the footer element.

- [ ] **Step 2: Run RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_executive_career_dossier tests.test_render_recruiter_practice_session tests.test_render_private_recruiter_reply_triage tests.test_render_private_recruiter_conversion_outcome tests.test_render_private_recruiter_followthrough_checkpoint -v
```

Expected: the new print-footer assertions fail because current print blocks do
not protect footer fragmentation.

### Task 2: Implement CSS-only atomicity

**Files:**
- Modify: `plugins/professional-growth-coach/assets/executive-career-dossier-v1.css`.
- Modify: `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css`.
- Modify: `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.css`.
- Modify: `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.css`.
- Modify: `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.css`.
- Modify: `.superdesign/init/theme.md` matching raw CSS dumps.

- [ ] **Step 1: Add the declarations**

Inside each existing `@media print` block, extend the current footer selector
with exactly:

```css
break-inside: avoid;
page-break-inside: avoid;
```

Do not change colors, display, copy, or DOM.

- [ ] **Step 2: Run GREEN focused tests and parity**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_executive_career_dossier tests.test_render_recruiter_practice_session tests.test_render_private_recruiter_reply_triage tests.test_render_private_recruiter_conversion_outcome tests.test_render_private_recruiter_followthrough_checkpoint -q
python3 -B plugins/professional-growth-coach/tests/validate_design_tokens.py
git diff --check
```

### Task 3: Regression and release

- [ ] **Step 1:** Run plugin and root suites plus static/privacy/release/official validator gates.
- [ ] **Step 2:** Commit CSS/theme/tests and rebind deterministic sidecars to the functional commit.
- [ ] **Step 3:** Consume one cachebuster, install the canonical plugin, and verify source/cache parity.
- [ ] **Step 4:** Smoke EN/ES dossier, practice, triage, and compact receipts from the installed cache; update attestation and sidecars; rerun all gates with a clean worktree.
