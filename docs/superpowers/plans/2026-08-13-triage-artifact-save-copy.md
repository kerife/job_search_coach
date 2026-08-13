# Triage Artifact-Save Boundary Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clarify that the raw source reply is not retained while the requested private HTML artifact is saved locally.

**Architecture:** Keep the change in the renderer's existing localized fixed-copy map. Do not interpolate filesystem paths into HTML; `_atomic_private_write` remains the only write authority and existing receipt tests remain the permission proof.

**Tech Stack:** Python 3 standard library, `unittest`, existing triage renderer/validator, repository static/privacy/release scripts.

## Global Constraints

- Preserve `delivery.local_save_mode=disabled` semantics: the raw source reply is not retained.
- Preserve the existing no-external-action copy in English and Spanish.
- Never interpolate the requested filesystem path into rendered HTML.
- Preserve atomic private output permissions (`0600`) and symlink-safe output behavior.
- Do not modify schema, CSS, Superdesign assets, or external-action behavior.

---

### Task 1: Lock the clarified copy with RED tests

**Files:**
- Modify: `tests/test_render_private_recruiter_reply_triage.py:95-110, 210-230, 939-1000`

**Interfaces:**
- Consumes: `renderer.render_triage_html()` and `renderer.write_triage_html()`.
- Produces: assertions for the two localized boundary sentences and the requested receipt path.

- [ ] **Step 1: Replace the ambiguous copy expectations with exact EN/ES strings**

```python
expected = {
    "en": (
        "Source reply is not retained by this flow.",
        "This private HTML artifact is saved only at the path you requested.",
    ),
    "es": (
        "Este flujo no conserva la respuesta de origen.",
        "Este artefacto HTML privado solo se guarda en la ruta que solicitaste.",
    ),
}
```

- [ ] **Step 2: Assert the old sentence and internal enum are absent**

```python
self.assertNotIn("Nothing is saved on this device.", document)
self.assertNotIn("No se guarda nada en este dispositivo.", document)
self.assertNotIn("local_save_mode=", document)
```

- [ ] **Step 3: Add a receipt-path assertion to the existing write test**

```python
receipt = self.renderer.write_triage_html(fixture, output)
self.assertEqual(receipt.artifact_path, output.resolve())
```

- [ ] **Step 4: Run the focused tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/professional-growth-coach/scripts \
python3 -B -m unittest \
  tests.test_render_private_recruiter_reply_triage \
  -q
```

Expected: FAIL because the renderer still emits the old ambiguous sentence.

- [ ] **Step 5: Commit the RED tests**

```bash
git add tests/test_render_private_recruiter_reply_triage.py
git commit -m "test: clarify triage artifact save boundary"
```

### Task 2: Implement the minimal localized copy change

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/render_private_recruiter_reply_triage.py:168,269,517`

**Interfaces:**
- Consumes: existing locale-selected `labels["save_disabled"]` rendering.
- Produces: two fixed localized sentences in the existing footer, with no dynamic path data.

- [ ] **Step 1: Replace the English and Spanish `save_disabled` labels**

```python
# English locale
"save_disabled": (
    "Source reply is not retained by this flow. "
    "This private HTML artifact is saved only at the path you requested."
)

# Spanish locale
"save_disabled": (
    "Este flujo no conserva la respuesta de origen. "
    "Este artefacto HTML privado solo se guarda en la ruta que solicitaste."
)
```

Keep both values fixed strings; do not add a path argument or derive copy from
the receipt path.

- [ ] **Step 2: Run the focused tests and verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/professional-growth-coach/scripts \
python3 -B -m unittest \
  tests.test_render_private_recruiter_reply_triage \
  -q
```

Expected: PASS with all renderer tests green and no raw path in output.

- [ ] **Step 3: Run the triage contract tests**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/professional-growth-coach/scripts \
python3 -B -m unittest tests.test_private_recruiter_reply_triage -q
```

Expected: PASS; validator and delivery boundaries remain unchanged.

- [ ] **Step 4: Commit the implementation**

```bash
git add plugins/professional-growth-coach/scripts/render_private_recruiter_reply_triage.py tests/test_render_private_recruiter_reply_triage.py
git commit -m "fix: clarify triage artifact save boundary"
```

### Task 3: Run independent review and release gates

**Files:**
- Read-only review of the implementation and tests.
- No additional production files expected.

**Interfaces:**
- Consumes: Task 2 renderer and test changes.
- Produces: review approval plus verified release candidate.

- [ ] **Step 1: Ask an independent reviewer to check copy, path non-interpolation, and permissions**

The reviewer must exercise both locales and all three states with
`render_triage_html()`, assert each new sentence appears exactly once, assert
the requested path is absent from the HTML, and run the existing
`test_cli_writes_mode_0600_deterministic_output_and_rejects_symlink_targets`.
It must report any false claim or privacy regression without editing files.

- [ ] **Step 2: Run the full plugin suite and static/privacy checks**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/professional-growth-coach/tests -p 'test_*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
bash scripts/run_release_validation.sh
```

- [ ] **Step 3: Run the root suite and record any known harness diagnostics**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/professional-growth-coach/scripts \
python3 -B -m unittest discover -s tests -p 'test_*.py' -q
```

### Task 4: Bump, install, attest, and publish

**Files:**
- Modify: generated plugin manifest version through the approved cachebuster.
- Modify: `tests/evals/final/cycle-1/*.json`, `tests/evals/final/cycle-2/*.json`, both cycle index files, and `tests/evals/final/installed-smoke-test.md` for provenance.

**Interfaces:**
- Consumes: verified source commit and installed cache.
- Produces: source/cache parity, installed smoke, and pushed `main` release.

- [ ] **Step 1: Run the cachebuster exactly once and commit the manifest bump**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  /Users/kevinriosferrer/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py \
  plugins/professional-growth-coach
git add plugins/professional-growth-coach/.codex-plugin/plugin.json
git commit -m "chore: bump triage artifact copy cachebuster"
```

- [ ] **Step 2: Install the local plugin and verify the materialized version**

```bash
codex plugin add professional-growth-coach@professional-growth-coach-local --json
codex plugin list
```

The listed local version must match the manifest and be enabled.

- [ ] **Step 3: Compute source/cache parity**

Compare the source and installed cache with `diff -qr --exclude='__pycache__'`;
both file counts must be 109. Hash each relative path plus its file SHA-256 in
sorted order and record the resulting normalized hash in installed smoke.

- [ ] **Step 4: Rebind all cycle provenance to the immediate parent of the final attestation commit**

Set every cycle JSON/Markdown `source_commit` to the source commit used for the
installed cache, set `source_tree` to
`git rev-parse <source_commit>:plugins/professional-growth-coach`, and update
the installed smoke timestamp, materialized version, file counts, and hash.
Commit the attestation, then verify the recorded source commit is the final
attestation commit's immediate parent.

- [ ] **Step 5: Run static/privacy/official/root gates again after attestation**

Run the exact commands from Task 3, plus the source/cache parity comparison;
all commands must exit 0 before publication.

- [ ] **Step 6: Verify repository and plugin identity**

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
codex plugin list
```

The worktree must be clean. The local plugin must be enabled at the new
version; any separately enabled public identity is reported, not silently
changed.

- [ ] **Step 7: Push `main` and verify the tracking ref matches**

```bash
git push origin main
git rev-parse HEAD
git rev-parse origin/main
```

The two commit IDs must match after the push.
