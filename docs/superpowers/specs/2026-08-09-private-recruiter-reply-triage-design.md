# Private Recruiter Reply Triage Design

## Goal

Turn an identity-free inbound recruiter-reply summary into a private decision card: classify the reply, decide clarify/prepare/stop, expose one missing question, and preserve a draft-only handoff without sending or scheduling anything.

## Product decision

Keep the executive dossier and practice-session contracts separate. Add a closed triage-session artifact that accepts only a safe summary, one candidate fact, and explicit constraints; it never accepts raw recruiter text, identity, URL, contact, or attachment.

## States and flow

- `clarify_first`: show one smallest missing question and no handoff.
- `ready_for_private_prep`: show categorical ready decision and local handoff to interview preparation.
- `stop`: show the bounded reason and no draft/handoff.

Every card has a neutral classification chip, “Qué sabemos”, “Falta confirmar”, “No afirmar”, a no-save disclosure, and the no-action boundary. Classification never implies permission or fit.

## Safety

No raw reply, recruiter/company identity, contact details, URLs, calendar data, compensation/eligibility claims, outcome promises, send controls, or external action. `draft_only=true`, `external_actions_authorized=false`, `no_calendar_action=true`, `raw_reply_retained=false`, and `local_save_mode=disabled` are immutable. A handoff is false unless stage/role context, supported fact, and critical constraints are confirmed.

## Visual direction

Reuse the approved paper/forest/gold/coral card system. Use semantic headings, visible text states, one-column mobile flow, print-safe layout, `aria-live=polite` only for state updates, and no color-only decisions.

## Verification

Valid ES/EN clarify, ready, and stop fixtures render deterministically at 0600. Missing/identity/raw/action/time/guarantee/analytics mutations fail closed. Normal dossier and private practice routing remain unchanged. Full, privacy, static, schema, and official release gates stay green.
