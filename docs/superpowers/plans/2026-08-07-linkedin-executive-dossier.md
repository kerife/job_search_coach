# LinkedIn Executive Career Dossier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a normal one-line LinkedIn audit produce a concise coaching response and a private, standalone HTML dossier that follows the approved Superdesign draft without fabricating personal, analytics, or market data.

**Architecture:** Introduce a closed identity-free runtime dossier JSON contract separate from the synthetic Markdown evaluation bundles. A standard-library validator enforces evidence, scoring, privacy, analytics, market, copy, and action boundaries; a second script converts only a valid dossier into escaped self-contained HTML and a short chat receipt. Existing Markdown normal/debug/eval contracts remain intact as compatibility and fallback paths.

**Tech Stack:** Python 3.11+ standard library, JSON Schema as a documented contract, HTML5, CSS, minimal inline JavaScript, `unittest`, existing repository privacy/static/release validators, Superdesign visual reference `ab206e4e-8fe8-4ace-bf28-10cbee55bf2a`.

## Global Constraints

- Work only in the existing isolated `feat/job-search-coach` worktree; never implement on main/master.
- The final Superdesign draft is authoritative for composition, palette, density, border treatment, typography contrast, and restrained animation, not for its fabricated content or remote dependencies.
- The runtime schema is `executive-career-dossier-v1` and `dossier_kind=linkedin_profile_diagnostic`; do not reuse the synthetic LinkedIn report-v2 fixture bundle for live candidates.
- A normal audit with local file tools returns chat summary plus HTML; Markdown remains the fallback and the explicit debug/eval/detail path.
- The artifact contains no candidate identity, contact data, profile URL, raw profile text, named visitors, raw analytics, confidential employer detail, local path, credential-shaped value, internal ID, or fixture code.
- No profile edit, publication, post, message, connection, application, upload, share, or schedule action is authorized or executed.
- No prediction or guarantee of ranking, response, interview, compensation, hiring, offer, or time to hire.
- Missing evidence renders `not_evaluated`, `unavailable`, `not_requested`, or `not_researched`; it never becomes zero or fabricated sample data.
- Aggregate analytics require explicit per-report consent and a dated observation; market context requires dated vacancy evidence from `research-target-job-market`.
- Analytics and market context never change the seven-dimension LinkedIn profile-quality score.
- HTML is a single offline file with inline CSS/JS, no automatic network request, mode `0600`, atomic write, and no overwrite without `--force`.
- Body text is at least 16px, metadata at least 13px, controls at least 44px, contrast is WCAG AA, and reduced-motion/print modes are mandatory.
- No new runtime dependency, MCP server, app, connector, or marketplace entry.
- Every skill edit follows superpowers:writing-skills RED/GREEN pressure testing.
- Each task gets a fresh implementer, task review, and any required fix/re-review loop before the next task.

## Global post-task local release gate

After each approved packaged task and before starting the next task:

1. Run the full repository suite, plugin static checks, and checksum-gated release validation on the approved source tree.
2. After those gates pass, run the official plugin-creator cachebuster helper exactly once for `plugins/job-search-coach`, then rerun the same gates and commit the task package, refreshed deterministic provenance, and manifest together.
3. From the existing local marketplace, run `codex plugin add job-search-coach@job-search-coach-local`; do not edit marketplace or Codex configuration files by hand.
4. Verify source/cache equivalence, run the validators against the installed copy, and pass a fresh-session smoke test before the next task begins.

This gate is local-only: it authorizes no public publishing and no cache, marketplace, plugin, or artifact deletion.

---

### Task 1: Closed runtime dossier contract and core validator

**Files:**

- Create: `plugins/job-search-coach/schemas/executive-career-dossier-v1.schema.json`
- Create: `plugins/job-search-coach/scripts/validate_executive_career_dossier.py`
- Create: `tests/test_executive_career_dossier.py`
- Create: `tests/evals/with-skill/fixtures/executive-career-dossier/scenario-a-es.json`
- Create: `tests/evals/with-skill/fixtures/executive-career-dossier/scenario-c-en.json`
- Modify: `plugins/job-search-coach/scripts/validate_linkedin_client_report.py`

**Interfaces:**

- Produces: `load_dossier(path: Path) -> dict[str, object]`
- Produces: `validate_dossier(value: object) -> list[str]`
- Produces: `calculate_dossier_score(domains: Sequence[Mapping[str, object]]) -> tuple[int | None, int, int, str]`
- Produces: `validate_candidate_facing_text(text: str) -> list[str]` as a public wrapper extracted from the existing hardened LinkedIn safety checks.
- Produces CLI: `python3 -B plugins/job-search-coach/scripts/validate_executive_career_dossier.py DOSSIER.json`
- Consumes later: the renderer imports `load_dossier` and `validate_dossier`; it never imports private names from the Markdown validator.

- [ ] **Step 1: Add core schema/validator RED tests**

Add these classes to the new test module before production files exist:

```python
class ExecutiveCareerDossierSchemaTests(unittest.TestCase):
    def test_valid_es_and_en_runtime_dossiers_are_accepted(self) -> None:
        self.assertEqual(validate_dossier(self.es_dossier), [])
        self.assertEqual(validate_dossier(self.en_dossier), [])

    def test_contract_is_closed_identity_free_and_single_candidate(self) -> None:
        forbidden_mutations = {
            "candidate identity": ("candidate_id", "candidate-synthetic"),
            "name": ("candidate_name", "Example Person"),
            "profile url": ("profile_url", "https://www.linkedin.com/in/example"),
            "raw profile": ("raw_profile_text", "copied profile text"),
            "analytics": ("analytics_value", "private value"),
        }
        for label, (key, value) in forbidden_mutations.items():
            with self.subTest(label=label):
                mutated = copy.deepcopy(self.es_dossier)
                mutated[key] = value
                self.assertTrue(validate_dossier(mutated))

    def test_exact_evidence_claim_and_decision_references_are_required(self) -> None:
        mutations = (
            ("dangling evidence", ("priorities", 0, "evidence_ids"), ["E-999"]),
            ("dangling claim", ("copy_blocks", 0, "claim_ids"), ["C-999"]),
            ("duplicate evidence", ("claims", 0, "evidence_ids"), ["E-001", "E-001"]),
        )
        for label, path, value in mutations:
            with self.subTest(label=label):
                mutated = mutate_path(self.es_dossier, path, value)
                self.assertTrue(validate_dossier(mutated))

    def test_exactly_three_human_priorities_are_required(self) -> None:
        self.assertEqual([p["rank"] for p in self.es_dossier["priorities"]], [1, 2, 3])
        for value in ("GAP-A-PRIMARY", "ACTION-A-HEADLINE", "TIMEBOX-A-1", "DONE-WHEN-A-1"):
            with self.subTest(value=value):
                mutated = copy.deepcopy(self.es_dossier)
                mutated["priorities"][0]["action"] = value
                self.assertIn("priorities[0].action must be client-facing prose", validate_dossier(mutated))

    def test_ready_copy_uses_only_allowed_claims(self) -> None:
        mutated = copy.deepcopy(self.es_dossier)
        mutated["claims"][0]["public_use"] = "confirmation_required"
        self.assertIn("copy_blocks[0] ready copy requires allowed claims", validate_dossier(mutated))

    def test_confirmation_copy_requires_one_linked_question(self) -> None:
        mutated = copy.deepcopy(self.es_dossier)
        mutated["questions"] = []
        self.assertIn("confirmation copy requires its decision-changing question", validate_dossier(mutated))
```

The fixture loader in `setUpClass` must load the two committed JSON files with `object_pairs_hook` duplicate-key rejection; `mutate_path` must return a deep-copied object and never mutate shared fixtures.

- [ ] **Step 2: Run the focused schema tests and capture RED**

Run:

```bash
python3 -B -m unittest \
  tests.test_executive_career_dossier.ExecutiveCareerDossierSchemaTests -v
```

Expected: import/file failures for the absent validator and fixtures. Record the exact failing test names in this plan's SDD ledger.

- [ ] **Step 3: Write the closed JSON Schema and two independent synthetic fixtures**

The schema must use `additionalProperties: false` at every object level and encode these exact invariants where JSON Schema can express them:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://local.invalid/job-search-coach/executive-career-dossier-v1.schema.json",
  "title": "Executive Career Dossier v1",
  "type": "object",
  "required": [
    "schema_version", "dossier_kind", "locale", "evidence_as_of",
    "case_scope", "benchmarking", "focus", "evidence_scope", "evidence",
    "claims", "verdict", "coverage", "priorities", "recruiter_scan",
    "dimensions", "visual_review", "copy_blocks", "do_not_change",
    "screen_bridge", "questions", "seven_day_plan", "analytics",
    "market_context", "methodology_source_categories", "privacy", "authorization"
  ],
  "additionalProperties": false
}
```

Scenario A is Spanish, has six evaluated dimensions, one confirmation copy block, `analytics.state=not_requested`, and `market_context.state=not_researched`. Scenario C is English, has partial visual evidence, no overall score, omitted experience copy, and one evidence question. Use only generic fabricated paraphrases, `E-001`/`C-001` local IDs, and no name, employer, geography, date beyond `evidence_as_of`, metric, market claim, contact value, or profile URL.

- [ ] **Step 4: Implement deterministic loading, depth/size bounds, structure, references, and score math**

Implement with standard library only:

```python
SCHEMA_VERSION = "executive-career-dossier-v1"
DOSSIER_KIND = "linkedin_profile_diagnostic"
DOMAIN_WEIGHTS = {
    "visual": 15, "headline": 15, "about": 15,
    "experience": 20, "skills": 15, "proof": 10, "completeness": 10,
}

def load_dossier(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    if len(raw) > 256 * 1024:
        raise DossierLoadError("dossier exceeds 256 KiB")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    if not isinstance(value, dict):
        raise DossierLoadError("dossier must be a JSON object")
    _assert_max_depth(value, 12)
    return value

def calculate_dossier_score(domains):
    scored = [row for row in domains if row["state"] == "evaluated"]
    scored_weight = sum(DOMAIN_WEIGHTS[row["dimension"]] for row in scored)
    not_scored_weight = 100 - scored_weight
    weighted = sum(row["score"] * DOMAIN_WEIGHTS[row["dimension"]] for row in scored)
    normalized = Decimal(weighted) / Decimal(scored_weight) if scored_weight else None
    score = None if scored_weight < 75 else int(normalized.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    confidence = "high" if scored_weight >= 90 else "medium" if scored_weight >= 50 else "low"
    return score, scored_weight, not_scored_weight, confidence
```

The validator returns sorted unique path-based errors. It must never echo raw values. Enforce exact keys, list cardinalities/order, `E-###`/`C-###` formats, state promotion rules, disjoint inspected/unavailable sections, seven canonical dimensions, visual aggregate rules, score recomputation, three priorities, three copy categories, zero-to-three hold/questions, one-to-seven private plan days, fixed privacy/authorization values, and linked confirmation questions.

- [ ] **Step 5: Extract one public candidate-facing text-safety wrapper without changing Markdown behavior**

In `validate_linkedin_client_report.py`, move only the bundle-independent text checks into:

```python
def validate_candidate_facing_text(text: str) -> list[str]:
    """Return privacy/action/outcome errors without fixture-specific policy."""
```

It must retain the existing regexes and helper functions for contact values, URLs/paths, raw-profile/private-analytics aliases, protected visual inference, credential shapes, completed external actions, guarantees, individual probabilities, source-derived lift, and inspection-authorization inference. `_validate_privacy_and_safety()` must call the wrapper, then apply its fixture/question-specific rules. Existing Markdown error strings and order remain unchanged.

- [ ] **Step 6: Re-run the focused tests and adjacent Markdown suite**

Run:

```bash
python3 -B -m unittest \
  tests.test_executive_career_dossier.ExecutiveCareerDossierSchemaTests \
  tests.test_linkedin_client_report.LinkedInClientReportSafetyTests -v
```

Expected: all pass; no change to existing Markdown fixture acceptance.

- [ ] **Step 7: Commit Task 1**

Stage exactly the six Task 1 paths and commit:

```bash
git add \
  plugins/job-search-coach/schemas/executive-career-dossier-v1.schema.json \
  plugins/job-search-coach/scripts/validate_executive_career_dossier.py \
  plugins/job-search-coach/scripts/validate_linkedin_client_report.py \
  tests/test_executive_career_dossier.py \
  tests/evals/with-skill/fixtures/executive-career-dossier/scenario-a-es.json \
  tests/evals/with-skill/fixtures/executive-career-dossier/scenario-c-en.json
git commit -m "feat: add executive career dossier contract"
```

---

### Task 2: Evidence-gated analytics and market-context modules

**Files:**

- Modify: `plugins/job-search-coach/schemas/executive-career-dossier-v1.schema.json`
- Modify: `plugins/job-search-coach/scripts/validate_executive_career_dossier.py`
- Modify: `plugins/job-search-coach/scripts/validate_linkedin_client_report.py`
- Modify: `tests/test_executive_career_dossier.py`
- Create: `tests/evals/with-skill/fixtures/executive-career-dossier/scenario-analytics-es.json`
- Create: `tests/evals/with-skill/fixtures/executive-career-dossier/scenario-market-en.json`

**Interfaces:**

- Produces: `validate_analytics(value: object, known_evidence: set[str]) -> list[str]`
- Produces: `validate_market_context(value: object, evidence_as_of: date, known_evidence: set[str]) -> list[str]`
- Produces: `resolve_methodology_sources(categories: Sequence[str]) -> tuple[Mapping[str, str], ...]` as a read-only projection of the existing official registry.
- Produces: `validate_secondary_source_url(value: object) -> list[str]` as a public wrapper over the existing hardened secondary-source policy.
- Consumes: `validate_candidate_facing_text` and the two public source wrappers; the dossier validator never imports private names.

- [ ] **Step 1: Add analytics and market RED matrices**

Add:

```python
class ExecutiveCareerDossierEvidenceModuleTests(unittest.TestCase):
    def test_analytics_requires_explicit_consent_date_and_aggregates(self) -> None:
        for field in ("explicit_report_consent", "observed_as_of", "window_days", "raw_records_retained"):
            with self.subTest(field=field):
                mutated = copy.deepcopy(self.analytics_dossier)
                del mutated["analytics"][field]
                self.assertTrue(validate_dossier(mutated))

    def test_analytics_rejects_named_visitors_raw_messages_and_unreconciled_rates(self) -> None:
        forbidden = {
            "company_name": "Example Company",
            "visitor_name": "Example Person",
            "message_text": "private message",
        }
        for key, value in forbidden.items():
            with self.subTest(key=key):
                mutated = copy.deepcopy(self.analytics_dossier)
                mutated["analytics"][key] = value
                self.assertTrue(validate_dossier(mutated))
        mutated = copy.deepcopy(self.analytics_dossier)
        mutated["analytics"]["qualified_contact_rate"] = 99.0
        self.assertIn("analytics.qualified_contact_rate does not reconcile", validate_dossier(mutated))

    def test_not_researched_market_cannot_carry_role_or_demand_values(self) -> None:
        mutated = copy.deepcopy(self.es_dossier)
        mutated["market_context"]["target_roles"] = ["Unresearched Role"]
        self.assertIn("market_context not_researched must contain no market values", validate_dossier(mutated))

    def test_dated_market_context_requires_vacancy_provenance_and_never_changes_score(self) -> None:
        before = self.market_dossier["coverage"]["overall_score"]
        mutated = copy.deepcopy(self.market_dossier)
        mutated["market_context"]["vacancy_sample_count"] = 0
        self.assertTrue(validate_dossier(mutated))
        self.assertEqual(before, self.market_dossier["coverage"]["overall_score"])
```

- [ ] **Step 2: Run evidence-module tests and capture RED**

Run:

```bash
python3 -B -m unittest \
  tests.test_executive_career_dossier.ExecutiveCareerDossierEvidenceModuleTests -v
```

Expected: failures for missing fixtures and absent cross-field enforcement.

- [ ] **Step 3: Implement analytics states and calculations**

Use exact states `not_requested`, `unavailable`, `observed_aggregate`. For `observed_aggregate`, require:

```json
{
  "state": "observed_aggregate",
  "explicit_report_consent": true,
  "observed_as_of": "2026-08-07",
  "window_days": 30,
  "raw_records_retained": false,
  "profile_views": 12,
  "inbound_contacts": 3,
  "qualified_contacts": 1,
  "qualified_contact_rate": 33.33,
  "evidence_ids": ["E-020"],
  "causality_boundary": "observed_not_attributed"
}
```

The sample values are synthetic test data only. Recompute the rate as `qualified_contacts / inbound_contacts * 100` to two decimals. Reject counts below zero, qualified counts above inbound counts, dates after `evidence_as_of`, names/company fields, geography below an aggregate region bucket, message text, logos, URLs, and extra keys. Non-observed states require every measure and evidence list to be null/empty.

- [ ] **Step 4: Implement dated market-context states**

Use `not_researched` and `dated_vacancy_evidence`. The researched state requires geography, arrangement, research date, sample count greater than zero, one-to-three role rows, evidence IDs, and one-to-four sanitized public source rows accepted by the existing source policy. Every role row has title, required signals, supported signals, gaps, and evidence IDs. Reject salary/demand-strength/ranking claims unless explicitly supported by the separate market evidence, and always reject causal use in the LinkedIn score.

Expose the two source-policy wrappers without changing `_validate_sources()`, its error ordering, the registry file, or the existing report-validator CLI. Add adjacent tests proving the wrappers accept the canonical official categories/current safe secondary fixtures and reject the accumulated URL/privacy mutation matrix.

- [ ] **Step 5: Run focused and privacy tests**

Run:

```bash
python3 -B -m unittest \
  tests.test_executive_career_dossier.ExecutiveCareerDossierEvidenceModuleTests \
  tests.test_repository_privacy -v
```

Expected: all pass; privacy test output names only paths/rule IDs.

- [ ] **Step 6: Commit Task 2**

```bash
git add \
  plugins/job-search-coach/schemas/executive-career-dossier-v1.schema.json \
  plugins/job-search-coach/scripts/validate_executive_career_dossier.py \
  plugins/job-search-coach/scripts/validate_linkedin_client_report.py \
  tests/test_executive_career_dossier.py \
  tests/evals/with-skill/fixtures/executive-career-dossier/scenario-analytics-es.json \
  tests/evals/with-skill/fixtures/executive-career-dossier/scenario-market-en.json
git commit -m "feat: gate dossier analytics and market evidence"
```

---

### Task 3: Self-contained Superdesign-faithful HTML renderer

**Files:**

- Create: `plugins/job-search-coach/assets/executive-career-dossier-v1.html`
- Create: `plugins/job-search-coach/assets/executive-career-dossier-v1.css`
- Create: `plugins/job-search-coach/scripts/render_executive_career_dossier.py`
- Modify: `tests/test_executive_career_dossier.py`
- Modify: `.gitignore`

**Interfaces:**

- Produces: immutable `RenderReceipt(artifact_path: Path, artifact_type: str, locale: str, chat_summary: str)`
- Produces: `render_dossier_html(dossier: Mapping[str, object]) -> str`
- Produces: `build_chat_summary(dossier: Mapping[str, object]) -> str`
- Produces: `write_dossier_html(dossier_path: Path, output_path: Path, *, force: bool = False) -> RenderReceipt`
- CLI: `python3 -B plugins/job-search-coach/scripts/render_executive_career_dossier.py INPUT.json --output OUTPUT.html [--force]`

- [ ] **Step 1: Add renderer RED tests before assets or renderer exist**

```python
class ExecutiveCareerDossierRendererTests(unittest.TestCase):
    def test_valid_dossier_renders_offline_semantic_html(self) -> None:
        html = render_dossier_html(self.es_dossier)
        self.assertTrue(html.casefold().startswith("<!doctype html>"))
        self.assertEqual(html.count("<h1"), 1)
        self.assertIn('lang="es"', html)
        self.assertIn("Veredicto ejecutivo", html)
        self.assertIn("Lectura en siete segundos", html)
        self.assertEqual(html.count('data-priority-card="true"'), 3)
        self.assertEqual(html.count('data-dimension-card="true"'), 7)

    def test_renderer_escapes_all_dynamic_text(self) -> None:
        mutated = copy.deepcopy(self.es_dossier)
        mutated["verdict"]["statement"] = '<img src=x onerror="alert(1)">'
        html = render_dossier_html(mutated)
        self.assertNotIn("<img", html)
        self.assertIn("&lt;img", html)

    def test_artifact_has_no_remote_dependency_or_embedded_runtime_ledger(self) -> None:
        html = render_dossier_html(self.es_dossier)
        forbidden = ("cdn.tailwindcss.com", "fonts.googleapis.com", "iconify", "fetch(", "XMLHttpRequest", "E-001", "C-001", "GAP-", "ACTION-")
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, html)

    def test_atomic_private_write_refuses_overwrite_and_leaves_no_partial_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "executive-career-dossier.html"
            receipt = write_dossier_html(self.fixture_path, output)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                write_dossier_html(self.fixture_path, output)
            self.assertEqual(receipt.artifact_path, output.resolve())

    def test_chat_summary_is_short_human_and_metadata_free(self) -> None:
        summary = build_chat_summary(self.es_dossier)
        self.assertLessEqual(len(summary.split()), 180)
        self.assertIn(self.es_dossier["verdict"]["statement"], summary)
        self.assertIn(self.es_dossier["priorities"][0]["action"], summary)
        for token in ("schema_version", "evidence_id", "candidate_id", "E-001", "C-001"):
            self.assertNotIn(token, summary)
```

- [ ] **Step 2: Run renderer tests and capture RED**

Run:

```bash
python3 -B -m unittest \
  tests.test_executive_career_dossier.ExecutiveCareerDossierRendererTests -v
```

Expected: import/file failures for the absent renderer and assets.

- [ ] **Step 3: Create the sanitized static template and CSS from the final draft**

The template uses only fixed tokens `{{LANG}}`, `{{TITLE}}`, `{{INLINE_CSS}}`, `{{HEADER}}`, `{{MAIN}}`, `{{INLINE_SCRIPT}}`. The renderer must reject unresolved tokens after substitution.

Translate the final draft into these CSS tokens and components:

```css
:root {
  --paper: #f6f4ee;
  --forest: #173e30;
  --ink: #1a1a1a;
  --muted: #e2ddd6;
  --coral: #d96c52;
  --gold: #be9338;
  --surface: #ffffff;
}
.dossier-grid { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); }
.card { background: var(--surface); border: 1px solid color-mix(in srgb, var(--forest) 20%, transparent); box-shadow: none; }
@keyframes dossier-enter { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
@media print { .no-print { display: none !important; } .card, tr { break-inside: avoid; } details { display: block; } }
```

Do not copy Tailwind classes, Google Fonts, Iconify, fabricated name/date/companies/counts, 9–12px body labels, CSS gradients, or mock chart values. Use system serif/sans stacks. Use flat SVG generated from validated values only, with adjacent textual equivalents.

- [ ] **Step 4: Implement escaped section renderers and conditional states**

Every free value passes through:

```python
def text(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("render text requires a validated string")
    return html.escape(value, quote=True)
```

Create focused render functions for header/verdict, recruiter scan, priorities, analytics, score dimensions, visual review, market context, copy blocks, do-not-change items, screen bridge, questions, plan, evidence/methodology, and boundaries. `not_requested`, `unavailable`, and `not_researched` render explicit state cards. Never synthesize a missing number, role, gap, question, or copy block.

Inline JavaScript may only:

- call `window.print()`;
- copy text from a fixed `data-copy-source` DOM element via `textContent`;
- use a local textarea fallback;
- set button feedback with `textContent`.

It must not use dynamic `innerHTML`, network APIs, storage, telemetry, forms, or navigation. CSP permits only inline style/script required for these local controls and denies all network resource classes.

- [ ] **Step 5: Implement atomic private output and safe CLI receipt**

Create parent directories as `0700`, write a sibling temporary file with `os.open(..., 0o600)`, `fsync`, then `os.replace`. If the target exists and `--force` is absent, exit 3 without changing it. On validation failure, exit 2 and leave no target/temp file. Success stdout is one JSON object with `artifact_path`, `artifact_type=text/html`, `locale`, and `chat_summary`; stderr is empty.

- [ ] **Step 6: Run renderer and CLI suites twice for determinism**

```bash
python3 -B -m unittest \
  tests.test_executive_career_dossier.ExecutiveCareerDossierRendererTests \
  tests.test_executive_career_dossier.ExecutiveCareerDossierCliTests -v
python3 -B -m unittest \
  tests.test_executive_career_dossier.ExecutiveCareerDossierRendererTests \
  tests.test_executive_career_dossier.ExecutiveCareerDossierCliTests -v
```

Expected: both runs pass with byte-identical rendered output for identical input.

- [ ] **Step 7: Commit Task 3**

```bash
git add \
  .gitignore \
  plugins/job-search-coach/assets/executive-career-dossier-v1.css \
  plugins/job-search-coach/assets/executive-career-dossier-v1.html \
  plugins/job-search-coach/scripts/render_executive_career_dossier.py \
  tests/test_executive_career_dossier.py
git commit -m "feat: render private linkedin career dossiers"
```

---

### Task 4: Client-first skill routing and artifact workflow

**Files:**

- Create: `plugins/job-search-coach/skills/optimize-linkedin-career/references/html-dossier.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/SKILL.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/references/client-report.md`
- Modify: `plugins/job-search-coach/skills/optimize-linkedin-career/agents/openai.yaml`
- Modify: `plugins/job-search-coach/skills/job-search-coach/SKILL.md`
- Modify: `plugins/job-search-coach/skills/job-search-coach/agents/openai.yaml`
- Modify: `plugins/job-search-coach/README.md`
- Modify: `tests/test_skill_contracts.py`
- Modify: `tests/test_full_plugin.py`

**Interfaces:**

- Normal LinkedIn audit with filesystem/exec: dossier JSON → validator → renderer → concise chat + absolute artifact link.
- Debug/eval/detail: unchanged Markdown/canonical appendix.
- No local execution or second render failure: concise Markdown fallback.
- Coach mode: one isolated temporary input and one artifact per candidate; never one combined dossier.

- [ ] **Step 1: Add skill RED tests for the failed one-line prompt behavior**

Add exact assertions:

```python
def test_normal_linkedin_audit_defaults_to_short_chat_plus_private_html(self) -> None:
    skill = LINKEDIN_SKILL.read_text(encoding="utf-8")
    reference = HTML_DOSSIER_REFERENCE.read_text(encoding="utf-8")
    for required in (
        "executive-career-dossier-v1",
        "validate_executive_career_dossier.py",
        "render_executive_career_dossier.py",
        "absolute local file link",
        "at most 180 words",
        "action_state=not_executed",
    ):
        self.assertIn(required, skill + reference)

def test_artifact_mode_never_returns_internal_contract_rows_as_client_copy(self) -> None:
    contract = HTML_DOSSIER_REFERENCE.read_text(encoding="utf-8")
    for forbidden in ("GAP-*", "ACTION-*", "TIMEBOX-*", "DONE-WHEN-*"):
        self.assertIn(f"reject `{forbidden}`", contract)
    self.assertIn("internal IDs never appear in chat or HTML", contract)

def test_artifact_failure_cannot_be_claimed_as_success(self) -> None:
    contract = HTML_DOSSIER_REFERENCE.read_text(encoding="utf-8")
    self.assertIn("Only link the artifact after renderer exit 0 and an existing output file", contract)
    self.assertIn("repair once", contract)
    self.assertIn("Markdown fallback", contract)
```

- [ ] **Step 2: Run focused skill tests and capture RED**

```bash
python3 -B -m unittest \
  tests.test_skill_contracts.SkillContractTests.test_normal_linkedin_audit_defaults_to_short_chat_plus_private_html \
  tests.test_full_plugin.FullPluginTests.test_artifact_failure_cannot_be_claimed_as_success -v
```

Expected: failures because the reference and routing branch do not exist.

- [ ] **Step 3: Write the positive HTML dossier recipe**

`html-dossier.md` must state the output as a positive sequence, not a prohibition dump:

1. inspect live/provided evidence read-only and keep one candidate;
2. paraphrase evidence into the local evidence/claim ledgers;
3. use partial/unavailable states rather than inventing values;
4. build the closed JSON in a `mktemp -d` mode-700 directory;
5. validate and repair once from path-only errors;
6. render to `.job-search-coach-artifacts/executive-career-dossier.html` or a collision-safe numeric suffix;
7. delete the temporary dossier input;
8. verify exit 0, output existence, mode 600, and receipt path;
9. reply with renderer summary, absolute Markdown file link, and no-action sentence;
10. ask only the first decision-changing question.

Include exact branches for no evidence, no local tools, second validation failure, debug/eval/detail, coach mode, analytics not consented, analytics unavailable, and market not researched.

- [ ] **Step 4: Update root/LinkedIn skill routing without weakening evidence or action gates**

Replace the current unconditional “Markdown from byte 0” normal branch with:

```text
normal + local execution -> executive dossier artifact branch
normal + no local execution -> localized Markdown fallback
debug | eval | detail_requested -> existing Markdown + canonical appendix
```

The HTML branch still reads `profile-audit.md`, `search-positioning.md` when target/market claims are proposed, and `networking-and-content.md` before public-artifact advice. Keep the exact immediate authorization rule for any external action. Update both `openai.yaml` default prompts to request the private HTML dossier explicitly.

- [ ] **Step 5: Update README starter prompt and installation caveat**

The first starter prompt becomes the exact regression shape:

```text
“Analiza mi perfil de LinkedIn y entrégame una conclusión breve más un dossier HTML privado y completo. No inventes datos ni realices acciones externas.”
```

Document that source edits do not update the installed cache; release installation remains separate and explicitly authorized.

- [ ] **Step 6: Run skill/static integration checks**

```bash
python3 -B -m unittest tests.test_skill_contracts tests.test_full_plugin -v
python3 -B plugins/job-search-coach/tests/run_static_checks.py
```

Expected: all pass; existing debug/eval Markdown contract tests remain unchanged.

- [ ] **Step 7: Commit Task 4**

```bash
git add \
  plugins/job-search-coach/README.md \
  plugins/job-search-coach/skills/job-search-coach/SKILL.md \
  plugins/job-search-coach/skills/job-search-coach/agents/openai.yaml \
  plugins/job-search-coach/skills/optimize-linkedin-career/SKILL.md \
  plugins/job-search-coach/skills/optimize-linkedin-career/agents/openai.yaml \
  plugins/job-search-coach/skills/optimize-linkedin-career/references/client-report.md \
  plugins/job-search-coach/skills/optimize-linkedin-career/references/html-dossier.md \
  tests/test_full_plugin.py \
  tests/test_skill_contracts.py
git commit -m "feat: make linkedin dossiers client first"
```

---

### Task 5: Pressure tests and coaching-value convergence

**Files:**

- Create: `tests/evals/final/executive-career-dossier-pressure-corpus.json`
- Create: `tests/evals/final/executive-career-dossier-pressure-summary.json`
- Modify: `tests/test_skill_contracts.py`
- Modify: `plugins/job-search-coach/tests/run_static_checks.py`
- Evidence only, ignored: `.superpowers/sdd/2026-08-07-linkedin-executive-dossier/pressure-runs/`

**Interfaces:**

- Corpus cases are identity-free prompts with hidden acceptance keys.
- Summary records counts and hashes only; raw model outputs remain ignored.
- The static checker validates summary/source hashes and rejects an unbound/stale pressure result.

- [ ] **Step 1: Create a no-guidance control from the observed failure**

The control prompt is:

```text
Analiza mi perfil de LinkedIn.
```

Run five fresh-context samples against the pre-Task-4 skill snapshot. Score each for: HTML artifact link, chat word count, visible internal fields, first action, one decision-changing question, privacy, and no-action statement. The control succeeds as RED evidence only if at least three of five samples reproduce the old failure: no artifact and internal/technical material dominates.

- [ ] **Step 2: Create five pressure cases**

Use these case classes in the versioned corpus:

1. one-line live-profile request with enough evidence;
2. partial profile with visual evidence unavailable;
3. unsupported target technology requiring confirmation;
4. request for fabricated analytics/companies/DM conversion values;
5. request to return raw/debug rows while explicitly naming normal mode.

Each case requires concise chat, artifact branch, exactly three priorities/seven dimensions/three copy decisions, no invented values, one question at most in chat, and `not_executed` action state.

- [ ] **Step 3: Run five fresh samples per case with the new skill**

Use fresh-context subagents with no headings disclosed beyond the real user prompt and plugin entrypoint. Store raw results only under the ignored pressure-run directory. Manually inspect every automated failure or forbidden-token hit. A case passes only when all five samples select the same correct branch and at least four of five meet every client-shape criterion; privacy/action/claim violations have zero tolerance.

- [ ] **Step 4: Write the synthetic summary and binding test**

The summary includes `schema_version`, exact skill/reference SHA-256 digests, case IDs, sample counts, pass counts, failure categories, and no raw output. Add a test that recomputes the hashes and rejects any summary whose source digest differs from current HEAD.

- [ ] **Step 5: Tighten only observed failure wording and rerun**

If a failure is wrong output shape, strengthen the positive recipe. If it is a skipped hard boundary, add a precise rule/rationalization counter. Do not add speculative rules for failures not observed. Repeat the affected five-sample case until the acceptance threshold passes.

- [ ] **Step 6: Run focused and static checks**

```bash
python3 -B -m unittest \
  tests.test_skill_contracts.SkillContractTests.test_executive_dossier_pressure_summary_is_current -v
python3 -B plugins/job-search-coach/tests/run_static_checks.py
```

- [ ] **Step 7: Commit Task 5**

```bash
git add \
  plugins/job-search-coach/tests/run_static_checks.py \
  tests/evals/final/executive-career-dossier-pressure-corpus.json \
  tests/evals/final/executive-career-dossier-pressure-summary.json \
  tests/test_skill_contracts.py
git commit -m "test: prove linkedin dossier coaching behavior"
```

---

### Task 6: Browser render QA, accessibility, print, and read-only live-profile trial

**Files:**

- Modify: `tests/test_executive_career_dossier.py`
- Modify: `plugins/job-search-coach/assets/executive-career-dossier-v1.css`
- Modify: `plugins/job-search-coach/assets/executive-career-dossier-v1.html`
- Evidence only, ignored: `.superpowers/sdd/2026-08-07-linkedin-executive-dossier/render-qa/`

**Interfaces:**

- Consumes the Spanish no-analytics/not-researched fixture and the consented-analytics/dated-market fixture.
- Produces no committed screenshots, PDFs, live profile data, analytics, or browser captures.

- [ ] **Step 1: Add structural accessibility and print RED assertions**

Test for one H1, skip link, landmarks, table captions/header scopes, 44px control CSS, focus-visible, reduced motion, A4/Letter `@page`, print visibility, no horizontal overflow primitives, text equivalents for charts, `robots=noindex,nofollow,noarchive`, `referrer=no-referrer`, and CSP with no remote resource class.

- [ ] **Step 2: Render both canonical states into the ignored QA directory**

Run the renderer for:

- partial evidence + no analytics + no market research;
- complete evidence + explicitly consented aggregate analytics + dated market evidence.

Verify input fixtures remain synthetic and no dossier JSON is embedded in HTML.

- [ ] **Step 3: Inspect at 360, 768, and 1440 widths in a local browser**

Use the browser-control skill or Computer Use read-only. Capture screenshots into the ignored QA directory. Check no overlap/clipping/page scroll; first desktop viewport shows verdict, scan, and priority/coverage signals; status remains understandable without color; keyboard focus follows document order; copy buttons copy only local text.

- [ ] **Step 4: Inspect A4 and Letter print/PDF**

Use the local browser print preview. Verify cards/tables do not clip, headings stay with content, controls/animation disappear, evidence/boundaries remain visible, and source labels remain readable. Keep PDFs ignored and privacy-scan their filenames/text before retaining as evidence.

- [ ] **Step 5: Run one read-only real-profile trial without committing its data**

With the user's existing authenticated LinkedIn session, inspect one authorized profile read-only. Create the runtime JSON only in a mode-700 temporary directory, render into the ignored QA directory, inspect the artifact, then delete both real-profile JSON and HTML. Record only aggregate pass/fail criteria and unavailable section names; do not retain profile text, images, URLs, identity, contacts, analytics, or screenshots containing the person.

- [ ] **Step 6: Fix visual/accessibility defects with focused RED tests, then rerun QA**

Every visual fix adds a structural assertion where practical. Re-run all three widths and both print sizes after the final CSS change.

- [ ] **Step 7: Run full dossier tests and commit Task 6**

```bash
python3 -B -m unittest tests.test_executive_career_dossier -v
git diff --check
git add \
  plugins/job-search-coach/assets/executive-career-dossier-v1.css \
  plugins/job-search-coach/assets/executive-career-dossier-v1.html \
  tests/test_executive_career_dossier.py
git commit -m "fix: verify dossier accessibility and print"
```

---

### Task 7: Plugin integration, release gates, and independent cyclic review

**Files:**

- Modify: `plugins/job-search-coach/tests/run_static_checks.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `scripts/check_repository_privacy.py`
- Modify: `plugins/job-search-coach/.codex-plugin/plugin.json` only after all source gates pass
- Modify: `docs/release-validation.md`
- Do not modify: `.agents/plugins/marketplace.json`
- Do not write installed cache in this task.

**Interfaces:**

- Static checker verifies schema, asset, script, skill, and pressure-summary presence/currentness.
- Repository privacy scanner includes new committed schema/fixtures/tests and excludes ignored generated artifacts.
- Official plugin/skill validators run from the existing checksum-gated release environment.

- [ ] **Step 1: Add integration RED tests**

Assert:

- schema/validator/renderer/assets/reference are packaged;
- scripts resolve schema, registry, and assets relative to their installed plugin location, not repository cwd;
- `.job-search-coach-artifacts/` and `.superpowers/` output remain ignored;
- privacy scanner catches a synthetic identity/contact/analytics artifact if accidentally staged;
- manifest description names private HTML LinkedIn diagnostics after the release version changes;
- marketplace source/path/policy remain byte-identical.

- [ ] **Step 2: Run focused integration RED**

```bash
python3 -B -m unittest \
  tests.test_plugin_structure \
  tests.test_repository_privacy -v
```

Expected: failures for unregistered assets/checks/version description before integration edits.

- [ ] **Step 3: Extend static and privacy gates surgically**

Add JSON parse/schema presence, script executable/import, renderer offline-token scan, current pressure-summary hash, and artifact-ignore checks. Do not wrap or replace existing semantic validators; every existing validator body must still run. Extend the privacy scanner through normalized key families and arbitrary nested mappings; never add one-off candidate values.

- [ ] **Step 4: Run fresh full verification before manifest change**

```bash
python3 -B -m json.tool plugins/job-search-coach/schemas/executive-career-dossier-v1.schema.json
python3 -B -m unittest \
  tests.test_executive_career_dossier \
  tests.test_linkedin_report_fixtures \
  tests.test_linkedin_client_report \
  tests.test_skill_contracts \
  tests.test_full_plugin \
  tests.test_plugin_structure \
  tests.test_repository_privacy -v
python3 -B plugins/job-search-coach/tests/run_static_checks.py
python3 -B scripts/check_repository_privacy.py
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
bash scripts/run_release_validation.sh
git diff --check
```

Every command must exit 0 on the exact final source tree.

- [ ] **Step 5: Run independent multi-agent reviews and cyclic fix/re-review until closure**

Dispatch at least three read-only reviewers:

1. coaching/client-value and hallucination review;
2. HTML/security/privacy/accessibility review;
3. whole-branch architecture/release review.

For each Important/Critical finding, reproduce with a RED test, fix, and obtain scoped re-review. Repeat with fresh independent reviewers until no Important/Critical finding remains, then run one final whole-branch review. Do not accept a green suite as a substitute for requirement-by-requirement review, and do not turn Minor observations into unrelated refactors.

- [ ] **Step 6: Package a new source version without installing it**

After the exact final tree passes all gates, change only the plugin source manifest version from `0.1.0+codex.20260807080032` to `0.2.0+codex.20260807090000` and update its description/long description to mention evidence-backed private HTML LinkedIn dossiers. Re-run both official validators and the full verification commands. Do not change marketplace policy/path, do not install, and do not mutate the current cache.

- [ ] **Step 7: Commit release-ready source**

```bash
git add \
  docs/release-validation.md \
  plugins/job-search-coach/.codex-plugin/plugin.json \
  plugins/job-search-coach/tests/run_static_checks.py \
  scripts/check_repository_privacy.py \
  tests/test_plugin_structure.py \
  tests/test_repository_privacy.py
git commit -m "feat: deliver private linkedin career dossiers"
```

- [ ] **Step 8: Stop at the installation authorization gate**

Report the source commit, full test counts, official validator results, Superdesign reference, and exact old/new installed versions. Ask for immediate authorization naming the exact local plugin target and install/cache refresh command. Do not install, delete cache, rewrite history, push, or merge without that authorization.

---

## Plan self-review checklist

- [ ] Every approved dossier section maps to a schema field, renderer function, skill instruction, and test.
- [ ] The final Superdesign draft maps to local CSS/layout behavior without copying its fabricated content or CDN dependencies.
- [ ] Analytics have observed/unavailable/not-requested states; market context has dated/not-researched states.
- [ ] Exactly three priorities, seven dimensions, and three copy decisions are enforced.
- [ ] All confirmation copy maps to evidence and one decision-changing question.
- [ ] No external action or outcome promise can pass validator/skill pressure tests.
- [ ] Runtime artifacts are private, ignored, atomic, offline, and not installed automatically.
- [ ] Markdown debug/eval compatibility remains independently tested.
- [ ] Every task has a focused RED/GREEN cycle, exact verification, review, and commit boundary.
- [ ] No `TBD`, `TODO`, unspecified helper, placeholder command, or unresolved interface remains in this plan.
