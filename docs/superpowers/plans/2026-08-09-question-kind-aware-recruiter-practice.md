# Question-kind-aware Recruiter Practice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved decision-led recruiter-practice experience with a truthful answer destination and closed coaching guidance for all five validated question kinds.

**Architecture:** Keep the existing schema and offline renderer boundary. Add one closed bilingual coaching table keyed by `question.kind`, make the rehearsal helper fail closed, and make sourced pre-feedback composition place the fixed next-action region before the scaffold. Preserve independent and feedback flows, then exercise the behavior in both the repository behavioral suite and the plugin-local release gate.

**Tech Stack:** Python 3 standard library, generated offline HTML, CSS already present in the plugin, `unittest`, plugin static/schema gates, local Codex plugin marketplace.

## Global Constraints

- Do not change the recruiter-practice JSON Schema or accepted state machine.
- Do not add forms, inputs, textareas, buttons, links, clipboard actions, automatic navigation, persistence, scores, or external actions.
- Render coaching labels only from fixed bilingual copy selected by validated `question.kind`; never interpolate candidate prose into coaching copy.
- Preserve escaping, raw-answer omission, internal identifier omission, CSP/offline behavior, print, responsive, forced-colors, prefers-contrast, and quiet ARIA behavior.
- `eligibility_boundary` and `compensation_boundary` copy must not assert rights, amounts, fit, availability, or outcomes.
- Keep the functional change surgical: renderer plus focused tests and release evidence only.
- Run the official cachebuster exactly once, after all functional review and pre-release gates are green.
- Install only through `codex plugin add job-search-coach@job-search-coach-local --json`; do not edit the installed cache or marketplace configuration manually.

---

### Task 1: Closed question-kind coaching and truthful awaiting state

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_recruiter_practice_session.py:59-150,208-217,237-247`
- Modify: `tests/test_render_recruiter_practice_session.py:103-149,193-196`

**Interfaces:**
- Consumes: validated `locale` in `{"es", "en"}` and validated `question.kind` in the existing five-value enum.
- Produces: `REHEARSAL_COPY[locale][question_kind]` entries with `hint: str` and `steps: tuple[str, str, str]`; `_render_rehearsal_scaffold(locale: str, question_kind: str, labels: Mapping[str, str]) -> str`.

- [ ] **Step 1: Write failing bilingual kind-copy and state tests**

Add a closed expected table to `RecruiterPracticeSessionRendererTests` and test every kind in both locales:

```python
def test_each_question_kind_renders_closed_bilingual_coaching(self) -> None:
    expected = {
        "screen_opening": {
            "es": ("Prepara una apertura breve que conecte el contexto confirmado con la conversación.", ("Contexto confirmado", "Enfoque relevante", "Puente a la conversación")),
            "en": ("Prepare a brief opening that connects confirmed context to the conversation.", ("Confirmed context", "Relevant focus", "Conversation bridge")),
        },
        "proof_example": {
            "es": ("Presenta una evidencia confirmada en tres movimientos fáciles de seguir.", ("Contexto de la evidencia", "Acción técnica concreta", "Impacto observado directo")),
            "en": ("Present confirmed evidence in three easy-to-follow moves.", ("Evidence context", "Concrete technical action", "Directly observed impact")),
        },
        "eligibility_boundary": {
            "es": ("Separa lo confirmado de la pregunta de elegibilidad que aún debe aclararse.", ("Contexto confirmado", "Pregunta abierta", "Límite seguro")),
            "en": ("Separate confirmed context from the eligibility question that still needs clarification.", ("Confirmed context", "Open question", "Safe boundary")),
        },
        "compensation_boundary": {
            "es": ("Separa lo conocido de la condición de compensación que necesitas aclarar.", ("Contexto conocido", "Pregunta de compensación", "Límite de decisión")),
            "en": ("Separate what is known from the compensation condition you need to clarify.", ("Known context", "Compensation question", "Decision boundary")),
        },
        "missing_detail": {
            "es": ("Expón lo mínimo conocido y formula solo el detalle que falta confirmar.", ("Mínimo confirmado", "Detalle faltante", "Próxima confirmación")),
            "en": ("State the minimum known context and ask only for the detail still needing confirmation.", ("Confirmed minimum", "Missing detail", "Next confirmation")),
        },
    }
    self.assertEqual(set(self.renderer.REHEARSAL_COPY), {"es", "en"})
    for locale in ("es", "en"):
        self.assertEqual(set(self.renderer.REHEARSAL_COPY[locale]), set(expected))
    for kind, localized in expected.items():
        for locale, (hint, steps) in localized.items():
            with self.subTest(kind=kind, locale=locale):
                session = copy.deepcopy(self.awaiting_session)
                session["question"]["kind"] = kind
                session["locale"] = locale
                rendered = self.renderer.render_session_html(session)
                rehearsal = rendered.split('<section class="practice-rehearsal"', 1)[1].split("</section>", 1)[0]
                self.assertIn(f'<p class="practice-rehearsal-hint">{hint}</p>', rehearsal)
                self.assertEqual(re.findall(r"<li>(.*?)</li>", rehearsal), list(steps))
```

Update state expectations and add the fail-closed helper test:

```python
self.assertIn("Lista para responder", rendered)
self.assertNotIn("Esperando tu respuesta", rendered)
self.assertIn("Ready to answer", english)
self.assertNotIn("Awaiting your answer", english)

with self.assertRaisesRegex(ValueError, "unsupported recruiter practice question kind: free_form"):
    self.renderer._render_rehearsal_scaffold("es", "free_form", self.renderer.COPY["es"])
```

Explicitly replace every old root-test expectation for `Esperando tu
respuesta`, `Awaiting your answer`, and the generic `Contexto breve / Acción
concreta / Resultado observado` scaffold. No old sourced-copy expectation may
remain after Task 1.

- [ ] **Step 2: Run the focused tests and confirm RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_recruiter_practice_session -q
```

Expected: failures show the old awaiting labels, generic scaffold, old helper signature, and missing kind-specific copy.

- [ ] **Step 3: Add the minimal closed coaching mapping and renderer**

In `render_recruiter_practice_session.py`:

```python
REHEARSAL_COPY = {
    "es": {
        "screen_opening": {
            "hint": "Prepara una apertura breve que conecte el contexto confirmado con la conversación.",
            "steps": ("Contexto confirmado", "Enfoque relevante", "Puente a la conversación"),
        },
        "proof_example": {
            "hint": "Presenta una evidencia confirmada en tres movimientos fáciles de seguir.",
            "steps": ("Contexto de la evidencia", "Acción técnica concreta", "Impacto observado directo"),
        },
        "eligibility_boundary": {
            "hint": "Separa lo confirmado de la pregunta de elegibilidad que aún debe aclararse.",
            "steps": ("Contexto confirmado", "Pregunta abierta", "Límite seguro"),
        },
        "compensation_boundary": {
            "hint": "Separa lo conocido de la condición de compensación que necesitas aclarar.",
            "steps": ("Contexto conocido", "Pregunta de compensación", "Límite de decisión"),
        },
        "missing_detail": {
            "hint": "Expón lo mínimo conocido y formula solo el detalle que falta confirmar.",
            "steps": ("Mínimo confirmado", "Detalle faltante", "Próxima confirmación"),
        },
    },
    "en": {
        "screen_opening": {
            "hint": "Prepare a brief opening that connects confirmed context to the conversation.",
            "steps": ("Confirmed context", "Relevant focus", "Conversation bridge"),
        },
        "proof_example": {
            "hint": "Present confirmed evidence in three easy-to-follow moves.",
            "steps": ("Evidence context", "Concrete technical action", "Directly observed impact"),
        },
        "eligibility_boundary": {
            "hint": "Separate confirmed context from the eligibility question that still needs clarification.",
            "steps": ("Confirmed context", "Open question", "Safe boundary"),
        },
        "compensation_boundary": {
            "hint": "Separate what is known from the compensation condition you need to clarify.",
            "steps": ("Known context", "Compensation question", "Decision boundary"),
        },
        "missing_detail": {
            "hint": "State the minimum known context and ask only for the detail still needing confirmation.",
            "steps": ("Confirmed minimum", "Missing detail", "Next confirmation"),
        },
    },
}

def _render_rehearsal_scaffold(
    locale: str, question_kind: str, labels: Mapping[str, str]
) -> str:
    try:
        coaching = REHEARSAL_COPY[locale][question_kind]
    except KeyError as error:
        raise ValueError(
            f"unsupported recruiter practice question kind: {question_kind}"
        ) from error
    steps = coaching["steps"]
    return f'''<section class="practice-rehearsal" aria-labelledby="rehearsal-title">
      <h2 id="rehearsal-title">{labels["rehearsal"]}</h2>
      <p class="practice-rehearsal-hint">{coaching["hint"]}</p>
      <ol>{"".join(f"<li>{step}</li>" for step in steps)}</ol>
    </section>'''
```

Set `COPY["es"]["awaiting_answer"] = "Lista para responder"` and
`COPY["en"]["awaiting_answer"] = "Ready to answer"`. Remove the now-unused
generic rehearsal hint/step keys. In `_render_main`, obtain
`question_kind = _text(question["kind"])` and call
`_render_rehearsal_scaffold(locale, question_kind, labels)`.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_recruiter_practice_session -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_recruiter_practice_session -q
```

Expected: both modules pass; schema and validation behavior remain unchanged.

- [ ] **Step 5: Commit Task 1**

```bash
git add plugins/job-search-coach/scripts/render_recruiter_practice_session.py tests/test_render_recruiter_practice_session.py
git commit -m "feat: tailor recruiter practice coaching"
```

---

### Task 2: Decision-led sourced continuation

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_recruiter_practice_session.py:59-150,220-260`
- Modify: `tests/test_render_recruiter_practice_session.py:122-179,193-196`

**Interfaces:**
- Consumes: `_render_rehearsal_scaffold(locale, question_kind, labels)` from Task 1, validated `state`, and `sourced = session.get("handoff_context") is not None`.
- Produces: `_render_next_action(state: str, labels: Mapping[str, str], *, sourced: bool) -> str`; sourced pre-feedback sequence `handoff -> next_action -> rehearsal`.

- [ ] **Step 1: Write failing order, venue, ARIA, independence, and privacy tests**

Replace the old sourced-order assertion with:

```python
def test_sourced_pre_feedback_session_is_decision_led(self) -> None:
    sourced = self.renderer.render_session_html(self.awaiting_session)
    handoff = sourced.index('<aside class="practice-handoff ')
    next_action = sourced.index('<section class="practice-next-action')
    rehearsal = sourced.index('<section class="practice-rehearsal"')
    evidence = sourced.index('<section class="practice-evidence"')
    boundary = sourced.index('<aside class="practice-boundary"')
    self.assertLess(handoff, next_action)
    self.assertLess(next_action, rehearsal)
    self.assertLess(rehearsal, evidence)
    self.assertLess(evidence, boundary)
    self.assertIn("Regresa a la conversación privada de Codex que originó esta práctica", sourced)
    self.assertIn("Esta página no guarda tu respuesta.", sourced)
    next_action_html = sourced.split(
        '<section class="practice-next-action', 1
    )[1].split("</section>", 1)[0]
    self.assertIn(
        'aria-describedby="prompt-title practice-question-text"',
        next_action_html,
    )
    self.assertNotIn("rehearsal-title", next_action_html)
```

Add exact ES/EN sourced ready/awaiting copy assertions and independent-session
assertions:

```python
expected_sourced = {
    ("es", "ready_to_practice"): "Lee la pregunta y prepara tu respuesta; después regresa a la conversación privada de Codex que originó esta práctica. Esta página no guarda tu respuesta.",
    ("es", "awaiting_answer"): "Regresa a la conversación privada de Codex que originó esta práctica para responder. Esta página no guarda tu respuesta.",
    ("en", "ready_to_practice"): "Read the question and prepare your answer; then return to the private Codex conversation that originated this practice. This page does not save your answer.",
    ("en", "awaiting_answer"): "Return to the private Codex conversation that originated this practice to answer. This page does not save your answer.",
}
for (locale, state), expected_copy in expected_sourced.items():
    candidate = self.english_session() if locale == "en" else copy.deepcopy(self.awaiting_session)
    candidate["state"] = state
    with self.subTest(locale=locale, state=state):
        self.assertIn(f"<p>{expected_copy}</p>", self.renderer.render_session_html(candidate))

expected_independent = {
    ("es", "ready_to_practice"): "Lee la pregunta y prepara tu respuesta en tres movimientos. No se guarda tu respuesta.",
    ("es", "awaiting_answer"): "Responde con contexto breve, acción concreta y resultado observado. No se guarda tu respuesta.",
    ("en", "ready_to_practice"): "Read the question and prepare your answer in three moves. Your answer is not saved.",
    ("en", "awaiting_answer"): "Answer with brief context, a concrete action, and an observed result. Your answer is not saved.",
}
for (locale, state), expected_copy in expected_independent.items():
    candidate = self.english_session() if locale == "en" else copy.deepcopy(self.awaiting_session)
    candidate["state"] = state
    candidate.pop("handoff_context")
    with self.subTest(locale=locale, state=state, sourced=False):
        self.assertIn(f"<p>{expected_copy}</p>", self.renderer.render_session_html(candidate))

expected_feedback = {
    "es": "Revisa los comentarios y decide qué quieres volver a practicar. No se guarda tu respuesta.",
    "en": "Review the feedback and decide what you want to rehearse again. Your answer is not saved.",
}
for locale, expected_copy in expected_feedback.items():
    for sourced in (True, False):
        candidate = self.feedback_session()
        candidate["locale"] = locale
        if not sourced:
            candidate.pop("handoff_context")
        with self.subTest(locale=locale, state="feedback_available", sourced=sourced):
            self.assertIn(f"<p>{expected_copy}</p>", self.renderer.render_session_html(candidate))

independent = copy.deepcopy(self.awaiting_session)
independent.pop("handoff_context")
independent_html = self.renderer.render_session_html(independent)
self.assertLess(independent_html.index('<section class="practice-rehearsal"'), independent_html.index('<section class="practice-next-action'))
self.assertNotIn("originó esta práctica", independent_html)
self.assertNotIn("originated this practice", independent_html)
```

Update `test_ready_and_awaiting_states_have_distinct_next_actions` so sourced
sessions require the new fixed sourced strings. Update
`test_feedback_next_action_references_feedback_region_only_when_available` so
the sourced awaiting next action requires
`prompt-title practice-question-text`; add the independent candidate above to
retain the old `prompt-title rehearsal-title` assertion.

Add one parameterized sequence matrix that extracts section indices and the
next-action region for all six sourced/independent state combinations:

| Case | Expected order | Next-action description |
| --- | --- | --- |
| sourced ready/awaiting | `handoff < next < rehearsal < evidence < boundary` | `prompt-title practice-question-text` |
| independent ready/awaiting | `rehearsal < next < evidence < boundary` | `prompt-title rehearsal-title` |
| sourced feedback | `handoff < rehearsal < next < feedback < evidence < boundary` | `feedback-title` |
| independent feedback | `rehearsal < next < feedback < evidence < boundary` | `feedback-title` |

For each rendered matrix document, collect every `id="..."`, assert IDs are
unique, then parse every space-separated token in `aria-labelledby` and
`aria-describedby` and assert that each resolves to an ID in the same document.

Preserve feedback assertions and add a compact unsafe-surface regression:

```python
for forbidden in ("<form", "<input", "<textarea", "<button"):
    self.assertNotIn(forbidden, sourced.casefold())
self.assertEqual(sourced.count("href="), 1)  # skip link only
self.assertNotRegex(sourced, r"\b(?:Q|R|F|C|E|OBS|RB)-\d{3}\b")
self.assertNotIn("source_snapshot", sourced)
self.assertNotIn("external_actions_authorized", sourced)
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_recruiter_practice_session -q
```

Expected: the old sequence is `handoff -> rehearsal -> next_action`; venue copy and prompt/question ARIA relationship are absent.

- [ ] **Step 3: Add fixed sourced copy and conditional composition**

Add these fixed COPY entries:

```python
"next_action_sourced_ready": "Lee la pregunta y prepara tu respuesta; después regresa a la conversación privada de Codex que originó esta práctica. Esta página no guarda tu respuesta.",
"next_action_sourced_answer": "Regresa a la conversación privada de Codex que originó esta práctica para responder. Esta página no guarda tu respuesta.",
```

and the exact English translations from the specification. Update the helper:

```python
def _render_next_action(
    state: str, labels: Mapping[str, str], *, sourced: bool
) -> str:
    copy_keys = {
        "ready_to_practice": "next_action_sourced_ready" if sourced else "next_action_ready",
        "awaiting_answer": "next_action_sourced_answer" if sourced else "next_action_answer",
        "feedback_available": "next_action_feedback",
    }
    try:
        copy_key = copy_keys[state]
    except KeyError as error:
        raise ValueError(f"unsupported recruiter practice state: {state}") from error
    if state == "feedback_available":
        described_by = "feedback-title"
    elif sourced:
        described_by = "prompt-title practice-question-text"
    else:
        described_by = "prompt-title rehearsal-title"
    return f'''<section class="practice-next-action practice-next-action--{html.escape(state)}" aria-labelledby="next-action-title" aria-describedby="{described_by}">
      <h2 id="next-action-title">{labels["next_action"]}</h2>
      <p>{labels[copy_key]}</p>
    </section>'''
```

Compose `_render_main` with the existing feedback branch preserved:

```python
sourced = session.get("handoff_context") is not None
next_action = _render_next_action(state, labels, sourced=sourced)
if state == "feedback_available":
    practice_sequence = f"{handoff}{rehearsal}{next_action}{feedback}"
elif sourced:
    practice_sequence = f"{handoff}{next_action}{rehearsal}"
else:
    practice_sequence = f"{rehearsal}{next_action}"
```

Update the direct unknown-state test to pass `sourced=False`.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_recruiter_practice_session -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_recruiter_practice_session -q
```

Expected: both pass; feedback behavior and contract remain unchanged.

- [ ] **Step 5: Commit Task 2**

```bash
git add plugins/job-search-coach/scripts/render_recruiter_practice_session.py tests/test_render_recruiter_practice_session.py
git commit -m "feat: clarify private practice continuation"
```

---

### Task 3: Plugin-local release regression and independent review

**Files:**
- Modify: `plugins/job-search-coach/tests/test_render_recruiter_practice_session.py:96-123`
- Review only: `plugins/job-search-coach/scripts/render_recruiter_practice_session.py`
- Review only: `tests/test_render_recruiter_practice_session.py`

**Interfaces:**
- Consumes: final renderer behavior from Tasks 1 and 2.
- Produces: plugin-local discovery coverage that fails if any closed kind loses its unique scaffold or if sourced continuation loses its truthful response venue.

- [ ] **Step 1: Replace the generic plugin-local scaffold expectations**

Keep the existing minimal valid session and change its proof assertions to:

```python
self.assertIn("Presenta una evidencia confirmada", rendered)
self.assertIn("Contexto de la evidencia", rendered)
self.assertIn("Acción técnica concreta", rendered)
self.assertIn("Impacto observado directo", rendered)
self.assertNotIn("Contexto breve", rendered)
```

Add a loop over all five kinds using copies of the same accepted session and
assert one unique ES step per kind:

```python
expected_steps = {
    "screen_opening": "Puente a la conversación",
    "proof_example": "Impacto observado directo",
    "eligibility_boundary": "Pregunta abierta",
    "compensation_boundary": "Pregunta de compensación",
    "missing_detail": "Detalle faltante",
}
for kind, expected_step in expected_steps.items():
    candidate = copy.deepcopy(session)
    candidate["question"]["kind"] = kind
    with self.subTest(kind=kind):
        self.assertIn(expected_step, renderer.render_session_html(candidate))
```

Import `copy` at the top of the module. Add a sourced variation by attaching
this exact validated handoff shape to a copy of the minimal session:

```python
sourced = copy.deepcopy(session)
sourced["handoff_context"] = {
    "source": "executive_career_dossier",
    "source_snapshot": "snap-dossier-001",
    "question_rank": 1,
    "question_id": "Q-001",
    "requirement_id": "R-001",
    "fact_ids": ["F-001"],
    "claim_ids": ["C-001"],
    "evidence_ids": ["E-001"],
    "draft_only": True,
    "external_actions_authorized": False,
}
sourced_html = renderer.render_session_html(sourced)
self.assertLess(
    sourced_html.index('<section class="practice-next-action'),
    sourced_html.index('<section class="practice-rehearsal"'),
)
self.assertIn("Lista para responder", sourced_html)
self.assertIn(
    "Regresa a la conversación privada de Codex que originó esta práctica",
    sourced_html,
)
```

- [ ] **Step 2: Run plugin-local discovery and confirm GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/job-search-coach/tests -p 'test_render_recruiter_practice_session.py' -q
```

Expected: all plugin-local renderer tests pass.

- [ ] **Step 3: Run the combined functional suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_recruiter_practice_session tests.test_recruiter_practice_session -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/job-search-coach/tests -p 'test*.py' -q
git diff --check
```

Expected: every test passes and the diff check is silent. Do not use
`py_compile`; it writes `__pycache__` even with `-B`.

- [ ] **Step 4: Render and inspect the approved visual matrix**

Create temporary, private HTML outputs outside the repository for these exact
valid sessions: sourced awaiting ES, sourced ready EN, independent awaiting ES,
sourced feedback ES, and independent feedback ES. Use the canonical fixture as
the base; mutations must preserve validator acceptance, and the feedback
variants must use a unique raw-answer sentinel.

Use the local browser-control workflow to capture and inspect:

- sourced awaiting ES at 1440 px and 360 px;
- sourced ready EN at 1440 px and 360 px;
- independent awaiting at 1440 px and 360 px;
- sourced and independent feedback at 1440 px;
- print preview for the sourced awaiting and sourced feedback artifacts;
- forced-colors and `prefers-contrast: more` emulation for sourced awaiting.

Acceptance is visual and semantic: no horizontal overflow; sourced pre-feedback
reads `handoff -> next step -> scaffold`; independent pre-feedback reads
`scaffold -> next step`; feedback reads `handoff? -> scaffold -> next step ->
feedback`; headings remain attached to their blocks in print; state, handoff,
next action, and boundary remain distinguishable without color. Store
screenshots only under a temporary directory and do not stage them.

- [ ] **Step 5: Request independent specification and code-quality reviews**

Dispatch separate fresh reviewers. The specification reviewer checks exact
copy, state, order, independence, feedback preservation, accessibility, and
privacy requirements. The code-quality reviewer checks mapping closure,
escaping, fail-closed behavior, test strength, and absence of unrelated edits.
Fix every confirmed finding with a new focused RED/GREEN cycle and repeat the
affected review until approved.

- [ ] **Step 6: Commit Task 3**

```bash
git add plugins/job-search-coach/tests/test_render_recruiter_practice_session.py
git commit -m "test: gate decision-led recruiter practice"
```

If a review fix changes runtime or root tests, include only those reviewed
files and use a separate descriptive fix commit before this test commit.

---

### Task 4: Verify, publish, install, and prove identity

**Files:**
- Modify: `tests/evals/final/cycle-1.md`
- Modify: `tests/evals/final/cycle-1/*.json`
- Modify: `tests/evals/final/cycle-2.md`
- Modify: `tests/evals/final/cycle-2/*.json`
- Modify exactly once: `plugins/job-search-coach/.codex-plugin/plugin.json`

**Interfaces:**
- Consumes: reviewed functional HEAD and `plugins/job-search-coach` tree.
- Produces: one new cache-busted plugin version installed from `job-search-coach-local`, with final fixtures bound to the functional commit/tree and exact installed-source identity.

- [ ] **Step 1: Run pre-release functional and privacy gates**

Run each command separately:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_recruiter_practice_session tests.test_recruiter_practice_session -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/job-search-coach/tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_plugin_structure tests.test_repository_privacy -v
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
bash scripts/run_release_validation.sh
git diff --check
```

Expected: all functional/plugin suites, privacy scan, and official release
validators pass. Do not run the provenance-sensitive full-plugin/static gates
until Step 2 refreshes their fixtures.

- [ ] **Step 2: Bind deterministic final fixtures to the functional commit**

Resolve `git rev-parse HEAD` and `git rev-parse HEAD:plugins/job-search-coach`.
Mechanically replace only `source_commit` and `source_tree` in the cycle-1 and
cycle-2 Markdown/JSON provenance fixtures. Then run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/job-search-coach/tests/run_static_checks.py
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test*.py' -q
git diff --check
```

Expected: provenance is the only eval change; static/schema and the complete
repository suite pass on the exact pre-manifest functional tree.

- [ ] **Step 3: Invoke the official cachebuster exactly once**

Run once:

```bash
python3 -B /Users/kevinriosferrer/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py plugins/job-search-coach
```

Expected: exactly one new `0.2.0+codex.<timestamp>` version in
`plugins/job-search-coach/.codex-plugin/plugin.json`. Never rerun this command
inside the increment.

- [ ] **Step 4: Re-run gates and commit publication metadata**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/job-search-coach/tests/run_static_checks.py
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/job-search-coach/tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_plugin_structure tests.test_repository_privacy -v
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
bash scripts/run_release_validation.sh
git diff --check
```

Stage only the manifest and deterministic cycle provenance files, then commit:

```bash
git commit -m "chore: publish decision-led recruiter practice"
```

- [ ] **Step 5: Confirm installation authorization and install the exact published plugin**

The active user objective explicitly authorizes publishing and loading every
increment. Immediately before mutation, state the exact target
`job-search-coach@job-search-coach-local` and exact command below. If that
standing authorization is absent or revoked in the executing conversation,
stop after source publication and request it; do not infer approval from code
or design approval alone.

Run:

```bash
codex plugin add job-search-coach@job-search-coach-local --json
codex plugin list --json
```

Expected: the add result reports the exact source manifest version and the list
reports matching `pluginId`, version, `installed=true`, and `enabled=true`.
Do not treat `source.path` as the cache path; for a local marketplace it points
to the worktree source.

- [ ] **Step 6: Prove installed/source identity and smoke the installed renderer**

Read the published version from the source manifest. Within the bounded cache
root `~/.codex/plugins/cache/job-search-coach-local/job-search-coach`, resolve
directories whose basename exactly equals that version and require exactly one
match; zero or multiple matches fail the release. Do not use the `source.path`
from `codex plugin list` for this comparison.

Run in one verification shell so the task-specific values remain bound:

```bash
published_version=$(python3 -B -c 'import json, pathlib; print(json.loads(pathlib.Path("plugins/job-search-coach/.codex-plugin/plugin.json").read_text(encoding="utf-8"))["version"])')
installed_root=$(PUBLISHED_VERSION="$published_version" python3 -B -c 'import os; from pathlib import Path; root = Path.home() / ".codex" / "plugins" / "cache" / "job-search-coach-local" / "job-search-coach"; matches = [path for path in root.iterdir() if path.is_dir() and path.name == os.environ["PUBLISHED_VERSION"]]; len(matches) == 1 or (_ for _ in ()).throw(SystemExit(f"expected exactly one installed cache directory, found {len(matches)}")); print(matches[0])')
test -d "$installed_root"
diff -qr plugins/job-search-coach "$installed_root"
SOURCE_PLUGIN_ROOT="$installed_root" LINKEDIN_SKILL_ROOT="$installed_root/skills/optimize-linkedin-career" bash scripts/run_release_validation.sh
```

Compare `plugins/job-search-coach` against that exact versioned cache directory
with `diff -qr`; require no output. Set `SOURCE_PLUGIN_ROOT` to that directory
and `LINKEDIN_SKILL_ROOT` to its installed LinkedIn skill, then run
`scripts/run_release_validation.sh` so the checksum-pinned official validators
exercise the cache rather than source.

Render the canonical installed practice fixture and assert the output contains:

```text
Lista para responder
Regresa a la conversación privada de Codex que originó esta práctica
Contexto de la evidencia
Acción técnica concreta
Impacto observado directo
```

Create three additional valid private temporary inputs outside the repository:

1. a dossier-sourced `feedback_available` session with raw answer sentinel
   `PRIVATE-ANSWER-SENTINEL-DO-NOT-RENDER`;
2. a triage-sourced awaiting session with `source=private_recruiter_reply_triage`,
   `source_snapshot=snap-triage-001`, and no dossier-only C/E arrays;
3. an independent awaiting session with no `handoff_context`.

Render all three through the installed renderer. Assert the sentinel, both
source enums, both snapshot values, Q/R/F/C/E/OBS/RB identifiers,
`aria-live`, `role="status"`, forms, inputs, textareas, buttons,
`external_actions_authorized`, and links other than the one skip link are
absent. Assert the independent output also omits the originating-conversation
claim and preserves `rehearsal < next_action`.

- [ ] **Step 7: Run final completion audit**

Run the Step 4 verification matrix again against published HEAD. Confirm every
specification acceptance item has direct test, rendered-output, gate, and
installed-identity evidence. `git diff --check` must be silent; tracked files
must be clean. The local untracked `.superdesign/` context is not part of the
plugin package and must not be staged into either publication commit.
