# Candidate identity guard for private recruiter triage

## Context

The private recruiter triage contract is identity-free, but its prose guard
currently catches recruiter/contact labels and selected unlabelled names while
missing candidate labels such as `Candidate name: John Smith` and
`Nombre del candidato: Juan Pérez`. The validator accepts those values and the
renderer places them in the private HTML artifact.

## Design

Extend the existing `FORBIDDEN_PROSE["identity"]` rule only for explicit
candidate identity markers in English and Spanish:

- `candidate`, `candidate name`, `candidate:`, `candidate is/named`;
- `nombre del candidato`, `nombre de la candidata`, `candidato/a`, and their
  `es/llamado` forms.

The guard remains prose-level and bounded: it rejects the field through the
existing privacy-safe error, never echoes the value, and leaves role-focused
words such as `candidate evidence` or `candidate-reported` untouched unless a
name/value follows an identity marker. No schema, renderer markup, locale,
snapshot, or external-action behavior changes.

## Acceptance

1. Validator rejects candidate-labelled names in every prose field currently
   traversed by `_walk_strings`.
2. Renderer raises its existing validation error and never emits the sentinel
   name or raw prose.
3. Existing recruiter/contact/company, unsupported-script, v1/v2, and safe
   English/Spanish fixtures remain green.
4. Static, privacy, schema, release, source/cache, and installed smoke gates
   remain green before publishing a new cachebuster.
