# Question-kind-aware Feedback Decision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn categorical recruiter-practice feedback into an evidence-safe,
question-kind-aware decision for the candidate's next private rehearsal.

**Architecture:** Keep the existing recruiter-practice schema, validator,
private writer, and offline HTML boundary unchanged. Add closed bilingual copy
tables and small fail-closed renderer helpers, render feedback before a separate
three-field decision region only in `feedback_available`, and extend the
existing scoped CSS for the approved Superdesign Variation A hierarchy.
Preserve all pre-feedback flows and use validated categorical observations as
the only decision input.

**Tech Stack:** Python 3 standard library, escaped offline HTML, scoped CSS,
`unittest`, local browser visual inspection, plugin static/privacy/release
gates, and the local Codex plugin marketplace.

## Global Constraints

- Approved source is Superdesign Variation A draft
  `29030547-5e3b-4532-874e-67810b45bbbd`; generated Tailwind, remote fonts,
  `data-sd-id`, synthetic facts, and synthetic questions never enter production.
- Do not change the recruiter-practice JSON Schema, validator state machine,
  feedback taxonomy, `score=unknown`, or `score_state=categorical` semantics.
- Closed locales are exactly `{es, en}`; question kinds are exactly
  `{screen_opening, proof_example, eligibility_boundary,
  compensation_boundary, missing_detail}`; labels are exactly
  `{solid, confirm, do_not_assert}`.
- Governing precedence is exactly `do_not_assert > confirm > solid`; accept
  only unique labels in canonical order `solid`, `confirm`, `do_not_assert`.
- `solid` is a supplied categorical observation, not independently verified
  truth, readiness evidence, or an outcome prediction.
- Use confirmed/verified wording only for `proof_example`; the other four kinds
  preserve supplied-evidence wording and accept candidate-reported facts.
- In the new feedback and decision regions, render only fixed copy and localized
  category labels. Never render raw answer, `feedback.statement`, source refs,
  internal IDs, snapshots, source enum, recruiter identity, raw vacancy text,
  URLs, or authorization flags.
- Preserve existing safe context, prompt, evidence, boundary, escaping,
  deterministic output, CSP/offline behavior, atomic mode-`0600` writer, and
  no-save-by-default semantics.
- Add no forms, controls, buttons, `aria-live`, `role=status`, focus target,
  navigation, persistence, network request, scheduling, sending, or external
  action. The page keeps exactly one `href`, the skip link to `#main-content`.
- Feedback and decision remain adjacent. The decision has exactly three ordered
  `dt`/`dd` pairs and no redundant `aria-describedby`.
- Normal text contrast is at least 4.5:1, large text at least 3:1, and meaningful
  borders/non-text indicators at least 3:1. `#dfbf70` remains the decision-term
  color on forest, with approximately 6.69:1 contrast.
- Keep base plugin version `0.2.0`. Run the official cachebuster exactly once,
  only after functional review and all pre-publication gates are green.
- Install only while standing authorization applies, using
  `codex plugin add job-search-coach@job-search-coach-local --json`.
- Never stage `.superdesign/`.

---

### Task 1: Closed coaching copy and governing-label helpers

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_recruiter_practice_session.py:36-182,233-267`
- Modify: `tests/test_render_recruiter_practice_session.py:55-120,290-365`

**Interfaces:**
- Consumes: validated `locale: str`, validated `question_kind: str`, and
  canonical `labels: Sequence[str]`.
- Produces: `QUESTION_KINDS`, `FEEDBACK_LABELS`,
  `FEEDBACK_DESCRIPTION_COPY`, `DECISION_TARGET_COPY`,
  `DECISION_ACTION_COPY`, corrected `REHEARSAL_COPY`,
  `_feedback_description(locale, question_kind, label)`,
  `_decision_target(locale, question_kind)`, `_decision_action(locale, label)`,
  and `_governing_feedback_label(labels)`.

- [ ] **Step 1: Write the failing closed-table and bilingual copy tests**

Add exact expected dictionaries to `RecruiterPracticeSessionRendererTests`.
The expected feedback table is the 30-cell ES/EN `Kind-aware feedback copy`
table in the approved spec
`docs/superpowers/specs/2026-08-09-question-kind-aware-feedback-decision-design.md`.
The test must first assert exact key sets and then assert every leaf through the
public helper:

```python
self.assertEqual(set(self.renderer.FEEDBACK_DESCRIPTION_COPY), {"es", "en"})
for locale, kinds in expected.items():
    self.assertEqual(set(kinds), set(self.renderer.QUESTION_KINDS))
    for kind, label_copy in kinds.items():
        self.assertEqual(set(label_copy), set(self.renderer.FEEDBACK_LABELS))
        for label, sentence in label_copy.items():
            with self.subTest(locale=locale, kind=kind, label=label):
                self.assertEqual(
                    self.renderer._feedback_description(locale, kind, label),
                    sentence,
                )
```

Copy the exact approved `Kind-specific target` and `Governing-label action`
tables into the test. Assert equality with
`DECISION_TARGET_COPY`/`DECISION_ACTION_COPY` and every helper result. Do not
abbreviate or derive expected strings from production constants.

- [ ] **Step 2: Write the failing precedence tests**

```python
def test_governing_feedback_uses_most_cautious_present_label(self) -> None:
    cases = {
        ("solid",): "solid",
        ("confirm",): "confirm",
        ("do_not_assert",): "do_not_assert",
        ("solid", "confirm"): "confirm",
        ("solid", "do_not_assert"): "do_not_assert",
        ("confirm", "do_not_assert"): "do_not_assert",
        ("solid", "confirm", "do_not_assert"): "do_not_assert",
    }
    for labels, expected in cases.items():
        with self.subTest(labels=labels):
            self.assertEqual(
                self.renderer._governing_feedback_label(labels), expected
            )
```

- [ ] **Step 3: Write the failing privacy-safe helper rejection tests**

```python
def test_feedback_decision_helpers_fail_closed_without_echoing_input(self) -> None:
    cases = (
        (lambda: self.renderer._feedback_description("xx-private", "screen_opening", "solid"), "unsupported locale", "xx-private"),
        (lambda: self.renderer._feedback_description("es", "private-kind", "solid"), "unsupported question kind", "private-kind"),
        (lambda: self.renderer._feedback_description("es", "screen_opening", "private-label"), "unsupported feedback label", "private-label"),
        (lambda: self.renderer._decision_target("xx-private", "screen_opening"), "unsupported locale", "xx-private"),
        (lambda: self.renderer._decision_target("es", "private-kind"), "unsupported question kind", "private-kind"),
        (lambda: self.renderer._decision_action("xx-private", "solid"), "unsupported locale", "xx-private"),
        (lambda: self.renderer._decision_action("es", "private-label"), "unsupported feedback label", "private-label"),
        (lambda: self.renderer._governing_feedback_label(()), "feedback labels must not be empty", "private"),
        (lambda: self.renderer._governing_feedback_label(("solid", "solid")), "feedback labels must be unique", "private"),
        (lambda: self.renderer._governing_feedback_label(("confirm", "solid")), "feedback labels must use canonical order", "private"),
        (lambda: self.renderer._governing_feedback_label(("private-label",)), "unsupported feedback label", "private-label"),
    )
    for call, expected, private_value in cases:
        with self.subTest(expected=expected):
            with self.assertRaises(ValueError) as context:
                call()
            self.assertEqual(str(context.exception), expected)
            self.assertNotIn(private_value, str(context.exception))
```

- [ ] **Step 4: Write the failing rehearsal evidence-state tests**

For each non-proof kind, both locales, and all three valid states, set the fact
to `candidate_reported`. Isolate the rehearsal region. Assert the exact strings
from the approved spec's `Rehearsal evidence wording` table and reject all
evidence upgrades:

```python
def test_non_proof_rehearsal_never_upgrades_candidate_reported_facts(self) -> None:
    kinds = (
        "screen_opening",
        "eligibility_boundary",
        "compensation_boundary",
        "missing_detail",
    )
    for locale in ("es", "en"):
        for kind in kinds:
            for state in ("ready_to_practice", "awaiting_answer", "feedback_available"):
                session = self.feedback_session() if state == "feedback_available" else copy.deepcopy(self.awaiting_session)
                session["locale"] = locale
                session["state"] = state
                session["question"]["kind"] = kind
                session["facts"][0]["state"] = "candidate_reported"
                if state != "feedback_available":
                    session["observed_answer"] = None
                    session["feedback"] = {
                        "score": "unknown",
                        "score_state": "unknown",
                        "observations": [],
                    }
                with self.subTest(locale=locale, kind=kind, state=state):
                    rendered = self.renderer.render_session_html(session)
                    rehearsal = rendered.split('<section class="practice-rehearsal"', 1)[1].split("</section>", 1)[0]
                    self.assertNotRegex(
                        rehearsal.casefold(),
                        r"\b(?:confirmad[oa]s?|verified|confirmed)\b",
                    )
```

The test also asserts each locale/kind's exact revised hint and first evidence
step. `proof_example` remains verified and retains confirmed wording.

- [ ] **Step 5: Run the focused test and confirm RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_recruiter_practice_session -q
```

Expected: missing tables/helpers fail; unrelated renderer tests remain green.

- [ ] **Step 6: Implement the closed constants and helpers**

Copy the exact approved tables into the renderer, then add:

```python
QUESTION_KINDS = (
    "screen_opening",
    "proof_example",
    "eligibility_boundary",
    "compensation_boundary",
    "missing_detail",
)
FEEDBACK_LABELS = ("solid", "confirm", "do_not_assert")
FEEDBACK_PRECEDENCE = {
    label: index for index, label in enumerate(FEEDBACK_LABELS)
}


def _require_locale(locale: str) -> None:
    if locale not in ("es", "en"):
        raise ValueError("unsupported locale")


def _require_question_kind(question_kind: str) -> None:
    if question_kind not in QUESTION_KINDS:
        raise ValueError("unsupported question kind")


def _require_feedback_label(label: str) -> None:
    if label not in FEEDBACK_LABELS:
        raise ValueError("unsupported feedback label")


def _feedback_description(locale: str, question_kind: str, label: str) -> str:
    _require_locale(locale)
    _require_question_kind(question_kind)
    _require_feedback_label(label)
    return FEEDBACK_DESCRIPTION_COPY[locale][question_kind][label]


def _decision_target(locale: str, question_kind: str) -> str:
    _require_locale(locale)
    _require_question_kind(question_kind)
    return DECISION_TARGET_COPY[locale][question_kind]


def _decision_action(locale: str, label: str) -> str:
    _require_locale(locale)
    _require_feedback_label(label)
    return DECISION_ACTION_COPY[locale][label]


def _governing_feedback_label(labels: Sequence[str]) -> str:
    if not labels:
        raise ValueError("feedback labels must not be empty")
    if not all(
        isinstance(label, str) and label in FEEDBACK_LABELS for label in labels
    ):
        raise ValueError("unsupported feedback label")
    if len(labels) != len(set(labels)):
        raise ValueError("feedback labels must be unique")
    canonical = tuple(label for label in FEEDBACK_LABELS if label in labels)
    if tuple(labels) != canonical:
        raise ValueError("feedback labels must use canonical order")
    return max(labels, key=FEEDBACK_PRECEDENCE.__getitem__)
```

Remove the three generic `feedback_description_*` keys from `COPY`.

Update `REHEARSAL_COPY` exactly as the approved spec's rehearsal table:

```python
REHEARSAL_COPY["es"]["screen_opening"]["hint"] = "Prepara una apertura breve que conecte la evidencia suministrada con la conversación."
REHEARSAL_COPY["es"]["screen_opening"]["steps"] = ("Contexto suministrado", "Enfoque relevante", "Puente a la conversación")
REHEARSAL_COPY["en"]["screen_opening"]["hint"] = "Prepare a brief opening that connects the supplied evidence to the conversation."
REHEARSAL_COPY["en"]["screen_opening"]["steps"] = ("Supplied context", "Relevant focus", "Conversation bridge")
REHEARSAL_COPY["es"]["eligibility_boundary"]["hint"] = "Separa el dato suministrado de la pregunta de elegibilidad que aún debe aclararse."
REHEARSAL_COPY["es"]["eligibility_boundary"]["steps"] = ("Dato suministrado", "Pregunta abierta", "Límite seguro")
REHEARSAL_COPY["en"]["eligibility_boundary"]["hint"] = "Separate the supplied fact from the eligibility question that still needs clarification."
REHEARSAL_COPY["en"]["eligibility_boundary"]["steps"] = ("Supplied fact", "Open question", "Safe boundary")
REHEARSAL_COPY["es"]["missing_detail"]["hint"] = "Expón el mínimo suministrado y formula solo el detalle que falta confirmar."
REHEARSAL_COPY["es"]["missing_detail"]["steps"] = ("Mínimo suministrado", "Detalle faltante", "Próxima confirmación")
REHEARSAL_COPY["en"]["missing_detail"]["hint"] = "State the supplied minimum and ask only for the detail still needing confirmation."
REHEARSAL_COPY["en"]["missing_detail"]["steps"] = ("Supplied minimum", "Missing detail", "Next confirmation")
```

Keep compensation's existing known-context wording and proof-example's verified
wording unchanged.

- [ ] **Step 7: Run Task 1 checks and confirm GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_recruiter_practice_session -q
python3 -B -c 'from pathlib import Path; p=Path("plugins/job-search-coach/scripts/render_recruiter_practice_session.py"); compile(p.read_text(encoding="utf-8"), str(p), "exec")'
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 8: Commit Task 1**

```bash
git add plugins/job-search-coach/scripts/render_recruiter_practice_session.py tests/test_render_recruiter_practice_session.py
git commit -m "feat: add kind-aware practice feedback copy"
```

---

### Task 2: Feedback-first decision region and evidence-state safety

**Files:**
- Modify: `plugins/job-search-coach/scripts/render_recruiter_practice_session.py:233-333`
- Modify: `tests/test_render_recruiter_practice_session.py:55-290,365-530`

**Interfaces:**
- Consumes: Task 1 helpers, `session["question"]["kind"]`, and validated
  `feedback.observations` in canonical order.
- Produces: `_render_feedback(locale, question_kind, feedback_labels, labels) -> str`
  and `_render_decision(locale, question_kind, governing_label, labels) -> str`.
- Changes `feedback_available` composition to
  `handoff -> rehearsal -> feedback -> decision -> evidence -> boundary` and
  removes the old feedback-state next-action panel.

- [ ] **Step 1: Write failing kind-aware rendered-feedback tests**

For every locale, kind, and label, build a valid `feedback_available` session,
set non-proof facts to `candidate_reported`, render, isolate the feedback
section, and assert the exact Task 1 sentence:

```python
def test_rendered_feedback_uses_kind_copy_without_upgrading_candidate_reported_facts(self) -> None:
    for locale in ("es", "en"):
        for kind in self.renderer.QUESTION_KINDS:
            for label in self.renderer.FEEDBACK_LABELS:
                session = self.feedback_session()
                session["locale"] = locale
                session["question"]["kind"] = kind
                session["feedback"]["observations"] = [{
                    "label": label,
                    "statement": "Bounded observation.",
                    "source_refs": ["OBS-001", "RB-001"],
                }]
                session["facts"][0]["state"] = (
                    "verified" if kind == "proof_example" else "candidate_reported"
                )
                with self.subTest(locale=locale, kind=kind, label=label):
                    rendered = self.renderer.render_session_html(session)
                    feedback = rendered.split(
                        '<section class="practice-feedback"', 1
                    )[1].split("</section>", 1)[0]
                    rehearsal = rendered.split(
                        '<section class="practice-rehearsal"', 1
                    )[1].split("</section>", 1)[0]
                    decision = rendered.split(
                        '<section class="practice-decision"', 1
                    )[1].split("</section>", 1)[0]
                    self.assertIn(
                        self.renderer._feedback_description(locale, kind, label),
                        feedback,
                    )
                    if kind != "proof_example":
                        self.assertNotRegex(
                            (rehearsal + feedback + decision).casefold(),
                            r"\b(?:confirmad[oa]s?|verified|confirmed)\b",
                        )
```

Add a mixed-observation case proving only present labels render, canonical list
order is preserved, and `feedback.statement` plus raw-answer sentinels remain
absent.

- [ ] **Step 2: Write failing decision hierarchy, precedence, and order tests**

```python
def test_feedback_available_renders_one_three_pair_decision_after_feedback(self) -> None:
    session = self.feedback_session()
    session["feedback"]["observations"] = [
        {
            "label": label,
            "statement": "Bounded observation.",
            "source_refs": ["OBS-001", "RB-001"],
        }
        for label in ("solid", "confirm", "do_not_assert")
    ]
    rendered = self.renderer.render_session_html(session)
    markers = (
        '<aside class="practice-handoff ',
        '<section class="practice-rehearsal"',
        '<section class="practice-feedback"',
        '<section class="practice-decision"',
        '<section class="practice-evidence"',
        '<aside class="practice-boundary"',
    )
    indices = [rendered.index(marker) for marker in markers]
    self.assertEqual(indices, sorted(indices))
    self.assertNotIn("practice-next-action--feedback_available", rendered)
    self.assertEqual(rendered.count('<section class="practice-decision"'), 1)
    decision = rendered.split(
        '<section class="practice-decision"', 1
    )[1].split("</section>", 1)[0]
    self.assertIn('aria-labelledby="decision-title"', decision)
    self.assertNotIn("aria-describedby", decision)
    self.assertEqual(decision.count("<dt>"), 3)
    self.assertEqual(decision.count("<dd>"), 3)
    self.assertLess(
        decision.index("Señal prioritaria"),
        decision.index("Objetivo de esta respuesta"),
    )
    self.assertLess(
        decision.index("Objetivo de esta respuesta"),
        decision.index("Decisión antes de volver a practicar"),
    )
    self.assertIn("No afirmar todavía", decision)
```

Add exact ES/EN explanation assertions:

```python
explanations = {
    "es": "Cuando aparecen varias señales, la que requiere más cautela guía la siguiente versión.",
    "en": "When several signals appear, the one requiring the most caution guides the next version.",
}
```

Update the six-state sequence matrix so the two feedback cases use
`rehearsal, feedback, decision, evidence, boundary`; ready/awaiting cases retain
their current sequence and next-action descriptions.

- [ ] **Step 3: Write failing privacy and ARIA regression tests**

For sourced and independent feedback cases, assert:

```python
self.assertEqual(rendered.count('href="#main-content"'), 1)
self.assertEqual(rendered.count("href="), 1)
for forbidden in (
    "<form", "<input", "<textarea", "<button", "aria-live", 'role="status"'
):
    self.assertNotIn(forbidden, rendered.casefold())
self.assertNotRegex(rendered, r"\b(?:Q|R|F|C|E|OBS|RB)-\d{3}\b")
self.assertNotIn("PRIVATE-ANSWER-SENTINEL", rendered)
self.assertNotIn("PRIVATE-FEEDBACK-SENTINEL", rendered)
```

Collect every `id`, require uniqueness, and resolve every
`aria-labelledby`/`aria-describedby`. Assert feedback alone retains
`aria-describedby="feedback-ephemeral-note"`; decision has no description.

Directly invoke the composed decision helper with private unsupported values:

```python
for locale, kind, label, message, private_value in (
    ("xx-private", "screen_opening", "solid", "unsupported locale", "xx-private"),
    ("es", "private-kind", "solid", "unsupported question kind", "private-kind"),
    ("es", "screen_opening", "private-label", "unsupported feedback label", "private-label"),
):
    with self.subTest(message=message):
        with self.assertRaises(ValueError) as context:
            self.renderer._render_decision(
                locale, kind, label, self.renderer.COPY.get(locale, self.renderer.COPY["es"])
            )
        self.assertEqual(str(context.exception), message)
        self.assertNotIn(private_value, str(context.exception))

for locale, kind, label, message, private_value in (
    ("xx-private", "screen_opening", "solid", "unsupported locale", "xx-private"),
    ("es", "private-kind", "solid", "unsupported question kind", "private-kind"),
    ("es", "screen_opening", "private-label", "unsupported feedback label", "private-label"),
):
    with self.subTest(message=message, helper="feedback"):
        with self.assertRaises(ValueError) as context:
            self.renderer._render_feedback(
                locale,
                kind,
                (label,),
                self.renderer.COPY.get(locale, self.renderer.COPY["es"]),
            )
        self.assertEqual(str(context.exception), message)
        self.assertNotIn(private_value, str(context.exception))
```

Add equivalent direct `_render_feedback` unsupported locale/kind/label cases
with a single categorical label tuple and the standard locale copy mapping.
These helper interfaces receive neither the full session nor observation rows,
so raw answer, `feedback.statement`, and source refs cannot enter them.

- [ ] **Step 4: Run the root renderer suite and confirm RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_recruiter_practice_session -q
```

Expected: failures show generic feedback copy, old feedback next-action, and the
missing decision region.

- [ ] **Step 5: Implement feedback and decision rendering**

Add these ES labels to `COPY` and their exact English translations from the
approved spec:

```python
"decision_heading": "Decide tu siguiente versión",
"decision_governing": "Señal prioritaria",
"decision_target": "Objetivo de esta respuesta",
"decision_action": "Decisión antes de volver a practicar",
"decision_explanation": "Cuando aparecen varias señales, la que requiere más cautela guía la siguiente versión.",
```

Implement:

```python
def _render_feedback(
    locale: str,
    question_kind: str,
    feedback_labels: Sequence[str],
    labels: Mapping[str, str],
) -> str:
    _require_locale(locale)
    _require_question_kind(question_kind)
    _governing_feedback_label(feedback_labels)
    items = "".join(
        f'<li class="feedback-item feedback-item--{label}">'
        f'<span class="feedback-label feedback-label--{label}">'
        f'{labels[label]}:</span> '
        f'{html.escape(_feedback_description(locale, question_kind, label))}</li>'
        for label in feedback_labels
    )
    return f'''<section class="practice-feedback" role="region" aria-labelledby="feedback-title" aria-describedby="feedback-ephemeral-note">
      <h2 id="feedback-title">{labels["feedback"]}</h2>
      <p class="visually-hidden" id="feedback-ephemeral-note">{labels["ephemeral_note"]}</p>
      <ul>{items}</ul>
    </section>'''


def _render_decision(
    locale: str,
    question_kind: str,
    governing_label: str,
    labels: Mapping[str, str],
) -> str:
    _require_locale(locale)
    _require_question_kind(question_kind)
    _require_feedback_label(governing_label)
    return f'''<section class="practice-decision" aria-labelledby="decision-title">
      <h2 id="decision-title">{labels["decision_heading"]}</h2>
      <p class="practice-decision-explanation">{labels["decision_explanation"]}</p>
      <dl>
        <dt>{labels["decision_governing"]}</dt><dd>{labels[governing_label]}</dd>
        <dt>{labels["decision_target"]}</dt><dd>{html.escape(_decision_target(locale, question_kind))}</dd>
        <dt>{labels["decision_action"]}</dt><dd>{html.escape(_decision_action(locale, governing_label))}</dd>
      </dl>
    </section>'''
```

In `_render_main`, only for `feedback_available`, obtain validated observations,
derive their categorical labels before either renderer, and call:

```python
feedback_labels = tuple(
    _text(observation["label"]) for observation in observations
)
governing_label = _governing_feedback_label(feedback_labels)
feedback = _render_feedback(locale, question_kind, feedback_labels, labels)
decision = _render_decision(locale, question_kind, governing_label, labels)
```

Then compose exactly:

```python
practice_sequence = f"{handoff}{rehearsal}{feedback}{decision}"
```

Do not call `_render_next_action` in feedback state. Remove both unused
`next_action_feedback` keys. Keep ready/awaiting composition unchanged.

- [ ] **Step 6: Run Task 2 checks and confirm GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_recruiter_practice_session -q
python3 -B -c 'from pathlib import Path; p=Path("plugins/job-search-coach/scripts/render_recruiter_practice_session.py"); compile(p.read_text(encoding="utf-8"), str(p), "exec")'
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 7: Commit Task 2**

```bash
git add plugins/job-search-coach/scripts/render_recruiter_practice_session.py tests/test_render_recruiter_practice_session.py
git commit -m "feat: add recruiter practice decision region"
```

---

### Task 3: Accessible styling and plugin-facing contract docs

**Files:**
- Modify: `plugins/job-search-coach/assets/recruiter-practice-session-v1.css:1-260`
- Modify: `plugins/job-search-coach/skills/prepare-role-interviews/SKILL.md:26-32`
- Modify: `plugins/job-search-coach/skills/prepare-role-interviews/references/interview-map.md:7-13`
- Modify: `plugins/job-search-coach/tests/test_render_recruiter_practice_session.py:20-165`
- Modify: `tests/test_render_recruiter_practice_session.py:480-590`

**Interfaces:**
- Consumes: `.practice-feedback`, `.feedback-item`, and `.practice-decision`
  markup from Task 2.
- Produces: scoped screen/mobile/print/forced-colors/increased-contrast rules,
  plugin-local behavioral regressions, and skill documentation of the new
  feedback-to-decision behavior.

- [ ] **Step 1: Write failing CSS contract tests**

Add a selector-scoped block helper and assertions against rendered inline CSS.
Generic substring presence is insufficient because the same values occur in
unrelated rules:

```python
def _css_block(self, css: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]+)\}}", css)
    self.assertIsNotNone(match, selector)
    assert match is not None
    return match.group(1)

def test_feedback_decision_css_covers_contrast_mobile_print_and_system_modes(self) -> None:
    rendered = self.renderer.render_session_html(self.feedback_session())
    self.assertIn("--decision-term: #dfbf70;", rendered)
    self.assertIn("color: var(--ink);", self._css_block(rendered, ".recruiter-practice-document .feedback-label"))
    for suffix in ("solid", "confirm", "do_not_assert"):
        block = self._css_block(rendered, f".recruiter-practice-document .feedback-label--{suffix}")
        self.assertIn("color: var(--ink);", block)
    self.assertIn("color: var(--decision-term);", self._css_block(rendered, ".recruiter-practice-document .practice-decision dt"))
    self.assertRegex(rendered, r"(?s)@media \(forced-colors: active\).*?\.practice-feedback[^}]*background: Canvas;[^}]*color: CanvasText;.*?\.practice-decision[^}]*background: Canvas;[^}]*color: CanvasText;")
    self.assertRegex(rendered, r"(?s)@media \(forced-colors: active\).*?\.practice-decision h2,[^{]*\.practice-decision dt,[^{]*\.practice-decision dd\s*\{[^}]*color: CanvasText;")
    self.assertRegex(rendered, r"(?s)@media \(prefers-contrast: more\).*?\.practice-feedback,[^{]*\.feedback-item,[^{]*\.practice-decision\s*\{[^}]*border-width: 2px;")
    self.assertRegex(rendered, r"(?s)@media print.*?\.practice-feedback\s*\{[^}]*break-after: avoid-page;[^}]*\}.*?\.practice-decision\s*\{[^}]*break-before: avoid-page;[^}]*\}")
    self.assertRegex(rendered, r"(?s)@media print.*?\.practice-decision h2,[^{]*\.practice-decision dt,[^{]*\.practice-decision dd\s*\{[^}]*color: var\(--ink\);")
```

Also assert decision `dl`, `dt`, and `dd` have `min-width: 0` or explicit
wrapping and the mobile shell retains `min(100% - 1rem, 920px)`.

- [ ] **Step 2: Write plugin-local semantic and privacy regressions**

Replace the generic feedback-copy test with valid sessions across all five
kinds and both locales. Add one mixed-label case requiring:

```python
self.assertLess(
    rendered.index('<section class="practice-feedback"'),
    rendered.index('<section class="practice-decision"'),
)
self.assertLess(
    rendered.index('<section class="practice-decision"'),
    rendered.index('<section class="practice-evidence"'),
)
self.assertEqual(rendered.count("<dt>"), 3)
self.assertEqual(rendered.count("<dd>"), 3)
self.assertNotIn("practice-next-action--feedback_available", rendered)
self.assertEqual(rendered.count("href="), 1)
self.assertNotRegex(rendered, r"\b(?:Q|R|F|C|E|OBS|RB)-\d{3}\b")
```

Keep canonical taxonomy, pre-answer scaffold, validator parity, and private
answer omission tests green.

- [ ] **Step 3: Run both renderer suites and confirm RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_recruiter_practice_session -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/job-search-coach/tests -p 'test_render_recruiter_practice_session.py' -q
```

Expected: CSS/source-contract assertions fail before styling; plugin-local
semantic assertions fail until they reflect Task 2 markup.

- [ ] **Step 4: Add the scoped Variation A CSS**

Add `--decision-term: #dfbf70`, include `.practice-decision` in shared card
padding/border rules, and implement:

```css
.recruiter-practice-document .practice-decision {
  padding: 1rem;
  border: 1px solid var(--forest);
  border-left: 4px solid var(--decision-term);
  background: var(--forest);
  color: #fff;
}
.recruiter-practice-document .practice-decision h2 { color: #fff; }
.recruiter-practice-document .practice-decision-explanation {
  max-width: var(--measure);
  margin: 0.45rem 0 0;
}
.recruiter-practice-document .practice-decision dl {
  display: grid;
  grid-template-columns: minmax(9rem, 0.35fr) minmax(0, 1fr);
  gap: 0.5rem 1rem;
  margin: 1rem 0 0;
}
.recruiter-practice-document .practice-decision dt {
  min-width: 0;
  color: var(--decision-term);
  font-weight: 700;
}
.recruiter-practice-document .practice-decision dd {
  min-width: 0;
  margin: 0;
  color: #fff;
}
.recruiter-practice-document .feedback-label { color: var(--ink); }
.recruiter-practice-document .feedback-label--solid { color: var(--ink); }
.recruiter-practice-document .feedback-label--confirm { color: var(--ink); }
.recruiter-practice-document .feedback-label--do_not_assert { color: var(--ink); }
```

Replace the current forest/gold/coral `color` declarations on all three
state-specific feedback-label rules rather than adding a weaker rule before
them. State differentiation remains only on item borders and backgrounds.

At `max-width: 640px`, set decision `dl` to one column and retain the existing
0.5rem shell gutters. In forced colors, set feedback, feedback items, and
decision to `Canvas`, `CanvasText`, and visible system borders. In
`prefers-contrast: more`, include feedback, items, and decision in the 2px
border rule. In print add:

```css
.recruiter-practice-document .practice-feedback {
  break-after: avoid-page;
}
.recruiter-practice-document .practice-decision {
  break-inside: avoid;
  page-break-inside: avoid;
  break-before: avoid-page;
  background: transparent;
  color: var(--ink);
  border: 1px solid var(--ink);
}
.recruiter-practice-document .practice-decision h2,
.recruiter-practice-document .practice-decision dt,
.recruiter-practice-document .practice-decision dd {
  color: var(--ink);
}
```

- [ ] **Step 5: Update skill contract documentation**

Add this paragraph to the private practice sections of `SKILL.md` and
`interview-map.md`:

```text
In feedback_available, visible feedback uses fixed bilingual guidance selected
only by the validated question kind and supplied categorical label. The most
cautious present label governs one separate next-private-rehearsal decision:
do_not_assert > confirm > solid. This is evidence-bounded coaching, not semantic
verification, readiness scoring, or an interview-outcome claim; the raw answer
and feedback statement remain omitted from the artifact.
```

- [ ] **Step 6: Run Task 3 checks and confirm GREEN**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_recruiter_practice_session -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/job-search-coach/tests -p 'test_render_recruiter_practice_session.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/job-search-coach/tests/run_static_checks.py
git diff --check
```

Expected: renderer suites exit 0. If the static gate reports only stale
provenance because Tasks 1–3 created commits, record that exact expected result
and defer deterministic fixture refresh to Task 5; no other failure is accepted.

- [ ] **Step 7: Commit Task 3**

```bash
git add plugins/job-search-coach/assets/recruiter-practice-session-v1.css plugins/job-search-coach/skills/prepare-role-interviews/SKILL.md plugins/job-search-coach/skills/prepare-role-interviews/references/interview-map.md plugins/job-search-coach/tests/test_render_recruiter_practice_session.py tests/test_render_recruiter_practice_session.py
git commit -m "feat: style recruiter practice decision feedback"
```

---

### Task 4: Production-render visual verification and independent reviews

**Files:**
- Modify only when a review finds a defect:
  `plugins/job-search-coach/scripts/render_recruiter_practice_session.py`,
  `plugins/job-search-coach/assets/recruiter-practice-session-v1.css`,
  `plugins/job-search-coach/tests/test_render_recruiter_practice_session.py`,
  `tests/test_render_recruiter_practice_session.py`, and the two Task 3 docs.
- Do not add screenshots, temporary fixtures, browser profiles, or
  `.superdesign/` to Git.

**Interfaces:**
- Consumes: Tasks 1–3 functional tree and approved Superdesign Variation A.
- Produces: visual evidence for ES/EN, five kinds, governing-label states,
  desktop/mobile/zoom/print/system modes, plus clean spec and quality reviews.

- [ ] **Step 1: Build private temporary visual fixtures outside the repository**

Use `/tmp` and the canonical fixture to create valid `feedback_available`
variants for every locale × kind × singleton label, plus a mixed-label
sentinel. For non-proof kinds set the fact state to `candidate_reported`; for
`proof_example` keep `verified`. Set raw answer and feedback statements to
private sentinels and validate every fixture before rendering it.

- [ ] **Step 2: Render the production HTML matrix**

Run the actual renderer CLI for each temporary input into a private mode-`0600`
temporary output. Require validator and renderer exit 0, exact fixed copy, one
decision region, three ordered `dt`/`dd` pairs, exactly one skip-link `href`, and
absence of raw-answer/statement/ID/source/snapshot sentinels.

- [ ] **Step 3: Inspect desktop, mobile, 200% zoom, and document order**

Open representative ES and EN production renders in the browser. At desktop,
320px viewport, and 200% zoom, evaluate:

```javascript
const rgb = value => (value.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
const luminance = value => {
  const channels = rgb(value).map(channel => {
    const normalized = channel / 255;
    return normalized <= 0.04045
      ? normalized / 12.92
      : ((normalized + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
};
const contrast = (foreground, background) => {
  const light = Math.max(luminance(foreground), luminance(background));
  const dark = Math.min(luminance(foreground), luminance(background));
  return (light + 0.05) / (dark + 0.05);
};
const feedbackLabels = [...document.querySelectorAll('.feedback-label')];
const decisionTerms = [...document.querySelectorAll('.practice-decision dt')];
({
  fits: document.documentElement.scrollWidth <= document.documentElement.clientWidth,
  visibleTerms: [...document.querySelectorAll('.practice-decision dt, .practice-decision dd')]
    .every(node => node.getBoundingClientRect().width > 0 && node.getBoundingClientRect().height > 0),
  clipped: [...document.querySelectorAll('.practice-decision dt, .practice-decision dd')]
    .some(node => node.scrollWidth > node.clientWidth || node.scrollHeight > node.clientHeight),
  order: [...document.querySelectorAll('.practice-rehearsal, .practice-feedback, .practice-decision, .practice-evidence, .practice-boundary')]
    .map(node => node.className),
  feedbackTextContrast: feedbackLabels.map(node => {
    const style = getComputedStyle(node);
    const itemStyle = getComputedStyle(node.closest('.feedback-item'));
    return contrast(style.color, itemStyle.backgroundColor);
  }),
  decisionTermContrast: decisionTerms.map(node => {
    const style = getComputedStyle(node);
    const panelStyle = getComputedStyle(node.closest('.practice-decision'));
    return contrast(style.color, panelStyle.backgroundColor);
  }),
  meaningfulBorders: [...document.querySelectorAll('.feedback-item, .practice-feedback, .practice-decision')]
    .map(node => {
      const style = getComputedStyle(node);
      return {
        width: parseFloat(style.borderLeftWidth),
        color: style.borderLeftColor,
        adjacentBackground: style.backgroundColor,
        contrast: contrast(style.borderLeftColor, style.backgroundColor),
      };
    }),
})
```

Pass only with `fits=true`, `visibleTerms=true`, `clipped=false`, side gutters
at least 0.5rem, approved DOM order, every normal-text contrast at least 4.5:1,
every large-text contrast at least 3:1, and every meaningful border/adjacent
background contrast at least 3:1. Record computed foreground, background,
border colors, and ratios rather than relying on visual impression alone.

- [ ] **Step 4: Inspect print and accessibility preference modes**

Use browser print preview on sourced feedback ES and EN. Confirm
feedback/decision stay on one page when their combined height fits, headings do
not orphan, and decision prints with white/transparent background, ink text,
and visible border. Exercise forced colors and `prefers-contrast: more` through
available emulation; if one mode cannot be emulated, record the unsupported
capability and require explicit CSS source assertions plus second-reviewer
inspection. Confirm reduced motion disables the existing session animation.

- [ ] **Step 5: Run independent specification and quality reviews**

Dispatch separate expert agents:

1. spec reviewer compares the functional diff to the approved spec and reports
   missing or extra behavior;
2. code/UX reviewer inspects evidence semantics, private-data boundaries,
   helper failure paths, HTML/ARIA, CSS contrast/print/mobile behavior, and test
   adequacy.

Resolve every Critical or Important finding with a focused RED→GREEN test,
rerun affected suites, and repeat both reviews until clean. Screenshot-only
approval is insufficient; reviewers inspect source, tests, and rendered HTML.

- [ ] **Step 6: Run the functional gate matrix**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_render_recruiter_practice_session tests.test_recruiter_practice_session -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/job-search-coach/tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_plugin_structure tests.test_repository_privacy -q
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
bash scripts/run_release_validation.sh
git diff --check
```

Expected: all functional/plugin/privacy/release checks exit 0. Provenance-bound
static/full-repository gates wait for Task 5 Step 2.

- [ ] **Step 7: Commit accepted review fixes**

If review changes were required, stage only scoped functional/test/doc files and
commit:

```bash
git commit -m "fix: address practice decision review"
```

Run `git status --short --untracked-files=all`. Require a clean tracked
worktree and reject every unexpected untracked path; only the known
`.superdesign/` tree may remain untracked.

---

### Task 5: Publish, install, and prove the exact increment

**Files:**
- Modify: `plugins/job-search-coach/.codex-plugin/plugin.json`
- Modify provenance only:
  `tests/evals/final/cycle-1.md`,
  `tests/evals/final/cycle-1/imminent-interview.json`,
  `tests/evals/final/cycle-1/junior.json`,
  `tests/evals/final/cycle-1/non-technical-transition.json`,
  `tests/evals/final/cycle-1/senior-technical.json`,
  `tests/evals/final/cycle-1/two-candidate-coach-mode.json`,
  `tests/evals/final/cycle-1/unsupported-technology-claim.json`,
  `tests/evals/final/cycle-2.md`,
  `tests/evals/final/cycle-2/imminent-interview.json`,
  `tests/evals/final/cycle-2/junior.json`,
  `tests/evals/final/cycle-2/non-technical-transition.json`,
  `tests/evals/final/cycle-2/senior-technical.json`,
  `tests/evals/final/cycle-2/two-candidate-coach-mode.json`, and
  `tests/evals/final/cycle-2/unsupported-technology-claim.json`.

**Interfaces:**
- Consumes: reviewed functional HEAD with green Task 4 gates.
- Produces: one new `0.2.0+codex.<timestamp>` version, deterministic provenance,
  exact installed/source identity, installed-renderer smoke evidence, and clean
  final gates.

- [ ] **Step 1: Freeze the reviewed functional tree**

Run `git status --short --untracked-files=all`, `git log -5 --oneline`, and
`git diff --check`. Require no tracked modification and reject every unexpected
untracked path; only the known `.superdesign/` tree may remain. Record
functional commit and `git rev-parse HEAD:plugins/job-search-coach`. Do not
stage `.superdesign/`.

- [ ] **Step 2: Refresh provenance and run complete pre-cachebuster gates**

Replace only `source_commit` and `source_tree` in the 14 listed cycle fixtures
with exact functional HEAD and plugin tree. Then run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/job-search-coach/tests/run_static_checks.py
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/job-search-coach/tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_plugin_structure tests.test_repository_privacy -q
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
bash scripts/run_release_validation.sh
git diff --check
```

Expected: all gates exit 0. Audit the diff and require provenance fields are the
only eval changes.

- [ ] **Step 3: Invoke the official cachebuster exactly once**

Run once and increment an explicit local invocation counter from 0 to 1:

```bash
python3 -B $HOME/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py plugins/job-search-coach
```

Require one new manifest version starting `0.2.0+codex.`. Never rerun the helper
inside this increment.

- [ ] **Step 4: Re-run publication gates and commit only metadata/provenance**

Repeat the full Step 2 matrix. Stage only manifest and 14 provenance files,
verify `git diff --cached --name-only` contains no other path, then commit:

```bash
git commit -m "chore: publish kind-aware practice decision"
```

Run `git status --short --untracked-files=all`. Require clean tracked state and
reject every untracked path except the known `.superdesign/` tree.

- [ ] **Step 5: Recheck authorization and install the exact plugin**

Immediately before mutation, state exact target
`job-search-coach@job-search-coach-local`. The active objective authorizes
publishing and loading each increment; if authorization is revoked or narrowed,
stop before installation. Otherwise run:

```bash
codex plugin add job-search-coach@job-search-coach-local --json
codex plugin list --json
```

Require exact source manifest version and `installed=true`, `enabled=true`.
Immediately before `codex plugin add`, rerun
`git status --short --untracked-files=all` and enforce the same exact allowlist;
an unexpected cache, fixture, output, or browser artifact stops installation.

- [ ] **Step 6: Prove source/cache identity and installed validation**

Resolve exactly one cache directory whose basename equals the published version
under `~/.codex/plugins/cache/job-search-coach-local/job-search-coach`; do not
use marketplace `source.path`. Run in one shell:

```bash
published_version=$(python3 -B -c 'import json, pathlib; print(json.loads(pathlib.Path("plugins/job-search-coach/.codex-plugin/plugin.json").read_text(encoding="utf-8"))["version"])')
installed_root=$(PUBLISHED_VERSION="$published_version" python3 -B -c 'import os; from pathlib import Path; root = Path.home() / ".codex" / "plugins" / "cache" / "job-search-coach-local" / "job-search-coach"; matches = [path for path in root.iterdir() if path.is_dir() and path.name == os.environ["PUBLISHED_VERSION"]]; len(matches) == 1 or (_ for _ in ()).throw(SystemExit(f"expected exactly one installed cache directory, found {len(matches)}")); print(matches[0])')
test -d "$installed_root"
diff -qr plugins/job-search-coach "$installed_root"
SOURCE_PLUGIN_ROOT="$installed_root" LINKEDIN_SKILL_ROOT="$installed_root/skills/optimize-linkedin-career" bash scripts/run_release_validation.sh
```

Require silent `diff -qr` and installed release validation exit 0.

- [ ] **Step 7: Smoke canonical and privacy sentinels through installed code**

Render from exact installed root:

1. canonical awaiting fixture;
2. sourced ES feedback with mixed labels and raw-answer/statement sentinels;
3. independent EN `eligibility_boundary` with candidate-reported fact;
4. sourced EN `compensation_boundary` governed by `do_not_assert`.

Require exact kind-aware sentences, one decision, correct governing feedback,
three `dt`/`dd` pairs, approved order, one skip `href`, mode `0600`, and absence
of raw sentinels, IDs, snapshots, source enum, forms, controls, `aria-live`,
status roles, remote dependencies, and old generic copy.

- [ ] **Step 8: Run the final gate matrix**

Repeat Task 5 Step 2 from clean publication HEAD and run
`git status --short --untracked-files=all`.
Expected: all gates exit 0; tracked state is clean; only `.superdesign/` remains
untracked. Record functional commit, publication commit, plugin tree, installed
version, installed cache path, test counts, cachebuster count `1`, identity
result, and installed smoke results.

---

## Execution order and review gates

Use `superpowers:subagent-driven-development` because the user requires multiple
expert agents. Tasks 1–3 each receive a fresh implementer plus specification and
quality review before the next task starts. Task 4 uses separate UX and contract
reviewers. Task 5 uses a release-only agent that may not change functional code;
any functional defect returns to the relevant task and invalidates prior release
evidence before cachebusting.

The source-binding contract improvement remains a separate next cycle. Do not
fold it into this renderer increment because it changes cross-artifact
validation rather than the approved feedback decision experience.
