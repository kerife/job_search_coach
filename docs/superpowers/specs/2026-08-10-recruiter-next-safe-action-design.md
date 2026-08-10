# Recruiter next safe action

## Goal

Make the triage result's next safe step machine-readable without turning it
into an executable action.

## Contract

Add a required closed `next_safe_action` enum to every triage state with an
exact mapping: `clarify_first` → `clarify_context_before_private_prep`,
`ready_for_private_prep` → `manual_reenter_private_prep`, and `stop` →
`record_stop_decision`. Schema and validator reject missing, unknown, or
mismatched values. Existing handoff and verified-fact rules remain unchanged.

## Rendering

Render one localized static next-step label from the validated enum. It has no
button, link, form, auto-start, calendar, contact, time, score, guarantee, or
outcome language. Existing state-specific gates remain visually and
semantically intact.

## Verification

Tests cover all state mappings in English/Spanish, missing/unknown/mismatch
mutations, ready/clarify/stop rendering, one-question invariant, privacy,
accessibility, print/mobile, deterministic output, and unchanged routing.
