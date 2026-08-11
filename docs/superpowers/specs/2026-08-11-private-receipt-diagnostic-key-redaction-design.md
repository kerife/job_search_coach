# Private receipt diagnostic-key redaction

## Context

The follow-through checkpoint and conversion-outcome validators reject closed
objects, but their unsupported-field errors currently interpolate the supplied
field name verbatim. Triage and practice already use the shared
`safe_diagnostic_field_name` policy. A contact-, path-, or credential-shaped
key must not reach validator lists or CLI stderr.

## Contract

- `validate_checkpoint` and `validate_outcome` continue to reject unknown keys.
- Suspicious keys render as exactly `<redacted-field>` in the error context.
- Ordinary short keys retain their current wording and value.
- No schema, HTML, IDs, actions, persistence, or loader behavior changes.
- The shared sanitizer remains the single policy for all four private receipt
  validators.

## Verification

Table-driven tests mutate valid checkpoint and outcome fixtures with contact,
local-path, and credential-shaped keys, asserting rejection and absence of
each sentinel. Existing `extra` rejection tests preserve ordinary diagnostics.
