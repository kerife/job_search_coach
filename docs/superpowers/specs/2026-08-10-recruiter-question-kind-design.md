# Recruiter question kind

## Goal

Bind the one safe question to the decision it is intended to unlock.

## Contract

Add a closed `question_kind` enum to the question object and require an exact
mapping from classification: screen invite → `screen_opening`, proof request →
`proof_example`, eligibility question → `eligibility_boundary`, compensation
question → `compensation_boundary`, and unknown → `missing_detail`. Decline
cannot be ready. Any mismatch, unsupported kind, or missing kind fails closed;
clarify and stop retain their existing behavior but still use the closed
question shape.

## Rendering

The ready preview displays one localized `Question type` label derived from the
validated enum next to the existing purpose and safe question. It remains
static and noninteractive, with no new raw data, identity, contact, time,
calendar, action, score, outcome, or link content.

## Verification

Tests cover valid mappings in English/Spanish, every mismatch and unknown kind,
ready/clarify/stop behavior, exactly one question, localized rendering,
escaping, accessibility/print/mobile, privacy, and unchanged routing.
