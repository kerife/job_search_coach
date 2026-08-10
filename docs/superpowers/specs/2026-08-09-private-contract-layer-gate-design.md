# Private contract-layer gate

## Goal

Ensure every private conversion-outcome and follow-through fixture passes both
the dependency-free JSON Schema subset checker and its authoritative Python
semantic validator.

## Design

Extend the existing private schema conformance harness with a second, explicit
semantic layer. Conversion fixtures are loaded through
`validate_private_recruiter_conversion_outcome.load_outcome` and validated with
`validate_outcome(..., today=date(2026, 8, 9))`. Follow-through fixtures are
loaded with a fixed screen-requested receipt and validated with
`validate_checkpoint(..., as_of=date(2026, 8, 9))`. The harness fails with a
bounded, non-sensitive error if either layer rejects a fixture.

Negative cases remain in-memory mutations: future dates, mismatched receipt
event, enabled external action, and an incorrect next-safe action. They must
fail the semantic validator even when the schema layer accepts the mutation.
No runtime artifact, routing behavior, external action, identity field, or
third-party dependency is added.

## Acceptance

- All existing conversion and follow-through fixtures pass both layers.
- The four semantic mutations are rejected deterministically.
- Static checks invoke the expanded harness and retain bounded diagnostics.
- Existing focused and full plugin tests remain green.
