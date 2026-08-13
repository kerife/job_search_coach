# Identity-free triage bare-name guard

## Problem

Private recruiter reply triage promises identity-free input and output. The
existing prose guard rejects labelled and contextual personal names, but a
summary containing only a bare two-token name such as `John Smith` can pass
validation and then be persisted by the HTML renderer.

## Decision

Extend the existing identity-free prose policy with a structural bare-name
check. When a prose value, after trimming terminal punctuation, consists only
of two to four capitalized name tokens (including accented, apostrophe, or
hyphenated tokens), return the existing fixed
`session contains forbidden unlabelled_identity prose` diagnostic. Apply this
to the same prose fields already traversed by `_walk_strings`; do not echo the
name. Keep technical role phrases and ordinary sentences accepted, and retain
the existing contextual-name and company rules. The renderer remains
validator-gated, so no HTML or CSS changes are required.

## Verification

Add RED cases for English and Spanish bare names in context, fact, question,
and blocked-claim prose, plus renderer rejection with no name in diagnostics.
Add acceptance cases for role-focused prose and ordinary sentences. Run the
triage API/CLI and renderer suites, static/privacy/release gates, and the full
plugin suite. No schema, HTML template, CSS, or Superdesign dump changes are
expected.
