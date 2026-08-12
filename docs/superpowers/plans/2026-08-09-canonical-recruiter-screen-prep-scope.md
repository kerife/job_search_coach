# Canonical Recruiter-Screen Preparation Scope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every ready recruiter-reply `prep_scope` directly assignable to `practice.question.kind` by using only the canonical `screen_opening` literal.

**Architecture:** Keep the existing closed triage and practice artifacts. Remove the one exceptional alias at the triage producer boundary, compare packet scopes directly with `question.kind`, and retain the existing localized label lookup. Exercise the schema, Python validator, renderer, and manual triage-to-practice boundary as one atomic TDD change.

**Tech Stack:** Python 3 standard library, `unittest`, Draft 2020-12 JSON Schema, static offline HTML/CSS, Git, Codex plugin CLI.

## Global Constraints

- `screen_opening` is the only canonical screen-opening scope.
- `recruiter_screen_opening` must fail closed in packet and reentry packet.
- The handoff remains partial and manual; it does not construct a complete practice session.
- Preserve Q/F/context/snapshot parity, `question_rank=1`, unanswered state, no-save, no-auto-start, and no-external-action invariants.
- Preserve `Screen opening` / `Apertura de filtro`, existing ARIA relationships, heading/region order, responsive, print, and forced-colors behavior.
- Do not expose either raw enum in visible or accessible candidate-facing output.
- Do not add an adapter, expand the practice enum, retain raw replies/answers, or authorize messaging, calendar, contact, or any external action.
- Run the cachebuster exactly once, only after all tests and static checks are green.

---

## File Structure

- `plugins/job-search-coach/schemas/private-recruiter-reply-triage-v1.schema.json`: closed packet and reentry scope enums.
- `plugins/job-search-coach/scripts/validate_private_recruiter_reply_triage.py`: direct scope-to-question-kind validation.
- `plugins/job-search-coach/scripts/render_private_recruiter_reply_triage.py`: canonical scope-to-localized-copy lookup.
- `tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json`: canonical screen-invite packet fixture.
- `tests/test_private_recruiter_reply_triage.py`: procedural contract and removed-alias coverage.
- `tests/test_render_private_recruiter_reply_triage.py`: localized rendering and privacy/accessibility regression coverage.
- `tests/test_recruiter_practice_session.py`: five-route triage-to-practice scope parity.
- `plugins/job-search-coach/tests/test_private_schema_conformance.py`: executable JSON Schema mutation coverage.
- `plugins/job-search-coach/.codex-plugin/plugin.json`: publication version only.
- `tests/evals/final/cycle-1.md`, `tests/evals/final/cycle-1/*.json`, `tests/evals/final/cycle-2.md`, `tests/evals/final/cycle-2/*.json`: mechanical publication provenance.

### Task 1: Canonicalize the triage scope atomically

**Files:**
- Modify: `plugins/job-search-coach/schemas/private-recruiter-reply-triage-v1.schema.json:140-164`
- Modify: `plugins/job-search-coach/scripts/validate_private_recruiter_reply_triage.py:294-340`
- Modify: `plugins/job-search-coach/scripts/render_private_recruiter_reply_triage.py:253-261`
- Modify: `tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json`
- Modify: `tests/test_private_recruiter_reply_triage.py:107-115,160-200,250-325`
- Modify: `tests/test_render_private_recruiter_reply_triage.py:240-380`
- Modify: `tests/test_recruiter_practice_session.py:96-145`
- Modify: `plugins/job-search-coach/tests/test_private_schema_conformance.py:55-75`

**Interfaces:**
- Consumes: validated triage fields `classification`, `question.kind`, `handoff.packet`, and `handoff.reentry_packet`; complete `recruiter-practice-session-v1` fixture.
- Produces: packet and reentry `prep_scope` values that are literal members of `QUESTION_KINDS` and can be assigned to `practice.question.kind` without translation.

- [ ] **Step 1: Reconfirm the in-place 0.x migration precondition**

Run:

```bash
rg -n "recruiter_screen_opening" . \
  --glob '!docs/superpowers/specs/2026-08-09-canonical-recruiter-screen-prep-scope-design.md' \
  --glob '!docs/superpowers/plans/2026-08-09-canonical-recruiter-screen-prep-scope.md'
active_version=$(python3 -B -c 'import json, pathlib; print(json.loads(pathlib.Path("plugins/job-search-coach/.codex-plugin/plugin.json").read_text())["version"])')
active_plugin="$HOME/.codex/plugins/cache/job-search-coach-local/job-search-coach/$active_version"
test -d "$active_plugin"
rg -n "recruiter_screen_opening" "$active_plugin"
```

Expected: repository hits are limited to the known schema, validator, renderer, fixture, and tests; active-install hits are limited to the managed plugin cache. If another durable consumer appears, stop this in-place plan and write a versioned triage/reentry migration plan.

- [ ] **Step 2: Write failing schema, contract, renderer, and integration tests**

Add executable schema mutation coverage in `plugins/job-search-coach/tests/test_private_schema_conformance.py`:

```python
def test_triage_schema_uses_canonical_screen_opening_scope(self):
    schema = self._schema("private-recruiter-reply-triage-v1.schema.json")
    fixture = json.loads(
        (
            ROOT.parent.parent
            / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json"
        ).read_text(encoding="utf-8")
    )
    canonical = copy.deepcopy(fixture)
    canonical["handoff"]["packet"]["prep_scope"] = "screen_opening"
    canonical["handoff"]["reentry_packet"]["prep_scope"] = "screen_opening"
    self.assertEqual([], validate_schema_instance(canonical, schema))

    for field in ("packet", "reentry_packet"):
        with self.subTest(field=field):
            removed_alias = copy.deepcopy(canonical)
            removed_alias["handoff"][field]["prep_scope"] = "recruiter_screen_opening"
            self.assertIn(
                f"$.handoff.{field}.prep_scope: enum mismatch",
                validate_schema_instance(removed_alias, schema),
            )
```

In `tests/test_private_recruiter_reply_triage.py`, change all expected scope maps to identity maps and add explicit removed-alias rejection:

```python
scopes = {
    "screen_opening": "screen_opening",
    "proof_example": "proof_example",
    "eligibility_boundary": "eligibility_boundary",
    "compensation_boundary": "compensation_boundary",
    "missing_detail": "missing_detail",
}

canonical = copy.deepcopy(fixture)
canonical["classification"] = "screen_invite"
canonical["question"]["kind"] = "screen_opening"
canonical["handoff"]["packet"]["prep_scope"] = "screen_opening"
canonical["handoff"]["reentry_packet"]["prep_scope"] = "screen_opening"
for field, message in (
    ("packet", "handoff.packet.prep_scope has invalid value"),
    ("reentry_packet", "handoff.reentry_packet.prep_scope has invalid value"),
):
    with self.subTest(removed_alias_field=field):
        removed_alias = copy.deepcopy(canonical)
        removed_alias["handoff"][field]["prep_scope"] = "recruiter_screen_opening"
        self.assert_rejected(removed_alias, message)
```

In `tests/test_render_private_recruiter_reply_triage.py`, replace each test-only `screen_opening` scope alias with the canonical value and retain literal expectations for `Screen opening` / `Apertura de filtro`. Add privacy assertions to the screen-opening subcase:

```python
self.assertNotIn("screen_opening", document)
self.assertNotIn("recruiter_screen_opening", document)
self.assertIn('aria-labelledby="handoff-title"', document)
self.assertIn('aria-describedby="handoff-description"', document)
```

Add a five-route integration test in `tests/test_recruiter_practice_session.py`:

```python
def test_all_ready_triage_scopes_are_directly_assignable_to_practice_kind(self) -> None:
    cases = {
        "screen_invite": "screen_opening",
        "request_for_proof": "proof_example",
        "eligibility_question": "eligibility_boundary",
        "compensation_question": "compensation_boundary",
        "unknown": "missing_detail",
    }
    for classification, kind in cases.items():
        with self.subTest(classification=classification):
            triage = load_triage_fixture()
            triage["classification"] = classification
            triage["question"]["kind"] = kind
            triage["handoff"]["packet"]["prep_scope"] = kind
            triage["handoff"]["reentry_packet"]["prep_scope"] = kind
            triage_result = self.run_triage_cli(triage)
            self.assertEqual(triage_result.returncode, 0, triage_result.stderr)

            practice = copy.deepcopy(self.awaiting_session)
            practice["safe_context"]["summary"] = triage["safe_context"]["summary"]
            practice["facts"][0] = copy.deepcopy(triage["facts"][0])
            practice["question"]["id"] = triage["question"]["id"]
            practice["question"]["kind"] = triage["handoff"]["reentry_packet"]["prep_scope"]
            practice["question"]["text"] = triage["question"]["text"]
            practice["question"]["fact_ids"] = [triage["facts"][0]["id"]]
            practice["requirement"]["fact_ids"] = [triage["facts"][0]["id"]]
            practice["handoff_context"]["source"] = "private_recruiter_reply_triage"
            practice["handoff_context"]["source_snapshot"] = triage["handoff"]["reentry_packet"]["source_snapshot"]
            practice["handoff_context"]["question_id"] = triage["question"]["id"]
            practice["handoff_context"]["fact_ids"] = [triage["facts"][0]["id"]]
            practice["handoff_context"].pop("claim_ids")
            practice["handoff_context"].pop("evidence_ids")

            self.assertEqual(kind, triage["question"]["kind"])
            self.assertEqual(kind, triage["handoff"]["packet"]["prep_scope"])
            self.assertEqual(kind, triage["handoff"]["reentry_packet"]["prep_scope"])
            self.assertEqual(kind, practice["question"]["kind"])
            self.assertEqual(1, practice["handoff_context"]["question_rank"])
            self.assert_accepted(practice)
```

- [ ] **Step 3: Run the focused tests and verify RED**

Run:

```bash
python3 -B -m unittest \
  plugins/job-search-coach/tests/test_private_schema_conformance.py \
  tests.test_private_recruiter_reply_triage \
  tests.test_render_private_recruiter_reply_triage \
  tests.test_recruiter_practice_session -q
```

Expected: failures attributable only to the new canonical `screen_opening` schema/validator expectations; the `screen_invite` integration subcase reports that triage rejected the canonical scope. This proves the existing alias blocks direct assignment.

- [ ] **Step 4: Implement the minimal canonical contract**

In both schema packet definitions, replace only the first enum member:

```json
"prep_scope": {
  "enum": [
    "screen_opening",
    "proof_example",
    "eligibility_boundary",
    "compensation_boundary",
    "missing_detail"
  ]
}
```

In `validate_private_recruiter_reply_triage.py`, remove the special `scopes` translation and validate both packet fields directly:

```python
scope = packet.get("prep_scope")
if scope not in QUESTION_KINDS:
    errors.append("handoff.packet.prep_scope has invalid value")
elif question_kind != scope:
    errors.append("handoff.packet.prep_scope must match question.kind")
```

```python
reentry_scope = reentry.get("prep_scope")
if reentry_scope not in QUESTION_KINDS:
    errors.append("handoff.reentry_packet.prep_scope has invalid value")
elif question_kind != reentry_scope:
    errors.append("handoff.reentry_packet.prep_scope must match question.kind")
```

In the renderer lookup, change only the validated key:

```python
PREP_SCOPE_LABEL_KEYS = {
    "screen_opening": "question_type_screen_opening",
    "proof_example": "question_type_proof_example",
    "eligibility_boundary": "question_type_eligibility_boundary",
    "compensation_boundary": "question_type_compensation_boundary",
    "missing_detail": "question_type_missing_detail",
}
```

Change both `ready-es.json` packet values to `"screen_opening"`. Change each test-only scope map to the same identity mapping. Do not alter HTML, CSS, localized strings, IDs, ordering, or delivery flags.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run:

```bash
python3 -B -m unittest \
  plugins/job-search-coach/tests/test_private_schema_conformance.py \
  tests.test_private_recruiter_reply_triage \
  tests.test_render_private_recruiter_reply_triage \
  tests.test_recruiter_practice_session -q
python3 -B -m json.tool plugins/job-search-coach/schemas/private-recruiter-reply-triage-v1.schema.json >/dev/null
git diff --check
```

Expected: all focused tests pass, JSON parses, and diff check is clean.

- [ ] **Step 6: Review the complete functional diff**

Run:

```bash
git diff -- \
  plugins/job-search-coach/schemas/private-recruiter-reply-triage-v1.schema.json \
  plugins/job-search-coach/scripts/validate_private_recruiter_reply_triage.py \
  plugins/job-search-coach/scripts/render_private_recruiter_reply_triage.py \
  tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json \
  tests/test_private_recruiter_reply_triage.py \
  tests/test_render_private_recruiter_reply_triage.py \
  tests/test_recruiter_practice_session.py \
  plugins/job-search-coach/tests/test_private_schema_conformance.py
```

Expected: only the canonical literal, direct validation, fixture, and focused test changes appear; no candidate-facing copy, HTML structure, CSS, authorization, or persistence changes.

- [ ] **Step 7: Commit the functional increment**

```bash
git add \
  plugins/job-search-coach/schemas/private-recruiter-reply-triage-v1.schema.json \
  plugins/job-search-coach/scripts/validate_private_recruiter_reply_triage.py \
  plugins/job-search-coach/scripts/render_private_recruiter_reply_triage.py \
  tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json \
  tests/test_private_recruiter_reply_triage.py \
  tests/test_render_private_recruiter_reply_triage.py \
  tests/test_recruiter_practice_session.py \
  plugins/job-search-coach/tests/test_private_schema_conformance.py
git commit -m "fix: canonicalize recruiter screen prep scope"
```

### Task 2: Verify, publish, install, and prove identity

**Files:**
- Modify: `plugins/job-search-coach/.codex-plugin/plugin.json`
- Modify: `tests/evals/final/cycle-1.md`
- Modify: `tests/evals/final/cycle-1/*.json`
- Modify: `tests/evals/final/cycle-2.md`
- Modify: `tests/evals/final/cycle-2/*.json`

**Interfaces:**
- Consumes: committed functional HEAD and `plugins/job-search-coach` tree.
- Produces: one cache-busted plugin version installed from `job-search-coach-local`, with final fixtures bound to the functional commit/tree and exact installed-source identity.

- [ ] **Step 1: Run full verification before changing publication metadata**

Run:

```bash
python3 -B -m unittest tests.test_private_recruiter_reply_triage -q
python3 -B -m unittest tests.test_render_private_recruiter_reply_triage -q
python3 -B -m unittest tests.test_recruiter_practice_session -q
python3 -B -m unittest discover -s plugins/job-search-coach/tests -p 'test*.py' -q
git diff --check
```

Expected: all functional and plugin-local suites pass with zero failures. Do
not run `test_full_plugin` or the static gate yet: after the functional commit,
the deterministic final fixtures are intentionally stale until Step 2 binds
them to that commit.

- [ ] **Step 2: Bind final fixtures to the functional commit and tree**

Run:

```bash
task_head=$(git rev-parse HEAD)
task_tree=$(git rev-parse HEAD:plugins/job-search-coach)
find tests/evals/final/cycle-1 tests/evals/final/cycle-2 -name '*.json' -print0 \
  | xargs -0 perl -pi -e 's/"source_commit": "[^"]+"/"source_commit": "'"$task_head"'"/; s/"source_tree": "[^"]+"/"source_tree": "'"$task_tree"'"/'
perl -pi -e 's/^source_commit=.*/source_commit='"$task_head"'/; s/^source_tree=.*/source_tree='"$task_tree"'/' \
  tests/evals/final/cycle-1.md tests/evals/final/cycle-2.md
python3 -B plugins/job-search-coach/tests/run_static_checks.py
python3 -B -m unittest tests.test_full_plugin -q
git diff --check
```

Expected: only final cycle provenance changes; static/schema checks and the
full-plugin integration suite pass before cachebusting.

- [ ] **Step 3: Run the cachebuster exactly once**

Run once:

```bash
python3 -B $HOME/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py plugins/job-search-coach
```

Expected: one new `0.2.0+codex.<timestamp>` version in `plugin.json`. Do not rerun this command in the increment.

- [ ] **Step 4: Re-run static checks and commit publication metadata**

```bash
python3 -B plugins/job-search-coach/tests/run_static_checks.py
git diff --check
git add \
  plugins/job-search-coach/.codex-plugin/plugin.json \
  tests/evals/final/cycle-1.md tests/evals/final/cycle-1 \
  tests/evals/final/cycle-2.md tests/evals/final/cycle-2
git commit -m "chore: publish canonical recruiter screen scope"
```

- [ ] **Step 5: Install the published plugin**

Run:

```bash
codex plugin add job-search-coach@job-search-coach-local --json
```

Expected: JSON reports the same version stored in `plugins/job-search-coach/.codex-plugin/plugin.json` and a versioned installed path.

- [ ] **Step 6: Verify published HEAD, installed identity, and clean worktree**

Run:

```bash
python3 -B -m unittest tests.test_private_recruiter_reply_triage -q
python3 -B -m unittest tests.test_render_private_recruiter_reply_triage -q
python3 -B -m unittest tests.test_recruiter_practice_session -q
python3 -B -m unittest tests.test_full_plugin -q
python3 -B -m unittest discover -s plugins/job-search-coach/tests -p 'test*.py' -q
python3 -B plugins/job-search-coach/tests/run_static_checks.py
installed_version=$(python3 -B -c 'import json, pathlib; print(json.loads(pathlib.Path("plugins/job-search-coach/.codex-plugin/plugin.json").read_text())["version"])')
diff -qr plugins/job-search-coach "$HOME/.codex/plugins/cache/job-search-coach-local/job-search-coach/$installed_version"
git diff --check
git status --porcelain=v1
```

Expected: every test and static gate passes; `diff -qr`, `git diff --check`, and `git status --porcelain=v1` produce no output.
