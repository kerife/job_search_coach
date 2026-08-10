# Recruiter Follow-through Checkpoint Design

## Goal

Close the loop after a private recruiter outcome receipt by recording one
candidate-supplied action state and the next observable event, without changing
the original receipt, storing raw messages, or executing any external action.

## Current evidence

- `private_recruiter_conversion_outcome_v1` safely records a dated observed
  event and a fixed next-safe-action, but is terminal.
- Existing interview preparation and outcome tracking contracts require manual
  re-entry and observed evidence; they do not provide a closed checkpoint for
  accepted/deferred/declined/completed follow-through.
- The current receipt and CSV path must remain unchanged and candidate-isolated.

## Proposed artifact

Create `private_recruiter_followthrough_checkpoint_v1`, a closed artifact with:

- `schema_version`, `artifact_kind`, `locale` (`en`/`es`).
- `source_receipt`: closed `schema_version`, `artifact_kind`, `D-###` receipt
  ID, source version, and source event type; it is accepted only when a
  separately supplied valid receipt matches every field.
- `action_state`: `accepted`, `deferred`, `declined`, or `completed`.
- `observed_date`: real ISO date no later than an injected `as_of` date.
- `next_measurement_event`: `screen_prepared`, `screen_attended`,
  `interview_requested`, `stop_decision`, or `unknown`.
- `next_safe_action`: exact mapping: accepted → `manual_reenter_private_prep`;
  deferred → `clarify_context_before_reply`; declined → `record_stop_decision`;
  completed with `screen_prepared`/`interview_requested` →
  `route_to_prepare-role-interviews`; completed with `stop_decision` →
  `record_stop_decision`; all other completed cases →
  `clarify_context_before_reply`.
- For `accepted`, `deferred`, and `declined`, `next_measurement_event` must be
  `unknown`; only `completed` may name a concrete next event. A source
  `stop_decision` may only be `declined` or `completed`, and it can never route
  to preparation. `observed_date` must be on or after the source receipt's
  `event_date` and no later than the injected `as_of` date (default today).
- immutable `delivery`: draft-only, no external actions, no calendar, no raw
  event retention, local save disabled.

No free-form prose, candidate ID, recruiter/company identity, URL, contact,
time, score, outcome/fit/offer guarantee, answer text, or extra field is
allowed. A checkpoint is transient unless explicitly accepted by a later local
workflow; the renderer does not persist it. It cannot auto-create a module
execution packet, update CSV, aggregate candidates, or reuse an answer.

## Validation and rendering

The validator accepts `--receipt <path>` and `--as-of <date>`. It validates the
receipt first, then exact source ID/version/event equality, checkpoint enums,
date, and action mapping. The offline EN/ES renderer shows fixed state/date/
next-event/next-action labels, omits all IDs, and has no controls, links, raw
text, or external-action language. Output remains atomic, symlink-safe, and
mode `0600`.

## Verification

- Contract tests cover valid states, every mapping branch, missing/invalid
  receipt, mismatched source, dates, extra/wrong types, raw/identity/action/
  outcome/score injection, and immutable delivery.
- Renderer tests cover EN/ES, ID omission, deterministic fixed copy, no
  interactive output, accessibility/print/forced-colors, and 0600 writes.
- Routing tests prove completed screen/interview follows only manual prep,
  decline/stop never routes to prep, replay with identical validated inputs is
  byte-identical and side-effect free, and normal CSV and recruiter paths
  remain unchanged.

## Non-goals

No LinkedIn browsing, messaging, scheduling, scorecard, causal attribution,
candidate identity storage, aggregation, or automatic preparation.
