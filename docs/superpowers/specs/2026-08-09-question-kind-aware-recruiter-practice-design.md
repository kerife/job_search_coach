# Question-kind-aware recruiter practice design

## Status

Approved visual direction: Superdesign Variation A, decision-led continuation.

## Problem

The private recruiter-practice artifact currently uses the same three-part
`context / action / result` scaffold for every validated `question.kind`.
That scaffold is suitable for a proof example but is misleading for boundary
and missing-detail questions. The awaiting state also says that the artifact is
waiting for an answer even though the offline page has no input control and
does not identify where the answer belongs.

## Outcome

Make the first decision after reading the prompt unambiguous:

1. A sourced, pre-feedback practice session says where to answer before it
   presents the coaching scaffold.
2. The awaiting state describes readiness rather than implying that the static
   page is listening.
3. The scaffold is selected from the five already validated question kinds.
4. The page remains private, offline, non-interactive, and ephemeral. It gains
   no form, link, button, automatic transfer, storage, score, or external
   action.

## Scope

### In scope

- Change the visible `awaiting_answer` label:
  - ES: `Lista para responder`
  - EN: `Ready to answer`
- Add a closed bilingual rehearsal-copy mapping for every existing
  `question.kind`.
- In sourced `ready_to_practice` and `awaiting_answer` sessions, place
  `Siguiente paso / Next step` after the prompt and handoff and before the
  rehearsal scaffold.
- Tell sourced sessions to return to the originating private Codex
  conversation to answer, while reiterating that this HTML page does not save
  the response.
- Preserve the independent-session next-action semantics because an
  independent artifact does not prove that an originating Codex conversation
  exists.
- Update focused renderer, accessibility, privacy, and static release-gate
  coverage.

### Out of scope

- Contract or JSON Schema changes.
- New `question.kind` values.
- Dossier-to-practice provenance expansion.
- Input controls, links, buttons, clipboard actions, or automatic navigation.
- Capturing, retaining, scoring, or transmitting an answer.
- Changing feedback taxonomy, evidence, safe-boundary logic, or raw-data
  redaction.

## Information architecture

### Sourced pre-feedback session

The document order is:

1. State
2. Safe context
3. Practice prompt and purpose
4. Practice source handoff
5. Next step and response venue
6. Question-kind-aware answer structure
7. Evidence
8. Safe boundary

This is the approved decision-led direction. A reader learns where the answer
belongs before reading coaching instructions. The next-step region describes
the prompt and question text, not the later rehearsal heading.

### Independent pre-feedback session

The current order and autonomous wording remain:

1. State
2. Safe context
3. Practice prompt and purpose
4. Question-kind-aware answer structure
5. Next step
6. Evidence
7. Safe boundary

The renderer must not invent a source or originating conversation.

### Feedback session

Keep the current feedback flow unchanged: handoff when present, rehearsal,
next step, feedback, evidence, boundary. The feedback next step continues to
reference the quiet feedback region. This increment does not reorder completed
practice or change its no-retention boundary.

## Closed coaching copy

The renderer derives the scaffold only from the validated `question.kind`.
Candidate prose is never interpolated into labels or instructions.

| Kind | ES hint | ES steps | EN hint | EN steps |
| --- | --- | --- | --- | --- |
| `screen_opening` | Prepara una apertura breve que conecte el contexto confirmado con la conversación. | Contexto confirmado; Enfoque relevante; Puente a la conversación | Prepare a brief opening that connects confirmed context to the conversation. | Confirmed context; Relevant focus; Conversation bridge |
| `proof_example` | Presenta una evidencia confirmada en tres movimientos fáciles de seguir. | Contexto de la evidencia; Acción técnica concreta; Impacto observado directo | Present confirmed evidence in three easy-to-follow moves. | Evidence context; Concrete technical action; Directly observed impact |
| `eligibility_boundary` | Separa lo confirmado de la pregunta de elegibilidad que aún debe aclararse. | Contexto confirmado; Pregunta abierta; Límite seguro | Separate confirmed context from the eligibility question that still needs clarification. | Confirmed context; Open question; Safe boundary |
| `compensation_boundary` | Separa lo conocido de la condición de compensación que necesitas aclarar. | Contexto conocido; Pregunta de compensación; Límite de decisión | Separate what is known from the compensation condition you need to clarify. | Known context; Compensation question; Decision boundary |
| `missing_detail` | Expón lo mínimo conocido y formula solo el detalle que falta confirmar. | Mínimo confirmado; Detalle faltante; Próxima confirmación | State the minimum known context and ask only for the detail still needing confirmation. | Confirmed minimum; Missing detail; Next confirmation |

Boundary scaffolds must not assert eligibility, legal rights, compensation
amounts, availability, fit, or outcomes. The proof scaffold says `observed`
rather than encouraging an unverified result.

## Next-action copy

For a sourced `awaiting_answer` session:

- ES: `Regresa a la conversación privada de Codex que originó esta práctica para responder. Esta página no guarda tu respuesta.`
- EN: `Return to the private Codex conversation that originated this practice to answer. This page does not save your answer.`

For a sourced `ready_to_practice` session:

- ES: `Lee la pregunta y prepara tu respuesta; después regresa a la conversación privada de Codex que originó esta práctica. Esta página no guarda tu respuesta.`
- EN: `Read the question and prepare your answer; then return to the private Codex conversation that originated this practice. This page does not save your answer.`

Independent sessions retain their current read/answer wording and no-save
statement. `feedback_available` retains its current review-feedback wording.

## Renderer design

- Replace the generic rehearsal keys with a closed mapping keyed by locale and
  `question.kind`; each entry contains one hint and exactly three steps.
- Make `_render_rehearsal_scaffold` require the validated question kind and
  fail closed if a caller bypasses validation with an unsupported kind.
- Make next-action selection aware of whether the session has a sourced
  handoff. Do not inspect or render provenance identifiers.
- Compose the pre-feedback sequence conditionally:
  - sourced: `handoff -> next_action -> rehearsal`
  - independent: `rehearsal -> next_action`
- Preserve the current feedback sequence.
- Keep all candidate-controlled prose escaped and keep fixed copy fixed.

No new abstraction beyond these small closed mappings is required.

## Accessibility and visual behavior

- Keep one visible state chip associated with the practice region through
  `aria-describedby="practice-session-state"`.
- Do not add `aria-live` or `role="status"`; the document is static.
- A sourced pre-feedback next step references `prompt-title` and
  `practice-question-text`, which both exist before it in document order.
- Feedback next action continues to reference `feedback-title`.
- Preserve the existing responsive, print, forced-colors, and
  prefers-contrast behavior. The approved visual direction changes hierarchy
  and copy, not the palette, typography, borders, spacing system, or motion.

## Verification

Focused TDD must cover:

1. ES and EN awaiting state labels are `Lista para responder` and
   `Ready to answer`; the old awaiting labels are absent.
2. Each of the five question kinds renders its localized hint and exactly three
   localized steps.
3. Unsupported kinds fail closed in the rehearsal helper.
4. Sourced pre-feedback order is
   `handoff < next_action < rehearsal < evidence < boundary`.
5. Independent pre-feedback order remains
   `rehearsal < next_action`, with no source claim.
6. Sourced next-action copy names the private Codex conversation and states
   that the page does not save the answer.
7. Feedback order and `aria-describedby="feedback-title"` remain unchanged.
8. Pre-feedback next action references prompt/question IDs and does not point
   forward to `rehearsal-title`.
9. HTML contains no raw answer, internal Q/R/F/C/E/OBS/RB identifiers,
   provenance snapshot, source enum, form, input, textarea, button, external
   link, or external-action authorization.
10. Existing renderer, contract, static, schema-conformance, and plugin release
    gates remain green.

## Acceptance boundary

The increment is complete when the approved hierarchy and closed coaching copy
render deterministically for both locales and all five kinds, with no schema or
privacy-boundary change. Dossier provenance and cross-artifact receipt
validation remain a separate future design cycle.
