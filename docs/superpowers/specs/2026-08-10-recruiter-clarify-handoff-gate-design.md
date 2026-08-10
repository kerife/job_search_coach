# Recruiter clarify handoff gate

## Goal

Explain why a private recruiter triage is not ready for handoff and what
evidence category must be confirmed next.

## Design

Only `clarify_first` renders a static localized `Handoff gate` cue before its
existing question. Fixed mapping: a `candidate_reported` fact means a verified
fact is still needed; missing stage/role/critical constraints means screen
context still needs confirmation; otherwise one clarification remains. The
cue never interpolates `blocked_claims` or other user prose.

Ready and stop output remain unchanged. The cue has no button, link, score,
action, calendar, identity, raw text, contact, or outcome language and keeps
exactly one question overall.

## Verification

Tests cover all blocker categories in English/Spanish, clarify-only presence,
ready/stop omission, ordering, accessibility/print/mobile, escaping, privacy,
and deterministic output.
