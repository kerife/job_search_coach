# Question-kind-aware feedback decision design

## Status

Approved visual direction: Superdesign Variation A, separate feedback and
decision regions.

- Source design: `510a1cdd-16eb-4891-99a6-d8b152ef02ab`
- Approved branch: `29030547-5e3b-4532-874e-67810b45bbbd`
- Rejected compact branch: `8be2cba4-2b24-44ac-95cf-acea30b5cd22`

The generated HTML is a visual reference only. Production remains the existing
Python renderer, local template, scoped CSS, restrictive CSP, and offline
artifact. No Tailwind runtime, remote font, generated `data-sd-id`, synthetic
fact, or generated question is copied into production.

## Problem

The previous increment made pre-answer coaching depend on the validated
`question.kind`, but the completed-practice state is still proof-example
biased:

- all five kinds receive feedback such as “connects the action to an observed
  result”;
- the generic next step asks the candidate to decide what to rehearse before
  the page identifies which signal governs that decision;
- eligibility, compensation, and missing-detail questions therefore receive
  the wrong answer model;
- the candidate must infer whether the answer is safe to keep, needs a bounded
  confirmation, or must lose an unsupported claim.

This is a preparation-quality defect. The artifact must help the candidate
choose the next truthful private rehearsal; it cannot predict or guarantee a
first interview.

## Candidate decision

After reading observed feedback, the candidate must be able to decide one of
three bounded next states:

1. keep the structure for another private rehearsal within the scope supported
   by the supplied evidence;
2. confirm or qualify one uncertain point, then rehearse again; or
3. remove the unsupported claim, replace it with supported evidence or a
   bounded clarification, or pause the answer.

The page derives this decision from the validated question kind and the most
restrictive feedback label actually present. It never interprets or renders the
raw answer or the feedback observation statement.

## Scope

### In scope

- Make the visible feedback description depend on `question.kind` and the
  existing categorical label.
- Align the existing rehearsal scaffold with the same evidence-state boundary:
  only `proof_example` may use confirmed wording; the four non-proof kinds use
  supplied/known wording in every valid state.
- Derive one governing feedback label with fixed precedence:
  `do_not_assert > confirm > solid`.
- Replace the feedback-state generic next-action panel with a separate,
  labelled decision region immediately after feedback.
- Show the governing signal, the kind-specific answer target, and one bounded
  next-private-rehearsal action.
- Preserve the existing feedback taxonomy, categorical score state, source
  references, raw-answer omission, and no-retention note.
- Add responsive, print, forced-colors, increased-contrast, privacy, and
  release-gate coverage.

### Out of scope

- JSON Schema or validator-contract changes.
- New feedback labels, numeric scores, readiness scores, hiring predictions,
  or interview-success claims.
- Rendering `feedback.statement`, the observed answer, source references,
  provenance snapshots, or internal identifiers.
- Input controls, links, buttons, automatic navigation, persistence, sending,
  scheduling, or another external action.
- Source-bound triage or dossier validation. That integrity improvement is the
  next independent contract cycle.

## Information architecture

Pre-feedback flows remain unchanged.

For `feedback_available`, the production document order is:

1. State
2. Safe context
3. Practice prompt and purpose
4. Source handoff, when present
5. Question-kind-aware rehearsal structure
6. Quiet feedback region
7. Decision for the next private version
8. Evidence
9. Safe boundary
10. No-action footer

The old feedback-state next-action panel is omitted. Feedback and decision are
adjacent, separate named regions. Evidence cannot appear between them.

## Closed derivation

### Governing signal

The validator already guarantees one to three unique observations in canonical
order for `feedback_available`. The renderer still fails closed if it receives
an empty or unknown set.

```text
feedback_labels = labels actually present in feedback.observations
governing_label = max(feedback_labels, precedence)
precedence = solid:0, confirm:1, do_not_assert:2
```

The renderer displays only observations that are present. It does not invent
all three labels.

### Decision composition

The visible decision is composed only from closed fixed copy:

```text
governing signal = existing localized label for governing_label
answer target = DECISION_TARGET_COPY[locale][question_kind]
next private action = DECISION_ACTION_COPY[locale][governing_label]
```

No candidate-controlled prose enters these fields.

### Rehearsal evidence wording

The existing three-step rehearsal remains structurally unchanged. Its
non-proof evidence terms become:

| Kind | ES hint / evidence term | EN hint / evidence term |
| --- | --- | --- |
| `screen_opening` | `Prepara una apertura breve que conecte la evidencia suministrada con la conversación.` / `Contexto suministrado` | `Prepare a brief opening that connects the supplied evidence to the conversation.` / `Supplied context` |
| `eligibility_boundary` | `Separa el dato suministrado de la pregunta de elegibilidad que aún debe aclararse.` / `Dato suministrado` | `Separate the supplied fact from the eligibility question that still needs clarification.` / `Supplied fact` |
| `compensation_boundary` | Retain `Separa lo conocido...` / `Contexto conocido` | Retain `Separate what is known...` / `Known context` |
| `missing_detail` | `Expón el mínimo suministrado y formula solo el detalle que falta confirmar.` / `Mínimo suministrado` | `State the supplied minimum and ask only for the detail still needing confirmation.` / `Supplied minimum` |

`proof_example` retains its confirmed wording because the validator requires a
verified fact for that kind. No state changes, facts, or schema fields are
introduced.

## Kind-aware feedback copy

### Spanish

| Kind | `solid` | `confirm` | `do_not_assert` |
| --- | --- | --- | --- |
| `screen_opening` | Una versión respaldada mantiene el posicionamiento dentro del alcance de la evidencia suministrada y crea un puente relevante hacia la conversación. | Confirma o acota el enfoque antes de usar esta apertura para representar tu experiencia. | Quita de la apertura cualquier afirmación de ajuste, propiedad, disponibilidad o resultado que no esté respaldada. |
| `proof_example` | Una versión respaldada distingue el contexto confirmado, una acción concreta y un impacto observado directamente. | Confirma el alcance o el impacto antes de presentarlo como hecho. | Quita la afirmación sin respaldo; sustitúyela por evidencia confirmada o pausa este ejemplo. |
| `eligibility_boundary` | Una versión respaldada separa el dato suministrado, la condición de elegibilidad aún desconocida y una aclaración concreta. | Confirma la condición de elegibilidad pendiente antes de presentarla como hecho. | No afirmes elegibilidad, autorización o disponibilidad que no esté respaldada; formula una pregunta acotada o pausa la respuesta. |
| `compensation_boundary` | Una versión respaldada separa la evidencia suministrada, la condición de compensación pendiente y el límite de decisión. | Confirma la condición, el rango o el contexto pendiente antes de depender de ello en el ensayo privado. | No afirmes monto, rango, moneda o aceptación sin evidencia; conviértelo en una aclaración o pausa la respuesta. |
| `missing_detail` | Una versión respaldada presenta el mínimo suministrado y nombra un solo detalle que aún necesita aclaración antes del próximo ensayo privado. | Confirma el detalle faltante antes de depender de él en la respuesta. | Quita el detalle sin respaldo; pide una sola aclaración o pausa la respuesta. |

### English

| Kind | `solid` | `confirm` | `do_not_assert` |
| --- | --- | --- | --- |
| `screen_opening` | A supported version keeps the positioning within the scope of the supplied evidence and creates a relevant bridge into the conversation. | Confirm or qualify the focus before using this opening to represent your experience. | Remove any unsupported fit, ownership, availability, or outcome claim from the opening. |
| `proof_example` | A supported version distinguishes confirmed context, a concrete action, and directly observed impact. | Confirm the scope or impact before presenting it as fact. | Remove the unsupported claim; replace it with confirmed evidence or pause this example. |
| `eligibility_boundary` | A supported version separates the supplied fact, the still-unknown eligibility condition, and one concrete clarification. | Confirm the pending eligibility condition before presenting it as fact. | Do not assert unsupported eligibility, authorization, or availability; ask one bounded question or pause the answer. |
| `compensation_boundary` | A supported version separates the supplied evidence, the pending compensation condition, and the decision boundary. | Confirm the pending condition, range, or context before relying on it in the private rehearsal. | Do not assert an unsupported amount, range, currency, or acceptance; turn it into a clarification or pause the answer. |
| `missing_detail` | A supported version presents the supplied minimum and names one detail that still needs clarification before the next private rehearsal. | Confirm the missing detail before relying on it in the answer. | Remove the unsupported detail; ask one clarification or pause the answer. |

These sentences describe only observable structure and evidence boundaries.
They do not claim legal eligibility, work authorization, availability,
compensation, fit, outcome, or readiness.

## Decision copy

### Field labels

| Field | ES | EN |
| --- | --- | --- |
| Heading | Decide tu siguiente versión | Decide your next version |
| Governing signal | Señal prioritaria | Governing feedback |
| Answer target | Objetivo de esta respuesta | Target for this answer |
| Next decision | Decisión antes de volver a practicar | Decision before rehearsing again |

### Kind-specific target

| Kind | ES | EN |
| --- | --- | --- |
| `screen_opening` | Presentar el posicionamiento respaldado por la evidencia suministrada, un enfoque relevante y un puente seguro hacia la conversación. | Present positioning supported by the supplied evidence, a relevant focus, and a safe bridge into the conversation. |
| `proof_example` | Presentar contexto confirmado, una acción concreta y un impacto observado directamente. | Present confirmed context, a concrete action, and directly observed impact. |
| `eligibility_boundary` | Separar el dato suministrado, la condición de elegibilidad desconocida y una sola pregunta de aclaración. | Separate the supplied fact, the unknown eligibility condition, and one clarification question. |
| `compensation_boundary` | Separar la evidencia suministrada, la condición de compensación pendiente y el límite de decisión. | Separate the supplied evidence, the pending compensation condition, and the decision boundary. |
| `missing_detail` | Presentar el mínimo suministrado y el único detalle que todavía necesita aclaración antes del próximo ensayo privado. | Present the supplied minimum and the one detail that still needs clarification before the next private rehearsal. |

### Governing-label action

| Label | ES | EN |
| --- | --- | --- |
| `solid` | Conserva esta estructura para el próximo ensayo privado y mantén el alcance respaldado por la evidencia suministrada. | Keep this structure for the next private rehearsal and stay within the scope supported by the supplied evidence. |
| `confirm` | Confirma o acota el punto incierto antes del próximo ensayo privado. | Confirm or qualify the uncertain point before the next private rehearsal. |
| `do_not_assert` | Quita la afirmación sin respaldo; sustitúyela por evidencia respaldada o una aclaración acotada, o pausa la respuesta. | Remove the unsupported claim; replace it with supported evidence or a bounded clarification, or pause the answer. |

Immediately before the three-pair definition list, render one fixed explanation:

- ES: `Cuando aparecen varias señales, la que requiere más cautela guía la
  siguiente versión.`
- EN: `When several signals appear, the one requiring the most caution guides
  the next version.`

## Renderer design

- Replace label-only feedback descriptions with a closed mapping keyed by
  locale, question kind, and label.
- Pass the validated `question.kind` into the feedback renderer.
- Add a small helper that derives the governing label from only the labels
  actually present and fails closed for an empty or unsupported collection.
- Add a decision renderer keyed only by locale, validated kind, and governing
  label.
- Render the decision fields as `dl`, `dt`, and `dd`, not three paragraph
  labels.
- Compose the feedback sequence as:
  `handoff -> rehearsal -> feedback -> decision`.
- Keep sourced and independent pre-feedback composition unchanged.
- Keep all candidate-controlled text escaped. Continue ignoring
  `feedback.statement` in candidate-facing HTML.

No new schema field, score, adapter, or general-purpose abstraction is needed.

## Semantic HTML and ARIA

Feedback retains:

```html
<section class="practice-feedback"
         role="region"
         aria-labelledby="feedback-title"
         aria-describedby="feedback-ephemeral-note">
```

The decision region is:

```html
<section class="practice-decision"
         aria-labelledby="decision-title">
  <h2 id="decision-title">...</h2>
  <p>...</p>
  <dl>...</dl>
</section>
```

All IDs are unique and resolve in the same document. Natural document order
supplies the feedback-to-decision relationship; the feedback region alone
retains `aria-describedby="feedback-ephemeral-note"`. The page adds no
`aria-live`, `role=status`, control role, or focus target.

## Visual behavior

- Use the approved Variation A hierarchy: a separate decision panel with the
  existing forest background, white body text, and retained decision-term
  color `#dfbf70`. On the existing forest it has approximately 6.69:1 contrast.
- Keep explanatory text at 16px or larger and within 72ch.
- Require at least 4.5:1 contrast for normal text, 3:1 for large text, and 3:1
  for meaningful borders or other non-text indicators. Every feedback label
  and description uses ink text; forest, gold, and coral remain
  border/background accents rather than low-contrast text.
- The decision panel must look prominent but static: no button shape, pointer,
  hover action, or target-size affordance.
- At 640px and below, retain one column and at least 0.5rem side gutters. The
  definition list wraps without horizontal overflow at 320px and 200% zoom.
- In print, feedback and decision each use `break-inside: avoid`; feedback uses
  `break-after: avoid-page`; and decision uses `break-before: avoid-page`. If
  their combined height fits, they remain on the same page. The decision
  switches to white or transparent background, ink text, and a visible border
  so it remains legible when backgrounds are disabled.
- In forced colors, both regions use `Canvas`, `CanvasText`, and visible system
  borders. In increased contrast, feedback, decision, and item borders become
  at least 2px and headings remain explicit.
- Reduced-motion behavior remains unchanged; the feature adds no motion.

## Privacy and evidence boundaries

- In the new feedback and decision regions, render only fixed copy and existing
  localized category labels. Continue rendering the existing validated and
  escaped safe context, prompt, evidence, and boundary outside those regions.
- In the new regions, do not render the raw observed answer,
  `feedback.statement`, source refs, question/fact/requirement/claim/evidence/
  observation/rubric IDs, snapshots, source enum, recruiter identity, raw
  vacancy text, URLs, or external-action flag. Existing candidate-facing fields
  and their escaping behavior remain unchanged.
- Keep the artifact offline under the existing CSP with no remote scripts,
  fonts, images, or network connections.
- Preserve mode `0600`, atomic private writing, deterministic rendering, and
  no-save-by-default answer semantics.
- `solid` is a supplied categorical observation citing the observed answer and
  rubric. The renderer does not independently verify semantic correctness and
  never treats it as readiness or outcome evidence. It does not mean
  interview-ready, recruiter-approved, publishable, or likely to advance.

## Error handling

- Validation remains the first boundary. Closed mappings must contain exactly
  locales `{es, en}`, question kinds `{screen_opening, proof_example,
  eligibility_boundary, compensation_boundary, missing_detail}`, and labels
  `{solid, confirm, do_not_assert}`, without omissions or extras.
- Renderer helpers raise `ValueError` with only these privacy-safe messages:
  - `unsupported locale`
  - `unsupported question kind`
  - `unsupported feedback label`
  - `feedback labels must not be empty`
  - `feedback labels must be unique`
  - `feedback labels must use canonical order`
  Messages never echo supplied values.
- The governing helper accepts only the validator's canonical label order
  (`solid`, then `confirm`, then `do_not_assert`, with absent labels skipped).
  It rejects duplicates, noncanonical order, empty input, and unsupported
  labels rather than sorting or repairing them.
- Feedback, target, action, governing-label, and composed-decision helpers each
  reject unsupported parameters applicable to that helper. Direct helper tests
  cover unknown locale, kind, and label values and prove that errors do not
  echo them.
- `feedback_available` without an observed answer or observation remains a
  validator error.
- Pre-feedback states never render a decision region.

## Verification

Focused TDD must prove:

1. Every locale × kind × label combination renders the exact fixed feedback
   sentence defined above (30 cases).
2. Every locale × kind renders the exact target, and every locale × governing
   label renders the exact bounded action.
3. All seven non-empty canonical label subsets derive the expected governing
   label with `do_not_assert > confirm > solid`.
4. Unknown, empty, duplicate, and noncanonical label collections fail closed
   with the specified privacy-safe `ValueError` messages; unknown locale and
   kind values fail closed in each applicable helper without echoing input.
5. Feedback order is
   `rehearsal < feedback < decision < evidence < boundary`, with handoff first
   only when present.
6. The old feedback next-action section and generic “review and decide” copy
   are absent, while pre-feedback next-action behavior remains unchanged.
7. Feedback and decision have unique, resolved `aria-labelledby` references;
   feedback alone retains its resolved no-retention `aria-describedby`, and
   the decision region has no redundant description reference.
8. Only present feedback labels render. Missing categories are not invented.
9. Raw answer text, `feedback.statement`, internal IDs, snapshots, source enum,
   forms, controls, buttons, `aria-live`, and status roles are absent. The whole
   page has exactly one `href`, the existing skip link to `#main-content`, and
   no other link.
10. ES and EN HTML remains deterministic, offline, CSP-compatible, private,
    and writable only through the existing atomic mode-`0600` path.
11. The rendered visual checks prove:
    - at desktop, 320px mobile, and 200% zoom,
      `scrollWidth <= clientWidth`, every `dt` and `dd` is visible, no text is
      clipped, side gutters remain at least 0.5rem, and DOM order is unchanged;
    - print source CSS contains the specified break rules, and rendered print
      verification shows feedback and decision together when their combined
      height fits, with white/transparent decision background, ink text, and a
      visible border;
    - forced-colors rendering retains `Canvas`, `CanvasText`, visible system
      borders, and text labels for every category and decision meaning;
    - `prefers-contrast: more` makes feedback, decision, and item borders at
      least 2px; and
    - reduced-motion adds no animation and keeps the existing session animation
      disabled.
12. Existing contract, renderer, schema-conformance, static, privacy, and plugin
    release gates remain green.
13. Exactly one decision region renders with exactly three ordered `dt`/`dd`
    pairs: governing feedback, answer target, and next private action.
14. Candidate-reported fixtures for `screen_opening`,
    `eligibility_boundary`, `compensation_boundary`, and `missing_detail` in
    ready, awaiting, and feedback states render supplied/known wording across
    the rehearsal, feedback, and decision regions and never upgrade it to
    confirmed or verified evidence. `proof_example` retains its existing
    verified-fact gate and confirmed wording.

## Publication boundary

After implementation and independent code review:

1. run the full pre-publication gate matrix;
2. refresh provenance deterministically;
3. invoke exactly once the official helper
   `python3 -B /Users/kevinriosferrer/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py plugins/job-search-coach`,
   preserving base version `0.2.0`;
4. commit only the manifest and deterministic provenance files in the
   publication commit, with a clean tracked worktree before installation;
5. confirm immediately before installation that the user's standing exact
   authorization still applies to installing this newly published version;
6. install the exact new version into Codex only while that authorization gate
   remains satisfied;
7. compare the source plugin tree with the resolved installed cache tree;
8. validate and render canonical plus feedback/privacy sentinel fixtures from
   the installed copy; and
9. rerun the final gate matrix.

The increment is complete only after the exact new version is installed,
enabled, byte-identical to the published source, and the installed renderer
proves the feedback decision without exposing private data.

## Next independent cycle

Source-bound validation for triage-sourced practice remains the next planned
contract cycle. This feedback design neither weakens nor claims to solve the
current shape-only provenance boundary.
