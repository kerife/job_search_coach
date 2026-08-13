# LinkedIn Dossier v2 Coverage and Coaching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a versioned private LinkedIn dossier that accounts for all 17 canonical sections, requests missing read-only inspection authorization one section at a time for the current session, and renders exactly three contextual coach priorities with blank client templates.

**Architecture:** Add a v2 schema, pure compatibility projection, validator, renderer, CSS extension, and synthetic fixtures without changing v1 behavior. The v2 validator projects shared fields to the mature v1 validator, validates the new section ledger and coach fields separately, and keeps all v2 prose inside existing privacy boundaries. The serialized ledger is status-only: a positive answer is consumed by the skill orchestrator and is never persisted as reusable consent. The v2 renderer reuses the v1 template, CSS, private writer, and unchanged rendering helpers, inserting only the new decision ledger, coach cards, and a bounded market-unavailable state.

**Tech Stack:** Python 3.11+, standard library only, JSON Schema draft 2020-12 subset, `unittest`, dependency-free offline HTML/CSS, existing private asset/input loaders, Superdesign parity tests, Codex plugin release tooling.

## Global Constraints

- Preserve `executive-career-dossier-v1` schema, validator, renderer, fixtures, HTML bytes, CLI behavior, and tests unchanged.
- V2 contains exactly these section keys, exactly once and in order: `photo`, `banner`, `name`, `profile_url`, `headline`, `location`, `contact_info`, `about`, `experience`, `skills`, `featured`, `certifications`, `education`, `recommendations`, `activity`, `analytics`, `job_preferences`.
- Authorization is section-specific, `read_only_visible_section_inspection`, `current_session_only`, and `carry_forward=false`; it never authorizes an external action or raw-profile retention. The positive answer is never serialized. Persisted request decisions are only `pending_response`, `declined_for_session`, and `authorized_inspection_failed`.
- `inspected_absent` is a completed inspection state and never creates another authorization request.
- Pending or declined sections never enter the existing seven-dimension score as zero.
- The artifact renders every unavailable section; the chat summary first checks priority targets in rank order, then falls back to canonical ledger order, and asks at most one pending authorization question.
- Every v2 evidence item adds `profile_section`, set to one canonical section or `null`; projection removes it before v1 validation.
- Exactly three priorities retain the complete v1 priority contract and add `target_section`, `coach_observation`, `why_it_matters`, `coach_prompt`, one closed `client_template` object, and `privacy_boundary=no_raw_profile_text_or_private_values`.
- Each priority references at least one evidence item whose `profile_section` equals `target_section`.
- This increment renders one honest market-evidence-unavailable state. It does not render vacancy percentages or learning recommendations until the separate market contract ships.
- Candidate identity, profile URLs, contact values, raw profile text, private analytics, local paths, raw enum values, and evidence IDs never appear in visible HTML or chat summary.
- No new dependency, remote asset, network request, form, external script, local storage, persisted answer, or relaxed CSP.
- Static checks do not count as empirical browser QA; report real-browser keyboard, 320px/200% zoom, print, forced-colors, dark-mode, and screen-reader status separately.
- Run the official cachebuster exactly once and only after functional, plugin, root, static, privacy, release, diff, and source checks are green.
- Leave `professional-growth-coach@codex-marketplace-public` unchanged and disclose that both public and local identities remain enabled.

---

### Task 1: V2 schema, compatibility projection, and semantic validator

**Files:**
- Create: `plugins/professional-growth-coach/schemas/executive-career-dossier-v2.schema.json`
- Create: `plugins/professional-growth-coach/scripts/executive_career_dossier_v2_compat.py`
- Create: `plugins/professional-growth-coach/scripts/validate_executive_career_dossier_v2.py`
- Create: `tests/test_executive_career_dossier_v2.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

**Interfaces:**
- Consumes: `validate_executive_career_dossier.validate_dossier(value) -> list[str]`, `validate_executive_career_dossier._scan_privacy(value) -> list[str]`, `private_input_loader.read_bounded_bytes(...)`, and `private_prose_safety.format_bounded_diagnostics(errors) -> str`.
- Produces in compat: `CANONICAL_PROFILE_SECTIONS: tuple[str, ...]` and `project_v2_to_v1(value: Mapping[str, object]) -> dict[str, object]`.
- Produces in validator: `validate_dossier(value: object) -> list[str]`, `load_dossier(path: Path) -> dict[str, object]`, `select_pending_inspection_section(dossier: Mapping[str, object]) -> str | None`, and `_cli(argv: list[str] | None = None) -> int`.
- Produces schema definitions `section_coverage_row`, `inspection_request`, and extended `priority` for Task 2.

- [ ] **Step 1: Add the v2 test helper and first RED contract tests**

Add this helper shape to `tests/test_executive_career_dossier_v2.py`; it deliberately builds on a real valid v1 fixture so shared semantics remain covered:

```python
CANONICAL_PROFILE_SECTIONS = (
    "photo", "banner", "name", "profile_url", "headline", "location",
    "contact_info", "about", "experience", "skills", "featured",
    "certifications", "education", "recommendations", "activity",
    "analytics", "job_preferences",
)

def make_v2_dossier(locale: str = "es") -> dict[str, object]:
    dossier = copy.deepcopy(load_v1_fixture(
        "scenario-a-es.json" if locale == "es" else "scenario-c-en.json"
    ))
    dossier["schema_version"] = "executive-career-dossier-v2"
    inspected = set(dossier["evidence_scope"]["inspected_sections"])
    dossier["section_coverage"] = []
    for section in CANONICAL_PROFILE_SECTIONS:
        if section in inspected:
            dossier["section_coverage"].append({
                "section": section,
                "availability": "inspected_present",
                "evidence_state": "verified",
                "reason": "inspected_content_available",
            })
            continue
        decision = (
            "declined_for_session" if section == "certifications"
            else "pending_response"
        )
        dossier["section_coverage"].append({
            "section": section,
            "availability": "unavailable",
            "evidence_state": "unknown",
            "reason": (
                "inspection_declined" if decision == "declined_for_session"
                else "authorization_required"
            ),
            "inspection_request": {
                "access_type": "read_only_visible_section_inspection",
                "decision": decision,
                "scope": "current_session_only",
                "carry_forward": False,
            },
        })
    for evidence in dossier["evidence"]:
        evidence["profile_section"] = (
            evidence["section"]
            if evidence["section"] in CANONICAL_PROFILE_SECTIONS
            else None
        )
    priority_sections = ("headline", "about", "experience")
    for priority, section in zip(dossier["priorities"], priority_sections, strict=True):
        priority["evidence_ids"] = {
            "headline": ["E-001"],
            "about": ["E-002"],
            "experience": ["E-003"],
        }[section]
        priority.update({
            "target_section": section,
            "coach_observation": f"Coach observation for {section}.",
            "why_it_matters": f"Evidence from {section} changes the review.",
            "coach_prompt": f"Complete the private template for {section}.",
            "client_template": {
                "template_id": "context_action_result_v1",
                "field_keys": ["context", "action", "result"],
            },
            "privacy_boundary": "no_raw_profile_text_or_private_values",
        })
    return dossier
```

Add focused tests that assert:

```python
def test_v2_requires_the_exact_canonical_section_ledger(self) -> None:
    dossier = make_v2_dossier()
    self.assertEqual(self.validator.validate_dossier(dossier), [])
    self.assertEqual(
        tuple(row["section"] for row in dossier["section_coverage"]),
        CANONICAL_PROFILE_SECTIONS,
    )
    for mutation in (
        dossier["section_coverage"][:-1],
        list(reversed(dossier["section_coverage"])),
        dossier["section_coverage"] + [copy.deepcopy(dossier["section_coverage"][0])],
    ):
        invalid = copy.deepcopy(dossier)
        invalid["section_coverage"] = mutation
        self.assertIn(
            "section_coverage must contain every canonical section exactly once in canonical order",
            self.validator.validate_dossier(invalid),
        )
```

```python
def test_unavailable_sections_require_current_session_read_only_decisions(self) -> None:
    dossier = make_v2_dossier()
    dossier["section_coverage"][10] = {
        "section": "featured",
        "availability": "unavailable",
        "evidence_state": "unknown",
        "reason": "authorization_required",
        "inspection_request": {
            "access_type": "read_only_visible_section_inspection",
            "decision": "pending_response",
            "scope": "current_session_only",
            "carry_forward": False,
        },
    }
    self.assertEqual(self.validator.validate_dossier(dossier), [])
    missing = copy.deepcopy(dossier)
    del missing["section_coverage"][10]["inspection_request"]
    self.assertIn(
        "section_coverage[10] unavailable section requires inspection_request",
        self.validator.validate_dossier(missing),
    )
    forbidden = make_v2_dossier()
    forbidden["section_coverage"][0]["inspection_request"] = copy.deepcopy(
        dossier["section_coverage"][10]["inspection_request"]
    )
    self.assertIn(
        "section_coverage[0] inspected section forbids inspection_request",
        self.validator.validate_dossier(forbidden),
    )
```

Add tests for the exact persisted state matrix:

- `inspected_present -> verified + inspected_content_available`;
- `inspected_absent -> verified + inspected_section_absent`;
- `candidate_supplied -> candidate_reported + candidate_material_supplied`;
- `unavailable/authorization_required -> unknown + pending_response`;
- `unavailable/inspection_declined -> unknown + declined_for_session`;
- `unavailable/authorized_inspection_failed -> unknown + authorized_inspection_failed`.

Also reject `authorized_for_session`, `carry_forward=true`, wrong access
type/scope, a request on any inspected/candidate-supplied row, and direct
contradictions with any section explicitly listed by the legacy
`evidence_scope.inspected_sections` or `unavailable_sections`. The v1 lists are
not exhaustive and therefore must not be treated as the 17-row authority. Add
tests that every `inspected_present` or `candidate_supplied` row has at least
one evidence record with the same `profile_section`, and for any change to
score or denominator when only a ledger row changes between pending and
declined. Prove that the input object is not mutated.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v2 -v
```

Expected: import failure because `validate_executive_career_dossier_v2.py` does
not exist. This is the intentional RED, not a fixture or syntax error.

- [ ] **Step 3: Add priority and privacy RED cases**

Add tests that remove each new priority field, use zero and six template field
keys, use an unknown template ID or duplicate field key, bind priority 1 to
evidence whose `profile_section=about` while targeting `headline`, insert a
profile URL/path/email/control character into each new prose field, and assert
fixed diagnostics do not echo the sentinel. Keep the safe control:

```python
def test_contextual_priorities_bind_same_section_evidence(self) -> None:
    dossier = make_v2_dossier()
    self.assertEqual(self.validator.validate_dossier(dossier), [])
    dossier["priorities"][0]["evidence_ids"] = ["E-002"]
    self.assertIn(
        "priorities[0].evidence_ids must bind to the target section",
        self.validator.validate_dossier(dossier),
    )
```

```python
def test_v2_diagnostics_do_not_echo_new_prose_values(self) -> None:
    sentinel = "/private/path/profile.json"
    dossier = make_v2_dossier()
    dossier["priorities"][0]["coach_prompt"] = sentinel
    errors = self.validator.validate_dossier(dossier)
    self.assertTrue(errors)
    self.assertNotIn(sentinel, "\n".join(errors))
```

Add boundary tests for an unknown top-level key containing an email, URL,
absolute path, newline, ANSI escape, or bidi control; invalid enum values;
duplicate JSON keys; invalid UTF-8; decoder recursion; oversize input; FIFO;
and leaf/intermediate symlinks. Every failure must use fixed, non-echoing text,
CLI exit 2, one bounded UTF-8 diagnostic block of at most 16 KiB, the existing
truncation marker when needed, and no traceback. Reuse existing real loader
fixtures and descriptor-boundary helpers rather than mocking filesystem reads.

- [ ] **Step 4: Copy and extend the closed v1 JSON schema**

Create `executive-career-dossier-v2.schema.json` from the v1 schema with only
these contract changes:

```json
"schema_version": {"const": "executive-career-dossier-v2"},
"section_coverage": {
  "type": "array",
  "minItems": 17,
  "maxItems": 17,
  "items": {"$ref": "#/$defs/section_coverage_row"}
}
```

Add `section_coverage` to the required top-level fields. Extend each evidence
item with required `profile_section`, whose value is one canonical section or
`null`; projection removes it before v1 validation. Define
`section_coverage_row` as a `oneOf` across four closed branches. The first is:

```json
{
  "type": "object",
  "required": ["section", "availability", "evidence_state", "reason"],
  "additionalProperties": false,
  "properties": {
    "section": {"enum": ["photo", "banner", "name", "profile_url", "headline", "location", "contact_info", "about", "experience", "skills", "featured", "certifications", "education", "recommendations", "activity", "analytics", "job_preferences"]},
    "availability": {"const": "inspected_present"},
    "evidence_state": {"const": "verified"},
    "reason": {"const": "inspected_content_available"}
  }
}
```

The other completed branches are exactly
`inspected_absent/verified/inspected_section_absent` and
`candidate_supplied/candidate_reported/candidate_material_supplied`; all three
forbid `inspection_request`. The fourth is an unavailable row requiring this
closed request:

```json
{
  "access_type": {"const": "read_only_visible_section_inspection"},
  "decision": {"enum": ["pending_response", "declined_for_session", "authorized_inspection_failed"]},
  "scope": {"const": "current_session_only"},
  "carry_forward": {"const": false}
}
```

Unavailable reason codes are exactly `authorization_required`,
`inspection_declined`, and `authorized_inspection_failed`, with the one-to-one
decision coupling above. Extend the existing priority definition with the six
v2 fields and exact bounds from Global Constraints; retain every v1 priority
field. `client_template.template_id` is one of
`context_action_result_v1`, `positioning_evidence_v1`, or
`proof_scope_result_v1`; `field_keys` contains one through five unique values
from `target_role`, `specialty`, `context`, `action`, `scope`, `result`,
`metric`, and `evidence_source`.

- [ ] **Step 5: Implement the minimal v2 compatibility validator**

Create `executive_career_dossier_v2_compat.py` with the tuple and pure
projection, and create `validate_executive_career_dossier_v2.py` using dynamic
sibling imports, the existing bounded private input loader, and no third-party
dependency. Implement these exact interfaces:

```python
CANONICAL_PROFILE_SECTIONS = (
    "photo", "banner", "name", "profile_url", "headline", "location",
    "contact_info", "about", "experience", "skills", "featured",
    "certifications", "education", "recommendations", "activity",
    "analytics", "job_preferences",
)

def project_v2_to_v1(value: Mapping[str, object]) -> dict[str, object]:
    projected = copy.deepcopy(dict(value))
    projected["schema_version"] = "executive-career-dossier-v1"
    projected.pop("section_coverage", None)
    for evidence in projected.get("evidence", []):
        if isinstance(evidence, dict):
            evidence.pop("profile_section", None)
    for priority in projected.get("priorities", []):
        if isinstance(priority, dict):
            for key in (
                "target_section", "coach_observation", "why_it_matters", "coach_prompt",
                "client_template", "privacy_boundary",
            ):
                priority.pop(key, None)
    return projected
```

`validate_dossier` must:

1. reject non-mappings with one fixed error;
2. verify v2 version and top-level closed fields;
3. call the v1 validator on `project_v2_to_v1(value)`;
4. require canonical ledger order, request/state coupling, and reject direct
   contradictions with sections explicitly present in legacy
   `evidence_scope`; do not require those legacy lists to be exhaustive;
5. require same-section evidence for `inspected_present` and
   `candidate_supplied` rows; validate priority new fields,
   same-`profile_section` evidence, and the
   closed template contract;
6. call the existing recursive privacy scan on the original v2 value so new
   prose cannot bypass privacy checks;
7. never interpolate untrusted keys, values, URLs, paths, capture references,
   digests, or control characters into diagnostics;
8. return `sorted(set(errors))`.

`select_pending_inspection_section` checks priority target sections in rank
order, then canonical ledger order, and returns at most one section. It must
ignore declined and failed requests. Its tests exercise real dossier objects,
not source-text greps.

Load at most 256 KiB with the existing descriptor-boundary loader, parse with
duplicate-key rejection, catch `UnicodeDecodeError`, `json.JSONDecodeError`,
and `RecursionError`, require maximum depth 12, and use the exact fixed load
messages already used by the v1 validator with `v2 dossier` substituted only
where the contract name is needed.

- [ ] **Step 6: Run RED to GREEN and the v1 compatibility suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v2 \
  tests.test_executive_career_dossier -v
```

Expected: all v2 tests pass and the complete v1 suite remains green.

- [ ] **Step 7: Add schema-subset conformance and CLI coverage**

Extend `test_private_schema_conformance.py` to load the v2 schema with
`validate_json_schema_subset.validate_schema_instance`, accept the helper
fixture, and reject missing ledger/request/priority fields. Add a subprocess
test for valid input exit 0 and invalid input exit 2 with exactly one or more
bounded diagnostic lines, no traceback, and no sentinel echo.

- [ ] **Step 8: Verify and commit Task 1**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v2 \
  tests.test_executive_career_dossier -v
(cd plugins/professional-growth-coach/tests && \
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  test_private_schema_conformance -v)
git diff --check
```

Commit only Task 1 files:

```bash
git add \
  plugins/professional-growth-coach/schemas/executive-career-dossier-v2.schema.json \
  plugins/professional-growth-coach/scripts/executive_career_dossier_v2_compat.py \
  plugins/professional-growth-coach/scripts/validate_executive_career_dossier_v2.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  tests/test_executive_career_dossier_v2.py
git commit -m "feat: validate linkedin dossier v2 coverage"
```

---

### Task 2: V2 renderer, authorization summary, and accessible product surface

**Files:**
- Create: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`
- Create: `plugins/professional-growth-coach/assets/executive-career-dossier-v2.css`
- Create: `tests/evals/with-skill/fixtures/executive-career-dossier-v2/scenario-a-es.json`
- Create: `tests/evals/with-skill/fixtures/executive-career-dossier-v2/scenario-c-en.json`
- Modify: `tests/test_executive_career_dossier_v2.py`
- Modify: `tests/test_dark_mode_accessibility.py`
- Modify: `tests/test_superdesign_theme_asset_parity.py`
- Modify: `.superdesign/init/theme.md`
- Modify: `plugins/professional-growth-coach/scripts/private_asset_loader.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_design_tokens.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_asset_loader.py`
- Modify: `plugins/professional-growth-coach/tests/test_design_tokens.py`
- Modify: `tests/test_print_continuity_footer_integrity.py`
- Modify: `tests/test_private_asset_boundary.py`

**Interfaces:**
- Consumes: Task 1 `validate_dossier`, `load_dossier`, `select_pending_inspection_section`, `project_v2_to_v1`, and `CANONICAL_PROFILE_SECTIONS`.
- Consumes unchanged v1 renderer helpers `_render_header`, `_render_verdict`, `_render_recruiter_scan`, `_render_analytics`, `_render_dimensions`, `_render_visual_review`, `_render_copy_blocks`, `_render_holds`, `_render_screen_bridge`, `_render_questions`, `_render_plan`, `_render_details`, `_atomic_private_write`, and `RenderReceipt`.
- Produces: `render_dossier_html(dossier: Mapping[str, object]) -> str`, `build_chat_summary(dossier: Mapping[str, object]) -> str`, `write_dossier_html(dossier_path: Path, output_path: Path, *, force: bool = False) -> RenderReceipt`, and `_cli(argv) -> int`.

- [ ] **Step 1: Add renderer RED tests for ledger, priorities, and summary**

Add EN/ES renderer tests that parse the returned HTML and assert:

- one named `section-coverage-ledger` region;
- exactly 17 `li.section-coverage-row` elements in canonical order, each with
  one named nested `article` and semantic `dl`;
- each row has a visible section label, availability label, reason, and request
  decision when unavailable;
- exactly three `.coach-priority-card` articles with `aria-labelledby`;
- each card names its target section, includes observation/prompt, and renders
  one-to-five blank template items;
- no evidence IDs, canonical section keys, internal request enums, raw local
  paths, profile URLs, or contact values occur in visible text;
- `build_chat_summary` contains exactly one question for the first
  `pending_response` row and contains none for declined/failed-only rows.

Use this exact behavior assertion:

```python
self.assertIn(
    "¿Autorizas inspeccionar en modo solo lectura la sección Nombre durante esta sesión?",
    summary,
)
self.assertNotIn("Certificaciones", summary)
self.assertLessEqual(len(summary.split()), 180)
```

The English equivalent begins `Do you authorize read-only inspection of the
Name section during this session?`.

- [ ] **Step 2: Run renderer tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v2.ExecutiveCareerDossierV2RendererTests -v
```

Expected: import failure for the missing v2 renderer.

- [ ] **Step 3: Create synthetic v2 fixtures**

Copy the corresponding valid v1 fixtures, set
`schema_version=executive-career-dossier-v2`, add the exact 17-row ledger,
required `profile_section` values, and all six priority fields. Use only
synthetic identity-free paraphrases. Each fixture must project deep-equal to
its source v1 fixture after removing v2-only fields.
For both fixtures:

- `featured` is unavailable with `pending_response` and
  `reason=authorization_required`;
- `certifications` is unavailable with `declined_for_session` and
  `reason=inspection_declined`;
- `analytics` preserves its separate existing consent state and does not become
  authorized by the section request;
- every other canonical section lacking explicit same-section evidence is
  unavailable with `pending_response`; the first such section is `name`;
- priority targets are `headline`, `about`, and `experience` and each priority
  references same-section evidence.

- [ ] **Step 4: Implement the v2 renderer by composition**

Load the Task 1 validator, compatibility module, and v1 renderer through
sibling paths. Reuse the v1 template. Extend the private asset allowlist for
the v2 CSS, then inline the exact v1 CSS followed by the v2 CSS extension.
Implement fixed EN/ES maps for all 17 section labels, four availability labels,
reason labels, request decisions, template IDs/field keys, and authorization
questions.

The main composition is exactly:

```python
def _render_main(dossier: Mapping[str, object], locale: str) -> str:
    projected = COMPAT.project_v2_to_v1(dossier)
    opening = BASE._render_verdict(projected, locale) + BASE._render_recruiter_scan(projected, locale)
    bridge_holds = BASE._render_holds(projected, locale) + BASE._render_screen_bridge(projected, locale)
    return f'''<main id="main-content" class="shell" tabindex="-1">
      <div class="dossier-grid">{opening}</div>
      {_render_section_coverage(dossier, locale)}
      {_render_coach_priorities(dossier, locale)}
      <div class="dossier-grid section-block">{BASE._render_analytics(projected, locale)}</div>
      {BASE._render_dimensions(projected, locale)}
      {BASE._render_visual_review(projected, locale)}
      {_render_market_evidence_unavailable(locale)}
      {BASE._render_copy_blocks(projected, locale)}
      <div class="dossier-grid section-block">{bridge_holds}</div>
      {BASE._render_questions(projected, locale)}
      <div class="dossier-grid section-block">{BASE._render_plan(projected, locale)}{BASE._render_details(projected, locale)}</div>
    </main>
    <footer class="shell footer"><strong>{BASE.COPY[locale]['action_boundary']}</strong> <span class="employment-boundary">{BASE.COPY[locale]['employment_boundary']}</span></footer>'''
```

Build each ledger row as `li > article[aria-labelledby] > h3 + dl`, and each
priority as a named article with a nested static template section. Use
`html.escape`, deterministic generic IDs, and no interactive control. Do not
render the old v1 priority `problem/action/timebox_minutes` presentation in v2.
Use the base renderer's validation/freeze conventions and private writer. The
CLI receipt remains one JSON line with absolute path, `text/html`, locale, and
summary. The bounded market placeholder contains no score, vacancy, employer,
course, or paid-learning copy.

- [ ] **Step 5: Implement chat authorization precedence**

`build_chat_summary` validates first, keeps the v1 verdict and first private
action, then delegates to `select_pending_inspection_section`: priority targets
in rank order first, canonical order second. It appends one fixed localized
authorization question and the existing no-action boundary. It does not append
the v1 rank-1 content question in the same turn when an inspection authorization
question exists. If no request is pending, retain the v1 summary behavior.

- [ ] **Step 6: Add the CSS extension and Superdesign parity dump**

Create only v2 extension selectors:

```css
.section-coverage-list { display: grid; gap: .75rem; margin: 0; padding: 0; list-style: none; }
.section-coverage-row { min-width: 0; overflow-wrap: anywhere; }
.section-coverage-row article { padding: 1rem; border: 1px solid var(--forest-soft); background: var(--surface); }
.section-coverage-facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem 1rem; }
.section-coverage-row h3 { margin: 0; }
.section-coverage-request { margin: 0; padding-left: .75rem; border-left: 4px solid var(--gold); }
.coach-priority-card { border-top: 4px solid var(--coral); }
.coach-template { margin: 1rem 0 0; padding: 1rem; border-left: 4px solid var(--forest); background: var(--paper); }
.coach-template-list { margin: .5rem 0 0; padding-left: 1.25rem; }
```

At `max-width: 480px`, set `.section-coverage-facts { grid-template-columns:
1fr; }`, preserve `min-width:0`, and forbid horizontal-scroll/nowrap
primitives. Add print `break-inside`, dark token-only reuse, forced-colors
`Canvas`/`CanvasText` surfaces with `Highlight` focus/left edges, and
`prefers-contrast: more` 2px borders. Do not add colors outside the existing
dossier palette or apply the v1 card animation/hover treatment to all 17 rows.

Append the exact CSS bytes to `.superdesign/init/theme.md` under a v2 source
dump heading and extend `test_superdesign_theme_asset_parity.py` to compare it
byte-for-byte.

- [ ] **Step 7: Verify GREEN, DOM integrity, and neighboring surfaces**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v2 \
  tests.test_executive_career_dossier \
  tests.test_print_continuity_footer_integrity \
  tests.test_private_asset_boundary \
  tests.test_superdesign_theme_asset_parity \
  tests.test_dark_mode_accessibility -v
git diff --check
```

Render both fixtures to a temporary private directory and assert one H1, one
main, one footer, unique IDs, zero missing `aria-labelledby` or
`aria-describedby` targets, exactly 17 ledger rows, exactly three coach cards,
one market-unavailable state, zero progress/percentage/paid-learning text, and
output mode 0600. The 320px static contract requires a one-column ledger and no
horizontal-scroll rule; empirical browser zoom remains a reported follow-up.

- [ ] **Step 8: Commit Task 2**

```bash
git add \
  .superdesign/init/theme.md \
  plugins/professional-growth-coach/assets/executive-career-dossier-v2.css \
  plugins/professional-growth-coach/scripts/private_asset_loader.py \
  plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py \
  plugins/professional-growth-coach/scripts/validate_design_tokens.py \
  plugins/professional-growth-coach/tests/test_design_tokens.py \
  plugins/professional-growth-coach/tests/test_private_asset_loader.py \
  tests/evals/with-skill/fixtures/executive-career-dossier-v2 \
  tests/test_dark_mode_accessibility.py \
  tests/test_executive_career_dossier_v2.py \
  tests/test_print_continuity_footer_integrity.py \
  tests/test_private_asset_boundary.py \
  tests/test_superdesign_theme_asset_parity.py
git commit -m "feat: render linkedin dossier v2 coaching"
```

---

### Task 3: Default skill routing and package validation

**Files:**
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/SKILL.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/references/html-dossier.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/references/profile-audit.md`
- Modify: `plugins/professional-growth-coach/README.md`
- Modify: `plugins/professional-growth-coach/scripts/build_dossier_recruiter_practice_handoff.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_dossier_recruiter_practice_handoff.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_dossier_recruiter_practice_handoff.py`
- Modify: `tests/test_full_plugin.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `tests/test_repository_privacy.py`
- Modify: `tests/test_skill_contracts.py`

**Interfaces:**
- Consumes: Task 1 v2 schema/validator and Task 2 v2 renderer/fixtures.
- Produces: default normal-local artifact routing to v2, one-question chat authorization behavior, v1/v2-safe downstream handoff projection, and static package inventory checks.

- [ ] **Step 1: Add RED skill and package tests**

Add assertions that normal local profile audits name
`executive-career-dossier-v2`, invoke the v2 validator and renderer, require all
17 ledger rows, and use one pending current-session inspection question. Test
the behavior of the real validator/renderer and handoff builder; use source-text
assertions only for instructional boundaries that have no executable consumer.
Assert the skill still says:

- render a supported partial dossier now;
- absent sections are not scored as zero;
- no authorization carries forward;
- a positive answer is consumed immediately and never stored in the artifact;
- analytics needs separate explicit consent;
- no inspection authorization permits an external action;
- v1 remains an accepted compatibility artifact for debug/eval fixtures.

Extend package tests to require the new schema, compat helper, validator,
renderer, and CSS,
reject a missing v2 package file, run the v2 validator against both fixtures,
and render both fixtures without unsafe inline/network boundaries.

Add handoff RED cases proving v1 remains accepted unchanged, v2 is validated by
the v2 validator, extraction uses a pure v1 projection, and
`source_snapshot` stays bound to the original v2 object rather than its
projection. A mutated ledger, priority, or `profile_section` after snapshot
creation must fail closed.

- [ ] **Step 2: Run tests and verify RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_full_plugin \
  tests.test_plugin_structure -v
```

Expected: failures that the skill and static package inventory still reference
v1 as the normal default and do not validate the v2 package.

- [ ] **Step 3: Update the skill contract**

Change only the normal local artifact branch to v2. Add the exact sequence:

1. account for all 17 sections;
2. render available findings immediately;
3. record unavailable sections and their current-session request states;
4. ask only the first pending authorization question in chat;
5. on an explicit positive answer, inspect only that named section immediately
   without writing `authorized_for_session` or any session identifier;
6. never infer authorization, analytics consent, raw retention, or an external
   action;
7. after the inspection attempt, regenerate a new
   collision-safe v2 artifact.

Retain the existing 180-word receipt, one absolute local file link, candidate
isolation, one repair, Markdown fallback, and no overwrite rules. Update README
only where it describes the default artifact version.

- [ ] **Step 4: Extend static package checks without weakening v1**

Add `EXECUTIVE_DOSSIER_V2_PACKAGE_PATHS` with the five new plugin paths and the
two synthetic fixture paths. Validate schema JSON, script regular-file/no-link
boundaries, fixture acceptance, renderer exit 0, one style/script boundary,
offline CSP, and mode-600 writer behavior. Keep the existing v1 package checks
unchanged.

- [ ] **Step 5: Run focused and full pre-release gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v2 \
  tests.test_dossier_recruiter_practice_handoff \
  tests.test_full_plugin \
  tests.test_plugin_structure \
  tests.test_repository_privacy \
  tests.test_skill_contracts \
  tests.test_superdesign_theme_asset_parity \
  tests.test_dark_mode_accessibility -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s plugins/professional-growth-coach/tests -p 'test_*.py' -q
python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
python3 -B scripts/check_repository_privacy.py
scripts/run_release_validation.sh
git diff --check
```

Expected: every command exits 0 before any cachebuster or install.

- [ ] **Step 6: Commit Task 3**

```bash
git add \
  plugins/professional-growth-coach/README.md \
  plugins/professional-growth-coach/scripts/build_dossier_recruiter_practice_handoff.py \
  plugins/professional-growth-coach/scripts/validate_dossier_recruiter_practice_handoff.py \
  plugins/professional-growth-coach/skills/optimize-professional-profile/SKILL.md \
  plugins/professional-growth-coach/skills/optimize-professional-profile/references/html-dossier.md \
  plugins/professional-growth-coach/skills/optimize-professional-profile/references/profile-audit.md \
  plugins/professional-growth-coach/tests/run_static_checks.py \
  tests/test_dossier_recruiter_practice_handoff.py \
  tests/test_full_plugin.py \
  tests/test_plugin_structure.py \
  tests/test_repository_privacy.py \
  tests/test_skill_contracts.py
git commit -m "feat: route profile audits to dossier v2"
```

---

### Task 4: Independent review, release, install, provenance, and publication

**Files:**
- Modify once: `plugins/professional-growth-coach/.codex-plugin/plugin.json` through the official cachebuster.
- Modify mechanically: `tests/evals/final/cycle-1/*.json`, `tests/evals/final/cycle-2/*.json`, `tests/evals/final/cycle-1.md`, `tests/evals/final/cycle-2.md`, and `tests/evals/final/installed-smoke-test.md`.
- Create ignored evidence: `.superpowers/sdd/2026-08-13-linkedin-dossier-v2-coverage-coaching/task-4-report.md`.

**Interfaces:**
- Consumes: reviewed commits from Tasks 1-3 and the existing local marketplace `professional-growth-coach-local`.
- Produces: one exact installed version, source/cache parity and hash, current provenance, full gate evidence, and synchronized `origin/main` if the push is permitted.

- [ ] **Step 1: Run final pre-cachebuster evidence**

Run all Task 3 gates plus the full root suite:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_*.py' -q
```

Also run the focused v2 suite under `/Users/kevinriosferrer/.local/bin/python3.11`
when that interpreter exists. Do not continue if any non-provenance gate fails.

- [ ] **Step 2: Obtain independent task and whole-increment reviews**

Use the subagent-driven review package workflow. Require explicit verdicts for
spec compliance and code quality. Resolve every Critical/Important finding
through the bounded fix loop before release. The final reviewer verifies all 17
sections, current-session authorization, one-question summary, coach priority
context, v1 compatibility, privacy, accessible DOM/CSS, and no external action.

- [ ] **Step 3: Consume the cachebuster exactly once**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  /Users/kevinriosferrer/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py \
  plugins/professional-growth-coach
git add plugins/professional-growth-coach/.codex-plugin/plugin.json
git commit -m "chore: bump linkedin dossier v2 cachebuster"
```

Record this commit as `source_commit` and its plugin tree as `source_tree`.

- [ ] **Step 4: Install the exact local plugin and prove parity**

Use the repository's established Codex plugin add/install command for
`professional-growth-coach@professional-growth-coach-local`, then confirm the
exact version is enabled with:

```bash
codex plugin list --json
```

Resolve the versioned cache path, exclude `__pycache__`, require identical file
sets and contents with `diff -qr`, require equal source/cache file counts, and
compute the normalized path-plus-file-SHA256 inventory hash using the existing
attestation convention.

- [ ] **Step 5: Refresh deterministic provenance and installed smoke**

Set all 12 cycle JSON records and both cycle indexes to the cachebuster source
commit and plugin tree. Update installed smoke with release timestamp, exact
installed version, enabled local identity, source/cache counts, normalized
hash, `source_cache_equivalence=diff_qr_silent`, new installed v2 validator and
renderer smokes in EN/ES, and the persistent
`active_config=canonical_and_public_enabled_ambiguous` caveat. Keep
`fresh_agent_smoke=not_run` unless a genuinely new Codex task verifies the
callable local skill identity.

- [ ] **Step 6: Commit attestation and rerun every gate fresh**

```bash
git add tests/evals/final
git commit -m "test: attest linkedin dossier v2 installation"
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

Recheck installed source/cache parity after the attestation commit; the plugin
tree and installed cache must remain identical because attestation files live
outside the plugin.

- [ ] **Step 7: Publish and verify refs**

With the user's explicit publication authorization, run:

```bash
git push origin main
git rev-parse HEAD
git rev-parse origin/main
```

The two hashes must match. If policy rejects default-branch mutation, do not
retry or work around it; report the exact blocker while keeping the verified
local plugin installed.

- [ ] **Step 8: Record Task 4 evidence**

Write the ignored report with commit IDs, version, source/tree, 109-plus new
file counts, normalized hash, all exact test counts and exit codes, installed
smokes, ref status, dual-identity caveat, and empirical browser/AT verification
status. Do not claim visual QA from static tests.
