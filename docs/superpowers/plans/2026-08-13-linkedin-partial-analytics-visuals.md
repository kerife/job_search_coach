# LinkedIn Partial Aggregate Analytics Visuals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a versioned dossier that accepts consented partial LinkedIn aggregate analytics, computes only compatible descriptive measures, and renders accessible KPI and composition visuals without retaining raw data or changing v1/v2 behavior.

**Architecture:** Create `executive-career-dossier-v3` as a closed extension of the published v2 contract. A pure v3-to-v2 projection removes/reconciles the new analytics shape; v3 validation delegates all unchanged profile/coverage/coaching behavior to v2 and validates analytics separately. A v3 renderer composes the v2 renderer while replacing only the analytics region, so optional market composition remains independent.

**Tech Stack:** Python 3.11+, standard library only, JSON Schema draft 2020-12 subset, integer arithmetic, `unittest`, offline semantic HTML/CSS, existing private loaders/writers and Superdesign parity tooling.

## Global Constraints

- Preserve v1 and published v2 schemas, validators, renderers, fixtures, CLI behavior, and no-market/market behavior unchanged.
- V3 analytics states are exactly `not_requested`, `unavailable`, `observed_partial`, and `observed_complete`.
- Every observed branch requires explicit report consent, observation date, no raw records retained, one local common window, evidence references, and `observed_not_attributed` causality boundary.
- Allowed metrics are `profile_views`, `recruiter_viewers`, `inbound_contacts`, and `qualified_contacts`; each appears at most once and is a non-negative integer.
- No value, date, candidate, percentage, or window from the user's current report is hardcoded. Live values are re-confirmed at run time.
- `other_views` and proportions/rates are derived only from compatible inputs and are never accepted from caller input.
- Missing or incompatible observations remain useful standalone KPIs but suppress their derived chart; no fabricated zero or estimate.
- No identity, visitor/company identity, message/contact text, screenshot, cookie, session data, raw record, profile URL, local path, private analytics value, internal ID, or source snapshot appears in HTML or diagnostics.
- Analytics never changes the LinkedIn score, vacancy score, recurrence, or learning decision.
- No remote asset, chart library, CDN, canvas, SVG, trend line, form, external action, local storage, or relaxed CSP.
- Publish/install only after independent review and all gates; use exactly one cachebuster per increment and leave the public marketplace identity unchanged.

---

### Task 1: V3 partial analytics schema, projection, and validation

**Files:**
- Create: `plugins/professional-growth-coach/schemas/executive-career-dossier-v3.schema.json`
- Create: `plugins/professional-growth-coach/scripts/executive_career_dossier_v3_compat.py`
- Create: `plugins/professional-growth-coach/scripts/validate_executive_career_dossier_v3.py`
- Create: `tests/test_executive_career_dossier_v3.py`
- Create: `tests/evals/with-skill/fixtures/executive-career-dossier-v3/partial-analytics-es.json`
- Create: `tests/evals/with-skill/fixtures/executive-career-dossier-v3/complete-analytics-en.json`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

**Interfaces:**
- Produces `project_v3_to_v2(value: Mapping[str, object]) -> dict[str, object]`.
- Produces `validate_dossier(value: object) -> list[str]`, `load_dossier(path: Path) -> dict[str, object]`, `analytics_metrics(value) -> dict[str, int]`, `analytics_composition(value) -> dict[str, int] | None`, and `_cli(argv) -> int`.

- [ ] **Step 1: Write RED state and partial-observation tests**

Build v3 fixtures from valid v2 fixtures. The partial ES fixture contains
synthetic `profile_views=40` and `recruiter_viewers=8` in `WINDOW-001` for 30
days. The complete EN fixture contains synthetic values for all four metrics.
Assert v1/v2 fixtures are untouched and valid, v3 partial/complete validate
only after implementation, and v3 projects deep-equal to v2 except for the
documented fixed analytics fallback/conversion.

- [ ] **Step 2: Observe RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v3 -v
```

Expected: missing v3 validator import.

- [ ] **Step 3: Add arithmetic, privacy, and malformed-input RED cases**

Assert partial composition returns `other_views=32` and
`recruiter_share_percent=20`; zero total returns zero share. Assert complete
contacts derive an integer-half-up `qualified_contact_rate_percent`; zero
inbound returns no rate. Add cases for every missing/duplicate/unknown metric,
partial labelled complete, four metrics labelled partial, negative/non-integer
counts, `recruiter_viewers > profile_views`, qualified above inbound, duplicate
window ID, incompatible date/window, future date, unknown evidence ID, raw
records/private fields, additional keys, duplicate JSON, recursion, invalid
UTF-8, oversize input, FIFO, leaf/intermediate symlink, control characters,
and diagnostics that never echo sentinels.

- [ ] **Step 4: Create the closed v3 schema**

Copy the complete v2 schema, change only `schema_version` and the analytics
definition. Observed analytics requires
`explicit_report_consent`, `observed_as_of`, `raw_records_retained=false`,
`observations`, `evidence_ids`, and
`causality_boundary=observed_not_attributed`. Each closed observation has
`metric`, integer `value`, `window_id` matching `^WINDOW-[0-9]{3}$`, and
positive integer `window_days`. Partial has one through three unique metrics;
complete has exactly four. Semantic validation enforces uniqueness and exact
complete membership.

- [ ] **Step 5: Implement pure projection and semantic validation**

Deep-copy input. Change v3 to v2 and convert analytics:

- not-requested/unavailable keep the legacy reason branches;
- partial becomes v2 `unavailable` with one fixed localized-neutral reason;
- complete becomes v2 `observed_aggregate` only after compatible-window and
  count validation, with the derived qualified rate.

Delegate projected object to v2 validation, then validate v3 analytics and the
original privacy tree. Use integer half-up helpers, never floating-point source
values. Return sorted unique fixed errors. Follow v2 descriptor boundary,
depth-12, 256-KiB, duplicate-key, recursion, and bounded CLI patterns.

- [ ] **Step 6: Verify GREEN and conformance**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugins/professional-growth-coach/scripts \
  python3 -B -m unittest \
  tests.test_executive_career_dossier_v3 \
  tests.test_executive_career_dossier_v2 \
  tests.test_executive_career_dossier \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py -v
git diff --check
```

- [ ] **Step 7: Commit Task 1**

```bash
git add \
  plugins/professional-growth-coach/schemas/executive-career-dossier-v3.schema.json \
  plugins/professional-growth-coach/scripts/executive_career_dossier_v3_compat.py \
  plugins/professional-growth-coach/scripts/validate_executive_career_dossier_v3.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  tests/evals/with-skill/fixtures/executive-career-dossier-v3 \
  tests/test_executive_career_dossier_v3.py
git commit -m "feat: validate partial linkedin analytics"
```

---

### Task 2: Accessible KPI and composition rendering

**Files:**
- Create: `plugins/professional-growth-coach/assets/executive-career-dossier-v3.css`
- Create: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v3.py`
- Modify: `plugins/professional-growth-coach/scripts/private_asset_loader.py`
- Modify: `.superdesign/init/theme.md`
- Modify: `.superdesign/design-system.md`
- Modify: `tests/test_executive_career_dossier_v3.py`
- Modify: `tests/test_dark_mode_accessibility.py`
- Modify: `tests/test_print_continuity_footer_integrity.py`
- Modify: `tests/test_private_asset_boundary.py`
- Modify: `tests/test_superdesign_theme_asset_parity.py`

**Interfaces:**
- Consumes Task 1 v3 validator/helpers and v2 renderer with optional market artifact.
- Produces `render_dossier_html(dossier, market_dossier=None) -> str`, `write_dossier_html(..., market_dossier_path=None, force=False) -> RenderReceipt`, and CLI parity with v2.

- [ ] **Step 1: Write renderer RED tests**

Assert partial analytics renders exactly two KPI values, one comparable
segmented composition, exact other/recruiter counts and rounded share once,
window/date, and one causal/quality boundary. Assert missing recruiter metric
renders available profile-views KPI but no segmented bar. Assert incompatible
windows fail validation. Complete renders four KPI values and the derived rate
only when inbound is positive. Not-requested/unavailable preserve prior text
without metrics. EN/ES tests reject internal enums, IDs, private values, or
duplicate percentage prose.

- [ ] **Step 2: Observe RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v3.ExecutiveCareerDossierV3RendererTests -v
```

Expected: missing v3 renderer.

- [ ] **Step 3: Compose v3 renderer from v2**

Validate/freeze v3, project to v2, and reuse v2 header, coverage ledger,
coach priorities, market composition, copy studio, plan, and writer boundaries.
Replace only the analytics block with `_render_v3_analytics`. Preserve optional
market dossier snapshot validation and v2 placeholder behavior. Escape every
display value and never render window IDs, evidence IDs, or snapshots.

- [ ] **Step 4: Implement semantic visuals and no-duplication CSS**

KPI items use a semantic description list. The composition uses one named
figure with visible exact segment labels/counts and one visible rounded share;
CSS widths derive from validated percentage through an inline custom property
whose value is an integer 0–100, not untrusted text. Add a text fallback and
do not use the CSS width as the only value carrier.

At mobile, stack KPI/segment labels; no overflow or nowrap dependency. Print
keeps figure/labels together. Forced-colors uses system colors and borders;
grayscale meaning remains in text. Add exact CSS bytes to Superdesign parity.

- [ ] **Step 5: Verify renderer, DOM, privacy, responsive, and compatibility**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v3 \
  tests.test_executive_career_dossier_v2 \
  tests.test_dark_mode_accessibility \
  tests.test_print_continuity_footer_integrity \
  tests.test_private_asset_boundary \
  tests.test_superdesign_theme_asset_parity -v
git diff --check
```

Render EN/ES partial and complete fixtures to a private temp directory and
assert unique IDs, zero missing ARIA references, no remote resources/handlers,
one H1/main/footer, exact value counts, no duplication, and 0600 output. Record
browser/AT QA separately.

- [ ] **Step 6: Commit Task 2**

```bash
git add \
  .superdesign/design-system.md \
  .superdesign/init/theme.md \
  plugins/professional-growth-coach/assets/executive-career-dossier-v3.css \
  plugins/professional-growth-coach/scripts/private_asset_loader.py \
  plugins/professional-growth-coach/scripts/render_executive_career_dossier_v3.py \
  tests/test_dark_mode_accessibility.py \
  tests/test_executive_career_dossier_v3.py \
  tests/test_print_continuity_footer_integrity.py \
  tests/test_private_asset_boundary.py \
  tests/test_superdesign_theme_asset_parity.py
git commit -m "feat: visualize partial linkedin analytics"
```

---

### Task 3: Default routing, package validation, release, and live report

**Files:**
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/SKILL.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/references/html-dossier.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/references/profile-audit.md`
- Modify: `plugins/professional-growth-coach/README.md`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `tests/test_repository_privacy.py`
- Modify: `tests/test_skill_contracts.py`
- Modify once: `plugins/professional-growth-coach/.codex-plugin/plugin.json` through the official cachebuster.
- Modify mechanically: `tests/evals/final/cycle-1/*.json`, `tests/evals/final/cycle-2/*.json`, `tests/evals/final/cycle-1.md`, `tests/evals/final/cycle-2.md`, and `tests/evals/final/installed-smoke-test.md`.
- Create ignored evidence: `.superpowers/sdd/2026-08-13-linkedin-partial-analytics-visuals/task-3-report.md`.

**Interfaces:**
- Produces default v3 only after explicit aggregate-report consent; without consent, v3 records `not_requested` and does not inspect analytics.

- [ ] **Step 1: Add RED routing and package tests**

Require v3 normal artifact routing, separate analytics consent, partial-state
preservation, no raw retention, no implied authorization from profile-section
inspection, complete package inventory, installed validator/renderer smokes,
and v1/v2 compatibility. Reject any instruction to browse identities/messages,
persist raw analytics, edit, message, connect, apply, or publish.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_full_plugin \
  tests.test_plugin_structure \
  tests.test_repository_privacy \
  tests.test_skill_contracts -v
```

Expected: the new v3 routing and package assertions fail while prior-version
checks stay green.

- [ ] **Step 2: Update routing and package checks**

Document one explicit analytics-consent question when analytics would
materially improve the report. On approval inspect only aggregate values,
discard raw records, generate a new collision-safe artifact, and never reuse
the consent. Extend static/privacy/release checks for v3 schema/scripts/CSS and
fixtures without weakening prior versions.

- [ ] **Step 3: Run pre-cachebuster gates and independent reviews**

Run focused v3/v2/v1, full plugin, static, privacy, official release, full root,
design parity, dark/forced-colors, print, and descriptor-boundary suites on the
default Python and CPython 3.11. Resolve all Critical/Important findings.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v3 \
  tests.test_executive_career_dossier_v2 \
  tests.test_executive_career_dossier \
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

Repeat the v3/v2/v1 and full plugin suites with
`/Users/kevinriosferrer/.local/bin/python3.11` when it exists. Only stale
final-eval provenance is permitted before the cachebuster.

- [ ] **Step 4: Cachebust once, install, prove parity, attest, and publish**

Run the official cachebuster exactly once:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  /Users/kevinriosferrer/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py \
  plugins/professional-growth-coach
git add plugins/professional-growth-coach/.codex-plugin/plugin.json
git commit -m "chore: bump partial analytics cachebuster"
```

Install the exact local version using the repository's established marketplace
command. Verify it with `codex plugin list --json`; require silent
`diff -qr --exclude='__pycache__'`, equal normalized file sets/counts, and equal
path-plus-file-SHA256 hashes. Rebind 12 cycle JSONs, two indexes, and installed
smoke to the cachebuster commit/tree. Then run:

```bash
git add tests/evals/final
git commit -m "test: attest partial analytics installation"
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
authorization, then require `git rev-parse HEAD` and
`git rev-parse origin/main` to match. If policy rejects the default-branch
mutation, do not retry or work around it. Leave the public identity enabled
unchanged and disclose ambiguity.

- [ ] **Step 5: Reconfirm live aggregate analytics and generate a private artifact**

Use read-only LinkedIn access only under the supplied explicit aggregate
consent. Do not inspect messages or individual visitor identities. Reconfirm
available metrics/date/window; generate partial or complete structured input
without raw retention; validate and render the first collision-safe private
artifact without overwriting prior reports. If values are inaccessible, render
unavailable rather than reusing the user's example.

- [ ] **Step 6: Empirical and structural QA**

Open the actual artifact in Codex Browser when supported, or use a temporary
loopback-only server and close it after inspection. Check desktop, 320px/200%
zoom, print, dark, forced-colors, keyboard/AT labels, clipping, overlap,
grayscale, and duplication. Run DOM/ARIA/privacy/source checks regardless and
record every unverified browser/AT item explicitly.

- [ ] **Step 7: Record evidence**

Write the ignored report with commits, exact version, source/tree/hash/counts,
test results, installed parity/smokes, live metric availability without raw
values in logs, artifact path/mode, ref status, dual-identity caveat, and visual
QA state.
