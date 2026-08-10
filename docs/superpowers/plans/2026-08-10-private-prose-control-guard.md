# Private Prose Control Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make dossier, recruiter-practice, and recruiter-reply-triage prose reject all Unicode control/format characters without changing visible copy or action behavior.

**Architecture:** Add a dependency-free helper in `private_prose_safety.py` that NFKC-normalizes only for inspection and rejects any character categorized by `unicodedata` as `Cc` or `Cf`. Existing validators call the helper before their current regex checks; each schema adds equivalent control-character `not.pattern` guards to the prose definitions used by its validator.

**Tech Stack:** Python 3 standard library (`unicodedata`, `re`), dependency-free JSON Schema subset checker, `unittest`, JSON Schema fixtures.

## Global Constraints

- Reject controls fail-closed; do not strip them before storing or rendering.
- Preserve visible whitespace, existing privacy regexes, copy, ordering, and action flags.
- Do not add runtime dependencies or echo rejected prose in diagnostics.
- Canonical marketplace remains `/Users/kevinriosferrer/projects/job_search_coach`.

---

### Task 1: Shared Unicode-control helper

**Files:**
- Create: `plugins/job-search-coach/scripts/private_prose_safety.py`
- Test: `plugins/job-search-coach/tests/test_private_prose_safety.py`

**Interfaces:**
- Produces `contains_unicode_controls(value: object) -> bool`.
- Produces `is_safe_prose_text(value: object) -> bool`, rejecting non-strings and any `Cc`/`Cf` character while accepting normal text and whitespace.

- [ ] **Step 1: Write the failing tests**

```python
from private_prose_safety import contains_unicode_controls, is_safe_prose_text

def test_rejects_zero_width_bidi_and_bom_controls():
    for value in ("Recruiter\u200b: Jordan Lee", "Candidate\u202e: Ana López", "x\u2066y", "x\ufeffy"):
        assert contains_unicode_controls(value)
        assert not is_safe_prose_text(value)

def test_accepts_normalized_visible_prose_and_whitespace():
    assert not contains_unicode_controls("The candidate should explain scope.")
    assert is_safe_prose_text("  The candidate should explain scope.  ")
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins/job-search-coach/tests/test_private_prose_safety.py -q`

Expected: import failure because the helper does not exist.

- [ ] **Step 3: Implement the minimal helper**

```python
import unicodedata

def contains_unicode_controls(value: object) -> bool:
    return isinstance(value, str) and any(
        unicodedata.category(character) in {"Cc", "Cf"}
        for character in unicodedata.normalize("NFKC", value)
    )

def is_safe_prose_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not contains_unicode_controls(value)
```

- [ ] **Step 4: Run the focused test and verify it passes**

Run the command from Step 2. Expected: all helper tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/job-search-coach/scripts/private_prose_safety.py plugins/job-search-coach/tests/test_private_prose_safety.py
git commit -m "test: define Unicode control prose boundary"
```

### Task 2: Apply the helper to validators and dossier guard

**Files:**
- Modify: `plugins/job-search-coach/scripts/dossier_practice_safe_text.py`
- Modify: `plugins/job-search-coach/scripts/validate_private_recruiter_reply_triage.py`
- Modify: `plugins/job-search-coach/scripts/validate_recruiter_practice_session.py`
- Test: `plugins/job-search-coach/tests/test_dossier_recruiter_practice_handoff.py`
- Test: `plugins/job-search-coach/tests/test_private_recruiter_reply_triage.py`
- Test: `plugins/job-search-coach/tests/test_recruiter_practice_session.py`

**Interfaces:**
- Existing validator entry points remain unchanged.
- `_text`/safe-text paths add the helper as an additional fail-closed condition.
- Existing error categories remain bounded and do not include rejected values.

- [ ] **Step 1: Add RED mutations to all prose surfaces**

```python
mutations = (
    "Recruiter\u200b: Jordan Lee.",
    "Candidate\u202e: Ana López.",
    "Raw\u2066 recruiter reply.",
    "person\ufeff@example.org",
)
for field in prose_fields:
    mutated = copy.deepcopy(valid_fixture)
    set_nested(mutated, field, mutations[0])
    self.assertTrue(validate(mutated), field)
```

Cover safe context, facts, question/requirement prose, blocked claims, rubric, and feedback statements where each artifact supports them.

- [ ] **Step 2: Run focused tests and verify RED**

Run the two artifact test modules plus the dossier handoff module. Expected: each control mutation is currently accepted by at least one validator.

- [ ] **Step 3: Wire the shared helper into the existing prose checks**

Call `is_safe_prose_text` for each `_text`/safe-text value before existing regex checks; extend dossier’s `is_safe_handoff_text` to reject every `Cc`/`Cf` category instead of only its previous explicit subset. Preserve current visible prose and error strings.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins/job-search-coach/tests/test_private_prose_safety.py plugins/job-search-coach/tests/test_dossier_recruiter_practice_handoff.py plugins/job-search-coach/tests/test_private_recruiter_reply_triage.py plugins/job-search-coach/tests/test_recruiter_practice_session.py -q`

Expected: all canonical and mutation tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/job-search-coach/scripts plugins/job-search-coach/tests
git commit -m "fix: reject Unicode controls in private prose"
```

### Task 3: Schema parity and static gate coverage

**Files:**
- Modify: `plugins/job-search-coach/schemas/dossier-recruiter-practice-handoff-v1.schema.json`
- Modify: `plugins/job-search-coach/schemas/private-recruiter-reply-triage-v1.schema.json`
- Modify: `plugins/job-search-coach/schemas/recruiter-practice-session-v1.schema.json`
- Test: `plugins/job-search-coach/tests/test_private_schema_conformance.py`

**Interfaces:**
- Schema instances containing `Cc`/`Cf` in projected prose fail the existing dependency-free checker.
- Canonical fixtures remain schema-valid and custom-validator-valid.

- [ ] **Step 1: Add schema mutation tests**

```python
for control in ("\u200b", "\u202e", "\u2066", "\ufeff"):
    mutated = copy.deepcopy(canonical)
    mutated["facts"][0]["summary"] = f"Safe prefix{control} hidden"
    self.assertTrue(validate_schema_instance(mutated, schema), control)
```

- [ ] **Step 2: Run schema tests and verify RED**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins/job-search-coach/tests/test_private_schema_conformance.py -q`

Expected: schema-only validation accepts at least one mutation before schema guards are added.

- [ ] **Step 3: Add bounded `not.pattern` control guards**

Use the dependency-free checker-compatible pattern `.*[\\u0000-\\u001f\\u007f-\\u009f\\u200b-\\u200d\\u2060\\u202a-\\u202e\\u2066-\\u2069\\ufeff].*` (and the equivalent complete Unicode category coverage in custom validators). Apply it only to prose fields, not IDs or enum fields.

- [ ] **Step 4: Run schema, static, and plugin tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins/job-search-coach/tests/test_private_schema_conformance.py -q
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/job-search-coach/tests/run_static_checks.py
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/job-search-coach/tests -p 'test_*.py' -q
```

Expected: all commands exit 0 and static output remains bounded.

- [ ] **Step 5: Commit**

```bash
git add plugins/job-search-coach/schemas plugins/job-search-coach/tests/test_private_schema_conformance.py
git commit -m "test: enforce schema parity for Unicode controls"
```

### Task 4: Marketplace release and verification

**Files:**
- Modify: `plugins/job-search-coach/.codex-plugin/plugin.json` via `update_plugin_cachebuster.py`
- Modify: final fixture provenance only as required by existing gate

- [ ] **Step 1: Run official plugin and skill validators, privacy, diff checks, and root suite.**
- [ ] **Step 2: Refresh deterministic provenance against the immediate parent after the final code commit.**
- [ ] **Step 3: Run the cachebuster exactly once and commit the manifest update.**
- [ ] **Step 4: Refresh provenance once more against the cachebuster parent and commit it.**
- [ ] **Step 5: Run final static/plugin/root gates.**
- [ ] **Step 6: Reinstall `job-search-coach@job-search-coach-local` and verify installed path/version/cache diff.**
- [ ] **Step 7: Confirm `git status --short` is clean and provide Codex View/Share links.**
