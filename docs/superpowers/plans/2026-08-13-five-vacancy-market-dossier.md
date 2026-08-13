# Five-Vacancy Market Dossier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Research and validate up to five current SRE, Platform Engineering, or DevOps vacancies for Mexico or a stated remote arrangement, compute reproducible candidate-evidence alignment and actual-sample recurrence, and compose accessible charts and a five-column matrix into the existing private LinkedIn dossier v2.

**Architecture:** Keep current-market evidence separate from the LinkedIn profile contract. A closed `target-vacancy-research-v1` artifact records active sources, employer qualification, posting identity, requirements, and unknown eligibility gates. A pure builder combines that validated research with a closed identity-free signal-binding input and an already-valid executive dossier v2, computes all scores and recurrence, and emits `career-market-learning-dossier-v1` with `learning_state=not_evaluated`; the v2 renderer accepts this second validated artifact as an optional composition input and never recomputes it.

**Tech Stack:** Python 3.11+, standard library only, JSON Schema draft 2020-12 subset, `unittest`, dependency-free offline HTML/CSS, existing descriptor-boundary loaders and private writers, native `<progress>`, semantic tables, Superdesign byte-parity checks, Codex plugin release tooling.

## Global Constraints

- A complete market sample contains exactly five active unique postings; the artifact admits at most five postings.
- A limited sample contains exactly one through four active unique postings and remains scoreable; zero postings produces `market_evidence_unavailable` and no scores or recurrence.
- Search five distinct objectively qualified employers first. A second genuinely different posting from one employer is allowed only after the bounded distinct-employer search is exhausted and the limitation is recorded.
- Source priority is official employer page, employer-operated ATS, then explicitly labelled LinkedIn Jobs backup. Search snippets, cached previews, other aggregators, stale, expired, inaccessible, redirected-to-search, or incompatible postings never enter the sample.
- Every included posting records an access date and is confirmed active on that date. Unknown publication date remains explicit and never becomes a recent-publication claim.
- Do not infer work authorization, internal mobility, relocation, Mexico eligibility, contractor/EOR availability, tax eligibility, or remote compatibility. Every unresolved gate is `unknown` and is not a candidate deficit.
- Recurrence is exactly `k/N`, where `N` is the real included sample size. It is never described as broad labor-market demand.
- Candidate support states are `verified_match`, `candidate_reported_match`, `adjacent_evidence`, `explicit_gap`, and `unknown`. Unknown never becomes absence.
- Score weights are `must_have=2`, `preferred=1`, and `responsibility_only=0`; factors are `2/2`, `2/2`, `1/2`, `0/2`, and `0/2` respectively. All arithmetic is integer and reproducible.
- Market evidence never changes the seven-dimension LinkedIn profile score.
- This increment does not recommend a paid course or certification. It emits `learning_state=not_evaluated`; the separately planned learning increment consumes recurring gaps.
- V1 and the first-increment v2 schema, validation, fixtures, rendering without a market artifact, and CLI behavior remain valid.
- No candidate identity, profile URL, contact value, private analytics value, raw profile text, raw vacancy dump, local path, source snapshot digest, internal ID, or eligibility inference appears in visible HTML or diagnostics.
- No remote asset, chart library, CDN, SVG, canvas, JavaScript chart, form, external action, application, message, connection, enrollment, or relaxed CSP.
- Complete-state matrix has five vacancy columns. Limited state has exactly `N` columns with no empty padding. Desktop, mobile, print, grayscale, forced-colors, dark, and reduced-motion contracts remain accessible without color or horizontal scrolling as the only access method.
- Run the official cachebuster exactly once, only after every non-provenance gate is green; then install, prove source/cache parity, refresh provenance, rerun all gates, publish, and verify refs.
- Leave `professional-growth-coach@codex-marketplace-public` unchanged and disclose the dual-enabled-identity caveat.

---

### Task 1: Closed five-vacancy research contract

**Files:**
- Create: `plugins/professional-growth-coach/schemas/target-vacancy-research-v1.schema.json`
- Create: `plugins/professional-growth-coach/scripts/validate_target_vacancy_research.py`
- Create: `tests/test_target_vacancy_research.py`
- Create: `tests/evals/with-skill/fixtures/target-vacancy-research/complete-five-es.json`
- Create: `tests/evals/with-skill/fixtures/target-vacancy-research/limited-four-en.json`
- Create: `tests/evals/with-skill/fixtures/target-vacancy-research/unavailable-es.json`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

**Interfaces:**
- Produces: `validate_research(value: object) -> list[str]`, `load_research(path: Path) -> dict[str, object]`, `canonical_research_snapshot(value: Mapping[str, object]) -> str`, `snapshot_for_market_dossier(value: Mapping[str, object]) -> str`, and `_cli(argv: list[str] | None = None) -> int`.
- Produces vacancy IDs `V-001` through `V-005`, employer IDs `EMP-001` through `EMP-005`, and requirement IDs matching `^V-[0-9]{3}-R-[0-9]{2}$`.
- Produces normalized signal keys matching `^[a-z][a-z0-9_]{1,63}$`.

- [ ] **Step 1: Write RED tests for the three sample states**

Create table-driven tests with these exact state/count pairs:

```python
STATE_COUNTS = {
    "complete": {5},
    "limited_market_evidence": {1, 2, 3, 4},
    "market_evidence_unavailable": {0},
}
```

Build synthetic identity-free fixtures with `Fixture Employer A` through
`Fixture Employer E` and `https://example.com/careers/...` test URLs. Mark the
fixtures as test data in comments and never reuse their companies, jobs, or
URLs as real market evidence.

Assert complete input has five unique vacancy IDs and fingerprints, limited
input has four, unavailable has zero, and all validate only after the new
validator exists. Assert that `as_of_date` equals every included vacancy
`access_date`.

- [ ] **Step 2: Run the focused tests and observe RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_target_vacancy_research -v
```

Expected: import failure because `validate_target_vacancy_research.py` does not
exist.

- [ ] **Step 3: Add adversarial source, duplicate, and eligibility tests**

Add tests that reject:

- six vacancies, five vacancies in limited state, and four in complete state;
- duplicate vacancy ID, duplicate fingerprint, duplicate requirement ID, and
  duplicate requirement signal within one vacancy;
- a repeated employer unless
  `distinct_employer_search_exhausted=true` and the fingerprints differ;
- `source_state` other than `active` for an included vacancy;
- access date different from `as_of_date`, future publication date, and a
  publication date labelled current without an actual date;
- `linkedin_jobs_backup` whose host is not `linkedin.com` or whose path does
  not begin `/jobs/`;
- an official/ATS source that points to LinkedIn, localhost, a private IP,
  credentials-in-URL, non-HTTPS, or a local path;
- `target_reached` with fewer than five postings;
- `distinct_employer_search_exhausted=false` when employer IDs repeat;
- any eligibility value other than `pass`, `blocked`, or `unknown`;
- an `unknown` gate containing an inferred pass/eligibility conclusion;
- raw vacancy HTML, script markup, candidate identity/contact, control
  characters, or additional properties.

All diagnostics are fixed, one bounded block of at most 16 KiB, never echo an
untrusted company/title/URL/path/key, and never include a traceback.

- [ ] **Step 4: Create the closed schema**

Use these top-level fields exactly:

```json
{
  "schema_version": "target-vacancy-research-v1",
  "research_kind": "sre_platform_devops_current_vacancies",
  "locale": "es",
  "as_of_date": "2026-08-13",
  "search_scope": {
    "geography_scope": "mexico_or_stated_remote",
    "target_role_families": ["site_reliability_engineering", "platform_engineering", "devops_engineering"],
    "maximum_vacancies": 5,
    "distinct_employers_preferred": true,
    "official_sources_first": true,
    "linkedin_jobs_backup_allowed": true,
    "no_eligibility_inference": true
  },
  "state": "complete",
  "search_limit": {
    "bounded_queries_run": 12,
    "limit_reason": "target_reached",
    "distinct_employer_search_exhausted": false,
    "limitation": "none"
  },
  "employers": [],
  "vacancies": [],
  "privacy_boundary": "public_vacancy_sources_and_identity_free_candidate_evidence_only",
  "no_external_action": true
}
```

Close every object. Employer records require `employer_id`, `display_name`,
`qualification_type=official_headcount|official_index_membership`,
`qualification_observation`, `official_source_title`, `official_source_url`,
`source_date`, and `access_date`. Vacancy records require `vacancy_id`,
`duplicate_fingerprint`, `employer_id`, `title`, `role_family`, `location`,
`arrangement=onsite|hybrid|remote|flexible`,
`geographic_compatibility=explicit_mexico|stated_remote_unknown_eligibility`,
`source_kind=official_employer|employer_operated_ats|linkedin_jobs_backup`,
`source_url`, `official_referrer_url` nullable, `source_state=active`,
`access_date`, `publication_date` nullable, `freshness_status=current|unknown`,
`eligibility_gates`, and one through 30 `requirements`.

Each requirement requires `requirement_id`, `signal`,
`importance=must_have|preferred|responsibility_only`, and a bounded
`source_paraphrase`. Each eligibility gate requires
`gate=work_authorization|country_geography|work_arrangement|language|seniority|experience_floor|employment_arrangement`,
`state=pass|blocked|unknown`, and a bounded factual `observed_condition`.

- [ ] **Step 5: Implement semantic validation and snapshot binding**

Follow `validate_executive_career_dossier_v2.py` for dynamic sibling imports,
descriptor-boundary reads, duplicate-key rejection, depth 12, 256 KiB, fixed
diagnostics, `RecursionError` handling, and CLI exit codes.

Implement:

```python
def canonical_research_snapshot(value: Mapping[str, object]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def snapshot_for_market_dossier(value: Mapping[str, object]) -> str:
    return f"snap-market-sha256-{canonical_research_snapshot(value)}"
```

The typed snapshot is the only market-binding value copied into downstream
dossiers; the bare digest remains available for deterministic fixture checks.
Neither value is rendered or echoed. Validate URL
shape with the existing public-HTTPS helper, then add the source-kind hostname
rules. Verify state/count coupling, uniqueness, employer references,
requirement ID prefixes, dates, source state, and the repeated-employer search
flag. Return `sorted(set(errors))` without mutating input.

- [ ] **Step 6: Verify GREEN, schema subset, and compatibility**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/professional-growth-coach/scripts \
  python3 -B -m unittest \
  tests.test_target_vacancy_research \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py -v
git diff --check
```

- [ ] **Step 7: Commit Task 1**

```bash
git add \
  plugins/professional-growth-coach/schemas/target-vacancy-research-v1.schema.json \
  plugins/professional-growth-coach/scripts/validate_target_vacancy_research.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  tests/evals/with-skill/fixtures/target-vacancy-research \
  tests/test_target_vacancy_research.py
git commit -m "feat: validate five-vacancy market research"
```

---

### Task 2: Pure alignment builder and reproducible market snapshot

**Files:**
- Create: `plugins/professional-growth-coach/schemas/candidate-market-alignment-v1.schema.json`
- Create: `plugins/professional-growth-coach/schemas/career-market-learning-dossier-v1.schema.json`
- Create: `plugins/professional-growth-coach/scripts/build_career_market_learning_dossier.py`
- Create: `plugins/professional-growth-coach/scripts/validate_career_market_learning_dossier.py`
- Create: `tests/test_career_market_learning_dossier.py`
- Create: `tests/evals/with-skill/fixtures/career-market-learning-dossier/complete-five-es.json`
- Create: `tests/evals/with-skill/fixtures/career-market-learning-dossier/limited-four-en.json`
- Create: `tests/evals/with-skill/fixtures/career-market-learning-dossier/unavailable-es.json`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

**Interfaces:**
- Consumes: Task 1 `validate_research`, `load_research`, and
  `snapshot_for_market_dossier`; dossier v2 `validate_dossier`; and
  `dossier_snapshot.snapshot_for_dossier(dossier) -> str`.
- Produces: `build_market_dossier(research, executive_dossier, alignment) -> dict[str, object]`, `validate_market_dossier(value) -> list[str]`, and pure integer helpers `alignment_score(requirements, bindings) -> tuple[int, int, int]` and `recurrence_rows(vacancies, bindings) -> list[dict[str, object]]`.

- [ ] **Step 1: Write RED arithmetic and state tests**

Use this exact factor numerator map and two-point denominator:

```python
SUPPORT_NUMERATORS = {
    "verified_match": 2,
    "candidate_reported_match": 2,
    "adjacent_evidence": 1,
    "explicit_gap": 0,
    "unknown": 0,
}
IMPORTANCE_WEIGHTS = {"must_have": 2, "preferred": 1, "responsibility_only": 0}

def rounded_percent(numerator: int, denominator: int) -> int:
    return (100 * numerator + denominator // 2) // denominator
```

Test an exact vacancy with one must-have verified, one must-have adjacent, one
preferred unknown, and one responsibility-only gap. Expected earned points are
`6`, maximum points `10`, evidence-known points `8`, alignment `60`, and
evidence coverage `80`. Changing unknown to explicit gap keeps alignment `60`
and raises coverage to `100`.

Test recurrence over five vacancies as `3/5`, then remove one vacancy and
assert the same three occurrences become `3/4`. Assert no recurrence rows when
`N=0` and no sample-wide score in any state.

- [ ] **Step 2: Observe RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_career_market_learning_dossier -v
```

Expected: missing builder/validator imports.

- [ ] **Step 3: Define the closed alignment input**

`candidate-market-alignment-v1` requires:

```json
{
  "schema_version": "candidate-market-alignment-v1",
  "research_snapshot": "snap-market-sha256-<64 lowercase hex>",
  "executive_dossier_snapshot": "snap-dossier-sha256-<64 lowercase hex>",
  "signal_bindings": [
    {
      "signal": "kubernetes",
      "support_state": "verified_match",
      "evidence_ids": ["E-004"]
    }
  ],
  "privacy_boundary": "identity_free_evidence_references_only"
}
```

Signals are unique and cover every scoreable signal in the research artifact
exactly once. `verified_match`, `candidate_reported_match`, and
`adjacent_evidence` require one or more dossier evidence IDs. `explicit_gap`
requires one or more verified/candidate-reported evidence IDs that explicitly
support the gap. `unknown` requires an empty list. The builder verifies every
ID exists and that its evidence state is compatible; it never derives a match
from prose keywords.

- [ ] **Step 4: Define the derived market dossier**

The closed output carries `schema_version=career-market-learning-dossier-v1`,
locale, as-of date, state, `source_research_snapshot`,
`source_executive_dossier_snapshot`, search summary, ordered vacancy cards,
matrix rows, recurrence rows, `learning_state=not_evaluated`,
`learning_decisions=[]`, methodology boundaries, privacy boundary, and
`no_external_action=true`.

Each vacancy card requires source metadata plus:

```json
{
  "earned_points": 6,
  "maximum_points": 10,
  "known_points": 8,
  "alignment_percent": 60,
  "evidence_coverage_percent": 80,
  "interpretation": "directional_documented_evidence_not_hiring_fit",
  "qualitative_band": "insufficient_evidence"
}
```

`qualitative_band` is `insufficient_evidence` whenever coverage is below 50;
otherwise it is `higher_documented_alignment`, `moderate_documented_alignment`,
or `lower_documented_alignment` using fixed 75/50 cut points. It never says
fit, ATS, probability, or competitiveness.

Matrix rows require one signal binding and exactly `N` ordered cells with
`vacancy_id` and `required=true|false`. Recurrence rows require `signal`,
`occurrences=k`, `sample_size=N`, `display_fraction=k/N`, and the same binding
state. Sort vacancies by `alignment_percent` descending then `vacancy_id`;
matrix cells use that same order. Sort recurrence by occurrences descending,
then signal.

- [ ] **Step 5: Implement the pure builder and independent validator**

Deep-copy inputs. Validate all three inputs first. Verify both snapshots before
using any binding. Calculate every derived number; reject caller-supplied
scores. The output validator recomputes scores, coverage, cell order,
recurrence, state/count coupling, source snapshots, and learning placeholder.
It rejects mutation of any score, denominator, cell, order, or fraction.

The builder must preserve the research source URL and public employer/title
but omit raw source paraphrases from visible-facing card fields. Keep detailed
requirements in the matrix source data, bounded and escaped later.

- [ ] **Step 6: Verify RED-to-GREEN and mutation resistance**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/professional-growth-coach/scripts \
  python3 -B -m unittest \
  tests.test_target_vacancy_research \
  tests.test_career_market_learning_dossier \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py -v
git diff --check
```

Add mutation tests for every calculated field, reordered vacancy/matrix cell,
unknown evidence ID, stale snapshot, mismatched locale/date/state, private
value/control character, and an unhashable/malformed nested value. Every error
is bounded and non-echoing.

- [ ] **Step 7: Commit Task 2**

```bash
git add \
  plugins/professional-growth-coach/schemas/candidate-market-alignment-v1.schema.json \
  plugins/professional-growth-coach/schemas/career-market-learning-dossier-v1.schema.json \
  plugins/professional-growth-coach/scripts/build_career_market_learning_dossier.py \
  plugins/professional-growth-coach/scripts/validate_career_market_learning_dossier.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  tests/evals/with-skill/fixtures/career-market-learning-dossier \
  tests/test_career_market_learning_dossier.py
git commit -m "feat: compute vacancy evidence alignment"
```

---

### Task 3: Compose accessible vacancy charts and matrix into dossier v2

**Files:**
- Create: `plugins/professional-growth-coach/assets/career-market-learning-dossier-v1.css`
- Modify: `plugins/professional-growth-coach/scripts/private_asset_loader.py`
- Modify: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`
- Modify: `plugins/professional-growth-coach/assets/executive-career-dossier-v2.css`
- Modify: `.superdesign/init/theme.md`
- Modify: `.superdesign/design-system.md`
- Modify: `tests/test_executive_career_dossier_v2.py`
- Modify: `tests/test_dark_mode_accessibility.py`
- Modify: `tests/test_print_continuity_footer_integrity.py`
- Modify: `tests/test_private_asset_boundary.py`
- Modify: `tests/test_superdesign_theme_asset_parity.py`

**Interfaces:**
- Consumes: Task 2 validated `career-market-learning-dossier-v1`.
- Extends without breaking: `render_dossier_html(dossier, market_dossier=None) -> str`, `write_dossier_html(dossier_path, output_path, *, market_dossier_path: Path | None = None, force: bool = False) -> RenderReceipt`, and CLI `--market-dossier PATH`.
- Produces HTML classes `.market-summary`, `.vacancy-alignment-card`, `.market-matrix`, `.recurrence-row`, and `.gap-closure-route`.

- [ ] **Step 1: Write renderer RED tests for complete, limited, and unavailable states**

For the complete fixture assert:

- exactly five named `.vacancy-alignment-card` articles sorted by score;
- exactly five `<progress max="100">` elements inside the market region, each
  labelled by company/title plus visible `N de 100` / `N out of 100` text;
- one semantic matrix table with `Signal`, `Profile evidence`, and exactly five
  vacancy column headers `V1` through `V5`;
- a visible key mapping V1–V5 to full employer and role labels;
- every matrix cell has visible state text, a `data-label`, and no
  color-only meaning;
- each recurrence row shows exact `k/N`, never `market demand`;
- one four-stage gap route and no duplicated coach-priority paragraphs;
- no course/certification recommendation while
  `learning_state=not_evaluated`.

For limited four, assert four cards/progress/columns, `N=4`, one limitation,
and no empty V5. For unavailable, retain the existing one placeholder and
render zero market progress elements, matrix rows, percentages, or learning
copy.

- [ ] **Step 2: Observe RED without changing existing no-market behavior**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v2.ExecutiveCareerDossierV2RendererTests -v
```

Expected: new market-composition tests fail while existing placeholder tests
remain green.

- [ ] **Step 3: Implement validated optional composition**

Load the market validator by sibling path. Validate and deep-freeze the market
artifact independently. Require locale and `evidence_as_of/as_of_date` match,
and require `source_executive_dossier_snapshot` to match the exact v2 dossier.
If no market artifact is supplied, preserve current bytes and placeholder.

Replace only `_render_market_evidence_unavailable(locale)` with
`_render_market_context(market_dossier, locale)`. Use `html.escape` for all
display fields. Never render source snapshot strings, internal IDs, raw
requirement paraphrases, or eligibility conclusions beyond the validated fixed
gate labels.

The CLI accepts optional `--market-dossier PATH`; both inputs use existing
bounded no-follow loaders and one repair maximum. The receipt remains one JSON
line, one absolute HTML path, 0600 output, and no overwrite without `--force`.

- [ ] **Step 4: Render semantic zero-based charts and matrix**

Use native progress for vacancy alignment. The visible score text is the only
percentage repetition and serves as the progress label; do not add a second
score table. The matrix is the detailed explanation.

Use these exact text states:

```python
MATRIX_STATE_COPY = {
    "verified_match": ("✓", "Evidencia directa", "Direct evidence"),
    "candidate_reported_match": ("●", "Reportado por cliente", "Candidate reported"),
    "adjacent_evidence": ("≈", "Evidencia adyacente", "Adjacent evidence"),
    "explicit_gap": ("!", "Brecha confirmada", "Confirmed gap"),
    "unknown": ("?", "No verificado", "Not verified"),
    "not_required": ("—", "No solicitado", "Not requested"),
}
```

Matrix headers stay short (`V1`–`V5`); the adjacent ordered key contains full
employer/title labels. Mobile cell `data-label` combines the short key and full
label. Recurrence rows use `progress value=k max=N` plus visible `k/N` text and
the fixed sample-only boundary.

- [ ] **Step 5: Add responsive, print, contrast, and parity contracts**

Use only existing dossier tokens. At desktop, use a fixed-layout semantic table
with short headers and bounded wrapping. At `max-width: 680px`, keep table
semantics in DOM but visually stack each row and expose `data-label` before
each cell; do not use `overflow-x:auto`, `min-width` wider than the viewport,
or `white-space:nowrap` as the only access path.

Print keeps the vacancy key with the matrix, uses compact readable type, repeats
table headers when the user agent supports it, and applies `break-inside:avoid`
to vacancy cards and recurrence rows. Forced-colors uses Canvas, CanvasText,
and Highlight; text/symbols remain sufficient in grayscale. Add exact CSS bytes
to Superdesign theme parity and update the design-system contract.

- [ ] **Step 6: Verify DOM, calculations, v1/v2 compatibility, and private output**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v2 \
  tests.test_career_market_learning_dossier \
  tests.test_dark_mode_accessibility \
  tests.test_print_continuity_footer_integrity \
  tests.test_private_asset_boundary \
  tests.test_superdesign_theme_asset_parity -v
git diff --check
```

Render EN/ES complete and limited fixtures to a temporary private directory.
Assert one H1/main/footer, unique IDs, zero missing ARIA references, exact
card/column counts, no horizontal-scroll CSS contract, no remote resources,
no inline event handlers, no duplicate score block, and mode 0600. Record that
browser/AT QA is still unverified unless actually run.

- [ ] **Step 7: Commit Task 3**

```bash
git add \
  .superdesign/design-system.md \
  .superdesign/init/theme.md \
  plugins/professional-growth-coach/assets/career-market-learning-dossier-v1.css \
  plugins/professional-growth-coach/assets/executive-career-dossier-v2.css \
  plugins/professional-growth-coach/scripts/private_asset_loader.py \
  plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py \
  tests/test_dark_mode_accessibility.py \
  tests/test_executive_career_dossier_v2.py \
  tests/test_print_continuity_footer_integrity.py \
  tests/test_private_asset_boundary.py \
  tests/test_superdesign_theme_asset_parity.py
git commit -m "feat: visualize five-vacancy evidence alignment"
```

---

### Task 4: Default live research routing and package/security gates

**Files:**
- Modify: `plugins/professional-growth-coach/skills/research-professional-market/SKILL.md`
- Modify: `plugins/professional-growth-coach/skills/research-professional-market/references/source-policy.md`
- Modify: `plugins/professional-growth-coach/skills/research-professional-market/references/market-brief.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/SKILL.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/references/html-dossier.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/references/profile-audit.md`
- Modify: `plugins/professional-growth-coach/README.md`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `tests/test_repository_privacy.py`
- Modify: `tests/test_skill_contracts.py`

**Interfaces:**
- Consumes: Tasks 1–3 validators, builder, fixtures, and renderer.
- Produces: default read-only search of five current vacancies, bounded fallback, exact source state, and a composed private dossier with no external action.

- [ ] **Step 1: Write RED skill and package tests**

Assert executable/static contracts require:

1. default target families SRE, Platform Engineering, and DevOps;
2. Mexico or stated remote scope;
3. target and maximum of five postings;
4. five distinct employers searched first;
5. official employer/ATS sources first and LinkedIn Jobs backup only;
6. active verification and access date per included posting;
7. limited `1..4` and unavailable `0` behavior with no padding;
8. actual-sample `k/N` recurrence;
9. no work-authorization, internal-mobility, EOR, or remote-eligibility
   inference;
10. no apply, message, connect, follow, publish, enroll, or purchase action;
11. the market artifact passed to v2 renderer through `--market-dossier`;
12. `learning_state=not_evaluated` until the next increment.

Extend package inventories for the two schemas, three scripts, CSS, and six
fixtures. Add privacy negative controls for company/title/URL HTML injection,
local/private URLs, candidate identity, raw vacancy text, snapshot leakage,
unbounded diagnostics, symlinks, FIFOs, oversize input, duplicate keys,
recursion, and invalid UTF-8.

- [ ] **Step 2: Observe RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_full_plugin \
  tests.test_plugin_structure \
  tests.test_skill_contracts \
  tests.test_repository_privacy -v
```

Expected: new package and default-five contracts fail.

- [ ] **Step 3: Update research and profile orchestration**

Document that every live run browses current sources at generation time. The
skill first attempts official employer and employer-operated ATS pages, then
may use an inspectable active LinkedIn Jobs posting as an explicitly labelled
backup. A result snippet never becomes evidence.

The profile skill renders supported profile findings first, runs the bounded
five-vacancy research, builds the identity-free alignment input from validated
dossier evidence, validates the market artifact, and composes it into a new
collision-safe dossier v2 path. If the market run fails, preserve the valid
profile dossier with limited/unavailable market state and one bounded reason.

Keep inspection read-only. Browser session access never authorizes profile
editing, networking expansion, recruiter messaging, applying, or retention of
cookies/session data. Do not write real company/vacancy/course values into the
skill source.

- [ ] **Step 4: Extend static, privacy, and package validation**

Require every new file as a regular non-link package path. Parse both schemas;
validate all fixtures; run validators/builders/renderers; verify offline CSP,
one style/script boundary, no remote assets, 0600 writer, source URL rules,
snapshot non-disclosure, and v1/no-market v2 compatibility. Do not weaken any
existing v1 or first-increment v2 check.

- [ ] **Step 5: Run all non-provenance gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_target_vacancy_research \
  tests.test_career_market_learning_dossier \
  tests.test_executive_career_dossier_v2 \
  tests.test_full_plugin \
  tests.test_plugin_structure \
  tests.test_repository_privacy \
  tests.test_skill_contracts \
  tests.test_superdesign_theme_asset_parity \
  tests.test_dark_mode_accessibility \
  tests.test_print_continuity_footer_integrity -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s plugins/professional-growth-coach/tests -p 'test_*.py' -q
python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
python3 -B scripts/check_repository_privacy.py
scripts/run_release_validation.sh
git diff --check
```

Only stale final-eval provenance assertions may remain before release.

- [ ] **Step 6: Commit Task 4**

```bash
git add \
  plugins/professional-growth-coach/README.md \
  plugins/professional-growth-coach/skills/research-professional-market \
  plugins/professional-growth-coach/skills/optimize-professional-profile/SKILL.md \
  plugins/professional-growth-coach/skills/optimize-professional-profile/references/html-dossier.md \
  plugins/professional-growth-coach/skills/optimize-professional-profile/references/profile-audit.md \
  plugins/professional-growth-coach/tests/run_static_checks.py \
  tests/test_full_plugin.py \
  tests/test_plugin_structure.py \
  tests/test_repository_privacy.py \
  tests/test_skill_contracts.py
git commit -m "feat: research five vacancies by default"
```

---

### Task 5: Independent review, release, install, provenance, and publication

**Files:**
- Modify once: `plugins/professional-growth-coach/.codex-plugin/plugin.json` through the official cachebuster.
- Modify mechanically: `tests/evals/final/cycle-1/*.json`, `tests/evals/final/cycle-2/*.json`, `tests/evals/final/cycle-1.md`, `tests/evals/final/cycle-2.md`, and `tests/evals/final/installed-smoke-test.md`.
- Create ignored evidence: `.superpowers/sdd/2026-08-13-five-vacancy-market-dossier/task-5-report.md`.

**Interfaces:**
- Consumes: reviewed Tasks 1–4 and `professional-growth-coach-local`.
- Produces: one exact installed version, source/cache parity/hash, current provenance, full gate evidence, and synchronized published refs.

- [ ] **Step 1: Run final pre-cachebuster evidence and independent reviews**

Run every Task 4 gate plus full root discovery. Also run the focused market,
renderer, descriptor-boundary, and privacy suites under
`/Users/kevinriosferrer/.local/bin/python3.11` when present. Dispatch one
task-scoped reviewer per task and one most-capable whole-increment reviewer.
Resolve every Critical/Important finding through the bounded fix loop.

- [ ] **Step 2: Run empirical visual QA when the browser supports it**

Generate complete-five ES, complete-five EN, and limited-four HTML artifacts in
a private temporary directory. Inspect desktop, 320px/200% zoom, print preview,
dark, forced-colors, keyboard order, labels, overlap, clipping, matrix reading,
and grayscale/non-color meaning. Record each as verified or unverified; never
turn static CSS assertions into visual claims.

- [ ] **Step 3: Consume the official cachebuster exactly once**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  /Users/kevinriosferrer/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py \
  plugins/professional-growth-coach
git add plugins/professional-growth-coach/.codex-plugin/plugin.json
git commit -m "chore: bump five-vacancy market cachebuster"
```

Record that commit and its plugin tree as provenance.

- [ ] **Step 4: Install exact local version and prove parity**

Use the established local marketplace install command. Verify enabled identity
and exact version with `codex plugin list --json`. Require silent
`diff -qr --exclude='__pycache__'`, identical normalized file sets/counts, and
equal path-plus-file-SHA256 inventory hashes between source and installed cache.

- [ ] **Step 5: Rebind provenance and installed smoke**

Update all 12 cycle JSONs, both cycle indexes, and installed smoke to the
cachebuster source commit/tree. Record exact version, timestamp, counts, hash,
source/cache equivalence, installed research validator, builder, complete and
limited renderer smokes, and the dual-enabled-identity caveat. Keep
`fresh_agent_smoke=not_run` unless a genuinely new task proves the callable
local identity.

- [ ] **Step 6: Commit attestation and rerun every gate fresh**

```bash
git add tests/evals/final
git commit -m "test: attest five-vacancy market installation"
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

Recheck installed parity after attestation; provenance files are outside the
plugin and must not change its tree.

- [ ] **Step 7: Publish and verify refs**

Integrate the reviewed feature branch into local `main` without rewriting
history. With the user's standing authorization to publish each increment,
push `main`, then require `git rev-parse HEAD` and `git rev-parse origin/main`
to match. If policy rejects the default-branch mutation, do not retry or work
around it; preserve the verified local installation and report the blocker.

- [ ] **Step 8: Record release evidence**

Write the ignored report with commit IDs, version, source/tree, file counts,
normalized hash, all exact test counts and exit codes, installed smokes, ref
status, dual-identity caveat, and empirical browser/AT status.

---

### Task 6: Live five-vacancy research and first private client artifact

**Files:**
- Create privately and outside git: first collision-safe artifacts under `.professional-growth-coach-artifacts/` in the canonical source checkout.
- Create ignored evidence: `.superpowers/sdd/2026-08-13-five-vacancy-market-dossier/task-6-report.md`.

**Interfaces:**
- Consumes: the installed reviewed plugin, the existing validated private dossier input for the user, authenticated read-only LinkedIn access only if evidence needed for profile or LinkedIn Jobs backup is unavailable elsewhere, and public current employer sources.
- Produces: private research JSON, candidate-market alignment JSON, market dossier JSON, and one composed dossier v2 HTML path; none are committed.

- [ ] **Step 1: Reconfirm the live-run boundary**

Use the authorization already supplied for read-only profile and aggregate
analytics inspection. Do not open messages or visitor identities, retain raw
records, edit the profile, expand the network, connect, follow, message, apply,
or publish. If a new external action becomes desirable, stop and obtain exact
target-and-action authorization.

- [ ] **Step 2: Revalidate the candidate evidence input**

Use the installed v2 validator. Resolve any pending section inspection one
section at a time only through an explicit current-conversation answer. Preserve
unknowns and render the partial dossier immediately rather than filling gaps
from memory.

- [ ] **Step 3: Execute the bounded current-market search**

Search official employer and employer-operated ATS pages first for current SRE,
Platform Engineering, or DevOps roles in Mexico or a stated remote arrangement.
Attempt five distinct qualified employers. Use LinkedIn Jobs only as labelled
backup. Open every included posting on the run date, record access date, reject
expired/inaccessible/duplicate/incompatible postings, and stop at five or the
documented bounded-search limit.

- [ ] **Step 4: Normalize, bind, calculate, and validate**

Create identity-free structured inputs; do not copy raw vacancy prose. Verify
candidate evidence state for every signal, keep unresolved evidence and
eligibility `unknown`, run both validators and the pure builder, and confirm all
scores and recurrence reproduce from normalized inputs.

- [ ] **Step 5: Render the first collision-safe private artifact**

Never overwrite the user's prior report. Write the first available generic
name in the canonical source checkout's artifact directory with mode 0600.
Return only its absolute local link plus a bounded summary; do not expose the
profile URL, source snapshots, internal IDs, or raw evidence.

- [ ] **Step 6: Perform empirical and structural QA**

Open the generated HTML in Codex Browser when local-file access is supported;
otherwise serve only the private temporary artifact through a loopback-only
local server and close it after QA. Check desktop, 320px/200% zoom, print,
dark, forced-colors, keyboard focus, labels, clipping, overlap, grayscale,
matrix reading, and no duplicate analysis. Run DOM/ARIA/source/privacy checks
regardless. Record browser/AT items honestly as verified or unverified.

- [ ] **Step 7: Record the live evidence limits**

Write the ignored report with the verified vacancy count, unique-employer
count, source-kind counts, access date, duplicate/expired exclusion count,
actual recurrence denominator, validation commands, artifact mode/path, visual
QA evidence, and all unknown eligibility or source limitations. Do not retain
raw LinkedIn/session/browser data in the report.
