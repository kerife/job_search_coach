# Identity-free triage unlabeled-name guard

## Problem

Private recruiter reply triage promises identity-free input and output. Its
prose guard rejects explicit labels such as `Candidate name: ...` and some
contextual introductions, but accepts ordinary prose beginning with a full
capitalized name, for example `John Smith has a verified technical
achievement.` The renderer escapes that text but correctly preserves it, so a
personal name can still be persisted in an offline triage artifact.

## Decision

Extend the existing `unlabelled_identity` prose pattern in
`validate_private_recruiter_reply_triage.py` to cover the same conservative
verb family already used by the dossier practice identity-free guard:
`reports`, `describes`, `works`, `has`, `joined`, `explains`, `reported`,
`reporta`, `describe`, `trabaja`, `tiene`, `explica`, and `menciona`. Preserve
the existing contextual and company patterns and the technical-role allowlist
behavior. The error remains the fixed diagnostic category
`session contains forbidden unlabelled_identity prose`; raw names never appear
in diagnostics.

## Verification

Add RED cases for English and Spanish ordinary name sentences across
`safe_context.summary`, fact summary, question text, and blocked claims, and
assert the renderer rejects the same payload before writing HTML. Keep existing
role-focused acceptance cases green. Run triage API/CLI and renderer suites,
static/privacy/release gates, and the full plugin suite. No CSS, HTML template,
schema, or Superdesign dump changes are expected.
