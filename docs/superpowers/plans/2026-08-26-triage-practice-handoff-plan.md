# Private triage-to-practice handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compose a verified, identity-free triage v2 handoff into an unanswered recruiter-practice-session-v2 artifact without adding external actions or persistence.

**Architecture:** Add one closed wrapper schema and one fail-closed builder. The builder validates a ready triage, recomputes its content snapshot, creates a fixed-copy practice requirement, and validates the nested session with the existing practice validator. The existing practice renderer receives a triage-specific static route cue; no existing triage or practice schema is widened.

**Tech Stack:** Python 3, JSON Schema subset validator already used by the plugin, `unittest`, static HTML/CSS assets, Superdesign theme raw-CSS parity checks.

**Spec:** `docs/superpowers/specs/2026-08-26-triage-practice-handoff-design.md`

## Global Constraints

- Source input is `private-recruiter-reply-triage-v2` and must be `state=ready_for_private_prep` with `handoff_allowed=true` and one `verified` fact.
- Recompute `snap-triage-sha256-` provenance and require it to match both triage handoff packet snapshots and all fact/question/scope references.
- Output is `recruiter-practice-session-v2`, `state=ready_to_practice`, `observed_answer=null`, `score=unknown`, `score_state=unknown`, and `draft_only=true`.
- The output contains no raw reply, names, contacts, URLs, internal source IDs, proposed times, answer text, network calls, forms, uploads, messages, scheduling, ranking, fit claims, or outcome promises.
- `clarify_first` and `stop` triage states are rejected; manual re-entry remains required and auto-start remains false.
- Every increment ends with focused tests, full plugin/static/privacy/release validation, plugin installation, source/cache parity, and the authorized `git push origin HEAD:main`.

### Task 1: Lock the composition contract with failing tests

**Files:**
- Create: `plugins/professional-growth-coach/tests/test_private_recruiter_triage_practice_handoff.py`
- Read: `tests/test_private_recruiter_reply_triage.py` helper patterns for constructing v2 triage mappings
- Read: `plugins/professional-growth-coach/scripts/triage_snapshot.py` and existing practice validator imports

**Interfaces:**
- The test will import `build_private_recruiter_triage_practice_handoff.build_handoff` and `CompositionError` once Task 2 supplies them.
- The test fixture helper returns a valid v2 mapping with `handoff.packet` and `handoff.reentry_packet` snapshots recalculated through `snapshot_for_triage`.

- [ ] **Step 1: Write the failing tests**

  Add a valid ES and EN case that calls `build_handoff(triage)` and asserts:
  `schema_version == "private-recruiter-triage-practice-handoff-v1"`, nested
  session `schema_version == "recruiter-practice-session-v2"`,
  `state == "ready_to_practice"`, `handoff_context.source_snapshot` equals the
  recomputed triage snapshot, and `validate_session(result["practice_session"])`
  returns `[]`. Add cases asserting `CompositionError` for `clarify_first`,
  `stop`, a changed packet snapshot, a changed fact ID, a changed question ID,
  and `candidate_reported` evidence. Add a redaction assertion that the nested
  session contains none of the source IDs or a sentinel raw reply string.

- [ ] **Step 2: Run the focused tests and confirm the expected RED**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins.professional-growth-coach.tests.test_private_recruiter_triage_practice_handoff -q
  ```

  Expected: import failure because `build_private_recruiter_triage_practice_handoff.py`
  does not yet exist. No production implementation is written before this
  failure is observed.

- [ ] **Step 3: Commit the test contract**

  ```bash
  git add plugins/professional-growth-coach/tests/test_private_recruiter_triage_practice_handoff.py
  git commit -m "test: define triage practice composition contract"
  ```

### Task 2: Implement the closed handoff schema and builder

**Files:**
- Create: `plugins/professional-growth-coach/schemas/private-recruiter-triage-practice-handoff-v1.schema.json`
- Create: `plugins/professional-growth-coach/scripts/build_private_recruiter_triage_practice_handoff.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_recruiter_triage_practice_handoff.py`

**Interfaces:**
- `build_handoff(triage: Mapping[str, object]) -> dict[str, object]` returns the closed wrapper described in the spec.
- `CompositionError(ValueError)` carries deterministic bounded errors and never returns a partial session.
- The builder imports `validate_private_recruiter_reply_triage.validate_triage`, `triage_snapshot.snapshot_for_triage`, `validate_recruiter_practice_session.validate_session`, and `validate_json_schema_subset.validate_schema_instance` through the existing sibling-loading pattern.

- [ ] **Step 1: Define the closed JSON schema**

  Require `schema_version`, `source_artifact_kind`, `source_snapshot`,
  `prep_scope`, `practice_session`, and `delivery`. Close every object with
  `additionalProperties: false`; constrain the snapshot to
  `^snap-triage-sha256-[0-9a-f]{64}$`, the source kind to
  `private_recruiter_reply_triage`, the scope to the five existing practice
  question kinds, and delivery to `draft_only=true`,
  `external_actions_authorized=false`, `manual_reentry_required=true`,
  `auto_start=false`, `local_save_mode=disabled`, and
  `raw_reply_retained=false`.

- [ ] **Step 2: Implement the minimal fail-closed projection**

  Validate the triage and require the ready state, verified fact, exact packet
  and re-entry values, and snapshot equality. Build a v2 session with fixed
  bilingual requirement/rubric copy keyed by `prep_scope`; copy only validated
  safe context, question text, and fact summary; set all pre-answer delivery and
  feedback invariants; bind `handoff_context` to the exact triage snapshot; and
  validate both the wrapper schema and nested practice session before return.

- [ ] **Step 3: Run the focused tests and confirm GREEN**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins.professional-growth-coach.tests.test_private_recruiter_triage_practice_handoff -q
  ```

  Expected: all valid ES/EN cases pass and every tamper/state/privacy case is
  rejected deterministically.

- [ ] **Step 4: Commit the builder and schema**

  ```bash
  git add plugins/professional-growth-coach/schemas/private-recruiter-triage-practice-handoff-v1.schema.json plugins/professional-growth-coach/scripts/build_private_recruiter_triage_practice_handoff.py plugins/professional-growth-coach/tests/test_private_recruiter_triage_practice_handoff.py
  git commit -m "feat: compose triage into private practice"
  ```

### Task 3: Add the renderer route cue and visual parity

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/render_recruiter_practice_session.py`
- Modify: `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css`
- Modify: `plugins/professional-growth-coach/tests/test_render_recruiter_practice_session.py`
- Modify: `.superdesign/init/theme.md`

**Interfaces:**
- When `handoff_context.source == "private_recruiter_reply_triage"`, the renderer emits one static `.triage-practice-route` section with textual stages `validated triage`, `private rehearsal`, and `private review`.
- Other sources retain their existing handoff copy and markup.

- [ ] **Step 1: Add the failing renderer assertions**

  Build a valid triage-composed session through the Task 2 builder and assert
  exactly one route section, all three localized stage labels, no internal IDs,
  no `href` beyond the existing skip link, no form/button/script tags, and
  responsive/print/forced-color selectors in the inline CSS.

- [ ] **Step 2: Run the renderer test to confirm RED**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins.professional-growth-coach.tests.test_render_recruiter_practice_session -q
  ```

  Expected: the new route assertion fails because no triage-specific route is
  emitted.

- [ ] **Step 3: Implement the static route and co-located CSS**

  Add constant bilingual copy selected only by the validated source enum; place
  the route cue before the existing practice sequence; style it with current
  family tokens, one-column layout at 640px, print break protection, reduced
  motion, forced colors, and high contrast. Preserve old exact selector groups
  when adding new rules so existing contract tests remain valid.

- [ ] **Step 4: Run focused renderer and parity checks**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins.professional-growth-coach.tests.test_render_recruiter_practice_session -q
  python3 -B - <<'PY'
  from pathlib import Path
  theme = Path('.superdesign/init/theme.md').read_text()
  marker = '### `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css`'
  body = theme[theme.index(marker):]
  start = body.index('```css\n') + len('```css\n')
  end = body.index('\n```', start)
  actual = Path('plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css').read_text().rstrip()
  assert body[start:end].rstrip() == actual
  print('superdesign raw CSS parity: OK')
  PY
  ```

- [ ] **Step 5: Commit the route and visual updates**

  ```bash
  git add plugins/professional-growth-coach/scripts/render_recruiter_practice_session.py plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css plugins/professional-growth-coach/tests/test_render_recruiter_practice_session.py .superdesign/init/theme.md
  git commit -m "feat: show triage practice route"
  ```

### Task 4: Document the contract and run release gates

**Files:**
- Modify: `plugins/professional-growth-coach/README.md`
- Modify: `plugins/professional-growth-coach/skills/prepare-role-interviews/references/interview-map.md`
- Modify: `plugins/professional-growth-coach/skills/prepare-role-interviews/SKILL.md` only if its focused-loading limit remains below 16,000 bytes

- [ ] **Step 1: Document manual re-entry and provenance**

  State that triage composition accepts only ready/verified inputs, recalculates
  the snapshot, emits unanswered practice, and never copies raw reply material
  or performs external action. Keep the focused skill file under 16,000 bytes;
  put detailed contract prose in README/reference when needed.

- [ ] **Step 2: Run all plugin checks**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/professional-growth-coach/tests -p 'test_*.py' -q
  PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
  PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py --repo-root .
  scripts/run_release_validation.sh
  git diff --check
  ```

  Expected: plugin tests, private schema conformance, dossier handoff
  conformance, static checks, privacy checks, release validation, and diff
  checks all exit zero.

- [ ] **Step 3: Commit documentation**

  ```bash
  git add plugins/professional-growth-coach/README.md plugins/professional-growth-coach/skills/prepare-role-interviews/references/interview-map.md
  git commit -m "docs: document triage practice provenance"
  ```

### Task 5: Review, install, attest, and publish

**Files:**
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json`
- Modify: `tests/evals/final/cycle-1/*.json`, `tests/evals/final/cycle-2/*.json`, `tests/evals/final/cycle-1.md`, `tests/evals/final/cycle-2.md`, `tests/evals/final/installed-smoke-test.md`

- [ ] **Step 1: Request two fresh reviews**

  Give one reviewer the complete diff and ask for functional/UX contract risks;
  give another the same diff and ask for privacy, input-echo, CSP, and release
  provenance risks. Resolve every Critical/Important finding before merging.

- [ ] **Step 2: Bump and install the exact plugin version**

  Set `plugin.json` to a new UTC cachebuster, commit it, then run:

  ```bash
  codex plugin add professional-growth-coach@professional-growth-coach-local --json
  ```

  Record the installed version/path locally without exposing credentials.

- [ ] **Step 3: Verify source/cache parity and installed smoke**

  Require `diff -qr --exclude='__pycache__'` silence, equal file counts,
  equal normalized path/SHA hash, and direct installed ES/EN validator/renderer
  smoke for the triage-composed fixture. Keep `fresh_agent_smoke=not_run` unless
  an actual fresh agent session is executed; do not claim that evidence from a
  direct CLI smoke is a fresh-agent run.

- [ ] **Step 4: Refresh final provenance and run the full repository suite**

  Bind all final fixtures to the commit immediately before the attestation
  commit. Set `source_tree` with `git rev-parse "$SOURCE_COMMIT:plugins/professional-growth-coach"`
  after assigning `SOURCE_COMMIT` to that immediate parent,
  update installed version/hash/counts, commit the attestation, then run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_*.py' -q
  ```

  Expected: `Ran ... tests ... OK`; known private harness timeout warnings may
  appear but a nonzero exit is a release blocker.

- [ ] **Step 5: Push and verify parity**

  ```bash
  git fetch origin
  git push origin HEAD:main
  git fetch origin
  git status --short --branch
  git rev-parse HEAD
  git rev-parse origin/main
  git diff --check
  ```

  Proceed only when local and remote hashes are identical and the worktree is
  clean. Report the final commit, installed plugin version, tests, reviews,
  parity, and bounded visual-QA scope.
