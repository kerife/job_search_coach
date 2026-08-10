# Recruiter question purpose

## Goal

Make the single safe question actionable by explaining what decision it is
intended to unlock.

## Design

Add one localized `Question purpose` cue immediately before the safe-question
row in the ready-only preview. Fixed copy is derived from the existing
classification: screen invite opens readiness, proof request selects one
verified example, eligibility/compensation clarify their boundary, and unknown
finds the smallest missing detail. `decline` cannot be ready. The purpose is
descriptive, not a score, promise, or additional question.

No schema, routing, persistence, identity, raw reply, contact, calendar,
action, outcome, or link changes are introduced. Clarify/stop omit the preview
and purpose cue.

## Verification

Tests cover all ready classifications in English and Spanish, exact order
context → fact → purpose → one question, omission outside ready, no extra
question marks or unsafe prose, escaping, accessibility/print/mobile hooks,
and deterministic output.
