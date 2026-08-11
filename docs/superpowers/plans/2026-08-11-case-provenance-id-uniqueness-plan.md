# Case Provenance ID Uniqueness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject duplicate provenance IDs within each case collection while preserving all existing validation and privacy behavior.

**Architecture:** Add a per-collection `seen_ids` set inside the existing `_validate_records` loop. The validator emits a generic path-specific uniqueness error after the existing required/non-empty-string check. Update the case contract and add a table-driven regression matrix; no schema or cross-collection namespace changes.

**Tech Stack:** Python 3, `unittest`, Markdown contract/specs, existing plugin validation scripts.

## Global Constraints

- IDs must be non-empty strings before uniqueness is checked.
- Uniqueness applies only within `sources`, `claims`, `interventions`, or `outcomes` respectively.
- Error messages must not echo supplied ID values.
- Candidate binding, benchmark consent, privacy scanning, and closed mappings remain unchanged.
- Do not install or publish until source/cache/provenance gates are rerun after the functional commit.

---

### Task 1: Add the failing uniqueness matrix

**Files:**
- Modify: `tests/test_validate_case.py` near the existing provenance presence/type tests.

**Interfaces:**
- Consumes: `valid_case()` and `run_validator()` helpers already used by the validator tests.
- Produces: one table-driven test covering the four collection/id-field pairs.

- [ ] **Step 1: Write the failing test**

Create a test that duplicates the first valid record in each collection, keeps the duplicate ID, changes an allowed field so both records are otherwise valid, runs the real validator, and asserts:

```python
def test_rejects_duplicate_provenance_ids_without_echoing_values(self) -> None:
    cases = (
        ("sources", "source_id", "kind", "article"),
        ("claims", "claim_id", "text", "A second claim"),
        ("interventions", "intervention_id", "description", "A second intervention"),
        ("outcomes", "outcome_id", "value", "A second outcome"),
    )
    for field, id_field, changed_field, changed_value in cases:
        with self.subTest(field=field):
            case = valid_case()
            duplicate = dict(case[field][0])
            duplicate[changed_field] = changed_value
            case[field] = [case[field][0], duplicate]
            result = run_validator(case)
            self.assertEqual(result.returncode, 2)
            self.assertIn(f"{field}[1].{id_field} must be unique", result.stderr)
            self.assertNotIn(str(case[field][0][id_field]), result.stderr)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python3 -B -m unittest tests.test_validate_case.ValidateCaseTests.test_rejects_duplicate_provenance_ids_without_echoing_values -v
```

Expected: four subtests fail because the current validator returns success for duplicate IDs.

### Task 2: Implement uniqueness and update the contract

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_case.py:285-325`.
- Modify: `plugins/professional-growth-coach/skills/professional-growth-coach/references/case-contract.md` record requirements.

**Interfaces:**
- Consumes: the existing `_validate_records(field, records, candidate_id, benchmark_consent)` function.
- Produces: the same list-of-error-strings API with one new bounded error for duplicate IDs.

- [ ] **Step 1: Add minimal production logic**

Initialize `seen_ids: set[str] = set()` once per `_validate_records` call. After the existing non-empty-string branch succeeds, append:

```python
record_id = record[provenance_field]
if record_id in seen_ids:
    errors.append(f"{location}.{provenance_field} must be unique")
else:
    seen_ids.add(record_id)
```

Do not add invalid values to `seen_ids`.

- [ ] **Step 2: Clarify the contract**

Update the case contract sentence to state that each collection's provenance ID is stable, non-empty, and unique within that collection; retain the existing rule that every record carries the case `candidate_id`.

- [ ] **Step 3: Run the focused test and verify GREEN**

Run the same focused unittest command from Task 1 and expect all four subtests to pass with no ID value in stderr.

### Task 3: Run regression gates

**Files:**
- No additional production files.

- [ ] **Step 1: Run validator and plugin suites**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_validate_case -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/professional-growth-coach/tests -p 'test*.py' -q
```

Expected: zero failures and zero errors.

- [ ] **Step 2: Run static/privacy/release checks**

```bash
python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
python3 -B scripts/check_repository_privacy.py
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_release_validation.sh
git diff --check
```

Expected: schema, handoff, static, privacy, skill, plugin, and diff checks all pass.

### Task 4: Publish and verify the increment

**Files:**
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json` via the repository's cachebuster/release workflow.
- Modify: final-cycle provenance/installed-smoke metadata only as required by the release workflow.

- [ ] **Step 1: Commit the functional change**

Commit validator, test, contract, spec, and plan after the fresh gates pass.

- [ ] **Step 2: Bump once and install the canonical plugin**

Run the existing cachebuster exactly once, commit the manifest/provenance release metadata, and install `professional-growth-coach@professional-growth-coach-local`.

- [ ] **Step 3: Verify installed parity and smoke**

Confirm one canonical enabled plugin, exact source/cache manifest version, byte-identical source/cache inventory/hash, and installed validator rejection of a duplicate-ID case without echoing the ID.

- [ ] **Step 4: Attest and rerun final gates**

Update installed-smoke metadata with the new release source/tree/hash, bind cycle sidecars to the immediate parent release commit, then rerun plugin/root suites, provenance, static/privacy/release validators, and `git status --short`.
