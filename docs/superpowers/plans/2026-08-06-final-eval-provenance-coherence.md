# Superseded Final Eval Provenance Plan

Status: superseded by the completed live-agent evaluation capture in commits `bbede66` and `806403e`. The deterministic-fixture conversion proposed below was not adopted because twelve fresh `fork_turns=none` agent outputs, canonical task paths, prompts, transcripts, and hashes were preserved. It remains here only as historical design context; do not execute it against the current live artifacts.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make final evaluation provenance internally coherent so the plugin cannot pass with stale live-agent sidecars that contradict deterministic fixture indexes.

**Architecture:** Keep final evaluation records as deterministic regression fixtures with external Markdown transcripts and JSON sidecars. Strengthen the validator so every final artifact agrees with its cycle index, points to the documented pre-fixture source commit/tree, rejects stale `live-agent-transcript` artifacts unless they are fresh and explicitly allowed, and fails when index prose contradicts sidecar metadata.

**Tech Stack:** Markdown/JSON fixtures, stdlib Python static checker, stdlib Python `unittest`, no new dependencies.

## Global Constraints

- No LinkedIn edit, message, connection request, post, upload, application, or external share may be executed without exact action-and-target authorization immediately before execution.
- Every material recommendation, draft, and claim must keep one of the canonical evidence prefixes: `verified:`, `candidate-reported:`, `inferred:`, or `unknown:`.
- Do not promise response rates, interviews, salaries, time-to-hire, recruiter ranking, search ranking, or causal uplift.
- Do not infer market demand from static keyword lists; dated current vacancies are required for market/current-demand claims.
- Preserve candidate isolation and confidentiality review requirements for internal/employer/customer material.
- Do not claim final evaluation fixtures are live agent transcripts unless the recorded source commit is the current evaluated source and the transcript is explicitly captured from that live run.

---

### Task 1: Coherent deterministic final-eval provenance

**Files:**
- Modify: `plugins/job-search-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`
- Modify: `tests/evals/final/cycle-1.md`
- Modify: `tests/evals/final/cycle-2.md`
- Modify: all `tests/evals/final/cycle-1/*.json`
- Modify: all `tests/evals/final/cycle-2/*.json`

**Interfaces:**
- Consumes: existing final eval sidecar fields `artifact_kind`, `source_commit`, `source_tree`, `provenance_note`, `prompt`, `prompt_sha256`, `transcript_file`, `transcript_sha256`, and `scores`.
- Produces: validator behavior that enforces deterministic sidecar/index agreement and rejects stale live-agent provenance.

- [ ] **Step 1: Write failing tests**

Add assertions to `FullPluginIntegrationTests.test_cross_cycle_validator_rejects_copies_prompt_drift_and_stale_provenance`:

```python
for cycle in (1, 2):
    cycle_index = (REPO_ROOT / "tests" / "evals" / "final" / f"cycle-{cycle}.md").read_text(
        encoding="utf-8"
    )
    self.assertIn("artifact_kind=deterministic-regression-fixture", cycle_index)
    self.assertNotIn("artifact_kind=live-agent-transcript", cycle_index)
    for artifact_path in sorted((REPO_ROOT / "tests" / "evals" / "final" / f"cycle-{cycle}").glob("*.json")):
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        self.assertEqual("deterministic-regression-fixture", artifact["artifact_kind"])
        self.assertIn("not a live agent transcript", artifact["provenance_note"].lower())
        self.assertIn(artifact["source_commit"], cycle_index)

live_stale = dict(first)
live_stale["artifact_kind"] = "live-agent-transcript"
live_stale["provenance_note"] = "Fresh read-only agent final answer; canonical task recorded in agent_id."
live_stale["source_commit"] = "a8611cd7a3636b697c4c9c81ac7e0c1a7d81f1f9"
live_stale["source_tree"] = "f6fbf246311f411354ec2e56ea55c11128c92b2f"
live_errors = validate_provenance(live_stale, REPO_ROOT)
self.assertTrue(any("live transcript" in error and "stale" in error for error in live_errors))
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python3 -B -m unittest tests.test_full_plugin.FullPluginIntegrationTests.test_cross_cycle_validator_rejects_copies_prompt_drift_and_stale_provenance -v
```

Expected: fail because current sidecars still declare `artifact_kind=live-agent-transcript` sourced from `a8611cd`.

- [ ] **Step 3: Implement coherent deterministic metadata**

Update all final JSON sidecars so:

- `artifact_kind` is exactly `deterministic-regression-fixture`.
- `provenance_note` contains `not a live agent transcript`.
- `source_commit` is the same documented pre-fixture source commit named in both cycle indexes.
- `source_tree` is the Git tree for `plugins/job-search-coach` at that source commit.
- `run_id` and `agent_id` are fixture/curator IDs, not canonical live-agent task paths.
- Prompts remain byte-identical between cycle 1 and cycle 2 for the same `case_id`.
- Transcripts remain materially different across cycles and retain canonical evidence prefixes.

Update `validate_eval_provenance` so:

- deterministic fixtures must point to `HEAD` or an ancestor close enough to be the documented pre-fixture source, and their `provenance_note` must state they are not live transcripts.
- live-agent transcripts must be fresh: their source commit must be the current evaluated plugin source or its immediate parent, and stale `a8611cd` live sidecars fail.
- cycle index prose and sidecar `artifact_kind`/`source_commit` must agree.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
python3 -B -m unittest tests.test_full_plugin.FullPluginIntegrationTests.test_cross_cycle_validator_rejects_copies_prompt_drift_and_stale_provenance -v
python3 plugins/job-search-coach/tests/run_static_checks.py
```

Expected: both pass.

- [ ] **Step 5: Full validation and commit**

Run:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
git status --short --branch
```

Expected: all tests pass and only intended files are modified.

Commit:

```bash
git add plugins/job-search-coach/tests/run_static_checks.py tests/test_full_plugin.py tests/evals/final/cycle-1.md tests/evals/final/cycle-2.md tests/evals/final/cycle-1/*.json tests/evals/final/cycle-2/*.json
git commit -m "fix: align final eval provenance"
```

## Plan Self-Review

- Spec coverage: the single task addresses stale live sidecars, deterministic fixture/index contradiction, validator gaps, and current-source provenance rules.
- Placeholder scan: no TODO/TBD placeholders.
- Scope check: this cycle intentionally does not regenerate new live LLM evaluations; it makes deterministic fixture claims honest and machine-checked. A later cycle may add true live-agent eval capture if needed.
