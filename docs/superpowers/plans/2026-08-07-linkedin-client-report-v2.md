# LinkedIn Client Report v2 Implementation Plan

> Synthetic example provenance: `no_real_profile_mapping`; legacy identity literals are prohibited.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `optimize-linkedin-career` deliver a concise, evidence-backed Markdown diagnostic before any technical appendix, with deterministic validation against synthetic, privacy-safe cases.

**Architecture:** The plugin is declarative, so the production renderer is the skill instruction plus `client-report.md`; do not add a prose-generating Python runtime that Codex never calls. Add one standard-library Python validator that parses the actual Markdown delivery, validates its synthetic evidence bundle, and is reused by the static checker and a CLI. Preserve the existing semicolon contracts as a legacy full appendix for `debug`, `eval`, or explicit detail requests.

**Tech Stack:** Agent Skills Markdown, Markdown report fixtures, JSON synthetic fixture bundles, Python 3 standard library, `unittest`, existing Codex plugin manifest and local marketplace.

## Global Constraints

- `client_report` starts at byte 0 with a localized H1 and ends immediately before the first localized evidence-appendix H2.
- The client report contains exactly eight ordered sections; normal mode appends only a compact appendix index.
- The client report is at most 800 words excluding its score table; the normal appendix is at most 250 words; the complete normal payload is at most 1,100 words.
- The client report contains zero `candidate_id=`, `linkedin_*=`, or canonical semicolon-delimited rows.
- Debug/eval output starts with the same client report and may expose canonical rows only after the appendix boundary; its internal candidate ID must match the bundle.
- The score table covers exactly seven dimensions. Unavailable visual evidence is `No evaluado`/`Not scored`, excluded from the denominator, and never converted to zero.
- The visible score derives from the existing weighted ledger with half-up integer rounding; it is not LinkedIn Job Match, recruiter ranking, or an outcome probability.
- Exactly three priorities and three copy blocks are required. Each links to evidence IDs and a concrete boundary; copy states are `listo|requiere confirmación|omitir` or their English equivalents.
- Unverified technology may appear in a confirmation question or coach rationale, never as visible candidate experience or a ready skill claim.
- Fixtures are synthetic, composite, counterfactual, and non-mappable. New or modified profile-derived artifacts contain no real name, profile URL, image, raw profile text, analytics value, contact data, or singularizable real-profile combination.
- Official source URLs are allowed only in the source catalog. Package author metadata and unmistakably synthetic negative-test sentinels remain allowed in their own paths.
- Deterministic gates are blocking. Any AI quality grader is advisory and cannot override a deterministic failure.
- Source freshness is computed from a fixture `evaluation_date`, never the system clock; age 90 days is current and age 91 days is stale.
- No LinkedIn edit, publish, connect, message, application, upload, share, or other external action occurs.
- No new third-party runtime dependency.
- Use strict RED → verify failure → GREEN → verify pass for every production behavior.

---

### Task 1: Define and validate privacy-safe synthetic fixture bundles

**Files:**
- Create: `plugins/job-search-coach/scripts/validate_linkedin_client_report.py`
- Create: `tests/test_linkedin_report_fixtures.py`
- Create: `tests/evals/with-skill/fixtures/linkedin-report-v2/schema.json`
- Create: `tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-a.json`
- Create: `tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-b.json`
- Create: `tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-c.json`
- Create: `tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-d.json`
- Create: `tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-d-banner-only.json`

**Interfaces:**
- Produces: `load_bundle(path: Path) -> dict[str, object]`
- Produces: `validate_fixture_bundle(bundle: object) -> list[str]`
- Produces: closed bundle keys `schema_version`, `fixture_id`, `internal_candidate_id`, `origin_class`, `derivation`, `real_profile_mapping`, `locale`, `evaluation_date`, `evidence_mode`, `structural_state_fixture`, `synthetic_fact_catalog`, `score_ledger`, `priorities`, `copy_blocks`, `blocked_claims`, `source_catalog`, `authorization_state`, and `eval_expectations`.
- Produces: five bundle/fixture IDs—four primary scenarios plus one banner-only D variant—with distinct candidate IDs and no real-profile mapping.

- [ ] **Step 1: Hand-author the five bundle inputs before the first RED**

Create four primary composite fixtures plus the banner-only variant using the case decisions in Step 5 below. Write `schema.json` at the same time. These are independent test inputs; do not use production validator or score functions to generate them. Confirm all five JSON files parse with `python3 -B -m json.tool`. No test may fail because a fixture file is absent.

- [ ] **Step 2: Write fixture tests that name the privacy and schema breaks**

Create tests that import the validator by file path and prove all four hand-authored bundles pass. Add one mutation per failure:

```python
def test_all_four_fixture_bundles_are_valid(self) -> None:
    paths = sorted(FIXTURE_ROOT.glob("scenario-[abcd].json"))
    self.assertEqual(4, len(paths))
    for path in paths:
        self.assertEqual([], validator.validate_fixture_bundle(json.loads(path.read_text())))

def test_banner_only_variant_is_valid_and_has_its_own_ids(self) -> None:
    primary_ids = {
        self.fixture(path.name)["fixture_id"]
        for path in FIXTURE_ROOT.glob("scenario-[abcd].json")
    }
    variant = self.fixture("scenario-d-banner-only.json")
    self.assertEqual([], validator.validate_fixture_bundle(variant))
    self.assertNotIn(variant["fixture_id"], primary_ids)

def test_fixture_rejects_unknown_property(self) -> None:
    bundle = self.fixture("scenario-a.json")
    bundle["profile_name"] = "Synthetic Person"
    self.assertIn("fixture has unsupported field: profile_name", validator.validate_fixture_bundle(bundle))

def test_fixture_rejects_profile_derived_private_field(self) -> None:
    bundle = self.fixture("scenario-a.json")
    bundle["structural_state_fixture"]["profile_url"] = "profile-reference-omitted
    self.assertIn("structural_state_fixture has unsupported field: profile_url", validator.validate_fixture_bundle(bundle))
```

Also cover email, phone, image/screenshot/OCR/hash/embedding fields, raw text, analytics values, social counts, literal employer/location/date fields, unknown enums, `real_profile_mapping != none_created`, duplicate fact IDs, and references to nonexistent facts. Add `test_schema_document_matches_executable_field_and_enum_contract` so `schema.json` cannot drift from the executable allowlists.

- [ ] **Step 3: Run the fixture suite and verify RED**

Run:

```bash
python3 -B -m unittest tests.test_linkedin_report_fixtures -v
```

Expected: import/function failure because the validator behavior does not exist, or assertion failures naming missing validation. File-not-found is not an acceptable RED because all test inputs already exist.

- [ ] **Step 4: Implement the closed fixture validator**

Use explicit allowlists and exact enum sets. Do not use JSON Schema as the executable validator; `schema.json` documents the same contract for reviewers.

```python
REQUIRED_BUNDLE_FIELDS = frozenset({
    "schema_version", "fixture_id", "origin_class", "derivation",
    "internal_candidate_id", "real_profile_mapping", "locale", "evaluation_date",
    "evidence_mode",
    "structural_state_fixture", "synthetic_fact_catalog", "score_ledger",
    "priorities", "copy_blocks", "blocked_claims", "source_catalog",
    "authorization_state", "eval_expectations",
})

EVIDENCE_MODES = frozenset({
    "authorized_visual_visible", "structural_only", "partial_visual_photo_only",
    "partial_visual_banner_only",
})

def validate_fixture_bundle(bundle: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(bundle, dict):
        return ["fixture must be a JSON object"]
    for field in sorted(set(bundle) - REQUIRED_BUNDLE_FIELDS):
        errors.append(f"fixture has unsupported field: {field}")
    for field in sorted(REQUIRED_BUNDLE_FIELDS - set(bundle)):
        errors.append(f"fixture missing required field: {field}")
    if errors:
        return errors
    expected = {
        "schema_version": "linkedin-client-report-v2-fixture-1",
        "origin_class": "synthetic_from_authorized_structural_review",
        "derivation": "composite_plus_counterfactual_perturbation",
        "real_profile_mapping": "none_created",
    }
    for field, value in expected.items():
        if bundle[field] != value:
            errors.append(f"fixture must use {field}={value}")
    if bundle["evidence_mode"] not in EVIDENCE_MODES:
        errors.append("fixture has invalid evidence_mode")
    return errors
```

Synthetic facts may use only controlled fields: `fact_id`, `evidence_state`, `fact_type`, `role_family`, `capability_family`, `scope_bucket`, and `claim_tokens`. No free-form biography is accepted.

Define closed nested contracts as constants and validate every nested object with exact keys:

```python
FACT_FIELDS = frozenset({"fact_id", "evidence_state", "fact_type", "role_family", "capability_family", "scope_bucket", "claim_tokens"})
PRIORITY_FIELDS = frozenset({"priority_id", "rank", "section", "diagnosed_gap", "action_type", "evidence_ids", "timebox", "done_when", "impact_basis"})
COPY_FIELDS = frozenset({"copy_id", "section", "state", "audience", "problem", "fact_ids", "evidence_ids", "claim_boundary"})
SOURCE_FIELDS = frozenset({"source_id", "source_category", "source_class", "url", "access_date", "reachability", "scope", "inference_limit", "fallback"})
SCORE_LEDGER_FIELDS = frozenset({"numeric_weighted_total", "scored_weight", "not_scored_weight", "overall_score", "confidence", "domains"})
DOMAIN_SCORE_FIELDS = frozenset({"domain", "weight", "state", "raw_score", "weighted_points", "evidence_ids", "reason_code"})
```

Every string value in every nested object passes the privacy scanner. `claim_tokens`, gap/action codes, role/capability families, scope buckets, blocked claims, expectations, and authorization values must resolve to explicit enum vocabularies; arbitrary strings are rejected.

- [ ] **Step 5: Complete and cross-check the five fixture states**

Use these identity-independent case decisions:

| Fixture | Locale | Visual evidence | Scored weight | Overall score | Distinct blocked claim |
|---|---|---|---:|---:|---|
| A `technical-signal-dispersed` | `es` | full | 100 | 58 | `CAPABILITY_UNVERIFIED` |
| B `leadership-story-general` | `en` | full; proof not scored | 90 | 61 | `LEADERSHIP_SCOPE_UNQUANTIFIED` |
| C `structural-no-visual` | `es` | structural only | 85 | 64 | `VISUAL_NOT_INSPECTED` |
| D `partial-visual-no-aggregate` | `en` | photo only | 75 | 63 | `VISUAL_PARTIAL_NO_AGGREGATE` |

Use domain weights `15,15,15,20,15,10,10` for visual, headline, About, experience, skills, proof, and completeness. Store hand-checked `weighted_points`, `scored_weight`, `not_scored_weight`, and `overall_score`; do not calculate fixture expectations with production code.

Also create `scenario-d-banner-only.json` as a positive variant with `evidence_mode=partial_visual_banner_only`, no aggregate visual score, a different synthetic internal candidate ID, and the same privacy contract. It is not counted among the four primary scenarios.

- [ ] **Step 6: Verify GREEN and commit**

Run:

```bash
python3 -B -m unittest tests.test_linkedin_report_fixtures -v
```

Expected: all fixture tests pass.

Commit:

```bash
git add plugins/job-search-coach/scripts/validate_linkedin_client_report.py tests/test_linkedin_report_fixtures.py tests/evals/with-skill/fixtures/linkedin-report-v2
git commit -m "test: define synthetic linkedin report fixtures"
```

---

### Task 2: Parse the real client-first Markdown layers and localized structure

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_linkedin_client_report.py`
- Create: `tests/test_linkedin_client_report.py`
- Create: `tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-a-es.md`
- Create: `tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-b-en.md`
- Create: `tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-c-es.md`
- Create: `tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-d-en.md`
- Create: `tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-d-banner-only-en.md`
- Create: `tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-a-es-debug.md`

**Interfaces:**
- Consumes: valid bundles from Task 1.
- Produces: immutable structural `ParsedClientReport(locale, client_report, evidence_appendix, section_bodies)`; it contains no derived scores, decisions, or evidence indexes.
- Produces: `parse_client_report(markdown: str) -> ParsedClientReport` that raises `ValueError` only for unparseable layer/heading structure.
- Produces: `parse_full_debug_appendix(parsed: ParsedClientReport) -> tuple[LegacyAppendixSection, ...]` for the complete legacy appendix only.
- Produces: `validate_client_report(markdown: str, bundle: Mapping[str, object], *, appendix_mode: str = "normal") -> list[str]`.

- [ ] **Step 1: Hand-author test reports, then write parser RED tests against them**

The Markdown format begins exactly with the localized H1 and uses the following eight H2 sections before the appendix delimiter:

```text
Veredicto / Verdict
Calificación / Score
Las tres decisiones prioritarias / Three priority decisions
Copy listo para revisar / Copy ready for review
No cambies todavía / Do not change yet
Plan privado de siete días / Private seven-day plan
Evidencia pendiente / Evidence needed
Límites del diagnóstico / Diagnostic boundaries
```

Create all six Markdown test inputs before running the tests; they are independent test data, not output from production code. Add tests for byte-zero H1, Spanish/English maps, exact ordering, missing/duplicate/reordered headings, content before H1, the first appendix heading as the layer boundary, photo-only and banner-only positive partial-visual cases, and a semicolon contract row pretending to be a report.

In the same RED class, add explicit debug tests: the complete 14-section debug fixture is accepted in `debug` mode; deleting any legacy section is rejected; replacing its internal candidate ID with scenario B's ID is rejected; and moving one canonical row before the appendix boundary is rejected. These assertions must fail before Step 4 implements full-debug parsing.

```python
def test_report_starts_at_byte_zero_and_has_eight_ordered_sections(self) -> None:
    parsed = validator.parse_client_report(self.report("scenario-a-es.md"))
    self.assertEqual("es", parsed.locale)
    self.assertTrue(parsed.client_report.startswith("# Diagnóstico ejecutivo de LinkedIn\n"))
    self.assertEqual(validator.SECTION_KEYS, tuple(parsed.section_bodies))

def test_contract_row_cannot_substitute_for_rendered_report(self) -> None:
    errors = validator.validate_client_report(
        "- inferred: candidate_id=x; linkedin_rendered_client_report_sample=x.",
        self.bundle("scenario-a.json"),
    )
    self.assertIn("client report must start at byte 0 with a localized H1", errors)
```

- [ ] **Step 2: Run the parser class and verify RED**

Run:

```bash
python3 -B -m unittest tests.test_linkedin_client_report.LinkedInClientReportParsingTests -v
```

Expected: failure because `ParsedClientReport`, localized heading maps, and parser do not exist.

- [ ] **Step 3: Implement the minimal parser and layer limits**

Add localized maps and parse only H1/H2 structure. Use this control flow:

```python
def parse_client_report(markdown: str) -> ParsedClientReport:
    if markdown.startswith("# Diagnóstico ejecutivo de LinkedIn\n"):
        locale = "es"
    elif markdown.startswith("# LinkedIn Executive Diagnostic\n"):
        locale = "en"
    else:
        raise ValueError("client report must start at byte 0 with a localized H1")
    headings = HEADING_MAP[locale]
    appendix_heading = headings["appendix"]
    marker = f"\n## {appendix_heading}\n"
    if markdown.count(marker) != 1:
        raise ValueError("report requires exactly one localized appendix boundary")
    client_report, appendix_body = markdown.split(marker, 1)
    matches = list(re.finditer(r"(?m)^## ([^\n]+)$", client_report))
    if tuple(match.group(1) for match in matches) != tuple(headings[key] for key in SECTION_KEYS):
        raise ValueError("client report sections are missing, duplicated, or out of order")
    section_bodies = _slice_h2_bodies(client_report, matches)
    return ParsedClientReport(locale, client_report, appendix_body, section_bodies)
```

Count words after removing only lines that begin and end with `|` inside the score section; do not remove arbitrary paragraphs. Validate:

- client report ≤800 words;
- normal appendix ≤250 words;
- normal total ≤1,100 words;
- zero contract markers in `client_report`;
- sparse reports may be below 450 words.

Use both contract detectors: explicit sensitive keys and a canonical evidence-prefix row containing at least two `key=value` pairs separated by semicolons.

```python
CONTRACT_TOKEN = re.compile(r"(?:^|[; ])(?:candidate_id|linkedin_[a-z0-9_]+)=", re.I)
CANONICAL_CONTRACT_ROW = re.compile(
    r"(?m)^-\s*(?:verified|candidate-reported|inferred|unknown):"
    r"[^\n]*\b[a-z][a-z0-9_]*=[^;\n]+;\s*[^\n]*\b[a-z][a-z0-9_]*=",
    re.I,
)
```

- [ ] **Step 4: Implement mode-specific appendix parsing**

Normal mode rejects canonical rows in the appendix and enforces 250/1,100-word caps. `debug|eval|detail_requested` requires the full legacy appendix only after the boundary. Define `LEGACY_APPENDIX_SECTION_KEYS` as the exact 14 canonical section keys already required by the existing `profile-audit.md` contract. `parse_full_debug_appendix()` requires each section exactly once and in order; the installed validator checks generic canonical-row syntax, placement, and internal candidate identity only. It must never import repository test/static-check modules. A partial appendix—even one valid row—is an error.

`scenario-a-es-debug.md` must start with the same valid report, then contain all 14 canonical legacy sections/rows whose `candidate_id` equals bundle `internal_candidate_id`; reject a missing/reordered/duplicated section, a copied row from scenario B, and any canonical row moved before the appendix. The debug fixture is complete compatibility evidence, not a normal client payload.

- [ ] **Step 5: Verify GREEN and commit**

Run:

```bash
python3 -B -m unittest tests.test_linkedin_client_report.LinkedInClientReportParsingTests -v
```

Commit:

```bash
git add plugins/job-search-coach/scripts/validate_linkedin_client_report.py tests/test_linkedin_client_report.py tests/evals/with-skill/fixtures/linkedin-report-v2/*.md
git commit -m "feat: validate client-first linkedin report structure"
```

---

### Task 3: Reconcile scores, coverage, and evidence traceability

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_linkedin_client_report.py`
- Modify: `tests/test_linkedin_client_report.py`
- Modify: `tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-*.md`

**Interfaces:**
- Consumes: `ParsedClientReport` and the bundle score ledger.
- Produces: `parse_score_table(parsed: ParsedClientReport) -> tuple[ReportDomainScore, ...]`.
- Produces: `calculate_half_up_score(numeric_weighted_total: float, scored_weight: int) -> int | None` with the same observable result as the existing checker helper.
- Adds score/coverage errors to `validate_client_report`.

- [ ] **Step 1: Write score RED tests with hand-derived literals**

Cover all seven dimensions, evaluated state/score/evidence/reason, `No evaluado` exclusion, partial visual exclusion, denominator and confidence, report/ledger mismatch, nonexistent evidence IDs, and candidate isolation via fixture-specific evidence IDs.

```python
def test_half_up_score_uses_nonlegacy_values(self) -> None:
    cases = ((47.0, 70, 67), (50.5, 100, 51), (64.0, 85, 75), (79.0, 90, 88), (88.0, 100, 88))
    for points, weight, expected in cases:
        self.assertEqual(expected, validator.calculate_half_up_score(points, weight))
    self.assertIsNone(validator.calculate_half_up_score(0.0, 0))

def test_visible_score_cannot_disagree_with_ledger(self) -> None:
    report = self.report("scenario-c-es.md").replace("64/100", "61/100", 1)
    errors = validator.validate_client_report(report, self.bundle("scenario-c.json"))
    self.assertIn("visible overall score 61 does not match ledger score 64", errors)
```

- [ ] **Step 2: Run score tests and verify RED**

Run:

```bash
python3 -B -m unittest tests.test_linkedin_client_report.LinkedInClientReportScoreTests -v
```

Expected: failure because table parsing and score reconciliation are absent.

- [ ] **Step 3: Implement score parsing and reconciliation**

Parse localized score table columns, require the seven canonical domain codes from the bundle, and compare visible values to the hand-authored ledger. `not_scored` rows use an em dash for score and must not add weight or points. Reject a visual aggregate for `structural_only`, `partial_visual_photo_only`, or `partial_visual_banner_only`.

```python
def calculate_half_up_score(points: float, scored_weight: int) -> int | None:
    if scored_weight <= 0:
        return None
    return int((points / scored_weight) * 100 + 0.5)

def _validate_scores(parsed: ParsedClientReport, bundle: Mapping[str, object]) -> list[str]:
    rows = parse_score_table(parsed)
    expected = {row["domain"]: row for row in bundle["score_ledger"]["domains"]}
    errors: list[str] = []
    if set(row.domain for row in rows) != set(DOMAIN_WEIGHTS):
        errors.append("score table must contain exactly the seven canonical dimensions")
    for row in rows:
        ledger_row = expected.get(row.domain)
        if ledger_row is None:
            continue
        if row.state != ledger_row["state"]:
            errors.append(f"visible state for {row.domain} does not match ledger")
        if not row.reason.strip():
            errors.append(f"score row {row.domain} requires a reason")
        if not row.evidence_ids:
            errors.append(f"score row {row.domain} requires evidence")
        if ledger_row["state"] == "not_scored":
            if row.score is not None:
                errors.append(f"unavailable dimension {row.domain} must be not scored, not zero")
        elif row.score != ledger_row["raw_score"]:
            errors.append(f"visible domain score for {row.domain} does not match ledger")
        for evidence_id in row.evidence_ids:
            if evidence_id not in _bundle_evidence_ids(bundle):
                errors.append(f"score row references unknown evidence {evidence_id}")
    ledger = bundle["score_ledger"]
    visible_scored_weight, visible_not_scored_weight = parse_visible_coverage(parsed)
    if visible_scored_weight != ledger["scored_weight"] or visible_not_scored_weight != ledger["not_scored_weight"]:
        errors.append("visible coverage denominator/exclusions do not match ledger")
    recomputed_points = sum(
        row["weighted_points"] for row in ledger["domains"] if row["state"] == "scored"
    )
    if recomputed_points != ledger["numeric_weighted_total"]:
        errors.append("ledger weighted points do not reconcile")
    recomputed = calculate_half_up_score(ledger["numeric_weighted_total"], ledger["scored_weight"])
    visible_overall_score = parse_visible_overall_score(parsed)
    if recomputed != ledger["overall_score"]:
        errors.append("ledger overall score does not reconcile")
    if visible_overall_score != ledger["overall_score"]:
        errors.append(
            f"visible overall score {visible_overall_score} does not match ledger score {ledger['overall_score']}"
        )
    if parse_visible_confidence(parsed) != ledger["confidence"]:
        errors.append("visible confidence does not match scored coverage")
    return errors
```

- [ ] **Step 4: Verify GREEN and commit**

Run the whole report test file:

```bash
python3 -B -m unittest tests.test_linkedin_client_report -v
```

Commit:

```bash
git add plugins/job-search-coach/scripts/validate_linkedin_client_report.py tests/test_linkedin_client_report.py tests/evals/with-skill/fixtures/linkedin-report-v2/*.md
git commit -m "feat: reconcile linkedin report scores and evidence"
```

---

### Task 4: Validate candidate-specific priorities and copy decisions

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_linkedin_client_report.py`
- Modify: `tests/test_linkedin_client_report.py`
- Modify: `tests/evals/with-skill/fixtures/linkedin-report-v2/scenario-*.md`

**Interfaces:**
- Consumes: parsed priority and copy blocks plus fixture `priorities`, `copy_blocks`, `blocked_claims`, and fact IDs.
- Produces: `priority_fingerprint(priority: Mapping[str, object]) -> tuple[str, str, str, tuple[str, ...], str]`, ordered as `(section, diagnosed_gap, action_type, evidence_ids, done_when)`.
- Produces: `validate_report_pair_differentiation(report_a, bundle_a, report_b, bundle_b) -> list[str]`.

- [ ] **Step 1: Write priority and copy RED tests**

Require exactly three numbered priority blocks. Each block exposes `gap`, `action`, `evidence`, `timebox`, and `done_when` in the request locale. Require exactly three copy blocks for headline, About opening, and experience bullet; each has state, audience, problem, evidence IDs, and claim boundary.

Add one-mutant tests for missing fields, nonexistent evidence, duplicate fingerprints, swappable generic advice, unsupported fact in ready copy, ready copy duplicated in blocked claims, confirmation-state contradiction, and an evidence question that changes no score/priority/copy.

Also cover these client-safety constraints:

- `No cambies todavía` contains at most three explicit items;
- the private seven-day plan contains only profile, copy, evidence, or proof work—not outreach, applications, interview preparation, or external LinkedIn actions;
- every priority uses `impact_basis=COACH_HEURISTIC` unless a current official source directly supports the narrower factual statement;
- scenario C asks only for the minimum evidence that could change a score, priority, or copy state;
- `improve_profile`, `add_keywords`, `create_content`, and equivalent generic action/gap codes are invalid in all cases, even when decorated with timebox or evidence metadata.

```python
def test_scenarios_a_and_b_are_materially_different(self) -> None:
    errors = validator.validate_report_pair_differentiation(
        self.report("scenario-a-es.md"), self.bundle("scenario-a.json"),
        self.report("scenario-b-en.md"), self.bundle("scenario-b.json"),
    )
    self.assertEqual([], errors)

def test_ready_copy_cannot_use_unconfirmed_fact(self) -> None:
    bundle = self.bundle("scenario-a.json")
    unknown_fact = next(
        fact for fact in bundle["synthetic_fact_catalog"]
        if fact["evidence_state"] == "unknown"
    )
    bundle["copy_blocks"][0]["fact_ids"].append(unknown_fact["fact_id"])
    report = self.report("scenario-a-es.md").replace(
        "Evidencia: FACT-A-READY", f"Evidencia: FACT-A-READY, {unknown_fact['fact_id']}", 1
    )
    errors = validator.validate_client_report(report, bundle)
    self.assertIn(f"ready copy references unsupported fact {unknown_fact['fact_id']}", errors)

def test_copying_a_decisions_into_b_fails_material_differentiation(self) -> None:
    def replace_many(text: str, replacements: dict[str, str]) -> str:
        for old, new in replacements.items():
            self.assertIn(old, text)
            text = text.replace(old, new)
        return text

    copied = replace_many(self.report("scenario-b-en.md"), {
        "GAP-B-PRIMARY": "GAP-A-PRIMARY",
        "GAP-B-SECONDARY": "GAP-A-SECONDARY",
        "GAP-B-PROOF": "GAP-A-PROOF",
        "ACTION-B-HEADLINE": "ACTION-A-HEADLINE",
        "ACTION-B-ABOUT": "ACTION-A-ABOUT",
        "ACTION-B-EXPERIENCE": "ACTION-A-EXPERIENCE",
        "EVID-B-PRIORITY-1": "EVID-A-PRIORITY-1",
        "EVID-B-PRIORITY-2": "EVID-A-PRIORITY-2",
        "EVID-B-PRIORITY-3": "EVID-A-PRIORITY-3",
        "TIMEBOX-B-1": "TIMEBOX-A-1",
        "TIMEBOX-B-2": "TIMEBOX-A-2",
        "TIMEBOX-B-3": "TIMEBOX-A-3",
        "DONE-WHEN-B-1": "DONE-WHEN-A-1",
        "DONE-WHEN-B-2": "DONE-WHEN-A-2",
        "DONE-WHEN-B-3": "DONE-WHEN-A-3",
        "COPY-B-PRIMARY": "COPY-A-PRIMARY",
    })
    errors = validator.validate_report_pair_differentiation(
        self.report("scenario-a-es.md"), self.bundle("scenario-a.json"),
        copied, self.bundle("scenario-b.json"),
    )
    self.assertIn("report pair must differ in at least two priority fingerprints", errors)
    self.assertIn("report pair must not reuse the same primary diagnosed gap", errors)
    self.assertIn("report pair must recommend a different primary copy category", errors)
```

The hand-authored A/B reports must contain these controlled codes exactly once so the mutation is causal and cannot fail because of localization or malformed Markdown.

- [ ] **Step 2: Run priority/copy tests and verify RED**

Run:

```bash
python3 -B -m unittest tests.test_linkedin_client_report.LinkedInClientReportDecisionTests -v
```

- [ ] **Step 3: Implement semantic fingerprints and claim-state consistency**

Parse priority blocks by their numbered H3 plus fixed localized field labels, and parse copy blocks by their fixed section H3 plus localized state/audience/problem/evidence/boundary labels. Reject duplicate/missing fields before semantic checks. Resolve every referenced evidence/fact ID against the same bundle.

Compare A/B by structured fingerprints, not literal prose. Require at least two of three differing fingerprints plus different primary gap and recommended copy category. Reject generic priority/action/gap codes `improve_profile`, `add_keywords`, and `create_content` unconditionally.

Use this validation sequence:

```python
def _validate_decisions(parsed, bundle):
    priorities = parse_priority_blocks(parsed)
    copies = parse_copy_blocks(parsed)
    errors = _require_exact_three_complete_priorities(priorities)
    errors += _require_exact_three_copy_categories(copies)
    errors += _resolve_decision_references(priorities, copies, bundle)
    errors += _validate_copy_claim_states(copies, bundle["synthetic_fact_catalog"], bundle["blocked_claims"])
    errors += _validate_private_plan_scope(parsed.section_bodies["seven_day_plan"])
    errors += _validate_pending_evidence_changes_a_decision(parsed, bundle)
    return errors
```

- [ ] **Step 4: Verify GREEN and commit**

Run:

```bash
python3 -B -m unittest tests.test_linkedin_report_fixtures tests.test_linkedin_client_report -v
```

Commit:

```bash
git add plugins/job-search-coach/scripts/validate_linkedin_client_report.py tests/test_linkedin_client_report.py tests/evals/with-skill/fixtures/linkedin-report-v2
git commit -m "feat: validate linkedin report decisions and copy"
```

---

### Task 5: Enforce report privacy, safety, sources, and CLI behavior

**Files:**
- Modify: `plugins/job-search-coach/scripts/validate_linkedin_client_report.py`
- Modify: `tests/test_linkedin_client_report.py`
- Create: `plugins/job-search-coach/tests/linkedin-client-report-advisory-rubric.json`

**Interfaces:**
- Produces: deterministic CLI `python3 validate_linkedin_client_report.py REPORT.md BUNDLE.json [--appendix-mode normal|debug|eval|detail_requested]`.
- CLI exit `0`: valid, no stdout/stderr. Exit `2`: sorted deterministic errors, one per stderr line.
- Produces: advisory rubric metadata only; it cannot change validator outcome.
- Requires a minimum official-source catalog covering `good_profile`, `profile_photo`, `cover_image`, `featured_section`, `skills`, `job_match`, `ai_hiring_agents`, and `job_seeker_hirer_connection`.

- [ ] **Step 1: Write mutation-based security and source RED tests**

Each test starts with one valid report and changes one behavior. Assert the exact error for email, phone, LinkedIn profile URL, local path, raw-profile aliases, analytics values, case-insensitive placeholders, `[CONFIRMAR DESPUÉS]` without a decision-changing question, protected-trait visual inference, external action claimed as executed, outcome guarantee, and authorization inferred from inspection.

Add source tests requiring unique `source_id`, an allowlisted official LinkedIn/Microsoft URL, `access_date`, `scope`, `inference_limit`, and computed `state=current|stale|unreachable`. The bundle stores the access date and declared reachability; production computes freshness relative to bundle `evaluation_date`. Test ages 89, 90, and 91 days. A stale/unreachable source must degrade to `COACH_HEURISTIC` or block the linked claim. Secondary sources are optional and can never satisfy a missing required official-source category. Reject any source-derived `lift`, individual probability, or use of “2x” in score math.

Add exact negative cases for placeholders `x`, `criteria`, `generic`, and `TBD`; mixed-case variants; scenario C requesting more evidence than can change a current decision; and `COACH_HEURISTIC` impact statements presented as LinkedIn measurements or causal guarantees.

Keep advisory grading as a separate, non-input interface. Test that `validate_client_report` has no advisory/override parameter, the CLI has no advisory-override flag, and the same deterministically invalid report exits 2 regardless of a separately constructed all-5 advisory result. Assert the rubric metadata says `cannot_override_deterministic_failure=true`; do not add `combine_validation` or any bypass path.

- [ ] **Step 2: Write CLI RED tests**

```python
def test_cli_accepts_valid_pair_without_output(self) -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(REPORT_A), str(BUNDLE_A)],
        capture_output=True, text=True, check=False,
    )
    self.assertEqual(0, result.returncode)
    self.assertEqual("", result.stdout)
    self.assertEqual("", result.stderr)

def test_cli_returns_two_for_cross_case_pair(self) -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(REPORT_A), str(BUNDLE_B)],
        capture_output=True, text=True, check=False,
    )
    self.assertEqual(2, result.returncode)
    self.assertIn("report evidence does not belong to fixture", result.stderr)
```

- [ ] **Step 3: Run safety/CLI tests and verify RED**

Run:

```bash
python3 -B -m unittest tests.test_linkedin_client_report.LinkedInClientReportSafetyTests tests.test_linkedin_client_report.LinkedInClientReportCliTests -v
```

- [ ] **Step 4: Implement deterministic scanners, source resolution, and CLI**

Keep source URLs allowed only under `source_catalog`. Do not promise perfect human-name detection: deterministically reject emails, phones, profile URLs, local paths, forbidden fields, raw text, analytics values, and known protected-trait inference phrases. Record free-name/singling-out review as advisory.

Apply privacy scanning recursively to every top-level and nested scalar value except the official source URL itself. URL validation must first prove the object is inside `source_catalog`, then require HTTPS and the official hostname/path allowlist. Use bundle `evaluation_date` only—never `date.today()` or filesystem timestamps.

```python
def resolve_source_state(source, evaluation_date):
    if source["reachability"] == "unreachable":
        return "unreachable"
    age = (evaluation_date - date.fromisoformat(source["access_date"])).days
    return "current" if 0 <= age <= 90 else "stale"

def validate_client_report(markdown, bundle, *, appendix_mode="normal"):
    errors = validate_fixture_bundle(bundle)
    if errors:
        return sorted(set(errors))
    try:
        parsed = parse_client_report(markdown)
    except ValueError as exc:
        return [str(exc)]
    errors += _validate_layers(parsed, bundle, appendix_mode)
    errors += _validate_scores(parsed, bundle)
    errors += _validate_decisions(parsed, bundle)
    errors += _validate_privacy_and_safety(parsed, bundle)
    errors += _validate_sources(parsed, bundle)
    return sorted(set(errors))
```

The CLI parses arguments with `argparse`, reads UTF-8 files, reports file/JSON/parser failures as deterministic error lines, prints nothing on success, prints sorted unique errors to stderr on failure, and returns 2. Advisory input is never accepted as a bypass flag.

The advisory rubric JSON contains versioned axes `specificity`, `decision_utility`, `evidence_fidelity`, `differentiation`, `clarity`, `actionability`, and `boundaries`, each scored 1–5 with anchors. It states `blocking=false`, `cannot_override_deterministic_failure=true`, and requires `prompt_version`, `rubric_version`, `model`, and textual evidence per score.

- [ ] **Step 5: Verify GREEN and commit**

Run:

```bash
python3 -B -m unittest tests.test_linkedin_report_fixtures tests.test_linkedin_client_report -v
```

Commit:

```bash
git add plugins/job-search-coach/scripts/validate_linkedin_client_report.py plugins/job-search-coach/tests/linkedin-client-report-advisory-rubric.json tests/test_linkedin_client_report.py
git commit -m "feat: enforce linkedin report privacy and safety"
```

---

### Task 6: Pressure-test and update the LinkedIn skill delivery contract

**Files:**
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/SKILL.md`
- Create: `plugins/job-search-coach/skills/optimize-linkedin-career/references/client-report.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/references/profile-audit.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/agents/openai.yaml`
- Modify: `plugins/job-search-coach/README.md`
- Modify: `tests/test_skill_contracts.py`
- Create: `tests/evals/final/linkedin-client-report-v2-pressure-summary.json`
- Test artifacts only: this plan's `.superpowers/sdd/...` workspace, never the repo or plugin package.

**Interfaces:**
- Consumes: the v2 report format and validator from Tasks 1–5.
- Produces: default normal response = client report first + compact appendix.
- Produces: `debug|eval|detail_requested` response = same client report first + full legacy appendix.
- Preserves: evidence labels, visual/protected-trait boundaries, candidate isolation, confidentiality, and exact action-and-target authorization.

- [ ] **Step 1: Run a five-case fresh-context baseline corpus before editing the skill**

Use one fixed prompt each for scenario A, scenario B, scenario C, D-banner-only, and an in-memory adversarial counterfactual in five fresh subagents created with `fork_turns=none` and an explicitly recorded identical model/reasoning setting. Give each only the current checkout skill path and its synthetic bundle; do not reveal expected headings or the intended fix. Ask for a normal LinkedIn diagnosis. Save raw outputs only in this plan's ignored SDD workspace. Store the privacy-safe prompt corpus hash and case IDs so GREEN reuses the exact inputs.

For every output, run the v2 validator and record word count, first heading, contract-token count, section count, and validator errors. Require per-case results, not only an aggregate rate, plus A/B differentiation. Expected RED: current instructions produce contract rows or omit the real eight-section report.

- [ ] **Step 2: Write contract tests for the skill/reference before editing**

In `tests/test_skill_contracts.py`, add a structural contract test that reads `client-report.md`, confirms the default/debug mode decision and localized section maps are specified once, and validates all five normal report fixtures (four primary scenarios plus banner-only) and the complete debug fixture with the real validator. Update `REFERENCE_NAMES` to include `client-report.md`. Treat this as wiring/static evidence only; the fresh-context samples are the behavioral evidence.

Run:

```bash
python3 -B -m unittest tests.test_skill_contracts.OptimizeLinkedInCareerContractTests -v
```

Expected: failure because the reference and default client-first instruction do not exist.

- [ ] **Step 3: Add the positive report recipe and make it the default output**

Keep `SKILL.md` concise. It must require reading `client-report.md` for every audit and state:

```markdown
## Client-first delivery

Return the localized Markdown client report from byte 0. In normal mode, follow it with only the compact evidence index. Use the full canonical sections only after the report when the user requests detail or the run is explicitly `debug` or `eval`. A `linkedin_rendered_client_report_sample` row never substitutes for the rendered report.
```

Move the detailed eight-section recipe, localized headings, score table, priority/copy block formats, appendix modes, word limits, and mapping from existing contracts into `references/client-report.md`. Keep existing semicolon contracts in `profile-audit.md` as appendix sources, not the visible deliverable. Change source policy so an official source can stand alone, dated secondary guidance is optional, and coach weights/windows are `COACH_HEURISTIC`.

- [ ] **Step 4: Update user-facing metadata without promising outcomes**

The agent default prompt and README starter prompt must ask for a “client-first executive LinkedIn diagnostic with a compact evidence appendix.” Do not add ranking, response, interview, salary, or time-to-hire claims. Replace the README's `krf-self` identifier and personal technology/role sample with an unmistakably generic synthetic candidate and stack; package author metadata remains intentional.

- [ ] **Step 5: Run five fresh-context GREEN pressure samples**

Use five new subagents with `fork_turns=none`, the byte-identical baseline prompt corpus and model/reasoning settings, and the updated checkout skill. Do not supply the expected answer. Validate every output against its own case bundle. Required result: every case independently passes all deterministic gates, A/B passes structured differentiation, report shapes converge, and no output exposes a contract dump before the appendix. Record advisory rubric scores and exact evidence, but do not make them blocking.

Write a privacy-safe durable summary to `tests/evals/final/linkedin-client-report-v2-pressure-summary.json`. Preserve `cases[]` with `case_id`, deterministic pass/errors, first H1, section count, contract-token count, client/appendix/total word counts, and sanitized advisory axis scores plus short evidence codes. Also include run/pass totals, model, prompt/rubric versions, corpus hash, distributions, the A/B differentiation result, and a statement that raw outputs remain in ignored SDD storage. Aggregates summarize but never replace per-case gates. Do not commit prompts containing real-profile data or any raw sampled report.

- [ ] **Step 6: Refactor wording only if fresh agents find a loophole**

If an agent emits a row instead of Markdown, adds the full appendix in normal mode, or omits required sections, tighten the positive recipe and rerun the failing pressure prompt with a new subagent. Do not add another client-facing contract row.

- [ ] **Step 7: Verify GREEN and commit**

Run:

```bash
python3 -B -m unittest tests.test_skill_contracts.OptimizeLinkedInCareerContractTests -v
python3 -B -m unittest tests.test_linkedin_report_fixtures tests.test_linkedin_client_report -v
```

Commit:

```bash
git add plugins/job-search-coach/skills/optimize-linkedin-career plugins/job-search-coach/README.md tests/test_skill_contracts.py tests/evals/final/linkedin-client-report-v2-pressure-summary.json
git commit -m "feat: deliver client-first linkedin diagnostics"
```

---

### Task 7: Integrate v2 reports into static checks and legacy regression coverage

**Files:**
- Modify: `plugins/job-search-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`
- Modify: `tests/test_skill_contracts.py`
- Create: `tests/evals/with-skill/linkedin-client-report-v2.md`
- Superseded historical file instruction: `tests/evals/with-skill/linkedin.md` is now a closed-vocabulary, independently fabricated contract inventory validated by its exact schema.

**Interfaces:**
- Consumes: validator CLI/module, five normal report/bundle pairs (four primary plus banner-only), and one complete debug pair.
- Produces: `validate_linkedin_report_fixture_directory(root: Path) -> list[str]` in `run_static_checks.py`, validating every v2 pair and A/B differentiation.
- Superseded historical interface: legacy semantic behavior is exercised by independent minimal synthetic fixtures; the closed artifact proves only its enumerated contract inventory.

- [ ] **Step 1: Write integration RED tests**

Add `TemporaryDirectory` tests for `validate_linkedin_report_fixture_directory(root)` proving zero/missing report sets fail, exactly the five normal report/bundle pairs (four primary plus banner-only) are validated, the debug pair is validated in debug mode with client-report-first ordering and candidate-ID matching, and A/B differentiation is enforced. Also prove the old 2,154-word `coach_brief` fails when submitted to the v2 validator.

Replace misleading assertions:

- rename `test_linkedin_jenkins_smoke_is_coach_grade_not_a_compliance_dump` to `test_legacy_debug_smoke_preserves_evidence_and_safety_contracts`;
- replace `test_linkedin_diagnostic_requires_rendered_client_report_sample` with `test_client_report_v2_is_the_actual_client_delivery`;
- keep legacy delivery-map/sample validators only as debug-appendix compatibility, not as proof of client readability;
- remove Jenkins/72 special cases from helpers used by v2 tests.

Add a fifth in-memory counterfactual bundle/report derived from scenario C with these hand-authored expected literals: `internal_candidate_id=SYNTH-X-COUNTERFACTUAL`, evidence IDs `EVID-X-01`, `EVID-X-02`, `EVID-X-03`, copy states `ready`, `requires_confirmation`, and `omit`, and this complete ledger:

| Domain | Weight | State | Raw score | Weighted points |
|---|---:|---|---:|---:|
| visual | 15 | not_scored | — | 0.00 |
| headline | 15 | scored | 65 | 9.75 |
| about | 15 | scored | 65 | 9.75 |
| experience | 20 | scored | 65 | 13.00 |
| skills | 15 | scored | 65 | 9.75 |
| proof | 10 | not_scored | — | 0.00 |
| completeness | 10 | scored | 65 | 6.50 |

The hand sum is `numeric_weighted_total=48.75`, `scored_weight=75`, `not_scored_weight=25`, and half-up `overall_score=65`. Use priority fingerprints `("headline","TARGET_ROLE_AMBIGUOUS","REWRITE_TARGET_ROLE",("EVID-X-01",),"HEADLINE_TARGET_ROLE_VISIBLE")`, `("about","PROOF_SEQUENCE_WEAK","REORDER_PROOF",("EVID-X-02",),"ABOUT_OPENS_WITH_VERIFIED_PROOF")`, and `("experience","SCOPE_BOUNDARY_MISSING","ADD_SCOPE_BOUNDARY",("EVID-X-03",),"EXPERIENCE_STATES_SCOPE_BOUNDARY")`; store timeboxes separately as `35m`, `45m`, and `50m`.

Build these expected literals in test code without calling production score/fingerprint functions. The counterfactual must validate without adding code constants for it. Mutate `EVID-X-02` back to a scenario-C evidence ID and require a candidate/evidence-isolation failure. This is anti-hardcoding behavior evidence, not a fifth committed primary fixture.

- [ ] **Step 2: Run integration tests and verify RED**

Run:

```bash
python3 -B -m unittest tests.test_full_plugin.FullPluginIntegrationTests tests.test_skill_contracts.OptimizeLinkedInCareerContractTests -v
```

Expected: new v2 integration assertions fail because static checks do not load the validator or v2 pairs.

- [ ] **Step 3: Integrate the validator without duplicating its logic**

Superseded historical integration instruction: load `scripts/validate_linkedin_client_report.py` by explicit path and keep v2 parsing in that validator. The static dispatcher validates the closed-vocabulary LinkedIn artifact exactly once and does not route it through legacy semantic validators. Each semantic validator retains its implementation and is exercised directly with an independent minimal synthetic fixture or mutation tailored to its calculation, isolation, source, action, or safety contract. `run_static_checks.py` must not reimplement v2 report parsing, score math, privacy scanners, source validation, generic row syntax, or section extraction; the installed validator must not import `tests/run_static_checks.py`.

Create `linkedin-client-report-v2.md` as a short index that explains the four synthetic cases, points to their report/bundle files, states `no_real_profile_mapping`, and contains no real-profile data.

- [ ] **Step 4: Run focused static and integration verification**

Run:

```bash
python3 plugins/job-search-coach/tests/run_static_checks.py
python3 -B -m unittest tests.test_full_plugin.FullPluginIntegrationTests tests.test_skill_contracts.OptimizeLinkedInCareerContractTests -v
```

Expected: static checks and both LinkedIn integration classes pass.

Audit the new validator, reference, and v2 tests for leaked legacy hardcoding:

```bash
rg -n "Jenkins|linkedin-jenkins-001|\b72\b" plugins/job-search-coach/scripts/validate_linkedin_client_report.py plugins/job-search-coach/skills/optimize-linkedin-career/references/client-report.md tests/test_linkedin_client_report.py tests/test_linkedin_report_fixtures.py
```

Expected: no matches.

- [ ] **Step 5: Commit**

```bash
git add plugins/job-search-coach/tests/run_static_checks.py tests/test_full_plugin.py tests/test_skill_contracts.py tests/evals/with-skill/linkedin-client-report-v2.md
git commit -m "test: integrate linkedin client report v2"
```

---

### Task 8: Verify, version, reinstall, and attest the local plugin

**Files:**
- Modify through helper: `plugins/job-search-coach/.codex-plugin/plugin.json`
- Modify: `tests/evals/final/installed-smoke-test.md`
- Do not modify: marketplace JSON or Codex config.

**Interfaces:**
- Consumes: clean verified source plugin.
- Produces: one new `0.1.0+codex.<timestamp>` cachebuster, installed/enabled local plugin, source/cache equivalence evidence, and a fresh-agent smoke result.

- [ ] **Step 1: Run whole-branch review before freezing the package**

Use `superpowers:requesting-code-review` from the plan merge base through Task 7 HEAD. Resolve every Critical/Important finding through the SDD fix loop, rerun its focused tests, and repeat review until approved. Commit every accepted review fix and require the Task 1–7/review worktree to be clean before release freeze. This happens before the cachebuster so review fixes do not silently invalidate the installed package.

- [ ] **Step 2: Prove the source tree is clean and run pre-release verification**

Before validation, require no untracked package files, bytecode, pressure-test raw outputs, screenshots, or advisory scratch artifacts:

```bash
git diff --check
git diff --exit-code
git diff --cached --exit-code
test -z "$(git ls-files --others --exclude-standard)"
find plugins/job-search-coach -type d -name __pycache__ -o -type f -name '*.pyc'
```

Expected: no tracked, staged, or untracked changes anywhere in the release worktree, and zero bytecode/package artifacts. Ignored SDD files may remain under `.superpowers/sdd` because the commands above do not include them.

Run:

```bash
python3 -B -m unittest tests.test_linkedin_report_fixtures tests.test_linkedin_client_report -v
python3 -B plugins/job-search-coach/tests/run_static_checks.py
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
python3 -B /path/to/workspace/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/job-search-coach/skills/optimize-linkedin-career
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/private/tmp/job-search-coach-validator-deps python3 -B /path/to/workspace/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/job-search-coach
```

Expected: every command exits 0.

- [ ] **Step 3: Update the cachebuster exactly once with the official helper**

Run:

```bash
python3 -B /path/to/workspace/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py plugins/job-search-coach
```

Confirm the base remains `0.1.0` and only one `+codex.<timestamp>` suffix exists.
Before commit, require `git status --short` to show exactly `plugins/job-search-coach/.codex-plugin/plugin.json` and no other path.

- [ ] **Step 4: Re-run manifest, static, and full verification**

Run the five verification commands from Step 2 again. Any failure blocks installation.

- [ ] **Step 5: Commit the verified source version**

```bash
git add plugins/job-search-coach/.codex-plugin/plugin.json
git commit -m "chore: refresh job search coach cachebuster"
```

- [ ] **Step 6: Obtain exact installation authorization, then reinstall**

If the current conversation does not already contain immediate authorization to reinstall this exact local plugin, pause only the installation step and ask permission for this exact state change and target:

```bash
codex plugin add job-search-coach@job-search-coach-local --json
```

Continue only after approval. Do not treat approval of the source changes or report design as installation authorization.

Run:

```bash
codex plugin add job-search-coach@job-search-coach-local --json
codex plugin list --json
```

Resolve the installed cache path from the JSON. Do not add or rewrite the marketplace.

- [ ] **Step 7: Prove source and installed package equivalence**

Compare source and installed directories with `diff -qr`. Build sorted relative-path SHA-256 inventories for both directories and require an empty diff. Do not run the repository static checker against the cache because its repository-level eval dependencies are intentionally absent there. Instead, run the official plugin validator and `quick_validate.py` against the cache, then run the installed cache's `scripts/validate_linkedin_client_report.py` against the checkout's five normal fixture pairs and named debug pair.

Also require:

```bash
git diff --exit-code HEAD -- plugins/job-search-coach
git ls-files --others --exclude-standard plugins/job-search-coach
```

Expected: no source diff and no untracked package files.

- [ ] **Step 8: Run a fresh-agent installed-plugin smoke test**

Spawn a fresh-context agent with `fork_turns=none` after reinstall. Give it the resolved cache paths and require it to read the installed `SKILL.md` and installed `references/client-report.md`, then use that installed skill on synthetic scenario C in normal mode. Do not provide expected headings. Run the validator from the same installed cache against scenario C and confirm `no_external_linkedin_action=true`. Do not claim namespace autodiscovery unless a genuinely new Codex task independently proves it.

- [ ] **Step 9: Update the installation attestation and commit**

Record in `installed-smoke-test.md`: source commit, source tree, installed version/path, enabled state, file counts, normalized source/cache hash, diff result, validation commands/results, fresh-agent smoke result, and `no_external_linkedin_action=true`. Replace the stale installed version evidence; do not append contradictory versions.

Commit:

```bash
git add tests/evals/final/installed-smoke-test.md
git commit -m "test: attest linkedin report v2 installation"
```

- [ ] **Step 10: Final equivalence, verification, and completion audit**

After the attestation commit, re-run `git diff --exit-code HEAD -- plugins/job-search-coach`, source/cache `diff -qr`, and the sorted SHA-256 inventory comparison. Run the full suite one final time and verify every specification deliverable has authoritative file/test/install evidence.

If any post-cachebuster review or fix changes `plugins/job-search-coach`, the installed evidence is invalid: repeat cachebuster update → source commit → authorization-aware reinstall → equivalence → installed validation → fresh-agent smoke → replacement attestation. Never append contradictory attestation evidence.

Use `superpowers:verification-before-completion` before claiming the increment complete. This LinkedIn report increment may be reported complete only when every Task 1–8 checkbox is satisfied; do not mark the broader persistent coaching-system goal complete unless its separate remaining requirements are also proven.
