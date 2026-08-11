# Triage identity-free prose guard

## Context

Professional Growth Coach promises that private recruiter triage keeps prose
identity-free. The current validator catches labelled identity/company forms,
but a sentence such as `Jordan Lee works at Acme Corporation` can pass and be
embedded in the private HTML receipt. This is a privacy-contract gap, not a
request to infer or store a person's identity.

## Design

Extend the existing triage prose-safety guard with conservative contextual
patterns for an unlabelled person/company disclosure. The guard will reject a
full-name-shaped phrase only when it is coupled to a relationship or
employment verb/marker (for example `works at`, `described`, `contacted`, or
`from <company>`). It will not reject every pair of capitalized words, which
would incorrectly block ordinary role, product, or sentence prose.

Apply the same guard before length/field-specific checks to every client-facing
triage prose field: `safe_context.summary`, fact summaries, question text, and
blocked claims. Keep the existing labelled identity/company and raw-contact
guards unchanged. The renderer continues to validate first and therefore emits
no HTML for rejected input.

## Contract and privacy behavior

- Invalid input returns a bounded, field-oriented error without echoing the
  supplied prose or names.
- Valid canonical fixtures and ordinary role-focused prose remain accepted.
- The HTML renderer never receives the rejected payload, so sentinel names and
  company names cannot appear in the receipt.
- No schema, external action, network, or UI flow changes are introduced in
  this increment.

## Verification

1. Add RED tests for contextual unlabelled person/company prose in all four
   fields, plus a valid ordinary role sentence.
2. Implement the shared guard and run the focused triage validator/renderer
   suite.
3. Run schema/privacy/static/release gates and the full repository suite.
4. Consume the plugin cachebuster once, install the new marketplace version,
   compare source and cache byte-for-byte, and run the installed validator.

