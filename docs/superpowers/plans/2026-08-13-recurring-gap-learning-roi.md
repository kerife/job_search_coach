# Recurring-Gap Learning ROI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn recurring learnable gaps from the verified vacancy sample into current, source-backed course/certification decisions, study topics, and candidate-owned proof alternatives without creating a shopping list or implying hiring outcomes.

**Architecture:** Preserve `career-market-learning-dossier-v1` as the market-only placeholder release. A closed `learning-option-research-v1` artifact records current official provider evidence and candidate time/budget preferences; a pure builder binds it to an exact validated market snapshot and emits `career-market-learning-dossier-v2`. V2 retains every market score/matrix/recurrence byte-for-byte and adds ranked ROI decisions; the renderer composes one learning region after recurring gaps and never recomputes provider or market evidence.

**Tech Stack:** Python 3.11+, standard library only, JSON Schema draft 2020-12 subset, `unittest`, current official provider browsing at generation time, offline semantic HTML/CSS, existing private loaders/writers and Superdesign parity tooling.

## Global Constraints

- Preserve v1/v2/v3 executive dossiers and `career-market-learning-dossier-v1` schema, validation, fixtures, arithmetic, matrix, rendering, and CLI behavior unchanged.
- Every learning decision is bound to an exact validated market-dossier snapshot and recurring gap IDs; no free-text keyword matching creates a recommendation.
- Paid learning requires a sample of at least two vacancies and recurrence `k >= max(2, floor(N/2)+1)`: `2/2`, `2/3`, `3/4`, or `3/5`.
- A single-vacancy or non-recurring requirement may produce a source-specific study topic or `do_nothing_now`, never a paid recommendation.
- Current provider fields come from an official source opened on the access date or remain `unknown`; never hardcode prices, duration, prerequisites, renewal, maintenance, availability, or Mexico eligibility.
- Separate cost, currency, tax, duration, prerequisite, renewal, maintenance, geography, availability, and unknowns. Online delivery does not prove Mexico eligibility.
- A project/lab/proof alternative is evaluated before paid learning. A certification never substitutes for production experience.
- Paid `recommended` requires current official source, learnable gap, known candidate budget/time fit, and no cheaper higher-signal proof alternative. Otherwise use `consider`, `pause`, `project_first`, `apply_with_boundary`, or `not_needed`.
- Every expected-signal statement begins `bounded hypothesis`; never predict interview, job, offer, salary, time-to-hire, ATS/recruiter ranking, exam pass, or ROI.
- No enrollment, purchase, account creation, exam scheduling, reimbursement, publication, sharing, upload, message, connection, application, or other external action without exact action-and-target authorization immediately before execution.
- Candidate-owned projects require ownership, secrets, confidentiality, customer-data, rights-holder, and public-disclosure review before publication.
- Provider/company/course names and values exist only in structured run-time artifacts, synthetic fixtures, and escaped HTML; never in skill logic.
- No remote asset, chart library, CDN, canvas, SVG, form, local storage, or relaxed CSP.
- One cachebuster only after all non-provenance gates and independent reviews are green; leave the public marketplace identity unchanged and disclose both identities enabled.

---

### Task 1: Closed provider and learning-option research contract

**Files:**
- Create: `plugins/professional-growth-coach/schemas/learning-option-research-v1.schema.json`
- Create: `plugins/professional-growth-coach/scripts/validate_learning_option_research.py`
- Create: `tests/test_learning_option_research.py`
- Create: `tests/evals/with-skill/fixtures/learning-option-research/complete-five-es.json`
- Create: `tests/evals/with-skill/fixtures/learning-option-research/limited-four-en.json`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

**Interfaces:**
- Produces `validate_research(value: object) -> list[str]`, `load_research(path: Path) -> dict[str, object]`, `snapshot_for_learning_research(value: Mapping[str, object]) -> str`, and `_cli(argv) -> int`.
- Consumes a `source_market_snapshot` matching the canonical market-dossier snapshot format.

- [ ] **Step 1: Write RED state/source tests**

Use synthetic fixture providers `Fixture University`, `Fixture Learning
Platform`, and `Fixture Vendor`; use only `example.com` URLs and
`source_state=synthetic`. Test artifacts must be unmistakably synthetic and
cannot support a live recommendation.

Each research artifact requires one through five options and one candidate
preference object:

```json
{
  "schema_version": "learning-option-research-v1",
  "locale": "es",
  "as_of_date": "2026-08-13",
  "source_market_snapshot": "snap-market-sha256-<64 lowercase hex>",
  "candidate_preferences": {
    "weekly_time_budget": "unknown",
    "money_budget": "unknown",
    "currency": "unknown",
    "purchase_authorized": false
  },
  "options": [],
  "privacy_boundary": "identity_free_market_and_provider_evidence_only",
  "no_external_action": true
}
```

Observe import RED before implementation.

- [ ] **Step 2: Add closed option and official-source RED cases**

Every option requires `option_id`, `gap_signal`,
`option_type=free_resource|course|certification|lab|candidate_owned_project|do_nothing_now`,
`provider`, `option`, `source_title`, `source_date`, `source_state`, `url`,
`geography`, `availability`, `role`, `seniority`, `current_cost`, `currency`,
`tax`, `duration`, `duration_basis=provider_verified|provider_duration_unknown|candidate_estimated`,
`prerequisite`, `renewal`, `maintenance`, `unknowns`,
`proof_artifact`, and `action_gate`.

Reject duplicate option IDs, duplicate URLs, non-HTTPS/private/credential URLs,
future dates, stale/unavailable source treated as current, provider options
without official source, course price without currency/tax, merged
renewal/maintenance, online-as-Mexico-eligibility inference, candidate project
without ownership/privacy gates, `purchase_authorized=true`, private values,
raw source content, control characters, extra fields, malformed JSON, deep
recursion, oversize, FIFO, and symlinks. Diagnostics remain fixed/non-echoing.

- [ ] **Step 3: Implement schema, descriptor-safe validator, and snapshot**

Follow the market validator's closed-schema, depth-12, 256-KiB,
duplicate-key, descriptor-no-follow, bounded diagnostic, and CLI patterns.
Live provider options require `source_state=active`; fixtures may use
`synthetic`. `do_nothing_now` has provider `none`, URL `null`, and all provider
commercial fields `not_applicable`. Project/lab rows use candidate-estimated
duration and no price. Return sorted unique errors without mutating input.

- [ ] **Step 4: Verify GREEN and conformance**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/professional-growth-coach/scripts \
  python3 -B -m unittest \
  tests.test_learning_option_research \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py -v
git diff --check
```

- [ ] **Step 5: Commit Task 1**

```bash
git add \
  plugins/professional-growth-coach/schemas/learning-option-research-v1.schema.json \
  plugins/professional-growth-coach/scripts/validate_learning_option_research.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  tests/evals/with-skill/fixtures/learning-option-research \
  tests/test_learning_option_research.py
git commit -m "feat: validate current learning option research"
```

---

### Task 2: Pure recurring-gap ROI builder and v2 market-learning contract

**Files:**
- Create: `plugins/professional-growth-coach/schemas/career-market-learning-dossier-v2.schema.json`
- Create: `plugins/professional-growth-coach/scripts/build_career_market_learning_dossier_v2.py`
- Create: `plugins/professional-growth-coach/scripts/validate_career_market_learning_dossier_v2.py`
- Create: `tests/test_career_market_learning_dossier_v2.py`
- Create: `tests/evals/with-skill/fixtures/career-market-learning-dossier-v2/project-first-five-es.json`
- Create: `tests/evals/with-skill/fixtures/career-market-learning-dossier-v2/consider-course-four-en.json`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

**Interfaces:**
- Consumes validated market v1 plus
  `snapshot_for_market_dossier(market) -> snap-market-sha256-<64 lowercase hex>`
  and Task 1 learning research.
- Produces `build_learning_dossier(market, learning_research) -> dict[str, object]`, `validate_learning_dossier(value) -> list[str]`, and `required_recurrence(sample_size: int) -> int`.

- [ ] **Step 1: Write exact recurrence and decision RED tests**

Assert thresholds `2->2`, `3->2`, `4->3`, `5->3`; reject paid
recommendation for `N=1`, `2/4`, or `2/5`. Assert a professional-experience
gap can only be `project_first`, `apply_with_boundary`, or `pause`, never
replaced by a certificate. Assert unknown time or money budget prevents paid
`recommended` but still permits `consider` with an exact review gate.

- [ ] **Step 2: Observe RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_career_market_learning_dossier_v2 -v
```

Expected: missing builder/validator.

- [ ] **Step 3: Define the closed v2 derived contract**

Copy every market-v1 field unchanged, change schema version, bind
`source_market_snapshot` and `source_learning_research_snapshot`, set
`learning_state=evaluated`, and require three through five ranked decisions.
Each decision contains:

```json
{
  "rank": 1,
  "gap_signal": "terraform_iac",
  "frequency_occurrences": 3,
  "frequency_sample_size": 5,
  "frequency_display": "3/5",
  "gap_type": "proof_gap",
  "option_id": "LO-001",
  "option_type": "candidate_owned_project",
  "decision": "project_first",
  "proof_needed": "fixed bounded identity-free text",
  "opportunity_cost": "fixed bounded identity-free text",
  "decision_basis": "candidate-owned evidence ...",
  "next_action_gate": "no external action ...",
  "expected_signal": "bounded hypothesis ...",
  "confidence": "medium",
  "outcome_boundary": "not_an_interview_offer_salary_or_roi_prediction",
  "draft_only": true,
  "no_external_action": true
}
```

Provider/source details remain separately addressable through `option_id` and
are copied as structured rows. Include exactly one `coach_decision`, and when
it selects a candidate-owned project require one five-day private proof sprint
plus exactly three reuse-map rows for LinkedIn, application packet, and
interview. Every reuse row retains exact authorization gates and private-safe
claims.

- [ ] **Step 4: Implement pure builder and independent recomputation**

Validate both inputs and snapshots. Deep-copy market v1 unchanged. Map only
exact recurrence rows and exact option gap signals; never infer from prose.
Calculate thresholds and frequency fields. Rank `project_first` before paid
learning when its evidence value is higher, then `recommended`, `consider`,
`apply_with_boundary`, `pause`, `not_needed`, with stable option-ID tie-break.

Reject caller mutation of any copied market field, threshold, frequency,
decision, rank, option binding, source state, sprint/reuse map, or boundary.
Provider options require `decision_basis` mentioning official provider source
and purchase/enrollment authorization; candidate options require
candidate-owned evidence and publication review. All expected signals start
with `bounded hypothesis`.

- [ ] **Step 5: Verify GREEN, mutation resistance, and conformance**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/professional-growth-coach/scripts \
  python3 -B -m unittest \
  tests.test_learning_option_research \
  tests.test_career_market_learning_dossier_v2 \
  tests.test_career_market_learning_dossier \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py -v
git diff --check
```

- [ ] **Step 6: Commit Task 2**

```bash
git add \
  plugins/professional-growth-coach/schemas/career-market-learning-dossier-v2.schema.json \
  plugins/professional-growth-coach/scripts/build_career_market_learning_dossier_v2.py \
  plugins/professional-growth-coach/scripts/validate_career_market_learning_dossier_v2.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  tests/evals/with-skill/fixtures/career-market-learning-dossier-v2 \
  tests/test_career_market_learning_dossier_v2.py
git commit -m "feat: decide learning from recurring gaps"
```

---

### Task 3: Integrate learning ROI into the private dossier experience

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`
- Modify: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v3.py`
- Modify: `plugins/professional-growth-coach/assets/career-market-learning-dossier-v1.css`
- Modify: `.superdesign/init/theme.md`
- Modify: `.superdesign/design-system.md`
- Modify: `tests/test_executive_career_dossier_v2.py`
- Modify: `tests/test_executive_career_dossier_v3.py`
- Modify: `tests/test_dark_mode_accessibility.py`
- Modify: `tests/test_print_continuity_footer_integrity.py`
- Modify: `tests/test_superdesign_theme_asset_parity.py`

**Interfaces:**
- Extends market composition to accept market-learning v1 or v2; v1 preserves the not-evaluated placeholder, v2 renders decisions.

- [ ] **Step 1: Write renderer RED tests**

Assert one named learning ROI region after recurring gaps; three through five
ranked decision rows; one coach decision; provider details with current/unknown
fields; project-first five-day sprint and three asset reuse rows when present;
fixed outcome/action boundaries; no duplicate market scores/matrix/priorities;
no purchase/enroll/apply controls; escaped source text; no internal IDs,
snapshots, candidate ID, raw vacancy/provider content, or unverified Mexico
eligibility. EN/ES, v2/v3 executive dossier, market v1 placeholder, market v2
evaluated, limited sample, and no-market states all receive tests.

- [ ] **Step 2: Observe RED**

```bash
PYTHONDWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v2 \
  tests.test_executive_career_dossier_v3 -v
```

- [ ] **Step 3: Implement validated learning composition**

Load the v2 market-learning validator only for v2 input; preserve v1 path.
Require exact executive dossier/market snapshots and matching locale/date.
Render a decision table/card sequence with fixed localized field labels. Keep
provider unknowns explicit, one proof alternative per paid option, and the
coach decision before options. Render project sprint/reuse maps only when the
validated decision requires them. Never create an interactive purchase or
publication affordance.

- [ ] **Step 4: Add responsive/print/contrast and Superdesign parity**

Use existing dossier tokens, semantic table/list/section structures, visible
text labels, and no color-only status. Mobile stacks decision/provider fields;
print keeps decision plus source/boundary together. Forced-colors uses system
colors. Update exact CSS dump and accessibility/print tests.

- [ ] **Step 5: Verify focused UI, privacy, and compatibility gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_career_market_learning_dossier_v2 \
  tests.test_executive_career_dossier_v2 \
  tests.test_executive_career_dossier_v3 \
  tests.test_dark_mode_accessibility \
  tests.test_print_continuity_footer_integrity \
  tests.test_superdesign_theme_asset_parity \
  tests.test_repository_privacy -v
git diff --check
```

Render complete/limited EN/ES to private temp paths. Assert unique IDs, zero
missing ARIA references, no remote resources/handlers, no duplicate metrics or
scores, one H1/main/footer, and mode 0600.

- [ ] **Step 6: Commit Task 3**

```bash
git add \
  .superdesign/design-system.md \
  .superdesign/init/theme.md \
  plugins/professional-growth-coach/assets/career-market-learning-dossier-v1.css \
  plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py \
  plugins/professional-growth-coach/scripts/render_executive_career_dossier_v3.py \
  tests/test_dark_mode_accessibility.py \
  tests/test_executive_career_dossier_v2.py \
  tests/test_executive_career_dossier_v3.py \
  tests/test_print_continuity_footer_integrity.py \
  tests/test_superdesign_theme_asset_parity.py
git commit -m "feat: render recurring-gap learning decisions"
```

---

### Task 4: Default routing, release, current provider research, and live artifact

**Files:**
- Modify: `plugins/professional-growth-coach/skills/recommend-career-learning/SKILL.md`
- Modify: `plugins/professional-growth-coach/skills/recommend-career-learning/references/learning-roi.md`
- Modify: `plugins/professional-growth-coach/skills/recommend-career-learning/references/evidence-projects.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/SKILL.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/references/html-dossier.md`
- Modify: `plugins/professional-growth-coach/README.md`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `tests/test_repository_privacy.py`
- Modify: `tests/test_skill_contracts.py`
- Modify once: `plugins/professional-growth-coach/.codex-plugin/plugin.json` through cachebuster.
- Modify mechanically: `tests/evals/final/cycle-1/*.json`, `tests/evals/final/cycle-2/*.json`, `tests/evals/final/cycle-1.md`, `tests/evals/final/cycle-2.md`, and `tests/evals/final/installed-smoke-test.md`.
- Create ignored evidence: `.superpowers/sdd/2026-08-13-recurring-gap-learning-roi/task-4-report.md`.

**Interfaces:**
- Produces current official provider research, validated ROI decisions, installed local plugin, and one private client artifact.

- [ ] **Step 1: Add RED routing/package/privacy tests**

Require strict-majority recurrence, current official provider sources, unknown
commercial fields preserved, project/proof comparison, no certificate-as-
experience substitution, budget/time gate, exact action authorization, market
snapshot binding, package inventory, private diagnostics, and no external
action. Observe RED in full-plugin/structure/privacy/skill suites.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_full_plugin \
  tests.test_plugin_structure \
  tests.test_repository_privacy \
  tests.test_skill_contracts -v
```

- [ ] **Step 2: Update skill orchestration and static checks**

After market validation, research official university/vendor/platform pages for
options tied to recurring learnable gaps. Always include a project/lab/no-
learning alternative. Build/validate learning v2 and compose it into the
private dossier. If sources, recurrence, budget, or time are insufficient,
render `consider`, `pause`, `project_first`, or `not_needed` rather than a paid
recommendation. Extend package/static/privacy checks without weakening prior
contracts.

- [ ] **Step 3: Run full pre-cachebuster gates and independent reviews**

Run focused learning/market/dossier, full plugin, static, privacy, release,
full root, descriptor, design parity, dark/forced-colors, and print suites on
default Python and CPython 3.11. Resolve all Critical/Important findings.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_learning_option_research \
  tests.test_career_market_learning_dossier_v2 \
  tests.test_career_market_learning_dossier \
  tests.test_executive_career_dossier_v2 \
  tests.test_executive_career_dossier_v3 \
  tests.test_full_plugin \
  tests.test_plugin_structure \
  tests.test_repository_privacy \
  tests.test_skill_contracts \
  tests.test_superdesign_theme_asset_parity \
  tests.test_dark_mode_accessibility \
  tests.test_print_continuity_footer_integrity \
  tests.test_private_asset_boundary -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s plugins/professional-growth-coach/tests -p 'test_*.py' -q
python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
python3 -B scripts/check_repository_privacy.py
scripts/run_release_validation.sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s tests -p 'test_*.py' -q
git diff --check
```

Repeat the focused learning/market/dossier and plugin suites with
`/Users/kevinriosferrer/.local/bin/python3.11` when present. Only the known
stale final-eval provenance assertions are permitted before release.

- [ ] **Step 4: Cachebust once, install, attest, rerun, and publish**

Use the official update script exactly once:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  /Users/kevinriosferrer/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py \
  plugins/professional-growth-coach
git add plugins/professional-growth-coach/.codex-plugin/plugin.json
git commit -m "chore: bump learning roi cachebuster"
```

Install the exact local version using the established marketplace command.
Require the local identity/version in `codex plugin list --json`, silent
`diff -qr --exclude='__pycache__'`, equal normalized file sets/counts, and
equal path-plus-file-SHA256 hashes. Rebind the 12 cycle JSONs, two indexes, and
installed smoke to the cachebuster commit/tree, then run:

```bash
git add tests/evals/final
git commit -m "test: attest learning roi installation"
python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
python3 -B scripts/check_repository_privacy.py
scripts/run_release_validation.sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s plugins/professional-growth-coach/tests -p 'test_*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s tests -p 'test_*.py' -q
git diff --check
git status --short --branch
```

Recheck source/cache parity after attestation. Integrate into local `main`
without rewriting history, push under the user's standing increment-publication
authorization, and require `git rev-parse HEAD` equals
`git rev-parse origin/main`. If default-branch policy rejects the push, do not
retry or work around it. Never modify the public identity.

- [ ] **Step 5: Execute current provider research and live private report**

Using the actual validated recurring gaps, open current official provider
sources. Verify every available cost/duration/prerequisite/renewal/maintenance/
availability/geography field or mark it unknown. Do not purchase or enroll.
Build the learning artifact and generate the first collision-safe private HTML
without overwriting prior reports.

- [ ] **Step 6: Empirical and structural QA**

Inspect the actual report in supported Codex Browser or a closed loopback-only
server for desktop, 320px/200%, print, dark, forced-colors, keyboard/AT,
grayscale, labels, overlap, clipping, no duplication, and action boundaries.
Run DOM/ARIA/privacy/source checks regardless; report unverified items honestly.

- [ ] **Step 7: Record release/live evidence**

Write the ignored report with commits, exact version/tree/hash/counts, tests,
installed parity, provider source state counts, recurring-gap denominators,
decision types, unknown fields, artifact path/mode, ref status, dual-identity
caveat, and empirical QA status—without copying private inputs or raw records.
