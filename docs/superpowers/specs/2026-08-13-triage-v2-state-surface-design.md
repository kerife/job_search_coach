# Triage v2 Answer-Path Design

## Goal

Make the ready triage handoff actionable without weakening its manual, private
boundary: show a short answer-path scaffold derived from the validated question
kind, while making the v2 state/locale contract explicit across all states.

## Scope

The renderer adds one ready-only `triage-handoff-answer-path` card. Its copy is
fixed and localized by the validated question kind; it never interpolates an
answer, ID, snapshot, recruiter text, score, or readiness claim. The v2 locale
matrix proves the card and surrounding question surface remain state-correct.
No schema or fixture changes are needed.

## Contract

- Every v2 case has `ui_locale` and `content_locale`, with the v1 `locale`
  field removed.
- The document language and fixed labels use `ui_locale`.
- Dynamic safe context, fact, and question prose use `content_locale` and carry
  a matching `lang` attribute.
- `clarify_first` renders exactly one visible question section and exactly one
  occurrence of the question text.
- `ready_for_private_prep` omits the clarify question section but retains the
  question once in the handoff preview.
- `stop` omits both the question section and question text from the document.
- `ready_for_private_prep` shows exactly one answer-path card with a semantic
  heading and three static steps. `clarify_first` and `stop` omit it.
- `screen_opening` and `proof_example` use a context/action/result scaffold;
  `eligibility_boundary` and `compensation_boundary` use a known-boundary/
  missing-confirmation/question scaffold; `missing_detail` uses a known-fact/
  exact-gap/clarification scaffold.
- The card contains no `button`, `form`, `input`, `a`, score, auto-start, or
  persisted-answer language.
- The matrix covers both EN UI/ES content and ES UI/EN content for each state,
  without asserting private IDs, snapshots, or raw recruiter text.

## Verification

Focused renderer tests must fail if the locale split is ignored, if a state
duplicates or drops the question surface, if the answer-path card appears in a
non-ready state, or if v2 falls back to the v1 locale field. Existing validator,
renderer, parity, and plugin suites remain regression gates.
