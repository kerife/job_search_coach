# Recruiter handoff packet

## Goal

Bind a ready triage result to the exact identity-free inputs that private
recruiter-screen preparation may receive.

## Contract

Add a closed `handoff_packet` only for `ready_for_private_prep` containing the
validated `context_summary`, the sole verified `fact_id`, the sole `question_id`,
and a fixed `prep_scope` mapped from `question.kind`: opening, proof example,
eligibility boundary, compensation boundary, or missing detail. All values
must match existing fields; unknown IDs, mismatched kinds, extra fields, or
candidate-reported facts fail closed. Clarify and stop omit the packet.

The packet remains metadata for manual re-entry, not an execution packet: no
raw recruiter text, identity, contact, calendar, links, score, outcome, send,
or auto-start fields are permitted. Existing fixed handoff delivery guards
remain authoritative.

## Rendering and routing

The ready card shows a localized preparation-scope receipt from the validated
enum. Routing still emits no module packet/router rows and does not invoke
private practice automatically.

## Verification

Tests cover schema/validator bindings, ready-only packet presence, all five
scopes in EN/ES, mutation rejection, privacy/no-action/one-question behavior,
escaping, accessibility/print/mobile, and unchanged clarify/stop/legacy routes.
