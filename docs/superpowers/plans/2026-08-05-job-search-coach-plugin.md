# Job Search Coach Plugin Implementation Plan

> Synthetic example provenance: `no_real_profile_mapping`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, validate, and locally install a Codex plugin that provides an evidence-based, LinkedIn-specialist job-search coach through one orchestrator and seven tested domain skills.

**Architecture:** The plugin lives at `plugins/job-search-coach/` and exposes eight skills through `.codex-plugin/plugin.json`. The orchestrator owns candidate isolation, consent, evidence labels, routing, and action boundaries; each domain skill owns one career workflow and loads only its focused references. Python standard-library scripts provide deterministic case validation and outcome calculations, while Markdown skill behavior is evaluated with baseline and forward-test transcripts.

**Tech Stack:** Codex plugin manifest JSON, Agent Skills Markdown/YAML, `agents/openai.yaml`, Python 3 standard library, `unittest`, JSON Schema-style contracts documented in Markdown, Git.

## Global Constraints

- Plugin name and directory are exactly `job-search-coach`.
- Source is repo-local at `plugins/job-search-coach/`; marketplace installation is a separate authorized step.
- Skills are created and deployed one at a time using RED-GREEN-REFACTOR; no skill is written before its failing baseline transcript exists.
- Every skill description starts with `Use when...`, contains triggering conditions only, and uses lowercase hyphen-case names.
- Candidate claims are labeled `observed`, `declared`, `inferred`, or `recommended`; missing evidence is never fabricated.
- Candidate records are isolated by `candidate_id`; cross-candidate benchmarking is off unless explicit consent is recorded.
- Editing LinkedIn, posting, messaging, connecting, applying, uploading, or sharing requires action-time authorization.
- Current market, salary, vacancy, course, certification, and platform claims require dated sources and confidence labels.
- The plugin must support self-service and coach mode for Mexico, the United States, and remote international searches.
- The plugin must specialize deeply in LinkedIn while supporting technical and non-technical high-compensation roles.
- No MCP server or app manifest is included in version `0.1.0`; available Codex web, Chrome, and file capabilities are used when authorized.
- The full test suite is `python3 -m unittest discover -s tests -p 'test_*.py' -v`.

---

### Task 1: Plugin scaffold and structural validation

**Files:**
- Create: `plugins/job-search-coach/.codex-plugin/plugin.json`
- Create: `plugins/job-search-coach/skills/`
- Create: `plugins/job-search-coach/scripts/`
- Create: `plugins/job-search-coach/tests/fixtures/expected-skills.json`
- Create: `tests/test_plugin_structure.py`

**Interfaces:**
- Produces: manifest `name`, `version`, `description`, `author.name`, `skills`, and required `interface` metadata.
- Produces: `EXPECTED_SKILLS: tuple[str, ...]` in the test fixture as the canonical module inventory.

- [ ] **Step 1: Write the failing structural test**

Create `tests/test_plugin_structure.py` to assert that the manifest exists, uses strict semver `0.1.0`, points `skills` to `./skills/`, omits `apps` and `mcpServers`, contains no unresolved placeholder marker, and that the canonical inventory contains exactly eight unique valid skill names.

Use this fixture in `plugins/job-search-coach/tests/fixtures/expected-skills.json`:

```json
[
  "job-search-coach",
  "optimize-linkedin-career",
  "discover-high-value-career-paths",
  "research-target-job-market",
  "optimize-job-search-assets",
  "prepare-role-interviews",
  "recommend-career-learning",
  "track-job-search-outcomes"
]
```

- [ ] **Step 2: Run the structural test and verify RED**

Run: `python3 -m unittest tests.test_plugin_structure -v`

Expected: FAIL because `plugins/job-search-coach/.codex-plugin/plugin.json` does not exist.

- [ ] **Step 3: Generate the scaffold**

Run from the worktree root:

```bash
python3 /path/to/workspace/.codex/skills/.system/plugin-creator/scripts/create_basic_plugin.py job-search-coach \
  --path plugins \
  --with-skills --with-scripts
```

Superseded historical identity instruction: use configured metadata or a JSC synthetic identifier only.

- [ ] **Step 4: Add the canonical inventory and run GREEN**

Create the fixture required by the test. Skill directories are created later, one at a time, only after each skill has a failing behavioral baseline. Then run:

`python3 -m unittest tests.test_plugin_structure -v`

Expected: PASS.

- [ ] **Step 5: Validate the plugin and commit**

Run:

```bash
python3 /path/to/workspace/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/job-search-coach
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Commit: `feat: scaffold job search coach plugin`

### Task 2: Orchestrator, candidate isolation, and action boundaries

**Files:**
- Create: `tests/evals/baseline/orchestrator.md`
- Create: `plugins/job-search-coach/skills/job-search-coach/SKILL.md`
- Create: `plugins/job-search-coach/skills/job-search-coach/agents/openai.yaml`
- Create: `plugins/job-search-coach/skills/job-search-coach/references/case-contract.md`
- Create: `plugins/job-search-coach/skills/job-search-coach/references/evidence-and-safety.md`
- Create: `plugins/job-search-coach/skills/job-search-coach/references/routing.md`
- Create: `plugins/job-search-coach/scripts/validate_case.py`
- Create: `tests/test_validate_case.py`
- Create: `tests/evals/with-skill/orchestrator.md`

**Interfaces:**
- Produces CLI: `python3 validate_case.py CASE.json`, exit `0` for valid cases and `2` with newline-delimited errors for invalid cases.
- Produces case keys: `schema_version`, `candidate_id`, `mode`, `consent`, `target`, `sources`, `claims`, `interventions`, `outcomes`.
- Produces router output contract: `case_state`, `evidence_gaps`, `selected_module`, `next_action`, `authorization_required`.

- [ ] **Step 1: Capture RED baseline behavior**

Dispatch at least two fresh agents without access to the new skill. Give one a self-service case with conflicting LinkedIn/CV facts and one a coach-mode request containing two candidates. Save verbatim outputs and observed failures in `tests/evals/baseline/orchestrator.md`; specifically score data leakage, unlabeled inference, missing authorization boundary, and incorrect routing.

- [ ] **Step 2: Write failing case-validator tests**

Create tests for a valid isolated case, missing `candidate_id`, invalid evidence label, benchmark consent defaulting to false, and mixed candidate IDs in one record.

- [ ] **Step 3: Run validator tests and verify RED**

Run: `python3 -m unittest tests.test_validate_case -v`

Expected: FAIL because `validate_case.py` does not exist.

- [ ] **Step 4: Implement the validator and orchestrator skill**

Implement the standard-library validator. Initialize the skill with `init_skill.py`, generate `agents/openai.yaml`, then replace placeholders with a concise router workflow. The skill must require reading `case-contract.md`, `evidence-and-safety.md`, and `routing.md` only when their conditions apply.

- [ ] **Step 5: Verify GREEN and forward-test**

Run the validator tests, quick validation, and the same two scenarios with the skill. Store verbatim outputs and rubric results in `tests/evals/with-skill/orchestrator.md`. Require zero cross-candidate leakage, explicit evidence labels, correct module selection, and action-time authorization flags.

- [ ] **Step 6: Refactor and commit**

Run the scenarios once more with contradictory facts and an urgent request to auto-apply. Add only guidance needed to close observed loopholes. Commit: `feat: add safe job search coach orchestrator`.

### Task 3: LinkedIn expert module

**Files:**
- Create: `tests/evals/baseline/linkedin.md`
- Create: `plugins/job-search-coach/skills/optimize-linkedin-career/SKILL.md`
- Create: `plugins/job-search-coach/skills/optimize-linkedin-career/agents/openai.yaml`
- Create: `plugins/job-search-coach/skills/optimize-linkedin-career/references/profile-audit.md`
- Create: `plugins/job-search-coach/skills/optimize-linkedin-career/references/search-positioning.md`
- Create: `plugins/job-search-coach/skills/optimize-linkedin-career/references/networking-and-content.md`
- Create: `plugins/job-search-coach/skills/optimize-linkedin-career/references/experiments.md`
- Create: `tests/evals/with-skill/linkedin.md`
- Create: `tests/test_skill_contracts.py`

**Interfaces:**
- Consumes: orchestrator evidence labels and action boundaries.
- Produces sections: `executive_diagnosis`, `visibility_gaps`, `positioning`, `rewrites`, `networking_drafts`, `content_plan`, `experiment_plan`, `approval_gates`.

- [ ] **Step 1: Capture RED baselines**

Use fresh agents to audit the approved senior technology profile facts and a second incomplete non-technical profile without the skill. Record whether they inspect every LinkedIn section, distinguish visible from unavailable data, avoid inventing algorithm claims, and tie keywords to current vacancies.

- [ ] **Step 2: Gather read-only LinkedIn evidence**

Use the authenticated Chrome session only for reading. Record the capture date, visible headline, location, analytics values, visible sections, and inaccessible sections. Do not connect, message, post, edit, or apply. Store only non-sensitive professional observations in `tests/evals/baseline/linkedin.md`.

- [ ] **Step 3: Write failing contract tests**

Extend `tests/test_skill_contracts.py` to require frontmatter, matching names, `Use when...` descriptions, valid `agents/openai.yaml`, links to the four reference files, a visible/unavailable distinction, dated-source requirements, and action-time approval gates.

- [ ] **Step 4: Run RED, initialize, and implement**

Run the contract test before creating the skill. Initialize with `init_skill.py`, then implement the minimum audit, recruiter-search positioning, evidence-based rewriting, networking/content drafting, vacancy matching, and 14/30/60/90-day experiment workflow that fixes the baseline failures.

- [ ] **Step 5: Run GREEN and adversarial forward tests**

Test: senior technical profile, junior profile without metrics, profile with CV contradictions, request to claim Terraform expertise without evidence, and request to send recruiter messages immediately. Save outputs in `tests/evals/with-skill/linkedin.md`.

- [ ] **Step 6: Validate and commit**

Run quick validation, contract tests, and the plugin validator. Commit: `feat: add linkedin career optimization skill`.

### Task 4: High-value career path discovery

**Files:**
- Create: `tests/evals/baseline/market.md`
- Create: `plugins/job-search-coach/skills/discover-high-value-career-paths/SKILL.md`
- Create: `plugins/job-search-coach/skills/discover-high-value-career-paths/agents/openai.yaml`
- Create: `plugins/job-search-coach/skills/discover-high-value-career-paths/references/path-scoring.md`
- Create: `tests/evals/with-skill/market.md`

**Interfaces:**
- Produces path score dimensions: compensation, demand, transferability, gap_cost, geography_fit, evidence_confidence.

- [ ] **Step 1: Run a no-skill market baseline**

Ask fresh agents for the highest-paying current roles for one senior technical and one non-technical candidate in Mexico, the US, and remote markets. Record stale claims, unsupported rankings, geography/currency mixing, and unrealistic transitions.

- [ ] **Step 2: Write RED contract tests**

Require source dates, geography and currency, confidence, primary-source preference, transferability, gap cost, and refusal to call a role “highest paying” from a single anecdote.

- [ ] **Step 3: Implement and verify the skill**

Initialize, implement, validate, and forward-test `discover-high-value-career-paths`. The module must request a separate market brief when current demand or compensation is needed rather than inventing market evidence.

- [ ] **Step 4: Forward-test and commit**

Verify that path discovery compares realistic transitions and routes current evidence gathering to `research-target-job-market`. Save outputs in `tests/evals/with-skill/market.md`.

Commit: `feat: add high value career path discovery`.

### Task 5: Current target-market research

**Files:**
- Modify: `tests/evals/baseline/market.md`
- Create: `plugins/job-search-coach/skills/research-target-job-market/SKILL.md`
- Create: `plugins/job-search-coach/skills/research-target-job-market/agents/openai.yaml`
- Create: `plugins/job-search-coach/skills/research-target-job-market/references/source-policy.md`
- Create: `plugins/job-search-coach/skills/research-target-job-market/references/market-brief.md`
- Modify: `tests/evals/with-skill/market.md`

**Interfaces:**
- Produces market brief fields: role, geography, currency, seniority, source_date, sample_context, range, demand_signals, recurring_requirements, confidence.
- Consumes a target role or comparison list and returns evidence; it does not choose the candidate's career path.

- [ ] **Step 1: Capture a dated no-skill research baseline**

Ask a fresh agent to compare one role across Mexico, the US, and remote international markets. Record stale or missing dates, incompatible salary bases, unsupported demand claims, and weak source hierarchy.

- [ ] **Step 2: Write RED contract tests**

Require dated sources, geography, currency, compensation basis, seniority, sample context, confidence, and a warning when data is not comparable.

- [ ] **Step 3: Implement and forward-test**

Initialize and implement the skill. Market research must browse because demand and compensation are time-sensitive. Prefer current vacancies and official employer sources, followed by government data and transparent salary studies.

- [ ] **Step 4: Cross-module integration test and commit**

Verify that path discovery can consume the market brief while market research does not make the final career decision. Commit: `feat: add target job market research`.

### Task 6: CV, ATS, portfolio, and application assets

**Files:**
- Create: `tests/evals/baseline/assets.md`
- Create: `plugins/job-search-coach/skills/optimize-job-search-assets/SKILL.md`
- Create: `plugins/job-search-coach/skills/optimize-job-search-assets/agents/openai.yaml`
- Create: `plugins/job-search-coach/skills/optimize-job-search-assets/references/asset-workflow.md`
- Create: `plugins/job-search-coach/skills/optimize-job-search-assets/references/ats-and-truthfulness.md`
- Create: `plugins/job-search-coach/skills/optimize-job-search-assets/assets/candidate-fact-matrix.md`
- Create: `tests/evals/with-skill/assets.md`

**Interfaces:**
- Consumes: candidate facts and a target vacancy.
- Produces: fact matrix, ATS gap map, master CV recommendations, vacancy-tailored draft, portfolio evidence plan, consistency report.

- [ ] **Step 1: Capture RED baseline**

Give a fresh agent a vacancy requiring Terraform and Argo CD plus a candidate who has neither. Record keyword stuffing, fabricated experience, generic bullets, and missing LinkedIn/CV consistency checks.

- [ ] **Step 2: Add failing contracts and initialize**

Require every rewritten claim to map to a candidate fact ID or be labeled a recommendation. Require ATS feedback to distinguish formatting, terminology, evidence, and genuine skill gaps.

- [ ] **Step 3: Implement minimal truthful asset workflow**

Add a candidate fact matrix asset, impact-first bullet guidance without invented metrics, vacancy tailoring, portfolio evidence, and export recommendations. Do not promise ATS scores from opaque systems.

- [ ] **Step 4: Forward-test and commit**

Test technical, non-technical, junior, and career-transition cases. Commit: `feat: add truthful job search asset optimization`.

### Task 7: Vacancy-specific interview preparation

**Files:**
- Create: `tests/evals/baseline/interviews.md`
- Create: `plugins/job-search-coach/skills/prepare-role-interviews/SKILL.md`
- Create: `plugins/job-search-coach/skills/prepare-role-interviews/agents/openai.yaml`
- Create: `plugins/job-search-coach/skills/prepare-role-interviews/references/interview-map.md`
- Create: `plugins/job-search-coach/skills/prepare-role-interviews/references/evaluation-rubrics.md`
- Create: `plugins/job-search-coach/skills/prepare-role-interviews/assets/mock-interview-scorecard.md`
- Create: `tests/evals/with-skill/interviews.md`

**Interfaces:**
- Consumes: vacancy, company evidence, candidate fact matrix, interview stage.
- Produces: competency map, likely questions with rationale, truthful story bank, technical/system/design practice when relevant, mock interview, scorecard, interviewer questions, follow-up draft.

- [ ] **Step 1: Capture RED baseline**

Evaluate generic interview advice against a Principal SRE vacancy and a high-paying non-technical role. Record questions not grounded in the vacancy, hallucinated company process, and feedback without a rubric.

- [ ] **Step 2: Add RED contracts and implement**

Require vacancy-to-question traceability, stage-specific preparation, fact IDs for answer stories, explicit unknowns, and a weighted scorecard. Initialize and implement the skill.

- [ ] **Step 3: Forward-test multiple interview stages**

Test recruiter screen, hiring-manager interview, technical deep dive, system design, behavioral loop, and offer-stage questions. The skill must state when a stage is not applicable.

- [ ] **Step 4: Validate and commit**

Commit: `feat: add vacancy specific interview preparation`.

### Task 8: Learning and certification return-on-investment

**Files:**
- Create: `tests/evals/baseline/learning.md`
- Create: `plugins/job-search-coach/skills/recommend-career-learning/SKILL.md`
- Create: `plugins/job-search-coach/skills/recommend-career-learning/agents/openai.yaml`
- Create: `plugins/job-search-coach/skills/recommend-career-learning/references/learning-roi.md`
- Create: `plugins/job-search-coach/skills/recommend-career-learning/references/evidence-projects.md`
- Create: `tests/evals/with-skill/learning.md`

**Interfaces:**
- Produces learning recommendation fields: gap, frequency_in_target_jobs, proof_needed, option, provider, current_cost, duration, prerequisite, opportunity_cost, expected_signal, confidence.

- [ ] **Step 1: Capture RED baseline**

Ask a fresh agent for certifications for a senior SRE and courses for a non-technical transition. Record certificate collecting, stale prices, recommendations disconnected from vacancies, and failure to prefer a demonstrable project.

- [ ] **Step 2: Add RED contracts and implement**

Require repeated vacancy evidence, current official course/certification sources, total cost and time, prerequisites, alternatives, and a “do nothing now” option. Initialize and implement the skill.

- [ ] **Step 3: Forward-test and commit**

Test a candidate with a real gap, one with only a keyword mismatch, one with limited budget, and one where a portfolio project has higher expected return. Commit: `feat: add evidence based career learning recommendations`.

### Task 9: Outcome tracking and experiments

**Files:**
- Create: `plugins/job-search-coach/skills/track-job-search-outcomes/SKILL.md`
- Create: `plugins/job-search-coach/skills/track-job-search-outcomes/agents/openai.yaml`
- Create: `plugins/job-search-coach/skills/track-job-search-outcomes/references/measurement.md`
- Create: `plugins/job-search-coach/skills/track-job-search-outcomes/assets/outcomes.csv`
- Create: `plugins/job-search-coach/scripts/summarize_outcomes.py`
- Create: `tests/test_summarize_outcomes.py`
- Create: `tests/evals/baseline/outcomes.md`
- Create: `tests/evals/with-skill/outcomes.md`

**Interfaces:**
- CLI: `python3 summarize_outcomes.py outcomes.csv --window 30 --as-of YYYY-MM-DD`.
- Output JSON: `window_days`, `applications`, `responses`, `interviews`, `offers`, `response_rate`, `interview_rate`, `offer_rate`, `days_to_first_interview`, `warnings`.

- [ ] **Step 1: Write outcome-calculation tests and verify RED**

Test zero denominators, 14/30/60/90-day windows, missing dates, multiple currencies, and no false causal attribution. Run before creating the script.

- [ ] **Step 2: Implement script and verify GREEN**

Use `csv`, `datetime`, `decimal`, and `json` from the Python standard library. Never convert currencies without an explicit dated exchange rate.

- [ ] **Step 3: Capture behavioral baseline and implement skill**

Baseline a request to prove that a headline change caused an offer. Implement controlled-change guidance, intervention logging, confounder warnings, and coach-mode aggregation with explicit anonymized benchmarking consent.

- [ ] **Step 4: Forward-test and commit**

Test sparse data, simultaneous interventions, and two isolated candidates. Commit: `feat: add job search outcome tracking`.

### Task 10: Full-plugin routing, adversarial evaluation, and documentation

**Files:**
- Create: `plugins/job-search-coach/README.md`
- Create: `plugins/job-search-coach/tests/eval-rubric.json`
- Create: `plugins/job-search-coach/tests/run_static_checks.py`
- Create: `tests/test_full_plugin.py`
- Modify: `plugins/job-search-coach/skills/job-search-coach/references/routing.md`
- Modify: `plugins/job-search-coach/skills/job-search-coach/SKILL.md`
- Create: `tests/evals/final/cycle-1.md`
- Create: `tests/evals/final/cycle-2.md`

**Interfaces:**
- `run_static_checks.py` returns exit `0` only when every skill passes naming, frontmatter, link, placeholder, size, agent-metadata, and required-sub-skill checks.
- Full router recognizes audit, market, assets, interview, learning, and outcome requests, including multi-module plans.

- [ ] **Step 1: Write failing full-plugin tests**

Require all eight skills, valid links, no placeholders, no duplicate descriptions, orchestrator routes for all modules, and examples covering self-service and coach mode.

- [ ] **Step 2: Implement static checker and complete routing**

Keep the README limited to plugin-level usage, privacy, installation, and starter prompts; do not add README files inside skills.

- [ ] **Step 3: Run improvement cycle 1**

Dispatch fresh agents on six end-to-end cases: senior technical, non-technical transition, junior, imminent interview, unsupported technology claim, and two-candidate coach mode. Record raw outputs, rubric scores, and every observed failure in `cycle-1.md`.

- [ ] **Step 4: Refactor from cycle 1 and run improvement cycle 2**

Add only changes tied to recorded failures. Repeat the six cases with fresh agents and record comparisons in `cycle-2.md`. Require no regression in truthfulness, privacy, or authorization boundaries.

- [ ] **Step 5: Run full verification and commit**

Run:

```bash
python3 plugins/job-search-coach/tests/run_static_checks.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 /path/to/workspace/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/job-search-coach
for skill in plugins/job-search-coach/skills/*; do
  python3 /path/to/workspace/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$skill"
done
```

Commit: `test: validate integrated job search coach plugin`.

### Task 11: Local marketplace installation and fresh-session smoke test

**Files:**
- Create or update only after action-time approval: `.agents/plugins/marketplace.json`
- Modify during reinstall cycles: `plugins/job-search-coach/.codex-plugin/plugin.json`
- Create: `tests/evals/final/installed-smoke-test.md`

**Interfaces:**
- Marketplace entry points to `./plugins/job-search-coach` with installation `AVAILABLE`, authentication `ON_INSTALL`, and category `Productivity`.
- A new Codex thread discovers `$job-search-coach` and routes one LinkedIn audit plus one interview request.

- [ ] **Step 1: Request marketplace authorization**

Immediately before creating or modifying the marketplace and installing the plugin, show the exact target path and commands. Do not infer installation approval from implementation approval.

- [ ] **Step 2: Create repo-local marketplace entry**

Run the plugin scaffold helper with explicit repo paths and `--with-marketplace`; do not hand-edit an existing marketplace entry.

- [ ] **Step 3: Validate and install the marketplace**

Run `codex plugin marketplace add <repo-root>/.agents/plugins` only if the non-default marketplace is not configured, then install `job-search-coach@<marketplace-name>`.

- [ ] **Step 4: Start a fresh thread and smoke-test**

Verify discovery, routing, LinkedIn evidence labels, and interview-vacancy traceability. Record the prompts and outcomes in `installed-smoke-test.md`.

- [ ] **Step 5: Final requirement audit and release commit**

Map every objective and design requirement to a file, command result, or eval transcript. Resolve missing evidence before tagging or publishing. Commit: `chore: prepare job search coach plugin release`.
