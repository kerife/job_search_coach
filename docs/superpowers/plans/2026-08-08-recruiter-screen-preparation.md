# Recruiter Screen Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the private dossier turn an evidence-backed `screen_bridge` into a concise, localized rehearsal for the first recruiter conversation without changing schema v1 or authorizing external action.

**Architecture:** Reuse the existing validated `screen_bridge`, linked rank-1 question, claims/evidence, and seven-day plan. Add a typed renderer view-model helper that derives categorical readiness and up to three safe evidence points, then render one semantic card with the existing inline HTML/CSS system. The validator remains unchanged unless a focused regression proves the new presentation exposes an unsafe value.

**Tech Stack:** Python 3.11 standard library, existing HTML renderer, inline CSS, JSON fixtures, `unittest`, repository privacy/static/release validators.

## Global Constraints

- No schema v2, new score, readiness percentage, recruiter identity, contact target, recruiter promise, interview probability, or market claim.
- `screen_bridge` remains private, draft-only, and `action_state=not_executed`.
- Render natural evidence states; never expose raw profile text, URLs, IDs, private analytics, or confidential employer detail.
- Unsupported technology stays in confirmation/omit or do-not-change copy and cannot enter the opener.
- Analytics and market evidence remain separate from the LinkedIn quality score.
- Missing evidence is unavailable/not requested/not researched, never zero and never a blocker when the remaining dossier is honest.
- Preserve the approved forest/paper/coral/gold palette, typography contrast, offline CSP, mobile layout, print behavior, 0600 output, and no remote dependencies.

## File map

- Modify `plugins/job-search-coach/scripts/render_executive_career_dossier.py`: derive and render the recruiter-screen card.
- Modify `plugins/job-search-coach/assets/executive-career-dossier-v1.css`: add only semantic readiness/evidence/rehearsal card tokens and responsive/print rules.
- Modify `tests/test_executive_career_dossier.py`: add RED/GREEN renderer matrices and safety regressions.
- Modify `tests/evals/with-skill/fixtures/executive-career-dossier/scenario-a-es.json`, `scenario-c-en.json`, and state variants in test memory: cover ready/confirmation/omit/unavailable bridge states without adding schema fields.
- Modify `tests/test_plugin_structure.py`: lock HTML structure, localized labels, no IDs, no external action, mobile/print selectors.
- Modify `plugins/job-search-coach/skills/optimize-linkedin-career/references/html-dossier.md`: document the visible card mapping and the exact no-action/rehearsal boundary.

### Task 1: Build the screen-preparation view model with tests first

**Interfaces:**

- Add `def _screen_bridge_view(dossier: Mapping[str, object], locale: str) -> Mapping[str, object]` in the renderer.
- The return mapping contains only renderer-safe values: `state_label`, `state_tone`, `opener`, `evidence_points`, `boundary`, `question`, and `rehearsal_label`; it never returns IDs or raw source values.
- `evidence_points` has at most three strings selected from linked claims/evidence paraphrases, preserving evidence state and omitting unknown/private values.

- [ ] **Step 1: Add failing tests for the Spanish and English ready bridge.**

```python
def test_screen_preparation_card_uses_bridge_claims_and_rank_one_question(self):
    html = self.render(self.es_dossier)
    self.assertIn("Preparación para la primera conversación", html)
    self.assertIn("Enfoque profesional claro", html)
    self.assertIn("No afirmar todavía", html)
    self.assertIn("Ensayo", html)
    self.assertEqual(html.count("questions-title"), 1)
    self.assertNotRegex(html, r"\b(?:E|C)-\d{3}\b")
```

```python
def test_screen_preparation_card_localizes_english_labels(self):
    html = self.render(self.en_dossier)
    self.assertIn("First-conversation preparation", html)
    self.assertIn("Do not claim yet", html)
    self.assertIn("Rehearsal", html)
```

- [ ] **Step 2: Run the focused tests and verify RED.**

Run:

```bash
python3 -B -m unittest tests.test_executive_career_dossier.ExecutiveCareerDossierRendererTests.test_screen_preparation_card_uses_bridge_claims_and_rank_one_question tests.test_executive_career_dossier.ExecutiveCareerDossierRendererTests.test_screen_preparation_card_localizes_english_labels -v
```

Expected: FAIL because the new card labels and view-model mapping do not exist.

- [ ] **Step 3: Implement the safe view model and card rendering.**

Use the existing bridge mapping and evidence records; never interpolate an ID:

```python
def _screen_bridge_view(dossier, locale):
    bridge = _mapping(dossier["screen_bridge"])
    state = bridge.get("state")
    labels = SCREEN_PREPARATION_LABELS[locale]
    evidence_points = _linked_evidence_points(dossier, bridge, limit=3)
    question = _ranked_bridge_question(dossier, bridge.get("question_rank"))
    rehearsal = _rehearsal_step(dossier)
    return {
        "state_label": labels["state"].get(state, labels["paused"]),
        "state_tone": state if state in {"ready", "requires_confirmation", "omit"} else "paused",
        "opener": bridge.get("copy") if state != "omit" else None,
        "evidence_points": evidence_points,
        "boundary": bridge.get("claim_boundary", ""),
        "question": question,
        "rehearsal_label": rehearsal,
    }
```

The helper must escape every value through the renderer’s existing `_escape`,
exclude IDs, and return no invented question when `question_rank` is absent.

- [ ] **Step 4: Run the focused tests and adjacent renderer tests.**

Run:

```bash
python3 -B -m unittest tests.test_executive_career_dossier -v
```

Expected: new tests and all existing dossier tests pass.

- [ ] **Step 5: Commit the view-model/test slice.**

```bash
git add plugins/job-search-coach/scripts/render_executive_career_dossier.py tests/test_executive_career_dossier.py
git commit -m "feat: add recruiter screen preparation view"
```

### Task 2: Add responsive, printable visual treatment

**Interfaces:** The existing `_render_main` calls `_render_screen_bridge`; the new card remains inside that section and does not change receipt fields or schema.

- [ ] **Step 1: Add RED assertions for semantic structure and states.**

```python
def test_screen_preparation_card_has_semantic_state_and_evidence_structure(self):
    html = self.render(self.es_dossier)
    self.assertRegex(html, r'<section[^>]+aria-labelledby="screen-preparation-title"')
    self.assertIn("screen-preparation-evidence", html)
    self.assertIn("screen-preparation-boundary", html)
    self.assertIn("screen-preparation-rehearsal", html)
```

```python
def test_confirmation_and_omit_states_never_show_numeric_readiness(self):
    for state in ("requires_confirmation", "omit"):
        dossier = copy.deepcopy(self.es_dossier)
        dossier["screen_bridge"]["state"] = state
        if state == "omit":
            dossier["screen_bridge"]["copy"] = None
        html = self.render(dossier)
        self.assertNotRegex(html, r"\b(?:\d+%|score|readiness|preparación\s+\d)\b")
```

- [ ] **Step 2: Run the new structure tests and verify RED.**

Run:

```bash
python3 -B -m unittest tests.test_executive_career_dossier.ExecutiveCareerDossierRendererTests.test_screen_preparation_card_has_semantic_state_and_evidence_structure tests.test_executive_career_dossier.ExecutiveCareerDossierRendererTests.test_confirmation_and_omit_states_never_show_numeric_readiness -v
```

Expected: FAIL until the semantic classes, labels, and state branches are present.

- [ ] **Step 3: Implement CSS and localized state branches.**

Add only scoped selectors such as `.screen-preparation-card`, `.readiness-chip`,
`.screen-preparation-evidence`, `.screen-preparation-boundary`, and
`.screen-preparation-rehearsal`. Keep body text at least `1rem`, controls at
least `44px`, `@media (max-width: 680px)` single-column flow, and print rules
that keep the card heading/content together. The readiness chip must include
visible text and not rely on color.

- [ ] **Step 4: Run accessibility, responsive, print, and renderer tests.**

Run:

```bash
python3 -B -m unittest tests.test_executive_career_dossier tests.test_plugin_structure -v
python3 -B plugins/job-search-coach/tests/run_static_checks.py
```

Expected: PASS except any known provenance records outside this increment; no
new HTML/CSP/offline/static error is allowed.

- [ ] **Step 5: Commit the visual slice.**

```bash
git add plugins/job-search-coach/assets/executive-career-dossier-v1.css plugins/job-search-coach/tests/test_plugin_structure.py
git commit -m "feat: style recruiter screen preparation card"
```

### Task 3: Update skill contract and integration gates

- [ ] **Step 1: Add RED contract assertions.**

Assert that `html-dossier.md` describes the card as private draft-only,
evidence-linked, one-question maximum, and never a recruiter contact or outcome
promise. Assert the four canonical fixtures keep exactly one receipt link,
one no-action sentence, 3/7/3 cards, and no internal IDs.

- [ ] **Step 2: Run contract tests and verify RED.**

```bash
python3 -B -m unittest tests.test_skill_contracts tests.test_full_plugin -v
```

Expected: the new wording/structure assertions fail before the reference and
integration checks are updated.

- [ ] **Step 3: Update `html-dossier.md` with the visible mapping.**

Document that the renderer maps `screen_bridge` to the preparation card, maps
only the linked rank-1 question, shows up to three safe evidence points, and
uses a rehearsal marker instead of any public recruiter action. Keep normal
HTML as the client branch and debug/eval Markdown compatibility unchanged.

- [ ] **Step 4: Run the complete verification set.**

```bash
python3 -B -m json.tool plugins/job-search-coach/schemas/executive-career-dossier-v1.schema.json
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
python3 -B scripts/check_repository_privacy.py
python3 -B plugins/job-search-coach/tests/run_static_checks.py
bash scripts/run_release_validation.sh
git diff --check
```

Expected: all commands exit 0 on the exact increment tree. Any stale
provenance is refreshed only in the dedicated publication step, not by changing
the semantic fixtures in this task.

- [ ] **Step 5: Run two independent reviews and fix any Important/Critical finding.**

Dispatch a coaching-value reviewer and an accessibility/security reviewer. For
each finding, add a RED regression, fix it, rerun the focused and full suites,
and obtain a fresh scoped re-review. Do not expand into LinkedIn actions or
recruiter contact automation.

- [ ] **Step 6: Commit the integration slice.**

```bash
git add plugins/job-search-coach/skills/optimize-linkedin-career/references/html-dossier.md tests/test_skill_contracts.py
git commit -m "docs: document recruiter screen preparation flow"
```

### Task 4: Publish and load the increment

- [ ] **Step 1: Refresh deterministic provenance to the final functional parent.**
- [ ] **Step 2: Run the full suite, privacy/static/schema checks, and official validators.**
- [ ] **Step 3: Run the official cachebuster exactly once, preserving the `0.2.0` base.**
- [ ] **Step 4: Commit the release manifest/provenance changes.**
- [ ] **Step 5: Run post-commit provenance, full, privacy, static, and official checks.**
- [ ] **Step 6: Install with `codex plugin add job-search-coach@job-search-coach-local` and verify source/cache identity plus an installed smoke scenario.**

## Review checklist

- No schema v2 or new score.
- One visible preparation card, one linked rank-1 question, one no-action sentence.
- No internal IDs, raw profile, contact targets, recruiter promises, or public actions.
- Mobile and print card remain readable and do not split heading/content.
- Existing dossier and Markdown compatibility tests remain green.
