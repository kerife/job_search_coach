# State-aware recruiter triage question

## Context

The private recruiter triage renderer currently emits the `Confirm next` /
`Falta confirmar` question section for every decision state. In
`ready_for_private_prep`, the same validated question is already shown once in
the manual preparation preview, so the page duplicates it. In `stop`, the
question contradicts the decision and its `record_stop_decision` boundary by
suggesting that preparation can continue.

## Decision

Render the standalone question section only for `clarify_first`.

- `clarify_first` keeps the existing localized heading and question.
- `ready_for_private_prep` keeps the question exactly once inside the existing
  ready-only preparation preview.
- `stop` omits the interrogative section entirely; its stop decision, safe next
  step, and no-continuation boundary remain visible.

This is a renderer-only visibility correction. It does not change schemas,
state enums, question text, handoff packets, IDs, persistence, external
actions, or employment-boundary copy.

## Verification

Tests will assert for both EN and ES that:

1. clarify output contains the standalone question section and question text;
2. ready output contains the question exactly once and keeps the handoff
   preview;
3. stop output contains neither the question section nor the question text;
4. all existing deterministic, accessibility, print, privacy, and no-action
   contracts remain unchanged.

No browser screenshot is claimed; the evidence is deterministic renderer HTML
and static contract tests.
