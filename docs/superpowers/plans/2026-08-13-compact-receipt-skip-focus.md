# Compact receipt skip-link focus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the two compact receipt skip links visibly keyboard-focusable in forced-colors mode without changing normal layout or behavior.

**Architecture:** Extend the existing forced-colors media block in each compact receipt stylesheet with system colors and a `:focus-visible` Highlight outline. Keep the two CSS files byte-aligned with their `.superdesign/init/theme.md` source dump, and prove the contract with a parametrized static test.

**Tech Stack:** Python `unittest`, static HTML/CSS assets, Superdesign parity checks, local Codex plugin packaging and release validators.

## Global Constraints

- Modify only the two compact receipt CSS files, `tests/test_dark_mode_accessibility.py`, and the synchronized `.superdesign/init/theme.md` dump until release metadata is intentionally updated.
- Preserve HTML, copy, normal palette, layout, JavaScript, schema, and print behavior.
- The forced-colors skip link must use `Canvas`, `CanvasText`, `Highlight`, and `outline-offset: 2px`.
- Browser/OS forced-colors rendering is not claimed; static evidence and renderer tests are required.

---

### Task 1: Add the failing forced-colors contract test

**Files:**
- Modify: `tests/test_dark_mode_accessibility.py` near the existing compact forced-colors tests

**Interfaces:**
- Consumes: the two compact CSS paths already used by the test module.
- Produces: one parametrized test that fails when either forced-colors block lacks system-colored skip-link focus.

- [ ] **Step 1: Write the failing test**

Add a test that iterates over `private-recruiter-conversion-outcome-v1.css` and `private-recruiter-followthrough-checkpoint-v1.css`, extracts text beginning at `@media (forced-colors: active)`, and asserts:

```python
self.assertRegex(forced, r"\.skip-link\s*\{[^}]*background:\s*Canvas;[^}]*border-color:\s*CanvasText;[^}]*color:\s*CanvasText;")
self.assertRegex(forced, r"\.skip-link:focus-visible\s*\{[^}]*outline:\s*2px solid Highlight;[^}]*outline-offset:\s*2px;")
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_dark_mode_accessibility.DarkModeAccessibilityTests.test_compact_receipt_skip_link_forced_colors -v
```

Expected: FAIL for both compact CSS files because the current forced-colors blocks do not define the skip-link system colors or `:focus-visible` outline.

- [ ] **Step 3: Commit the RED test**

```bash
git add tests/test_dark_mode_accessibility.py
git commit -m "test: cover compact skip link forced focus"
```

### Task 2: Implement the minimal CSS and parity dump

**Files:**
- Modify: `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.css`
- Modify: `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.css`
- Modify: `.superdesign/init/theme.md` matching raw CSS dumps

**Interfaces:**
- Consumes: the RED contract from Task 1.
- Produces: identical forced-colors skip-link behavior in both receipt stylesheets and the source-backed Superdesign dump.

- [ ] **Step 1: Add the minimal rules**

Inside each existing forced-colors block, add:

```css
.skip-link { background: Canvas; border-color: CanvasText; color: CanvasText; }
.skip-link:focus-visible { outline: 2px solid Highlight; outline-offset: 2px; }
```

Mirror the exact declarations in both corresponding raw dumps in `.superdesign/init/theme.md`.

- [ ] **Step 2: Run focused GREEN checks**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_dark_mode_accessibility tests.test_superdesign_theme_asset_parity -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins.professional-growth-coach.tests.test_render_private_recruiter_conversion_outcome plugins.professional-growth-coach.tests.test_render_private_recruiter_followthrough_checkpoint -q
git diff --check
```

Expected: all tests pass and the two CSS dumps remain exact.

- [ ] **Step 3: Commit the implementation**

```bash
git add plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.css plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.css .superdesign/init/theme.md tests/test_dark_mode_accessibility.py
git commit -m "fix: expose compact skip focus in forced colors"
```

### Task 3: Verify and publish the increment

**Files:**
- Modify: release manifest/version and final provenance files only through the repository's existing release workflow.

**Interfaces:**
- Consumes: green CSS/test increment from Task 2.
- Produces: installed local plugin version matching source, cache parity, current attestation, and a synchronized `main`.

- [ ] **Step 1: Run proportional full verification**

Run the compact renderer tests, dark/parity/print tests, full plugin suite, static/privacy checks, and `bash scripts/run_release_validation.sh`. Do not proceed if any fails.

- [ ] **Step 2: Bump, install, and rebind provenance**

After the functional commit, run the official helper exactly once:

```bash
python3 -B /Users/kevinriosferrer/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py plugins/professional-growth-coach
codex plugin add professional-growth-coach@professional-growth-coach-local --json
```

Record the resulting timestamped version, source commit/tree, 109-file
source/cache counts, and normalized hash in every cycle-1/cycle-2 provenance
sidecar and `tests/evals/final/installed-smoke-test.md`.

- [ ] **Step 3: Re-run release gates and publish**

Verify source/cache parity and local plugin identity, run the release/static/privacy/full suites again on the final tree, commit the attestation, and push `main`. Record that the independent remote check may be DNS-blocked and that two enabled plugin identities remain a configuration ambiguity.
