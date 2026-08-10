# First Interview Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add draft-only recruiter/LinkedIn first-interview workflows that turn evidence-safe profile positioning into recruiter screens, referral conversations, and stage-specific interview prep without claiming guaranteed outcomes.

**Architecture:** Keep the existing plugin structure. Extend the LinkedIn skill with auditable matrices for recruiter searchability, keyword placement, outreach/referral drafts, proof assets, and funnel measurement. Extend the interview skill with a recruiter-screen playbook, vacancy-gap/objection mapping, stage-aware questions, and follow-up lifecycle language.

**Tech Stack:** Markdown skill/reference files, stdlib Python `unittest`, existing static checker, no new dependencies.

## Global Constraints

- No LinkedIn edit, message, connection request, post, upload, application, or external share may be executed without exact action-and-target authorization immediately before execution.
- Every material recommendation, draft, and claim must keep one of the canonical evidence prefixes: `verified:`, `candidate-reported:`, `inferred:`, or `unknown:`.
- Do not promise response rates, interviews, salaries, time-to-hire, recruiter ranking, search ranking, or causal uplift.
- Do not infer market demand from static keyword lists; dated current vacancies are required for market/current-demand claims.
- Preserve candidate isolation and confidentiality review requirements for internal/employer/customer material.

---

### Task 1: LinkedIn first-interview funnel contract

**Files:**
- Modify: `tests/test_skill_contracts.py`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/SKILL.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/references/profile-audit.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/references/search-positioning.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/references/networking-and-content.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/references/experiments.md`

**Interfaces:**
- Produces: a LinkedIn contract with `audit_priority_matrix`, `keyword_evidence_matrix`, `outreach_funnel`, `proof_asset_matrix`, and `linkedin_funnel_events`.
- Consumes: existing LinkedIn sections `executive_diagnosis`, `visibility_gaps`, `positioning`, `rewrites`, `networking_drafts`, `content_plan`, `experiment_plan`, and `approval_gates`.

- [ ] **Step 1: Write failing tests**

Add assertions to `OptimizeLinkedInCareerContractTests.test_linkedin_skill_has_the_required_safe_contract`:

```python
for required in (
    "audit_priority_matrix",
    "keyword_evidence_matrix",
    "outreach_funnel",
    "proof_asset_matrix",
    "linkedin_funnel_events",
    "connection_note",
    "recruiter_interest",
    "referral_request",
    "follow_up_stop_condition",
    "exact action-and-target authorization",
):
    self.assertIn(required, contract)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python3 -B -m unittest tests.test_skill_contracts.OptimizeLinkedInCareerContractTests.test_linkedin_skill_has_the_required_safe_contract -v
```

Expected: fail because at least `audit_priority_matrix` is not present.

- [ ] **Step 3: Implement minimal LinkedIn contract**

Update the LinkedIn skill/reference files to require:

- `audit_priority_matrix`: section, evidence status, target theme/query, supported proof, issue, priority, draft/change, confirmation needed.
- `keyword_evidence_matrix`: phrase/title variant, dated vacancy source, geography/arrangement, candidate fact ID or `unknown`, safe profile section, decision `use|confirm|omit`.
- `outreach_funnel`: contact category, evidence source, draft type, relationship context, stop condition, and exact authorization gate.
- `proof_asset_matrix`: audience, fact IDs demonstrated, confidentiality status, public-disclosure evidence, format, Featured/content placement, and measurement hypothesis.
- `linkedin_funnel_events`: dated candidate-isolated observations for profile view/search appearance, qualified contact, conversation, referral/application, recruiter screen, interview, source, version, and confounders.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
python3 -B -m unittest tests.test_skill_contracts.OptimizeLinkedInCareerContractTests.test_linkedin_skill_has_the_required_safe_contract -v
python3 plugins/job-search-coach/tests/run_static_checks.py
```

Expected: both pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_skill_contracts.py plugins/job-search-coach/skills/optimize-linkedin-career/SKILL.md plugins/job-search-coach/skills/optimize-linkedin-career/references/profile-audit.md plugins/job-search-coach/skills/optimize-linkedin-career/references/search-positioning.md plugins/job-search-coach/skills/optimize-linkedin-career/references/networking-and-content.md plugins/job-search-coach/skills/optimize-linkedin-career/references/experiments.md
git commit -m "feat: add linkedin first interview funnel"
```

### Task 2: Recruiter-screen and objection-map interview contract

**Files:**
- Modify: `tests/test_skill_contracts.py`
- Modify: `plugins/job-search-coach/skills/prepare-role-interviews/SKILL.md`
- Modify: `plugins/job-search-coach/skills/prepare-role-interviews/references/interview-map.md`
- Modify: `plugins/job-search-coach/skills/prepare-role-interviews/references/evaluation-rubrics.md`
- Modify: `plugins/job-search-coach/skills/prepare-role-interviews/assets/mock-interview-scorecard.md`

**Interfaces:**
- Produces: recruiter-screen playbook, gap/objection map, stage-aware question bank, follow-up lifecycle, and stage-aware scorecard anchors.
- Consumes: existing interview sections `competency_map`, `likely_questions`, `truthful_story_bank`, `role_practice`, `mock_interview`, `scorecard`, `interviewer_questions`, and `follow_up_draft`.

- [ ] **Step 1: Write failing tests**

Add assertions to `PrepareRoleInterviewsContractTests.test_interview_preparation_is_vacancy_specific_and_truthful`:

```python
for required in (
    "recruiter_screen_brief",
    "vacancy_candidate_gap_map",
    "objection_response_map",
    "question_bank",
    "follow_up_lifecycle",
    "technical screen",
    "take-home",
    "panel",
    "recipient",
    "event reference",
):
    self.assertIn(required, contract)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python3 -B -m unittest tests.test_skill_contracts.PrepareRoleInterviewsContractTests.test_interview_preparation_is_vacancy_specific_and_truthful -v
```

Expected: fail because at least `recruiter_screen_brief` is not present.

- [ ] **Step 3: Implement minimal interview contract**

Update interview skill/reference/asset files to require:

- `recruiter_screen_brief`: opening pitch, why-now/why-this-role, scope, logistics, compensation handling, location/work authorization/notice period confirmation, recruiter questions, and safe close.
- `vacancy_candidate_gap_map`: each `V-###` with must-have/preferred when supplied, strength/transferable/gap/unknown, recency, proof needed, likely objection, truthful bridge language.
- `objection_response_map`: objection, evidence, candidate clarification, safe response, and unsupported-claim refusal.
- `question_bank`: stage, question ID, requirement/process/constraint ID, core question, follow-up probe, expected signal, fact IDs.
- `follow_up_lifecycle`: recruiter-screen thank-you, hiring-manager follow-up, clarification note, overdue-process check-in, recipient, event reference, timing state, draft-only gate.
- `technical screen`, `take-home`, and `panel` as stage labels, with not-applicable reasons when not requested.
- scorecard anchors for 0–4 and stage-aware weighting notes.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
python3 -B -m unittest tests.test_skill_contracts.PrepareRoleInterviewsContractTests.test_interview_preparation_is_vacancy_specific_and_truthful -v
python3 plugins/job-search-coach/tests/run_static_checks.py
```

Expected: both pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_skill_contracts.py plugins/job-search-coach/skills/prepare-role-interviews/SKILL.md plugins/job-search-coach/skills/prepare-role-interviews/references/interview-map.md plugins/job-search-coach/skills/prepare-role-interviews/references/evaluation-rubrics.md plugins/job-search-coach/skills/prepare-role-interviews/assets/mock-interview-scorecard.md
git commit -m "feat: add recruiter screen interview contract"
```

### Task 3: Integration and eval record

**Files:**
- Modify: `tests/test_full_plugin.py`
- Modify: `tests/evals/with-skill/interviews.md`
- Modify: `tests/evals/with-skill/linkedin.md`
- Modify: `plugins/job-search-coach/README.md`

**Interfaces:**
- Produces: visible eval transcript evidence that the first-interview engine is part of the plugin behavior.
- Consumes: Task 1 and Task 2 terms exactly.

- [ ] **Step 1: Write failing tests**

Add a first-interview integration assertion:

```python
combined = "\n".join(
    path.read_text(encoding="utf-8")
    for path in (
        REPO_ROOT / "tests" / "evals" / "with-skill" / "linkedin.md",
        REPO_ROOT / "tests" / "evals" / "with-skill" / "interviews.md",
    )
)
for required in (
    "keyword_evidence_matrix",
    "outreach_funnel",
    "recruiter_screen_brief",
    "objection_response_map",
    "do not send",
    "exact action-and-target authorization",
):
    self.assertIn(required, combined)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python3 -B -m unittest tests.test_full_plugin.FullPluginIntegrationTests -v
```

Expected: fail because the eval transcripts do not yet include the new cycle terms.

- [ ] **Step 3: Update eval records and README**

Update eval records with compact, normalized transcript snippets that demonstrate:

- LinkedIn keyword evidence matrix with `use|confirm|omit`.
- Draft-only outreach funnel with connection, recruiter-interest, referral-request, and follow-up stop conditions.
- Recruiter screen brief with logistics/compensation/work authorization as unknowns or candidate-reported facts.
- Objection response map that refuses unsupported production/quota/salary claims.
- Explicit `do not send` and exact authorization gate.

Update README starter prompts with one first-interview prompt.

- [ ] **Step 4: Verify GREEN and full suite**

Run:

```bash
python3 plugins/job-search-coach/tests/run_static_checks.py
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_full_plugin.py tests/evals/with-skill/interviews.md tests/evals/with-skill/linkedin.md plugins/job-search-coach/README.md
git commit -m "test: record first interview engine evals"
```

## Plan Self-Review

- Spec coverage: covers LinkedIn recruiter funnel, recruiter-screen interview prep, objection/gap maps, authorization gates, and eval evidence.
- Placeholder scan: no TODO/TBD placeholders.
- Scope check: market-source observation ledger is intentionally deferred to a later cycle because it is a separate subsystem.
