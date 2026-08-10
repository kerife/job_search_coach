# Recruiter Handoff Re-entry Design

## Goal

Close the handoff seam between the private recruiter-reply triage artifact and
`prepare-role-interviews` without auto-starting preparation, persisting a raw
reply, or performing any LinkedIn, messaging, calendar, or recruiter action.

## Current evidence

- The ready triage artifact already validates one identity-free context summary,
  one verified fact, one question, and a mapped preparation scope.
- The rendered handoff is intentionally manual and omits internal IDs from HTML.
- `prepare-role-interviews` requires a supplied vacancy/context and fact matrix,
  waits for the candidate's answer before scoring, and forbids outcome claims.
- The missing boundary is a machine-readable re-entry receipt that downstream
  preparation can validate without reconstructing or broadening the input.

## Proposed contract

Add a required `reentry_packet` under the existing ready-only `handoff` object.
It is required when `state=ready_for_private_prep` and forbidden for
`clarify_first` or `stop`. It must contain exactly:

- `schema_version`: `private-recruiter-screen-reentry-v1`.
- `source_artifact_kind`: `private_recruiter_reply_triage`.
- `context_summary`: equal as a decoded Unicode string to `safe_context.summary`
  and the existing `handoff.packet.context_summary`.
- `fact_id`: the sole fact ID, whose state is `verified`, and equal to the
  existing `handoff.packet.fact_id`.
- `question_id`: the sole question ID, whose `fact_ids` contains `fact_id`, and
  equal to the existing `handoff.packet.question_id`.
- `prep_scope`: equal to the existing `question.kind` mapping and the existing
  `handoff.packet.prep_scope`.
- `manual_reentry_required`: `true`.
- `candidate_answer_state`: `unanswered`.
- `score_state`: `unknown`.

The contract is closed (`additionalProperties=false`). Clarify and stop states
must omit both handoff and re-entry packet. Candidate-reported facts,
unknown IDs, mismatched context/scope, answer text, scores, recruiter/company
identity, raw reply text, contact details, URLs, times, sending, calendar, and
outcome/fit/offer language fail closed. The packet is a local draft-only
continuation receipt, not an execution packet and not a durable answer store.

## Data flow and UI

The validator derives and checks the packet against the already validated triage
fields. The renderer may show a fixed localized “manual re-entry” scope cue but
must not show internal IDs or raw packet fields. No buttons, links, forms, or
auto-start hooks are added. The existing ready/clarify/stop visual states and
normal recruiter-reply routing remain unchanged.

## Verification

- Contract RED/GREEN tests cover valid English/Spanish ready packets, omission
  for clarify/stop, missing/extra fields, candidate-reported facts, mismatched
  IDs/context/scope, answer/score injection, and forbidden prose.
- Renderer tests cover ready-only localized scope, HTML escaping, no internal
  IDs/raw/action output, deterministic output, accessibility, and 0600 atomic
  file behavior.
- Integration tests prove private triage precedence remains above normal
  recruiter-reply/debug/router/module packet routes and preparation does not
  auto-start.
- Release gates refresh provenance mechanically, run focused and full suites,
  invoke the cachebuster exactly once, install the exact version, compare the
  source/cache inventory, and smoke clarify/ready/stop outputs.

## Non-goals

No vacancy research, recruiter expansion, LinkedIn browsing, outgoing copy,
message/calendar action, candidate answer storage, scoring before an observed
answer, interview likelihood, or automated handoff execution.
