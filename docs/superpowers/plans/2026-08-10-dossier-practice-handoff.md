# Dossier-to-Practice Handoff v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a closed, privacy-safe bridge that binds a recruiter-practice session to a validated dossier question/evidence projection and an independent identity-free vacancy summary.

**Architecture:** A pure builder creates a sidecar from a validated dossier, safe vacancy summary, and synthetic dossier snapshot. A custom parity validator checks the sidecar and target practice session against both source objects; the existing v1 schemas and renderers remain compatible and unchanged.

**Tech Stack:** Python 3 standard library, Draft 2020-12 JSON Schema, repository dependency-free schema checker, `unittest`, existing static/privacy gates.

## Global Constraints

- Keep existing dossier-v1 and recruiter-practice-session-v1 schemas unchanged; the bridge is additive.
- Accept only dossier `screen_bridge.state=requires_confirmation`, `question_rank=1`, and linked question category `screen_bridge`.
- Use only synthetic `snap-dossier-###` values; never store URLs, names, contact details, raw profile/reply text, browser/session identifiers, or hashes.
- Preserve source fact state exactly; only `verified` and `candidate_reported` are allowed for the bridge.
- Preserve `draft_only=true`, `external_actions_authorized=false`, manual re-entry, no auto-start, and ephemeral unanswered state.
- Keep renderer output unchanged and hide all Q/R/F/C/E IDs, snapshots, source enums, and raw source text.
- Do not add third-party dependencies or remote resources.

---

### Task 1: Closed bridge schema and pure source projection

**Files:**
- Create: `plugins/job-search-coach/schemas/dossier-recruiter-practice-handoff-v1.schema.json`
- Create: `plugins/job-search-coach/scripts/build_dossier_recruiter_practice_handoff.py`
- Create: `plugins/job-search-coach/tests/fixtures/dossier-recruiter-practice-handoff/valid-es.json`
- Create: `plugins/job-search-coach/tests/test_dossier_recruiter_practice_handoff.py`

**Interfaces:**
- Produces `build_handoff(dossier: Mapping[str, object], vacancy: Mapping[str, object], source_snapshot: str) -> dict[str, object]`.
- The returned sidecar contains `schema_version`, `source`, `source_snapshot`, `dossier_projection`, `practice_projection`, and `delivery`.
- `dossier_projection` contains `question_rank`, `claim_ids`, `evidence_ids`, `question_evidence_ids`, `source_fact_evidence_id`, `fact_state`, and `fact_summary`.
- `practice_projection` contains the identity-free `safe_context`, `requirement`, `question`, `facts`, and exact `handoff_context`.

- [ ] **Step 1: Add the RED fixture and schema mutation tests**

Create a fixture with a validated `requires_confirmation` rank-1 bridge, a
linked `screen_bridge` question, known C/E records, a safe vacancy summary, and
the expected projection. Add tests that first call the not-yet-defined builder
and assert the positive shape plus rejection of a missing rank, unknown C/E,
unknown source evidence, malformed snapshot, raw URL, and external-action flag.

- [ ] **Step 2: Run the focused tests and verify RED**

```bash
python3 -B -m unittest plugins/job-search-coach/tests/test_dossier_recruiter_practice_handoff.py -v
```

Expected: import/implementation failures for the new builder and schema
conformance tests, with no changes to the existing plugin tests.

- [ ] **Step 3: Implement the closed schema and builder**

Implement the standard-library builder. It must call the existing dossier
validator first, select rank 1 exactly, resolve C/E and the selected question's
evidence, preserve the source evidence state/summary, copy only the supplied
identity-free vacancy fields, generate target projection IDs `Q-001`, `R-001`,
and `F-001`, and set manual/draft delivery constants. Keep all input mappings
closed and raise deterministic `ValueError` messages on invalid source data.

- [ ] **Step 4: Run focused tests and schema conformance**

Run the focused module and:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest plugins/job-search-coach/tests/test_private_schema_conformance.py -q
```

Expected: all new builder tests and existing conformance tests pass.

- [ ] **Step 5: Commit the self-contained source projection**

```bash
git add plugins/job-search-coach/schemas/dossier-recruiter-practice-handoff-v1.schema.json plugins/job-search-coach/scripts/build_dossier_recruiter_practice_handoff.py plugins/job-search-coach/tests/fixtures/dossier-recruiter-practice-handoff/valid-es.json plugins/job-search-coach/tests/test_dossier_recruiter_practice_handoff.py
git commit -m "feat: add dossier practice handoff projection"
```

### Task 2: Parity validator and practice-session integration

**Files:**
- Create: `plugins/job-search-coach/scripts/validate_dossier_recruiter_practice_handoff.py`
- Modify: `plugins/job-search-coach/tests/test_dossier_recruiter_practice_handoff.py`
- Modify: `plugins/job-search-coach/tests/test_recruiter_practice_session.py`
- Modify: `plugins/job-search-coach/skills/prepare-role-interviews/SKILL.md`
- Modify: `plugins/job-search-coach/skills/prepare-role-interviews/references/interview-map.md`

**Interfaces:**
- Produces `validate_handoff(handoff: Mapping[str, object], dossier: Mapping[str, object], vacancy: Mapping[str, object], practice_session: Mapping[str, object]) -> list[str]`.
- Returns deterministic field-scoped errors and never renders or logs raw input values.
- The existing `validate_recruiter_practice_session.validate_session` remains the first layer; parity validation is the second source-binding layer.

- [ ] **Step 1: Add RED parity and mutation tests**

Load the positive sidecar, dossier, vacancy summary, and matching practice
session. Assert zero errors for the valid set. Add mutations for source
snapshot, rank, question kind/text, requirement, Q/R/F, bridge C/E, source
fact state/summary, prefilled answer, score, auto-start, URL, and missing
source side. Each mutation must produce a deterministic field-specific error.

- [ ] **Step 2: Run the parity tests and verify RED**

```bash
python3 -B -m unittest plugins/job-search-coach/tests/test_dossier_recruiter_practice_handoff.py tests/test_recruiter_practice_session.py -q
```

Expected: the new parity import/calls fail before implementation while the
existing direct triage-to-practice tests remain green.

- [ ] **Step 3: Implement the parity validator**

Validate the sidecar schema, then the dossier and practice validators, then
compare exact projections. Check C/E membership and claim-to-evidence links in
the dossier, selected question/category/rank, source evidence state, target
projection equality, and all no-action/ephemeral constants. Use bounded errors
without embedding raw summaries, URLs, or private text.

- [ ] **Step 4: Document the two-source handoff contract**

Update the interview-preparation skill to state that a dossier supplies
candidate evidence/context while a separate identity-free vacancy summary
supplies the requirement; no dossier-to-practice handoff may invent a vacancy
requirement or automatically start a session.

- [ ] **Step 5: Run focused integration tests and commit**

```bash
python3 -B -m unittest plugins/job-search-coach/tests/test_dossier_recruiter_practice_handoff.py tests/test_recruiter_practice_session.py -q
git diff --check
git add plugins/job-search-coach/scripts/validate_dossier_recruiter_practice_handoff.py plugins/job-search-coach/tests/test_dossier_recruiter_practice_handoff.py plugins/job-search-coach/tests/test_recruiter_practice_session.py plugins/job-search-coach/skills/prepare-role-interviews/SKILL.md plugins/job-search-coach/skills/prepare-role-interviews/references/interview-map.md
git commit -m "test: bind dossier provenance to practice sessions"
```

### Task 3: Release-gate integration and privacy proof

**Files:**
- Modify: `plugins/job-search-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`
- Modify: `plugins/job-search-coach/tests/test_private_schema_conformance.py`
- Modify: `plugins/job-search-coach/tests/test_render_recruiter_practice_session.py`

**Interfaces:**
- Static checks execute the bridge schema/parity harness and emit a bounded
  `dossier practice handoff conformance passed` marker.
- Full-plugin tests assert the marker and rejection of a source-drift mutation.

- [ ] **Step 1: Add RED gate and privacy assertions**

Add a static harness invocation with a bounded timeout, tests for malformed or
zero-test summaries, and renderer assertions that sourced sessions still omit
all source IDs/snapshots/raw text. Add a conformance mutation proving an
unrelated but shape-valid Q/R/F/C/E projection fails the pair validator.

- [ ] **Step 2: Implement the gate wiring**

Reuse existing bounded subprocess diagnostics and abort-before-expensive-check
behavior. Do not print source summaries or private fixture values in failures.

- [ ] **Step 3: Run the complete pre-release matrix**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/job-search-coach/tests/run_static_checks.py
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/job-search-coach/tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_plugin_structure tests.test_repository_privacy -q
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
bash scripts/run_release_validation.sh
git diff --check
```

Expected: all gates exit 0; no renderer output changes; only the new bridge
files, tests, and narrowly scoped skill/gate docs are modified.

- [ ] **Step 4: Commit gate integration and prepare Task 4 review**

```bash
git add plugins/job-search-coach/tests/run_static_checks.py tests/test_full_plugin.py plugins/job-search-coach/tests/test_private_schema_conformance.py plugins/job-search-coach/tests/test_render_recruiter_practice_session.py
git commit -m "test: gate dossier practice provenance"
```

Task 4 will independently review the contract, privacy, and release impact;
only after review will the release-only Task 5 refresh provenance, run the full
matrix, invoke the cachebuster exactly once, publish, install, and prove source
/cache identity.

