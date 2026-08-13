# Identity-free triage bare-name guard

## Problem

Private recruiter reply triage promises identity-free input and output. The
existing prose guard rejects labelled and contextual personal names, but a
summary containing only a bare two-token name such as `John Smith` can pass
validation and then be persisted by the HTML renderer.

## Decision

Extend the existing identity-free prose policy with a structural bare-name
check. After trimming terminal punctuation, reject any standalone two-to-four
token Title Case phrase, honorific form, or surname-particle form such as `van
der Meer` or `Juan de la Cruz`, except for the explicit closed vocabulary of
known plugin labels (the entries in `_SAFE_STANDALONE_PROSE`, including
`Recruiter Screen`, `AWS Lambda`, `Mexico City`, and `Principal Engineer`).
This avoids an impossible finite name catalog while preserving legitimate
stage, role, technology, and location labels. Unknown standalone Title Case
phrases remain rejected, while explanatory sentences remain accepted. Return the existing fixed
`session contains forbidden unlabelled_identity prose` diagnostic, never echo
the candidate, and keep the existing contextual-name and company rules. The
renderer remains validator-gated, so no HTML or CSS changes are required.

## Verification

Add RED cases for English and Spanish bare names, uncommon names, honorifics,
and surname particles in context, fact, question, and blocked-claim prose,
plus renderer rejection with no name in diagnostics. Add acceptance cases for
technical phrases such as `AWS Lambda`, `Machine Learning`, and `Kubernetes
Platform` both as approved standalone labels and embedded in explanatory
sentences.
Run the triage API/CLI and renderer suites, static/privacy/release gates, and
the full plugin suite. No schema, HTML template, CSS, or Superdesign dump
changes are expected.
