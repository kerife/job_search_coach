# Private recruiter-screen handoff

## Goal

Make a `ready_for_private_prep` recruiter-reply triage result re-enterable by
the interview-preparation skill without copying raw reply text, identities, or
unverified facts.

## Contract

Add one closed `handoff` object only when `state` is
`ready_for_private_prep` and `handoff_allowed` is true. It contains the fixed
module `prepare-role-interviews`, the fixed scope `one recruiter-screen
question`, the fixed input mode `identity_free_summary_plus_verified_fact`,
`auto_start: false`, `external_actions: false`, `raw_reply_retained: false`,
and `local_save_mode: disabled`. Clarify and stop artifacts must omit the
object; candidate-reported facts cannot produce it.

The validator binds the object to the same confirmed stage, role context,
critical constraints, and verified fact already required for a ready handoff.
Unknown fields, alternate modules/scopes, IDs, contacts, times, links,
messages, calendar actions, and outcome promises remain rejected by the
existing prose gate. The handoff is a re-entry cue, never an auto-start or
transfer of execution context.

## Rendering and routing

The ready card shows a localized “private recruiter-screen preparation” scope
and “re-enter preparation manually” boundary, plus the existing no-action and
no-save disclosures. Clarify and stop retain their current single-question or
stop presentation. Routing keeps private triage above ordinary reply handling,
suppresses router/module packets, and leaves the normal LinkedIn dossier path
unchanged.

## Verification

RED tests cover missing/extra handoff fields, handoff in clarify/stop,
candidate-reported facts, wrong module/scope, auto-start/action/raw-save
mutations, and ready rendering. GREEN gates cover the existing triage and
practice suites, accessibility/print/privacy invariants, routing precedence,
and deterministic 0600 output.
